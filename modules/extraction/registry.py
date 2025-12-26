"""
Stage 8 Extractor Registry

Central registry mapping file extensions to extractors.
This is the ONLY place where extractors are defined.

Rules:
- One extractor per extension
- No dynamic loading
- No ambiguity
- Registry is authoritative
"""

import logging
import os
from pathlib import Path
from typing import Callable, Optional

from modules.extraction.allowlist import FileTypeTier, get_file_tier
from modules.extraction.extractors import (
    extract_csv,
    extract_json,
    extract_txt,
    extract_yaml,
)
from modules.extraction.types import ExtractionResult

logger = logging.getLogger(__name__)

# Type alias for extractor functions
ExtractorFunc = Callable[[Path, Optional[int]], ExtractionResult]


class ExtractorRegistryEntry:
    """
    Single entry in the extractor registry.
    
    Immutable spec for an extractor.
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        extensions: list[str],
        tier: int,
        deterministic: bool,
        allows_partial: bool,
        max_size_mb: Optional[int],
        extract_func: ExtractorFunc,
    ):
        self.name = name
        self.version = version
        self.extensions = extensions
        self.tier = tier
        self.deterministic = deterministic
        self.allows_partial = allows_partial
        self.max_size_mb = max_size_mb
        self.extract_func = extract_func
    
    def __repr__(self) -> str:
        return f"<Extractor {self.name} v{self.version} tier={self.tier} exts={self.extensions}>"


# TIER 1 EXTRACTORS — Safe text formats (enabled by default)
_TIER_1_EXTRACTORS = [
    ExtractorRegistryEntry(
        name="plain_text",
        version="1.0.0",
        extensions=[".txt", ".log", ".md", ".rtf", ".xml"],
        tier=1,
        deterministic=True,
        allows_partial=True,
        max_size_mb=int(os.getenv("PLK_MAX_EXTRACT_MB", "100")),
        extract_func=extract_txt,
    ),
    ExtractorRegistryEntry(
        name="csv",
        version="1.0.0",
        extensions=[".csv", ".tsv"],
        tier=1,
        deterministic=True,
        allows_partial=True,
        max_size_mb=int(os.getenv("PLK_MAX_EXTRACT_MB", "100")),
        extract_func=extract_csv,
    ),
    ExtractorRegistryEntry(
        name="json",
        version="1.0.0",
        extensions=[".json"],
        tier=1,
        deterministic=True,
        allows_partial=False,  # JSON must be valid or failed
        max_size_mb=int(os.getenv("PLK_MAX_EXTRACT_MB", "100")),
        extract_func=extract_json,
    ),
    ExtractorRegistryEntry(
        name="yaml",
        version="1.0.0",
        extensions=[".yaml", ".yml"],
        tier=1,
        deterministic=True,
        allows_partial=False,  # YAML must be valid or failed
        max_size_mb=int(os.getenv("PLK_MAX_EXTRACT_MB", "100")),
        extract_func=extract_yaml,
    ),
]

# TIER 2 EXTRACTORS — Structured office formats (disabled by default)
# TODO: Implement when PLK_ENABLE_TIER_2=true
_TIER_2_EXTRACTORS: list[ExtractorRegistryEntry] = []

# Build extension → extractor mapping
_EXTENSION_MAP: dict[str, ExtractorRegistryEntry] = {}
for extractor in _TIER_1_EXTRACTORS + _TIER_2_EXTRACTORS:
    for ext in extractor.extensions:
        if ext in _EXTENSION_MAP:
            logger.warning("Duplicate extractor registration for %s (overwriting)", ext)
        _EXTENSION_MAP[ext.lower()] = extractor


def get_extractor(file_path: Path | str) -> Optional[ExtractorRegistryEntry]:
    """
    Get extractor for a file based on extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        ExtractorRegistryEntry if registered, None otherwise
        
    Rules:
        - Lookup is case-insensitive
        - Only checks extension, not content
        - Returns None for unsupported extensions
        
    Example:
        >>> extractor = get_extractor("doc.txt")
        >>> if extractor:
        ...     result = extractor.extract_func(Path("doc.txt"), extractor.max_size_mb)
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    ext = file_path.suffix.lower()
    return _EXTENSION_MAP.get(ext)


def list_supported_extensions() -> list[str]:
    """
    Get list of all supported file extensions.
    
    Returns:
        Sorted list of extensions with leading dots
        
    Example:
        >>> list_supported_extensions()
        ['.csv', '.json', '.log', '.md', '.rtf', '.tsv', '.txt', '.yaml', '.yml']
    """
    return sorted(_EXTENSION_MAP.keys())


def extract_file(file_path: Path, enable_tier_2: bool = False) -> tuple[ExtractionResult, str]:
    """
    Extract text from a file using registered extractors.
    
    This is the primary entry point for extraction.
    
    Args:
        file_path: Path to file to extract
        enable_tier_2: Whether Tier 2 extractors are enabled
        
    Returns:
        Tuple of (ExtractionResult, reason)
        - If extraction succeeds/fails: (result, "extracted via {extractor}")
        - If no extractor: (failed_result, "no extractor for tier X")
        - If tier disabled: (failed_result, "tier X not enabled")
        
    Rules:
        - Tier 1: always attempted
        - Tier 2: only if enable_tier_2=True
        - Tier 3: never extracted (returns failed)
        - Unknown: never extracted (returns failed)
        
    Example:
        >>> result, reason = extract_file(Path("doc.txt"))
        >>> if result["status"] == "success":
        ...     text = result["text"]
    """
    tier = get_file_tier(file_path)
    
    # Check if tier is enabled
    if tier == FileTypeTier.TIER_1:
        pass  # Always enabled
    elif tier == FileTypeTier.TIER_2:
        if not enable_tier_2:
            return (
                {
                    "status": "failed",
                    "text": None,
                    "warnings": [],
                    "errors": [f"Tier 2 not enabled (set PLK_ENABLE_TIER_2=true)"],
                    "confidence": None,
                    "metadata": {"tier": 2, "extension": file_path.suffix},
                },
                "tier 2 not enabled",
            )
    else:
        # Tier 3 or Unknown
        tier_name = "tier 3 (unsupported)" if tier == FileTypeTier.TIER_3 else "unknown"
        return (
            {
                "status": "failed",
                "text": None,
                "warnings": [],
                "errors": [f"File type not supported: {file_path.suffix}"],
                "confidence": None,
                "metadata": {"tier": tier.value, "extension": file_path.suffix},
            },
            f"no extractor for {tier_name}",
        )
    
    # Get extractor
    extractor = get_extractor(file_path)
    if not extractor:
        return (
            {
                "status": "failed",
                "text": None,
                "warnings": [],
                "errors": [f"No extractor registered for {file_path.suffix}"],
                "confidence": None,
                "metadata": {"tier": tier.value, "extension": file_path.suffix},
            },
            f"no extractor for {file_path.suffix}",
        )
    
    # Extract
    try:
        result = extractor.extract_func(file_path, extractor.max_size_mb)
        reason = f"extracted via {extractor.name} v{extractor.version}"
        return (result, reason)
    except Exception as exc:
        logger.exception("Extractor %s failed unexpectedly for %s", extractor.name, file_path)
        return (
            {
                "status": "failed",
                "text": None,
                "warnings": [],
                "errors": [f"Extractor crashed: {type(exc).__name__}: {exc}"],
                "confidence": None,
                "metadata": {
                    "extractor": extractor.name,
                    "version": extractor.version,
                    "tier": tier.value,
                },
            },
            f"extractor {extractor.name} crashed",
        )
