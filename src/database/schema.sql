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

-- ============================================================================
-- Phase 3: Multi-Jurisdictional Compliance Extensions
-- ============================================================================

-- ============================================================================
-- TABLE: jurisdictions
-- ============================================================================
-- Tracks all jurisdictions with prosecutorial authority
CREATE TABLE IF NOT EXISTS jurisdictions (
    jurisdiction_id TEXT PRIMARY KEY,
    jurisdiction_name TEXT NOT NULL,
    jurisdiction_type TEXT NOT NULL, -- STATE, FEDERAL, INTERNATIONAL
    regulatory_body TEXT NOT NULL,
    has_authority BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jurisdiction_type ON jurisdictions(jurisdiction_type);
CREATE INDEX IF NOT EXISTS idx_jurisdiction_name ON jurisdictions(jurisdiction_name);

-- ============================================================================
-- TABLE: jurisdiction_authority
-- ============================================================================
-- Tracks basis for jurisdiction authority (many-to-many with evidence)
CREATE TABLE IF NOT EXISTS jurisdiction_authority (
    id SERIAL PRIMARY KEY,
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(jurisdiction_id) ON DELETE CASCADE,
    authority_basis TEXT NOT NULL,
    evidence_id TEXT,
    statute_citation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jurisdiction_authority_jid ON jurisdiction_authority(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_jurisdiction_authority_evidence ON jurisdiction_authority(evidence_id);

-- ============================================================================
-- TABLE: state_violations
-- ============================================================================
-- State-specific securities law violations
CREATE TABLE IF NOT EXISTS state_violations (
    violation_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    statute_citation TEXT NOT NULL,
    statute_name TEXT NOT NULL,
    violation_description TEXT NOT NULL,
    penalties_json TEXT NOT NULL, -- JSON: {criminal, civil, administrative}
    statute_of_limitations TEXT,
    elements_met TEXT[], -- Array of legal elements satisfied
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_state_violations_state ON state_violations(state);
CREATE INDEX IF NOT EXISTS idx_state_violations_statute ON state_violations(statute_citation);

-- ============================================================================
-- TABLE: international_violations
-- ============================================================================
-- International regulatory violations
CREATE TABLE IF NOT EXISTS international_violations (
    violation_id TEXT PRIMARY KEY,
    jurisdiction TEXT NOT NULL,
    regulator TEXT NOT NULL,
    regulation_citation TEXT NOT NULL,
    regulation_name TEXT NOT NULL,
    violation_description TEXT NOT NULL,
    violation_type TEXT NOT NULL, -- MARKET_MANIPULATION, INSIDER_TRADING, FRAUD, etc.
    mlat_available BOOLEAN NOT NULL DEFAULT FALSE,
    penalties_json TEXT NOT NULL,
    extraterritorial_basis TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_intl_violations_jurisdiction ON international_violations(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_intl_violations_type ON international_violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_intl_violations_mlat ON international_violations(mlat_available);

-- ============================================================================
-- TABLE: forum_analyses
-- ============================================================================
-- Prosecution venue analysis and scoring
CREATE TABLE IF NOT EXISTS forum_analyses (
    analysis_id TEXT PRIMARY KEY,
    jurisdiction_id TEXT NOT NULL REFERENCES jurisdictions(jurisdiction_id) ON DELETE CASCADE,
    jurisdiction_name TEXT NOT NULL,
    jurisdiction_type TEXT NOT NULL,
    venue_score REAL NOT NULL, -- 0-100 score
    recommended_priority TEXT NOT NULL, -- PRIMARY, SECONDARY, TERTIARY
    analysis_json TEXT NOT NULL, -- Full ForumAnalysis JSON
    penalty_score REAL,
    evidentiary_score REAL,
    limitations_score REAL,
    precedent_score REAL,
    resources_score REAL,
    political_will_score REAL,
    victim_impact_score REAL,
    statute_of_limitations_remaining INTEGER, -- Days remaining
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_forum_venue_score ON forum_analyses(venue_score DESC);
CREATE INDEX IF NOT EXISTS idx_forum_priority ON forum_analyses(recommended_priority);
CREATE INDEX IF NOT EXISTS idx_forum_jurisdiction ON forum_analyses(jurisdiction_id);

-- ============================================================================
-- VIEWS: Multi-Jurisdictional Analysis
-- ============================================================================

-- Primary venue recommendation view
CREATE OR REPLACE VIEW primary_prosecution_venues AS
SELECT 
    fa.jurisdiction_name,
    fa.jurisdiction_type,
    fa.venue_score,
    fa.recommended_priority,
    fa.penalty_score,
    fa.evidentiary_score,
    fa.statute_of_limitations_remaining,
    j.regulatory_body
FROM forum_analyses fa
JOIN jurisdictions j ON fa.jurisdiction_id = j.jurisdiction_id
WHERE fa.recommended_priority = 'PRIMARY'
ORDER BY fa.venue_score DESC;

-- State violations summary view
CREATE OR REPLACE VIEW state_violations_summary AS
SELECT 
    state,
    COUNT(*) as violation_count,
    COUNT(DISTINCT statute_citation) as unique_statutes,
    ARRAY_AGG(DISTINCT statute_name) as statute_names
FROM state_violations
GROUP BY state
ORDER BY violation_count DESC;

-- International violations with MLAT availability
CREATE OR REPLACE VIEW international_violations_mlat AS
SELECT 
    iv.jurisdiction,
    iv.regulator,
    iv.violation_type,
    COUNT(*) as violation_count,
    BOOL_OR(iv.mlat_available) as has_mlat_treaty
FROM international_violations iv
GROUP BY iv.jurisdiction, iv.regulator, iv.violation_type
ORDER BY violation_count DESC;

-- Jurisdiction authority matrix
CREATE OR REPLACE VIEW jurisdiction_authority_matrix AS
SELECT 
    j.jurisdiction_name,
    j.jurisdiction_type,
    j.regulatory_body,
    COUNT(ja.id) as authority_basis_count,
    ARRAY_AGG(DISTINCT ja.authority_basis) as authority_reasons,
    ARRAY_AGG(DISTINCT ja.statute_citation) as applicable_statutes
FROM jurisdictions j
LEFT JOIN jurisdiction_authority ja ON j.jurisdiction_id = ja.jurisdiction_id
GROUP BY j.jurisdiction_id, j.jurisdiction_name, j.jurisdiction_type, j.regulatory_body
ORDER BY authority_basis_count DESC;

-- ============================================================================
-- COMMENTS: Multi-Jurisdictional Tables
-- ============================================================================

COMMENT ON TABLE jurisdictions IS 'All jurisdictions (federal, state, international) with prosecutorial authority';
COMMENT ON TABLE jurisdiction_authority IS 'Basis for jurisdiction authority with supporting evidence';
COMMENT ON TABLE state_violations IS '50-state Blue Sky Law violations with penalties and elements';
COMMENT ON TABLE international_violations IS 'International regulatory violations with MLAT treaty information';
COMMENT ON TABLE forum_analyses IS 'Prosecution venue scoring and forum shopping optimization';

COMMENT ON COLUMN forum_analyses.venue_score IS 'Overall venue score 0-100 from multi-factor algorithm';
COMMENT ON COLUMN forum_analyses.recommended_priority IS 'PRIMARY (lead), SECONDARY (coordinated), or TERTIARY (support)';
COMMENT ON COLUMN state_violations.elements_met IS 'Array of legal elements satisfied by the violation';
COMMENT ON COLUMN international_violations.mlat_available IS 'Whether Mutual Legal Assistance Treaty exists with U.S.';

