"""
Rule 144(e)(3) Affiliate Volume Aggregator
==========================================

Implements affiliate volume aggregation for Rule 144(e) volume limitations.

Under Rule 144(e)(3), sales by affiliates and persons acting in concert must
be aggregated within the applicable 90-day period.

SEC Reference: 17 CFR §230.144(e)(3)
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AffiliateRelationship(Enum):
    """Types of affiliate relationships."""
    OFFICER = "Officer"
    DIRECTOR = "Director"
    TEN_PERCENT_OWNER = "10% Beneficial Owner"
    CONTROL_PERSON = "Control Person"
    ACTING_IN_CONCERT = "Acting in Concert"
    FAMILY_MEMBER = "Family Member"
    TRUST_BENEFICIARY = "Trust Beneficiary"


@dataclass
class AffiliateSale:
    """Individual sale by an affiliate."""
    sale_date: date
    affiliate_cik: str
    affiliate_name: str
    relationship: AffiliateRelationship
    shares_sold: int
    sale_value: float
    form_144_accession: str
    issuer_cik: str
    issuer_name: str


@dataclass
class AggregatedVolume:
    """Aggregated volume for a group of affiliates."""
    issuer_cik: str
    issuer_name: str
    window_start: date
    window_end: date
    total_shares: int
    total_value: float
    affiliate_count: int
    affiliates: List[str]
    sales: List[AffiliateSale]
    
    def to_dict(self):
        return {
            "issuer_cik": self.issuer_cik,
            "issuer_name": self.issuer_name,
            "window": {
                "start": self.window_start.isoformat(),
                "end": self.window_end.isoformat(),
                "days": (self.window_end - self.window_start).days
            },
            "aggregated_volume": {
                "total_shares": self.total_shares,
                "total_value": self.total_value,
                "affiliate_count": self.affiliate_count,
                "affiliates": self.affiliates
            },
            "sales_count": len(self.sales)
        }


@dataclass
class VolumeViolation:
    """Volume limit violation alert."""
    issuer_cik: str
    issuer_name: str
    window_start: date
    window_end: date
    aggregated_shares: int
    volume_limit: int
    outstanding_shares: int
    percent_of_outstanding: float
    excess_shares: int
    violation_severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    involved_affiliates: List[str]
    
    def to_dict(self):
        return {
            "issuer": {
                "cik": self.issuer_cik,
                "name": self.issuer_name
            },
            "window": {
                "start": self.window_start.isoformat(),
                "end": self.window_end.isoformat()
            },
            "volume_analysis": {
                "aggregated_shares": self.aggregated_shares,
                "volume_limit": self.volume_limit,
                "outstanding_shares": self.outstanding_shares,
                "percent_of_outstanding": round(self.percent_of_outstanding, 4),
                "excess_shares": self.excess_shares,
                "excess_percent": round((self.excess_shares / self.volume_limit) * 100, 2)
            },
            "violation_severity": self.violation_severity,
            "involved_affiliates": self.involved_affiliates,
            "affiliate_count": len(self.involved_affiliates)
        }


class AffiliateVolumeAggregator:
    """
    Aggregates affiliate sales volume for Rule 144(e) compliance checking.
    
    Rule 144(e) limits sales to the greater of:
    - 1% of outstanding shares, or
    - Average weekly trading volume over preceding 4 weeks
    
    Rule 144(e)(3) requires aggregation of sales by:
    - All affiliates of the issuer
    - Persons acting in concert
    within any 90-day period.
    """
    
    def __init__(self, aggregation_window_days: int = 90):
        """
        Initialize the aggregator.
        
        Args:
            aggregation_window_days: Window for volume aggregation (default 90)
        """
        self.aggregation_window_days = aggregation_window_days
        self.logger = logger
    
    def aggregate_sales_by_issuer(
        self,
        sales: List[AffiliateSale],
        as_of_date: Optional[date] = None
    ) -> Dict[str, List[AggregatedVolume]]:
        """
        Aggregate sales by issuer across all 90-day windows.
        
        Args:
            sales: List of affiliate sales
            as_of_date: Date to calculate windows as of (defaults to today)
        
        Returns:
            Dictionary mapping issuer_cik to list of aggregated volumes
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Group sales by issuer
        issuer_sales = defaultdict(list)
        for sale in sales:
            issuer_sales[sale.issuer_cik].append(sale)
        
        # Aggregate each issuer's sales
        result = {}
        for issuer_cik, issuer_sales_list in issuer_sales.items():
            result[issuer_cik] = self._aggregate_issuer_sales(
                issuer_sales_list,
                as_of_date
            )
        
        return result
    
    def _aggregate_issuer_sales(
        self,
        sales: List[AffiliateSale],
        as_of_date: date
    ) -> List[AggregatedVolume]:
        """
        Aggregate sales for a single issuer across all applicable windows.
        
        Creates overlapping 90-day windows starting from each sale date.
        """
        if not sales:
            return []
        
        # Sort sales by date
        sorted_sales = sorted(sales, key=lambda s: s.sale_date)
        
        aggregated_volumes = []
        
        # Create a 90-day window starting from each unique sale date
        unique_dates = sorted(set(sale.sale_date for sale in sorted_sales))
        
        for window_start in unique_dates:
            window_end = window_start + timedelta(days=self.aggregation_window_days - 1)
            
            # Only process windows that are complete (end date <= as_of_date)
            if window_end > as_of_date:
                continue
            
            # Find all sales in this window
            window_sales = [
                sale for sale in sorted_sales
                if window_start <= sale.sale_date <= window_end
            ]
            
            if window_sales:
                # Calculate aggregated metrics
                total_shares = sum(sale.shares_sold for sale in window_sales)
                total_value = sum(sale.sale_value for sale in window_sales)
                affiliates = list(set(sale.affiliate_name for sale in window_sales))
                
                aggregated = AggregatedVolume(
                    issuer_cik=window_sales[0].issuer_cik,
                    issuer_name=window_sales[0].issuer_name,
                    window_start=window_start,
                    window_end=window_end,
                    total_shares=total_shares,
                    total_value=total_value,
                    affiliate_count=len(affiliates),
                    affiliates=affiliates,
                    sales=window_sales
                )
                
                aggregated_volumes.append(aggregated)
        
        return aggregated_volumes
    
    def detect_volume_violations(
        self,
        aggregated_volumes: List[AggregatedVolume],
        outstanding_shares: int,
        avg_weekly_trading_volume: Optional[int] = None
    ) -> List[VolumeViolation]:
        """
        Detect volume limit violations.
        
        Args:
            aggregated_volumes: List of aggregated volume windows
            outstanding_shares: Total outstanding shares for the issuer
            avg_weekly_trading_volume: Average weekly trading volume (optional)
        
        Returns:
            List of volume violations
        """
        violations = []
        
        # Calculate volume limit (greater of 1% or avg weekly volume)
        one_percent_limit = int(outstanding_shares * 0.01)
        
        if avg_weekly_trading_volume is not None:
            volume_limit = max(one_percent_limit, avg_weekly_trading_volume)
        else:
            # If no trading volume data, use 1% limit
            volume_limit = one_percent_limit
        
        # Check each window for violations
        for agg_vol in aggregated_volumes:
            if agg_vol.total_shares > volume_limit:
                excess_shares = agg_vol.total_shares - volume_limit
                percent_of_outstanding = (agg_vol.total_shares / outstanding_shares) * 100
                
                # Determine severity
                excess_ratio = agg_vol.total_shares / volume_limit
                if excess_ratio >= 2.0:
                    severity = "CRITICAL"
                elif excess_ratio >= 1.5:
                    severity = "HIGH"
                elif excess_ratio >= 1.2:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
                
                violation = VolumeViolation(
                    issuer_cik=agg_vol.issuer_cik,
                    issuer_name=agg_vol.issuer_name,
                    window_start=agg_vol.window_start,
                    window_end=agg_vol.window_end,
                    aggregated_shares=agg_vol.total_shares,
                    volume_limit=volume_limit,
                    outstanding_shares=outstanding_shares,
                    percent_of_outstanding=percent_of_outstanding,
                    excess_shares=excess_shares,
                    violation_severity=severity,
                    involved_affiliates=agg_vol.affiliates
                )
                
                violations.append(violation)
        
        return violations
    
    def identify_acting_in_concert(
        self,
        sales: List[AffiliateSale],
        temporal_threshold_days: int = 7,
        min_participants: int = 2
    ) -> List[Dict[str, any]]:
        """
        Identify potential "acting in concert" groups.
        
        Flags when multiple affiliates make sales within a narrow time window,
        suggesting coordination.
        
        Args:
            sales: List of affiliate sales
            temporal_threshold_days: Days within which sales are suspicious
            min_participants: Minimum number of participants for a group
        
        Returns:
            List of potential coordinated sale groups
        """
        if not sales:
            return []
        
        # Sort sales by date
        sorted_sales = sorted(sales, key=lambda s: s.sale_date)
        
        coordinated_groups = []
        
        # Use sliding window to find temporal clusters
        for i, sale in enumerate(sorted_sales):
            window_start = sale.sale_date
            window_end = window_start + timedelta(days=temporal_threshold_days)
            
            # Find all sales in this window
            cluster = [
                s for s in sorted_sales[i:]
                if window_start <= s.sale_date <= window_end
            ]
            
            # Check if cluster meets minimum participants
            unique_affiliates = set(s.affiliate_cik for s in cluster)
            
            if len(unique_affiliates) >= min_participants:
                # Check if this is a new group (not already reported)
                group_key = tuple(sorted(unique_affiliates))
                existing = any(
                    tuple(sorted(g['affiliate_ciks'])) == group_key
                    for g in coordinated_groups
                )
                
                if not existing:
                    total_shares = sum(s.shares_sold for s in cluster)
                    total_value = sum(s.sale_value for s in cluster)
                    
                    coordinated_groups.append({
                        'window_start': window_start,
                        'window_end': window_end,
                        'window_days': temporal_threshold_days,
                        'participant_count': len(unique_affiliates),
                        'affiliate_ciks': list(unique_affiliates),
                        'affiliate_names': list(set(s.affiliate_name for s in cluster)),
                        'total_shares': total_shares,
                        'total_value': total_value,
                        'sale_count': len(cluster),
                        'sales': [
                            {
                                'date': s.sale_date.isoformat(),
                                'affiliate': s.affiliate_name,
                                'shares': s.shares_sold,
                                'value': s.sale_value
                            }
                            for s in cluster
                        ]
                    })
        
        return coordinated_groups
    
    def calculate_rolling_90day_volumes(
        self,
        sales: List[AffiliateSale],
        start_date: date,
        end_date: date
    ) -> List[Tuple[date, int]]:
        """
        Calculate rolling 90-day volumes for time series analysis.
        
        Args:
            sales: List of affiliate sales
            start_date: Start of analysis period
            end_date: End of analysis period
        
        Returns:
            List of (date, volume) tuples for each day
        """
        results = []
        current_date = start_date
        
        while current_date <= end_date:
            window_start = current_date - timedelta(days=self.aggregation_window_days - 1)
            
            # Sum all sales in the 90-day window ending on current_date
            volume = sum(
                sale.shares_sold
                for sale in sales
                if window_start <= sale.sale_date <= current_date
            )
            
            results.append((current_date, volume))
            current_date += timedelta(days=1)
        
        return results
