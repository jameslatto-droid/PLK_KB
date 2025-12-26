"""
Extraction module for PLK_KB - Stage 8

Provides:
- Tiered filetype allowlist
- Extractor registry
- Standardized extraction results
- Safe, explicit, deterministic file handling
"""

from modules.extraction.types import ExtractionResult
from modules.extraction.allowlist import FileTypeTier, get_file_tier
from modules.extraction.registry import get_extractor, list_supported_extensions

__all__ = [
    "ExtractionResult",
    "FileTypeTier",
    "get_file_tier",
    "get_extractor",
    "list_supported_extensions",
]
