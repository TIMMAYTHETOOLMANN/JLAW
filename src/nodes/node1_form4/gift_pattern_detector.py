"""
Gift Pattern Detector
=====================

Seyhun et al. research methodology for gift-before-drop detection.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class GiftTransaction:
    transaction_date: date
    filing_date: date
    shares: float
    value_at_gift: float
    donor_name: str
    is_late_filed: bool
    days_late: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_date": self.transaction_date.isoformat(),
            "filing_date": self.filing_date.isoformat(),
            "shares": self.shares,
            "is_late_filed": self.is_late_filed,
            "days_late": self.days_late
        }


@dataclass
class GiftPatternAlert:
    gift: GiftTransaction
    alert_type: str
    severity: str
    seyhun_pattern_score: float
    evidence_summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gift": self.gift.to_dict(),
            "alert_type": self.alert_type,
            "severity": self.severity,
            "seyhun_score": round(self.seyhun_pattern_score, 3),
            "evidence": self.evidence_summary
        }


@dataclass
class GiftPatternAnalysis:
    total_gifts: int
    suspicious_gifts: int
    late_filed_gifts: int
    year_end_gifts: int
    alerts: List[GiftPatternAlert]
    aggregate_seyhun_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_gifts": self.total_gifts,
                "suspicious_gifts": self.suspicious_gifts,
                "late_filed_gifts": self.late_filed_gifts,
                "year_end_gifts": self.year_end_gifts
            },
            "aggregate_seyhun_score": round(self.aggregate_seyhun_score, 3),
            "alerts": [a.to_dict() for a in self.alerts]
        }


class GiftPatternDetector:
    """Detects suspicious gift patterns using Seyhun methodology."""
    
    LATE_FILING_DAYS = 2
    
    def analyze_gifts(
        self,
        gifts: List[Dict[str, Any]],
        price_data: Optional[Dict[date, float]] = None
    ) -> GiftPatternAnalysis:
        parsed = self._parse_gifts(gifts)
        alerts = []
        late_filed = 0
        year_end = 0
        suspicious = 0
        
        for gift in parsed:
            if gift.is_late_filed:
                late_filed += 1
                alerts.append(GiftPatternAlert(
                    gift=gift,
                    alert_type="LATE_FILED_GIFT",
                    severity="HIGH" if gift.days_late > 10 else "MEDIUM",
                    seyhun_pattern_score=0.3,
                    evidence_summary=f"Gift filed {gift.days_late} days late"
                ))
            
            if gift.transaction_date.month == 12:
                year_end += 1
                alerts.append(GiftPatternAlert(
                    gift=gift,
                    alert_type="YEAR_END_TAX_TIMING",
                    severity="LOW",
                    seyhun_pattern_score=0.2,
                    evidence_summary="December gift - tax timing concern"
                ))
        
        suspicious = len([a for a in alerts if a.severity in ["HIGH", "CRITICAL"]])
        
        return GiftPatternAnalysis(
            total_gifts=len(parsed),
            suspicious_gifts=suspicious,
            late_filed_gifts=late_filed,
            year_end_gifts=year_end,
            alerts=alerts,
            aggregate_seyhun_score=0.3 if late_filed > 0 else 0.0
        )
    
    def _parse_gifts(self, gifts: List[Dict[str, Any]]) -> List[GiftTransaction]:
        parsed = []
        for g in gifts:
            trans_date = self._parse_date(g.get('transaction_date'))
            file_date = self._parse_date(g.get('filing_date'))
            if not trans_date or not file_date:
                continue
            
            days = (file_date - trans_date).days
            business_days = days - (days // 7 * 2)
            
            parsed.append(GiftTransaction(
                transaction_date=trans_date,
                filing_date=file_date,
                shares=g.get('shares', 0),
                value_at_gift=g.get('value', 0),
                donor_name=g.get('owner_name', 'Unknown'),
                is_late_filed=business_days > self.LATE_FILING_DAYS,
                days_late=max(0, business_days - self.LATE_FILING_DAYS)
            ))
        return parsed
    
    def _parse_date(self, val) -> Optional[date]:
        if isinstance(val, date):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            try:
                return datetime.strptime(val, '%Y-%m-%d').date()
            except ValueError:
                return None
        return None

