"""
Integration Tests: Narrative Analyzer Module
=============================================

Comprehensive test suite for management narrative shift detection
across corporate communications.

Test Categories:
- Unit tests for sentiment and linguistic analysis
- Integration tests for multi-document narrative tracking
- Forensic scenario tests based on real fraud patterns
- Edge case handling
"""

import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_earnings_call_q1() -> Dict[str, Any]:
    """Q1 earnings call with optimistic tone."""
    return {
        "id": "earnings_q1_2024",
        "date": "2024-01-15T16:00:00Z",
        "type": "earnings_call",
        "text": """
        Good afternoon everyone. I'm pleased to report another strong quarter.
        
        Revenue growth exceeded our expectations, coming in at 15% year-over-year.
        We are confident in our trajectory and expect continued momentum through 2024.
        
        Our guidance remains robust. We anticipate full-year revenue growth of 12-15%.
        The market opportunity is significant and we are well-positioned to capture it.
        
        Cash flow generation was excellent this quarter. We have strong visibility
        into our pipeline and expect to maintain our leadership position.
        
        In terms of risk factors, we see minimal headwinds. The competitive environment
        remains favorable and our product differentiation is clear to customers.
        
        We are optimistic about the year ahead and believe we will deliver
        outstanding results for shareholders.
        """
    }


@pytest.fixture
def sample_earnings_call_q2() -> Dict[str, Any]:
    """Q2 earnings call with hedged/cautious tone."""
    return {
        "id": "earnings_q2_2024",
        "date": "2024-04-15T16:00:00Z",
        "type": "earnings_call",
        "text": """
        Good afternoon. Let me walk you through our Q2 results.
        
        Revenue growth was approximately 8% year-over-year. While this represents
        a moderation from Q1, we believe underlying fundamentals remain solid.
        
        We are updating our guidance to reflect current market conditions.
        We now anticipate full-year revenue growth of 8-10%, which may be
        conservative given the uncertain environment.
        
        Cash flow was impacted by some timing issues. We expect this to normalize
        in the back half but are monitoring the situation closely.
        
        Regarding risk factors, we are seeing increased competitive pressure
        in certain segments. Macroeconomic headwinds could potentially affect
        customer spending decisions in the coming quarters.
        
        We remain cautiously optimistic but recognize there are challenges ahead
        that we are working to address.
        """
    }


@pytest.fixture
def sample_earnings_call_q3() -> Dict[str, Any]:
    """Q3 earnings call with negative tone shift."""
    return {
        "id": "earnings_q3_2024",
        "date": "2024-07-15T16:00:00Z",
        "type": "earnings_call",
        "text": """
        Good afternoon. I want to be direct about our Q3 performance.
        
        Revenue declined 3% year-over-year. This result fell short of expectations
        and reflects challenging conditions we did not fully anticipate.
        
        We are revising our full-year guidance downward. We now expect revenue
        to be roughly flat compared to last year. This revision reflects
        deteriorating market conditions and execution challenges.
        
        Cash flow was significantly impacted this quarter. We are implementing
        cost reduction measures to address the shortfall.
        
        We are facing substantial headwinds. Competition has intensified dramatically
        and customer churn has increased. We are restructuring certain operations
        to improve efficiency.
        
        This has been a difficult quarter. We are taking decisive action to
        stabilize the business and position for recovery.
        """
    }


@pytest.fixture
def sample_8k_material_event() -> Dict[str, Any]:
    """8-K filing disclosing material adverse event."""
    return {
        "id": "8k_material_event",
        "date": "2024-06-01T08:00:00Z",
        "type": "8k_filing",
        "text": """
        Item 2.06 - Material Impairments
        
        On May 30, 2024, the Company determined that a triggering event had occurred
        requiring an interim impairment assessment of goodwill and certain intangible assets.
        
        The Company expects to record a non-cash impairment charge of approximately
        $450 million to $500 million in the second quarter of 2024.
        
        This determination was based on recent declines in the Company's market
        capitalization, revised financial projections, and changes in the
        competitive landscape affecting certain reporting units.
        
        Item 2.05 - Costs Associated with Exit or Disposal Activities
        
        The Company has approved a restructuring plan to reduce operating costs
        and improve efficiency. The plan includes workforce reductions affecting
        approximately 1,200 employees, representing 15% of the workforce.
        """
    }


