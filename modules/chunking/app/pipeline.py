"""
Chunking pipeline.

Consumes extracted artefacts and produces chunks.
"""

from app.models import SourceArtefact


def run_chunking(artefact: SourceArtefact):
    """
    Steps:
    1. Normalise content
    2. Apply chunking rules
    3. Produce chunk artefacts
    4. Register chunks with metadata

    No other behaviour is permitted.
    """
    raise NotImplementedError("Chunking pipeline not implemented")
