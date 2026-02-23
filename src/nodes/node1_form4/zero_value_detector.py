"""
Zero Value Transaction Analyzer - ENHANCED FORENSIC MODULE
============================================================

CORE PURPOSE MODULE: Every $0 transaction receives FULL forensic investigation
regardless of transaction code. No early exits. No automatic legitimacy stamps.

CRITICAL DESIGN PRINCIPLE:
    The previous system immediately classified Gift (G), Award (A/I), Tax (F),
    and Vesting (V) codes as "LEGITIMATE" with risk_score=0.0 and exited.
    This is EXACTLY how the system was exploited. A $0 transaction filed under
    any "expected" code bypassed ALL forensic analysis.

    THIS VERSION: Every $0 transaction, regardless of code, undergoes:
    1. Financial benefit extraction (shares x market price = implied value)
    2. Material event proximity analysis (all 33 8-K item types)
    3. Filing party recidivism profiling (repeat $0 patterns)
    4. Disclosure contradiction detection (Form 4 vs DEF 14A vs 10-K)
    5. Temporal cluster analysis (multi-insider same-window detection)
    6. Late filing suspicion weighting
    7. Footnote obfuscation scoring
    8. Indirect ownership entity complexity scoring

Detection vectors:
- transactionPricePerShare == 0 regardless of transaction code
- High-value securities transferred at zero reported consideration
- Temporal clustering of $0 transactions near material events
- Cross-reference with DEF 14A compensation disclosures
- Repeat $0 filer pattern detection across issuers
- Code rotation detection (same insider cycling G->A->V->M)
- Multi-insider same-window $0 clustering

Statutory framework:
- 15 USC section 78j(b) / Rule 10b-5: Insider trading, gift timing manipulation
- 17 CFR section 229.402: Undisclosed compensation (Regulation S-K Item 402)
- 17 CFR section 229.404: Related party transactions (Regulation S-K Item 404)
- 15 USC section 78p(a): Section 16(a) late filing violations
- 15 USC section 78p(b): Section 16(b) short-swing profit recovery
- 26 USC section 83: IRC compensation taxation
- 17 CFR section 240.10b5-1: Trading plan defense scrutiny
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict
import logging
import math

logger = logging.getLogger(__name__)


class ZeroValuePattern(Enum):
    """Classification of $0 transaction patterns - ENHANCED."""
    ZERO_PRICE_NON_GIFT = "zero_price_non_gift"
    DERIVATIVE_EXERCISE_ADVANTAGE = "derivative_exercise_advantage"
    UNDISCLOSED_COMPENSATION = "undisclosed_compensation"
    RELATED_PARTY_TRANSFER = "related_party_transfer"
    TIMING_ANOMALY = "timing_anomaly"
    GIFT_REQUIRING_SCRUTINY = "gift_requiring_scrutiny"
    AWARD_REQUIRING_SCRUTINY = "award_requiring_scrutiny"
    TAX_REQUIRING_SCRUTINY = "tax_requiring_scrutiny"
    VESTING_REQUIRING_SCRUTINY = "vesting_requiring_scrutiny"
    CODE_ROTATION_DETECTED = "code_rotation_detected"
    MULTI_INSIDER_CLUSTER = "multi_insider_cluster"
    DISCLOSURE_CONTRADICTION = "disclosure_contradiction"
    LATE_FILED_ZERO_DOLLAR = "late_filed_zero_dollar"
    FOOTNOTE_OBFUSCATION = "footnote_obfuscation"
    BENEFICIAL_OWNERSHIP_TRANSFER = "beneficial_ownership_transfer"
    RECIDIVIST_ZERO_FILER = "recidivist_zero_filer"
    HIGH_VALUE_ZERO_TRANSFER = "high_value_zero_transfer"


class ZeroValueSeverity(Enum):
    """Alert severity for zero-value transactions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ForensicFindings:
    """Detailed forensic findings for a single $0 transaction."""
    implied_market_value: float = 0.0
    market_price_at_transaction: float = 0.0
    days_to_nearest_material_event: Optional[int] = None
    nearest_event_type: Optional[str] = None
    nearest_event_direction: Optional[str] = None  # PRE_EVENT or POST_EVENT
    insider_zero_dollar_history_count: int = 0
    insider_zero_dollar_total_shares: float = 0.0
    insider_zero_dollar_total_implied_value: float = 0.0
    compensation_disclosed_in_proxy: bool = False
    proxy_compensation_amount: float = 0.0
    disclosure_gap: float = 0.0  # Form 4 implied value minus proxy disclosed
    is_late_filed: bool = False
    days_late: int = 0
    has_footnotes: bool = False
    footnote_vagueness_score: float = 0.0  # 0.0=clear, 1.0=maximally vague
    indirect_ownership: bool = False
    ownership_entity_type: Optional[str] = None  # Trust, LLC, Foundation, etc.
    entity_complexity_score: float = 0.0  # 0.0=direct, 1.0=maximally complex
    code_rotation_detected: bool = False
    codes_used_by_insider: List[str] = field(default_factory=list)
    cluster_insider_count: int = 0  # Other insiders with $0 in same window
    cluster_total_shares: float = 0.0
    multi_vector_escalation: bool = False
    escalation_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "implied_market_value": round(self.implied_market_value, 2),
            "market_price_at_transaction": round(self.market_price_at_transaction, 2),
            "days_to_nearest_material_event": self.days_to_nearest_material_event,
            "nearest_event_type": self.nearest_event_type,
            "nearest_event_direction": self.nearest_event_direction,
            "insider_zero_dollar_history": {
                "count": self.insider_zero_dollar_history_count,
                "total_shares": self.insider_zero_dollar_total_shares,
                "total_implied_value": round(self.insider_zero_dollar_total_implied_value, 2),
            },
            "disclosure_analysis": {
                "compensation_in_proxy": self.compensation_disclosed_in_proxy,
                "proxy_amount": round(self.proxy_compensation_amount, 2),
                "disclosure_gap": round(self.disclosure_gap, 2),
            },
            "filing_compliance": {
                "is_late_filed": self.is_late_filed,
                "days_late": self.days_late,
            },
            "footnote_analysis": {
                "has_footnotes": self.has_footnotes,
                "vagueness_score": round(self.footnote_vagueness_score, 3),
            },
            "ownership_structure": {
                "indirect": self.indirect_ownership,
                "entity_type": self.ownership_entity_type,
                "complexity_score": round(self.entity_complexity_score, 3),
            },
            "pattern_analysis": {
                "code_rotation_detected": self.code_rotation_detected,
                "codes_used": self.codes_used_by_insider,
                "cluster_insiders": self.cluster_insider_count,
                "cluster_total_shares": self.cluster_total_shares,
            },
            "escalation": {
                "multi_vector": self.multi_vector_escalation,
                "reasons": self.escalation_reasons,
            },
        }


