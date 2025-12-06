"""
JARVIS:LAW - Financial Flow Tracer Module
==========================================

Module: financial_flow_tracer.py
Purpose: Comprehensive financial transaction flow analysis for forensic investigations
Classification: Forensic Grade - Financial Intelligence Layer

CAPABILITIES:
- Transaction flow mapping and visualization
- Circular flow detection (wash trading, round-tripping)
- Hidden enrichment scheme detection
- Cross-entity transaction correlation
- Insider-to-company flow analysis
- Anomalous flow pattern detection
- Integration with zero_dollar_detector for comprehensive analysis

PowerShell Compatible: YES (No Unicode, emojis, or special characters)
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class FlowType(Enum):
    """Types of financial flows."""
    ACQUISITION = "acquisition"
    DISPOSITION = "disposition"
    GRANT = "grant"
    GIFT = "gift"
    EXERCISE = "exercise"
    CONVERSION = "conversion"
    DERIVATIVE = "derivative"
    UNKNOWN = "unknown"


class FlowRiskLevel(Enum):
    """Risk level classification for flows."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class TransactionFlow:
    """Represents a single transaction flow."""
    flow_id: str
    source_entity: str
    target_entity: str
    flow_type: FlowType
    shares: float
    value: float
    transaction_date: str
    transaction_code: str
    price_per_share: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowPattern:
    """Detected flow pattern."""
    pattern_type: str
    flows: List[TransactionFlow]
    risk_level: FlowRiskLevel
    description: str
    recommendation: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowAnalysisResult:
    """Result of financial flow analysis."""
    total_flows: int
    total_value: float
    entities: List[str]
    patterns: List[FlowPattern]
    risk_score: float
    risk_level: FlowRiskLevel
    findings: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


# Transaction code mappings.
TRANSACTION_CODE_MAP = {
    "A": FlowType.GRANT,  # Award
    "C": FlowType.CONVERSION,  # Conversion
    "D": FlowType.DISPOSITION,  # Disposition to issuer
    "E": FlowType.EXERCISE,  # Expiration
    "F": FlowType.EXERCISE,  # In-kind payment for taxes
    "G": FlowType.GIFT,  # Gift
    "H": FlowType.EXERCISE,  # Expiration
    "I": FlowType.ACQUISITION,  # Discretionary
    "J": FlowType.ACQUISITION,  # Other acquisition
    "K": FlowType.DERIVATIVE,  # Equity swap
    "L": FlowType.ACQUISITION,  # Small acquisition
    "M": FlowType.EXERCISE,  # Exercise/conversion
    "O": FlowType.EXERCISE,  # Exercise out-of-money
    "P": FlowType.ACQUISITION,  # Open market purchase
    "S": FlowType.DISPOSITION,  # Open market sale
    "U": FlowType.DERIVATIVE,  # Disposition pursuant to tender
    "V": FlowType.ACQUISITION,  # Transaction in non-public tender
    "W": FlowType.ACQUISITION,  # Acquisition pursuant to will
    "X": FlowType.EXERCISE,  # Exercise of in-the-money derivative
    "Z": FlowType.ACQUISITION,  # Trust deposit
}


def get_flow_type(transaction_code: str) -> FlowType:
    """Map transaction code to flow type."""
    return TRANSACTION_CODE_MAP.get(transaction_code.upper(), FlowType.UNKNOWN)


def is_acquisition_flow(transaction_code: str) -> bool:
    """Check if transaction code indicates an acquisition flow."""
    flow_type = get_flow_type(transaction_code)
    return flow_type in [FlowType.ACQUISITION, FlowType.GRANT, FlowType.EXERCISE]


