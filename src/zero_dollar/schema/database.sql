-- ============================================================================
-- Zero-Dollar Transaction Anomaly Detection Database Schema
-- ============================================================================
--
-- PostgreSQL schema for DOJ-grade forensic analysis of zero-dollar
-- transactions in SEC Form 4 filings.
--
-- Reference: Section 11 - Data Schema Specifications
--
-- Version: 1.0.0
-- Created: 2024
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- ============================================================================
-- Schema Version Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES 
('1.0.0', 'Initial zero-dollar transaction schema');

-- ============================================================================
-- Core Transaction Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    -- Primary Key
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- SEC Filing Identifiers
    accession_number VARCHAR(20) NOT NULL,
    issuer_cik VARCHAR(10) NOT NULL,
    issuer_name TEXT NOT NULL,
    
    -- Reporting Person
    reporting_person_cik VARCHAR(10) NOT NULL,
    reporting_person_name TEXT NOT NULL,
    
    -- Transaction Details
    transaction_date DATE NOT NULL,
    filing_date DATE NOT NULL,
    transaction_code CHAR(1) NOT NULL,
    shares NUMERIC(20, 4) NOT NULL,
    price_per_share NUMERIC(20, 4),  -- NULL for zero-dollar
    transaction_acquired_disposed CHAR(1) NOT NULL,  -- 'A' or 'D'
    shares_owned_following NUMERIC(20, 4) NOT NULL,
    
    -- Ownership Type
    direct_indirect CHAR(1) NOT NULL,  -- 'D' or 'I'
    nature_of_ownership TEXT,
    
    -- Additional Metadata
    footnotes TEXT[],
    security_title TEXT DEFAULT 'Common Stock',
    form_type VARCHAR(10) DEFAULT '4',
    document_url TEXT,
    
    -- Derivative Fields
    derivative_security BOOLEAN DEFAULT FALSE,
    conversion_exercise_price NUMERIC(20, 4),
    exercise_date DATE,
    expiration_date DATE,
    
    -- Forensic Metadata
    is_zero_dollar BOOLEAN GENERATED ALWAYS AS (
        price_per_share IS NULL OR price_per_share = 0
    ) STORED,
    notional_value NUMERIC(20, 2) GENERATED ALWAYS AS (
        CASE 
            WHEN price_per_share IS NULL OR price_per_share = 0 THEN 0
            ELSE ABS(shares) * price_per_share
        END
    ) STORED,
    days_to_filing INTEGER GENERATED ALWAYS AS (
        filing_date - transaction_date
    ) STORED,
    is_late_filing BOOLEAN GENERATED ALWAYS AS (
        (filing_date - transaction_date) > 3
    ) STORED,
    
    -- Timestamps
    extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for transactions table
CREATE INDEX idx_transactions_accession ON transactions(accession_number);
CREATE INDEX idx_transactions_issuer_cik ON transactions(issuer_cik);
CREATE INDEX idx_transactions_reporting_person ON transactions(reporting_person_cik);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_filing_date ON transactions(filing_date);
CREATE INDEX idx_transactions_code ON transactions(transaction_code);
CREATE INDEX idx_transactions_zero_dollar ON transactions(is_zero_dollar) WHERE is_zero_dollar = TRUE;
CREATE INDEX idx_transactions_late_filing ON transactions(is_late_filing) WHERE is_late_filing = TRUE;
CREATE INDEX idx_transactions_issuer_date ON transactions(issuer_cik, transaction_date);
CREATE INDEX idx_transactions_person_date ON transactions(reporting_person_cik, transaction_date);

-- Full-text search index on company name
CREATE INDEX idx_transactions_issuer_name_trgm ON transactions USING gin(issuer_name gin_trgm_ops);

-- ============================================================================
-- Transaction Clustering Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS transaction_clusters (
    cluster_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporting_person_cik VARCHAR(10) NOT NULL,
    reporting_person_name TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_shares NUMERIC(20, 4) NOT NULL,
    zero_dollar_count INTEGER NOT NULL,
    cluster_score NUMERIC(5, 2) NOT NULL,
    detection_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Computed fields
    cluster_span_days INTEGER GENERATED ALWAYS AS (end_date - start_date) STORED,
    
    CONSTRAINT chk_cluster_dates CHECK (end_date >= start_date),
    CONSTRAINT chk_cluster_score CHECK (cluster_score BETWEEN 0 AND 100)
);