@dataclass
class ZeroValueAlert:
    """Alert for a $0 transaction - ENHANCED with full forensic detail."""
    pattern: ZeroValuePattern
    severity: ZeroValueSeverity
    transaction_date: Optional[date]
    transaction_code: str
    shares: float
    security_title: str
    owner_name: str
    is_derivative: bool
    evidence_summary: str
    statutory_references: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    forensic_findings: Optional[ForensicFindings] = None
    # Enhanced fields
    implied_market_value: float = 0.0
    filing_party_role: str = ""
    officer_title: str = ""
    is_director: bool = False
    is_officer: bool = False
    is_ten_percent_owner: bool = False
    filing_date: Optional[date] = None
    accession_number: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "pattern": self.pattern.value,
            "severity": self.severity.value,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "transaction_code": self.transaction_code,
            "shares": self.shares,
            "security_title": self.security_title,
            "owner_name": self.owner_name,
            "is_derivative": self.is_derivative,
            "evidence_summary": self.evidence_summary,
            "statutory_references": self.statutory_references,
            "risk_score": round(self.risk_score, 3),
            "implied_market_value": round(self.implied_market_value, 2),
            "filing_party": {
                "name": self.owner_name,
                "role": self.filing_party_role,
                "officer_title": self.officer_title,
                "is_director": self.is_director,
                "is_officer": self.is_officer,
                "is_ten_percent_owner": self.is_ten_percent_owner,
            },
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "accession_number": self.accession_number,
        }
        if self.forensic_findings:
            result["forensic_findings"] = self.forensic_findings.to_dict()
        return result


@dataclass
class ZeroValueAnalysis:
    """Complete analysis of $0 transactions in a filing set - ENHANCED."""
    total_zero_value: int
    legitimate_count: int  # Kept for backward compat but always 0 in enhanced mode
    suspicious_count: int
    alerts: List[ZeroValueAlert]
    patterns_detected: Dict[str, int]
    aggregate_risk_score: float
    # Enhanced aggregate fields
    total_implied_market_value: float = 0.0
    unique_insiders_flagged: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    material_event_correlations: int = 0
    disclosure_contradictions: int = 0
    repeat_offender_count: int = 0
    multi_insider_clusters: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_zero_value": self.total_zero_value,
                "legitimate_count": self.legitimate_count,
                "suspicious_count": self.suspicious_count,
                "total_implied_market_value": round(self.total_implied_market_value, 2),
                "unique_insiders_flagged": self.unique_insiders_flagged,
                "severity_breakdown": {
                    "CRITICAL": self.critical_alerts,
                    "HIGH": self.high_alerts,
                },
                "material_event_correlations": self.material_event_correlations,
                "disclosure_contradictions": self.disclosure_contradictions,
                "repeat_offenders": self.repeat_offender_count,
                "multi_insider_clusters": self.multi_insider_clusters,
            },
            "patterns_detected": self.patterns_detected,
            "aggregate_risk_score": round(self.aggregate_risk_score, 3),
            "alerts": [a.to_dict() for a in self.alerts],
        }


# Transaction code sets - used for CLASSIFICATION, not for exemption
GIFT_CODES = {'G'}
AWARD_CODES = {'A', 'I'}
TAX_CODES = {'F'}
VESTING_CODES = {'V'}
DERIVATIVE_CODES = {'M', 'C', 'X', 'E', 'O', 'H'}
TRANSFER_CODES = {'J', 'L', 'W', 'Z', 'K', 'D'}
MARKET_CODES = {'P', 'S'}

# ALL known transaction codes
ALL_CODES = GIFT_CODES | AWARD_CODES | TAX_CODES | VESTING_CODES | DERIVATIVE_CODES | TRANSFER_CODES | MARKET_CODES

# Entity patterns suggesting indirect ownership structures
ENTITY_PATTERNS = {
    'trust': 0.6,
    'family trust': 0.7,
    'irrevocable trust': 0.8,
    'revocable trust': 0.5,
    'llc': 0.7,
    'holdings': 0.6,
    'foundation': 0.7,
    'partnership': 0.6,
    'lp': 0.6,
    'gp': 0.5,
    'charitable': 0.5,
    'family': 0.6,
    'spouse': 0.5,
    'children': 0.6,
    'custodian': 0.5,
    'estate': 0.4,
    'beneficiary': 0.6,
}

# Vague footnote indicators (footnotes that obscure rather than clarify)
VAGUE_FOOTNOTE_PATTERNS = [
    'pursuant to',
    'in connection with',
    'as described',
    'see above',
    'previously reported',
    'certain',
    'various',
    'from time to time',
    'may',
    'subject to',
]