class FinancialFlowTracer:
    """
    Financial Flow Tracer for forensic transaction analysis.

    Traces and analyzes financial transaction flows to detect:
    - Circular flow patterns (potential wash trading)
    - Hidden enrichment schemes (zero-dollar grants followed by sales)
    - Coordinated insider activity
    - Suspicious flow timing patterns
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Financial Flow Tracer.

        Args:
            config: Configuration dictionary for thresholds and parameters
        """
        self.config = config or self._default_config()
        self.flows: List[TransactionFlow] = []
        self.entity_flows: Dict[str, List[TransactionFlow]] = defaultdict(list)
        self._flow_counter = 0

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for flow analysis."""
        return {
            "circular_flow_window_days": 30,
            "enrichment_threshold_shares": 10000,
            "high_value_threshold": 100000.0,
            "suspicious_timing_window_days": 7,
            "min_circular_flow_value": 50000.0,
            "zero_dollar_flag_threshold": 20000,
            "correlation_window_days": 14,
        }

    def _generate_flow_id(self) -> str:
        """Generate unique flow ID."""
        self._flow_counter += 1
        return f"FLOW-{self._flow_counter:06d}"

    def add_transaction(
        self,
        insider_name: str,
        company_name: str,
        transaction_code: str,
        shares: float,
        price_per_share: float,
        transaction_date: str,
        is_acquisition: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TransactionFlow:
        """
        Add a transaction to the flow tracker.

        Args:
            insider_name: Name of the insider
            company_name: Name of the company
            transaction_code: SEC transaction code
            shares: Number of shares
            price_per_share: Price per share
            transaction_date: Date of transaction (YYYY-MM-DD)
            is_acquisition: True if acquiring shares, False if disposing
            metadata: Additional transaction metadata

        Returns:
            TransactionFlow object
        """
        flow_type = get_flow_type(transaction_code)

        # Determine source and target based on transaction direction.
        if is_acquisition or flow_type in [FlowType.GRANT, FlowType.GIFT]:
            source_entity = company_name
            target_entity = insider_name
        else:
            source_entity = insider_name
            target_entity = company_name

        value = shares * price_per_share

        flow = TransactionFlow(
            flow_id=self._generate_flow_id(),
            source_entity=source_entity,
            target_entity=target_entity,
            flow_type=flow_type,
            shares=shares,
            value=value,
            transaction_date=transaction_date,
            transaction_code=transaction_code,
            price_per_share=price_per_share,
            metadata=metadata or {},
        )

        self.flows.append(flow)
        self.entity_flows[insider_name].append(flow)
        self.entity_flows[company_name].append(flow)

        return flow

    def add_transactions_from_filing(
        self, filing_data: Dict[str, Any]
    ) -> List[TransactionFlow]:
        """
        Add transactions from a parsed SEC filing.

        Args:
            filing_data: Parsed Form 4 filing data

        Returns:
            List of created TransactionFlow objects
        """
        created_flows = []

        insider_name = filing_data.get("reporting_owner", {}).get("name", "UNKNOWN")
        company_name = filing_data.get("issuer", {}).get("name", "UNKNOWN")

        for tx in filing_data.get("transactions", []):
            transaction_code = tx.get("transaction_code", "")
            shares_str = str(tx.get("shares", tx.get("shares_traded", "0")))
            price_str = str(tx.get("price_per_share", "0"))
            transaction_date = tx.get("transaction_date", "")

            # Parse shares.
            try:
                shares = float(shares_str.replace(",", "").replace("$", ""))
            except (ValueError, AttributeError):
                shares = 0.0

            # Parse price.
            try:
                price = float(price_str.replace(",", "").replace("$", ""))
            except (ValueError, AttributeError):
                price = 0.0

            # Determine if acquisition based on code.
            is_acquisition = is_acquisition_flow(transaction_code)

            flow = self.add_transaction(
                insider_name=insider_name,
                company_name=company_name,
                transaction_code=transaction_code,
                shares=shares,
                price_per_share=price,
                transaction_date=transaction_date,
                is_acquisition=is_acquisition,
                metadata={
                    "filing_accession": filing_data.get("accession_number", ""),
                    "original_transaction": tx,
                },
            )
            created_flows.append(flow)

        return created_flows

    def detect_circular_flows(self) -> List[FlowPattern]:
        """
        Detect circular flow patterns (potential wash trading/round-tripping).

        A circular flow is when shares flow from Entity A -> Entity B -> Entity A
        within a short time window.

        Returns:
            List of detected circular flow patterns
        """
        patterns = []
        window_days = self.config["circular_flow_window_days"]
        min_value = self.config["min_circular_flow_value"]

        # Group flows by entity pairs.
        pair_flows: Dict[Tuple[str, str], List[TransactionFlow]] = defaultdict(list)
        for flow in self.flows:
            pair_key = (flow.source_entity, flow.target_entity)
            pair_flows[pair_key].append(flow)

        # Look for reverse flows within window.
        for (source, target), forward_flows in pair_flows.items():
            reverse_key = (target, source)
            reverse_flows = pair_flows.get(reverse_key, [])

            if not reverse_flows:
                continue

            for fwd in forward_flows:
                try:
                    fwd_date = datetime.strptime(fwd.transaction_date, "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue

                for rev in reverse_flows:
                    try:
                        rev_date = datetime.strptime(rev.transaction_date, "%Y-%m-%d")
                    except (ValueError, TypeError):
                        continue

                    days_diff = abs((rev_date - fwd_date).days)

                    if days_diff <= window_days:
                        combined_value = fwd.value + rev.value

                        if combined_value >= min_value:
                            patterns.append(
                                FlowPattern(
                                    pattern_type="CIRCULAR_FLOW",
                                    flows=[fwd, rev],
                                    risk_level=FlowRiskLevel.HIGH,
                                    description=(
                                        f"Circular flow detected: {source} -> {target} "
                                        f"-> {source} within {days_diff} days"
                                    ),
                                    recommendation=(
                                        "Investigate for potential wash trading or "
                                        "round-tripping scheme"
                                    ),
                                    confidence=min(1.0, 1.0 - (days_diff / window_days)),
                                    metadata={
                                        "days_between": days_diff,
                                        "combined_value": combined_value,
                                    },
                                )
                            )

        return patterns

    def detect_enrichment_schemes(self) -> List[FlowPattern]:
        """
        Detect hidden enrichment schemes.

        Pattern: Zero-dollar grant/award followed by sale within window.

        Returns:
            List of detected enrichment scheme patterns
        """
        patterns = []
        window_days = self.config["suspicious_timing_window_days"]
        threshold_shares = self.config["enrichment_threshold_shares"]

        for entity, flows in self.entity_flows.items():
            # Skip company entities.
            if any(
                keyword in entity.lower()
                for keyword in ["inc", "corp", "llc", "ltd", "company"]
            ):
                continue

            # Find zero-dollar grants.
            grants = [
                f
                for f in flows
                if f.flow_type == FlowType.GRANT and f.price_per_share == 0.0
            ]

            # Find subsequent sales.
            sales = [f for f in flows if f.flow_type == FlowType.DISPOSITION]

            for grant in grants:
                try:
                    grant_date = datetime.strptime(grant.transaction_date, "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue

                for sale in sales:
                    try:
                        sale_date = datetime.strptime(sale.transaction_date, "%Y-%m-%d")
                    except (ValueError, TypeError):
                        continue

                    days_diff = (sale_date - grant_date).days

                    if 0 < days_diff <= window_days * 2 and grant.shares >= threshold_shares:
                        patterns.append(
                            FlowPattern(
                                pattern_type="ENRICHMENT_SCHEME",
                                flows=[grant, sale],
                                risk_level=(
                                    FlowRiskLevel.CRITICAL
                                    if days_diff <= window_days
                                    else FlowRiskLevel.HIGH
                                ),
                                description=(
                                    f"Potential enrichment: Zero-dollar grant of "
                                    f"{int(grant.shares):,} shares followed by sale "
                                    f"after {days_diff} days"
                                ),
                                recommendation=(
                                    "Verify board authorization and compensation committee "
                                    "approval; compare to industry benchmarks"
                                ),
                                confidence=min(1.0, grant.shares / 100000),
                                metadata={
                                    "days_to_sale": days_diff,
                                    "grant_shares": grant.shares,
                                    "sale_value": sale.value,
                                    "insider": entity,
                                },
                            )
                        )

        return patterns

    def detect_coordinated_activity(self) -> List[FlowPattern]:
        """
        Detect coordinated insider trading activity.

        Pattern: Multiple insiders trading in same direction within narrow window.

        Returns:
            List of detected coordinated activity patterns
        """
        patterns = []
        window_days = self.config["correlation_window_days"]

        # Group flows by date.
        dated_flows: Dict[str, List[TransactionFlow]] = defaultdict(list)
        for flow in self.flows:
            if flow.transaction_date:
                dated_flows[flow.transaction_date].append(flow)

        # Look for multiple unique insiders trading on same/near dates.
        sorted_dates = sorted(dated_flows.keys())

        for i, base_date in enumerate(sorted_dates):
            try:
                base_dt = datetime.strptime(base_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                continue

            cluster_flows = []
            cluster_entities: Set[str] = set()

            for check_date in sorted_dates[i:]:
                try:
                    check_dt = datetime.strptime(check_date, "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue

                if (check_dt - base_dt).days > window_days:
                    break

                for flow in dated_flows[check_date]:
                    # Skip company entities.
                    entity = flow.target_entity
                    if any(
                        keyword in entity.lower()
                        for keyword in ["inc", "corp", "llc", "ltd", "company"]
                    ):
                        entity = flow.source_entity

                    cluster_flows.append(flow)
                    cluster_entities.add(entity)

            if len(cluster_entities) >= 3:
                # Check if flows are in same direction.
                acquisition_count = sum(
                    1
                    for f in cluster_flows
                    if f.flow_type
                    in [FlowType.ACQUISITION, FlowType.GRANT, FlowType.EXERCISE]
                )
                disposition_count = len(cluster_flows) - acquisition_count

                if acquisition_count == len(cluster_flows) or disposition_count == len(
                    cluster_flows
                ):
                    direction = (
                        "acquiring" if acquisition_count > disposition_count else "disposing"
                    )
                    total_value = sum(f.value for f in cluster_flows)

                    patterns.append(
                        FlowPattern(
                            pattern_type="COORDINATED_ACTIVITY",
                            flows=cluster_flows[:10],  # Limit stored flows.
                            risk_level=FlowRiskLevel.HIGH,
                            description=(
                                f"{len(cluster_entities)} insiders {direction} shares "
                                f"within {window_days}-day window starting {base_date}"
                            ),
                            recommendation=(
                                "Investigate for potential coordinated insider activity "
                                "or MNPI sharing"
                            ),
                            confidence=min(1.0, len(cluster_entities) / 5),
                            metadata={
                                "entities": list(cluster_entities),
                                "total_value": total_value,
                                "direction": direction,
                                "window_start": base_date,
                            },
                        )
                    )

        # Deduplicate overlapping patterns.
        unique_patterns = []
        seen_starts = set()
        for pattern in patterns:
            start = pattern.metadata.get("window_start", "")
            if start not in seen_starts:
                seen_starts.add(start)
                unique_patterns.append(pattern)

        return unique_patterns

    def detect_anomalous_value_flows(self) -> List[FlowPattern]:
        """
        Detect flows with anomalous values.

        Pattern: Unusually high or suspiciously low transaction values.

        Returns:
            List of detected anomalous value patterns
        """
        patterns = []
        high_value_threshold = self.config["high_value_threshold"]

        # Calculate average flow value.
        values = [f.value for f in self.flows if f.value > 0]
        avg_value = sum(values) / len(values) if values else 0.0

        for flow in self.flows:
            # High value anomaly.
            if avg_value > 0 and flow.value > high_value_threshold and flow.value > avg_value * 3:
                patterns.append(
                    FlowPattern(
                        pattern_type="ANOMALOUS_HIGH_VALUE",
                        flows=[flow],
                        risk_level=FlowRiskLevel.MEDIUM,
                        description=(
                            f"Unusually high transaction value: ${flow.value:,.2f} "
                            f"({flow.value / avg_value:.1f}x average)"
                        ),
                        recommendation=(
                            "Verify transaction context and compare to "
                            "historical patterns"
                        ),
                        confidence=min(1.0, flow.value / (avg_value * 5)),
                        metadata={
                            "value": flow.value,
                            "average": avg_value,
                            "multiplier": flow.value / avg_value,
                        },
                    )
                )

            # Zero-dollar high-volume anomaly.
            if (
                flow.price_per_share == 0.0
                and flow.shares >= self.config["zero_dollar_flag_threshold"]
            ):
                patterns.append(
                    FlowPattern(
                        pattern_type="ZERO_DOLLAR_HIGH_VOLUME",
                        flows=[flow],
                        risk_level=FlowRiskLevel.HIGH,
                        description=(
                            f"Zero-dollar transaction with high volume: "
                            f"{int(flow.shares):,} shares"
                        ),
                        recommendation=(
                            "Verify against compensation records and "
                            "board authorization"
                        ),
                        confidence=min(1.0, flow.shares / 100000),
                        metadata={
                            "shares": flow.shares,
                            "transaction_code": flow.transaction_code,
                        },
                    )
                )

        return patterns

    def analyze(self) -> FlowAnalysisResult:
        """
        Run complete flow analysis.

        Returns:
            FlowAnalysisResult with all detected patterns and risk assessment
        """
        # Detect all pattern types.
        circular_patterns = self.detect_circular_flows()
        enrichment_patterns = self.detect_enrichment_schemes()
        coordinated_patterns = self.detect_coordinated_activity()
        anomalous_patterns = self.detect_anomalous_value_flows()

        all_patterns = (
            circular_patterns
            + enrichment_patterns
            + coordinated_patterns
            + anomalous_patterns
        )

        # Calculate totals.
        total_flows = len(self.flows)
        total_value = sum(f.value for f in self.flows)
        all_entities = set()
        for flow in self.flows:
            all_entities.add(flow.source_entity)
            all_entities.add(flow.target_entity)

        # Calculate risk score.
        risk_score = self._calculate_risk_score(all_patterns)
        risk_level = self._determine_risk_level(risk_score)

        # Generate findings.
        findings = self._generate_findings(all_patterns)
        recommendations = self._generate_recommendations(all_patterns, risk_level)

        return FlowAnalysisResult(
            total_flows=total_flows,
            total_value=total_value,
            entities=list(all_entities),
            patterns=all_patterns,
            risk_score=risk_score,
            risk_level=risk_level,
            findings=findings,
            recommendations=recommendations,
            metadata={
                "analysis_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pattern_counts": {
                    "circular": len(circular_patterns),
                    "enrichment": len(enrichment_patterns),
                    "coordinated": len(coordinated_patterns),
                    "anomalous": len(anomalous_patterns),
                },
            },
        )

    def _calculate_risk_score(self, patterns: List[FlowPattern]) -> float:
        """Calculate overall risk score from detected patterns."""
        if not patterns:
            return 0.0

        # Weight by risk level.
        level_weights = {
            FlowRiskLevel.CRITICAL: 1.0,
            FlowRiskLevel.HIGH: 0.7,
            FlowRiskLevel.MEDIUM: 0.4,
            FlowRiskLevel.LOW: 0.2,
            FlowRiskLevel.INFO: 0.1,
        }

        weighted_sum = sum(
            level_weights.get(p.risk_level, 0.5) * p.confidence for p in patterns
        )

        # Normalize with diminishing returns.
        count_factor = len(patterns) ** 0.5
        raw_score = weighted_sum / count_factor if count_factor > 0 else 0

        return min(raw_score, 1.0)

    def _determine_risk_level(self, score: float) -> FlowRiskLevel:
        """Determine risk level from score."""
        if score >= 0.8:
            return FlowRiskLevel.CRITICAL
        elif score >= 0.6:
            return FlowRiskLevel.HIGH
        elif score >= 0.3:
            return FlowRiskLevel.MEDIUM
        elif score >= 0.1:
            return FlowRiskLevel.LOW
        return FlowRiskLevel.INFO

    def _generate_findings(self, patterns: List[FlowPattern]) -> List[str]:
        """Generate key findings from patterns."""
        findings = []

        # Count by pattern type.
        type_counts: Dict[str, int] = {}
        for p in patterns:
            type_counts[p.pattern_type] = type_counts.get(p.pattern_type, 0) + 1

        for ptype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            findings.append(f"{ptype}: {count} instance(s) detected")

        # Add specific findings for critical patterns.
        critical_patterns = [p for p in patterns if p.risk_level == FlowRiskLevel.CRITICAL]
        for p in critical_patterns[:3]:
            findings.append(f"CRITICAL: {p.description}")

        return findings

    def _generate_recommendations(
        self, patterns: List[FlowPattern], risk_level: FlowRiskLevel
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        if risk_level == FlowRiskLevel.CRITICAL:
            recommendations.append(
                "IMMEDIATE FORENSIC REVIEW REQUIRED - Multiple high-risk patterns detected"
            )
            recommendations.append(
                "Consider engagement of external forensic accountants"
            )
        elif risk_level == FlowRiskLevel.HIGH:
            recommendations.append(
                "PRIORITY INVESTIGATION RECOMMENDED - Significant suspicious patterns"
            )
            recommendations.append(
                "Cross-reference with earnings calendar and material events"
            )

        # Deduplicate pattern recommendations.
        seen_recs = set()
        for p in patterns:
            if p.recommendation not in seen_recs:
                recommendations.append(p.recommendation)
                seen_recs.add(p.recommendation)

        if not recommendations:
            recommendations.append(
                "Continue monitoring - No significant issues detected"
            )

        return recommendations[:10]

    def generate_flow_report(self) -> Dict[str, Any]:
        """
        Generate complete flow analysis report.

        Returns:
            Dictionary containing complete analysis report
        """
        result = self.analyze()

        return {
            "report_metadata": {
                "timestamp": result.metadata.get("analysis_timestamp", ""),
                "module": "FinancialFlowTracer",
                "version": "1.0",
            },
            "summary": {
                "total_flows": result.total_flows,
                "total_value": round(result.total_value, 2),
                "entity_count": len(result.entities),
                "pattern_count": len(result.patterns),
                "risk_score": round(result.risk_score, 3),
                "risk_level": result.risk_level.value,
            },
            "pattern_breakdown": result.metadata.get("pattern_counts", {}),
            "entities": result.entities,
            "findings": result.findings,
            "recommendations": result.recommendations,
            "patterns": [
                {
                    "type": p.pattern_type,
                    "risk_level": p.risk_level.value,
                    "description": p.description,
                    "confidence": round(p.confidence, 2),
                    "metadata": p.metadata,
                }
                for p in result.patterns
            ],
        }


# Module-level convenience functions.
def trace_flows(transactions: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> FlowAnalysisResult:
    """
    Trace financial flows from a list of transactions.

    Args:
        transactions: List of transaction dictionaries
        config: Optional configuration

    Returns:
        FlowAnalysisResult
    """
    tracer = FinancialFlowTracer(config)

    for tx in transactions:
        insider = tx.get("reporting_owner", tx.get("insider", "UNKNOWN"))
        company = tx.get("issuer", tx.get("company", "UNKNOWN"))
        code = tx.get("transaction_code", "")
        shares_str = str(tx.get("shares", tx.get("shares_traded", "0")))
        price_str = str(tx.get("price_per_share", "0"))
        date = tx.get("transaction_date", "")

        try:
            shares = float(shares_str.replace(",", "").replace("$", ""))
        except (ValueError, AttributeError):
            shares = 0.0

        try:
            price = float(price_str.replace(",", "").replace("$", ""))
        except (ValueError, AttributeError):
            price = 0.0

        tracer.add_transaction(
            insider_name=insider,
            company_name=company,
            transaction_code=code,
            shares=shares,
            price_per_share=price,
            transaction_date=date,
            is_acquisition=is_acquisition_flow(code),
        )

    return tracer.analyze()


def trace_filings(
    filings: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Trace financial flows from parsed SEC filings.

    Args:
        filings: List of parsed filing dictionaries
        config: Optional configuration

    Returns:
        Complete flow analysis report
    """
    tracer = FinancialFlowTracer(config)

    for filing in filings:
        tracer.add_transactions_from_filing(filing)

    return tracer.generate_flow_report()


