"""Build the data on first start when it is missing.

The database and the vector index are not stored in Git (they are generated files).
On a fresh server (e.g. Streamlit Community Cloud) this runs the pipeline once:
download CSVs -> SQLite -> Wikipedia articles -> Qdrant index (a few minutes).
"""
import subprocess
import sys
from pathlib import Path

from app.config import settings

ROOT = Path(__file__).resolve().parent.parent
STEPS = ["download_data.py", "build_db.py", "build_wiki_corpus.py", "build_index.py"]


def data_is_ready() -> bool:
    return settings.db_path.exists() and settings.qdrant_path.exists() and any(settings.qdrant_path.iterdir())


def ensure_data() -> None:
    if data_is_ready():
        return
    for script in STEPS:
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True, cwd=ROOT)
