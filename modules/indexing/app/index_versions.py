"""
Index versioning contract.

Indexes are derived state. Versions must be explicitly recorded.
"""


def record_index_version(index_version: str, notes: str | None = None):
    raise NotImplementedError("Index version recording not implemented (Stage 2)")
