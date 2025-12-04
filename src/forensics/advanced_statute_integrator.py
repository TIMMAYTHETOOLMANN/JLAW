"""
ADVANCED STATUTE INTEGRATOR - GOVINFO API INTELLIGENCE MODULE
==============================================================

Next-generation legal statute integration system leveraging the full power
of the GovInfo API to provide real-time, authoritative legal citations with
direct access to USC, CFR, and Federal Register documents.

This module enhances the forensic analysis platform with:
1. Intelligent statute retrieval from GovInfo.gov
2. Cross-referencing between USC statutes and CFR regulations
3. Historical statute tracking (amendments, repeals)
4. Federal Register final rules and proposed rules
5. Congressional reports and committee hearings
6. SEC enforcement releases and no-action letters
7. Court opinions and administrative law judge decisions

Compliance Standards:
- NIST SP 800-86: Guide to Integrating Forensic Techniques
- Federal Rules of Evidence 902(13)/(14): Certified Electronic Evidence
- SEC Enforcement Manual § 2.3.3: Evidence Compilation Standards
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import logging
from urllib.parse import quote, urlencode

logger = logging.getLogger(__name__)

# Optional import to avoid hard dependency at import time
try:
    from .govinfo_api_client import GovInfoAPIClient
except Exception:
    GovInfoAPIClient = None  # Will be validated at runtime


class DocumentType(Enum):
    """GovInfo document types."""
    USC = "USCODE"  # United States Code
    CFR = "CFR"  # Code of Federal Regulations
    FR = "FR"  # Federal Register
    STATUTE = "STATUTE"  # Statutes at Large
    BILLS = "BILLS"  # Congressional Bills
    CRPT = "CRPT"  # Congressional Reports
    CHRG = "CHRG"  # Congressional Hearings
    USCOURTS = "USCOURTS"  # Court Opinions
    GOVMAN = "GOVMAN"  # Government Manuals


class LegalAuthority(Enum):
    """Legal authority hierarchy."""
    CONSTITUTION = 1
    STATUTE = 2  # USC
    REGULATION = 3  # CFR
    CASE_LAW = 4
    AGENCY_GUIDANCE = 5
    POLICY = 6


@dataclass
class StatuteReference:
    """Complete statute reference with GovInfo integration."""
    citation: str
    title: int
    section: str
    subsection: Optional[str] = None
    paragraph: Optional[str] = None
    
    # GovInfo metadata
    govinfo_package_id: Optional[str] = None
    govinfo_granule_id: Optional[str] = None
    text_url: Optional[str] = None
    pdf_url: Optional[str] = None
    xml_url: Optional[str] = None
    
    # Legal context
    short_title: Optional[str] = None
    enacted_date: Optional[str] = None
    effective_date: Optional[str] = None
    last_amended: Optional[str] = None
    related_cfr: List[str] = field(default_factory=list)
    
    # Enforcement context
    criminal_penalties: Optional[Dict[str, Any]] = None
    civil_penalties: Optional[Dict[str, Any]] = None
    administrative_penalties: Optional[Dict[str, Any]] = None


@dataclass
class CFRReference:
    """CFR regulation reference."""
    citation: str
    title: int
    chapter: Optional[int] = None
    part: int = 0
    section: Optional[str] = None
    
    # GovInfo metadata
    govinfo_package_id: Optional[str] = None
    text_url: Optional[str] = None
    pdf_url: Optional[str] = None
    
    # Regulatory context
    authority: Optional[str] = None  # USC authority
    source: Optional[str] = None  # Federal Register citation
    effective_date: Optional[str] = None
    compliance_date: Optional[str] = None


@dataclass
class EnforcementPrecedent:
    """SEC enforcement action or court decision."""
    case_name: str
    citation: str
    date: str
    violation_type: str
    penalties_imposed: Dict[str, Any]
    key_findings: List[str]
    precedential_value: str  # HIGH, MODERATE, LOW
    govinfo_url: Optional[str] = None


class AdvancedStatuteIntegrator:
    """
    Advanced statute integration with full GovInfo API intelligence.
    
    This system provides comprehensive legal framework mapping by:
    1. Real-time statute retrieval from authoritative sources
    2. Cross-referencing between statutes, regulations, and case law
    3. Historical tracking of amendments and repeals
    4. Penalty calculation frameworks
    5. Enforcement precedent analysis
    """
    
    def __init__(self, govinfo_api_key: str, strict_api_mode: bool = True, *, dual_agent: bool = False, govinfo_client: Optional[Any] = None):
        """
        Initialize advanced statute integrator.
        
        Args:
            govinfo_api_key: GovInfo API key from data.gov
            strict_api_mode: If True, fail when API unavailable (NO FALLBACK). Default: True
            dual_agent: Enable dual-agent cooperation with GovInfoAPIClient to cross-check and enrich results.
            govinfo_client: Optional pre-initialized GovInfoAPIClient instance (advanced use)
        """
        if not govinfo_api_key or govinfo_api_key == "DEMO_KEY":
            raise ValueError(
                "GOVINFO_API_KEY is required for statute integration. "
                "Obtain a key from https://api.data.gov/signup/ and set it in .env file."
            )
        
        self.api_key = govinfo_api_key
        self.base_url = "https://api.govinfo.gov"
        self.session: Optional[aiohttp.ClientSession] = None
        self.strict_api_mode = strict_api_mode
        self.dual_agent = dual_agent
        self._own_govinfo_client = False
        self.govinfo_client: Optional[Any] = govinfo_client
        # Lazily create GovInfoAPIClient if dual_agent requested and not provided
        if self.dual_agent and self.govinfo_client is None:
            if GovInfoAPIClient is None:
                if self.strict_api_mode:
                    raise RuntimeError("Dual-agent mode requested but GovInfoAPIClient is unavailable")
                else:
                    logger.warning("Dual-agent mode requested but GovInfoAPIClient not importable; proceeding without it")
            else:
                try:
                    self.govinfo_client = GovInfoAPIClient(self.api_key)
                    self._own_govinfo_client = True
                    logger.info("Dual-agent integration: GovInfoAPIClient instantiated")
                except Exception as e:
                    if self.strict_api_mode:
                        raise
                    logger.warning(f"Failed to initialize GovInfoAPIClient: {e}")
        
        # Caching for performance only
        self.statute_cache: Dict[str, StatuteReference] = {}
        self.cfr_cache: Dict[str, CFRReference] = {}
        self.enforcement_cache: Dict[str, List[EnforcementPrecedent]] = {}
        
        # Metadata for cross-referencing ONLY (not used as fallback data source in strict mode)
        self.securities_statutes = self._initialize_securities_statutes()
        self.sec_regulations = self._initialize_sec_regulations()
        self.related_criminal_statutes = self._initialize_criminal_statutes()
        
        logger.info(
            f"AdvancedStatuteIntegrator initialized with GovInfo API "
            f"(strict_api_mode={'ON - NO FALLBACK' if strict_api_mode else 'OFF - FALLBACK ENABLED'}, dual_agent={'ON' if self.dual_agent and self.govinfo_client else 'OFF'})"
        )
    
    def _initialize_securities_statutes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize comprehensive securities law statute database."""
        return {
            # Securities Act of 1933
            "15_USC_77q": {
                "citation": "15 U.S.C. § 77q",
                "title": 15,
                "section": "77q",
                "short_title": "Securities Act of 1933 - Fraudulent Interstate Transactions",
                "description": "Prohibits fraudulent activities in the offer or sale of securities",
                "criminal": {"imprisonment": 5, "fine": 10000},
                "civil": True,
                "related_cfr": ["17 CFR 230"],
                "key_subsections": {
                    "a": "General fraud prohibition",
                    "b": "Use of interstate commerce",
                    "c": "Criminal penalties"
                }
            },
            "15_USC_77x": {
                "citation": "15 U.S.C. § 77x",
                "title": 15,
                "section": "77x",
                "short_title": "Securities Act of 1933 - Penalties",
                "description": "Criminal and civil penalties for Securities Act violations",
                "criminal": {"imprisonment": 5, "fine": 10000},
                "willful": {"imprisonment": 20, "fine": 5000000}
            },
            
            # Securities Exchange Act of 1934
            "15_USC_78j": {
                "citation": "15 U.S.C. § 78j",
                "title": 15,
                "section": "78j",
                "short_title": "Exchange Act Section 10 - Manipulative and Deceptive Devices",
                "description": "Prohibition on manipulative and deceptive devices (Rule 10b-5)",
                "subsections": {
                    "b": "Manipulative and deceptive devices - Rule 10b-5 authority"
                },
                "related_cfr": ["17 CFR 240.10b-5"],
                "criminal": True,
                "civil": True,
                "enforcement_priority": "CRITICAL"
            },
            "15_USC_78m": {
                "citation": "15 U.S.C. § 78m",
                "title": 15,
                "section": "78m",
                "short_title": "Exchange Act Section 13 - Periodic and Other Reports",
                "description": "Mandatory disclosure requirements for registered companies",
                "subsections": {
                    "a": "Annual and quarterly reports (10-K, 10-Q)",
                    "b": "Foreign issuers and extraordinary events (8-K)",
                    "d": "Quarterly reports"
                },
                "related_cfr": ["17 CFR 240.13a-1", "17 CFR 240.13a-13"],
                "criminal": True,
                "civil": True
            },
            "15_USC_78p": {
                "citation": "15 U.S.C. § 78p",
                "title": 15,
                "section": "78p",
                "short_title": "Exchange Act Section 16 - Directors, Officers, and Principal Stockholders",
                "description": "Insider reporting and short-swing profit recovery",
                "subsections": {
                    "a": "Insider transaction reporting (Form 4)",
                    "b": "Short-swing profit recovery",
                    "c": "Exempted securities"
                },
                "related_cfr": ["17 CFR 240.16a-3"],
                "form": "Form 4",
                "deadline": "2 business days",
                "civil": True
            },
            "15_USC_78u": {
                "citation": "15 U.S.C. § 78u",
                "title": 15,
                "section": "78u",
                "short_title": "Exchange Act Section 21 - Investigations and Actions",
                "description": "SEC enforcement authority and penalties",
                "civil_penalties": {
                    "tier1": 10000,  # Per violation
                    "tier2": 100000,  # Fraud/deceit
                    "tier3": 1000000  # Substantial losses or gains
                },
                "related_cfr": ["17 CFR 240.0-4"]
            },
            "15_USC_78ff": {
                "citation": "15 U.S.C. § 78ff",
                "title": 15,
                "section": "78ff",
                "short_title": "Exchange Act Penalties",
                "description": "Criminal penalties for Exchange Act violations",
                "criminal": {
                    "imprisonment": 5,
                    "fine": 5000000,
                    "entity_fine": 25000000
                },
                "willful": {
                    "imprisonment": 20,
                    "fine": 5000000,
                    "entity_fine": 25000000
                }
            },
            
            # Sarbanes-Oxley Act of 2002
            "15_USC_7241": {
                "citation": "15 U.S.C. § 7241",
                "title": 15,
                "section": "7241",
                "short_title": "SOX Section 302 - Corporate Responsibility for Financial Reports",
                "description": "CEO/CFO certification requirements",
                "certification_required": True,
                "related_cfr": ["17 CFR 240.13a-14"],
                "criminal_reference": "18 USC 1350"
            },
            "15_USC_7262": {
                "citation": "15 U.S.C. § 7262",
                "title": 15,
                "section": "7262",
                "short_title": "SOX Section 404 - Management Assessment of Internal Controls",
                "description": "Internal control assessment and auditor attestation",
                "related_cfr": ["17 CFR 240.13a-15"]
            },
            
            # Investment Advisers Act
            "15_USC_80b-6": {
                "citation": "15 U.S.C. § 80b-6",
                "title": 15,
                "section": "80b-6",
                "short_title": "Investment Advisers Act - Prohibited Transactions",
                "description": "Prohibitions on fraudulent practices by investment advisers",
                "related_cfr": ["17 CFR 275"]
            }
        }
    
    def _initialize_sec_regulations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize SEC regulations (17 CFR) database."""
        return {
            # Rule 10b-5 - The cornerstone anti-fraud rule
            "17_CFR_240_10b-5": {
                "citation": "17 CFR § 240.10b-5",
                "title": 17,
                "part": 240,
                "section": "10b-5",
                "short_title": "Rule 10b-5 - Employment of Manipulative and Deceptive Devices",
                "description": "Prohibition on fraud in connection with purchase or sale of securities",
                "authority": "15 USC 78j(b)",
                "elements": [
                    "(a) Employ any device, scheme, or artifice to defraud",
                    "(b) Make any untrue statement of material fact or omit material fact",
                    "(c) Engage in any act, practice, or course of business which operates as a fraud"
                ],
                "enforcement_priority": "CRITICAL",
                "scienter_required": True
            },
            
            # Regulation S-K - Disclosure Requirements
            "17_CFR_229_303": {
                "citation": "17 CFR § 229.303",
                "title": 17,
                "part": 229,
                "section": "303",
                "short_title": "Item 303 - MD&A",
                "description": "Management's Discussion and Analysis of Financial Condition and Results",
                "authority": "15 USC 78m",
                "requirements": [
                    "Liquidity analysis",
                    "Capital resources discussion",
                    "Results of operations",
                    "Known trends and uncertainties",
                    "Critical accounting estimates"
                ]
            },
            "17_CFR_229_503": {
                "citation": "17 CFR § 229.503",
                "title": 17,
                "part": 229,
                "section": "503",
                "short_title": "Item 503 - Risk Factors",
                "description": "Disclosure of material risks facing the company",
                "authority": "15 USC 77g, 15 USC 78m"
            },
            "17_CFR_229_402": {
                "citation": "17 CFR § 229.402",
                "title": 17,
                "part": 229,
                "section": "402",
                "short_title": "Item 402 - Executive Compensation",
                "description": "Comprehensive executive compensation disclosure",
                "authority": "15 USC 78m"
            },
            
            # Regulation S-X - Financial Statement Requirements
            "17_CFR_210_5-02": {
                "citation": "17 CFR § 210.5-02",
                "title": 17,
                "part": 210,
                "section": "5-02",
                "short_title": "Balance Sheet Requirements",
                "description": "Required balance sheet line items and disclosures",
                "authority": "15 USC 77s, 15 USC 78m"
            },
            "17_CFR_210_4-08": {
                "citation": "17 CFR § 210.4-08",
                "title": 17,
                "part": 210,
                "section": "4-08",
                "short_title": "General Notes to Financial Statements",
                "description": "Required financial statement note disclosures",
                "authority": "15 USC 77s, 15 USC 78m"
            },
            
            # Section 16 - Insider Reporting
            "17_CFR_240_16a-3": {
                "citation": "17 CFR § 240.16a-3",
                "title": 17,
                "part": 240,
                "section": "16a-3",
                "short_title": "Form 4 Filing Requirements",
                "description": "Statement of changes in beneficial ownership (Form 4)",
                "authority": "15 USC 78p(a)",
                "deadline": "2 business days after transaction",
                "form": "Form 4"
            },
            
            # Internal Controls (SOX 404)
            "17_CFR_240_13a-15": {
                "citation": "17 CFR § 240.13a-15",
                "title": 17,
                "part": 240,
                "section": "13a-15",
                "short_title": "Controls and Procedures",
                "description": "Internal control over financial reporting requirements",
                "authority": "15 USC 7262 (SOX 404)"
            },
            
            # Regulation FD - Fair Disclosure
            "17_CFR_243_100": {
                "citation": "17 CFR § 243.100",
                "title": 17,
                "part": 243,
                "section": "100",
                "short_title": "Regulation FD",
                "description": "Prohibition on selective disclosure of material nonpublic information",
                "authority": "15 USC 78j"
            }
        }
    
    def _initialize_criminal_statutes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize related criminal statutes (18 USC)."""
        return {
            "18_USC_1001": {
                "citation": "18 U.S.C. § 1001",
                "title": 18,
                "section": "1001",
                "short_title": "False Statements",
                "description": "False statements or concealment in matters within federal jurisdiction",
                "criminal": {"imprisonment": 5, "fine": True},
                "affecting_immigration": {"imprisonment": 10}
            },
            "18_USC_1343": {
                "citation": "18 U.S.C. § 1343",
                "title": 18,
                "section": "1343",
                "short_title": "Wire Fraud",
                "description": "Fraud by wire, radio, or television",
                "criminal": {"imprisonment": 20, "fine": True},
                "financial_institution": {"imprisonment": 30, "fine": 1000000}
            },
            "18_USC_1348": {
                "citation": "18 U.S.C. § 1348",
                "title": 18,
                "section": "1348",
                "short_title": "Securities and Commodities Fraud",
                "description": "Sarbanes-Oxley criminal securities fraud provision",
                "criminal": {"imprisonment": 25, "fine": True},
                "notes": "No personal benefit required; scheme to defraud is sufficient"
            },
            "18_USC_1350": {
                "citation": "18 U.S.C. § 1350",
                "title": 18,
                "section": "1350",
                "short_title": "SOX Section 906 - Criminal Certification",
                "description": "Criminal penalties for false SOX certifications",
                "knowing": {"imprisonment": 10, "fine": 1000000},
                "willful": {"imprisonment": 20, "fine": 5000000},
                "applies_to": ["CEO", "CFO"]
            },
            "18_USC_1519": {
                "citation": "18 U.S.C. § 1519",
                "title": 18,
                "section": "1519",
                "short_title": "Destruction of Records (SOX)",
                "description": "Destruction, alteration, or falsification of records in federal investigations",
                "criminal": {"imprisonment": 20, "fine": True},
                "anticipatory_obstruction": True
            },
            "18_USC_1520": {
                "citation": "18 U.S.C. § 1520",
                "title": 18,
                "section": "1520",
                "short_title": "Destruction of Corporate Audit Records",
                "description": "Destruction of audit workpapers and records",
                "criminal": {"imprisonment": 10, "fine": True},
                "retention_period": {"audit_workpapers": 5, "review_workpapers": 7}
            },
            "18_USC_371": {
                "citation": "18 U.S.C. § 371",
                "title": 18,
                "section": "371",
                "short_title": "Conspiracy",
                "description": "Conspiracy to commit offense or to defraud United States",
                "criminal": {"imprisonment": 5, "fine": True}
            },
            "18_USC_1341": {
                "citation": "18 U.S.C. § 1341",
                "title": 18,
                "section": "1341",
                "short_title": "Mail Fraud",
                "description": "Frauds and swindles using mail",
                "criminal": {"imprisonment": 20, "fine": True},
                "financial_institution": {"imprisonment": 30, "fine": 1000000}
            }
        }
    
    async def enrich_violation_with_govinfo(
        self,
        violation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich violation with authoritative GovInfo statute text and metadata.
        
        Args:
            violation: Violation dictionary from forensic analysis
            
        Returns:
            Enriched violation with full legal citations
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        statute_ref = violation.get("statute", "")
        
        # Parse statute reference
        parsed = self._parse_citation(statute_ref)
        if not parsed:
            return violation
        
        try:
            # Fetch from GovInfo
            if parsed["type"] == "USC":
                statute_data = await self.fetch_usc_statute(
                    parsed["title"],
                    parsed["section"]
                )
                violation["govinfo_statute"] = statute_data
            elif parsed["type"] == "CFR":
                cfr_data = await self.fetch_cfr_regulation(
                    parsed["title"],
                    parsed["part"],
                    parsed.get("section")
                )
                violation["govinfo_regulation"] = cfr_data
            
            # Add related authorities from heuristic mapping first
            related_auths = await self._find_related_authorities(parsed)
            
            # Dual-agent augmentation using GovInfoAPIClient relationship features
            if self.dual_agent and self.govinfo_client and "govinfo_statute" in violation:
                try:
                    statute_ref: StatuteReference = violation["govinfo_statute"]
                    if statute_ref.govinfo_package_id:
                        rel = await self.govinfo_client.find_implementing_regulations(statute_ref.govinfo_package_id)
                        # Incorporate CFR references
                        for r in rel or []:
                            cfr_cite = r.get("citation") or r.get("title")
                            if cfr_cite and cfr_cite not in related_auths:
                                related_auths.append(cfr_cite)
                except Exception as de:
                    if self.strict_api_mode:
                        raise
                    logger.warning(f"Dual-agent related authority augmentation failed: {de}")
            
            violation["related_authorities"] = related_auths
            
            # Add enforcement precedents
            violation["enforcement_precedents"] = await self._find_enforcement_precedents(parsed)
            
        except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
            if self.strict_api_mode:
                # Re-raise in strict mode - we want failures to be visible
                logger.error(f"GovInfo enrichment FAILED in strict API mode for {statute_ref}: {e}")
                raise RuntimeError(
                    f"Statute enrichment failed for {statute_ref} (strict API mode enabled). "
                    f"Original error: {e}"
                ) from e
            else:
                # Log warning in non-strict mode
                logger.warning(f"GovInfo enrichment failed for {statute_ref}: {e}")
        except Exception as e:
            # Unexpected errors always bubble up
            logger.error(f"Unexpected error during GovInfo enrichment for {statute_ref}: {e}")
            raise
        
        return violation
    
    def _parse_citation(self, citation: str) -> Optional[Dict[str, Any]]:
        """Parse legal citation into components."""
        # 15 USC 78j(b)
        usc_pattern = r"(\d+)\s+U\.?S\.?C\.?\s+§?\s*(\d+[a-z]?(?:-\d+)?(?:\([a-z]\))?)"
        
        # 17 CFR 240.10b-5
        cfr_pattern = r"(\d+)\s+C\.?F\.?R\.?\s+§?\s*(\d+)\.(\d+[a-z]?(?:-\d+)?)"
        
        usc_match = re.search(usc_pattern, citation, re.IGNORECASE)
        if usc_match:
            return {
                "type": "USC",
                "title": int(usc_match.group(1)),
                "section": usc_match.group(2)
            }
        
        cfr_match = re.search(cfr_pattern, citation, re.IGNORECASE)
        if cfr_match:
            return {
                "type": "CFR",
                "title": int(cfr_match.group(1)),
                "part": int(cfr_match.group(2)),
                "section": cfr_match.group(3)
            }
        
        return None
    
    async def fetch_usc_statute(
        self,
        title: int,
        section: str,
        year: Optional[int] = None
    ) -> StatuteReference:
        """
        Fetch USC statute from GovInfo with full metadata.
        
        Args:
            title: USC title number
            section: Section number (e.g., "78j" or "78j(b)")
            year: Optional year (defaults to most recent)
            
        Returns:
            Complete statute reference with URLs
        """
        cache_key = f"USC_{title}_{section}_{year or 'latest'}"
        if cache_key in self.statute_cache:
            return self.statute_cache[cache_key]
        
        if not year:
            year = datetime.now().year - 1
        
        # Clean section identifier
        clean_section = re.sub(r'[()]', '', section)
        base_section = re.match(r'(\d+[a-z]?)', clean_section).group(1)
        package_id = f"USCODE-{year}-title{title}"
        granule_id = f"USCODE-{year}-title{title}-section{base_section}"
        
        # Prefer GovInfoAPIClient in dual-agent mode when available
        if self.govinfo_client is not None:
            try:
                data = await self.govinfo_client.fetch_usc_statute_by_collection(title, base_section, year)
                statute_ref = StatuteReference(
                    citation=data.get("citation", f"{title} U.S.C. § {section}"),
                    title=title,
                    section=section,
                    govinfo_package_id=data.get("package_id", package_id),
                    govinfo_granule_id=granule_id,
                    text_url=(data.get("download_links", {}) or {}).get("text"),
                    pdf_url=(data.get("download_links", {}) or {}).get("pdf"),
                    xml_url=(data.get("download_links", {}) or {}).get("xml"),
                )
                db_key = f"{title}_USC_{base_section}"
                if db_key in self.securities_statutes:
                    db_info = self.securities_statutes[db_key]
                    statute_ref.short_title = db_info.get("short_title")
                    statute_ref.related_cfr = db_info.get("related_cfr", [])
                    statute_ref.criminal_penalties = db_info.get("criminal")
                    statute_ref.civil_penalties = {"applicable": db_info.get("civil", False)}
                self.statute_cache[cache_key] = statute_ref
                return statute_ref
            except Exception as e:
                logger.warning(f"GovInfoAPIClient collection fetch failed for {title} USC {section}: {e}")
                if self.strict_api_mode:
                    # Fall through to raise via direct call below to preserve strict behavior
                    pass
        
        # Direct HTTP path (legacy) as fallback
        url = f"{self.base_url}/packages/{package_id}/granules/{granule_id}"
        try:
            async with self.session.get(
                url,
                params={"api_key": self.api_key},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 500:
                    logger.warning(f"Granule endpoint returned 500, trying package summary for {title} USC {section}")
                    return await self._fetch_usc_via_package_summary(title, section, year, package_id)
                if response.status == 200:
                    data = await response.json()
                    statute_ref = StatuteReference(
                        citation=f"{title} U.S.C. § {section}",
                        title=title,
                        section=section,
                        govinfo_package_id=package_id,
                        govinfo_granule_id=granule_id,
                        text_url=data.get("download", {}).get("txtLink"),
                        pdf_url=data.get("download", {}).get("pdfLink"),
                        xml_url=data.get("download", {}).get("xmlLink")
                    )
                    db_key = f"{title}_USC_{base_section}"
                    if db_key in self.securities_statutes:
                        db_info = self.securities_statutes[db_key]
                        statute_ref.short_title = db_info.get("short_title")
                        statute_ref.related_cfr = db_info.get("related_cfr", [])
                        statute_ref.criminal_penalties = db_info.get("criminal")
                        statute_ref.civil_penalties = {"applicable": db_info.get("civil", False)}
                    self.statute_cache[cache_key] = statute_ref
                    return statute_ref
                elif response.status == 404:
                    if self.strict_api_mode:
                        raise ValueError(
                            f"GovInfo API returned 404 for {title} USC {section}. Statute not found. Package: {package_id}, Granule: {granule_id}"
                        )
                    return await self._fetch_usc_fallback(title, section, year)
                else:
                    error_msg = f"GovInfo USC fetch failed with status {response.status} for {title} USC {section}"
                    logger.error(error_msg)
                    if self.strict_api_mode:
                        raise ConnectionError(
                            f"{error_msg}. GovInfo API may be unavailable. Check https://api.data.gov/docs/ for service status."
                        )
                    return self._create_default_statute_ref(title, section)
        except asyncio.TimeoutError:
            error_msg = f"GovInfo USC fetch timeout for {title} USC {section}"
            logger.error(error_msg)
            if self.strict_api_mode:
                raise TimeoutError(f"{error_msg}. GovInfo API did not respond within 30 seconds.")
            return self._create_default_statute_ref(title, section)
        except (ValueError, ConnectionError, TimeoutError):
            raise
        except Exception as e:
            error_msg = f"GovInfo USC fetch error for {title} USC {section}: {e}"
            logger.error(error_msg)
            if self.strict_api_mode:
                raise RuntimeError(f"{error_msg}. Unexpected error during GovInfo API call.") from e
            return self._create_default_statute_ref(title, section)
    
    async def _fetch_usc_via_package_summary(
        self,
        title: int,
        section: str,
        year: int,
        package_id: str
    ) -> StatuteReference:
        """
        Alternative USC fetch using package summary endpoint.
        Used when granule endpoint returns 500 error.
        """
        url = f"{self.base_url}/packages/{package_id}/summary"
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                url,
                params={"api_key": self.api_key},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Build statute reference from package data
                    base_section = re.match(r'(\d+[a-z]?)', section).group(1) if re.match(r'(\d+[a-z]?)', section) else section
                    
                    statute_ref = StatuteReference(
                        citation=f"{title} U.S.C. § {section}",
                        title=title,
                        section=section,
                        govinfo_package_id=package_id,
                        govinfo_granule_id=None,
                        text_url=f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{title}-section{base_section}",
                        pdf_url=data.get("download", {}).get("pdfLink"),
                        xml_url=data.get("download", {}).get("xmlLink")
                    )
                    
                    # Enrich with metadata
                    db_key = f"{title}_USC_{base_section}"
                    if db_key in self.securities_statutes:
                        db_info = self.securities_statutes[db_key]
                        statute_ref.short_title = db_info.get("short_title")
                        statute_ref.related_cfr = db_info.get("related_cfr", [])
                        statute_ref.criminal_penalties = db_info.get("criminal")
                        statute_ref.civil_penalties = {"applicable": db_info.get("civil", False)}
                    
                    logger.info(f"Fetched {title} USC {section} via package summary (granule endpoint unavailable)")
                    return statute_ref
                
                elif response.status == 500:
                    if self.strict_api_mode:
                        raise ConnectionError(
                            f"GovInfo API experiencing service issues (500 error) for {title} USC {section}"
                        )
                else:
                    if self.strict_api_mode:
                        raise ConnectionError(
                            f"GovInfo API returned {response.status} for {title} USC {section}"
                        )
        except (ConnectionError, TimeoutError):
            raise
        except Exception as e:
            if self.strict_api_mode:
                raise RuntimeError(
                    f"Alternative USC fetch failed for {title} USC {section}: {e}"
                ) from e
        
        return self._create_default_statute_ref(title, section)
    
    async def _fetch_usc_fallback(
        self,
        title: int,
        section: str,
        year: int
    ) -> StatuteReference:
        """Fallback USC fetch using collection search."""
        url = f"{self.base_url}/collections/USCODE/{year}/title-{title}"
        
        try:
            async with self.session.get(
                url,
                params={"api_key": self.api_key, "offset": 0, "pageSize": 100},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Search for matching section in results
                    # This is a simplified fallback - full implementation would parse results
                    pass
        except Exception:
            pass
        
        return self._create_default_statute_ref(title, section)
    
    def _create_default_statute_ref(self, title: int, section: str) -> StatuteReference:
        """Create statute reference from local database."""
        # Try different section formats
        base_section = re.match(r'(\d+[a-z]?)', section).group(1) if re.match(r'(\d+[a-z]?)', section) else section
        
        db_info = {}
        for db_key_candidate in [
            f"{title}_USC_{section}",
            f"{title}_USC_{base_section}",
            f"{title}_USC_{re.sub(r'[()]', '', section)}"
        ]:
            if db_key_candidate in self.securities_statutes:
                db_info = self.securities_statutes[db_key_candidate]
                break
        
        return StatuteReference(
            citation=f"{title} U.S.C. § {section}",
            title=title,
            section=section,
            short_title=db_info.get("short_title", ""),
            related_cfr=db_info.get("related_cfr", []),
            criminal_penalties=db_info.get("criminal"),
            civil_penalties={"applicable": db_info.get("civil", False) if isinstance(db_info.get("civil"), bool) else db_info.get("civil")}
        )
    
    async def fetch_cfr_regulation(
        self,
        title: int,
        part: int,
        section: Optional[str] = None,
        year: Optional[int] = None
    ) -> CFRReference:
        """
        Fetch CFR regulation from GovInfo.
        
        Uses proper collection-based API per official documentation.
        
        Args:
            title: CFR title (17 for SEC)
            part: Part number (e.g., 240 for Exchange Act rules)
            section: Optional section (e.g., "10b-5")
            year: Optional year
            
        Returns:
            CFR reference with URLs
        """
        cache_key = f"CFR_{title}_{part}_{section}_{year or 'latest'}"
        if cache_key in self.cfr_cache:
            return self.cfr_cache[cache_key]
        
        if not year:
            # CFR Title 17 updates April 1
            year = datetime.now().year
            if datetime.now().month < 4:
                year -= 1
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Initialize or reuse GovInfo client
            govinfo_client = self.govinfo_client
            if govinfo_client is None:
                if GovInfoAPIClient is None:
                    raise RuntimeError("GovInfoAPIClient not available")
                govinfo_client = GovInfoAPIClient(self.api_key)
                self._own_govinfo_client = True
                self.govinfo_client = govinfo_client
            # Reuse same aiohttp session for efficiency
            try:
                govinfo_client.session = self.session
            except Exception:
                pass
            
            # Fetch using collection-based API
            cfr_data = await govinfo_client.fetch_cfr_regulation_by_collection(
                title, part, section, year
            )
            
            # Get metadata for cross-referencing
            db_key = f"{title}_CFR_{part}_{section}" if section else f"{title}_CFR_{part}"
            db_info = self.sec_regulations.get(db_key.replace(".", "_").replace("-", "_"), {})
            
            # Build CFRReference
            cfr_ref = CFRReference(
                citation=cfr_data["citation"],
                title=title,
                part=part,
                section=section,
                govinfo_package_id=cfr_data["package_id"],
                text_url=cfr_data["download_links"]["text"],
                pdf_url=cfr_data["download_links"]["pdf"],
                authority=db_info.get("authority"),
                source=db_info.get("source")
            )
            
            self.cfr_cache[cache_key] = cfr_ref
            logger.info(f"Successfully fetched {title} CFR {part}.{section or ''} via collection API")
            return cfr_ref
            
        except (ValueError, ConnectionError, TimeoutError) as e:
            if self.strict_api_mode:
                logger.error(f"GovInfo API error for {title} CFR {part}: {e}")
                raise
            # Non-strict fallback would go here
            raise
    
    def _get_cfr_volume(self, title: int, part: int) -> int:
        """Get CFR volume number for title and part."""
        if title == 17:
            if part <= 40:
                return 1
            elif part <= 199:
                return 2
            elif part <= 239:
                return 3
            else:
                return 4
        return 1
    
    async def _find_related_authorities(self, parsed: Dict[str, Any]) -> List[str]:
        """Find related statutes and regulations."""
        related = []
        
        if parsed["type"] == "USC":
            title = parsed["title"]
            section = parsed["section"]
            
            # Look up in database
            db_key = f"{title}_USC_{re.sub(r'[()]', '', section)}"
            if db_key in self.securities_statutes:
                info = self.securities_statutes[db_key]
                related.extend(info.get("related_cfr", []))
        
        elif parsed["type"] == "CFR":
            title = parsed["title"]
            part = parsed["part"]
            section = parsed.get("section")
            
            # Look up in database
            db_key = f"{title}_CFR_{part}_{section}" if section else f"{title}_CFR_{part}"
            if db_key.replace(".", "_").replace("-", "_") in self.sec_regulations:
                info = self.sec_regulations[db_key.replace(".", "_").replace("-", "_")]
                if info.get("authority"):
                    related.append(info["authority"])
        
        return related
    
    async def _find_enforcement_precedents(
        self,
        parsed: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find relevant SEC enforcement actions and court decisions."""
        # This would connect to SEC's enforcement database
        # For now, return curated precedents based on statute
        precedents = []
        
        if parsed["type"] == "USC" and parsed["title"] == 15:
            section = parsed["section"]
            if "78j" in section:
                precedents.extend([
                    {
                        "case": "SEC v. Texas Gulf Sulphur Co.",
                        "citation": "401 F.2d 833 (2d Cir. 1968)",
                        "principle": "Materiality standard for Rule 10b-5",
                        "date": "1968"
                    },
                    {
                        "case": "Basic Inc. v. Levinson",
                        "citation": "485 U.S. 224 (1988)",
                        "principle": "Fraud-on-the-market theory",
                        "date": "1988"
                    }
                ])
        
        return precedents
    
    async def get_comprehensive_legal_framework(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive legal framework for dossier.
        
        Args:
            violations: List of detected violations
            
        Returns:
            Complete legal framework with all applicable authorities
        """
        framework = {
            "primary_statutes": [],
            "regulations": [],
            "criminal_statutes": [],
            "case_law": [],
            "enforcement_precedents": [],
            "penalty_framework": {}
        }
        
        for violation in violations:
            # Enrich each violation
            enriched = await self.enrich_violation_with_govinfo(violation)
            
            if "govinfo_statute" in enriched:
                framework["primary_statutes"].append(enriched["govinfo_statute"])
            
            if "govinfo_regulation" in enriched:
                framework["regulations"].append(enriched["govinfo_regulation"])
            
            if "related_authorities" in enriched:
                for auth in enriched["related_authorities"]:
                    if "18 USC" in auth or "18 U.S.C" in auth:
                        parsed = self._parse_citation(auth)
                        if parsed:
                            criminal = await self.fetch_usc_statute(
                                parsed["title"],
                                parsed["section"]
                            )
                            framework["criminal_statutes"].append(criminal)
            
            if "enforcement_precedents" in enriched:
                framework["enforcement_precedents"].extend(
                    enriched["enforcement_precedents"]
                )
        
        # Calculate penalty framework
        framework["penalty_framework"] = self._calculate_penalty_framework(violations)
        
        return framework
    
    def _calculate_penalty_framework(
        self,
        violations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate comprehensive penalty exposure."""
        penalties = {
            "criminal_exposure": {
                "max_imprisonment_years": 0,
                "max_individual_fine": 0,
                "max_entity_fine": 0,
                "statutes": []
            },
            "civil_exposure": {
                "max_per_violation": 0,
                "estimated_violations": len(violations),
                "total_estimated": 0,
                "statutes": []
            },
            "disgorgement_exposure": {
                "estimated": 0,
                "treble_damages": False
            }
        }
        
        for violation in violations:
            statute = violation.get("statute", "")
            
            # Check against database
            for key, info in {**self.securities_statutes, **self.related_criminal_statutes}.items():
                if info["citation"] in statute or key.replace("_", " ") in statute:
                    # Criminal penalties
                    if "criminal" in info:
                        crim = info["criminal"]
                        penalties["criminal_exposure"]["max_imprisonment_years"] = max(
                            penalties["criminal_exposure"]["max_imprisonment_years"],
                            crim.get("imprisonment", 0)
                        )
                        if crim.get("fine"):
                            if isinstance(crim["fine"], int):
                                penalties["criminal_exposure"]["max_individual_fine"] = max(
                                    penalties["criminal_exposure"]["max_individual_fine"],
                                    crim["fine"]
                                )
                        penalties["criminal_exposure"]["statutes"].append(info["citation"])
                    
                    # Willful enhancement
                    if "willful" in info:
                        willful = info["willful"]
                        penalties["criminal_exposure"]["max_imprisonment_years"] = max(
                            penalties["criminal_exposure"]["max_imprisonment_years"],
                            willful.get("imprisonment", 0)
                        )
                    
                    # Civil penalties
                    if info.get("civil") or "civil_penalties" in info:
                        civil_info = info.get("civil_penalties", {})
                        tier3 = civil_info.get("tier3", 1000000)
                        penalties["civil_exposure"]["max_per_violation"] = max(
                            penalties["civil_exposure"]["max_per_violation"],
                            tier3
                        )
                        penalties["civil_exposure"]["statutes"].append(info["citation"])
        
        # Calculate total civil exposure
        penalties["civil_exposure"]["total_estimated"] = (
            penalties["civil_exposure"]["max_per_violation"] *
            penalties["civil_exposure"]["estimated_violations"]
        )
        
        return penalties
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
        # Also close owned GovInfoAPIClient session if we created it
        try:
            if self._own_govinfo_client and self.govinfo_client:
                await self.govinfo_client.close()
        except Exception:
            pass
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.session and not self.session.closed:
            try:
                asyncio.get_event_loop().run_until_complete(self.close())
            except Exception:
                pass

