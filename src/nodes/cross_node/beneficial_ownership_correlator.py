"""
Beneficial Ownership Correlator
================================

Cross-node intelligence synthesis for beneficial ownership change detection.

Correlation matrix:
- Form 4 (Node 1) + 13D/13G (Node 8) = Ownership threshold breach detection
- Form 4 (Node 1) + 13F (Node 7) = Insider vs institutional divergence
- Form 4 (Node 1) + 8-K (Node 9) = Material event correlation
- Form 4 (Node 1) + Form 144 (Node 10) = Restricted sale intent
- Form 4 (Node 1) + DEF 14A (Node 2) = Compensation verification

Statutory framework:
- 15 USC §78j(b) / Rule 10b-5: Gift timing manipulation
- 15 USC §78m(d): Beneficial ownership misreporting
- 15 USC §78p(b): Short-swing profit via gifts (Section 16(b))
- 17 CFR §229.402: Undisclosed compensation (Regulation S-K Item 402)
- 17 CFR §229.404: Related party transactions (Regulation S-K Item 404)
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OwnershipAlertType(Enum):
    """Types of beneficial ownership correlation alerts."""
    THRESHOLD_BREACH = "Ownership Threshold Breach Detection"
    INSIDER_INSTITUTIONAL_DIVERGENCE = "Insider vs Institutional Movement Divergence"
    MATERIAL_EVENT_CORRELATION = "Material Event Timing Correlation"
    RESTRICTED_SALE_INTENT = "Restricted Sale Intent Correlation"
    COMPENSATION_MISMATCH = "Compensation Verification Mismatch"
    INFORMATION_ASYMMETRY = "Potential Information Asymmetry"
    OWNERSHIP_RESTRUCTURING = "Beneficial Ownership Restructuring"


class OwnershipSeverity(Enum):
    """Severity levels for ownership alerts."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AsymmetryAlert:
    """Alert for potential information asymmetry between insiders and institutions."""
    alert_type: OwnershipAlertType
    severity: OwnershipSeverity
    insider_action: str
    institutional_action: str
    temporal_gap_days: int
    evidence_summary: str
    statutory_references: List[str] = field(default_factory=list)
    risk_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "insider_action": self.insider_action,
            "institutional_action": self.institutional_action,
            "temporal_gap_days": self.temporal_gap_days,
            "evidence_summary": self.evidence_summary,
            "statutory_references": self.statutory_references,
            "risk_score": round(self.risk_score, 3),
        }


@dataclass
class OwnershipCorrelationAlert:
    """Unified alert from beneficial ownership correlation analysis."""
    alert_type: OwnershipAlertType
    severity: OwnershipSeverity
    company_cik: str
    company_name: str
    source_nodes: List[int]
    evidence_summary: str
    statutory_references: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "company_cik": self.company_cik,
            "company_name": self.company_name,
            "source_nodes": self.source_nodes,
            "evidence_summary": self.evidence_summary,
            "statutory_references": self.statutory_references,
            "risk_score": round(self.risk_score, 3),
            "details": self.details,
        }


@dataclass
class OwnershipCorrelationReport:
    """Comprehensive ownership change correlation report."""
    company_cik: str
    company_name: str
    analysis_start: date
    analysis_end: date
    alerts: List[OwnershipCorrelationAlert] = field(default_factory=list)
    asymmetry_alerts: List[AsymmetryAlert] = field(default_factory=list)
    total_correlations: int = 0
    aggregate_risk_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": {
                "cik": self.company_cik,
                "name": self.company_name,
            },
            "analysis_period": {
                "start": self.analysis_start.isoformat(),
                "end": self.analysis_end.isoformat(),
            },
            "total_correlations": self.total_correlations,
            "aggregate_risk_score": round(self.aggregate_risk_score, 3),
            "alerts": [a.to_dict() for a in self.alerts],
            "asymmetry_alerts": [a.to_dict() for a in self.asymmetry_alerts],
            "timestamp": self.timestamp.isoformat(),
        }


