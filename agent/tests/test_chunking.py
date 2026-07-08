"""Unit tests for RAG chunking and tipo detection (no external deps)."""

from app.rag.chunking import chunk_text, clean_text, detect_tipo


def test_clean_text_collapses_whitespace_and_drops_nulls():
    raw = "a\x00b   c\t\t d\n\n\n\n\n e"
    assert clean_text(raw) == "a b c d\n\n e"


def test_chunk_text_respects_min_length_and_overlap():
    text = ("line one\n" * 400).strip()
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=40, min_len=20)
    assert len(chunks) >= 2
    assert all(len(c) > 20 for c in chunks)
    # Overlap means the last char of chunk[i] should reappear near the start of chunk[i+1]
    # — assert at least one token carries over.
    assert chunks[0][-10:].strip() in chunks[1] or chunks[1][:10].strip() in chunks[0]


def test_chunk_text_short_text_returns_single_chunk():
    # default min_len=50 would drop a tiny string; lower it explicitly.
    assert chunk_text("hello world", min_len=1) == ["hello world"]
    assert chunk_text("hello world") == []  # below default min_len=50


def test_detect_tipo_finops_categories():
    assert detect_tipo("pricing-huawei-ecs-2025.pdf") == "pricing"
    assert detect_tipo("well-architected-cost-optimization.pdf") == "well_architected"
    assert detect_tipo("finops-playbook-rightsizing.md") == "playbook"
    assert detect_tipo("tagging-policy.md") == "policy"
    assert detect_tipo("case-study-storage-tiering.pdf") == "case_study"
    assert detect_tipo("best-practices-reserved-instances.md") == "best_practice"
    assert detect_tipo("random-notes.txt") == "reference"
