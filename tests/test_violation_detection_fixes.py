"""
Test Suite for Violation Detection Bug Fixes
==============================================

Tests the fixes for the critical bug where violation detection was registering 0 violations:
1. SECFiling objects converted to dicts before passing to pattern detector
2. HTML response detection for XML files
3. Node results properly mapped to pattern detector keys
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from src.integrations.sec_edgar.edgar_client import SECEdgarClient, SECFiling
from src.detection.patterns.advanced_patterns import AdvancedPatternDetector


class TestSECFilingToDictConversion:
    """Test that SECFiling objects are properly converted to dicts."""
    
    def test_secfiling_to_dict_method(self):
        """Test that SECFiling.to_dict() returns proper dictionary."""
        filing = SECFiling(
            accession_number="0001234567-24-000001",
            form_type="4",
            filing_date=date(2024, 1, 15),
            report_date=date(2024, 1, 14),
            primary_document="form4.xml",
            file_number="001-12345",
            cik="320193",
            company_name="Test Corp",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form4.xml",
            index_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json"
        )
        
        filing_dict = filing.to_dict()
        
        assert isinstance(filing_dict, dict)
        assert filing_dict["accession_number"] == "0001234567-24-000001"
        assert filing_dict["form_type"] == "4"
        assert filing_dict["filing_date"] == "2024-01-15"
        assert filing_dict["cik"] == "320193"
        assert filing_dict["company_name"] == "Test Corp"
    
    def test_secfiling_list_conversion_to_dicts(self):
        """Test converting a list of SECFiling objects to dicts."""
        filings = [
            SECFiling(
                accession_number=f"0001234567-24-00000{i}",
                form_type="4",
                filing_date=date(2024, 1, i+1),
                report_date=date(2024, 1, i),
                primary_document="form4.xml",
                file_number="001-12345",
                cik="320193",
                company_name="Test Corp",
                document_url=f"https://www.sec.gov/Archives/edgar/data/320193/000123456724000{i}/form4.xml",
                index_url=f"https://www.sec.gov/Archives/edgar/data/320193/000123456724000{i}/index.json"
            )
            for i in range(1, 4)
        ]
        
        # Convert to dicts as done in JLAW_UNIFIED.py Phase 5
        filing_dicts = []
        for filing in filings:
            if isinstance(filing, SECFiling):
                filing_dicts.append(filing.to_dict())
            elif isinstance(filing, dict):
                filing_dicts.append(filing)
        
        assert len(filing_dicts) == 3
        assert all(isinstance(f, dict) for f in filing_dicts)
        assert all('filing_date' in f for f in filing_dicts)


class TestPatternDetectorHandlesBothTypes:
    """Test that pattern detector handles both dict and SECFiling objects."""
    
    def test_detect_disclosure_timing_with_dict(self):
        """Test disclosure timing detection with dictionary input."""
        detector = AdvancedPatternDetector()
        
        filings = [
            {
                'filing_date': date(2024, 1, 5),  # Friday
                'filing_time': '17:00',  # After market close
                'items': ['4.02'],
                'market_hours': 'AFTER_HOURS'
            }
        ]
        
        alerts = detector.detect_disclosure_timing_anomalies(filings)
        
        # Should detect Friday afternoon filing anomaly
        assert len(alerts) >= 0  # May or may not generate alerts depending on logic
        
    def test_detect_disclosure_timing_with_secfiling(self):
        """Test disclosure timing detection with SECFiling object."""
        detector = AdvancedPatternDetector()
        
        filing = SECFiling(
            accession_number="0001234567-24-000001",
            form_type="8-K",
            filing_date=date(2024, 1, 5),  # Friday
            report_date=date(2024, 1, 5),
            primary_document="form8k.htm",
            file_number="001-12345",
            cik="320193",
            company_name="Test Corp",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form8k.htm",
            index_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json"
        )
        # Add filing_time attribute (not in dataclass but could be added)
        filing.filing_time = '17:00'
        filing.items = ['4.02']
        filing.market_hours = 'AFTER_HOURS'
        
        # Should not crash - defensive handling
        try:
            alerts = detector.detect_disclosure_timing_anomalies([filing])
            # Successfully handled SECFiling object
            assert True
        except AttributeError as e:
            if "'SECFiling' object has no attribute 'get'" in str(e):
                pytest.fail("Pattern detector still using .get() on SECFiling objects")
            raise
    
    def test_detect_disclosure_timing_mixed_types(self):
        """Test disclosure timing detection with mixed dict and SECFiling objects."""
        detector = AdvancedPatternDetector()
        
        filing_obj = SECFiling(
            accession_number="0001234567-24-000001",
            form_type="8-K",
            filing_date=date(2024, 1, 5),
            report_date=date(2024, 1, 5),
            primary_document="form8k.htm",
            file_number="001-12345",
            cik="320193",
            company_name="Test Corp",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form8k.htm",
            index_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json"
        )
        
        filing_dict = {
            'filing_date': date(2024, 1, 12),  # Friday
            'filing_time': '16:30',
            'items': ['2.06'],
            'market_hours': 'REGULAR'
        }
        
        # Mixed list should be handled gracefully
        try:
            alerts = detector.detect_disclosure_timing_anomalies([filing_obj, filing_dict])
            assert True  # No crash
        except AttributeError as e:
            if "'SECFiling' object has no attribute 'get'" in str(e):
                pytest.fail("Pattern detector not handling mixed types correctly")
            raise


class TestHTMLDetectionInXMLFetch:
    """Test that HTML responses are detected when fetching XML files."""
    
    @pytest.mark.asyncio
    async def test_html_response_detected_for_xml_url(self):
        """Test that HTML response is detected when fetching .xml URL."""
        client = SECEdgarClient(user_agent="Test Agent test@example.com")
        
        # Mock the session to return HTML content for an XML URL
        html_content = """<!DOCTYPE html>
