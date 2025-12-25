"""OpenSearch client utilities for lexical index."""

from typing import List

from opensearchpy import OpenSearch, helpers, exceptions

from .config import settings


CHUNK_INDEX_BODY = {
    "settings": {
        "analysis": {
            "analyzer": {
                "plk_text": {
                    "type": "standard",
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "chunk_id": {"type": "keyword"},
            "artefact_id": {"type": "keyword"},
            "document_id": {"type": "keyword"},
            "content": {"type": "text", "analyzer": "plk_text"},
            "chunk_index": {"type": "integer"},
            "char_start": {"type": "integer"},
            "char_end": {"type": "integer"},
        }
    },
}


def _assert_connection(client: OpenSearch) -> None:
    """Fail fast if authentication or connectivity is broken."""
    try:
        client.info()
    except exceptions.AuthenticationException as exc:  # type: ignore[attr-defined]
        raise RuntimeError("OpenSearch authentication failed; check OPENSEARCH_USER/OPENSEARCH_PASSWORD") from exc
    except exceptions.TransportError as exc:  # type: ignore[attr-defined]
        raise RuntimeError("OpenSearch connection failed") from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("OpenSearch client initialization failed") from exc


def get_client() -> OpenSearch:
    secure = settings.opensearch_scheme.lower() == "https"
    client = OpenSearch(
        hosts=[
            {
                "host": settings.opensearch_host,
                "port": settings.opensearch_port,
                "scheme": settings.opensearch_scheme,
            }
        ],
        http_auth=(settings.opensearch_user, settings.opensearch_password),
        use_ssl=secure,
        verify_certs=False,
        ssl_show_warn=False,
    )
    _assert_connection(client)
    return client


def create_index(client: OpenSearch, index_name: str) -> None:
    client.indices.create(index=index_name, body=CHUNK_INDEX_BODY)


def delete_index(client: OpenSearch, index_name: str) -> None:
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)


def bulk_index(client: OpenSearch, index_name: str, docs: List[dict]) -> None:
    actions = [
        {
            "_op_type": "index",
            "_index": index_name,
            "_id": doc["chunk_id"],
            "_source": doc,
        }
        for doc in docs
    ]
    helpers.bulk(client, actions)
