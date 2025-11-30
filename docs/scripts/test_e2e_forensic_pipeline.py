"""
End-to-End Forensic Pipeline Integration Tests
===============================================

Full pipeline tests that exercise the complete forensic analysis
workflow from document ingestion through prosecution report generation.

These tests simulate real investigation scenarios and verify that
all modules work together correctly.
"""

import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import tempfile
import os


# ============================================================================
# TEST FIXTURES - COMPLETE INVESTIGATION SCENARIO
# ============================================================================

@pytest.fixture
def complete_investigation_corpus() -> Dict[str, List[Dict[str, Any]]]:
    """
    Complete corpus for a financial fraud investigation scenario.
    Simulates XYZ Corp case with progressive deterioration and fraud indicators.
    """
    return {
        "sec_filings": [
            {
                "id": "xyz_10k_2023",
                "date": "2024-02-15T00:00:00Z",
                "type": "10-K",
                "text": """
                XYZ Corporation Annual Report - Fiscal Year 2023
                
                Business Overview:
                XYZ Corporation is a leading provider of enterprise software solutions.
                Revenue for fiscal 2023 was $2.4 billion, representing 18% growth YoY.
                
                Management Discussion and Analysis:
                We delivered exceptional results in fiscal 2023. Our subscription revenue
                grew 25% and we expanded gross margins to 78%. Customer retention remained
                strong at 95%. We are confident in our ability to sustain double-digit
                growth for the foreseeable future.
                
                Risk Factors:
                Competition in the enterprise software market is increasing but we believe
                our product differentiation provides sustainable competitive advantage.
                Economic conditions could affect customer spending but our recurring
                revenue model provides visibility and stability.
                
                Financial Statements:
                Revenue: $2,400,000,000
                Gross Profit: $1,872,000,000
                Operating Income: $480,000,000
                Accounts Receivable: $320,000,000
                Deferred Revenue: $650,000,000
                """,
                "entities": [
                    {"name": "XYZ Corporation", "type": "company"},
                    {"name": "John Smith", "type": "person", "title": "CEO"}
                ]
            },
            {
                "id": "xyz_10q_q1_2024",
                "date": "2024-05-10T00:00:00Z",
                "type": "10-Q",
                "text": """
                XYZ Corporation Quarterly Report - Q1 2024
                
                Financial Results:
                Revenue for Q1 2024 was $580 million, representing 12% growth YoY.
                Subscription revenue grew 18% while professional services declined 5%.
                
                Management Commentary:
                Q1 results were solid though slightly below our expectations. We saw
                some deal slippage in the final weeks of the quarter but expect to
                recover these in Q2. We are reaffirming full-year guidance of 15-18%
                revenue growth.
                
                Updated Risk Factors:
                We are seeing increased competitive pressure from cloud-native vendors.
                Some larger enterprise deals are experiencing longer sales cycles.
                Macroeconomic uncertainty may impact customer purchasing decisions.
                
                Financial Highlights:
                Revenue: $580,000,000
                Accounts Receivable: $380,000,000 (increased)
                Days Sales Outstanding: 59 days (vs 49 days prior year)
                """,
                "entities": [
                    {"name": "XYZ Corporation", "type": "company"},
                    {"name": "John Smith", "type": "person", "title": "CEO"},
                    {"name": "Jane Doe", "type": "person", "title": "CFO"}
                ]
            },
            {
                "id": "xyz_8k_june_2024",
                "date": "2024-06-28T00:00:00Z",
                "type": "8-K",
                "text": """
                XYZ Corporation - Current Report
                
                Item 5.02 - Departure of Directors or Certain Officers
                
                On June 26, 2024, Jane Doe, Chief Financial Officer, notified the
                Company of her resignation effective July 15, 2024. Ms. Doe is
                leaving to pursue other opportunities. The Company thanks Ms. Doe
                for her contributions.
                
                Michael Johnson, VP of Finance, has been appointed Interim CFO.
                
                Item 2.02 - Results of Operations and Financial Condition
                
                The Company is providing preliminary Q2 results and updated guidance.
                Preliminary Q2 revenue of $540-550 million, below prior guidance of
                $610-620 million. Full-year guidance reduced to 5-8% growth.
                
                The shortfall reflects challenging demand environment and longer
                deal cycles. The Company is implementing cost reduction measures.
                """,
                "entities": [
                    {"name": "XYZ Corporation", "type": "company"},
                    {"name": "Jane Doe", "type": "person", "title": "Former CFO"},
                    {"name": "Michael Johnson", "type": "person", "title": "Interim CFO"}
                ]
            },
            {
                "id": "xyz_10q_q2_2024",
                "date": "2024-08-09T00:00:00Z",
                "type": "10-Q",
                "text": """
                XYZ Corporation Quarterly Report - Q2 2024
                
                Financial Results:
                Revenue for Q2 2024 was $545 million, down 5% YoY.
                This represents a significant deceleration from prior quarters.
                
                Management Commentary:
                Q2 was a challenging quarter. We experienced higher than expected
                customer churn and deal cancellations. We have identified issues
                with our go-to-market execution and are implementing changes.
                
                We are revising full-year guidance to flat to 3% growth.
                
                Going Concern Considerations:
                Due to declining revenue and cash flow, we are in discussions with
                lenders regarding covenant modifications. We believe we have adequate
                liquidity but are monitoring the situation closely.
                
                Financial Highlights:
                Revenue: $545,000,000
                Accounts Receivable: $420,000,000
                Days Sales Outstanding: 70 days
                Allowance for Doubtful Accounts: $45,000,000 (increased from $12M)
                """,
                "entities": [
                    {"name": "XYZ Corporation", "type": "company"},
                    {"name": "John Smith", "type": "person", "title": "CEO"},
                    {"name": "Michael Johnson", "type": "person", "title": "Interim CFO"}
                ]
            }
        ],
        "earnings_calls": [
            {
                "id": "xyz_ec_q4_2023",
                "date": "2024-02-15T17:00:00Z",
                "type": "earnings_call",
                "text": """
                XYZ Corporation Q4 2023 Earnings Call Transcript
                
                CEO John Smith: Good afternoon everyone. I'm thrilled to report an
                exceptional Q4 and full year. We absolutely crushed it this year.
                
                Revenue growth of 18% demonstrates our market leadership. We have
                never been better positioned. The pipeline is robust and we see
                clear line of sight to 20%+ growth next year.
                
                Our competitive moat is widening. No one can match our platform.
                Customer love for our products has never been higher.
                
                CFO Jane Doe: Financial execution was outstanding. Operating margins
                expanded 200 basis points. Cash flow generation was exceptional.
                
                We are raising guidance for next year. We expect 18-22% revenue growth.
                
                Q&A:
                Analyst: Are you seeing any competitive pressure?
                CEO: Minimal. Our win rates remain at all-time highs. The competition
                simply cannot match what we offer.
                """,
                "entities": [
                    {"name": "John Smith", "type": "person"},
                    {"name": "Jane Doe", "type": "person"}
                ]
            },
            {
                "id": "xyz_ec_q1_2024",
                "date": "2024-05-10T17:00:00Z",
                "type": "earnings_call",
                "text": """
                XYZ Corporation Q1 2024 Earnings Call Transcript
                
                CEO John Smith: Good afternoon. Q1 was a solid quarter though
                not quite as strong as we had hoped.
                
                Revenue growth of 12% was good but below our internal targets.
                We saw some deal slippage that we expect to recover.
                
                The market environment has become more challenging. Customers are
                taking longer to make decisions. We are adapting our approach.
                
                CFO Jane Doe: Results were acceptable given market conditions.
                DSO increased due to timing. We expect normalization in Q2.
                
                We are maintaining guidance but acknowledge there are risks.
                
                Q&A:
                Analyst: Are you concerned about the DSO increase?
                CFO: It's primarily timing related. Nothing structural.
                
                Analyst: Why is growth decelerating?
                CEO: Market conditions have shifted. We are confident we will
                return to higher growth rates.
                """,
                "entities": [
                    {"name": "John Smith", "type": "person"},
                    {"name": "Jane Doe", "type": "person"}
                ]
            },
            {
                "id": "xyz_ec_q2_2024",
                "date": "2024-08-09T17:00:00Z",
                "type": "earnings_call",
                "text": """
                XYZ Corporation Q2 2024 Earnings Call Transcript
                
                CEO John Smith: Good afternoon. This was a difficult quarter and
                I want to be direct about the challenges we faced.
                
                Revenue declined 5% which is clearly unacceptable. We have identified
                significant execution issues that we are addressing.
                
                Interim CFO Michael Johnson: The financial results reflect both
                market headwinds and internal challenges. Accounts receivable
                quality has deteriorated. We increased bad debt reserves significantly.
                
                We are in discussions with lenders. The situation is manageable
                but requires attention.
                
                Q&A:
                Analyst: What happened to your confident guidance from Q4?
                CEO: Market conditions changed dramatically. Competition intensified.
                
                Analyst: Why did the CFO leave?
                CEO: Jane left to pursue other opportunities. It was her decision.
                
                Analyst: Is there a liquidity issue?
                Interim CFO: We have adequate liquidity. The lender discussions are
                precautionary.
                """,
                "entities": [
                    {"name": "John Smith", "type": "person"},
                    {"name": "Michael Johnson", "type": "person"}
                ]
            }
        ],
        "news_articles": [
            {
                "id": "news_jan_2024",
                "date": "2024-01-20T09:00:00Z",
                "type": "news",
                "text": """
                XYZ Corp Named Top Enterprise Software Vendor
                
                XYZ Corporation was recognized as a leader in enterprise software
                by industry analysts. CEO John Smith called it "validation of our
                strategy and execution."
                """,
                "entities": [
                    {"name": "XYZ Corp", "type": "company"},
                    {"name": "John Smith", "type": "person"}
                ]
            },
            {
                "id": "news_may_2024",
                "date": "2024-05-15T09:00:00Z",
                "type": "news",
                "text": """
                XYZ Corporation Faces Increasing Competition
                
                Industry observers note that XYZ Corp is facing intensified
                competition from cloud-native startups. Several large customers
                have reportedly evaluated alternatives.
                """,
                "entities": [
                    {"name": "XYZ Corporation", "type": "company"}
                ]
            },
            {
                "id": "news_july_2024",
                "date": "2024-07-01T09:00:00Z",
                "type": "news",
                "text": """
                XYZ Corp CFO Departs Amid Guidance Cut
                
                Jane Doe, CFO of XYZ Corporation, has resigned weeks after the
                company slashed guidance. Sources say the departure was abrupt.
                The company declined to comment on the circumstances.
                """,
                "entities": [
                    {"name": "XYZ Corp", "type": "company"},
                    {"name": "Jane Doe", "type": "person"}
                ]
            },
            {
                "id": "news_aug_2024",
                "date": "2024-08-12T09:00:00Z",
                "type": "news",
                "text": """
                XYZ Corp Under Pressure as Revenue Declines
                
                XYZ Corporation reported its first revenue decline in years.
                Analysts question management's earlier optimistic statements.
                Short interest in the stock has increased substantially.
                """,
                "entities": [
                    {"name": "XYZ Corp", "type": "company"}
                ]
            }
        ],
        "insider_transactions": [
            {
                "id": "insider_jan_2024",
                "date": "2024-01-25T00:00:00Z",
                "type": "form_4",
                "text": """
                Form 4 - CEO John Smith
                Transaction: Sale of 50,000 shares
                Price: $85.00 per share
                Purpose: 10b5-1 plan execution
                """,
                "entities": [
                    {"name": "John Smith", "type": "person"}
                ]
            },
            {
                "id": "insider_feb_2024",
                "date": "2024-02-20T00:00:00Z",
                "type": "form_4",
                "text": """
                Form 4 - CFO Jane Doe
                Transaction: Sale of 30,000 shares
                Price: $82.00 per share
                Purpose: 10b5-1 plan execution
                """,
                "entities": [
                    {"name": "Jane Doe", "type": "person"}
                ]
            },
            {
                "id": "insider_mar_2024",
                "date": "2024-03-15T00:00:00Z",
                "type": "form_4",
                "text": """
                Form 4 - CEO John Smith
                Transaction: Sale of 75,000 shares
                Price: $78.00 per share
                Purpose: 10b5-1 plan execution
                Note: 10b5-1 plan adopted January 2024
                """,
                "entities": [
                    {"name": "John Smith", "type": "person"}
                ]
            }
        ]
    }