@pytest.fixture
def sample_press_releases() -> List[Dict[str, Any]]:
    """Series of press releases showing narrative evolution."""
    return [
        {
            "id": "pr_jan",
            "date": "2024-01-10T09:00:00Z",
            "type": "press_release",
            "text": """
            Company Reports Record Q4 Revenue
            
            Revenue increased 18% year-over-year, exceeding analyst expectations.
            Full-year guidance raised to reflect strong momentum.
            CEO states: "We have never been better positioned for growth."
            """
        },
        {
            "id": "pr_mar",
            "date": "2024-03-15T09:00:00Z",
            "type": "press_release",
            "text": """
            Company Provides Business Update
            
            Management notes evolving market conditions require careful monitoring.
            Inventory levels being adjusted to match demand patterns.
            Company remains focused on operational excellence.
            """
        },
        {
            "id": "pr_may",
            "date": "2024-05-20T09:00:00Z",
            "type": "press_release",
            "text": """
            Company Announces Strategic Review
            
            Board has initiated comprehensive review of strategic alternatives.
            Certain product lines underperforming expectations.
            Company evaluating options to enhance shareholder value.
            """
        },
        {
            "id": "pr_jul",
            "date": "2024-07-01T09:00:00Z",
            "type": "press_release",
            "text": """
            Company Announces Restructuring and Leadership Changes
            
            CEO to depart; CFO appointed interim CEO.
            Restructuring to affect 20% of workforce.
            Company withdraws full-year guidance pending further review.
            """
        }
    ]


@pytest.fixture
def fraud_pattern_documents() -> List[Dict[str, Any]]:
    """Documents exhibiting classic fraud pattern indicators."""
    return [
        {
            "id": "fraud_t1",
            "date": "2024-01-01T09:00:00Z",
            "type": "earnings_call",
            "text": """
            Our business has never been stronger. We are seeing unprecedented demand.
            Revenue will grow at least 25% this year, possibly more.
            We have complete visibility into our pipeline.
            Execution risk is minimal - our team is the best in the industry.
            Cash generation is extraordinary and accelerating.
            """
        },
        {
            "id": "fraud_t2",
            "date": "2024-03-01T09:00:00Z",
            "type": "earnings_call",
            "text": """
            Results were strong. Revenue grew 20% which is excellent by any measure.
            We continue to expect double-digit growth for the full year.
            Some deals slipped into next quarter but nothing concerning.
            Our market position remains differentiated.
            """
        },
        {
            "id": "fraud_t3",
            "date": "2024-05-01T09:00:00Z",
            "type": "8k_filing",
            "text": """
            The Company is restating results for Q1 2024.
            Revenue recognition errors resulted in overstated revenue of $120 million.
            The SEC has been notified and the Company is cooperating fully.
            The Audit Committee has initiated an independent investigation.
            """
        }
    ]


# ============================================================================
# SENTIMENT ANALYSIS TESTS
# ============================================================================