CREATE INDEX idx_clusters_person ON transaction_clusters(reporting_person_cik);
CREATE INDEX idx_clusters_score ON transaction_clusters(cluster_score) WHERE cluster_score >= 15.0;
CREATE INDEX idx_clusters_date_range ON transaction_clusters(start_date, end_date);

-- Junction table for cluster membership
CREATE TABLE IF NOT EXISTS cluster_transactions (
    cluster_id UUID NOT NULL REFERENCES transaction_clusters(cluster_id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (cluster_id, transaction_id)
);

CREATE INDEX idx_cluster_transactions_cluster ON cluster_transactions(cluster_id);
CREATE INDEX idx_cluster_transactions_transaction ON cluster_transactions(transaction_id);

-- ============================================================================
-- Anomaly Detection Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS anomaly_flags (
    flag_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    transaction_accession VARCHAR(20) NOT NULL,
    reporting_person_cik VARCHAR(10) NOT NULL,
    reporting_person_name TEXT NOT NULL,
    issuer_cik VARCHAR(10) NOT NULL,
    issuer_name TEXT NOT NULL,
    detection_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    transaction_date DATE NOT NULL,
    shares_involved NUMERIC(20, 4) NOT NULL,
    notional_value NUMERIC(20, 2) NOT NULL,
    description TEXT NOT NULL,
    supporting_evidence TEXT[],
    forensic_score NUMERIC(5, 2) NOT NULL DEFAULT 0,
    requires_investigation BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT chk_severity CHECK (severity IN ('critical', 'high', 'moderate', 'low')),
    CONSTRAINT chk_forensic_score CHECK (forensic_score BETWEEN 0 AND 100)
);

CREATE INDEX idx_anomaly_flags_type ON anomaly_flags(anomaly_type);
CREATE INDEX idx_anomaly_flags_severity ON anomaly_flags(severity);
CREATE INDEX idx_anomaly_flags_accession ON anomaly_flags(transaction_accession);
CREATE INDEX idx_anomaly_flags_issuer ON anomaly_flags(issuer_cik);
CREATE INDEX idx_anomaly_flags_person ON anomaly_flags(reporting_person_cik);
CREATE INDEX idx_anomaly_flags_score ON anomaly_flags(forensic_score) WHERE forensic_score >= 50;
CREATE INDEX idx_anomaly_flags_investigation ON anomaly_flags(requires_investigation) WHERE requires_investigation = TRUE;

-- ============================================================================
-- Material Events and Proximity Analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS material_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    issuer_cik VARCHAR(10) NOT NULL,
    issuer_name TEXT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_date DATE NOT NULL,
    event_description TEXT NOT NULL,
    stock_price_impact NUMERIC(10, 4),
    is_price_sensitive BOOLEAN DEFAULT FALSE,
    sec_filing_url TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_material_events_issuer ON material_events(issuer_cik);
CREATE INDEX idx_material_events_date ON material_events(event_date);
CREATE INDEX idx_material_events_type ON material_events(event_type);
CREATE INDEX idx_material_events_sensitive ON material_events(is_price_sensitive) WHERE is_price_sensitive = TRUE;

CREATE TABLE IF NOT EXISTS event_proximity_flags (
    proximity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_accession VARCHAR(20) NOT NULL,
    event_id UUID NOT NULL REFERENCES material_events(event_id) ON DELETE CASCADE,
    days_before_event INTEGER NOT NULL,
    proximity_score NUMERIC(5, 2) NOT NULL,
    is_suspicious_timing BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_proximity_score CHECK (proximity_score BETWEEN 0 AND 100)
);

CREATE INDEX idx_event_proximity_accession ON event_proximity_flags(transaction_accession);
CREATE INDEX idx_event_proximity_event ON event_proximity_flags(event_id);
CREATE INDEX idx_event_proximity_suspicious ON event_proximity_flags(is_suspicious_timing) WHERE is_suspicious_timing = TRUE;

-- ============================================================================
-- Entity and Ownership Structure Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS entity_references (
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_name TEXT NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    transaction_accession VARCHAR(20) NOT NULL,
    reporting_person_cik VARCHAR(10) NOT NULL,
    confidence_score NUMERIC(3, 2) NOT NULL,
    raw_text TEXT NOT NULL,
    extracted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_confidence CHECK (confidence_score BETWEEN 0 AND 1),
    CONSTRAINT chk_entity_type CHECK (entity_type IN (
        'revocable_living_trust', 'irrevocable_trust', 'grantor_retained_annuity_trust',
        'family_limited_partnership', 'limited_liability_company', 'donor_advised_fund',
        'private_foundation', 'charitable_remainder_trust', 'spouse', 'child'
    ))
);

CREATE INDEX idx_entity_references_type ON entity_references(entity_type);
CREATE INDEX idx_entity_references_person ON entity_references(reporting_person_cik);
CREATE INDEX idx_entity_references_accession ON entity_references(transaction_accession);
CREATE INDEX idx_entity_references_confidence ON entity_references(confidence_score) WHERE confidence_score >= 0.8;

CREATE TABLE IF NOT EXISTS ownership_chains (
    chain_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporting_person_cik VARCHAR(10) NOT NULL,
    issuer_cik VARCHAR(10) NOT NULL,
    total_depth INTEGER NOT NULL,
    effective_ownership NUMERIC(5, 2) NOT NULL,
    contains_foreign_entities BOOLEAN DEFAULT FALSE,
    is_complex_structure BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_effective_ownership CHECK (effective_ownership BETWEEN 0 AND 100)
);

CREATE INDEX idx_ownership_chains_person ON ownership_chains(reporting_person_cik);
CREATE INDEX idx_ownership_chains_issuer ON ownership_chains(issuer_cik);
CREATE INDEX idx_ownership_chains_complex ON ownership_chains(is_complex_structure) WHERE is_complex_structure = TRUE;

CREATE TABLE IF NOT EXISTS ownership_nodes (
    node_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chain_id UUID NOT NULL REFERENCES ownership_chains(chain_id) ON DELETE CASCADE,
    entity_name TEXT NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    ownership_percentage NUMERIC(5, 2) NOT NULL,
    node_depth INTEGER NOT NULL,
    is_ultimate_beneficiary BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT chk_ownership_percentage CHECK (ownership_percentage BETWEEN 0 AND 100)
);

CREATE INDEX idx_ownership_nodes_chain ON ownership_nodes(chain_id);
CREATE INDEX idx_ownership_nodes_beneficiary ON ownership_nodes(is_ultimate_beneficiary) WHERE is_ultimate_beneficiary = TRUE;

-- ============================================================================
-- Behavioral Assessment Tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS behavioral_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporting_person_cik VARCHAR(10) NOT NULL,
    reporting_person_name TEXT NOT NULL,
    issuer_cik VARCHAR(10) NOT NULL,
    issuer_name TEXT NOT NULL,
    assessment_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Score components
    magnitude_score NUMERIC(5, 2) NOT NULL,
    frequency_score NUMERIC(5, 2) NOT NULL,
    timing_score NUMERIC(5, 2) NOT NULL,
    filing_compliance_score NUMERIC(5, 2) NOT NULL,
    entity_complexity_score NUMERIC(5, 2) NOT NULL,
    
    -- Transaction counts
    zero_dollar_transaction_count INTEGER NOT NULL,
    total_transaction_count INTEGER NOT NULL,
    temporal_clusters_detected INTEGER NOT NULL,
    
    -- Assessment results
    total_risk_score NUMERIC(5, 2) GENERATED ALWAYS AS (
        magnitude_score + frequency_score + timing_score + 
        filing_compliance_score + entity_complexity_score
    ) STORED,
    risk_level VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN (magnitude_score + frequency_score + timing_score + 
                  filing_compliance_score + entity_complexity_score) >= 75 THEN 'CRITICAL'
            WHEN (magnitude_score + frequency_score + timing_score + 
                  filing_compliance_score + entity_complexity_score) >= 60 THEN 'HIGH'
            WHEN (magnitude_score + frequency_score + timing_score + 
                  filing_compliance_score + entity_complexity_score) >= 40 THEN 'MODERATE'
            ELSE 'LOW'
        END
    ) STORED,
    prosecutorial_priority INTEGER DEFAULT 5,
    recommendation TEXT,
    next_steps TEXT[],
    
    CONSTRAINT chk_prosecutorial_priority CHECK (prosecutorial_priority BETWEEN 1 AND 5),
    CONSTRAINT chk_score_components CHECK (
        magnitude_score BETWEEN 0 AND 25 AND
        frequency_score BETWEEN 0 AND 25 AND
        timing_score BETWEEN 0 AND 20 AND
        filing_compliance_score BETWEEN 0 AND 15 AND
        entity_complexity_score BETWEEN 0 AND 15
    )
);

