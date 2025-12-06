"""
Financial Flow Analyzer - SEC Transaction Flow Forensics
=========================================================

Advanced financial flow analysis for SEC Form 4 insider transactions.
Provides comprehensive flow tracing with integration into the JLAW
forensic analysis platform.

Features:
- Multi-entity transaction flow mapping
- Circular flow detection (wash trading patterns)
- Enrichment scheme identification
- Coordinated insider activity detection
- Integration with contradiction detection
- Temporal flow analysis

Usage:
    analyzer = FinancialFlowAnalyzer()

    filings = [
        {"reporting_owner": {"name": "John Doe"}, "issuer": {"name": "ACME Inc"},
         "transactions": [...]},
        # ... more filings
    ]

    result = analyzer.analyze_filings(filings)
    if result.overall_risk_score > 0.7:
        print("HIGH RISK:", result.key_findings)
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TransactionFlowType(Enum):
    """Types of financial flows in SEC filings."""
    ACQUISITION = "acquisition"
    DISPOSITION = "disposition"
    GRANT = "grant"
    GIFT = "gift"
    EXERCISE = "exercise"
    CONVERSION = "conversion"
    DERIVATIVE = "derivative"
    OTHER = "other"


class FlowRiskSeverity(Enum):
    """Severity levels for detected flow issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FlowPatternType(Enum):
    """Types of detected flow patterns."""
    CIRCULAR_FLOW = "circular_flow"
    ENRICHMENT_SCHEME = "enrichment_scheme"
    COORDINATED_TRADING = "coordinated_trading"
    ANOMALOUS_VALUE = "anomalous_value"
    ZERO_DOLLAR_HIGH_VOLUME = "zero_dollar_high_volume"
    RAPID_TURNOVER = "rapid_turnover"
    CONCENTRATION_RISK = "concentration_risk"


@dataclass
class InsiderFlowProfile:
    """Profile of an insider's transaction flows."""
    insider_name: str
    total_acquisitions: float = 0.0
    total_dispositions: float = 0.0
    total_grants: float = 0.0
    total_exercises: float = 0.0
    net_position_change: float = 0.0
    transaction_count: int = 0
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    zero_dollar_transactions: int = 0
    zero_dollar_shares: float = 0.0
    companies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowPatternAlert:
    """Alert for a detected flow pattern."""
    pattern_type: FlowPatternType
    severity: FlowRiskSeverity
    description: str
    evidence: List[str]
    involved_entities: List[str]
    recommendation: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowAnalysisResult:
    """Result of comprehensive flow analysis."""
    filings_analyzed: int
    total_transactions: int
    total_value_analyzed: float
    insider_profiles: List[InsiderFlowProfile]
    detected_patterns: List[FlowPatternAlert]
    overall_risk_score: float
    risk_severity: FlowRiskSeverity
    key_findings: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# SEC transaction code to flow type mapping.
TRANSACTION_CODE_MAPPING = {
    "A": TransactionFlowType.GRANT,
    "C": TransactionFlowType.CONVERSION,
    "D": TransactionFlowType.DISPOSITION,
    "E": TransactionFlowType.EXERCISE,
    "F": TransactionFlowType.DISPOSITION,
    "G": TransactionFlowType.GIFT,
    "H": TransactionFlowType.OTHER,
    "I": TransactionFlowType.ACQUISITION,
    "J": TransactionFlowType.ACQUISITION,
    "K": TransactionFlowType.DERIVATIVE,
    "L": TransactionFlowType.ACQUISITION,
    "M": TransactionFlowType.EXERCISE,
    "O": TransactionFlowType.EXERCISE,
    "P": TransactionFlowType.ACQUISITION,
    "S": TransactionFlowType.DISPOSITION,
    "U": TransactionFlowType.DISPOSITION,
    "V": TransactionFlowType.ACQUISITION,
    "W": TransactionFlowType.ACQUISITION,
    "X": TransactionFlowType.EXERCISE,
    "Z": TransactionFlowType.ACQUISITION,
}


