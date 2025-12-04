# Phase 2: Omniscient Intelligence Gathering System

## 🎯 Overview

Phase 2 implements a comprehensive multi-source intelligence gathering system for forensic investigations. This system aggregates data from regulatory filings, social media, market data, corporate communications, and web sources with advanced anti-detection capabilities.

## 🏗️ Architecture

```
intelligence/
├── omniscient_gatherer.py       # Master orchestrator
├── sec_edgar_integrator.py      # SEC EDGAR filing retrieval
├── social_intelligence.py       # Social media sentiment analysis
├── financial_collector.py       # Market data aggregation
├── earnings_analyzer.py         # Earnings call transcript analysis
├── stealth_browser.py           # Undetectable web scraping
└── proxy_manager.py             # Proxy rotation & management
```

## 📦 Components

### 1. OmniscientIntelligenceGatherer
**Master intelligence orchestrator coordinating all sources**

**Features:**
- Async parallel source gathering
- Real-time data fusion and correlation
- Entity resolution across sources
- Temporal co-occurrence detection
- Credibility scoring with source weighting
- Cross-source contradiction detection
- Intelligence deduplication

**Usage:**
```python
from forensics.intelligence import OmniscientIntelligenceGatherer

async with OmniscientIntelligenceGatherer() as gatherer:
    # Register source gatherers
    gatherer.register_gatherer('sec_edgar', sec_integrator)
    gatherer.register_gatherer('twitter', twitter_intel)
    
    # Gather intelligence
    report = await gatherer.gather_intelligence(
        target="AAPL",
        lookback_days=90,
        max_items=5000
    )
    
    print(f"Collected: {report.unique_items} items")
    print(f"Credibility: {report.credibility_score:.3f}")
    print(f"Temporal clusters: {len(report.temporal_clusters)}")
```

### 2. SECEdgarIntegrator
**Deep SEC filing extraction with XBRL parsing**

**Capabilities:**
- Complete filing retrieval (10-K, 10-Q, 8-K, DEF 14A, Form 4/3/5)
- XBRL financial data extraction
- Insider transaction analysis (Form 4)
- SEC compliance (10 req/sec limit)
- Insider trading pattern detection

**Form 4 Pattern Analysis:**
- Large sale detection
- Cluster activity identification
- Unusual timing detection

**Usage:**
```python
from forensics.intelligence import SECEdgarIntegrator

async with SECEdgarIntegrator() as integrator:
    # Get filings
    filings = await integrator.get_company_filings(
        ticker="TSLA",
        form_types=['10-K', '10-Q', '8-K'],
        date_from=datetime(2024, 1, 1),
        max_filings=20
    )
    
    # Get insider transactions
    transactions = await integrator.get_insider_transactions(
        ticker="TSLA",
        lookback_days=180
    )
    
    # Analyze patterns
    patterns = integrator.analyze_insider_patterns(
        transactions,
        threshold_value=1000000  # $1M+
    )
```

### 3. SocialMediaIntelligence
**Multi-platform sentiment analysis**

**Platforms:**
- Twitter/X API v2
- Reddit (PRAW)
- StockTwits
- Discord (optional)

**Features:**
- Real-time sentiment analysis (FinBERT)
- Trend detection and anomaly identification
- Coordinated behavior detection (pump & dump, FUD campaigns)
- Influencer tracking
- Sentiment timeline analysis

**Usage:**
```python
from forensics.intelligence import SocialMediaIntelligence

intel = SocialMediaIntelligence(config={
    'twitter_api_key': 'xxx',
    'reddit_client_id': 'xxx'
})

items = await intel.gather('AAPL', lookback_days=7)

# Analyze sentiment trends
trends = intel.analyze_sentiment_trends(posts, window_hours=24)

# Detect coordinated behavior
coordinated = intel.detect_coordinated_behavior(
    posts,
    min_similarity=0.8
)
```

### 4. FinancialDataCollector
**Market data intelligence**

