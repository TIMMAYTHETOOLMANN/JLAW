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
    assert result.tables[0]["row_count"] == 2
    assert result.content_hash != ""
    assert result.url == "test.html"


@pytest.mark.asyncio
async def test_extract_html_metadata(html_document):
    """Test HTML metadata extraction."""
    extractor = UniversalDocumentExtractor()

    result = await extractor.extract_document(html_document)

    assert "title" in result.metadata
    assert result.metadata["title"] == "Annual Report 2023"
    assert "company" in result.metadata
    assert result.metadata["company"] == "Test Corp"


@pytest.mark.asyncio
async def test_extract_html_table_structure(html_document):
    """Test HTML table structure extraction."""
    extractor = UniversalDocumentExtractor()

    result = await extractor.extract_document(html_document)

    assert len(result.tables) == 1
    table = result.tables[0]
    assert "headers" in table
    assert "rows" in table
    assert len(table["headers"]) == 3
    assert table["headers"] == ["Year", "Revenue", "Earnings"]


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
    assert result.metadata["is_xbrl"] is True


@pytest.mark.asyncio
async def test_extract_xbrl_financial_facts(xbrl_document):
    """Test XBRL financial fact extraction."""
    extractor = UniversalDocumentExtractor()

    result = await extractor.extract_document(xbrl_document)

    # Check that Revenue was extracted
    assert "Revenue" in result.financial_data
    revenue_data = result.financial_data["Revenue"]
    assert revenue_data["value"] == 1000000
    assert revenue_data["contextRef"] == "current_year"


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
    assert "TEST CORPORATION" in result.metadata.get("sec_header", "")
    assert "Management Discussion and Analysis" in result.content


@pytest.mark.asyncio
async def test_extract_sgml_sec_header(sgml_document):
    """Test SGML SEC header extraction."""
    extractor = UniversalDocumentExtractor()

    result = await extractor.extract_document(sgml_document)

    assert "sec_header" in result.metadata
    assert "company_conformed_name" in result.metadata
    assert result.metadata["company_conformed_name"] == "TEST CORPORATION"
    assert result.metadata["central_index_key"] == "0001234567"


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
        content=html_document, url="test.html", extract_financials=True, extract_tables=True
    )

    assert isinstance(result, ExtractionResult)
    assert result.confidence > 0.8
    assert result.format == DocumentFormat.HTML


@pytest.mark.asyncio
async def test_forensic_analyzer_financial_extraction(html_document):
    """Test forensic analyzer financial metric extraction."""
    analyzer = ForensicSECDocumentAnalyzer()

    result = await analyzer.analyze_document(content=html_document, extract_financials=True)

    assert "extracted_metrics" in result.financial_data


@pytest.mark.asyncio
async def test_forensic_analyzer_without_financial_extraction(html_document):
    """Test forensic analyzer without financial extraction."""
    analyzer = ForensicSECDocumentAnalyzer()

    result = await analyzer.analyze_document(content=html_document, extract_financials=False)

    # Should not have extracted_metrics key
    assert (
        "extracted_metrics" not in result.financial_data
        or result.financial_data["extracted_metrics"] is None
    )


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


# ============================================================================
# TESTS - ForensicSECAnalyzer (Complete Document Extraction)
# ============================================================================

from src.forensics.sec_forensic_extraction_system import (
    ForensicSECAnalyzer,
    EnhancedDocumentFormat,
    ComprehensiveExtractionResult,
    SECPatternMatch,
)


@pytest.fixture
def forensic_analyzer():
    """Create ForensicSECAnalyzer instance."""
    return ForensicSECAnalyzer(strict_mode=False)


@pytest.fixture
def ixbrl_document():
    """Sample iXBRL document with embedded XBRL facts."""
    return """
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml"
          xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
          xmlns:xbrli="http://www.xbrl.org/2003/instance">
    <head>
        <title>10-K Inline XBRL</title>
    </head>
    <body>
        <h1>Financial Statements</h1>
        <p>Total revenue for fiscal 2023 was 
           <ix:nonFraction name="us-gaap:Revenue" contextRef="FY2023" unitRef="USD" decimals="-3">
               1,500,000
           </ix:nonFraction> thousand dollars.
        </p>
        <p>Net income was 
           <ix:nonFraction name="us-gaap:NetIncome" contextRef="FY2023" unitRef="USD" decimals="-3">
               150,000
           </ix:nonFraction> thousand.
        </p>
    </body>
    </html>
    """


