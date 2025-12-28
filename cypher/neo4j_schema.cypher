// ============================================================================
// JLAW Neo4j Graph Schema
// ============================================================================
//
// This schema supports network analysis for JLAW forensic investigations:
// - Executive relationship networks
// - Board interlocks and connections
// - Compensation committee networks
// - Institutional investor networks
// - Entity relationships
//
// ============================================================================

// ============================================================================
// CONSTRAINTS
// ============================================================================

// Executive constraints
CREATE CONSTRAINT executive_cik IF NOT EXISTS FOR (e:Executive) REQUIRE e.cik IS UNIQUE;
CREATE CONSTRAINT executive_id IF NOT EXISTS FOR (e:Executive) REQUIRE e.id IS UNIQUE;

// Company constraints
CREATE CONSTRAINT company_cik IF NOT EXISTS FOR (c:Company) REQUIRE c.cik IS UNIQUE;
CREATE CONSTRAINT company_ticker IF NOT EXISTS FOR (c:Company) REQUIRE c.ticker IS UNIQUE;

// Board member constraints
CREATE CONSTRAINT board_member_id IF NOT EXISTS FOR (b:BoardMember) REQUIRE b.id IS UNIQUE;

// Institutional investor constraints
CREATE CONSTRAINT investor_cik IF NOT EXISTS FOR (i:InstitutionalInvestor) REQUIRE i.cik IS UNIQUE;

// ============================================================================
// INDEXES
// ============================================================================

// Name-based lookup indexes
CREATE INDEX executive_name IF NOT EXISTS FOR (e:Executive) ON (e.name);
CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX board_member_name IF NOT EXISTS FOR (b:BoardMember) ON (b.name);
CREATE INDEX investor_name IF NOT EXISTS FOR (i:InstitutionalInvestor) ON (i.name);

// Relationship type indexes
CREATE INDEX relationship_type IF NOT EXISTS FOR ()-[r:EMPLOYED_BY]-() ON (r.from_date, r.to_date);
CREATE INDEX compensation_date IF NOT EXISTS FOR ()-[r:RECEIVED_COMPENSATION]-() ON (r.year);
CREATE INDEX board_service IF NOT EXISTS FOR ()-[r:SERVES_ON_BOARD]-() ON (r.from_date);

// ============================================================================
// SAMPLE QUERIES (for validation)
// ============================================================================

// Find all executives at a company
// MATCH (e:Executive)-[:EMPLOYED_BY]->(c:Company {ticker: 'NKE'})
// RETURN e.name, e.title;

// Find board interlocks (executives serving on multiple boards)
// MATCH (e:Executive)-[:SERVES_ON_BOARD]->(c:Company)
// WITH e, COUNT(c) as board_count
// WHERE board_count > 1
// RETURN e.name, board_count;

// Find compensation committee networks
// MATCH (e:Executive)-[:MEMBER_OF]->(comm:Committee {type: 'compensation'})
// RETURN e.name, comm.company;

// ============================================================================
// VALIDATION
// ============================================================================

// Return schema information
CALL db.schema.visualization();
