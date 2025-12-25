"""Metadata access layer."""

from .repository import (
    create_document,
    get_document,
    list_documents,
    update_document,
    delete_document,
    get_connection,
)

__all__ = [
    "create_document",
    "get_document",
    "list_documents",
    "update_document",
    "delete_document",
    "get_connection",
]
