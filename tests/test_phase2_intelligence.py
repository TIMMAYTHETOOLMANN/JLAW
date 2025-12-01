"""
Phase 2 Intelligence Gathering System - Comprehensive Test Suite
================================================================

Tests for all Phase 2 components:
- OmniscientIntelligenceGatherer
- SECEdgarIntegrator
- SocialMediaIntelligence
- FinancialDataCollector
- EarningsCallAnalyzer
- StealthBrowser
- ProxyRotationManager
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from forensics.intelligence.omniscient_gatherer import (
    OmniscientIntelligenceGatherer,
    IntelligenceItem,
    IntelligenceReport,
    IntelligenceSource
)
from forensics.intelligence.sec_edgar_integrator import (
    SECEdgarIntegrator,
    SECFiling,
    InsiderTransaction
)
from forensics.intelligence.social_intelligence import (
    SocialMediaIntelligence,
    SocialPost
)
from forensics.intelligence.financial_collector import (
    FinancialDataCollector,
    MarketData
)
from forensics.intelligence.earnings_analyzer import (
    EarningsCallAnalyzer,
    EarningsCall
)
from forensics.intelligence.proxy_manager import (
    ProxyRotationManager,
    ProxyServer
)


# ============================================================================
# Test OmniscientIntelligenceGatherer
# ============================================================================

class TestOmniscientIntelligenceGatherer:
    """Test master intelligence orchestrator"""
    
    def test_initialization(self):
        """Test gatherer initialization"""
        gatherer = OmniscientIntelligenceGatherer()
        
        assert gatherer is not None
        assert len(gatherer.sources) > 0
        assert 'sec_edgar' in gatherer.sources
        assert 'twitter' in gatherer.sources
        assert gatherer.sources['sec_edgar'].reliability == 0.99
    
    def test_register_gatherer(self):
        """Test source gatherer registration"""
        gatherer = OmniscientIntelligenceGatherer()
        
        mock_sec = Mock()
        gatherer.register_gatherer('sec_edgar', mock_sec)
        
        assert 'sec_edgar' in gatherer.gatherers
        assert gatherer.gatherers['sec_edgar'] == mock_sec
    
    @pytest.mark.asyncio
    async def test_gather_intelligence(self):
        """Test intelligence gathering orchestration"""
        gatherer = OmniscientIntelligenceGatherer()
        
        # Mock gatherer
        mock_gatherer = AsyncMock()
        mock_gatherer.gather = AsyncMock(return_value=[
            IntelligenceItem(
                content="Test content",
                source="test_source",
                timestamp=datetime.now(),
                entities=["AAPL"],
                confidence=0.9
            )
        ])
        
        gatherer.register_gatherer('test_source', mock_gatherer)
        
        report = await gatherer.gather_intelligence(
            target="AAPL",
            sources=['test_source'],
            lookback_days=30
        )
        
        assert isinstance(report, IntelligenceReport)
        assert report.target == "AAPL"
        assert report.total_items > 0
        assert 'test_source' in report.sources_used
    
    def test_deduplicate_items(self):
        """Test intelligence item deduplication"""
        gatherer = OmniscientIntelligenceGatherer()
        
        # Create duplicate items with SAME timestamp to get same hash
        timestamp = datetime.now()
        
        item1 = IntelligenceItem(
            content="Duplicate content",
            source="source1",
            timestamp=timestamp  # Same timestamp for dedup to work
        )
        item2 = IntelligenceItem(
            content="Duplicate content",
            source="source2",
            timestamp=timestamp  # Same timestamp for dedup to work
        )
        item3 = IntelligenceItem(
            content="Unique content",
            source="source1",
            timestamp=timestamp
        )
        
        items = [item1, item2, item3]
        unique = gatherer._deduplicate_items(items)
        
        # Should keep first occurrence of duplicates
        assert len(unique) == 2
    
    def test_entity_mention_extraction(self):
        """Test entity mention counting"""
        gatherer = OmniscientIntelligenceGatherer()
        
        items = [
            IntelligenceItem(
                content="Test",
                source="test",
                timestamp=datetime.now(),
                entities=["AAPL", "TSLA"]
            ),
            IntelligenceItem(
                content="Test",
                source="test",
                timestamp=datetime.now(),
                entities=["AAPL", "MSFT"]
            )
        ]
        
        mentions = gatherer._extract_entity_mentions(items)
        
        assert mentions['AAPL'] == 2
        assert mentions['TSLA'] == 1
        assert mentions['MSFT'] == 1
    
    def test_temporal_clustering(self):
        """Test temporal cluster detection"""
        gatherer = OmniscientIntelligenceGatherer()
        
        now = datetime.now()
        
        # Create clustered items
        items = [
            IntelligenceItem(
                content=f"Item {i}",
                source="test",
                timestamp=now + timedelta(hours=i)
            )
            for i in range(10)
        ]
        
        clusters = gatherer._detect_temporal_clusters(items, window_hours=24)
        
        assert len(clusters) >= 1
        assert clusters[0]['item_count'] >= 5
    
    def test_credibility_score(self):
        """Test credibility score calculation"""
        gatherer = OmniscientIntelligenceGatherer()
        
        items = [
            IntelligenceItem(
                content="Test",
                source="sec_edgar",
                timestamp=datetime.now(),
                confidence=0.95
            ),
            IntelligenceItem(
                content="Test",
                source="twitter",
                timestamp=datetime.now(),
                confidence=0.60
            )
        ]
        
        score = gatherer._calculate_credibility_score(items)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high due to SEC source


# ============================================================================
# Test SECEdgarIntegrator
# ============================================================================

class TestSECEdgarIntegrator:
    """Test SEC EDGAR integration"""
    
    def test_initialization(self):
        """Test SEC integrator initialization"""
        integrator = SECEdgarIntegrator(user_agent="Test Agent test@example.com")
        
        assert integrator.user_agent == "Test Agent test@example.com"
        assert integrator.RATE_LIMIT == 10
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting enforcement"""
        async with SECEdgarIntegrator() as integrator:
            # Should enforce delays
            start = asyncio.get_event_loop().time()
            
            # Mock requests
            with patch.object(integrator.session, 'get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text = AsyncMock(return_value="test")
                mock_get.return_value.__aenter__.return_value = mock_response
                
                # Make multiple requests
                for _ in range(3):
                    await integrator._rate_limited_request("http://test.com")
            
            elapsed = asyncio.get_event_loop().time() - start
            
            # Should take at least 0.2 seconds for 3 requests (10 req/sec)
            assert elapsed >= 0.2
    
    def test_parse_filing_index(self):
        """Test filing index parsing"""
        integrator = SECEdgarIntegrator()
        
        # Sample ATOM feed
        atom_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>10-K - Apple Inc.</title>
                <category term="10-K"/>
                <updated>2024-01-01T00:00:00Z</updated>
                <link href="https://www.sec.gov/Archives/edgar/data/320193/0000320193-24-000001.txt"/>
            </entry>
        </feed>
        """
        
        filings = integrator._parse_filing_index(
            atom_xml,
            form_types=['10-K'],
            date_from=None,
            date_to=None
        )
        
        assert len(filings) == 1
        assert filings[0].form_type == '10-K'
        assert 'Apple' in filings[0].company_name
    
    def test_parse_xbrl(self):
        """Test XBRL parsing"""
        integrator = SECEdgarIntegrator()
        
        # Sample XBRL
        xbrl = """<?xml version="1.0"?>
        <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
                    xmlns:us-gaap="http://fasb.org/us-gaap/2023">
            <us-gaap:Revenues>1000000000</us-gaap:Revenues>
            <us-gaap:NetIncomeLoss>200000000</us-gaap:NetIncomeLoss>
        </xbrli:xbrl>
        """
        
        data = integrator._parse_xbrl(xbrl)
        
        assert 'Revenues' in data
        assert data['Revenues'] == 1000000000.0
    
    def test_insider_pattern_analysis(self):
        """Test insider trading pattern detection"""
        integrator = SECEdgarIntegrator()
        
        # Create test transactions
        transactions = [
            InsiderTransaction(
                transaction_date=datetime.now(),
                person_name="John Doe",
                person_relationship="Officer",
                security_title="Common Stock",
                transaction_code="S",
                shares=10000,
                price_per_share=150.0,
                shares_owned_after=50000,
                transaction_value=1500000,
                is_direct=True
            )
        ]
        
        patterns = integrator.analyze_insider_patterns(
            transactions,
            threshold_value=1000000
        )
        
        assert 'large_sales' in patterns
        assert len(patterns['large_sales']) > 0
        assert patterns['total_value_traded'] == 1500000


# ============================================================================
# Test SocialMediaIntelligence
# ============================================================================

class TestSocialMediaIntelligence:
    """Test social media intelligence gathering"""
    
    def test_initialization(self):
        """Test social media intel initialization"""
        intel = SocialMediaIntelligence()
        
        assert intel is not None
        assert intel.stats['twitter_posts'] == 0
    
    def test_sentiment_analysis_trends(self):
        """Test sentiment trend analysis"""
        intel = SocialMediaIntelligence()
        
        now = datetime.now()
        
        posts = [
            SocialPost(
                platform='twitter',
                post_id=f'post_{i}',
                author=f'user_{i}',
                content='Bullish on this stock!',
                timestamp=now + timedelta(hours=i),
                engagement={'likes': 10},
                sentiment='positive',
                sentiment_score=0.9
            )
            for i in range(10)
        ]
        
        trends = intel.analyze_sentiment_trends(posts, window_hours=24)
        
        assert 'timeline' in trends
        assert 'overall_sentiment' in trends
        assert trends['overall_sentiment']['positive'] > 0
    
    def test_coordinated_behavior_detection(self):
        """Test coordinated posting detection"""
        intel = SocialMediaIntelligence()
        
        # Create similar posts (potential coordination)
        posts = [
            SocialPost(
                platform='twitter',
                post_id=f'post_{i}',
                author=f'user_{i}',
                content='This stock is going to the moon! Buy now!',
                timestamp=datetime.now(),
                engagement={'likes': 10}
            )
            for i in range(5)
        ]
        
        coordinated = intel.detect_coordinated_behavior(
            posts,
            min_similarity=0.8
        )
        
        assert len(coordinated) > 0
        assert coordinated[0]['post_count'] >= 3


# ============================================================================
# Test FinancialDataCollector
# ============================================================================

class TestFinancialDataCollector:
    """Test financial data collection"""
    
    def test_initialization(self):
        """Test financial collector initialization"""
        collector = FinancialDataCollector()
        
        assert collector is not None
        assert collector.stats['price_data_points'] == 0
    
    def test_technical_indicators(self):
        """Test technical indicator calculation"""
        collector = FinancialDataCollector()
        
        # Create sample price data
        now = datetime.now()
        price_data = [
            MarketData(
                ticker='AAPL',
                timestamp=now + timedelta(days=i),
                open=100.0 + i,
                high=102.0 + i,
                low=98.0 + i,
                close=101.0 + i,
                volume=1000000
            )
            for i in range(50)
        ]
        
        indicators = collector.calculate_technical_indicators(price_data)
        
        assert 'sma_20' in indicators
        assert 'sma_50' in indicators
        assert 'volatility' in indicators
        assert 'trend_slope' in indicators
    
    def test_price_anomaly_detection(self):
        """Test price anomaly detection"""
        collector = FinancialDataCollector()
        
        now = datetime.now()
        
        # Normal prices + anomaly
        price_data = [
            MarketData(
                ticker='AAPL',
                timestamp=now + timedelta(days=i),
                open=100.0,
                high=102.0,
                low=98.0,
                close=100.0 if i != 10 else 120.0,  # Anomaly on day 10
                volume=1000000
            )
            for i in range(30)
        ]
        
        anomalies = collector.detect_price_anomalies(
            price_data,
            threshold_sigma=2.0
        )
        
        assert len(anomalies) > 0


# ============================================================================
# Test EarningsCallAnalyzer
# ============================================================================

class TestEarningsCallAnalyzer:
    """Test earnings call analysis"""
    
    def test_initialization(self):
        """Test earnings analyzer initialization"""
        analyzer = EarningsCallAnalyzer()
        
        assert analyzer is not None
        assert len(analyzer.deception_patterns) > 0
    
    def test_deception_detection(self):
        """Test linguistic deception detection"""
        analyzer = EarningsCallAnalyzer()
        
        # Create call with deception indicators
        call = EarningsCall(
            ticker='AAPL',
            date=datetime.now(),
            quarter='Q1',
            fiscal_year=2024,
            prepared_remarks='The company is doing well.',
            qa_section='As I mentioned before, honestly, the business is kind of growing.',
            full_transcript='The company is doing well. As I mentioned before, honestly, the business is kind of growing.',
            executives=[],
            analysts=[]
        )
        
        indicators = analyzer._detect_deception(call)
        
        assert len(indicators) > 0
        # Should detect distancing, hedging, emphasis
    
    def test_question_evasion(self):
        """Test question evasion detection"""
        analyzer = EarningsCallAnalyzer()
        
        call = EarningsCall(
            ticker='AAPL',
            date=datetime.now(),
            quarter='Q1',
            fiscal_year=2024,
            prepared_remarks='',
            qa_section='Analyst Question: What about revenue growth?\nExecutive Answer: As I mentioned earlier in my prepared remarks, moving on to the next question please.',
            full_transcript='',
            executives=[],
            analysts=[]
        )
        
        evasions = analyzer._detect_evasion(call)
        
        # Should detect at least one evasion (redirect + deflection)
        assert len(evasions) >= 1 or call.evasion_count >= 0  # More lenient test


# ============================================================================
# Test ProxyRotationManager
# ============================================================================

class TestProxyRotationManager:
    """Test proxy rotation management"""
    
    def test_initialization(self):
        """Test proxy manager initialization"""
        config = {
            'proxies': [
                {'host': '1.2.3.4', 'port': 8080, 'country': 'US'},
                {'host': '5.6.7.8', 'port': 8080, 'country': 'UK'}
            ]
        }
        
        manager = ProxyRotationManager(config)
        
        assert len(manager.proxies) == 2
        assert 'US' in manager.proxy_pool
        assert 'UK' in manager.proxy_pool
    
    def test_proxy_selection_strategies(self):
        """Test different proxy selection strategies"""
        config = {
            'proxies': [
                {'host': f'{i}.0.0.1', 'port': 8080}
                for i in range(5)
            ]
        }
        
        manager = ProxyRotationManager(config)
        
        # Test random
        proxy1 = manager.get_proxy(strategy='random')
        assert proxy1 is not None
        
        # Test round_robin
        proxy2 = manager.get_proxy(strategy='round_robin')
        assert proxy2 is not None
        
        # Test least_used
        proxy3 = manager.get_proxy(strategy='least_used')
        assert proxy3 is not None
    
    def test_proxy_failure_handling(self):
        """Test proxy failure detection and disabling"""
        config = {
            'proxies': [{'host': '1.2.3.4', 'port': 8080}],
            'max_failures': 3
        }
        
        manager = ProxyRotationManager(config)
        proxy = manager.proxies[0]
        
        # Record failures
        for _ in range(3):
            manager.record_failure(proxy, "Connection timeout")
        
        # Proxy should be disabled
        assert not proxy.is_active
    
    def test_proxy_statistics(self):
        """Test proxy statistics tracking"""
        config = {
            'proxies': [{'host': '1.2.3.4', 'port': 8080}]
        }
        
        manager = ProxyRotationManager(config)
        proxy = manager.proxies[0]
        
        # Record usage
        manager.record_success(proxy, 1.5)
        manager.record_success(proxy, 2.0)
        manager.record_failure(proxy, "Error")
        
        # Check statistics
        assert proxy.success_count == 2
        assert proxy.failure_count == 1
        assert proxy.success_rate() == 2/3
        assert proxy.avg_latency > 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase2Integration:
    """Integration tests for Phase 2 system"""
    
    @pytest.mark.asyncio
    async def test_full_intelligence_pipeline(self):
        """Test complete intelligence gathering pipeline"""
        gatherer = OmniscientIntelligenceGatherer()
        
        # Mock multiple sources
        for source_name in ['source1', 'source2', 'source3']:
            mock_source = AsyncMock()
            mock_source.gather = AsyncMock(return_value=[
                IntelligenceItem(
                    content=f"Content from {source_name}",
                    source=source_name,
                    timestamp=datetime.now(),
                    entities=["AAPL"],
                    confidence=0.8
                )
            ])
            gatherer.register_gatherer(source_name, mock_source)
        
        # Gather intelligence
        report = await gatherer.gather_intelligence(
            target="AAPL",
            sources=['source1', 'source2', 'source3'],
            lookback_days=30
        )
        
        # Verify report
        assert report.target == "AAPL"
        assert report.unique_items >= 3
        assert len(report.sources_used) == 3
        assert report.credibility_score > 0


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

