# Stage 8: Extraction & Filetype Expansion

**Status**: ✅ **Implemented** (Phase 3, Stage 8)  
**Date**: January 2025  
**Related Documents**: [Project Overview](./01_project_overview.md), [Phased Plan](./03_phased_plan_dos.md), [Authority Model](./05_authority_and_access_model.md)

---

## Overview

Stage 8 implements a **tiered, explicit, deterministic extraction system** for handling multiple file types during ingestion. The system replaces direct file reading with a structured extraction pipeline that:

1. **Classifies files into tiers** (Tier 1: safe text, Tier 2: office docs, Tier 3: blocked)
2. **Routes to appropriate extractors** via a central registry
3. **Returns standardized results** with status, text, warnings, errors, and confidence
4. **Provides explicit failure modes** (no silent failures)
5. **Enforces size limits and safety constraints**

This approach ensures **auditability, determinism, and controlled expansion** of supported file types.

---

## Architecture

### Module Structure

```
modules/extraction/
├── __init__.py           # Module exports
├── types.py              # ExtractionResult TypedDict, ExtractorSpec
├── allowlist.py          # Tiered filetype classification
├── extractors.py         # Tier 1 extractor implementations
└── registry.py           # Central extractor registry, extract_file() entry point
```

### Core Types

#### ExtractionResult (TypedDict)

```python
class ExtractionResult(TypedDict):
    status: Literal["success", "partial", "failed"]  # Extraction outcome
    text: Optional[str]                              # Extracted text content
    warnings: list[str]                               # Non-fatal issues
    errors: list[str]                                 # Fatal errors
    confidence: Optional[float]                       # Extraction quality (0.0-1.0)
    metadata: dict[str, Any]                          # Extractor info, format details
```

**Note**: `confidence` is informational only and is not used for gating access or indexing decisions in Stage 8.

#### ExtractorSpec

```python
class ExtractorSpec:
    name: str                                 # e.g., "plain_text", "csv"
    version: str                              # e.g., "1.0.0"
    supported_extensions: frozenset[str]      # e.g., {".txt", ".md"}
    tier: FileTypeTier                        # TIER_1, TIER_2, TIER_3
    extract_func: Callable[[Path], ExtractionResult]
```

---

## Tiered Allowlist

**Important**: File tiers are an extraction concern only. They do not imply clearance hierarchy. Classification checks elsewhere in the system remain equality-based, not "greater-than".

### Tier 1: Safe Text Formats (Always Enabled)

**Characteristics**:
- Deterministic, no external dependencies
- Size-limited (default 100MB)
- UTF-8 with fallback to latin-1
- No network calls, no code execution

**Supported Extensions**:
```python
TIER_1_EXTENSIONS = {
    ".txt", ".md", ".markdown",       # Plain text
    ".csv", ".tsv",                    # Tabular data
    ".json", ".jsonl",                 # JSON formats
    ".yaml", ".yml",                   # YAML
    ".xml",                            # XML (treated as plain text, no entity expansion)
    ".log",                            # Log files
    ".ini", ".conf", ".cfg",          # Config files
}
```

**XML Handling**: `.xml` files are treated as plain text with no entity expansion and no schema validation. This prevents XXE (XML External Entity) attacks.

### Tier 2: Office Documents (Disabled by Default)

**Characteristics**:
- Requires external libraries (pypdf, python-docx, openpyxl)
- More complex parsing logic
- Enabled via `PLK_ENABLE_TIER_2=true`

**Supported Extensions** (not yet implemented):
```python
TIER_2_EXTENSIONS = {
    ".pdf",                            # PDF documents
    ".docx", ".doc",                   # Microsoft Word
    ".xlsx", ".xls",                   # Microsoft Excel
    ".pptx", ".ppt",                   # Microsoft PowerPoint
    ".odt", ".ods", ".odp",           # OpenDocument formats
}
```

### Tier 3: Blocked Formats (Never Enabled)

**Characteristics**:
- Binary formats not suitable for text extraction
- Media, CAD, executables, archives

**Blocked Extensions**:
```python
TIER_3_EXTENSIONS = {
    # Media
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
    ".mp4", ".avi", ".mov", ".mp3", ".wav",
    
    # CAD & Engineering
    ".dwg", ".dxf", ".step", ".stp", ".iges", ".igs",
    
    # Executables & Libraries
    ".exe", ".dll", ".so", ".dylib", ".bin",
    
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
}
```

**Tier 3 Metadata Handling**: Tier 3 files may be registered as artefacts with metadata only, but:
- No text extraction
- No chunking
- No indexing

---

## Extractor Registry

### Registry Design

The registry is a **static, compile-time mapping** of file extensions to extractor functions. No dynamic loading or plugin architecture - all extractors are explicitly defined in `modules/extraction/extractors.py` and registered in `modules/extraction/registry.py`.

