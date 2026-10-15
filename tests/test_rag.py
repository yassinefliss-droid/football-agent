from qdrant_client import QdrantClient

from app.rag import Chunk, KnowledgeBase, chunk_text, format_results, load_documents


def test_chunk_text_respects_size_and_overlap():
    text = "\n".join(f"Paragraph {i} " + "word " * 40 for i in range(20))
    chunks = chunk_text(text, max_chars=500, overlap=100)
    assert len(chunks) > 1
    assert all(len(c) <= 500 + 100 + 1 for c in chunks)
    assert chunks[0][-50:] in chunks[1]  # overlap: end of chunk 0 repeated in chunk 1


def test_load_documents(tmp_path):
    (tmp_path / "a.md").write_text("# Maracanazo\nSource: https://example.org/m\nUruguay beat Brazil in 1950.")
    chunks = list(load_documents(tmp_path))
    assert chunks[0].title == "Maracanazo" and chunks[0].url == "https://example.org/m"
    assert chunks[0].text.startswith("Maracanazo\n")


def _kb(fake_embedders):
    dense, sparse = fake_embedders
    kb = KnowledgeBase(QdrantClient(":memory:"), "test", dense, sparse)
    kb.build([
        Chunk("uruguay beat brazil at the maracana in 1950", "Maracanazo", "u1", 0),
        Chunk("maradona scored with his hand against england in 1986", "Hand of God goal", "u2", 0),
        Chunk("video assistant referee was used at the 2018 world cup", "Video assistant referee", "u3", 0),
    ])
    return kb


def test_hybrid_search_finds_relevant_chunk(fake_embedders):
    kb = _kb(fake_embedders)
    for mode in ["hybrid", "dense", "sparse"]:
        assert kb.search("maradona hand england", k=1, mode=mode)[0]["title"] == "Hand of God goal"


def test_format_results_cites_sources(fake_embedders):
    out = format_results(_kb(fake_embedders).search("uruguay brazil 1950", k=2))
    assert out.startswith("[1] Maracanazo (u1)")
