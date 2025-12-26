"""
Tier 1 Extractors - Safe Text Formats

Deterministic, bounded, fail-safe extractors for:
- Plain text (.txt)
- CSV (.csv, .tsv)
- JSON (.json)
- YAML (.yaml, .yml)

All extractors follow these rules:
- No external binaries
- Size limits enforced
- Errors populate errors[] list
- Never raise uncaught exceptions
- Return standardized ExtractionResult
"""

import csv
import json
import logging
from pathlib import Path
from typing import Optional

import yaml

from modules.extraction.types import ExtractionResult

logger = logging.getLogger(__name__)

# Default size limits (can be overridden by config)
DEFAULT_MAX_SIZE_MB = 100
MAX_TEXT_LENGTH = 50_000_000  # 50MB text limit


def _check_file_size(file_path: Path, max_size_mb: Optional[int] = None) -> Optional[str]:
    """
    Check if file exceeds size limit.
    
    Returns:
        Error message if file too large, None if acceptable
    """
    max_size = (max_size_mb or DEFAULT_MAX_SIZE_MB) * 1024 * 1024
    file_size = file_path.stat().st_size
    
    if file_size > max_size:
        return f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit ({max_size_mb or DEFAULT_MAX_SIZE_MB}MB)"
    
    return None


def extract_txt(file_path: Path, max_size_mb: Optional[int] = None) -> ExtractionResult:
    """
    Extract plain text files (.txt, .log, .md, .rtf treated as text).
    
    Rules:
    - UTF-8 with fallback to latin-1
    - Size limit enforced
    - Empty files return success with empty text
    - Malformed encoding triggers partial status
    
    Args:
        file_path: Path to text file
        max_size_mb: Maximum file size in MB
        
    Returns:
        ExtractionResult with status, text, and metadata
    """
    result: ExtractionResult = {
        "status": "success",
        "text": None,
        "warnings": [],
        "errors": [],
        "confidence": 1.0,
        "metadata": {"extractor": "txt", "version": "1.0.0"},
    }
    
    try:
        # Check size
        size_error = _check_file_size(file_path, max_size_mb)
        if size_error:
            result["status"] = "failed"
            result["errors"].append(size_error)
            return result
        
        # Read with UTF-8, fallback to latin-1
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result["warnings"].append("UTF-8 decode failed, using latin-1 fallback")
            text = file_path.read_text(encoding="latin-1", errors="replace")
            result["confidence"] = 0.9
            result["status"] = "partial"
        
        # Enforce text length limit
        if len(text) > MAX_TEXT_LENGTH:
            result["warnings"].append(f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars")
            text = text[:MAX_TEXT_LENGTH]
            result["status"] = "partial"
            result["confidence"] = 0.8
        
        result["text"] = text
        result["metadata"]["char_count"] = len(text)
        result["metadata"]["line_count"] = text.count("\n") + 1
        
    except Exception as exc:
        result["status"] = "failed"
        result["errors"].append(f"Extraction failed: {type(exc).__name__}: {exc}")
        logger.exception("TXT extraction failed for %s", file_path)
    
    return result


def extract_csv(file_path: Path, max_size_mb: Optional[int] = None) -> ExtractionResult:
    """
    Extract CSV/TSV files as structured text.
    
    Rules:
    - Converts to tab-delimited text for chunking
    - Detects delimiter automatically
    - Empty files return success with empty text
    - Malformed CSV triggers partial status
    
    Args:
        file_path: Path to CSV/TSV file
        max_size_mb: Maximum file size in MB
        
    Returns:
        ExtractionResult with delimited text
    """
    result: ExtractionResult = {
        "status": "success",
        "text": None,
        "warnings": [],
        "errors": [],
        "confidence": 1.0,
        "metadata": {"extractor": "csv", "version": "1.0.0"},
    }
    
    try:
        # Check size
        size_error = _check_file_size(file_path, max_size_mb)
        if size_error:
            result["status"] = "failed"
            result["errors"].append(size_error)
            return result
        
        # Detect delimiter
        delimiter = "\t" if file_path.suffix.lower() == ".tsv" else ","
        
        # Read and convert to text
        lines = []
        row_count = 0
        
        with file_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)
            try:
                for row in reader:
                    lines.append("\t".join(row))
                    row_count += 1
                    
                    # Safety limit
                    if row_count > 1_000_000:
                        result["warnings"].append("CSV truncated at 1M rows")
                        result["status"] = "partial"
                        result["confidence"] = 0.9
                        break
            except csv.Error as e:
                result["warnings"].append(f"CSV parsing error at row {row_count}: {e}")
                result["status"] = "partial"
                result["confidence"] = 0.7
        
        text = "\n".join(lines)
        
        if len(text) > MAX_TEXT_LENGTH:
            result["warnings"].append(f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars")
            text = text[:MAX_TEXT_LENGTH]
            result["status"] = "partial"
            result["confidence"] = min(result["confidence"] or 1.0, 0.8)
        
        result["text"] = text
        result["metadata"]["row_count"] = row_count
        result["metadata"]["char_count"] = len(text)
        
    except Exception as exc:
        result["status"] = "failed"
        result["errors"].append(f"Extraction failed: {type(exc).__name__}: {exc}")
        logger.exception("CSV extraction failed for %s", file_path)
    
    return result


def extract_json(file_path: Path, max_size_mb: Optional[int] = None) -> ExtractionResult:
    """
    Extract JSON files as formatted text.
    
    Rules:
    - Pretty-prints JSON for readability
    - Validates JSON structure
    - Invalid JSON triggers failed status
    
    Args:
        file_path: Path to JSON file
        max_size_mb: Maximum file size in MB
        
    Returns:
        ExtractionResult with formatted JSON text
    """
    result: ExtractionResult = {
        "status": "success",
        "text": None,
        "warnings": [],
        "errors": [],
        "confidence": 1.0,
        "metadata": {"extractor": "json", "version": "1.0.0"},
    }
    
    try:
        # Check size
        size_error = _check_file_size(file_path, max_size_mb)
        if size_error:
            result["status"] = "failed"
            result["errors"].append(size_error)
            return result
        
        # Parse and re-serialize
        raw_text = file_path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
        
        # Pretty-print for chunking
        text = json.dumps(data, indent=2, ensure_ascii=False)
        
        if len(text) > MAX_TEXT_LENGTH:
            result["warnings"].append(f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars")
            text = text[:MAX_TEXT_LENGTH]
            result["status"] = "partial"
            result["confidence"] = 0.8
        
        result["text"] = text
        result["metadata"]["char_count"] = len(text)
        result["metadata"]["valid_json"] = True
        
    except json.JSONDecodeError as exc:
        result["status"] = "failed"
        result["errors"].append(f"Invalid JSON: {exc}")
        result["metadata"]["valid_json"] = False
        
    except Exception as exc:
        result["status"] = "failed"
        result["errors"].append(f"Extraction failed: {type(exc).__name__}: {exc}")
        logger.exception("JSON extraction failed for %s", file_path)
    
    return result


def extract_yaml(file_path: Path, max_size_mb: Optional[int] = None) -> ExtractionResult:
    """
    Extract YAML files as formatted text.
    
    Rules:
    - Converts to JSON-like text for chunking
    - Validates YAML structure
    - Invalid YAML triggers failed status
    
    Args:
        file_path: Path to YAML file
        max_size_mb: Maximum file size in MB
        
    Returns:
        ExtractionResult with formatted YAML text
    """
    result: ExtractionResult = {
        "status": "success",
        "text": None,
        "warnings": [],
        "errors": [],
        "confidence": 1.0,
        "metadata": {"extractor": "yaml", "version": "1.0.0"},
    }
    
    try:
        # Check size
        size_error = _check_file_size(file_path, max_size_mb)
        if size_error:
            result["status"] = "failed"
            result["errors"].append(size_error)
            return result
        
        # Parse YAML
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        # Convert to JSON for consistent format
        text = json.dumps(data, indent=2, ensure_ascii=False)
        
        if len(text) > MAX_TEXT_LENGTH:
            result["warnings"].append(f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} chars")
            text = text[:MAX_TEXT_LENGTH]
            result["status"] = "partial"
            result["confidence"] = 0.8
        
        result["text"] = text
        result["metadata"]["char_count"] = len(text)
        result["metadata"]["valid_yaml"] = True
        
    except yaml.YAMLError as exc:
        result["status"] = "failed"
        result["errors"].append(f"Invalid YAML: {exc}")
        result["metadata"]["valid_yaml"] = False
        
    except Exception as exc:
        result["status"] = "failed"
        result["errors"].append(f"Extraction failed: {type(exc).__name__}: {exc}")
        logger.exception("YAML extraction failed for %s", file_path)
    
    return result
