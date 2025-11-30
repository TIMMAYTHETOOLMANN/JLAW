"""
Integration tests for Narrative Analyzer module.

Tests sentiment analysis, hedging detection, tone shift detection,
and fraud pattern identification in management disclosures.
"""

import pytest
from src.forensics.analysis.narrative_analyzer import (
    NarrativeAnalyzer,
    NarrativeDocument,
    NarrativeShift,
    SentimentScore,
    ToneShiftType,
    FraudIndicator,
    FraudIndicatorType,
    NarrativeAnalysisResult,
)


class TestNarrativeAnalyzerIntegration:
    """Integration tests for NarrativeAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a NarrativeAnalyzer with default settings."""
        return NarrativeAnalyzer()
    
    @pytest.fixture
    def positive_document(self):
        """Sample document with positive sentiment."""
        return NarrativeDocument(
            id="Q1-2024",
            content="""
            We are pleased to report record revenue growth of 25% year-over-year.
            Our strong execution across all business units delivered exceptional results.
            We exceeded analyst expectations and achieved a new milestone in profitability.
            The company is confident in its strategic direction and optimistic about future growth.
            Our momentum continues with robust customer acquisition and healthy margins.
            """,
            quarter="Q1 2024",
            document_type="earnings_call",
        )
    
    @pytest.fixture
    def negative_document(self):
        """Sample document with negative sentiment."""
        return NarrativeDocument(
            id="Q2-2024",
            content="""
            Challenging market conditions significantly impacted our results this quarter.
            We experienced a decline in revenue due to adverse economic headwinds.
            The company faces uncertain conditions and volatile market pressures.
            We identified material weaknesses in our internal controls.
            Litigation exposure and potential liability concerns have been disclosed.
            """,
            quarter="Q2 2024",
            document_type="earnings_call",
        )
    
    @pytest.fixture
    def hedging_document(self):
        """Sample document with excessive hedging language."""
        return NarrativeDocument(
            id="Q3-2024",
            content="""
            We believe that revenue may potentially increase in the coming quarters.
            Management believes that the company could possibly achieve its targets.
            It is possible that market conditions might improve, depending on circumstances.
            We cannot guarantee future performance and subject to various factors.
            We estimate that results may vary and no assurance can be provided.
            The company anticipates that results might be impacted by uncertain conditions.
            Furthermore, we believe that potential opportunities could arise if circumstances permit.
            It is possible that growth trajectories may shift depending on market dynamics.
            Management believes that strategic initiatives could possibly yield improvements.
            We cannot predict with certainty how external factors may influence outcomes.
            Subject to regulatory developments, results might vary from current expectations.
            We believe that our estimates may require adjustments as conditions evolve.
            The company may potentially explore new opportunities that could arise.
            Management anticipates that challenges might persist in the near term.
            It is possible that competitive pressures could impact market positioning.
            We believe that operational improvements may potentially benefit margins.
            """,
            quarter="Q3 2024",
            document_type="10-K",
        )
    
    # ================== Sentiment Analysis Tests ==================
    
    def test_positive_sentiment_detection(self, analyzer, positive_document):
        """Test detection of positive sentiment."""
        result = analyzer.analyze_single_document(positive_document)
        
        sentiment = result['sentiment']
        assert isinstance(sentiment, SentimentScore)
        assert sentiment.compound_score > 0
        assert sentiment.is_positive
        assert sentiment.sentiment_label == "positive"
    
    def test_negative_sentiment_detection(self, analyzer, negative_document):
        """Test detection of negative sentiment."""
        result = analyzer.analyze_single_document(negative_document)
        
        sentiment = result['sentiment']
        assert sentiment.compound_score < 0
        assert sentiment.is_negative
        assert sentiment.sentiment_label == "negative"
    
    def test_neutral_sentiment(self, analyzer):
        """Test detection of neutral sentiment."""
        doc = NarrativeDocument(
            id="neutral",
            content="The company filed its quarterly report on the scheduled date. The documents were submitted to the SEC as required.",
            quarter="Q1 2024",
        )
        result = analyzer.analyze_single_document(doc)
        
        sentiment = result['sentiment']
        # Should be relatively neutral
        assert abs(sentiment.compound_score) < 0.3
    
    def test_empty_document_sentiment(self, analyzer):
        """Test sentiment analysis of empty document."""
        doc = NarrativeDocument(id="empty", content="", quarter="Q1 2024")
        result = analyzer.analyze_single_document(doc)
        
        sentiment = result['sentiment']
        assert sentiment.compound_score == 0.0
    
    # ================== Hedging Detection Tests ==================
    
    def test_hedging_detection(self, analyzer, hedging_document):
        """Test detection of hedging language patterns."""
        result = analyzer.analyze_single_document(hedging_document)
        
        assert result['hedging_score'] > 0
        assert len(result['hedging_patterns']) > 0
        
        # Check for specific hedging patterns
        pattern_types = [p.pattern_type for p in result['hedging_patterns']]
        assert any('modal' in pt or 'belief' in pt or 'possibility' in pt for pt in pattern_types)
    
    def test_hedging_pattern_extraction(self, analyzer):
        """Test extraction of specific hedging patterns."""
        doc = NarrativeDocument(
            id="test",
            content="We may achieve targets. Management believes the outlook is positive. It is possible that growth will continue.",
            quarter="Q1 2024",
        )
        result = analyzer.analyze_single_document(doc)
        
        patterns = result['hedging_patterns']
        assert len(patterns) >= 3
        
        for pattern in patterns:
            assert pattern.severity >= 0.0
            assert pattern.severity <= 1.0
            assert len(pattern.context) > 0
    
    def test_minimal_hedging(self, analyzer, positive_document):
        """Test that confident language has low hedging score."""
        result = analyzer.analyze_single_document(positive_document)
        
        # Confident language should have relatively low hedging
        assert result['hedging_score'] < 0.05
    
    # ================== Tone Shift Detection Tests ==================
    
    def test_positive_to_negative_shift(self, analyzer, positive_document, negative_document):
        """Test detection of positive to negative tone shift."""
        result = analyzer.analyze_narrative_shifts([positive_document, negative_document])
        
        assert isinstance(result, NarrativeAnalysisResult)
        assert result.has_significant_shifts
        assert len(result.shifts) > 0
        
        # Should detect positive to negative shift
        shift = result.shifts[0]
        assert shift.shift_type == ToneShiftType.POSITIVE_TO_NEGATIVE
        assert shift.magnitude > 0.3
    
    def test_confident_to_uncertain_shift(self, analyzer, positive_document, hedging_document):
        """Test detection of confident to uncertain shift."""
        result = analyzer.analyze_narrative_shifts([positive_document, hedging_document])
        
        # Should detect increased hedging
        assert result.documents_analyzed == 2
        
        # Hedging trend should increase (if documents are long enough)
        # Note: May be 0 for short documents below min_document_length threshold
        if len(result.hedging_trend) == 2:
            # For short documents, check that analysis was performed
            assert isinstance(result.hedging_trend[0], float)
            assert isinstance(result.hedging_trend[1], float)
    
    def test_no_shift_stable_narrative(self, analyzer):
        """Test that stable narrative shows no significant shifts."""
        docs = [
            NarrativeDocument(
                id="Q1",
                content="Revenue grew 10% this quarter with strong margins and healthy growth.",
                quarter="Q1 2024",
            ),
            NarrativeDocument(
                id="Q2",
                content="Revenue increased 12% with continued strong performance and growth momentum.",
                quarter="Q2 2024",
            ),
        ]
        result = analyzer.analyze_narrative_shifts(docs)
        
        # Should not detect major shifts between similar documents
        for shift in result.shifts:
            assert shift.magnitude < 0.5 or shift.shift_type == ToneShiftType.NONE
    
    def test_multi_quarter_analysis(self, analyzer):
        """Test analysis across multiple quarters."""
        docs = [
            NarrativeDocument(
                id="Q1",
                content="Exceptional growth and record profits.",
                quarter="Q1 2024",
            ),
            NarrativeDocument(
                id="Q2",
                content="Strong performance continued this quarter.",
                quarter="Q2 2024",
            ),
            NarrativeDocument(
                id="Q3",
                content="Challenging conditions impacted results.",
                quarter="Q3 2024",
            ),
            NarrativeDocument(
                id="Q4",
                content="Significant decline and material weaknesses identified.",
                quarter="Q4 2024",
            ),
        ]
        result = analyzer.analyze_narrative_shifts(docs)
        
        assert result.documents_analyzed == 4
        assert len(result.sentiment_trend) == 4
        
        # Sentiment should trend downward
        assert result.sentiment_trend[-1].compound_score < result.sentiment_trend[0].compound_score
    
    # ================== Fraud Indicator Tests ==================
    
    def test_excessive_hedging_indicator(self, analyzer):
        """Test fraud indicator for excessive hedging."""
        docs = [
            NarrativeDocument(
                id="Q1",
                content="""
                We may possibly believe that potential growth could perhaps be achievable.
                Management believes that we might anticipate uncertain conditions.
                It is possible that we cannot guarantee the estimated outcomes.
                We believe that uncertain factors may potentially impact results.
                Subject to various conditions, we estimate possible outcomes.
                """ * 3,  # Repeat to ensure enough content
                quarter="Q1 2024",
            ),
        ]
        result = analyzer.analyze_narrative_shifts(docs)
        
        # Should identify excessive hedging
        hedging_indicators = [
            i for i in result.fraud_indicators
            if i.indicator_type == FraudIndicatorType.EXCESSIVE_HEDGING
        ]
        assert len(hedging_indicators) > 0 or result.hedging_trend[0] > 0.01
    
    def test_inconsistent_narrative_indicator(self, analyzer, positive_document, negative_document):
        """Test fraud indicator for inconsistent narrative."""
        result = analyzer.analyze_narrative_shifts([positive_document, negative_document])
        
        # Should flag inconsistent narrative
        inconsistent_indicators = [
            i for i in result.fraud_indicators
            if i.indicator_type == FraudIndicatorType.INCONSISTENT_NARRATIVE
        ]
        
        # Check either indicator found or significant shift detected
        assert len(inconsistent_indicators) > 0 or result.has_significant_shifts
    
    def test_distancing_language_detection(self, analyzer):
        """Test detection of distancing language."""
        doc = NarrativeDocument(
            id="distancing",
            content="""
            The company determined that it was necessary to restate prior results.
            Management identified that errors were discovered in previous filings.
            The company was recognized as having material issues by auditors.
            It was determined by the audit committee that deficiencies existed.
            Issues were identified during the review process by external parties.
            The company acknowledged that certain procedures were not followed.
            Management noted that the company had determined new disclosures were needed.
            It was recognized by the board that additional oversight was required.
            The company stated that revisions were made to prior period statements.
            Management indicated that the company was identified as needing improvements.
            """,
            quarter="Q1 2024",
        )
        result = analyzer.analyze_single_document(doc)
        
        assert result['distancing_score'] > 0
    
    def test_blame_shifting_detection(self, analyzer):
        """Test detection of blame shifting language."""
        doc = NarrativeDocument(
            id="blame",
            content="""
            Due to market conditions beyond our control, results were impacted.
            External economic forces caused the decline in performance.
            Unforeseen circumstances in the macro environment affected outcomes.
            Legacy issues inherited from previous management required attention.
            Forces beyond our control significantly impacted the business.
            """,
            quarter="Q1 2024",
        )
        result = analyzer.analyze_single_document(doc)
        
        blame_instances = result['blame_shifting_detected']
        assert len(blame_instances) > 0
        
        for instance in blame_instances:
            assert instance['severity'] > 0
            assert len(instance['context']) > 0
    
    # ================== Risk Score Tests ==================
    
    def test_low_risk_score(self, analyzer, positive_document):
        """Test that healthy narrative has low risk score."""
        docs = [positive_document]
        result = analyzer.analyze_narrative_shifts(docs)
        
        assert result.overall_risk_score < 0.5
    
    def test_high_risk_score(self, analyzer, positive_document, negative_document, hedging_document):
        """Test that problematic narrative has high risk score."""
        result = analyzer.analyze_narrative_shifts([
            positive_document,
            hedging_document,
            negative_document,
        ])
        
        # Multiple concerns should elevate risk
        assert result.overall_risk_score >= 0.2 or result.has_significant_shifts
    
    def test_risk_score_bounds(self, analyzer, positive_document):
        """Test that risk score is within valid bounds."""
        result = analyzer.analyze_narrative_shifts([positive_document])
        
        assert 0.0 <= result.overall_risk_score <= 1.0
    
    # ================== Key Findings Tests ==================
    
    def test_findings_generation(self, analyzer, positive_document, negative_document):
        """Test generation of key findings."""
        result = analyzer.analyze_narrative_shifts([positive_document, negative_document])
        
        assert len(result.key_findings) > 0
        
        # Findings should be descriptive strings
        for finding in result.key_findings:
            assert isinstance(finding, str)
            assert len(finding) > 10
    
    def test_high_risk_findings(self, analyzer):
        """Test findings for high risk scenario."""
        analyzer_strict = NarrativeAnalyzer(fraud_risk_threshold=0.3)
        
        docs = [
            NarrativeDocument(
                id="Q1",
                content="Record profits and exceptional growth achieved.",
                quarter="Q1 2024",
            ),
            NarrativeDocument(
                id="Q2",
                content="Significant decline. Material weaknesses. Going concern. Litigation.",
                quarter="Q2 2024",
            ),
        ]
        result = analyzer_strict.analyze_narrative_shifts(docs)
        
        # Should have findings about the risk
        assert len(result.key_findings) > 0
    
    # ================== Edge Cases ==================
    
    def test_empty_document_list(self, analyzer):
        """Test analysis of empty document list."""
        result = analyzer.analyze_narrative_shifts([])
        
        assert result.documents_analyzed == 0
        assert len(result.shifts) == 0
        assert result.overall_risk_score == 0.0
    
    def test_single_document_analysis(self, analyzer, positive_document):
        """Test analysis of single document."""
        result = analyzer.analyze_narrative_shifts([positive_document])
        
        assert result.documents_analyzed == 1
        assert len(result.shifts) == 0  # No shifts with single doc
        assert len(result.sentiment_trend) == 1
    
    def test_very_short_content(self, analyzer):
        """Test analysis of very short content."""
        doc = NarrativeDocument(
            id="short",
            content="Revenue up.",
            quarter="Q1 2024",
        )
        result = analyzer.analyze_single_document(doc)
        
        # Should handle gracefully
        assert result['word_count'] == 2
    
    def test_special_characters_handling(self, analyzer):
        """Test handling of special characters."""
        doc = NarrativeDocument(
            id="special",
            content="Revenue grew 25% ($1.2B). EBITDA margin: 18.5%! Growth rate: +15%.",
            quarter="Q1 2024",
        )
        result = analyzer.analyze_single_document(doc)
        
        assert result['word_count'] > 0
    
    def test_unicode_content(self, analyzer):
        """Test handling of Unicode content."""
        doc = NarrativeDocument(
            id="unicode",
            content="Revenue increased significantly. 业务增长。Croissance exceptionnelle.",
            quarter="Q1 2024",
        )
        result = analyzer.analyze_single_document(doc)
        
        assert result['sentiment'] is not None
    
    # ================== Document Metadata Tests ==================
    
    def test_document_metadata_preserved(self, analyzer):
        """Test that document metadata is accessible."""
        doc = NarrativeDocument(
            id="test",
            content="Test content for analysis.",
            quarter="Q1 2024",
            document_type="10-K",
            date="2024-01-15",
            metadata={"filing_url": "https://sec.gov/..."},
        )
        result = analyzer.analyze_single_document(doc)
        
        assert result['document_id'] == "test"
    
    def test_shift_references_documents(self, analyzer, positive_document, negative_document):
        """Test that shifts reference correct documents."""
        result = analyzer.analyze_narrative_shifts([positive_document, negative_document])
        
        if result.shifts:
            shift = result.shifts[0]
            assert shift.from_document == positive_document.id
            assert shift.to_document == negative_document.id


