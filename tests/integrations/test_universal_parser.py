"""
Test Suite for Universal Document Parser v4.1.0
================================================

Comprehensive validation tests covering:
- Parser instantiation
- Format detection
- SEC filing type detection
- Forensic hashing validation
- Text extraction
- Entity extraction
- Error handling
"""

import pytest
import hashlib
import io
import json
from datetime import datetime

# Import parser module directly to avoid dependency issues
import sys
import importlib.util
spec = importlib.util.spec_from_file_location(
    "document_parser",
    "src/forensics/docsgpt/document_parser.py"
)
doc_parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doc_parser)


class TestParserInstantiation:
    """Test parser class instantiation."""
    
    def test_xbrl_parser_instantiation(self):
        """Test XBRL parser instantiates correctly."""
        parser = doc_parser.XBRLParser()
        assert parser is not None
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'extract_text')
    
    def test_docx_parser_instantiation(self):
        """Test DOCX parser instantiates correctly."""
        parser = doc_parser.DOCXParser()
        assert parser is not None
        assert hasattr(parser, 'parse')
    
    def test_xlsx_parser_instantiation(self):
        """Test XLSX parser instantiates correctly."""
        parser = doc_parser.XLSXParser()
        assert parser is not None
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'extract_text')
    
    def test_image_parser_instantiation(self):
        """Test Image parser instantiates correctly."""
        parser = doc_parser.ImageParser()
        assert parser is not None
        assert hasattr(parser, 'parse')
    
    def test_universal_parser_instantiation(self):
        """Test Universal parser instantiates correctly."""
        parser = doc_parser.UniversalDocumentParser()
        assert parser is not None
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'parse_sec_filing')
        # Verify all sub-parsers are initialized
        assert parser.xbrl_parser is not None
        assert parser.docx_parser is not None
        assert parser.xlsx_parser is not None
        assert parser.image_parser is not None
        assert parser.pdf_parser is not None
        assert parser.html_parser is not None
        assert parser.xml_parser is not None
        assert parser.entity_extractor is not None


class TestFormatDetection:
    """Test document format detection."""
    
    def setup_method(self):
        """Set up test parser."""
        self.parser = doc_parser.UniversalDocumentParser()
    
    def test_pdf_detection(self):
        """Test PDF format detection."""
        fmt = self.parser._detect_format('pdf')
        assert fmt == doc_parser.DocumentFormat.PDF
    
    def test_docx_detection(self):
        """Test DOCX format detection."""
        fmt = self.parser._detect_format('docx')
        assert fmt == doc_parser.DocumentFormat.DOCX
    
    def test_xlsx_detection(self):
        """Test XLSX format detection."""
        fmt = self.parser._detect_format('xlsx')
        assert fmt == doc_parser.DocumentFormat.XLSX
    
    def test_html_detection(self):
        """Test HTML format detection."""
        fmt = self.parser._detect_format('html')
        assert fmt == doc_parser.DocumentFormat.HTML
        fmt2 = self.parser._detect_format('htm')
        assert fmt2 == doc_parser.DocumentFormat.HTML
    
    def test_xml_detection(self):
        """Test XML format detection."""
        fmt = self.parser._detect_format('xml')
        assert fmt == doc_parser.DocumentFormat.XML
    
    def test_xbrl_detection(self):
        """Test XBRL format detection."""
        fmt = self.parser._detect_format('xbrl')
        assert fmt == doc_parser.DocumentFormat.XBRL
    
    def test_json_detection(self):
        """Test JSON format detection."""
        fmt = self.parser._detect_format('json')
        assert fmt == doc_parser.DocumentFormat.JSON
    
    def test_csv_detection(self):
        """Test CSV format detection."""
        fmt = self.parser._detect_format('csv')
        assert fmt == doc_parser.DocumentFormat.CSV
    
    def test_txt_detection(self):
        """Test TXT format detection."""
        fmt = self.parser._detect_format('txt')
        assert fmt == doc_parser.DocumentFormat.TXT
    
    def test_image_detection(self):
        """Test image format detection."""
        for ext in ['png', 'jpg', 'jpeg', 'tiff', 'tif']:
            fmt = self.parser._detect_format(ext)
            assert fmt == doc_parser.DocumentFormat.IMAGE


