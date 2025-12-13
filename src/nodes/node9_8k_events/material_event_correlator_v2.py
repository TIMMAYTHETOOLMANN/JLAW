"""
NODE 9: 8-K Material Event Correlator v2.0 (FORTIFIED)
=====================================================

Enhanced version with:
- Real-time market data correlation
- Price/volume impact quantification
- Enhanced timing anomaly detection
- Cross-node correlation (Nodes 1, 7, 8)
- Item 1.05 (Cybersecurity) event support

SEC Reference: https://www.sec.gov/about/forms/form8-k.pdf
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import logging
from statistics import mean, stdev

from .market_data_client import MarketDataClient, Bar

logger = logging.getLogger(__name__)


# SEC 8-K Item reference codes (updated December 2023)
MATERIAL_EVENT_ITEMS = {
    # Section 1 - Business Operations
    '1.01': 'Entry into Material Definitive Agreement',
    '1.02': 'Termination of Material Definitive Agreement',
    '1.03': 'Bankruptcy or Receivership',
    '1.04': 'Mine Safety Reporting',
    '1.05': 'Material Cybersecurity Incidents',  # NEW December 2023
    
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
HIGH_RISK_ITEMS = ['1.01', '1.02', '1.05', '2.01', '2.02', '2.05', '2.06', '4.01', '4.02', '5.01', '5.02']
CRITICAL_ITEMS = ['1.05', '2.06', '4.02', '5.01']  # Cybersecurity, impairments, restatements, control changes

# Negative items (may indicate upcoming price decline)
NEGATIVE_ITEMS = ['1.02', '1.03', '1.05', '2.05', '2.06', '4.01', '4.02', '5.02']


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
    ABNORMAL_VOLUME = "Abnormal Volume"
    SIGNIFICANT_PRICE_MOVE = "Significant Price Movement"
    PRE_EVENT_INSTITUTIONAL_POSITIONING = "Pre-Event Institutional Positioning"


@dataclass
class MarketImpactAnalysis:
    """Market impact analysis for an 8-K event."""
    event_date: date
    ticker: str
    cusip: Optional[str] = None
    
    # Price metrics
    price_t_minus_5: Optional[float] = None
    price_t_minus_1: Optional[float] = None
    price_t_0: Optional[float] = None
    price_t_plus_1: Optional[float] = None
    price_t_plus_5: Optional[float] = None
    
    # Calculated impacts
    pre_event_drift: Optional[float] = None  # (T-1 - T-5) / T-5
    event_day_return: Optional[float] = None  # (T+0 close - T-1 close) / T-1
    post_event_drift: Optional[float] = None  # (T+5 - T+0) / T+0
    cumulative_abnormal_return: Optional[float] = None
    
    # Volume metrics
    avg_volume_20d: Optional[int] = None
    event_day_volume: Optional[int] = None
    volume_ratio: Optional[float] = None  # event_day / avg_20d
    
    # Flags
    is_abnormal_volume: bool = False  # volume_ratio > 2.0
    is_significant_price_move: bool = False  # abs(event_day_return) > 0.05
    
    # Intraday analysis
    intraday_high: Optional[float] = None
    intraday_low: Optional[float] = None
    intraday_volatility: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_date": self.event_date.isoformat(),
            "ticker": self.ticker,
            "cusip": self.cusip,
            "price_metrics": {
                "T-5": self.price_t_minus_5,
                "T-1": self.price_t_minus_1,
                "T+0": self.price_t_0,
                "T+1": self.price_t_plus_1,
                "T+5": self.price_t_plus_5
            },
            "impact_metrics": {
                "pre_event_drift": round(self.pre_event_drift, 4) if self.pre_event_drift else None,
                "event_day_return": round(self.event_day_return, 4) if self.event_day_return else None,
                "post_event_drift": round(self.post_event_drift, 4) if self.post_event_drift else None,
                "cumulative_abnormal_return": round(self.cumulative_abnormal_return, 4) if self.cumulative_abnormal_return else None
            },
            "volume_metrics": {
                "avg_volume_20d": self.avg_volume_20d,
                "event_day_volume": self.event_day_volume,
                "volume_ratio": round(self.volume_ratio, 2) if self.volume_ratio else None
            },
            "flags": {
                "abnormal_volume": self.is_abnormal_volume,
                "significant_price_move": self.is_significant_price_move
            }
        }


@dataclass
class MaterialEvent8KV2:
    """Enhanced 8-K material event filing with market data."""
    accession_number: str
    cik: str
    company_name: str
    ticker: Optional[str]
    filing_date: date
    filing_time: str
    items: List[str]
    item_descriptions: List[str]
    narrative: str
    market_hours_status: MarketHoursStatus
    
    # v2.0 enhancements
    cusip: Optional[str] = None
    market_impact: Optional[MarketImpactAnalysis] = None
    sentiment_score: Optional[float] = None  # -1 (negative) to +1 (positive)
    complexity_score: Optional[float] = None  # 0-1 based on multi-item events
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "company_name": self.company_name,
            "ticker": self.ticker,
            "filing_date": self.filing_date.isoformat(),
            "filing_time": self.filing_time,
            "items": self.items,
            "item_descriptions": self.item_descriptions,
            "market_hours_status": self.market_hours_status.value,
            "is_high_risk": any(item in HIGH_RISK_ITEMS for item in self.items),
            "is_critical": any(item in CRITICAL_ITEMS for item in self.items),
            "sentiment_score": self.sentiment_score,
            "complexity_score": self.complexity_score,
            "market_impact": self.market_impact.to_dict() if self.market_impact else None
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
class EventCorrelationAlertV2:
    """Enhanced alert for correlated suspicious activity."""
    alert_type: EventAlertType
    event: MaterialEvent8KV2
    correlated_trades: List[CorrelatedTrade]
    risk_score: float
    regulatory_flags: List[str]
    evidence_hash: str
    severity: str
    
    # v2.0 enhancements
    market_impact: Optional[MarketImpactAnalysis] = None
    node7_holdings_changes: Optional[List[Dict]] = None  # Institutional positioning
    node8_ownership_changes: Optional[List[Dict]] = None  # Beneficial ownership
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "event": self.event.to_dict(),
            "correlated_trades_count": len(self.correlated_trades),
            "correlated_trades": [t.to_dict() for t in self.correlated_trades[:5]],
            "risk_score": round(self.risk_score, 3),
            "regulatory_flags": self.regulatory_flags,
            "severity": self.severity,
            "market_impact": self.market_impact.to_dict() if self.market_impact else None,
            "node7_correlation": len(self.node7_holdings_changes) if self.node7_holdings_changes else 0,
            "node8_correlation": len(self.node8_ownership_changes) if self.node8_ownership_changes else 0
        }


@dataclass
class ComprehensiveEventAnalysis:
    """Complete cross-node event analysis."""
    event: MaterialEvent8KV2
    form4_correlation: Optional[Dict[str, Any]] = None
    node7_correlation: Optional[Dict[str, Any]] = None
    node8_correlation: Optional[Dict[str, Any]] = None
    market_impact: Optional[MarketImpactAnalysis] = None
    combined_risk_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "correlations": {
                "form4_insider_trades": self.form4_correlation,
                "node7_institutional_holdings": self.node7_correlation,
                "node8_beneficial_ownership": self.node8_correlation
            },
            "market_impact": self.market_impact.to_dict() if self.market_impact else None,
            "combined_risk_score": round(self.combined_risk_score, 3)
        }


@dataclass
class Node9OutputV2:
    """Enhanced output from Node 9 v2.0 analysis."""
    events_analyzed: int
    high_risk_events: int
    critical_events: int
    alerts: List[EventCorrelationAlertV2]
    pre_event_trading_alerts: int
    timing_anomalies: int
    sequential_event_patterns: int
    abnormal_volume_alerts: int
    significant_price_move_alerts: int
    market_data_correlations: int
    cross_node_correlations: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "events_analyzed": self.events_analyzed,
                "high_risk_events": self.high_risk_events,
                "critical_events": self.critical_events,
                "pre_event_trading_alerts": self.pre_event_trading_alerts,
                "timing_anomalies": self.timing_anomalies,
                "sequential_patterns": self.sequential_event_patterns,
                "abnormal_volume_alerts": self.abnormal_volume_alerts,
                "significant_price_moves": self.significant_price_move_alerts,
                "market_data_correlations": self.market_data_correlations,
                "cross_node_correlations": self.cross_node_correlations
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class MaterialEventCorrelatorV2:
    """
    8-K Material Event Correlator v2.0 (FORTIFIED).
    
    Enhanced capabilities:
    - Real-time market data integration
    - Pre/post event price impact calculation
    - Abnormal volume detection
    - Cross-node correlation (Nodes 1, 7, 8)
    - Item 1.05 cybersecurity event handling
    - Multi-item event complexity scoring
    """
    
    # US holidays for timing analysis (simplified)
    HOLIDAYS = {
        (1, 1), (7, 4), (12, 25), (12, 31)
    }
    
    # Price/volume thresholds
    ABNORMAL_VOLUME_THRESHOLD = 2.0  # 2x average
    SIGNIFICANT_PRICE_MOVE_THRESHOLD = 0.05  # 5%
    
    def __init__(self, market_data_client: Optional[MarketDataClient] = None):
        """
        Initialize correlator.
        
        Args:
            market_data_client: Optional market data client for price/volume analysis
        """
        self.market_data_client = market_data_client
    
    async def analyze(
        self,
        events: List[MaterialEvent8KV2],
        form4_trades: Optional[List[Dict[str, Any]]] = None,
        node7_output: Optional[Any] = None,
        node8_output: Optional[Any] = None,
        lookback_days: int = 30
    ) -> Node9OutputV2:
        """
        Run complete 8-K event correlation analysis with v2.0 enhancements.
        
        Args:
            events: List of 8-K material events
            form4_trades: Optional Form 4 trades for correlation
            node7_output: Optional Node 7 output (13F holdings)
            node8_output: Optional Node 8 output (13D/G filings)
            lookback_days: Days to look back for correlated trades
            
        Returns:
            Node9OutputV2 with all analysis results
        """
        logger.info(f"[NODE 9 v2.0] Analyzing {len(events)} 8-K material events")
        
        alerts = []
        market_data_count = 0
        cross_node_count = 0
        
        # Enrich events with market data if available
        if self.market_data_client:
            for event in events:
                if event.ticker:
                    impact = await self.calculate_market_impact(event)
                    event.market_impact = impact
                    if impact:
                        market_data_count += 1
        
        # Correlate with insider trades (Node 1)
        if form4_trades:
            trade_alerts = self.correlate_with_insider_trades(
                events, form4_trades, lookback_days
            )
            alerts.extend(trade_alerts)
        
        # Correlate with institutional holdings (Node 7)
        if node7_output:
            holdings_alerts = self.correlate_with_node7(events, node7_output)
            alerts.extend(holdings_alerts)
            cross_node_count += len(holdings_alerts)
        
        # Correlate with beneficial ownership (Node 8)
        if node8_output:
            ownership_alerts = self.correlate_with_node8(events, node8_output)
            alerts.extend(ownership_alerts)
            cross_node_count += len(ownership_alerts)
        
        # Detect timing anomalies
        timing_alerts = self.detect_timing_anomalies(events)
        alerts.extend(timing_alerts)
        
        # Detect sequential adverse events
        seq_alerts = self.detect_sequential_adverse_events(events)
        alerts.extend(seq_alerts)
        
        # Detect abnormal volume/price movements
        volume_alerts = self.detect_abnormal_volume(events)
        alerts.extend(volume_alerts)
        
        # Calculate metrics
        high_risk = len([e for e in events if any(i in HIGH_RISK_ITEMS for i in e.items)])
        critical = len([e for e in events if any(i in CRITICAL_ITEMS for i in e.items)])
        
        return Node9OutputV2(
            events_analyzed=len(events),
            high_risk_events=high_risk,
            critical_events=critical,
            alerts=alerts,
            pre_event_trading_alerts=len([a for a in alerts if a.alert_type == EventAlertType.PRE_EVENT_TRADING]),
            timing_anomalies=len([a for a in alerts if a.alert_type == EventAlertType.TIMING_ANOMALY]),
            sequential_event_patterns=len([a for a in alerts if a.alert_type == EventAlertType.SEQUENTIAL_EVENTS]),
            abnormal_volume_alerts=len([a for a in alerts if a.alert_type == EventAlertType.ABNORMAL_VOLUME]),
            significant_price_move_alerts=len([a for a in alerts if a.alert_type == EventAlertType.SIGNIFICANT_PRICE_MOVE]),
            market_data_correlations=market_data_count,
            cross_node_correlations=cross_node_count
        )
    
    async def calculate_market_impact(
        self,
        event: MaterialEvent8KV2
    ) -> Optional[MarketImpactAnalysis]:
        """
        Calculate market impact for an event using real-time data.
        
        Args:
            event: Material event
            
        Returns:
            MarketImpactAnalysis or None
        """
        if not self.market_data_client or not event.ticker:
            return None
        
        try:
            # Fetch daily bars for T-5 through T+5
            start_date = event.filing_date - timedelta(days=10)  # Extra days for weekends
            end_date = event.filing_date + timedelta(days=10)
            
            bars = await self.market_data_client.get_daily_bars(
                event.ticker,
                start_date,
                end_date
            )
            
            if not bars:
                return None
            
            # Find relevant bars
            bars_dict = {b.timestamp.date(): b for b in bars}
            
            # Calculate T-5, T-1, T+0, T+1, T+5 prices
            prices = {}
            for offset, key in [(-5, 'T-5'), (-1, 'T-1'), (0, 'T+0'), (1, 'T+1'), (5, 'T+5')]:
                target_date = event.filing_date + timedelta(days=offset)
                # Find closest trading day
                for i in range(7):  # Look up to 7 days for weekends/holidays
                    check_date = target_date + timedelta(days=i if offset >= 0 else -i)
                    if check_date in bars_dict:
                        prices[key] = bars_dict[check_date].close
                        break
            
            # Calculate 20-day average volume
            recent_bars = [b for b in bars if b.timestamp.date() < event.filing_date]
            avg_volume = int(mean([b.volume for b in recent_bars[-20:]])) if len(recent_bars) >= 20 else None
            
            # Get event day volume
            event_bar = bars_dict.get(event.filing_date)
            event_volume = event_bar.volume if event_bar else None
            
            # Calculate metrics
            pre_drift = ((prices.get('T-1', 0) - prices.get('T-5', 1)) / prices.get('T-5', 1)) if 'T-5' in prices and 'T-1' in prices else None
            event_return = ((prices.get('T+0', 0) - prices.get('T-1', 1)) / prices.get('T-1', 1)) if 'T-1' in prices and 'T+0' in prices else None
            post_drift = ((prices.get('T+5', 0) - prices.get('T+0', 1)) / prices.get('T+0', 1)) if 'T+0' in prices and 'T+5' in prices else None
            
            # Calculate CAR (simplified)
            car = sum(filter(None, [pre_drift or 0, event_return or 0, post_drift or 0]))
            
            volume_ratio = (event_volume / avg_volume) if avg_volume and event_volume else None
            
            # Flags
            is_abnormal_vol = volume_ratio > self.ABNORMAL_VOLUME_THRESHOLD if volume_ratio else False
            is_sig_move = abs(event_return) > self.SIGNIFICANT_PRICE_MOVE_THRESHOLD if event_return else False
            
            impact = MarketImpactAnalysis(
                event_date=event.filing_date,
                ticker=event.ticker,
                cusip=event.cusip,
                price_t_minus_5=prices.get('T-5'),
                price_t_minus_1=prices.get('T-1'),
                price_t_0=prices.get('T+0'),
                price_t_plus_1=prices.get('T+1'),
                price_t_plus_5=prices.get('T+5'),
                pre_event_drift=pre_drift,
                event_day_return=event_return,
                post_event_drift=post_drift,
                cumulative_abnormal_return=car,
                avg_volume_20d=avg_volume,
                event_day_volume=event_volume,
                volume_ratio=volume_ratio,
                is_abnormal_volume=is_abnormal_vol,
                is_significant_price_move=is_sig_move
            )
            
            logger.info(f"Calculated market impact for {event.ticker}: return={event_return:.2%}, vol_ratio={volume_ratio:.2f}" if event_return and volume_ratio else f"Market impact calculated for {event.ticker}")
            return impact
            
        except Exception as e:
            logger.error(f"Error calculating market impact: {e}")
            return None
    
    def correlate_with_insider_trades(
        self,
        events: List[MaterialEvent8KV2],
        form4_trades: List[Dict[str, Any]],
        lookback_days: int
    ) -> List[EventCorrelationAlertV2]:
        """
        Correlate 8-K events with preceding insider trades (Node 1).
        """
        alerts = []
        
        for event in events:
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
            
            risk_score = self._calculate_risk_score(relevant_trades, event, has_critical)
            
            if risk_score >= 0.5:
                alerts.append(EventCorrelationAlertV2(
                    alert_type=EventAlertType.PRE_EVENT_TRADING,
                    event=event,
                    correlated_trades=relevant_trades,
                    risk_score=risk_score,
                    regulatory_flags=self._generate_regulatory_flags(event, relevant_trades),
                    evidence_hash=self._generate_hash({'event': event, 'trades': relevant_trades}),
                    severity=self._classify_severity(risk_score, has_critical),
                    market_impact=event.market_impact
                ))
        
        return alerts
    
    def correlate_with_node7(
        self,
        events: List[MaterialEvent8KV2],
        node7_output: Any
    ) -> List[EventCorrelationAlertV2]:
        """
        Correlate events with Node 7 institutional holdings changes.
        """
        alerts = []
        
        if not hasattr(node7_output, 'alerts'):
            return alerts
        
        for event in events:
            matching_holdings = []
            
            for alert in node7_output.alerts:
                # Check if CUSIP matches
                if event.cusip and alert.cusip == event.cusip:
                    matching_holdings.append({
                        'alert_type': alert.alert_type.value,
                        'institutions': alert.institutions,
                        'share_change': alert.total_share_change,
                        'correlation_score': alert.correlation_score
                    })
            
            if matching_holdings:
                risk_score = 0.7  # High risk when institutional + event
                
                alerts.append(EventCorrelationAlertV2(
                    alert_type=EventAlertType.PRE_EVENT_INSTITUTIONAL_POSITIONING,
                    event=event,
                    correlated_trades=[],
                    risk_score=risk_score,
                    regulatory_flags=[
                        f'{len(matching_holdings)} institutional holdings alerts for same security',
                        'Coordinated institutional positioning before material event',
                        'Potential information leakage'
                    ],
                    evidence_hash=self._generate_hash({'event': event, 'holdings': matching_holdings}),
                    severity='HIGH',
                    node7_holdings_changes=matching_holdings
                ))
        
        return alerts
    
    def correlate_with_node8(
        self,
        events: List[MaterialEvent8KV2],
        node8_output: Any
    ) -> List[EventCorrelationAlertV2]:
        """
        Correlate events with Node 8 beneficial ownership changes.
        """
        alerts = []
        
        if not hasattr(node8_output, 'alerts'):
            return alerts
        
        for event in events:
            matching_ownership = []
            
            for alert in node8_output.alerts:
                # Check if CIK matches
                if event.cik == alert.subject_company_cik:
                    matching_ownership.append({
                        'alert_type': alert.alert_type.value,
                        'parties': [p['name'] for p in alert.involved_parties],
                        'aggregate_ownership': alert.aggregate_ownership,
                        'intent_score': alert.intent_analysis.intent_score
                    })
            
            if matching_ownership:
                risk_score = 0.8  # Very high risk
                
                alerts.append(EventCorrelationAlertV2(
                    alert_type=EventAlertType.PRE_EVENT_TRADING,
                    event=event,
                    correlated_trades=[],
                    risk_score=risk_score,
                    regulatory_flags=[
                        f'{len(matching_ownership)} beneficial ownership alerts for company',
                        'Activist positioning before material event',
                        'Potential coordination'
                    ],
                    evidence_hash=self._generate_hash({'event': event, 'ownership': matching_ownership}),
                    severity='CRITICAL',
                    node8_ownership_changes=matching_ownership
                ))
        
        return alerts
    
    def correlate_all_sources(
        self,
        event: MaterialEvent8KV2,
        form4_trades: List[Dict],
        holdings_changes: List[Dict],
        ownership_filings: List[Dict]
    ) -> ComprehensiveEventAnalysis:
        """
        Full cross-node correlation for 8-K material events.
        
        Args:
            event: Material event
            form4_trades: Form 4 trades (Node 1)
            holdings_changes: Holdings changes (Node 7)
            ownership_filings: Ownership filings (Node 8)
            
        Returns:
            ComprehensiveEventAnalysis
        """
        # Calculate individual correlations
        form4_corr = None
        if form4_trades:
            form4_corr = {
                "trade_count": len(form4_trades),
                "total_value": sum(t.get('value', 0) for t in form4_trades),
                "insiders": list(set(t.get('insider_name', 'Unknown') for t in form4_trades))
            }
        
        node7_corr = None
        if holdings_changes:
            node7_corr = {
                "alert_count": len(holdings_changes),
                "institutions": [h.get('institutions', []) for h in holdings_changes]
            }
        
        node8_corr = None
        if ownership_filings:
            node8_corr = {
                "filing_count": len(ownership_filings),
                "parties": [o.get('parties', []) for o in ownership_filings]
            }
        
        # Calculate combined risk score
        risk_factors = []
        if form4_corr:
            risk_factors.append(0.3)
        if node7_corr:
            risk_factors.append(0.35)
        if node8_corr:
            risk_factors.append(0.35)
        if event.market_impact and event.market_impact.is_significant_price_move:
            risk_factors.append(0.2)
        
        combined_risk = sum(risk_factors)
        
        return ComprehensiveEventAnalysis(
            event=event,
            form4_correlation=form4_corr,
            node7_correlation=node7_corr,
            node8_correlation=node8_corr,
            market_impact=event.market_impact,
            combined_risk_score=combined_risk
        )
    
    def detect_timing_anomalies(
        self,
        events: List[MaterialEvent8KV2]
    ) -> List[EventCorrelationAlertV2]:
        """
        Detect disclosure timing anomalies (Friday dumps, holiday filings).
        """
        alerts = []
        
        for event in events:
            anomalies = []
            
            day_of_week = event.filing_date.weekday()
            hour = int(event.filing_time.split(':')[0]) if ':' in event.filing_time else 16
            
            if day_of_week == 4 and hour >= 16:
                anomalies.append('Friday after-market filing (reduced media coverage)')
            
            if self._is_holiday_adjacent(event.filing_date):
                anomalies.append('Holiday-adjacent filing (reduced analyst attention)')
            
            has_critical = any(item in CRITICAL_ITEMS for item in event.items)
            if has_critical and event.market_hours_status == MarketHoursStatus.AFTER_HOURS:
                anomalies.append('Critical event disclosed after market hours')
            
            # Item 1.05 (Cybersecurity)
            if '1.05' in event.items:
                anomalies.append('Item 1.05 Cybersecurity incident - December 2023 disclosure requirement')
            
            # Item 4.02 (restatement)
            if '4.02' in event.items:
                anomalies.append('Item 4.02 Non-Reliance filing - potential earnings manipulation')
            
            if anomalies:
                alerts.append(EventCorrelationAlertV2(
                    alert_type=EventAlertType.TIMING_ANOMALY,
                    event=event,
                    correlated_trades=[],
                    risk_score=0.3 + (len(anomalies) * 0.2),
                    regulatory_flags=anomalies,
                    evidence_hash=self._generate_hash({'event': event, 'anomalies': anomalies}),
                    severity='MEDIUM' if len(anomalies) >= 2 else 'LOW',
                    market_impact=event.market_impact
                ))
        
        return alerts
    
    def detect_sequential_adverse_events(
        self,
        events: List[MaterialEvent8KV2],
        window_days: int = 90
    ) -> List[EventCorrelationAlertV2]:
        """
        Detect patterns of sequential adverse events indicating deterioration.
        """
        alerts = []
        
        by_company = {}
        for event in events:
            if event.cik not in by_company:
                by_company[event.cik] = []
            by_company[event.cik].append(event)
        
        for cik, company_events in by_company.items():
            sorted_events = sorted(company_events, key=lambda e: e.filing_date)
            
            adverse_events = [
                e for e in sorted_events
                if any(item in NEGATIVE_ITEMS for item in e.items)
            ]
            
            i = 0
            while i < len(adverse_events):
                cluster = [adverse_events[i]]
                
                for j in range(i + 1, len(adverse_events)):
                    if (adverse_events[j].filing_date - adverse_events[i].filing_date).days <= window_days:
                        cluster.append(adverse_events[j])
                
                if len(cluster) >= 3:
                    alerts.append(EventCorrelationAlertV2(
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
    
    def detect_abnormal_volume(
        self,
        events: List[MaterialEvent8KV2]
    ) -> List[EventCorrelationAlertV2]:
        """
        Detect abnormal volume/price movements from market impact analysis.
        """
        alerts = []
        
        for event in events:
            if not event.market_impact:
                continue
            
            impact = event.market_impact
            
            if impact.is_abnormal_volume:
                alerts.append(EventCorrelationAlertV2(
                    alert_type=EventAlertType.ABNORMAL_VOLUME,
                    event=event,
                    correlated_trades=[],
                    risk_score=0.6,
                    regulatory_flags=[
                        f'Abnormal volume: {impact.volume_ratio:.2f}x average',
                        f'Event day volume: {impact.event_day_volume:,}',
                        f'20-day average: {impact.avg_volume_20d:,}'
                    ],
                    evidence_hash=self._generate_hash({'event': event, 'impact': impact}),
                    severity='MEDIUM',
                    market_impact=impact
                ))
            
            if impact.is_significant_price_move:
                alerts.append(EventCorrelationAlertV2(
                    alert_type=EventAlertType.SIGNIFICANT_PRICE_MOVE,
                    event=event,
                    correlated_trades=[],
                    risk_score=0.7,
                    regulatory_flags=[
                        f'Significant price move: {impact.event_day_return:.2%}',
                        f'Event day: {impact.price_t_0}',
                        f'Previous close: {impact.price_t_minus_1}'
                    ],
                    evidence_hash=self._generate_hash({'event': event, 'impact': impact}),
                    severity='HIGH' if abs(impact.event_day_return) > 0.10 else 'MEDIUM',
                    market_impact=impact
                ))
        
        return alerts
    
    def _calculate_risk_score(
        self,
        trades: List[CorrelatedTrade],
        event: MaterialEvent8KV2,
        has_critical: bool
    ) -> float:
        """Calculate risk score for correlated trading."""
        score = 0.0
        
        score += min(len(trades) * 0.1, 0.3)
        
        if trades:
            avg_days = sum(t.days_before_event for t in trades) / len(trades)
            if avg_days <= 5:
                score += 0.3
            elif avg_days <= 10:
                score += 0.2
            elif avg_days <= 20:
                score += 0.1
        
        sales_count = len([t for t in trades if t.transaction_code == 'S'])
        has_negative = any(item in NEGATIVE_ITEMS for item in event.items)
        if sales_count > 0 and has_negative:
            score += 0.2
        
        if has_critical:
            score += 0.2
        
        # Boost for market impact
        if event.market_impact and event.market_impact.is_significant_price_move:
            score += 0.15
        
        return min(score, 1.0)
    
    def _generate_regulatory_flags(
        self,
        event: MaterialEvent8KV2,
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
            flags.append('Material cybersecurity incident - SEC December 2023 disclosure mandate')
        
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
        
        if month == 1 and day <= 3:
            return True
        if month == 12 and day >= 23:
            return True
        if month == 7 and 3 <= day <= 5:
            return True
        if month == 11 and 22 <= day <= 28 and d.weekday() >= 3:
            return True
        
        return False
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()
