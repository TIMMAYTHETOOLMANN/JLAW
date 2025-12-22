"""
Unit Tests for SEC EDGAR Forensic Analyzer
==========================================

Tests for src/forensics/sec_edgar_analyzer.py:
- FilingAnalysis creation and evidence hash computation
- SECForensicAnalyzer initialization
- Async analyze_filing with mock client
- Violation detection
- Cache clearing
"""

import pytest
import asyncio
from datetime import datetime, date
from src.forensics.sec_edgar_analyzer import (
    FilingAnalysis,
    SECForensicAnalyzer,
    ExtractedEntity,
    DetectedViolation,
    ViolationSeverity,
    FilingType,
    RegulatoryAgency,
    MockEdgarClient
)


class TestFilingAnalysis:
    """Test FilingAnalysis dataclass."""
    
    def test_filing_analysis_creation(self):
        """Test basic FilingAnalysis creation."""
        analysis = FilingAnalysis(
            cik="0001234567",
            filing_type="10-K",
            filing_date=datetime(2024, 3, 15),
            period_end_date=datetime(2023, 12, 31),
            delay_days=10,
            amendments=[],
            red_flags=[],
            fraud_indicators={},
            cross_reference_issues=[],
            revenue_anomalies=[],
            benford_analysis={},
            narrative_consistency=1.0,
            integrity_hash=""
        )
        
        assert analysis.cik == "0001234567"
        assert analysis.filing_type == "10-K"
        assert analysis.delay_days == 10
        assert analysis.narrative_consistency == 1.0
    
    def test_integrity_hash_computation(self):
        """Test that integrity hash is computed automatically."""
        analysis = FilingAnalysis(
            cik="0001234567",
            filing_type="10-K",
            filing_date=datetime(2024, 3, 15),
            period_end_date=datetime(2023, 12, 31),
            delay_days=10,
            amendments=[],
            red_flags=[],
            fraud_indicators={},
            cross_reference_issues=[],
            revenue_anomalies=[],
            benford_analysis={},
            narrative_consistency=1.0,
            integrity_hash=""  # Should be auto-computed
        )
        
        # Verify hash was computed
        assert analysis.integrity_hash != ""
        assert len(analysis.integrity_hash) == 64  # SHA-256 hex length
    
    def test_integrity_hash_deterministic(self):
        """Test that same data produces same hash."""
        analysis1 = FilingAnalysis(
            cik="0001234567",
            filing_type="10-K",
            filing_date=datetime(2024, 3, 15),
            period_end_date=datetime(2023, 12, 31),
            delay_days=10,
            amendments=[],
            red_flags=[],
            fraud_indicators={'test': 1},
            cross_reference_issues=[],
            revenue_anomalies=[],
            benford_analysis={},
            narrative_consistency=1.0,
            integrity_hash=""
        )
        
        analysis2 = FilingAnalysis(
            cik="0001234567",
            filing_type="10-K",
            filing_date=datetime(2024, 3, 15),
            period_end_date=datetime(2023, 12, 31),
            delay_days=10,
            amendments=[],
            red_flags=[],
            fraud_indicators={'test': 1},
            cross_reference_issues=[],
            revenue_anomalies=[],
            benford_analysis={},
            narrative_consistency=1.0,
            integrity_hash=""
        )
        
        assert analysis1.integrity_hash == analysis2.integrity_hash
    
    def test_to_dict_serialization(self):
        """Test to_dict method."""
        analysis = FilingAnalysis(
            cik="0001234567",
            filing_type="10-K",
            filing_date=datetime(2024, 3, 15),
            period_end_date=datetime(2023, 12, 31),
            delay_days=10,
            amendments=[],
            red_flags=[],
            fraud_indicators={},
            cross_reference_issues=[],
            revenue_anomalies=[],
            benford_analysis={},
            narrative_consistency=1.0,
            integrity_hash=""
        )
        
        result = analysis.to_dict()
        
        assert isinstance(result, dict)
        assert result['cik'] == "0001234567"
        assert result['filing_type'] == "10-K"
        assert 'filing_date' in result
        assert 'integrity_hash' in result


class TestMockEdgarClient:
    """Test MockEdgarClient functionality."""
    
    def test_mock_client_initialization(self):
        """Test MockEdgarClient can be initialized."""
        client = MockEdgarClient(user_agent="Test/1.0")
        assert client.user_agent == "Test/1.0"
    
    @pytest.mark.asyncio
    async def test_mock_fetch_filing_content(self):
        """Test mock fetch filing content."""
        client = MockEdgarClient(user_agent="Test/1.0")
        content = await client.fetch_filing_content("https://example.com/filing.txt")
        
        assert isinstance(content, str)
        assert "Mock filing content" in content
    
    @pytest.mark.asyncio
    async def test_mock_get_form4_filings(self):
        """Test mock get form4 filings."""
        client = MockEdgarClient(user_agent="Test/1.0")
        filings = await client.get_form4_filings(cik="0001234567")
        
        assert isinstance(filings, list)
        assert len(filings) == 0  # Mock returns empty list