CREATE INDEX idx_behavioral_assessments_person ON behavioral_assessments(reporting_person_cik);
CREATE INDEX idx_behavioral_assessments_issuer ON behavioral_assessments(issuer_cik);
CREATE INDEX idx_behavioral_assessments_risk_level ON behavioral_assessments(risk_level);
CREATE INDEX idx_behavioral_assessments_priority ON behavioral_assessments(prosecutorial_priority);
CREATE INDEX idx_behavioral_assessments_score ON behavioral_assessments(total_risk_score) WHERE total_risk_score >= 60;

-- ============================================================================
-- Evidence Chain and Custody Tables (FRE 902 Compliance)
-- ============================================================================

CREATE TABLE IF NOT EXISTS evidence_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_type VARCHAR(50) NOT NULL,
    source_url TEXT NOT NULL,
    acquisition_timestamp TIMESTAMP NOT NULL,
    
    -- Triple-hash integrity (FRE 902(13)/(14))
    sha256_hash CHAR(64) NOT NULL,
    sha3_512_hash CHAR(128) NOT NULL,
    blake2b_hash CHAR(128) NOT NULL,
    
    file_size_bytes BIGINT NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    related_transaction_accession VARCHAR(20),
    custody_chain_id UUID,
    merkle_root CHAR(64),
    is_verified BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_sha256_format CHECK (sha256_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT chk_sha3_format CHECK (sha3_512_hash ~ '^[0-9a-f]{128}$'),
    CONSTRAINT chk_blake2b_format CHECK (blake2b_hash ~ '^[0-9a-f]{128}$')
);