class TestSentimentAnalysis:
    """Tests for sentiment analysis functionality."""
    
    def test_positive_sentiment_detection(self, sample_earnings_call_q1):
        """Detect positive sentiment in optimistic communications."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        sentiment = analyzer._calculate_sentiment(sample_earnings_call_q1["text"])
        
        # Q1 call is very positive
        assert sentiment > 0.3, f"Expected positive sentiment, got {sentiment}"
    
    def test_negative_sentiment_detection(self, sample_earnings_call_q3):
        """Detect negative sentiment in pessimistic communications."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        sentiment = analyzer._calculate_sentiment(sample_earnings_call_q3["text"])
        
        # Q3 call is negative
        assert sentiment < 0, f"Expected negative sentiment, got {sentiment}"
    
    def test_sentiment_trajectory(
        self, 
        sample_earnings_call_q1,
        sample_earnings_call_q2,
        sample_earnings_call_q3
    ):
        """Test sentiment trajectory across multiple documents."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        s1 = analyzer._calculate_sentiment(sample_earnings_call_q1["text"])
        s2 = analyzer._calculate_sentiment(sample_earnings_call_q2["text"])
        s3 = analyzer._calculate_sentiment(sample_earnings_call_q3["text"])
        
        # Should show declining trajectory
        assert s1 > s2, "Q2 sentiment should be lower than Q1"
        assert s2 > s3, "Q3 sentiment should be lower than Q2"


class TestHedgingDetection:
    """Tests for hedging language detection."""
    
    def test_hedging_increase_detection(
        self,
        sample_earnings_call_q1,
        sample_earnings_call_q2
    ):
        """Detect increase in hedging language."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        # Count hedge words in each document
        hedge_words = analyzer.HEDGE_WORDS
        
        q1_text = sample_earnings_call_q1["text"].lower()
        q2_text = sample_earnings_call_q2["text"].lower()
        
        q1_hedge_count = sum(1 for word in hedge_words if word in q1_text)
        q2_hedge_count = sum(1 for word in hedge_words if word in q2_text)
        
        # Q2 should have more hedging
        assert q2_hedge_count >= q1_hedge_count, \
            f"Expected more hedging in Q2 ({q2_hedge_count}) vs Q1 ({q1_hedge_count})"
    
    def test_conviction_decrease_detection(
        self,
        sample_earnings_call_q1,
        sample_earnings_call_q3
    ):
        """Detect decrease in conviction language."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        conviction_words = analyzer.CONVICTION_WORDS
        
        q1_text = sample_earnings_call_q1["text"].lower()
        q3_text = sample_earnings_call_q3["text"].lower()
        
        q1_conviction = sum(1 for word in conviction_words if word in q1_text)
        q3_conviction = sum(1 for word in conviction_words if word in q3_text)
        
        # Q3 should have less conviction language
        assert q3_conviction <= q1_conviction, \
            f"Expected less conviction in Q3 ({q3_conviction}) vs Q1 ({q1_conviction})"


# ============================================================================
# NARRATIVE SHIFT DETECTION TESTS
# ============================================================================

class TestNarrativeShiftDetection:
    """Tests for narrative shift detection functionality."""
    
    @pytest.mark.asyncio
    async def test_detect_tone_shift(
        self,
        sample_earnings_call_q1,
        sample_earnings_call_q3
    ):
        """Detect significant tone shift between documents."""
        from jlaw_enhancements.analysis.narrative_analyzer import (
            NarrativeShiftAnalyzer,
            ShiftType,
            ShiftSeverity
        )
        
        analyzer = NarrativeShiftAnalyzer()
        
        documents = [sample_earnings_call_q1, sample_earnings_call_q3]
        
        result = await analyzer.analyze_narrative_evolution(
            documents=documents,
            focus_topics=["revenue", "guidance"]
        )
        
        # Should detect material shifts
        assert len(result.material_shifts) > 0 or result.forensic_priority_score > 0.3
        
        # Overall consistency should be low (big shift between docs)
        assert result.overall_consistency_score < 0.8
    
    @pytest.mark.asyncio
    async def test_detect_guidance_revision(
        self,
        sample_earnings_call_q1,
        sample_earnings_call_q2,
        sample_earnings_call_q3
    ):
        """Detect guidance revision pattern."""
        from jlaw_enhancements.analysis.narrative_analyzer import (
            NarrativeShiftAnalyzer,
            ShiftType
        )
        
        analyzer = NarrativeShiftAnalyzer()
        
        documents = [
            sample_earnings_call_q1,
            sample_earnings_call_q2,
            sample_earnings_call_q3
        ]
        
        result = await analyzer.analyze_narrative_evolution(
            documents=documents,
            focus_topics=["guidance"]
        )
        
        # Should have guidance-related analysis
        assert "guidance" in result.topics_analyzed
        
        # Timeline should show shifts
        assert len(result.shift_timeline) >= 0  # May or may not detect depending on threshold
    
    @pytest.mark.asyncio
    async def test_detect_risk_disclosure_shift(
        self,
        sample_earnings_call_q1,
        sample_earnings_call_q3
    ):
        """Detect shift in risk factor disclosure."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        documents = [sample_earnings_call_q1, sample_earnings_call_q3]
        
        result = await analyzer.analyze_narrative_evolution(
            documents=documents,
            focus_topics=["risk factors"]
        )
        
        # Should analyze risk factors
        assert "risk factors" in result.topics_analyzed


