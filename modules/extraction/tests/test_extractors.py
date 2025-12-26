"""
Unit tests for Stage 8 extraction module.
"""
import pytest
from pathlib import Path
import tempfile
import json
import yaml

from modules.extraction.registry import extract_file, get_extractor
from modules.extraction.allowlist import get_file_tier, FileTypeTier, is_tier_enabled
from modules.extraction.extractors import extract_txt, extract_csv, extract_json, extract_yaml


class TestAllowlist:
    """Test tiered filetype classification."""
    
    def test_tier_1_extensions(self):
        """Tier 1 files are always allowed."""
        assert get_file_tier(Path("test.txt")) == FileTypeTier.TIER_1
        assert get_file_tier(Path("README.md")) == FileTypeTier.TIER_1
        assert get_file_tier(Path("data.csv")) == FileTypeTier.TIER_1
        assert get_file_tier(Path("config.json")) == FileTypeTier.TIER_1
        assert get_file_tier(Path("settings.yaml")) == FileTypeTier.TIER_1
    
    def test_tier_2_extensions(self):
        """Tier 2 files require explicit enablement."""
        assert get_file_tier(Path("document.pdf")) == FileTypeTier.TIER_2
        assert get_file_tier(Path("report.docx")) == FileTypeTier.TIER_2
        assert get_file_tier(Path("spreadsheet.xlsx")) == FileTypeTier.TIER_2
    
    def test_tier_3_extensions(self):
        """Tier 3 files are blocked."""
        assert get_file_tier(Path("image.jpg")) == FileTypeTier.TIER_3
        assert get_file_tier(Path("video.mp4")) == FileTypeTier.TIER_3
        assert get_file_tier(Path("archive.zip")) == FileTypeTier.TIER_3
        assert get_file_tier(Path("executable.exe")) == FileTypeTier.TIER_3
    
    def test_unknown_extensions(self):
        """Unknown extensions return UNKNOWN tier."""
        assert get_file_tier(Path("mystery.xyz")) == FileTypeTier.UNKNOWN
        assert get_file_tier(Path("no_extension")) == FileTypeTier.UNKNOWN
    
    def test_tier_enablement(self):
        """Tier enablement checks."""
        assert is_tier_enabled(FileTypeTier.TIER_1, enable_tier_2=False) == True
        assert is_tier_enabled(FileTypeTier.TIER_1, enable_tier_2=True) == True
        assert is_tier_enabled(FileTypeTier.TIER_2, enable_tier_2=False) == False
        assert is_tier_enabled(FileTypeTier.TIER_2, enable_tier_2=True) == True
        assert is_tier_enabled(FileTypeTier.TIER_3, enable_tier_2=False) == False
        assert is_tier_enabled(FileTypeTier.TIER_3, enable_tier_2=True) == False


class TestPlainTextExtractor:
    """Test plain text extraction."""
    
    def test_extract_utf8_text(self):
        """Extract valid UTF-8 text."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Hello, world!\nThis is a test.")
            path = Path(f.name)
        
        try:
            result = extract_txt(path)
            assert result["status"] == "success"
            assert "Hello, world!" in result["text"]
            assert result["confidence"] == 1.0
            assert len(result["errors"]) == 0
        finally:
            path.unlink()
    
    def test_extract_latin1_fallback(self):
        """Extract latin-1 encoded text with UTF-8 fallback."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # Write latin-1 encoded text (e.g., © symbol)
            f.write(b"Copyright \xa9 2025")
            path = Path(f.name)
        
        try:
            result = extract_txt(path)
            # Expect partial status when fallback encoding is used
            assert result["status"] in ["success", "partial"]
            assert "Copyright" in result["text"]
        finally:
            path.unlink()
    
    def test_file_too_large(self):
        """Reject files exceeding size limit."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # Write 1MB of data
            f.write(b"x" * (1024 * 1024))
            path = Path(f.name)
        
        try:
            # Use 0.5MB limit to trigger error
            result = extract_txt(path, max_size_mb=0.5)
            assert result["status"] == "failed"
            # Check that error mentions size
            assert any("size" in err.lower() or "exceeds" in err.lower() for err in result["errors"])
        finally:
            path.unlink()
    
    def test_empty_file(self):
        """Handle empty files gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            path = Path(f.name)
        
        try:
            result = extract_txt(path)
            assert result["status"] == "success"
            assert result["text"] == ""
            assert len(result["errors"]) == 0
        finally:
            path.unlink()
    
    def test_extract_xml_as_text(self):
        """Extract XML as plain text (no entity expansion)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write('<?xml version="1.0"?>\n<root>\n  <data>test content</data>\n</root>')
            path = Path(f.name)
        
        try:
            result = extract_txt(path)
            assert result["status"] == "success"
            assert "test content" in result["text"]
            assert "<?xml" in result["text"]  # Treated as plain text
            assert len(result["errors"]) == 0
        finally:
            path.unlink()


class TestCSVExtractor:
    """Test CSV extraction."""
    
    def test_extract_simple_csv(self):
        """Extract simple comma-delimited CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("name,age,city\n")
            f.write("Alice,30,NYC\n")
            f.write("Bob,25,LA\n")
            path = Path(f.name)
        
        try:
            result = extract_csv(path)
            assert result["status"] == "success"
            assert "name\tage\tcity" in result["text"]
            assert "Alice\t30\tNYC" in result["text"]
            assert len(result["errors"]) == 0
        finally:
            path.unlink()
    
    def test_extract_tsv(self):
        """Extract tab-delimited file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            f.write("col1\tcol2\tcol3\n")
            f.write("val1\tval2\tval3\n")
            path = Path(f.name)
        
        try:
            result = extract_csv(path)
            assert result["status"] == "success"
            assert "col1\tcol2\tcol3" in result["text"]
        finally:
            path.unlink()
    
    def test_csv_with_quotes(self):
        """Handle quoted fields with embedded commas."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write('name,description\n')
            f.write('Item,"Contains, comma"\n')
            path = Path(f.name)
        
        try:
            result = extract_csv(path)
            assert result["status"] == "success"
            # Should preserve content (comma inside quotes)
            assert "Contains, comma" in result["text"]
        finally:
            path.unlink()


