# Multi-Jurisdictional Compliance Framework

## Overview

The **Multi-Jurisdictional Compliance Framework** is a DOJ-grade legal compliance mapping system that determines prosecutorial authority across federal, state (50 states), and international jurisdictions. It provides comprehensive venue analysis and forum shopping optimization for securities fraud prosecution.

## Architecture

### Core Components

1. **JurisdictionMapper** (`src/compliance/jurisdiction_mapper.py`)
   - Determines all jurisdictions with prosecutorial authority
   - Implements 7 jurisdiction triggers
   - Maps federal, state, and international authority

2. **StateSecuritiesLawEngine** (`src/compliance/state_securities_laws.py`)
   - 50-state Blue Sky Law database
   - State violation analysis
   - Penalty comparison (state vs federal)

3. **InternationalComplianceAnalyzer** (`src/compliance/international_compliance.py`)
   - International regulatory framework (UK, EU, Canada, Australia, Switzerland, Japan, Singapore, Hong Kong)
   - Cross-border violation detection
   - MLAT (Mutual Legal Assistance Treaty) request generation

4. **ForumShoppingOptimizer** (`src/compliance/forum_optimizer.py`)
   - Multi-factor venue scoring (0-100 scale)
   - Prosecution strategy generation
   - Primary/secondary/tertiary venue recommendations

## Jurisdiction Determination Logic

### 7 Jurisdiction Triggers

1. **ISSUER_DOMICILE**: State of incorporation
2. **PRINCIPAL_PLACE_OF_BUSINESS**: Headquarters location
3. **OFFER_LOCATION**: Where securities offered/sold
4. **VICTIM_RESIDENCE**: Where defrauded investors reside
5. **ACTOR_RESIDENCE**: Where perpetrators reside
6. **LISTING_VENUE**: NYSE/NASDAQ triggers federal SEC
7. **CROSS_BORDER**: International securities sales

### Federal Jurisdiction

Automatically triggered for:
- **SEC**: Securities registered under Securities Exchange Act of 1934
- **DOJ**: Interstate commerce, wire/mail fraud
- **FINRA**: Broker-dealer involvement (optional)

Key Statutes:
- 15 U.S.C. §78j(b) - Rule 10b-5 (Securities Fraud)
- 18 U.S.C. §1348 - Securities/Commodities Fraud
- 15 U.S.C. §78p - Section 16 (Insider Trading)

### State Jurisdiction

Triggered by:
- Issuer domiciled in state
- Principal place of business in state
- Securities offered/sold in state
- Victims reside in state
- Actors reside in state

**Major State Frameworks:**
- **California**: CA Corp Code §25401 (fraud), §25110 (registration) - Extraterritorial reach
- **New York**: Martin Act (NY Gen Bus Law §352) - **Strict liability (no scienter required)**, 6-year SOL
- **Texas**: TX Securities Act §33.04 - **Up to 99 years criminal penalty**
- **Florida**: FL Stat §517.07 - Fraudulent transactions

**Uniform Securities Act (USA) States (40 states):**
- USA §501 - Securities Fraud
- USA §301 - Registration Requirements
- USA §401 - Broker-Dealer Registration

### International Jurisdiction

Triggered by:
- Securities listed in foreign jurisdiction
- Securities offered/sold to foreign investors
- Cross-border activity
- Foreign actors involved

**Major International Frameworks:**

**United Kingdom (FCA):**
- FSMA 2000 s.397 - Misleading statements
- Criminal Justice Act 1993 Part V - Insider Dealing
- Market Abuse Regulation (MAR)
- Penalties: Up to 7 years + unlimited fines
- **MLAT Available**: Yes

**European Union (ESMA):**
- MAR Article 15 - Market Manipulation
- MiFID II - Conduct violations
- Prospectus Regulation (EU 2017/1129)
- Penalties: Up to €5M or 10-15% of annual turnover
- **MLAT Available**: Yes

**Canada (IIROC/CSA):**
- National Instrument 31-103
- Ontario Securities Act
- Criminal Code §380 - Fraud (up to 14 years)
- **MLAT Available**: Yes

**Australia (ASIC):**
- Corporations Act 2001 - Market misconduct (up to 10 years)
- ASIC Act 2001
- **MLAT Available**: Yes

## Forum Shopping Optimization

### Venue Scoring Algorithm

Multi-factor scoring (0-100 scale) with weighted factors:

1. **Penalty Severity (25%)**: Criminal years + civil damages
2. **Evidentiary Advantages (20%)**: Scienter requirements, burden of proof
3. **Statute of Limitations (15%)**: Time remaining
4. **Precedent Favorability (15%)**: Case law strength
5. **Prosecutorial Resources (10%)**: Experienced prosecutors available
6. **Political Will (10%)**: Regulatory enforcement priorities
7. **Victim Impact (5%)**: Local victim concentration