**Data Sources:**
- Yahoo Finance (yfinance) - Free
- Polygon.io - Professional
- Alpha Vantage - API
- Unusual Whales - Options flow (premium)

**Analytics:**
- Price history & technical indicators
- Volume anomaly detection
- Price anomaly detection (statistical)
- SMA/trend analysis
- Volatility calculation

**Usage:**
```python
from forensics.intelligence import FinancialDataCollector

collector = FinancialDataCollector(config={
    'polygon_api_key': 'xxx'
})

items = await collector.gather('NVDA', lookback_days=90)

# Technical indicators
indicators = collector.calculate_technical_indicators(price_data)

# Detect anomalies
anomalies = collector.detect_price_anomalies(
    price_data,
    threshold_sigma=2.0
)
```

### 5. EarningsCallAnalyzer
**Corporate communications intelligence**

**Analysis Capabilities:**
- Tone and sentiment analysis (prepared vs Q&A)
- Linguistic deception detection
- Question evasion pattern detection
- Forward-looking statement extraction
- Tone shift analysis

**Deception Indicators:**
- Distancing language
- Hedging patterns
- Evasion tactics
- Emphasis markers
- Minimization language

**Usage:**
```python
from forensics.intelligence import EarningsCallAnalyzer

analyzer = EarningsCallAnalyzer()

items = await analyzer.gather('MSFT', lookback_days=365)

# Would analyze transcripts for:
# - Sentiment shifts
# - Deception indicators
# - Question evasion
# - Forward guidance
```

### 6. StealthBrowser
**Undetectable headless browsing**

**Anti-Detection Features:**
- undetected-playwright CDP bypass
- Fingerprint randomization
- Human-like behavior simulation
- Bot detection evasion
- CAPTCHA avoidance

**Usage:**
```python
from forensics.intelligence import StealthBrowser

async with StealthBrowser() as browser:
    # Navigate with anti-detection
    content = await browser.goto('https://example.com')
    
    # Extract structured data
    data = await browser.extract_structured_data(
        url='https://example.com',
        selectors={
            'title': 'h1.title',
            'price': '.price',
            'description': '.desc'
        }
    )
```

### 7. ProxyRotationManager
**Intelligent proxy management**

**Features:**
- Rotating residential/datacenter proxies
- Rate limit distribution
- Geographic distribution
- Automatic failure detection
- Performance-based selection

**Selection Strategies:**
- `round_robin`: Sequential rotation
- `random`: Random selection
- `best_performance`: Select by success rate
- `least_used`: Least recently used

**Usage:**
```python
from forensics.intelligence import ProxyRotationManager

manager = ProxyRotationManager(config={
    'proxies': [
        {'host': '1.2.3.4', 'port': 8080, 'country': 'US'},
        {'host': '5.6.7.8', 'port': 8080, 'country': 'UK'}
    ]
})

# Get proxy
proxy = manager.get_proxy(
    country='US',
    strategy='best_performance'
)

# Record usage
manager.record_success(proxy, latency=1.5)

# Test all proxies
await manager.test_proxies()
```

## 📊 Intelligence Report Structure

```python
IntelligenceReport:
  - target: Investigation subject
  - intelligence_items: List[IntelligenceItem]
  - entity_mentions: Dict[entity -> count]
  - temporal_clusters: List[activity_cluster]
  - contradictions: List[contradiction]
  - credibility_score: 0.0-1.0
  - sources_used: List[source_name]
  - collection_start/end: datetime
  - total_items / unique_items: int
```

## 🔧 Configuration

```python
config = {
    # API Keys
    'sec_user_agent': 'Company Name email@domain.com',
    'twitter_api_key': 'xxx',
    'reddit_client_id': 'xxx',
    'polygon_api_key': 'xxx',
    'alpha_vantage_key': 'xxx',
    
    # Proxy Configuration
    'proxies': [...],
    'min_success_rate': 0.5,
    'max_failures': 5,
    
    # Collection Parameters
    'default_lookback_days': 90,
    'max_items_per_source': 1000,
    'deduplication_enabled': True,
    'confidence_threshold': 0.6
}
```

