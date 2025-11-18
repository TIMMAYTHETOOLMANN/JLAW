# Statute Mapper - Legal Compliance Module

## Overview
Complete statute mapping system that maps forensic findings to specific USC and CFR violations with direct GovInfo API access for legal document retrieval.

## Implementation Status
✅ **FULLY IMPLEMENTED** - Module created and operational

## Components

### 1. StatuteTitle (Enum)
Six USC titles relevant to securities fraud:
- **USC_15**: Commerce and Trade (Securities laws)
- **USC_17_CFR**: SEC Regulations (CFR)
- **USC_18**: Crimes and Criminal Procedure (Criminal fraud)
- **USC_26**: Internal Revenue Code (Tax disclosures)
- **USC_31**: Money and Finance (BSA/AML)
- **USC_12**: Banks and Banking (Banking regulations)

### 2. StatuteViolation (dataclass)
Detected violation container:
- `title`: USC/CFR title number
- `section`: Section identifier
- `description`: Human-readable violation description
- `severity`: CRIMINAL, CIVIL, or REGULATORY
- `max_penalty`: Maximum penalty description
- `imprisonment_years`: Maximum imprisonment term
- `fine_amount`: Maximum fine amount
- `pattern_matched`: Evidence that triggered detection
- `evidence_refs`: List of evidence IDs
- `detection_confidence`: 0.0-1.0 confidence score

### 3. StatuteMapper (class)
Main mapping engine with GovInfo integration.

#### Initialization
```python
mapper = StatuteMapper(api_key="YOUR_GOVINFO_API_KEY")
```

**Attributes:**
- `api_key`: GovInfo API key
- `base_url`: https://api.govinfo.gov
- `hash_chain`: Forensic audit trail
- `statute_cache`: Document cache
- `violation_patterns`: Pattern library (13 patterns)

## Violation Patterns

### 15 USC §77g - Securities Act Registration
- **Severity**: CIVIL
- **Patterns**: Missing financials, incomplete risk factors, undisclosed contracts
- **Forms**: S-1, S-3, S-4, S-8

### 15 USC §78j(b) - Rule 10b-5 Anti-Fraud
- **Severity**: CIVIL_CRIMINAL
- **Patterns**: Material misstatement, omission, insider trading, price manipulation
- **Rule**: 10b-5

### 18 USC §1001 - False Statements
- **Severity**: CRIMINAL
- **Imprisonment**: Up to 5 years
- **Patterns**: False statements to SEC, contradictory statements, concealment

### 18 USC §1343 - Wire Fraud
- **Severity**: CRIMINAL
- **Imprisonment**: Up to 20 years (30 if affects financial institution)
- **Patterns**: Electronic filing fraud, false investor communication, pump-and-dump

### 18 USC §1348 - Securities Fraud
- **Severity**: CRIMINAL
- **Imprisonment**: Up to 25 years
- **Patterns**: Accounting fraud, false revenue recognition, concealed liabilities
- **Note**: No personal benefit required for conviction

### 18 USC §1350 - SOX Certification
- **Severity**: CRIMINAL
- **Knowing**: 10 years + $1M fine
- **Willful**: 20 years + $5M fine
- **Patterns**: False CEO/CFO certification despite known issues

### 18 USC §1519 - Document Destruction
- **Severity**: CRIMINAL
- **Imprisonment**: Up to 20 years
- **Patterns**: Mass shredding, email deletion, audit workpaper destruction

### 17 CFR §229.303 - MD&A Requirements (Item 303)
- **Severity**: REGULATORY
- **Patterns**: Boilerplate MD&A, missing trend discussion, inadequate liquidity analysis

### 17 CFR §240.10b-5 - Rule 10b-5
- **Severity**: CIVIL_CRIMINAL
- **Patterns**: Deceptive device, untrue material fact, material omission

### 17 CFR §240.12b-25 - Late Filing Notification
- **Severity**: REGULATORY
- **Penalties**: $25,000 - $225,000
- **Patterns**: Late without NT, false NT reason, undisclosed restatement

### 26 USC - Tax Disclosure
- **Severity**: CIVIL
- **Patterns**: Unusual tax rate change, insufficient valuation allowance, undisclosed audit

