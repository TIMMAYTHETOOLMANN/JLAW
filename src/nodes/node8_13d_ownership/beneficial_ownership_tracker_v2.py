"""
NODE 8: Beneficial Ownership Tracker v2.0 (FORTIFIED)
====================================================

December 2024 XML mandate compliance (SEC Release No. 34-99232):
- Shortened filing deadlines: 13D within 5 business days (was 10 calendar)
- Amendment deadline: 2 business days for material changes
- 13G-to-13D conversion detection
- Group formation analysis (Section 13(d)(3))
- Wolf pack coordination with Node 7
- Intent signal extraction from Item 4
- Schedule 13G category tracking (QII, Passive, Exempt)

SEC Reference: https://www.sec.gov/divisions/corpfin/guidance/reg13d-interp
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import logging
import xml.etree.ElementTree as ET
from collections import defaultdict

logger = logging.getLogger(__name__)


class Schedule13Type(Enum):
    """Schedule 13 filing type."""
    SC_13D = "SC 13D"
    SC_13D_A = "SC 13D/A"  # Amendment
    SC_13G = "SC 13G"
    SC_13G_A = "SC 13G/A"  # Amendment


class Schedule13GCategory(Enum):
    """Schedule 13G filer category."""
    QII = "Qualified Institutional Investor"  # Rule 13d-1(b)
    PASSIVE = "Passive Investor"  # Rule 13d-1(c)
    EXEMPT = "Exempt Investor"  # Rule 13d-1(d)


class OwnershipAlertType(Enum):
    """Type of ownership alert."""
    PASSIVE_TO_ACTIVE_CONVERSION = "Passive to Active Conversion (13G→13D)"
    RAPID_ACCUMULATION = "Rapid Accumulation"
    WOLF_PACK_FORMATION = "Wolf Pack Formation"
    HSR_THRESHOLD_APPROACH = "Hart-Scott-Rodino Threshold Approach"
    HOSTILE_INTENT_DETECTED = "Hostile Intent Detected"
    CONTROL_ACQUISITION_PATTERN = "Control Acquisition Pattern"
    FILING_DEADLINE_VIOLATION = "Filing Deadline Violation"
    GROUP_FORMATION_13D3 = "Section 13(d)(3) Group Formation"


class IntentSignal(Enum):
    """Intent signals from Item 4 narrative."""
    PASSIVE_INVESTMENT = "Passive Investment"
    BOARD_REPRESENTATION = "Board Representation"
    MANAGEMENT_CHANGE = "Management Change"
    STRATEGIC_ALTERNATIVES = "Strategic Alternatives"
    MERGER_ACQUISITION = "Merger/Acquisition"
    PROXY_CONTEST = "Proxy Contest"
    ASSET_RESTRUCTURING = "Asset Restructuring"
    SPIN_OFF = "Spin-off"


class Severity(Enum):
    """Alert severity level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Schedule13Filing:
    """Enhanced Schedule 13D/13G filing record with December 2024 compliance."""
    filing_type: Schedule13Type
    cik: str
    filer_name: str
    subject_company_cik: str
    subject_company_name: str
    filing_date: date
    event_date: date  # Date of event triggering filing requirement
    shares_owned: int
    percent_owned: float
    voting_power: float
    investment_power: float
    purpose_of_transaction: str
    source_of_funds: str
    item4_narrative: str
    schedule_type: str  # '13D' or '13G'
    
    # December 2024 enhancements
    filing_deadline_days: int  # Expected deadline (5 business days for 13D, 2 for amendments)
    days_from_event_to_filing: int  # Actual days taken
    is_deadline_compliant: bool
    schedule_13g_category: Optional[Schedule13GCategory] = None
    is_amendment: bool = False
    amendment_type: Optional[str] = None  # Material or Non-material
    group_member_ciks: List[str] = field(default_factory=list)  # Section 13(d)(3) group
    
    # Legacy fields
    previous_ownership: Optional[float] = None
    exemption_basis: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "filing_type": self.filing_type.value,
            "filer_name": self.filer_name,
            "subject_company": self.subject_company_name,
            "filing_date": self.filing_date.isoformat(),
            "event_date": self.event_date.isoformat(),
            "percent_owned": round(self.percent_owned, 2),
            "schedule_type": self.schedule_type,
            "filing_deadline_days": self.filing_deadline_days,
            "days_from_event_to_filing": self.days_from_event_to_filing,
            "is_deadline_compliant": self.is_deadline_compliant,
            "schedule_13g_category": self.schedule_13g_category.value if self.schedule_13g_category else None,
            "is_amendment": self.is_amendment,
            "group_members": len(self.group_member_ciks),
            "purpose": self.purpose_of_transaction[:200] if self.purpose_of_transaction else ""
        }


