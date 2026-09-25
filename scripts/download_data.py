"""Download the International Football Results dataset (martj42) into data/raw/.

Source: https://github.com/martj42/international_results
(same data as the Kaggle dataset "International football results from 1872 to ...")
"""
from pathlib import Path

import requests

BASE_URL = "https://raw.githubusercontent.com/martj42/international_results/master"
FILES = ["results.csv", "goalscorers.csv", "shootouts.csv", "former_names.csv"]
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        response = requests.get(f"{BASE_URL}/{name}", timeout=30)
        response.raise_for_status()  # stop with a clear error if the download fails
        (RAW_DIR / name).write_bytes(response.content)
        print(f"Downloaded {name} ({len(response.content) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
