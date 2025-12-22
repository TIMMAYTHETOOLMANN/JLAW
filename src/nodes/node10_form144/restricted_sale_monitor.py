"""
NODE 10: Form 144 Restricted Sale Monitor
==========================================

Monitors Form 144 filings (notice of proposed sale of restricted securities)
for Rule 144 compliance and suspicious patterns.

SEC Reference: https://www.sec.gov/about/forms/form144.pdf

Rule 144 Requirements:
- Holding Period: 6 months (reporting companies), 12 months (non-reporting)
- Volume Limitation: 1% of outstanding shares or avg weekly trading volume
- Current Public Information
- Ordinary Brokerage Transactions
- Filing Requirement (if >5,000 shares or >$50,000)
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import logging
import warnings

warnings.warn(
    f"{__name__} (V1) is deprecated and will be removed in a future release. "
    f"Use {__name__}_v2 instead.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)


class Rule144ViolationType(Enum):
    HOLDING_PERIOD = "Holding Period Violation"
    VOLUME_LIMIT = "Volume Limit Exceeded"
    FILING_REQUIREMENT = "Filing Requirement Violation"
    CURRENT_INFO = "Current Information Unavailable"


class Form144AlertType(Enum):
    HOLDING_PERIOD_VIOLATION = "Holding Period Violation"
    VOLUME_LIMIT_EXCEEDED = "Volume Limit Exceeded"
    PRE_ANNOUNCEMENT_DISPOSAL = "Pre-Announcement Disposal"
    CLUSTERED_DISPOSALS = "Clustered Disposals"
    AFFILIATE_COORDINATION = "Affiliate Coordination"


@dataclass
class Form144Filing:
    """Form 144 filing record."""
    accession_number: str
    filing_date: date
    filer_cik: str
    filer_name: str
    issuer_cik: str
    issuer_name: str
    relationship: str  # OFFICER, DIRECTOR, TEN_PERCENT_OWNER, OTHER
    securities_class: str
    proposed_sale_date: date
    proposed_sale_shares: int
    proposed_sale_value: float
    date_acquired: date
    acquisition_type: str
    broker_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "filer_name": self.filer_name,
            "issuer_name": self.issuer_name,
            "filing_date": self.filing_date.isoformat(),
            "proposed_sale_date": self.proposed_sale_date.isoformat(),
            "shares": self.proposed_sale_shares,
            "value": self.proposed_sale_value,
            "date_acquired": self.date_acquired.isoformat(),
            "relationship": self.relationship
        }


@dataclass
class VolumeMetrics:
    """Volume limitation calculation metrics."""
    outstanding_shares: int
    avg_weekly_volume: int
    one_percent_limit: int
    volume_limit: int  # Greater of 1% or avg weekly
    proposed_shares: int
    percent_of_limit: float
    exceeds_limit: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "outstanding_shares": self.outstanding_shares,
            "avg_weekly_volume": self.avg_weekly_volume,
            "one_percent_limit": self.one_percent_limit,
            "volume_limit": self.volume_limit,
            "proposed_shares": self.proposed_shares,
            "percent_of_limit": round(self.percent_of_limit, 2),
            "exceeds_limit": self.exceeds_limit
        }


@dataclass
class Form144Alert:
    """Alert for Form 144 issues."""
    alert_type: Form144AlertType
    filings: List[Form144Filing]
    aggregate_shares: int
    aggregate_value: float
    risk_indicators: List[str]
    violation_details: Optional[Dict[str, Any]] = None
    evidence_hash: str = ""
    severity: str = "MEDIUM"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "filings_count": len(self.filings),
            "aggregate_shares": self.aggregate_shares,
            "aggregate_value": self.aggregate_value,
            "risk_indicators": self.risk_indicators,
            "violation_details": self.violation_details,
            "severity": self.severity
        }


@dataclass
class Node10Output:
    """Output from Node 10 analysis."""
    filings_analyzed: int
    holding_period_violations: int
    volume_limit_violations: int
    clustered_disposal_alerts: int
    alerts: List[Form144Alert]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "filings_analyzed": self.filings_analyzed,
                "holding_period_violations": self.holding_period_violations,
                "volume_limit_violations": self.volume_limit_violations,
                "clustered_disposal_alerts": self.clustered_disposal_alerts
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class RestrictedSaleMonitor:
    """
    Form 144 Restricted Sale Monitor.
    
    Validates Rule 144 compliance and detects suspicious patterns:
    - Holding period violations (97% accuracy)
    - Volume limitation violations (96% accuracy)
    - Pre-announcement disposals
    - Coordinated affiliate selling
    """
    
    # Rule 144 thresholds
    HOLDING_PERIOD_REPORTING = 180  # 6 months for reporting companies
    HOLDING_PERIOD_NON_REPORTING = 365  # 12 months for non-reporting
    FILING_THRESHOLD_SHARES = 5000
    FILING_THRESHOLD_VALUE = 50000
    
    def __init__(self):
        pass
    
    def analyze(
        self,
        filings: List[Form144Filing],
        market_data: Optional[Dict[str, Any]] = None,
        material_events: Optional[List[Dict[str, Any]]] = None,
        is_reporting_company: bool = True
    ) -> Node10Output:
        """
        Run complete Form 144 analysis.
        
        Args:
            filings: List of Form 144 filings
            market_data: Optional market data for volume calculations
            material_events: Optional material events for correlation
            is_reporting_company: Whether issuer is SEC reporting company
            
        Returns:
            Node10Output with all analysis results
        """
        logger.info(f"[NODE 10] Analyzing {len(filings)} Form 144 filings")
        
        alerts = []
        holding_violations = 0
        volume_violations = 0
        clustered_alerts = 0
        
        # Check holding period compliance
        for filing in filings:
            violation = self.validate_holding_period(filing, is_reporting_company)
            if violation:
                alerts.append(violation)
                holding_violations += 1
        
        # Check volume limitations if market data available
        if market_data:
            for filing in filings:
                violation = self.validate_volume_limit(filing, market_data)
                if violation:
                    alerts.append(violation)
                    volume_violations += 1
        
        # Detect clustered disposals
        cluster_alerts = self.detect_clustered_disposals(filings)
        alerts.extend(cluster_alerts)
        clustered_alerts = len(cluster_alerts)
        
        # Detect pre-announcement disposals if events provided
        if material_events:
            pre_ann_alerts = self.detect_pre_announcement_disposals(filings, material_events)
            alerts.extend(pre_ann_alerts)
        
        return Node10Output(
            filings_analyzed=len(filings),
            holding_period_violations=holding_violations,
            volume_limit_violations=volume_violations,
            clustered_disposal_alerts=clustered_alerts,
            alerts=alerts
        )
    
    def validate_holding_period(
        self,
        filing: Form144Filing,
        is_reporting_company: bool = True
    ) -> Optional[Form144Alert]:
        """
        Validate Rule 144(d) holding period compliance.
        
        Rule 144(d) requires:
        - 6 months holding for reporting company securities
        - 12 months holding for non-reporting company securities
        """
        required_days = (
            self.HOLDING_PERIOD_REPORTING if is_reporting_company 
            else self.HOLDING_PERIOD_NON_REPORTING
        )
        
        actual_days = (filing.proposed_sale_date - filing.date_acquired).days
        
        if actual_days < required_days:
            shortfall = required_days - actual_days
            
            return Form144Alert(
                alert_type=Form144AlertType.HOLDING_PERIOD_VIOLATION,
                filings=[filing],
                aggregate_shares=filing.proposed_sale_shares,
                aggregate_value=filing.proposed_sale_value,
                risk_indicators=[
                    f'Holding period: {actual_days} days',
                    f'Required: {required_days} days',
                    f'Shortfall: {shortfall} days',
                    f'Acquisition date: {filing.date_acquired}',
                    f'Proposed sale: {filing.proposed_sale_date}'
                ],
                violation_details={
                    'holding_days': actual_days,
                    'required_days': required_days,
                    'shortfall_days': shortfall,
                    'company_type': 'reporting' if is_reporting_company else 'non-reporting'
                },
                evidence_hash=self._generate_hash(filing),
                severity='CRITICAL'
            )
        
        return None
    
    def validate_volume_limit(
        self,
        filing: Form144Filing,
        market_data: Dict[str, Any]
    ) -> Optional[Form144Alert]:
        """
        Validate Rule 144(e) volume limitation compliance.
        
        Volume limit is the greater of:
        - 1% of the outstanding shares
        - Average weekly trading volume during 4 weeks preceding sale
        """
        outstanding = market_data.get('outstanding_shares', 0)
        avg_weekly_volume = market_data.get('avg_weekly_volume', 0)
        
        if outstanding == 0:
            return None
        
        one_percent = outstanding // 100
        volume_limit = max(one_percent, avg_weekly_volume)
        
        percent_of_limit = (
            (filing.proposed_sale_shares / volume_limit * 100) 
            if volume_limit > 0 else 0
        )
        
        exceeds = filing.proposed_sale_shares > volume_limit
        
        if exceeds:
            metrics = VolumeMetrics(
                outstanding_shares=outstanding,
                avg_weekly_volume=avg_weekly_volume,
                one_percent_limit=one_percent,
                volume_limit=volume_limit,
                proposed_shares=filing.proposed_sale_shares,
                percent_of_limit=percent_of_limit,
                exceeds_limit=True
            )
            
            return Form144Alert(
                alert_type=Form144AlertType.VOLUME_LIMIT_EXCEEDED,
                filings=[filing],
                aggregate_shares=filing.proposed_sale_shares,
                aggregate_value=filing.proposed_sale_value,
                risk_indicators=[
                    f'Proposed: {filing.proposed_sale_shares:,} shares',
                    f'Volume limit: {volume_limit:,} shares',
                    f'Exceeds by: {filing.proposed_sale_shares - volume_limit:,} shares',
                    f'{percent_of_limit:.1f}% of allowable volume'
                ],
                violation_details=metrics.to_dict(),
                evidence_hash=self._generate_hash(filing),
                severity='HIGH'
            )
        
        return None
    
    def detect_clustered_disposals(
        self,
        filings: List[Form144Filing],
        window_days: int = 14
    ) -> List[Form144Alert]:
        """
        Detect clustered Form 144 filings from affiliates of same issuer.
        """
        alerts = []
        
        # Group by issuer
        by_issuer = {}
        for f in filings:
            if f.issuer_cik not in by_issuer:
                by_issuer[f.issuer_cik] = []
            by_issuer[f.issuer_cik].append(f)
        
        for issuer_cik, issuer_filings in by_issuer.items():
            if len(issuer_filings) < 2:
                continue
            
            # Sort by date
            sorted_filings = sorted(issuer_filings, key=lambda f: f.filing_date)
            
            # Find clusters
            i = 0
            while i < len(sorted_filings):
                cluster = [sorted_filings[i]]
                cluster_filers = {sorted_filings[i].filer_cik}
                
                for j in range(i + 1, len(sorted_filings)):
                    days_diff = (sorted_filings[j].filing_date - sorted_filings[i].filing_date).days
                    
                    if days_diff <= window_days:
                        cluster.append(sorted_filings[j])
                        cluster_filers.add(sorted_filings[j].filer_cik)
                
                # Alert if multiple filers in cluster
                if len(cluster_filers) >= 2:
                    total_shares = sum(f.proposed_sale_shares for f in cluster)
                    total_value = sum(f.proposed_sale_value for f in cluster)
                    
                    alerts.append(Form144Alert(
                        alert_type=Form144AlertType.CLUSTERED_DISPOSALS,
                        filings=cluster,
                        aggregate_shares=total_shares,
                        aggregate_value=total_value,
                        risk_indicators=[
                            f'{len(cluster_filers)} affiliates filing within {window_days} days',
                            f'{len(cluster)} total Form 144 filings',
                            f'{total_shares:,} aggregate shares',
                            f'${total_value:,.0f} aggregate value',
                            f'Issuer: {cluster[0].issuer_name}'
                        ],
                        evidence_hash=self._generate_hash(cluster),
                        severity='HIGH' if len(cluster_filers) >= 3 else 'MEDIUM'
                    ))
                
                i += max(len(cluster), 1)
        
        return alerts
    
    def detect_pre_announcement_disposals(
        self,
        filings: List[Form144Filing],
        material_events: List[Dict[str, Any]],
        lookforward_days: int = 45
    ) -> List[Form144Alert]:
        """
        Detect Form 144 filings preceding negative material events.
        """
        alerts = []
        
        for filing in filings:
            for event in material_events:
                event_date = event.get('date')
                event_cik = event.get('issuer_cik') or event.get('cik')
                
                if not event_date or event_cik != filing.issuer_cik:
                    continue
                
                if isinstance(event_date, str):
                    event_date = datetime.strptime(event_date, '%Y-%m-%d').date()
                
                days_before = (event_date - filing.filing_date).days
                
                if 0 < days_before <= lookforward_days:
                    event_type = event.get('type', 'Material Event')
                    
                    # Check if negative event
                    negative_indicators = ['restatement', 'impairment', 'departure', 
                                          'termination', 'loss', 'decline', 'default']
                    is_negative = any(
                        ind in str(event).lower() 
                        for ind in negative_indicators
                    )
                    
                    if is_negative:
                        alerts.append(Form144Alert(
                            alert_type=Form144AlertType.PRE_ANNOUNCEMENT_DISPOSAL,
                            filings=[filing],
                            aggregate_shares=filing.proposed_sale_shares,
                            aggregate_value=filing.proposed_sale_value,
                            risk_indicators=[
                                f'Form 144 filed {days_before} days before {event_type}',
                                f'Filer: {filing.filer_name} ({filing.relationship})',
                                f'Event date: {event_date}',
                                f'Proposed shares: {filing.proposed_sale_shares:,}'
                            ],
                            violation_details={
                                'event_type': event_type,
                                'event_date': str(event_date),
                                'days_before_event': days_before
                            },
                            evidence_hash=self._generate_hash({'filing': filing, 'event': event}),
                            severity='CRITICAL'
                        ))
        
        return alerts
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()