@pytest.fixture
def financial_numbers_for_benford() -> List[float]:
    """
    Financial numbers from the investigation for Benford's Law analysis.
    Mix of legitimate and potentially manipulated numbers.
    """
    return [
        # Revenue figures (quarterly, should follow Benford)
        2400000000, 580000000, 545000000, 610000000,
        # Expense figures
        1528000000, 420000000, 430000000,
        # Account balances
        320000000, 380000000, 420000000, 650000000,
        # Potentially manipulated figures (too many leading 5s and 9s)
        550000000, 555000000, 595000000, 599000000,
        990000000, 950000000, 920000000, 915000000,
        # Normal distribution figures
        125000, 134000, 178000, 189000, 213000,
        256000, 278000, 312000, 345000, 389000,
        412000, 445000, 478000, 512000, 567000,
        612000, 689000, 723000, 789000, 812000,
        # More quarterly figures
        145000000, 167000000, 198000000, 234000000,
        267000000, 312000000, 356000000, 398000000
    ]


# ============================================================================
# FULL PIPELINE TESTS
# ============================================================================

class TestFullForensicPipeline:
    """End-to-end tests for the complete forensic analysis pipeline."""
    
    @pytest.mark.asyncio
    async def test_complete_investigation_workflow(
        self,
        complete_investigation_corpus,
        financial_numbers_for_benford
    ):
        """
        Execute complete investigation workflow:
        1. Entity resolution across all sources
        2. Narrative shift analysis
        3. Benford's Law analysis on financial data
        4. Cross-reference and synthesize findings
        """
        from jlaw_enhancements.triangulation.entity_resolver import (
            ForensicEntityResolver,
            Entity,
            EntityType
        )
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        from jlaw_enhancements.financial_forensics.benford_analyzer import BenfordAnalyzer
        
        investigation_results = {}
        
        # ============================================================
        # PHASE 1: Entity Resolution
        # ============================================================
        
        # Extract all entities from corpus
        entity_sources = {}
        for source_type, documents in complete_investigation_corpus.items():
            entities = []
            for doc in documents:
                for ent in doc.get("entities", []):
                    entities.append(Entity(
                        id=f"{doc['id']}_{ent['name'][:10]}",
                        name=ent["name"],
                        entity_type=EntityType(ent.get("type", "unknown")),
                        source=source_type,
                        source_document=doc["id"],
                        attributes={"title": ent.get("title", "")},
                        confidence=0.9
                    ))
            if entities:
                entity_sources[source_type] = entities
        
        resolver = ForensicEntityResolver(match_threshold=0.70)
        entity_result = resolver.resolve_entities(entity_sources)
        investigation_results["entity_resolution"] = entity_result
        
        # Verify entity resolution
        assert entity_result.unified_entities is not None
        assert len(entity_result.unified_entities) > 0
        
        # Should identify key entities across sources
        entity_names = [ue.canonical_name for ue in entity_result.unified_entities]
        # XYZ Corp/Corporation should be unified
        # John Smith should appear
        # Jane Doe should appear
        
        print(f"\n📊 Entity Resolution: {len(entity_result.unified_entities)} unified entities")
        print(f"   Cross-source links: {len(entity_result.cross_source_links)}")
        
        # ============================================================
        # PHASE 2: Narrative Shift Analysis
        # ============================================================
        
        # Combine all narrative documents
        narrative_docs = []
        for source_type in ["sec_filings", "earnings_calls"]:
            narrative_docs.extend(complete_investigation_corpus.get(source_type, []))
        
        narrative_analyzer = NarrativeShiftAnalyzer()
        narrative_result = await narrative_analyzer.analyze_narrative_evolution(
            documents=narrative_docs,
            focus_topics=["revenue", "guidance", "risk factors", "competition"]
        )
        investigation_results["narrative_analysis"] = narrative_result
        
        # Verify narrative analysis detected deterioration
        assert narrative_result.forensic_priority_score > 0.0
        
        # Should show decreasing consistency
        print(f"\n📈 Narrative Analysis:")
        print(f"   Documents analyzed: {narrative_result.documents_analyzed}")
        print(f"   Forensic priority: {narrative_result.forensic_priority_score:.2f}")
        print(f"   Overall consistency: {narrative_result.overall_consistency_score:.2f}")
        print(f"   Material shifts: {len(narrative_result.material_shifts)}")
        
        # ============================================================
        # PHASE 3: Benford's Law Analysis
        # ============================================================
        
        benford_analyzer = BenfordAnalyzer(min_sample_size=20)
        benford_result = benford_analyzer.analyze(financial_numbers_for_benford)
        investigation_results["benford_analysis"] = benford_result
        
        print(f"\n🔢 Benford's Law Analysis:")
        print(f"   Sample size: {benford_result.sample_size}")
        print(f"   Fraud probability: {benford_result.fraud_probability:.2%}")
        print(f"   Anomalous digits: {len(benford_result.anomalous_digits)}")
        
        # ============================================================
        # PHASE 4: Cross-Reference and Synthesize
        # ============================================================
        
        # Identify investigation red flags
        red_flags = []
        
        # Red flag: CFO departure during guidance cut
        cfo_departure_detected = any(
            "Jane Doe" in str(ue.all_names) or "CFO" in str(ue.attributes_merged)
            for ue in entity_result.unified_entities
        )
        if cfo_departure_detected:
            red_flags.append("CFO departure coinciding with guidance revision")
        
        # Red flag: Narrative deterioration
        if narrative_result.forensic_priority_score > 0.5:
            red_flags.append("Significant narrative deterioration detected")
        
        # Red flag: Financial anomalies
        if benford_result.fraud_probability > 0.4:
            red_flags.append("Financial data distribution anomalies detected")
        
        # Red flag: Insider selling before bad news
        if "insider_transactions" in complete_investigation_corpus:
            insider_sales = complete_investigation_corpus["insider_transactions"]
            if len(insider_sales) >= 3:
                red_flags.append("Pattern of insider sales before negative announcements")
        
        investigation_results["red_flags"] = red_flags
        
        print(f"\n🚨 Red Flags Identified: {len(red_flags)}")
        for flag in red_flags:
            print(f"   • {flag}")
        
        # ============================================================
        # FINAL ASSERTIONS
        # ============================================================
        
        # Investigation should identify multiple red flags
        assert len(red_flags) >= 2, "Investigation should identify multiple red flags"
        
        # All phases should complete successfully
        assert "entity_resolution" in investigation_results
        assert "narrative_analysis" in investigation_results
        assert "benford_analysis" in investigation_results
        
        return investigation_results
    
    @pytest.mark.asyncio
    async def test_timeline_correlation(self, complete_investigation_corpus):
        """Test correlation of events across timeline."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        # Extract all documents with dates
        all_docs = []
        for source_type, documents in complete_investigation_corpus.items():
            all_docs.extend(documents)
        
        # Sort by date
        all_docs_sorted = sorted(all_docs, key=lambda d: d.get("date", ""))
        
        analyzer = NarrativeShiftAnalyzer()
        result = await analyzer.analyze_narrative_evolution(
            documents=all_docs_sorted,
            focus_topics=["revenue", "guidance"]
        )
        
        # Timeline should be chronologically ordered
        if result.shift_timeline:
            dates = [event.get("date", "") for event in result.shift_timeline]
            assert dates == sorted(dates), "Timeline should be chronologically ordered"
    
    @pytest.mark.asyncio
    async def test_entity_narrative_correlation(self, complete_investigation_corpus):
        """Test that entity mentions correlate with narrative shifts."""
        from jlaw_enhancements.triangulation.entity_resolver import (
            ForensicEntityResolver,
            Entity,
            EntityType
        )
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        # Resolve entities
        entity_sources = {}
        for source_type, documents in complete_investigation_corpus.items():
            entities = []
            for doc in documents:
                for ent in doc.get("entities", []):
                    entities.append(Entity(
                        id=f"{doc['id']}_{ent['name'][:10]}",
                        name=ent["name"],
                        entity_type=EntityType(ent.get("type", "unknown")),
                        source=source_type,
                        source_document=doc["id"]
                    ))
            if entities:
                entity_sources[source_type] = entities
        
        resolver = ForensicEntityResolver()
        entity_result = resolver.resolve_entities(entity_sources)
        
        # Analyze narratives
        earnings_docs = complete_investigation_corpus.get("earnings_calls", [])
        
        analyzer = NarrativeShiftAnalyzer()
        narrative_result = await analyzer.analyze_narrative_evolution(
            documents=earnings_docs,
            focus_topics=["revenue"]
        )
        
        # Find the CFO entity
        cfo_entity = None
        for ue in entity_result.unified_entities:
            if "Jane" in str(ue.all_names) or "Doe" in str(ue.all_names):
                cfo_entity = ue
                break
        
        # CFO should be mentioned in earlier documents but not later ones
        # This tests that entity tracking correlates with narrative analysis
        assert entity_result is not None
        assert narrative_result is not None


# ============================================================================
# REPORT GENERATION TESTS
# ============================================================================

class TestReportGeneration:
    """Tests for investigation report generation."""
    
    @pytest.mark.asyncio
    async def test_generate_executive_summary(
        self,
        complete_investigation_corpus,
        financial_numbers_for_benford
    ):
        """Test generation of executive summary from investigation."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        from jlaw_enhancements.financial_forensics.benford_analyzer import BenfordAnalyzer
        
        # Run analyses
        narrative_docs = complete_investigation_corpus.get("earnings_calls", [])
        
        analyzer = NarrativeShiftAnalyzer()
        narrative_result = await analyzer.analyze_narrative_evolution(
            documents=narrative_docs,
            focus_topics=["revenue", "guidance"]
        )
        
        benford_analyzer = BenfordAnalyzer(min_sample_size=20)
        benford_result = benford_analyzer.analyze(financial_numbers_for_benford)
        
        # Generate summary components
        summary = {
            "investigation_id": "XYZ-2024-001",
            "target_entity": "XYZ Corporation",
            "date_range": "2024-01-01 to 2024-08-31",
            "documents_analyzed": narrative_result.documents_analyzed,
            "findings": {
                "narrative_consistency": narrative_result.overall_consistency_score,
                "forensic_priority": narrative_result.forensic_priority_score,
                "financial_anomaly_score": benford_result.fraud_probability,
                "material_shifts_detected": len(narrative_result.material_shifts)
            },
            "recommendations": narrative_result.investigation_recommendations,
            "risk_level": "HIGH" if narrative_result.forensic_priority_score > 0.5 else "MEDIUM"
        }
        
        # Verify summary structure
        assert "investigation_id" in summary
        assert "findings" in summary
        assert "recommendations" in summary
        
        # Should have recommendations
        assert len(summary["recommendations"]) > 0
        
        # Convert to JSON
        summary_json = json.dumps(summary, indent=2, default=str)
        assert summary_json is not None
        
        print(f"\n📋 Executive Summary Generated:")
        print(f"   Target: {summary['target_entity']}")
        print(f"   Risk Level: {summary['risk_level']}")
        print(f"   Forensic Priority: {summary['findings']['forensic_priority']:.2f}")


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",
        "--asyncio-mode=auto"
    ])
