-- ============================================================================
-- RIM Phase 1: Recursive Forensics Database Schema
-- ============================================================================
-- Migration: 007_recursive_forensics.sql
-- Purpose: Add database tables for RIM Phase 1 implementation
-- 
-- Tables:
--   1. transaction_clusters - Clustered transactions by actor/date
--   2. temporal_correlations - Transaction timing relative to material events
--   3. statutory_bindings - Violation-to-statute mappings
--   4. rim_compliance_validations - RIM compliance validation results
--
-- Compliance: FRE 902(13)/(14) evidence chain requirements
-- ============================================================================

-- ============================================================================
-- 1. TRANSACTION CLUSTERS
-- ============================================================================
-- Stores clustered transactions for secondary forensic analysis
-- Supports zero-dollar clustering and same-day transaction aggregation

CREATE TABLE IF NOT EXISTS transaction_clusters (
    cluster_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    actor_cik TEXT,
    cluster_date DATE NOT NULL,
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    aggregate_value NUMERIC(20, 2),
    aggregate_shares INTEGER,
    transaction_count INTEGER NOT NULL DEFAULT 0,
    suspicious_patterns JSONB,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    transactions JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_transaction_clusters_case_id 
    ON transaction_clusters(case_id);
CREATE INDEX IF NOT EXISTS idx_transaction_clusters_actor_name 
    ON transaction_clusters(actor_name);
CREATE INDEX IF NOT EXISTS idx_transaction_clusters_cluster_date 
    ON transaction_clusters(cluster_date);
CREATE INDEX IF NOT EXISTS idx_transaction_clusters_risk_level 
    ON transaction_clusters(risk_level);
CREATE INDEX IF NOT EXISTS idx_transaction_clusters_aggregate_value 
    ON transaction_clusters(aggregate_value);

-- GIN index for JSONB suspicious_patterns
CREATE INDEX IF NOT EXISTS idx_transaction_clusters_patterns 
    ON transaction_clusters USING GIN (suspicious_patterns);

-- Comments
COMMENT ON TABLE transaction_clusters IS 
    'Transaction clusters identified during RIM Phase 1 secondary analysis';
COMMENT ON COLUMN transaction_clusters.cluster_id IS 
    'Unique cluster identifier (UUID)';
COMMENT ON COLUMN transaction_clusters.case_id IS 
    'JLAW case identifier';
COMMENT ON COLUMN transaction_clusters.actor_name IS 
    'Name of insider/actor executing transactions';
COMMENT ON COLUMN transaction_clusters.actor_cik IS 
    'CIK of actor (if available)';
COMMENT ON COLUMN transaction_clusters.aggregate_value IS 
    'Total dollar value of transactions in cluster';
COMMENT ON COLUMN transaction_clusters.aggregate_shares IS 
    'Total shares traded in cluster';
COMMENT ON COLUMN transaction_clusters.suspicious_patterns IS 
    'Array of suspicious pattern descriptions (JSONB)';
COMMENT ON COLUMN transaction_clusters.risk_level IS 
    'Risk classification: LOW, MEDIUM, HIGH, CRITICAL';

-- ============================================================================
-- 2. TEMPORAL CORRELATIONS
-- ============================================================================
-- Maps transactions to material events for insider trading detection

CREATE TABLE IF NOT EXISTS temporal_correlations (
    correlation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    material_event_type TEXT NOT NULL,
    material_event_date DATE NOT NULL,
    days_before_event INTEGER NOT NULL,
    actor_name TEXT NOT NULL,
    actor_cik TEXT,
    position_change NUMERIC(20, 2),
    transaction_value NUMERIC(20, 2),
    risk_score NUMERIC(3, 2) CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    material_event_details JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_temporal_correlations_case_id 
    ON temporal_correlations(case_id);
CREATE INDEX IF NOT EXISTS idx_temporal_correlations_actor_name 
    ON temporal_correlations(actor_name);
CREATE INDEX IF NOT EXISTS idx_temporal_correlations_transaction_date 
    ON temporal_correlations(transaction_date);
CREATE INDEX IF NOT EXISTS idx_temporal_correlations_material_event_date 
    ON temporal_correlations(material_event_date);
CREATE INDEX IF NOT EXISTS idx_temporal_correlations_risk_score 
    ON temporal_correlations(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_temporal_correlations_days_before 
    ON temporal_correlations(days_before_event);

-- Comments
COMMENT ON TABLE temporal_correlations IS 
    'Temporal correlations between transactions and material events';
COMMENT ON COLUMN temporal_correlations.correlation_id IS 
    'Unique correlation identifier (UUID)';
COMMENT ON COLUMN temporal_correlations.days_before_event IS 
    'Number of days transaction occurred before material event';
COMMENT ON COLUMN temporal_correlations.risk_score IS 
    'Risk score (0.0-1.0) based on proximity and transaction characteristics';
COMMENT ON COLUMN temporal_correlations.material_event_details IS 
    'Additional event details (form type, accession number, etc.)';

-- ============================================================================
-- 3. STATUTORY BINDINGS
-- ============================================================================
-- Maps violations to specific statutes for enforcement action

CREATE TABLE IF NOT EXISTS statutory_bindings (
    binding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL,
    violation_id TEXT NOT NULL,
    violation_type TEXT NOT NULL,
    statute_code TEXT NOT NULL,
    statute_title TEXT NOT NULL,
    statute_description TEXT,
    enforcement_agency TEXT NOT NULL CHECK (
        enforcement_agency IN ('SEC', 'DOJ', 'IRS', 'MULTIPLE')
    ),
    case_type TEXT NOT NULL CHECK (
        case_type IN ('CIVIL', 'CRIMINAL', 'BOTH')
    ),
    confidence NUMERIC(3, 2) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    plain_language_explanation TEXT,
    recommended_actions JSONB,
    evidence_requirements JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_statutory_bindings_case_id 
    ON statutory_bindings(case_id);
CREATE INDEX IF NOT EXISTS idx_statutory_bindings_violation_id 
    ON statutory_bindings(violation_id);
CREATE INDEX IF NOT EXISTS idx_statutory_bindings_statute_code 
    ON statutory_bindings(statute_code);
CREATE INDEX IF NOT EXISTS idx_statutory_bindings_enforcement_agency 
    ON statutory_bindings(enforcement_agency);
CREATE INDEX IF NOT EXISTS idx_statutory_bindings_case_type 
    ON statutory_bindings(case_type);
CREATE INDEX IF NOT EXISTS idx_statutory_bindings_confidence 
    ON statutory_bindings(confidence DESC);

-- Comments
COMMENT ON TABLE statutory_bindings IS 
    'Violation-to-statute bindings for enforcement pathway determination';
COMMENT ON COLUMN statutory_bindings.binding_id IS 
    'Unique binding identifier (UUID)';
COMMENT ON COLUMN statutory_bindings.statute_code IS 
    'Legal statute code (e.g., "17 CFR § 240.10b-5")';
COMMENT ON COLUMN statutory_bindings.enforcement_agency IS 
    'Primary enforcement agency: SEC, DOJ, IRS, or MULTIPLE';
COMMENT ON COLUMN statutory_bindings.case_type IS 
    'Civil, Criminal, or Both enforcement pathways';
COMMENT ON COLUMN statutory_bindings.confidence IS 
    'Confidence in binding (0.0-1.0)';
COMMENT ON COLUMN statutory_bindings.plain_language_explanation IS 
    'Plain-language explanation of statute and violation';

-- ============================================================================
-- 4. RIM COMPLIANCE VALIDATIONS
-- ============================================================================
-- Stores RIM compliance validation results

CREATE TABLE IF NOT EXISTS rim_compliance_validations (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL,
    is_compliant BOOLEAN NOT NULL,
    compliance_status TEXT NOT NULL CHECK (
        compliance_status IN ('PASS', 'FAIL', 'WARNING')
    ),
    deficiencies JSONB,
    prohibited_language_count INTEGER DEFAULT 0,
    statutory_binding_coverage NUMERIC(3, 2) CHECK (
        statutory_binding_coverage >= 0.0 AND statutory_binding_coverage <= 1.0
    ),
    secondary_pass_coverage NUMERIC(3, 2) CHECK (
        secondary_pass_coverage >= 0.0 AND secondary_pass_coverage <= 1.0
    ),
    validation_summary TEXT,
    validated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_rim_compliance_validations_case_id 
    ON rim_compliance_validations(case_id);
CREATE INDEX IF NOT EXISTS idx_rim_compliance_validations_is_compliant 
    ON rim_compliance_validations(is_compliant);
CREATE INDEX IF NOT EXISTS idx_rim_compliance_validations_status 
    ON rim_compliance_validations(compliance_status);
CREATE INDEX IF NOT EXISTS idx_rim_compliance_validations_validated_at 
    ON rim_compliance_validations(validated_at DESC);

-- GIN index for deficiencies
CREATE INDEX IF NOT EXISTS idx_rim_compliance_deficiencies 
    ON rim_compliance_validations USING GIN (deficiencies);

-- Comments
COMMENT ON TABLE rim_compliance_validations IS 
    'RIM Non-Negotiable Execution Standard compliance validation results';
COMMENT ON COLUMN rim_compliance_validations.validation_id IS 
    'Unique validation identifier (UUID)';
COMMENT ON COLUMN rim_compliance_validations.is_compliant IS 
    'True if dossier meets RIM standards';
COMMENT ON COLUMN rim_compliance_validations.compliance_status IS 
    'PASS, FAIL, or WARNING';
COMMENT ON COLUMN rim_compliance_validations.deficiencies IS 
    'Array of compliance deficiencies (JSONB)';
COMMENT ON COLUMN rim_compliance_validations.prohibited_language_count IS 
    'Count of prohibited hedging language instances';
COMMENT ON COLUMN rim_compliance_validations.statutory_binding_coverage IS 
    'Percentage of violations with statutory bindings (0.0-1.0)';
COMMENT ON COLUMN rim_compliance_validations.secondary_pass_coverage IS 
    'Percentage of violations receiving secondary analysis (0.0-1.0)';

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS (Optional - depends on your schema)
-- ============================================================================
-- If you have a cases table, you can add foreign key constraints:
-- ALTER TABLE transaction_clusters 
--     ADD CONSTRAINT fk_transaction_clusters_case 
--     FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE;
-- 
-- ALTER TABLE temporal_correlations 
--     ADD CONSTRAINT fk_temporal_correlations_case 
--     FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE;
-- 
-- ALTER TABLE statutory_bindings 
--     ADD CONSTRAINT fk_statutory_bindings_case 
--     FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE;
-- 
-- ALTER TABLE rim_compliance_validations 
--     ADD CONSTRAINT fk_rim_compliance_validations_case 
--     FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Create or replace function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for transaction_clusters
DROP TRIGGER IF EXISTS update_transaction_clusters_updated_at ON transaction_clusters;
CREATE TRIGGER update_transaction_clusters_updated_at
    BEFORE UPDATE ON transaction_clusters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers for temporal_correlations
DROP TRIGGER IF EXISTS update_temporal_correlations_updated_at ON temporal_correlations;
CREATE TRIGGER update_temporal_correlations_updated_at
    BEFORE UPDATE ON temporal_correlations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers for statutory_bindings
DROP TRIGGER IF EXISTS update_statutory_bindings_updated_at ON statutory_bindings;
CREATE TRIGGER update_statutory_bindings_updated_at
    BEFORE UPDATE ON statutory_bindings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- GRANT PERMISSIONS (Adjust as needed for your environment)
-- ============================================================================
-- Example: Grant permissions to jlaw_user role
-- GRANT SELECT, INSERT, UPDATE, DELETE ON transaction_clusters TO jlaw_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON temporal_correlations TO jlaw_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON statutory_bindings TO jlaw_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON rim_compliance_validations TO jlaw_user;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
