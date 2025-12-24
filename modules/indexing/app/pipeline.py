"""
Indexing pipeline contract.

Consumes chunks and writes derived index state.
No retrieval logic permitted.
No authority decisions permitted.
No embeddings generated in Stage 2.
"""

from app.models import IndexBuildRequest


def build_lexical_index(req: IndexBuildRequest):
    """
    Contract:
    - consume chunks
    - produce OpenSearch index entries
    - record index version
    """
    raise NotImplementedError("Lexical indexing not implemented (Stage 2)")


def build_vector_index(req: IndexBuildRequest):
    """
    Contract:
    - consume chunks
    - produce Qdrant vector entries
    - record index version

    Stage 2: does NOT generate embeddings. This is a stub.
    """
    raise NotImplementedError("Vector indexing not implemented (Stage 2)")
