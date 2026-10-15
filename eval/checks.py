"""Automatic answer checking for the evaluation (no LLM judge: deterministic and free).

- SQL questions: the gold SQL query is run on the database; every value of its first row
  (numbers and names) must appear in the agent's answer.
- RAG questions: each keyword group must be matched by at least one of its alternatives.
"""
import re
import sqlite3
import unicodedata
from pathlib import Path


def normalize(text: str) -> str:
    """lowercase, no accents, only letters/digits/spaces: "Samuel Eto'o" -> "samuel etoo"."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]", "", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def numbers_in(text: str) -> list[float]:
    text = re.sub(r"(?<=\d)[,   ](?=\d{3}\b)", "", text)  # 1,105 / 1 105 -> 1105
    return [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]


def value_in_answer(value, answer: str) -> bool:
    if isinstance(value, (int, float)) or (isinstance(value, str) and re.fullmatch(r"\d+(\.\d+)?", value)):
        target = float(value)
        tolerance = 0.5 if target != int(target) else 0  # 22.7 accepts 23 / 22.7, integers must be exact
        return any(abs(n - target) <= tolerance for n in numbers_in(answer))
    return normalize(str(value)) in normalize(answer)


def gold_values(gold_sql: str, db_path: Path) -> list:
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
        row = conn.execute(gold_sql).fetchone()
    return list(row)


def check_sql(answer: str, gold: list) -> bool:
    return all(value_in_answer(v, answer) for v in gold)


def check_keywords(answer: str, keyword_groups: list[list[str]]) -> bool:
    norm = normalize(answer)
    return all(any(normalize(k) in norm for k in group) for group in keyword_groups)
