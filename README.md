# ⚽ Football Analyst Agent

An LLM agent that answers questions about 150 years of international football
(1872 → today) by writing SQL, running a match-prediction model and drawing charts.
It runs 100% locally with Ollama.

> 🚧 Work in progress. Step 1 (data pipeline) is done.

## Dataset
[International football results](https://github.com/martj42/international_results) (martj42, also on Kaggle):
~49,500 matches, ~48,000 goals and ~680 penalty shootouts.

## Database schema (`data/football.db`)
| Table | Key columns |
|---|---|
| `matches` | match_id, date, home_team, away_team, home_score, away_score, tournament, city, country, neutral, **winner** (team or 'Draw') |
| `goals` | match_id → matches, team, scorer, minute, own_goal, penalty |
| `shootouts` | match_id → matches, winner, first_shooter |
| `former_names` | current, former, start_date, end_date |

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python scripts/download_data.py    # download the CSV files
python scripts/build_db.py         # build data/football.db
python scripts/explore.py          # sanity-check queries
```

## Roadmap
- [x] Step 1: data pipeline (download → clean → SQLite)
- [ ] Step 2: text-to-SQL agent with LangChain + Ollama
- [ ] Step 3: match-prediction model and plotting tool
- [ ] Step 4: Streamlit interface, evaluation set, demo
