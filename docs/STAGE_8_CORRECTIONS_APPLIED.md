# Stage 8 Corrections Applied

**Date**: December 26, 2025

## Required Corrections (All Applied)

### 1️⃣ Classification Semantics Clarification ✅

**Added to both documents**:
> **Important**: File tiers are an extraction concern only. They do not imply clearance hierarchy. Classification checks elsewhere in the system remain equality-based, not "greater-than".

**Location**:
- [STAGE_8_QUICK_REFERENCE.md](./STAGE_8_QUICK_REFERENCE.md) - After "Status Meanings"
- [11_stage_8_extraction_and_filetypes.md](./11_stage_8_extraction_and_filetypes.md) - Before "Tier 1" section

**Prevents**: Future developers assuming "Tier 2 can read Tier 1" logic

---

### 2️⃣ XML Handling Explicit Documentation ✅

**Added explicit XML handling**:
- Extractor: `plain_text`
- Algorithm: Raw text read (UTF-8)
- **No entity expansion**
- **No schema validation**

**Updated Files**:
- [allowlist.py](../modules/extraction/allowlist.py): Added `.xml` to `TIER_1_EXTENSIONS`
- [registry.py](../modules/extraction/registry.py): Added `.xml` to plain_text extractor extensions
- [test_extractors.py](../modules/extraction/tests/test_extractors.py): Added `test_extract_xml_as_text()`
- Both documentation files: Added XML row with explicit "no entity expansion" note

**Security Rationale**: Prevents XXE (XML External Entity) attacks by treating XML as plain text

**Verification**:
```bash
$ python3 -m pytest modules/extraction/tests/test_extractors.py::TestPlainTextExtractor::test_extract_xml_as_text -v
============================== 1 passed in 0.03s ===============================
```

---

### 3️⃣ Confidence Semantics Definition ✅

**Added to ExtractionResult Contract section**:
> **Note**: `confidence` is informational only and is not used for gating access or indexing decisions in Stage 8.

**Location**:
- [STAGE_8_QUICK_REFERENCE.md](./STAGE_8_QUICK_REFERENCE.md) - After ExtractionResult contract
- [11_stage_8_extraction_and_filetypes.md](./11_stage_8_extraction_and_filetypes.md) - After ExtractionResult TypedDict

**Prevents**: Premature coupling to authority or ranking logic

---

### 4️⃣ Tier 3 Metadata-Only Behavior Clarification ✅

**Added to Tier 3 section**:
> **Tier 3 Metadata Handling**: Tier 3 files may be registered as artefacts with metadata only, but:
> - No text extraction
> - No chunking
> - No indexing

**Location**:
- [STAGE_8_QUICK_REFERENCE.md](./STAGE_8_QUICK_REFERENCE.md) - After Tier 3 extensions list
- [11_stage_8_extraction_and_filetypes.md](./11_stage_8_extraction_and_filetypes.md) - After TIER_3_EXTENSIONS definition

**Aligns**: With artefact transparency goals while maintaining extraction boundaries

---

### 5️⃣ Naming Consistency (Deferred)

**Status**: Not yet applied - requires broader codebase audit

**Recommendation**: Use `created_at (UTC)` consistently throughout:
- Database schema comments
- API response field names
- UI display labels
- Log timestamps

**Scope**: Affects multiple modules beyond extraction (ingestion, metadata, API)

**Next Step**: Create separate ticket for global naming standardization pass

---

## Updated Support Matrix

| Extension | Extractor | Tier | Notes |
|-----------|-----------|------|-------|
| `.txt`, `.md`, `.log`, `.rtf` | plain_text | 1 | UTF-8 with latin-1 fallback |
| `.xml` | plain_text | 1 | **No entity expansion, no schema validation** |
| `.csv`, `.tsv` | csv | 1 | Converts to tab-delimited |
| `.json` | json | 1 | Validates + pretty-prints |
| `.yaml`, `.yml` | yaml | 1 | Converts to JSON |