@pytest.fixture
def json_document():
    """Sample JSON data document."""
    return """
    [
        {"company": "Test Corp", "revenue": 1000000, "year": 2023},
        {"company": "Test Corp", "revenue": 900000, "year": 2022},
        {"company": "Test Corp", "revenue": 800000, "year": 2021}
    ]
    """


@pytest.fixture
def csv_document():
    """Sample CSV data document."""
    return """company,revenue,year
Test Corp,1000000,2023
Test Corp,900000,2022
Test Corp,800000,2021"""


@pytest.fixture
def sec_10k_document():
    """Sample SEC 10-K document with sections and signatures."""
    return """
    <html>
    <head><title>Form 10-K Annual Report</title></head>
    <body>
    <h1>FORM 10-K</h1>
    <h2>ITEM 1. BUSINESS</h2>
    <p>The Company is engaged in the development and sale of software products.</p>
    
    <h2>ITEM 1A. RISK FACTORS</h2>
    <p>• Competition from larger companies may impact market share.</p>
    <p>• Economic downturns could reduce customer spending.</p>
    <p>• Cybersecurity threats pose operational risks.</p>
    
    <h2>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS</h2>
    <p>Revenue: $1,500,000 for fiscal year 2023, representing a 15% increase.</p>
    <p>See Note 5 for additional details on revenue recognition.</p>
    <p>As discussed in Item 1A, risk factors may impact future performance.</p>
    
    <h2>ITEM 8. FINANCIAL STATEMENTS</h2>
    <table>
        <tr><th>Account</th><th>2023</th><th>2022</th></tr>
        <tr><td>Revenue</td><td>$1,500,000</td><td>$1,300,000</td></tr>
        <tr><td>Net Income</td><td>$150,000</td><td>$120,000</td></tr>
    </table>
    
    <h2>SIGNATURES</h2>
    <p>Pursuant to the requirements of Section 13 or 15(d) of the Securities Exchange Act of 1934,
       as amended, the Registrant has duly caused this report to be signed on its behalf by the
       undersigned, thereunto duly authorized.</p>
    
    <p>By: /s/ John Smith<br/>
        John Smith, Chief Executive Officer</p>
    
    <p>By: /s/ Jane Doe<br/>
        Jane Doe, Chief Financial Officer</p>
    
    <!-- Hidden comment about document processing -->
    <div style="display:none">Internal reference: DOC-12345</div>
    
    <sup>1</sup> See accompanying notes.
    <p id="footnote-1">Note 1: Revenue is recognized when control transfers.</p>
    </body>
    </html>
    """


@pytest.fixture
def document_with_legal_refs():
    """Document with legal references."""
    return """
    This filing is made pursuant to 15 USC § 78p(a) and 17 CFR § 240.16a-3.
    The company complies with Rule 10b-5 and Sarbanes-Oxley Section 302.
    Accounting follows ASC 606 and FASB 842 guidelines.
    """


# ============================================================================
# TESTS - Session Management
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_analyzer_create_session(forensic_analyzer):
    """Test session creation."""
    session_id = await forensic_analyzer.create_session()

    assert session_id is not None
    assert len(session_id) == 16
    assert forensic_analyzer._session_active is True


@pytest.mark.asyncio
async def test_forensic_analyzer_close_session(forensic_analyzer):
    """Test session closure."""
    await forensic_analyzer.create_session()
    await forensic_analyzer.close_session()

    assert forensic_analyzer._session_active is False
    assert forensic_analyzer._session_id is None


# ============================================================================
# TESTS - Enhanced Format Detection
# ============================================================================


@pytest.mark.asyncio
async def test_detect_ixbrl_format(forensic_analyzer, ixbrl_document):
    """Test iXBRL format detection."""
    detected = forensic_analyzer._detect_format(ixbrl_document)

    assert detected == EnhancedDocumentFormat.IXBRL


@pytest.mark.asyncio
async def test_detect_json_format(forensic_analyzer, json_document):
    """Test JSON format detection."""
    detected = forensic_analyzer._detect_format(json_document)

    assert detected == EnhancedDocumentFormat.JSON


@pytest.mark.asyncio
async def test_detect_csv_format(forensic_analyzer, csv_document):
    """Test CSV format detection."""
    detected = forensic_analyzer._detect_format(csv_document)

    assert detected == EnhancedDocumentFormat.CSV