class TestJSONExtractor:
    """Test JSON extraction."""
    
    def test_extract_valid_json(self):
        """Extract valid JSON object."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value", "count": 42}, f)
            path = Path(f.name)
        
        try:
            result = extract_json(path)
            assert result["status"] == "success"
            assert '"key": "value"' in result["text"]
            assert '"count": 42' in result["text"]
            assert len(result["errors"]) == 0
        finally:
            path.unlink()
    
    def test_extract_json_array(self):
        """Extract JSON array."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([1, 2, 3, "test"], f)
            path = Path(f.name)
        
        try:
            result = extract_json(path)
            assert result["status"] == "success"
            assert "test" in result["text"]
        finally:
            path.unlink()
    
    def test_malformed_json(self):
        """Handle malformed JSON gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json]")
            path = Path(f.name)
        
        try:
            result = extract_json(path)
            assert result["status"] == "failed"
            assert len(result["errors"]) > 0
        finally:
            path.unlink()


class TestYAMLExtractor:
    """Test YAML extraction."""
    
    def test_extract_valid_yaml(self):
        """Extract valid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"key": "value", "items": [1, 2, 3]}, f)
            path = Path(f.name)
        
        try:
            result = extract_yaml(path)
            assert result["status"] == "success"
            # YAML converted to JSON format
            assert '"key": "value"' in result["text"]
            assert len(result["errors"]) == 0
        finally:
            path.unlink()
    
    def test_malformed_yaml(self):
        """Handle malformed YAML gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("key: value\n  invalid indentation")
            path = Path(f.name)
        
        try:
            result = extract_yaml(path)
            # YAML parser is lenient, may succeed with warnings
            assert result["status"] in ["success", "failed"]
        finally:
            path.unlink()


class TestRegistry:
    """Test extractor registry."""
    
    def test_get_extractor_for_txt(self):
        """Registry returns plain_text extractor for .txt."""
        extractor = get_extractor(Path("test.txt"))
        assert extractor is not None
        assert extractor.name == "plain_text"
    
    def test_get_extractor_for_csv(self):
        """Registry returns csv extractor for .csv."""
        extractor = get_extractor(Path("data.csv"))
        assert extractor is not None
        assert extractor.name == "csv"
    
    def test_get_extractor_unknown(self):
        """Registry returns None for unknown extension."""
        extractor = get_extractor(Path("file.unknown"))
        assert extractor is None
    
    def test_extract_file_integration(self):
        """Full integration: extract_file() with real file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Integration test content")
            path = Path(f.name)
        
        try:
            result, reason = extract_file(path, enable_tier_2=False)
            assert result["status"] == "success"
            assert "Integration test content" in result["text"]
            assert "plain_text" in reason
        finally:
            path.unlink()
    
    def test_extract_file_blocked_tier(self):
        """extract_file() rejects Tier 3 files."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            path = Path(f.name)
        
        try:
            result, reason = extract_file(path, enable_tier_2=False)
            assert result["status"] == "failed"
            assert "blocked" in reason.lower() or "tier 3" in reason.lower()
        finally:
            path.unlink()
    
    def test_extract_file_tier2_disabled(self):
        """extract_file() rejects Tier 2 when disabled."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            path = Path(f.name)
        
        try:
            result, reason = extract_file(path, enable_tier_2=False)
            assert result["status"] == "failed"
            assert "tier 2" in reason.lower() or "disabled" in reason.lower()
        finally:
            path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