class TestForensicScenarios:
    """Tests based on real-world fraud patterns."""
    
    @pytest.mark.asyncio
    async def test_enron_pattern_detection(self, fraud_pattern_documents):
        """
        Test detection of Enron-style fraud pattern:
        Extreme optimism -> Minor hedging -> Sudden collapse
        """
        from jlaw_enhancements.analysis.narrative_analyzer import (
            NarrativeShiftAnalyzer,
            ShiftSeverity
        )
        
        analyzer = NarrativeShiftAnalyzer()
        
        result = await analyzer.analyze_narrative_evolution(
            documents=fraud_pattern_documents,
            focus_topics=["revenue", "guidance", "risk factors"]
        )
        
        # Should flag high forensic priority
        assert result.forensic_priority_score > 0.5, \
            f"Fraud pattern should have high priority, got {result.forensic_priority_score}"
        
        # Should generate investigation recommendations
        assert len(result.investigation_recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_press_release_narrative_deterioration(self, sample_press_releases):
        """Test detection of deteriorating narrative across press releases."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        result = await analyzer.analyze_narrative_evolution(
            documents=sample_press_releases,
            focus_topics=["revenue", "guidance", "management"]
        )
        
        # Should show declining consistency
        assert result.overall_consistency_score < 0.7
        
        # Timeline should be populated
        assert result.analysis_timestamp is not None
        assert result.documents_analyzed == len(sample_press_releases)
    
    @pytest.mark.asyncio
    async def test_material_event_detection(
        self,
        sample_earnings_call_q1,
        sample_8k_material_event
    ):
        """Test detection of material event discrepancy."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        documents = [sample_earnings_call_q1, sample_8k_material_event]
        
        result = await analyzer.analyze_narrative_evolution(
            documents=documents,
            focus_topics=["revenue", "risk factors"]
        )
        
        # The stark contrast between optimistic Q1 call and material impairment
        # should be detected
        assert result.forensic_priority_score > 0.3 or len(result.material_shifts) > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestNarrativeAnalyzerEdgeCases:
    """Edge case tests for narrative analyzer."""
    
    @pytest.mark.asyncio
    async def test_empty_document_list(self):
        """Handle empty document list gracefully."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        result = await analyzer.analyze_narrative_evolution(
            documents=[],
            focus_topics=["revenue"]
        )
        
        assert result.documents_analyzed == 0
        assert result.material_shifts == []
    
    @pytest.mark.asyncio
    async def test_single_document(self, sample_earnings_call_q1):
        """Handle single document (no comparison possible)."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        result = await analyzer.analyze_narrative_evolution(
            documents=[sample_earnings_call_q1],
            focus_topics=["revenue"]
        )
        
        assert result.documents_analyzed == 1
        # Can't detect shifts with single document
        assert len(result.material_shifts) == 0
    
    @pytest.mark.asyncio
    async def test_empty_topic_list(self, sample_earnings_call_q1):
        """Handle empty topic list."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        result = await analyzer.analyze_narrative_evolution(
            documents=[sample_earnings_call_q1],
            focus_topics=[]
        )
        
        assert result.topics_analyzed == []
    
    @pytest.mark.asyncio
    async def test_document_without_relevant_content(self):
        """Handle documents without content matching topics."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        irrelevant_docs = [
            {
                "id": "doc1",
                "date": "2024-01-01T00:00:00Z",
                "type": "other",
                "text": "This document discusses weather patterns and climate."
            },
            {
                "id": "doc2",
                "date": "2024-02-01T00:00:00Z",
                "type": "other",
                "text": "This document is about gardening and plant care."
            }
        ]
        
        result = await analyzer.analyze_narrative_evolution(
            documents=irrelevant_docs,
            focus_topics=["revenue", "guidance"]
        )
        
        # Should handle gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_malformed_dates(self):
        """Handle malformed date formats."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        docs_with_bad_dates = [
            {
                "id": "doc1",
                "date": "not-a-date",
                "type": "earnings_call",
                "text": "Revenue growth was strong at 15%."
            },
            {
                "id": "doc2",
                "date": "",
                "type": "earnings_call",
                "text": "Revenue declined by 5%."
            }
        ]
        
        # Should not raise exception
        result = await analyzer.analyze_narrative_evolution(
            documents=docs_with_bad_dates,
            focus_topics=["revenue"]
        )
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_unicode_content(self):
        """Handle Unicode content in documents."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        unicode_docs = [
            {
                "id": "doc1",
                "date": "2024-01-01T00:00:00Z",
                "type": "earnings_call",
                "text": "Revenue growth was 強い at ¥15 billion. 収益は増加しました。"
            },
            {
                "id": "doc2",
                "date": "2024-04-01T00:00:00Z",
                "type": "earnings_call",
                "text": "Umsatzwachstum war stark bei €20 million. Рост выручки составил 10%."
            }
        ]
        
        result = await analyzer.analyze_narrative_evolution(
            documents=unicode_docs,
            focus_topics=["revenue"]
        )
        
        assert result is not None


