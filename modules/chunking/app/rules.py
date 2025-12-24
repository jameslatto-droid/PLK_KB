"""
Chunking rules.

This module defines invariant rules that govern chunk creation.
"""

ALLOWED_CHUNK_TYPES = {
    "text",
    "table",
    "calculation",
    "summary"
}

PROHIBITED_ACTIONS = [
    "semantic merging",
    "embedding generation",
    "authority inference",
    "content rewriting"
]
