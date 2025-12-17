"""
DOJ-Level Reporting Constants
=============================

Standardized statutory references, violation types, severity tiers,
and penalty calculations for DOJ-grade forensic reporting.

This module provides the legal and regulatory framework references
used throughout the JLAW reporting system to ensure consistency
and accuracy in prosecution-ready documentation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


# =============================================================================
# SEVERITY TIERS
# =============================================================================

class SeverityTier(str, Enum):
    """
    Violation severity classification with prosecutorial implications.
    
    Each tier corresponds to specific enforcement thresholds and
    determines regulatory routing recommendations.
    """
    CRITICAL = "CRITICAL"  # Immediate DOJ referral, criminal exposure
    HIGH = "HIGH"          # SEC enforcement priority, significant penalties
    MEDIUM = "MEDIUM"      # Standard enforcement, civil penalties
    LOW = "LOW"            # Monitoring, potential warning letter


# =============================================================================
# VIOLATION TYPES
# =============================================================================

class ViolationType(str, Enum):
    """
    Comprehensive enumeration of SEC violation types.
    
    Categories:
    - Insider Trading & Section 16
    - Disclosure & Reporting
    - Fraud & Material Misstatement
    - Corporate Governance
    - Tax & Compensation
    """
    # Section 16 / Form 4 Violations
    LATE_FORM4 = "LATE_FORM4"
    SHORT_SWING_PROFIT = "SHORT_SWING_PROFIT"
    BENEFICIAL_OWNERSHIP_FAILURE = "BENEFICIAL_OWNERSHIP_FAILURE"
    ZERO_DOLLAR_TRANSACTION = "ZERO_DOLLAR_TRANSACTION"
    GIFT_PATTERN_ABUSE = "GIFT_PATTERN_ABUSE"
    
    # Schedule 13D/13G Violations
    LATE_13D = "LATE_13D"
    LATE_13G = "LATE_13G"
    PASSIVE_TO_ACTIVIST_SHIFT = "PASSIVE_TO_ACTIVIST_SHIFT"
    WOLF_PACK_COORDINATION = "WOLF_PACK_COORDINATION"
    
    # 8-K Material Event Violations
    LATE_8K = "LATE_8K"
    MATERIAL_OMISSION = "MATERIAL_OMISSION"
    PRE_ANNOUNCEMENT_TRADING = "PRE_ANNOUNCEMENT_TRADING"
    
    # 10-K/10-Q Violations
    SOX_302_CERTIFICATION_FAILURE = "SOX_302_CERTIFICATION_FAILURE"
    SOX_404_INTERNAL_CONTROL_WEAKNESS = "SOX_404_INTERNAL_CONTROL_WEAKNESS"
    RESTATEMENT_REQUIRED = "RESTATEMENT_REQUIRED"
    REVENUE_MANIPULATION = "REVENUE_MANIPULATION"
    TEMPORAL_INCONSISTENCY = "TEMPORAL_INCONSISTENCY"
    
    # Fraud Indicators
    BENEISH_MSCORE_ALERT = "BENEISH_MSCORE_ALERT"
    BENFORD_LAW_VIOLATION = "BENFORD_LAW_VIOLATION"
    FINANCIAL_STATEMENT_FRAUD = "FINANCIAL_STATEMENT_FRAUD"
    CHANNEL_STUFFING = "CHANNEL_STUFFING"
    ROUND_TRIPPING = "ROUND_TRIPPING"
    
    # DEF 14A / Compensation
    EXCESSIVE_COMPENSATION = "EXCESSIVE_COMPENSATION"
    SAY_ON_PAY_FAILURE = "SAY_ON_PAY_FAILURE"
    GOLDEN_PARACHUTE_ABUSE = "GOLDEN_PARACHUTE_ABUSE"
    RELATED_PARTY_TRANSACTION = "RELATED_PARTY_TRANSACTION"
    
    # Rule 144 Violations
    HOLDING_PERIOD_VIOLATION = "HOLDING_PERIOD_VIOLATION"
    VOLUME_LIMIT_EXCEEDED = "VOLUME_LIMIT_EXCEEDED"
    TACKING_VIOLATION = "TACKING_VIOLATION"
    
    # Tax Violations (IRC §83)
    IRC_83B_ELECTION_FAILURE = "IRC_83B_ELECTION_FAILURE"
    DEFERRED_COMPENSATION_VIOLATION = "DEFERRED_COMPENSATION_VIOLATION"
    BACKDATING_DETECTION = "BACKDATING_DETECTION"
    
    # General
    DISCLOSURE_TIMING_MANIPULATION = "DISCLOSURE_TIMING_MANIPULATION"
    HEDGING_LANGUAGE_ABUSE = "HEDGING_LANGUAGE_ABUSE"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    REG_FD_VIOLATION = "REG_FD_VIOLATION"


# =============================================================================
# STATUTORY REFERENCES
# =============================================================================

@dataclass
class StatutoryInfo:
    """Complete statutory reference information."""
    citation: str
    title: str
    summary: str
    violation_types: List[ViolationType]
    default_severity: SeverityTier
    civil_penalty_min: float
    civil_penalty_max: float
    criminal_exposure: bool
    prison_years_max: int
    govinfo_collection: str  # GovInfo API collection identifier


# Primary SEC Statutes
SEC_STATUTES: Dict[str, StatutoryInfo] = {
    # Section 16(a) - Insider Reporting
    "15_USC_78p_a": StatutoryInfo(
        citation="15 U.S.C. § 78p(a)",
        title="Section 16(a) - Insider Reporting Requirements",
        summary="Directors, officers, and 10%+ beneficial owners must file Forms 3, 4, and 5 within 2 business days of transactions.",
        violation_types=[ViolationType.LATE_FORM4, ViolationType.BENEFICIAL_OWNERSHIP_FAILURE],
        default_severity=SeverityTier.HIGH,
        civil_penalty_min=5000.0,
        civil_penalty_max=25000.0,
        criminal_exposure=False,
        prison_years_max=0,
        govinfo_collection="uscode"
    ),
    
    # Section 16(b) - Short-Swing Profits
    "15_USC_78p_b": StatutoryInfo(
        citation="15 U.S.C. § 78p(b)",
        title="Section 16(b) - Short-Swing Profit Recovery",
        summary="Profits from buy-sell or sell-buy transactions within 6 months by insiders are recoverable by the issuer.",
        violation_types=[ViolationType.SHORT_SWING_PROFIT],
        default_severity=SeverityTier.HIGH,
        civil_penalty_min=0.0,  # Disgorgement of profits
        civil_penalty_max=0.0,  # Varies by profit amount
        criminal_exposure=False,
        prison_years_max=0,
        govinfo_collection="uscode"
    ),
    
    # Section 10(b) - Securities Fraud
    "15_USC_78j_b": StatutoryInfo(
        citation="15 U.S.C. § 78j(b)",
        title="Section 10(b) - Securities Fraud",
        summary="Prohibits manipulative and deceptive practices in securities transactions.",
        violation_types=[
            ViolationType.FINANCIAL_STATEMENT_FRAUD,
            ViolationType.MATERIAL_OMISSION,
            ViolationType.CHANNEL_STUFFING,
            ViolationType.ROUND_TRIPPING
        ],
        default_severity=SeverityTier.CRITICAL,
        civil_penalty_min=100000.0,
        civil_penalty_max=5000000.0,
        criminal_exposure=True,
        prison_years_max=20,
        govinfo_collection="uscode"
    ),
    
    # Section 13(d) - Beneficial Ownership
    "15_USC_78m_d": StatutoryInfo(
        citation="15 U.S.C. § 78m(d)",
        title="Section 13(d) - Beneficial Ownership Reporting",
        summary="5%+ beneficial owners must file Schedule 13D within 10 days of crossing threshold.",
        violation_types=[
            ViolationType.LATE_13D,
            ViolationType.WOLF_PACK_COORDINATION,
            ViolationType.PASSIVE_TO_ACTIVIST_SHIFT
        ],
        default_severity=SeverityTier.HIGH,
        civil_penalty_min=50000.0,
        civil_penalty_max=500000.0,
        criminal_exposure=False,
        prison_years_max=0,
        govinfo_collection="uscode"
    ),
    
    # SOX Section 302 - Officer Certification
    "15_USC_7241": StatutoryInfo(
        citation="15 U.S.C. § 7241",
        title="SOX Section 302 - Corporate Responsibility for Financial Reports",
        summary="CEO and CFO must certify accuracy of financial statements and disclosure controls.",
        violation_types=[ViolationType.SOX_302_CERTIFICATION_FAILURE],
        default_severity=SeverityTier.CRITICAL,
        civil_penalty_min=100000.0,
        civil_penalty_max=1000000.0,
        criminal_exposure=True,
        prison_years_max=20,
        govinfo_collection="uscode"
    ),
    
    # SOX Section 404 - Internal Controls
    "15_USC_7262": StatutoryInfo(
        citation="15 U.S.C. § 7262",
        title="SOX Section 404 - Internal Control Assessment",
        summary="Management must assess and report on internal control over financial reporting.",
        violation_types=[ViolationType.SOX_404_INTERNAL_CONTROL_WEAKNESS],
        default_severity=SeverityTier.HIGH,
        civil_penalty_min=50000.0,
        civil_penalty_max=500000.0,
        criminal_exposure=False,
        prison_years_max=0,
        govinfo_collection="uscode"
    ),
    
    # Regulation FD - Fair Disclosure
    "17_CFR_243": StatutoryInfo(
        citation="17 C.F.R. § 243.100",
        title="Regulation FD - Selective Disclosure",
        summary="Prohibits selective disclosure of material nonpublic information.",
        violation_types=[ViolationType.REG_FD_VIOLATION],
        default_severity=SeverityTier.HIGH,
        civil_penalty_min=50000.0,
        civil_penalty_max=500000.0,
        criminal_exposure=False,
        prison_years_max=0,
        govinfo_collection="cfr"
    ),
    
    # IRC Section 83 - Property Transfers
    "26_USC_83": StatutoryInfo(
        citation="26 U.S.C. § 83",
        title="IRC Section 83 - Property Transferred in Connection with Services",
        summary="Governs taxation of property (including stock) transferred for services.",
        violation_types=[
            ViolationType.IRC_83B_ELECTION_FAILURE,
            ViolationType.DEFERRED_COMPENSATION_VIOLATION,
            ViolationType.BACKDATING_DETECTION
        ],
        default_severity=SeverityTier.HIGH,
        civil_penalty_min=25000.0,
        civil_penalty_max=250000.0,
        criminal_exposure=True,
        prison_years_max=5,
        govinfo_collection="uscode"
    ),
    
    # Rule 144 - Restricted Securities
    "17_CFR_230_144": StatutoryInfo(
        citation="17 C.F.R. § 230.144",
        title="Rule 144 - Sale of Restricted and Control Securities",
        summary="Conditions for public sale of restricted and control securities.",
        violation_types=[
            ViolationType.HOLDING_PERIOD_VIOLATION,
            ViolationType.VOLUME_LIMIT_EXCEEDED,
            ViolationType.TACKING_VIOLATION
        ],
        default_severity=SeverityTier.MEDIUM,
        civil_penalty_min=10000.0,
        civil_penalty_max=100000.0,
        criminal_exposure=False,
        prison_years_max=0,
        govinfo_collection="cfr"
    ),
    
    # Securities Fraud (Criminal)
    "18_USC_1348": StatutoryInfo(
        citation="18 U.S.C. § 1348",
        title="Securities Fraud (Criminal)",
        summary="Criminal securities fraud - defrauding investors or obtaining money through false pretenses.",
        violation_types=[
            ViolationType.FINANCIAL_STATEMENT_FRAUD,
            ViolationType.MATERIAL_OMISSION
        ],
        default_severity=SeverityTier.CRITICAL,
        civil_penalty_min=0.0,
        civil_penalty_max=5000000.0,
        criminal_exposure=True,
        prison_years_max=25,
        govinfo_collection="uscode"
    ),
}


# =============================================================================
# VIOLATION TYPE TO STATUTE MAPPING
# =============================================================================

VIOLATION_STATUTE_MAP: Dict[ViolationType, List[str]] = {
    ViolationType.LATE_FORM4: ["15_USC_78p_a"],
    ViolationType.SHORT_SWING_PROFIT: ["15_USC_78p_b"],
    ViolationType.BENEFICIAL_OWNERSHIP_FAILURE: ["15_USC_78p_a"],
    ViolationType.ZERO_DOLLAR_TRANSACTION: ["15_USC_78p_a", "26_USC_83"],
    ViolationType.GIFT_PATTERN_ABUSE: ["15_USC_78p_a", "26_USC_83"],
    
    ViolationType.LATE_13D: ["15_USC_78m_d"],
    ViolationType.LATE_13G: ["15_USC_78m_d"],
    ViolationType.PASSIVE_TO_ACTIVIST_SHIFT: ["15_USC_78m_d"],
    ViolationType.WOLF_PACK_COORDINATION: ["15_USC_78m_d", "15_USC_78j_b"],
    
    ViolationType.LATE_8K: ["15_USC_78m_d"],
    ViolationType.MATERIAL_OMISSION: ["15_USC_78j_b", "18_USC_1348"],
    ViolationType.PRE_ANNOUNCEMENT_TRADING: ["15_USC_78j_b"],
    
    ViolationType.SOX_302_CERTIFICATION_FAILURE: ["15_USC_7241"],
    ViolationType.SOX_404_INTERNAL_CONTROL_WEAKNESS: ["15_USC_7262"],
    ViolationType.RESTATEMENT_REQUIRED: ["15_USC_78j_b", "15_USC_7241"],
    ViolationType.REVENUE_MANIPULATION: ["15_USC_78j_b", "18_USC_1348"],
    ViolationType.TEMPORAL_INCONSISTENCY: ["15_USC_78j_b"],
    
    ViolationType.BENEISH_MSCORE_ALERT: ["15_USC_78j_b"],
    ViolationType.BENFORD_LAW_VIOLATION: ["15_USC_78j_b"],
    ViolationType.FINANCIAL_STATEMENT_FRAUD: ["15_USC_78j_b", "18_USC_1348"],
    ViolationType.CHANNEL_STUFFING: ["15_USC_78j_b"],
    ViolationType.ROUND_TRIPPING: ["15_USC_78j_b"],
    
    ViolationType.EXCESSIVE_COMPENSATION: ["17_CFR_243"],
    ViolationType.SAY_ON_PAY_FAILURE: ["17_CFR_243"],
    ViolationType.GOLDEN_PARACHUTE_ABUSE: ["17_CFR_243"],
    ViolationType.RELATED_PARTY_TRANSACTION: ["15_USC_78j_b"],
    
    ViolationType.HOLDING_PERIOD_VIOLATION: ["17_CFR_230_144"],
    ViolationType.VOLUME_LIMIT_EXCEEDED: ["17_CFR_230_144"],
    ViolationType.TACKING_VIOLATION: ["17_CFR_230_144"],
    
    ViolationType.IRC_83B_ELECTION_FAILURE: ["26_USC_83"],
    ViolationType.DEFERRED_COMPENSATION_VIOLATION: ["26_USC_83"],
    ViolationType.BACKDATING_DETECTION: ["26_USC_83", "15_USC_78j_b"],
    
    ViolationType.DISCLOSURE_TIMING_MANIPULATION: ["15_USC_78j_b"],
    ViolationType.HEDGING_LANGUAGE_ABUSE: ["15_USC_78j_b"],
    ViolationType.CONTRADICTION_DETECTED: ["15_USC_78j_b"],
    ViolationType.REG_FD_VIOLATION: ["17_CFR_243"],
}


# =============================================================================
# PENALTY CALCULATION MULTIPLIERS
# =============================================================================

SEVERITY_PENALTY_MULTIPLIERS: Dict[SeverityTier, Dict[str, float]] = {
    SeverityTier.CRITICAL: {
        "civil_min_multiplier": 5.0,
        "civil_max_multiplier": 10.0,
        "disgorgement_multiplier": 3.0,
        "prejudgment_interest_rate": 0.05,
    },
    SeverityTier.HIGH: {
        "civil_min_multiplier": 2.0,
        "civil_max_multiplier": 5.0,
        "disgorgement_multiplier": 2.0,
        "prejudgment_interest_rate": 0.04,
    },
    SeverityTier.MEDIUM: {
        "civil_min_multiplier": 1.0,
        "civil_max_multiplier": 2.0,
        "disgorgement_multiplier": 1.5,
        "prejudgment_interest_rate": 0.03,
    },
    SeverityTier.LOW: {
        "civil_min_multiplier": 0.5,
        "civil_max_multiplier": 1.0,
        "disgorgement_multiplier": 1.0,
        "prejudgment_interest_rate": 0.02,
    },
}


# =============================================================================
# REGULATORY ROUTING THRESHOLDS
# =============================================================================

@dataclass
class RegulatoryRoutingConfig:
    """Configuration for regulatory agency routing."""
    agency: str
    full_name: str
    violation_threshold: int
    severity_threshold: SeverityTier
    criminal_threshold: bool


REGULATORY_ROUTING: Dict[str, RegulatoryRoutingConfig] = {
    "SEC": RegulatoryRoutingConfig(
        agency="SEC",
        full_name="Securities and Exchange Commission",
        violation_threshold=1,
        severity_threshold=SeverityTier.LOW,
        criminal_threshold=False
    ),
    "DOJ": RegulatoryRoutingConfig(
        agency="DOJ",
        full_name="Department of Justice",
        violation_threshold=3,
        severity_threshold=SeverityTier.CRITICAL,
        criminal_threshold=True
    ),
    "IRS": RegulatoryRoutingConfig(
        agency="IRS",
        full_name="Internal Revenue Service",
        violation_threshold=1,
        severity_threshold=SeverityTier.MEDIUM,
        criminal_threshold=False
    ),
}


# =============================================================================
# PROSECUTORIAL MERIT SCORING
# =============================================================================

@dataclass
class ProsecutorialMeritCriteria:
    """Criteria for assessing prosecutorial merit."""
    weight: float
    description: str


PROSECUTORIAL_MERIT_FACTORS: Dict[str, ProsecutorialMeritCriteria] = {
    "evidence_strength": ProsecutorialMeritCriteria(
        weight=0.25,
        description="Quality and completeness of documentary evidence"
    ),
    "dual_agent_consensus": ProsecutorialMeritCriteria(
        weight=0.20,
        description="Agreement between OpenAI and Anthropic analysis agents"
    ),
    "statutory_clarity": ProsecutorialMeritCriteria(
        weight=0.15,
        description="Clear mapping to specific statutory violations"
    ),
    "damage_quantification": ProsecutorialMeritCriteria(
        weight=0.15,
        description="Ability to quantify financial damages"
    ),
    "pattern_consistency": ProsecutorialMeritCriteria(
        weight=0.15,
        description="Consistency across multiple detection patterns"
    ),
    "chain_of_custody": ProsecutorialMeritCriteria(
        weight=0.10,
        description="Integrity of evidence chain with cryptographic verification"
    ),
}


# =============================================================================
# NIKE 2019 BASELINE REFERENCE
# =============================================================================

NIKE_2019_BASELINE = {
    "company": "NIKE, Inc.",
    "cik": "320187",
    "analysis_year": 2019,
    "reference_standard": True,
    "expected_sections": [
        "Executive Summary",
        "Target Information",
        "Per-Filing Analysis",
        "Violation Details with Statutory Citations",
        "Dual-Agent Consensus",
        "Evidence Chain",
        "Financial Impact Assessment",
        "Regulatory Routing Recommendations",
    ],
    "minimum_quality_metrics": {
        "exact_quotes_per_violation": 1,
        "statutory_citations_per_violation": 1,
        "chain_of_custody_records": True,
        "dual_agent_validation": True,
        "damage_estimation": True,
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_statute_for_violation(violation_type: ViolationType) -> Optional[StatutoryInfo]:
    """
    Get primary statutory reference for a violation type.
    
    Args:
        violation_type: The violation type enum
        
    Returns:
        StatutoryInfo for the primary applicable statute, or None
    """
    statute_keys = VIOLATION_STATUTE_MAP.get(violation_type, [])
    if statute_keys:
        return SEC_STATUTES.get(statute_keys[0])
    return None


def get_all_statutes_for_violation(violation_type: ViolationType) -> List[StatutoryInfo]:
    """
    Get all applicable statutory references for a violation type.
    
    Args:
        violation_type: The violation type enum
        
    Returns:
        List of StatutoryInfo for all applicable statutes
    """
    statute_keys = VIOLATION_STATUTE_MAP.get(violation_type, [])
    return [SEC_STATUTES[key] for key in statute_keys if key in SEC_STATUTES]


def calculate_penalty_range(
    violation_type: ViolationType,
    severity: SeverityTier,
    profit_amount: float = 0.0
) -> Tuple[float, float]:
    """
    Calculate estimated penalty range for a violation.
    
    Args:
        violation_type: Type of violation
        severity: Severity tier
        profit_amount: Ill-gotten gains amount (for disgorgement)
        
    Returns:
        Tuple of (minimum, maximum) penalty estimates
    """
    statute = get_statute_for_violation(violation_type)
    if not statute:
        return (0.0, 0.0)
    
    multipliers = SEVERITY_PENALTY_MULTIPLIERS.get(severity, {})
    min_mult = multipliers.get("civil_min_multiplier", 1.0)
    max_mult = multipliers.get("civil_max_multiplier", 1.0)
    disg_mult = multipliers.get("disgorgement_multiplier", 1.0)
    
    base_min = statute.civil_penalty_min * min_mult
    base_max = statute.civil_penalty_max * max_mult
    disgorgement = profit_amount * disg_mult
    
    return (base_min + disgorgement, base_max + disgorgement)


def determine_regulatory_routing(
    violations: List[Tuple[ViolationType, SeverityTier]]
) -> Dict[str, bool]:
    """
    Determine which regulatory agencies should receive referrals.
    
    Args:
        violations: List of (violation_type, severity) tuples
        
    Returns:
        Dict mapping agency names to referral recommendations
    """
    routing = {"SEC": False, "DOJ": False, "IRS": False}
    
    # Count by severity
    critical_count = sum(1 for _, s in violations if s == SeverityTier.CRITICAL)
    high_count = sum(1 for _, s in violations if s == SeverityTier.HIGH)
    total_count = len(violations)
    
    # Check for criminal exposure
    has_criminal = any(
        get_statute_for_violation(v).criminal_exposure
        for v, _ in violations
        if get_statute_for_violation(v)
    )
    
    # Check for IRS-related violations
    irs_violations = [ViolationType.IRC_83B_ELECTION_FAILURE,
                      ViolationType.DEFERRED_COMPENSATION_VIOLATION,
                      ViolationType.BACKDATING_DETECTION]
    has_irs = any(v in irs_violations for v, _ in violations)
    
    # Apply routing rules
    if total_count >= 1:
        routing["SEC"] = True
    
    if critical_count >= 1 or has_criminal:
        routing["DOJ"] = True
    
    if has_irs:
        routing["IRS"] = True
    
    return routing
