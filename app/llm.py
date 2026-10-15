"""Return the chat model chosen in the configuration.

- ollama: runs locally, free, private (development).
- groq:   hosted API with a free tier, fast (cloud deployment, CI evaluation).
Both expose the same LangChain interface, so the agent code does not change.
"""
from langchain_core.language_models import BaseChatModel

from app.config import settings


def get_llm() -> BaseChatModel:
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq  # needs GROQ_API_KEY in the environment

        return ChatGroq(model=settings.groq_model, temperature=0)

    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url, temperature=0)

    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r} (use 'ollama' or 'groq')")
