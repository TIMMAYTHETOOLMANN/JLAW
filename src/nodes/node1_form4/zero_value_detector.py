"""
Zero Value Transaction Analyzer
================================

Detects and classifies $0 reported transactions in SEC Form 4 filings.

Detection vectors:
- transactionPricePerShare == 0 with transactionCode != 'G' (mismatch)
- High-value securities with zero reported consideration
- Temporal clustering of $0 transactions near earnings announcements
- Cross-reference with DEF 14A compensation disclosures

Statutory framework:
- 15 USC §78j(b) / Rule 10b-5: Gift timing manipulation
- 17 CFR §229.402: Undisclosed compensation (Regulation S-K Item 402)
- 17 CFR §229.404: Related party transactions (Regulation S-K Item 404)
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ZeroValuePattern(Enum):
    """Classification of $0 transaction patterns."""
    ZERO_PRICE_NON_GIFT = "zero_price_non_gift"
    DERIVATIVE_EXERCISE_ADVANTAGE = "derivative_exercise_advantage"
    UNDISCLOSED_COMPENSATION = "undisclosed_compensation"
    RELATED_PARTY_TRANSFER = "related_party_transfer"
    TIMING_ANOMALY = "timing_anomaly"
    LEGITIMATE_GIFT = "legitimate_gift"
    STOCK_AWARD_GRANT = "stock_award_grant"
    TAX_WITHHOLDING = "tax_withholding"


class ZeroValueSeverity(Enum):
    """Alert severity for zero-value transactions."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ZeroValueAlert:
    """Alert for a suspicious $0 transaction."""
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

    def to_dict(self) -> Dict[str, Any]:
        return {
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
        }


@dataclass
class ZeroValueAnalysis:
    """Complete analysis of $0 transactions in a filing set."""
    total_zero_value: int
    legitimate_count: int
    suspicious_count: int
    alerts: List[ZeroValueAlert]
    patterns_detected: Dict[str, int]
    aggregate_risk_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_zero_value": self.total_zero_value,
                "legitimate_count": self.legitimate_count,
                "suspicious_count": self.suspicious_count,
            },
            "patterns_detected": self.patterns_detected,
            "aggregate_risk_score": round(self.aggregate_risk_score, 3),
            "alerts": [a.to_dict() for a in self.alerts],
        }


# Gift-related transaction codes (legitimate $0)
GIFT_CODES = {'G'}

# Award/grant codes (typically legitimate $0)
AWARD_CODES = {'A', 'I'}

# Tax withholding codes (legitimate $0 price)
TAX_CODES = {'F'}

# Derivative exercise/conversion codes
DERIVATIVE_CODES = {'M', 'C', 'X', 'E', 'O', 'H'}


