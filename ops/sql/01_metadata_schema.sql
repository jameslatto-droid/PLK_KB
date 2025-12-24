-- PLK_KB Database Schema
-- Stage 2 – Metadata & Governance Control Plane
-- PostgreSQL 16+

-- 3.1 documents
-- Logical document identity
CREATE TABLE documents (
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
-- Explicit document versions
CREATE TABLE document_versions (
    version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    version_label TEXT NOT NULL,
    source_path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    supersedes TEXT REFERENCES document_versions(version_id)
);

-- 3.3 artefacts
-- Derived artefacts produced by pipelines
CREATE TABLE artefacts (
    artefact_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    artefact_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    confidence_level TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3.4 chunks
-- Retrievable knowledge units
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    artefact_id TEXT NOT NULL REFERENCES artefacts(artefact_id),
    chunk_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3.5 access_rules
-- Access control metadata
CREATE TABLE access_rules (
    rule_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    project TEXT,
    discipline TEXT,
    commercial TEXT,
    sensitivity TEXT
);

-- 3.6 audit_log
-- Mandatory traceability for retrieval and reasoning
CREATE TABLE audit_log (
    audit_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    document_ids TEXT[],
    version_ids TEXT[],
    model_version TEXT,
    index_version TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX idx_documents_authority ON documents(authority_level);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_document_versions_document_id ON document_versions(document_id);
CREATE INDEX idx_artefacts_version_id ON artefacts(version_id);
CREATE INDEX idx_artefacts_type ON artefacts(artefact_type);
CREATE INDEX idx_chunks_artefact_id ON chunks(artefact_id);
CREATE INDEX idx_access_rules_document_id ON access_rules(document_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
