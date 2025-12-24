"""
Ingestion pipeline contract.

This file defines the ingestion flow WITHOUT implementing extraction.
"""

from app.models import IngestionJob


def run_ingestion(job: IngestionJob):
    """
    Execute an ingestion job.

    Steps (contractual):
    1. Validate document + version exist
    2. Read source file from storage
    3. Produce derived artefacts
    4. Register artefacts with metadata

    No other steps are permitted at this stage.
    """
    raise NotImplementedError("Ingestion pipeline not implemented")
