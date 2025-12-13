"""
Cross-Node Correlator
====================

Provides unified correlation across Nodes 1, 7, 8, and 9 to detect
coordinated suspicious activity across multiple data sources.

Key Correlations:
- Node 7 ↔ Node 8: Wolf pack 13F holdings + 13D activist filings
- Node 9 ↔ Nodes 1, 7, 8: Material events + insider/institutional activity
- Multi-node patterns: Coordinated campaigns across all sources
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CrossNodeAlertType(Enum):
    """Types of cross-node alerts."""
    WOLF_PACK_13F_13D_CORRELATION = "Wolf Pack: 13F Holdings + 13D Activist Correlation"
    EVENT_INSIDER_INSTITUTIONAL_CORRELATION = "8-K Event + Insider + Institutional Correlation"
    COORDINATED_CAMPAIGN = "Coordinated Multi-Source Campaign"
    PRE_EVENT_POSITIONING = "Pre-Event Positioning Across Sources"
    ACTIVIST_ACCUMULATION_PATTERN = "Activist Accumulation Pattern"


class Severity(Enum):
    """Alert severity."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class CrossNodeAlert:
    """
    Unified alert correlating multiple forensic nodes.
    """
    alert_type: CrossNodeAlertType
    cusip: Optional[str]
    company_name: str
    company_cik: str
    
    # Source data references
    node1_data: Optional[Dict[str, Any]] = None  # Form 4 insider trades
    node7_data: Optional[Dict[str, Any]] = None  # 13F institutional holdings
    node8_data: Optional[Dict[str, Any]] = None  # 13D/G beneficial ownership
    node9_data: Optional[Dict[str, Any]] = None  # 8-K material events
    
    # Correlation metrics
    correlation_score: float = 0.0  # 0.0-1.0
    risk_indicators: List[str] = field(default_factory=list)
    regulatory_implications: List[str] = field(default_factory=list)
    
    # Timing analysis
    temporal_window_days: int = 0
    earliest_signal_date: Optional[date] = None
    latest_signal_date: Optional[date] = None
    
    severity: Severity = Severity.MEDIUM
    evidence_chain: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "company": {
                "name": self.company_name,
                "cik": self.company_cik,
                "cusip": self.cusip
            },
            "correlation_score": round(self.correlation_score, 3),
            "severity": self.severity.value,
            "sources": {
                "node1_insider_trades": bool(self.node1_data),
                "node7_institutional_holdings": bool(self.node7_data),
                "node8_beneficial_ownership": bool(self.node8_data),
                "node9_material_events": bool(self.node9_data)
            },
            "temporal_analysis": {
                "window_days": self.temporal_window_days,
                "earliest_signal": self.earliest_signal_date.isoformat() if self.earliest_signal_date else None,
                "latest_signal": self.latest_signal_date.isoformat() if self.latest_signal_date else None
            },
            "risk_indicators": self.risk_indicators,
            "regulatory_implications": self.regulatory_implications,
            "evidence_chain_items": len(self.evidence_chain),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class UnifiedForensicAnalysis:
    """
    Complete unified forensic analysis across all nodes.
    """
    company_cik: str
    company_name: str
    analysis_period_start: date
    analysis_period_end: date
    
    # Individual node outputs
    node1_output: Optional[Any] = None
    node7_output: Optional[Any] = None
    node8_output: Optional[Any] = None
    node9_output: Optional[Any] = None
    
    # Cross-node alerts
    cross_node_alerts: List[CrossNodeAlert] = field(default_factory=list)
    
    # Unified risk scoring
    overall_risk_score: float = 0.0  # 0.0-1.0
    risk_factors: List[str] = field(default_factory=list)
    
    # Summary statistics
    total_insider_trades: int = 0
    total_institutional_alerts: int = 0
    total_ownership_alerts: int = 0
    total_material_events: int = 0
    total_cross_node_correlations: int = 0
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": {
                "cik": self.company_cik,
                "name": self.company_name
            },
            "analysis_period": {
                "start": self.analysis_period_start.isoformat(),
                "end": self.analysis_period_end.isoformat()
            },
            "overall_risk_score": round(self.overall_risk_score, 3),
            "risk_factors": self.risk_factors,
            "summary": {
                "insider_trades": self.total_insider_trades,
                "institutional_alerts": self.total_institutional_alerts,
                "ownership_alerts": self.total_ownership_alerts,
                "material_events": self.total_material_events,
                "cross_node_correlations": self.total_cross_node_correlations
            },
            "cross_node_alerts": [a.to_dict() for a in self.cross_node_alerts],
            "timestamp": self.timestamp.isoformat()
        }


