"""Download the RAG corpus: plain-text Wikipedia articles about international football.

Why Wikipedia: open licence (CC BY-SA, cite the source), rich historical context that the
statistics database does not contain (stories, controversies, rules, hosts...).
Output: one Markdown file per article in data/docs/ (line 1: title, line 2: source URL).
"""
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings  # noqa: E402

API = "https://en.wikipedia.org/w/api.php"
# Wikipedia asks API clients to identify themselves: put your own contact here.
HEADERS = {"User-Agent": "football-agent/1.0 (student project; contact: yassinefliss@gmail.com)"}

WORLD_CUPS = [f"{y} FIFA World Cup" for y in
              [1930, 1934, 1938, 1950, 1954, 1958, 1962, 1966, 1970, 1974, 1978, 1982,
               1986, 1990, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]]
OTHER = [
    "FIFA World Cup", "Africa Cup of Nations", "UEFA European Championship", "Copa América",
    "UEFA Euro 2004", "UEFA Euro 2016", "2004 African Cup of Nations", "Maracanazo",
    "Hand of God goal", "Video assistant referee", "Laws of the Game (association football)",
    "Penalty shoot-out (association football)", "Golden goal", "History of association football",
    "Tunisia national football team", "Morocco national football team", "Brazil national football team",
    "France national football team", "Argentina national football team", "Germany national football team",
]
SKIP_SECTIONS = re.compile(r"\n=+ (See also|References|External links|Notes|Further reading|Bibliography) =+\n.*", re.S)


def fetch_article(title: str) -> tuple[str, str] | None:
    params = {
        "action": "query", "prop": "extracts|info", "explaintext": 1, "inprop": "url",
        "titles": title, "redirects": 1, "format": "json", "formatversion": 2,
    }
    response = requests.get(API, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    page = response.json()["query"]["pages"][0]
    if page.get("missing") or not page.get("extract"):
        return None
    text = SKIP_SECTIONS.sub("", page["extract"])  # drop reference lists: noise for retrieval
    text = re.sub(r"\n=+ (.+?) =+\n", r"\n\1\n", text)  # "== History ==" -> "History"
    return text, page["fullurl"]


def main() -> None:
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    for title in WORLD_CUPS + OTHER:
        article = fetch_article(title)
        if article is None:
            print(f"  skipped (not found): {title}")
            continue
        text, url = article
        filename = re.sub(r"[^\w]+", "_", title).strip("_") + ".md"
        (settings.docs_dir / filename).write_text(f"# {title}\nSource: {url}\n{text}", encoding="utf-8")
        print(f"Saved {title} ({len(text) // 1000}k chars)")
        time.sleep(0.5)  # be polite with the API


if __name__ == "__main__":
    main()