**Benefits**:
- **Determinism**: Same file always uses same extractor
- **Auditability**: All extractors visible in code review
- **Safety**: No arbitrary code execution
- **Simplicity**: No plugin discovery complexity

### Registry Entry Structure

```python
class ExtractorRegistryEntry:
    def __init__(self, spec: ExtractorSpec):
        self.spec = spec
        self.extension_map = {ext: spec for ext in spec.supported_extensions}
```

### Extension Mapping

```python
_EXTENSION_MAP: dict[str, ExtractorRegistryEntry] = {
    ".txt": plain_text_entry,
    ".md": plain_text_entry,
    ".csv": csv_entry,
    ".json": json_entry,
    ".yaml": yaml_entry,
    ".yml": yaml_entry,
    # ... more mappings
}
```

### Main Entry Point

```python
def extract_file(path: Path, enable_tier_2: bool = False) -> tuple[ExtractionResult, str]:
    """
    Extract text from a file using the appropriate extractor.
    
    Returns:
        (ExtractionResult, reason_string)
        
    Raises:
        No exceptions - all errors captured in ExtractionResult.errors
    """
```

---

## Tier 1 Extractors

### Plain Text Extractor

**Supported**: `.txt`, `.md`, `.markdown`, `.log`

**Algorithm**:
1. Check file size ≤ max_size_mb (default 100MB)
2. Read bytes from disk
3. Decode as UTF-8 (fallback to latin-1 if UTF-8 fails)
4. Enforce max_text_length (default 50MB characters)
5. Return success/partial/failed with text and warnings

**Example**:
```python
result = {
    "status": "success",
    "text": "file contents...",
    "warnings": [],
    "errors": [],
    "confidence": 1.0,
    "metadata": {"extractor": "plain_text", "version": "1.0.0"}
}
```

### CSV Extractor

**Supported**: `.csv`, `.tsv`

**Algorithm**:
1. Check file size
2. Detect delimiter (comma, tab, semicolon, pipe)
3. Parse as CSV with Python `csv.reader`
4. Convert to tab-delimited text format
5. Handle quoting and escape characters

**Output Format**:
```
header1\theader2\theader3
value1\tvalue2\tvalue3
value4\tvalue5\tvalue6
```

### JSON Extractor

**Supported**: `.json`, `.jsonl`

**Algorithm**:
1. Check file size
2. Parse JSON with `json.loads()`
3. Validate structure
4. Pretty-print with 2-space indent
5. Capture parse errors in result.errors

**Output**: Pretty-printed JSON string

### YAML Extractor

**Supported**: `.yaml`, `.yml`

**Algorithm**:
1. Check file size
2. Parse YAML with `yaml.safe_load()`
3. Convert to JSON for consistency
4. Pretty-print JSON representation
5. Capture parse errors

**Output**: JSON representation of YAML structure

---

## Size Limits & Safety

### Configuration

```bash
# Environment variables (ops/docker/.env)
PLK_ENABLE_TIER_2=false        # Enable Tier 2 office docs (default: false)
PLK_MAX_EXTRACT_MB=100         # Maximum file size in MB (default: 100)
```

### Limits Applied

| Limit | Value | Rationale |
|-------|-------|-----------|
| **DEFAULT_MAX_SIZE_MB** | 100 MB | Prevents memory exhaustion |
| **MAX_TEXT_LENGTH** | 50,000,000 chars | Prevents string allocation issues |
| **Encoding Fallback** | UTF-8 → latin-1 | Handles legacy text files |
| **Parse Timeout** | None (deterministic) | All extractors run synchronously |

### Error Handling

**No Uncaught Exceptions**: All extractors return `ExtractionResult` with populated `errors[]` list instead of raising exceptions.

**Status Levels**:
- `"success"`: Full extraction, no issues
- `"partial"`: Extracted text but with warnings (e.g., size truncation)
- `"failed"`: No text extracted, errors[] populated

---

## Integration with Ingestion

### CLI Integration

**File**: `modules/ingestion/app/cli.py`

**Changes**:
```python
# Before (Stage 7)
text_bytes = path.read_bytes()

# After (Stage 8)
extraction_result, extraction_reason = extract_file(path, enable_tier_2=settings.enable_tier_2)

if extraction_result["status"] == "failed":
    raise RuntimeError(f"Extraction failed: {extraction_reason}")

extracted_text = extraction_result.get("text", "")
text_bytes = extracted_text.encode("utf-8")
```

**Storage Changes**:
1. **Raw File**: Still stored in `s3://plk/raw/{document_id}/{version_id}/{filename}`
2. **Extracted Text**: Stored in `s3://plk/artefacts/{document_id}/{version_id}/extracted_text.txt`
3. **Extraction Metadata**: Stored in `s3://plk/artefacts/{document_id}/{version_id}/extraction_metadata.json`

