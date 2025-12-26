"""
Stage 8 Filetype Allowlist

Defines three tiers of file support:
- Tier 1: Enabled by default (safe text formats)
- Tier 2: Disabled by default (structured office formats)
- Tier 3: Recognised but blocked (media, CAD, binaries)

This allowlist is the authoritative source for what PLK_KB can ingest.
"""

from enum import Enum
from pathlib import Path


class FileTypeTier(Enum):
    """
    Three-tier filetype classification.
    
    TIER_1: Safe text formats - enabled by default
    TIER_2: Structured office formats - requires explicit enablement
    TIER_3: Unsupported formats - recognised but blocked
    UNKNOWN: Not in allowlist - must be explicitly rejected
    """
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    UNKNOWN = -1


# Tier 1: Enabled by default — safe text formats
TIER_1_EXTENSIONS = {
    ".txt",   # Plain text
    ".md",    # Markdown
    ".csv",   # Comma-separated values
    ".tsv",   # Tab-separated values
    ".json",  # JSON data
    ".yaml",  # YAML configuration
    ".yml",   # YAML (alternate extension)
    ".xml",   # XML (treated as plain text, no entity expansion)
    ".log",   # Log files
    ".rtf",   # Rich text format (text-based)
}

# Tier 2: Disabled by default — structured office formats
# Requires PLK_ENABLE_TIER_2=true in config
TIER_2_EXTENSIONS = {
    ".pdf",   # PDF (text-based only, no OCR)
    ".docx",  # Microsoft Word
    ".xlsx",  # Microsoft Excel
    ".pptx",  # Microsoft PowerPoint
}

# Tier 3: Recognised but blocked — unsupported formats
# These are logged as "recognised but unsupported"
# Can be metadata-only ingestion in future
TIER_3_EXTENSIONS = {
    # Images
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".svg", ".webp",
    # Audio
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac",
    # Video
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm",
    # CAD/Engineering
    ".dwg", ".dxf", ".step", ".stp", ".iges", ".igs", ".stl",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    # Executables
    ".exe", ".dll", ".so", ".dylib", ".bin",
    # Other binaries
    ".db", ".sqlite", ".pyc", ".class",
}


def get_file_tier(file_path: Path | str) -> FileTypeTier:
    """
    Classify a file into one of three tiers based on extension.
    
    Args:
        file_path: Path to the file (can be str or Path)
        
    Returns:
        FileTypeTier enum indicating tier classification
        
    Rules:
        - Comparison is case-insensitive
        - Leading dot is required in extension sets
        - Unknown extensions return FileTypeTier.UNKNOWN
        
    Example:
        >>> get_file_tier("document.txt")
        FileTypeTier.TIER_1
        >>> get_file_tier("report.pdf")
        FileTypeTier.TIER_2
        >>> get_file_tier("image.jpg")
        FileTypeTier.TIER_3
        >>> get_file_tier("random.xyz")
        FileTypeTier.UNKNOWN
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    ext = file_path.suffix.lower()
    
    if ext in TIER_1_EXTENSIONS:
        return FileTypeTier.TIER_1
    elif ext in TIER_2_EXTENSIONS:
        return FileTypeTier.TIER_2
    elif ext in TIER_3_EXTENSIONS:
        return FileTypeTier.TIER_3
    else:
        return FileTypeTier.UNKNOWN


def get_tier_description(tier: FileTypeTier) -> str:
    """
    Get human-readable description of a tier.
    
    Args:
        tier: FileTypeTier enum value
        
    Returns:
        Description string for logging/UI
    """
    descriptions = {
        FileTypeTier.TIER_1: "Safe text format (enabled by default)",
        FileTypeTier.TIER_2: "Structured office format (requires explicit enablement)",
        FileTypeTier.TIER_3: "Recognised but unsupported (media/CAD/binary)",
        FileTypeTier.UNKNOWN: "Unknown/unrecognised file type",
    }
    return descriptions.get(tier, "Invalid tier")


def is_tier_enabled(tier: FileTypeTier, enable_tier_2: bool = False) -> bool:
    """
    Check if a tier is enabled for ingestion.
    
    Args:
        tier: FileTypeTier to check
        enable_tier_2: Whether Tier 2 is explicitly enabled (from config)
        
    Returns:
        True if tier is allowed, False otherwise
        
    Rules:
        - Tier 1: always enabled
        - Tier 2: only if enable_tier_2=True
        - Tier 3: never enabled (always blocked)
        - Unknown: never enabled (always blocked)
    """
    if tier == FileTypeTier.TIER_1:
        return True
    elif tier == FileTypeTier.TIER_2:
        return enable_tier_2
    else:
        return False