### Scoring Examples

| Jurisdiction | Penalty | Evidentiary | SOL | Precedent | Resources | Political | Victim | **Total Score** |
|-------------|---------|-------------|-----|-----------|-----------|-----------|--------|-----------------|
| **Federal (SEC)** | 85 | 80 | 80 | 90 | 95 | 85 | 80 | **85.5** |
| **NY (Martin Act)** | 80 | **95** | **100** | 75 | 85 | 90 | 70 | **86.0** |
| **TX** | **95** | 65 | 60 | 60 | 65 | **95** | 60 | **74.8** |
| **CA** | 75 | 70 | 60 | 75 | 85 | 80 | 75 | **73.5** |

### Prosecution Strategy Output

**Primary Venue**: Highest score (typically federal or NY Martin Act)
- Lead prosecution
- File first
- Set narrative

**Secondary Venues**: Coordinated state AG actions
- File 30-60 days after primary
- Complement primary action
- Maximize penalties

**Tertiary Venues**: International regulators
- File MLAT requests 60-90 days after primary
- Coordinate with primary action
- Secure foreign evidence

## State Law Database Coverage

### Comprehensive 50-State Coverage

**Detailed Coverage (10 major states):**
- California, New York, Texas, Florida, Massachusetts
- Illinois, Pennsylvania, Ohio, Georgia, North Carolina

**USA Framework Coverage (40 states):**
- Alabama, Alaska, Arizona, Arkansas, Colorado, Connecticut, Delaware
- Georgia, Hawaii, Idaho, Illinois, Indiana, Iowa, Kansas, Kentucky
- Louisiana, Maine, Maryland, Massachusetts, Michigan, Minnesota
- Mississippi, Missouri, Montana, Nebraska, Nevada, New Hampshire
- New Jersey, New Mexico, North Carolina, North Dakota, Ohio
- Oklahoma, Oregon, Pennsylvania, Rhode Island, South Carolina
- South Dakota, Tennessee, Utah, Vermont, Virginia, Washington
- West Virginia, Wisconsin, Wyoming

### State Law Variations

**Strictest Liability**: New York Martin Act (no scienter required)
**Longest SOL**: New York (6 years)
**Highest Criminal Penalties**: Texas (up to 99 years)
**Extraterritorial Reach**: California, New York, Texas

## Integration with Master Controller

### Phase 5.6 Execution Flow

```python
# Phase 5.6: Multi-Jurisdictional Compliance Mapping
await self._execute_phase_5_6_jurisdiction_mapping()
```

**Steps:**

1. **Map Jurisdictions** - Determine all authorities
2. **Analyze State Violations** - Apply 50-state database
3. **Analyze International Violations** - Apply international frameworks
4. **Optimize Venues** - Score and rank forums
5. **Generate Strategy** - Create coordinated prosecution timeline

### State Storage

```python
self.phase3_results = {
    'jurisdictions': List[JurisdictionProfile],
    'state_violations': List[Dict[str, Any]],
    'international_violations': List[Dict[str, Any]],
    'forum_analyses': List[ForumAnalysis],
    'prosecution_strategy': Dict[str, Any]
}
```

## Database Schema

### 5 New Tables

**jurisdictions** - All jurisdictions with authority
```sql
CREATE TABLE jurisdictions (
    jurisdiction_id TEXT PRIMARY KEY,
    jurisdiction_name TEXT NOT NULL,
    jurisdiction_type TEXT NOT NULL, -- STATE | FEDERAL | INTERNATIONAL
    regulatory_body TEXT NOT NULL,
    has_authority BOOLEAN NOT NULL
);
```

**jurisdiction_authority** - Authority basis with evidence links
```sql
CREATE TABLE jurisdiction_authority (
    id SERIAL PRIMARY KEY,
    jurisdiction_id TEXT NOT NULL,
    authority_basis TEXT NOT NULL,
    evidence_id TEXT,
    statute_citation TEXT
);
```

**state_violations** - State-specific violations
```sql
CREATE TABLE state_violations (
    violation_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    statute_citation TEXT NOT NULL,
    penalties_json TEXT NOT NULL,
    elements_met TEXT[]
);
```

**international_violations** - International violations
```sql
CREATE TABLE international_violations (
    violation_id TEXT PRIMARY KEY,
    jurisdiction TEXT NOT NULL,
    regulation_citation TEXT NOT NULL,
    mlat_available BOOLEAN NOT NULL
);
```

