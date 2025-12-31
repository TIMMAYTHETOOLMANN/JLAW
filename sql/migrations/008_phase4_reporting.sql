-- ═══════════════════════════════════════════════════════════════════════════
-- JLAW Phase 4: Enhanced Reporting & Visualization
-- Migration 008: Prosecutorial Dossier & Dashboard Schema
-- ═══════════════════════════════════════════════════════════════════════════
-- 
-- Purpose: Add tables for tracking prosecutorial dossier generation,
--          interactive dashboard sessions, and report exports
-- 
-- Tables:
--   1. prosecutorial_dossiers - Dossier generation tracking
--   2. dashboard_sessions - Dashboard session tracking
--   3. report_exports - Report export tracking
-- 
-- Author: JLAW Phase 4 Implementation Team
-- Date: 2025-12-31
-- ═══════════════════════════════════════════════════════════════════════════

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ═══════════════════════════════════════════════════════════════════════════
-- Table: prosecutorial_dossiers
-- ═══════════════════════════════════════════════════════════════════════════
-- Tracks generation of DOJ-grade prosecutorial dossiers with 7 RIM-mandated sections

CREATE TABLE IF NOT EXISTS prosecutorial_dossiers (
    -- Primary identification
    dossier_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    cik VARCHAR(10) NOT NULL,
    
    -- Generation metadata
    generation_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dossier_type VARCHAR(50) NOT NULL CHECK (dossier_type IN ('DOJ_GRADE', 'SEC_REFERRAL', 'INTERNAL')),
    
    -- Content statistics
    total_violations INTEGER NOT NULL DEFAULT 0 CHECK (total_violations >= 0),
    total_actors INTEGER NOT NULL DEFAULT 0 CHECK (total_actors >= 0),
    total_evidence_items INTEGER NOT NULL DEFAULT 0 CHECK (total_evidence_items >= 0),
    
    -- RIM compliance
    rim_compliance_status VARCHAR(20) NOT NULL CHECK (rim_compliance_status IN ('COMPLIANT', 'NON_COMPLIANT', 'PENDING')),
    
    -- Evidence integrity
    merkle_root VARCHAR(128),
    
    -- Output configuration
    output_formats JSONB,  -- Array of formats: ['pdf', 'json', 'markdown']
    
    -- RIM-mandated sections (JSONB for flexible structure)
    sections JSONB,  -- {
                      --   "executive_summary": {...},
                      --   "violations_table": {...},
                      --   "actor_mapping": {...},
                      --   "transaction_clustering": {...},
                      --   "interrogation_packages": {...},
                      --   "enforcement_pathways": {...},
                      --   "evidence_strength": {...}
                      -- }
    
    -- Additional metadata
    metadata JSONB,  -- {
                     --   "analysis_duration_seconds": 3600,
                     --   "nodes_executed": 15,
                     --   "patterns_detected": 8,
                     --   "dual_agent_validation": true,
                     --   "strict_mode": true
                     -- }
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for dossier queries
CREATE INDEX IF NOT EXISTS idx_dossiers_case_id ON prosecutorial_dossiers(case_id);
CREATE INDEX IF NOT EXISTS idx_dossiers_cik ON prosecutorial_dossiers(cik);
CREATE INDEX IF NOT EXISTS idx_dossiers_company_name ON prosecutorial_dossiers(company_name);
CREATE INDEX IF NOT EXISTS idx_dossiers_generation_date ON prosecutorial_dossiers(generation_date);
CREATE INDEX IF NOT EXISTS idx_dossiers_type ON prosecutorial_dossiers(dossier_type);
CREATE INDEX IF NOT EXISTS idx_dossiers_rim_status ON prosecutorial_dossiers(rim_compliance_status);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_dossiers_sections_gin ON prosecutorial_dossiers USING GIN(sections);
CREATE INDEX IF NOT EXISTS idx_dossiers_metadata_gin ON prosecutorial_dossiers USING GIN(metadata);

-- Comments
COMMENT ON TABLE prosecutorial_dossiers IS 'DOJ-grade prosecutorial dossier generation tracking with 7 RIM-mandated sections';
COMMENT ON COLUMN prosecutorial_dossiers.rim_compliance_status IS 'RIM execution standard compliance: COMPLIANT (zero hedging, 100% statutory binding), NON_COMPLIANT, PENDING';
COMMENT ON COLUMN prosecutorial_dossiers.merkle_root IS 'RFC 6962 Merkle tree root hash for evidence chain integrity';
COMMENT ON COLUMN prosecutorial_dossiers.sections IS '7 RIM sections: executive_summary, violations_table, actor_mapping, transaction_clustering, interrogation_packages, enforcement_pathways, evidence_strength';


-- ═══════════════════════════════════════════════════════════════════════════
-- Table: dashboard_sessions
-- ═══════════════════════════════════════════════════════════════════════════
-- Tracks interactive dashboard sessions for audit and usage analytics

CREATE TABLE IF NOT EXISTS dashboard_sessions (
    -- Primary identification
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(255) NOT NULL,
    
    -- User identification (optional for privacy)
    user_identifier VARCHAR(255),  -- IP address, username, or anonymized ID
    
    -- Session timing
    session_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    
    -- Activity tracking
    actions_log JSONB,  -- Array of actions: [
                        --   {"timestamp": "2024-01-01T10:00:00Z", "action": "view_violations", "details": {...}},
                        --   {"timestamp": "2024-01-01T10:05:00Z", "action": "export_pdf", "details": {...}}
                        -- ]
    
    -- Export tracking
    exports_generated JSONB,  -- Array of exports: [
                              --   {"format": "pdf", "timestamp": "2024-01-01T10:10:00Z", "file_path": "..."},
                              --   {"format": "csv", "timestamp": "2024-01-01T10:15:00Z", "file_path": "..."}
                              -- ]
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for session queries
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_case_id ON dashboard_sessions(case_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_user ON dashboard_sessions(user_identifier);
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_start ON dashboard_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_end ON dashboard_sessions(session_end);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_actions_gin ON dashboard_sessions USING GIN(actions_log);
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_exports_gin ON dashboard_sessions USING GIN(exports_generated);

-- Comments
COMMENT ON TABLE dashboard_sessions IS 'Interactive dashboard session tracking for audit and usage analytics';
COMMENT ON COLUMN dashboard_sessions.actions_log IS 'Chronological log of user actions in dashboard session';
COMMENT ON COLUMN dashboard_sessions.exports_generated IS 'List of exports generated during session';


-- ═══════════════════════════════════════════════════════════════════════════
-- Table: report_exports
-- ═══════════════════════════════════════════════════════════════════════════
-- Tracks all report exports with file integrity hashes and Bates stamping

CREATE TABLE IF NOT EXISTS report_exports (
    -- Primary identification
    export_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID REFERENCES prosecutorial_dossiers(dossier_id) ON DELETE CASCADE,
    
    -- Export metadata
    export_format VARCHAR(50) NOT NULL CHECK (export_format IN ('PDF', 'JSON', 'MARKDOWN', 'CSV', 'HTML')),
    file_path TEXT,
    file_hash VARCHAR(128),  -- SHA-256 hash for integrity verification
    
    -- Bates stamping (for legal exhibits)
    bates_prefix VARCHAR(50),  -- e.g., "JLAW-NIKE-2019-"
    bates_start INTEGER,       -- Starting Bates number
    bates_end INTEGER,         -- Ending Bates number
    page_count INTEGER,
    
    -- Timing
    export_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB,  -- {
                     --   "generated_by": "user@example.com",
                     --   "file_size_bytes": 1048576,
                     --   "compression": "none",
                     --   "encryption": false
                     -- }
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for export queries
CREATE INDEX IF NOT EXISTS idx_report_exports_dossier_id ON report_exports(dossier_id);
CREATE INDEX IF NOT EXISTS idx_report_exports_format ON report_exports(export_format);
CREATE INDEX IF NOT EXISTS idx_report_exports_timestamp ON report_exports(export_timestamp);
CREATE INDEX IF NOT EXISTS idx_report_exports_bates_prefix ON report_exports(bates_prefix);

-- GIN index for JSONB metadata
CREATE INDEX IF NOT EXISTS idx_report_exports_metadata_gin ON report_exports USING GIN(metadata);

-- Comments
COMMENT ON TABLE report_exports IS 'Report export tracking with file integrity and Bates stamping';
COMMENT ON COLUMN report_exports.file_hash IS 'SHA-256 hash of exported file for integrity verification';
COMMENT ON COLUMN report_exports.bates_prefix IS 'Bates prefix for legal exhibit numbering (e.g., JLAW-NIKE-2019-)';
COMMENT ON COLUMN report_exports.page_count IS 'Total pages in export (for PDF/printed reports)';


-- ═══════════════════════════════════════════════════════════════════════════
-- Triggers: Auto-update timestamps
-- ═══════════════════════════════════════════════════════════════════════════

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for prosecutorial_dossiers
DROP TRIGGER IF EXISTS update_prosecutorial_dossiers_updated_at ON prosecutorial_dossiers;
CREATE TRIGGER update_prosecutorial_dossiers_updated_at
    BEFORE UPDATE ON prosecutorial_dossiers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ═══════════════════════════════════════════════════════════════════════════
-- Sample Queries for Testing
-- ═══════════════════════════════════════════════════════════════════════════

-- Query: Get all dossiers for a specific company
-- SELECT * FROM prosecutorial_dossiers WHERE company_name = 'NIKE, Inc.' ORDER BY generation_date DESC;

-- Query: Get all exports for a dossier
-- SELECT * FROM report_exports WHERE dossier_id = '<uuid>' ORDER BY export_timestamp DESC;

-- Query: Get active dashboard sessions
-- SELECT * FROM dashboard_sessions WHERE session_end IS NULL ORDER BY session_start DESC;

-- Query: Get dossier statistics
-- SELECT 
--     dossier_type,
--     COUNT(*) as count,
--     AVG(total_violations) as avg_violations,
--     AVG(total_actors) as avg_actors
-- FROM prosecutorial_dossiers
-- GROUP BY dossier_type;


-- ═══════════════════════════════════════════════════════════════════════════
-- Migration Complete
-- ═══════════════════════════════════════════════════════════════════════════