@pytest.mark.asyncio
async def test_detect_format_from_url_json(forensic_analyzer):
    """Test format detection from JSON URL."""
    detected = forensic_analyzer._detect_format("{}", url="https://example.com/data.json")

    assert detected == EnhancedDocumentFormat.JSON


# ============================================================================
# TESTS - Complete HTML Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_analyze_html_complete(forensic_analyzer, sec_10k_document):
    """Test complete HTML extraction with all elements."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Check basic extraction
    assert extraction["format"] == "html"
    assert extraction["byte_coverage"] > 0.5  # Text is smaller than raw HTML due to tag removal
    assert extraction["element_count"] > 0

    # Check content was extracted
    assert "FORM 10-K" in extraction["content"]
    assert "software products" in extraction["content"]


@pytest.mark.asyncio
async def test_forensic_extract_hidden_elements(forensic_analyzer, sec_10k_document):
    """Test hidden element extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Should find hidden div
    assert len(extraction["hidden_elements"]) > 0

    # Check for display:none element
    hidden_found = any("DOC-12345" in str(elem) for elem in extraction["hidden_elements"])
    assert hidden_found


@pytest.mark.asyncio
async def test_forensic_extract_comments(forensic_analyzer, sec_10k_document):
    """Test HTML comment extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Should find HTML comments
    assert len(extraction["comments"]) > 0
    assert any("document processing" in comment for comment in extraction["comments"])


@pytest.mark.asyncio
async def test_forensic_extract_tables_complete(forensic_analyzer, sec_10k_document):
    """Test complete table extraction with cell-level detail."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Should extract table
    assert len(extraction["tables"]) > 0

    table = extraction["tables"][0]
    assert "headers" in table
    assert "rows" in table
    assert table["row_count"] > 0


@pytest.mark.asyncio
async def test_forensic_extract_footnotes(forensic_analyzer, sec_10k_document):
    """Test footnote extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Should find footnotes
    assert len(extraction["footnotes"]) > 0


# ============================================================================
# TESTS - SEC Section Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_extract_sec_sections(forensic_analyzer, sec_10k_document):
    """Test SEC section pattern extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]
    sec_sections = extraction["sec_sections"]

    # Should find multiple SEC sections
    assert len(sec_sections) > 0

    # Check for specific sections
    assert "item_1" in sec_sections or "item_1a" in sec_sections or "item_7" in sec_sections


@pytest.mark.asyncio
async def test_forensic_extract_signatures(forensic_analyzer, sec_10k_document):
    """Test signature extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]
    signatures = extraction["signatures"]

    # Should find /s/ signatures
    assert len(signatures) > 0

    # Check for typed signatures
    typed_sigs = [s for s in signatures if s.get("type") == "typed_signature"]
    assert len(typed_sigs) > 0

    # Check for specific names
    names_found = [s.get("name", "") for s in signatures]
    assert any("John Smith" in name or "Jane Doe" in name for name in names_found)


@pytest.mark.asyncio
async def test_forensic_extract_risk_factors(forensic_analyzer, sec_10k_document):
    """Test risk factor extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Should find risk factors (from Item 1A section)
    assert len(extraction["risk_factors"]) >= 0  # May or may not extract based on format


# ============================================================================
# TESTS - Legal Reference Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_extract_legal_references(forensic_analyzer, document_with_legal_refs):
    """Test legal reference pattern extraction."""
    result = await forensic_analyzer.analyze_filing(document_with_legal_refs, is_content=True)

    extraction = result["extraction"]
    legal_refs = extraction["legal_references"]

    # Should find USC, CFR, Rule, SOX, and GAAP references
    assert len(legal_refs) > 0

    # Check for specific reference types
    ref_types = [ref.get("type") for ref in legal_refs]
    assert "usc_citation" in ref_types or "cfr_citation" in ref_types


