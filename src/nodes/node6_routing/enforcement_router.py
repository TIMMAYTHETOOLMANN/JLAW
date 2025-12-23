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


@dataclass
class AggregatedRoutingReport:
    """Comprehensive routing analysis across all nodes."""
    case_id: str
    company_name: str
    cik: str
    total_violations: int
    violations_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    primary_agencies: List[EnforcementAgency]
    secondary_agencies: List[EnforcementAgency]
    total_estimated_penalties: float
    criminal_referrals: int
    max_criminal_exposure_years: int
    prosecution_likelihood: str  # "High", "Medium", "Low"
    recommended_actions: List[str]
    routing_details: List[EnforcementRouting]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "case_id": self.case_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "total_violations": self.total_violations,
            "violations_by_type": self.violations_by_type,
            "violations_by_severity": self.violations_by_severity,
            "primary_agencies": [a.value for a in self.primary_agencies],
            "secondary_agencies": [a.value for a in self.secondary_agencies],
            "total_estimated_penalties": self.total_estimated_penalties,
            "criminal_referrals": self.criminal_referrals,
            "max_criminal_exposure_years": self.max_criminal_exposure_years,
            "prosecution_likelihood": self.prosecution_likelihood,
            "recommended_actions": self.recommended_actions,
            "routing_details": [r.to_dict() for r in self.routing_details]
        }


