# Actor Mapping & Interrogation Package Implementation

## Overview

Phase 2 of the JLAW forensic analysis system transforms forensic findings into actionable prosecutorial intelligence by identifying actors, classifying their roles, attributing evidence, and generating DOJ-ready interrogation packages.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Phase 5.5: Actor Mapping Pipeline                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Actor           │    │  Actor Role      │    │  Evidence        │
│  Extraction      │───▶│  Classifier      │───▶│  Attribution     │
│  Engine          │    │                  │    │  Linker          │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │                        │                        │
         │  Nodes 1,2,5,7,10     │  DOJ 6-Tier           │  5 Attribution
         │  Pattern Results       │  Classification        │  Types
         │                        │                        │
         ▼                        ▼                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Interrogation Package Generator                │
│  • Background (positions, compensation)                           │
│  • Violations Attributed (statutory violations)                   │
│  • Evidence Exhibits (chronological, FRE 902)                    │
│  • Interrogation Protocol (FBI question tree)                    │
│  • Legal Framework (statutes, USSG sentencing)                   │
└──────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  Database Persistence │
                        │  & Dossier Integration│
                        └───────────────────────┘
```

## Component APIs

### 1. Actor Extraction Engine

**File**: `src/detection/actor_extraction_engine.py`

Extracts and deduplicates actors from multiple sources using fuzzy name matching and CIK alignment.

#### Key Classes

```python
@dataclass
class ActorProfile:
    actor_id: str              # UUID
    name: str                  # Full name
    actor_type: str           # INDIVIDUAL or ENTITY
    roles: List[str]          # ["CEO", "Director", ...]
    cik: Optional[str]        # SEC CIK number
    first_appearance: Optional[date]
    last_appearance: Optional[date]
    evidence_items: List[str] # Evidence IDs
    violations: List[str]     # Violation IDs
    risk_score: float         # 0-100
    metadata: Dict[str, Any]  # Additional info

class ActorExtractionEngine:
    def extract_actors_from_nodes(
        node_results: Dict[str, Any]
    ) -> List[ActorProfile]
    
    def extract_actors_from_patterns(
        pattern_results: Dict[str, Any]
    ) -> List[ActorProfile]
```

#### Usage Example

```python
from src.detection.actor_extraction_engine import ActorExtractionEngine

engine = ActorExtractionEngine()

# Extract from nodes
actors = engine.extract_actors_from_nodes(node_results)

# Extract from patterns
actors = engine.extract_actors_from_patterns(pattern_results)

# Get all unique actors
all_actors = engine.get_all_actors()

# Filter by role
ceos = engine.get_actors_by_role("CEO")
```

### 2. Actor Role Classifier

**File**: `src/detection/actor_role_classifier.py`

Implements DOJ 6-tier role classification and calculates risk scores based on four weighted components.

#### Classification Tiers

| Role | Risk Score | Criteria |
|------|-----------|----------|
| SUBJECT | 90-100 | C-suite + direct violation + material benefit |
| TARGET | 70-89 | Officer/Director + substantial evidence |
| WITNESS | 50-69 | Transaction participant + documentary evidence |
| PERSON_OF_INTEREST | 30-49 | Peripheral involvement |
| VICTIM | 0-29 | Shareholders harmed |
| ENABLER | 0-29 | Facilitated violations without benefit |

#### Risk Score Components

- **Violation Severity**: 30% (0-30 points)
- **Evidence Strength**: 25% (0-25 points)
- **Corporate Position**: 25% (0-25 points)
- **Financial Benefit**: 20% (0-20 points)

#### Key Classes

```python
class ActorRoleClassifier:
    def classify_actor(
        actor: ActorProfile,
        violation_details: Optional[List[Dict[str, Any]]],
        evidence_items: Optional[List[Dict[str, Any]]]
    ) -> ActorRole
    
    def calculate_risk_score(
        actor: ActorProfile,
        violation_details: Optional[List[Dict[str, Any]]],
        evidence_items: Optional[List[Dict[str, Any]]]
    ) -> RiskScoreComponents
    
    def get_priority_actors(
        actors: List[ActorProfile],
        min_risk_score: float = 50.0
    ) -> List[ActorProfile]