Total Tier 1 extensions: **10**

---

## Test Coverage Update

```bash
$ python3 -m pytest modules/extraction/tests/test_extractors.py -v
============================== 24 passed in 0.04s ===============================
```

**New Test**: `test_extract_xml_as_text()` verifies XML treated as plain text

---

## Documentation Files Updated

1. ✅ [docs/STAGE_8_QUICK_REFERENCE.md](./STAGE_8_QUICK_REFERENCE.md)
   - Added classification semantics note
   - Added XML handling row
   - Added confidence semantics note
   - Added Tier 3 metadata behavior

2. ✅ [docs/11_stage_8_extraction_and_filetypes.md](./11_stage_8_extraction_and_filetypes.md)
   - Added classification semantics warning
   - Added XML handling explanation with security note
   - Added confidence semantics definition
   - Added Tier 3 metadata handling clarification

3. ✅ [modules/extraction/allowlist.py](../modules/extraction/allowlist.py)
   - Added `.xml` to `TIER_1_EXTENSIONS` with comment

4. ✅ [modules/extraction/registry.py](../modules/extraction/registry.py)
   - Added `.xml` to plain_text extractor extensions

5. ✅ [modules/extraction/tests/test_extractors.py](../modules/extraction/tests/test_extractors.py)
   - Added `test_extract_xml_as_text()`

---

## Verification Commands

```bash
# 1. Verify .xml is Tier 1
python3 -c "from modules.extraction.allowlist import get_file_tier; from pathlib import Path; print(get_file_tier(Path('test.xml')))"
# Output: FileTypeTier.TIER_1

# 2. Test XML extraction
python3 -c "from modules.extraction.registry import extract_file; from pathlib import Path; import tempfile; f = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False); f.write('<?xml version=\"1.0\"?><data>test</data>'); f.close(); result, _ = extract_file(Path(f.name)); print(f'Status: {result[\"status\"]}, Has XML tag: {\"<?xml\" in result[\"text\"]}')"
# Output: Status: success, Has XML tag: True

# 3. Run all extraction tests
python3 -m pytest modules/extraction/tests/test_extractors.py -v
# Output: 24 passed in 0.04s
```

---

## Optional Enhancements (Not Yet Implemented)

These are nice-to-have but not required:

### Decision Tree Diagram
```
File → Check Extension → Get Tier → Check Enablement
                                        ↓
                                 Tier 1? → Always extract
                                 Tier 2? → Check PLK_ENABLE_TIER_2
                                 Tier 3? → Register metadata only
                                 Unknown? → Reject with reason
```

### "Why Not Auto-Detect MIME?" Sidebar

**Q**: Why use file extensions instead of MIME detection?

**A**: 
1. **Determinism**: Same filename always routes to same extractor
2. **Performance**: No file I/O or magic number checks before extraction
3. **Security**: User-provided MIME types are untrustworthy
4. **Simplicity**: Extension mapping is explicit and auditable
5. **Unix Philosophy**: Trust the user's declared file type (but validate content)

Future enhancement: Add optional MIME validation as a post-extraction sanity check.

---

## Breaking Changes

**None** - All corrections are additive or clarifications:
- `.xml` support is new, doesn't affect existing files
- Documentation clarifications don't change behavior
- Tier 3 metadata handling was always the intended behavior

---

## Changelog Entry

```markdown
### [1.0.1] - 2025-12-26

#### Added
- `.xml` support as Tier 1 (plain text, no entity expansion)
- `test_extract_xml_as_text()` test case

#### Clarified
- File tiers are extraction-only, not clearance hierarchy
- XML handling explicitly documented (no entity expansion)
- `confidence` is informational only, not used for access gating
- Tier 3 files may have metadata-only artefacts (no extraction)

#### Fixed
- Documentation consistency across quick reference and comprehensive doc
```

---

**Status**: All required corrections applied and verified ✅

**Next**: Ready for Stage 9 (UI Polish & Error Handling)
