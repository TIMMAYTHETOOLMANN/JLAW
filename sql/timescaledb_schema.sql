-- ============================================================================
-- JLAW TimescaleDB Schema
-- ============================================================================
-- 
-- This schema supports time-series forensic analysis of financial data:
-- - Stock prices and market data
-- - Financial metrics over time
-- - Trading volumes and patterns
-- - Executive compensation trends
-- - Forensic event timeline
--
-- TimescaleDB Extension: Provides hypertable functionality for efficient
-- time-series data storage and querying.
-- ============================================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ============================================================================
-- TABLE: market_data
-- ============================================================================
-- Store historical stock price and volume data
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    open DECIMAL(12, 4),
    high DECIMAL(12, 4),
    low DECIMAL(12, 4),
    close DECIMAL(12, 4) NOT NULL,
    volume BIGINT,
    adjusted_close DECIMAL(12, 4),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, ticker)
);

-- Convert to hypertable for efficient time-series operations
SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_market_data_ticker_time ON market_data (ticker, time DESC);

-- Add compression policy (compress data older than 7 days)
SELECT add_compression_policy('market_data', INTERVAL '7 days', if_not_exists => TRUE);

-- ============================================================================
-- TABLE: financial_metrics
-- ============================================================================
-- Store quarterly/annual financial metrics from SEC filings
CREATE TABLE IF NOT EXISTS financial_metrics (
    time TIMESTAMPTZ NOT NULL,
    cik VARCHAR(10) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 4),
    metric_unit VARCHAR(20),
    period_type VARCHAR(10), -- Q1, Q2, Q3, Q4, FY
    filing_date DATE,
    form_type VARCHAR(10),
    accession_number VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, cik, metric_name)
);

-- Convert to hypertable
SELECT create_hypertable('financial_metrics', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_financial_metrics_cik_time ON financial_metrics (cik, time DESC);
CREATE INDEX IF NOT EXISTS idx_financial_metrics_metric ON financial_metrics (metric_name, time DESC);

-- Add compression policy
SELECT add_compression_policy('financial_metrics', INTERVAL '30 days', if_not_exists => TRUE);

-- ============================================================================
-- TABLE: forensic_events
-- ============================================================================
-- Store forensic events and timeline markers
CREATE TABLE IF NOT EXISTS forensic_events (
    time TIMESTAMPTZ NOT NULL,
    event_id VARCHAR(50) NOT NULL,
    cik VARCHAR(10) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20), -- LOW, MEDIUM, HIGH, CRITICAL
    description TEXT,
    source_document VARCHAR(200),
    confidence_score DECIMAL(5, 4),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, event_id)
);

-- Convert to hypertable
SELECT create_hypertable('forensic_events', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_forensic_events_cik_time ON forensic_events (cik, time DESC);
CREATE INDEX IF NOT EXISTS idx_forensic_events_type ON forensic_events (event_type, time DESC);
CREATE INDEX IF NOT EXISTS idx_forensic_events_severity ON forensic_events (severity, time DESC);
CREATE INDEX IF NOT EXISTS idx_forensic_events_metadata ON forensic_events USING GIN (metadata);

-- Add compression policy
SELECT add_compression_policy('forensic_events', INTERVAL '90 days', if_not_exists => TRUE);

-- ============================================================================
-- GRANTS
-- ============================================================================
-- Grant necessary permissions to jlaw user

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO jlaw;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO jlaw;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO jlaw;
