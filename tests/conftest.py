"""Shared test fixtures: a tiny football database and fake embedders.

Tests never call an LLM or download a model: they are fast, free and run in CI.
"""
import hashlib
import sqlite3

import pytest
from qdrant_client import models


@pytest.fixture
def tiny_db(tmp_path):
    db = tmp_path / "football.db"
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE matches (
            match_id INTEGER PRIMARY KEY, date TEXT, home_team TEXT, away_team TEXT,
            home_score INTEGER, away_score INTEGER, tournament TEXT, city TEXT,
            country TEXT, neutral INTEGER, winner TEXT -- team name, or 'Draw'
        )""")
        conn.executemany("INSERT INTO matches VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
            (1, "1978-06-02", "Tunisia", "Mexico", 3, 1, "FIFA World Cup", "Rosario", "Argentina", 1, "Tunisia"),
            (2, "2004-02-14", "Tunisia", "Morocco", 2, 1, "African Cup of Nations", "Radès", "Tunisia", 0, "Tunisia"),
            (3, "2022-11-30", "Tunisia", "France", 1, 0, "FIFA World Cup", "Al Rayyan", "Qatar", 1, "Tunisia"),
            (4, "2022-11-22", "Denmark", "Tunisia", 0, 0, "FIFA World Cup", "Al Rayyan", "Qatar", 1, "Draw"),
        ])
    return db


def _hash_tokens(text):
    return [int(hashlib.md5(w.encode()).hexdigest(), 16) % 1000 for w in text.lower().split()]


class FakeDense:
    """Bag-of-words vector of size 64: similar words -> similar vectors. Good enough for tests."""
    dim = 64

    def _vec(self, text):
        v = [0.0] * self.dim
        for h in _hash_tokens(text):
            v[h % self.dim] += 1.0
        return v

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


class FakeSparse:
    def _vec(self, text):
        counts = {}
        for h in _hash_tokens(text):
            counts[h] = counts.get(h, 0) + 1.0
        return models.SparseVector(indices=list(counts), values=list(counts.values()))

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


@pytest.fixture
def fake_embedders():
    return FakeDense(), FakeSparse()
