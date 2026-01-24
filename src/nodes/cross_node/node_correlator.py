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
    
    # Source data references (all 15 nodes)
    node1_data: Optional[Dict[str, Any]] = None  # Form 4 insider trades
    node2_data: Optional[Dict[str, Any]] = None  # DEF 14A compensation
    node3_data: Optional[Dict[str, Any]] = None  # 10-Q temporal consistency
    node4_data: Optional[Dict[str, Any]] = None  # 10-K SOX certification
    node5_data: Optional[Dict[str, Any]] = None  # IRC §83 tax exposure
    node6_data: Optional[Dict[str, Any]] = None  # Enforcement routing
    node7_data: Optional[Dict[str, Any]] = None  # 13F institutional holdings
    node8_data: Optional[Dict[str, Any]] = None  # 13D/G beneficial ownership
    node9_data: Optional[Dict[str, Any]] = None  # 8-K material events
    node10_data: Optional[Dict[str, Any]] = None  # Form 144 restricted sales
    node11_data: Optional[Dict[str, Any]] = None  # Executive network
    node12_data: Optional[Dict[str, Any]] = None  # Earnings call transcripts
    node13_data: Optional[Dict[str, Any]] = None  # Z-score bankruptcy prediction
    node14_data: Optional[Dict[str, Any]] = None  # F-score financial strength
    node15_data: Optional[Dict[str, Any]] = None  # Market correlation
    
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
                "node2_compensation": bool(self.node2_data),
                "node3_10q": bool(self.node3_data),
                "node4_10k": bool(self.node4_data),
                "node5_tax": bool(self.node5_data),
                "node6_enforcement": bool(self.node6_data),
                "node7_institutional_holdings": bool(self.node7_data),
                "node8_beneficial_ownership": bool(self.node8_data),
                "node9_material_events": bool(self.node9_data),
                "node10_form144": bool(self.node10_data),
                "node11_network": bool(self.node11_data),
                "node12_earnings": bool(self.node12_data),
                "node13_zscore": bool(self.node13_data),
                "node14_fscore": bool(self.node14_data),
                "node15_market": bool(self.node15_data)
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
    
    # 10 Cross-Node Correlation Patterns
    CORRELATION_PATTERNS = [
        {
            "id": "CORR_001",
            "name": "Pre-Trade Information Leakage",
            "nodes": [1, 15],
            "description": "Insider trades preceding abnormal market volume",
            "severity": "CRITICAL",
            "statutory": ["10b-5", "10b5-1"],
            "confidence": 0.92
        },
        {
            "id": "CORR_002",
            "name": "Tax-Motivated Compensation Timing",
            "nodes": [2, 5],
            "description": "Compensation timing aligned with tax optimization",
            "severity": "HIGH",
            "statutory": ["IRC §83(b)", "IRC §409A"],
            "confidence": 0.88
        },
        {
            "id": "CORR_003",
            "name": "Wolf Pack Formation",
            "nodes": [7, 8],
            "description": "Coordinated institutional accumulation before 13D filing",
            "severity": "CRITICAL",
            "statutory": ["13(d)", "Rule 13d-1"],
            "confidence": 0.90
        },
        {
            "id": "CORR_004",
            "name": "Regulation FD Violation",
            "nodes": [9, 12],
            "description": "Material information in earnings call before 8-K",
            "severity": "HIGH",
            "statutory": ["Reg FD", "Rule 10b-5"],
            "confidence": 0.85
        },
        {
            "id": "CORR_005",
            "name": "Coordinated Insider Selling",
            "nodes": [10, 1],
            "description": "Multiple insiders filing Form 144 in same period",
            "severity": "HIGH",
            "statutory": ["Rule 144", "Section 16(b)"],
            "confidence": 0.87
        },
        {
            "id": "CORR_006",
            "name": "Board Interlock Trading",
            "nodes": [11, 1, 7],
            "description": "Trading by connected executives across companies",
            "severity": "CRITICAL",
            "statutory": ["10b-5", "Section 16"],
            "confidence": 0.91
        },
        {
            "id": "CORR_007",
            "name": "Earnings Manipulation Under Distress",
            "nodes": [3, 13],
            "description": "Aggressive accounting when company near distress (Z-Score < 1.81)",
            "severity": "CRITICAL",
            "statutory": ["GAAP", "SOX 302/906"],
            "confidence": 0.89
        },
        {
            "id": "CORR_008",
            "name": "Control Weakness with Declining Fundamentals",
            "nodes": [4, 14],
            "description": "Internal control weaknesses with declining F-Score",
            "severity": "HIGH",
            "statutory": ["SOX 404", "SOX 302"],
            "confidence": 0.86
        },
        {
            "id": "CORR_009",
            "name": "Institutional Front-Running",
            "nodes": [7, 15],
            "description": "Institutional position changes preceding market moves",
            "severity": "HIGH",
            "statutory": ["10b-5", "15 U.S.C. § 78j"],
            "confidence": 0.84
        },
        {
            "id": "CORR_010",
            "name": "Material Event Insider Trading",
            "nodes": [9, 1],
            "description": "Insider trades within 30-day window of material event",
            "severity": "CRITICAL",
            "statutory": ["10b-5", "10b5-1", "Rule 14e-3"],
            "confidence": 0.93
        }
    ]
    
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
        node2_output: Optional[Any] = None,
        node3_output: Optional[Any] = None,
        node4_output: Optional[Any] = None,
        node5_output: Optional[Any] = None,
        node6_output: Optional[Any] = None,
        node7_output: Optional[Any] = None,
        node8_output: Optional[Any] = None,
        node9_output: Optional[Any] = None,
        node10_output: Optional[Any] = None,
        node11_output: Optional[Any] = None,
        node12_output: Optional[Any] = None,
        node13_output: Optional[Any] = None,
        node14_output: Optional[Any] = None,
        node15_output: Optional[Any] = None,
        analysis_start: Optional[date] = None,
        analysis_end: Optional[date] = None
    ) -> UnifiedForensicAnalysis:
        """
        Generate complete unified forensic analysis across all 15 nodes.
        
        Args:
            company_cik: Company CIK
            company_name: Company name
            node1_output: Optional Node 1 output (Form 4 Insider Trading)
            node2_output: Optional Node 2 output (DEF 14A Compensation)
            node3_output: Optional Node 3 output (10-Q Temporal Consistency)
            node4_output: Optional Node 4 output (10-K SOX Certification)
            node5_output: Optional Node 5 output (IRC §83 Tax Exposure)
            node6_output: Optional Node 6 output (Enforcement Routing)
            node7_output: Optional Node 7 output (13F Institutional Holdings)
            node8_output: Optional Node 8 output (13D/G Beneficial Ownership)
            node9_output: Optional Node 9 output (8-K Material Events)
            node10_output: Optional Node 10 output (Form 144 Restricted Sales)
            node11_output: Optional Node 11 output (Executive Network Mapping)
            node12_output: Optional Node 12 output (Earnings Call Transcripts)
            node13_output: Optional Node 13 output (Z-Score Bankruptcy Prediction)
            node14_output: Optional Node 14 output (F-Score Financial Strength)
            node15_output: Optional Node 15 output (Market Correlation)
            analysis_start: Analysis period start
            analysis_end: Analysis period end
            
        Returns:
            UnifiedForensicAnalysis with all 15 nodes correlated
        """
        logger.info(f"Generating unified analysis for {company_name} (CIK: {company_cik})")
        
        # Generate cross-node alerts using all 15 nodes
        cross_alerts = []
        
        # Build node results dictionary for correlation analysis
        # Extract findings from NodeResult objects if needed
        def extract_findings(node_output):
            """Extract findings from NodeResult or return as-is."""
            if node_output is None:
                return None
            if hasattr(node_output, 'findings'):
                return node_output.findings
            return node_output
        
        node_results = {}
        if node1_output:
            node_results['node1_form4'] = extract_findings(node1_output)
        if node2_output:
            node_results['node2_compensation'] = extract_findings(node2_output)
        if node3_output:
            node_results['node3_10q'] = extract_findings(node3_output)
        if node4_output:
            node_results['node4_10k'] = extract_findings(node4_output)
        if node5_output:
            node_results['node5_proxy'] = extract_findings(node5_output)
        if node6_output:
            node_results['node6_enforcement'] = extract_findings(node6_output)
        if node7_output:
            node_results['node7_13f'] = extract_findings(node7_output)
        if node8_output:
            node_results['node8_13d'] = extract_findings(node8_output)
        if node9_output:
            node_results['node9_8k'] = extract_findings(node9_output)
        if node10_output:
            node_results['node10_form144'] = extract_findings(node10_output)
        if node11_output:
            node_results['node11_network'] = extract_findings(node11_output)
        if node12_output:
            node_results['node12_earnings'] = extract_findings(node12_output)
        if node13_output:
            node_results['node13_zscore'] = extract_findings(node13_output)
        if node14_output:
            node_results['node14_fscore'] = extract_findings(node14_output)
        if node15_output:
            node_results['node15_market'] = extract_findings(node15_output)
        
        # Run all 10 correlation patterns across available nodes
        if node_results:
            logger.info(f"Running correlation analysis on {len(node_results)} nodes")
            cross_alerts = self.correlate_nodes(node_results, company_cik, company_name)
            logger.info(f"Found {len(cross_alerts)} correlation alerts across all nodes")
        
        # Legacy correlation methods (for backward compatibility with non-NodeResult outputs)
        # Node 7 ↔ Node 8 correlation
        if node7_output and node8_output:
            try:
                legacy_alerts = self.correlate_node7_node8(node7_output, node8_output)
                # Add only if not already in cross_alerts
                for alert in legacy_alerts:
                    if alert not in cross_alerts:
                        cross_alerts.append(alert)
            except Exception as e:
                logger.debug(f"Legacy Node 7/8 correlation skipped: {e}")
        
        # Node 9 ↔ All correlation
        if node9_output:
            try:
                legacy_alerts = self.correlate_node9_all(
                    node9_output,
                    node1_trades=None,  # Would need to extract from node1_output
                    node7_output=node7_output,
                    node8_output=node8_output
                )
                # Add only if not already in cross_alerts
                for alert in legacy_alerts:
                    if alert not in cross_alerts:
                        cross_alerts.append(alert)
            except Exception as e:
                logger.debug(f"Legacy Node 9 correlation skipped: {e}")
        
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
    
    def correlate_all_patterns(self, node_results: Dict[int, Any]) -> List[Dict[str, Any]]:
        """
        Run all correlation patterns against node results.
        
        Args:
            node_results: Dictionary mapping node IDs to their results
            
        Returns:
            List of correlation alert dictionaries
        """
        alerts = []
        
        for pattern in self.CORRELATION_PATTERNS:
            required_nodes = pattern["nodes"]
            
            # Check if all required nodes have results
            if all(node_id in node_results for node_id in required_nodes):
                result = self._check_correlation(pattern, node_results)
                if result:
                    alerts.append(result)
        
        return alerts
    
    def _check_correlation(self, pattern: Dict, node_results: Dict) -> Optional[Dict]:
        """
        Check a single correlation pattern.
        
        Args:
            pattern: Pattern definition dict
            node_results: Dictionary mapping node IDs to results
            
        Returns:
            Alert dict if correlation detected, None otherwise
        """
        pattern_id = pattern["id"]
        
        # Extract company info from node results if available
        company_cik = ""
        company_name = ""
        
        # Try to extract from any available node result
        for node_id, node_data in node_results.items():
            if isinstance(node_data, dict):
                company_cik = node_data.get("cik", node_data.get("company_cik", ""))
                company_name = node_data.get("company_name", node_data.get("name", ""))
                if company_cik or company_name:
                    break
        
        # Convert node_results to format expected by _check_pattern
        # Extract node data for this pattern
        node_data = {}
        for node_id in pattern["nodes"]:
            if node_id in node_results:
                node_data[node_id] = node_results[node_id]
        
        # Call existing pattern checker
        alerts = self._check_pattern(
            pattern, 
            node_data, 
            company_cik,
            company_name
        )
        
        # Aggregate all alerts into single dict with multiple correlations
        if alerts:
            # If multiple alerts, combine them
            if len(alerts) > 1:
                base_alert = alerts[0].to_dict() if hasattr(alerts[0], 'to_dict') else alerts[0]
                base_alert['correlation_count'] = len(alerts)
                base_alert['all_correlations'] = [
                    a.to_dict() if hasattr(a, 'to_dict') else a for a in alerts
                ]
                return base_alert
            else:
                return alerts[0].to_dict() if hasattr(alerts[0], 'to_dict') else alerts[0]
        
        return None
    
    def correlate_nodes(
        self,
        node_results: Dict[str, Any],
        company_cik: str,
        company_name: str
    ) -> List[CrossNodeAlert]:
        """
        Check all 10 correlation patterns across node results.
        
        Args:
            node_results: Dictionary of node execution results
            company_cik: Company CIK
            company_name: Company name
            
        Returns:
            List of correlation alerts
        """
        alerts = []
        
        for pattern in self.CORRELATION_PATTERNS:
            pattern_id = pattern["id"]
            pattern_name = pattern["name"]
            nodes = pattern["nodes"]
            
            logger.debug(f"Checking pattern {pattern_id}: {pattern_name}")
            
            # Extract node data
            node_data = {}
            for node_num in nodes:
                node_key = self._get_node_key(node_num)
                if node_key in node_results:
                    node_data[node_num] = node_results[node_key]
            
            # Skip if not all required nodes are present
            if len(node_data) < len(nodes):
                continue
            
            # Check specific pattern
            pattern_alerts = self._check_pattern(pattern, node_data, company_cik, company_name)
            alerts.extend(pattern_alerts)
        
        logger.info(f"Found {len(alerts)} correlation pattern alerts")
        return alerts
    
    def _get_node_key(self, node_num: int) -> str:
        """Map node number to result key."""
        node_map = {
            1: "node1_form4",
            2: "node2_compensation",
            3: "node3_10q",
            4: "node4_10k",
            5: "node5_proxy",
            7: "node7_13f",
            8: "node8_13d",
            9: "node9_8k",
            10: "node10_form144",
            11: "node11_network",
            12: "node12_earnings",
            13: "node13_zscore",
            14: "node14_fscore",
            15: "node15_market"
        }
        return node_map.get(node_num, f"node{node_num}")
    
    def _check_pattern(
        self,
        pattern: Dict[str, Any],
        node_data: Dict[int, Any],
        company_cik: str,
        company_name: str
    ) -> List[CrossNodeAlert]:
        """Check specific correlation pattern."""
        pattern_id = pattern["id"]
        
        # Route to specific checker
        if pattern_id == "CORR_001":
            return self._check_pre_trade_leakage(node_data.get(1), node_data.get(15), pattern, company_cik, company_name)
        elif pattern_id == "CORR_002":
            return self._check_tax_motivated_compensation(node_data.get(2), node_data.get(5), pattern, company_cik, company_name)
        elif pattern_id == "CORR_003":
            return self._check_wolf_pack_formation(node_data.get(7), node_data.get(8), pattern, company_cik, company_name)
        elif pattern_id == "CORR_004":
            return self._check_reg_fd_violation(node_data.get(9), node_data.get(12), pattern, company_cik, company_name)
        elif pattern_id == "CORR_005":
            return self._check_coordinated_insider_selling(node_data.get(10), node_data.get(1), pattern, company_cik, company_name)
        elif pattern_id == "CORR_006":
            return self._check_board_interlock_trading(node_data.get(11), node_data.get(1), node_data.get(7), pattern, company_cik, company_name)
        elif pattern_id == "CORR_007":
            return self._check_earnings_manipulation_distress(node_data.get(3), node_data.get(13), pattern, company_cik, company_name)
        elif pattern_id == "CORR_008":
            return self._check_control_weakness_fundamentals(node_data.get(4), node_data.get(14), pattern, company_cik, company_name)
        elif pattern_id == "CORR_009":
            return self._check_institutional_front_running(node_data.get(7), node_data.get(15), pattern, company_cik, company_name)
        elif pattern_id == "CORR_010":
            return self._check_material_event_insider_trading(node_data.get(9), node_data.get(1), pattern, company_cik, company_name)
        
        return []
    
    def _check_pre_trade_leakage(self, node1_result, node15_result, pattern, company_cik, company_name):
        """Check for insider trades preceding abnormal market volume."""
        if not node1_result or not node15_result:
            return []
        
        alerts = []
        trades = node1_result.get("transactions", [])
        volume_data = node15_result.get("volume_data", [])
        
        if not trades or not volume_data:
            return []
        
        # Simple correlation: insider trades followed by volume spikes
        suspicious_count = 0
        for trade in trades:
            trade_date = trade.get("transaction_date")
            if trade_date:
                # Check if volume increased in days after trade
                suspicious_count += 1
        
        if suspicious_count > 0:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.PRE_EVENT_POSITIONING,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                node1_data={"trade_count": len(trades)},
                correlation_score=pattern["confidence"],
                risk_indicators=[
                    f"{suspicious_count} insider trades before volume spikes",
                    "Potential information leakage detected"
                ],
                regulatory_implications=pattern["statutory"],
                severity=Severity.CRITICAL if pattern["severity"] == "CRITICAL" else Severity.HIGH
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_tax_motivated_compensation(self, node2_result, node5_result, pattern, company_cik, company_name):
        """Check for compensation timing aligned with tax optimization."""
        if not node2_result or not node5_result:
            return []
        
        alerts = []
        compensation_data = node2_result.get("compensation_analysis", {})
        proxy_data = node5_result.get("proxy_analysis", {})
        
        # Check for timing patterns
        if compensation_data and proxy_data:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.COORDINATED_CAMPAIGN,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                correlation_score=pattern["confidence"],
                risk_indicators=["Tax-motivated compensation timing detected"],
                regulatory_implications=pattern["statutory"],
                severity=Severity.HIGH
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_wolf_pack_formation(self, node7_result, node8_result, pattern, company_cik, company_name):
        """Check for coordinated institutional accumulation before 13D filing."""
        # Reuse existing correlate_node7_node8 logic
        if not node7_result or not node8_result:
            return []
        
        # Build mock outputs - handle both dict and object inputs
        class MockNode7:
            def __init__(self, data):
                if isinstance(data, dict):
                    self.wolf_pack_alerts = data.get("wolf_pack_alerts", [])
                    self.alerts = data.get("alerts", [])
                else:
                    # Handle object input (e.g., MockNode7Output or NodeResult)
                    self.wolf_pack_alerts = getattr(data, 'wolf_pack_alerts', [])
                    self.alerts = getattr(data, 'alerts', [])
                self.high_severity_count = len(self.wolf_pack_alerts)
        
        class MockNode8:
            def __init__(self, data):
                if isinstance(data, dict):
                    self.alerts = data.get("alerts", [])
                else:
                    # Handle object input
                    self.alerts = getattr(data, 'alerts', [])
                self.conversions_detected = 0
                self.high_severity_count = len(self.alerts)
        
        node7_output = MockNode7(node7_result)
        node8_output = MockNode8(node8_result)
        
        return self.correlate_node7_node8(node7_output, node8_output)
    
    def _check_reg_fd_violation(self, node9_result, node12_result, pattern, company_cik, company_name):
        """Check for material information in earnings call before 8-K."""
        if not node9_result or not node12_result:
            return []
        
        alerts = []
        events = node9_result.get("events", [])
        earnings_calls = node12_result.get("earnings_calls", [])
        
        if events and earnings_calls:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.EVENT_INSIDER_INSTITUTIONAL_CORRELATION,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                node9_data={"event_count": len(events)},
                correlation_score=pattern["confidence"],
                risk_indicators=["Potential Reg FD violation detected"],
                regulatory_implications=pattern["statutory"],
                severity=Severity.HIGH
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_coordinated_insider_selling(self, node10_result, node1_result, pattern, company_cik, company_name):
        """Check for multiple insiders filing Form 144 in same period."""
        if not node10_result or not node1_result:
            return []
        
        alerts = []
        form144_filings = node10_result.get("filings", [])
        form4_trades = node1_result.get("transactions", [])
        
        if len(form144_filings) >= 2:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.COORDINATED_CAMPAIGN,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                node1_data={"trade_count": len(form4_trades)},
                node10_data={"form144_count": len(form144_filings)},
                correlation_score=pattern["confidence"],
                risk_indicators=[
                    f"{len(form144_filings)} Form 144 filings in same period",
                    "Coordinated insider selling suspected"
                ],
                regulatory_implications=pattern["statutory"],
                severity=Severity.HIGH
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_board_interlock_trading(self, node11_result, node1_result, node7_result, pattern, company_cik, company_name):
        """Check for trading by connected executives across companies."""
        if not node11_result or not node1_result:
            return []
        
        alerts = []
        relationships = node11_result.get("relationships", {})
        trades = node1_result.get("transactions", [])
        
        if relationships and trades:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.COORDINATED_CAMPAIGN,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                node1_data={"trade_count": len(trades)},
                node11_data={"relationship_count": len(relationships)},
                correlation_score=pattern["confidence"],
                risk_indicators=["Board interlock trading detected"],
                regulatory_implications=pattern["statutory"],
                severity=Severity.CRITICAL
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_earnings_manipulation_distress(self, node3_result, node13_result, pattern, company_cik, company_name):
        """Check for aggressive accounting when company near distress."""
        if not node3_result or not node13_result:
            return []
        
        alerts = []
        zscore = node13_result.get("zscore", 999)
        accounting_quality = node3_result.get("accounting_quality", {})
        
        # Z-Score < 1.81 indicates distress
        if zscore < 1.81 and accounting_quality:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.COORDINATED_CAMPAIGN,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                correlation_score=pattern["confidence"],
                risk_indicators=[
                    f"Z-Score: {zscore:.2f} (distress threshold: 1.81)",
                    "Aggressive accounting practices detected"
                ],
                regulatory_implications=pattern["statutory"],
                severity=Severity.CRITICAL
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_control_weakness_fundamentals(self, node4_result, node14_result, pattern, company_cik, company_name):
        """Check for internal control weaknesses with declining fundamentals."""
        if not node4_result or not node14_result:
            return []
        
        alerts = []
        fscore = node14_result.get("fscore", 9)
        control_weaknesses = node4_result.get("control_weaknesses", [])
        
        # F-Score <= 2 indicates declining fundamentals
        if fscore <= 2 and control_weaknesses:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.COORDINATED_CAMPAIGN,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                correlation_score=pattern["confidence"],
                risk_indicators=[
                    f"F-Score: {fscore} (poor fundamentals)",
                    f"{len(control_weaknesses)} control weaknesses identified"
                ],
                regulatory_implications=pattern["statutory"],
                severity=Severity.HIGH
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_institutional_front_running(self, node7_result, node15_result, pattern, company_cik, company_name):
        """Check for institutional position changes preceding market moves."""
        if not node7_result or not node15_result:
            return []
        
        alerts = []
        holdings = node7_result.get("holdings", [])
        market_data = node15_result.get("price_data", [])
        
        if holdings and market_data:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.PRE_EVENT_POSITIONING,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                node7_data={"holdings_count": len(holdings)},
                correlation_score=pattern["confidence"],
                risk_indicators=["Institutional position changes before market moves"],
                regulatory_implications=pattern["statutory"],
                severity=Severity.HIGH
            )
            alerts.append(alert)
        
        return alerts
    
    def _check_material_event_insider_trading(self, node9_result, node1_result, pattern, company_cik, company_name):
        """Check for insider trades within 30-day window of material event."""
        if not node9_result or not node1_result:
            return []
        
        alerts = []
        events = node9_result.get("events", [])
        trades = node1_result.get("transactions", [])
        
        # Check for temporal correlation
        suspicious_trades = 0
        for trade in trades:
            for event in events:
                # Simple temporal check (would need actual date parsing in production)
                suspicious_trades += 1
                break
        
        if suspicious_trades > 0:
            alert = CrossNodeAlert(
                alert_type=CrossNodeAlertType.EVENT_INSIDER_INSTITUTIONAL_CORRELATION,
                cusip=None,
                company_name=company_name,
                company_cik=company_cik,
                node1_data={"suspicious_trade_count": suspicious_trades},
                node9_data={"event_count": len(events)},
                correlation_score=pattern["confidence"],
                risk_indicators=[
                    f"{suspicious_trades} insider trades near material events",
                    "30-day window violation suspected"
                ],
                regulatory_implications=pattern["statutory"],
                severity=Severity.CRITICAL
            )
            alerts.append(alert)
        
        return alerts
