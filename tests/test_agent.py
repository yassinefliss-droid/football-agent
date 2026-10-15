"""Test the agent wiring with a scripted fake LLM (no real model needed)."""
from dataclasses import replace

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

import app.agent as agent_module


class ScriptedLLM(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def test_agent_calls_sql_tool_and_answers(tiny_db, monkeypatch):
    script = iter([
        AIMessage(content="", tool_calls=[{"name": "query_database", "id": "c1",
                                           "args": {"sql": "SELECT COUNT(*) FROM matches WHERE winner = 'Tunisia'"}}]),
        AIMessage(content="Tunisia won 3 matches."),
    ])
    monkeypatch.setattr(agent_module, "settings", replace(agent_module.settings, db_path=tiny_db))
    monkeypatch.setattr(agent_module, "get_llm", lambda: ScriptedLLM(messages=script))
    agent_module.get_agent.cache_clear()

    result = agent_module.ask("How many matches did Tunisia win?")

    assert result["answer"] == "Tunisia won 3 matches."
    assert result["tool_calls"][0]["tool"] == "query_database"
    assert result["tool_calls"][0]["output"].splitlines()[-1] == "3"
    agent_module.get_agent.cache_clear()
