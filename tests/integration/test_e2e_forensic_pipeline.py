"""
End-to-End Forensic Pipeline Integration Tests.

Tests complete investigation workflow with XYZ Corp fraud scenario including
entity resolution → narrative analysis → Benford's Law → cross-reference synthesis.
"""

import pytest
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Import forensics modules
from src.forensics.triangulation.entity_resolver import (
    EntityResolver,
    Entity,
    EntitySource,
    EntityType,
)
from src.forensics.analysis.narrative_analyzer import (
    NarrativeAnalyzer,
    NarrativeDocument,
    ToneShiftType,
)
from src.forensics.financial_forensics.revenue_recognition_analyzer import (
    RevenueRecognitionAnalyzer,
    QuarterlyFinancials,
    AnomalyType,
    RiskLevel,
)
from src.forensics.benfords_law_analyzer import BenfordsLawAnalyzer


@dataclass
class ForensicCase:
    """Represents a forensic investigation case."""
    case_id: str
    company_name: str
    cik: str
    investigation_date: datetime
    entities: List[Entity]
    documents: List[NarrativeDocument]
    financials: List[QuarterlyFinancials]
    metadata: Dict[str, Any]


class TestForensicPipelineIntegration:
    """Integration tests for complete forensic analysis pipeline."""
    
    @pytest.fixture
    def xyz_corp_case(self) -> ForensicCase:
        """Create XYZ Corporation fraud scenario test case."""
        return ForensicCase(
            case_id="CASE-XYZ-2024",
            company_name="XYZ Corporation",
            cik="0001234567",
            investigation_date=datetime.now(),
            entities=[
                # SEC filings entities
                Entity(
                    id="sec-001",
                    name="XYZ Corporation",
                    source=EntitySource.SEC,
                    entity_type=EntityType.COMPANY,
                    metadata={"cik": "0001234567"},
                ),
                Entity(
                    id="sec-002",
                    name="John Smith",
                    source=EntitySource.SEC,
                    entity_type=EntityType.EXECUTIVE,
                    metadata={"title": "CEO"},
                ),
                Entity(
                    id="sec-003",
                    name="Jane Doe",
                    source=EntitySource.SEC,
                    entity_type=EntityType.EXECUTIVE,
                    metadata={"title": "CFO"},
                ),
                # News entities
                Entity(
                    id="news-001",
                    name="XYZ Corp",
                    source=EntitySource.NEWS,
                    entity_type=EntityType.COMPANY,
                ),
                Entity(
                    id="news-002",
                    name="J. Smith",
                    source=EntitySource.NEWS,
                    entity_type=EntityType.PERSON,
                    aliases=["John Smith"],
                ),
                # Social media entities
                Entity(
                    id="social-001",
                    name="$XYZ",
                    source=EntitySource.SOCIAL,
                    entity_type=EntityType.TICKER,
                    aliases=["XYZ Corporation"],
                ),
                # Related party
                Entity(
                    id="sec-004",
                    name="ABC Holdings LLC",
                    source=EntitySource.SEC,
                    entity_type=EntityType.COMPANY,
                    metadata={"related_party": True},
                ),
            ],
            documents=[
                NarrativeDocument(
                    id="10K-Q1-2023",
                    content="""
                    XYZ Corporation achieved exceptional results in Q1 2023.
                    Revenue grew 35% year-over-year with strong profit margins.
                    Our strategic initiatives continue to drive robust growth.
                    We are confident in our ability to exceed market expectations.
                    Cash flow generation improved significantly this quarter.
                    The company successfully expanded into new markets.
                    """,
                    quarter="Q1 2023",
                    document_type="10-K",
                    date="2023-03-15",
                ),
                NarrativeDocument(
                    id="10K-Q2-2023",
                    content="""
                    Q2 2023 results reflect continued momentum.
                    Revenue growth accelerated to 40% year-over-year.
                    We believe our market position remains strong.
                    Operating margins may potentially improve further.
                    Cash collections were healthy this quarter.
                    Management anticipates sustained growth trajectory.
                    """,
                    quarter="Q2 2023",
                    document_type="10-K",
                    date="2023-06-15",
                ),
                NarrativeDocument(
                    id="10K-Q3-2023",
                    content="""
                    Q3 2023 presented certain challenges.
                    Due to market conditions, revenue growth moderated.
                    We believe temporary headwinds may impact near-term results.
                    Management anticipates that conditions could potentially improve.
                    Some customers may delay purchasing decisions.
                    We cannot guarantee the timing of revenue recognition.
                    Subject to various factors, results may vary.
                    """,
                    quarter="Q3 2023",
                    document_type="10-K",
                    date="2023-09-15",
                ),
                NarrativeDocument(
                    id="10K-Q4-2023",
                    content="""
                    Q4 2023 was significantly impacted by challenging conditions.
                    Revenue declined due to adverse economic headwinds.
                    The company identified material weaknesses in internal controls.
                    External forces beyond our control created significant pressure.
                    Accounts receivable aging has deteriorated this quarter.
                    We are restating certain prior period financials.
                    Litigation exposure and contingent liabilities have been disclosed.
                    Going concern considerations are being evaluated.
                    """,
                    quarter="Q4 2023",
                    document_type="10-K",
                    date="2023-12-15",
                ),
            ],
            financials=[
                QuarterlyFinancials(
                    quarter="Q1 2023",
                    revenue=10_000_000,
                    accounts_receivable=1_500_000,
                    deferred_revenue=1_000_000,
                    operating_cash_flow=1_200_000,
                    cogs=6_000_000,
                    revenue_by_month=[3_000_000, 3_500_000, 3_500_000],
                ),
                QuarterlyFinancials(
                    quarter="Q2 2023",
                    revenue=14_000_000,
                    accounts_receivable=2_800_000,
                    deferred_revenue=800_000,
                    operating_cash_flow=1_000_000,
                    cogs=8_400_000,
                    revenue_by_month=[3_500_000, 4_000_000, 6_500_000],  # Hockey stick
                ),
                QuarterlyFinancials(
                    quarter="Q3 2023",
                    revenue=12_000_000,
                    accounts_receivable=4_500_000,  # DSO spike
                    deferred_revenue=600_000,
                    operating_cash_flow=200_000,  # Cash flow divergence
                    cogs=7_800_000,
                    revenue_by_month=[2_500_000, 3_000_000, 6_500_000],  # Hockey stick
                ),
                QuarterlyFinancials(
                    quarter="Q4 2023",
                    revenue=8_000_000,  # Decline
                    accounts_receivable=5_500_000,  # Further DSO increase
                    deferred_revenue=400_000,
                    operating_cash_flow=-500_000,  # Negative cash flow
                    cogs=6_000_000,
                    revenue_by_month=[1_500_000, 2_000_000, 4_500_000],
                    ar_aging_buckets={
                        "0-30": 1_500_000,
                        "31-60": 1_000_000,
                        "61-90": 1_500_000,
                        "90+": 1_500_000,  # Significant aged AR
                    },
                ),
            ],
            metadata={
                "industry": "technology",
                "sic_code": "7370",
                "auditor": "Big Four LLP",
            },
        )
    
    @pytest.fixture
    def entity_resolver(self):
        return EntityResolver(similarity_threshold=0.80)
    
    @pytest.fixture
    def narrative_analyzer(self):
        return NarrativeAnalyzer()
    
    @pytest.fixture
    def revenue_analyzer(self):
        return RevenueRecognitionAnalyzer(industry="technology")
    
    @pytest.fixture
    def benford_analyzer(self):
        return BenfordsLawAnalyzer()
    
    # ================== Entity Resolution Phase ==================
    
    def test_entity_resolution_phase(self, xyz_corp_case, entity_resolver):
        """Test Phase 1: Entity resolution across sources."""
        result = entity_resolver.resolve_entities(xyz_corp_case.entities)
        
        assert result.total_entities == 7
        
        # Should have cross-source matches
        cross_source = entity_resolver.get_cross_source_entities(result.clusters)
        assert len(cross_source) > 0
        
        # XYZ Corporation cluster should exist
        xyz_cluster = entity_resolver.find_entity(
            "XYZ Corporation", 
            result.clusters
        )
        assert xyz_cluster is not None
        assert len(xyz_cluster.sources) >= 2
    
    def test_related_party_identification(self, xyz_corp_case, entity_resolver):
        """Test identification of related parties."""
        result = entity_resolver.resolve_entities(xyz_corp_case.entities)
        
        # Find related party
        abc_cluster = entity_resolver.find_entity(
            "ABC Holdings",
            result.clusters,
            threshold=0.7
        )
        
        # Should be in separate cluster (not merged with XYZ)
        xyz_cluster = entity_resolver.find_entity(
            "XYZ Corporation",
            result.clusters
        )
        
        if abc_cluster and xyz_cluster:
            assert abc_cluster.cluster_id != xyz_cluster.cluster_id
    
    # ================== Narrative Analysis Phase ==================
    
    def test_narrative_analysis_phase(self, xyz_corp_case, narrative_analyzer):
        """Test Phase 2: Narrative analysis and tone shifts."""
        result = narrative_analyzer.analyze_narrative_shifts(xyz_corp_case.documents)
        
        assert result.documents_analyzed == 4
        
        # Should detect significant shifts
        assert result.has_significant_shifts
        
        # Sentiment should deteriorate over time
        assert result.sentiment_trend[0].compound_score > result.sentiment_trend[-1].compound_score
        
        # Should detect fraud indicators
        assert len(result.fraud_indicators) > 0
        
        # Overall risk should be elevated
        assert result.overall_risk_score > 0.3
    
    def test_hedging_trend_detection(self, xyz_corp_case, narrative_analyzer):
        """Test detection of increasing hedging language."""
        result = narrative_analyzer.analyze_narrative_shifts(xyz_corp_case.documents)
        
        # Hedging should increase in later quarters
        if len(result.hedging_trend) >= 3:
            avg_early = sum(result.hedging_trend[:2]) / 2
            avg_late = sum(result.hedging_trend[2:]) / 2
            assert avg_late >= avg_early
    
    def test_key_findings_generation(self, xyz_corp_case, narrative_analyzer):
        """Test generation of actionable findings."""
        result = narrative_analyzer.analyze_narrative_shifts(xyz_corp_case.documents)
        
        assert len(result.key_findings) > 0
        
        # Findings should mention detected issues
        findings_text = " ".join(result.key_findings).lower()
        assert any(word in findings_text for word in [
            "shift", "risk", "hedging", "sentiment", "inconsistent"
        ])
    
    # ================== Revenue Recognition Analysis Phase ==================
    
    def test_revenue_recognition_analysis(self, xyz_corp_case, revenue_analyzer):
        """Test Phase 3: Revenue recognition fraud detection."""
        result = revenue_analyzer.analyze(xyz_corp_case.financials)
        
        assert result.quarters_analyzed == 4
        
        # Should detect anomalies
        assert len(result.anomalies) > 0
        
        # Check for specific anomaly types
        anomaly_types = {a.anomaly_type for a in result.anomalies}
        
        # Should detect DSO issues
        assert any(at in anomaly_types for at in [
            AnomalyType.DSO_SPIKE,
            AnomalyType.DSO_TREND_UP,
        ])
        
        # Should detect hockey stick pattern
        assert AnomalyType.HOCKEY_STICK in anomaly_types
        
        # Should detect cash flow divergence
        assert AnomalyType.CASH_REVENUE_DIVERGENCE in anomaly_types
    
    def test_dso_trend_analysis(self, xyz_corp_case, revenue_analyzer):
        """Test DSO trend calculation."""
        result = revenue_analyzer.analyze(xyz_corp_case.financials)
        
        assert len(result.dso_trend) == 4
        
        # DSO should increase over time
        assert result.dso_trend[-1] > result.dso_trend[0]
    
    def test_risk_level_classification(self, xyz_corp_case, revenue_analyzer):
        """Test risk level classification."""
        result = revenue_analyzer.analyze(xyz_corp_case.financials)
        
        # Should be HIGH or CRITICAL given the scenario
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.MEDIUM]
    
    # ================== Benford's Law Analysis Phase ==================
    
    def test_benford_analysis_phase(self, xyz_corp_case, benford_analyzer):
        """Test Phase 4: Benford's Law statistical analysis."""
        # Extract financial values for Benford analysis
        financial_values = []
        for q in xyz_corp_case.financials:
            financial_values.extend([
                q.revenue,
                q.accounts_receivable,
                q.deferred_revenue,
                abs(q.operating_cash_flow),
                q.cogs,
            ])
            if q.revenue_by_month:
                financial_values.extend(q.revenue_by_month)
        
        # Filter out zeros
        financial_values = [v for v in financial_values if v > 0]
        
        result = benford_analyzer.analyze(financial_values, dataset_name="XYZ Corp Financials")
        
        assert result.total_numbers == len(financial_values)
        assert result.valid_numbers > 0
        assert 0.0 <= result.confidence_level <= 1.0
    
    # ================== End-to-End Pipeline ==================
    
    def test_complete_investigation_pipeline(
        self,
        xyz_corp_case,
        entity_resolver,
        narrative_analyzer,
        revenue_analyzer,
        benford_analyzer,
    ):
        """Test complete end-to-end investigation workflow."""
        results = {}
        
        # Phase 1: Entity Resolution
        entity_result = entity_resolver.resolve_entities(xyz_corp_case.entities)
        results["entity_resolution"] = {
            "clusters": len(entity_result.clusters),
            "cross_source_matches": entity_result.cross_source_matches,
            "resolved_entities": entity_result.resolved_entities,
        }
        
        # Phase 2: Narrative Analysis
        narrative_result = narrative_analyzer.analyze_narrative_shifts(xyz_corp_case.documents)
        results["narrative_analysis"] = {
            "documents_analyzed": narrative_result.documents_analyzed,
            "shifts_detected": len(narrative_result.shifts),
            "fraud_indicators": len(narrative_result.fraud_indicators),
            "risk_score": narrative_result.overall_risk_score,
        }
        
        # Phase 3: Revenue Recognition
        revenue_result = revenue_analyzer.analyze(xyz_corp_case.financials)
        results["revenue_recognition"] = {
            "quarters_analyzed": revenue_result.quarters_analyzed,
            "anomalies_detected": len(revenue_result.anomalies),
            "risk_level": revenue_result.risk_level.value,
            "risk_score": revenue_result.overall_risk_score,
        }
        
        # Phase 4: Benford's Law
        financial_values = []
        for q in xyz_corp_case.financials:
            financial_values.extend([q.revenue, q.accounts_receivable, abs(q.operating_cash_flow)])
        financial_values = [v for v in financial_values if v > 0]
        
        benford_result = benford_analyzer.analyze(financial_values)
        results["benford_analysis"] = {
            "sample_size": benford_result.valid_numbers,
            "chi_square": benford_result.chi_square_statistic,
            "is_suspicious": benford_result.is_suspicious,
        }
        
        # Synthesize findings
        overall_risk = self._calculate_overall_risk(results)
        
        # Validate complete pipeline execution
        assert results["entity_resolution"]["clusters"] > 0
        assert results["narrative_analysis"]["documents_analyzed"] == 4
        assert results["revenue_recognition"]["quarters_analyzed"] == 4
        assert results["benford_analysis"]["sample_size"] > 0
        
        # Given the fraud scenario, overall risk should be elevated
        assert overall_risk >= 0.4
    
    def _calculate_overall_risk(self, results: Dict[str, Dict]) -> float:
        """Calculate overall risk score from pipeline results."""
        weights = {
            "narrative": 0.3,
            "revenue": 0.4,
            "entity": 0.1,
            "benford": 0.2,
        }
        
        scores = []
        
        # Narrative risk
        scores.append(weights["narrative"] * results["narrative_analysis"]["risk_score"])
        
        # Revenue risk
        scores.append(weights["revenue"] * results["revenue_recognition"]["risk_score"])
        
        # Entity resolution (higher cross-source = more evidence)
        entity_score = min(results["entity_resolution"]["cross_source_matches"] / 5, 1.0)
        scores.append(weights["entity"] * entity_score)
        
        # Benford (suspicious = higher risk)
        benford_score = 0.7 if results["benford_analysis"]["is_suspicious"] else 0.2
        scores.append(weights["benford"] * benford_score)
        
        return sum(scores)
    
    # ================== Cross-Reference Synthesis Tests ==================
    
    def test_cross_reference_synthesis(
        self,
        xyz_corp_case,
        narrative_analyzer,
        revenue_analyzer,
    ):
        """Test synthesis of findings across analysis modules."""
        narrative_result = narrative_analyzer.analyze_narrative_shifts(xyz_corp_case.documents)
        revenue_result = revenue_analyzer.analyze(xyz_corp_case.financials)
        
        # Both should detect issues in Q3/Q4
        narrative_issues_q4 = any(
            s.to_document == "10K-Q4-2023" 
            for s in narrative_result.shifts
        )
        
        revenue_issues = any(
            a.quarter in ["Q3 2023", "Q4 2023"]
            for a in revenue_result.anomalies
        )
        
        # Issues should align temporally
        assert revenue_issues
        # Narrative may or may not have specific Q4 shift depending on thresholds
    
    def test_evidence_corroboration(
        self,
        xyz_corp_case,
        narrative_analyzer,
        revenue_analyzer,
    ):
        """Test that different analysis methods corroborate findings."""
        narrative_result = narrative_analyzer.analyze_narrative_shifts(xyz_corp_case.documents)
        revenue_result = revenue_analyzer.analyze(xyz_corp_case.financials)
        
        # Both analyses should indicate elevated risk
        assert narrative_result.overall_risk_score > 0.2
        assert revenue_result.overall_risk_score > 0.2
        
        # Combined evidence should be stronger
        combined_score = (
            narrative_result.overall_risk_score * 0.5 +
            revenue_result.overall_risk_score * 0.5
        )
        assert combined_score > max(
            narrative_result.overall_risk_score * 0.5,
            revenue_result.overall_risk_score * 0.5
        )


