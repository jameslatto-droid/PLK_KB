"""OpenSearch search utilities for hybrid search."""

from opensearchpy import OpenSearch, exceptions

from .config import settings


def _assert_connection(client: OpenSearch) -> None:
    try:
        client.info()
    except exceptions.AuthenticationException as exc:  # type: ignore[attr-defined]
        raise RuntimeError("OpenSearch authentication failed; check OPENSEARCH_USER/OPENSEARCH_PASSWORD") from exc
    except exceptions.TransportError as exc:  # type: ignore[attr-defined]
        raise RuntimeError("OpenSearch connection failed") from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError("OpenSearch client initialization failed") from exc


def get_client() -> OpenSearch:
    client = OpenSearch(
        hosts=[{"host": settings.opensearch_host, "port": settings.opensearch_port}],
        http_auth=(settings.opensearch_user, settings.opensearch_password),
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
    )
    _assert_connection(client)
    return client
