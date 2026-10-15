from fastapi.testclient import TestClient

import app.api as api

client = TestClient(api.app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_ask(monkeypatch):
    fake = {"answer": "Tunisia won 296 matches.", "latency_s": 1.2,
            "tool_calls": [{"tool": "query_database", "args": {"sql": "SELECT 1"}, "output": "1"}]}
    monkeypatch.setattr(api, "ask", lambda q: fake)
    response = client.post("/ask", json={"question": "How many matches has Tunisia won?"})
    assert response.status_code == 200 and response.json() == fake


def test_ask_rejects_empty_question():
    assert client.post("/ask", json={"question": ""}).status_code == 422
