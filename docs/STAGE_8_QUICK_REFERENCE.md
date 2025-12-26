# Stage 8: Extraction Quick Reference

## Entry Point

```python
from modules.extraction.registry import extract_file
from pathlib import Path

result, reason = extract_file(Path("/path/to/file.txt"), enable_tier_2=False)

if result["status"] == "success":
    text = result["text"]
    # Process extracted text
elif result["status"] == "partial":
    text = result["text"]
    for warning in result["warnings"]:
        log.warning(warning)
elif result["status"] == "failed":
    for error in result["errors"]:
        log.error(error)
    raise RuntimeError(f"Extraction failed: {reason}")
```

## Supported Extensions (Tier 1)

| Extension | Extractor | Output Format |
|-----------|-----------|---------------|
| `.txt`, `.md`, `.log`, `.rtf` | plain_text | Raw text (UTF-8) |
| `.csv`, `.tsv` | csv | Tab-delimited text |
| `.json` | json | Pretty-printed JSON |
| `.yaml`, `.yml` | yaml | JSON representation |
| `.xml` | plain_text | Raw text (no entity expansion, no schema validation) |

## ExtractionResult Contract

```python
{
    "status": "success" | "partial" | "failed",
    "text": str | None,
    "warnings": list[str],
    "errors": list[str],
    "confidence": float | None,  # 0.0-1.0
    "metadata": {
        "extractor": str,    # e.g., "plain_text"
        "version": str,      # e.g., "1.0.0"
        ...
    }
}
```

**Note**: `confidence` is informational only and is not used for gating access or indexing decisions in Stage 8.

## Status Meanings

- **success**: Full extraction, no issues
- **partial**: Extracted text but with warnings (e.g., encoding fallback, size truncation)
- **failed**: No text extracted, see `errors[]`

**Important**: File tiers are an extraction concern only. They do not imply clearance hierarchy. Classification checks elsewhere in the system remain equality-based, not "greater-than".

## File Tiers

### Tier 1 (Safe Text) - Always Enabled
`.txt`, `.md`, `.csv`, `.json`, `.yaml`, `.log`, `.ini`, `.conf`, `.cfg`, `.xml`

### Tier 2 (Office Docs) - Disabled by Default
`.pdf`, `.docx`, `.xlsx`, `.pptx`, `.odt`, `.ods`, `.odp`

### Tier 3 (Blocked) - Never Enabled
`.jpg`, `.png`, `.mp4`, `.zip`, `.exe`, `.dll`, `.dwg`, `.dxf`

**Tier 3 Metadata Handling**: Tier 3 files may be registered as artefacts with metadata only, but:
- No text extraction
- No chunking
- No indexing

## Configuration

```bash
# Environment variables
PLK_ENABLE_TIER_2=false        # Enable Tier 2 (default: false)
PLK_MAX_EXTRACT_MB=100         # Max file size in MB (default: 100)
```

```python
# In code
from modules.ingestion.app.config import settings

enable_tier_2 = settings.enable_tier_2
max_size = settings.max_extract_mb
```

## Failure Modes

| Scenario | Status | Reason |
|----------|--------|--------|
| Unknown extension `.xyz` | failed | "Unknown file type" |
| Tier 3 file `.jpg` | failed | "Blocked tier (TIER_3)" |
| Tier 2 disabled `.pdf` | failed | "Tier 2 disabled" |
| File > 100MB | failed | "File size exceeds limit" |
| Malformed JSON | failed | "JSON decode error: ..." |
| UTF-8 decode fail | partial | "Used latin-1 fallback" |

## Adding New Extractors

### 1. Implement Extractor Function

```python
# modules/extraction/extractors.py

def extract_pdf(path: Path, max_size_mb: int = DEFAULT_MAX_SIZE_MB) -> ExtractionResult:
    """Extract text from PDF."""
    try:
        _check_file_size(path, max_size_mb)
        import pypdf
        # ... extraction logic
        return {
            "status": "success",
            "text": extracted_text,
            "warnings": [],
            "errors": [],
            "confidence": 0.9,
            "metadata": {"extractor": "pdf", "version": "1.0.0"}
        }
    except Exception as e:
        return {
            "status": "failed",
            "text": None,
            "warnings": [],
            "errors": [str(e)],
            "confidence": 0.0,
            "metadata": {"extractor": "pdf", "version": "1.0.0"}
        }
```

### 2. Register in Registry

```python
# modules/extraction/registry.py

_TIER_2_EXTRACTORS = [
    ExtractorRegistryEntry(
        name="pdf",
        version="1.0.0",
        extensions=[".pdf"],
        tier=2,
        deterministic=False,  # PDF extraction may vary
        allows_partial=True,
        max_size_mb=int(os.getenv("PLK_MAX_EXTRACT_MB", "100")),
        extract_func=extract_pdf,
    ),
]
```

### 3. Update Allowlist

```python
# modules/extraction/allowlist.py

TIER_2_EXTENSIONS = {
    ".pdf",  # <-- Add here
    ".docx",
    # ...
}
```

### 4. Add Tests

```python
# modules/extraction/tests/test_extractors.py

def test_extract_pdf():
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        # Create test PDF
        ...
    result = extract_pdf(Path(f.name))
    assert result["status"] == "success"
```

## Testing

```bash
# Run all extraction tests
python3 -m pytest modules/extraction/tests/ -v

# Run specific test
python3 -m pytest modules/extraction/tests/test_extractors.py::TestPlainTextExtractor::test_extract_utf8_text -v

# Test extraction on real file
python3 -c "from modules.extraction.registry import extract_file; from pathlib import Path; print(extract_file(Path('test.txt')))"
```

## Debugging

```python
# Enable extraction logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("modules.extraction")
logger.setLevel(logging.DEBUG)

# Extract with verbose output
result, reason = extract_file(Path("problematic_file.csv"))
print(f"Status: {result['status']}")
print(f"Reason: {reason}")
print(f"Warnings: {result['warnings']}")
print(f"Errors: {result['errors']}")
```

## Performance Tips

1. **Size Limits**: Adjust `PLK_MAX_EXTRACT_MB` based on available memory
2. **Parallel Ingestion**: Multiple files can extract concurrently
3. **Chunking**: Extraction happens before chunking (chunking is slower)
4. **Monitoring**: Log extraction time per file for bottleneck analysis

## Security Best Practices

1. **Disable Tier 2 in untrusted environments**
2. **Set conservative size limits** (default 100MB is safe)
3. **Monitor extraction failures** for attack patterns
4. **Audit new extractors** before production deployment
5. **Use sandboxed containers** for Tier 2 extraction (future)

---

**Quick Start**

```bash
# 1. Check file tier
python3 -c "from modules.extraction.allowlist import get_file_tier; from pathlib import Path; print(get_file_tier(Path('myfile.pdf')))"

# 2. Extract file
python3 -c "from modules.extraction.registry import extract_file; from pathlib import Path; result, reason = extract_file(Path('myfile.txt')); print(f'{result[\"status\"]}: {len(result[\"text\"])} chars')"

# 3. Run tests
python3 -m pytest modules/extraction/tests/ -v
```

---

**See Also**

- [Full Documentation](./11_stage_8_extraction_and_filetypes.md)
- [Implementation Summary](./STAGE_8_SUMMARY.md)
- [Code: modules/extraction/](../modules/extraction/)