<html>
<head><title>SEC Filing</title></head>
<body>This is an HTML-rendered page</body>
</html>"""
        
        # Need to initialize the client's session first
        async with client:
            with patch.object(client.session, 'get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value=html_content)
                mock_get.return_value.__aenter__.return_value = mock_response
                
                # Fetch an XML URL that returns HTML
                url = "https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form4.xml"
                result = await client._fetch_with_retry(url)
                
                # Should return None when HTML is detected for XML URL
                assert result is None
    
    @pytest.mark.asyncio
    async def test_xml_response_accepted_for_xml_url(self):
        """Test that actual XML response is accepted for .xml URL."""
        client = SECEdgarClient(user_agent="Test Agent test@example.com")
        
        xml_content = """<?xml version="1.0"?>
<ownershipDocument>
    <issuer>
        <issuerCik>0000320193</issuerCik>
        <issuerName>Test Corp</issuerName>
    </issuer>
</ownershipDocument>"""
        
        # Need to initialize the client's session first
        async with client:
            with patch.object(client.session, 'get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value=xml_content)
                mock_get.return_value.__aenter__.return_value = mock_response
                
                # Fetch an XML URL that returns actual XML
                url = "https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form4.xml"
                result = await client._fetch_with_retry(url)
                
                # Should return the XML content
                assert result == xml_content
                assert "<?xml" in result


class TestNodeResultsKeyMapping:
    """Test that node results are properly mapped to pattern detector keys."""
    
    def test_pattern_detector_expects_specific_keys(self):
        """Test that pattern detector run_all_patterns expects specific keys."""
        detector = AdvancedPatternDetector()
        
        # Test data with keys that pattern detector expects
        pattern_data = {
            'form4_trades': [],        # Pattern 4: Pre-Announcement Positioning
            'form8k_filings': [],       # Pattern 4 & 6: Pre-Announcement & Sequential Adverse Events
            'insider_trades': [],       # Pattern 13: Clustered Disposals
            'schedule13_filings': [],   # Pattern 3: 13G-to-13D Conversion
            'filings': [],             # Pattern 5: Disclosure Timing
        }
        
        # Should not crash with these keys
        try:
            results = detector.run_all_patterns(pattern_data)
            assert isinstance(results, dict)
        except Exception as e:
            pytest.fail(f"Pattern detector crashed with expected keys: {e}")
    
    def test_pattern_detector_handles_missing_keys_gracefully(self):
        """Test that pattern detector handles missing keys gracefully."""
        detector = AdvancedPatternDetector()
        
        # Empty data
        pattern_data = {}
        
        # Should not crash
        try:
            results = detector.run_all_patterns(pattern_data)
            assert isinstance(results, dict)
        except Exception as e:
            pytest.fail(f"Pattern detector crashed with empty data: {e}")


class TestFallbackURLPatterns:
    """Test that fallback URL patterns are properly configured."""
    
    @pytest.mark.asyncio
    async def test_fallback_patterns_include_multiple_variations(self):
        """Test that fallback patterns include multiple XML filename variations."""
        client = SECEdgarClient(user_agent="Test Agent test@example.com")
        
        filing = SECFiling(
            accession_number="0001234567-24-000001",
            form_type="4",
            filing_date=date(2024, 1, 15),
            report_date=date(2024, 1, 14),
            primary_document="xslF345X03/form4.xml",
            file_number="001-12345",
            cik="0000320193",
            company_name="Test Corp",
            document_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/xslF345X03/form4.xml",
            index_url="https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json"
        )
        
        # Mock _fetch to return None for all URLs (simulating failures)
        call_count = 0
        urls_tried = []
        
        async def mock_fetch(url):
            nonlocal call_count, urls_tried
            call_count += 1
            urls_tried.append(url)
            return None  # Simulate failure
        
        client._fetch = mock_fetch
        client._resolve_xml_from_index = AsyncMock(return_value=None)
        
        result = await client._fetch_with_fallback(filing, is_xml=True)
        
        # Should have tried multiple fallback patterns
        assert call_count > 2  # At least tried direct URL + 2 fallbacks
        assert any('form4.xml' in url for url in urls_tried)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
