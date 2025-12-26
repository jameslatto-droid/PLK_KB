"""
Stage 8 Extraction Types

Defines the standard contract for all extraction results.
This contract ensures extraction behavior is explicit and auditable.
"""

from typing import Literal, Optional, TypedDict


class ExtractionResult(TypedDict):
    """
    Standard result contract for all extractors.
    
    status values:
    - 'success': extraction completed, text is safe to chunk & index
    - 'partial': extraction incomplete but usable, warnings present
    - 'failed': extraction failed, only metadata should be stored
    
    Rules:
    - Extractors MUST populate status
    - 'success' implies text is present and complete
    - 'partial' implies text is present but may be incomplete
    - 'failed' implies text is None or unusable
    - warnings/errors are always lists (never None)
    """
    status: Literal["success", "partial", "failed"]
    text: Optional[str]
    warnings: list[str]
    errors: list[str]
    confidence: Optional[float]
    metadata: dict[str, str | int | float | bool]


class ExtractorSpec(TypedDict):
    """
    Extractor specification for registry.
    
    Each extractor must declare:
    - name: human-readable identifier
    - version: semver-compatible version
    - extensions: supported file extensions (with leading dot)
    - tier: 1 (safe), 2 (structured), or 3 (blocked)
    - deterministic: whether extraction is reproducible
    - allows_partial: whether partial results are acceptable
    - max_size_mb: maximum file size in MB (None = unlimited)
    - extract_func: callable(Path) -> ExtractionResult
    """
    name: str
    version: str
    extensions: list[str]
    tier: Literal[1, 2, 3]
    deterministic: bool
    allows_partial: bool
    max_size_mb: Optional[int]
