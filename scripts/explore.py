"""First look at the database with plain SQL.

Writing these queries yourself matters: in step 2 the LLM will write queries
like these, and you need to know what a correct answer looks like.
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "football.db"

QUERIES = {
    "Date range and number of matches": """
        SELECT MIN(date) AS first_match, MAX(date) AS last_match, COUNT(*) AS n_matches
        FROM matches""",

    "Most common tournaments": """
        SELECT tournament, COUNT(*) AS n_matches
        FROM matches GROUP BY tournament ORDER BY n_matches DESC LIMIT 5""",

    "Tunisia: wins, draws, losses": """
        SELECT
            SUM(winner = 'Tunisia') AS wins,
            SUM(winner = 'Draw')    AS draws,
            SUM(winner NOT IN ('Tunisia', 'Draw')) AS losses
        FROM matches
        WHERE home_team = 'Tunisia' OR away_team = 'Tunisia'""",

    "Top 5 scorers in FIFA World Cup matches": """
        SELECT g.scorer, g.team, COUNT(*) AS goals
        FROM goals g JOIN matches m ON m.match_id = g.match_id
        WHERE m.tournament = 'FIFA World Cup' AND g.own_goal = 0
        GROUP BY g.scorer, g.team ORDER BY goals DESC LIMIT 5""",

    "Home advantage (non-neutral matches only)": """
        SELECT
            ROUND(100.0 * AVG(winner = home_team), 1) AS home_win_pct,
            ROUND(100.0 * AVG(winner = 'Draw'), 1)    AS draw_pct,
            ROUND(100.0 * AVG(winner = away_team), 1) AS away_win_pct
        FROM matches WHERE neutral = 0""",
}


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        for title, sql in QUERIES.items():
            print(f"\n=== {title} ===")
            print(pd.read_sql(sql, conn).to_string(index=False))


if __name__ == "__main__":
    main()