```

#### Usage Example

```python
from src.detection.actor_role_classifier import ActorRoleClassifier

classifier = ActorRoleClassifier()

# Classify single actor
role = classifier.classify_actor(actor, violations, evidence)
print(f"Actor classified as: {role.value}")
print(f"Risk score: {actor.risk_score}")

# Batch classify
classifications = classifier.classify_multiple_actors(actors)

# Get priority actors for interrogation
priority = classifier.get_priority_actors(actors, min_risk_score=50.0)
```

### 3. Evidence Attribution Linker

**File**: `src/core/evidence_chain/evidence_attribution.py`

Links evidence to actors through multiple attribution mechanisms with relevance scoring.

#### Attribution Types

| Type | Relevance | Description |
|------|-----------|-------------|
| DIRECT_AUTHORSHIP | 1.0 | Signed or certified document |
| DISCLOSURE_OBLIGOR | 0.95 | SOX 302/906 certification duty |
| TRANSACTION_PARTY | 0.9 | Direct transaction participant |
| BENEFICIARY | 0.85 | Financial benefit recipient |
| FIDUCIARY_ROLE | 0.8 | Role requires disclosure |
| INDIRECT | 0.5 | Mentioned but not direct |

#### Key Classes

```python
@dataclass
class EvidenceAttribution:
    actor_id: str
    evidence_id: str
    attribution_type: AttributionType
    relevance_score: float  # 0.0-1.0
    attribution_date: Optional[date]
    metadata: Dict[str, Any]

class EvidenceAttributionLinker:
    def attribute_evidence_to_actors(
        actors: List[ActorProfile],
        evidence_items: List[Dict[str, Any]],
        node_results: Optional[Dict[str, Any]]
    ) -> List[EvidenceAttribution]
    
    def calculate_actor_evidence_strength(
        actor_id: str
    ) -> float
```

#### Signature Extraction Patterns

```python
SIGNATURE_PATTERNS = [
    r'/s/\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # /s/ John Smith
    r'Signature:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    r'By:\s*/s/\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    r'Signed by:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    r'Pursuant to[^:]+:\s*/s/\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
]
```

#### Usage Example

```python
from src.core.evidence_chain.evidence_attribution import EvidenceAttributionLinker

linker = EvidenceAttributionLinker()

# Create attributions
attributions = linker.attribute_evidence_to_actors(
    actors=actors,
    evidence_items=evidence_items,
    node_results=node_results
)

# Filter high-relevance attributions
high_rel = linker.get_high_relevance_attributions(min_relevance=0.8)

# Get attributions for specific actor
actor_attrs = linker.get_attributions_for_actor(actor_id)

# Calculate evidence strength
strength = linker.calculate_actor_evidence_strength(actor_id)
```

### 4. Interrogation Package Generator

**File**: `src/reporting/interrogation_package.py`

Generates DOJ-ready interview protocols with 5 sections following FBI interview phases.

#### Package Structure

1. **SECTION I: BACKGROUND**
   - Corporate positions with dates
   - Compensation history (salary, equity, bonuses)

2. **SECTION II: VIOLATIONS ATTRIBUTED**
   - Statutory violations with actor's role
   - Financial impact amounts
   - Evidence strength ratings

3. **SECTION III: EVIDENCE EXHIBITS**
   - Chronologically organized evidence
   - Direct quotes with actor involvement
   - FRE 902 authentication notes

4. **SECTION IV: INTERROGATION PROTOCOL**
   - Interview objectives (legal elements to establish)
   - Question tree: RAPPORT → BASELINE → ACCUSATION → CONFRONTATION
   - Anticipated defenses with rebuttal evidence

5. **SECTION V: LEGAL FRAMEWORK**
   - Applicable statutes with elements of proof
   - Evidence strength per element
   - USSG sentencing calculations

#### FBI Interview Phases

```python
class InterviewPhase(Enum):
    RAPPORT = "RAPPORT"             # Build rapport, baseline behavior
    BASELINE = "BASELINE"           # Establish factual baseline
    ACCUSATION = "ACCUSATION"       # Present accusations/evidence
    CONFRONTATION = "CONFRONTATION" # Direct confrontation
