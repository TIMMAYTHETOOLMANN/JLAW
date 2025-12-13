"""
NODE 10: Form 144 Restricted Sale Monitor v2.0 (FORTIFIED)
===========================================================

Enhanced version with:
- Rule 144(d)(3) tacking provisions (conversion, gift, estate transfers)
- Rule 144(e)(3) affiliate volume aggregation (90-day windows)
- Cross-correlation with Form 4 (Node 1), 13D (Node 8), 8-K (Node 9)
- FINRA electronic filing XML parser

SEC Reference: 17 CFR §230.144
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging

from .tacking_calculator import (
    TackingCalculator,
    SecurityAcquisition,
    TackingAnalysis
)
from .affiliate_aggregator import (
    AffiliateVolumeAggregator,
    AffiliateSale,
    AggregatedVolume,
    VolumeViolation,
    AffiliateRelationship
)
from .finra_parser import FINRAForm144Parser, FINRAForm144Data

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Alert severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Enhanced alert types for Node 10."""
    HOLDING_PERIOD_VIOLATION = "Holding Period Violation"
    VOLUME_LIMIT_EXCEEDED = "Volume Limit Exceeded"
    TACKING_VIOLATION = "Tacking Violation"
    AFFILIATE_COORDINATION = "Affiliate Coordination"
    PRE_ANNOUNCEMENT_DISPOSAL = "Pre-Announcement Disposal"
    CLUSTERED_DISPOSALS = "Clustered Disposals"
    FORM4_CORRELATION = "Form 4 Correlation"
    NODE8_CORRELATION = "13D Filing Correlation"
    NODE9_CORRELATION = "8-K Event Correlation"


@dataclass
class Form144FilingV2:
    """Enhanced Form 144 filing record with tacking and cross-node data."""
    accession_number: str
    filing_date: date
    filer_cik: str
    filer_name: str
    issuer_cik: str
    issuer_name: str
    relationship: str
    securities_class: str
    proposed_sale_date: date
    proposed_sale_shares: int
    proposed_sale_value: float
    date_acquired: date
    acquisition_type: str
    broker_name: Optional[str] = None
    
    # Tacking analysis
    tacking_analysis: Optional[TackingAnalysis] = None
    effective_holding_period_days: Optional[int] = None
    
    # Cross-node correlations
    correlated_form4_trades: List[Dict[str, Any]] = field(default_factory=list)
    correlated_node8_filings: List[Dict[str, Any]] = field(default_factory=list)
    correlated_node9_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "filing_date": self.filing_date.isoformat(),
            "filer": {
                "cik": self.filer_cik,
                "name": self.filer_name
            },
            "issuer": {
                "cik": self.issuer_cik,
                "name": self.issuer_name
            },
            "relationship": self.relationship,
            "securities_class": self.securities_class,
            "proposed_sale": {
                "date": self.proposed_sale_date.isoformat(),
                "shares": self.proposed_sale_shares,
                "value": self.proposed_sale_value
            },
            "acquisition": {
                "date": self.date_acquired.isoformat(),
                "type": self.acquisition_type
            },
            "broker": self.broker_name,
            "tacking_analysis": self.tacking_analysis.to_dict() if self.tacking_analysis else None,
            "effective_holding_period_days": self.effective_holding_period_days,
            "cross_node_correlations": {
                "form4_count": len(self.correlated_form4_trades),
                "node8_count": len(self.correlated_node8_filings),
                "node9_count": len(self.correlated_node9_events)
            }
        }