CREATE INDEX idx_evidence_artifacts_type ON evidence_artifacts(artifact_type);
CREATE INDEX idx_evidence_artifacts_accession ON evidence_artifacts(related_transaction_accession);
CREATE INDEX idx_evidence_artifacts_sha256 ON evidence_artifacts(sha256_hash);
CREATE INDEX idx_evidence_artifacts_verified ON evidence_artifacts(is_verified);
CREATE INDEX idx_evidence_artifacts_acquisition ON evidence_artifacts(acquisition_timestamp);

-- RFC 3161 Trusted Timestamps
CREATE TABLE IF NOT EXISTS trusted_timestamps (
    timestamp_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES evidence_artifacts(artifact_id) ON DELETE CASCADE,
    timestamp_token TEXT NOT NULL,
    timestamp_authority TEXT NOT NULL,
    timestamp_value TIMESTAMP NOT NULL,
    hash_algorithm VARCHAR(20) NOT NULL,
    signature TEXT NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trusted_timestamps_artifact ON trusted_timestamps(artifact_id);
CREATE INDEX idx_trusted_timestamps_value ON trusted_timestamps(timestamp_value);

-- Chain of Custody Records
CREATE TABLE IF NOT EXISTS chain_of_custody_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES evidence_artifacts(artifact_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action_description TEXT NOT NULL,
    pre_action_hash CHAR(64) NOT NULL,
    post_action_hash CHAR(64),
    location TEXT DEFAULT 'JLAW_EVIDENCE_CHAIN',
    metadata JSONB,
    
    CONSTRAINT chk_event_type CHECK (event_type IN (
        'acquisition', 'verification', 'access', 'analysis', 
        'export', 'archival', 'integrity_check'
    ))
);

CREATE INDEX idx_custody_records_artifact ON chain_of_custody_records(artifact_id);
CREATE INDEX idx_custody_records_timestamp ON chain_of_custody_records(timestamp);
CREATE INDEX idx_custody_records_event_type ON chain_of_custody_records(event_type);
CREATE INDEX idx_custody_records_actor ON chain_of_custody_records(actor);

-- Verification Events Log
CREATE TABLE IF NOT EXISTS verification_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id UUID NOT NULL REFERENCES evidence_artifacts(artifact_id) ON DELETE CASCADE,
    verification_type VARCHAR(50) NOT NULL,
    verification_result BOOLEAN NOT NULL,
    verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verifier VARCHAR(100) NOT NULL,
    error_message TEXT,
    
    CONSTRAINT chk_verification_type CHECK (verification_type IN (
        'hash_integrity', 'merkle_proof', 'timestamp_verification',
        'signature_verification', 'chain_continuity'
    ))
);

