"""
Statutory Citation Engine
=========================

Integrates with GovInfo API to retrieve and validate statutory citations
for DOJ-level forensic reporting. Provides enriched legal references
with full text, summaries, and penalty information.

Key Features:
- GovInfo API integration for USC and CFR lookups
- Statutory reference enrichment with full text
- Penalty information extraction
- Citation validation and formatting
- Caching for performance optimization
"""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .constants import (
    SEC_STATUTES,
    StatutoryInfo,
    ViolationType,
    VIOLATION_STATUTE_MAP,
    get_statute_for_violation,
    get_all_statutes_for_violation,
)
from .models import StatutoryReference

logger = logging.getLogger(__name__)


@dataclass
class GovInfoCitation:
    """
    Citation retrieved from GovInfo API.
    
    Contains full text, metadata, and source URL
    for a USC or CFR citation.
    """
    citation: str
    title: str
    collection: str  # uscode, cfr, bills
    full_text: str
    summary: str
    effective_date: Optional[str] = None
    govinfo_url: str = ""
    pdf_url: str = ""
    xml_url: str = ""
    
    # Penalty information (extracted from text)
    civil_penalty_min: Optional[float] = None
    civil_penalty_max: Optional[float] = None
    criminal_penalty: Optional[bool] = None
    prison_years_max: Optional[int] = None
    
    # Metadata
    retrieved_at: datetime = field(default_factory=datetime.utcnow)
    cache_key: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation": self.citation,
            "title": self.title,
            "collection": self.collection,
            "full_text": self.full_text[:2000] + "..." if len(self.full_text) > 2000 else self.full_text,
            "summary": self.summary,
            "effective_date": self.effective_date,
            "govinfo_url": self.govinfo_url,
            "pdf_url": self.pdf_url,
            "civil_penalty_min": self.civil_penalty_min,
            "civil_penalty_max": self.civil_penalty_max,
            "criminal_penalty": self.criminal_penalty,
            "prison_years_max": self.prison_years_max,
            "retrieved_at": self.retrieved_at.isoformat(),
        }


