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
    PRE_EVENT_WINDOW_DAYS = 30
    SERIAL_GIFT_THRESHOLD = 3
    
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
    
    def detect_suspicious_gifts(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[GiftPatternAlert]:
        """
        Analyze gift transactions for:
        1. Timing anomalies (pre-earnings, pre-8K)
        2. Valuation discrepancies (gift value vs market)
        3. Relationship patterns (serial gifting chains)
        4. Beneficial ownership obfuscation
        
        Args:
            transactions: List of Form 4 transaction dicts with keys:
                transaction_code, transaction_date, shares, price_per_share,
                owner_name, filing_date, value
                
        Returns:
            List of GiftPatternAlert for suspicious gifts
        """
        gift_txns = [
            t for t in transactions
            if t.get('transaction_code', '').upper() == 'G'
        ]
        
        if not gift_txns:
            return []
        
        alerts: List[GiftPatternAlert] = []
        
        # Detect serial gifting patterns
        donors: Dict[str, List[Dict[str, Any]]] = {}
        for g in gift_txns:
            donor = g.get('owner_name', 'Unknown')
            donors.setdefault(donor, []).append(g)
        
        for donor, donor_gifts in donors.items():
            if len(donor_gifts) >= self.SERIAL_GIFT_THRESHOLD:
                total_shares = sum(g.get('shares', 0) for g in donor_gifts)
                gift = self._to_gift_transaction(donor_gifts[0])
                if gift:
                    alerts.append(GiftPatternAlert(
                        gift=gift,
                        alert_type="SERIAL_GIFT_PATTERN",
                        severity="HIGH",
                        seyhun_pattern_score=0.6,
                        evidence_summary=(
                            f"{donor} made {len(donor_gifts)} gifts "
                            f"totaling {total_shares:,.0f} shares - "
                            f"potential systematic tax avoidance"
                        )
                    ))
        
        # Detect large single gifts
        for g in gift_txns:
            shares = g.get('shares', 0)
            if shares > 100000:
                gift = self._to_gift_transaction(g)
                if gift:
                    alerts.append(GiftPatternAlert(
                        gift=gift,
                        alert_type="LARGE_GIFT",
                        severity="MEDIUM",
                        seyhun_pattern_score=0.4,
                        evidence_summary=(
                            f"Large gift of {shares:,.0f} shares by "
                            f"{g.get('owner_name', 'Unknown')}"
                        )
                    ))
        
        return alerts
    
    def correlate_with_material_events(
        self,
        gifts: List[Dict[str, Any]],
        events: List[Dict[str, Any]]
    ) -> List[GiftPatternAlert]:
        """
        Cross-reference gifts with material events (Node 9).
        
        Detects gifts immediately preceding negative announcements,
        which may indicate MNPI exploitation via gift timing.
        
        Args:
            gifts: List of gift transaction dicts
            events: List of material event dicts with event_date, event_type
            
        Returns:
            List of GiftPatternAlert for suspicious correlations
        """
        alerts: List[GiftPatternAlert] = []
        
        if not gifts or not events:
            return alerts
        
        for g in gifts:
            gift_date = self._parse_date(g.get('transaction_date'))
            if not gift_date:
                continue
            
            for event in events:
                event_date = self._parse_date(event.get('event_date'))
                if not event_date:
                    continue
                
                days_before = (event_date - gift_date).days
                if 0 < days_before <= self.PRE_EVENT_WINDOW_DAYS:
                    event_type = event.get('event_type', 'material event')
                    gift_obj = self._to_gift_transaction(g)
                    if gift_obj:
                        severity = "CRITICAL" if days_before <= 7 else "HIGH"
                        alerts.append(GiftPatternAlert(
                            gift=gift_obj,
                            alert_type="PRE_EVENT_GIFT",
                            severity=severity,
                            seyhun_pattern_score=min(
                                1.0,
                                0.5 + (1.0 - days_before / self.PRE_EVENT_WINDOW_DAYS) * 0.5
                            ),
                            evidence_summary=(
                                f"Gift {days_before} days before {event_type} - "
                                f"potential MNPI timing (15 USC §78j(b))"
                            )
                        ))
        
        return alerts
    
    def map_beneficial_ownership_chain(
        self,
        gift: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trace ultimate beneficial ownership through gift chains.
        
        Builds ownership chain from donor to donee to identify
        potential ownership obfuscation through trusts, LLCs, foundations.
        
        Args:
            gift: Gift transaction dict
            
        Returns:
            Dict with ownership chain information
        """
        donor = gift.get('owner_name', 'Unknown')
        donee = gift.get('donee_name', gift.get('indirect_owner', ''))
        ownership_nature = gift.get('ownership_nature', 'direct')
        indirect_entity = gift.get('indirect_entity', '')
        
        chain = {
            'donor': donor,
            'donee': donee if donee else 'Undisclosed',
            'ownership_type': ownership_nature,
            'indirect_entity': indirect_entity,
            'shares': gift.get('shares', 0),
            'transaction_date': gift.get('transaction_date'),
            'obfuscation_risk': 'LOW',
            'chain_links': [
                {'party': donor, 'role': 'donor', 'type': 'individual'}
            ]
        }
        
        # Assess obfuscation risk
        if indirect_entity:
            entity_lower = indirect_entity.lower()
            if any(term in entity_lower for term in ['trust', 'llc', 'foundation', 'family']):
                chain['obfuscation_risk'] = 'HIGH'
                chain['chain_links'].append({
                    'party': indirect_entity,
                    'role': 'intermediary',
                    'type': 'entity'
                })
            else:
                chain['obfuscation_risk'] = 'MEDIUM'
        
        if donee:
            chain['chain_links'].append({
                'party': donee,
                'role': 'donee',
                'type': 'unknown'
            })
        
        return chain
    
    def _to_gift_transaction(self, g: Dict[str, Any]) -> Optional[GiftTransaction]:
        """Convert a raw gift dict to a GiftTransaction dataclass."""
        trans_date = self._parse_date(g.get('transaction_date'))
        file_date = self._parse_date(g.get('filing_date'))
        if not trans_date or not file_date:
            return None
        
        days = (file_date - trans_date).days
        business_days = days - (days // 7 * 2)
        
        return GiftTransaction(
            transaction_date=trans_date,
            filing_date=file_date,
            shares=g.get('shares', 0),
            value_at_gift=g.get('value', 0),
            donor_name=g.get('owner_name', 'Unknown'),
            is_late_filed=business_days > self.LATE_FILING_DAYS,
            days_late=max(0, business_days - self.LATE_FILING_DAYS)
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

