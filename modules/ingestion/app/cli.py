import argparse
import hashlib
import io
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

from .config import settings


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
    version_id = uuid.uuid4().hex
    version_label = "A"
    artefact_id = uuid.uuid4().hex

    client = _minio_client()
    _ensure_bucket(client, settings.minio_bucket)

    checksum = _compute_checksum(path)
    filename = path.name
    raw_key = _object_path("raw", document_id, version_id, filename)
    artefact_key = _object_path("artefacts", document_id, version_id, "extracted_text.txt")

    with path.open("rb") as f:
        client.put_object(
            settings.minio_bucket,
            raw_key,
            data=f,
            length=path.stat().st_size,
            content_type="text/plain",
        )

    text_bytes = path.read_bytes()
    client.put_object(
        settings.minio_bucket,
        artefact_key,
        data=io.BytesIO(text_bytes),
        length=len(text_bytes),
        content_type="text/plain",
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

    artefact = md_models.Artefact(
        artefact_id=artefact_id,
        version_id=version_id,
        artefact_type="EXTRACTED_TEXT",
        storage_path=f"s3://{settings.minio_bucket}/{artefact_key}",
        tool_name="ingestion_txt",
        tool_version="0.1",
        confidence_level="DECLARED",
    )
    ArtefactRepository.insert(artefact)

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
