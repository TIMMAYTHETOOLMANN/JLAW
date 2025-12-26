#!/usr/bin/env python3
"""
NODE 4: 10-K SOX Certification Analyzer
Validates Sarbanes-Oxley Section 302/906 certifications in annual reports.
Detects: Certification omissions, material weakness disclosures, internal control
deficiencies, auditor opinion modifications, management report inconsistencies.

Legal Basis: SOX Section 302 (15 USC 7241), Section 906 (18 USC 1350),
SEC Rules 13a-14 and 13a-15, PCAOB AS 2201
"""

import re
import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timezone
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
from enum import Enum
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SOXViolationType(Enum):
    """Classification of SOX compliance violations"""
    SECTION_302_OMISSION = "section_302_certification_omission"
    SECTION_906_OMISSION = "section_906_certification_omission"
    MATERIAL_WEAKNESS = "material_weakness_disclosed"
    SIGNIFICANT_DEFICIENCY = "significant_deficiency_disclosed"
    ADVERSE_ICFR_OPINION = "adverse_icfr_opinion"
    SCOPE_LIMITATION = "audit_scope_limitation"
    LATE_REMEDIATION = "late_material_weakness_remediation"
    INCONSISTENT_DISCLOSURE = "inconsistent_management_disclosure"
    AUDITOR_CHANGE_PROXIMATE = "auditor_change_near_weakness"
    RESTATEMENT_CONTROL_FAILURE = "restatement_indicating_control_failure"
    CEO_CFO_SIGNATURE_MISSING = "required_signature_missing"
    DISCLOSURE_COMMITTEE_FAILURE = "disclosure_committee_failure"


class AuditOpinionType(Enum):
    """Types of auditor opinions"""
    UNQUALIFIED = "unqualified"
    QUALIFIED = "qualified"
    ADVERSE = "adverse"
    DISCLAIMER = "disclaimer"


class ICFROpinionType(Enum):
    """Types of ICFR opinions per AS 2201"""
    UNQUALIFIED = "unqualified"
    ADVERSE = "adverse"
    DISCLAIMER = "disclaimer"


@dataclass
class Section302Certification:
    """SOX Section 302 Certification per Rule 13a-14(a)"""
    certifier_name: str
    certifier_title: str  # CEO or CFO
    certification_date: date
    
    # Required certifications
    reviewed_report: bool = False
    no_material_misstatement: bool = False
    fair_presentation: bool = False
    
    # Internal controls certifications
    responsible_for_controls: bool = False
    designed_controls: bool = False
    evaluated_effectiveness: bool = False
    disclosed_to_auditors: bool = False
    disclosed_material_weakness: bool = False
    disclosed_significant_deficiencies: bool = False
    disclosed_fraud: bool = False
    
    # Disclosure of changes
    changes_in_icfr: Optional[str] = None
    
    # Raw certification text for evidence
    certification_text: str = ""


@dataclass
class Section906Certification:
    """SOX Section 906 Certification per 18 USC 1350"""
    certifier_name: str
    certifier_title: str
    certification_date: date
    
    # Criminal certification requirements
    fully_complies_with_requirements: bool = False
    fairly_presents_financial_condition: bool = False
    
    # Penalties acknowledged (implicit)
    # Willful violation: Up to $5M fine, 20 years imprisonment
    # Knowing violation: Up to $1M fine, 10 years imprisonment
    
    certification_text: str = ""


@dataclass
class MaterialWeakness:
    """Material weakness in internal control per AS 2201"""
    description: str
    control_area: str  # Revenue, Inventory, Financial Close, IT, etc.
    identified_date: date
    remediated: bool = False
    remediation_date: Optional[date] = None
    management_assessment: str = ""
    auditor_assessment: str = ""
    
    # Impact assessment
    accounts_affected: List[str] = field(default_factory=list)
    financial_statement_impact: str = ""
    
    def is_timely_remediated(self) -> bool:
        """Check if remediated within 1 year (typical expectation)"""
        if not self.remediated or not self.remediation_date:
            return False
        return (self.remediation_date - self.identified_date).days <= 365


@dataclass
class AuditOpinion:
    """External auditor opinion on financial statements and ICFR"""
    auditor_firm: str
    opinion_date: date
    fiscal_year_end: date
    
    # Financial statement opinion
    fs_opinion_type: AuditOpinionType
    fs_opinion_basis: str = ""
    
    # ICFR opinion (if integrated audit)
    icfr_opinion_type: Optional[ICFROpinionType] = None
    icfr_opinion_basis: str = ""
    
    # Critical Audit Matters (CAMs) per AS 3101
    critical_audit_matters: List[str] = field(default_factory=list)
    
    # Key audit matters / emphasis paragraphs
    going_concern_emphasis: bool = False
    other_emphasis_paragraphs: List[str] = field(default_factory=list)
    
    # Auditor tenure
    auditor_tenure_years: int = 0


