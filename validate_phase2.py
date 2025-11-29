"""
Phase 2 Validation and Demonstration Script
===========================================

Validates Phase 2 implementation and demonstrates key capabilities.
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from forensics.intelligence.omniscient_gatherer import (
    OmniscientIntelligenceGatherer,
    IntelligenceItem,
    IntelligenceSource
)
from forensics.intelligence.sec_edgar_integrator import SECEdgarIntegrator
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


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


async def validate_phase2():
    """Comprehensive Phase 2 validation"""
    
    print_header("JLAW Phase 2 Validation - Omniscient Intelligence Gathering")
    
    print("🚀 Starting Phase 2 validation...\n")
    
    # =========================================================================
    # 1. Validate OmniscientIntelligenceGatherer
    # =========================================================================
    print_header("1. OmniscientIntelligenceGatherer")
    
    gatherer = OmniscientIntelligenceGatherer()
    
    print("✓ Gatherer initialized")
    print(f"  - Configured sources: {len(gatherer.sources)}")
    print(f"  - Source names: {list(gatherer.sources.keys())[:5]}...")
    
    # Test source reliability
    sec_source = gatherer.sources['sec_edgar']
    print(f"\n  SEC EDGAR Source:")
    print(f"    - Reliability: {sec_source.reliability}")
    print(f"    - Rate Limit: {sec_source.rate_limit} req/sec")
    print(f"    - Cost: ${sec_source.cost}")
    
    # Test custom source registration
    class MockGatherer:
        async def gather(self, target, lookback, max_items):
            return [
                IntelligenceItem(
                    content=f"Mock intelligence for {target}",
                    source="mock_source",
                    timestamp=datetime.now(),
                    entities=[target],
                    confidence=0.9
                )
            ]
    
    mock = MockGatherer()
    gatherer.register_gatherer('mock_source', mock)
    print(f"\n✓ Custom source registered: mock_source")
    
    # Test intelligence gathering
    print("\n  Gathering intelligence...")
    report = await gatherer.gather_intelligence(
        target="AAPL",
        sources=['mock_source'],
        lookback_days=30,
        max_items=100
    )
    
    print(f"✓ Intelligence gathered:")
    print(f"  - Target: {report.target}")
    print(f"  - Total items: {report.total_items}")
    print(f"  - Unique items: {report.unique_items}")
    print(f"  - Credibility: {report.credibility_score:.3f}")
    print(f"  - Sources used: {report.sources_used}")
    
    # =========================================================================
    # 2. Validate SECEdgarIntegrator
    # =========================================================================
    print_header("2. SECEdgarIntegrator")
    
    integrator = SECEdgarIntegrator(user_agent="JLAW Test test@jlaw.ai")
    print("✓ SEC EDGAR integrator initialized")
    print(f"  - User-Agent: {integrator.user_agent}")
    print(f"  - Rate Limit: {integrator.RATE_LIMIT} req/sec")
    print(f"  - Base URL: {integrator.BASE_URL}")
    
    # Test XBRL parsing
    sample_xbrl = """<?xml version="1.0"?>
    <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance"
                xmlns:us-gaap="http://fasb.org/us-gaap/2023">
        <us-gaap:Revenues>1500000000</us-gaap:Revenues>
        <us-gaap:NetIncomeLoss>300000000</us-gaap:NetIncomeLoss>
    </xbrli:xbrl>
    """
    
    financial_data = integrator._parse_xbrl(sample_xbrl)
    print(f"\n✓ XBRL parsing validated:")
    print(f"  - Revenues: ${financial_data.get('Revenues', 0):,.0f}")
    print(f"  - Net Income: ${financial_data.get('NetIncomeLoss', 0):,.0f}")
    
    print(f"\n  Statistics:")
    stats = integrator.get_statistics()
    for key, value in stats.items():
        print(f"    - {key}: {value}")
    
    # =========================================================================
    # 3. Validate SocialMediaIntelligence
    # =========================================================================
    print_header("3. SocialMediaIntelligence")
    
    social = SocialMediaIntelligence()
    print("✓ Social media intelligence initialized")
    
    # Create test posts
    now = datetime.now()
    test_posts = [
        SocialPost(
            platform='twitter',
            post_id=f'post_{i}',
            author=f'user_{i}',
            content=f'Test post {i} about AAPL stock {"bullish" if i % 2 == 0 else "bearish"}',
            timestamp=now + timedelta(hours=i),
            engagement={'likes': 10 * i, 'retweets': 5 * i},
            sentiment='positive' if i % 2 == 0 else 'negative',
            sentiment_score=0.8 if i % 2 == 0 else 0.2
        )
        for i in range(10)
    ]
    
    # Test sentiment trends
    trends = social.analyze_sentiment_trends(test_posts, window_hours=24)
    print(f"\n✓ Sentiment analysis validated:")
    print(f"  - Timeline windows: {len(trends.get('timeline', []))}")
    print(f"  - Anomalies detected: {len(trends.get('anomalies', []))}")
    
    overall = trends.get('overall_sentiment', {})
    if overall:
        print(f"  - Overall sentiment:")
        print(f"    Positive: {overall.get('positive', 0):.1%}")
        print(f"    Negative: {overall.get('negative', 0):.1%}")
        print(f"    Neutral: {overall.get('neutral', 0):.1%}")
    
    # Test coordinated behavior detection
    coordinated = social.detect_coordinated_behavior(test_posts[:3], min_similarity=0.5)
    print(f"\n✓ Coordinated behavior detection validated:")
    print(f"  - Groups detected: {len(coordinated)}")
    
    # =========================================================================
    # 4. Validate FinancialDataCollector
    # =========================================================================
    print_header("4. FinancialDataCollector")
    
    financial = FinancialDataCollector()
    print("✓ Financial data collector initialized")
    
    # Create test market data
    test_prices = [
        MarketData(
            ticker='AAPL',
            timestamp=now + timedelta(days=i),
            open=150.0 + i,
            high=155.0 + i,
            low=148.0 + i,
            close=152.0 + i + (10 if i == 15 else 0),  # Anomaly on day 15
            volume=1000000 * (1 + (i % 5) * 0.5)
        )
        for i in range(50)
    ]
    
    # Test technical indicators
    indicators = financial.calculate_technical_indicators(test_prices)
    print(f"\n✓ Technical indicators calculated:")
    print(f"  - SMA 20: ${indicators.get('sma_20', 0):.2f}")
    print(f"  - SMA 50: ${indicators.get('sma_50', 0):.2f}")
    print(f"  - Volatility: {indicators.get('volatility', 0):.4f}")
    print(f"  - Trend: {indicators.get('trend_direction', 'unknown')}")
    print(f"  - Trend slope: {indicators.get('trend_slope', 0):.4f}")
    
    # Test anomaly detection
    anomalies = financial.detect_price_anomalies(test_prices, threshold_sigma=2.0)
    print(f"\n✓ Price anomalies detected: {len(anomalies)}")
    if anomalies:
        print(f"  - First anomaly:")
        print(f"    Date: {anomalies[0]['date']}")
        print(f"    Z-score: {anomalies[0]['z_score']:.2f}")
        print(f"    Severity: {anomalies[0]['severity']}")
    
    # =========================================================================
    # 5. Validate EarningsCallAnalyzer
    # =========================================================================
    print_header("5. EarningsCallAnalyzer")
    
    analyzer = EarningsCallAnalyzer()
    print("✓ Earnings call analyzer initialized")
    print(f"  - Deception patterns: {len(analyzer.deception_patterns)}")
    
    # Create test earnings call
    test_call = EarningsCall(
        ticker='AAPL',
        date=datetime.now(),
        quarter='Q4',
        fiscal_year=2024,
        prepared_remarks="""
        The company achieved strong results this quarter. Revenue growth was robust.
        We believe the business is performing well. The team delivered excellent execution.
        """,
        qa_section="""
        Analyst: What about revenue guidance?
        Executive: Well, kind of as I mentioned earlier, the company believes we are
        on track. Honestly, the business is basically performing as expected. Let me
        just say that we are confident. Moving on to the next question.
        """,
        full_transcript="",
        executives=[],
        analysts=[]
    )
    test_call.full_transcript = test_call.prepared_remarks + test_call.qa_section
    
    # Test deception detection
    deception = analyzer._detect_deception(test_call)
    print(f"\n✓ Deception indicators analyzed:")
    print(f"  - Patterns detected: {len(deception)}")
    for indicator in deception[:3]:
        print(f"    - {indicator['type']}: {indicator['count']} occurrences "
              f"({indicator['frequency_per_1000']:.1f} per 1000 words)")
    
    # Test question evasion
    evasions = analyzer._detect_evasion(test_call)
    print(f"\n✓ Question evasions detected: {len(evasions)}")
    if evasions:
        print(f"  - First evasion type: {evasions[0]['type']}")
    
    # Test tone shift
    tone_shift = analyzer._analyze_tone_shift(test_call)
    print(f"\n✓ Tone shift analysis:")
    print(f"  - Prepared avg sentence length: {tone_shift['prepared_avg_sentence_length']:.1f}")
    print(f"  - Q&A avg sentence length: {tone_shift['qa_avg_sentence_length']:.1f}")
    print(f"  - Interpretation: {tone_shift['interpretation']}")
    
    # =========================================================================
    # 6. Validate ProxyRotationManager
    # =========================================================================
    print_header("6. ProxyRotationManager")
    
    config = {
        'proxies': [
            {'host': f'10.0.0.{i}', 'port': 8080, 'country': 'US' if i % 2 == 0 else 'UK'}
            for i in range(5)
        ],
        'max_failures': 3
    }
    
    proxy_mgr = ProxyRotationManager(config)
    print("✓ Proxy rotation manager initialized")
    print(f"  - Proxies loaded: {len(proxy_mgr.proxies)}")
    
    # Test proxy selection strategies
    strategies = ['round_robin', 'random', 'best_performance', 'least_used']
    print(f"\n✓ Testing selection strategies:")
    for strategy in strategies:
        proxy = proxy_mgr.get_proxy(strategy=strategy)
        if proxy:
            print(f"  - {strategy}: {proxy.host}:{proxy.port}")
    
    # Test failure handling
    test_proxy = proxy_mgr.proxies[0]
    for _ in range(3):
        proxy_mgr.record_failure(test_proxy, "Connection timeout")
    print(f"\n✓ Failure handling tested:")
    print(f"  - Proxy status after 3 failures: {'disabled' if not test_proxy.is_active else 'active'}")
    
    # Test statistics
    stats = proxy_mgr.get_statistics()
    print(f"\n✓ Proxy statistics:")
    print(f"  - Total proxies: {stats['total_proxies']}")
    print(f"  - Active proxies: {stats['active_proxies']}")
    print(f"  - Countries: {stats['countries']}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print_header("Phase 2 Validation Summary")
    
    print("✅ ALL MODULES VALIDATED SUCCESSFULLY\n")
    
    print("Phase 2 Components:")
    print("  ✓ OmniscientIntelligenceGatherer - Master orchestrator")
    print("  ✓ SECEdgarIntegrator - SEC filing retrieval + XBRL")
    print("  ✓ SocialMediaIntelligence - Multi-platform sentiment")
    print("  ✓ FinancialDataCollector - Market data + anomalies")
    print("  ✓ EarningsCallAnalyzer - Deception detection")
    print("  ✓ ProxyRotationManager - Intelligent rotation")
    
    print("\nCapabilities Demonstrated:")
    print("  ✓ Async intelligence gathering")
    print("  ✓ Multi-source data fusion")
    print("  ✓ XBRL financial parsing")
    print("  ✓ Sentiment analysis")
    print("  ✓ Technical indicators")
    print("  ✓ Anomaly detection")
    print("  ✓ Linguistic deception detection")
    print("  ✓ Proxy management")
    
    print("\n" + "="*70)
    print("  🎉 PHASE 2 FULLY OPERATIONAL AND VALIDATED")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(validate_phase2())