@dataclass
class Form144AlertV2:
    """Enhanced alert for Form 144 issues with cross-node correlation."""
    alert_type: AlertType
    severity: Severity
    filings: List[Form144FilingV2]
    aggregate_shares: int
    aggregate_value: float
    risk_indicators: List[str]
    
    # Enhanced fields
    tacking_violations: List[Dict[str, Any]] = field(default_factory=list)
    volume_violations: List[VolumeViolation] = field(default_factory=list)
    coordination_score: float = 0.0
    
    # Cross-node correlations
    form4_correlations: List[Dict[str, Any]] = field(default_factory=list)
    node8_correlations: List[Dict[str, Any]] = field(default_factory=list)
    node9_correlations: List[Dict[str, Any]] = field(default_factory=list)
    
    evidence_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "filings_count": len(self.filings),
            "aggregate_volume": {
                "shares": self.aggregate_shares,
                "value": self.aggregate_value
            },
            "risk_indicators": self.risk_indicators,
            "tacking_violations": self.tacking_violations,
            "volume_violations": [v.to_dict() for v in self.volume_violations],
            "coordination_score": round(self.coordination_score, 3),
            "cross_node_correlations": {
                "form4_count": len(self.form4_correlations),
                "node8_count": len(self.node8_correlations),
                "node9_count": len(self.node9_correlations),
                "form4_correlations": self.form4_correlations,
                "node8_correlations": self.node8_correlations,
                "node9_correlations": self.node9_correlations
            },
            "evidence_hash": self.evidence_hash,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Node10OutputV2:
    """Enhanced output from Node 10 v2.0 analysis."""
    filings_analyzed: int
    holding_period_violations: int
    volume_limit_violations: int
    tacking_violations: int
    clustered_disposal_alerts: int
    affiliate_coordination_alerts: int
    cross_node_correlations: int
    alerts: List[Form144AlertV2]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "filings_analyzed": self.filings_analyzed,
                "holding_period_violations": self.holding_period_violations,
                "volume_limit_violations": self.volume_limit_violations,
                "tacking_violations": self.tacking_violations,
                "clustered_disposal_alerts": self.clustered_disposal_alerts,
                "affiliate_coordination_alerts": self.affiliate_coordination_alerts,
                "cross_node_correlations": self.cross_node_correlations
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class RestrictedSaleMonitorV2:
    """
    Form 144 Restricted Sale Monitor v2.0 (FORTIFIED).
    
    Validates Rule 144 compliance with enhanced features:
    - Rule 144(d)(3) tacking provisions
    - Rule 144(e)(3) affiliate volume aggregation
    - Cross-node integration with Form 4, 13D, and 8-K
    - FINRA XML parsing
    """
    
    def __init__(
        self,
        holding_period_reporting: int = 180,
        holding_period_non_reporting: int = 365,
        volume_window_days: int = 90
    ):
        """
        Initialize the monitor.
        
        Args:
            holding_period_reporting: Days for reporting companies (default 180 = 6 months)
            holding_period_non_reporting: Days for non-reporting (default 365 = 12 months)
            volume_window_days: Window for volume aggregation (default 90)
        """
        self.holding_period_reporting = holding_period_reporting
        self.holding_period_non_reporting = holding_period_non_reporting
        self.volume_window_days = volume_window_days
        
        # Initialize sub-components
        self.tacking_calculator = TackingCalculator()
        self.affiliate_aggregator = AffiliateVolumeAggregator(volume_window_days)
        self.finra_parser = FINRAForm144Parser()
        
        self.logger = logger
    
    def analyze(
        self,
        filings: List[Form144FilingV2],
        outstanding_shares: Dict[str, int],
        avg_weekly_volumes: Optional[Dict[str, int]] = None,
        is_reporting_company: Optional[Dict[str, bool]] = None,
        form4_trades: Optional[List[Dict[str, Any]]] = None,
        node8_output: Optional[Any] = None,
        node9_output: Optional[Any] = None
    ) -> Node10OutputV2:
        """
        Comprehensive Form 144 analysis with cross-node correlation.
        
        Args:
            filings: List of Form 144 filings to analyze
            outstanding_shares: Map of issuer_cik -> outstanding shares
            avg_weekly_volumes: Map of issuer_cik -> avg weekly volume (optional)
            is_reporting_company: Map of issuer_cik -> bool (optional)
            form4_trades: Form 4 trades from Node 1 (optional)
            node8_output: Output from Node 8 (optional)
            node9_output: Output from Node 9 (optional)
        
        Returns:
            Node10OutputV2 with comprehensive analysis
        """
        if not filings:
            return Node10OutputV2(
                filings_analyzed=0,
                holding_period_violations=0,
                volume_limit_violations=0,
                tacking_violations=0,
                clustered_disposal_alerts=0,
                affiliate_coordination_alerts=0,
                cross_node_correlations=0,
                alerts=[]
            )
        
        alerts = []
        
        # Step 1: Analyze tacking eligibility for each filing
        self._analyze_tacking_for_filings(filings)
        
        # Step 2: Check holding period violations
        holding_violations = self._detect_holding_period_violations(
            filings,
            is_reporting_company or {}
        )
        alerts.extend(holding_violations)
        
        # Step 3: Check volume limit violations
        volume_violations = self._detect_volume_violations(
            filings,
            outstanding_shares,
            avg_weekly_volumes or {}
        )
        alerts.extend(volume_violations)
        
        # Step 4: Detect affiliate coordination
        coordination_alerts = self._detect_affiliate_coordination(filings)
        alerts.extend(coordination_alerts)
        
        # Step 5: Cross-correlate with other nodes
        if form4_trades:
            self._correlate_with_form4(filings, form4_trades)
            form4_alerts = self._detect_form4_correlations(filings)
            alerts.extend(form4_alerts)
        
        if node8_output:
            self._correlate_with_node8(filings, node8_output)
            node8_alerts = self._detect_node8_correlations(filings)
            alerts.extend(node8_alerts)
        
        if node9_output:
            self._correlate_with_node9(filings, node9_output)
            node9_alerts = self._detect_node9_correlations(filings)
            alerts.extend(node9_alerts)
        
        # Count violations
        holding_count = sum(1 for a in alerts if a.alert_type == AlertType.HOLDING_PERIOD_VIOLATION)
        volume_count = sum(1 for a in alerts if a.alert_type == AlertType.VOLUME_LIMIT_EXCEEDED)
        tacking_count = sum(1 for a in alerts if a.alert_type == AlertType.TACKING_VIOLATION)
        clustered_count = sum(1 for a in alerts if a.alert_type == AlertType.CLUSTERED_DISPOSALS)
        coordination_count = sum(1 for a in alerts if a.alert_type == AlertType.AFFILIATE_COORDINATION)
        cross_node_count = sum(
            1 for a in alerts
            if a.alert_type in (AlertType.FORM4_CORRELATION, AlertType.NODE8_CORRELATION, AlertType.NODE9_CORRELATION)
        )
        
        return Node10OutputV2(
            filings_analyzed=len(filings),
            holding_period_violations=holding_count,
            volume_limit_violations=volume_count,
            tacking_violations=tacking_count,
            clustered_disposal_alerts=clustered_count,
            affiliate_coordination_alerts=coordination_count,
            cross_node_correlations=cross_node_count,
            alerts=alerts
        )
    
    def _analyze_tacking_for_filings(self, filings: List[Form144FilingV2]) -> None:
        """Analyze tacking eligibility for all filings."""
        for filing in filings:
            acquisition = SecurityAcquisition(
                acquisition_date=filing.date_acquired,
                acquisition_type=filing.acquisition_type,
                shares=filing.proposed_sale_shares,
                original_acquisition_date=None  # Would need to be provided
            )
            
            tacking_analysis = self.tacking_calculator.analyze_tacking_eligibility(
                acquisition,
                as_of_date=filing.proposed_sale_date
            )
            
            filing.tacking_analysis = tacking_analysis
            filing.effective_holding_period_days = tacking_analysis.holding_period_days
    
    def _detect_holding_period_violations(
        self,
        filings: List[Form144FilingV2],
        is_reporting_company: Dict[str, bool]
    ) -> List[Form144AlertV2]:
        """Detect holding period violations."""
        violations = []
        
        for filing in filings:
            # Determine required holding period
            is_reporting = is_reporting_company.get(filing.issuer_cik, True)
            required_period = self.holding_period_reporting if is_reporting else self.holding_period_non_reporting
            
            # Use effective holding period if tacking was analyzed
            actual_period = filing.effective_holding_period_days or 0
            
            if actual_period < required_period:
                risk_indicators = [
                    f"Holding period: {actual_period} days < {required_period} days required",
                    f"Issuer type: {'Reporting' if is_reporting else 'Non-reporting'}"
                ]
                
                if filing.tacking_analysis and not filing.tacking_analysis.eligible_for_tacking:
                    risk_indicators.append(f"Tacking not available: {filing.tacking_analysis.tacking_type.value}")
                
                violations.append(Form144AlertV2(
                    alert_type=AlertType.HOLDING_PERIOD_VIOLATION,
                    severity=Severity.HIGH,
                    filings=[filing],
                    aggregate_shares=filing.proposed_sale_shares,
                    aggregate_value=filing.proposed_sale_value,
                    risk_indicators=risk_indicators,
                    evidence_hash=self._generate_evidence_hash([filing])
                ))
        
        return violations
    
    def _detect_volume_violations(
        self,
        filings: List[Form144FilingV2],
        outstanding_shares: Dict[str, int],
        avg_weekly_volumes: Dict[str, int]
    ) -> List[Form144AlertV2]:
        """Detect volume limit violations using affiliate aggregation."""
        violations = []
        
        # Convert filings to AffiliateSale objects
        affiliate_sales = []
        for filing in filings:
            # Map relationship to AffiliateRelationship enum
            if "OFFICER" in filing.relationship.upper():
                relationship = AffiliateRelationship.OFFICER
            elif "DIRECTOR" in filing.relationship.upper():
                relationship = AffiliateRelationship.DIRECTOR
            elif "TEN" in filing.relationship.upper() and "PERCENT" in filing.relationship.upper():
                relationship = AffiliateRelationship.TEN_PERCENT_OWNER
            else:
                relationship = AffiliateRelationship.CONTROL_PERSON
            
            affiliate_sales.append(AffiliateSale(
                sale_date=filing.proposed_sale_date,
                affiliate_cik=filing.filer_cik,
                affiliate_name=filing.filer_name,
                relationship=relationship,
                shares_sold=filing.proposed_sale_shares,
                sale_value=filing.proposed_sale_value,
                form_144_accession=filing.accession_number,
                issuer_cik=filing.issuer_cik,
                issuer_name=filing.issuer_name
            ))
        
        # Aggregate by issuer
        aggregated_by_issuer = self.affiliate_aggregator.aggregate_sales_by_issuer(affiliate_sales)
        
        # Detect violations for each issuer
        for issuer_cik, aggregated_volumes in aggregated_by_issuer.items():
            issuer_outstanding = outstanding_shares.get(issuer_cik, 0)
            issuer_avg_volume = avg_weekly_volumes.get(issuer_cik)
            
            if issuer_outstanding == 0:
                continue
            
            volume_violations_list = self.affiliate_aggregator.detect_volume_violations(
                aggregated_volumes,
                issuer_outstanding,
                issuer_avg_volume
            )
            
            # Convert to Form144AlertV2 format
            for vol_violation in volume_violations_list:
                # Find all filings in this window
                window_filings = [
                    f for f in filings
                    if f.issuer_cik == issuer_cik
                    and vol_violation.window_start <= f.proposed_sale_date <= vol_violation.window_end
                ]
                
                violations.append(Form144AlertV2(
                    alert_type=AlertType.VOLUME_LIMIT_EXCEEDED,
                    severity=Severity[vol_violation.violation_severity],
                    filings=window_filings,
                    aggregate_shares=vol_violation.aggregated_shares,
                    aggregate_value=sum(f.proposed_sale_value for f in window_filings),
                    risk_indicators=[
                        f"Aggregate volume: {vol_violation.aggregated_shares:,} shares",
                        f"Volume limit: {vol_violation.volume_limit:,} shares",
                        f"Excess: {vol_violation.excess_shares:,} shares",
                        f"Percent of outstanding: {vol_violation.percent_of_outstanding:.2f}%",
                        f"Affiliates involved: {len(vol_violation.involved_affiliates)}"
                    ],
                    volume_violations=[vol_violation],
                    evidence_hash=self._generate_evidence_hash(window_filings)
                ))
        
        return violations
    
    def _detect_affiliate_coordination(
        self,
        filings: List[Form144FilingV2]
    ) -> List[Form144AlertV2]:
        """Detect potential affiliate coordination (acting in concert)."""
        alerts = []
        
        # Convert to AffiliateSale objects
        affiliate_sales = []
        for filing in filings:
            if "OFFICER" in filing.relationship.upper():
                relationship = AffiliateRelationship.OFFICER
            elif "DIRECTOR" in filing.relationship.upper():
                relationship = AffiliateRelationship.DIRECTOR
            else:
                relationship = AffiliateRelationship.CONTROL_PERSON
            
            affiliate_sales.append(AffiliateSale(
                sale_date=filing.proposed_sale_date,
                affiliate_cik=filing.filer_cik,
                affiliate_name=filing.filer_name,
                relationship=relationship,
                shares_sold=filing.proposed_sale_shares,
                sale_value=filing.proposed_sale_value,
                form_144_accession=filing.accession_number,
                issuer_cik=filing.issuer_cik,
                issuer_name=filing.issuer_name
            ))
        
        # Identify coordinated groups
        coordinated_groups = self.affiliate_aggregator.identify_acting_in_concert(
            affiliate_sales,
            temporal_threshold_days=7,
            min_participants=2
        )
        
        # Create alerts for each group
        for group in coordinated_groups:
            group_filings = [
                f for f in filings
                if f.filer_cik in group['affiliate_ciks']
                and group['window_start'] <= f.proposed_sale_date <= group['window_end']
            ]
            
            # Calculate coordination score (0.0-1.0)
            # Based on temporal clustering and participant count
            days_span = (group['window_end'] - group['window_start']).days
            coordination_score = 1.0 - (days_span / 30.0)  # Tighter clustering = higher score
            coordination_score *= min(1.0, group['participant_count'] / 5.0)  # More participants = higher score
            
            alerts.append(Form144AlertV2(
                alert_type=AlertType.AFFILIATE_COORDINATION,
                severity=Severity.HIGH if coordination_score > 0.7 else Severity.MEDIUM,
                filings=group_filings,
                aggregate_shares=group['total_shares'],
                aggregate_value=group['total_value'],
                risk_indicators=[
                    f"Coordinated sales: {group['sale_count']} filings",
                    f"Participants: {group['participant_count']} affiliates",
                    f"Temporal window: {group['window_days']} days",
                    f"Coordination score: {coordination_score:.2f}"
                ],
                coordination_score=coordination_score,
                evidence_hash=self._generate_evidence_hash(group_filings)
            ))
        
        return alerts
    
    def _correlate_with_form4(
        self,
        filings: List[Form144FilingV2],
        form4_trades: List[Dict[str, Any]]
    ) -> None:
        """Correlate Form 144 filings with Form 4 trades."""
        for filing in filings:
            # Find Form 4 trades by same filer around same time
            correlated_trades = []
            
            for trade in form4_trades:
                if trade.get('filer_cik') == filing.filer_cik:
                    trade_date = trade.get('transaction_date')
                    if trade_date:
                        # Check if within reasonable window (e.g., 30 days)
                        if isinstance(trade_date, str):
                            trade_date = datetime.fromisoformat(trade_date.split('T')[0]).date()
                        
                        days_diff = abs((filing.proposed_sale_date - trade_date).days)
                        if days_diff <= 30:
                            correlated_trades.append({
                                'transaction_date': trade_date.isoformat(),
                                'transaction_type': trade.get('transaction_type'),
                                'shares': trade.get('shares'),
                                'days_from_form144': days_diff
                            })
            
            filing.correlated_form4_trades = correlated_trades
    
    def _correlate_with_node8(
        self,
        filings: List[Form144FilingV2],
        node8_output: Any
    ) -> None:
        """Correlate Form 144 filings with 13D/13G filings."""
        if not node8_output or not hasattr(node8_output, 'alerts'):
            return
        
        for filing in filings:
            correlated_filings = []
            
            for alert in node8_output.alerts:
                # Check if issuer matches
                if hasattr(alert, 'issuer_cik') and alert.issuer_cik == filing.issuer_cik:
                    correlated_filings.append({
                        'alert_type': alert.alert_type.value if hasattr(alert.alert_type, 'value') else str(alert.alert_type),
                        'ownership_percent': getattr(alert, 'aggregate_ownership', 0),
                        'filing_date': getattr(alert, 'filing_date', '').isoformat() if hasattr(getattr(alert, 'filing_date', None), 'isoformat') else ''
                    })
            
            filing.correlated_node8_filings = correlated_filings
    
    def _correlate_with_node9(
        self,
        filings: List[Form144FilingV2],
        node9_output: Any
    ) -> None:
        """Correlate Form 144 filings with 8-K material events."""
        if not node9_output or not hasattr(node9_output, 'events'):
            return
        
        events = node9_output.events if hasattr(node9_output, 'events') else []
        
        for filing in filings:
            correlated_events = []
            
            for event in events:
                # Check if issuer matches
                event_cik = event.get('issuer_cik') if isinstance(event, dict) else getattr(event, 'issuer_cik', None)
                event_date = event.get('event_date') if isinstance(event, dict) else getattr(event, 'event_date', None)
                
                if event_cik == filing.issuer_cik and event_date:
                    if isinstance(event_date, str):
                        event_date = datetime.fromisoformat(event_date.split('T')[0]).date()
                    
                    # Check if Form 144 was filed shortly after 8-K event
                    days_after = (filing.proposed_sale_date - event_date).days
                    
                    if 0 <= days_after <= 30:  # Sold within 30 days after event
                        correlated_events.append({
                            'event_date': event_date.isoformat(),
                            'event_type': event.get('event_type') if isinstance(event, dict) else getattr(event, 'event_type', ''),
                            'days_after_event': days_after
                        })
            
            filing.correlated_node9_events = correlated_events
    
    def _detect_form4_correlations(
        self,
        filings: List[Form144FilingV2]
    ) -> List[Form144AlertV2]:
        """Detect suspicious Form 144/Form 4 correlations."""
        alerts = []
        
        for filing in filings:
            if filing.correlated_form4_trades:
                alerts.append(Form144AlertV2(
                    alert_type=AlertType.FORM4_CORRELATION,
                    severity=Severity.MEDIUM,
                    filings=[filing],
                    aggregate_shares=filing.proposed_sale_shares,
                    aggregate_value=filing.proposed_sale_value,
                    risk_indicators=[
                        f"Form 4 trades found: {len(filing.correlated_form4_trades)}",
                        "Potential coordination between Form 144 and Form 4 activity"
                    ],
                    form4_correlations=filing.correlated_form4_trades,
                    evidence_hash=self._generate_evidence_hash([filing])
                ))
        
        return alerts
    
    def _detect_node8_correlations(
        self,
        filings: List[Form144FilingV2]
    ) -> List[Form144AlertV2]:
        """Detect Form 144 correlations with 13D/13G filings."""
        alerts = []
        
        for filing in filings:
            if filing.correlated_node8_filings:
                alerts.append(Form144AlertV2(
                    alert_type=AlertType.NODE8_CORRELATION,
                    severity=Severity.HIGH,
                    filings=[filing],
                    aggregate_shares=filing.proposed_sale_shares,
                    aggregate_value=filing.proposed_sale_value,
                    risk_indicators=[
                        f"13D/13G filings found: {len(filing.correlated_node8_filings)}",
                        "Potential activist activity correlation"
                    ],
                    node8_correlations=filing.correlated_node8_filings,
                    evidence_hash=self._generate_evidence_hash([filing])
                ))
        
        return alerts
    
    def _detect_node9_correlations(
        self,
        filings: List[Form144FilingV2]
    ) -> List[Form144AlertV2]:
        """Detect Form 144 filings after material events."""
        alerts = []
        
        for filing in filings:
            if filing.correlated_node9_events:
                alerts.append(Form144AlertV2(
                    alert_type=AlertType.NODE9_CORRELATION,
                    severity=Severity.HIGH,
                    filings=[filing],
                    aggregate_shares=filing.proposed_sale_shares,
                    aggregate_value=filing.proposed_sale_value,
                    risk_indicators=[
                        f"Material events found: {len(filing.correlated_node9_events)}",
                        "Potential insider knowledge of upcoming events"
                    ],
                    node9_correlations=filing.correlated_node9_events,
                    evidence_hash=self._generate_evidence_hash([filing])
                ))
        
        return alerts
    
    def _generate_evidence_hash(self, filings: List[Form144FilingV2]) -> str:
        """Generate SHA-256 hash for evidence chain."""
        content = "|".join(
            f"{f.accession_number}:{f.filing_date}:{f.filer_cik}:{f.proposed_sale_shares}"
            for f in filings
        )
        return hashlib.sha256(content.encode()).hexdigest()
    
    def parse_finra_xml(self, xml_content: str) -> Optional[FINRAForm144Data]:
        """
        Parse FINRA electronic Form 144 XML filing.
        
        Args:
            xml_content: XML string content
        
        Returns:
            FINRAForm144Data object or None if parsing fails
        """
        return self.finra_parser.parse_xml(xml_content)
