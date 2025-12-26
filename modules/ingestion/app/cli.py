import argparse
import hashlib
import io
import json
import logging
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

from minio import Minio

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.metadata.app import models as md_models  # type: ignore
from modules.metadata.app.repository import (  # type: ignore
    DocumentRepository,
    DocumentVersionRepository,
    ArtefactRepository,
)
from modules.authority.app.policy import validate_authority_level  # type: ignore
from modules.extraction.registry import extract_file  # Stage 8
from modules.extraction.allowlist import get_file_tier, get_tier_description  # Stage 8

from .config import settings

logger = logging.getLogger(__name__)


def _minio_client():
    parsed = urlparse(settings.minio_endpoint)
    endpoint = parsed.netloc or parsed.path
    secure = parsed.scheme == "https"
    return Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )


def _ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def _object_path(prefix: str, document_id: str, version_id: str, filename: str) -> str:
    return f"{prefix}/{document_id}/{version_id}/{filename}"


def _compute_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ingest_txt(document_id: str, title: str, path: Path, document_type: str, authority_level: str):
    """
    Ingest a file using Stage 8 extraction pipeline.
    
    Stage 8 Changes:
    - Uses extractor registry for file type handling
    - Supports tiered allowlist (Tier 1, 2, 3)
    - Stores extraction metadata
    - Fails explicitly on unsupported types
    """
    validate_authority_level(authority_level)
    version_id = uuid.uuid4().hex
    version_label = "A"
    artefact_id = uuid.uuid4().hex
    
    # Stage 8: Extract text using registry
    enable_tier_2 = settings.enable_tier_2
    tier = get_file_tier(path)
    extraction_result, extraction_reason = extract_file(path, enable_tier_2=enable_tier_2)
    
    # Log extraction status
    logger.info(
        "Extraction for %s: status=%s tier=%s reason=%s",
        path.name,
        extraction_result["status"],
        tier.value,
        extraction_reason,
    )
    
    if extraction_result["warnings"]:
        for warning in extraction_result["warnings"]:
            logger.warning("Extraction warning for %s: %s", path.name, warning)
    
    if extraction_result["errors"]:
        for error in extraction_result["errors"]:
            logger.error("Extraction error for %s: %s", path.name, error)
    
    # Determine if ingestion should proceed
    if extraction_result["status"] == "failed":
        # Print extraction details to stdout for UI capture
        print(json.dumps({
            "extraction_status": "failed",
            "tier": tier.value,
            "tier_description": get_tier_description(tier),
            "reason": extraction_reason,
            "errors": extraction_result["errors"],
        }))
        raise RuntimeError(f"Extraction failed for {path.name}: {extraction_reason}")
    
    # Extraction succeeded or partial - proceed with ingestion
    extracted_text = extraction_result.get("text", "")
    if not extracted_text:
        logger.warning("Extraction returned no text for %s", path.name)
        extracted_text = ""  # Empty text is acceptable

    client = _minio_client()
    _ensure_bucket(client, settings.minio_bucket)

    checksum = _compute_checksum(path)
    filename = path.name
    raw_key = _object_path("raw", document_id, version_id, filename)
    artefact_key = _object_path("artefacts", document_id, version_id, "extracted_text.txt")

    # Store raw file
    with path.open("rb") as f:
        client.put_object(
            settings.minio_bucket,
            raw_key,
            data=f,
            length=path.stat().st_size,
            content_type="text/plain",
        )

    # Store extracted text
    text_bytes = extracted_text.encode("utf-8")
    client.put_object(
        settings.minio_bucket,
        artefact_key,
        data=io.BytesIO(text_bytes),
        length=len(text_bytes),
        content_type="text/plain",
    )
    
    # Store extraction metadata
    extraction_metadata_key = _object_path("artefacts", document_id, version_id, "extraction_metadata.json")
    metadata_bytes = json.dumps(extraction_result, indent=2).encode("utf-8")
    client.put_object(
        settings.minio_bucket,
        extraction_metadata_key,
        data=io.BytesIO(metadata_bytes),
        length=len(metadata_bytes),
        content_type="application/json",
    )

    doc = md_models.Document(
        document_id=document_id,
        title=title,
        document_type=document_type,
        authority_level=authority_level,
    )
    DocumentRepository.insert(doc)

    version = md_models.DocumentVersion(
        version_id=version_id,
        document_id=document_id,
        version_label=version_label,
        source_path=str(path),
        checksum=checksum,
    )
    DocumentVersionRepository.insert(version)

    # Stage 8: Enhanced artefact metadata
    extractor_name = extraction_result.get("metadata", {}).get("extractor", "unknown")
    extractor_version = extraction_result.get("metadata", {}).get("version", "unknown")
    confidence_score = extraction_result.get("confidence")
    
    artefact = md_models.Artefact(
        artefact_id=artefact_id,
        version_id=version_id,
        artefact_type="EXTRACTED_TEXT",
        storage_path=f"s3://{settings.minio_bucket}/{artefact_key}",
        tool_name=f"extraction_{extractor_name}",
        tool_version=extractor_version,
        confidence_level=extraction_result["status"].upper(),  # SUCCESS, PARTIAL, FAILED
    )
    ArtefactRepository.insert(artefact)
    
    # Print success details to stdout for UI capture
    print(json.dumps({
        "document_id": document_id,
        "version_id": version_id,
        "artefact_id": artefact_id,
        "extraction_status": extraction_result["status"],
        "extraction_confidence": confidence_score,
        "extractor": extractor_name,
        "tier": tier.value,
        "warnings": extraction_result["warnings"],
    }))

    return version_id, artefact_id


def main(argv=None):
    parser = argparse.ArgumentParser(description="Ingest a plain text file")
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--document-type", required=True)
    parser.add_argument("--authority-level", required=True)
    args = parser.parse_args(argv)

    ingest_txt(
        document_id=args.document_id,
        title=args.title,
        path=Path(args.path).resolve(),
        document_type=args.document_type,
        authority_level=args.authority_level,
    )


if __name__ == "__main__":
    main()