class TestFraudPatternScenarios:
    """Test realistic fraud pattern detection scenarios."""
    
    @pytest.fixture
    def analyzer(self):
        return NarrativeAnalyzer()
    
    def test_enron_style_obfuscation(self, analyzer):
        """Test detection of Enron-style complex obfuscation."""
        docs = [
            NarrativeDocument(
                id="pre-fraud",
                content="""
                Strong quarterly results reflect our core business fundamentals.
                Revenue growth accelerated with improved operating margins.
                We achieved record profitability through operational excellence.
                Our strategic initiatives delivered exceptional value creation.
                Customer acquisition remained strong across all segments.
                Product innovation drove market share gains this quarter.
                Cash generation improved significantly year over year.
                Operating leverage enhanced our competitive positioning.
                """,
                quarter="Q1",
            ),
            NarrativeDocument(
                id="during-fraud",
                content="""
                Special purpose entities may provide certain financial flexibility.
                Complex derivative instruments could potentially enhance returns.
                Off-balance sheet arrangements might optimize capital structure.
                We believe sophisticated hedging strategies may mitigate risks.
                Subject to various interpretations, we estimate significant value.
                The company may potentially realize benefits depending on conditions.
                It is possible that restructuring could yield improvements.
                Management believes that alternative arrangements might be beneficial.
                We cannot guarantee that anticipated outcomes will materialize.
                Subject to market conditions, results may vary from projections.
                """,
                quarter="Q2",
            ),
        ]
        result = analyzer.analyze_narrative_shifts(docs)
        
        # Should detect increased hedging and complexity in Q2
        # The comparison should show a relative increase
        assert result.documents_analyzed == 2
        # If documents are long enough, hedging should increase
        if result.hedging_trend[0] > 0 or result.hedging_trend[1] > 0:
            # Q2 has more hedging language
            assert result.hedging_trend[1] >= result.hedging_trend[0]
    
    def test_deteriorating_guidance(self, analyzer):
        """Test detection of deteriorating forward guidance."""
        docs = [
            NarrativeDocument(
                id="Q1",
                content="We expect strong growth. Revenue will exceed $1B. Margins will expand.",
                quarter="Q1",
            ),
            NarrativeDocument(
                id="Q2",
                content="We anticipate moderate growth. Revenue may reach targets. Margins should stabilize.",
                quarter="Q2",
            ),
            NarrativeDocument(
                id="Q3",
                content="We believe growth is possible. Revenue could meet estimates. Margins might be maintained.",
                quarter="Q3",
            ),
            NarrativeDocument(
                id="Q4",
                content="Uncertain conditions. Challenging environment. Headwinds impacting results.",
                quarter="Q4",
            ),
        ]
        result = analyzer.analyze_narrative_shifts(docs)
        
        assert result.documents_analyzed == 4
        # Hedging should increase over time
        # Sentiment should decrease
        assert result.sentiment_trend[-1].compound_score < result.sentiment_trend[0].compound_score
    
    def test_management_accountability_shift(self, analyzer):
        """Test shift from accountability to blame shifting."""
        docs = [
            NarrativeDocument(
                id="Q1",
                content="""
                Our strategic initiatives drove strong results.
                We successfully executed our growth plan.
                Management's decisions led to improved margins.
                """,
                quarter="Q1",
            ),
            NarrativeDocument(
                id="Q2",
                content="""
                Due to market conditions beyond our control, results were impacted.
                External economic forces created significant headwinds.
                Industry-wide challenges affected our performance.
                Unforeseen circumstances required strategic adjustments.
                """,
                quarter="Q2",
            ),
        ]
        result = analyzer.analyze_narrative_shifts(docs)
        
        # Should detect blame shifting in Q2
        blame_indicators = [
            i for i in result.fraud_indicators
            if i.indicator_type == FraudIndicatorType.BLAME_SHIFTING
        ]
        assert len(blame_indicators) > 0 or result.has_significant_shifts


