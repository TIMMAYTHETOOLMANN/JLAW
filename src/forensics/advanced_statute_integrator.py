"""
ADVANCED STATUTE INTEGRATOR - DUAL-AGENT CROSS-REFERENCE SYSTEM
================================================================

Integrates with GovInfo API to pull every statute and legal framework
correlated with SEC filings. Used by Anthropic agent for comprehensive
cross-referencing of violations flagged by OpenAI agent.

API Documentation:
- GovInfo API: https://api.govinfo.gov/docs/
- USC Collection: https://api.govinfo.gov/collections/USCODE
- CFR Collection: https://api.govinfo.gov/collections/CFR

Integration Pattern:
1. OpenAI flags violation → Extract statute reference
2. Anthropic receives violation → Calls statute integrator
3. Statute integrator → Queries GovInfo API for full text
4. Returns complete legal framework to Anthropic
5. Anthropic validates violation against full statute text
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum

from src.forensics.govinfo_api_client import GovInfoAPIClient, SearchRequest, SearchSort

logger = logging.getLogger(__name__)


class StatuteSeverity(Enum):
    """Statute severity classification for prosecutorial merit."""
    CRIMINAL = "CRIMINAL"  # Criminal penalties
    CIVIL = "CIVIL"  # Civil penalties
    REGULATORY = "REGULATORY"  # Regulatory enforcement
    ADMINISTRATIVE = "ADMINISTRATIVE"  # Administrative action


@dataclass
class StatuteReference:
    """Complete statute reference with full legal text."""
    citation: str  # e.g., "15 USC § 78p(a)"
    title: int  # e.g., 15 (Securities)
    section: str  # e.g., "78p"
    subsection: Optional[str] = None  # e.g., "(a)"
    full_text: Optional[str] = None
    summary: Optional[str] = None
    penalties: Dict[str, Any] = field(default_factory=dict)
    severity: StatuteSeverity = StatuteSeverity.REGULATORY
    related_cfr: List[str] = field(default_factory=list)  # Related CFR sections
    govinfo_url: Optional[str] = None
    package_id: Optional[str] = None
    last_updated: Optional[datetime] = None


@dataclass
class CFRReference:
    """Complete CFR (Code of Federal Regulations) reference."""
    citation: str  # e.g., "17 CFR § 240.10b-5"
    title: int  # e.g., 17
    part: str  # e.g., "240"
    section: str  # e.g., "10b-5"
    full_text: Optional[str] = None
    summary: Optional[str] = None
    implementing_statute: Optional[str] = None  # USC reference
    govinfo_url: Optional[str] = None
    package_id: Optional[str] = None
    last_updated: Optional[datetime] = None


@dataclass
class LegalFramework:
    """Complete legal framework for a violation."""
    primary_statute: StatuteReference
    related_statutes: List[StatuteReference] = field(default_factory=list)
    cfr_regulations: List[CFRReference] = field(default_factory=list)
    case_law: List[Dict[str, Any]] = field(default_factory=list)
    enforcement_history: Dict[str, Any] = field(default_factory=dict)
    prosecutorial_guidance: Optional[str] = None


class AdvancedStatuteIntegrator:
    """
    Advanced statute integration system using GovInfo API.
    
    Pulls complete legal frameworks for cross-referencing violations.
    """
    
    # Statute citation patterns
    USC_PATTERN = re.compile(r'(\d+)\s+U\.?S\.?C\.?\s*§\s*(\d+[a-z]?)(?:\(([a-z0-9]+)\))?', re.IGNORECASE)
    CFR_PATTERN = re.compile(r'(\d+)\s+C\.?F\.?R\.?\s*§\s*(\d+)\.(\d+[a-z]?(?:-\d+)?)', re.IGNORECASE)
    
    # SEC-specific statute mappings
    SEC_STATUTE_MAP = {
        "78p": {
            "name": "Directors, Officers, and Principal Stockholders",
            "subsections": {
                "(a)": "Reporting requirements for beneficial ownership",
                "(b)": "Profits from short-swing transactions",
                "(c)": "Conditions for sale of security by beneficial owner",
            },
            "penalties": {
                "civil": "$100,000 to $500,000 per violation",
                "criminal": "Up to 20 years imprisonment",
            },
            "severity": StatuteSeverity.CRIMINAL,
            "related_cfr": ["17 CFR § 240.16a-1", "17 CFR § 240.16a-3"],
        },
        "78m": {
            "name": "Periodical and Other Reports",
            "subsections": {
                "(a)": "Reports by issuers of securities",
                "(b)": "Form and contents of reports",
            },
            "penalties": {
                "civil": "$100,000 to $500,000 per violation",
                "criminal": "Up to 20 years imprisonment",
            },
            "severity": StatuteSeverity.CRIMINAL,
            "related_cfr": ["17 CFR § 240.13a-1", "17 CFR § 240.13a-13"],
        },
        "78j": {
            "name": "Manipulative and Deceptive Devices",
            "subsections": {
                "(b)": "Prohibition on manipulative and deceptive devices (Rule 10b-5)",
            },
            "penalties": {
                "civil": "$500,000 to $5,000,000 per violation",
                "criminal": "Up to 25 years imprisonment",
            },
            "severity": StatuteSeverity.CRIMINAL,
            "related_cfr": ["17 CFR § 240.10b-5"],
        },
    }
    
    def __init__(
        self,
        govinfo_api_key: str,
        strict_api_mode: bool = False,
        dual_agent: bool = True,
        govinfo_client: Optional[GovInfoAPIClient] = None
    ):
        """
        Initialize advanced statute integrator.
        
        Args:
            govinfo_api_key: GovInfo API key
            strict_api_mode: If True, fail on API errors. If False, use fallback data.
            dual_agent: Enable dual-agent cross-referencing mode
            govinfo_client: Optional pre-configured GovInfo client
        """
        self.api_key = govinfo_api_key
        self.strict_api_mode = strict_api_mode
        self.dual_agent = dual_agent
        
        # Initialize or use provided GovInfo client
        self.govinfo_client = govinfo_client or GovInfoAPIClient(api_key=govinfo_api_key)
        
        # Cache for statute lookups
        self._statute_cache: Dict[str, StatuteReference] = {}
        self._cfr_cache: Dict[str, CFRReference] = {}
        
        logger.info(f"✅ Advanced Statute Integrator initialized (strict={strict_api_mode}, dual_agent={dual_agent})")
    
    def parse_statute_citation(self, citation: str) -> Optional[StatuteReference]:
        """
        Parse a statute citation string into structured reference.
        
        Args:
            citation: Citation string (e.g., "15 USC § 78p(a)")
            
        Returns:
            StatuteReference object or None if parsing fails
        """
        # Try USC pattern
        usc_match = self.USC_PATTERN.search(citation)
        if usc_match:
            title = int(usc_match.group(1))
            section = usc_match.group(2)
            subsection = f"({usc_match.group(3)})" if usc_match.group(3) else None
            
            # Build citation
            full_citation = f"{title} USC § {section}"
            if subsection:
                full_citation += subsection
            
            # Get metadata from SEC statute map
            metadata = self.SEC_STATUTE_MAP.get(section, {})
            
            return StatuteReference(
                citation=full_citation,
                title=title,
                section=section,
                subsection=subsection,
                summary=metadata.get("name"),
                penalties=metadata.get("penalties", {}),
                severity=metadata.get("severity", StatuteSeverity.REGULATORY),
                related_cfr=metadata.get("related_cfr", []),
            )
        
        return None
    
    def parse_cfr_citation(self, citation: str) -> Optional[CFRReference]:
        """
        Parse a CFR citation string into structured reference.
        
        Args:
            citation: Citation string (e.g., "17 CFR § 240.10b-5")
            
        Returns:
            CFRReference object or None if parsing fails
        """
        cfr_match = self.CFR_PATTERN.search(citation)
        if cfr_match:
            title = int(cfr_match.group(1))
            part = cfr_match.group(2)
            section = cfr_match.group(3)
            
            full_citation = f"{title} CFR § {part}.{section}"
            
            return CFRReference(
                citation=full_citation,
                title=title,
                part=part,
                section=section,
            )
        
        return None
    
    async def fetch_statute_from_govinfo(self, statute_ref: StatuteReference) -> StatuteReference:
        """
        Fetch complete statute text from GovInfo API.
        
        Args:
            statute_ref: Statute reference to enrich
            
        Returns:
            Enriched statute reference with full text
        """
        # Check cache first
        cache_key = statute_ref.citation
        if cache_key in self._statute_cache:
            logger.debug(f"[Statute Cache Hit] {cache_key}")
            return self._statute_cache[cache_key]
        
        try:
            # Build search query for USCODE collection
            query = f"title:{statute_ref.title} AND section:{statute_ref.section}"
            
            search_request = SearchRequest(
                query=query,
                pageSize=5,
                sorts=[SearchSort("relevancy", "DESC")],
                resultLevel="full"
            )
            
            # Search for statute
            response = await self.govinfo_client.search_documents(search_request, collection="USCODE")
            
            if response.results:
                result = response.results[0]
                
                # Try to get full text
                if "txt" in result.download:
                    txt_url = result.download["txt"]
                    async with aiohttp.ClientSession() as session:
                        async with session.get(txt_url) as resp:
                            if resp.status == 200:
                                statute_ref.full_text = await resp.text()
                
                statute_ref.govinfo_url = result.resultLink
                statute_ref.package_id = result.packageId
                statute_ref.last_updated = datetime.utcnow()
                
                logger.info(f"✅ Fetched statute from GovInfo: {statute_ref.citation}")
            else:
                logger.warning(f"⚠️ No GovInfo results for statute: {statute_ref.citation}")
                if self.strict_api_mode:
                    raise ValueError(f"Statute not found in GovInfo: {statute_ref.citation}")
        
        except Exception as e:
            logger.error(f"❌ GovInfo API error for {statute_ref.citation}: {e}")
            if self.strict_api_mode:
                raise
            # In non-strict mode, continue with partial data
        
        # Cache result
        self._statute_cache[cache_key] = statute_ref
        return statute_ref
    
    async def fetch_cfr_from_govinfo(self, cfr_ref: CFRReference) -> CFRReference:
        """
        Fetch complete CFR regulation text from GovInfo API.
        
        Args:
            cfr_ref: CFR reference to enrich
            
        Returns:
            Enriched CFR reference with full text
        """
        # Check cache first
        cache_key = cfr_ref.citation
        if cache_key in self._cfr_cache:
            logger.debug(f"[CFR Cache Hit] {cache_key}")
            return self._cfr_cache[cache_key]
        
        try:
            # Build search query for CFR collection
            query = f"title:{cfr_ref.title} AND part:{cfr_ref.part} AND section:{cfr_ref.section}"
            
            search_request = SearchRequest(
                query=query,
                pageSize=5,
                sorts=[SearchSort("relevancy", "DESC")],
                resultLevel="full"
            )
            
            # Search for CFR
            response = await self.govinfo_client.search_documents(search_request, collection="CFR")
            
            if response.results:
                result = response.results[0]
                
                # Try to get full text
                if "txt" in result.download:
                    txt_url = result.download["txt"]
                    async with aiohttp.ClientSession() as session:
                        async with session.get(txt_url) as resp:
                            if resp.status == 200:
                                cfr_ref.full_text = await resp.text()
                
                cfr_ref.govinfo_url = result.resultLink
                cfr_ref.package_id = result.packageId
                cfr_ref.last_updated = datetime.utcnow()
                
                logger.info(f"✅ Fetched CFR from GovInfo: {cfr_ref.citation}")
            else:
                logger.warning(f"⚠️ No GovInfo results for CFR: {cfr_ref.citation}")
                if self.strict_api_mode:
                    raise ValueError(f"CFR not found in GovInfo: {cfr_ref.citation}")
        
        except Exception as e:
            logger.error(f"❌ GovInfo API error for {cfr_ref.citation}: {e}")
            if self.strict_api_mode:
                raise
        
        # Cache result
        self._cfr_cache[cache_key] = cfr_ref
        return cfr_ref
    
    async def build_legal_framework(
        self,
        primary_citation: str,
        include_related: bool = True
    ) -> LegalFramework:
        """
        Build complete legal framework for a statute citation.
        
        This is called by the Anthropic agent when cross-referencing
        violations flagged by the OpenAI agent.
        
        Args:
            primary_citation: Primary statute citation (e.g., "15 USC § 78p(a)")
            include_related: Whether to include related statutes and CFRs
            
        Returns:
            Complete legal framework with all correlated statutes
        """
        logger.info(f"[Legal Framework] Building framework for: {primary_citation}")
        
        # Parse primary statute
        primary_statute = self.parse_statute_citation(primary_citation)
        if not primary_statute:
            raise ValueError(f"Invalid statute citation: {primary_citation}")
        
        # Fetch full text from GovInfo
        primary_statute = await self.fetch_statute_from_govinfo(primary_statute)
        
        # Build framework
        framework = LegalFramework(primary_statute=primary_statute)
        
        if include_related:
            # Fetch related CFR regulations
            for cfr_citation in primary_statute.related_cfr:
                cfr_ref = self.parse_cfr_citation(cfr_citation)
                if cfr_ref:
                    cfr_ref = await self.fetch_cfr_from_govinfo(cfr_ref)
                    framework.cfr_regulations.append(cfr_ref)
            
            # Search for related statutes
            related_citations = await self._find_related_statutes(primary_statute)
            for citation in related_citations:
                related_ref = self.parse_statute_citation(citation)
                if related_ref:
                    related_ref = await self.fetch_statute_from_govinfo(related_ref)
                    framework.related_statutes.append(related_ref)
        
        logger.info(
            f"✅ Legal framework built: {len(framework.related_statutes)} related statutes, "
            f"{len(framework.cfr_regulations)} CFR regulations"
        )
        
        return framework
    
    async def _find_related_statutes(self, statute_ref: StatuteReference) -> List[str]:
        """
        Find related statutes in the same title.
        
        Args:
            statute_ref: Primary statute reference
            
        Returns:
            List of related statute citations
        """
        related = []
        
        # For SEC statutes (Title 15), find related sections
        if statute_ref.title == 15 and statute_ref.section.startswith("78"):
            # Common related SEC statutes
            base_section = statute_ref.section[:3]  # e.g., "78p" -> "78"
            
            related_sections = {
                "78p": ["78m", "78j"],  # Section 16 related to 13, 10
                "78m": ["78p", "78j"],  # Section 13 related to 16, 10
                "78j": ["78m", "78p"],  # Section 10 related to 13, 16
            }
            
            if statute_ref.section in related_sections:
                for related_sec in related_sections[statute_ref.section]:
                    related.append(f"{statute_ref.title} USC § {related_sec}")
        
        return related
    
    async def cross_reference_violation(
        self,
        violation: Dict[str, Any],
        filing_content: str
    ) -> Dict[str, Any]:
        """
        Cross-reference a flagged violation with complete legal framework.
        
        This is the main entry point called by the Anthropic agent during
        dual-agent investigation workflow.
        
        Args:
            violation: Violation dict from OpenAI agent
            filing_content: Original filing content for evidence extraction
            
        Returns:
            Enhanced violation with complete legal framework
        """
        logger.info(f"[Cross-Reference] Processing violation: {violation.get('type', 'UNKNOWN')}")
        
        # Extract statute citation
        statute_citation = violation.get("statute")
        if not statute_citation:
            logger.warning(f"⚠️ No statute citation in violation: {violation}")
            return violation
        
        # Build complete legal framework
        try:
            framework = await self.build_legal_framework(statute_citation, include_related=True)
            
            # Enhance violation with framework
            enhanced_violation = {
                **violation,
                "legal_framework": {
                    "primary_statute": {
                        "citation": framework.primary_statute.citation,
                        "full_text": framework.primary_statute.full_text,
                        "summary": framework.primary_statute.summary,
                        "penalties": framework.primary_statute.penalties,
                        "severity": framework.primary_statute.severity.value,
                        "govinfo_url": framework.primary_statute.govinfo_url,
                    },
                    "related_statutes": [
                        {
                            "citation": s.citation,
                            "summary": s.summary,
                            "govinfo_url": s.govinfo_url,
                        }
                        for s in framework.related_statutes
                    ],
                    "cfr_regulations": [
                        {
                            "citation": c.citation,
                            "full_text": c.full_text,
                            "govinfo_url": c.govinfo_url,
                        }
                        for c in framework.cfr_regulations
                    ],
                },
                "cross_reference_complete": True,
                "cross_reference_timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(f"✅ Cross-reference complete for: {violation.get('type')}")
            return enhanced_violation
        
        except Exception as e:
            logger.error(f"❌ Cross-reference failed: {e}")
            if self.strict_api_mode:
                raise
            
            # In non-strict mode, return original violation with error flag
            return {
                **violation,
                "cross_reference_error": str(e),
                "cross_reference_complete": False,
            }
    
    async def batch_cross_reference(
        self,
        violations: List[Dict[str, Any]],
        filing_content: str,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Cross-reference multiple violations in batch.
        
        Args:
            violations: List of violations from OpenAI agent
            filing_content: Original filing content
            max_concurrent: Maximum concurrent API requests
            
        Returns:
            List of enhanced violations with legal frameworks
        """
        logger.info(f"[Batch Cross-Reference] Processing {len(violations)} violations")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_one(violation: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.cross_reference_violation(violation, filing_content)
        
        # Process all violations concurrently
        tasks = [process_one(v) for v in violations]
        enhanced_violations = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        results = []
        for i, result in enumerate(enhanced_violations):
            if isinstance(result, Exception):
                logger.error(f"❌ Batch cross-reference error for violation {i}: {result}")
                results.append(violations[i])  # Return original on error
            else:
                results.append(result)
        
        logger.info(f"✅ Batch cross-reference complete: {len(results)} violations processed")
        return results

