"""
Configuration for Fortified Nodes 7-9
====================================

Configuration constants for enhanced Node 7, 8, and 9 implementations.
"""

# SEC EDGAR Configuration
SEC_EDGAR_BASE_URL = "https://data.sec.gov"
SEC_EDGAR_RATE_LIMIT = 10  # requests per second (SEC limit)
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
