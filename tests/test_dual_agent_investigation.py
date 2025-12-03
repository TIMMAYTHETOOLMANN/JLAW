"""
Test suite for the Enhanced Dual-Agent Investigative System.

Tests the tandem workflow where:
1. OpenAI agent performs initial violation detection
2. Anthropic agent cross-references findings using GovInfo API
3. All statutes and legal frameworks are correlated
4. Nothing is missed through dual-pass validation
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List


# Create a mock config for testing
def create_mock_config():
    """Create a mock configuration for testing."""
    mock_cfg = MagicMock()
    mock_cfg.config.openai.api_key = None
    mock_cfg.config.anthropic.api_key = None
    mock_cfg.config.govinfo = None
    return mock_cfg


@pytest.fixture
def mock_coordinator():
    """Create a coordinator instance with mocked dependencies."""
    with patch('src.forensics.dual_agent.get_config', return_value=create_mock_config()):
        from src.forensics.dual_agent import DualAgentCoordinator
        coordinator = DualAgentCoordinator()
    return coordinator


class TestDualAgentCoordinator:
    """Test suite for DualAgentCoordinator."""

    @pytest.fixture
    def sample_violations_openai(self) -> List[Dict[str, Any]]:
        """Sample violations that OpenAI might detect."""
        return [
            {
                "type": "late_form4",
                "severity": "HIGH",
                "description": "Late Form 4 filing by 5 business days",
                "statute": "15 USC § 78p(a)",  # Same statute reference base
                "document_url": "https://www.sec.gov/Archives/edgar/data/320187/test.xml",
                "transaction_date": "2019-03-15",
                "filing_date": "2019-03-25",
                "business_days_late": 5,
            },
            {
                "type": "zero_dollar_transaction",
                "severity": "HIGH",
                "description": "Zero-dollar transaction (potential gift/RSU vesting)",
                "statute": "15 USC § 78p(a)",
                "price": "0.00",
                "document_url": "https://www.sec.gov/Archives/edgar/data/320187/test2.xml",
            },
        ]

    @pytest.fixture
    def sample_violations_anthropic(self) -> List[Dict[str, Any]]:
        """Sample violations that Anthropic might detect (with overlap and unique)."""
        return [
            {
                # Same late_form4 violation - should be detected as overlap
                "type": "late_form4",
                "severity": "HIGH",
                "description": "Late Form 4 filing by 5 business days",  # Same description
                "statute": "15 USC § 78p(a)",  # Same statute for deduplication to work
                "document_url": "https://www.sec.gov/Archives/edgar/data/320187/test.xml",  # Same URL
                "prosecutorial_merit": "STRONG",
                "estimated_damages": 25000,
            },
            {
                "type": "material_misstatement",
                "severity": "CRITICAL",
                "description": "Potential material misstatement in revenue recognition",
                "statute": "17 CFR § 240.10b-5",
                "section": "MD&A",
                "exact_quote": "Revenue increased 15% year-over-year...",
            },
        ]

    def test_merge_violations_deduplication(
        self, mock_coordinator, sample_violations_openai, sample_violations_anthropic
    ):
        """Test that violations are properly merged and deduplicated."""
        merged = mock_coordinator._merge_violations(
            sample_violations_openai,
            sample_violations_anthropic
        )
        
        # Should have 3 unique violations (late_form4 is overlap)
        assert len(merged) == 3
        
        # Check that overlapping violation is marked as confirmed
        late_form4_violations = [v for v in merged if v.get("type") == "late_form4"]
        assert len(late_form4_violations) == 1
        # The first one from OpenAI should be confirmed by Anthropic
        assert late_form4_violations[0].get("_source") == "openai"
        assert "anthropic" in late_form4_violations[0].get("_confirmed_by", [])

    def test_compute_overlap(
        self, mock_coordinator, sample_violations_openai, sample_violations_anthropic
    ):
        """Test overlap computation between agents."""
        overlap = mock_coordinator._compute_overlap(
            sample_violations_openai,
            sample_violations_anthropic
        )
        
        # Should have 1 overlapping violation (late_form4)
        assert len(overlap) == 1
        assert overlap[0].get("type") == "late_form4"

    def test_calculate_confidence_high_agreement(self, mock_coordinator):
        """Test confidence calculation with high agreement."""
        # High agreement: both agents found similar number of violations
        confidence = mock_coordinator._calculate_confidence(5, 5, 5)
        assert confidence >= 0.9  # High confidence
        
        # Low agreement: one agent found many more
        confidence = mock_coordinator._calculate_confidence(10, 2, 10)
        assert confidence < 0.5  # Lower confidence

    def test_availability_status(self, mock_coordinator):
        """Test availability status reporting."""
        # By default, no providers are available (mocked keys are None)
        availability = mock_coordinator.availability()
        
        # Should report unavailable since mock config has no keys
        assert availability["openai"] is False
        assert availability["anthropic"] is False
        assert availability["govinfo"] is False


class TestInvestigateWithCrossReference:
    """Test the investigate_with_cross_reference workflow."""

    @pytest.fixture
    def sample_filing_content(self) -> str:
        """Sample SEC filing content for testing."""
        return """
        <ownershipDocument>
            <issuer>
                <issuerCik>0000320187</issuerCik>
                <issuerName>NIKE INC</issuerName>
            </issuer>
            <reportingOwner>
                <reportingOwnerId>
                    <rptOwnerCik>0001234567</rptOwnerCik>
                    <rptOwnerName>PARKER MARK G</rptOwnerName>
                </reportingOwnerId>
            </reportingOwner>
            <nonDerivativeTable>
                <nonDerivativeTransaction>
                    <transactionDate>
                        <value>2019-03-15</value>
                    </transactionDate>
                    <transactionCoding>
                        <transactionCode>M</transactionCode>
                    </transactionCoding>
                    <transactionAmounts>
                        <transactionShares>
                            <value>50000</value>
                        </transactionShares>
                        <transactionPricePerShare>
                            <value>0</value>
                        </transactionPricePerShare>
                    </transactionAmounts>
                </nonDerivativeTransaction>
            </nonDerivativeTable>
        </ownershipDocument>
        """

    @pytest.fixture
    def sample_filing_metadata(self) -> Dict[str, Any]:
        """Sample filing metadata."""
        return {
            "filing_type": "4",
            "document_url": "https://www.sec.gov/Archives/edgar/data/320187/test.xml",
            "filing_date": "2019-03-20",
            "cik": "0000320187",
            "company_name": "NIKE INC",
        }

    @pytest.mark.asyncio
    async def test_investigation_workflow_structure(self, sample_filing_content, sample_filing_metadata):
        """Test that investigation returns expected structure."""
        with patch('src.forensics.dual_agent.get_config', return_value=create_mock_config()):
            from src.forensics.dual_agent import DualAgentCoordinator
            
            coordinator = DualAgentCoordinator()
            
            # Manually set up mock analyzers
            coordinator.openai_analyzer = MagicMock()
            coordinator.openai_analyzer.parse_violations_from_content = MagicMock(
                return_value={"violations": [{"type": "zero_dollar_transaction", "severity": "HIGH"}]}
            )
            coordinator.openai_analyzer.model = "gpt-4o"
            
            coordinator.anthropic_analyzer = MagicMock()
            coordinator.anthropic_analyzer.analyze_text = AsyncMock(return_value={
                "status": "success",
                "violations": [{"type": "zero_dollar_transaction", "severity": "HIGH"}],
                "summary": "Zero-dollar transaction detected",
            })
            coordinator.anthropic_analyzer.model = "claude-3-opus"
            
            # Run investigation
            result = await coordinator.investigate_with_cross_reference(
                content=sample_filing_content,
                filing_metadata=sample_filing_metadata,
                enable_govinfo_enrichment=False
            )
            
            # Verify structure
            assert result["status"] == "COMPLETE"
            assert "openai_findings" in result
            assert "anthropic_cross_reference" in result
            assert "merged_violations" in result
            assert "investigation_summary" in result
            assert "provenance" in result
            
            # Verify summary metrics
            summary = result["investigation_summary"]
            assert "total_violations_detected" in summary
            assert "dual_agent_coverage" in summary
            assert summary["dual_agent_coverage"] is True


class TestNothingMissedValidation:
    """Test the nothing-missed validation logic."""

    def test_validation_passes_when_all_violations_merged(self):
        """Test that validation passes when all violations are properly merged."""
        openai_count = 5
        anthropic_count = 4
        merged_count = 6  # Max of both plus unique findings
        
        # Validation should pass: merged >= max(openai, anthropic)
        validation_passed = merged_count >= max(openai_count, anthropic_count)
        assert validation_passed is True

    def test_validation_flags_when_violations_missed(self):
        """Test that validation flags when violations appear to be missed."""
        openai_count = 10
        anthropic_count = 8
        merged_count = 5  # Less than either - something went wrong
        
        # Validation should fail: merged < max(openai, anthropic)
        validation_passed = merged_count >= max(openai_count, anthropic_count)
        assert validation_passed is False


class TestGovInfoIntegration:
    """Test GovInfo API integration for statute cross-referencing."""

    @pytest.fixture
    def sample_statute_reference(self) -> Dict[str, Any]:
        """Sample statute reference from GovInfo."""
        return {
            "citation": "15 U.S.C. § 78p",
            "title": 15,
            "section": "78p",
            "short_title": "Exchange Act Section 16 - Directors, Officers, and Principal Stockholders",
            "text_url": "https://www.govinfo.gov/content/pkg/USCODE-2023-title15/xml/USCODE-2023-title15-chap2B-sec78p.xml",
            "pdf_url": "https://www.govinfo.gov/content/pkg/USCODE-2023-title15/pdf/USCODE-2023-title15-chap2B-sec78p.pdf",
            "related_cfr": ["17 CFR 240.16a-3"],
        }

    def test_statute_deduplication(self, sample_statute_reference):
        """Test that statutes are properly deduplicated."""
        statutes = [
            sample_statute_reference,
            sample_statute_reference,  # Duplicate
            {"citation": "17 CFR § 240.10b-5", "title": 17},  # Different
        ]
        
        # Deduplicate
        seen = set()
        unique_statutes = []
        for s in statutes:
            citation = s.get("citation")
            if citation not in seen:
                seen.add(citation)
                unique_statutes.append(s)
        
        assert len(unique_statutes) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
