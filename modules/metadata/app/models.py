from typing import Optional, Dict, List
from pydantic import BaseModel


class Document(BaseModel):
    document_id: str
    title: str
    document_type: str
    authority_level: str
    owner: Optional[str] = None
    project_code: Optional[str] = None
    status: str = "active"
    created_at: Optional[str] = None


class DocumentVersion(BaseModel):
    version_id: str
    document_id: str
    version_label: str
    source_path: str
    checksum: str
    created_at: Optional[str] = None
    supersedes: Optional[str] = None


class Artefact(BaseModel):
    artefact_id: str
    version_id: str
    artefact_type: str
    storage_path: str
    created_at: Optional[str] = None
    tool_name: Optional[str] = None
    tool_version: Optional[str] = None
    confidence_level: Optional[str] = None


class Chunk(BaseModel):
    chunk_id: str
    artefact_id: str
    chunk_type: str
    content: str
    metadata: Optional[Dict] = None


class AccessRule(BaseModel):
    rule_id: Optional[int] = None
    document_id: str
    project_code: Optional[str] = None
    discipline: Optional[str] = None
    classification: Optional[str] = None
    commercial_sensitivity: Optional[str] = None
    allowed_roles: Optional[List[str]] = None
    created_at: Optional[str] = None


class AuditLog(BaseModel):
    audit_id: Optional[int] = None
    actor: str
    action: str
    document_id: Optional[str] = None
    version_id: Optional[str] = None
    model_version: Optional[str] = None
    index_version: Optional[str] = None
    details: Optional[Dict] = None
    created_at: Optional[str] = None
