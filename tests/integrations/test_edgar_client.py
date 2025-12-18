"""
Test Suite for SEC EDGAR Client URL Resolution
==============================================

Tests the 403 error handling and index.json URL resolution 
for XSL-transformed URLs in SEC EDGAR filings.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from src.integrations.sec_edgar.edgar_client import SECEdgarClient, SECFiling


class TestEdgarClientUrlResolution:
    """Test URL resolution and 403 error handling."""
    
    @pytest.fixture
    def mock_filing(self):
        """Create a mock Form 4 filing with XSL-transformed URL."""
        return SECFiling(
            accession_number="0001234567-24-000001",
            form_type="4",
            filing_date=date(2024, 1, 15),
            report_date=date(2024, 1, 14),
            primary_document="xslF345X03/form4.xml",
            file_number="001-12345",
            cik="320193",
            company_name="Test Corp",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/xslF345X03/form4.xml",
            index_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json"
        )
    
    @pytest.fixture
    def mock_index_json(self):
        """Mock index.json response from SEC EDGAR."""
        return {
            "directory": {
                "item": [
                    {"name": "form4.xml", "type": "form4.xml", "size": "5678"},
                    {"name": "xslF345X03/form4.xml", "type": "xml", "size": "1234"},
                    {"name": "form4-doc.xml", "type": "xml", "size": "9012"},
                    {"name": "primary_doc.xml", "type": "xml", "size": "3456"}
                ],
                "name": "000123456724000001",
                "parent-dir": "../"
            }
        }
    
    @pytest.mark.asyncio
    async def test_resolve_xml_from_index_finds_form4(self, mock_filing, mock_index_json):
        """Test that _resolve_xml_from_index finds form4.xml from index.json."""
        client = SECEdgarClient()
        client._fetch_json = AsyncMock(return_value=mock_index_json)
        
        resolved_url = await client._resolve_xml_from_index(mock_filing)
        
        assert resolved_url is not None
        assert "form4.xml" in resolved_url
        assert "xslF345X03" not in resolved_url
        assert resolved_url == "https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form4.xml"
    
    @pytest.mark.asyncio
    async def test_resolve_xml_from_index_handles_no_index(self, mock_filing):
        """Test that _resolve_xml_from_index handles missing index.json."""
        client = SECEdgarClient()
        client._fetch_json = AsyncMock(return_value=None)
        
        resolved_url = await client._resolve_xml_from_index(mock_filing)
        
        assert resolved_url is None
    
    @pytest.mark.asyncio
    async def test_fetch_with_fallback_uses_direct_url_first(self, mock_filing):
        """Test that _fetch_with_fallback tries direct URL first."""
        client = SECEdgarClient()
        xml_content = '<?xml version="1.0"?><form4>...</form4>'
        client._fetch = AsyncMock(return_value=xml_content)
        
        content = await client._fetch_with_fallback(mock_filing, is_xml=True)
        
        assert content == xml_content
        client._fetch.assert_called_once_with(mock_filing.document_url)
    
    @pytest.mark.asyncio
    async def test_fetch_with_fallback_tries_index_on_403(self, mock_filing, mock_index_json):
        """Test that _fetch_with_fallback uses index.json when direct URL fails."""
        client = SECEdgarClient()
        xml_content = '<?xml version="1.0"?><form4>...</form4>'
        
        # First call (direct URL) returns None (simulating 403)
        # Second call (index.json) returns index data
        # Third call (resolved URL) returns content
        call_count = 0
        async def mock_fetch(url):
            nonlocal call_count
            call_count += 1
            if "xslF345X03" in url:
                return None  # Simulate 403 for XSL URL
            elif url.endswith("form4.xml"):
                return xml_content
            return None
        
        client._fetch = mock_fetch
        client._fetch_json = AsyncMock(return_value=mock_index_json)
        
        content = await client._fetch_with_fallback(mock_filing, is_xml=True)
        
        assert content == xml_content
    
    @pytest.mark.asyncio
    async def test_fetch_with_fallback_tries_hardcoded_patterns(self, mock_filing):
        """Test that _fetch_with_fallback tries hardcoded fallback patterns."""
        client = SECEdgarClient()
        xml_content = '<?xml version="1.0"?><form4>...</form4>'
        
        # All attempts fail except the hardcoded form4.xml pattern
        async def mock_fetch(url):
            if url.endswith("/form4.xml") and "xslF345X03" not in url:
                return xml_content
            return None
        
        client._fetch = mock_fetch
        client._fetch_json = AsyncMock(return_value={"directory": {"item": []}})
        
        content = await client._fetch_with_fallback(mock_filing, is_xml=True)
        
        assert content == xml_content
    
    @pytest.mark.asyncio
    async def test_get_form4_xml_uses_fallback(self, mock_filing, mock_index_json):
        """Test that get_form4_xml uses the fallback mechanism."""
        client = SECEdgarClient()
        xml_content = '<?xml version="1.0"?><form4>...</form4>'
        
        async def mock_fetch(url):
            if "xslF345X03" in url:
                return None  # Simulate 403
            return xml_content
        
        client._fetch = mock_fetch
        client._fetch_json = AsyncMock(return_value=mock_index_json)
        
        content = await client.get_form4_xml(mock_filing)
        
        assert content == xml_content
    
    @pytest.mark.asyncio
    async def test_get_filing_text_uses_fallback_for_form4(self, mock_filing, mock_index_json):
        """Test that get_filing_text uses fallback for Form 4."""
        client = SECEdgarClient()
        xml_content = '<?xml version="1.0"?><form4>...</form4>'
        
        async def mock_fetch(url):
            if "xslF345X03" in url:
                return None  # Simulate 403
            return xml_content
        
        client._fetch = mock_fetch
        client._fetch_json = AsyncMock(return_value=mock_index_json)
        
        content = await client.get_filing_text(mock_filing)
        
        assert content == xml_content
    
    @pytest.mark.asyncio
    async def test_get_filing_text_direct_for_non_form4(self):
        """Test that get_filing_text uses direct fetch for non-Form 4."""
        filing = SECFiling(
            accession_number="0001234567-24-000001",
            form_type="10-K",
            filing_date=date(2024, 1, 15),
            report_date=date(2024, 1, 14),
            primary_document="annual-report.htm",
            file_number="001-12345",
            cik="320193",
            company_name="Test Corp",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/annual-report.htm",
            index_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json"
        )
        
        client = SECEdgarClient()
        html_content = '<html>Annual Report...</html>'
        client._fetch = AsyncMock(return_value=html_content)
        
        content = await client.get_filing_text(filing)
        
        assert content == html_content
        client._fetch.assert_called_once_with(filing.document_url)
    
    @pytest.mark.asyncio
    async def test_get_form4_xml_returns_none_for_non_form4(self):
        """Test that get_form4_xml returns None for non-Form 4 filings."""
        filing = SECFiling(
            accession_number="0001234567-24-000001",
            form_type="10-K",
            filing_date=date(2024, 1, 15),
            report_date=date(2024, 1, 14),
            primary_document="annual-report.htm",
            file_number="001-12345",
            cik="320193",
            company_name="Test Corp",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/annual-report.htm",
            index_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json"
        )
        
        client = SECEdgarClient()
        
        content = await client.get_form4_xml(filing)
        
        assert content is None
    
    @pytest.mark.asyncio
    async def test_resolve_handles_exception(self, mock_filing):
        """Test that _resolve_xml_from_index handles exceptions gracefully."""
        client = SECEdgarClient()
        client._fetch_json = AsyncMock(side_effect=Exception("Network error"))
        
        resolved_url = await client._resolve_xml_from_index(mock_filing)
        
        assert resolved_url is None