class NodeCorrelator:
    """
    Cross-node correlator for unified forensic analysis.
    
    Correlates findings across:
    - Node 1: Form 4 insider trades
    - Node 7: 13F-HR institutional holdings
    - Node 8: 13D/13G beneficial ownership
    - Node 9: 8-K material events
    """
    
    # Correlation thresholds (from config.fortified_nodes_config)
    # Note: In production, import MIN_CROSS_NODE_CORRELATION_SCORE and CROSS_NODE_TEMPORAL_WINDOW_DAYS
    MIN_CORRELATION_SCORE = 0.6  # MIN_CROSS_NODE_CORRELATION_SCORE
    TEMPORAL_WINDOW_DAYS = 90  # CROSS_NODE_TEMPORAL_WINDOW_DAYS
    
    def __init__(self):
        """Initialize correlator."""
        pass
    
    def correlate_node7_node8(
        self,
        node7_output: Any,
        node8_output: Any
    ) -> List[CrossNodeAlert]:
        """
        Correlate Node 7 (13F holdings) with Node 8 (13D/G ownership).
        
        Wolf pack formations in 13F that also have 13D filings represent
        heightened activist risk.
        
        Args:
            node7_output: Node 7 output with wolf pack alerts
            node8_output: Node 8 output with ownership alerts
            
        Returns:
            List of cross-node alerts
        """
        alerts = []
        
        if not node7_output or not node8_output:
            return alerts
        
        # Extract wolf packs from Node 7
        wolf_packs = getattr(node7_output, 'wolf_pack_alerts', [])
        if not wolf_packs:
            # Try legacy alerts
            wolf_packs = [a for a in getattr(node7_output, 'alerts', []) 
                         if hasattr(a, 'alert_type') and 'WOLF_PACK' in str(a.alert_type)]
        
        # Extract ownership alerts from Node 8
        ownership_alerts = getattr(node8_output, 'alerts', [])
        
        logger.info(f"Correlating {len(wolf_packs)} wolf packs with {len(ownership_alerts)} ownership alerts")
        
        for wolf_pack in wolf_packs:
            wolf_institutions = set(wolf_pack.institutions if hasattr(wolf_pack, 'institutions') else [])
            wolf_cusip = getattr(wolf_pack, 'cusip', None)
            
            for ownership_alert in ownership_alerts:
                # Extract party names from ownership alert
                parties = set()
                for party in getattr(ownership_alert, 'involved_parties', []):
                    if isinstance(party, dict):
                        parties.add(party.get('name', ''))
                    else:
                        parties.add(str(party))
                
                # Check for overlap
                overlap = wolf_institutions.intersection(parties)
                
                if overlap or (wolf_cusip and hasattr(ownership_alert, 'subject_company_cik')):
                    # Calculate correlation score
                    correlation_score = self._calculate_node7_node8_correlation(
                        wolf_pack, ownership_alert, overlap
                    )
                    
                    if correlation_score >= self.MIN_CORRELATION_SCORE:
                        # Calculate temporal window
                        dates = []
                        if hasattr(wolf_pack, 'filing_window_start'):
                            dates.append(wolf_pack.filing_window_start)
                        if hasattr(wolf_pack, 'filing_window_end'):
                            dates.append(wolf_pack.filing_window_end)
                        if hasattr(ownership_alert, 'timestamp'):
                            dates.append(ownership_alert.timestamp.date() if isinstance(ownership_alert.timestamp, datetime) else ownership_alert.timestamp)
                        
                        temporal_window = (max(dates) - min(dates)).days if len(dates) >= 2 else 0
                        
                        alert = CrossNodeAlert(
                            alert_type=CrossNodeAlertType.WOLF_PACK_13F_13D_CORRELATION,
                            cusip=wolf_cusip,
                            company_name=getattr(wolf_pack, 'issuer_name', 'Unknown'),
                            company_cik=getattr(ownership_alert, 'subject_company_cik', ''),
                            node7_data={
                                'wolf_pack_id': getattr(wolf_pack, 'pack_id', ''),
                                'institutions': list(wolf_institutions),
                                'coordination_score': getattr(wolf_pack, 'coordination_score', 0.0),
                                'aggregate_13f_ownership': getattr(wolf_pack, 'aggregate_ownership_percent', 0.0)
                            },
                            node8_data={
                                'alert_type': ownership_alert.alert_type.value if hasattr(ownership_alert, 'alert_type') else 'Unknown',
                                'parties': list(parties),
                                'aggregate_13d_ownership': getattr(ownership_alert, 'aggregate_ownership', 0.0),
                                'intent_score': getattr(ownership_alert.intent_analysis, 'intent_score', 0.0) if hasattr(ownership_alert, 'intent_analysis') else 0.0
                            },
                            correlation_score=correlation_score,
                            risk_indicators=[
                                f'{len(overlap)} overlapping institutions/parties detected',
                                f'Combined 13F + 13D ownership: {getattr(wolf_pack, "aggregate_ownership_percent", 0) + getattr(ownership_alert, "aggregate_ownership", 0):.2f}%',
                                'Coordinated activist campaign confirmed',
                                f'13F coordination score: {getattr(wolf_pack, "coordination_score", 0):.2f}',
                                f'13D intent score: {getattr(ownership_alert.intent_analysis, "intent_score", 0):.2f}' if hasattr(ownership_alert, 'intent_analysis') else ''
                            ],
                            regulatory_implications=[
                                'Potential Section 13(d)(3) group formation',
                                'SEC may require disclosure of coordination',
                                'Hart-Scott-Rodino notification may be triggered',
                                'Schedule 13D mandatory filing requirements',
                                'Heightened regulatory scrutiny expected'
                            ],
                            temporal_window_days=temporal_window,
                            earliest_signal_date=min(dates) if dates else None,
                            latest_signal_date=max(dates) if dates else None,
                            severity=Severity.CRITICAL,
                            evidence_chain=[
                                {'source': 'Node 7', 'type': '13F Wolf Pack', 'data': wolf_pack.to_dict() if hasattr(wolf_pack, 'to_dict') else str(wolf_pack)},
                                {'source': 'Node 8', 'type': '13D/G Filing', 'data': ownership_alert.to_dict() if hasattr(ownership_alert, 'to_dict') else str(ownership_alert)}
                            ]
                        )
                        
                        alerts.append(alert)
        
        logger.info(f"Generated {len(alerts)} Node 7 ↔ Node 8 cross-correlations")
        return alerts
    
    def correlate_node9_all(
        self,
        node9_output: Any,
        node1_trades: Optional[List[Dict]] = None,
        node7_output: Optional[Any] = None,
        node8_output: Optional[Any] = None
    ) -> List[CrossNodeAlert]:
        """
        Correlate Node 9 (8-K events) with all other nodes.
        
        Args:
            node9_output: Node 9 output with event alerts
            node1_trades: Optional Form 4 trades
            node7_output: Optional Node 7 output
            node8_output: Optional Node 8 output
            
        Returns:
            List of cross-node alerts
        """
        alerts = []
        
        if not node9_output or not hasattr(node9_output, 'alerts'):
            return alerts
        
        for event_alert in node9_output.alerts:
            # Check if alert has multi-source correlation
            has_node1 = event_alert.correlated_trades if hasattr(event_alert, 'correlated_trades') else None
            has_node7 = event_alert.node7_holdings_changes if hasattr(event_alert, 'node7_holdings_changes') else None
            has_node8 = event_alert.node8_ownership_changes if hasattr(event_alert, 'node8_ownership_changes') else None
            
            # Require at least 2 sources for cross-node alert
            source_count = sum([bool(has_node1), bool(has_node7), bool(has_node8)])
            
            if source_count >= 2:
                correlation_score = self._calculate_multi_node_correlation(
                    has_node1, has_node7, has_node8, event_alert
                )
                
                if correlation_score >= self.MIN_CORRELATION_SCORE:
                    event = getattr(event_alert, 'event', None)
                    
                    alert = CrossNodeAlert(
                        alert_type=CrossNodeAlertType.EVENT_INSIDER_INSTITUTIONAL_CORRELATION,
                        cusip=getattr(event, 'cusip', None) if event else None,
                        company_name=getattr(event, 'company_name', 'Unknown') if event else 'Unknown',
                        company_cik=getattr(event, 'cik', '') if event else '',
                        node1_data={'trade_count': len(has_node1)} if has_node1 else None,
                        node7_data={'alert_count': len(has_node7)} if has_node7 else None,
                        node8_data={'alert_count': len(has_node8)} if has_node8 else None,
                        node9_data={
                            'event_type': event_alert.alert_type.value if hasattr(event_alert, 'alert_type') else 'Unknown',
                            'items': getattr(event, 'items', []) if event else [],
                            'filing_date': str(getattr(event, 'filing_date', '')) if event else ''
                        },
                        correlation_score=correlation_score,
                        risk_indicators=[
                            f'Multi-source correlation detected ({source_count} nodes)',
                            'Coordinated activity across insider trades, institutional holdings, and/or beneficial ownership',
                            'Material event timing suspicious',
                            f'Risk score: {getattr(event_alert, "risk_score", 0):.2f}'
                        ],
                        regulatory_implications=[
                            'Potential Rule 10b-5 insider trading violation',
                            'SEC investigation recommended',
                            'Market manipulation indicators present',
                            'Coordinated group activity suspected'
                        ],
                        severity=Severity.CRITICAL if source_count >= 3 else Severity.HIGH
                    )
                    
                    alerts.append(alert)
        
        logger.info(f"Generated {len(alerts)} Node 9 ↔ All cross-correlations")
        return alerts
    
    def generate_unified_analysis(
        self,
        company_cik: str,
        company_name: str,
        node1_output: Optional[Any] = None,
        node7_output: Optional[Any] = None,
        node8_output: Optional[Any] = None,
        node9_output: Optional[Any] = None,
        analysis_start: Optional[date] = None,
        analysis_end: Optional[date] = None
    ) -> UnifiedForensicAnalysis:
        """
        Generate complete unified forensic analysis across all nodes.
        
        Args:
            company_cik: Company CIK
            company_name: Company name
            node1_output: Optional Node 1 output
            node7_output: Optional Node 7 output
            node8_output: Optional Node 8 output
            node9_output: Optional Node 9 output
            analysis_start: Analysis period start
            analysis_end: Analysis period end
            
        Returns:
            UnifiedForensicAnalysis
        """
        logger.info(f"Generating unified analysis for {company_name} (CIK: {company_cik})")
        
        # Generate cross-node alerts
        cross_alerts = []
        
        # Node 7 ↔ Node 8 correlation
        if node7_output and node8_output:
            cross_alerts.extend(self.correlate_node7_node8(node7_output, node8_output))
        
        # Node 9 ↔ All correlation
        if node9_output:
            cross_alerts.extend(self.correlate_node9_all(
                node9_output,
                node1_trades=None,  # Would need to extract from node1_output
                node7_output=node7_output,
                node8_output=node8_output
            ))
        
        # Calculate overall risk score
        risk_score = self._calculate_overall_risk_score(
            node1_output, node7_output, node8_output, node9_output, cross_alerts
        )
        
        # Gather risk factors
        risk_factors = []
        if cross_alerts:
            risk_factors.append(f'{len(cross_alerts)} cross-node correlations detected')
        if node7_output and hasattr(node7_output, 'wolf_pack_alerts'):
            if len(node7_output.wolf_pack_alerts) > 0:
                risk_factors.append(f'{len(node7_output.wolf_pack_alerts)} wolf pack formations')
        if node8_output and hasattr(node8_output, 'conversions_detected'):
            if node8_output.conversions_detected > 0:
                risk_factors.append(f'{node8_output.conversions_detected} 13G-to-13D conversions')
        if node9_output and hasattr(node9_output, 'critical_events'):
            if node9_output.critical_events > 0:
                risk_factors.append(f'{node9_output.critical_events} critical material events')
        
        # Gather statistics
        total_insider = 0
        total_institutional = len(getattr(node7_output, 'alerts', [])) if node7_output else 0
        total_ownership = len(getattr(node8_output, 'alerts', [])) if node8_output else 0
        total_events = getattr(node9_output, 'events_analyzed', 0) if node9_output else 0
        
        analysis = UnifiedForensicAnalysis(
            company_cik=company_cik,
            company_name=company_name,
            analysis_period_start=analysis_start or date.today(),
            analysis_period_end=analysis_end or date.today(),
            node1_output=node1_output,
            node7_output=node7_output,
            node8_output=node8_output,
            node9_output=node9_output,
            cross_node_alerts=cross_alerts,
            overall_risk_score=risk_score,
            risk_factors=risk_factors,
            total_insider_trades=total_insider,
            total_institutional_alerts=total_institutional,
            total_ownership_alerts=total_ownership,
            total_material_events=total_events,
            total_cross_node_correlations=len(cross_alerts)
        )
        
        logger.info(f"Unified analysis complete: {len(cross_alerts)} cross-correlations, risk score: {risk_score:.2f}")
        return analysis
    
    def _calculate_node7_node8_correlation(
        self,
        wolf_pack: Any,
        ownership_alert: Any,
        overlap: set
    ) -> float:
        """
        Calculate correlation score for Node 7 ↔ Node 8.
        
        Factors:
        - Number of overlapping institutions/parties
        - Combined ownership percentage
        - Coordination scores
        - Intent signals
        """
        score = 0.0
        
        # Overlap factor (max 0.4)
        if overlap:
            score += min(len(overlap) / 5, 0.4)
        
        # Coordination score factor (max 0.3)
        wolf_coord = getattr(wolf_pack, 'coordination_score', 0.0)
        score += wolf_coord * 0.3
        
        # Intent score factor (max 0.3)
        intent_score = 0.0
        if hasattr(ownership_alert, 'intent_analysis'):
            intent_score = getattr(ownership_alert.intent_analysis, 'intent_score', 0.0)
            # Normalize to 0-1 (from -1 to +1)
            intent_score = (intent_score + 1) / 2
        score += intent_score * 0.3
        
        return min(score, 1.0)
    
    def _calculate_multi_node_correlation(
        self,
        node1_data: Any,
        node7_data: Any,
        node8_data: Any,
        event_alert: Any
    ) -> float:
        """Calculate correlation score for multi-node event."""
        score = 0.0
        
        # Base score from number of sources
        source_count = sum([bool(node1_data), bool(node7_data), bool(node8_data)])
        score += (source_count / 3) * 0.4
        
        # Event risk score
        event_risk = getattr(event_alert, 'risk_score', 0.0)
        score += event_risk * 0.3
        
        # Data size factors
        if node1_data and hasattr(node1_data, '__len__'):
            score += min(len(node1_data) / 10, 0.1)
        if node7_data and hasattr(node7_data, '__len__'):
            score += min(len(node7_data) / 5, 0.1)
        if node8_data and hasattr(node8_data, '__len__'):
            score += min(len(node8_data) / 3, 0.1)
        
        return min(score, 1.0)
    
    def _calculate_overall_risk_score(
        self,
        node1_output: Any,
        node7_output: Any,
        node8_output: Any,
        node9_output: Any,
        cross_alerts: List[CrossNodeAlert]
    ) -> float:
        """Calculate overall unified risk score."""
        score = 0.0
        
        # Cross-node correlation factor (highest weight)
        if cross_alerts:
            avg_cross_score = sum(a.correlation_score for a in cross_alerts) / len(cross_alerts)
            score += avg_cross_score * 0.4
        
        # Individual node factors
        if node7_output:
            high_sev = getattr(node7_output, 'high_severity_count', 0)
            score += min(high_sev / 10, 0.15)
        
        if node8_output:
            high_sev = getattr(node8_output, 'high_severity_count', 0)
            score += min(high_sev / 10, 0.15)
        
        if node9_output:
            critical = getattr(node9_output, 'critical_events', 0)
            score += min(critical / 5, 0.15)
        
        # Critical if multiple CRITICAL severity cross-alerts
        critical_alerts = len([a for a in cross_alerts if a.severity == Severity.CRITICAL])
        if critical_alerts >= 2:
            score = max(score, 0.9)
        
        return min(score, 1.0)
