"""
Chunk creation logic.

Produces deterministic, fixed-size chunks.
"""

import hashlib
from typing import List

from .models import Chunk
from .config import settings


def _stable_chunk_id(artefact_id: str, chunk_index: int, content: str) -> str:
    raw = f"{artefact_id}:{chunk_index}:{content}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def create_chunks(artefact_id: str, content: str) -> List[Chunk]:
    """Split content into fixed-size chunks (no overlap) and assign stable IDs."""
    max_chars = settings.max_chunk_chars
    chunks: List[Chunk] = []

    start = 0
    chunk_index = 0
    text_len = len(content)
    while start < text_len:
        end = min(start + max_chars, text_len)
        chunk_text = content[start:end]
        chunk_id = _stable_chunk_id(artefact_id, chunk_index, chunk_text)
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                artefact_id=artefact_id,
                chunk_type="TEXT",
                content=chunk_text,
                metadata={
                    "chunk_index": chunk_index,
                    "char_start": start,
                    "char_end": end,
                },
            )
        )
        chunk_index += 1
        start = end

    return chunks