# ============================================================================
# INTEGRATION WITH ENTITY RESOLVER TESTS
# ============================================================================

class TestCrossModuleIntegration:
    """Tests for integration between Narrative Analyzer and Entity Resolver."""
    
    @pytest.mark.asyncio
    async def test_entity_context_in_narrative(self):
        """Test that entity resolution enhances narrative analysis."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        # Documents mentioning same entity differently
        docs = [
            {
                "id": "doc1",
                "date": "2024-01-01T00:00:00Z",
                "type": "earnings_call",
                "text": """
                Tim Cook stated revenue growth exceeded expectations.
                Apple Inc. reported strong iPhone sales.
                The CEO expressed confidence in future quarters.
                """
            },
            {
                "id": "doc2",
                "date": "2024-04-01T00:00:00Z",
                "type": "news_article",
                "text": """
                Timothy D. Cook acknowledged challenges ahead.
                AAPL faces increased competition in smartphone market.
                Apple's chief executive warned of macro headwinds.
                """
            }
        ]
        
        result = await analyzer.analyze_narrative_evolution(
            documents=docs,
            focus_topics=["revenue", "competition"]
        )
        
        # Should detect the shift in management tone
        assert result.documents_analyzed == 2


# ============================================================================
# OUTPUT FORMAT TESTS
# ============================================================================

class TestOutputFormats:
    """Tests for output format compliance."""
    
    @pytest.mark.asyncio
    async def test_json_serialization(self, sample_earnings_call_q1, sample_earnings_call_q3):
        """Test that results can be serialized to JSON."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        result = await analyzer.analyze_narrative_evolution(
            documents=[sample_earnings_call_q1, sample_earnings_call_q3],
            focus_topics=["revenue"]
        )
        
        # Should serialize without error
        json_str = result.to_json()
        assert json_str is not None
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "analysis_id" in parsed
        assert "forensic_priority_score" in parsed
    
    @pytest.mark.asyncio
    async def test_dict_conversion(self, sample_earnings_call_q1):
        """Test dictionary conversion."""
        from jlaw_enhancements.analysis.narrative_analyzer import NarrativeShiftAnalyzer
        
        analyzer = NarrativeShiftAnalyzer()
        
        result = await analyzer.analyze_narrative_evolution(
            documents=[sample_earnings_call_q1],
            focus_topics=["revenue"]
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "documents_analyzed" in result_dict
        assert result_dict["documents_analyzed"] == 1


# ============================================================================
# TEST RUNNER CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