class TestSECForensicAnalyzer:
    """Test SECForensicAnalyzer functionality."""
    
    def test_analyzer_initialization(self):
        """Test SECForensicAnalyzer initialization."""
        analyzer = SECForensicAnalyzer(user_agent="Test/1.0", rate_limit=8.0)
        
        assert analyzer.user_agent == "Test/1.0"
        assert analyzer.rate_limit == 8.0
        assert analyzer._sec_client is None  # Lazy-loaded
        assert isinstance(analyzer._cache, dict)
    
    def test_analyzer_default_initialization(self):
        """Test default initialization."""
        analyzer = SECForensicAnalyzer()
        
        assert analyzer.user_agent is not None
        assert analyzer.rate_limit == 8.0
    
    def test_extract_entities(self):
        """Test entity extraction from text."""
        analyzer = SECForensicAnalyzer()
        
        text = """
        The company reported revenue of $1.5 million in Q1 2024.
        Net income increased by 15.3% year over year.
        The filing was submitted on 03/15/2024.
        Total assets are $25.7 billion.
        """
        
        entities = analyzer._extract_entities(text)
        
        # Should find money amounts
        money_entities = [e for e in entities if e.entity_type == "MONEY"]
        assert len(money_entities) > 0
        
        # Should find percentages
        percent_entities = [e for e in entities if e.entity_type == "PERCENT"]
        assert len(percent_entities) > 0
        
        # Should find dates
        date_entities = [e for e in entities if e.entity_type == "DATE"]
        assert len(date_entities) > 0
    
    def test_detect_violations(self):
        """Test violation detection in text."""
        analyzer = SECForensicAnalyzer()
        
        # Text with potential violations
        text = """
        The audit revealed material misstatements in the financial statements.
        There were concerns about insider trading based on material non-public information.
        Internal controls were found to be inadequate with material weaknesses.
        """
        
        violations = analyzer._detect_violations(text, "https://example.com/filing.txt")
        
        assert len(violations) > 0
        assert all(isinstance(v, DetectedViolation) for v in violations)
        
        # Check for specific violation types
        violation_types = {v.violation_type for v in violations}
        assert 'securities_fraud' in violation_types or 'insider_trading' in violation_types
    
    def test_calculate_risk_score(self):
        """Test risk score calculation."""
        analyzer = SECForensicAnalyzer()
        
        # No violations = 0 risk
        assert analyzer._calculate_risk_score([]) == 0.0
        
        # Critical violation = high risk
        violations = [
            DetectedViolation(
                violation_type="insider_trading",
                severity=ViolationSeverity.CRITICAL,
                description="Test violation",
                regulatory_citation="17 CFR § 240.10b5-1",
                confidence=0.9,
                evidence_quote="test quote",
                document_url="https://example.com"
            )
        ]
        
        risk_score = analyzer._calculate_risk_score(violations)
        assert risk_score > 0.5  # Should be high
        assert risk_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_filing(self):
        """Test async analyze_filing method."""
        analyzer = SECForensicAnalyzer(user_agent="Test/1.0")
        
        # Mock URL that won't actually be fetched (will fall back to error handling)
        result = await analyzer.analyze_filing(
            cik="0001234567",
            accession_number="0001234567-24-000001",
            filing_type="10-K",
            document_url="https://example.com/filing.txt",
            filing_date="2024-03-15"
        )
        
        # Should return FilingAnalysis even on error
        assert isinstance(result, FilingAnalysis)
        assert result.cik == "0001234567"
        assert result.filing_type == "10-K"
    
    @pytest.mark.asyncio
    async def test_batch_analyze(self):
        """Test batch analysis of multiple filings."""
        analyzer = SECForensicAnalyzer(user_agent="Test/1.0")
        
        filings = [
            {
                'cik': '0001234567',
                'accession_number': '0001234567-24-000001',
                'filing_type': '10-K',
                'document_url': 'https://example.com/filing1.txt'
            },
            {
                'cik': '0001234567',
                'accession_number': '0001234567-24-000002',
                'filing_type': '10-Q',
                'document_url': 'https://example.com/filing2.txt'
            }
        ]
        
        results = await analyzer.batch_analyze(filings)
        
        assert len(results) == 2
        assert all(isinstance(r, FilingAnalysis) for r in results)
        assert results[0].filing_type == "10-K"
        assert results[1].filing_type == "10-Q"
    
    def test_cache_functionality(self):
        """Test cache clearing."""
        analyzer = SECForensicAnalyzer()
        
        # Add something to cache
        analyzer._cache['test_key'] = 'test_value'
        assert len(analyzer._cache) == 1
        
        # Clear cache
        analyzer.clear_cache()
        assert len(analyzer._cache) == 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting enforcement."""
        analyzer = SECForensicAnalyzer(rate_limit=10.0)
        
        import time
        start = time.time()
        
        # Make two rate-limited calls
        await analyzer._rate_limit_wait()
        await analyzer._rate_limit_wait()
        
        elapsed = time.time() - start
        
        # Should take at least 0.1 seconds (1/10 req/sec)
        assert elapsed >= 0.09  # Allow small margin


class TestEnums:
    """Test enum definitions."""
    
    def test_filing_type_enum(self):
        """Test FilingType enum."""
        assert FilingType.FORM_4.value == "4"
        assert FilingType.FORM_10K.value == "10-K"
        assert FilingType.DEF_14A.value == "DEF 14A"
    
    def test_violation_severity_enum(self):
        """Test ViolationSeverity enum."""
        assert ViolationSeverity.LOW.value == "LOW"
        assert ViolationSeverity.MEDIUM.value == "MEDIUM"
        assert ViolationSeverity.HIGH.value == "HIGH"
        assert ViolationSeverity.CRITICAL.value == "CRITICAL"
    
    def test_regulatory_agency_enum(self):
        """Test RegulatoryAgency enum."""
        assert RegulatoryAgency.SEC.value == "SEC"
        assert RegulatoryAgency.DOJ.value == "DOJ"
        assert RegulatoryAgency.IRS.value == "IRS"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
