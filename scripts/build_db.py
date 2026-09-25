"""Build a clean SQLite database (data/football.db) from the raw CSV files.

Design choices (things to be able to explain in an interview):
- SQLite: a single file, no server, and the LLM will later write SQL against it.
- A `match_id` primary key, so goals and shootouts link to matches with a simple JOIN
  instead of a 3-column join on (date, home_team, away_team).
- A precomputed `winner` column, because "who won?" is the most common question and
  pre-computing it makes the SQL the LLM has to write much simpler.
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "football.db"
MATCH_KEY = ["date", "home_team", "away_team"]


def load_matches() -> pd.DataFrame:
    matches = pd.read_csv(RAW_DIR / "results.csv")
    matches = matches.dropna(subset=["home_score", "away_score"])  # drop unplayed fixtures, if any
    matches["home_score"] = matches["home_score"].astype(int)
    matches["away_score"] = matches["away_score"].astype(int)
    matches["neutral"] = matches["neutral"].astype(bool)

    matches["winner"] = "Draw"
    matches.loc[matches.home_score > matches.away_score, "winner"] = matches.home_team
    matches.loc[matches.home_score < matches.away_score, "winner"] = matches.away_team

    matches = matches.sort_values("date").reset_index(drop=True)
    matches.insert(0, "match_id", matches.index + 1)
    return matches


def attach_match_id(df: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Replace the (date, home_team, away_team) key with match_id."""
    merged = df.merge(matches[["match_id", *MATCH_KEY]], on=MATCH_KEY, how="inner")
    lost = len(df) - len(merged)
    if lost:
        print(f"  warning: {lost} rows had no matching game and were dropped")
    return merged


def main() -> None:
    matches = load_matches()

    goals = attach_match_id(pd.read_csv(RAW_DIR / "goalscorers.csv"), matches)
    goals = goals.dropna(subset=["scorer"])
    goals = goals[["match_id", "team", "scorer", "minute", "own_goal", "penalty"]]

    shootouts = attach_match_id(pd.read_csv(RAW_DIR / "shootouts.csv"), matches)
    shootouts = shootouts[["match_id", "winner", "first_shooter"]]

    former_names = pd.read_csv(RAW_DIR / "former_names.csv")

    DB_PATH.unlink(missing_ok=True)  # rebuild from scratch each time
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE matches (
                match_id   INTEGER PRIMARY KEY,
                date       TEXT NOT NULL,      -- ISO format YYYY-MM-DD
                home_team  TEXT NOT NULL,
                away_team  TEXT NOT NULL,
                home_score INTEGER NOT NULL,
                away_score INTEGER NOT NULL,
                tournament TEXT NOT NULL,      -- e.g. 'FIFA World Cup', 'Friendly'
                city       TEXT,
                country    TEXT,               -- country where the match was played
                neutral    INTEGER NOT NULL,   -- 1 if played on neutral ground
                winner     TEXT NOT NULL       -- team name, or 'Draw'
            )""")
        conn.execute("""
            CREATE TABLE goals (
                match_id INTEGER NOT NULL REFERENCES matches(match_id),
                team     TEXT NOT NULL,        -- team credited with the goal
                scorer   TEXT NOT NULL,
                minute   INTEGER,
                own_goal INTEGER NOT NULL,
                penalty  INTEGER NOT NULL
            )""")
        conn.execute("""
            CREATE TABLE shootouts (
                match_id      INTEGER NOT NULL REFERENCES matches(match_id),
                winner        TEXT NOT NULL,
                first_shooter TEXT
            )""")
        matches.to_sql("matches", conn, if_exists="append", index=False)
        goals.to_sql("goals", conn, if_exists="append", index=False)
        shootouts.to_sql("shootouts", conn, if_exists="append", index=False)
        former_names.to_sql("former_names", conn, index=False)

        # Indexes on the columns the agent will filter and join on most
        conn.execute("CREATE INDEX idx_matches_home ON matches(home_team)")
        conn.execute("CREATE INDEX idx_matches_away ON matches(away_team)")
        conn.execute("CREATE INDEX idx_goals_match ON goals(match_id)")

    print(f"Built {DB_PATH.name}: {len(matches)} matches, {len(goals)} goals, {len(shootouts)} shootouts")


if __name__ == "__main__":
    main()
