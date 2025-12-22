"""
NODE 9: 8-K Material Event Correlator
=====================================

Correlates material events disclosed in 8-K filings with:
- Pre-announcement insider trading patterns
- Institutional positioning changes
- Price and volume anomalies
- Disclosure timing relative to market hours

SEC Reference: https://www.sec.gov/about/forms/form8-k.pdf
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
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


# SEC 8-K Item reference codes
MATERIAL_EVENT_ITEMS = {
    # Section 1 - Business Operations
    '1.01': 'Entry into Material Definitive Agreement',
    '1.02': 'Termination of Material Definitive Agreement',
    '1.03': 'Bankruptcy or Receivership',
    '1.04': 'Mine Safety Reporting',
    '1.05': 'Material Cybersecurity Incidents',
    
    # Section 2 - Financial Information
    '2.01': 'Completion of Acquisition or Disposition',
    '2.02': 'Results of Operations and Financial Condition',
    '2.03': 'Creation of Direct Financial Obligation',
    '2.04': 'Triggering Events for Accelerated Obligations',
    '2.05': 'Costs for Exit/Disposal Activities',
    '2.06': 'Material Impairments',
    
    # Section 3 - Securities and Trading
    '3.01': 'Delisting/Transfer/Failure to Satisfy Listing Rule',
    '3.02': 'Unregistered Sales of Equity Securities',
    '3.03': 'Material Modification of Rights',
    
    # Section 4 - Accounting and Financial Statements
    '4.01': "Changes in Registrant's Certifying Accountant",
    '4.02': 'Non-Reliance on Previously Issued Financials',
    
    # Section 5 - Corporate Governance
    '5.01': 'Changes in Control of Registrant',
    '5.02': 'Departure/Appointment of Directors/Officers',
    '5.03': 'Amendments to Articles/Bylaws',
    '5.04': 'Temporary Suspension of Trading under ERISA',
    '5.05': 'Amendments to Code of Ethics',
    '5.06': 'Change in Shell Company Status',
    '5.07': 'Submission of Matters to Vote of Security Holders',
    '5.08': 'Shareholder Nominations (Proxy Access)',
    
    # Section 7 - Regulation FD
    '7.01': 'Regulation FD Disclosure',
    
    # Section 8 - Other Events
    '8.01': 'Other Events',
    
    # Section 9 - Financial Statements and Exhibits
    '9.01': 'Financial Statements and Exhibits'
}

# High-risk items for insider trading correlation
HIGH_RISK_ITEMS = ['1.01', '1.02', '2.01', '2.02', '2.05', '2.06', '4.01', '4.02', '5.01', '5.02']
CRITICAL_ITEMS = ['1.05', '2.06', '4.02', '5.01']  # Cybersecurity, impairments, restatements, control changes

# Negative items (may indicate upcoming price decline)
NEGATIVE_ITEMS = ['1.02', '1.03', '2.05', '2.06', '4.01', '4.02', '5.02']


class MarketHoursStatus(Enum):
    PRE_MARKET = "Pre-Market"
    MARKET_HOURS = "Market Hours"
    AFTER_HOURS = "After Hours"
    WEEKEND = "Weekend"


class EventAlertType(Enum):
    PRE_EVENT_TRADING = "Pre-Event Insider Trading"
    TIMING_ANOMALY = "Disclosure Timing Anomaly"
    DISCLOSURE_GAP = "Disclosure Gap"
    SEQUENTIAL_EVENTS = "Sequential Adverse Events"
    CROSS_COMPANY_CORRELATION = "Cross-Company Correlation"


@dataclass
class MaterialEvent8K:
    """8-K material event filing."""
    accession_number: str
    cik: str
    company_name: str
    filing_date: date
    filing_time: str
    items: List[str]
    item_descriptions: List[str]
    narrative: str
    market_hours_status: MarketHoursStatus
    price_impact: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "company_name": self.company_name,
            "filing_date": self.filing_date.isoformat(),
            "filing_time": self.filing_time,
            "items": self.items,
            "item_descriptions": self.item_descriptions,
            "market_hours_status": self.market_hours_status.value,
            "is_high_risk": any(item in HIGH_RISK_ITEMS for item in self.items),
            "is_critical": any(item in CRITICAL_ITEMS for item in self.items)
        }


@dataclass
class CorrelatedTrade:
    """Insider trade correlated with material event."""
    insider_name: str
    transaction_date: date
    days_before_event: int
    shares: int
    value: float
    transaction_code: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "insider_name": self.insider_name,
            "transaction_date": self.transaction_date.isoformat(),
            "days_before_event": self.days_before_event,
            "shares": self.shares,
            "value": self.value,
            "transaction_code": self.transaction_code
        }


@dataclass
class EventCorrelationAlert:
    """Alert for correlated suspicious activity."""
    alert_type: EventAlertType
    event: MaterialEvent8K
    correlated_trades: List[CorrelatedTrade]
    risk_score: float
    regulatory_flags: List[str]
    evidence_hash: str
    severity: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "event": self.event.to_dict(),
            "correlated_trades_count": len(self.correlated_trades),
            "correlated_trades": [t.to_dict() for t in self.correlated_trades[:5]],  # Top 5
            "risk_score": round(self.risk_score, 3),
            "regulatory_flags": self.regulatory_flags,
            "severity": self.severity
        }


@dataclass
class Node9Output:
    """Output from Node 9 analysis."""
    events_analyzed: int
    high_risk_events: int
    critical_events: int
    alerts: List[EventCorrelationAlert]
    pre_event_trading_alerts: int
    timing_anomalies: int
    sequential_event_patterns: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "events_analyzed": self.events_analyzed,
                "high_risk_events": self.high_risk_events,
                "critical_events": self.critical_events,
                "pre_event_trading_alerts": self.pre_event_trading_alerts,
                "timing_anomalies": self.timing_anomalies,
                "sequential_patterns": self.sequential_event_patterns
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class MaterialEventCorrelator:
    """
    8-K Material Event Correlator.
    
    Correlates material events with:
    - Pre-announcement insider trading patterns
    - Disclosure timing anomalies (Friday afternoon dumps)
    - Sequential adverse events indicating deterioration
    """
    
    # US holidays for timing analysis (simplified)
    HOLIDAYS = {
        (1, 1), (7, 4), (12, 25), (12, 31)  # (month, day)
    }
    
    def __init__(self):
        pass
    
    def analyze(
        self,
        events: List[MaterialEvent8K],
        form4_trades: Optional[List[Dict[str, Any]]] = None,
        lookback_days: int = 30
    ) -> Node9Output:
        """
        Run complete 8-K event correlation analysis.
        
        Args:
            events: List of 8-K material events
            form4_trades: Optional Form 4 trades for correlation
            lookback_days: Days to look back for correlated trades
            
        Returns:
            Node9Output with all analysis results
        """
        logger.info(f"[NODE 9] Analyzing {len(events)} 8-K material events")
        
        alerts = []
        
        # Correlate with insider trades
        if form4_trades:
            trade_alerts = self.correlate_with_insider_trades(
                events, form4_trades, lookback_days
            )
            alerts.extend(trade_alerts)
        
        # Detect timing anomalies
        timing_alerts = self.detect_timing_anomalies(events)
        alerts.extend(timing_alerts)
        
        # Detect sequential adverse events
        seq_alerts = self.detect_sequential_adverse_events(events)
        alerts.extend(seq_alerts)
        
        # Calculate metrics
        high_risk = len([e for e in events if any(i in HIGH_RISK_ITEMS for i in e.items)])
        critical = len([e for e in events if any(i in CRITICAL_ITEMS for i in e.items)])
        
        return Node9Output(
            events_analyzed=len(events),
            high_risk_events=high_risk,
            critical_events=critical,
            alerts=alerts,
            pre_event_trading_alerts=len([a for a in alerts if a.alert_type == EventAlertType.PRE_EVENT_TRADING]),
            timing_anomalies=len([a for a in alerts if a.alert_type == EventAlertType.TIMING_ANOMALY]),
            sequential_event_patterns=len([a for a in alerts if a.alert_type == EventAlertType.SEQUENTIAL_EVENTS])
        )
    
    def correlate_with_insider_trades(
        self,
        events: List[MaterialEvent8K],
        form4_trades: List[Dict[str, Any]],
        lookback_days: int
    ) -> List[EventCorrelationAlert]:
        """
        Correlate 8-K events with preceding insider trades.
        """
        alerts = []
        
        for event in events:
            # Check if high-risk or critical item
            has_high_risk = any(item in HIGH_RISK_ITEMS for item in event.items)
            has_critical = any(item in CRITICAL_ITEMS for item in event.items)
            
            if not has_high_risk and not has_critical:
                continue
            
            # Find trades in lookback window
            relevant_trades = []
            for trade in form4_trades:
                trade_date = trade.get('date') or trade.get('transaction_date')
                if not trade_date:
                    continue
                
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
                elif isinstance(trade_date, datetime):
                    trade_date = trade_date.date()
                
                days_before = (event.filing_date - trade_date).days
                
                if 0 < days_before <= lookback_days:
                    relevant_trades.append(CorrelatedTrade(
                        insider_name=trade.get('insider_name', trade.get('owner_name', 'Unknown')),
                        transaction_date=trade_date,
                        days_before_event=days_before,
                        shares=trade.get('shares', 0),
                        value=trade.get('shares', 0) * trade.get('price', trade.get('price_per_share', 0)),
                        transaction_code=trade.get('code', trade.get('transaction_code', 'U'))
                    ))
            
            if not relevant_trades:
                continue
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(relevant_trades, event, has_critical)
            
            if risk_score >= 0.5:
                alerts.append(EventCorrelationAlert(
                    alert_type=EventAlertType.PRE_EVENT_TRADING,
                    event=event,
                    correlated_trades=relevant_trades,
                    risk_score=risk_score,
                    regulatory_flags=self._generate_regulatory_flags(event, relevant_trades),
                    evidence_hash=self._generate_hash({'event': event, 'trades': relevant_trades}),
                    severity=self._classify_severity(risk_score, has_critical)
                ))
        
        return alerts
    
    def detect_timing_anomalies(
        self,
        events: List[MaterialEvent8K]
    ) -> List[EventCorrelationAlert]:
        """
        Detect disclosure timing anomalies (Friday dumps, holiday filings).
        """
        alerts = []
        
        for event in events:
            anomalies = []
            
            # Check for Friday afternoon filing
            day_of_week = event.filing_date.weekday()
            hour = int(event.filing_time.split(':')[0]) if ':' in event.filing_time else 16
            
            if day_of_week == 4 and hour >= 16:  # Friday after 4 PM
                anomalies.append('Friday after-market filing (reduced media coverage)')
            
            # Check for holiday-adjacent
            if self._is_holiday_adjacent(event.filing_date):
                anomalies.append('Holiday-adjacent filing (reduced analyst attention)')
            
            # Check for critical items filed after hours
            has_critical = any(item in CRITICAL_ITEMS for item in event.items)
            if has_critical and event.market_hours_status == MarketHoursStatus.AFTER_HOURS:
                anomalies.append('Critical event disclosed after market hours')
            
            # Item 4.02 (restatement)
            if '4.02' in event.items:
                anomalies.append('Item 4.02 Non-Reliance filing - potential earnings manipulation')
            
            if anomalies:
                alerts.append(EventCorrelationAlert(
                    alert_type=EventAlertType.TIMING_ANOMALY,
                    event=event,
                    correlated_trades=[],
                    risk_score=0.3 + (len(anomalies) * 0.2),
                    regulatory_flags=anomalies,
                    evidence_hash=self._generate_hash({'event': event, 'anomalies': anomalies}),
                    severity='MEDIUM' if len(anomalies) >= 2 else 'LOW'
                ))
        
        return alerts
    
    def detect_sequential_adverse_events(
        self,
        events: List[MaterialEvent8K],
        window_days: int = 90
    ) -> List[EventCorrelationAlert]:
        """
        Detect patterns of sequential adverse events indicating deterioration.
        """
        alerts = []
        
        # Group by company
        by_company = {}
        for event in events:
            if event.cik not in by_company:
                by_company[event.cik] = []
            by_company[event.cik].append(event)
        
        for cik, company_events in by_company.items():
            sorted_events = sorted(company_events, key=lambda e: e.filing_date)
            
            # Filter to adverse events
            adverse_events = [
                e for e in sorted_events
                if any(item in NEGATIVE_ITEMS for item in e.items)
            ]
            
            # Find clusters
            i = 0
            while i < len(adverse_events):
                cluster = [adverse_events[i]]
                
                for j in range(i + 1, len(adverse_events)):
                    if (adverse_events[j].filing_date - adverse_events[i].filing_date).days <= window_days:
                        cluster.append(adverse_events[j])
                
                if len(cluster) >= 3:
                    alerts.append(EventCorrelationAlert(
                        alert_type=EventAlertType.SEQUENTIAL_EVENTS,
                        event=cluster[0],
                        correlated_trades=[],
                        risk_score=min(0.4 + (len(cluster) * 0.15), 1.0),
                        regulatory_flags=[
                            f'{len(cluster)} adverse events in {window_days} days',
                            'Pattern suggests deteriorating corporate condition',
                            'Heightened bankruptcy/fraud risk',
                            *[f'{e.filing_date}: {", ".join(e.items)}' for e in cluster[:5]]
                        ],
                        evidence_hash=self._generate_hash(cluster),
                        severity='CRITICAL' if len(cluster) >= 4 else 'HIGH'
                    ))
                    i += len(cluster)
                    break
                else:
                    i += 1
        
        return alerts
    
    def _calculate_risk_score(
        self,
        trades: List[CorrelatedTrade],
        event: MaterialEvent8K,
        has_critical: bool
    ) -> float:
        """Calculate risk score for correlated trading."""
        score = 0.0
        
        # Base score from trade count
        score += min(len(trades) * 0.1, 0.3)
        
        # Boost for trades closer to event
        if trades:
            avg_days = sum(t.days_before_event for t in trades) / len(trades)
            if avg_days <= 5:
                score += 0.3
            elif avg_days <= 10:
                score += 0.2
            elif avg_days <= 20:
                score += 0.1
        
        # Boost for sales before negative events
        sales_count = len([t for t in trades if t.transaction_code == 'S'])
        has_negative = any(item in NEGATIVE_ITEMS for item in event.items)
        if sales_count > 0 and has_negative:
            score += 0.2
        
        # Boost for critical items
        if has_critical:
            score += 0.2
        
        return min(score, 1.0)
    
    def _generate_regulatory_flags(
        self,
        event: MaterialEvent8K,
        trades: List[CorrelatedTrade]
    ) -> List[str]:
        """Generate regulatory flags for alert."""
        flags = []
        
        if trades:
            flags.append(f'{len(trades)} insider trades in 30-day pre-event window')
        
        sales_value = sum(t.value for t in trades if t.transaction_code == 'S')
        if sales_value > 100000:
            flags.append(f'${sales_value / 1000:.0f}K in pre-event insider sales')
        
        if '4.02' in event.items:
            flags.append('Item 4.02 restatement - potential Rule 10b-5 violation')
        
        if '1.05' in event.items:
            flags.append('Material cybersecurity incident - new SEC disclosure requirements')
        
        return flags
    
    def _classify_severity(self, risk_score: float, has_critical: bool) -> str:
        """Classify alert severity."""
        if risk_score >= 0.8 or (has_critical and risk_score >= 0.6):
            return 'CRITICAL'
        if risk_score >= 0.6:
            return 'HIGH'
        if risk_score >= 0.4:
            return 'MEDIUM'
        return 'LOW'
    
    def _is_holiday_adjacent(self, d: date) -> bool:
        """Check if date is adjacent to a holiday."""
        month, day = d.month, d.day
        
        # Check for days around major holidays
        if month == 1 and day <= 3:  # New Year's
            return True
        if month == 12 and day >= 23:  # Christmas/New Year's
            return True
        if month == 7 and 3 <= day <= 5:  # July 4th
            return True
        if month == 11 and 22 <= day <= 28 and d.weekday() >= 3:  # Thanksgiving
            return True
        
        return False
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()

