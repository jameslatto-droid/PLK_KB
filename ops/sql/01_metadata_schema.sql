-- PLK_KB Database Schema
-- Stage 2 – Metadata & Governance Control Plane
-- PostgreSQL 16+

-- 3.1 documents
-- Logical document identity
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    document_type TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    owner TEXT,
    project_code TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3.2 document_versions
-- Explicit version identity and lineage for each document
CREATE TABLE IF NOT EXISTS document_versions (
    version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    version_label TEXT NOT NULL,
    source_path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    supersedes TEXT REFERENCES document_versions(version_id)
);

-- 3.3 artefacts
-- Derived outputs produced from document versions
CREATE TABLE IF NOT EXISTS artefacts (
    artefact_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    artefact_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tool_name TEXT,
    tool_version TEXT,
    confidence_level TEXT
);

-- 3.4 chunks
-- Stable, retrievable segments derived from artefacts
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    artefact_id TEXT NOT NULL REFERENCES artefacts(artefact_id),
    chunk_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB
);

-- 3.5 access_rules
-- Access filters applied to documents and derived content
CREATE TABLE IF NOT EXISTS access_rules (
    rule_id BIGSERIAL PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    project_code TEXT,
    discipline TEXT,
    classification TEXT,
    commercial_sensitivity TEXT,
    allowed_roles TEXT[],
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3.6 audit_log
-- Traceability records for user actions and model responses
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    document_id TEXT REFERENCES documents(document_id),
    version_id TEXT REFERENCES document_versions(version_id),
    model_version TEXT,
    index_version TEXT,
    details JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
