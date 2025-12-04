"""
GovInfo API Client - Federal Legal Document Retrieval
====================================================

Comprehensive integration with GovInfo.gov API for:
- USC (United States Code) title harvesting
- CFR (Code of Federal Regulations) retrieval
- Congressional bills and public laws
- Federal Register documents
- Supreme Court opinions

API Documentation: https://api.govinfo.gov/docs/
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import xml.etree.ElementTree as ET
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class LegalDocument:
    """Federal legal document metadata and content"""
    package_id: str
    title: str
    document_type: str  # 'USC', 'CFR', 'PLAW', 'FR', 'USCOURTS'
    
    # USC/CFR specific
    title_number: Optional[int] = None
    section: Optional[str] = None
    chapter: Optional[str] = None
    
    # Metadata
    publication_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    
    # Content
    full_text: str = ""
    xml_content: str = ""
    
    # Citations
    citations: List[str] = field(default_factory=list)
    
    # Relationships
    amends: List[str] = field(default_factory=list)
    repealed_by: Optional[str] = None
    
    def __post_init__(self):
        """Extract title number from package_id if not provided"""
        if not self.title_number and self.document_type in ['USC', 'CFR']:
            match = re.search(r'title(\d+)', self.package_id.lower())
            if match:
                self.title_number = int(match.group(1))


@dataclass
class USCTitle:
    """United States Code Title"""
    title_number: int
    title_name: str
    sections: Dict[str, LegalDocument] = field(default_factory=dict)
    chapters: Dict[str, str] = field(default_factory=dict)
    total_sections: int = 0


class GovInfoAPIClient:
    """
    GovInfo.gov API client for federal legal document retrieval
    
    Focus Areas (Enhancement Protocol):
    - Title 15: Commerce and Trade (Securities)
    - Title 17: Copyrights
    - Title 18: Crimes and Criminal Procedure
    - Title 26: Internal Revenue Code
    - Title 29: Labor
    - Title 31: Money and Finance
    - Title 33: Navigation and Navigable Waters
    - Title 42: Public Health and Welfare
    """
    
    BASE_URL = "https://api.govinfo.gov"
    
    # Priority USC Titles for financial/corporate investigations
    PRIORITY_TITLES = {
        15: "Commerce and Trade",
        17: "Copyrights", 
        18: "Crimes and Criminal Procedure",
        26: "Internal Revenue Code",
        29: "Labor",
        31: "Money and Finance",
        33: "Navigation and Navigable Waters",
        42: "Public Health and Welfare"
    }
    
    # Priority CFR Titles
    PRIORITY_CFR_TITLES = {
        17: "Commodity and Securities Exchanges",
        26: "Internal Revenue",
        29: "Labor"
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GovInfo API client
        
        Args:
            api_key: GovInfo API key (register at https://api.govinfo.gov/docs/)
        """
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Cache
        self._cache: Dict[str, Any] = {}
        
        # Statistics
        self.stats = {
            'api_calls': 0,
            'documents_retrieved': 0,
            'cache_hits': 0,
            'errors': 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {}
        if self.api_key:
            headers['X-Api-Key'] = self.api_key
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Execute API request with error handling"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Check cache
        cache_key = f"{endpoint}:{str(params)}"
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key]
        
        try:
            self.stats['api_calls'] += 1
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self._cache[cache_key] = data
                    return data
                elif response.status == 429:
                    logger.warning("⚠️ GovInfo rate limit hit, retrying...")
                    await asyncio.sleep(5)
                    return await self._request(endpoint, params)
                else:
                    logger.error(f"❌ GovInfo API error: {response.status}")
                    self.stats['errors'] += 1
                    return {}
        
        except Exception as e:
            logger.error(f"❌ GovInfo request failed: {e}")
            self.stats['errors'] += 1
            return {}
    
    async def get_usc_title(
        self,
        title_number: int,
        year: Optional[int] = None
    ) -> USCTitle:
        """
        Retrieve complete USC title
        
        Args:
            title_number: USC title number (1-54)
            year: Year of USC edition (default: latest)
        
        Returns:
            USCTitle object with all sections
        """
        logger.info(f"📚 Retrieving USC Title {title_number}...")
        
        if not year:
            year = datetime.now().year
        
        # Get title metadata
        package_id = f"USCODE-{year}-title{title_number}"
        
        endpoint = f"packages/{package_id}/summary"
        metadata = await self._request(endpoint)
        
        if not metadata:
            logger.error(f"❌ Failed to retrieve USC Title {title_number}")
            return USCTitle(
                title_number=title_number,
                title_name=self.PRIORITY_TITLES.get(title_number, f"Title {title_number}")
            )
        
        # Parse title structure
        title = USCTitle(
            title_number=title_number,
            title_name=metadata.get('title', f"Title {title_number}")
        )
        
        # Get granules (sections)
        granules_endpoint = f"packages/{package_id}/granules"
        granules_data = await self._request(granules_endpoint, params={'pageSize': 1000})
        
        granules = granules_data.get('granules', [])
        title.total_sections = len(granules)
        
        logger.info(f"✓ USC Title {title_number}: {title.total_sections} sections found")
        
        # Retrieve section content (sample for efficiency)
        for granule in granules[:100]:  # Limit to first 100 for performance
            granule_id = granule.get('granuleId')
            section = await self._get_usc_section(granule_id)
            
            if section:
                title.sections[section.section] = section
        
        self.stats['documents_retrieved'] += len(title.sections)
        
        return title
    
    async def _get_usc_section(self, granule_id: str) -> Optional[LegalDocument]:
        """Retrieve individual USC section"""
        try:
            # Get section summary
            endpoint = f"packages/{granule_id.split('/')[0]}/granules/{granule_id}/summary"
            summary = await self._request(endpoint)
            
            if not summary:
                return None
            
            # Extract section number
            section_match = re.search(r'§\s*(\d+[a-z]?(?:-\d+)?)', summary.get('title', ''))
            section_number = section_match.group(1) if section_match else granule_id
            
            # Get content
            content_endpoint = f"packages/{granule_id.split('/')[0]}/granules/{granule_id}/htm"
            content_response = await self._request(content_endpoint)
            
            doc = LegalDocument(
                package_id=granule_id,
                title=summary.get('title', ''),
                document_type='USC',
                section=section_number,
                full_text=content_response.get('content', '') if content_response else '',
                publication_date=self._parse_date(summary.get('dateIssued'))
            )
            
            return doc
        
        except Exception as e:
            logger.debug(f"Failed to retrieve section {granule_id}: {e}")
            return None
    
    async def get_cfr_title(
        self,
        title_number: int,
        year: Optional[int] = None
    ) -> Dict[str, LegalDocument]:
        """
        Retrieve CFR title (regulations)
        
        Args:
            title_number: CFR title number
            year: Year of CFR edition (default: latest)
        
        Returns:
            Dictionary of CFR sections
        """
        logger.info(f"📖 Retrieving CFR Title {title_number}...")
        
        if not year:
            year = datetime.now().year
        
        package_id = f"CFR-{year}-title{title_number}"
        
        # Get title metadata
        endpoint = f"packages/{package_id}/summary"
        metadata = await self._request(endpoint)
        
        if not metadata:
            logger.error(f"❌ Failed to retrieve CFR Title {title_number}")
            return {}
        
        # Get parts
        granules_endpoint = f"packages/{package_id}/granules"
        granules_data = await self._request(granules_endpoint, params={'pageSize': 1000})
        
        granules = granules_data.get('granules', [])
        logger.info(f"✓ CFR Title {title_number}: {len(granules)} parts found")
        
        cfr_sections = {}
        
        # Retrieve section content (sample)
        for granule in granules[:50]:  # Limit for performance
            granule_id = granule.get('granuleId')
            section = await self._get_cfr_section(granule_id)
            
            if section and section.section:
                cfr_sections[section.section] = section
        
        self.stats['documents_retrieved'] += len(cfr_sections)
        
        return cfr_sections
    
    async def _get_cfr_section(self, granule_id: str) -> Optional[LegalDocument]:
        """Retrieve individual CFR section"""
        try:
            # Get section summary
            endpoint = f"packages/{granule_id.split('/')[0]}/granules/{granule_id}/summary"
            summary = await self._request(endpoint)
            
            if not summary:
                return None
            
            # Extract part/section number
            title_text = summary.get('title', '')
            part_match = re.search(r'Part\s+(\d+)', title_text)
            section_match = re.search(r'§\s*(\d+\.\d+)', title_text)
            
            section_number = (
                section_match.group(1) if section_match
                else part_match.group(1) if part_match
                else granule_id
            )
            
            doc = LegalDocument(
                package_id=granule_id,
                title=title_text,
                document_type='CFR',
                section=section_number,
                publication_date=self._parse_date(summary.get('dateIssued'))
            )
            
            return doc
        
        except Exception as e:
            logger.debug(f"Failed to retrieve CFR section {granule_id}: {e}")
            return None
    
    async def search_documents(
        self,
        query: str,
        collection: str = "USCODE",
        max_results: int = 100
    ) -> List[LegalDocument]:
        """
        Search GovInfo for documents
        
        Args:
            query: Search query
            collection: Document collection (USCODE, CFR, PLAW, etc.)
            max_results: Maximum results to return
        
        Returns:
            List of matching documents
        """
        logger.info(f"🔍 Searching {collection} for: {query}")
        
        endpoint = "search"
        params = {
            'query': query,
            'collection': collection,
            'pageSize': min(max_results, 1000)
        }
        
        results = await self._request(endpoint, params=params)
        
        documents = []
        
        for result in results.get('results', [])[:max_results]:
            doc = LegalDocument(
                package_id=result.get('packageId', ''),
                title=result.get('title', ''),
                document_type=collection,
                publication_date=self._parse_date(result.get('dateIssued'))
            )
            documents.append(doc)
        
        logger.info(f"✓ Found {len(documents)} documents")
        
        return documents
    
    async def get_related_documents(
        self,
        package_id: str
    ) -> List[str]:
        """Get documents related to a package"""
        endpoint = f"packages/{package_id}/related"
        
        related = await self._request(endpoint)
        
        return [
            doc.get('packageId')
            for doc in related.get('relatedDocuments', [])
        ]
    
    async def harvest_priority_titles(self) -> Dict[int, USCTitle]:
        """
        Harvest all priority USC titles for investigations
        
        Returns:
            Dictionary mapping title number to USCTitle
        """
        logger.info("🌾 Harvesting priority USC titles...")
        
        titles = {}
        
        for title_num, title_name in self.PRIORITY_TITLES.items():
            logger.info(f"  Harvesting Title {title_num}: {title_name}")
            
            try:
                title = await self.get_usc_title(title_num)
                titles[title_num] = title
                
                # Rate limiting
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"  ❌ Failed to harvest Title {title_num}: {e}")
        
        total_sections = sum(t.total_sections for t in titles.values())
        logger.info(f"✓ Harvested {len(titles)} titles with {total_sections} total sections")
        
        return titles
    
    async def harvest_priority_cfr(self) -> Dict[int, Dict[str, LegalDocument]]:
        """
        Harvest priority CFR titles (regulations)
        
        Returns:
            Dictionary mapping CFR title number to sections
        """
        logger.info("🌾 Harvesting priority CFR titles...")
        
        cfr_titles = {}
        
        for title_num, title_name in self.PRIORITY_CFR_TITLES.items():
            logger.info(f"  Harvesting CFR Title {title_num}: {title_name}")
            
            try:
                sections = await self.get_cfr_title(title_num)
                cfr_titles[title_num] = sections
                
                # Rate limiting
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"  ❌ Failed to harvest CFR Title {title_num}: {e}")
        
        total_sections = sum(len(s) for s in cfr_titles.values())
        logger.info(f"✓ Harvested {len(cfr_titles)} CFR titles with {total_sections} sections")
        
        return cfr_titles
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse GovInfo date string"""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    # Demo usage
    async def demo():
        # Note: API key not required for basic access but recommended
        async with GovInfoAPIClient() as client:
            # Get USC Title 18 (Crimes)
            title18 = await client.get_usc_title(18)
            print(f"Title 18: {title18.title_name}")
            print(f"Sections retrieved: {len(title18.sections)}")
            
            # Search for securities fraud
            results = await client.search_documents(
                query="securities fraud",
                collection="USCODE",
                max_results=10
            )
            print(f"\nSearch results: {len(results)}")
            
            # Statistics
            stats = client.get_statistics()
            print(f"\nStatistics: {stats}")
    
    asyncio.run(demo())

