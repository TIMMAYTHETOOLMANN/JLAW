"""
Node 6: Enforcement Routing
============================

Maps violations to appropriate enforcement agencies with penalty
structures and prosecution recommendations.

Agencies:
- SEC Division of Enforcement: Market manipulation, fraud, disclosure
- DOJ Securities & Financial Fraud: Criminal referrals
- IRS: Tax violations (IRC §83)
- DOJ Tax Division: Criminal tax evasion
- OSHA: Workplace safety (29 CFR 1910)
- EPA: Environmental violations
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EnforcementAgency(Enum):
    """Federal enforcement agencies."""
    SEC_ENFORCEMENT = "SEC Division of Enforcement"
    DOJ_SECURITIES = "DOJ Securities & Financial Fraud Unit"
    DOJ_TAX = "DOJ Tax Division"
    IRS_EXAM = "IRS Examination Division"
    IRS_CI = "IRS Criminal Investigation"
    OSHA = "OSHA Area Office"
    EPA = "EPA Regional Office"
    FINRA = "FINRA Enforcement"
    PCAOB = "PCAOB Division of Enforcement"
    CFTC = "CFTC Division of Enforcement"


class ViolationType(Enum):
    """Violation type classification."""
    # Securities Violations
    SECURITIES_FRAUD = "Securities Fraud (10b-5)"
    INSIDER_TRADING = "Insider Trading"
    MARKET_MANIPULATION = "Market Manipulation"
    DISCLOSURE_VIOLATION = "Disclosure Violation"
    PROXY_VIOLATION = "Proxy Rule Violation"
    SHORT_SWING_PROFIT = "Short-Swing Profit (16b)"
    LATE_FILING = "Late Filing Violation"
    BENEFICIAL_OWNERSHIP = "Beneficial Ownership Violation"
    
    # SOX Violations
    SOX_302_CERTIFICATION = "SOX 302 Certification Fraud"
    SOX_404_CONTROLS = "SOX 404 Internal Control Deficiency"
    SOX_906_CERTIFICATION = "SOX 906 Criminal Certification"
    
    # Tax Violations
    IRC_83_VIOLATION = "IRC §83 Compensation Violation"
    TAX_EVASION = "Tax Evasion"
    FALSE_RETURN = "False Tax Return"
    
    # Other
    WIRE_FRAUD = "Wire Fraud"
    MAIL_FRAUD = "Mail Fraud"
    OBSTRUCTION = "Obstruction of Justice"
    DOCUMENT_DESTRUCTION = "Document Destruction"


class PenaltySeverity(Enum):
    """Penalty severity tiers."""
    TIER_1 = "Tier 1 - Standard"
    TIER_2 = "Tier 2 - Fraud/Deceit"
    TIER_3 = "Tier 3 - Substantial Losses"


@dataclass
class StatutoryReference:
    """Reference to applicable statute."""
    citation: str
    name: str
    description: str
    penalties_civil: str
    penalties_criminal: str
    govinfo_url: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation": self.citation,
            "name": self.name,
            "description": self.description,
            "penalties_civil": self.penalties_civil,
            "penalties_criminal": self.penalties_criminal,
            "govinfo_url": self.govinfo_url
        }


@dataclass
class EnforcementRouting:
    """Routing decision for a violation."""
    primary_agency: EnforcementAgency
    secondary_agencies: List[EnforcementAgency]
    violation_type: ViolationType
    statutory_references: List[StatutoryReference]
    penalty_severity: PenaltySeverity
    estimated_civil_penalty: float
    criminal_referral_recommended: bool
    criminal_exposure_years: int
    routing_rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_agency": self.primary_agency.value,
            "secondary_agencies": [a.value for a in self.secondary_agencies],
            "violation_type": self.violation_type.value,
            "statutory_references": [s.to_dict() for s in self.statutory_references],
            "penalty_severity": self.penalty_severity.value,
            "estimated_civil_penalty": self.estimated_civil_penalty,
            "criminal_referral_recommended": self.criminal_referral_recommended,
            "criminal_exposure_years": self.criminal_exposure_years,
            "routing_rationale": self.routing_rationale
        }


class EnforcementRouter:
    """
    Routes violations to appropriate enforcement agencies.
    
    Decision factors:
    - Violation type and severity
    - Scienter (intent) evidence
    - Monetary harm/damages
    - Pattern of conduct
    - Public interest
    """
    
    # Statutory reference database
    STATUTES = {
        "10b-5": StatutoryReference(
            citation="17 CFR § 240.10b-5",
            name="Rule 10b-5 - Employment of Manipulative and Deceptive Devices",
            description="Prohibits fraud in connection with purchase or sale of securities",
            penalties_civil="Up to $2,304,757 per violation (entities)",
            penalties_criminal="Up to 20 years imprisonment",
            govinfo_url="https://www.ecfr.gov/current/title-17/chapter-II/part-240/subpart-A/section-240.10b-5"
        ),
        "16b": StatutoryReference(
            citation="15 U.S.C. § 78p(b)",
            name="Section 16(b) - Short-Swing Profits",
            description="Recovery of short-swing profits by officers, directors, 10% owners",
            penalties_civil="Disgorgement of profits",
            penalties_criminal="N/A (civil remedy only)",
            govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2023-title15/html/USCODE-2023-title15-chap2B-sec78p.htm"
        ),
        "16a": StatutoryReference(
            citation="17 CFR § 240.16a-3",
            name="Rule 16a-3 - Reporting Transactions and Holdings",
            description="Insider transaction reporting requirements",
            penalties_civil="$10,000 - $100,000 per violation",
            penalties_criminal="N/A",
            govinfo_url="https://www.ecfr.gov/current/title-17/chapter-II/part-240/section-240.16a-3"
        ),
        "sox302": StatutoryReference(
            citation="15 U.S.C. § 7241",
            name="SOX Section 302 - Corporate Responsibility",
            description="CEO/CFO certification of financial reports",
            penalties_civil="Up to $1,000,000",
            penalties_criminal="Up to 10 years imprisonment",
            govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2023-title15/html/USCODE-2023-title15-chap98-subchapIII-sec7241.htm"
        ),
        "sox906": StatutoryReference(
            citation="18 U.S.C. § 1350",
            name="SOX Section 906 - Criminal Certification",
            description="Failure to certify periodic financial reports",
            penalties_civil="N/A",
            penalties_criminal="Willful: $5M and/or 20 years",
            govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2023-title18/html/USCODE-2023-title18-partI-chap63-sec1350.htm"
        ),
        "wire_fraud": StatutoryReference(
            citation="18 U.S.C. § 1343",
            name="Wire Fraud",
            description="Fraud using wire communications",
            penalties_civil="N/A",
            penalties_criminal="Up to 20 years imprisonment",
            govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2023-title18/html/USCODE-2023-title18-partI-chap63-sec1343.htm"
        ),
        "securities_fraud": StatutoryReference(
            citation="18 U.S.C. § 1348",
            name="Securities Fraud",
            description="Criminal securities fraud",
            penalties_civil="N/A",
            penalties_criminal="Up to 25 years imprisonment",
            govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2023-title18/html/USCODE-2023-title18-partI-chap63-sec1348.htm"
        ),
        "irc83": StatutoryReference(
            citation="26 U.S.C. § 83",
            name="IRC Section 83 - Property Transferred in Connection with Services",
            description="Taxation of property transferred for services",
            penalties_civil="Back taxes, interest, penalties (20-75%)",
            penalties_criminal="Tax evasion: up to 5 years",
            govinfo_url="https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapB-partII-sec83.htm"
        ),
    }
    
    # Penalty tiers (2024 amounts)
    PENALTY_AMOUNTS = {
        PenaltySeverity.TIER_1: {
            "individual": 11524,
            "entity": 115241
        },
        PenaltySeverity.TIER_2: {
            "individual": 115241,
            "entity": 576201
        },
        PenaltySeverity.TIER_3: {
            "individual": 230483,
            "entity": 1152415
        }
    }
    
    def __init__(self):
        pass
    
    def route_violation(
        self,
        violation_type: ViolationType,
        estimated_damages: float,
        scienter_evidence: bool = False,
        pattern_of_conduct: bool = False,
        public_company: bool = True
    ) -> EnforcementRouting:
        """
        Route a violation to appropriate enforcement agencies.
        
        Args:
            violation_type: Type of violation detected
            estimated_damages: Estimated monetary harm
            scienter_evidence: Evidence of intent/knowledge
            pattern_of_conduct: Multiple violations over time
            public_company: Whether issuer is public company
            
        Returns:
            EnforcementRouting with agency assignments and penalties
        """
        # Determine primary and secondary agencies
        primary, secondary = self._determine_agencies(
            violation_type, scienter_evidence, estimated_damages
        )
        
        # Get applicable statutes
        statutes = self._get_statutes(violation_type)
        
        # Determine penalty severity
        severity = self._determine_severity(
            estimated_damages, scienter_evidence, pattern_of_conduct
        )
        
        # Calculate estimated penalty
        penalty = self._calculate_penalty(severity, estimated_damages)
        
        # Determine criminal referral
        criminal = self._should_refer_criminal(
            violation_type, scienter_evidence, estimated_damages, pattern_of_conduct
        )
        
        # Get criminal exposure
        criminal_years = self._get_criminal_exposure(violation_type)
        
        # Generate rationale
        rationale = self._generate_rationale(
            violation_type, primary, criminal, severity
        )
        
        return EnforcementRouting(
            primary_agency=primary,
            secondary_agencies=secondary,
            violation_type=violation_type,
            statutory_references=statutes,
            penalty_severity=severity,
            estimated_civil_penalty=penalty,
            criminal_referral_recommended=criminal,
            criminal_exposure_years=criminal_years,
            routing_rationale=rationale
        )
    
    def _determine_agencies(
        self,
        violation_type: ViolationType,
        scienter: bool,
        damages: float
    ) -> tuple:
        """Determine primary and secondary enforcement agencies."""
        
        # Securities violations -> SEC primary
        if violation_type in [
            ViolationType.SECURITIES_FRAUD,
            ViolationType.INSIDER_TRADING,
            ViolationType.MARKET_MANIPULATION,
            ViolationType.DISCLOSURE_VIOLATION,
            ViolationType.SHORT_SWING_PROFIT,
            ViolationType.LATE_FILING,
        ]:
            primary = EnforcementAgency.SEC_ENFORCEMENT
            secondary = []
            
            # Criminal referral for scienter + large damages
            if scienter and damages > 1000000:
                secondary.append(EnforcementAgency.DOJ_SECURITIES)
        
        # SOX violations
        elif violation_type in [
            ViolationType.SOX_302_CERTIFICATION,
            ViolationType.SOX_404_CONTROLS,
            ViolationType.SOX_906_CERTIFICATION,
        ]:
            primary = EnforcementAgency.SEC_ENFORCEMENT
            secondary = [EnforcementAgency.PCAOB]
            
            if scienter:
                secondary.append(EnforcementAgency.DOJ_SECURITIES)
        
        # Tax violations
        elif violation_type in [
            ViolationType.IRC_83_VIOLATION,
            ViolationType.TAX_EVASION,
            ViolationType.FALSE_RETURN,
        ]:
            primary = EnforcementAgency.IRS_EXAM
            secondary = []
            
            if scienter:
                secondary.append(EnforcementAgency.IRS_CI)
                secondary.append(EnforcementAgency.DOJ_TAX)
        
        # Wire/mail fraud
        elif violation_type in [
            ViolationType.WIRE_FRAUD,
            ViolationType.MAIL_FRAUD,
        ]:
            primary = EnforcementAgency.DOJ_SECURITIES
            secondary = [EnforcementAgency.SEC_ENFORCEMENT]
        
        else:
            primary = EnforcementAgency.SEC_ENFORCEMENT
            secondary = []
        
        return primary, secondary
    
    def _get_statutes(self, violation_type: ViolationType) -> List[StatutoryReference]:
        """Get applicable statutory references for violation type."""
        mapping = {
            ViolationType.SECURITIES_FRAUD: ["10b-5", "securities_fraud"],
            ViolationType.INSIDER_TRADING: ["10b-5"],
            ViolationType.SHORT_SWING_PROFIT: ["16b"],
            ViolationType.LATE_FILING: ["16a"],
            ViolationType.SOX_302_CERTIFICATION: ["sox302"],
            ViolationType.SOX_906_CERTIFICATION: ["sox906"],
            ViolationType.IRC_83_VIOLATION: ["irc83"],
            ViolationType.WIRE_FRAUD: ["wire_fraud"],
        }
        
        statute_keys = mapping.get(violation_type, ["10b-5"])
        return [self.STATUTES[k] for k in statute_keys if k in self.STATUTES]
    
    def _determine_severity(
        self,
        damages: float,
        scienter: bool,
        pattern: bool
    ) -> PenaltySeverity:
        """Determine penalty severity tier."""
        if damages > 10000000 or (scienter and damages > 1000000):
            return PenaltySeverity.TIER_3
        elif scienter or pattern or damages > 100000:
            return PenaltySeverity.TIER_2
        else:
            return PenaltySeverity.TIER_1
    
    def _calculate_penalty(
        self,
        severity: PenaltySeverity,
        damages: float
    ) -> float:
        """Calculate estimated civil penalty."""
        tier_amounts = self.PENALTY_AMOUNTS[severity]
        
        # Penalty is generally per-violation or percentage of damages
        base_penalty = tier_amounts["entity"]
        
        # For large damages, penalty can be multiplied
        if damages > 1000000:
            multiplier = min(10, damages / 1000000)
            return base_penalty * multiplier
        
        return base_penalty
    
    def _should_refer_criminal(
        self,
        violation_type: ViolationType,
        scienter: bool,
        damages: float,
        pattern: bool
    ) -> bool:
        """Determine if criminal referral is recommended."""
        # Always criminal for certain violations with scienter
        criminal_violations = [
            ViolationType.SECURITIES_FRAUD,
            ViolationType.SOX_906_CERTIFICATION,
            ViolationType.WIRE_FRAUD,
            ViolationType.MAIL_FRAUD,
            ViolationType.OBSTRUCTION,
            ViolationType.TAX_EVASION,
        ]
        
        if violation_type in criminal_violations and scienter:
            return True
        
        # Large damages with pattern
        if damages > 5000000 and pattern:
            return True
        
        return False
    
    def _get_criminal_exposure(self, violation_type: ViolationType) -> int:
        """Get maximum criminal exposure in years."""
        exposures = {
            ViolationType.SECURITIES_FRAUD: 25,
            ViolationType.WIRE_FRAUD: 20,
            ViolationType.MAIL_FRAUD: 20,
            ViolationType.SOX_906_CERTIFICATION: 20,
            ViolationType.SOX_302_CERTIFICATION: 10,
            ViolationType.OBSTRUCTION: 20,
            ViolationType.TAX_EVASION: 5,
        }
        return exposures.get(violation_type, 0)
    
    def _generate_rationale(
        self,
        violation_type: ViolationType,
        agency: EnforcementAgency,
        criminal: bool,
        severity: PenaltySeverity
    ) -> str:
        """Generate routing rationale."""
        parts = [
            f"Violation: {violation_type.value}",
            f"Primary Agency: {agency.value}",
            f"Penalty Tier: {severity.value}",
        ]
        
        if criminal:
            parts.append("CRIMINAL REFERRAL RECOMMENDED - Sufficient scienter evidence and harm magnitude.")
        
        return " | ".join(parts)

