from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str


class MetadataResponse(BaseModel):
    document_id: str
    title: str
    document_type: str
    authority_level: str
    status: str


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class RetrievalRequest(BaseModel):
    query: str
    include_references: bool = True


class AnalysisRequest(BaseModel):
    analysis_type: str
    parameters: dict