## 🚀 Quick Start

```python
import asyncio
from forensics.intelligence import (
    OmniscientIntelligenceGatherer,
    SECEdgarIntegrator,
    SocialMediaIntelligence,
    FinancialDataCollector
)

async def investigate_company(ticker: str):
    # Initialize gatherer
    gatherer = OmniscientIntelligenceGatherer()
    
    # Register sources
    async with SECEdgarIntegrator() as sec:
        gatherer.register_gatherer('sec_edgar', sec)
    
    social = SocialMediaIntelligence()
    gatherer.register_gatherer('twitter', social)
    
    financial = FinancialDataCollector()
    gatherer.register_gatherer('yfinance', financial)
    
    # Gather intelligence
    report = await gatherer.gather_intelligence(
        target=ticker,
        lookback_days=90,
        max_items=10000
    )
    
    # Export report
    json_report = gatherer.export_report(report, format='json')
    
    # Analysis
    print(f"📊 Intelligence Report: {ticker}")
    print(f"   Items: {report.unique_items}")
    print(f"   Credibility: {report.credibility_score:.3f}")
    print(f"   Top Entities: {list(report.entity_mentions.keys())[:5]}")
    print(f"   Temporal Clusters: {len(report.temporal_clusters)}")
    print(f"   Contradictions: {len(report.contradictions)}")

asyncio.run(investigate_company('AAPL'))
```

## 📈 Performance Metrics

Each component tracks:
- Query execution count
- Items collected
- Success/failure rates
- Average latency
- Cache hit rates

```python
# Get metrics
metrics = gatherer.get_metrics()
print(f"Queries: {metrics['queries_executed']}")
print(f"Items: {metrics['items_collected']}")
print(f"Duplicates removed: {metrics['duplicates_removed']}")
```

## 🔒 Compliance & Ethics

**SEC EDGAR:**
- Mandatory User-Agent with company name and email
- 10 requests/second hard limit
- Respectful scraping practices

**Social Media:**
- API Terms of Service compliance
- Rate limit adherence
- No credential harvesting

**Stealth Browsing:**
- Educational/research purposes only
- Respect robots.txt
- No malicious activity

## 🧪 Testing

```bash
# Run Phase 2 tests
python -m pytest tests/test_phase2_intelligence.py -v

# Test specific components
python -m pytest tests/test_phase2_intelligence.py::test_sec_edgar -v
python -m pytest tests/test_phase2_intelligence.py::test_social_intel -v
```

## 📋 Dependencies

```
# Core
aiohttp>=3.9.0
asyncio

# SEC EDGAR
aiofiles>=23.0.0

# Social Media
transformers>=4.36.0
torch>=2.1.0

# Financial Data
yfinance>=0.2.32

# Stealth Browsing
playwright>=1.40.0

# NLP
spacy>=3.7.0
```

## 🎯 Phase 2 Completion Criteria

- [x] OmniscientIntelligenceGatherer implementation
- [x] SEC EDGAR integration with XBRL parsing
- [x] Insider transaction analysis (Form 4)
- [x] Social media intelligence framework
- [x] Financial data collector
- [x] Earnings call analyzer
- [x] Stealth browser with anti-detection
- [x] Proxy rotation manager
- [x] Temporal clustering
- [x] Cross-source contradiction detection
- [x] Credibility scoring
- [x] Export capabilities (JSON/HTML)

## 🔜 Next: Phase 3

Phase 3 will implement the Legal Statute Correlation Engine with:
- GovInfo API integration
- USC/CFR harvesting
- Neo4j legal knowledge graph
- ViolationDetector with pattern/semantic matching
- Legal-BERT NER for violation detection

---

**Status**: ✅ PHASE 2 IMPLEMENTATION COMPLETE

**Next Enhancement**: Legal Statute Correlation Engine (Phase 3)

