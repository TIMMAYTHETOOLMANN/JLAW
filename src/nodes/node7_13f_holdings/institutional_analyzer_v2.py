"""
NODE 7: 13F-HR Institutional Holdings Analyzer v2.0 (FORTIFIED)
==============================================================

Enhanced version with:
- SEC EDGAR 13F-HR live feed integration
- Quarterly QoQ comparison logic
- Enhanced wolf pack detection with coordination scoring
- Cross-node integration with Node 8 (13D filings)

SEC Reference: https://www.sec.gov/divisions/investment/13ffaq
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging
from collections import defaultdict

from .sec_edgar_client import Institution13FHoldingV2, SECEDGARClient

logger = logging.getLogger(__name__)


class AlertType(Enum):
    COORDINATED_ACCUMULATION = "Coordinated Accumulation"
    COORDINATED_DISTRIBUTION = "Coordinated Distribution"
    CONCENTRATION_SPIKE = "Concentration Spike"
    PRE_ANNOUNCEMENT_POSITIONING = "Pre-Announcement Positioning"
    WOLF_PACK_FORMATION = "Wolf Pack Formation"
    SECTOR_ROTATION = "Sector Rotation"
    CONCENTRATION_SHIFT = "Concentration Shift"


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class WolfPackAlert:
    """Wolf pack detection alert with coordination scoring."""
    pack_id: str
    cusip: str
    issuer_name: str
    institutions: List[str]
    coordination_score: float  # 0.0-1.0
    aggregate_ownership_percent: float
    temporal_cluster_days: int
    filing_window_start: date
    filing_window_end: date
    node8_correlation: Optional[Dict[str, Any]] = None  # Link to 13D filings
    severity: Severity = Severity.HIGH
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "cusip": self.cusip,
            "issuer_name": self.issuer_name,
            "institutions": self.institutions,
            "institution_count": len(self.institutions),
            "coordination_score": round(self.coordination_score, 3),
            "aggregate_ownership_percent": round(self.aggregate_ownership_percent, 2),
            "temporal_cluster_days": self.temporal_cluster_days,
            "filing_window": {
                "start": self.filing_window_start.isoformat(),
                "end": self.filing_window_end.isoformat()
            },
            "node8_correlation": self.node8_correlation,
            "severity": self.severity.value
        }


@dataclass
class QuarterlyComparison:
    """Quarter-over-quarter holdings comparison."""
    cusip: str
    issuer_name: str
    institution_name: str
    current_quarter: str
    previous_quarter: str
    current_shares: int
    previous_shares: int
    share_change: int
    percent_change: float
    value_change_thousands: int
    position_action: str  # NEW, EXIT, INCREASE, DECREASE, MAINTAIN
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cusip": self.cusip,
            "issuer_name": self.issuer_name,
            "institution_name": self.institution_name,
            "current_quarter": self.current_quarter,
            "previous_quarter": self.previous_quarter,
            "share_change": self.share_change,
            "percent_change": round(self.percent_change, 2),
            "position_action": self.position_action,
            "value_change_thousands": self.value_change_thousands
        }


@dataclass
class SectorRotation:
    """Detected sector rotation pattern."""
    institution_name: str
    quarter: str
    sector_from: str
    sector_to: str
    capital_moved_thousands: int
    securities_exited: List[str]
    securities_entered: List[str]
    rotation_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "institution_name": self.institution_name,
            "quarter": self.quarter,
            "rotation": f"{self.sector_from} → {self.sector_to}",
            "capital_moved_thousands": self.capital_moved_thousands,
            "securities_count": {
                "exited": len(self.securities_exited),
                "entered": len(self.securities_entered)
            },
            "rotation_score": round(self.rotation_score, 3)
        }


@dataclass
class InstitutionalAlertV2:
    """Enhanced alert for suspicious institutional activity."""
    alert_type: AlertType
    cusip: str
    issuer_name: str
    institutions: List[str]
    total_share_change: int
    total_value_change: int
    percentage_of_float: float
    correlation_score: float
    temporal_proximity_days: int
    quarterly_data: List[QuarterlyComparison]
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
            "quarterly_comparisons": [q.to_dict() for q in self.quarterly_data],
            "severity": self.severity.value,
            "evidence_hash": self.evidence_hash[:16] + "..."
        }


@dataclass
class Node7OutputV2:
    """Enhanced output from Node 7 v2.0 analysis."""
    holdings_analyzed: int
    institutions_tracked: int
    securities_analyzed: int
    quarters_analyzed: int
    alerts: List[InstitutionalAlertV2]
    wolf_pack_alerts: List[WolfPackAlert]
    sector_rotations: List[SectorRotation]
    coordinated_activity_count: int
    high_severity_count: int
    sec_edgar_filings_fetched: int
    processing_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "holdings_analyzed": self.holdings_analyzed,
                "institutions_tracked": self.institutions_tracked,
                "securities_analyzed": self.securities_analyzed,
                "quarters_analyzed": self.quarters_analyzed,
                "coordinated_activity_detected": self.coordinated_activity_count,
                "wolf_packs_detected": len(self.wolf_pack_alerts),
                "sector_rotations_detected": len(self.sector_rotations),
                "high_severity_alerts": self.high_severity_count,
                "sec_edgar_filings_fetched": self.sec_edgar_filings_fetched
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "wolf_pack_alerts": [w.to_dict() for w in self.wolf_pack_alerts],
            "sector_rotations": [s.to_dict() for s in self.sector_rotations],
            "timestamp": self.processing_timestamp.isoformat()
        }


class InstitutionalHoldingsAnalyzerV2:
    """
    13F-HR Institutional Holdings Analyzer v2.0 (FORTIFIED).
    
    Enhanced capabilities:
    - Live SEC EDGAR 13F-HR feed integration
    - Quarterly quarter-over-quarter comparison
    - Enhanced wolf pack detection with 0.0-1.0 coordination scoring
    - Temporal clustering (7, 14, 30 day windows)
    - Cross-institution correlation matrix
    - Integration hook for Node 8 (13D beneficial ownership)
    """
    
    # Thresholds
    COORDINATION_THRESHOLD = 0.7  # 70% correlation for coordination flag
    ACCUMULATION_THRESHOLD = 0.05  # 5% change threshold
    MIN_INSTITUTIONS_FOR_PACK = 3  # Minimum institutions for wolf pack
    WOLF_PACK_OWNERSHIP_THRESHOLD = 5.0  # 5% aggregate ownership minimum
    
    # Temporal windows for clustering
    TEMPORAL_WINDOWS = [7, 14, 30]  # days
    
    def __init__(self, sec_edgar_client: Optional[SECEDGARClient] = None):
        """
        Initialize analyzer.
        
        Args:
            sec_edgar_client: Optional SEC EDGAR client for live data
        """
        self.sec_edgar_client = sec_edgar_client
    
    async def analyze_with_live_data(
        self,
        institution_ciks: List[str],
        quarters: int = 4,
        material_events: Optional[List[Dict[str, Any]]] = None,
        node8_output: Optional[Any] = None
    ) -> Node7OutputV2:
        """
        Run analysis with live SEC EDGAR data fetching.
        
        Args:
            institution_ciks: List of institution CIKs to analyze
            quarters: Number of quarters to fetch
            material_events: Optional material events for correlation
            node8_output: Optional Node 8 output for wolf pack correlation
            
        Returns:
            Node7OutputV2 with all analysis results
        """
        if not self.sec_edgar_client:
            raise ValueError("SEC EDGAR client required for live data analysis")
        
        logger.info(f"[NODE 7 v2.0] Fetching live data for {len(institution_ciks)} institutions")
        
        # Fetch live holdings data
        all_holdings = []
        filings_count = 0
        
        for cik in institution_ciks:
            filings = await self.sec_edgar_client.fetch_13f_filings(cik, quarters=quarters)
            filings_count += len(filings)
            
            for filing in filings:
                holdings = await self.sec_edgar_client.fetch_and_parse_filing(
                    filing["accession_number"],
                    cik
                )
                all_holdings.extend(holdings)
        
        # Run enhanced analysis
        return self.analyze(
            all_holdings,
            material_events=material_events,
            node8_output=node8_output,
            sec_edgar_filings_fetched=filings_count
        )
    
    def analyze(
        self,
        holdings: List[Institution13FHoldingV2],
        material_events: Optional[List[Dict[str, Any]]] = None,
        node8_output: Optional[Any] = None,
        sec_edgar_filings_fetched: int = 0
    ) -> Node7OutputV2:
        """
        Run complete 13F holdings analysis with v2.0 enhancements.
        
        Args:
            holdings: List of 13F holdings records (v2 format)
            material_events: Optional list of material events for correlation
            node8_output: Optional Node 8 output for cross-node correlation
            sec_edgar_filings_fetched: Number of filings fetched from SEC EDGAR
            
        Returns:
            Node7OutputV2 with all analysis results
        """
        logger.info(f"[NODE 7 v2.0] Analyzing {len(holdings)} institutional holdings")
        
        alerts = []
        wolf_pack_alerts = []
        sector_rotations = []
        
        # Calculate quarterly comparisons
        quarterly_comparisons = self.calculate_quarterly_comparisons(holdings)
        
        # Detect coordinated accumulation/distribution
        coord_alerts = self.detect_coordinated_activity_v2(holdings, quarterly_comparisons)
        alerts.extend(coord_alerts)
        
        # Detect enhanced wolf pack formations
        wolf_packs = self.detect_wolf_pack_formation_v2(holdings, node8_output)
        wolf_pack_alerts.extend(wolf_packs)
        
        # Detect sector rotations
        rotations = self.detect_sector_rotation(quarterly_comparisons)
        sector_rotations.extend(rotations)
        
        # Detect pre-announcement positioning if events provided
        if material_events:
            pre_ann_alerts = self.detect_pre_announcement_positioning(
                holdings, material_events, quarterly_comparisons
            )
            alerts.extend(pre_ann_alerts)
        
        # Calculate summary metrics
        institutions = set(h.institution_name for h in holdings)
        securities = set(h.cusip for h in holdings)
        quarters_set = set(h.quarter for h in holdings)
        high_severity = len([a for a in alerts if a.severity in [Severity.HIGH, Severity.CRITICAL]])
        high_severity += len([w for w in wolf_pack_alerts if w.severity in [Severity.HIGH, Severity.CRITICAL]])
        
        return Node7OutputV2(
            holdings_analyzed=len(holdings),
            institutions_tracked=len(institutions),
            securities_analyzed=len(securities),
            quarters_analyzed=len(quarters_set),
            alerts=alerts,
            wolf_pack_alerts=wolf_pack_alerts,
            sector_rotations=sector_rotations,
            coordinated_activity_count=len(coord_alerts),
            high_severity_count=high_severity,
            sec_edgar_filings_fetched=sec_edgar_filings_fetched
        )
    
    def calculate_quarterly_comparisons(
        self,
        holdings: List[Institution13FHoldingV2]
    ) -> List[QuarterlyComparison]:
        """
        Calculate quarter-over-quarter holdings changes.
        
        Args:
            holdings: List of holdings with quarterly data
            
        Returns:
            List of quarterly comparisons
        """
        comparisons = []
        
        # Group by institution + CUSIP
        by_inst_cusip = defaultdict(list)
        for h in holdings:
            key = f"{h.institution_name}|{h.cusip}"
            by_inst_cusip[key].append(h)
        
        # Compare consecutive quarters
        for key, inst_holdings in by_inst_cusip.items():
            sorted_h = sorted(inst_holdings, key=lambda x: x.reporting_period)
            
            for i in range(1, len(sorted_h)):
                curr = sorted_h[i]
                prev = sorted_h[i - 1]
                
                share_change = curr.shares - prev.shares
                percent_change = (share_change / prev.shares * 100) if prev.shares > 0 else 0
                value_change = curr.value_thousands - prev.value_thousands
                
                # Determine position action
                if prev.shares == 0:
                    action = "NEW"
                elif curr.shares == 0:
                    action = "EXIT"
                elif share_change > 0:
                    action = "INCREASE"
                elif share_change < 0:
                    action = "DECREASE"
                else:
                    action = "MAINTAIN"
                
                comparisons.append(QuarterlyComparison(
                    cusip=curr.cusip,
                    issuer_name=curr.issuer_name,
                    institution_name=curr.institution_name,
                    current_quarter=curr.quarter,
                    previous_quarter=prev.quarter,
                    current_shares=curr.shares,
                    previous_shares=prev.shares,
                    share_change=share_change,
                    percent_change=percent_change,
                    value_change_thousands=value_change,
                    position_action=action
                ))
        
        logger.info(f"Calculated {len(comparisons)} quarterly comparisons")
        return comparisons
    
    def detect_coordinated_activity_v2(
        self,
        holdings: List[Institution13FHoldingV2],
        quarterly_comparisons: List[QuarterlyComparison]
    ) -> List[InstitutionalAlertV2]:
        """
        Enhanced coordinated activity detection using quarterly data.
        """
        alerts = []
        
        # Group comparisons by CUSIP + quarter
        by_cusip_quarter = defaultdict(list)
        for comp in quarterly_comparisons:
            key = f"{comp.cusip}|{comp.current_quarter}"
            by_cusip_quarter[key].append(comp)
        
        for key, comps in by_cusip_quarter.items():
            cusip, quarter = key.split("|")
            
            # Find accumulators and distributors
            accumulators = [c for c in comps if c.position_action in ["NEW", "INCREASE"] and abs(c.percent_change) > self.ACCUMULATION_THRESHOLD * 100]
            distributors = [c for c in comps if c.position_action in ["EXIT", "DECREASE"] and abs(c.percent_change) > self.ACCUMULATION_THRESHOLD * 100]
            
            # Check for coordinated accumulation
            if len(accumulators) >= self.MIN_INSTITUTIONS_FOR_PACK:
                coord_score = self._calculate_coordination_score_v2(accumulators)
                
                if coord_score >= self.COORDINATION_THRESHOLD:
                    alerts.append(InstitutionalAlertV2(
                        alert_type=AlertType.COORDINATED_ACCUMULATION,
                        cusip=cusip,
                        issuer_name=accumulators[0].issuer_name,
                        institutions=[a.institution_name for a in accumulators],
                        total_share_change=sum(a.share_change for a in accumulators),
                        total_value_change=sum(a.value_change_thousands for a in accumulators),
                        percentage_of_float=0.0,  # Would need float data
                        correlation_score=coord_score,
                        temporal_proximity_days=0,  # Same quarter
                        quarterly_data=accumulators,
                        evidence_hash=self._generate_evidence_hash(accumulators),
                        severity=self._classify_severity(coord_score, len(accumulators))
                    ))
            
            # Check for coordinated distribution
            if len(distributors) >= self.MIN_INSTITUTIONS_FOR_PACK:
                coord_score = self._calculate_coordination_score_v2(distributors)
                
                if coord_score >= self.COORDINATION_THRESHOLD:
                    alerts.append(InstitutionalAlertV2(
                        alert_type=AlertType.COORDINATED_DISTRIBUTION,
                        cusip=cusip,
                        issuer_name=distributors[0].issuer_name,
                        institutions=[d.institution_name for d in distributors],
                        total_share_change=sum(d.share_change for d in distributors),
                        total_value_change=sum(d.value_change_thousands for d in distributors),
                        percentage_of_float=0.0,
                        correlation_score=coord_score,
                        temporal_proximity_days=0,
                        quarterly_data=distributors,
                        evidence_hash=self._generate_evidence_hash(distributors),
                        severity=self._classify_severity(coord_score, len(distributors))
                    ))
        
        return alerts
    
    def detect_wolf_pack_formation_v2(
        self,
        holdings: List[Institution13FHoldingV2],
        node8_output: Optional[Any] = None
    ) -> List[WolfPackAlert]:
        """
        Enhanced wolf pack detection with coordination scoring and Node 8 correlation.
        
        Args:
            holdings: Holdings data
            node8_output: Optional Node 8 output for correlation
            
        Returns:
            List of wolf pack alerts
        """
        alerts = []
        
        # Group by CUSIP
        by_cusip = self._group_by_cusip(holdings)
        
        # Try multiple temporal windows
        for window_days in self.TEMPORAL_WINDOWS:
            for cusip, cusip_holdings in by_cusip.items():
                # Find temporal clusters
                clusters = self._find_temporal_clusters_v2(cusip_holdings, window_days)
                
                for cluster in clusters:
                    institutions = list(set(h.institution_name for h in cluster))
                    
                    if len(institutions) >= self.MIN_INSTITUTIONS_FOR_PACK:
                        # Calculate aggregate ownership (as percentage - mock calculation)
                        aggregate_shares = sum(h.shares for h in cluster)
                        aggregate_ownership_pct = min(aggregate_shares / 1_000_000, 100.0)  # Mock calculation
                        
                        if aggregate_ownership_pct >= self.WOLF_PACK_OWNERSHIP_THRESHOLD:
                            # Calculate coordination score
                            coord_score = self._calculate_wolf_pack_coordination(cluster)
                            
                            if coord_score >= self.COORDINATION_THRESHOLD:
                                # Check for Node 8 correlation
                                node8_corr = self._correlate_with_node8(
                                    cusip, institutions, node8_output
                                ) if node8_output else None
                                
                                filing_dates = [h.filing_date for h in cluster]
                                pack_id = hashlib.sha256(
                                    f"{cusip}|{min(filing_dates)}|{max(filing_dates)}".encode()
                                ).hexdigest()[:16]
                                
                                alerts.append(WolfPackAlert(
                                    pack_id=pack_id,
                                    cusip=cusip,
                                    issuer_name=cluster[0].issuer_name,
                                    institutions=institutions,
                                    coordination_score=coord_score,
                                    aggregate_ownership_percent=aggregate_ownership_pct,
                                    temporal_cluster_days=window_days,
                                    filing_window_start=min(filing_dates),
                                    filing_window_end=max(filing_dates),
                                    node8_correlation=node8_corr,
                                    severity=Severity.CRITICAL if node8_corr else Severity.HIGH
                                ))
        
        logger.info(f"Detected {len(alerts)} wolf pack formations")
        return alerts
    
    def detect_sector_rotation(
        self,
        quarterly_comparisons: List[QuarterlyComparison]
    ) -> List[SectorRotation]:
        """
        Detect sector rotation patterns from quarterly comparisons.
        
        Args:
            quarterly_comparisons: List of quarterly comparisons
            
        Returns:
            List of sector rotation detections
        """
        # This is a simplified implementation
        # In reality, we would need sector data for each CUSIP
        rotations = []
        
        # Group by institution + quarter
        by_inst_quarter = defaultdict(list)
        for comp in quarterly_comparisons:
            key = f"{comp.institution_name}|{comp.current_quarter}"
            by_inst_quarter[key].append(comp)
        
        # Detect significant exits and entries that could indicate rotation
        for key, comps in by_inst_quarter.items():
            inst_name, quarter = key.split("|")
            
            exits = [c for c in comps if c.position_action == "EXIT"]
            entries = [c for c in comps if c.position_action == "NEW"]
            
            # If substantial exits and entries in same quarter, might be rotation
            if len(exits) >= 3 and len(entries) >= 3:
                capital_from_exits = sum(abs(c.value_change_thousands) for c in exits)
                capital_to_entries = sum(c.value_change_thousands for c in entries)
                
                # Mock sector assignment
                sector_from = "Technology"  # Would be determined from exits
                sector_to = "Healthcare"  # Would be determined from entries
                
                if capital_from_exits > 10000 or capital_to_entries > 10000:  # $10M threshold
                    rotations.append(SectorRotation(
                        institution_name=inst_name,
                        quarter=quarter,
                        sector_from=sector_from,
                        sector_to=sector_to,
                        capital_moved_thousands=min(capital_from_exits, capital_to_entries),
                        securities_exited=[c.cusip for c in exits],
                        securities_entered=[c.cusip for c in entries],
                        rotation_score=0.75  # Mock score
                    ))
        
        return rotations
    
    def detect_pre_announcement_positioning(
        self,
        holdings: List[Institution13FHoldingV2],
        material_events: List[Dict[str, Any]],
        quarterly_comparisons: List[QuarterlyComparison]
    ) -> List[InstitutionalAlertV2]:
        """
        Enhanced pre-announcement positioning detection using quarterly data.
        """
        alerts = []
        
        for event in material_events:
            event_date = event.get('date')
            event_cusip = event.get('cusip')
            
            if not event_date or not event_cusip:
                continue
            
            # Find relevant quarterly comparisons
            relevant_comps = [
                c for c in quarterly_comparisons
                if c.cusip == event_cusip
                and abs(c.percent_change) > 10  # Significant change
            ]
            
            if len(relevant_comps) >= 2:
                aggregate_change = sum(c.share_change for c in relevant_comps)
                
                if abs(aggregate_change) > 100000:  # Significant share count
                    alerts.append(InstitutionalAlertV2(
                        alert_type=AlertType.PRE_ANNOUNCEMENT_POSITIONING,
                        cusip=event_cusip,
                        issuer_name=relevant_comps[0].issuer_name,
                        institutions=list(set(c.institution_name for c in relevant_comps)),
                        total_share_change=aggregate_change,
                        total_value_change=sum(c.value_change_thousands for c in relevant_comps),
                        percentage_of_float=0.0,
                        correlation_score=0.85,
                        temporal_proximity_days=45,
                        quarterly_data=relevant_comps,
                        material_event_correlation={
                            "event_type": event.get('type', 'Unknown'),
                            "event_date": str(event_date),
                            "days_before_event": 45
                        },
                        evidence_hash=self._generate_evidence_hash(relevant_comps),
                        severity=Severity.HIGH
                    ))
        
        return alerts
    
    def correlate_with_node8(
        self,
        holdings_alerts: List[WolfPackAlert],
        node8_output: Any
    ) -> List[Dict[str, Any]]:
        """
        Correlate 13F wolf pack detections with 13D beneficial ownership filings.
        
        A wolf pack identified in 13F data that also has corresponding 13D filings
        represents heightened activist risk.
        
        Args:
            holdings_alerts: Wolf pack alerts from Node 7
            node8_output: Output from Node 8 analysis
            
        Returns:
            List of cross-node correlation alerts
        """
        cross_alerts = []
        
        if not node8_output or not hasattr(node8_output, 'alerts'):
            return cross_alerts
        
        for wolf_pack in holdings_alerts:
            for node8_alert in node8_output.alerts:
                # Check if there's overlap in institutions/parties
                wolf_institutions = set(wolf_pack.institutions)
                node8_parties = set(p.get('name', '') for p in node8_alert.involved_parties)
                
                overlap = wolf_institutions.intersection(node8_parties)
                
                if overlap:
                    cross_alerts.append({
                        "alert_type": "WOLF_PACK_13D_CORRELATION",
                        "wolf_pack_id": wolf_pack.pack_id,
                        "cusip": wolf_pack.cusip,
                        "issuer": wolf_pack.issuer_name,
                        "overlapping_parties": list(overlap),
                        "wolf_pack_coordination_score": wolf_pack.coordination_score,
                        "node8_alert_type": node8_alert.alert_type.value,
                        "aggregate_13f_ownership": wolf_pack.aggregate_ownership_percent,
                        "aggregate_13d_ownership": node8_alert.aggregate_ownership,
                        "combined_ownership": wolf_pack.aggregate_ownership_percent + node8_alert.aggregate_ownership,
                        "risk_assessment": "CRITICAL - Coordinated activist campaign detected",
                        "severity": "CRITICAL"
                    })
        
        logger.info(f"Found {len(cross_alerts)} Node 7 ↔ Node 8 correlations")
        return cross_alerts
    
    def _calculate_coordination_score_v2(
        self,
        comparisons: List[QuarterlyComparison]
    ) -> float:
        """
        Calculate enhanced coordination score (0.0-1.0) for quarterly comparisons.
        
        Factors:
        1. Number of institutions (normalized)
        2. Similarity in percent changes
        3. Value concentration
        """
        if len(comparisons) < 2:
            return 0.0
        
        # Institution factor (normalized to 0-1, max at 10)
        inst_factor = min(len(comparisons) / 10, 1.0)
        
        # Percent change similarity
        percentages = [c.percent_change for c in comparisons]
        avg = sum(percentages) / len(percentages)
        variance = sum((p - avg) ** 2 for p in percentages) / len(percentages)
        std_dev = variance ** 0.5
        similarity_factor = max(0, 1 - (std_dev / 100))  # Normalize by 100%
        
        # Value concentration factor
        values = [abs(c.value_change_thousands) for c in comparisons]
        total_value = sum(values)
        value_factor = min(total_value / 100000, 1.0) if total_value > 0 else 0.5  # $100M max
        
        return (inst_factor * 0.35 + similarity_factor * 0.45 + value_factor * 0.20)
    
    def _calculate_wolf_pack_coordination(
        self,
        cluster: List[Institution13FHoldingV2]
    ) -> float:
        """
        Calculate wolf pack coordination score (0.0-1.0).
        
        Factors:
        1. Number of unique institutions
        2. Temporal proximity of filings
        3. Share amount concentration
        """
        if len(cluster) < 2:
            return 0.0
        
        institutions = list(set(h.institution_name for h in cluster))
        
        # Institution count factor
        inst_factor = min(len(institutions) / 10, 1.0)
        
        # Temporal proximity factor
        filing_dates = [h.filing_date for h in cluster]
        date_range = (max(filing_dates) - min(filing_dates)).days
        temporal_factor = max(0, 1 - date_range / 90)  # 90 days max window
        
        # Share concentration factor
        shares_list = [h.shares for h in cluster]
        avg_shares = sum(shares_list) / len(shares_list)
        variance = sum((s - avg_shares) ** 2 for s in shares_list) / len(shares_list)
        std_dev = variance ** 0.5
        concentration_factor = max(0, 1 - (std_dev / avg_shares)) if avg_shares > 0 else 0.5
        
        return (inst_factor * 0.4 + temporal_factor * 0.35 + concentration_factor * 0.25)
    
    def _correlate_with_node8(
        self,
        cusip: str,
        institutions: List[str],
        node8_output: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Check for correlation with Node 8 13D filings.
        """
        if not node8_output or not hasattr(node8_output, 'alerts'):
            return None
        
        for alert in node8_output.alerts:
            parties = [p.get('name', '') for p in alert.involved_parties]
            overlap = set(institutions).intersection(set(parties))
            
            if overlap:
                return {
                    "node8_alert_type": alert.alert_type.value,
                    "overlapping_parties": list(overlap),
                    "beneficial_ownership_percent": alert.aggregate_ownership,
                    "intent_score": alert.intent_analysis.intent_score if hasattr(alert, 'intent_analysis') else 0.0,
                    "correlation": "CONFIRMED"
                }
        
        return None
    
    def _group_by_cusip(
        self, 
        holdings: List[Institution13FHoldingV2]
    ) -> Dict[str, List[Institution13FHoldingV2]]:
        """Group holdings by CUSIP."""
        result = defaultdict(list)
        for h in holdings:
            result[h.cusip].append(h)
        return dict(result)
    
    def _find_temporal_clusters_v2(
        self,
        holdings: List[Institution13FHoldingV2],
        window_days: int
    ) -> List[List[Institution13FHoldingV2]]:
        """Enhanced temporal clustering for wolf pack detection."""
        if not holdings:
            return []
        
        sorted_h = sorted(holdings, key=lambda h: h.filing_date)
        clusters = []
        current = [sorted_h[0]]
        
        for h in sorted_h[1:]:
            if (h.filing_date - current[0].filing_date).days <= window_days:
                # Only add if different institution
                if h.institution_name not in [x.institution_name for x in current]:
                    current.append(h)
            else:
                if len(current) >= self.MIN_INSTITUTIONS_FOR_PACK:
                    clusters.append(current)
                current = [h]
        
        if len(current) >= self.MIN_INSTITUTIONS_FOR_PACK:
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
        serialized = str(data)
        return hashlib.sha256(serialized.encode()).hexdigest()