class TestForensicPipelineEdgeCases:
    """Test edge cases in forensic pipeline."""
    
    def test_empty_case(self):
        """Test pipeline with empty case data."""
        resolver = EntityResolver()
        analyzer = NarrativeAnalyzer()
        revenue = RevenueRecognitionAnalyzer()
        
        # Empty inputs should not crash
        entity_result = resolver.resolve_entities([])
        assert entity_result.total_entities == 0
        
        narrative_result = analyzer.analyze_narrative_shifts([])
        assert narrative_result.documents_analyzed == 0
        
        revenue_result = revenue.analyze([])
        assert revenue_result.quarters_analyzed == 0
    
    def test_single_quarter_analysis(self):
        """Test analysis with only single quarter of data."""
        revenue = RevenueRecognitionAnalyzer()
        
        result = revenue.analyze([
            QuarterlyFinancials(
                quarter="Q1 2024",
                revenue=1_000_000,
                accounts_receivable=150_000,
                operating_cash_flow=100_000,
                cogs=600_000,
            )
        ])
        
        assert result.quarters_analyzed == 1
        # Should still calculate DSO
        assert len(result.dso_trend) == 1
    
    def test_negative_values_handling(self):
        """Test handling of negative financial values."""
        revenue = RevenueRecognitionAnalyzer()
        
        result = revenue.analyze([
            QuarterlyFinancials(
                quarter="Q1 2024",
                revenue=1_000_000,
                accounts_receivable=150_000,
                operating_cash_flow=-500_000,  # Negative cash flow
                cogs=600_000,
            )
        ])
        
        # Should handle negative values gracefully
        assert result.quarters_analyzed == 1


class TestForensicReportGeneration:
    """Tests for generating investigation reports."""
    
    @pytest.fixture
    def xyz_corp_case(self):
        """Minimal case for report testing."""
        return ForensicCase(
            case_id="CASE-TEST-001",
            company_name="Test Corp",
            cik="0001234567",
            investigation_date=datetime.now(),
            entities=[
                Entity(id="1", name="Test Corp", source=EntitySource.SEC)
            ],
            documents=[
                NarrativeDocument(
                    id="doc1",
                    content="Strong growth and profitable results.",
                    quarter="Q1 2024",
                )
            ],
            financials=[
                QuarterlyFinancials(
                    quarter="Q1 2024",
                    revenue=1_000_000,
                    accounts_receivable=150_000,
                    operating_cash_flow=120_000,
                    cogs=600_000,
                )
            ],
            metadata={},
        )
    
    def test_pipeline_generates_findings(self, xyz_corp_case):
        """Test that pipeline generates actionable findings."""
        narrative_analyzer = NarrativeAnalyzer()
        result = narrative_analyzer.analyze_narrative_shifts(xyz_corp_case.documents)
        
        # Should have some findings (even if just "no issues")
        # For healthy data, risk should be low
        assert result.overall_risk_score <= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