CREATE INDEX idx_verification_events_artifact ON verification_events(artifact_id);
CREATE INDEX idx_verification_events_result ON verification_events(verification_result);
CREATE INDEX idx_verification_events_type ON verification_events(verification_type);

-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================

-- View: Zero-dollar transactions summary by reporting person
CREATE MATERIALIZED VIEW mv_zero_dollar_summary AS
SELECT 
    reporting_person_cik,
    reporting_person_name,
    issuer_cik,
    issuer_name,
    COUNT(*) as total_transactions,
    COUNT(*) FILTER (WHERE is_zero_dollar) as zero_dollar_count,
    COUNT(*) FILTER (WHERE is_late_filing) as late_filing_count,
    SUM(ABS(shares)) as total_shares,
    MIN(transaction_date) as first_transaction_date,
    MAX(transaction_date) as last_transaction_date,
    AVG(days_to_filing) as avg_days_to_filing
FROM transactions
GROUP BY reporting_person_cik, reporting_person_name, issuer_cik, issuer_name;

CREATE UNIQUE INDEX idx_mv_zero_dollar_summary_pk 
    ON mv_zero_dollar_summary(reporting_person_cik, issuer_cik);
CREATE INDEX idx_mv_zero_dollar_summary_zero_count 
    ON mv_zero_dollar_summary(zero_dollar_count) WHERE zero_dollar_count > 0;

-- View: High-risk anomalies requiring investigation
CREATE MATERIALIZED VIEW mv_high_risk_anomalies AS
SELECT 
    af.flag_id,
    af.anomaly_type,
    af.severity,
    af.reporting_person_cik,
    af.reporting_person_name,
    af.issuer_cik,
    af.issuer_name,
    af.forensic_score,
    ba.total_risk_score,
    ba.risk_level,
    ba.prosecutorial_priority
FROM anomaly_flags af
LEFT JOIN behavioral_assessments ba 
    ON af.reporting_person_cik = ba.reporting_person_cik 
    AND af.issuer_cik = ba.issuer_cik
WHERE af.severity IN ('critical', 'high')
   OR af.forensic_score >= 60
   OR ba.prosecutorial_priority <= 2;

CREATE UNIQUE INDEX idx_mv_high_risk_anomalies_pk 
    ON mv_high_risk_anomalies(flag_id);
CREATE INDEX idx_mv_high_risk_anomalies_severity 
    ON mv_high_risk_anomalies(severity);

-- ============================================================================
-- Triggers for Audit and Integrity
-- ============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_transactions_updated_at 
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Grants (adjust as needed for your environment)
-- ============================================================================

-- Example: Grant appropriate permissions to application role
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO jlaw_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO jlaw_app;

-- ============================================================================
-- End of Schema
-- ============================================================================