### 31 USC §5318 - BSA/AML
- **Severity**: CRIMINAL
- **Pattern Violation**: $100K amount over 12 months = $500K fine
- **Patterns**: Undisclosed AML weakness, hidden consent order, SAR pattern

### 12 USC §161 - Bank Reporting
- **Severity**: REGULATORY
- **Patterns**: Call report discrepancy, inadequate loan loss reserve, hidden regulatory action

## Main Methods

### map_violations()
```python
violations = await mapper.map_violations(forensic_findings)
```

**Input**: Forensic analysis results (from SEC analyzer)

**Process**:
1. Initialize aiohttp session
2. Check each violation pattern against findings
3. Match red flags to patterns
4. Calculate confidence scores
5. Sort by severity and confidence
6. Log to forensic hash chain

**Output**: List of StatuteViolation objects sorted by severity

**Confidence Scoring**:
- CRITICAL severity: 0.9 base
- HIGH severity: 0.7 base
- MEDIUM severity: 0.5 base
- LOW severity: 0.3 base
- Known patterns (WorldCom, Marvell, Enron): +0.2 bonus

### fetch_statute_text()
```python
statute = await mapper.fetch_statute_text(
    title=18,
    section="1348",
    year=2024  # Optional
)
```

**Returns**:
```python
{
    "title": 18,
    "section": "1348",
    "year": 2024,
    "text_url": "https://...",
    "pdf_url": "https://...",
    "xml_url": "https://...",
    "last_modified": "2024-01-15",
    "granule_id": "USCODE-2024-title18-chap2B-sec1348"
}
```

**Features**:
- GovInfo API integration
- Result caching
- 503 retry with 30s backoff
- Automatic year defaulting (previous year for stability)

### fetch_cfr_rule()
```python
rule = await mapper.fetch_cfr_rule(
    title=17,
    part=240,
    section="10b-5",
    year=2024  # Optional
)
```

**Returns**:
```python
{
    "title": 17,
    "part": 240,
    "section": "10b-5",
    "year": 2024,
    "volume": 3,
    "text_url": "https://...",
    "pdf_url": "https://...",
    "xml_url": "https://...",
    "last_modified": "2024-04-01"
}
```

**CFR Volume Mapping (Title 17)**:
- Volume 1: Parts 1-40
- Volume 2: Parts 41-199
- Volume 3: Parts 200-239
- Volume 4: Parts 240+

**Update Schedule**: CFR Title 17 updates April 1 annually

## Pattern Matching Logic

### Red Flag to Pattern Mappings
```python
{
    "material_misstatement": [
        "impossible_growth_ratio",
        "revenue_pull_forward"
    ],
    "material_omission": [
        "missing_mda",
        "undisclosed_material_event"
    ],
    "accounting_fraud": [
        "benford_violation",
        "expense_capitalization"
    ],
    "document_destruction": [
        "missing_audit_trail",
        "access_denied"
    ],
    "late_without_nt": [
        "missing_nt_filing"
    ]
}
```

### Special Detection Rules

**Material Misstatement Detection**:
```python
if fraud_indicators["overall_risk"] > 0.7:
    # Trigger 15 USC §78j(b) and 18 USC §1348
```

**False Revenue Recognition**:
```python
if anomaly["type"] == "quarter_end_spike":
    # Trigger 18 USC §1348
    # Confidence: 0.8
```

## Usage Example

