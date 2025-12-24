"""
Chunk creation logic.

Chunking splits normalised content into stable units.
"""

from app.models import Chunk


def create_chunks(artefact_id: str, content: str) -> list[Chunk]:
    """
    Create chunks from content.

    This function does NOT:
    - infer meaning
    - merge sections
    - generate embeddings
    """
    raise NotImplementedError("Chunk creation not implemented")
