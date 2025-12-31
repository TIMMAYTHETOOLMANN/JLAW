# Enforcement Routing Guide - Phase 5

## Overview

The Enforcement Routing Engine provides comprehensive enforcement agency routing with SEC investigation trigger assessment, whistleblower program flagging, and multi-agency coordination.

This guide covers:
- Agency jurisdiction decision trees
- SEC trigger threshold documentation
- Whistleblower program reference (Dodd-Frank §922)
- Integration examples

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agency Jurisdiction](#agency-jurisdiction)
3. [SEC Investigation Triggers](#sec-investigation-triggers)
4. [Whistleblower Program](#whistleblower-program)
5. [Penalty Estimation](#penalty-estimation)
6. [Integration Guide](#integration-guide)
7. [API Reference](#api-reference)

---

## Architecture Overview

### Components

**EnforcementRoutingEngine**
- Primary routing engine with threshold-based assessment
- Routes violations to SEC, DOJ, IRS, CFTC, FinCEN
- Assesses SEC trigger thresholds
- Flags whistleblower program relevance
- Estimates penalty ranges

**EnforcementRecommendation**
- Agency routing recommendation with complete justification
- Includes trigger assessment, whistleblower flagging, statutory references
- Provides recommended enforcement actions

**PenaltyRange**
- Conservative penalty estimates based on statutory maximums
- Includes civil and criminal exposure
- Documented legal basis

### Integration Points

```
┌─────────────────────────────────────────────────┐
│         Recursive Analysis Engine               │
│              (15 Nodes)                         │
└────────────────┬────────────────────────────────┘
                 │ Violations
                 ▼
┌─────────────────────────────────────────────────┐
│    Statutory Binding Engine (Phase 1)          │
│    Maps violations to statutes                  │
└────────────────┬────────────────────────────────┘
                 │ Statutory Bindings
                 ▼
┌─────────────────────────────────────────────────┐
│    Enforcement Routing Engine (Phase 5)         │
│    - SEC trigger assessment                     │
│    - Whistleblower flagging                     │
│    - Agency routing                             │
│    - Penalty estimation                         │
└────────────────┬────────────────────────────────┘
                 │ Enforcement Recommendations
                 ▼
┌─────────────────────────────────────────────────┐
│    Prosecutorial Dossier Generator (Phase 4)    │
│    DOJ/SEC submission-ready dossiers            │
└─────────────────────────────────────────────────┘
```

---

## Agency Jurisdiction

### Decision Tree

```
Violation Type → Agency Routing

SECURITIES VIOLATIONS
├── Insider Trading → SEC (primary) + DOJ (if scienter + high damages)
├── Securities Fraud → SEC + DOJ (criminal referral)
├── Market Manipulation → SEC + DOJ
├── Disclosure Violations → SEC
├── Late Filing (Form 4/13D/13G) → SEC
├── Beneficial Ownership → SEC
└── SOX Violations → SEC + PCAOB

TAX VIOLATIONS
├── IRC § 83 Violations → IRS + DOJ Tax Division (if criminal)
├── Tax Evasion → IRS + DOJ Tax Division
└── Unreported Compensation → IRS

COMMODITIES
└── Commodities Fraud → CFTC + DOJ

MONEY LAUNDERING
└── AML Violations → FinCEN + DOJ
```

### Agency Profiles

#### SEC (Securities and Exchange Commission)
**Jurisdiction**: Securities law violations under Securities Act of 1933, Securities Exchange Act of 1934

**Violation Types**:
- Insider trading (Rule 10b-5)
- Securities fraud
- Disclosure violations
- Form 4/13D/13G late filings
- SOX certification violations
- Market manipulation

**Penalties**:
- Civil: Up to $1M+ per violation (entities)
- Disgorgement of ill-gotten gains
- Officer/director bars
- Criminal referral to DOJ

**Referral Process**:
- Submit via TCR (Tips, Complaints, and Referrals) system
- Include evidence package with FRE 902(13)/(14) compliance
- Wells notice process for subjects

#### DOJ (Department of Justice)
**Jurisdiction**: Criminal violations under federal criminal statutes

**Violation Types**:
- Securities fraud (18 USC § 1348)
- Wire fraud (18 USC § 1343)
- Mail fraud (18 USC § 1341)
- Tax evasion (26 USC § 7201)
- Obstruction of justice

**Penalties**:
- Criminal: Up to 25 years imprisonment + fines
- Asset forfeiture
- Restitution to victims

**Referral Process**:
- Criminal referral package with prosecutorial memo
- Grand jury proceedings
- Coordinate with SEC for parallel civil/criminal actions

#### IRS (Internal Revenue Service)
**Jurisdiction**: Tax law violations under Internal Revenue Code

**Violation Types**:
- IRC § 83 compensation violations
- Tax evasion
- False tax returns
- Unreported income

**Penalties**:
- Civil: Back taxes + penalties (20-75% of underpayment)
- Criminal: Up to 5 years imprisonment

**Referral Process**:
- Submit IRS Form 3949-A (Information Referral)
- Criminal Investigation Division (IRS-CI) for criminal cases
- Coordinate with DOJ Tax Division

#### CFTC (Commodity Futures Trading Commission)
**Jurisdiction**: Commodities and derivatives violations

**Violation Types**:
- Commodities fraud
- Futures manipulation
- Swap dealer violations

**Penalties**:
- Civil penalties up to $1M+ per violation
- Trading bans

#### FinCEN (Financial Crimes Enforcement Network)
**Jurisdiction**: Anti-money laundering and financial crimes

**Violation Types**:
- Bank Secrecy Act violations
- Money laundering
- Suspicious activity not reported

**Penalties**:
- Civil penalties up to $100K per violation
- Criminal referral to DOJ

---

## SEC Investigation Triggers

### Trigger Thresholds

The SEC Division of Enforcement uses specific thresholds to prioritize investigations:

#### Insider Trading
- **Threshold**: 1 violation + $100,000 damages
- **Rationale**: Material harm to investors, market integrity concern
- **Typical Timeline**: Investigation opens within 30-90 days

#### Securities Fraud
- **Threshold**: 1 violation + $500,000 damages
- **Rationale**: Significant investor harm, potential systemic impact
- **Typical Timeline**: Investigation opens within 30 days

#### Late Filing (Form 4/13D/13G)
- **Threshold**: 5+ violations + $0 damages
- **Rationale**: Pattern of non-compliance with reporting requirements
- **Typical Timeline**: Investigation opens within 90-180 days

#### Disclosure Violations
- **Threshold**: 3+ violations + $0 damages
- **Rationale**: Material information asymmetry
- **Typical Timeline**: Investigation opens within 60-120 days

#### Market Manipulation
- **Threshold**: 1 violation + $250,000 damages
- **Rationale**: Market integrity threat
- **Typical Timeline**: Investigation opens within 30 days

#### SOX Violations
- **Threshold**: 1 violation + $0 damages
- **Rationale**: CEO/CFO certification fraud - zero tolerance
- **Typical Timeline**: Investigation opens immediately

#### Beneficial Ownership Violations
- **Threshold**: 3+ violations + $0 damages
- **Rationale**: Pattern of non-disclosure
- **Typical Timeline**: Investigation opens within 90 days

### Assessment Process

```python
from src.enforcement.routing_engine import EnforcementRoutingEngine

engine = EnforcementRoutingEngine()

# Example: Assess SEC trigger for insider trading
violations = [
    {
        'violation_id': 'V001',
        'violation_type': 'insider_trading',
        'estimated_damages': 750000,  # Exceeds $100K threshold
        'scienter_evidence': True
    }
]

trigger_met = engine.assess_sec_trigger(
    violations=violations,
    violation_type='insider_trading'
)

# Result: True (1 violation + $750K damages exceeds threshold)
```

---

## Whistleblower Program

### Dodd-Frank Act Section 922 (15 USC §78u-6)

The SEC Whistleblower Program provides monetary awards to individuals who provide original information leading to successful enforcement actions.

#### Eligibility Criteria

1. **Monetary Threshold**: Sanctions exceed $1,000,000
2. **Jurisdiction**: SEC or CFTC enforcement action
3. **Original Information**: New information not already known
4. **Voluntary Submission**: Submitted before formal request
5. **Leads to Successful Action**: Results in sanctions

#### Award Range

- **Minimum**: 10% of monetary sanctions
- **Maximum**: 30% of monetary sanctions
- **Determination Factors**:
  - Significance of information provided
  - Assistance provided to SEC
  - Law enforcement interest
  - Participation in internal compliance

#### Assessment Process

```python
from src.enforcement.routing_engine import EnforcementRoutingEngine

engine = EnforcementRoutingEngine()

# Example: Assess whistleblower relevance
whistleblower_relevant = engine.assess_whistleblower_relevance(
    estimated_sanctions=2500000,  # $2.5M exceeds $1M threshold
    violation_types=['SEC', 'DOJ']  # SEC jurisdiction
)

# Result: True (exceeds threshold + SEC jurisdiction)

# Potential award range: $250K - $750K (10-30% of $2.5M)
```

**IMPORTANT**: The enforcement routing engine flags whistleblower relevance but does NOT expose award calculations. This prevents gaming the system. Award estimates are for internal forensic analysis only.

#### Submission Process

1. **File Form TCR**: Submit via SEC's online portal or mail
2. **Provide Information**: Detailed description of violations
3. **Evidence Package**: Supporting documentation
4. **Anonymous Option**: Can file anonymously through attorney
5. **Wait for Action**: SEC investigates and brings enforcement action
6. **Claim Award**: File Form WB-APP within 90 days of Notice of Covered Action

---

## Penalty Estimation

### Methodology

Penalty estimates are **conservative** and based on:
1. Statutory penalty maximums (2024 inflation-adjusted)
2. Historical enforcement patterns
3. Violation count multipliers (up to 10x)
4. Damage magnitude multipliers (up to 2x for high damages)

### Penalty Ranges by Violation Type

#### Insider Trading
- **Civil**: $100K - $10M
- **Criminal**: Up to 20 years imprisonment
- **Basis**: 17 CFR § 240.10b-5, 15 USC § 78j(b)

#### Securities Fraud
- **Civil**: $500K - $50M
- **Criminal**: Up to 25 years imprisonment
- **Basis**: 18 USC § 1348, 15 USC § 78j(b)

#### Late Filing Violations
- **Civil**: $10K - $100K per violation
- **Criminal**: None (civil only)
- **Basis**: 17 CFR § 240.16a-3

#### SOX Violations
- **Civil**: $500K - $5M
- **Criminal**: Up to 20 years imprisonment + $5M fine
- **Basis**: SOX § 302, SOX § 906

#### Tax Violations (IRC § 83)
- **Civil**: Back taxes + penalties (20-75% of underpayment)
- **Criminal**: Up to 5 years imprisonment
- **Basis**: 26 USC § 83

### Calculation Example

```python
from src.enforcement.routing_engine import EnforcementRoutingEngine

engine = EnforcementRoutingEngine()

# Example: Calculate penalty for securities fraud
penalty = engine.calculate_penalty_estimate(
    violation_type='securities_fraud',
    violation_count=3,  # 3 violations
    estimated_damages=5000000  # $5M damages
)

print(f"Min Penalty: ${penalty.min_penalty:,.2f}")
print(f"Max Penalty: ${penalty.max_penalty:,.2f}")
print(f"Penalty Type: {penalty.penalty_type}")
print(f"Legal Basis: {penalty.basis}")

# Output:
# Min Penalty: $1,500,000.00  (3x base civil minimum)
# Max Penalty: $150,000,000.00  (3x base × 2x damage multiplier)
# Penalty Type: both
# Legal Basis: 18 USC § 1348, 15 USC § 78j(b)
```

---

## Integration Guide

### Basic Usage

```python
from src.enforcement.routing_engine import EnforcementRoutingEngine

# Initialize engine
engine = EnforcementRoutingEngine()

# Violations from recursive analysis
violations = [
    {
        'violation_id': 'V001',
        'violation_type': 'insider_trading',
        'estimated_damages': 1500000,
        'scienter_evidence': True,
        'severity': 'HIGH'
    },
    {
        'violation_id': 'V002',
        'violation_type': 'late_filing',
        'estimated_damages': 0,
        'scienter_evidence': False,
        'severity': 'LOW'
    }
]

# Route violations to agencies
recommendations = engine.route_violations(
    violations=violations,
    statutory_bindings=None  # Optional statutory bindings
)

# Examine recommendations
for rec in recommendations:
    print(f"Agency: {rec.agency}")
    print(f"Case Type: {rec.case_type}")
    print(f"Priority: {rec.priority}")
    print(f"Trigger Met: {rec.trigger_threshold_met}")
    print(f"Whistleblower Relevant: {rec.whistleblower_relevant}")
    print(f"Actions: {rec.recommended_actions}")
```

### Integration with Statutory Bindings

```python
from src.enforcement.routing_engine import EnforcementRoutingEngine
from src.legal.statutory_binding_engine import StatutoryBindingEngine

# Initialize engines
routing_engine = EnforcementRoutingEngine()
binding_engine = StatutoryBindingEngine()

# Violations
violations = [...]

# Bind violations to statutes
statutory_bindings = binding_engine.bind_all_violations(violations)

# Route with statutory context
recommendations = routing_engine.route_violations(
    violations=violations,
    statutory_bindings=[b.to_dict() for b in statutory_bindings]
)

# Statutory references are now included
for rec in recommendations:
    print(f"Statutory References: {rec.statutory_references}")
```

### Generate Routing Report

```python
from src.enforcement.routing_engine import EnforcementRoutingEngine

engine = EnforcementRoutingEngine()

# Route violations
recommendations = engine.route_violations(violations, None)

# Generate comprehensive report
report = engine.generate_routing_report(recommendations)

print(f"Total Recommendations: {report['total_recommendations']}")
print(f"Agencies: {report['agencies']}")
print(f"Trigger Thresholds Met: {report['trigger_thresholds_met']}")
print(f"Whistleblower Relevant: {report['whistleblower_relevant']}")
print(f"Estimated Sanctions: ${report['estimated_sanctions_range']['min']:,.2f} - ${report['estimated_sanctions_range']['max']:,.2f}")
print(f"Summary: {report['summary']}")
```

### Integration with Prosecutorial Dossier

```python
from src.enforcement.routing_engine import EnforcementRoutingEngine
from src.reporting.prosecutorial_dossier_generator import ProsecutorialDossierGenerator

# Route violations
routing_engine = EnforcementRoutingEngine()
recommendations = routing_engine.route_violations(violations, bindings)
routing_report = routing_engine.generate_routing_report(recommendations)

# Include in dossier
dossier_generator = ProsecutorialDossierGenerator()
dossier = dossier_generator.generate_dossier(
    violations=violations,
    statutory_bindings=bindings,
    enforcement_routing=routing_report  # Include routing report
)
```

---

## API Reference

### EnforcementRoutingEngine

#### `__init__()`
Initialize the enforcement routing engine.

#### `route_violations(violations, statutory_bindings=None) -> List[EnforcementRecommendation]`
Route violations to appropriate enforcement agencies.

**Parameters**:
- `violations` (List[Dict]): List of detected violations
- `statutory_bindings` (Optional[List[Dict]]): Statutory binding information

**Returns**: List of `EnforcementRecommendation` objects

#### `assess_sec_trigger(violations, violation_type) -> bool`
Assess whether SEC investigation trigger threshold is met.

**Parameters**:
- `violations` (List[Dict]): List of violations of a specific type
- `violation_type` (str): Type of violation

**Returns**: `True` if trigger threshold met, `False` otherwise

#### `assess_whistleblower_relevance(estimated_sanctions, violation_types) -> bool`
Assess whistleblower program relevance per Dodd-Frank §922.

**Parameters**:
- `estimated_sanctions` (float): Total estimated monetary sanctions
- `violation_types` (List[str]): List of violation types or agencies

**Returns**: `True` if case meets whistleblower program thresholds

#### `calculate_penalty_estimate(violation_type, violation_count, estimated_damages) -> PenaltyRange`
Calculate estimated penalty range.

**Parameters**:
- `violation_type` (str): Type of violation
- `violation_count` (int): Number of violations
- `estimated_damages` (float): Estimated monetary damages

**Returns**: `PenaltyRange` object with min/max estimates

#### `generate_routing_report(recommendations) -> Dict[str, Any]`
Generate comprehensive routing report.

**Parameters**:
- `recommendations` (List[EnforcementRecommendation]): List of enforcement recommendations

**Returns**: Dictionary containing routing report

### EnforcementRecommendation

**Attributes**:
- `agency` (str): Enforcement agency (SEC, DOJ, IRS, CFTC, FinCEN)
- `case_type` (str): Case type (civil, criminal)
- `priority` (str): Priority level (CRITICAL, HIGH, MEDIUM, LOW)
- `trigger_threshold_met` (bool): SEC trigger threshold status
- `justification` (str): Routing justification
- `estimated_penalties` (Optional[PenaltyRange]): Penalty estimates
- `whistleblower_relevant` (bool): Whistleblower program relevance flag
- `violation_ids` (List[str]): Associated violation IDs
- `statutory_references` (List[str]): Applicable statutory references
- `recommended_actions` (List[str]): Recommended enforcement actions

**Methods**:
- `to_dict() -> Dict[str, Any]`: Convert to dictionary for serialization

### PenaltyRange

**Attributes**:
- `min_penalty` (float): Minimum penalty estimate
- `max_penalty` (float): Maximum penalty estimate
- `penalty_type` (str): Penalty type (civil, criminal, both)
- `basis` (str): Legal basis for calculation

**Methods**:
- `to_dict() -> Dict[str, Any]`: Convert to dictionary for serialization

---

## Best Practices

### 1. Always Use with Statutory Bindings
Integrate with `StatutoryBindingEngine` for complete statutory context.

### 2. Include in Forensic Dossiers
Enforcement routing should be a standard section in all prosecutorial dossiers.

### 3. Don't Expose Whistleblower Calculations
The engine flags whistleblower relevance but does not expose award calculations. Keep internal.

### 4. Document Evidence Chain
All routing recommendations should be supported by FRE 902(13)/(14) compliant evidence.

### 5. Coordinate Multi-Agency Actions
When routing to multiple agencies, coordinate submission timelines and evidence sharing.

### 6. Monitor Trigger Thresholds
Regularly review trigger threshold assessments to prioritize enforcement actions.

### 7. Update Penalty Ranges Annually
Statutory penalty amounts are adjusted for inflation. Update `PENALTY_RANGES` annually.

---

## References

### Legal Authorities
- **Dodd-Frank Act § 922**: 15 USC § 78u-6 (Whistleblower Program)
- **Securities Exchange Act**: 15 USC § 78 et seq.
- **SEC Regulations**: 17 CFR § 240
- **Securities Fraud**: 18 USC § 1348
- **IRC § 83**: 26 USC § 83

### SEC Resources
- [SEC Whistleblower Program](https://www.sec.gov/whistleblower)
- [TCR System](https://www.sec.gov/tcr)
- [Division of Enforcement](https://www.sec.gov/enforcement)

### DOJ Resources
- [DOJ Fraud Section](https://www.justice.gov/criminal-fraud)
- [DOJ Tax Division](https://www.justice.gov/tax)

### IRS Resources
- [IRS Form 3949-A](https://www.irs.gov/pub/irs-pdf/f3949a.pdf)
- [IRS Criminal Investigation](https://www.irs.gov/compliance/criminal-investigation)

---

## Support

For questions or issues:
- File GitHub issue: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- Review codebase: `/src/enforcement/routing_engine.py`
- Run tests: `pytest tests/enforcement/test_routing_engine.py -v`

---

**Last Updated**: 2025-12-31  
**Version**: Phase 5 Implementation  
**Status**: Production Ready
