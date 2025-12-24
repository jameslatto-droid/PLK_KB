from pydantic import BaseModel
from typing import Optional


class IngestionJob(BaseModel):
    document_id: str
    version_id: str
    source_path: str


class ArtefactRecord(BaseModel):
    artefact_id: str
    version_id: str
    artefact_type: str
    storage_path: str
    tool_name: str
    tool_version: str
    confidence_level: str