class ZeroValueTransactionAnalyzer:
    """
    ENHANCED Zero Value Transaction Analyzer.

    CORE PRINCIPLE: NO TRANSACTION IS PRESUMED LEGITIMATE.

    Every $0 transaction undergoes full multi-vector forensic analysis:
    1. Financial benefit extraction (implied market value)
    2. Material event proximity (all 8-K item types)
    3. Filing party deep profiling (role, history, recidivism)
    4. Disclosure contradiction detection (Form 4 vs proxy)
    5. Temporal cluster analysis (multi-insider patterns)
    6. Late filing suspicion weighting
    7. Footnote obfuscation scoring
    8. Indirect ownership entity complexity
    9. Code rotation detection
    10. Multi-vector escalation logic
    """

    SUSPICIOUS_PATTERNS = [
        'zero_price_non_gift',
        'derivative_exercise_advantage',
        'undisclosed_compensation',
        'related_party_transfer',
        'timing_anomaly',
        'gift_requiring_scrutiny',
        'award_requiring_scrutiny',
        'tax_requiring_scrutiny',
        'vesting_requiring_scrutiny',
        'code_rotation_detected',
        'multi_insider_cluster',
        'disclosure_contradiction',
        'late_filed_zero_dollar',
        'footnote_obfuscation',
        'beneficial_ownership_transfer',
        'recidivist_zero_filer',
        'high_value_zero_transfer',
    ]

    # Temporal clustering window (days)
    CLUSTERING_WINDOW_DAYS = 30

    # Critical proximity threshold (days)
    CRITICAL_PROXIMITY_DAYS = 7

    # High proximity threshold (days)
    HIGH_PROXIMITY_DAYS = 14

    # Recidivist threshold (number of $0 transactions)
    RECIDIVIST_THRESHOLD = 3

    # High-value threshold for zero-dollar transfers
    HIGH_VALUE_THRESHOLD = 100000.0  # $100K implied market value

    # Code rotation minimum unique codes to flag
    CODE_ROTATION_MIN_CODES = 3

    def analyze(
        self,
        transactions: List[Dict[str, Any]],
        material_events: Optional[List[Dict[str, Any]]] = None,
        compensation_data: Optional[Dict[str, Any]] = None,
        market_prices: Optional[Dict[str, float]] = None,
        historical_zero_dollar: Optional[List[Dict[str, Any]]] = None,
        filing_metadata: Optional[Dict[str, Any]] = None,
    ) -> ZeroValueAnalysis:
        """
        Analyze ALL transactions for $0 value - FULL FORENSIC INVESTIGATION.

        CRITICAL: No early exits. Every $0 transaction is investigated regardless
        of transaction code.

        Args:
            transactions: List of Form 4 transaction dicts
            material_events: Material event dicts with event_date, event_type
            compensation_data: DEF 14A compensation data for cross-reference
            market_prices: Dict mapping security_title to market price at date
            historical_zero_dollar: Historical $0 transactions for recidivism
            filing_metadata: Filing-level metadata (filing_date, accession, etc.)

        Returns:
            ZeroValueAnalysis with FULL forensic detail on every $0 transaction
        """
        zero_value_txns = [
            t for t in transactions
            if self._is_zero_value(t)
        ]

        if not zero_value_txns:
            return ZeroValueAnalysis(
                total_zero_value=0,
                legitimate_count=0,
                suspicious_count=0,
                alerts=[],
                patterns_detected={},
                aggregate_risk_score=0.0,
            )

        # Build insider history index for recidivism detection
        insider_history = self._build_insider_history(
            zero_value_txns, historical_zero_dollar
        )

        # Build per-insider code usage for rotation detection
        code_usage = self._build_code_usage_index(
            zero_value_txns, historical_zero_dollar
        )

        # Detect multi-insider clusters
        clusters = self._detect_multi_insider_clusters(zero_value_txns)

        alerts: List[ZeroValueAlert] = []
        patterns: Dict[str, int] = {}
        total_implied_value = 0.0

        # EVERY $0 transaction gets full forensic workup
        for txn in zero_value_txns:
            # Phase 1: Base classification (no early exits)
            base_pattern, base_severity, base_evidence, base_statutes, base_risk = (
                self._classify_transaction_enhanced(
                    txn, material_events, compensation_data
                )
            )

            # Phase 2: Financial benefit extraction
            implied_value = self._extract_financial_benefit(txn, market_prices)
            total_implied_value += implied_value

            # Phase 3: Material event proximity
            event_proximity = self._analyze_event_proximity(txn, material_events)

            # Phase 4: Recidivism check
            owner_name = txn.get('owner_name', txn.get('reporting_owner_name', ''))
            recidivism = insider_history.get(owner_name, {})

            # Phase 5: Disclosure contradiction
            disclosure_gap = self._check_disclosure_contradiction(
                txn, compensation_data, implied_value
            )

            # Phase 6: Late filing check
            late_info = self._check_late_filing(txn, filing_metadata)

            # Phase 7: Footnote obfuscation
            footnote_score = self._score_footnote_obfuscation(txn)

            # Phase 8: Ownership entity complexity
            entity_info = self._analyze_ownership_entity(txn)

            # Phase 9: Code rotation
            rotation_info = self._check_code_rotation(owner_name, code_usage)

            # Phase 10: Multi-insider cluster membership
            cluster_info = self._get_cluster_membership(txn, clusters)

            # Phase 11: Build forensic findings
            findings = ForensicFindings(
                implied_market_value=implied_value,
                market_price_at_transaction=self._get_market_price(txn, market_prices),
                days_to_nearest_material_event=event_proximity.get('days', None),
                nearest_event_type=event_proximity.get('event_type', None),
                nearest_event_direction=event_proximity.get('direction', None),
                insider_zero_dollar_history_count=recidivism.get('count', 0),
                insider_zero_dollar_total_shares=recidivism.get('total_shares', 0),
                insider_zero_dollar_total_implied_value=recidivism.get('total_value', 0),
                compensation_disclosed_in_proxy=disclosure_gap.get('disclosed', False),
                proxy_compensation_amount=disclosure_gap.get('proxy_amount', 0),
                disclosure_gap=disclosure_gap.get('gap', 0),
                is_late_filed=late_info.get('is_late', False),
                days_late=late_info.get('days_late', 0),
                has_footnotes=bool(txn.get('footnotes')),
                footnote_vagueness_score=footnote_score,
                indirect_ownership=entity_info.get('indirect', False),
                ownership_entity_type=entity_info.get('entity_type', None),
                entity_complexity_score=entity_info.get('complexity', 0),
                code_rotation_detected=rotation_info.get('detected', False),
                codes_used_by_insider=rotation_info.get('codes', []),
                cluster_insider_count=cluster_info.get('count', 0),
                cluster_total_shares=cluster_info.get('total_shares', 0),
            )

            # Phase 12: Multi-vector severity escalation
            final_severity, final_risk, escalation_reasons = (
                self._multi_vector_escalation(
                    base_severity, base_risk, findings, event_proximity
                )
            )
            findings.multi_vector_escalation = len(escalation_reasons) > 0
            findings.escalation_reasons = escalation_reasons

            # Phase 13: Determine final pattern (may override base)
            final_pattern = self._determine_final_pattern(
                base_pattern, findings, txn
            )

            # Phase 14: Build comprehensive statutory references
            final_statutes = self._build_statutory_references(
                base_statutes, findings, final_pattern
            )

            # Phase 15: Build comprehensive evidence summary
            final_evidence = self._build_evidence_summary(
                base_evidence, findings, txn, implied_value
            )

            pattern_key = final_pattern.value
            patterns[pattern_key] = patterns.get(pattern_key, 0) + 1

            # Build filing party role string
            roles = []
            if txn.get('is_officer', False):
                roles.append(f"Officer ({txn.get('officer_title', 'Unknown Title')})")
            if txn.get('is_director', False):
                roles.append("Director")
            if txn.get('is_ten_percent_owner', False):
                roles.append("10%+ Owner")
            filing_party_role = ", ".join(roles) if roles else "Reporting Person"

            alert = ZeroValueAlert(
                pattern=final_pattern,
                severity=final_severity,
                transaction_date=self._parse_date(txn.get('transaction_date')),
                transaction_code=txn.get('transaction_code', ''),
                shares=txn.get('shares', 0),
                security_title=txn.get('security_title', ''),
                owner_name=owner_name,
                is_derivative=txn.get('is_derivative', False),
                evidence_summary=final_evidence,
                statutory_references=final_statutes,
                risk_score=final_risk,
                forensic_findings=findings,
                implied_market_value=implied_value,
                filing_party_role=filing_party_role,
                officer_title=txn.get('officer_title', ''),
                is_director=txn.get('is_director', False),
                is_officer=txn.get('is_officer', False),
                is_ten_percent_owner=txn.get('is_ten_percent_owner', False),
                filing_date=self._parse_date(
                    txn.get('filing_date') or
                    (filing_metadata or {}).get('filing_date')
                ),
                accession_number=txn.get('accession_number', '') or
                    (filing_metadata or {}).get('accession_number', ''),
            )
            alerts.append(alert)

        # Additional pattern alerts
        timing_alerts = self._detect_temporal_clustering(
            zero_value_txns, material_events
        )
        alerts.extend(timing_alerts)

        # Aggregate statistics
        suspicious = len(alerts)
        agg_risk = (
            sum(a.risk_score for a in alerts) / len(alerts) if alerts else 0.0
        )
        unique_insiders = len(set(a.owner_name for a in alerts))
        critical_count = sum(1 for a in alerts if a.severity == ZeroValueSeverity.CRITICAL)
        high_count = sum(1 for a in alerts if a.severity == ZeroValueSeverity.HIGH)
        event_correlations = sum(
            1 for a in alerts
            if a.forensic_findings and a.forensic_findings.days_to_nearest_material_event is not None
        )
        contradiction_count = sum(
            1 for a in alerts
            if a.forensic_findings and a.forensic_findings.disclosure_gap > 0
        )
        repeat_count = sum(
            1 for a in alerts
            if a.forensic_findings and a.forensic_findings.insider_zero_dollar_history_count >= self.RECIDIVIST_THRESHOLD
        )
        cluster_count = len(clusters)

        return ZeroValueAnalysis(
            total_zero_value=len(zero_value_txns),
            legitimate_count=0,  # Enhanced mode: nothing auto-cleared
            suspicious_count=suspicious,
            alerts=alerts,
            patterns_detected=patterns,
            aggregate_risk_score=min(agg_risk, 1.0),
            total_implied_market_value=total_implied_value,
            unique_insiders_flagged=unique_insiders,
            critical_alerts=critical_count,
            high_alerts=high_count,
            material_event_correlations=event_correlations,
            disclosure_contradictions=contradiction_count,
            repeat_offender_count=repeat_count,
            multi_insider_clusters=cluster_count,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1: ENHANCED CLASSIFICATION (NO EARLY EXITS)
    # ═══════════════════════════════════════════════════════════════════════

    def _classify_transaction_enhanced(
        self,
        txn: Dict[str, Any],
        material_events: Optional[List[Dict[str, Any]]],
        compensation_data: Optional[Dict[str, Any]],
    ) -> Tuple[ZeroValuePattern, ZeroValueSeverity, str, List[str], float]:
        """
        Classify a $0 transaction - ENHANCED. No early exits.

        Every code gets investigated. "Expected" codes (G, A, F, V) receive
        a REQUIRES_SCRUTINY classification, NOT automatic legitimacy.
        """
        code = txn.get('transaction_code', '').upper()
        is_derivative = txn.get('is_derivative', False)
        shares = txn.get('shares', 0)

        # Gift code - REQUIRES SCRUTINY, not auto-legitimate
        if code in GIFT_CODES:
            return (
                ZeroValuePattern.GIFT_REQUIRING_SCRUTINY,
                ZeroValueSeverity.MEDIUM,
                f"Gift (Code G) $0 transaction - {shares:,.0f} shares - "
                f"REQUIRES forensic timing/benefit/disclosure analysis",
                [
                    "15 USC section 78j(b) (Rule 10b-5 - gift timing manipulation)",
                    "17 CFR section 229.404 (Regulation S-K Item 404 - related party)",
                ],
                0.3,
            )

        # Award/grant code - REQUIRES SCRUTINY
        if code in AWARD_CODES:
            return (
                ZeroValuePattern.AWARD_REQUIRING_SCRUTINY,
                ZeroValueSeverity.MEDIUM,
                f"Award/Grant (Code {code}) $0 transaction - {shares:,.0f} shares - "
                f"REQUIRES proxy cross-reference and benefit extraction",
                [
                    "17 CFR section 229.402 (Regulation S-K Item 402 - compensation)",
                    "15 USC section 78j(b) (Rule 10b-5 - undisclosed compensation)",
                ],
                0.3,
            )

        # Tax withholding - REQUIRES SCRUTINY
        if code in TAX_CODES:
            return (
                ZeroValuePattern.TAX_REQUIRING_SCRUTINY,
                ZeroValueSeverity.MEDIUM,
                f"Tax withholding (Code F) $0 transaction - {shares:,.0f} shares - "
                f"REQUIRES verification against compensation disclosures",
                [
                    "26 USC section 83 (IRC compensation taxation)",
                    "17 CFR section 229.402 (Regulation S-K Item 402)",
                ],
                0.25,
            )

        # Vesting - REQUIRES SCRUTINY
        if code in VESTING_CODES:
            return (
                ZeroValuePattern.VESTING_REQUIRING_SCRUTINY,
                ZeroValueSeverity.MEDIUM,
                f"Vesting (Code V) $0 transaction - {shares:,.0f} shares - "
                f"REQUIRES timing analysis and proxy verification",
                [
                    "17 CFR section 229.402 (Regulation S-K Item 402)",
                    "26 USC section 83 (IRC compensation taxation)",
                ],
                0.25,
            )

        # Derivative exercise at $0 - HIGH suspicion
        if code in DERIVATIVE_CODES or is_derivative:
            exercise_price = txn.get('exercise_price', None)
            if exercise_price is not None:
                try:
                    if float(exercise_price) == 0.0:
                        return (
                            ZeroValuePattern.DERIVATIVE_EXERCISE_ADVANTAGE,
                            ZeroValueSeverity.HIGH,
                            f"Derivative exercise (Code {code}) at $0 exercise price - "
                            f"{shares:,.0f} shares - potential below-market exercise",
                            [
                                "17 CFR section 229.402 (Regulation S-K Item 402)",
                                "15 USC section 78j(b) (Rule 10b-5)",
                                "15 USC section 78p(b) (Section 16(b) short-swing)",
                            ],
                            0.7,
                        )
                except (ValueError, TypeError):
                    pass
            return (
                ZeroValuePattern.DERIVATIVE_EXERCISE_ADVANTAGE,
                ZeroValueSeverity.HIGH,
                f"Derivative (Code {code}) at $0 reported price - "
                f"{shares:,.0f} shares - REQUIRES benefit extraction",
                [
                    "17 CFR section 229.402 (Regulation S-K Item 402)",
                    "15 USC section 78j(b) (Rule 10b-5)",
                ],
                0.5,
            )

        # Transfer codes (J, L, W, Z, K, D) - HIGH suspicion
        if code in TRANSFER_CODES:
            return (
                ZeroValuePattern.BENEFICIAL_OWNERSHIP_TRANSFER,
                ZeroValueSeverity.HIGH,
                f"Transfer (Code {code}) at $0 - {shares:,.0f} shares - "
                f"potential beneficial ownership restructuring",
                [
                    "15 USC section 78j(b) (Rule 10b-5)",
                    "17 CFR section 229.404 (Regulation S-K Item 404)",
                    "17 CFR section 240.13d-3 (Beneficial ownership)",
                ],
                0.7,
            )

        # Market trade codes (P, S) at $0 - CRITICAL (extremely abnormal)
        if code in MARKET_CODES:
            return (
                ZeroValuePattern.ZERO_PRICE_NON_GIFT,
                ZeroValueSeverity.CRITICAL,
                f"Market transaction (Code {code}) at $0 - {shares:,.0f} shares - "
                f"EXTREMELY ABNORMAL - open market at zero consideration",
                [
                    "15 USC section 78j(b) (Rule 10b-5)",
                    "17 CFR section 229.402 (Regulation S-K Item 402)",
                    "17 CFR section 229.404 (Regulation S-K Item 404)",
                    "18 USC section 1348 (Securities fraud)",
                ],
                0.95,
            )

        # Unknown or unrecognized code at $0 - HIGH
        return (
            ZeroValuePattern.ZERO_PRICE_NON_GIFT,
            ZeroValueSeverity.HIGH,
            f"$0 transaction (Code {code}) - {shares:,.0f} shares of "
            f"{txn.get('security_title', 'Unknown')} - unrecognized code at zero value",
            [
                "15 USC section 78j(b) (Rule 10b-5)",
                "17 CFR section 229.402 (Regulation S-K Item 402)",
                "17 CFR section 229.404 (Regulation S-K Item 404)",
            ],
            0.8,
        )

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 2: FINANCIAL BENEFIT EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════

    def _extract_financial_benefit(
        self,
        txn: Dict[str, Any],
        market_prices: Optional[Dict[str, float]],
    ) -> float:
        """
        Extract implied financial benefit of a $0 transaction.

        Calculates: shares x market_price = actual value transferred at $0.
        For derivatives: (underlying_price - exercise_price) x shares.
        """
        shares = txn.get('shares', 0)
        if shares <= 0:
            return 0.0

        market_price = self._get_market_price(txn, market_prices)
        if market_price <= 0:
            return 0.0

        is_derivative = txn.get('is_derivative', False)
        if is_derivative:
            exercise_price = 0.0
            try:
                exercise_price = float(txn.get('exercise_price', 0) or 0)
            except (ValueError, TypeError):
                pass
            spread = max(0, market_price - exercise_price)
            return shares * spread

        return shares * market_price

    def _get_market_price(
        self,
        txn: Dict[str, Any],
        market_prices: Optional[Dict[str, float]],
    ) -> float:
        """Get market price for a security at transaction time."""
        if not market_prices:
            return 0.0

        security = txn.get('security_title', '')
        if security in market_prices:
            return market_prices[security]

        # Try underlying security for derivatives
        underlying = txn.get('underlying_security', '')
        if underlying and underlying in market_prices:
            return market_prices[underlying]

        # Try date-keyed lookup
        txn_date = txn.get('transaction_date', '')
        date_key = f"{security}:{txn_date}"
        if date_key in market_prices:
            return market_prices[date_key]

        return 0.0

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 3: MATERIAL EVENT PROXIMITY
    # ═══════════════════════════════════════════════════════════════════════

    def _analyze_event_proximity(
        self,
        txn: Dict[str, Any],
        material_events: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Analyze proximity to material events. Returns nearest event info."""
        if not material_events:
            return {}

        txn_date = self._parse_date(txn.get('transaction_date'))
        if not txn_date:
            return {}

        nearest_days = None
        nearest_event = None
        nearest_direction = None

        for event in material_events:
            event_date = self._parse_date(event.get('event_date'))
            if not event_date:
                continue

            delta = (event_date - txn_date).days
            abs_delta = abs(delta)

            if nearest_days is None or abs_delta < nearest_days:
                nearest_days = abs_delta
                nearest_event = event.get('event_type', 'material event')
                nearest_direction = 'PRE_EVENT' if delta > 0 else 'POST_EVENT'

        if nearest_days is not None:
            return {
                'days': nearest_days,
                'event_type': nearest_event,
                'direction': nearest_direction,
            }
        return {}

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 4: INSIDER RECIDIVISM / HISTORY
    # ═══════════════════════════════════════════════════════════════════════

    def _build_insider_history(
        self,
        current_txns: List[Dict[str, Any]],
        historical: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Dict[str, Any]]:
        """Build per-insider $0 transaction history."""
        history: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {'count': 0, 'total_shares': 0.0, 'total_value': 0.0, 'dates': []}
        )

        all_txns = list(current_txns)
        if historical:
            all_txns.extend(historical)

        for txn in all_txns:
            owner = txn.get('owner_name', txn.get('reporting_owner_name', ''))
            if not owner:
                continue
            history[owner]['count'] += 1
            history[owner]['total_shares'] += txn.get('shares', 0)
            txn_date = txn.get('transaction_date')
            if txn_date:
                history[owner]['dates'].append(txn_date)

        return dict(history)

    def _build_code_usage_index(
        self,
        current_txns: List[Dict[str, Any]],
        historical: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, List[str]]:
        """Build per-insider transaction code usage for rotation detection."""
        usage: Dict[str, List[str]] = defaultdict(list)

        all_txns = list(current_txns)
        if historical:
            all_txns.extend(historical)

        for txn in all_txns:
            owner = txn.get('owner_name', txn.get('reporting_owner_name', ''))
            code = txn.get('transaction_code', '')
            if owner and code:
                usage[owner].append(code)

        return dict(usage)

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 5: DISCLOSURE CONTRADICTION
    # ═══════════════════════════════════════════════════════════════════════

    def _check_disclosure_contradiction(
        self,
        txn: Dict[str, Any],
        compensation_data: Optional[Dict[str, Any]],
        implied_value: float,
    ) -> Dict[str, Any]:
        """Check $0 transaction against proxy compensation disclosures."""
        if not compensation_data:
            return {'disclosed': False, 'proxy_amount': 0, 'gap': implied_value}

        owner = txn.get('owner_name', txn.get('reporting_owner_name', ''))

        # Look up in compensation data
        person_comp = compensation_data.get(owner, compensation_data.get('executives', {}).get(owner, {}))

        if not person_comp:
            return {'disclosed': False, 'proxy_amount': 0, 'gap': implied_value}

        proxy_amount = person_comp.get('stock_awards', 0) + person_comp.get('option_awards', 0)
        gap = max(0, implied_value - proxy_amount)

        return {
            'disclosed': proxy_amount > 0,
            'proxy_amount': proxy_amount,
            'gap': gap,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 6: LATE FILING
    # ═══════════════════════════════════════════════════════════════════════

    def _check_late_filing(
        self,
        txn: Dict[str, Any],
        filing_metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check if transaction was filed late (> 2 business days)."""
        is_late = txn.get('is_late_filed', False)
        days_late = txn.get('days_late', 0)

        if not is_late and filing_metadata:
            txn_date = self._parse_date(txn.get('transaction_date'))
            filing_date = self._parse_date(filing_metadata.get('filing_date'))

            if txn_date and filing_date:
                business_days = 0
                current = txn_date
                while current < filing_date:
                    current = current + timedelta(days=1)
                    if current.weekday() < 5:
                        business_days += 1

                if business_days > 2:
                    is_late = True
                    days_late = business_days - 2

        return {'is_late': is_late, 'days_late': days_late}

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 7: FOOTNOTE OBFUSCATION
    # ═══════════════════════════════════════════════════════════════════════

    def _score_footnote_obfuscation(self, txn: Dict[str, Any]) -> float:
        """Score footnote vagueness. 0.0=clear/present, 1.0=maximally vague/absent."""
        footnotes = txn.get('footnotes', [])

        if not footnotes:
            # No footnotes on a $0 transaction is suspicious
            return 0.8

        if isinstance(footnotes, str):
            footnotes = [footnotes]

        combined = ' '.join(str(f).lower() for f in footnotes)

        if not combined.strip():
            return 0.8

        vague_count = sum(1 for p in VAGUE_FOOTNOTE_PATTERNS if p in combined)
        total_words = len(combined.split())

        if total_words == 0:
            return 0.8

        # Vagueness = ratio of vague patterns to total content
        vagueness = min(1.0, vague_count / max(1, total_words / 10))

        # Short footnotes are more suspicious
        if total_words < 10:
            vagueness = max(vagueness, 0.5)

        return round(vagueness, 3)

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 8: OWNERSHIP ENTITY COMPLEXITY
    # ═══════════════════════════════════════════════════════════════════════

    def _analyze_ownership_entity(self, txn: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze indirect ownership and entity complexity."""
        direct_indirect = txn.get('direct_indirect', 'D')
        ownership_nature = txn.get('ownership_nature', '') or ''
        owner_name = txn.get('owner_name', txn.get('reporting_owner_name', ''))

        is_indirect = (direct_indirect == 'I')
        entity_type = None
        complexity = 0.0

        text = (ownership_nature + ' ' + owner_name).lower()

        for pattern, score in ENTITY_PATTERNS.items():
            if pattern in text:
                is_indirect = True
                entity_type = pattern.title()
                complexity = max(complexity, score)

        return {
            'indirect': is_indirect,
            'entity_type': entity_type,
            'complexity': complexity,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 9: CODE ROTATION DETECTION
    # ═══════════════════════════════════════════════════════════════════════

    def _check_code_rotation(
        self,
        owner_name: str,
        code_usage: Dict[str, List[str]],
    ) -> Dict[str, Any]:
        """Detect if insider cycles through different transaction codes."""
        codes = code_usage.get(owner_name, [])
        unique_codes = list(set(codes))

        detected = len(unique_codes) >= self.CODE_ROTATION_MIN_CODES

        return {
            'detected': detected,
            'codes': unique_codes,
        }

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 10: MULTI-INSIDER CLUSTER DETECTION
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_multi_insider_clusters(
        self,
        zero_txns: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Detect clusters of multiple insiders filing $0 in same window."""
        clusters = []
        processed = set()

        for i, txn_a in enumerate(zero_txns):
            if i in processed:
                continue

            date_a = self._parse_date(txn_a.get('transaction_date'))
            if not date_a:
                continue

            cluster = [txn_a]
            cluster_indices = {i}
            cluster_insiders = {txn_a.get('owner_name', txn_a.get('reporting_owner_name', ''))}

            for j, txn_b in enumerate(zero_txns):
                if j <= i or j in processed:
                    continue

                date_b = self._parse_date(txn_b.get('transaction_date'))
                if not date_b:
                    continue

                if abs((date_a - date_b).days) <= self.CLUSTERING_WINDOW_DAYS:
                    owner_b = txn_b.get('owner_name', txn_b.get('reporting_owner_name', ''))
                    if owner_b not in cluster_insiders:
                        cluster.append(txn_b)
                        cluster_indices.add(j)
                        cluster_insiders.add(owner_b)

            if len(cluster_insiders) >= 2:
                processed.update(cluster_indices)
                total_shares = sum(t.get('shares', 0) for t in cluster)
                clusters.append({
                    'insiders': list(cluster_insiders),
                    'count': len(cluster_insiders),
                    'transactions': cluster,
                    'total_shares': total_shares,
                    'start_date': date_a,
                })

        return clusters

    def _get_cluster_membership(
        self,
        txn: Dict[str, Any],
        clusters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Get cluster membership info for a transaction."""
        owner = txn.get('owner_name', txn.get('reporting_owner_name', ''))

        for cluster in clusters:
            if owner in cluster['insiders']:
                return {
                    'count': cluster['count'],
                    'total_shares': cluster['total_shares'],
                }
        return {'count': 0, 'total_shares': 0}

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 12: MULTI-VECTOR SEVERITY ESCALATION
    # ═══════════════════════════════════════════════════════════════════════

    def _multi_vector_escalation(
        self,
        base_severity: ZeroValueSeverity,
        base_risk: float,
        findings: ForensicFindings,
        event_proximity: Dict[str, Any],
    ) -> Tuple[ZeroValueSeverity, float, List[str]]:
        """
        Escalate severity based on convergence of multiple forensic vectors.

        More vectors converging = higher escalation.
        """
        risk = base_risk
        reasons = []
        severity_level = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 3}
        current_level = severity_level[base_severity.value]

        # Vector 1: High implied value
        if findings.implied_market_value >= self.HIGH_VALUE_THRESHOLD:
            risk += 0.15
            current_level = max(current_level, 2)
            reasons.append(
                f"High implied value: ${findings.implied_market_value:,.2f}"
            )

        # Vector 2: Material event proximity
        if findings.days_to_nearest_material_event is not None:
            if findings.days_to_nearest_material_event <= self.CRITICAL_PROXIMITY_DAYS:
                risk += 0.25
                current_level = 3  # CRITICAL
                reasons.append(
                    f"CRITICAL proximity: {findings.days_to_nearest_material_event} days "
                    f"to {findings.nearest_event_type}"
                )
            elif findings.days_to_nearest_material_event <= self.HIGH_PROXIMITY_DAYS:
                risk += 0.15
                current_level = max(current_level, 2)
                reasons.append(
                    f"High proximity: {findings.days_to_nearest_material_event} days "
                    f"to {findings.nearest_event_type}"
                )
            elif findings.days_to_nearest_material_event <= self.CLUSTERING_WINDOW_DAYS:
                risk += 0.10
                current_level = max(current_level, 1)
                reasons.append(
                    f"Event correlation: {findings.days_to_nearest_material_event} days "
                    f"to {findings.nearest_event_type}"
                )

        # Vector 3: Recidivist filer
        if findings.insider_zero_dollar_history_count >= self.RECIDIVIST_THRESHOLD:
            risk += 0.10
            current_level = max(current_level, 2)
            reasons.append(
                f"Repeat $0 filer: {findings.insider_zero_dollar_history_count} historical "
                f"$0 transactions"
            )

        # Vector 4: Disclosure contradiction
        if findings.disclosure_gap > 0:
            risk += 0.15
            current_level = max(current_level, 2)
            reasons.append(
                f"Disclosure gap: ${findings.disclosure_gap:,.2f} between "
                f"implied value and proxy disclosure"
            )

        # Vector 5: Late filing
        if findings.is_late_filed:
            risk += 0.10
            current_level = max(current_level, 1)
            reasons.append(f"Late filed by {findings.days_late} business days")

        # Vector 6: Footnote obfuscation
        if findings.footnote_vagueness_score >= 0.6:
            risk += 0.05
            reasons.append(
                f"Footnote obfuscation score: {findings.footnote_vagueness_score:.2f}"
            )

        # Vector 7: Entity complexity
        if findings.entity_complexity_score >= 0.6:
            risk += 0.10
            current_level = max(current_level, 1)
            reasons.append(
                f"Complex ownership entity: {findings.ownership_entity_type} "
                f"(complexity: {findings.entity_complexity_score:.2f})"
            )

        # Vector 8: Code rotation
        if findings.code_rotation_detected:
            risk += 0.10
            current_level = max(current_level, 2)
            reasons.append(
                f"Code rotation: insider used codes {findings.codes_used_by_insider}"
            )

        # Vector 9: Multi-insider cluster
        if findings.cluster_insider_count >= 2:
            risk += 0.15
            current_level = max(current_level, 2)
            reasons.append(
                f"Multi-insider cluster: {findings.cluster_insider_count} insiders, "
                f"{findings.cluster_total_shares:,.0f} total shares"
            )

        # Cap risk at 1.0
        risk = min(1.0, risk)

        # Map level back to severity
        level_to_severity = {
            0: ZeroValueSeverity.LOW,
            1: ZeroValueSeverity.MEDIUM,
            2: ZeroValueSeverity.HIGH,
            3: ZeroValueSeverity.CRITICAL,
        }
        final_severity = level_to_severity[min(current_level, 3)]

        return final_severity, risk, reasons

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 13: FINAL PATTERN DETERMINATION
    # ═══════════════════════════════════════════════════════════════════════

    def _determine_final_pattern(
        self,
        base_pattern: ZeroValuePattern,
        findings: ForensicFindings,
        txn: Dict[str, Any],
    ) -> ZeroValuePattern:
        """Override base pattern if forensic findings warrant it."""

        # Code rotation overrides base pattern
        if findings.code_rotation_detected:
            return ZeroValuePattern.CODE_ROTATION_DETECTED

        # Recidivist overrides
        if findings.insider_zero_dollar_history_count >= self.RECIDIVIST_THRESHOLD:
            return ZeroValuePattern.RECIDIVIST_ZERO_FILER

        # High value transfer overrides
        if findings.implied_market_value >= self.HIGH_VALUE_THRESHOLD:
            return ZeroValuePattern.HIGH_VALUE_ZERO_TRANSFER

        # Disclosure contradiction overrides
        if findings.disclosure_gap > 0 and findings.implied_market_value > 0:
            return ZeroValuePattern.DISCLOSURE_CONTRADICTION

        # Multi-insider cluster overrides
        if findings.cluster_insider_count >= 2:
            return ZeroValuePattern.MULTI_INSIDER_CLUSTER

        # Entity complexity overrides for indirect ownership
        if findings.entity_complexity_score >= 0.6:
            return ZeroValuePattern.BENEFICIAL_OWNERSHIP_TRANSFER

        return base_pattern

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 14: STATUTORY REFERENCE BUILDER
    # ═══════════════════════════════════════════════════════════════════════

    def _build_statutory_references(
        self,
        base_statutes: List[str],
        findings: ForensicFindings,
        pattern: ZeroValuePattern,
    ) -> List[str]:
        """Build comprehensive statutory references based on all findings."""
        refs = list(base_statutes)

        if findings.is_late_filed:
            refs.append("15 USC section 78p(a) (Section 16(a) - late filing)")

        if findings.disclosure_gap > 0:
            if "17 CFR section 229.402" not in ' '.join(refs):
                refs.append("17 CFR section 229.402 (Regulation S-K Item 402)")
            if "17 CFR section 229.404" not in ' '.join(refs):
                refs.append("17 CFR section 229.404 (Regulation S-K Item 404)")

        if findings.days_to_nearest_material_event is not None:
            if findings.days_to_nearest_material_event <= self.CLUSTERING_WINDOW_DAYS:
                if "15 USC section 78j(b)" not in ' '.join(refs):
                    refs.append("15 USC section 78j(b) (Rule 10b-5)")
                if "17 CFR section 240.10b-5" not in ' '.join(refs):
                    refs.append("17 CFR section 240.10b-5 (Insider trading)")

        if findings.entity_complexity_score >= 0.6:
            refs.append("17 CFR section 240.13d-3 (Beneficial ownership)")

        if findings.implied_market_value >= self.HIGH_VALUE_THRESHOLD:
            refs.append("18 USC section 1348 (Securities fraud)")

        # Deduplicate
        seen = set()
        unique_refs = []
        for ref in refs:
            if ref not in seen:
                seen.add(ref)
                unique_refs.append(ref)

        return unique_refs

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 15: EVIDENCE SUMMARY BUILDER
    # ═══════════════════════════════════════════════════════════════════════

    def _build_evidence_summary(
        self,
        base_evidence: str,
        findings: ForensicFindings,
        txn: Dict[str, Any],
        implied_value: float,
    ) -> str:
        """Build comprehensive evidence summary incorporating all vectors."""
        parts = [base_evidence]

        if implied_value > 0:
            parts.append(
                f"IMPLIED MARKET VALUE: ${implied_value:,.2f}"
            )

        if findings.days_to_nearest_material_event is not None:
            parts.append(
                f"EVENT PROXIMITY: {findings.days_to_nearest_material_event} days "
                f"{findings.nearest_event_direction} {findings.nearest_event_type}"
            )

        if findings.insider_zero_dollar_history_count >= self.RECIDIVIST_THRESHOLD:
            parts.append(
                f"RECIDIVIST: {findings.insider_zero_dollar_history_count} prior "
                f"$0 transactions totaling {findings.insider_zero_dollar_total_shares:,.0f} shares"
            )

        if findings.disclosure_gap > 0:
            parts.append(
                f"DISCLOSURE GAP: ${findings.disclosure_gap:,.2f} "
                f"(proxy: ${findings.proxy_compensation_amount:,.2f}, "
                f"implied: ${findings.implied_market_value:,.2f})"
            )

        if findings.is_late_filed:
            parts.append(f"LATE FILED: {findings.days_late} business days late")

        if findings.code_rotation_detected:
            parts.append(
                f"CODE ROTATION: insider used codes {findings.codes_used_by_insider}"
            )

        if findings.cluster_insider_count >= 2:
            parts.append(
                f"CLUSTER: {findings.cluster_insider_count} insiders, "
                f"{findings.cluster_total_shares:,.0f} total shares in window"
            )

        if findings.entity_complexity_score >= 0.5:
            parts.append(
                f"ENTITY: {findings.ownership_entity_type} "
                f"(complexity: {findings.entity_complexity_score:.2f})"
            )

        if findings.footnote_vagueness_score >= 0.6:
            parts.append(
                f"FOOTNOTE OBFUSCATION: score {findings.footnote_vagueness_score:.2f}"
            )

        if findings.multi_vector_escalation:
            parts.append(
                f"ESCALATED: {' | '.join(findings.escalation_reasons)}"
            )

        return " | ".join(parts)

    # ═══════════════════════════════════════════════════════════════════════
    # TEMPORAL CLUSTERING (ENHANCED)
    # ═══════════════════════════════════════════════════════════════════════

    def _detect_temporal_clustering(
        self,
        zero_txns: List[Dict[str, Any]],
        material_events: Optional[List[Dict[str, Any]]],
    ) -> List[ZeroValueAlert]:
        """Detect temporal clustering of ALL $0 transactions near material events."""
        alerts: List[ZeroValueAlert] = []

        if not material_events:
            return alerts

        for txn in zero_txns:
            txn_date = self._parse_date(txn.get('transaction_date'))
            if not txn_date:
                continue

            for event in material_events:
                event_date = self._parse_date(event.get('event_date'))
                if not event_date:
                    continue

                days_diff = abs((txn_date - event_date).days)
                if days_diff <= self.CLUSTERING_WINDOW_DAYS:
                    event_type = event.get('event_type', 'material event')
                    direction = 'PRE_EVENT' if (event_date - txn_date).days > 0 else 'POST_EVENT'

                    if days_diff <= self.CRITICAL_PROXIMITY_DAYS:
                        severity = ZeroValueSeverity.CRITICAL
                    elif days_diff <= self.HIGH_PROXIMITY_DAYS:
                        severity = ZeroValueSeverity.HIGH
                    else:
                        severity = ZeroValueSeverity.MEDIUM

                    code = txn.get('transaction_code', '')

                    alerts.append(ZeroValueAlert(
                        pattern=ZeroValuePattern.TIMING_ANOMALY,
                        severity=severity,
                        transaction_date=txn_date,
                        transaction_code=code,
                        shares=txn.get('shares', 0),
                        security_title=txn.get('security_title', ''),
                        owner_name=txn.get('owner_name', txn.get('reporting_owner_name', '')),
                        is_derivative=txn.get('is_derivative', False),
                        evidence_summary=(
                            f"$0 transaction (Code {code}) {days_diff} days "
                            f"{direction} {event_type} - "
                            f"potential MNPI exploitation regardless of transaction code"
                        ),
                        statutory_references=[
                            "15 USC section 78j(b) (Rule 10b-5)",
                            "17 CFR section 240.10b-5 (Insider trading)",
                        ],
                        risk_score=min(
                            1.0,
                            0.6 + (1.0 - days_diff / self.CLUSTERING_WINDOW_DAYS) * 0.4
                        ),
                    ))

        return alerts

    # ═══════════════════════════════════════════════════════════════════════
    # UTILITY
    # ═══════════════════════════════════════════════════════════════════════

    def _is_zero_value(self, txn: Dict[str, Any]) -> bool:
        """Check if a transaction has zero or near-zero price."""
        price = txn.get('price_per_share', None)
        if price is None:
            return False
        try:
            return float(price) == 0.0
        except (ValueError, TypeError):
            return False

    def _parse_date(self, val: Any) -> Optional[date]:
        """Parse a date value from various formats."""
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y%m%d'):
                try:
                    return datetime.strptime(val, fmt).date()
                except ValueError:
                    continue
            return None
        return None
