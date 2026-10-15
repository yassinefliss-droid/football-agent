"""Retrieval-Augmented Generation: chunking, indexing and hybrid search with Qdrant.

Hybrid search = two retrievers combined:
- dense  (bge-small embeddings): finds passages with the same *meaning* ("final match lost at home")
- sparse (BM25):                 finds passages with the same *words* (names, years: "Maracanazo", "1950")
Their rankings are merged with Reciprocal Rank Fusion (RRF), which needs no score calibration.

Qdrant runs in "local mode" (a folder on disk, no server), which is enough for ~1k chunks.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

from qdrant_client import QdrantClient, models

DENSE, SPARSE = "dense", "bm25"


# ---------- Embedders (interfaces, so tests can plug in fake ones) ----------
class DenseEmbedder(Protocol):
    dim: int
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class SparseEmbedder(Protocol):
    def embed_documents(self, texts: list[str]) -> list[models.SparseVector]: ...
    def embed_query(self, text: str) -> models.SparseVector: ...


class FastEmbedDense:
    def __init__(self, model_name: str):
        from fastembed import TextEmbedding
        self.model = TextEmbedding(model_name)
        self.dim = len(next(iter(self.model.embed(["probe"]))))

    def embed_documents(self, texts):
        return [v.tolist() for v in self.model.embed(texts)]

    def embed_query(self, text):
        return next(iter(self.model.query_embed(text))).tolist()


class FastEmbedSparse:
    def __init__(self, model_name: str):
        from fastembed import SparseTextEmbedding
        self.model = SparseTextEmbedding(model_name)

    @staticmethod
    def _to_qdrant(e) -> models.SparseVector:
        return models.SparseVector(indices=e.indices.tolist(), values=e.values.tolist())

    def embed_documents(self, texts):
        return [self._to_qdrant(e) for e in self.model.embed(texts)]

    def embed_query(self, text):
        return self._to_qdrant(next(iter(self.model.query_embed(text))))


# ---------- Chunking ----------
@dataclass
class Chunk:
    text: str
    title: str
    url: str
    chunk_id: int


def chunk_text(text: str, max_chars: int = 1000, overlap: int = 200) -> list[str]:
    """Split on paragraphs, then pack paragraphs into chunks of ~max_chars.

    Paragraph boundaries keep sentences intact; the overlap repeats the end of the
    previous chunk so a fact split across two chunks is still retrievable.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        while len(para) > max_chars:  # very long paragraph: hard split
            chunks.append(para[:max_chars])
            para = para[max_chars - overlap:]
        if len(current) + len(para) + 1 > max_chars and current:
            chunks.append(current)
            current = current[-overlap:] + "\n" + para
        else:
            current = f"{current}\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks


def load_documents(docs_dir: Path) -> Iterable[Chunk]:
    """Each .md file: first line '# Title', second line 'Source: url', then the text."""
    for path in sorted(docs_dir.glob("*.md")):
        lines = path.read_text(encoding="utf-8").split("\n")
        title = lines[0].lstrip("# ").strip()
        url = lines[1].removeprefix("Source:").strip()
        for i, text in enumerate(chunk_text("\n".join(lines[2:]))):
            # Prefix the title so every chunk keeps its context ("2010 FIFA World Cup: ...")
            yield Chunk(text=f"{title}\n{text}", title=title, url=url, chunk_id=i)


# ---------- Index + search ----------
class KnowledgeBase:
    def __init__(self, client: QdrantClient, collection: str, dense: DenseEmbedder, sparse: SparseEmbedder):
        self.client, self.collection, self.dense, self.sparse = client, collection, dense, sparse

    def build(self, chunks: list[Chunk], batch_size: int = 64) -> None:
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config={DENSE: models.VectorParams(size=self.dense.dim, distance=models.Distance.COSINE)},
            sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            texts = [c.text for c in batch]
            dense_vecs = self.dense.embed_documents(texts)
            sparse_vecs = self.sparse.embed_documents(texts)
            self.client.upsert(self.collection, points=[
                models.PointStruct(
                    id=start + i,
                    vector={DENSE: d, SPARSE: s},
                    payload={"text": c.text, "title": c.title, "url": c.url, "chunk_id": c.chunk_id},
                )
                for i, (c, d, s) in enumerate(zip(batch, dense_vecs, sparse_vecs))
            ])

    def search(self, query: str, k: int = 5, mode: str = "hybrid") -> list[dict]:
        """mode: 'hybrid' (default), 'dense' or 'sparse'. The last two exist for the evaluation."""
        dense_q = models.Prefetch(query=self.dense.embed_query(query), using=DENSE, limit=k * 4)
        sparse_q = models.Prefetch(query=self.sparse.embed_query(query), using=SPARSE, limit=k * 4)
        if mode == "hybrid":
            result = self.client.query_points(
                self.collection, prefetch=[dense_q, sparse_q],
                query=models.FusionQuery(fusion=models.Fusion.RRF), limit=k, with_payload=True,
            )
        else:
            q = dense_q if mode == "dense" else sparse_q
            result = self.client.query_points(self.collection, query=q.query, using=q.using, limit=k, with_payload=True)
        return [p.payload | {"score": p.score} for p in result.points]


def format_results(results: list[dict]) -> str:
    """Numbered passages with their source, so the LLM can cite them."""
    if not results:
        return "No relevant passage found."
    return "\n\n".join(f"[{i}] {r['title']} ({r['url']})\n{r['text']}" for i, r in enumerate(results, 1))