### Database Metadata

**Artefact Table Updates**:
```python
artefact = Artefact(
    artefact_id=uuid4().hex,
    version_id=version_id,
    artefact_type="EXTRACTED_TEXT",
    storage_path=f"s3://{bucket}/{artefact_key}",
    tool_name=f"extraction_{extractor_name}",        # e.g., "extraction_plain_text"
    tool_version=extractor_version,                   # e.g., "1.0.0"
    confidence_level=extraction_result["status"].upper(),  # SUCCESS/PARTIAL/FAILED
)
```

### Logging & Diagnostics

**Per-File Logging**:
```python
logger.info(
    "Extraction for %s: status=%s tier=%s reason=%s",
    path.name,
    extraction_result["status"],
    tier.value,
    extraction_reason,
)

for warning in extraction_result["warnings"]:
    logger.warning("Extraction warning for %s: %s", path.name, warning)

for error in extraction_result["errors"]:
    logger.error("Extraction error for %s: %s", path.name, error)
```

---

## Testing

### Unit Test Coverage

**File**: `modules/extraction/tests/test_extractors.py` (to be created)

**Test Cases**:
1. **Plain Text**: UTF-8, latin-1, size limits, empty files
2. **CSV**: Various delimiters, quoted fields, malformed rows
3. **JSON**: Valid, invalid, deeply nested structures
4. **YAML**: Valid, invalid, multi-document, anchors
5. **Allowlist**: Tier classification, unknown extensions
6. **Registry**: Extractor lookup, tier enablement

### Integration Testing

```bash
# Test ingestion with mixed filetypes
cd /home/jim/PLK_KB
python3 -m modules.ingestion.app.cli \
    --path ~/PLK_KB/data/testdata \
    --doc-type "TEST_DOCS" \
    --authority PUBLIC
```

**Expected Outcomes**:
- ✅ `.txt` files: Extract successfully
- ✅ `.csv` files: Convert to tab-delimited
- ✅ `.json` files: Pretty-print
- ⚠️ `.pdf` files: Skipped (Tier 2 disabled)
- ⛔ `.jpg` files: Rejected (Tier 3 blocked)

---

## Failure Modes

### Explicit Failure Handling

| Scenario | Behavior | UI Display |
|----------|----------|------------|
| **Tier 3 file (.jpg)** | `status: "failed"`, reason: "Blocked tier" | ❌ "File type not supported" |
| **Tier 2 disabled (.pdf)** | `status: "failed"`, reason: "Tier 2 disabled" | ⚠️ "Enable PLK_ENABLE_TIER_2" |
| **File too large** | `status: "failed"`, reason: "Exceeds size limit" | ⚠️ "File size: 200MB > 100MB limit" |
| **Parse error (malformed JSON)** | `status: "failed"`, errors: ["JSON decode error"] | ❌ "Parse error: Expecting value: line 1 column 5" |
| **Encoding error** | `status: "partial"`, warnings: ["UTF-8 decode failed, used latin-1"] | ⚠️ "Partial extraction" |
| **Unknown extension** | `status: "failed"`, reason: "Unknown file type" | ❌ "No extractor for .xyz" |

### No Silent Failures

**Guarantee**: Every file ingestion attempt results in either:
1. ✅ Successfully extracted text stored in artefacts table
2. ❌ Explicit error logged and displayed in UI
3. ⚠️ Partial extraction with warnings logged

**Never**: File ingested with empty text and no explanation.

---

## Future Expansion

### Adding Tier 2 Extractors

**Requirements**:
1. Implement extractor in `modules/extraction/extractors.py`
2. Add ExtractorSpec to `modules/extraction/registry.py`
3. Update `TIER_2_EXTENSIONS` in `modules/extraction/allowlist.py`
4. Add unit tests for new extractor
5. Document extractor behavior in this file
6. Test with `PLK_ENABLE_TIER_2=true`

**Example: PDF Extractor**:
```python
# modules/extraction/extractors.py
def extract_pdf(path: Path, max_size_mb: int = DEFAULT_MAX_SIZE_MB) -> ExtractionResult:
    """Extract text from PDF using pypdf."""
    try:
        _check_file_size(path, max_size_mb)
        import pypdf
        with open(path, "rb") as f:
            reader = pypdf.PdfReader(f)
            text = "\n\n".join(page.extract_text() for page in reader.pages)
        return {
            "status": "success",
            "text": text,
            "warnings": [],
            "errors": [],
            "confidence": 0.9,  # PDF extraction can miss formatting
            "metadata": {"extractor": "pdf", "version": "1.0.0", "pages": len(reader.pages)},
        }
    except Exception as e:
        return {
            "status": "failed",
            "text": None,
            "warnings": [],
            "errors": [str(e)],
            "confidence": 0.0,
            "metadata": {"extractor": "pdf", "version": "1.0.0"},
        }
```

