-- ============================================================================
-- Phase 2: Actor Mapping & Interrogation Package Database Schema
-- ============================================================================
--
-- This schema supports actor mapping and interrogation package generation:
-- - Actor profiles with risk scores
-- - Actor roles (many-to-many with date ranges)
-- - Evidence attributions linking actors to evidence
-- - Interrogation packages with full protocol details
-- - Individual interrogation questions
--
-- Designed for PostgreSQL with TimescaleDB support
-- ============================================================================

-- ============================================================================
-- TABLE: actor_profiles
-- ============================================================================
-- Core actor data with risk scores
CREATE TABLE IF NOT EXISTS actor_profiles (
    actor_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    actor_type VARCHAR(50) NOT NULL, -- INDIVIDUAL or ENTITY
    cik VARCHAR(10),
    first_appearance DATE,
    last_appearance DATE,
    risk_score DECIMAL(5, 2) NOT NULL DEFAULT 0.0, -- 0-100 scale
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_actor_profiles_risk_score ON actor_profiles (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_actor_profiles_cik ON actor_profiles (cik);
CREATE INDEX IF NOT EXISTS idx_actor_profiles_name ON actor_profiles (name);
CREATE INDEX IF NOT EXISTS idx_actor_profiles_type ON actor_profiles (actor_type);
CREATE INDEX IF NOT EXISTS idx_actor_profiles_dates ON actor_profiles (first_appearance, last_appearance);

-- GIN index for metadata JSONB queries
CREATE INDEX IF NOT EXISTS idx_actor_profiles_metadata ON actor_profiles USING GIN (metadata);

-- ============================================================================
-- TABLE: actor_roles
-- ============================================================================
-- Many-to-many relationship between actors and roles with date ranges
CREATE TABLE IF NOT EXISTS actor_roles (
    id SERIAL PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actor_profiles(actor_id) ON DELETE CASCADE,
    role_name VARCHAR(255) NOT NULL,
    role_type VARCHAR(50), -- SUBJECT, TARGET, WITNESS, PERSON_OF_INTEREST, VICTIM, ENABLER
    start_date DATE,
    end_date DATE,
    source VARCHAR(255), -- Where role information came from (e.g., "Form 4", "DEF 14A")
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_actor_roles_actor_id ON actor_roles (actor_id);
CREATE INDEX IF NOT EXISTS idx_actor_roles_role_type ON actor_roles (role_type);
CREATE INDEX IF NOT EXISTS idx_actor_roles_name ON actor_roles (role_name);
CREATE INDEX IF NOT EXISTS idx_actor_roles_dates ON actor_roles (start_date, end_date);

-- Unique constraint to prevent duplicate role assignments
CREATE UNIQUE INDEX IF NOT EXISTS idx_actor_roles_unique ON actor_roles (actor_id, role_name, COALESCE(start_date, '1900-01-01'::DATE));

-- ============================================================================
-- TABLE: evidence_attributions
-- ============================================================================
-- Links evidence items to actors with relevance scores
CREATE TABLE IF NOT EXISTS evidence_attributions (
    id SERIAL PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actor_profiles(actor_id) ON DELETE CASCADE,
    evidence_id VARCHAR(255) NOT NULL,
    attribution_type VARCHAR(50) NOT NULL, -- DIRECT_AUTHORSHIP, FIDUCIARY_ROLE, etc.
    relevance_score DECIMAL(4, 3) NOT NULL, -- 0.000 to 1.000
    attribution_date DATE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_evidence_attr_actor_id ON evidence_attributions (actor_id);
CREATE INDEX IF NOT EXISTS idx_evidence_attr_evidence_id ON evidence_attributions (evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_attr_type ON evidence_attributions (attribution_type);
CREATE INDEX IF NOT EXISTS idx_evidence_attr_relevance ON evidence_attributions (relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_attr_date ON evidence_attributions (attribution_date);

-- GIN index for metadata
CREATE INDEX IF NOT EXISTS idx_evidence_attr_metadata ON evidence_attributions USING GIN (metadata);

-- Unique constraint to prevent duplicate attributions
CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_attr_unique ON evidence_attributions (actor_id, evidence_id, attribution_type);

-- ============================================================================
-- TABLE: interrogation_packages
-- ============================================================================
-- Stores complete interrogation packages for priority actors
CREATE TABLE IF NOT EXISTS interrogation_packages (
    package_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES actor_profiles(actor_id) ON DELETE CASCADE,
    actor_role VARCHAR(50) NOT NULL, -- SUBJECT, TARGET, WITNESS
    risk_score DECIMAL(5, 2) NOT NULL,
    generation_date TIMESTAMPTZ NOT NULL,
    
    -- Section I: Background
    corporate_positions JSONB,
    compensation_history JSONB,
    
    -- Section II: Violations
    violations JSONB,
    
    -- Section III: Evidence
    evidence_exhibits JSONB,
    
    -- Section IV: Protocol (high-level)
    interview_objectives JSONB,
    anticipated_defenses JSONB,
    
    -- Section V: Legal Framework
    applicable_statutes JSONB,
    evidence_strength_by_element JSONB,
    ussg_sentencing JSONB,
    
    -- Metadata
    package_version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_interrogation_pkg_actor_id ON interrogation_packages (actor_id);
CREATE INDEX IF NOT EXISTS idx_interrogation_pkg_role ON interrogation_packages (actor_role);
CREATE INDEX IF NOT EXISTS idx_interrogation_pkg_risk ON interrogation_packages (risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_interrogation_pkg_generation_date ON interrogation_packages (generation_date DESC);

-- Unique constraint: one package per actor (latest version)
CREATE UNIQUE INDEX IF NOT EXISTS idx_interrogation_pkg_actor_unique ON interrogation_packages (actor_id);

-- ============================================================================
-- TABLE: interrogation_questions
-- ============================================================================
-- Individual questions in interrogation protocol
CREATE TABLE IF NOT EXISTS interrogation_questions (
    question_id SERIAL PRIMARY KEY,
    package_id UUID NOT NULL REFERENCES interrogation_packages(package_id) ON DELETE CASCADE,
    phase VARCHAR(50) NOT NULL, -- RAPPORT, BASELINE, ACCUSATION, CONFRONTATION
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    legal_purpose TEXT NOT NULL,
    anticipated_response TEXT,
    follow_up_questions JSONB, -- Array of follow-up question strings
    rebuttal_evidence JSONB, -- Array of evidence IDs
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_interrogation_q_package_id ON interrogation_questions (package_id);
CREATE INDEX IF NOT EXISTS idx_interrogation_q_phase ON interrogation_questions (phase);
CREATE INDEX IF NOT EXISTS idx_interrogation_q_number ON interrogation_questions (question_number);

-- Unique constraint: one question per number per package
CREATE UNIQUE INDEX IF NOT EXISTS idx_interrogation_q_unique ON interrogation_questions (package_id, question_number);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Priority actors view (risk >= 50)
CREATE OR REPLACE VIEW priority_actors AS
SELECT 
    ap.*,
    array_agg(DISTINCT ar.role_name) as roles,
    COUNT(DISTINCT ea.evidence_id) as evidence_count,
    COUNT(DISTINCT ip.package_id) as has_package
FROM actor_profiles ap
LEFT JOIN actor_roles ar ON ap.actor_id = ar.actor_id
LEFT JOIN evidence_attributions ea ON ap.actor_id = ea.actor_id
LEFT JOIN interrogation_packages ip ON ap.actor_id = ip.actor_id
WHERE ap.risk_score >= 50.0
GROUP BY ap.actor_id
ORDER BY ap.risk_score DESC;

-- Subject/Target summary view
CREATE OR REPLACE VIEW subject_target_summary AS
SELECT 
    ap.actor_id,
    ap.name,
    ap.actor_type,
    ap.risk_score,
    ar.role_type,
    COUNT(DISTINCT ea.evidence_id) as direct_evidence_count,
    array_agg(DISTINCT ar.role_name) as positions,
    ap.first_appearance,
    ap.last_appearance
FROM actor_profiles ap
JOIN actor_roles ar ON ap.actor_id = ar.actor_id
LEFT JOIN evidence_attributions ea ON ap.actor_id = ea.actor_id AND ea.relevance_score >= 0.8
WHERE ar.role_type IN ('SUBJECT', 'TARGET')
GROUP BY ap.actor_id, ap.name, ap.actor_type, ap.risk_score, ar.role_type, ap.first_appearance, ap.last_appearance
ORDER BY ap.risk_score DESC;

-- Evidence attribution matrix view
CREATE OR REPLACE VIEW evidence_attribution_matrix AS
SELECT 
    ap.name as actor_name,
    ap.actor_type,
    ap.risk_score,
    ea.evidence_id,
    ea.attribution_type,
    ea.relevance_score,
    ea.attribution_date
FROM actor_profiles ap
JOIN evidence_attributions ea ON ap.actor_id = ea.actor_id
WHERE ea.relevance_score >= 0.7
ORDER BY ap.risk_score DESC, ea.relevance_score DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Update actor risk score based on violations and evidence
CREATE OR REPLACE FUNCTION update_actor_risk_score(p_actor_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    v_evidence_count INTEGER;
    v_high_relevance_count INTEGER;
    v_risk_score DECIMAL;
BEGIN
    -- Count evidence items
    SELECT COUNT(*), COUNT(CASE WHEN relevance_score >= 0.8 THEN 1 END)
    INTO v_evidence_count, v_high_relevance_count
    FROM evidence_attributions
    WHERE actor_id = p_actor_id;
    
    -- Calculate risk score (simplified)
    v_risk_score := LEAST(100.0, (v_evidence_count * 5.0) + (v_high_relevance_count * 10.0));
    
    -- Update actor profile
    UPDATE actor_profiles
    SET risk_score = v_risk_score,
        updated_at = NOW()
    WHERE actor_id = p_actor_id;
    
    RETURN v_risk_score;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_actor_profiles_updated_at
    BEFORE UPDATE ON actor_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interrogation_packages_updated_at
    BEFORE UPDATE ON interrogation_packages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================

-- Grant read access to analyst role (example)
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO jlaw_analyst;

-- Grant write access to application role (example)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO jlaw_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO jlaw_app;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE actor_profiles IS 'Core actor profiles with risk scores for prosecutorial prioritization';
COMMENT ON TABLE actor_roles IS 'Many-to-many relationship tracking actor roles and positions over time';
COMMENT ON TABLE evidence_attributions IS 'Links evidence items to actors with attribution types and relevance scores';
COMMENT ON TABLE interrogation_packages IS 'Complete DOJ-ready interrogation packages for priority actors';
COMMENT ON TABLE interrogation_questions IS 'Individual questions in FBI interview protocol with legal purpose';

COMMENT ON COLUMN actor_profiles.risk_score IS 'Risk score 0-100 calculated from violations (30%), evidence (25%), position (25%), benefit (20%)';
COMMENT ON COLUMN evidence_attributions.relevance_score IS 'Relevance score 0.0-1.0 indicating strength of actor-evidence link';
COMMENT ON COLUMN interrogation_questions.phase IS 'FBI interview phase: RAPPORT, BASELINE, ACCUSATION, or CONFRONTATION';