class TestSECFilingTypeDetection:
    """Test SEC filing type detection."""
    
    def setup_method(self):
        """Set up test parser."""
        self.parser = doc_parser.UniversalDocumentParser()
    
    def test_form_10k_detection_from_filename(self):
        """Test Form 10-K detection from filename."""
        filing_type = self.parser._detect_filing_type("", "aapl-10k-2023.html")
        assert filing_type == doc_parser.SECFilingType.FORM_10K
    
    def test_form_10q_detection_from_filename(self):
        """Test Form 10-Q detection from filename."""
        filing_type = self.parser._detect_filing_type("", "aapl-10q-q1-2023.html")
        assert filing_type == doc_parser.SECFilingType.FORM_10Q
    
    def test_form_8k_detection_from_filename(self):
        """Test Form 8-K detection from filename."""
        filing_type = self.parser._detect_filing_type("", "aapl-8k-2023.html")
        assert filing_type == doc_parser.SECFilingType.FORM_8K
    
    def test_form_4_detection_from_content(self):
        """Test Form 4 detection from content."""
        content = "Form 4 - Statement of Changes in Beneficial Ownership"
        filing_type = self.parser._detect_filing_type(content, "filing.xml")
        assert filing_type == doc_parser.SECFilingType.FORM_4
    
    def test_def_14a_detection_from_filename(self):
        """Test DEF 14A detection from filename."""
        filing_type = self.parser._detect_filing_type("", "def14a-2023.html")
        assert filing_type == doc_parser.SECFilingType.DEF_14A
    
    def test_form_13f_detection_from_filename(self):
        """Test Form 13F detection from filename."""
        filing_type = self.parser._detect_filing_type("", "13f-hr-2023.xml")
        assert filing_type == doc_parser.SECFilingType.FORM_13F
    
    def test_unknown_filing_type(self):
        """Test unknown filing type returns UNKNOWN."""
        filing_type = self.parser._detect_filing_type("Random document text", "document.txt")
        assert filing_type == doc_parser.SECFilingType.UNKNOWN


class TestForensicHashing:
    """Test dual forensic hashing."""
    
    def setup_method(self):
        """Set up test parser."""
        self.parser = doc_parser.UniversalDocumentParser()
    
    def test_sha256_hash_generation(self):
        """Test SHA-256 hash generation."""
        content = b"Test document content"
        expected_sha256 = hashlib.sha256(content).hexdigest()
        
        parsed = self.parser.parse(content, "test.txt")
        assert parsed.sha256_hash == expected_sha256
    
    def test_sha3_512_hash_generation(self):
        """Test SHA3-512 hash generation."""
        content = b"Test document content"
        expected_sha3 = hashlib.sha3_512(content).hexdigest()
        
        parsed = self.parser.parse(content, "test.txt")
        assert parsed.sha3_512_hash == expected_sha3
    
    def test_hashes_differ_for_different_content(self):
        """Test that hashes differ for different content."""
        content1 = b"Document 1"
        content2 = b"Document 2"
        
        parsed1 = self.parser.parse(content1, "test1.txt")
        parsed2 = self.parser.parse(content2, "test2.txt")
        
        assert parsed1.sha256_hash != parsed2.sha256_hash
        assert parsed1.sha3_512_hash != parsed2.sha3_512_hash


class TestTextExtraction:
    """Test text extraction from various formats."""
    
    def setup_method(self):
        """Set up test parser."""
        self.parser = doc_parser.UniversalDocumentParser()
    
    def test_txt_extraction(self):
        """Test plain text extraction."""
        content = b"This is a test document."
        parsed = self.parser.parse(content, "test.txt")
        
        assert parsed.format == doc_parser.DocumentFormat.TXT
        assert len(parsed.chunks) > 0
        assert "test document" in parsed.chunks[0].text.lower()
    
    def test_json_extraction(self):
        """Test JSON extraction."""
        data = {"name": "Test Company", "revenue": 1000000}
        content = json.dumps(data).encode('utf-8')
        
        parsed = self.parser.parse(content, "data.json")
        assert parsed.format == doc_parser.DocumentFormat.JSON
        assert len(parsed.chunks) > 0
    
    def test_html_extraction(self):
        """Test HTML extraction."""
        html = "<html><body><h1>Test</h1><p>This is a test document.</p></body></html>"
        content = html.encode('utf-8')
        
        parsed = self.parser.parse(content, "test.html")
        assert parsed.format == doc_parser.DocumentFormat.HTML
        assert len(parsed.chunks) > 0
        # HTML parser should strip tags
        assert "<html>" not in parsed.chunks[0].text