@dataclass
class SOXViolation:
    """Detected SOX compliance violation"""
    violation_type: SOXViolationType
    severity: int  # 1-10
    description: str
    affected_certifications: List[str]
    regulatory_citations: List[str]
    evidence_text: str
    evidence_hash: str
    potential_penalties: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['violation_type'] = self.violation_type.value
        result['detected_at'] = self.detected_at.isoformat()
        return result


class SOXCertificationAnalyzer:
    """
    10-K SOX Certification Analyzer
    
    Validates compliance with:
    - SOX Section 302 (CEO/CFO quarterly/annual certifications)
    - SOX Section 906 (criminal certification requirements)
    - SEC Rules 13a-14, 13a-15 (certification requirements)
    - PCAOB AS 2201 (integrated audit of ICFR)
    
    Detects:
    - Missing or incomplete certifications
    - Material weaknesses and significant deficiencies
    - Adverse ICFR opinions
    - Auditor changes near control issues
    - Restatements indicating control failures
    """
    
    # Required Section 302 language per Rule 13a-14(a)
    SECTION_302_REQUIREMENTS = [
        r"(?i)reviewed\s+this\s+(?:annual|quarterly)\s+report",
        r"(?i)does\s+not\s+contain\s+any\s+untrue\s+statement\s+of\s+(?:a\s+)?material\s+fact",
        r"(?i)fairly\s+present(?:s)?\s+in\s+all\s+material\s+respects",
        r"(?i)responsible\s+for\s+establishing\s+and\s+maintaining",
        r"(?i)designed\s+such\s+(?:disclosure\s+)?controls",
        r"(?i)evaluated\s+the\s+effectiveness",
        r"(?i)disclosed.*to\s+(?:the\s+)?(?:registrant'?s?\s+)?auditors?",
    ]
    
    # Section 906 language per 18 USC 1350
    SECTION_906_REQUIREMENTS = [
        r"(?i)fully\s+complies\s+with\s+(?:the\s+)?requirements\s+of\s+section\s+13\(a\)",
        r"(?i)fairly\s+presents.*financial\s+condition",
        r"(?i)18\s+U\.?S\.?C\.?\s+(?:Section\s+)?1350",
    ]
    
    # Material weakness indicators
    MATERIAL_WEAKNESS_INDICATORS = [
        r"(?i)material\s+weakness",
        r"(?i)our\s+internal\s+control.*(?:was|were)\s+not\s+effective",
        r"(?i)management.*concluded.*(?:internal\s+controls?|ICFR).*(?:was|were)\s+not\s+effective",
        r"(?i)adverse\s+opinion\s+on\s+(?:the\s+effectiveness\s+of\s+)?internal\s+control",
    ]
    
    # Control areas for weakness categorization
    CONTROL_AREAS = [
        "revenue_recognition", "inventory", "accounts_receivable",
        "financial_close", "information_technology", "segregation_of_duties",
        "journal_entries", "management_override", "related_party",
        "income_taxes", "stock_compensation", "derivatives"
    ]
    
    def __init__(self, output_dir: str = "./output/node4_sox"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.violations: List[SOXViolation] = []
        self.section302_certs: List[Section302Certification] = []
        self.section906_certs: List[Section906Certification] = []
        self.material_weaknesses: List[MaterialWeakness] = []
        self.audit_opinion: Optional[AuditOpinion] = None
    
    def analyze_annual_report(
        self,
        filing_text: str,
        company_info: Dict[str, str],
        prior_year_weaknesses: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for 10-K SOX analysis
        
        Args:
            filing_text: Full text of 10-K filing
            company_info: Company metadata
            prior_year_weaknesses: Known weaknesses from prior year for remediation tracking
            
        Returns:
            Complete analysis results with violations
        """
        logger.info(f"Beginning SOX certification analysis for {company_info.get('name', 'Unknown')}")
        
        # Phase 1: Extract Section 302 certifications (Exhibits 31.1 and 31.2)
        self._extract_section_302_certifications(filing_text)
        logger.info(f"Extracted {len(self.section302_certs)} Section 302 certifications")
        
        # Phase 2: Extract Section 906 certifications (Exhibits 32.1 and 32.2)
        self._extract_section_906_certifications(filing_text)
        logger.info(f"Extracted {len(self.section906_certs)} Section 906 certifications")
        
        # Phase 3: Validate Section 302 completeness
        self._validate_section_302_completeness()
        
        # Phase 4: Validate Section 906 completeness
        self._validate_section_906_completeness()
        
        # Phase 5: Extract management ICFR report (Item 9A)
        self._extract_management_icfr_report(filing_text)
        
        # Phase 6: Extract auditor opinion and ICFR opinion
        self._extract_audit_opinions(filing_text)
        
        # Phase 7: Identify material weaknesses
        self._identify_material_weaknesses(filing_text)
        logger.info(f"Identified {len(self.material_weaknesses)} material weaknesses")
        
        # Phase 8: Validate weakness remediation
        if prior_year_weaknesses:
            self._validate_weakness_remediation(prior_year_weaknesses)
        
        # Phase 9: Cross-validate management and auditor assessments
        self._cross_validate_assessments()
        
        # Phase 10: Analyze auditor changes near control issues
        self._analyze_auditor_changes(filing_text, company_info)
        
        # Phase 11: Check for restatement indicators
        self._check_restatement_indicators(filing_text)
        
        return self._compile_results(company_info)
    
    def _extract_section_302_certifications(self, text: str) -> None:
        """Extract Section 302 certifications from Exhibits 31.1 and 31.2.

        Improved to detect certifications even when Exhibit headers are not
        directly adjacent to certification text (common in modern SEC filings).
        """
        # Strategy 1: Find Exhibit 31 sections directly
        exhibit_31_pattern = r"(?i)exhibit\s+31\.?\d?"
        exhibit_matches = list(re.finditer(exhibit_31_pattern, text))
        
        # Strategy 2: Find certification blocks by content pattern (backup)
        cert_content_pattern = r"(?i)(?:CERTIFICATION(?:S)?|I,\s+[A-Z][a-z]+\s+[A-Z])[^\n]*(?:certify|pursuant\s+to)"

        # Track found certifications to avoid duplicates
        found_certs = set()

        # Process Exhibit 31 matches
        for match in exhibit_matches:
            cert_region = text[match.start():match.end() + 5000]
            self._process_certification_region(cert_region, found_certs)

        # If we didn't find enough certifications, search by content
        if len(self.section302_certs) < 2:
            # Look for Rule 13a-14(a) references which indicate Section 302
            rule_13a_pattern = r"(?i)(?:rule|pursuant\s+to)\s+13a-14\(a\)"
            rule_matches = list(re.finditer(rule_13a_pattern, text))

            for match in rule_matches:
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 5000)
                cert_region = text[start:end]
                self._process_certification_region(cert_region, found_certs)

    def _process_certification_region(self, cert_region: str, found_certs: set) -> None:
        """Process a potential certification region and extract certification details."""
        # Extract certifier information
        name_pattern = r"(?i)(?:I,\s+)?([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)"
        title_pattern = r"(?i)(Chief\s+Executive\s+Officer|CEO|Chief\s+Financial\s+Officer|CFO|Principal\s+(?:Executive|Financial)\s+Officer)"

        name_match = re.search(name_pattern, cert_region)
        title_match = re.search(title_pattern, cert_region)

        if name_match and title_match:
            cert_key = (name_match.group(1), title_match.group(1))
            if cert_key in found_certs:
                return  # Skip duplicate
            found_certs.add(cert_key)

            cert = Section302Certification(
                certifier_name=name_match.group(1),
                certifier_title=title_match.group(1),
                certification_date=date.today(),  # Would parse actual date
                certification_text=cert_region[:3000]
            )

            # Check for required elements
            for i, pattern in enumerate(self.SECTION_302_REQUIREMENTS):
                if re.search(pattern, cert_region):
                    if i == 0:
                        cert.reviewed_report = True
                    elif i == 1:
                        cert.no_material_misstatement = True
                    elif i == 2:
                        cert.fair_presentation = True
                    elif i == 3:
                        cert.responsible_for_controls = True
                    elif i == 4:
                        cert.designed_controls = True
                    elif i == 5:
                        cert.evaluated_effectiveness = True
                    elif i == 6:
                        cert.disclosed_to_auditors = True

            # Check for weakness/deficiency disclosure
            if re.search(r"(?i)material\s+weakness", cert_region):
                cert.disclosed_material_weakness = True
            if re.search(r"(?i)significant\s+deficienc", cert_region):
                cert.disclosed_significant_deficiencies = True

            self.section302_certs.append(cert)

    def _extract_section_906_certifications(self, text: str) -> None:
        """Extract Section 906 certifications from Exhibits 32.1 and 32.2"""
        exhibit_32_pattern = r"(?i)exhibit\s+32\.?\d?"
        exhibit_matches = list(re.finditer(exhibit_32_pattern, text))
        
        for match in exhibit_matches:
            cert_region = text[match.start():match.end() + 3000]
            
            name_pattern = r"(?i)(?:I,\s+)?([A-Z][a-z]+\s+[A-Z]\.?\s*[A-Z][a-z]+)"
            title_pattern = r"(?i)(Chief\s+Executive\s+Officer|CEO|Chief\s+Financial\s+Officer|CFO)"
            
            name_match = re.search(name_pattern, cert_region)
            title_match = re.search(title_pattern, cert_region)
            
            if name_match:
                cert = Section906Certification(
                    certifier_name=name_match.group(1),
                    certifier_title=title_match.group(1) if title_match else "Unknown",
                    certification_date=date.today(),
                    certification_text=cert_region[:2000]
                )
                
                # Check for required elements
                if re.search(self.SECTION_906_REQUIREMENTS[0], cert_region):
                    cert.fully_complies_with_requirements = True
                if re.search(self.SECTION_906_REQUIREMENTS[1], cert_region):
                    cert.fairly_presents_financial_condition = True
                
                self.section906_certs.append(cert)
    
    def _validate_section_302_completeness(self) -> None:
        """Validate that Section 302 certifications are complete"""
        # Must have both CEO and CFO certifications
        ceo_cert = None
        cfo_cert = None
        
        for cert in self.section302_certs:
            if "CEO" in cert.certifier_title.upper() or "EXECUTIVE" in cert.certifier_title.upper():
                ceo_cert = cert
            if "CFO" in cert.certifier_title.upper() or "FINANCIAL" in cert.certifier_title.upper():
                cfo_cert = cert
        
        if not ceo_cert:
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.CEO_CFO_SIGNATURE_MISSING,
                severity=10,
                description="CEO Section 302 certification missing from 10-K filing",
                affected_certifications=["Section 302 CEO"],
                regulatory_citations=[
                    "SOX Section 302",
                    "17 CFR 240.13a-14(a)",
                    "Exchange Act Rule 13a-14(a)"
                ],
                evidence_text="No CEO certification found in Exhibit 31",
                evidence_hash=self._hash_evidence("CEO_302_MISSING"),
                potential_penalties={
                    "civil": "SEC enforcement action",
                    "criminal": "Up to $1M fine, 10 years (knowing)",
                    "criminal_willful": "Up to $5M fine, 20 years (willful)"
                }
            ))
        
        if not cfo_cert:
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.CEO_CFO_SIGNATURE_MISSING,
                severity=10,
                description="CFO Section 302 certification missing from 10-K filing",
                affected_certifications=["Section 302 CFO"],
                regulatory_citations=[
                    "SOX Section 302",
                    "17 CFR 240.13a-14(a)"
                ],
                evidence_text="No CFO certification found in Exhibit 31",
                evidence_hash=self._hash_evidence("CFO_302_MISSING"),
                potential_penalties={
                    "civil": "SEC enforcement action",
                    "criminal": "Up to $1M fine, 10 years"
                }
            ))
        
        # Validate completeness of found certifications
        for cert in [ceo_cert, cfo_cert]:
            if cert:
                missing = []
                if not cert.reviewed_report:
                    missing.append("reviewed report statement")
                if not cert.no_material_misstatement:
                    missing.append("no material misstatement statement")
                if not cert.fair_presentation:
                    missing.append("fair presentation statement")
                if not cert.responsible_for_controls:
                    missing.append("responsibility for controls")
                
                if missing:
                    self.violations.append(SOXViolation(
                        violation_type=SOXViolationType.SECTION_302_OMISSION,
                        severity=8,
                        description=f"{cert.certifier_title} certification missing required elements: {', '.join(missing)}",
                        affected_certifications=[f"Section 302 {cert.certifier_title}"],
                        regulatory_citations=["17 CFR 240.13a-14(a)"],
                        evidence_text=cert.certification_text[:500],
                        evidence_hash=self._hash_evidence(cert.certification_text[:500])
                    ))
    
    def _validate_section_906_completeness(self) -> None:
        """Validate Section 906 certifications"""
        if len(self.section906_certs) < 2:
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.SECTION_906_OMISSION,
                severity=10,
                description=f"Only {len(self.section906_certs)} Section 906 certification(s) found - requires both CEO and CFO",
                affected_certifications=["Section 906"],
                regulatory_citations=[
                    "18 USC 1350",
                    "SOX Section 906"
                ],
                evidence_text="Insufficient Section 906 certifications",
                evidence_hash=self._hash_evidence("906_INCOMPLETE"),
                potential_penalties={
                    "criminal_knowing": "$1M fine, up to 10 years imprisonment",
                    "criminal_willful": "$5M fine, up to 20 years imprisonment"
                }
            ))
    
    def _extract_management_icfr_report(self, text: str) -> None:
        """Extract Management's Report on Internal Control from Item 9A"""
        item9a_pattern = r"(?i)item\s+9a\.?\s*(?:\.\s*)?(?:controls?\s+and\s+procedures?)"
        match = re.search(item9a_pattern, text)
        
        if not match:
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.SECTION_302_OMISSION,
                severity=7,
                description="Item 9A (Controls and Procedures) section not found",
                affected_certifications=["Management ICFR Report"],
                regulatory_citations=["Regulation S-K Item 308"],
                evidence_text="Item 9A missing from 10-K",
                evidence_hash=self._hash_evidence("ITEM9A_MISSING")
            ))
            return
        
        # Extract relevant section
        icfr_region = text[match.start():match.end() + 10000]
        
        # Check for effectiveness conclusion
        effective_pattern = r"(?i)(?:management|we)\s+(?:have\s+)?concluded\s+that.*internal\s+control.*(?:was|were)\s+effective"
        not_effective_pattern = r"(?i)(?:management|we)\s+(?:have\s+)?concluded\s+that.*internal\s+control.*(?:was|were)\s+not\s+effective"
        
        if re.search(not_effective_pattern, icfr_region):
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.ADVERSE_ICFR_OPINION,
                severity=9,
                description="Management concluded that internal controls were NOT effective",
                affected_certifications=["Management ICFR Assessment"],
                regulatory_citations=[
                    "SOX Section 404(a)",
                    "17 CFR 240.13a-15(c)"
                ],
                evidence_text=icfr_region[:1000],
                evidence_hash=self._hash_evidence(icfr_region[:500])
            ))
        elif not re.search(effective_pattern, icfr_region):
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.INCONSISTENT_DISCLOSURE,
                severity=6,
                description="No clear management conclusion on ICFR effectiveness found",
                affected_certifications=["Management ICFR Assessment"],
                regulatory_citations=["Regulation S-K Item 308(a)"],
                evidence_text="Effectiveness conclusion unclear",
                evidence_hash=self._hash_evidence("ICFR_UNCLEAR")
            ))
    
    def _extract_audit_opinions(self, text: str) -> None:
        """Extract auditor opinion on financial statements and ICFR"""
        # Find Report of Independent Registered Public Accounting Firm
        auditor_pattern = r"(?i)report\s+of\s+independent\s+registered\s+public\s+accounting\s+firm"
        match = re.search(auditor_pattern, text)
        
        if not match:
            return
        
        opinion_region = text[match.start():match.end() + 15000]
        
        # Identify auditor
        firm_patterns = [
            r"(Deloitte\s*&?\s*Touche)",
            r"(Ernst\s*&?\s*Young)",
            r"(KPMG)",
            r"(PricewaterhouseCoopers|PwC)",
            r"(Grant\s+Thornton)",
            r"(BDO)",
            r"(RSM)",
            r"(Crowe)"
        ]
        
        auditor_firm = "Unknown"
        for pattern in firm_patterns:
            firm_match = re.search(pattern, opinion_region, re.IGNORECASE)
            if firm_match:
                auditor_firm = firm_match.group(1)
                break
        
        # Determine opinion type
        fs_opinion = AuditOpinionType.UNQUALIFIED
        icfr_opinion = ICFROpinionType.UNQUALIFIED
        
        if re.search(r"(?i)adverse\s+opinion", opinion_region):
            if re.search(r"(?i)adverse\s+opinion\s+on.*internal\s+control", opinion_region):
                icfr_opinion = ICFROpinionType.ADVERSE
            else:
                fs_opinion = AuditOpinionType.ADVERSE
        
        if re.search(r"(?i)qualified\s+opinion", opinion_region):
            fs_opinion = AuditOpinionType.QUALIFIED
        
        if re.search(r"(?i)disclaimer\s+of\s+opinion", opinion_region):
            fs_opinion = AuditOpinionType.DISCLAIMER
            icfr_opinion = ICFROpinionType.DISCLAIMER
        
        # Going concern
        going_concern = bool(re.search(r"(?i)going\s+concern|substantial\s+doubt.*ability\s+to\s+continue", opinion_region))
        
        self.audit_opinion = AuditOpinion(
            auditor_firm=auditor_firm,
            opinion_date=date.today(),  # Would parse actual
            fiscal_year_end=date.today(),
            fs_opinion_type=fs_opinion,
            icfr_opinion_type=icfr_opinion,
            going_concern_emphasis=going_concern
        )
        
        # Flag adverse ICFR opinion
        if icfr_opinion == ICFROpinionType.ADVERSE:
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.ADVERSE_ICFR_OPINION,
                severity=10,
                description=f"Auditor ({auditor_firm}) issued adverse opinion on internal control over financial reporting",
                affected_certifications=["Auditor ICFR Opinion"],
                regulatory_citations=[
                    "PCAOB AS 2201",
                    "SOX Section 404(b)"
                ],
                evidence_text=opinion_region[:1000],
                evidence_hash=self._hash_evidence(opinion_region[:500])
            ))
    
    def _identify_material_weaknesses(self, text: str) -> None:
        """Identify disclosed material weaknesses"""
        for pattern in self.MATERIAL_WEAKNESS_INDICATORS:
            matches = list(re.finditer(pattern, text))
            
            for match in matches:
                context = text[max(0, match.start() - 500):match.end() + 1000]
                
                # Determine control area
                control_area = "unspecified"
                for area in self.CONTROL_AREAS:
                    if re.search(area.replace("_", r"\s*"), context, re.IGNORECASE):
                        control_area = area
                        break
                
                weakness = MaterialWeakness(
                    description=context[:500],
                    control_area=control_area,
                    identified_date=date.today(),
                    management_assessment=context[:300]
                )
                
                # Check if remediated
                if re.search(r"(?i)remediat(?:ed|ion)", context):
                    weakness.remediated = True
                
                self.material_weaknesses.append(weakness)
                
                self.violations.append(SOXViolation(
                    violation_type=SOXViolationType.MATERIAL_WEAKNESS,
                    severity=9,
                    description=f"Material weakness disclosed in {control_area} control area",
                    affected_certifications=["Management ICFR Assessment", "Auditor ICFR Opinion"],
                    regulatory_citations=[
                        "PCAOB AS 2201.A7",
                        "SOX Section 404"
                    ],
                    evidence_text=context[:500],
                    evidence_hash=self._hash_evidence(context[:500])
                ))
    
    def _validate_weakness_remediation(self, prior_weaknesses: List[Dict]) -> None:
        """Check if prior year material weaknesses were remediated"""
        current_descriptions = [mw.description.lower()[:100] for mw in self.material_weaknesses]
        
        for prior in prior_weaknesses:
            prior_desc = prior.get('description', '').lower()[:100]
            
            # Check if still present
            still_present = any(
                prior_desc in current for current in current_descriptions
            )
            
            if still_present:
                self.violations.append(SOXViolation(
                    violation_type=SOXViolationType.LATE_REMEDIATION,
                    severity=8,
                    description=f"Material weakness from prior year ({prior.get('control_area', 'unknown')}) not remediated",
                    affected_certifications=["Management ICFR Assessment"],
                    regulatory_citations=["SEC Staff Views on ICFR"],
                    evidence_text=f"Prior weakness: {prior_desc}",
                    evidence_hash=self._hash_evidence(prior_desc)
                ))
    
    def _cross_validate_assessments(self) -> None:
        """Cross-validate management and auditor ICFR assessments"""
        if not self.audit_opinion:
            return
        
        # Check for consistency between management and auditor conclusions
        management_adverse = any(
            v.violation_type == SOXViolationType.ADVERSE_ICFR_OPINION
            for v in self.violations
            if "Management" in str(v.affected_certifications)
        )
        
        auditor_adverse = self.audit_opinion.icfr_opinion_type == ICFROpinionType.ADVERSE
        
        if management_adverse != auditor_adverse:
            self.violations.append(SOXViolation(
                violation_type=SOXViolationType.INCONSISTENT_DISCLOSURE,
                severity=8,
                description="Management and auditor ICFR assessments are inconsistent",
                affected_certifications=["Management ICFR Assessment", "Auditor ICFR Opinion"],
                regulatory_citations=[
                    "PCAOB AS 2201.86",
                    "SEC Release 34-47986"
                ],
                evidence_text=f"Management adverse: {management_adverse}, Auditor adverse: {auditor_adverse}",
                evidence_hash=self._hash_evidence(f"INCONSISTENT:{management_adverse}:{auditor_adverse}")
            ))
    
    def _analyze_auditor_changes(self, text: str, company_info: Dict) -> None:
        """Detect auditor changes that may indicate control issues"""
        auditor_change_pattern = r"(?i)(?:change|dismiss|resign|terminat).*(?:independent\s+)?(?:registered\s+)?(?:public\s+)?(?:accounting\s+firm|auditor)"
        
        if re.search(auditor_change_pattern, text):
            # Check if change is near material weakness disclosure
            if self.material_weaknesses:
                self.violations.append(SOXViolation(
                    violation_type=SOXViolationType.AUDITOR_CHANGE_PROXIMATE,
                    severity=7,
                    description="Auditor change detected in year with material weakness disclosure - potential red flag",
                    affected_certifications=["External Audit"],
                    regulatory_citations=[
                        "Item 4.01 Form 8-K",
                        "SEC Staff Views on Auditor Changes"
                    ],
                    evidence_text="Auditor change concurrent with MW",
                    evidence_hash=self._hash_evidence("AUDITOR_CHANGE_MW")
                ))
    
    def _check_restatement_indicators(self, text: str) -> None:
        """Check for restatement language indicating control failures.

        IMPORTANT: Excludes common false positives like:
        - "Restated Articles of Incorporation" (corporate governance document)
        - "Restated Bylaws" (corporate governance document)
        - References to prior period comparatives
        """
        # Patterns that indicate ACTUAL financial restatements
        restatement_patterns = [
            r"(?i)(?:financial\s+)?restatement\s+of\s+(?:financial\s+)?(?:statements?|results|earnings)",
            r"(?i)correction\s+of\s+(?:an?\s+)?error\s+in\s+(?:previously\s+)?(?:issued|reported)",
            r"(?i)restated\s+(?:financial\s+)?statements?\s+for\s+(?:the\s+)?(?:year|quarter|period)",
            r"(?i)(?:we|the\s+company)\s+(?:have\s+)?restated\s+(?:our|its)\s+(?:financial|prior)",
            r"(?i)material\s+misstatement.*(?:restat|correct)",
            r"(?i)(?:big\s+r|little\s+r)\s+restatement",
            r"(?i)restated\s+(?:to\s+correct|due\s+to)\s+(?:an?\s+)?(?:error|misstatement)",
            r"(?i)amended\s+and\s+restated\s+financial\s+statements?"
        ]

        # Patterns that should be EXCLUDED (false positives)
        false_positive_patterns = [
            r"(?i)restated\s+articles\s+of\s+incorporation",
            r"(?i)restated\s+bylaws?",
            r"(?i)restated\s+certificate\s+of\s+incorporation",
            r"(?i)(?:first|second|third|fourth|fifth)\s+restated\s+(?:articles|bylaws?|certificate)",
            r"(?i)amended\s+and\s+restated\s+(?:bylaws?|articles|certificate|charter)",
            r"(?i)exhibit\s+\d+\.\d+.*restated",  # Exhibit references to governance docs
            r"(?i)have\s+not\s+been\s+restated"  # Explicit statement of NO restatement
        ]
        
        text_lower = text.lower()

        # Check if we should skip due to false positive patterns dominating
        for fp_pattern in false_positive_patterns:
            # If false positive context found, be more careful
            if re.search(fp_pattern, text):
                # Only flag if we find an ACTUAL financial restatement pattern
                for actual_pattern in restatement_patterns[:4]:  # Use strict patterns
                    match = re.search(actual_pattern, text)
                    if match:
                        # Verify this isn't near a false positive marker
                        start = max(0, match.start() - 200)
                        end = min(len(text), match.end() + 200)
                        context = text[start:end]

                        # Skip if context contains governance document references
                        is_false_positive = any(
                            re.search(fp, context)
                            for fp in false_positive_patterns
                        )

                        if not is_false_positive:
                            self.violations.append(SOXViolation(
                                violation_type=SOXViolationType.RESTATEMENT_CONTROL_FAILURE,
                                severity=9,
                                description="Financial restatement language detected - indicates potential control failure",
                                affected_certifications=["Financial Statements", "ICFR"],
                                regulatory_citations=[
                                    "ASC 250-10",
                                    "SEC Staff Accounting Bulletin 99/108"
                                ],
                                evidence_text=context[:500],
                                evidence_hash=self._hash_evidence(context[:500])
                            ))
                            return
                return  # False positive detected, no actual restatement found

        # No false positive context - check for restatement patterns normally
        for pattern in restatement_patterns:
            match = re.search(pattern, text)
            if match:
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                self.violations.append(SOXViolation(
                    violation_type=SOXViolationType.RESTATEMENT_CONTROL_FAILURE,
                    severity=9,
                    description="Financial restatement language detected - indicates potential control failure",
                    affected_certifications=["Financial Statements", "ICFR"],
                    regulatory_citations=[
                        "ASC 250-10",
                        "SEC Staff Accounting Bulletin 99/108"
                    ],
                    evidence_text=context,
                    evidence_hash=self._hash_evidence(context)
                ))
                break
    
    def _hash_evidence(self, evidence: str) -> str:
        """Generate SHA-256 hash of evidence"""
        return hashlib.sha256(evidence.encode('utf-8')).hexdigest()
    
    def _compile_results(self, company_info: Dict) -> Dict[str, Any]:
        """Compile analysis results"""
        results = {
            "node": "NODE_4_SOX",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "company": company_info,
            "section_302_certifications": [
                {
                    "certifier": c.certifier_name,
                    "title": c.certifier_title,
                    "complete": all([
                        c.reviewed_report, c.no_material_misstatement,
                        c.fair_presentation, c.responsible_for_controls
                    ])
                }
                for c in self.section302_certs
            ],
            "section_906_certifications": [
                {
                    "certifier": c.certifier_name,
                    "title": c.certifier_title,
                    "complete": c.fully_complies_with_requirements and c.fairly_presents_financial_condition
                }
                for c in self.section906_certs
            ],
            "audit_opinion": {
                "firm": self.audit_opinion.auditor_firm,
                "fs_opinion": self.audit_opinion.fs_opinion_type.value,
                "icfr_opinion": self.audit_opinion.icfr_opinion_type.value if self.audit_opinion.icfr_opinion_type else None,
                "going_concern": self.audit_opinion.going_concern_emphasis
            } if self.audit_opinion else None,
            "material_weaknesses": [
                {
                    "control_area": mw.control_area,
                    "remediated": mw.remediated,
                    "description": mw.description[:200]
                }
                for mw in self.material_weaknesses
            ],
            "violations_detected": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "severity_summary": {
                "critical": len([v for v in self.violations if v.severity >= 9]),
                "high": len([v for v in self.violations if 7 <= v.severity < 9]),
                "medium": len([v for v in self.violations if 5 <= v.severity < 7]),
                "low": len([v for v in self.violations if v.severity < 5])
            },
            "sox_compliance_score": self._calculate_compliance_score()
        }
        
        # Write results
        output_path = self.output_dir / f"sox_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"SOX certification analysis complete. Results: {output_path}")
        
        return results
    
    def _calculate_compliance_score(self) -> float:
        """Calculate overall SOX compliance score (0-100)"""
        score = 100.0
        
        for violation in self.violations:
            # Deduct based on severity
            if violation.severity >= 9:
                score -= 20
            elif violation.severity >= 7:
                score -= 10
            elif violation.severity >= 5:
                score -= 5
            else:
                score -= 2
        
        return max(0.0, score)


