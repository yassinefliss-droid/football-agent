"""Central configuration, read from environment variables (and a local .env file).

Keeping every setting here means the same code runs locally (Ollama) and in the
cloud (Groq API) by changing only environment variables, never the code.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    # LLM
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "groq"
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Data
    db_path: Path = Path(os.getenv("DB_PATH", ROOT / "data" / "football.db"))
    docs_dir: Path = Path(os.getenv("DOCS_DIR", ROOT / "data" / "docs"))
    qdrant_path: Path = Path(os.getenv("QDRANT_PATH", ROOT / "data" / "qdrant"))
    collection: str = os.getenv("QDRANT_COLLECTION", "football_knowledge")

    # Retrieval
    dense_model: str = os.getenv("DENSE_MODEL", "BAAI/bge-small-en-v1.5")
    sparse_model: str = os.getenv("SPARSE_MODEL", "Qdrant/bm25")
    top_k: int = int(os.getenv("TOP_K", "5"))


settings = Settings()