**forum_analyses** - Venue scoring and recommendations
```sql
CREATE TABLE forum_analyses (
    analysis_id TEXT PRIMARY KEY,
    jurisdiction_id TEXT NOT NULL,
    venue_score REAL NOT NULL,
    recommended_priority TEXT NOT NULL
);
```

## DOJ Report Enhancements

### 3 New Sections

**SECTION XI: Jurisdictional Authority Map**
- 11.1 Federal Jurisdiction Analysis
- 11.2 State Jurisdiction Analysis
- 11.3 International Jurisdiction Analysis
- 11.4 Jurisdiction Authority Matrix

**SECTION XII: Multi-Jurisdictional Violations**
- 12.1 State-Specific Violations
- 12.2 International Violations
- 12.3 Comparative Violation Analysis

**SECTION XIII: Forum Shopping Analysis & Prosecution Strategy**
- 13.1 Venue Scoring Matrix
- 13.2 Primary Venue Recommendation
- 13.3 Secondary/Tertiary Venue Recommendations
- 13.4 Coordinated Prosecution Timeline

## Usage Examples

### Standalone Usage

```python
from src.compliance import (
    JurisdictionMapper,
    StateSecuritiesLawEngine,
    InternationalComplianceAnalyzer,
    ForumShoppingOptimizer
)

# Map jurisdictions
mapper = JurisdictionMapper()
jurisdictions = await mapper.map_jurisdictions(
    company_profile={'state_of_incorporation': 'CA'},
    violations=[],
    classified_actors={}
)

# Analyze state violations
state_engine = StateSecuritiesLawEngine()
state_violations = await state_engine.analyze_state_violations(
    violations, jurisdictions
)

# Optimize forums
optimizer = ForumShoppingOptimizer()
forum_analyses = await optimizer.analyze_prosecution_venues(
    jurisdictions, violations, state_violations, []
)

strategy = optimizer.generate_prosecution_strategy(forum_analyses)
```

### Integrated with Master Controller

```python
from src.core.master_execution_controller import MasterExecutionController

controller = MasterExecutionController(
    cik="320187",
    company_name="NIKE, Inc.",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("output")
)

result = await controller.execute_full_analysis()

# Access Phase 3 results
phase3 = controller.phase3_results
print(f"Jurisdictions: {len(phase3['jurisdictions'])}")
print(f"Primary Venue: {phase3['prosecution_strategy']['primary_venue']['jurisdiction']}")
```

## Testing

Run comprehensive test suite:

```bash
# Test jurisdiction mapper
pytest tests/test_jurisdiction_mapper.py -v

# Test state securities laws
pytest tests/test_state_securities_laws.py -v

# Test international compliance
pytest tests/test_international_compliance.py -v

# Test forum optimizer
pytest tests/test_forum_optimizer.py -v

# Run all Phase 3 tests
pytest tests/test_jurisdiction*.py tests/test_state*.py tests/test_international*.py tests/test_forum*.py -v --cov=src/compliance
```

## Performance Considerations

- **Lazy Loading**: State laws loaded only when needed
- **Caching**: Jurisdiction determinations cached
- **Batch Processing**: Database inserts batched
- **Async Operations**: All I/O operations async

## Future Enhancements

1. **ML-Based Venue Prediction**: Use historical prosecution data to train venue predictor
2. **Additional Jurisdictions**: Add more international frameworks (Brazil, India, South Korea)
3. **Real-Time Updates**: Subscribe to regulatory changes via APIs
4. **Jurisdiction Conflict Resolution**: Handle overlapping authority automatically
5. **Sentencing Guidelines Integration**: Import USSG calculations
6. **Venue Shopping Risk Score**: Assess risk of forum shopping challenges

## Legal Disclaimer

This framework provides prosecutorial venue analysis for informational purposes only. It does not constitute legal advice. Consultation with qualified legal counsel is required before making prosecution decisions.

## References

- **Uniform Securities Act (2002)**: NCCUSL Model Act
- **Securities Exchange Act of 1934**: 15 U.S.C. §78a et seq.
- **NY Martin Act**: NY Gen Bus Law §§352-359-h
- **CA Corporate Code**: CA Corp Code §§25000-25707
- **UK FSMA 2000**: Financial Services and Markets Act 2000
- **EU MAR**: Market Abuse Regulation (EU) No 596/2014
- **IIROC Rules**: Canadian securities regulations
- **ASIC Act**: Australian Securities and Investments Commission Act 2001

## Contact

For questions or contributions:
- GitHub Issues: [JLAW Issues](https://github.com/TIMMAYTHETOOLMANN/JLAW/issues)
- Documentation: [JLAW Docs](https://github.com/TIMMAYTHETOOLMANN/JLAW/tree/main/docs)