def parse_transaction_code(code: str) -> TransactionFlowType:
    """Parse SEC transaction code to flow type."""
    return TRANSACTION_CODE_MAPPING.get(code.upper(), TransactionFlowType.OTHER)


def parse_float(value: Any) -> float:
    """Safely parse a value to float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("$", ""))
        except ValueError:
            return 0.0
    return 0.0


def parse_date(date_str: str) -> Optional[datetime]:
    """Safely parse date string."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


class FinancialFlowAnalyzer:
    """
    Comprehensive financial flow analyzer for SEC Form 4 filings.

    Analyzes transaction flows to detect:
    - Circular trading patterns
    - Hidden enrichment schemes
    - Coordinated insider activity
    - Anomalous transaction values
    - Zero-dollar high-volume grants
    """

    # Configuration defaults.
    DEFAULT_CONFIG = {
        "circular_window_days": 30,
        "coordination_window_days": 14,
        "enrichment_window_days": 60,
        "high_value_threshold": 100000.0,
        "zero_dollar_share_threshold": 20000,
        "min_coordination_insiders": 3,
        "rapid_turnover_days": 7,
        "concentration_threshold": 0.8,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Financial Flow Analyzer.

        Args:
            config: Configuration dictionary for analysis parameters
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._insider_profiles: Dict[str, InsiderFlowProfile] = {}
        self._transaction_timeline: List[Dict[str, Any]] = []
        self._flow_graph: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        logger.info("FinancialFlowAnalyzer initialized")

    def analyze_filings(self, filings: List[Dict[str, Any]]) -> FlowAnalysisResult:
        """
        Analyze a batch of SEC filings for flow patterns.

        Args:
            filings: List of parsed Form 4 filing dictionaries

        Returns:
            FlowAnalysisResult with comprehensive analysis
        """
        logger.info(f"Analyzing {len(filings)} filings for flow patterns")

        # Reset state.
        self._insider_profiles = {}
        self._transaction_timeline = []
        self._flow_graph = defaultdict(lambda: defaultdict(float))

        # Process filings.
        total_transactions = 0
        total_value = 0.0

        for filing in filings:
            transactions = self._process_filing(filing)
            total_transactions += len(transactions)
            total_value += sum(t.get("value", 0) for t in transactions)

        # Build insider profiles.
        insider_profiles = list(self._insider_profiles.values())

        # Detect patterns.
        patterns = []
        patterns.extend(self._detect_circular_flows())
        patterns.extend(self._detect_enrichment_schemes())
        patterns.extend(self._detect_coordinated_activity())
        patterns.extend(self._detect_anomalous_values())
        patterns.extend(self._detect_rapid_turnover())
        patterns.extend(self._detect_concentration_risk())

        # Calculate risk.
        risk_score = self._calculate_risk_score(patterns)
        risk_severity = self._determine_severity(risk_score)

        # Generate findings and recommendations.
        findings = self._generate_findings(patterns, insider_profiles)
        recommendations = self._generate_recommendations(patterns, risk_severity)

        return FlowAnalysisResult(
            filings_analyzed=len(filings),
            total_transactions=total_transactions,
            total_value_analyzed=total_value,
            insider_profiles=insider_profiles,
            detected_patterns=patterns,
            overall_risk_score=risk_score,
            risk_severity=risk_severity,
            key_findings=findings,
            recommendations=recommendations,
            metadata={
                "analysis_timestamp": datetime.now().isoformat(),
                "config": self.config,
                "pattern_counts": {
                    pt.value: sum(1 for p in patterns if p.pattern_type == pt)
                    for pt in FlowPatternType
                },
            },
        )

    def _process_filing(self, filing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single filing and extract transactions."""
        insider_name = filing.get("reporting_owner", {}).get("name", "UNKNOWN")
        company_name = filing.get("issuer", {}).get("name", "UNKNOWN")

        # Initialize or get insider profile.
        if insider_name not in self._insider_profiles:
            self._insider_profiles[insider_name] = InsiderFlowProfile(
                insider_name=insider_name
            )
        profile = self._insider_profiles[insider_name]

        if company_name not in profile.companies:
            profile.companies.append(company_name)

        processed_transactions = []

        for tx in filing.get("transactions", []):
            code = tx.get("transaction_code", "")
            flow_type = parse_transaction_code(code)
            shares = parse_float(tx.get("shares", tx.get("shares_traded", 0)))
            price = parse_float(tx.get("price_per_share", 0))
            date_str = tx.get("transaction_date", "")
            value = shares * price

            # Build processed transaction.
            processed_tx = {
                "insider": insider_name,
                "company": company_name,
                "flow_type": flow_type,
                "shares": shares,
                "price": price,
                "value": value,
                "date": date_str,
                "code": code,
                "original": tx,
            }
            processed_transactions.append(processed_tx)
            self._transaction_timeline.append(processed_tx)

            # Update insider profile.
            profile.transaction_count += 1
            if flow_type == TransactionFlowType.ACQUISITION:
                profile.total_acquisitions += shares
            elif flow_type == TransactionFlowType.DISPOSITION:
                profile.total_dispositions += shares
            elif flow_type == TransactionFlowType.GRANT:
                profile.total_grants += shares
            elif flow_type == TransactionFlowType.EXERCISE:
                profile.total_exercises += shares

            if price == 0.0 and shares > 0:
                profile.zero_dollar_transactions += 1
                profile.zero_dollar_shares += shares

            # Update date range.
            if date_str:
                if not profile.date_range_start or date_str < profile.date_range_start:
                    profile.date_range_start = date_str
                if not profile.date_range_end or date_str > profile.date_range_end:
                    profile.date_range_end = date_str

            # Update flow graph.
            if flow_type in [TransactionFlowType.ACQUISITION, TransactionFlowType.GRANT]:
                self._flow_graph[company_name][insider_name] += shares
            elif flow_type == TransactionFlowType.DISPOSITION:
                self._flow_graph[insider_name][company_name] += shares

        # Calculate net position.
        profile.net_position_change = (
            profile.total_acquisitions
            + profile.total_grants
            + profile.total_exercises
            - profile.total_dispositions
        )

        return processed_transactions

    def _detect_circular_flows(self) -> List[FlowPatternAlert]:
        """Detect circular flow patterns (potential wash trading)."""
        patterns = []

        # Look for A->B and B->A flows (bidirectional flows between entities).
        for source, targets in self._flow_graph.items():
            for target, forward_shares in targets.items():
                reverse_shares = self._flow_graph.get(target, {}).get(source, 0)
                if reverse_shares > 0 and forward_shares > 0:
                    min_shares = min(forward_shares, reverse_shares)
                    if min_shares > 1000:  # Significant volume.
                        patterns.append(
                            FlowPatternAlert(
                                pattern_type=FlowPatternType.CIRCULAR_FLOW,
                                severity=FlowRiskSeverity.HIGH,
                                description=(
                                    f"Circular flow detected: {source} <-> {target} "
                                    f"with {int(min_shares):,} overlapping shares"
                                ),
                                evidence=[
                                    f"Forward flow: {int(forward_shares):,} shares",
                                    f"Reverse flow: {int(reverse_shares):,} shares",
                                ],
                                involved_entities=[source, target],
                                recommendation=(
                                    "Investigate for potential wash trading or "
                                    "round-tripping scheme"
                                ),
                                confidence=min(1.0, min_shares / 100000),
                                metadata={
                                    "forward_shares": forward_shares,
                                    "reverse_shares": reverse_shares,
                                    "overlap_shares": min_shares,
                                },
                            )
                        )

        return patterns

    def _detect_enrichment_schemes(self) -> List[FlowPatternAlert]:
        """Detect enrichment schemes (zero-dollar grants followed by sales)."""
        patterns = []
        window_days = self.config["enrichment_window_days"]
        threshold_shares = self.config["zero_dollar_share_threshold"]

        # Find zero-dollar grants and subsequent sales.
        grant_dates: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        sale_dates: Dict[str, List[Tuple[str, float, float]]] = defaultdict(list)

        for tx in self._transaction_timeline:
            if tx["flow_type"] == TransactionFlowType.GRANT and tx["price"] == 0.0:
                grant_dates[tx["insider"]].append((tx["date"], tx["shares"]))
            elif tx["flow_type"] == TransactionFlowType.DISPOSITION:
                sale_dates[tx["insider"]].append((tx["date"], tx["shares"], tx["value"]))

        for insider in grant_dates:
            for grant_date, grant_shares in grant_dates[insider]:
                if grant_shares < threshold_shares:
                    continue

                grant_dt = parse_date(grant_date)
                if not grant_dt:
                    continue

                for sale_date, sale_shares, sale_value in sale_dates.get(insider, []):
                    sale_dt = parse_date(sale_date)
                    if not sale_dt:
                        continue

                    days_diff = (sale_dt - grant_dt).days
                    if 0 < days_diff <= window_days:
                        patterns.append(
                            FlowPatternAlert(
                                pattern_type=FlowPatternType.ENRICHMENT_SCHEME,
                                severity=(
                                    FlowRiskSeverity.CRITICAL
                                    if days_diff <= 14
                                    else FlowRiskSeverity.HIGH
                                ),
                                description=(
                                    f"Potential enrichment: {insider} received zero-dollar "
                                    f"grant of {int(grant_shares):,} shares, followed by sale "
                                    f"after {days_diff} days"
                                ),
                                evidence=[
                                    f"Grant: {grant_date} ({int(grant_shares):,} shares at $0)",
                                    f"Sale date: {sale_date} ({int(sale_shares):,} shares)",
                                    f"Days between: {days_diff}",
                                    f"Sale value: ${sale_value:,.2f}",
                                ],
                                involved_entities=[insider],
                                recommendation=(
                                    "Verify board authorization and compensation committee "
                                    "approval; compare to industry benchmarks"
                                ),
                                confidence=min(1.0, grant_shares / 100000),
                                metadata={
                                    "grant_date": grant_date,
                                    "grant_shares": grant_shares,
                                    "sale_date": sale_date,
                                    "sale_value": sale_value,
                                    "days_to_sale": days_diff,
                                },
                            )
                        )

        return patterns

    def _detect_coordinated_activity(self) -> List[FlowPatternAlert]:
        """Detect coordinated insider activity."""
        patterns = []
        window_days = self.config["coordination_window_days"]
        min_insiders = self.config["min_coordination_insiders"]

        # Group transactions by date.
        dated_transactions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for tx in self._transaction_timeline:
            if tx["date"]:
                dated_transactions[tx["date"]].append(tx)

        sorted_dates = sorted(dated_transactions.keys())

        seen_clusters: Set[str] = set()

        for i, base_date in enumerate(sorted_dates):
            base_dt = parse_date(base_date)
            if not base_dt:
                continue

            cluster_insiders: Set[str] = set()
            cluster_transactions: List[Dict[str, Any]] = []

            for check_date in sorted_dates[i:]:
                check_dt = parse_date(check_date)
                if not check_dt:
                    continue

                if (check_dt - base_dt).days > window_days:
                    break

                for tx in dated_transactions[check_date]:
                    cluster_insiders.add(tx["insider"])
                    cluster_transactions.append(tx)

            if len(cluster_insiders) >= min_insiders:
                cluster_key = "|".join(sorted(cluster_insiders))
                if cluster_key in seen_clusters:
                    continue
                seen_clusters.add(cluster_key)

                # Check if all moving in same direction.
                acquisitions = sum(
                    1
                    for t in cluster_transactions
                    if t["flow_type"]
                    in [
                        TransactionFlowType.ACQUISITION,
                        TransactionFlowType.GRANT,
                        TransactionFlowType.EXERCISE,
                    ]
                )
                dispositions = len(cluster_transactions) - acquisitions
                same_direction = (
                    acquisitions == len(cluster_transactions)
                    or dispositions == len(cluster_transactions)
                )

                if same_direction:
                    direction = "acquiring" if acquisitions > dispositions else "disposing"
                    total_value = sum(t["value"] for t in cluster_transactions)

                    patterns.append(
                        FlowPatternAlert(
                            pattern_type=FlowPatternType.COORDINATED_TRADING,
                            severity=FlowRiskSeverity.HIGH,
                            description=(
                                f"{len(cluster_insiders)} insiders {direction} shares "
                                f"within {window_days}-day window starting {base_date}"
                            ),
                            evidence=[
                                f"Insiders: {', '.join(cluster_insiders)}",
                                f"Total transactions: {len(cluster_transactions)}",
                                f"Total value: ${total_value:,.2f}",
                                f"Direction: {direction}",
                            ],
                            involved_entities=list(cluster_insiders),
                            recommendation=(
                                "Investigate for potential coordinated insider activity "
                                "or MNPI sharing"
                            ),
                            confidence=min(1.0, len(cluster_insiders) / 5),
                            metadata={
                                "window_start": base_date,
                                "insider_count": len(cluster_insiders),
                                "transaction_count": len(cluster_transactions),
                                "total_value": total_value,
                                "direction": direction,
                            },
                        )
                    )

        return patterns

    def _detect_anomalous_values(self) -> List[FlowPatternAlert]:
        """Detect anomalous transaction values."""
        patterns = []
        threshold = self.config["high_value_threshold"]
        zero_threshold = self.config["zero_dollar_share_threshold"]

        # Calculate average value.
        values = [t["value"] for t in self._transaction_timeline if t["value"] > 0]
        avg_value = sum(values) / len(values) if values else 0

        for tx in self._transaction_timeline:
            # High value anomaly.
            if tx["value"] > threshold and tx["value"] > avg_value * 3:
                patterns.append(
                    FlowPatternAlert(
                        pattern_type=FlowPatternType.ANOMALOUS_VALUE,
                        severity=FlowRiskSeverity.MEDIUM,
                        description=(
                            f"Unusually high transaction by {tx['insider']}: "
                            f"${tx['value']:,.2f} ({tx['value'] / avg_value:.1f}x average)"
                        ),
                        evidence=[
                            f"Transaction value: ${tx['value']:,.2f}",
                            f"Average value: ${avg_value:,.2f}",
                            f"Date: {tx['date']}",
                        ],
                        involved_entities=[tx["insider"]],
                        recommendation=(
                            "Verify transaction context and compare to historical patterns"
                        ),
                        confidence=min(1.0, tx["value"] / (avg_value * 5)),
                    )
                )

            # Zero-dollar high volume.
            if tx["price"] == 0.0 and tx["shares"] >= zero_threshold:
                patterns.append(
                    FlowPatternAlert(
                        pattern_type=FlowPatternType.ZERO_DOLLAR_HIGH_VOLUME,
                        severity=FlowRiskSeverity.HIGH,
                        description=(
                            f"Zero-dollar transaction by {tx['insider']}: "
                            f"{int(tx['shares']):,} shares"
                        ),
                        evidence=[
                            f"Shares: {int(tx['shares']):,}",
                            "Price: $0.00",
                            f"Transaction code: {tx['code']}",
                            f"Date: {tx['date']}",
                        ],
                        involved_entities=[tx["insider"]],
                        recommendation=(
                            "Verify against compensation records and board authorization"
                        ),
                        confidence=min(1.0, tx["shares"] / 100000),
                    )
                )

        return patterns

    def _detect_rapid_turnover(self) -> List[FlowPatternAlert]:
        """Detect rapid share turnover patterns."""
        patterns = []
        window_days = self.config["rapid_turnover_days"]

        for insider, profile in self._insider_profiles.items():
            if profile.total_acquisitions > 0 and profile.total_dispositions > 0:
                # Check for rapid buy-sell.
                insider_txs = [
                    t for t in self._transaction_timeline if t["insider"] == insider
                ]
                insider_txs.sort(key=lambda x: x["date"])

                for i, tx1 in enumerate(insider_txs):
                    if tx1["flow_type"] != TransactionFlowType.ACQUISITION:
                        continue

                    dt1 = parse_date(tx1["date"])
                    if not dt1:
                        continue

                    for tx2 in insider_txs[i + 1 :]:
                        if tx2["flow_type"] != TransactionFlowType.DISPOSITION:
                            continue

                        dt2 = parse_date(tx2["date"])
                        if not dt2:
                            continue

                        days_diff = (dt2 - dt1).days
                        if 0 < days_diff <= window_days:
                            patterns.append(
                                FlowPatternAlert(
                                    pattern_type=FlowPatternType.RAPID_TURNOVER,
                                    severity=FlowRiskSeverity.MEDIUM,
                                    description=(
                                        f"Rapid turnover by {insider}: acquisition followed "
                                        f"by disposition within {days_diff} days"
                                    ),
                                    evidence=[
                                        f"Acq: {tx1['date']} ({int(tx1['shares']):,} shares)",
                                        f"Disp: {tx2['date']} ({int(tx2['shares']):,} shares)",
                                        f"Days between: {days_diff}",
                                    ],
                                    involved_entities=[insider],
                                    recommendation=(
                                        "Review for potential short-swing profit violations (16b)"
                                    ),
                                    confidence=min(
                                        1.0, min(tx1["shares"], tx2["shares"]) / 10000
                                    ),
                                )
                            )
                            break  # One per acquisition.

        return patterns

    def _detect_concentration_risk(self) -> List[FlowPatternAlert]:
        """Detect concentration risk (few insiders dominating activity)."""
        patterns = []
        threshold = self.config["concentration_threshold"]

        if len(self._insider_profiles) < 3:
            return patterns

        # Calculate total activity.
        total_shares = sum(
            p.total_acquisitions + p.total_dispositions + p.total_grants
            for p in self._insider_profiles.values()
        )

        if total_shares == 0:
            return patterns

        # Find concentration.
        sorted_profiles = sorted(
            self._insider_profiles.values(),
            key=lambda p: p.total_acquisitions + p.total_dispositions + p.total_grants,
            reverse=True,
        )

        top_insider = sorted_profiles[0]
        top_shares = (
            top_insider.total_acquisitions
            + top_insider.total_dispositions
            + top_insider.total_grants
        )
        concentration = top_shares / total_shares

        if concentration >= threshold:
            patterns.append(
                FlowPatternAlert(
                    pattern_type=FlowPatternType.CONCENTRATION_RISK,
                    severity=FlowRiskSeverity.MEDIUM,
                    description=(
                        f"High concentration: {top_insider.insider_name} accounts for "
                        f"{concentration * 100:.1f}% of all activity"
                    ),
                    evidence=[
                        f"Top insider shares: {int(top_shares):,}",
                        f"Total shares: {int(total_shares):,}",
                        f"Concentration: {concentration * 100:.1f}%",
                    ],
                    involved_entities=[top_insider.insider_name],
                    recommendation=(
                        "Review concentration patterns and verify appropriate oversight"
                    ),
                    confidence=concentration,
                )
            )

        return patterns

    def _calculate_risk_score(self, patterns: List[FlowPatternAlert]) -> float:
        """Calculate overall risk score from patterns."""
        if not patterns:
            return 0.0

        severity_weights = {
            FlowRiskSeverity.CRITICAL: 1.0,
            FlowRiskSeverity.HIGH: 0.7,
            FlowRiskSeverity.MEDIUM: 0.4,
            FlowRiskSeverity.LOW: 0.2,
            FlowRiskSeverity.INFO: 0.1,
        }

        weighted_sum = sum(
            severity_weights.get(p.severity, 0.5) * p.confidence for p in patterns
        )

        # Normalize with diminishing returns.
        count_factor = len(patterns) ** 0.5
        raw_score = weighted_sum / count_factor if count_factor > 0 else 0

        return min(raw_score, 1.0)

    def _determine_severity(self, score: float) -> FlowRiskSeverity:
        """Determine severity from score."""
        if score >= 0.8:
            return FlowRiskSeverity.CRITICAL
        elif score >= 0.6:
            return FlowRiskSeverity.HIGH
        elif score >= 0.3:
            return FlowRiskSeverity.MEDIUM
        elif score >= 0.1:
            return FlowRiskSeverity.LOW
        return FlowRiskSeverity.INFO

    def _generate_findings(
        self,
        patterns: List[FlowPatternAlert],
        profiles: List[InsiderFlowProfile],
    ) -> List[str]:
        """Generate key findings."""
        findings = []

        # Pattern summary.
        type_counts: Dict[FlowPatternType, int] = {}
        for p in patterns:
            type_counts[p.pattern_type] = type_counts.get(p.pattern_type, 0) + 1

        for ptype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            findings.append(f"{ptype.value.upper()}: {count} instance(s) detected")

        # Profile highlights.
        high_zero_dollar = [p for p in profiles if p.zero_dollar_shares > 50000]
        for p in high_zero_dollar[:3]:
            findings.append(
                f"{p.insider_name}: {int(p.zero_dollar_shares):,} shares in "
                f"zero-dollar transactions"
            )

        # Critical patterns.
        critical = [p for p in patterns if p.severity == FlowRiskSeverity.CRITICAL]
        for p in critical[:3]:
            findings.append(f"CRITICAL: {p.description}")

        return findings[:10]

    def _generate_recommendations(
        self,
        patterns: List[FlowPatternAlert],
        severity: FlowRiskSeverity,
    ) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        if severity == FlowRiskSeverity.CRITICAL:
            recommendations.append(
                "IMMEDIATE FORENSIC REVIEW REQUIRED - Multiple critical patterns detected"
            )
            recommendations.append(
                "Consider engagement of external forensic accountants"
            )
        elif severity == FlowRiskSeverity.HIGH:
            recommendations.append(
                "PRIORITY INVESTIGATION RECOMMENDED - Significant suspicious patterns"
            )
            recommendations.append(
                "Cross-reference with earnings calendar and material events"
            )

        # Unique pattern recommendations.
        seen = set()
        for p in patterns:
            if p.recommendation not in seen:
                recommendations.append(p.recommendation)
                seen.add(p.recommendation)

        if not recommendations:
            recommendations.append("Continue monitoring - No significant issues detected")

        return recommendations[:10]


def analyze_filing_flows(
    filings: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> FlowAnalysisResult:
    """
    Convenience function to analyze filing flows.

    Args:
        filings: List of parsed SEC filings
        config: Optional configuration

    Returns:
        FlowAnalysisResult
    """
    analyzer = FinancialFlowAnalyzer(config)
    return analyzer.analyze_filings(filings)


def quick_flow_assessment(filings: List[Dict[str, Any]]) -> str:
    """
    Quick risk assessment for filings.

    Args:
        filings: List of parsed SEC filings

    Returns:
        Risk level string
    """
    result = analyze_filing_flows(filings)
    return result.risk_severity.value.upper()