@dataclass
class IntentAnalysis:
    """Enhanced intent analysis from Item 4 narrative."""
    hostile_indicators: List[str]
    passive_indicators: List[str]
    intent_score: float  # -1 (passive) to +1 (hostile)
    primary_intent: IntentSignal
    secondary_intents: List[IntentSignal]
    confidence: float  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hostile_indicators": self.hostile_indicators,
            "passive_indicators": self.passive_indicators,
            "intent_score": round(self.intent_score, 2),
            "primary_intent": self.primary_intent.value,
            "secondary_intents": [s.value for s in self.secondary_intents],
            "confidence": round(self.confidence, 2),
            "classification": "HOSTILE" if self.intent_score > 0.3 else "PASSIVE" if self.intent_score < -0.3 else "NEUTRAL"
        }


@dataclass
class OwnershipAlert:
    """Enhanced ownership alert with December 2024 features."""
    alert_type: OwnershipAlertType
    subject_company_cik: str
    subject_company_name: str
    involved_parties: List[Dict[str, Any]]
    aggregate_ownership: float
    risk_indicators: List[str]
    intent_analysis: IntentAnalysis
    regulatory_triggers: List[str]
    evidence_hash: str
    severity: Severity
    
    # December 2024 enhancements
    filing_compliance_issues: List[str] = field(default_factory=list)
    group_coordination_score: Optional[float] = None  # 0.0-1.0 for Section 13(d)(3) analysis
    node7_correlation: Optional[Dict[str, Any]] = None  # Link to 13F holdings
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "subject_company": self.subject_company_name,
            "involved_parties_count": len(self.involved_parties),
            "involved_parties": self.involved_parties,
            "aggregate_ownership": round(self.aggregate_ownership, 2),
            "risk_indicators": self.risk_indicators,
            "intent_analysis": self.intent_analysis.to_dict(),
            "regulatory_triggers": self.regulatory_triggers,
            "filing_compliance_issues": self.filing_compliance_issues,
            "group_coordination_score": round(self.group_coordination_score, 3) if self.group_coordination_score else None,
            "node7_correlation": self.node7_correlation,
            "severity": self.severity.value
        }


