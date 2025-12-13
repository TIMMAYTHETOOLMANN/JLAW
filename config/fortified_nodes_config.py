"""
Configuration for Fortified Nodes 7-15
=====================================

Configuration constants for enhanced Node 7-15 implementations.
"""

# SEC EDGAR Configuration
# Reference: https://www.sec.gov/os/webmaster-faq#code-support
# SEC enforces rate limits of 10 requests per second for users with proper User-Agent declaration
SEC_EDGAR_BASE_URL = "https://data.sec.gov"
SEC_EDGAR_RATE_LIMIT = 10  # requests per second (official SEC limit)
SEC_EDGAR_USER_AGENT_DEFAULT = "JLAW Forensic System contact@example.com"

# Node 7: 13F-HR Institutional Holdings Configuration
WOLF_PACK_COORDINATION_THRESHOLD = 0.7  # 0.0-1.0 scale
WOLF_PACK_MIN_INSTITUTIONS = 3  # Minimum institutions for wolf pack detection
WOLF_PACK_WINDOW_DAYS = 30  # Temporal clustering window
WOLF_PACK_TEMPORAL_WINDOWS = [7, 14, 30]  # Days for multi-window analysis
WOLF_PACK_OWNERSHIP_THRESHOLD = 5.0  # Minimum aggregate ownership percentage

# Node 7: Quarterly Comparison
ACCUMULATION_THRESHOLD = 0.05  # 5% change threshold for accumulation detection

# Node 8: Beneficial Ownership Configuration
# December 2024 SEC Release No. 34-99232 compliance
SCHEDULE_13D_FILING_DEADLINE_DAYS = 5  # Business days from triggering event
SCHEDULE_13D_AMENDMENT_DEADLINE_DAYS = 2  # Business days for material amendments
SCHEDULE_13G_FILING_DEADLINE_DAYS = 45  # Calendar days
SCHEDULE_13G_AMENDMENT_DEADLINE_DAYS = 45  # Calendar days

# Node 8: Ownership Thresholds
OWNERSHIP_THRESHOLDS = {
    'filing_required': 5.0,  # 5% triggers Schedule 13D/13G
    'heightened_13d': 10.0,  # 10% requires heightened scrutiny
    'hsr_first': 20.0,  # Hart-Scott-Rodino first threshold
    'presumption_control': 25.0,  # Presumption of control
    'majority': 50.0  # Majority control
}

# Node 8: Group Coordination
GROUP_COORDINATION_THRESHOLD = 0.7  # Section 13(d)(3) group detection threshold

# Node 9: 8-K Material Event Configuration
ABNORMAL_VOLUME_THRESHOLD = 2.0  # 2x average volume
SIGNIFICANT_PRICE_MOVE_THRESHOLD = 0.05  # 5% price change
MARKET_IMPACT_LOOKBACK_DAYS = 5  # T-5 to T+5 analysis window
AVERAGE_VOLUME_CALCULATION_DAYS = 20  # 20-day average volume

# Node 9: Event Classification
HIGH_RISK_ITEMS = ['1.01', '1.02', '1.05', '2.01', '2.02', '2.05', '2.06', '4.01', '4.02', '5.01', '5.02']
CRITICAL_ITEMS = ['1.05', '2.06', '4.02', '5.01']  # Cybersecurity, impairments, restatements, control
NEGATIVE_ITEMS = ['1.02', '1.03', '1.05', '2.05', '2.06', '4.01', '4.02', '5.02']

# Cross-Node Correlation Configuration
MIN_CROSS_NODE_CORRELATION_SCORE = 0.6  # Minimum score for cross-node alert
CROSS_NODE_TEMPORAL_WINDOW_DAYS = 90  # Look for correlations within 90 days

# Polygon.io Market Data Configuration
POLYGON_BASE_URL = "https://api.polygon.io"
POLYGON_RATE_LIMIT = 5  # requests per second (conservative for basic plan)

# Market Hours (US Eastern Time)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 0

# US Market Holidays (simplified - month, day tuples)
US_MARKET_HOLIDAYS = {
    (1, 1),   # New Year's Day
    (7, 4),   # Independence Day
    (12, 25), # Christmas
    (12, 31)  # New Year's Eve (early close)
}