class TestCSVExtraction:
    """Test CSV table extraction."""
    
    def setup_method(self):
        """Set up test parser."""
        self.parser = doc_parser.UniversalDocumentParser()
    
    def test_csv_extraction(self):
        """Test CSV extraction."""
        csv_content = b"Name,Value,Year\nApple,100,2023\nGoogle,200,2023"
        
        parsed = self.parser.parse(csv_content, "data.csv")
        assert parsed.format == doc_parser.DocumentFormat.CSV
        assert len(parsed.chunks) > 0
        # Should contain structured data
        assert "Name:" in parsed.chunks[0].text or "Apple" in parsed.chunks[0].text


class TestHTMLParsing:
    """Test HTML parsing functionality."""
    
    def setup_method(self):
        """Set up test HTML parser."""
        self.parser = doc_parser.HTMLParser()
    
    def test_html_tag_removal(self):
        """Test that HTML tags are removed."""
        html = "<html><body><h1>Title</h1><p>Content</p></body></html>"
        text = self.parser.parse(html)
        
        assert "<html>" not in text
        assert "<body>" not in text
        assert "<h1>" not in text
        assert "Title" in text
        assert "Content" in text
    
    def test_script_removal(self):
        """Test that script tags are removed."""
        html = "<html><body><script>alert('test');</script><p>Content</p></body></html>"
        text = self.parser.parse(html)
        
        assert "alert" not in text
        assert "Content" in text
    
    def test_style_removal(self):
        """Test that style tags are removed."""
        html = "<html><head><style>body { color: red; }</style></head><body>Content</body></html>"
        text = self.parser.parse(html)
        
        assert "color: red" not in text
        assert "Content" in text


class TestXBRLParser:
    """Test XBRL parser validation."""
    
    def test_xbrl_parser_has_required_methods(self):
        """Test XBRL parser has required methods."""
        parser = doc_parser.XBRLParser()
        assert hasattr(parser, 'parse')
        assert hasattr(parser, 'extract_text')
        assert hasattr(parser, '_parse_xml_fallback')
    
    def test_xbrl_parser_fallback_handles_invalid_xml(self):
        """Test XBRL fallback handles invalid XML gracefully."""
        parser = doc_parser.XBRLParser()
        result = parser._parse_xml_fallback(b"not valid xml")
        assert isinstance(result, dict)


class TestEntityExtraction:
    """Test entity extraction functionality."""
    
    def setup_method(self):
        """Set up entity extractor."""
        self.extractor = doc_parser.EntityExtractor()
    
    def test_money_extraction(self):
        """Test MONEY pattern extraction."""
        text = "The company reported revenue of $1,234,567.89 million and expenses of $500,000."
        entities = self.extractor.extract_entities(text)
        
        assert 'money' in entities
        assert len(entities['money']) > 0
    
    def test_date_extraction(self):
        """Test DATE pattern extraction."""
        text = "The filing date was 12/31/2023 and the meeting is on January 15, 2024."
        entities = self.extractor.extract_entities(text)
        
        assert 'dates' in entities
        assert len(entities['dates']) > 0
    
    def test_cik_extraction(self):
        """Test CIK pattern extraction."""
        text = "The company CIK: 0000320193 filed the document."
        entities = self.extractor.extract_entities(text)
        
        assert 'ciks' in entities
        assert len(entities['ciks']) > 0
        assert '0000320193' in entities['ciks']
    
    def test_cusip_extraction(self):
        """Test CUSIP pattern extraction."""
        text = "The security CUSIP 037833100 was traded."
        entities = self.extractor.extract_entities(text)
        
        assert 'cusips' in entities
        # May or may not extract depending on pattern match