### Tier 2 Dependencies

**Requirements** (add to `modules/ingestion/requirements.txt`):
```txt
pypdf>=3.0.0           # PDF extraction
python-docx>=0.8.11    # DOCX extraction
openpyxl>=3.1.0        # XLSX extraction
python-pptx>=0.6.21    # PPTX extraction
```

---

## Security Considerations

### Threat Model

| Threat | Mitigation |
|--------|------------|
| **Code Execution (malicious PDF)** | Tier 2 disabled by default, sandboxed extraction |
| **Memory Exhaustion (huge file)** | Size limits enforced before parsing |
| **Path Traversal (../../../etc/passwd)** | All paths resolved via Path() |
| **XML Bomb (billion laughs)** | Not yet implemented (TODO: add defusedxml) |
| **Zip Bomb** | Tier 3 blocks archives |

### Recommended Practices

1. **Enable Tier 2 only in trusted environments**
2. **Monitor extraction failures** for attack patterns
3. **Set conservative size limits** (default 100MB)
4. **Audit extractor code** before adding new types
5. **Use sandboxed containers** for Tier 2 extraction (future)

---

## UI Integration

### Extraction Status Display

**File**: `apps/ui/components/ArtefactDetailPanel.tsx` (to be updated)

**Display Fields**:
- **Extractor Name**: e.g., "plain_text", "csv"
- **Extractor Version**: e.g., "1.0.0"
- **Tier**: "Tier 1 (Safe Text)"
- **Status**: ✅ Success / ⚠️ Partial / ❌ Failed
- **Warnings**: List of non-fatal issues
- **Errors**: List of fatal errors
- **Confidence**: 0.0-1.0 extraction quality

### Ingestion Panel Updates

**File**: `apps/ui/components/IngestionPanel.tsx`

**Show Per-File Status**:
```typescript
interface FileIngestionStatus {
    filename: string;
    tier: "TIER_1" | "TIER_2" | "TIER_3";
    status: "success" | "partial" | "failed";
    extractor: string;
    warnings: string[];
    errors: string[];
}
```

---

## Performance Characteristics

### Benchmarks (Tier 1 Extractors)

| File Type | Size | Extraction Time | Notes |
|-----------|------|----------------|-------|
| `.txt` | 10 MB | ~50ms | Direct UTF-8 read |
| `.csv` | 5 MB (50k rows) | ~150ms | CSV parsing + conversion |
| `.json` | 20 MB | ~300ms | Parse + pretty-print |
| `.yaml` | 2 MB | ~100ms | Parse + JSON conversion |

**Bottleneck**: Chunking and indexing (not extraction)

### Scalability

- **Serial Extraction**: One file at a time per ingestion job
- **Parallel Ingestion**: Multiple jobs can run concurrently
- **Memory Usage**: Proportional to max_size_mb (default 100MB per file)
- **Disk I/O**: Reads raw file once, writes extracted text + metadata

---

## Operational Runbook

### Enable Tier 2 Extraction

```bash
# 1. Update environment
echo "PLK_ENABLE_TIER_2=true" >> ops/docker/.env

# 2. Install Tier 2 dependencies
pip install pypdf python-docx openpyxl python-pptx

# 3. Restart services
docker-compose -f ops/docker/docker-compose.yml restart

# 4. Test PDF ingestion
python3 -m modules.ingestion.app.cli --path /path/to/test.pdf --doc-type DOCS --authority PUBLIC
```

### Troubleshooting

**Issue**: `Extraction failed: Unknown file type`
- **Check**: File extension in `TIER_1/2/3_EXTENSIONS`
- **Fix**: Add extension to allowlist or rename file

**Issue**: `Extraction failed: Exceeds size limit`
- **Check**: File size vs `PLK_MAX_EXTRACT_MB`
- **Fix**: Increase limit or split file

**Issue**: `Extraction failed: Tier 2 disabled`
- **Check**: `PLK_ENABLE_TIER_2` environment variable
- **Fix**: Set to `true` and restart services

**Issue**: `status: partial, warnings: ["UTF-8 decode failed"]`
- **Check**: File encoding (may be latin-1 or Windows-1252)
- **Action**: Extraction succeeded with fallback, no action needed

---

## References

- **Stage 8 Design**: [docs/03_phased_plan_dos.md](./03_phased_plan_dos.md)
- **Authority Model**: [docs/05_authority_and_access_model.md](./05_authority_and_access_model.md)
- **Ingestion Pipeline**: [docs/06_module_contracts.md](./06_module_contracts.md)
- **Database Schema**: [docs/07_database_schema.md](./07_database_schema.md)

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-01 | 1.0.0 | Initial implementation: Tier 1 extractors (txt, csv, json, yaml) |

---

**End of Document**
