"""Chunk the Wikipedia articles, embed them (dense + BM25) and store them in Qdrant.

The first run downloads the embedding models (~150 MB) from Hugging Face.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from qdrant_client import QdrantClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.rag import FastEmbedDense, FastEmbedSparse, KnowledgeBase, load_documents  # noqa: E402


def main() -> None:
    chunks = list(load_documents(settings.docs_dir))
    if not chunks:
        sys.exit("No documents found: run scripts/build_wiki_corpus.py first.")
    print(f"{len(chunks)} chunks from {len({c.title for c in chunks})} articles")

    start = time.perf_counter()
    kb = KnowledgeBase(
        QdrantClient(path=str(settings.qdrant_path)), settings.collection,
        FastEmbedDense(settings.dense_model), FastEmbedSparse(settings.sparse_model),
    )
    kb.build(chunks)
    print(f"Indexed in {time.perf_counter() - start:.0f} s -> {settings.qdrant_path}")

    print("\nSanity check: 'What was the Maracanazo?'")
    for r in kb.search("What was the Maracanazo?", k=3):
        print(f"  {r['score']:.3f}  {r['title']}  #{r['chunk_id']}")


if __name__ == "__main__":
    main()