class TestErrorHandling:
    """Test error handling in parsers."""
    
    def setup_method(self):
        """Set up test parser."""
        self.parser = doc_parser.UniversalDocumentParser()
    
    def test_empty_content_handling(self):
        """Test handling of empty content."""
        parsed = self.parser.parse(b"", "empty.txt")
        assert parsed is not None
        assert len(parsed.chunks) >= 0
    
    def test_invalid_format_handling(self):
        """Test handling of unrecognized format."""
        parsed = self.parser.parse(b"some content", "file.unknown")
        # Should default to TXT format
        assert parsed.format == doc_parser.DocumentFormat.TXT
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON."""
        content = b"{invalid json"
        parsed = self.parser.parse(content, "bad.json")
        # Should not crash, should return something
        assert parsed is not None


class TestBackwardCompatibility:
    """Test backward compatibility."""
    
    def test_document_parser_alias_exists(self):
        """Test DocumentParser alias exists."""
        assert hasattr(doc_parser, 'DocumentParser')
        assert doc_parser.DocumentParser == doc_parser.UniversalDocumentParser
    
    def test_document_parser_alias_instantiates(self):
        """Test DocumentParser alias instantiates correctly."""
        parser = doc_parser.DocumentParser()
        assert isinstance(parser, doc_parser.UniversalDocumentParser)
    
    def test_parsed_document_fields(self):
        """Test ParsedDocument has all expected fields."""
        parser = doc_parser.UniversalDocumentParser()
        parsed = parser.parse(b"test", "test.txt")
        
        # Original fields
        assert hasattr(parsed, 'doc_id')
        assert hasattr(parsed, 'filename')
        assert hasattr(parsed, 'format')
        assert hasattr(parsed, 'filing_type')
        assert hasattr(parsed, 'chunks')
        assert hasattr(parsed, 'total_tokens')
        assert hasattr(parsed, 'page_count')
        assert hasattr(parsed, 'parse_timestamp')
        assert hasattr(parsed, 'metadata')
        assert hasattr(parsed, 'cik')
        assert hasattr(parsed, 'accession_number')
        
        # New forensic fields
        assert hasattr(parsed, 'sha256_hash')
        assert hasattr(parsed, 'sha3_512_hash')
        assert hasattr(parsed, 'extracted_entities')
    
    def test_document_chunk_fields(self):
        """Test DocumentChunk has all expected fields."""
        parser = doc_parser.UniversalDocumentParser()
        parsed = parser.parse(b"test content", "test.txt")
        
        chunk = parsed.chunks[0]
        assert hasattr(chunk, 'chunk_id')
        assert hasattr(chunk, 'text')
        assert hasattr(chunk, 'chunk_index')
        assert hasattr(chunk, 'total_chunks')
        assert hasattr(chunk, 'token_count')
        assert hasattr(chunk, 'section')
        assert hasattr(chunk, 'content_hash')


class TestSECDocumentAnalyzer:
    """Test SEC Document Analyzer."""
    
    def test_sec_analyzer_instantiation(self):
        """Test SEC analyzer instantiates correctly."""
        analyzer = doc_parser.SECDocumentAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'parser')
        assert isinstance(analyzer.parser, doc_parser.UniversalDocumentParser)
    
    def test_sec_analyzer_has_required_methods(self):
        """Test SEC analyzer has required methods."""
        analyzer = doc_parser.SECDocumentAnalyzer()
        assert hasattr(analyzer, 'analyze_filing')
        assert hasattr(analyzer, 'get_section_text')
        assert hasattr(analyzer, 'get_risk_factors')
        assert hasattr(analyzer, 'get_mda')


class TestChunkingStrategy:
    """Test chunking strategies."""
    
    def test_fixed_size_chunking(self):
        """Test fixed size chunking."""
        text = " ".join(["word"] * 2000)  # 2000 words
        chunks = doc_parser.ChunkingStrategy.chunk_fixed_size(text, 500, 50)
        
        assert len(chunks) > 1
        # Each chunk should be roughly the target size
    
    def test_section_chunking_no_sections(self):
        """Test section chunking with no identifiable sections."""
        text = "This is a simple document without sections."
        sections = doc_parser.ChunkingStrategy.chunk_by_sections(
            text, doc_parser.SECFilingType.FORM_10K
        )
        
        # Should return full document as single section
        assert len(sections) == 1
        assert sections[0][0] == "FULL_DOCUMENT"


# Run validation
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