class CitationCache:
    """
    Simple file-based cache for GovInfo citations.
    
    Caches API responses to reduce API calls and improve performance.
    """
    
    def __init__(self, cache_dir: str = "./cache/citations", ttl_hours: int = 24 * 7):
        """
        Initialize citation cache.
        
        Args:
            cache_dir: Directory for cache files
            ttl_hours: Cache TTL in hours (default: 7 days)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self._memory_cache: Dict[str, GovInfoCitation] = {}
    
    def _get_cache_key(self, citation: str) -> str:
        """Generate cache key from citation."""
        normalized = citation.lower().replace(" ", "_").replace(".", "").replace("§", "s")
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def get(self, citation: str) -> Optional[GovInfoCitation]:
        """Get citation from cache."""
        cache_key = self._get_cache_key(citation)
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            cached = self._memory_cache[cache_key]
            if datetime.utcnow() - cached.retrieved_at < self.ttl:
                return cached
        
        # Check file cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                retrieved_at = datetime.fromisoformat(data["retrieved_at"])
                if datetime.utcnow() - retrieved_at < self.ttl:
                    citation_obj = GovInfoCitation(
                        citation=data["citation"],
                        title=data["title"],
                        collection=data["collection"],
                        full_text=data["full_text"],
                        summary=data["summary"],
                        effective_date=data.get("effective_date"),
                        govinfo_url=data.get("govinfo_url", ""),
                        pdf_url=data.get("pdf_url", ""),
                        civil_penalty_min=data.get("civil_penalty_min"),
                        civil_penalty_max=data.get("civil_penalty_max"),
                        criminal_penalty=data.get("criminal_penalty"),
                        prison_years_max=data.get("prison_years_max"),
                        retrieved_at=retrieved_at,
                        cache_key=cache_key,
                    )
                    self._memory_cache[cache_key] = citation_obj
                    return citation_obj
            except Exception as e:
                logger.debug(f"Cache read error for {citation}: {e}")
        
        return None
    
    def set(self, citation: GovInfoCitation) -> None:
        """Store citation in cache."""
        cache_key = self._get_cache_key(citation.citation)
        citation.cache_key = cache_key
        
        # Store in memory
        self._memory_cache[cache_key] = citation
        
        # Store in file
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(citation.to_dict(), f, indent=2)
        except Exception as e:
            logger.debug(f"Cache write error for {citation.citation}: {e}")


class StatutoryCitationEngine:
    """
    Engine for retrieving and enriching statutory citations.
    
    Integrates with GovInfo API to provide comprehensive legal
    references for DOJ-level forensic reports.
    """
    
    # GovInfo API base URL
    GOVINFO_API_BASE = "https://api.govinfo.gov"
    
    # Citation patterns
    USC_PATTERN = re.compile(
        r"(\d+)\s*U\.?S\.?C\.?\s*§?\s*(\d+[a-z]?(?:\([a-z0-9]+\))*)",
        re.IGNORECASE
    )
    CFR_PATTERN = re.compile(
        r"(\d+)\s*C\.?F\.?R\.?\s*§?\s*([\d.]+)",
        re.IGNORECASE
    )
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: str = "./cache/citations",
        use_fallback: bool = True
    ):
        """
        Initialize Statutory Citation Engine.
        
        Args:
            api_key: GovInfo API key (optional, uses fallback if not provided)
            cache_dir: Directory for citation cache
            use_fallback: Use built-in statute database when API unavailable
        """
        self.api_key = api_key
        self.cache = CitationCache(cache_dir=cache_dir)
        self.use_fallback = use_fallback
        
        # HTTP client will be initialized on first use
        self._http_client = None
        
        logger.info(
            f"StatutoryCitationEngine initialized "
            f"(api_key={'configured' if api_key else 'not configured'}, "
            f"fallback={'enabled' if use_fallback else 'disabled'})"
        )
    
    async def get_citation(self, citation_text: str) -> Optional[GovInfoCitation]:
        """
        Retrieve statutory citation with full details.
        
        Args:
            citation_text: Citation string (e.g., "15 U.S.C. § 78p(a)")
            
        Returns:
            GovInfoCitation with full text and metadata, or None if not found
        """
        # Check cache first
        cached = self.cache.get(citation_text)
        if cached:
            logger.debug(f"Cache hit for {citation_text}")
            return cached
        
        # Try API if configured
        if self.api_key:
            citation = await self._fetch_from_govinfo(citation_text)
            if citation:
                self.cache.set(citation)
                return citation
        
        # Fall back to built-in database
        if self.use_fallback:
            citation = self._get_from_fallback(citation_text)
            if citation:
                self.cache.set(citation)
                return citation
        
        logger.warning(f"Could not retrieve citation: {citation_text}")
        return None
    
    async def enrich_violation_citations(
        self,
        violation_type: ViolationType
    ) -> List[GovInfoCitation]:
        """
        Get all statutory citations relevant to a violation type.
        
        Args:
            violation_type: Type of violation
            
        Returns:
            List of GovInfoCitation objects for all relevant statutes
        """
        statutes = get_all_statutes_for_violation(violation_type)
        citations = []
        
        for statute in statutes:
            citation = await self.get_citation(statute.citation)
            if citation:
                citations.append(citation)
        
        return citations
    
    async def batch_enrich_citations(
        self,
        citation_texts: List[str],
        max_concurrent: int = 5
    ) -> List[GovInfoCitation]:
        """
        Batch retrieve multiple citations with concurrency control.
        
        Args:
            citation_texts: List of citation strings
            max_concurrent: Maximum concurrent API requests
            
        Returns:
            List of retrieved GovInfoCitation objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(citation: str) -> Optional[GovInfoCitation]:
            async with semaphore:
                return await self.get_citation(citation)
        
        tasks = [fetch_with_semaphore(c) for c in citation_texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        citations = []
        for result in results:
            if isinstance(result, GovInfoCitation):
                citations.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"Citation fetch failed: {result}")
        
        return citations
    
    def create_statutory_reference(
        self,
        citation: GovInfoCitation
    ) -> StatutoryReference:
        """
        Convert GovInfoCitation to StatutoryReference model.
        
        Args:
            citation: GovInfoCitation object
            
        Returns:
            StatutoryReference for use in reporting models
        """
        penalties = None
        if citation.civil_penalty_min is not None or citation.criminal_penalty is not None:
            penalties = {
                "civil_min": citation.civil_penalty_min,
                "civil_max": citation.civil_penalty_max,
                "criminal_exposure": citation.criminal_penalty,
                "prison_years_max": citation.prison_years_max,
            }
        
        return StatutoryReference(
            citation=citation.citation,
            title=citation.title,
            summary=citation.summary,
            full_text=citation.full_text,
            govinfo_url=citation.govinfo_url,
            cfr_reference=None,  # Can be populated if CFR related
            penalties=penalties,
        )
    
    async def _fetch_from_govinfo(
        self,
        citation_text: str
    ) -> Optional[GovInfoCitation]:
        """Fetch citation from GovInfo API."""
        try:
            import aiohttp
            
            # Parse citation to determine collection and parameters
            parsed = self._parse_citation(citation_text)
            if not parsed:
                logger.debug(f"Could not parse citation: {citation_text}")
                return None
            
            collection, title, section = parsed
            
            # Build API URL
            # Note: This is a simplified implementation
            # Real GovInfo API has different endpoints for different collections
            if collection == "uscode":
                # Search for USC section
                url = (
                    f"{self.GOVINFO_API_BASE}/collections/USCODE/"
                    f"?offset=0&pageSize=10&titleNumber={title}&sectionNumber={section}"
                )
            elif collection == "cfr":
                url = (
                    f"{self.GOVINFO_API_BASE}/collections/CFR/"
                    f"?offset=0&pageSize=10&titleNumber={title}"
                )
            else:
                return None
            
            headers = {
                "X-Api-Key": self.api_key,
                "Accept": "application/json",
            }
            
            async with aiohttp.ClientSession(trust_env=True) as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_govinfo_response(data, citation_text, collection)
                    else:
                        logger.debug(f"GovInfo API returned {response.status} for {citation_text}")
                        return None
                        
        except ImportError:
            logger.debug("aiohttp not available for GovInfo API")
            return None
        except Exception as e:
            logger.debug(f"GovInfo API error for {citation_text}: {e}")
            return None
    
    def _parse_citation(self, citation_text: str) -> Optional[Tuple[str, str, str]]:
        """
        Parse citation text to extract collection, title, and section.
        
        Returns:
            Tuple of (collection, title, section) or None if parsing fails
        """
        # Try USC pattern
        usc_match = self.USC_PATTERN.search(citation_text)
        if usc_match:
            return ("uscode", usc_match.group(1), usc_match.group(2))
        
        # Try CFR pattern
        cfr_match = self.CFR_PATTERN.search(citation_text)
        if cfr_match:
            return ("cfr", cfr_match.group(1), cfr_match.group(2))
        
        return None
    
    def _parse_govinfo_response(
        self,
        data: Dict[str, Any],
        citation_text: str,
        collection: str
    ) -> Optional[GovInfoCitation]:
        """Parse GovInfo API response to GovInfoCitation."""
        try:
            packages = data.get("packages", [])
            if not packages:
                return None
            
            package = packages[0]
            
            return GovInfoCitation(
                citation=citation_text,
                title=package.get("title", ""),
                collection=collection,
                full_text=package.get("summary", ""),
                summary=package.get("summary", "")[:500],
                govinfo_url=package.get("packageLink", ""),
                pdf_url=package.get("pdfLink", ""),
            )
        except Exception as e:
            logger.debug(f"Error parsing GovInfo response: {e}")
            return None
    
    def _get_from_fallback(self, citation_text: str) -> Optional[GovInfoCitation]:
        """Get citation from built-in fallback database."""
        # Check built-in SEC_STATUTES database
        for key, statute in SEC_STATUTES.items():
            if self._citations_match(citation_text, statute.citation):
                return GovInfoCitation(
                    citation=statute.citation,
                    title=statute.title,
                    collection=statute.govinfo_collection,
                    full_text=statute.summary,  # Using summary as placeholder
                    summary=statute.summary,
                    civil_penalty_min=statute.civil_penalty_min,
                    civil_penalty_max=statute.civil_penalty_max,
                    criminal_penalty=statute.criminal_exposure,
                    prison_years_max=statute.prison_years_max,
                    govinfo_url=self._build_govinfo_url(statute.citation),
                )
        
        return None
    
    def _citations_match(self, citation1: str, citation2: str) -> bool:
        """Check if two citations refer to the same statute."""
        # Normalize citations
        def normalize(c: str) -> str:
            return (
                c.lower()
                .replace(".", "")
                .replace(" ", "")
                .replace("§", "")
                .replace("usc", "usc")
                .replace("cfr", "cfr")
            )
        
        return normalize(citation1) == normalize(citation2)
    
    def _extract_title(self, citation: str) -> str:
        """Extract title number from citation."""
        match = self.USC_PATTERN.search(citation)
        if match:
            return match.group(1)
        
        match = self.CFR_PATTERN.search(citation)
        if match:
            return match.group(1)
        
        return "15"  # Default to Title 15 (Securities)
    
    def _build_govinfo_url(self, citation: str) -> str:
        """Build GovInfo URL from citation."""
        title_num = self._extract_title(citation)
        return f"https://www.govinfo.gov/content/pkg/USCODE-2022-title{title_num}/html/USCODE-2022-title{title_num}.htm"
    
    def format_citation(
        self,
        citation: GovInfoCitation,
        format_type: str = "full"
    ) -> str:
        """
        Format citation for display in reports.
        
        Args:
            citation: GovInfoCitation object
            format_type: "full", "short", or "markdown"
            
        Returns:
            Formatted citation string
        """
        if format_type == "short":
            return citation.citation
        
        elif format_type == "markdown":
            return (
                f"**{citation.citation}** - *{citation.title}*\n\n"
                f"> {citation.summary}\n\n"
                f"[View on GovInfo]({citation.govinfo_url})"
            )
        
        else:  # full
            parts = [
                f"{citation.citation}",
                f"Title: {citation.title}",
                f"Summary: {citation.summary}",
            ]
            
            if citation.civil_penalty_max:
                parts.append(
                    f"Civil Penalty Range: ${citation.civil_penalty_min or 0:,.0f} - "
                    f"${citation.civil_penalty_max:,.0f}"
                )
            
            if citation.criminal_penalty:
                parts.append(
                    f"Criminal Exposure: Up to {citation.prison_years_max or 0} years imprisonment"
                )
            
            return "\n".join(parts)
    
    async def close(self) -> None:
        """Close HTTP client and clean up resources."""
        if self._http_client:
            try:
                await self._http_client.close()
            except Exception:
                pass


# Factory function for easy instantiation
def create_citation_engine(
    api_key: Optional[str] = None,
    cache_dir: str = "./cache/citations"
) -> StatutoryCitationEngine:
    """
    Create a StatutoryCitationEngine with optional API key.
    
    Args:
        api_key: GovInfo API key (optional)
        cache_dir: Cache directory path
        
    Returns:
        Configured StatutoryCitationEngine instance
    """
    return StatutoryCitationEngine(
        api_key=api_key,
        cache_dir=cache_dir,
        use_fallback=True
    )