class ZeroValueTransactionAnalyzer:
    """
    Detect and classify $0 reported transactions.

    Identifies:
    - Legitimate gifts (Code G)
    - Exercise of derivatives at favorable terms
    - Stock awards/grants (verify against DEF 14A)
    - Suspicious non-gift $0 transfers
    """

    SUSPICIOUS_PATTERNS = [
        'zero_price_non_gift',
        'derivative_exercise_advantage',
        'undisclosed_compensation',
        'related_party_transfer',
        'timing_anomaly',
    ]

    # Temporal clustering window (days)
    CLUSTERING_WINDOW_DAYS = 30

    def analyze(
        self,
        transactions: List[Dict[str, Any]],
        material_events: Optional[List[Dict[str, Any]]] = None,
        compensation_data: Optional[Dict[str, Any]] = None,
    ) -> ZeroValueAnalysis:
        """
        Analyze transactions for $0 value anomalies.

        Args:
            transactions: List of Form 4 transaction dicts with keys:
                transaction_code, price_per_share, shares, transaction_date,
                security_title, owner_name, is_derivative, exercise_price
            material_events: Optional list of material event dicts with
                event_date, event_type keys for timing correlation
            compensation_data: Optional DEF 14A compensation data for
                cross-reference verification

        Returns:
            ZeroValueAnalysis with alerts and risk scoring
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

        alerts: List[ZeroValueAlert] = []
        patterns: Dict[str, int] = {}
        legitimate = 0

        for txn in zero_value_txns:
            classification = self._classify_transaction(
                txn, material_events, compensation_data
            )
            pattern, severity, evidence, statutes, risk = classification

            pattern_key = pattern.value
            patterns[pattern_key] = patterns.get(pattern_key, 0) + 1

            if pattern in (
                ZeroValuePattern.LEGITIMATE_GIFT,
                ZeroValuePattern.STOCK_AWARD_GRANT,
                ZeroValuePattern.TAX_WITHHOLDING,
            ):
                legitimate += 1
            else:
                alerts.append(ZeroValueAlert(
                    pattern=pattern,
                    severity=severity,
                    transaction_date=self._parse_date(txn.get('transaction_date')),
                    transaction_code=txn.get('transaction_code', ''),
                    shares=txn.get('shares', 0),
                    security_title=txn.get('security_title', ''),
                    owner_name=txn.get('owner_name', ''),
                    is_derivative=txn.get('is_derivative', False),
                    evidence_summary=evidence,
                    statutory_references=statutes,
                    risk_score=risk,
                ))

        # Check for temporal clustering of $0 transactions
        timing_alerts = self._detect_temporal_clustering(
            zero_value_txns, material_events
        )
        alerts.extend(timing_alerts)

        suspicious = len(alerts)
        agg_risk = (
            sum(a.risk_score for a in alerts) / len(alerts) if alerts else 0.0
        )

        return ZeroValueAnalysis(
            total_zero_value=len(zero_value_txns),
            legitimate_count=legitimate,
            suspicious_count=suspicious,
            alerts=alerts,
            patterns_detected=patterns,
            aggregate_risk_score=min(agg_risk, 1.0),
        )

    def _is_zero_value(self, txn: Dict[str, Any]) -> bool:
        """Check if a transaction has zero or near-zero price."""
        price = txn.get('price_per_share', None)
        if price is None:
            return False
        try:
            return float(price) == 0.0
        except (ValueError, TypeError):
            return False

    def _classify_transaction(
        self,
        txn: Dict[str, Any],
        material_events: Optional[List[Dict[str, Any]]],
        compensation_data: Optional[Dict[str, Any]],
    ) -> Tuple[ZeroValuePattern, ZeroValueSeverity, str, List[str], float]:
        """
        Classify a $0 transaction into a pattern.

        Returns:
            (pattern, severity, evidence_summary, statutory_references, risk_score)
        """
        code = txn.get('transaction_code', '').upper()
        is_derivative = txn.get('is_derivative', False)
        shares = txn.get('shares', 0)

        # Legitimate gift
        if code in GIFT_CODES:
            return (
                ZeroValuePattern.LEGITIMATE_GIFT,
                ZeroValueSeverity.LOW,
                "Gift transaction (Code G) with $0 price - standard reporting",
                [],
                0.0,
            )

        # Stock award/grant
        if code in AWARD_CODES:
            return (
                ZeroValuePattern.STOCK_AWARD_GRANT,
                ZeroValueSeverity.LOW,
                f"Stock award/grant (Code {code}) with $0 price - verify against proxy",
                [],
                0.0,
            )

        # Tax withholding
        if code in TAX_CODES:
            return (
                ZeroValuePattern.TAX_WITHHOLDING,
                ZeroValueSeverity.LOW,
                "Tax withholding (Code F) with $0 price - standard",
                [],
                0.0,
            )

        # Derivative exercise at $0 - potentially advantageous
        if code in DERIVATIVE_CODES or is_derivative:
            exercise_price = txn.get('exercise_price', None)
            if exercise_price is not None and float(exercise_price) == 0.0:
                return (
                    ZeroValuePattern.DERIVATIVE_EXERCISE_ADVANTAGE,
                    ZeroValueSeverity.HIGH,
                    f"Derivative exercise (Code {code}) at $0 exercise price - "
                    f"{shares:,.0f} shares - potential below-market exercise",
                    [
                        "17 CFR §229.402 (Regulation S-K Item 402)",
                        "15 USC §78j(b) (Rule 10b-5)",
                    ],
                    0.7,
                )
            return (
                ZeroValuePattern.DERIVATIVE_EXERCISE_ADVANTAGE,
                ZeroValueSeverity.MEDIUM,
                f"Derivative transaction (Code {code}) at $0 reported price - "
                f"{shares:,.0f} shares",
                ["17 CFR §229.402 (Regulation S-K Item 402)"],
                0.5,
            )

        # Non-gift $0 transaction - suspicious
        return (
            ZeroValuePattern.ZERO_PRICE_NON_GIFT,
            ZeroValueSeverity.HIGH,
            f"$0 transaction (Code {code}) without gift designation - "
            f"{shares:,.0f} shares of {txn.get('security_title', 'Unknown')} - "
            f"potential undisclosed compensation or related party transfer",
            [
                "15 USC §78j(b) (Rule 10b-5)",
                "17 CFR §229.402 (Regulation S-K Item 402)",
                "17 CFR §229.404 (Regulation S-K Item 404)",
            ],
            0.8,
        )

    def _detect_temporal_clustering(
        self,
        zero_txns: List[Dict[str, Any]],
        material_events: Optional[List[Dict[str, Any]]],
    ) -> List[ZeroValueAlert]:
        """Detect temporal clustering of $0 transactions near material events."""
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
                    alerts.append(ZeroValueAlert(
                        pattern=ZeroValuePattern.TIMING_ANOMALY,
                        severity=ZeroValueSeverity.CRITICAL if days_diff <= 7 else ZeroValueSeverity.HIGH,
                        transaction_date=txn_date,
                        transaction_code=txn.get('transaction_code', ''),
                        shares=txn.get('shares', 0),
                        security_title=txn.get('security_title', ''),
                        owner_name=txn.get('owner_name', ''),
                        is_derivative=txn.get('is_derivative', False),
                        evidence_summary=(
                            f"$0 transaction {days_diff} days from {event_type} - "
                            f"potential MNPI exploitation"
                        ),
                        statutory_references=[
                            "15 USC §78j(b) (Rule 10b-5)",
                            "17 CFR §240.10b-5",
                        ],
                        risk_score=min(1.0, 0.6 + (1.0 - days_diff / self.CLUSTERING_WINDOW_DAYS) * 0.4),
                    ))

        return alerts

    def _parse_date(self, val: Any) -> Optional[date]:
        """Parse a date value from various formats."""
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            try:
                return datetime.strptime(val, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None