# CLI Entry Point
if __name__ == "__main__":
    analyzer = SOXCertificationAnalyzer()
    
    # Demo analysis
    sample_10k = """
    EXHIBIT 31.1
    CERTIFICATION OF CHIEF EXECUTIVE OFFICER
    
    I, John Smith, certify that:
    
    1. I have reviewed this annual report on Form 10-K of Nike, Inc.;
    
    2. Based on my knowledge, this report does not contain any untrue statement 
    of a material fact or omit to state a material fact necessary...
    
    3. Based on my knowledge, the financial statements, and other financial 
    information included in this report, fairly present in all material respects 
    the financial condition...
    
    4. The registrant's other certifying officer(s) and I are responsible for 
    establishing and maintaining disclosure controls and procedures...
    
    5. The registrant's other certifying officer(s) and I have:
    (a) Designed such disclosure controls and procedures...
    (b) Evaluated the effectiveness of the registrant's disclosure controls...
    (c) Disclosed in this report any change in the registrant's internal control...
    
    EXHIBIT 32.1
    CERTIFICATION PURSUANT TO 18 U.S.C. SECTION 1350
    
    I, John Smith, Chief Executive Officer, hereby certify that this annual report 
    fully complies with the requirements of section 13(a) or 15(d) of the Securities 
    Exchange Act of 1934 and that information contained in this report fairly presents,
    in all material respects, the financial condition and results of operations.
    
    ITEM 9A. CONTROLS AND PROCEDURES
    
    Management's Report on Internal Control Over Financial Reporting
    
    Management has concluded that our internal control over financial reporting was 
    effective as of the end of the fiscal year.
    
    Report of Independent Registered Public Accounting Firm
    
    PricewaterhouseCoopers LLP
    
    In our opinion, the Company maintained, in all material respects, effective 
    internal control over financial reporting.
    """
    
    company_info = {"cik": "0000320187", "name": "NIKE, Inc."}
    results = analyzer.analyze_annual_report(sample_10k, company_info)
    print(json.dumps(results, indent=2, default=str))

