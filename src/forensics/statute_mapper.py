"""
Complete statute mapping across six USC titles for forensic compliance.
Implements direct GovInfo access for legal document retrieval.
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
import json
from urllib.parse import quote, urlencode

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel, IntegrityError
)

class StatuteTitle(Enum):
    """USC titles relevant to securities fraud."""
    USC_15 = (15, "Commerce and Trade")  # Securities laws
    USC_17_CFR = (17, "SEC Regulations")  # CFR regulations
    USC_18 = (18, "Crimes and Criminal Procedure")  # Criminal fraud
    USC_26 = (26, "Internal Revenue Code")  # Tax disclosures
    USC_31 = (31, "Money and Finance")  # BSA/AML
    USC_12 = (12, "Banks and Banking")  # Banking regulations

@dataclass
class StatuteViolation:
    """Potential statute violation detected."""
    title: int
    section: str
    description: str
    severity: str  # CRIMINAL, CIVIL, REGULATORY
    max_penalty: Optional[str]
    imprisonment_years: Optional[int]
    fine_amount: Optional[int]
    pattern_matched: Dict[str, Any]
    evidence_refs: List[str]
    detection_confidence: float

class StatuteMapper:
    """
    Maps forensic findings to specific USC and CFR violations.
    Provides direct access to legal documents via GovInfo.
    """
    
    def __init__(self, api_key: str, strict_mode: bool = True):
        self.api_key = api_key
        self.base_url = "https://api.govinfo.gov"
        self.session = None
        self.hash_chain = ForensicHashChain("statute_mapping")
        self.statute_cache: Dict[str, Any] = {}
        self.strict_mode = strict_mode
        
        # Initialize violation patterns
        self.violation_patterns = self._initialize_patterns()
        
    def _initialize_patterns(self) -> Dict[str, Any]:
        """Initialize statute violation detection patterns."""
        return {
            "15_USC_77g": {  # Securities Act registration
                "title": 15,
                "section": "77g",
                "patterns": [
                    "missing_financial_statements",
                    "incomplete_risk_factors",
                    "undisclosed_material_contracts"
                ],
                "severity": "CIVIL",
                "forms": ["S-1", "S-3", "S-4", "S-8"]
            },
            "15_USC_78j_b": {  # Rule 10b-5 anti-fraud
                "title": 15,
                "section": "78j(b)",
                "patterns": [
                    "material_misstatement",
                    "material_omission",
                    "insider_trading",
                    "price_manipulation"
                ],
                "severity": "CIVIL_CRIMINAL",
                "rule": "10b-5"
            },
            "18_USC_1001": {  # False statements
                "title": 18,
                "section": "1001",
                "patterns": [
                    "false_statement_to_sec",
                    "contradictory_statements",
                    "concealment_during_investigation"
                ],
                "severity": "CRIMINAL",
                "imprisonment": 5
            },
            "18_USC_1343": {  # Wire fraud
                "title": 18,
                "section": "1343",
                "patterns": [
                    "electronic_filing_fraud",
                    "false_investor_communication",
                    "pump_and_dump_scheme"
                ],
                "severity": "CRIMINAL",
                "imprisonment": 20,
                "financial_institution_impact": 30
            },
            "18_USC_1348": {  # Securities fraud
                "title": 18,
                "section": "1348",
                "patterns": [
                    "accounting_fraud",
                    "false_revenue_recognition",
                    "concealed_liabilities",
                    "insider_trading_scheme"
                ],
                "severity": "CRIMINAL",
                "imprisonment": 25,
                "no_personal_benefit_required": True
            },
            "18_USC_1350": {  # SOX certification
                "title": 18,
                "section": "1350",
                "patterns": [
                    "false_ceo_certification",
                    "false_cfo_certification",
                    "certified_despite_known_issues"
                ],
                "severity": "CRIMINAL",
                "knowing": {"imprisonment": 10, "fine": 1000000},
                "willful": {"imprisonment": 20, "fine": 5000000}
            },
            "15_USC_78p_a": {  # Section 16(a) insider reporting (Form 4)
                "title": 15,
                "section": "78p(a)",
                "patterns": [
                    "late_form4",  # >2 business days late
                    "zero_dollar_transaction"  # Potential gifts/RSU vesting without price
                ],
                "severity": "CIVIL",
                "forms": ["4"]
            },
            "18_USC_1519": {  # Document destruction
                "title": 18,
                "section": "1519",
                "patterns": [
                    "mass_document_shredding",
                    "email_deletion_pattern",
                    "audit_workpaper_destruction",
                    "anticipatory_obstruction"
                ],
                "severity": "CRIMINAL",
                "imprisonment": 20
            },
            "17_CFR_229_303": {  # MD&A requirements
                "title": 17,
                "section": "229.303",
                "patterns": [
                    "boilerplate_mda",
                    "missing_trend_discussion",
                    "inadequate_liquidity_analysis"
                ],
                "severity": "REGULATORY",
                "item": "303"
            },
            "17_CFR_240_10b5": {  # Rule 10b-5
                "title": 17,
                "section": "240.10b-5",
                "patterns": [
                    "deceptive_device",
                    "untrue_material_fact",
                    "material_omission"
                ],
                "severity": "CIVIL_CRIMINAL"
            },
            "17_CFR_240_12b25": {  # Late filing notification
                "title": 17,
                "section": "240.12b-25",
                "patterns": [
                    "late_without_nt",
                    "false_nt_reason",
                    "undisclosed_restatement_in_nt"
                ],
                "severity": "REGULATORY",
                "penalties": [25000, 225000]  # Range
            },
            "26_USC_tax_disclosure": {
                "title": 26,
                "patterns": [
                    "unusual_tax_rate_change",
                    "insufficient_valuation_allowance",
                    "undisclosed_tax_audit"
                ],
                "severity": "CIVIL"
            },
            "31_USC_5318": {  # BSA suspicious activity
                "title": 31,
                "section": "5318",
                "patterns": [
                    "undisclosed_aml_weakness",
                    "hidden_consent_order",
                    "sar_filing_pattern"
                ],
                "severity": "CRIMINAL",
                "pattern_violation": {"amount": 100000, "period_months": 12, "fine": 500000}
            },
            "12_USC_161": {  # Bank reporting
                "title": 12,
                "section": "161",
                "patterns": [
                    "call_report_discrepancy",
                    "inadequate_loan_loss_reserve",
                    "hidden_regulatory_action"
                ],
                "severity": "REGULATORY"
            }
        }
    
    async def map_violations(
        self,
        forensic_findings: Dict[str, Any]
    ) -> List[StatuteViolation]:
        """
        Map forensic findings to specific statute violations.
        
        Args:
            forensic_findings: Analysis results from forensic analyzer
            
        Returns:
            List of potential statute violations
        """
        violations = []
        
        # Initialize session if needed
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Check each pattern
        for pattern_key, pattern_def in self.violation_patterns.items():
            matches = await self._check_pattern(forensic_findings, pattern_def)
            
            if matches:
                for match in matches:
                    # Enrich match with statute text/details (GovInfo) for stronger evidence
                    try:
                        statute_details = await self.fetch_statute_text(pattern_def["title"], pattern_def.get("section", ""))
                        match["statute_details"] = statute_details
                    except Exception:
                        # Best-effort enrichment; continue if GovInfo is unavailable
                        pass

                    # Ensure an estimated damages value is present when reasonable
                    evidence = match.get("evidence") or {}
                    if isinstance(evidence, dict) and "estimated_damages" not in evidence:
                        default_damage = self._default_estimated_damages(pattern_def, match)
                        if default_damage is not None:
                            evidence["estimated_damages"] = default_damage
                            match["evidence"] = evidence

                    violation = StatuteViolation(
                        title=pattern_def["title"],
                        section=pattern_def.get("section", ""),
                        description=self._generate_violation_description(pattern_def, match),
                        severity=pattern_def["severity"],
                        max_penalty=self._determine_penalty(pattern_def),
                        imprisonment_years=pattern_def.get("imprisonment"),
                        fine_amount=self._determine_fine(pattern_def),
                        pattern_matched=match,
                        evidence_refs=match.get("evidence_refs", []),
                        detection_confidence=match.get("confidence", 0.0)
                    )
                    violations.append(violation)
        
        # Sort by severity and confidence
        violations.sort(
            key=lambda v: (
                v.severity == "CRIMINAL",
                v.detection_confidence
            ),
            reverse=True
        )
        
        # Add to forensic chain
        await self.hash_chain.add_evidence(
            {
                "type": "statute_mapping",
                "violations_detected": len(violations),
                "criminal_violations": sum(1 for v in violations if v.severity == "CRIMINAL"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            IntegrityLevel.CRITICAL
        )
        
        return violations
    
    async def _check_pattern(
        self,
        findings: Dict[str, Any],
        pattern_def: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check if findings match violation pattern."""
        matches = []
        
        # Extract relevant findings
        red_flags = findings.get("red_flags", [])
        fraud_indicators = findings.get("fraud_indicators", {})
        
        for pattern in pattern_def.get("patterns", []):
            # Check red flags
            for red_flag in red_flags:
                if self._pattern_matches(pattern, red_flag):
                    candidate = {
                        "pattern": pattern,
                        "evidence": red_flag,
                        "confidence": self._calculate_confidence(red_flag),
                        "evidence_refs": [red_flag.get("id", "")]
                    }
                    # Strict evidence gating (production default)
                    if not self.strict_mode or self._passes_strict_evidence(pattern_def, candidate):
                        matches.append(candidate)
            
            # Check specific patterns
            if pattern == "material_misstatement" and fraud_indicators.get("overall_risk", 0) > 0.7:
                matches.append({
                    "pattern": pattern,
                    "evidence": {"fraud_risk": fraud_indicators["overall_risk"]},
                    "confidence": fraud_indicators["overall_risk"],
                    "evidence_refs": findings.get("evidence_ids", [])
                })
            
            if pattern == "false_revenue_recognition":
                for anomaly in findings.get("revenue_anomalies", []):
                    if anomaly.get("type") == "quarter_end_spike":
                        matches.append({
                            "pattern": pattern,
                            "evidence": anomaly,
                            "confidence": 0.8,
                            "evidence_refs": [anomaly.get("id", "")]
                        })
        
        return matches

    def _passes_strict_evidence(self, pattern_def: Dict[str, Any], match: Dict[str, Any]) -> bool:
        """Enforce strict evidence gating to reduce over-flagging.

        Rules (initial set):
        - For 10b-5 patterns (Title 17, sections like 240.10b-5), require either:
          a) exact_quote AND document_url present in evidence; OR
          b) confidence >= 0.70 AND document_url present.
        - For SOX 302 (18 USC 1350), allow if document_url present (exhibits section),
          quote optional (exhibit numbers may not appear verbatim).
        - Otherwise, require confidence >= 0.5 OR exact_quote present.
        """
        title = pattern_def.get("title")
        section = str(pattern_def.get("section", ""))
        evidence = match.get("evidence") or {}
        exact_quote = evidence.get("exact_quote")
        document_url = evidence.get("document_url")
        confidence = float(match.get("confidence", 0.0))

        # 10b-5 (CFR) patterns
        if title == 17 and ("240.10b-5" in section or section.startswith("240.")):
            return ((exact_quote and document_url) or (confidence >= 0.70 and document_url is not None))

        # SOX 302 (18 USC 1350)
        if title == 18 and "1350" in section:
            return document_url is not None

        # Default
        return (confidence >= 0.50) or bool(exact_quote)

    async def close(self):
        """Close internal HTTP session."""
        if self.session:
            try:
                await self.session.close()
            except Exception:
                pass
            self.session = None

    def _default_estimated_damages(self, pattern_def: Dict[str, Any], match: Dict[str, Any]) -> Optional[int]:
        """Provide a conservative default damages estimate when evidence lacks one.

        We avoid overstatement: values are calibrated as modest baselines and should
        be superseded by actual evidence-specific estimates when available.
        """
        title = pattern_def.get("title")
        section = (pattern_def.get("section") or "").lower()
        pattern = (match.get("pattern") or "").lower()

        # Section 10(b) / Rule 10b-5 related
        if title == 15 and "78j" in section:
            if pattern == "material_misstatement":
                return 10_000_000
            if pattern == "material_omission":
                return 2_000_000
            if pattern == "insider_trading":
                return 5_000_000
            if pattern == "price_manipulation":
                return 3_000_000

        # SOX 302 false certifications (18 USC 1350) – leverage statutory fine tiers
        if title == 18 and "1350" in section:
            # Prefer willful/knowing fines provided in pattern_def
            fine = self._determine_fine(pattern_def)
            if isinstance(fine, int):
                return fine
            return 1_000_000

        # Securities fraud (18 USC 1348) – conservative baseline
        if title == 18 and "1348" in section:
            return 5_000_000

        # Document destruction (18 USC 1519) – conservative baseline
        if title == 18 and "1519" in section:
            return 500_000

        # Default: None (no estimate)
        return None
    
    def _pattern_matches(self, pattern: str, red_flag: Dict) -> bool:
        """Check if red flag matches pattern."""
        pattern_mappings = {
            "material_misstatement": ["impossible_growth_ratio", "revenue_pull_forward", "material_misstatement"],
            "material_omission": ["missing_mda", "undisclosed_material_event"],
            "false_statement_to_sec": ["false_certification", "contradictory_filing"],
            # SOX 302 specific flags under 18 USC 1350
            "false_ceo_certification": ["false_ceo_certification"],
            "false_cfo_certification": ["false_cfo_certification"],
            "certified_despite_known_issues": ["certified_despite_known_issues"],
            "accounting_fraud": ["benford_violation", "expense_capitalization"],
            "document_destruction": ["missing_audit_trail", "access_denied"],
            "boilerplate_mda": ["incomplete_mda", "missing_uncertainty_language"],
            "late_without_nt": ["missing_nt_filing"],
            # Form 4 insider reporting
            "late_form4": ["late_form4"],
            "zero_dollar_transaction": ["zero_dollar_transaction"],
        }
        
        red_flag_type = red_flag.get("type", "")
        return red_flag_type in pattern_mappings.get(pattern, [])
    
    def _calculate_confidence(self, evidence: Dict) -> float:
        """Calculate confidence score for violation detection."""
        severity_scores = {
            "CRITICAL": 0.9,
            "HIGH": 0.7,
            "MEDIUM": 0.5,
            "LOW": 0.3
        }
        
        severity = evidence.get("severity", "LOW")
        base_score = severity_scores.get(severity, 0.3)
        
        # Adjust based on evidence strength
        if evidence.get("pattern") in ["worldcom", "marvell_technology", "enron"]:
            base_score = min(1.0, base_score + 0.2)
        
        return base_score
    
    def _generate_violation_description(
        self,
        pattern_def: Dict,
        match: Dict
    ) -> str:
        """Generate human-readable violation description."""
        descriptions = {
            "15_USC_78j_b": "Violation of Section 10(b) anti-fraud provisions",
            "18_USC_1001": "False statements to federal agency",
            "18_USC_1343": "Wire fraud through electronic filing system",
            "18_USC_1348": "Securities fraud affecting registered securities",
            "18_USC_1350": "False SOX certification by executive officer",
            "18_USC_1519": "Destruction of records to obstruct investigation",
            "17_CFR_229_303": "Deficient MD&A disclosure under Item 303",
            "17_CFR_240_10b5": "Violation of Rule 10b-5",
            "26_USC_tax_disclosure": "Inadequate tax-related disclosure",
            "31_USC_5318": "BSA/AML compliance failure",
            "12_USC_161": "Bank regulatory reporting violation"
        }
        
        base_desc = descriptions.get(
            f"{pattern_def['title']}_USC_{pattern_def.get('section', '')}".replace("(", "").replace(")", ""),
            "Statutory violation detected"
        )
        
        evidence = match.get("evidence", {})
        if evidence.get("type"):
            base_desc += f" - {evidence['type']}"
        
        return base_desc
    
    def _determine_penalty(self, pattern_def: Dict) -> str:
        """Determine maximum penalty for violation."""
        if pattern_def["severity"] == "CRIMINAL":
            years = pattern_def.get("imprisonment", 0)
            if "willful" in pattern_def:
                years = pattern_def["willful"]["imprisonment"]
            return f"Up to {years} years imprisonment"
        elif pattern_def["severity"] == "CIVIL":
            return "Civil penalties and disgorgement"
        else:
            return "Regulatory sanctions"
    
    def _determine_fine(self, pattern_def: Dict) -> Optional[int]:
        """Determine maximum fine amount."""
        if "fine" in pattern_def:
            return pattern_def["fine"]
        if "willful" in pattern_def:
            return pattern_def["willful"].get("fine")
        if "knowing" in pattern_def:
            return pattern_def["knowing"].get("fine")
        if "penalties" in pattern_def:
            return max(pattern_def["penalties"])
        return None
    
    async def fetch_statute_text(
        self,
        title: int,
        section: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch actual statute text from GovInfo.
        
        Args:
            title: USC title number
            section: Section identifier
            year: Optional year (defaults to most recent)
            
        Returns:
            Statute text and metadata
        """
        if not year:
            year = datetime.now().year - 1  # Use previous year for stability
        
        # Check cache
        cache_key = f"{title}_{section}_{year}"
        if cache_key in self.statute_cache:
            return self.statute_cache[cache_key]
        
        # Construct granule ID
        granule_id = self._construct_granule_id(title, section)
        
        # Fetch from GovInfo API
        url = f"{self.base_url}/packages/USCODE-{year}-title{title}/granules/{granule_id}/summary"
        
        try:
            async with self.session.get(
                url,
                params={"api_key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract download links
                    result = {
                        "title": title,
                        "section": section,
                        "year": year,
                        "text_url": data.get("download", {}).get("txtLink"),
                        "pdf_url": data.get("download", {}).get("pdfLink"),
                        "xml_url": data.get("download", {}).get("xmlLink"),
                        "last_modified": data.get("lastModified"),
                        "granule_id": granule_id
                    }
                    
                    # Cache result
                    self.statute_cache[cache_key] = result
                    
                    return result
                elif response.status == 503:
                    # Retry with backoff
                    await asyncio.sleep(30)
                    return await self.fetch_statute_text(title, section, year)
                else:
                    raise IntegrityError(f"Failed to fetch statute: {response.status}")
        except Exception as e:
            raise IntegrityError(f"Statute fetch failed: {e}")
    
    def _construct_granule_id(self, title: int, section: str) -> str:
        """Construct GovInfo granule ID for USC section."""
        # Remove parentheses and special characters
        clean_section = re.sub(r'[()]', '', section)
        
        # USC granule format
        return f"USCODE-{datetime.now().year-1}-title{title}-chap2B-sec{clean_section}"
    
    async def fetch_cfr_rule(
        self,
        title: int,
        part: int,
        section: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch CFR rule text from GovInfo.
        
        Args:
            title: CFR title number
            part: Part number
            section: Optional section
            year: Optional year
            
        Returns:
            Rule text and metadata
        """
        if not year:
            # CFR Title 17 updates April 1
            year = datetime.now().year
            if datetime.now().month < 4:
                year -= 1
        
        # Determine volume for Title 17
        volume = self._determine_cfr_volume(title, part)
        
        # Construct URL
        if section:
            granule_id = f"CFR-{year}-title{title}-vol{volume}-sec{part}-{section}"
        else:
            granule_id = f"CFR-{year}-title{title}-vol{volume}-part{part}"
        
        url = f"{self.base_url}/packages/CFR-{year}-title{title}-vol{volume}/granules/{granule_id}/summary"
        
        try:
            async with self.session.get(
                url,
                params={"api_key": self.api_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "title": title,
                        "part": part,
                        "section": section,
                        "year": year,
                        "volume": volume,
                        "text_url": data.get("download", {}).get("txtLink"),
                        "pdf_url": data.get("download", {}).get("pdfLink"),
                        "xml_url": data.get("download", {}).get("xmlLink"),
                        "last_modified": data.get("lastModified")
                    }
                elif response.status == 503:
                    await asyncio.sleep(30)
                    return await self.fetch_cfr_rule(title, part, section, year)
                else:
                    # Try link service as fallback
                    return await self._fetch_cfr_via_link(title, part, section, year)
        except Exception as e:
            raise IntegrityError(f"CFR fetch failed: {e}")
    
    def _determine_cfr_volume(self, title: int, part: int) -> int:
        """Determine CFR volume number for title and part."""
        if title == 17:  # SEC regulations
            if part <= 40:
                return 1
            elif part <= 199:
                return 2
            elif part <= 239:
                return 3
            else:
                return 4
        return 1  # Default
    
    async def _fetch_cfr_via_link(
        self,
        title: int,
        part: int,
        section: Optional[str],
        year: Optional[int]
    ) -> Dict[str, Any]:
        """Fetch CFR via link service as fallback."""
        base = "https://www.govinfo.gov/link/cfr"
        
        if section:
            url = f"{base}/{title}/{part}/{section}"
        else:
            url = f"{base}/{title}/{part}"
        
        params = {
            "link-type": "pdf",
            "year": year or "mostrecent"
        }
        
        # This returns a redirect to the actual document
        return {
            "title": title,
            "part": part,
            "section": section,
            "year": year,
            "link_url": f"{url}?{urlencode(params)}"
        }
    
    async def close(self):
        """Close aiohttp session to prevent resource warnings."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