```

#### Key Classes

```python
@dataclass
class InterrogationPackage:
    actor_id: str
    actor_name: str
    actor_role: ActorRole
    risk_score: float
    generation_date: datetime
    corporate_positions: List[Dict[str, Any]]
    compensation_history: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    evidence_exhibits: List[Dict[str, Any]]
    interview_objectives: List[str]
    questions: List[InterrogationQuestion]
    anticipated_defenses: List[Dict[str, Any]]
    applicable_statutes: List[Dict[str, Any]]
    evidence_strength_by_element: Dict[str, float]
    ussg_sentencing: Dict[str, Any]

class InterrogationPackageGenerator:
    def generate_package(
        actor: ActorProfile,
        actor_role: ActorRole,
        violations: List[Dict[str, Any]],
        evidence_attributions: List[EvidenceAttribution],
        evidence_items: List[Dict[str, Any]]
    ) -> InterrogationPackage
```

#### Usage Example

```python
from src.reporting.interrogation_package import InterrogationPackageGenerator

generator = InterrogationPackageGenerator()

# Generate package
package = generator.generate_package(
    actor=actor,
    actor_role=ActorRole.TARGET,
    violations=violations,
    evidence_attributions=evidence_attributions,
    evidence_items=evidence_items
)

# Access sections
print(f"Positions: {package.corporate_positions}")
print(f"Violations: {len(package.violations)}")
print(f"Questions: {len(package.questions)}")
print(f"USSG: {package.ussg_sentencing}")

