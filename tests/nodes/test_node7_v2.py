"""
Unit Tests for Node 7 v2.0 (13F-HR Institutional Holdings Analyzer)
"""

import pytest
from datetime import date, datetime
from src.nodes.node7_13f_holdings.institutional_analyzer_v2 import (
    InstitutionalHoldingsAnalyzerV2,
    Institution13FHoldingV2,
    WolfPackAlert,
    QuarterlyComparison,
    Severity
)
from src.nodes.node7_13f_holdings.sec_edgar_client import SECEDGARClient


class TestSECEDGARClient:
    """Test SEC EDGAR client functionality."""
    
    def test_quarter_string_generation(self):
        """Test quarter string generation."""
        client = SECEDGARClient()
        
        # Q1
        assert client._get_quarter_string(date(2024, 1, 15)) == "2024Q1"
        assert client._get_quarter_string(date(2024, 3, 31)) == "2024Q1"
        
        # Q2
        assert client._get_quarter_string(date(2024, 4, 1)) == "2024Q2"
        assert client._get_quarter_string(date(2024, 6, 30)) == "2024Q2"
        
        # Q3
        assert client._get_quarter_string(date(2024, 7, 1)) == "2024Q3"
        assert client._get_quarter_string(date(2024, 9, 30)) == "2024Q3"
        
        # Q4
        assert client._get_quarter_string(date(2024, 10, 1)) == "2024Q4"
        assert client._get_quarter_string(date(2024, 12, 31)) == "2024Q4"


class TestInstitutionalAnalyzerV2:
    """Test institutional analyzer v2.0."""
    
    def test_quarterly_comparison_calculation(self):
        """Test quarterly comparison calculation."""
        analyzer = InstitutionalHoldingsAnalyzerV2()
        
        # Create holdings for two quarters
        holdings = [
            Institution13FHoldingV2(
                cik="0000123456",
                institution_name="Test Fund",
                filing_date=date(2024, 11, 15),
                reporting_period=date(2024, 9, 30),
                quarter="2024Q3",
                cusip="123456789",
                issuer_name="Test Corp",
                shares=100000,
                value_thousands=10000,
                investment_discretion="SOLE",
                voting_authority_sole=100000,
                voting_authority_shared=0,
                voting_authority_none=0
            ),
            Institution13FHoldingV2(
                cik="0000123456",
                institution_name="Test Fund",
                filing_date=date(2025, 2, 15),
                reporting_period=date(2024, 12, 31),
                quarter="2024Q4",
                cusip="123456789",
                issuer_name="Test Corp",
                shares=120000,
                value_thousands=12000,
                investment_discretion="SOLE",
                voting_authority_sole=120000,
                voting_authority_shared=0,
                voting_authority_none=0
            )
        ]
        
        comparisons = analyzer.calculate_quarterly_comparisons(holdings)
        
        assert len(comparisons) == 1
        comp = comparisons[0]
        assert comp.cusip == "123456789"
        assert comp.current_quarter == "2024Q4"
        assert comp.previous_quarter == "2024Q3"
        assert comp.share_change == 20000
        assert comp.percent_change == 20.0
        assert comp.position_action == "INCREASE"
    
    def test_wolf_pack_coordination_score(self):
        """Test wolf pack coordination score calculation."""
        analyzer = InstitutionalHoldingsAnalyzerV2()
        
        # Create cluster of holdings with similar patterns
        cluster = [
            Institution13FHoldingV2(
                cik="0000111111",
                institution_name="Fund A",
                filing_date=date(2024, 11, 15),
                reporting_period=date(2024, 9, 30),
                quarter="2024Q3",
                cusip="123456789",
                issuer_name="Test Corp",
                shares=100000,
                value_thousands=10000,
                investment_discretion="SOLE",
                voting_authority_sole=100000,
                voting_authority_shared=0,
                voting_authority_none=0
            ),
            Institution13FHoldingV2(
                cik="0000222222",
                institution_name="Fund B",
                filing_date=date(2024, 11, 17),
                reporting_period=date(2024, 9, 30),
                quarter="2024Q3",
                cusip="123456789",
                issuer_name="Test Corp",
                shares=105000,
                value_thousands=10500,
                investment_discretion="SOLE",
                voting_authority_sole=105000,
                voting_authority_shared=0,
                voting_authority_none=0
            ),
            Institution13FHoldingV2(
                cik="0000333333",
                institution_name="Fund C",
                filing_date=date(2024, 11, 18),
                reporting_period=date(2024, 9, 30),
                quarter="2024Q3",
                cusip="123456789",
                issuer_name="Test Corp",
                shares=95000,
                value_thousands=9500,
                investment_discretion="SOLE",
                voting_authority_sole=95000,
                voting_authority_shared=0,
                voting_authority_none=0
            )
        ]
        
        score = analyzer._calculate_wolf_pack_coordination(cluster)
        
        # Should be relatively high due to similar shares and close timing
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Expect high coordination
    
    def test_severity_classification(self):
        """Test alert severity classification."""
        analyzer = InstitutionalHoldingsAnalyzerV2()
        
        # High coordination, many institutions
        assert analyzer._classify_severity(0.9, 10) == Severity.CRITICAL
        
        # Medium coordination
        assert analyzer._classify_severity(0.6, 5) == Severity.HIGH
        
        # Low coordination
        assert analyzer._classify_severity(0.4, 3) == Severity.MEDIUM
        assert analyzer._classify_severity(0.3, 2) == Severity.LOW


class TestDataStructures:
    """Test data structures."""
    
    def test_institution_holding_v2_to_dict(self):
        """Test Institution13FHoldingV2 serialization."""
        holding = Institution13FHoldingV2(
            cik="0000123456",
            institution_name="Test Fund",
            filing_date=date(2024, 11, 15),
            reporting_period=date(2024, 9, 30),
            quarter="2024Q3",
            cusip="123456789",
            issuer_name="Test Corp",
            shares=100000,
            value_thousands=10000,
            investment_discretion="SOLE",
            voting_authority_sole=100000,
            voting_authority_shared=0,
            voting_authority_none=0,
            previous_quarter_shares=90000,
            quarter_over_quarter_change=11.11,
            sector="Technology",
            market_cap_category="Large"
        )
        
        data = holding.to_dict()
        assert data['cik'] == "0000123456"
        assert data['quarter'] == "2024Q3"
        assert data['shares'] == 100000
        assert data['previous_quarter_shares'] == 90000
        assert data['quarter_over_quarter_change'] == 11.11
        assert data['sector'] == "Technology"
    
    def test_wolf_pack_alert_to_dict(self):
        """Test WolfPackAlert serialization."""
        alert = WolfPackAlert(
            pack_id="abc123",
            cusip="123456789",
            issuer_name="Test Corp",
            institutions=["Fund A", "Fund B", "Fund C"],
            coordination_score=0.85,
            aggregate_ownership_percent=15.5,
            temporal_cluster_days=30,
            filing_window_start=date(2024, 11, 1),
            filing_window_end=date(2024, 11, 30),
            severity=Severity.CRITICAL
        )
        
        data = alert.to_dict()
        assert data['pack_id'] == "abc123"
        assert data['institution_count'] == 3
        assert data['coordination_score'] == 0.85
        assert data['severity'] == "CRITICAL"
        assert 'filing_window' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
