"""REST API around the agent: lets any other app (web, mobile, Slack bot...) use it.

Run:  uvicorn app.api:app --reload    then open http://localhost:8000/docs
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.agent import ask
from app.config import settings

app = FastAPI(title="Football Analyst Agent", version="1.0")


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500, examples=["How many matches has Tunisia won?"])


class ToolCall(BaseModel):
    tool: str
    args: dict
    output: str


class Answer(BaseModel):
    answer: str
    tool_calls: list[ToolCall]
    latency_s: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "llm_provider": settings.llm_provider}


@app.post("/ask", response_model=Answer)
def ask_endpoint(payload: Question) -> dict:
    # A plain `def` (not async): FastAPI runs it in a thread pool, so a slow LLM call
    # does not block other requests.
    return ask(payload.question)
