"""Text cleaning and overlap chunking — ported from the uade-rag pattern.

Kept intentionally dependency-free so it can be unit-tested in isolation and
reused by the ingest pipeline.
"""

from __future__ import annotations

import re

CHUNK_SIZE = 1200  # characters per chunk
CHUNK_OVERLAP = 200  # overlap between consecutive chunks
MIN_CHUNK_LEN = 50  # discard fragments shorter than this


def clean_text(text: str) -> str:
    """Normalise whitespace and strip control characters."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
    min_len: int = MIN_CHUNK_LEN,
) -> list[str]:
    """Split text into overlapping chunks, breaking on line boundaries.

    Walks a sliding window of ``chunk_size`` characters with ``chunk_overlap``
    overlap. When the window end falls mid-line, it snaps back to the nearest
    newline in the second half of the window so chunks don't split sentences
    awkwardly. Fragments shorter than ``min_len`` are dropped.
    """
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = start + chunk_size
        if end < n:
            newline = text.rfind("\n", start + chunk_size // 2, end)
            if newline != -1:
                end = newline
        chunk = text[start:end].strip()
        if len(chunk) > min_len:
            chunks.append(chunk)
        start = end - chunk_overlap if end < n else n
    return chunks


def detect_tipo(filename: str) -> str:
    """Classify a knowledge-base document by its filename.

    FinOps categories: ``pricing``, ``best_practice``, ``well_architected``,
    ``playbook``, ``policy``, ``case_study``, ``reference``.
    """
    low = filename.lower()
    if "precio" in low or "pricing" in low or "tarifa" in low or "rate" in low:
        return "pricing"
    if "well-architected" in low or "well_architected" in low or "waf" in low:
        return "well_architected"
    if "playbook" in low or "runbook" in low or "guia" in low or "guide" in low:
        return "playbook"
    if "policy" in low or "politica" in low or "tagging" in low or "etiquetad" in low:
        return "policy"
    if "case" in low or "caso" in low or "estudio" in low:
        return "case_study"
    if "best" in low or "mejor" in low or "practica" in low:
        return "best_practice"
    return "reference"