# ============================================
# Node 10: Form 144 Configuration
# ============================================
# Rule 144(d) holding periods
RULE_144_HOLDING_PERIOD_REPORTING = 180  # 6 months for reporting companies (days)
RULE_144_HOLDING_PERIOD_NON_REPORTING = 365  # 12 months for non-reporting (days)

# Rule 144(e) volume limitations
AFFILIATE_VOLUME_WINDOW_DAYS = 90  # 90-day window for affiliate volume aggregation
VOLUME_LIMIT_PERCENT_OUTSTANDING = 0.01  # 1% of outstanding shares

# ============================================
# Node 11: Network Analysis Configuration
# ============================================
# Neo4j Connection
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "${NEO4J_PASSWORD}"  # From environment

# Network Metrics
PAGERANK_DAMPENING_FACTOR = 0.85  # Standard PageRank dampening
BETWEENNESS_THRESHOLD = 0.1  # Threshold for high betweenness centrality
CLOSENESS_THRESHOLD = 0.3  # Threshold for high closeness centrality

# Temporal Analysis
TEMPORAL_WINDOW_QUARTERS = 8  # 2 years of quarterly windows

# ============================================
# Node 12: Earnings Call Analysis Configuration
# ============================================
# DeBERTa Model
DEBERTA_MODEL = "microsoft/deberta-v3-large"
CONTRADICTION_THRESHOLD = 0.7  # Confidence threshold for contradiction detection

# API Keys
SEEKING_ALPHA_API_KEY = "${SEEKING_ALPHA_KEY}"
REFINITIV_API_KEY = "${REFINITIV_KEY}"

# Hedging Analysis
HEDGING_KEYWORDS = [
    "may", "might", "could", "possibly", "potentially", "uncertain",
    "unclear", "difficult to predict", "challenging", "headwinds"
]

# ============================================
# Node 13: Z-Score Configuration
# ============================================
# Industry-specific settings
INDUSTRY_THRESHOLDS_ENABLED = True
SIC_CODE_RANGES = 28  # Number of industry categories (01xx-99xx in groups)

# Standard Z-Score thresholds
Z_SCORE_SAFE_ZONE = 2.99  # Above this: financially safe
Z_SCORE_GREY_ZONE_UPPER = 2.99
Z_SCORE_GREY_ZONE_LOWER = 1.81
Z_SCORE_DISTRESS_ZONE = 1.81  # Below this: distress

# Ensemble Model
ENSEMBLE_WEIGHTS = {
    "z": 0.4,      # Z-Score weight
    "f": 0.3,      # F-Score weight
    "market": 0.3  # Market signals weight
}

# ============================================
# Node 14: F-Score Configuration
# ============================================
# Piotroski F-Score
WEIGHTED_FSCORE_ENABLED = True
PIOTROSKI_BACKTESTING_ENABLED = True
PIOTROSKI_EXPECTED_ALPHA = 0.134  # 13.4% annual alpha claim

# Score thresholds
F_SCORE_STRONG_THRESHOLD = 7  # Scores 7-9 are strong
F_SCORE_WEAK_THRESHOLD = 3    # Scores 0-3 are weak

# GICS Sector Classification (simplified)
GICS_SECTORS = [
    "Energy", "Materials", "Industrials", "Consumer Discretionary",
    "Consumer Staples", "Health Care", "Financials", "Information Technology",
    "Communication Services", "Utilities", "Real Estate"
]

# ============================================
# Node 15: Market Correlation Configuration
# ============================================
# Polygon.io WebSocket
POLYGON_API_KEY = "${POLYGON_API_KEY}"
POLYGON_WEBSOCKET_URL = "wss://socket.polygon.io/stocks"
POLYGON_WEBSOCKET_RECONNECT_DELAY = 5  # Seconds

# Intraday Analysis
INTRADAY_EVENT_WINDOW_MINUTES = 60  # +/- 60 minutes around event
MINUTE_BAR_LOOKBACK = 390  # Full trading day (6.5 hours)

# Isolation Forest (Anomaly Detection)
ISOLATION_FOREST_CONTAMINATION = 0.01  # Expected proportion of outliers (1%)
ISOLATION_FOREST_N_ESTIMATORS = 100
ISOLATION_FOREST_MAX_SAMPLES = 256

# Correlation Analysis
CORRELATION_WINDOW_DAYS = 30  # Rolling window for correlation calculation
CONTAGION_CORRELATION_THRESHOLD = 0.7  # High correlation for contagion detection
