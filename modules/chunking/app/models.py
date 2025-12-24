from pydantic import BaseModel
from typing import Optional, Dict


class SourceArtefact(BaseModel):
    artefact_id: str
    artefact_type: str
    content: str
    metadata: Optional[Dict] = None


class Chunk(BaseModel):
    chunk_id: str
    artefact_id: str
    chunk_type: str
    content: str
    metadata: Optional[Dict] = None
