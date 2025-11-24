"""
Unit tests for Universal Document Extraction System.
Tests multi-format document parsing with forensic precision.
"""

import pytest
import asyncio
from typing import Dict, Any

from src.forensics.sec_forensic_extraction_system import (
    UniversalDocumentExtractor,
    ForensicSECDocumentAnalyzer,
    DocumentFormat,
    ExtractionResult,
    FinancialMetrics,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def html_document():
    """Sample HTML document with financial data and tables."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Annual Report 2023</title>
        <meta name="company" content="Test Corp">
    </head>
    <body>
        <h1>Financial Statements</h1>
        <p>Revenue: $1,000,000</p>
        <p>Net Income: $150,000</p>
        <p>Total Assets: $5,000,000</p>
        <table>
            <thead>
                <tr><th>Year</th><th>Revenue</th><th>Earnings</th></tr>
            </thead>
            <tbody>
                <tr><td>2023</td><td>$1.0M</td><td>$150K</td></tr>
                <tr><td>2022</td><td>$900K</td><td>$120K</td></tr>
            </tbody>
        </table>
    </body>
    </html>
    """


@pytest.fixture
def xml_document():
    """Sample XML document."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <filing>
        <header>
            <company>Test Corporation</company>
            <cik>0001234567</cik>
            <filing_date>2024-01-15</filing_date>
        </header>
        <financial_data>
            <revenue>1000000</revenue>
            <expenses>850000</expenses>
            <net_income>150000</net_income>
        </financial_data>
    </filing>
    """


@pytest.fixture
def xbrl_document():
    """Sample XBRL document with financial data."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <xbrl xmlns="http://www.xbrl.org/2003/instance"
          xmlns:us-gaap="http://fasb.org/us-gaap/2023">
        <context id="current_year">
            <entity>
                <identifier scheme="http://www.sec.gov/CIK">0001234567</identifier>
            </entity>
            <period>
                <instant>2023-12-31</instant>
            </period>
        </context>
        <us-gaap:Revenue contextRef="current_year" unitRef="USD" decimals="-3">
            1000000
        </us-gaap:Revenue>
        <us-gaap:NetIncomeLoss contextRef="current_year" unitRef="USD" decimals="-3">
            150000
        </us-gaap:NetIncomeLoss>
    </xbrl>
    """


@pytest.fixture
def sgml_document():
    """Sample SGML SEC document."""
    return """<SEC-DOCUMENT>
<SEC-HEADER>
COMPANY CONFORMED NAME: TEST CORPORATION
CENTRAL INDEX KEY: 0001234567
FILING DATE: 20240101
FORM TYPE: 10-K
</SEC-HEADER>
<DOCUMENT>
<TYPE>10-K
<SEQUENCE>1
<FILENAME>test-10k.htm
<TEXT>
<HTML>
<HEAD><TITLE>Annual Report</TITLE></HEAD>
<BODY>
<H1>Management Discussion and Analysis</H1>
<P>Revenue increased by 15% year-over-year to $1,000,000.</P>
<P>Risk Factors: Market volatility may impact results.</P>
</BODY>
</HTML>
</TEXT>
</DOCUMENT>
</SEC-DOCUMENT>
"""


@pytest.fixture
def plain_text_document():
    """Sample plain text document."""
    return """
    ANNUAL REPORT 2023
    
    FINANCIAL HIGHLIGHTS:
    - Revenue: $1,000,000
    - Net Income: $150,000
    - Cash Flow: $200,000
    
    BUSINESS OVERVIEW:
    The company operates in three segments...
    """


# ============================================================================
# TESTS - Format Detection
# ============================================================================

@pytest.mark.asyncio
async def test_detect_html_format():
    """Test HTML format detection."""
    extractor = UniversalDocumentExtractor()
    
    html_content = "<!DOCTYPE html><html><body>Test</body></html>"
    detected_format = extractor.detect_format(html_content)
    
    assert detected_format == DocumentFormat.HTML


@pytest.mark.asyncio
async def test_detect_xml_format():
    """Test XML format detection."""
    extractor = UniversalDocumentExtractor()
    
    xml_content = '<?xml version="1.0"?><root><data>test</data></root>'
    detected_format = extractor.detect_format(xml_content)
    
    assert detected_format == DocumentFormat.XML


@pytest.mark.asyncio
async def test_detect_xbrl_format():
    """Test XBRL format detection."""
    extractor = UniversalDocumentExtractor()
    
    xbrl_content = '<?xml version="1.0"?><xbrl xmlns="http://www.xbrl.org/2003/instance"></xbrl>'
    detected_format = extractor.detect_format(xbrl_content)
    
    assert detected_format == DocumentFormat.XBRL


@pytest.mark.asyncio
async def test_detect_sgml_format():
    """Test SGML format detection."""
    extractor = UniversalDocumentExtractor()
    
    sgml_content = "<SEC-DOCUMENT><SEC-HEADER>test</SEC-HEADER></SEC-DOCUMENT>"
    detected_format = extractor.detect_format(sgml_content)
    
    assert detected_format == DocumentFormat.SGML


@pytest.mark.asyncio
async def test_detect_format_from_url():
    """Test format detection from URL."""
    extractor = UniversalDocumentExtractor()
    
    content = "Some content"
    
    # Test .xml URL
    detected = extractor.detect_format(content, url="https://example.com/doc.xml")
    assert detected == DocumentFormat.XML
    
    # Test .html URL
    detected = extractor.detect_format(content, url="https://example.com/doc.html")
    assert detected == DocumentFormat.HTML


# ============================================================================
# TESTS - HTML Extraction
# ============================================================================

@pytest.mark.asyncio
async def test_extract_html_document(html_document):
    """Test HTML document extraction with tables."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(html_document, url="test.html")
    
    assert result.format == DocumentFormat.HTML
    assert result.confidence >= 0.90
    assert "Financial Statements" in result.content
    assert "Revenue: $1,000,000" in result.content
    assert len(result.tables) == 1
    assert result.tables[0]['row_count'] == 2
    assert result.content_hash != ""
    assert result.url == "test.html"


@pytest.mark.asyncio
async def test_extract_html_metadata(html_document):
    """Test HTML metadata extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(html_document)
    
    assert 'title' in result.metadata
    assert result.metadata['title'] == "Annual Report 2023"
    assert 'company' in result.metadata
    assert result.metadata['company'] == "Test Corp"


@pytest.mark.asyncio
async def test_extract_html_table_structure(html_document):
    """Test HTML table structure extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(html_document)
    
    assert len(result.tables) == 1
    table = result.tables[0]
    assert 'headers' in table
    assert 'rows' in table
    assert len(table['headers']) == 3
    assert table['headers'] == ['Year', 'Revenue', 'Earnings']


# ============================================================================
# TESTS - XML Extraction
# ============================================================================

@pytest.mark.asyncio
async def test_extract_xml_document(xml_document):
    """Test XML document extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(xml_document, url="test.xml")
    
    assert result.format == DocumentFormat.XML
    assert result.confidence >= 0.85
    assert "Test Corporation" in result.content
    assert "0001234567" in result.content
    assert "1000000" in result.content


# ============================================================================
# TESTS - XBRL Extraction
# ============================================================================

@pytest.mark.asyncio
async def test_extract_xbrl_document(xbrl_document):
    """Test XBRL document extraction with financial data."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(xbrl_document)
    
    assert result.format == DocumentFormat.XBRL
    assert result.confidence >= 0.85
    assert len(result.financial_data) > 0
    assert result.metadata['is_xbrl'] is True


@pytest.mark.asyncio
async def test_extract_xbrl_financial_facts(xbrl_document):
    """Test XBRL financial fact extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(xbrl_document)
    
    # Check that Revenue was extracted
    assert 'Revenue' in result.financial_data
    revenue_data = result.financial_data['Revenue']
    assert revenue_data['value'] == 1000000
    assert revenue_data['contextRef'] == 'current_year'


# ============================================================================
# TESTS - SGML Extraction
# ============================================================================

@pytest.mark.asyncio
async def test_extract_sgml_document(sgml_document):
    """Test SGML SEC document extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(sgml_document)
    
    assert result.format == DocumentFormat.SGML
    assert result.confidence >= 0.80
    assert "TEST CORPORATION" in result.metadata.get('sec_header', '')
    assert "Management Discussion and Analysis" in result.content


@pytest.mark.asyncio
async def test_extract_sgml_sec_header(sgml_document):
    """Test SGML SEC header extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(sgml_document)
    
    assert 'sec_header' in result.metadata
    assert 'company_conformed_name' in result.metadata
    assert result.metadata['company_conformed_name'] == 'TEST CORPORATION'
    assert result.metadata['central_index_key'] == '0001234567'


# ============================================================================
# TESTS - Plain Text Extraction
# ============================================================================

@pytest.mark.asyncio
async def test_extract_plain_text_document(plain_text_document):
    """Test plain text document extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(plain_text_document)
    
    assert result.format == DocumentFormat.TXT
    assert result.confidence >= 0.80
    assert "ANNUAL REPORT 2023" in result.content
    assert "Revenue: $1,000,000" in result.content


# ============================================================================
# TESTS - Confidence Calculation
# ============================================================================

@pytest.mark.asyncio
async def test_extraction_confidence_with_tables(html_document):
    """Test confidence boost with table extraction."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document(html_document)
    confidence = extractor.calculate_extraction_confidence(result)
    
    # Confidence should be boosted due to table extraction
    assert confidence > result.confidence


@pytest.mark.asyncio
async def test_extraction_confidence_short_content():
    """Test confidence penalty for short content."""
    extractor = UniversalDocumentExtractor()
    
    short_content = "Test"
    result = await extractor.extract_document(short_content)
    confidence = extractor.calculate_extraction_confidence(result)
    
    # Confidence should be penalized
    assert confidence < result.confidence


# ============================================================================
# TESTS - Forensic Document Analyzer
# ============================================================================

@pytest.mark.asyncio
async def test_forensic_analyzer_basic(html_document):
    """Test forensic analyzer basic functionality."""
    analyzer = ForensicSECDocumentAnalyzer()
    
    result = await analyzer.analyze_document(
        content=html_document,
        url="test.html",
        extract_financials=True,
        extract_tables=True
    )
    
    assert isinstance(result, ExtractionResult)
    assert result.confidence > 0.8
    assert result.format == DocumentFormat.HTML


@pytest.mark.asyncio
async def test_forensic_analyzer_financial_extraction(html_document):
    """Test forensic analyzer financial metric extraction."""
    analyzer = ForensicSECDocumentAnalyzer()
    
    result = await analyzer.analyze_document(
        content=html_document,
        extract_financials=True
    )
    
    assert 'extracted_metrics' in result.financial_data


@pytest.mark.asyncio
async def test_forensic_analyzer_without_financial_extraction(html_document):
    """Test forensic analyzer without financial extraction."""
    analyzer = ForensicSECDocumentAnalyzer()
    
    result = await analyzer.analyze_document(
        content=html_document,
        extract_financials=False
    )
    
    # Should not have extracted_metrics key
    assert 'extracted_metrics' not in result.financial_data or result.financial_data['extracted_metrics'] is None


# ============================================================================
# TESTS - Financial Metrics Extraction
# ============================================================================

@pytest.mark.asyncio
async def test_extract_financial_metrics_from_text():
    """Test financial metrics extraction from text."""
    analyzer = ForensicSECDocumentAnalyzer()
    
    text = """
    Revenue: $1,000,000 million
    Net income: $150,000 million
    Cash flow: $200,000 million
    Total assets: $5,000,000 million
    Total liabilities: $3,000,000 million
    """
    
    metrics = await analyzer._extract_financial_metrics(text)
    
    assert metrics is not None
    assert metrics.revenue is not None
    assert metrics.revenue > 0


# ============================================================================
# TESTS - Content Hash
# ============================================================================

@pytest.mark.asyncio
async def test_content_hash_generation(html_document):
    """Test content hash is generated correctly."""
    extractor = UniversalDocumentExtractor()
    
    result1 = await extractor.extract_document(html_document)
    result2 = await extractor.extract_document(html_document)
    
    # Same content should generate same hash
    assert result1.content_hash == result2.content_hash
    assert len(result1.content_hash) == 64  # SHA256 hex digest


@pytest.mark.asyncio
async def test_different_content_different_hash():
    """Test different content generates different hash."""
    extractor = UniversalDocumentExtractor()
    
    result1 = await extractor.extract_document("<html>Content 1</html>")
    result2 = await extractor.extract_document("<html>Content 2</html>")
    
    assert result1.content_hash != result2.content_hash


# ============================================================================
# TESTS - Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_extract_invalid_xml():
    """Test extraction of invalid XML falls back gracefully."""
    extractor = UniversalDocumentExtractor()
    
    invalid_xml = "<?xml version='1.0'?><root><unclosed>"
    result = await extractor.extract_document(invalid_xml)
    
    # Should fall back to text extraction
    assert result.format == DocumentFormat.TXT


@pytest.mark.asyncio
async def test_extract_empty_content():
    """Test extraction of empty content."""
    extractor = UniversalDocumentExtractor()
    
    result = await extractor.extract_document("")
    
    assert result.content == ""
    assert result.confidence < 0.8


# ============================================================================
# TESTS - Integration
# ============================================================================

@pytest.mark.asyncio
async def test_extract_multiple_formats_sequentially():
    """Test extracting multiple document formats in sequence."""
    extractor = UniversalDocumentExtractor()
    
    html = "<html><body>Test HTML</body></html>"
    xml = "<?xml version='1.0'?><root>Test XML</root>"
    text = "Plain text content"
    
    results = []
    results.append(await extractor.extract_document(html))
    results.append(await extractor.extract_document(xml))
    results.append(await extractor.extract_document(text))
    
    assert len(results) == 3
    assert results[0].format == DocumentFormat.HTML
    assert results[1].format == DocumentFormat.XML
    assert results[2].format == DocumentFormat.TXT
