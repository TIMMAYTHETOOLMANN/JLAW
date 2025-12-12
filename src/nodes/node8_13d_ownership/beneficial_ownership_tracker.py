"""
NODE 8: Schedule 13D/13G Beneficial Ownership Tracker
=====================================================

Monitors 5%+ beneficial ownership filings to detect:
- 13G-to-13D conversions (passive to activist shift)
- Rapid accumulation patterns toward control thresholds
- Wolf pack formations (coordinated group acquisitions)
- Hart-Scott-Rodino threshold approaches

SEC Reference: https://www.sec.gov/divisions/corpfin/guidance/reg13d-interp
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class OwnershipAlertType(Enum):
    PASSIVE_TO_ACTIVE_CONVERSION = "Passive to Active Conversion (13G→13D)"
    RAPID_ACCUMULATION = "Rapid Accumulation"
    WOLF_PACK_FORMATION = "Wolf Pack Formation"
    HSR_THRESHOLD_APPROACH = "Hart-Scott-Rodino Threshold Approach"
    HOSTILE_INTENT_DETECTED = "Hostile Intent Detected"
    CONTROL_ACQUISITION_PATTERN = "Control Acquisition Pattern"


@dataclass
class BeneficialOwnershipFiling:
    """Schedule 13D/13G filing record."""
    filing_type: str  # 'SC 13D', 'SC 13D/A', 'SC 13G', 'SC 13G/A'
    cik: str
    filer_name: str
    subject_company_cik: str
    subject_company_name: str
    filing_date: date
    event_date: date
    shares_owned: int
    percent_owned: float
    voting_power: float
    investment_power: float
    purpose_of_transaction: str
    source_of_funds: str
    item4_narrative: str
    schedule_type: str  # '13D' or '13G'
    previous_ownership: Optional[float] = None
    exemption_basis: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "filing_type": self.filing_type,
            "filer_name": self.filer_name,
            "subject_company": self.subject_company_name,
            "filing_date": self.filing_date.isoformat(),
            "percent_owned": round(self.percent_owned, 2),
            "schedule_type": self.schedule_type,
            "purpose": self.purpose_of_transaction[:200] if self.purpose_of_transaction else ""
        }


@dataclass
class IntentAnalysis:
    """Analysis of filer intent from Item 4 narrative."""
    hostile_indicators: List[str]
    passive_indicators: List[str]
    intent_score: float  # -1 (passive) to +1 (hostile)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hostile_indicators": self.hostile_indicators,
            "passive_indicators": self.passive_indicators,
            "intent_score": round(self.intent_score, 2),
            "classification": "HOSTILE" if self.intent_score > 0.3 else "PASSIVE" if self.intent_score < -0.3 else "NEUTRAL"
        }


@dataclass
class OwnershipAlert:
    """Alert for suspicious beneficial ownership activity."""
    alert_type: OwnershipAlertType
    subject_company_cik: str
    subject_company_name: str
    involved_parties: List[Dict[str, Any]]
    aggregate_ownership: float
    risk_indicators: List[str]
    intent_analysis: IntentAnalysis
    regulatory_triggers: List[str]
    evidence_hash: str
    severity: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "subject_company": self.subject_company_name,
            "involved_parties_count": len(self.involved_parties),
            "aggregate_ownership": round(self.aggregate_ownership, 2),
            "risk_indicators": self.risk_indicators,
            "intent_analysis": self.intent_analysis.to_dict(),
            "regulatory_triggers": self.regulatory_triggers,
            "severity": self.severity
        }


@dataclass
class Node8Output:
    """Output from Node 8 analysis."""
    filings_analyzed: int
    unique_filers: int
    unique_subjects: int
    alerts: List[OwnershipAlert]
    conversions_detected: int
    wolf_packs_detected: int
    high_severity_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "filings_analyzed": self.filings_analyzed,
                "unique_filers": self.unique_filers,
                "unique_subjects": self.unique_subjects,
                "conversions_detected": self.conversions_detected,
                "wolf_packs_detected": self.wolf_packs_detected,
                "high_severity_alerts": self.high_severity_count
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class BeneficialOwnershipTracker:
    """
    Schedule 13D/13G Beneficial Ownership Tracker.
    
    Key Detection Capabilities:
    1. 13G to 13D conversions (shift from passive to activist)
    2. Wolf pack formations (coordinated group acquisitions)
    3. Rapid accumulation toward control thresholds
    4. Intent analysis from Item 4 narratives
    """
    
    # Hostile intent indicators
    HOSTILE_INDICATORS = [
        'seek representation on the board',
        'propose changes to',
        'seek to influence',
        'oppose the transaction',
        'nominate directors',
        'proxy contest',
        'strategic alternatives',
        'maximize shareholder value',
        'undervalued',
        'mismanaged',
        'replace management',
        'change in control',
        'merger or acquisition',
        'business combination',
        'restructuring',
        'spin-off',
        'sale of assets'
    ]
    
    # Passive intent indicators
    PASSIVE_INDICATORS = [
        'investment purposes only',
        'ordinary course of business',
        'no intention to influence',
        'passive investment',
        'not seeking control',
        'no current plans',
        'may engage in discussions'
    ]
    
    # Ownership thresholds
    THRESHOLDS = {
        'filing_required': 5.0,
        'heightened_13d': 10.0,
        'hsr_first': 20.0,  # Hart-Scott-Rodino
        'presumption_control': 25.0,
        'majority': 50.0
    }
    
    def __init__(self):
        pass
    
    def analyze(
        self,
        filings: List[BeneficialOwnershipFiling]
    ) -> Node8Output:
        """
        Run complete 13D/13G analysis.
        
        Args:
            filings: List of beneficial ownership filings
            
        Returns:
            Node8Output with all analysis results
        """
        logger.info(f"[NODE 8] Analyzing {len(filings)} beneficial ownership filings")
        
        alerts = []
        
        # Detect 13G to 13D conversions
        conversion_alerts = self.detect_13g_to_13d_conversion(filings)
        alerts.extend(conversion_alerts)
        
        # Detect wolf pack formations
        wolf_pack_alerts = self.detect_wolf_pack_formation(filings)
        alerts.extend(wolf_pack_alerts)
        
        # Detect rapid accumulation
        rapid_alerts = self.detect_rapid_accumulation(filings)
        alerts.extend(rapid_alerts)
        
        # Calculate metrics
        unique_filers = len(set(f.cik for f in filings))
        unique_subjects = len(set(f.subject_company_cik for f in filings))
        high_severity = len([a for a in alerts if a.severity in ['HIGH', 'CRITICAL']])
        
        return Node8Output(
            filings_analyzed=len(filings),
            unique_filers=unique_filers,
            unique_subjects=unique_subjects,
            alerts=alerts,
            conversions_detected=len(conversion_alerts),
            wolf_packs_detected=len(wolf_pack_alerts),
            high_severity_count=high_severity
        )
    
    def detect_13g_to_13d_conversion(
        self,
        filings: List[BeneficialOwnershipFiling]
    ) -> List[OwnershipAlert]:
        """
        Detect 13G to 13D conversions indicating shift from passive to activist.
        """
        alerts = []
        
        # Group by filer + subject company
        grouped = self._group_filings(filings)
        
        for key, filer_filings in grouped.items():
            sorted_filings = sorted(filer_filings, key=lambda f: f.filing_date)
            
            for i in range(1, len(sorted_filings)):
                prev = sorted_filings[i - 1]
                curr = sorted_filings[i]
                
                # Check for 13G followed by 13D
                if prev.schedule_type == '13G' and curr.schedule_type == '13D':
                    intent = self.analyze_intent(curr.item4_narrative)
                    
                    alerts.append(OwnershipAlert(
                        alert_type=OwnershipAlertType.PASSIVE_TO_ACTIVE_CONVERSION,
                        subject_company_cik=curr.subject_company_cik,
                        subject_company_name=curr.subject_company_name,
                        involved_parties=[{
                            'name': curr.filer_name,
                            'cik': curr.cik,
                            'current_ownership': curr.percent_owned,
                            'ownership_change': curr.percent_owned - (prev.percent_owned or 0)
                        }],
                        aggregate_ownership=curr.percent_owned,
                        risk_indicators=[
                            'Schedule 13G to 13D conversion detected',
                            f'Current ownership: {curr.percent_owned:.2f}%',
                            f'Days between filings: {(curr.filing_date - prev.filing_date).days}'
                        ],
                        intent_analysis=intent,
                        regulatory_triggers=self._identify_regulatory_triggers(curr),
                        evidence_hash=self._generate_hash([prev, curr]),
                        severity='HIGH' if intent.intent_score > 0.5 else 'MEDIUM'
                    ))
        
        return alerts
    
    def detect_wolf_pack_formation(
        self,
        filings: List[BeneficialOwnershipFiling],
        window_days: int = 30
    ) -> List[OwnershipAlert]:
        """
        Detect wolf pack formations - coordinated group acquisitions.
        """
        alerts = []
        
        # Group by subject company
        by_subject = defaultdict(list)
        for f in filings:
            by_subject[f.subject_company_cik].append(f)
        
        for subject_cik, subject_filings in by_subject.items():
            # Find temporal clusters
            clusters = self._find_temporal_clusters(subject_filings, window_days)
            
            for cluster in clusters:
                if len(cluster) >= 3:  # At least 3 filers
                    aggregate = sum(f.percent_owned for f in cluster)
                    
                    if aggregate >= 10:  # Combined >= 10%
                        involved = [
                            {
                                'name': f.filer_name,
                                'cik': f.cik,
                                'current_ownership': f.percent_owned,
                                'ownership_change': f.percent_owned - (f.previous_ownership or 0)
                            }
                            for f in cluster
                        ]
                        
                        # Analyze collective intent
                        combined_narrative = ' '.join(f.item4_narrative for f in cluster)
                        intent = self.analyze_intent(combined_narrative)
                        
                        alerts.append(OwnershipAlert(
                            alert_type=OwnershipAlertType.WOLF_PACK_FORMATION,
                            subject_company_cik=subject_cik,
                            subject_company_name=cluster[0].subject_company_name,
                            involved_parties=involved,
                            aggregate_ownership=aggregate,
                            risk_indicators=[
                                f'{len(cluster)} coordinated filers detected',
                                f'Aggregate ownership: {aggregate:.2f}%',
                                f'Filing window: {window_days} days',
                                'Potential Section 13(d)(3) group formation'
                            ],
                            intent_analysis=intent,
                            regulatory_triggers=[
                                'Potential Section 13(d)(3) "group" formation',
                                'SEC may require joint 13D filing'
                            ] + (['Hart-Scott-Rodino threshold exceeded'] if aggregate >= 20 else []),
                            evidence_hash=self._generate_hash(cluster),
                            severity='CRITICAL'
                        ))
        
        return alerts
    
    def detect_rapid_accumulation(
        self,
        filings: List[BeneficialOwnershipFiling]
    ) -> List[OwnershipAlert]:
        """
        Detect rapid accumulation toward control thresholds.
        """
        alerts = []
        
        grouped = self._group_filings(filings)
        
        for key, filer_filings in grouped.items():
            sorted_filings = sorted(filer_filings, key=lambda f: f.filing_date)
            
            if len(sorted_filings) >= 2:
                first = sorted_filings[0]
                last = sorted_filings[-1]
                
                ownership_change = last.percent_owned - first.percent_owned
                days = (last.filing_date - first.filing_date).days
                
                # Alert if rapid accumulation (>5% in 30 days)
                if ownership_change > 5.0 and days <= 30:
                    intent = self.analyze_intent(last.item4_narrative)
                    
                    alerts.append(OwnershipAlert(
                        alert_type=OwnershipAlertType.RAPID_ACCUMULATION,
                        subject_company_cik=last.subject_company_cik,
                        subject_company_name=last.subject_company_name,
                        involved_parties=[{
                            'name': last.filer_name,
                            'cik': last.cik,
                            'current_ownership': last.percent_owned,
                            'ownership_change': ownership_change
                        }],
                        aggregate_ownership=last.percent_owned,
                        risk_indicators=[
                            f'Accumulated {ownership_change:.2f}% in {days} days',
                            f'Current ownership: {last.percent_owned:.2f}%',
                            'Rapid accumulation pattern detected'
                        ],
                        intent_analysis=intent,
                        regulatory_triggers=self._identify_regulatory_triggers(last),
                        evidence_hash=self._generate_hash([first, last]),
                        severity='HIGH' if ownership_change > 10 else 'MEDIUM'
                    ))
        
        return alerts
    
    def analyze_intent(self, narrative: str) -> IntentAnalysis:
        """
        Analyze Item 4 narrative for intent signals.
        """
        if not narrative:
            return IntentAnalysis([], [], 0.0)
        
        lower = narrative.lower()
        
        found_hostile = [ind for ind in self.HOSTILE_INDICATORS if ind in lower]
        found_passive = [ind for ind in self.PASSIVE_INDICATORS if ind in lower]
        
        # Score from -1 (passive) to +1 (hostile)
        hostile_weight = len(found_hostile) * 0.2
        passive_weight = len(found_passive) * 0.2
        intent_score = max(-1, min(1, hostile_weight - passive_weight))
        
        return IntentAnalysis(
            hostile_indicators=found_hostile,
            passive_indicators=found_passive,
            intent_score=intent_score
        )
    
    def _identify_regulatory_triggers(self, filing: BeneficialOwnershipFiling) -> List[str]:
        """Identify regulatory threshold triggers."""
        triggers = []
        ownership = filing.percent_owned
        
        if 5 <= ownership < 10:
            triggers.append('5% beneficial ownership threshold - Schedule 13D/13G required')
        if ownership >= 10:
            triggers.append('10% ownership - Heightened 13D amendment requirements')
        if ownership >= 20:
            triggers.append('20% ownership - Potential Hart-Scott-Rodino notification')
        if ownership >= 25:
            triggers.append('25% ownership - Presumption of control threshold')
        if ownership >= 50:
            triggers.append('50% ownership - Majority control achieved')
        
        if filing.schedule_type == '13D':
            triggers.append('Schedule 13D filed - Active/non-passive investment')
        
        return triggers
    
    def _group_filings(
        self, 
        filings: List[BeneficialOwnershipFiling]
    ) -> Dict[str, List[BeneficialOwnershipFiling]]:
        """Group filings by filer + subject company."""
        result = defaultdict(list)
        for f in filings:
            key = f'{f.cik}-{f.subject_company_cik}'
            result[key].append(f)
        return dict(result)
    
    def _find_temporal_clusters(
        self,
        filings: List[BeneficialOwnershipFiling],
        window_days: int
    ) -> List[List[BeneficialOwnershipFiling]]:
        """Find clusters of filings within temporal window."""
        if not filings:
            return []
        
        sorted_f = sorted(filings, key=lambda f: f.filing_date)
        clusters = []
        current = [sorted_f[0]]
        
        for f in sorted_f[1:]:
            if (f.filing_date - current[0].filing_date).days <= window_days:
                current.append(f)
            else:
                if len(current) >= 2:
                    clusters.append(current)
                current = [f]
        
        if len(current) >= 2:
            clusters.append(current)
        
        return clusters
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        if isinstance(data, list):
            serialized = str([
                {'filer': getattr(d, 'filer_name', ''), 'date': str(getattr(d, 'filing_date', ''))}
                for d in data
            ])
        else:
            serialized = str(data)
        return hashlib.sha256(serialized.encode()).hexdigest()