```python
import asyncio
from src.forensics.sec_edgar_analyzer import SECForensicAnalyzer
from src.forensics.statute_mapper import StatuteMapper

async def full_forensic_analysis():
    # Analyze SEC filing
    sec_analyzer = SECForensicAnalyzer()
    filing_analysis = await sec_analyzer.analyze_filing(
        cik="0001318605",  # Tesla
        accession_number="0001564590-24-000123",
        filing_type="10-K"
    )
    
    # Map to statutes
    mapper = StatuteMapper(api_key="YOUR_API_KEY")
    
    violations = await mapper.map_violations({
        "red_flags": filing_analysis.red_flags,
        "fraud_indicators": filing_analysis.fraud_indicators,
        "revenue_anomalies": filing_analysis.revenue_anomalies
    })
    
    # Report violations
    for violation in violations:
        print(f"\n{violation.severity} VIOLATION")
        print(f"Statute: {violation.title} USC §{violation.section}")
        print(f"Description: {violation.description}")
        print(f"Penalty: {violation.max_penalty}")
        print(f"Confidence: {violation.detection_confidence:.1%}")
        
        # Fetch actual statute text
        if violation.severity == "CRIMINAL":
            statute = await mapper.fetch_statute_text(
                title=violation.title,
                section=violation.section
            )
            print(f"Statute URL: {statute['pdf_url']}")
    
    # Fetch specific regulation
    rule_10b5 = await mapper.fetch_cfr_rule(
        title=17,
        part=240,
        section="10b-5"
    )
    print(f"\nRule 10b-5: {rule_10b5['pdf_url']}")

asyncio.run(full_forensic_analysis())
```

## GovInfo API Requirements

### API Key
- Required for all requests
- Get free key at: https://api.data.gov/signup/
- Pass in `api_key` parameter

### Rate Limits
- Generally no strict limits for reasonable use
- 503 status triggers 30-second retry
- Built-in backoff for stability

### Granule ID Format

**USC**: `USCODE-{year}-title{title}-chap{chapter}-sec{section}`
**CFR**: `CFR-{year}-title{title}-vol{volume}-sec{part}-{section}`

### Link Service Fallback
If granule fetch fails, uses link service:
```
https://www.govinfo.gov/link/cfr/{title}/{part}/{section}?link-type=pdf&year=mostrecent
```

## Dependencies

**Standard Library**:
- asyncio
- json
- re
- datetime
- typing
- dataclasses
- enum
- urllib.parse

**External Packages**:
- aiohttp

**Internal Modules**:
- src.forensics.core.integrity_manager

## Forensic Integrity

All violation mappings logged to hash chain:
- Evidence type: "statute_mapping"
- Integrity level: CRITICAL
- Metadata: violation count, criminal violation count
- Immutable audit trail

## Integration Points

### Input Format (from SEC Analyzer)
```python
{
    "red_flags": [
        {
            "type": "revenue_pull_forward",
            "severity": "CRITICAL",
            "pattern": "marvell_technology"
        }
    ],
    "fraud_indicators": {
        "overall_risk": 0.85
    },
    "revenue_anomalies": [
        {
            "type": "quarter_end_spike",
            "deviation": 0.18
        }
    ]
}
```

### Output Format
```python
[
    StatuteViolation(
        title=18,
        section="1348",
        description="Securities fraud - revenue_pull_forward",
        severity="CRIMINAL",
        max_penalty="Up to 25 years imprisonment",
        imprisonment_years=25,
        fine_amount=None,
        pattern_matched={...},
        evidence_refs=["..."],
        detection_confidence=0.9
    )
]
```

## Standards & Regulations

### Criminal Statutes (Title 18)
- §1001: False statements (5 years)
- §1343: Wire fraud (20 years)
- §1348: Securities fraud (25 years)
- §1350: SOX certification (10-20 years)
- §1519: Document destruction (20 years)

### Securities Laws (Title 15)
- §77g: Registration requirements
- §78j(b): Anti-fraud (Rule 10b-5)

### CFR Regulations (Title 17)
- §229.303: MD&A requirements (Item 303)
- §240.10b-5: Anti-fraud rule
- §240.12b-25: Late filing notification

### BSA/AML (Title 31)
- §5318: Suspicious activity reporting

### Banking (Title 12)
- §161: Bank examination and reporting

## File Location
`src/forensics/statute_mapper.py`

## Next Integration Steps
⏳ **WAITING** - Ready for next modular enhancement file

**No additional files generated** - Only statute mapper and documentation created as requested.

## Status Summary
- ✅ Module created
- ✅ Import tests passing
- ✅ Integration with integrity_manager verified
- ✅ Integration with SEC analyzer ready
- ✅ GovInfo API support complete
- ✅ 13 violation patterns implemented
- ✅ No dependency conflicts
- ✅ No overlapping functionality
- ⏳ Awaiting next enhancement file