class IntelligentEnforcementRouter:
    """
    Intelligent enforcement router that analyzes violations across all 15 nodes.
    
    Aggregates violations from all forensic analysis nodes and determines
    optimal enforcement routing with jurisdiction analysis and prosecution
    likelihood estimation.
    
    Features:
    - Multi-node violation aggregation
    - Jurisdiction determination (SEC/DOJ/IRS/FinCEN/CFTC/State AGs)
    - Pattern-based severity escalation
    - Prosecution likelihood scoring
    - Coordinated multi-agency routing
    
    Usage:
        router = IntelligentEnforcementRouter()
        report = router.analyze_and_route(
            case_id="CASE-2019-001",
            company_name="NIKE, Inc.",
            cik="320187",
            node_results=all_node_results
        )
    """
    
    def __init__(self):
        self.base_router = EnforcementRouter()
        self.logger = logging.getLogger(__name__)
    
    def analyze_and_route(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        node_results: List[Dict[str, Any]]
    ) -> AggregatedRoutingReport:
        """
        Analyze violations across all nodes and generate routing report.
        
        Args:
            case_id: Unique case identifier
            company_name: Target company name
            cik: SEC CIK number
            node_results: Results from all 15 forensic analysis nodes
            
        Returns:
            AggregatedRoutingReport with comprehensive routing analysis
        """
        self.logger.info(f"Analyzing violations for enforcement routing: {company_name}")
        
        # Extract all violations from node results
        all_violations = self._extract_violations(node_results)
        
        if not all_violations:
            self.logger.warning("No violations found - generating empty report")
            return self._create_empty_report(case_id, company_name, cik)
        
        # Route each violation
        routing_details = []
        for violation in all_violations:
            routing = self._route_single_violation(violation)
            if routing:
                routing_details.append(routing)
        
        # Aggregate results
        violations_by_type = self._count_by_type(all_violations)
        violations_by_severity = self._count_by_severity(all_violations)
        
        # Determine agencies
        primary_agencies = self._extract_primary_agencies(routing_details)
        secondary_agencies = self._extract_secondary_agencies(routing_details)
        
        # Calculate totals
        total_penalties = sum(r.estimated_civil_penalty for r in routing_details)
        criminal_referrals = sum(1 for r in routing_details if r.criminal_referral_recommended)
        max_criminal_years = max(
            (r.criminal_exposure_years for r in routing_details),
            default=0
        )
        
        # Estimate prosecution likelihood
        prosecution_likelihood = self._estimate_prosecution_likelihood(
            total_violations=len(all_violations),
            criminal_referrals=criminal_referrals,
            total_damages=total_penalties,
            violations_by_type=violations_by_type
        )
        
        # Generate recommendations
        recommended_actions = self._generate_recommendations(
            routing_details,
            prosecution_likelihood,
            criminal_referrals
        )
        
        return AggregatedRoutingReport(
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            total_violations=len(all_violations),
            violations_by_type=violations_by_type,
            violations_by_severity=violations_by_severity,
            primary_agencies=primary_agencies,
            secondary_agencies=secondary_agencies,
            total_estimated_penalties=total_penalties,
            criminal_referrals=criminal_referrals,
            max_criminal_exposure_years=max_criminal_years,
            prosecution_likelihood=prosecution_likelihood,
            recommended_actions=recommended_actions,
            routing_details=routing_details
        )
    
    def _extract_violations(
        self,
        node_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract all violations from node results."""
        violations = []
        
        for node_result in node_results:
            node_id = node_result.get('node_id', 'unknown')
            node_violations = node_result.get('violations', [])
            
            # Add node context to each violation
            for violation in node_violations:
                if isinstance(violation, dict):
                    violation['source_node'] = node_id
                    violations.append(violation)
        
        return violations
    
    def _route_single_violation(
        self,
        violation: Dict[str, Any]
    ) -> Optional[EnforcementRouting]:
        """Route a single violation using base router."""
        try:
            # Map violation to ViolationType
            violation_type = self._map_violation_type(violation)
            
            # Extract violation details
            estimated_damages = violation.get('estimated_damages', 0)
            severity = violation.get('severity', 'MEDIUM')
            scienter = violation.get('scienter_evidence', False) or severity == 'CRITICAL'
            pattern = violation.get('pattern_of_conduct', False)
            
            # Route using base router
            routing = self.base_router.route_violation(
                violation_type=violation_type,
                estimated_damages=estimated_damages,
                scienter_evidence=scienter,
                pattern_of_conduct=pattern,
                public_company=True
            )
            
            return routing
            
        except Exception as e:
            self.logger.warning(f"Failed to route violation: {e}")
            return None
    
    def _map_violation_type(self, violation: Dict[str, Any]) -> ViolationType:
        """Map violation description to ViolationType enum."""
        description = violation.get('violation_type', '').lower()
        
        # Mapping logic
        if 'insider trading' in description or '10b-5' in description:
            return ViolationType.INSIDER_TRADING
        elif 'disclosure' in description or '8-k' in description:
            return ViolationType.DISCLOSURE_VIOLATION
        elif '16(b)' in description or 'short-swing' in description:
            return ViolationType.SHORT_SWING_PROFIT
        elif '16(a)' in description or 'late filing' in description:
            return ViolationType.LATE_FILING
        elif 'sox 302' in description:
            return ViolationType.SOX_302_CERTIFICATION
        elif 'sox 404' in description:
            return ViolationType.SOX_404_CONTROLS
        elif 'sox 906' in description:
            return ViolationType.SOX_906_CERTIFICATION
        elif 'irc' in description or 'tax' in description:
            return ViolationType.IRC_83_VIOLATION
        elif 'beneficial ownership' in description or '13d' in description or '13g' in description:
            return ViolationType.BENEFICIAL_OWNERSHIP
        elif 'market manipulation' in description:
            return ViolationType.MARKET_MANIPULATION
        elif 'proxy' in description or 'def 14a' in description:
            return ViolationType.PROXY_VIOLATION
        else:
            return ViolationType.SECURITIES_FRAUD  # Default
    
    def _count_by_type(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count violations by type."""
        counts = {}
        for violation in violations:
            vtype = violation.get('violation_type', 'Unknown')
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts
    
    def _count_by_severity(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count violations by severity."""
        counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for violation in violations:
            severity = violation.get('severity', 'MEDIUM')
            if severity in counts:
                counts[severity] += 1
        return counts
    
    def _extract_primary_agencies(
        self,
        routing_details: List[EnforcementRouting]
    ) -> List[EnforcementAgency]:
        """Extract unique primary agencies."""
        agencies = set()
        for routing in routing_details:
            agencies.add(routing.primary_agency)
        return list(agencies)
    
    def _extract_secondary_agencies(
        self,
        routing_details: List[EnforcementRouting]
    ) -> List[EnforcementAgency]:
        """Extract unique secondary agencies."""
        agencies = set()
        for routing in routing_details:
            agencies.update(routing.secondary_agencies)
        return list(agencies)
    
    def _estimate_prosecution_likelihood(
        self,
        total_violations: int,
        criminal_referrals: int,
        total_damages: float,
        violations_by_type: Dict[str, int]
    ) -> str:
        """
        Estimate prosecution likelihood based on violation profile.
        
        Scoring factors:
        - Number of violations (more = higher likelihood)
        - Criminal referrals (presence increases likelihood)
        - Total estimated damages (higher = higher likelihood)
        - Violation types (certain types more likely to prosecute)
        
        Returns:
            "High", "Medium", or "Low"
        """
        score = 0
        
        # Factor 1: Volume of violations
        if total_violations >= 10:
            score += 3
        elif total_violations >= 5:
            score += 2
        elif total_violations >= 2:
            score += 1
        
        # Factor 2: Criminal referrals
        if criminal_referrals >= 3:
            score += 4
        elif criminal_referrals >= 1:
            score += 2
        
        # Factor 3: Estimated damages
        if total_damages >= 10000000:  # $10M+
            score += 4
        elif total_damages >= 1000000:  # $1M+
            score += 3
        elif total_damages >= 100000:  # $100K+
            score += 1
        
        # Factor 4: High-profile violation types
        high_profile_types = [
            'insider trading', 'securities fraud', 'sox 906',
            'market manipulation', 'wire fraud'
        ]
        
        for vtype, count in violations_by_type.items():
            if any(hp in vtype.lower() for hp in high_profile_types):
                score += count
        
        # Classification
        if score >= 8:
            return "High"
        elif score >= 4:
            return "Medium"
        else:
            return "Low"
    
    def _generate_recommendations(
        self,
        routing_details: List[EnforcementRouting],
        prosecution_likelihood: str,
        criminal_referrals: int
    ) -> List[str]:
        """Generate action recommendations based on routing analysis."""
        recommendations = []
        
        # Always recommend documentation
        recommendations.append(
            "Compile comprehensive evidence package with FRE 902(13)/(14) compliance"
        )
        
        # Criminal referral recommendations
        if criminal_referrals > 0:
            recommendations.append(
                f"Prepare {criminal_referrals} criminal referral(s) to DOJ with scienter documentation"
            )
        
        # Prosecution likelihood recommendations
        if prosecution_likelihood == "High":
            recommendations.append(
                "HIGH PRIORITY: Expedite enforcement referral - strong prosecution indicators"
            )
            recommendations.append(
                "Coordinate with SEC Division of Enforcement and DOJ for parallel proceedings"
            )
        elif prosecution_likelihood == "Medium":
            recommendations.append(
                "Standard enforcement referral process - monitor for additional evidence"
            )
        else:
            recommendations.append(
                "Consider civil administrative proceedings before criminal referral"
            )
        
        # Agency-specific recommendations
        agencies = set()
        for routing in routing_details:
            agencies.add(routing.primary_agency)
            agencies.update(routing.secondary_agencies)
        
        if EnforcementAgency.SEC_ENFORCEMENT in agencies:
            recommendations.append(
                "File SEC enforcement referral via TCR system with Wells notice consideration"
            )
        
        if EnforcementAgency.DOJ_SECURITIES in agencies:
            recommendations.append(
                "Coordinate with DOJ Fraud Section for potential criminal prosecution"
            )
        
        if EnforcementAgency.IRS_CI in agencies:
            recommendations.append(
                "Submit IRS Form 3949-A for tax violation investigation"
            )
        
        return recommendations
    
    def _create_empty_report(
        self,
        case_id: str,
        company_name: str,
        cik: str
    ) -> AggregatedRoutingReport:
        """Create empty report when no violations found."""
        return AggregatedRoutingReport(
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            total_violations=0,
            violations_by_type={},
            violations_by_severity={},
            primary_agencies=[],
            secondary_agencies=[],
            total_estimated_penalties=0.0,
            criminal_referrals=0,
            max_criminal_exposure_years=0,
            prosecution_likelihood="N/A",
            recommended_actions=["No violations detected - no enforcement action required"],
            routing_details=[]
        )

