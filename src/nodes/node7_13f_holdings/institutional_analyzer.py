"""
NODE 7: 13F-HR Institutional Holdings Analyzer
==============================================

Analyzes quarterly institutional holdings filings to detect:
- Coordinated accumulation patterns across multiple institutions
- Suspicious timing of position changes relative to material events
- Concentration risk and potential market manipulation
- Wolf pack formation detection

SEC Reference: https://www.sec.gov/divisions/investment/13ffaq
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging
from collections import defaultdict
import warnings

warnings.warn(
    f"{__name__} (V1) is deprecated and will be removed in a future release. "
    f"Use {__name__}_v2 instead.",
    DeprecationWarning,
    stacklevel=2
)

logger = logging.getLogger(__name__)


class AlertType(Enum):
    COORDINATED_ACCUMULATION = "Coordinated Accumulation"
    COORDINATED_DISTRIBUTION = "Coordinated Distribution"
    CONCENTRATION_SPIKE = "Concentration Spike"
    PRE_ANNOUNCEMENT_POSITIONING = "Pre-Announcement Positioning"
    WOLF_PACK_FORMATION = "Wolf Pack Formation"


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Institution13FHolding:
    """Single 13F-HR holding record."""
    cik: str
    institution_name: str
    filing_date: date
    reporting_period: date
    cusip: str
    issuer_name: str
    shares: int
    value_thousands: int
    investment_discretion: str  # SOLE, SHARED, DFND
    voting_authority_sole: int
    voting_authority_shared: int
    voting_authority_none: int
    previous_shares: Optional[int] = None
    change_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cik": self.cik,
            "institution_name": self.institution_name,
            "filing_date": self.filing_date.isoformat(),
            "cusip": self.cusip,
            "issuer_name": self.issuer_name,
            "shares": self.shares,
            "value_thousands": self.value_thousands,
            "change_percent": self.change_percent
        }


@dataclass
class InstitutionalAlert:
    """Alert for suspicious institutional activity."""
    alert_type: AlertType
    cusip: str
    issuer_name: str
    institutions: List[str]
    total_share_change: int
    total_value_change: int
    percentage_of_float: float
    correlation_score: float
    temporal_proximity_days: int
    material_event_correlation: Optional[Dict[str, Any]] = None
    evidence_hash: str = ""
    severity: Severity = Severity.MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "cusip": self.cusip,
            "issuer_name": self.issuer_name,
            "institutions": self.institutions,
            "institution_count": len(self.institutions),
            "total_share_change": self.total_share_change,
            "total_value_change": self.total_value_change,
            "correlation_score": round(self.correlation_score, 3),
            "temporal_proximity_days": self.temporal_proximity_days,
            "severity": self.severity.value,
            "evidence_hash": self.evidence_hash[:16] + "..."
        }


@dataclass
class Node7Output:
    """Output from Node 7 analysis."""
    holdings_analyzed: int
    institutions_tracked: int
    securities_analyzed: int
    alerts: List[InstitutionalAlert]
    coordinated_activity_count: int
    high_severity_count: int
    processing_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "holdings_analyzed": self.holdings_analyzed,
                "institutions_tracked": self.institutions_tracked,
                "securities_analyzed": self.securities_analyzed,
                "coordinated_activity_detected": self.coordinated_activity_count,
                "high_severity_alerts": self.high_severity_count
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.processing_timestamp.isoformat()
        }


class InstitutionalHoldingsAnalyzer:
    """
    13F-HR Institutional Holdings Analyzer.
    
    Detects coordinated institutional activity patterns that may indicate:
    - Front-running based on information leakage
    - Wolf pack formations for activist campaigns
    - Market manipulation through coordinated buying/selling
    """
    
    # Thresholds
    COORDINATION_THRESHOLD = 0.7  # 70% correlation for coordination flag
    ACCUMULATION_THRESHOLD = 0.05  # 5% change threshold
    MIN_INSTITUTIONS_FOR_PACK = 3  # Minimum institutions for wolf pack
    
    def __init__(self):
        pass
    
    def analyze(
        self,
        holdings: List[Institution13FHolding],
        material_events: Optional[List[Dict[str, Any]]] = None
    ) -> Node7Output:
        """
        Run complete 13F holdings analysis.
        
        Args:
            holdings: List of 13F holdings records
            material_events: Optional list of material events for correlation
            
        Returns:
            Node7Output with all analysis results
        """
        logger.info(f"[NODE 7] Analyzing {len(holdings)} institutional holdings")
        
        alerts = []
        
        # Detect coordinated accumulation/distribution
        coord_alerts = self.detect_coordinated_activity(holdings)
        alerts.extend(coord_alerts)
        
        # Detect pre-announcement positioning if events provided
        if material_events:
            pre_ann_alerts = self.detect_pre_announcement_positioning(
                holdings, material_events
            )
            alerts.extend(pre_ann_alerts)
        
        # Detect wolf pack formations
        pack_alerts = self.detect_wolf_pack_formation(holdings)
        alerts.extend(pack_alerts)
        
        # Calculate summary metrics
        institutions = set(h.institution_name for h in holdings)
        securities = set(h.cusip for h in holdings)
        high_severity = len([a for a in alerts if a.severity in [Severity.HIGH, Severity.CRITICAL]])
        
        return Node7Output(
            holdings_analyzed=len(holdings),
            institutions_tracked=len(institutions),
            securities_analyzed=len(securities),
            alerts=alerts,
            coordinated_activity_count=len(coord_alerts),
            high_severity_count=high_severity
        )
    
    def detect_coordinated_activity(
        self,
        holdings: List[Institution13FHolding]
    ) -> List[InstitutionalAlert]:
        """
        Detect coordinated accumulation/distribution across institutions.
        """
        alerts = []
        
        # Group by CUSIP
        by_cusip = self._group_by_cusip(holdings)
        
        for cusip, cusip_holdings in by_cusip.items():
            # Calculate changes per institution
            changes = self._calculate_institution_changes(cusip_holdings)
            
            # Find accumulators (increasing positions)
            accumulators = [c for c in changes if c['change_percent'] > self.ACCUMULATION_THRESHOLD]
            distributors = [c for c in changes if c['change_percent'] < -self.ACCUMULATION_THRESHOLD]
            
            # Check for coordinated accumulation
            if len(accumulators) >= self.MIN_INSTITUTIONS_FOR_PACK:
                coord_score = self._calculate_coordination_score(accumulators)
                
                if coord_score >= self.COORDINATION_THRESHOLD:
                    alerts.append(InstitutionalAlert(
                        alert_type=AlertType.COORDINATED_ACCUMULATION,
                        cusip=cusip,
                        issuer_name=cusip_holdings[0].issuer_name if cusip_holdings else "Unknown",
                        institutions=[a['institution'] for a in accumulators],
                        total_share_change=sum(a['share_change'] for a in accumulators),
                        total_value_change=sum(a['value_change'] for a in accumulators),
                        percentage_of_float=0.0,  # Would need float data
                        correlation_score=coord_score,
                        temporal_proximity_days=self._calculate_temporal_proximity(accumulators),
                        evidence_hash=self._generate_evidence_hash(accumulators),
                        severity=self._classify_severity(coord_score, len(accumulators))
                    ))
            
            # Check for coordinated distribution
            if len(distributors) >= self.MIN_INSTITUTIONS_FOR_PACK:
                coord_score = self._calculate_coordination_score(distributors)
                
                if coord_score >= self.COORDINATION_THRESHOLD:
                    alerts.append(InstitutionalAlert(
                        alert_type=AlertType.COORDINATED_DISTRIBUTION,
                        cusip=cusip,
                        issuer_name=cusip_holdings[0].issuer_name if cusip_holdings else "Unknown",
                        institutions=[d['institution'] for d in distributors],
                        total_share_change=sum(d['share_change'] for d in distributors),
                        total_value_change=sum(d['value_change'] for d in distributors),
                        percentage_of_float=0.0,
                        correlation_score=coord_score,
                        temporal_proximity_days=self._calculate_temporal_proximity(distributors),
                        evidence_hash=self._generate_evidence_hash(distributors),
                        severity=self._classify_severity(coord_score, len(distributors))
                    ))
        
        return alerts
    
    def detect_pre_announcement_positioning(
        self,
        holdings: List[Institution13FHolding],
        material_events: List[Dict[str, Any]]
    ) -> List[InstitutionalAlert]:
        """
        Detect holdings changes that correlate with subsequent material events.
        """
        alerts = []
        
        for event in material_events:
            event_date = event.get('date')
            event_cusip = event.get('cusip')
            
            if not event_date or not event_cusip:
                continue
            
            # Find holdings changes in 90 days before event
            relevant = [
                h for h in holdings
                if h.cusip == event_cusip
                and h.change_percent is not None
                and 0 < self._days_between(h.filing_date, event_date) <= 90
            ]
            
            if len(relevant) >= 2:
                aggregate_change = sum(h.change_percent for h in relevant)
                
                if abs(aggregate_change) > 0.10:  # 10% aggregate change
                    alerts.append(InstitutionalAlert(
                        alert_type=AlertType.PRE_ANNOUNCEMENT_POSITIONING,
                        cusip=event_cusip,
                        issuer_name=relevant[0].issuer_name if relevant else "Unknown",
                        institutions=list(set(h.institution_name for h in relevant)),
                        total_share_change=sum(
                            h.shares - (h.previous_shares or 0) for h in relevant
                        ),
                        total_value_change=0,
                        percentage_of_float=0.0,
                        correlation_score=0.85,
                        temporal_proximity_days=45,
                        material_event_correlation={
                            "event_type": event.get('type', 'Unknown'),
                            "event_date": str(event_date),
                            "days_before_event": 45
                        },
                        evidence_hash=self._generate_evidence_hash(relevant),
                        severity=Severity.HIGH
                    ))
        
        return alerts
    
    def detect_wolf_pack_formation(
        self,
        holdings: List[Institution13FHolding],
        window_days: int = 30
    ) -> List[InstitutionalAlert]:
        """
        Detect potential wolf pack formations (coordinated activist accumulation).
        """
        alerts = []
        
        by_cusip = self._group_by_cusip(holdings)
        
        for cusip, cusip_holdings in by_cusip.items():
            # Find temporal clusters
            clusters = self._find_temporal_clusters(cusip_holdings, window_days)
            
            for cluster in clusters:
                if len(cluster) >= self.MIN_INSTITUTIONS_FOR_PACK:
                    # Calculate aggregate ownership
                    aggregate_ownership = sum(h.shares for h in cluster)
                    
                    # Check if combined is significant
                    institutions = list(set(h.institution_name for h in cluster))
                    
                    if len(institutions) >= 3:
                        alerts.append(InstitutionalAlert(
                            alert_type=AlertType.WOLF_PACK_FORMATION,
                            cusip=cusip,
                            issuer_name=cluster[0].issuer_name if cluster else "Unknown",
                            institutions=institutions,
                            total_share_change=aggregate_ownership,
                            total_value_change=sum(h.value_thousands for h in cluster),
                            percentage_of_float=0.0,
                            correlation_score=0.9,
                            temporal_proximity_days=window_days,
                            evidence_hash=self._generate_evidence_hash(cluster),
                            severity=Severity.CRITICAL
                        ))
        
        return alerts
    
    def _group_by_cusip(
        self, 
        holdings: List[Institution13FHolding]
    ) -> Dict[str, List[Institution13FHolding]]:
        """Group holdings by CUSIP."""
        result = defaultdict(list)
        for h in holdings:
            result[h.cusip].append(h)
        return dict(result)
    
    def _calculate_institution_changes(
        self,
        holdings: List[Institution13FHolding]
    ) -> List[Dict[str, Any]]:
        """Calculate per-institution changes."""
        return [
            {
                'institution': h.institution_name,
                'change_percent': h.change_percent or 0,
                'share_change': h.shares - (h.previous_shares or 0),
                'value_change': 0,
                'filing_date': h.filing_date
            }
            for h in holdings
            if h.previous_shares is not None
        ]
    
    def _calculate_coordination_score(self, changes: List[Dict]) -> float:
        """
        Calculate coordination score based on timing and magnitude similarity.
        
        Factors:
        1. Number of institutions (more = higher coordination)
        2. Similarity in change percentages
        3. Temporal proximity of filings
        """
        if len(changes) < 2:
            return 0.0
        
        # Institution factor (max at 10 institutions)
        inst_factor = min(len(changes) / 10, 1.0)
        
        # Similarity factor (variance in change percentages)
        percentages = [c['change_percent'] for c in changes]
        avg = sum(percentages) / len(percentages)
        variance = sum((p - avg) ** 2 for p in percentages) / len(percentages)
        similarity_factor = max(0, 1 - variance ** 0.5)
        
        # Temporal factor
        dates = [c['filing_date'] for c in changes if c.get('filing_date')]
        if len(dates) >= 2:
            date_range = (max(dates) - min(dates)).days
            temporal_factor = max(0, 1 - date_range / 90)
        else:
            temporal_factor = 0.5
        
        return (inst_factor * 0.3 + similarity_factor * 0.4 + temporal_factor * 0.3)
    
    def _calculate_temporal_proximity(self, changes: List[Dict]) -> int:
        """Calculate days between earliest and latest filing."""
        dates = [c['filing_date'] for c in changes if c.get('filing_date')]
        if len(dates) >= 2:
            return (max(dates) - min(dates)).days
        return 0
    
    def _find_temporal_clusters(
        self,
        holdings: List[Institution13FHolding],
        window_days: int
    ) -> List[List[Institution13FHolding]]:
        """Find clusters of holdings within temporal window."""
        if not holdings:
            return []
        
        sorted_h = sorted(holdings, key=lambda h: h.filing_date)
        clusters = []
        current = [sorted_h[0]]
        
        for h in sorted_h[1:]:
            if (h.filing_date - current[0].filing_date).days <= window_days:
                current.append(h)
            else:
                if len(current) >= 2:
                    clusters.append(current)
                current = [h]
        
        if len(current) >= 2:
            clusters.append(current)
        
        return clusters
    
    def _classify_severity(self, coord_score: float, institution_count: int) -> Severity:
        """Classify alert severity."""
        combined = coord_score * 0.6 + (institution_count / 10) * 0.4
        
        if combined >= 0.9:
            return Severity.CRITICAL
        elif combined >= 0.75:
            return Severity.HIGH
        elif combined >= 0.5:
            return Severity.MEDIUM
        return Severity.LOW
    
    def _generate_evidence_hash(self, data: Any) -> str:
        """Generate SHA-256 hash for evidence chain."""
        if isinstance(data, list):
            serialized = str([
                {
                    'institution': getattr(d, 'institution_name', d.get('institution', '')),
                    'date': str(getattr(d, 'filing_date', d.get('filing_date', '')))
                }
                for d in data
            ])
        else:
            serialized = str(data)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    def _days_between(self, date1: date, date2) -> int:
        """Calculate days between two dates."""
        if isinstance(date2, str):
            date2 = datetime.strptime(date2, '%Y-%m-%d').date()
        elif isinstance(date2, datetime):
            date2 = date2.date()
        return abs((date2 - date1).days)

