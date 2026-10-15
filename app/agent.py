"""The football analyst agent: an LLM that decides which tool to call.

Agent loop (ReAct pattern, implemented by LangChain's create_agent / LangGraph):
  question -> LLM thinks -> calls a tool -> reads the result -> calls another tool or answers.
Two tools:
  - query_database:           exact statistics via SQL (scores, counts, top scorers...)
  - search_football_knowledge: history and context via RAG over Wikipedia articles
"""
import time
from functools import lru_cache

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from app.config import settings
from app.llm import get_llm
from app.sql_tool import get_schema, run_query


@lru_cache
def get_knowledge_base():
    """Loaded once (embedding models take a few seconds to load)."""
    from qdrant_client import QdrantClient

    from app.rag import FastEmbedDense, FastEmbedSparse, KnowledgeBase

    return KnowledgeBase(
        QdrantClient(path=str(settings.qdrant_path)), settings.collection,
        FastEmbedDense(settings.dense_model), FastEmbedSparse(settings.sparse_model),
    )


@tool
def query_database(sql: str) -> str:
    """Run ONE read-only SQLite SELECT query on the international football database
    (matches since 1872, goals, penalty shootouts) and return the rows.
    Use it for any number: results, scores, counts, rankings, top scorers, head-to-head records."""
    return run_query(sql, settings.db_path)


@tool
def search_football_knowledge(query: str) -> str:
    """Search Wikipedia articles about football history (World Cups, Euros, Africa Cup of Nations,
    famous matches, rules, VAR, national teams). Use it for context, stories, explanations and
    anything that is not a statistic. Returns numbered passages with their source."""
    from app.rag import format_results

    return format_results(get_knowledge_base().search(query, k=settings.top_k))


SYSTEM_PROMPT = """You are a football analyst assistant for international (national team) football.

Tools:
- query_database: for statistics and facts that can be counted. Write SQLite SQL for the schema below.
- search_football_knowledge: for history, context, explanations and rules.
You may call both tools for one question (e.g. a statistic plus its context).

Rules:
- Never invent a number: every statistic must come from query_database.
- If a query returns an ERROR or no rows, read the message, fix the query and retry (at most 3 times).
- Team names are in English as in the data (e.g. 'Tunisia', 'United States', 'Ivory Coast').
  A team plays either at home or away: filter with (home_team = X OR away_team = X).
- Tournament names: 'FIFA World Cup', 'African Cup of Nations', 'UEFA Euro', 'Copa América', 'Friendly'...
  Use LIKE '%World Cup%' carefully: it also matches 'FIFA World Cup qualification'.
- The year of a match is substr(date, 1, 4).
- When you use search_football_knowledge, cite the sources as [title].
- Answer concisely, in the language of the question.

Database schema:
{schema}
"""


@lru_cache
def get_agent():
    prompt = SYSTEM_PROMPT.format(schema=get_schema(settings.db_path))
    return create_agent(get_llm(), tools=[query_database, search_football_knowledge], system_prompt=prompt)


def ask(question: str) -> dict:
    """Run the agent and return the answer plus a trace of the tool calls (for the UI and the evaluation)."""
    start = time.perf_counter()
    result = get_agent().invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"recursion_limit": 15},  # hard stop: an agent must never loop forever
    )
    messages = result["messages"]

    tool_calls = []
    outputs = {m.tool_call_id: m.content for m in messages if isinstance(m, ToolMessage)}
    for m in messages:
        if isinstance(m, AIMessage):
            for call in m.tool_calls:
                tool_calls.append({"tool": call["name"], "args": call["args"], "output": outputs.get(call["id"], "")})

    return {
        "answer": messages[-1].content,
        "tool_calls": tool_calls,
        "latency_s": round(time.perf_counter() - start, 2),
    }