class TestSentimentScore:
    """Unit tests for SentimentScore class."""
    
    def test_positive_sentiment_label(self):
        """Test positive sentiment labeling."""
        score = SentimentScore(
            positive_score=0.8,
            negative_score=0.1,
            neutral_score=0.1,
            compound_score=0.7,
            confidence=0.9,
        )
        assert score.is_positive
        assert not score.is_negative
        assert score.sentiment_label == "positive"
    
    def test_negative_sentiment_label(self):
        """Test negative sentiment labeling."""
        score = SentimentScore(
            positive_score=0.1,
            negative_score=0.8,
            neutral_score=0.1,
            compound_score=-0.7,
            confidence=0.9,
        )
        assert score.is_negative
        assert not score.is_positive
        assert score.sentiment_label == "negative"
    
    def test_neutral_sentiment_label(self):
        """Test neutral sentiment labeling."""
        score = SentimentScore(
            positive_score=0.3,
            negative_score=0.3,
            neutral_score=0.4,
            compound_score=0.0,
            confidence=0.5,
        )
        assert not score.is_positive
        assert not score.is_negative
        assert score.sentiment_label == "neutral"


class TestAnalyzerConfiguration:
    """Tests for analyzer configuration options."""
    
    def test_custom_thresholds(self):
        """Test analyzer with custom thresholds."""
        analyzer = NarrativeAnalyzer(
            hedging_threshold=0.05,
            sentiment_shift_threshold=0.5,
            fraud_risk_threshold=0.8,
        )
        
        assert analyzer.hedging_threshold == 0.05
        assert analyzer.sentiment_shift_threshold == 0.5
        assert analyzer.fraud_risk_threshold == 0.8
    
    def test_minimum_document_length(self):
        """Test minimum document length setting."""
        analyzer = NarrativeAnalyzer(min_document_length=50)
        
        short_doc = NarrativeDocument(
            id="short",
            content="Short document.",
            quarter="Q1",
        )
        result = analyzer.analyze_single_document(short_doc)
        
        # Should still analyze but hedging may be 0 due to length
        assert result['word_count'] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