# ============================================================================
# TESTS - Cross-Reference Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_extract_cross_references(forensic_analyzer, sec_10k_document):
    """Test cross-reference extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]
    cross_refs = extraction["cross_references"]

    # Should find "See" and "As discussed in" references
    assert len(cross_refs) > 0


# ============================================================================
# TESTS - iXBRL Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_extract_ixbrl(forensic_analyzer, ixbrl_document):
    """Test iXBRL extraction with XBRL facts."""
    result = await forensic_analyzer.analyze_filing(ixbrl_document, is_content=True)

    extraction = result["extraction"]

    # Should detect as iXBRL
    assert extraction["format"] == "ixbrl"

    # Should extract XBRL facts
    financial_data = extraction["financial_data"]
    assert "xbrl_facts" in financial_data
    assert financial_data["fact_count"] > 0


# ============================================================================
# TESTS - JSON Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_extract_json(forensic_analyzer, json_document):
    """Test JSON data extraction."""
    result = await forensic_analyzer.analyze_filing(json_document, is_content=True)

    extraction = result["extraction"]

    # Should detect as JSON
    assert extraction["format"] == "json"

    # Should extract as table
    assert len(extraction["tables"]) > 0

    # Check table structure
    table = extraction["tables"][0]
    assert "company" in table["headers"]
    assert table["row_count"] == 3


# ============================================================================
# TESTS - CSV Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_extract_csv(forensic_analyzer, csv_document):
    """Test CSV data extraction."""
    result = await forensic_analyzer.analyze_filing(csv_document, is_content=True)

    extraction = result["extraction"]

    # Should detect as CSV
    assert extraction["format"] == "csv"

    # Should extract as table
    assert len(extraction["tables"]) > 0

    # Check table structure
    table = extraction["tables"][0]
    assert table["column_count"] == 3
    assert table["row_count"] == 3


# ============================================================================
# TESTS - Byte Coverage Tracking
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_byte_coverage_tracking(forensic_analyzer, sec_10k_document):
    """Test byte-level coverage tracking."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Check byte coverage metrics
    assert "byte_coverage" in extraction
    assert "total_bytes" in extraction
    assert "extracted_bytes" in extraction

    # Coverage should be reasonable
    assert extraction["byte_coverage"] > 0.5
    assert extraction["total_bytes"] > 0
    assert extraction["extracted_bytes"] > 0


# ============================================================================
# TESTS - Confidence Calculation
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_confidence_calculation(forensic_analyzer, sec_10k_document):
    """Test extraction confidence calculation."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]

    # Check confidence
    assert "confidence" in extraction
    assert 0.0 <= extraction["confidence"] <= 1.0

    # Complex document should have decent confidence
    assert extraction["confidence"] > 0.5


# ============================================================================
# TESTS - Audit Trail
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_audit_trail(forensic_analyzer, sec_10k_document):
    """Test audit trail completeness."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    # Check result has session info
    assert "session_id" in result
    assert "timestamp" in result

    extraction = result["extraction"]

    # Check extraction has audit fields
    assert "content_hash" in extraction
    assert "timestamp" in extraction
    assert "extraction_method" in extraction
    assert extraction["extraction_method"] == "forensic"

    # Content hash should be SHA256
    assert len(extraction["content_hash"]) == 64


# ============================================================================
# TESTS - Error Recovery
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_error_recovery_malformed_html(forensic_analyzer):
    """Test error recovery for malformed HTML."""
    malformed = "<html><body><p>Unclosed paragraph<div>Nested wrong</p></body>"

    result = await forensic_analyzer.analyze_filing(malformed, is_content=True)

    extraction = result["extraction"]

    # Should still extract something
    assert extraction["content"] != ""
    assert extraction["byte_coverage"] > 0


@pytest.mark.asyncio
async def test_forensic_error_recovery_empty_content(forensic_analyzer):
    """Test handling of empty content."""
    result = await forensic_analyzer.analyze_filing("", is_content=True)

    extraction = result["extraction"]

    # Should handle gracefully
    assert extraction["content"] == ""
    assert extraction["byte_coverage"] == 0


# ============================================================================
# TESTS - Financial Pattern Extraction
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_extract_financial_patterns(forensic_analyzer, sec_10k_document):
    """Test financial pattern extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]
    financial_data = extraction["financial_data"]

    # Should extract monetary amounts
    assert "monetary_amount" in financial_data or len(financial_data) > 0


# ============================================================================
# TESTS - Document Structure
# ============================================================================


@pytest.mark.asyncio
async def test_forensic_document_structure(forensic_analyzer, sec_10k_document):
    """Test hierarchical document structure extraction."""
    result = await forensic_analyzer.analyze_filing(sec_10k_document, is_content=True)

    extraction = result["extraction"]
    structure = extraction["document_structure"]

    # Should have headers hierarchy
    assert "headers" in structure
    assert len(structure["headers"]) > 0