class BeneficialOwnershipCorrelator:
    """
    Synthesize intelligence across nodes for ownership change detection.

    Form 4 (Node 1) + 13D/13G (Node 8) = Threshold breach detection
    Form 4 (Node 1) + 13F (Node 7) = Insider vs institutional divergence
    Form 4 (Node 1) + 8-K (Node 9) = Material event correlation
    Form 4 (Node 1) + Form 144 (Node 10) = Restricted sale intent
    Form 4 (Node 1) + DEF 14A (Node 2) = Compensation verification
    """

    # Temporal windows for correlation (in days)
    THRESHOLD_BREACH_WINDOW = 30
    MATERIAL_EVENT_WINDOW = 30
    DIVERGENCE_WINDOW = 90
    RESTRICTED_SALE_WINDOW = 60

    # Ownership threshold for 13D filing requirement (5%)
    BENEFICIAL_OWNERSHIP_THRESHOLD = 5.0

    def correlate_ownership_changes(
        self,
        cik: str,
        company_name: str,
        date_range: Tuple[date, date],
        insider_trades: Optional[List[Dict[str, Any]]] = None,
        ownership_filings: Optional[List[Dict[str, Any]]] = None,
        institutional_holdings: Optional[List[Dict[str, Any]]] = None,
        material_events: Optional[List[Dict[str, Any]]] = None,
        restricted_sales: Optional[List[Dict[str, Any]]] = None,
        compensation_data: Optional[Dict[str, Any]] = None,
    ) -> OwnershipCorrelationReport:
        """
        Generate comprehensive ownership change analysis.

        Args:
            cik: Company CIK number
            company_name: Company name
            date_range: (start_date, end_date) for analysis
            insider_trades: Form 4 transactions (Node 1)
            ownership_filings: 13D/13G filings (Node 8)
            institutional_holdings: 13F holdings (Node 7)
            material_events: 8-K events (Node 9)
            restricted_sales: Form 144 filings (Node 10)
            compensation_data: DEF 14A data (Node 2)

        Returns:
            OwnershipCorrelationReport
        """
        alerts: List[OwnershipCorrelationAlert] = []
        asymmetry_alerts: List[AsymmetryAlert] = []

        # Node 1 + Node 8: Threshold breach detection
        if insider_trades and ownership_filings:
            alerts.extend(self._correlate_threshold_breaches(
                cik, company_name, insider_trades, ownership_filings
            ))

        # Node 1 + Node 7: Insider vs institutional divergence
        if insider_trades and institutional_holdings:
            divergence = self.detect_information_asymmetry(
                insider_trades, institutional_holdings
            )
            asymmetry_alerts.extend(divergence)

        # Node 1 + Node 9: Material event correlation
        if insider_trades and material_events:
            alerts.extend(self._correlate_material_events(
                cik, company_name, insider_trades, material_events
            ))

        # Node 1 + Node 10: Restricted sale intent
        if insider_trades and restricted_sales:
            alerts.extend(self._correlate_restricted_sales(
                cik, company_name, insider_trades, restricted_sales
            ))

        # Node 1 + Node 2: Compensation verification
        if insider_trades and compensation_data:
            alerts.extend(self._verify_compensation(
                cik, company_name, insider_trades, compensation_data
            ))

        total = len(alerts) + len(asymmetry_alerts)
        all_scores = [a.risk_score for a in alerts] + [a.risk_score for a in asymmetry_alerts]
        agg_risk = sum(all_scores) / len(all_scores) if all_scores else 0.0

        return OwnershipCorrelationReport(
            company_cik=cik,
            company_name=company_name,
            analysis_start=date_range[0],
            analysis_end=date_range[1],
            alerts=alerts,
            asymmetry_alerts=asymmetry_alerts,
            total_correlations=total,
            aggregate_risk_score=min(agg_risk, 1.0),
        )

    def detect_information_asymmetry(
        self,
        insider_trades: List[Dict[str, Any]],
        institutional_holdings: List[Dict[str, Any]],
    ) -> List[AsymmetryAlert]:
        """
        Flag potential MNPI exploitation patterns.

        Detects insider dispositions preceding institutional exits,
        which may indicate information asymmetry.

        Args:
            insider_trades: Form 4 transactions
            institutional_holdings: 13F quarterly holdings changes

        Returns:
            List of AsymmetryAlert
        """
        alerts: List[AsymmetryAlert] = []

        # Identify insider selling periods
        insider_sales = [
            t for t in insider_trades
            if t.get('acquired_disposed', '').upper() == 'D'
            or t.get('transaction_code', '').upper() == 'S'
        ]

        if not insider_sales or not institutional_holdings:
            return alerts

        for sale in insider_sales:
            sale_date = self._parse_date(sale.get('transaction_date'))
            if not sale_date:
                continue

            for holding in institutional_holdings:
                change_date = self._parse_date(
                    holding.get('reporting_period', holding.get('quarter_end'))
                )
                if not change_date:
                    continue

                pct_change = holding.get('percent_change', holding.get('quarter_over_quarter_change', 0))
                if pct_change is None:
                    continue

                days_diff = (change_date - sale_date).days

                # Insider sold BEFORE institutional exit
                if 0 < days_diff <= self.DIVERGENCE_WINDOW and float(pct_change) < -10.0:
                    institution = holding.get('institution_name', 'Unknown institution')
                    alerts.append(AsymmetryAlert(
                        alert_type=OwnershipAlertType.INFORMATION_ASYMMETRY,
                        severity=OwnershipSeverity.CRITICAL if days_diff <= 30 else OwnershipSeverity.HIGH,
                        insider_action=f"Sale of {sale.get('shares', 0):,.0f} shares on {sale_date}",
                        institutional_action=(
                            f"{institution} reduced position by {abs(float(pct_change)):.1f}% "
                            f"in quarter ending {change_date}"
                        ),
                        temporal_gap_days=days_diff,
                        evidence_summary=(
                            f"Insider disposition preceded institutional exit by {days_diff} days - "
                            f"potential MNPI exploitation"
                        ),
                        statutory_references=[
                            "15 USC §78j(b) (Rule 10b-5)",
                            "17 CFR §240.10b-5",
                        ],
                        risk_score=min(1.0, 0.6 + (1.0 - days_diff / self.DIVERGENCE_WINDOW) * 0.4),
                    ))

        logger.info(
            f"Detected {len(alerts)} information asymmetry alerts "
            f"from {len(insider_sales)} insider sales and "
            f"{len(institutional_holdings)} institutional holdings changes"
        )
        return alerts

    def _correlate_threshold_breaches(
        self,
        cik: str,
        company_name: str,
        insider_trades: List[Dict[str, Any]],
        ownership_filings: List[Dict[str, Any]],
    ) -> List[OwnershipCorrelationAlert]:
        """Detect ownership threshold breaches correlated with insider trades."""
        alerts: List[OwnershipCorrelationAlert] = []

        for filing in ownership_filings:
            pct = filing.get('percent_owned', 0)
            prev_pct = filing.get('previous_ownership', 0)
            filing_date = self._parse_date(filing.get('filing_date'))

            if not filing_date:
                continue

            # Detect threshold crossing
            crossed_threshold = (
                (prev_pct < self.BENEFICIAL_OWNERSHIP_THRESHOLD <= pct) or
                (pct < self.BENEFICIAL_OWNERSHIP_THRESHOLD <= prev_pct)
            )

            if not crossed_threshold:
                continue

            # Find correlated insider trades within window
            correlated = []
            for trade in insider_trades:
                trade_date = self._parse_date(trade.get('transaction_date'))
                if trade_date and abs((trade_date - filing_date).days) <= self.THRESHOLD_BREACH_WINDOW:
                    correlated.append(trade)

            if correlated:
                filer = filing.get('filer_name', 'Unknown')
                direction = "above" if pct >= self.BENEFICIAL_OWNERSHIP_THRESHOLD else "below"
                alerts.append(OwnershipCorrelationAlert(
                    alert_type=OwnershipAlertType.THRESHOLD_BREACH,
                    severity=OwnershipSeverity.HIGH,
                    company_cik=cik,
                    company_name=company_name,
                    source_nodes=[1, 8],
                    evidence_summary=(
                        f"{filer} crossed {self.BENEFICIAL_OWNERSHIP_THRESHOLD}% threshold "
                        f"({direction}) with {len(correlated)} correlated insider trades"
                    ),
                    statutory_references=[
                        "15 USC §78m(d) (Schedule 13D requirements)",
                        "15 USC §78p(b) (Section 16(b) disgorgement)",
                    ],
                    risk_score=0.7,
                    details={
                        "filer": filer,
                        "percent_owned": pct,
                        "previous_ownership": prev_pct,
                        "correlated_trade_count": len(correlated),
                    },
                ))

        return alerts

    def _correlate_material_events(
        self,
        cik: str,
        company_name: str,
        insider_trades: List[Dict[str, Any]],
        material_events: List[Dict[str, Any]],
    ) -> List[OwnershipCorrelationAlert]:
        """Correlate insider trades with material events."""
        alerts: List[OwnershipCorrelationAlert] = []

        for event in material_events:
            event_date = self._parse_date(event.get('event_date', event.get('filing_date')))
            if not event_date:
                continue

            pre_event_trades = []
            for trade in insider_trades:
                trade_date = self._parse_date(trade.get('transaction_date'))
                if not trade_date:
                    continue
                days_before = (event_date - trade_date).days
                if 0 < days_before <= self.MATERIAL_EVENT_WINDOW:
                    pre_event_trades.append((trade, days_before))

            if pre_event_trades:
                event_type = event.get('event_type', 'Unknown event')
                alerts.append(OwnershipCorrelationAlert(
                    alert_type=OwnershipAlertType.MATERIAL_EVENT_CORRELATION,
                    severity=OwnershipSeverity.CRITICAL,
                    company_cik=cik,
                    company_name=company_name,
                    source_nodes=[1, 9],
                    evidence_summary=(
                        f"{len(pre_event_trades)} insider trades within "
                        f"{self.MATERIAL_EVENT_WINDOW} days before {event_type}"
                    ),
                    statutory_references=[
                        "15 USC §78j(b) (Rule 10b-5)",
                        "17 CFR §240.10b-5",
                        "17 CFR §240.10b5-1",
                    ],
                    risk_score=0.85,
                    details={
                        "event_type": event_type,
                        "event_date": event_date.isoformat(),
                        "pre_event_trade_count": len(pre_event_trades),
                        "closest_trade_days": min(d for _, d in pre_event_trades),
                    },
                ))

        return alerts

    def _correlate_restricted_sales(
        self,
        cik: str,
        company_name: str,
        insider_trades: List[Dict[str, Any]],
        restricted_sales: List[Dict[str, Any]],
    ) -> List[OwnershipCorrelationAlert]:
        """Correlate Form 4 trades with Form 144 restricted sale intent."""
        alerts: List[OwnershipCorrelationAlert] = []

        for sale_intent in restricted_sales:
            intent_date = self._parse_date(sale_intent.get('filing_date'))
            if not intent_date:
                continue

            # Find Form 4 trades following Form 144 filing
            following_trades = []
            for trade in insider_trades:
                trade_date = self._parse_date(trade.get('transaction_date'))
                if not trade_date:
                    continue
                days_after = (trade_date - intent_date).days
                if 0 <= days_after <= self.RESTRICTED_SALE_WINDOW:
                    following_trades.append(trade)

            if following_trades:
                filer = sale_intent.get('filer_name', 'Unknown')
                alerts.append(OwnershipCorrelationAlert(
                    alert_type=OwnershipAlertType.RESTRICTED_SALE_INTENT,
                    severity=OwnershipSeverity.MEDIUM,
                    company_cik=cik,
                    company_name=company_name,
                    source_nodes=[1, 10],
                    evidence_summary=(
                        f"Form 144 intent by {filer} followed by "
                        f"{len(following_trades)} Form 4 trades within "
                        f"{self.RESTRICTED_SALE_WINDOW} days"
                    ),
                    statutory_references=["17 CFR §230.144 (Rule 144)"],
                    risk_score=0.5,
                    details={
                        "filer": filer,
                        "intent_date": intent_date.isoformat(),
                        "following_trade_count": len(following_trades),
                    },
                ))

        return alerts

    def _verify_compensation(
        self,
        cik: str,
        company_name: str,
        insider_trades: List[Dict[str, Any]],
        compensation_data: Dict[str, Any],
    ) -> List[OwnershipCorrelationAlert]:
        """Cross-reference insider transactions with DEF 14A compensation disclosures."""
        alerts: List[OwnershipCorrelationAlert] = []

        disclosed_awards = compensation_data.get('stock_awards', [])
        disclosed_names = {
            a.get('executive_name', '').lower()
            for a in disclosed_awards
            if isinstance(a, dict)
        }

        # Find $0 / award transactions not matching proxy disclosures
        award_codes = {'A', 'I', 'M'}
        undisclosed = []
        for trade in insider_trades:
            code = trade.get('transaction_code', '').upper()
            price = trade.get('price_per_share', 1)
            owner = trade.get('owner_name', '').lower()

            if code in award_codes and float(price) == 0.0:
                if owner and owner not in disclosed_names:
                    undisclosed.append(trade)

        if undisclosed:
            alerts.append(OwnershipCorrelationAlert(
                alert_type=OwnershipAlertType.COMPENSATION_MISMATCH,
                severity=OwnershipSeverity.HIGH,
                company_cik=cik,
                company_name=company_name,
                source_nodes=[1, 2],
                evidence_summary=(
                    f"{len(undisclosed)} insider award transactions at $0 "
                    f"not matched in DEF 14A proxy disclosures"
                ),
                statutory_references=[
                    "17 CFR §229.402 (Regulation S-K Item 402)",
                    "17 CFR §229.404 (Regulation S-K Item 404)",
                ],
                risk_score=0.75,
                details={"undisclosed_count": len(undisclosed)},
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
            except ValueError as e:
                logger.debug(f"Failed to parse date string '{val}': {e}")
                return None
        return None
