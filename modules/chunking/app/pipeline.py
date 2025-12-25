"""
Chunking pipeline.

Consumes EXTRACTED_TEXT artefacts and produces TEXT chunks.
"""

import argparse
import sys
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

from minio import Minio

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.metadata.app.repository import (  # type: ignore
    ArtefactRepository,
    ChunkRepository,
)

from .chunker import create_chunks
from .config import settings


def _minio_client() -> Minio:
    parsed = urlparse(settings.minio_endpoint)
    endpoint = parsed.netloc or parsed.path
    secure = parsed.scheme == "https"
    return Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )


def _load_artefact_content(storage_path: str) -> str:
    parsed = urlparse(storage_path)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")

    client = _minio_client()
    response = client.get_object(bucket, key)
    try:
        data = response.read()
    finally:
        response.close()
        response.release_conn()
    return data.decode("utf-8")


def chunk_extracted_text(artefact_id: str) -> Tuple[int, list[str]]:
    artefact = ArtefactRepository.get(artefact_id)
    if not artefact:
        raise ValueError(f"Artefact not found: {artefact_id}")
    if artefact["artefact_type"] != "EXTRACTED_TEXT":
        raise ValueError("chunk_extracted_text only supports EXTRACTED_TEXT artefacts")

    content = _load_artefact_content(artefact["storage_path"])
    chunks = create_chunks(artefact_id, content)

    inserted_ids = []
    for ch in chunks:
        ChunkRepository.insert(ch)
        inserted_ids.append(ch.chunk_id)

    return len(chunks), inserted_ids


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chunk an EXTRACTED_TEXT artefact")
    parser.add_argument("--artefact-id", required=True)
    args = parser.parse_args(argv)

    count, ids = chunk_extracted_text(args.artefact_id)
    print(f"Chunks created: {count}")
    if ids:
        print(f"First chunk_id: {ids[0]}")


if __name__ == "__main__":
    main()
