from pydantic import BaseModel
from typing import Optional, Dict, List


class ChunkRecord(BaseModel):
    chunk_id: str
    artefact_id: str
    chunk_type: str
    content: str
    metadata: Optional[Dict] = None


class IndexBuildRequest(BaseModel):
    index_name: str
    chunks: List[ChunkRecord]
    index_version: str


class IndexVersionRecord(BaseModel):
    index_version: str
    created_at: Optional[str] = None
    notes: Optional[str] = None