# Export to dict
package_dict = package.to_dict()
```

## Database Schema

### Tables

#### 1. actor_profiles
```sql
CREATE TABLE actor_profiles (
    actor_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    actor_type VARCHAR(50) NOT NULL,
    cik VARCHAR(10),
    first_appearance DATE,
    last_appearance DATE,
    risk_score DECIMAL(5, 2) DEFAULT 0.0,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_actor_profiles_risk_score ON actor_profiles (risk_score DESC);
CREATE INDEX idx_actor_profiles_cik ON actor_profiles (cik);
```

#### 2. actor_roles
```sql
CREATE TABLE actor_roles (
    id SERIAL PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actor_profiles(actor_id),
    role_name VARCHAR(255) NOT NULL,
    role_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    source VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3. evidence_attributions
```sql
CREATE TABLE evidence_attributions (
    id SERIAL PRIMARY KEY,
    actor_id UUID NOT NULL REFERENCES actor_profiles(actor_id),
    evidence_id VARCHAR(255) NOT NULL,
    attribution_type VARCHAR(50) NOT NULL,
    relevance_score DECIMAL(4, 3) NOT NULL,
    attribution_date DATE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 4. interrogation_packages
```sql
CREATE TABLE interrogation_packages (
    package_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID NOT NULL REFERENCES actor_profiles(actor_id),
    actor_role VARCHAR(50) NOT NULL,
    risk_score DECIMAL(5, 2) NOT NULL,
    generation_date TIMESTAMPTZ NOT NULL,
    corporate_positions JSONB,
    compensation_history JSONB,
    violations JSONB,
    evidence_exhibits JSONB,
    interview_objectives JSONB,
    anticipated_defenses JSONB,
    applicable_statutes JSONB,
    evidence_strength_by_element JSONB,
    ussg_sentencing JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 5. interrogation_questions
```sql
CREATE TABLE interrogation_questions (
    question_id SERIAL PRIMARY KEY,
    package_id UUID NOT NULL REFERENCES interrogation_packages(package_id),
    phase VARCHAR(50) NOT NULL,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    legal_purpose TEXT NOT NULL,
    anticipated_response TEXT,
    follow_up_questions JSONB,
    rebuttal_evidence JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Views

#### priority_actors
```sql
CREATE VIEW priority_actors AS
SELECT ap.*, array_agg(DISTINCT ar.role_name) as roles
FROM actor_profiles ap
LEFT JOIN actor_roles ar ON ap.actor_id = ar.actor_id
WHERE ap.risk_score >= 50.0
GROUP BY ap.actor_id
ORDER BY ap.risk_score DESC;
```

#### subject_target_summary
```sql
CREATE VIEW subject_target_summary AS
SELECT ap.*, ar.role_type, COUNT(DISTINCT ea.evidence_id) as evidence_count
FROM actor_profiles ap
JOIN actor_roles ar ON ap.actor_id = ar.actor_id
LEFT JOIN evidence_attributions ea ON ap.actor_id = ea.actor_id
WHERE ar.role_type IN ('SUBJECT', 'TARGET')
GROUP BY ap.actor_id, ar.role_type
ORDER BY ap.risk_score DESC;
```

## Integration with Master Controller

Phase 5.5 is integrated into the Master Execution Controller between Phase 5 (Pattern Detection) and Phase 6 (Dual-Agent Validation).

### Execution Flow

```python
async def _execute_phase_5_5_actor_mapping(self):
    """Execute Phase 5.5: Actor Mapping & Interrogation Package Generation."""
    
    # Step 1: Extract actors from nodes and patterns
    extraction_engine = ActorExtractionEngine()
    actors = extraction_engine.extract_actors_from_nodes(self.node_results)
    actors = extraction_engine.extract_actors_from_patterns(self.detection_results)
    
    # Step 2: Classify actors and calculate risk scores
    classifier = ActorRoleClassifier()
    for actor in actors:
        role = classifier.classify_actor(actor, violations, evidence)
        self.actor_classifications[actor.actor_id] = role
    
    # Step 3: Attribute evidence to actors
    attribution_linker = EvidenceAttributionLinker()
    self.evidence_attributions = attribution_linker.attribute_evidence_to_actors(
        actors, evidence_items, self.node_results
    )
    
    # Step 4: Generate interrogation packages (risk >= 50)
    package_generator = InterrogationPackageGenerator()
    priority_actors = classifier.get_priority_actors(actors, min_risk_score=50.0)
    
    for actor in priority_actors:
        package = package_generator.generate_package(
            actor, role, violations, attributions, evidence_items
        )
        self.interrogation_packages[actor.actor_id] = package
```

### State Variables

```python
# Phase 5.5 state
self.actor_profiles: List[ActorProfile]
self.actor_classifications: Dict[str, ActorRole]
self.evidence_attributions: List[EvidenceAttribution]
self.interrogation_packages: Dict[str, InterrogationPackage]
```

### UnifiedAnalysisResult

Phase 5.5 results are included in the final analysis result:

```python
@dataclass
class UnifiedAnalysisResult:
    # ... existing fields ...
    actor_profiles: Optional[List[ActorProfile]]
    interrogation_packages: Optional[Dict[str, InterrogationPackage]]
```

## Testing Guide

### Test Coverage

- **test_actor_extraction.py**: 22 test cases
  - Actor profile creation and merging
  - Extraction from nodes 1, 2, 5, 7, 10
  - Fuzzy matching and CIK deduplication
  - Pattern extraction

- **test_actor_classification.py**: 20 test cases
  - DOJ 6-tier classification
  - Risk score calculation
  - Component scoring (violations, evidence, position, benefit)
  - Enabler detection

- **test_evidence_attribution.py**: 21 test cases
  - Signature extraction
  - Attribution type determination
  - Relevance scoring
  - Evidence strength calculation

- **test_interrogation_package.py**: 18 test cases
  - Package generation for all actor roles
  - Section building (background, violations, evidence, protocol, legal)
  - Question tree generation
  - USSG sentencing calculation

### Running Tests

```bash
# Run all actor mapping tests
pytest tests/detection/test_actor_*.py tests/detection/test_evidence_*.py tests/detection/test_interrogation_*.py -v

# Run with coverage
pytest tests/detection/ --cov=src/detection --cov=src/core/evidence_chain --cov=src/reporting -v

# Run specific test
pytest tests/detection/test_actor_extraction.py::TestActorExtractionEngine::test_extract_from_node1_form4 -v
```

### Test Data Patterns

```python
# Sample node result for testing
node_results = {
    'node1': {
        'findings': {
            'transactions': [
                {
                    'reporting_owner': 'John Smith',
                    'transaction_code': 'P',
                    'transaction_date': '2023-01-15',
                    'shares': 1000,
                    'price_per_share': 50.0
                }
            ]
        }
    }
}

# Sample violation for testing
violations = [
    {
        'violation_type': 'insider_trading',
        'severity': 'HIGH',
        'financial_impact': 2000000,
        'description': 'Trading on MNPI'
    }
]

# Sample evidence for testing
evidence_items = [
    {
        'id': 'evidence-1',
        'type': '10-K',
        'content': '/s/ John Smith\nCEO',
        'filing_date': '2023-03-01'
    }
]
```

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**: Extract all actors at once rather than one-by-one
2. **Caching**: Cache normalized names and CIK lookups
3. **Lazy Loading**: Only generate packages for priority actors (risk >= 50)
4. **Database Indexes**: Risk score, CIK, relevance score indexes
5. **Async I/O**: All operations are async-compatible

### Scalability

- **Memory**: Each ActorProfile ~1KB, scales to thousands of actors
- **Performance**: Phase 5.5 adds ~5-10 seconds for typical analysis
- **Database**: Optimized with indexes and views for fast queries

## Integration Points

### Input Sources
- **Phase 4**: Node results (nodes 1, 2, 5, 7, 10)
- **Phase 5**: Pattern detection results (23 algorithms)
- **Phase 2**: SEC filings and parsed documents

### Output Consumers
- **Phase 9**: Dossier generator (Sections IX & X)
- **Database**: Persistent storage for interrogation packages
- **API**: External systems can query actor data

## Future Enhancements

1. **Actor Network Visualization**: Graph-based visualization of actor relationships
2. **Machine Learning Risk Scoring**: Train ML models on historical prosecution outcomes
3. **Real-time Updates**: Subscribe to actor changes and regenerate packages
4. **Multi-language Support**: Translate interrogation packages to other languages
5. **Video Interview Integration**: Link packages to recorded interviews

## References

### Legal Citations
- **18 U.S.C. § 1348**: Securities and Commodities Fraud
- **17 CFR § 240.10b-5**: Employment of Manipulative Devices
- **SOX § 302/906**: Corporate Responsibility for Financial Reports
- **FRE 902(13)/(14)**: Self-Authenticating Evidence

### DOJ Resources
- FBI Interview Protocols and Best Practices
- USSG Sentencing Guidelines Manual
- DOJ Criminal Resource Manual: Securities Fraud

### Implementation Notes
- Actor extraction uses fuzzy matching (85%+ similarity threshold)
- Risk scores are conservative (ambiguous cases classified to lower tier)
- Interrogation packages follow FBI PEACE model (Preparation, Engage, Account, Closure, Evaluate)

## Support

For issues or questions about the actor mapping implementation:
1. Review test cases for usage examples
2. Check database schema for data structure
3. Consult legal framework statutes for compliance requirements
4. Contact JLAW development team for technical support