def quick_flow_risk(transactions: List[Dict[str, Any]]) -> str:
    """
    Quick risk assessment for a list of transactions.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        Risk level string
    """
    result = trace_flows(transactions)
    return result.risk_level.value.upper()


def detect_enrichment(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect potential enrichment schemes in transactions.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        List of detected enrichment patterns
    """
    tracer = FinancialFlowTracer()

    for tx in transactions:
        insider = tx.get("reporting_owner", tx.get("insider", "UNKNOWN"))
        company = tx.get("issuer", tx.get("company", "UNKNOWN"))
        code = tx.get("transaction_code", "")
        shares_str = str(tx.get("shares", tx.get("shares_traded", "0")))
        price_str = str(tx.get("price_per_share", "0"))
        date = tx.get("transaction_date", "")

        try:
            shares = float(shares_str.replace(",", "").replace("$", ""))
        except (ValueError, AttributeError):
            shares = 0.0

        try:
            price = float(price_str.replace(",", "").replace("$", ""))
        except (ValueError, AttributeError):
            price = 0.0

        tracer.add_transaction(
            insider_name=insider,
            company_name=company,
            transaction_code=code,
            shares=shares,
            price_per_share=price,
            transaction_date=date,
            is_acquisition=is_acquisition_flow(code),
        )

    patterns = tracer.detect_enrichment_schemes()

    return [
        {
            "type": p.pattern_type,
            "risk_level": p.risk_level.value,
            "description": p.description,
            "recommendation": p.recommendation,
            "metadata": p.metadata,
        }
        for p in patterns
    ]


if __name__ == "__main__":
    print("[FFT] Financial Flow Tracer Module - PowerShell Compatible")
    print("[FFT] Version: 1.0")
    print("[FFT] Status: OPERATIONAL")
    print("[FFT] Capabilities:")
    print("  - Circular flow detection")
    print("  - Enrichment scheme detection")
    print("  - Coordinated activity detection")
    print("  - Anomalous value flow detection")