@dataclass
class Node8Output:
    """Enhanced Node 8 output with December 2024 metrics."""
    filings_analyzed: int
    unique_filers: int
    unique_subjects: int
    alerts: List[OwnershipAlert]
    conversions_detected: int
    wolf_packs_detected: int
    group_formations_detected: int  # Section 13(d)(3)
    filing_violations_detected: int  # Deadline violations
    high_severity_count: int
    xml_filings_parsed: int  # December 2024 XML format
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "filings_analyzed": self.filings_analyzed,
                "unique_filers": self.unique_filers,
                "unique_subjects": self.unique_subjects,
                "conversions_detected": self.conversions_detected,
                "wolf_packs_detected": self.wolf_packs_detected,
                "group_formations_detected": self.group_formations_detected,
                "filing_violations_detected": self.filing_violations_detected,
                "high_severity_alerts": self.high_severity_count,
                "xml_filings_parsed": self.xml_filings_parsed
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class Schedule13XMLParser:
    """
    Parser for December 2024 XML mandate Schedule 13D/13G filings.
    
    Handles new SEC Release No. 34-99232 XML format requirements.
    """
    
    @staticmethod
    def parse_xml(xml_content: str) -> Optional[Schedule13Filing]:
        """
        Parse XML format Schedule 13D/13G filing (December 2024 format).
        
        Args:
            xml_content: XML content string
            
        Returns:
            Schedule13Filing object or None if parsing fails
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Extract basic filing information
            filing_type_str = root.findtext(".//{*}submissionType", "SC 13D")
            filing_type = Schedule13Type.SC_13D if "13D" in filing_type_str else Schedule13Type.SC_13G
            
            # Extract dates
            filing_date_str = root.findtext(".//{*}filingDate", datetime.now().strftime("%Y-%m-%d"))
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d").date()
            
            event_date_str = root.findtext(".//{*}eventDate", filing_date_str)
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
            
            # Calculate deadline compliance
            days_from_event = (filing_date - event_date).days
            is_amendment = "/A" in filing_type_str
            
            if "13D" in filing_type_str:
                deadline_days = 2 if is_amendment else 5  # Business days
            else:
                deadline_days = 45 if not is_amendment else 45  # 13G has longer deadline
            
            is_compliant = days_from_event <= deadline_days
            
            # Extract ownership data
            shares_owned = int(root.findtext(".//{*}sharesOwned", "0"))
            percent_owned = float(root.findtext(".//{*}percentOwned", "0.0"))
            
            # Extract narrative fields
            item4_narrative = root.findtext(".//{*}item4Purpose", "")
            
            # Extract group members if present
            group_members = []
            for member in root.findall(".//{*}groupMember"):
                member_cik = member.findtext("{*}cik", "")
                if member_cik:
                    group_members.append(member_cik)
            
            # Determine 13G category if applicable
            category = None
            if "13G" in filing_type_str:
                category_str = root.findtext(".//{*}filerCategory", "")
                if "QII" in category_str or "Qualified" in category_str:
                    category = Schedule13GCategory.QII
                elif "Passive" in category_str:
                    category = Schedule13GCategory.PASSIVE
                elif "Exempt" in category_str:
                    category = Schedule13GCategory.EXEMPT
            
            filing = Schedule13Filing(
                filing_type=filing_type,
                cik=root.findtext(".//{*}filerCik", ""),
                filer_name=root.findtext(".//{*}filerName", "Unknown"),
                subject_company_cik=root.findtext(".//{*}issuerCik", ""),
                subject_company_name=root.findtext(".//{*}issuerName", "Unknown"),
                filing_date=filing_date,
                event_date=event_date,
                shares_owned=shares_owned,
                percent_owned=percent_owned,
                voting_power=float(root.findtext(".//{*}votingPower", str(percent_owned))),
                investment_power=float(root.findtext(".//{*}investmentPower", str(percent_owned))),
                purpose_of_transaction=item4_narrative,
                source_of_funds=root.findtext(".//{*}sourceOfFunds", ""),
                item4_narrative=item4_narrative,
                schedule_type="13D" if "13D" in filing_type_str else "13G",
                filing_deadline_days=deadline_days,
                days_from_event_to_filing=days_from_event,
                is_deadline_compliant=is_compliant,
                schedule_13g_category=category,
                is_amendment=is_amendment,
                group_member_ciks=group_members
            )
            
            return filing
            
        except Exception as e:
            logger.error(f"Error parsing Schedule 13 XML: {e}")
            return None


class BeneficialOwnershipTrackerV2:
    """
    Schedule 13D/13G Beneficial Ownership Tracker v2.0 (FORTIFIED).
    
    December 2024 compliance features:
    - XML mandate parsing (SEC Release No. 34-99232)
    - Shortened deadline tracking (5 business days for 13D, 2 for amendments)
    - Enhanced group formation detection (Section 13(d)(3))
    - Intent signal extraction and scoring
    - Cross-node correlation with Node 7 (13F holdings)
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
        'sale of assets',
        'improve operations',
        'enhance value'
    ]
    
    # Passive intent indicators
    PASSIVE_INDICATORS = [
        'investment purposes only',
        'ordinary course of business',
        'no intention to influence',
        'passive investment',
        'not seeking control',
        'no current plans',
        'may engage in discussions',
        'long-term investment',
        'portfolio investment'
    ]
    
    # Ownership thresholds
    THRESHOLDS = {
        'filing_required': 5.0,
        'heightened_13d': 10.0,
        'hsr_first': 20.0,  # Hart-Scott-Rodino
        'presumption_control': 25.0,
        'majority': 50.0
    }
    
    # Group coordination threshold
    GROUP_COORDINATION_THRESHOLD = 0.7
    
    def __init__(self):
        pass
    
    def analyze(
        self,
        filings: List[Schedule13Filing],
        node7_output: Optional[Any] = None
    ) -> Node8Output:
        """
        Run complete 13D/13G analysis with December 2024 enhancements.
        
        Args:
            filings: List of beneficial ownership filings
            node7_output: Optional Node 7 output for wolf pack correlation
            
        Returns:
            Node8Output with all analysis results
        """
        logger.info(f"[NODE 8 v2.0] Analyzing {len(filings)} beneficial ownership filings")
        
        alerts = []
        
        # Detect 13G to 13D conversions
        conversion_alerts = self.detect_13g_to_13d_conversion(filings)
        alerts.extend(conversion_alerts)
        
        # Detect wolf pack formations with Node 7 correlation
        wolf_pack_alerts = self.detect_wolf_pack_formation_v2(filings, node7_output)
        alerts.extend(wolf_pack_alerts)
        
        # Detect Section 13(d)(3) group formations
        group_alerts = self.detect_group_formation_13d3(filings)
        alerts.extend(group_alerts)
        
        # Detect rapid accumulation
        rapid_alerts = self.detect_rapid_accumulation(filings)
        alerts.extend(rapid_alerts)
        
        # Detect filing deadline violations
        violation_alerts = self.detect_filing_violations(filings)
        alerts.extend(violation_alerts)
        
        # Calculate metrics
        unique_filers = len(set(f.cik for f in filings))
        unique_subjects = len(set(f.subject_company_cik for f in filings))
        high_severity = len([a for a in alerts if a.severity in [Severity.HIGH, Severity.CRITICAL]])
        xml_count = len([f for f in filings if f.filing_deadline_days > 0])  # Proxy for XML parsed
        
        return Node8Output(
            filings_analyzed=len(filings),
            unique_filers=unique_filers,
            unique_subjects=unique_subjects,
            alerts=alerts,
            conversions_detected=len(conversion_alerts),
            wolf_packs_detected=len([a for a in wolf_pack_alerts if a.alert_type == OwnershipAlertType.WOLF_PACK_FORMATION]),
            group_formations_detected=len(group_alerts),
            filing_violations_detected=len(violation_alerts),
            high_severity_count=high_severity,
            xml_filings_parsed=xml_count
        )
    
    def detect_13g_to_13d_conversion(
        self,
        filings: List[Schedule13Filing]
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
                    intent = self.analyze_intent_v2(curr.item4_narrative)
                    
                    compliance_issues = []
                    if not curr.is_deadline_compliant:
                        compliance_issues.append(
                            f"Filing delay: {curr.days_from_event_to_filing} days (deadline: {curr.filing_deadline_days} business days)"
                        )
                    
                    alerts.append(OwnershipAlert(
                        alert_type=OwnershipAlertType.PASSIVE_TO_ACTIVE_CONVERSION,
                        subject_company_cik=curr.subject_company_cik,
                        subject_company_name=curr.subject_company_name,
                        involved_parties=[{
                            'name': curr.filer_name,
                            'cik': curr.cik,
                            'current_ownership': curr.percent_owned,
                            'ownership_change': curr.percent_owned - (prev.percent_owned or 0),
                            'previous_13g_category': prev.schedule_13g_category.value if prev.schedule_13g_category else None
                        }],
                        aggregate_ownership=curr.percent_owned,
                        risk_indicators=[
                            'Schedule 13G to 13D conversion detected',
                            f'Current ownership: {curr.percent_owned:.2f}%',
                            f'Days between filings: {(curr.filing_date - prev.filing_date).days}',
                            f'Intent score: {intent.intent_score:.2f} ({intent.primary_intent.value})'
                        ],
                        intent_analysis=intent,
                        regulatory_triggers=self._identify_regulatory_triggers(curr),
                        evidence_hash=self._generate_hash([prev, curr]),
                        filing_compliance_issues=compliance_issues,
                        severity=Severity.CRITICAL if intent.intent_score > 0.5 else Severity.HIGH
                    ))
        
        return alerts
    
    def detect_wolf_pack_formation_v2(
        self,
        filings: List[Schedule13Filing],
        node7_output: Optional[Any] = None,
        window_days: int = 30
    ) -> List[OwnershipAlert]:
        """
        Enhanced wolf pack detection with Node 7 correlation.
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
                        # Calculate group coordination score
                        coord_score = self._calculate_group_coordination_score(cluster)
                        
                        involved = [
                            {
                                'name': f.filer_name,
                                'cik': f.cik,
                                'current_ownership': f.percent_owned,
                                'ownership_change': f.percent_owned - (f.previous_ownership or 0),
                                'filing_date': f.filing_date.isoformat()
                            }
                            for f in cluster
                        ]
                        
                        # Analyze collective intent
                        combined_narrative = ' '.join(f.item4_narrative for f in cluster)
                        intent = self.analyze_intent_v2(combined_narrative)
                        
                        # Check for Node 7 correlation
                        node7_corr = self._correlate_with_node7(
                            subject_cik, [f.filer_name for f in cluster], node7_output
                        ) if node7_output else None
                        
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
                                f'Group coordination score: {coord_score:.2f}',
                                'Potential Section 13(d)(3) group formation'
                            ],
                            intent_analysis=intent,
                            regulatory_triggers=[
                                'Potential Section 13(d)(3) "group" formation',
                                'SEC may require joint 13D filing'
                            ] + (['Hart-Scott-Rodino threshold exceeded'] if aggregate >= 20 else []),
                            evidence_hash=self._generate_hash(cluster),
                            group_coordination_score=coord_score,
                            node7_correlation=node7_corr,
                            severity=Severity.CRITICAL
                        ))
        
        return alerts
    
    def detect_group_formation_13d3(
        self,
        filings: List[Schedule13Filing]
    ) -> List[OwnershipAlert]:
        """
        Detect Section 13(d)(3) group formations.
        
        Section 13(d)(3) defines a "group" as persons who act together for the
        purpose of acquiring, holding, or disposing of securities.
        """
        alerts = []
        
        # Find filings with group members declared
        for filing in filings:
            if filing.group_member_ciks and len(filing.group_member_ciks) >= 1:
                # Group explicitly declared
                intent = self.analyze_intent_v2(filing.item4_narrative)
                
                # Look up other group members' filings
                group_ownership = filing.percent_owned
                group_members = [{
                    'name': filing.filer_name,
                    'cik': filing.cik,
                    'current_ownership': filing.percent_owned
                }]
                
                for member_cik in filing.group_member_ciks:
                    member_filings = [f for f in filings if f.cik == member_cik and f.subject_company_cik == filing.subject_company_cik]
                    if member_filings:
                        member = member_filings[0]
                        group_ownership += member.percent_owned
                        group_members.append({
                            'name': member.filer_name,
                            'cik': member.cik,
                            'current_ownership': member.percent_owned
                        })
                
                coord_score = self._calculate_group_coordination_score(
                    [f for f in filings if f.cik in [filing.cik] + filing.group_member_ciks]
                )
                
                alerts.append(OwnershipAlert(
                    alert_type=OwnershipAlertType.GROUP_FORMATION_13D3,
                    subject_company_cik=filing.subject_company_cik,
                    subject_company_name=filing.subject_company_name,
                    involved_parties=group_members,
                    aggregate_ownership=group_ownership,
                    risk_indicators=[
                        f'Section 13(d)(3) group explicitly declared',
                        f'{len(group_members)} group members',
                        f'Aggregate group ownership: {group_ownership:.2f}%',
                        f'Group coordination score: {coord_score:.2f}'
                    ],
                    intent_analysis=intent,
                    regulatory_triggers=[
                        'Section 13(d)(3) group formation confirmed',
                        'Joint filing requirements apply',
                        'Group treated as single beneficial owner'
                    ] + (['Control threshold exceeded'] if group_ownership >= 25 else []),
                    evidence_hash=self._generate_hash([filing]),
                    group_coordination_score=coord_score,
                    severity=Severity.CRITICAL if group_ownership >= 25 else Severity.HIGH
                ))
        
        return alerts
    
    def detect_rapid_accumulation(
        self,
        filings: List[Schedule13Filing]
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
                    intent = self.analyze_intent_v2(last.item4_narrative)
                    
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
                            'Rapid accumulation pattern detected',
                            f'Number of filings: {len(sorted_filings)}'
                        ],
                        intent_analysis=intent,
                        regulatory_triggers=self._identify_regulatory_triggers(last),
                        evidence_hash=self._generate_hash([first, last]),
                        severity=Severity.HIGH if ownership_change > 10 else Severity.MEDIUM
                    ))
        
        return alerts
    
    def detect_filing_violations(
        self,
        filings: List[Schedule13Filing]
    ) -> List[OwnershipAlert]:
        """
        Detect filing deadline violations (December 2024 shortened deadlines).
        """
        alerts = []
        
        for filing in filings:
            if not filing.is_deadline_compliant:
                # Calculate business days (simplified - actual calculation more complex)
                calendar_days = filing.days_from_event_to_filing
                
                intent = self.analyze_intent_v2(filing.item4_narrative)
                
                alerts.append(OwnershipAlert(
                    alert_type=OwnershipAlertType.FILING_DEADLINE_VIOLATION,
                    subject_company_cik=filing.subject_company_cik,
                    subject_company_name=filing.subject_company_name,
                    involved_parties=[{
                        'name': filing.filer_name,
                        'cik': filing.cik,
                        'current_ownership': filing.percent_owned,
                        'event_date': filing.event_date.isoformat(),
                        'filing_date': filing.filing_date.isoformat()
                    }],
                    aggregate_ownership=filing.percent_owned,
                    risk_indicators=[
                        f'Filing deadline exceeded',
                        f'Event date: {filing.event_date}',
                        f'Filing date: {filing.filing_date}',
                        f'Days elapsed: {calendar_days} (deadline: {filing.filing_deadline_days} business days)',
                        f'Filing type: {filing.filing_type.value}'
                    ],
                    intent_analysis=intent,
                    regulatory_triggers=[
                        'SEC Release No. 34-99232 deadline violation',
                        'Potential enforcement action',
                        'Rule 13d-1/13d-2 non-compliance'
                    ],
                    evidence_hash=self._generate_hash([filing]),
                    filing_compliance_issues=[
                        f'Deadline violation: {calendar_days} days vs {filing.filing_deadline_days} business days required'
                    ],
                    severity=Severity.HIGH if calendar_days > filing.filing_deadline_days * 2 else Severity.MEDIUM
                ))
        
        return alerts
    
    def analyze_intent_v2(self, narrative: str) -> IntentAnalysis:
        """
        Enhanced intent analysis from Item 4 narrative.
        
        Args:
            narrative: Item 4 purpose of transaction text
            
        Returns:
            IntentAnalysis with signals and scoring
        """
        if not narrative:
            return IntentAnalysis(
                hostile_indicators=[],
                passive_indicators=[],
                intent_score=0.0,
                primary_intent=IntentSignal.PASSIVE_INVESTMENT,
                secondary_intents=[],
                confidence=0.0
            )
        
        lower = narrative.lower()
        
        found_hostile = [ind for ind in self.HOSTILE_INDICATORS if ind in lower]
        found_passive = [ind for ind in self.PASSIVE_INDICATORS if ind in lower]
        
        # Score from -1 (passive) to +1 (hostile)
        hostile_weight = len(found_hostile) * 0.2
        passive_weight = len(found_passive) * 0.2
        intent_score = max(-1, min(1, hostile_weight - passive_weight))
        
        # Determine primary intent
        primary_intent = IntentSignal.PASSIVE_INVESTMENT
        if 'board' in lower and 'representation' in lower:
            primary_intent = IntentSignal.BOARD_REPRESENTATION
        elif 'proxy' in lower and 'contest' in lower:
            primary_intent = IntentSignal.PROXY_CONTEST
        elif 'merger' in lower or 'acquisition' in lower:
            primary_intent = IntentSignal.MERGER_ACQUISITION
        elif 'strategic alternatives' in lower:
            primary_intent = IntentSignal.STRATEGIC_ALTERNATIVES
        elif 'replace' in lower and 'management' in lower:
            primary_intent = IntentSignal.MANAGEMENT_CHANGE
        
        # Determine secondary intents
        secondary = []
        if 'restructuring' in lower:
            secondary.append(IntentSignal.ASSET_RESTRUCTURING)
        if 'spin' in lower and 'off' in lower:
            secondary.append(IntentSignal.SPIN_OFF)
        
        # Confidence based on amount of text and indicators found
        confidence = min(1.0, (len(found_hostile) + len(found_passive)) / 10 * 0.5 + min(len(narrative) / 1000, 0.5))
        
        return IntentAnalysis(
            hostile_indicators=found_hostile,
            passive_indicators=found_passive,
            intent_score=intent_score,
            primary_intent=primary_intent,
            secondary_intents=secondary,
            confidence=confidence
        )
    
    def _calculate_group_coordination_score(
        self,
        filings: List[Schedule13Filing]
    ) -> float:
        """
        Calculate group coordination score (0.0-1.0) for Section 13(d)(3) analysis.
        
        Factors:
        1. Temporal proximity of filings
        2. Similar ownership percentages
        3. Similar narratives/intent
        4. Explicit group member declarations
        """
        if len(filings) < 2:
            return 0.0
        
        # Temporal proximity factor
        filing_dates = [f.filing_date for f in filings]
        date_range = (max(filing_dates) - min(filing_dates)).days
        temporal_factor = max(0, 1 - date_range / 90)  # 90 day window
        
        # Ownership similarity factor
        ownerships = [f.percent_owned for f in filings]
        avg_ownership = sum(ownerships) / len(ownerships)
        variance = sum((o - avg_ownership) ** 2 for o in ownerships) / len(ownerships)
        std_dev = variance ** 0.5
        similarity_factor = max(0, 1 - std_dev / 10)  # Normalize by 10%
        
        # Explicit group declaration factor
        has_group_members = any(f.group_member_ciks for f in filings)
        group_factor = 1.0 if has_group_members else 0.5
        
        return (temporal_factor * 0.4 + similarity_factor * 0.3 + group_factor * 0.3)
    
    def _correlate_with_node7(
        self,
        subject_company_cik: str,
        filer_names: List[str],
        node7_output: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Correlate with Node 7 13F holdings data.
        
        Args:
            subject_company_cik: Subject company CIK
            filer_names: List of filer names from 13D/13G
            node7_output: Node 7 output
            
        Returns:
            Correlation data or None
        """
        if not node7_output or not hasattr(node7_output, 'wolf_pack_alerts'):
            return None
        
        for wolf_pack in node7_output.wolf_pack_alerts:
            # Check for institution overlap
            overlap = set(filer_names).intersection(set(wolf_pack.institutions))
            
            if overlap:
                return {
                    "wolf_pack_id": wolf_pack.pack_id,
                    "overlapping_institutions": list(overlap),
                    "13f_aggregate_ownership": wolf_pack.aggregate_ownership_percent,
                    "13f_coordination_score": wolf_pack.coordination_score,
                    "correlation": "CONFIRMED",
                    "risk_level": "CRITICAL - Coordinated 13F + 13D activity"
                }
        
        return None
    
    def _identify_regulatory_triggers(self, filing: Schedule13Filing) -> List[str]:
        """Identify regulatory threshold triggers."""
        triggers = []
        ownership = filing.percent_owned
        
        if 5 <= ownership < 10:
            triggers.append('5% beneficial ownership threshold - Schedule 13D/13G required')
        if ownership >= 10:
            triggers.append('10% ownership - Heightened 13D amendment requirements (2 business days)')
        if ownership >= 20:
            triggers.append('20% ownership - Potential Hart-Scott-Rodino notification')
        if ownership >= 25:
            triggers.append('25% ownership - Presumption of control threshold')
        if ownership >= 50:
            triggers.append('50% ownership - Majority control achieved')
        
        if filing.schedule_type == '13D':
            triggers.append('Schedule 13D filed - Active/non-passive investment')
        
        if not filing.is_deadline_compliant:
            triggers.append(f'Filing deadline violation - SEC Release No. 34-99232')
        
        return triggers
    
    def _group_filings(
        self, 
        filings: List[Schedule13Filing]
    ) -> Dict[str, List[Schedule13Filing]]:
        """Group filings by filer + subject company."""
        result = defaultdict(list)
        for f in filings:
            key = f'{f.cik}-{f.subject_company_cik}'
            result[key].append(f)
        return dict(result)
    
    def _find_temporal_clusters(
        self,
        filings: List[Schedule13Filing],
        window_days: int
    ) -> List[List[Schedule13Filing]]:
        """Find clusters of filings within temporal window."""
        if not filings:
            return []
        
        sorted_f = sorted(filings, key=lambda f: f.filing_date)
        clusters = []
        current = [sorted_f[0]]
        
        for f in sorted_f[1:]:
            if (f.filing_date - current[0].filing_date).days <= window_days:
                # Only add if different filer
                if f.cik not in [x.cik for x in current]:
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
