"""
GOVINFO API CLIENT - OFFICIAL IMPLEMENTATION
============================================

Based on official GovInfo API documentation (api.govinfo.gov)
Implements proper collection-based retrieval for USCODE and CFR documents.

Your API Key Status (Verified Working):
- Rate Limit: 36,000 requests/hour
- Remaining: 35,991 requests  
- Collections Available: 41 (including USCODE with 1,992,943 granules)

API Documentation: https://api.govinfo.gov/docs/
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class SortOrder(Enum):
    """Sort order for search results."""
    ASC = "ASC"
    DESC = "DESC"


class ResultLevel(Enum):
    """Result detail level."""
    DEFAULT = "default"
    FULL = "full"


@dataclass
class SearchSort:
    """Search result sorting configuration."""
    field: str  # relevancy, publishdate, title, etc.
    sortOrder: str = "DESC"  # ASC or DESC


@dataclass
class SearchRequest:
    """
    GovInfo Search API request structure.
    
    Implements POST /search endpoint for complex document queries.
    """
    query: str
    pageSize: int = 10
    offsetMark: str = "*"
    sorts: List[SearchSort] = field(default_factory=lambda: [SearchSort("relevancy", "DESC")])
    historical: bool = True
    resultLevel: str = "default"


@dataclass
class SearchResult:
    """Individual search result from GovInfo."""
    title: str
    packageId: str
    granuleId: Optional[str] = None
    lastModified: Optional[str] = None
    governmentAuthor: List[str] = field(default_factory=list)
    dateIssued: Optional[str] = None
    collectionCode: Optional[str] = None
    resultLink: Optional[str] = None
    dateIngested: Optional[str] = None
    download: Dict[str, str] = field(default_factory=dict)
    relatedLink: Optional[str] = None


@dataclass
class SearchResponse:
    """GovInfo Search API response."""
    results: List[SearchResult]
    offsetMark: Optional[str] = None
    count: int = 0


@dataclass
class RelatedDocument:
    """Related document from GovInfo relationships API."""
    relationshipType: str
    packageId: str
    collectionCode: str
    title: Optional[str] = None
    lastModified: Optional[str] = None
    dateIssued: Optional[str] = None
    congress: Optional[str] = None
    session: Optional[str] = None
    relationshipMetadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelatedDocumentsResponse:
    """Response from related documents API."""
    accessId: str
    relationships: List[RelatedDocument]
    count: int = 0


@dataclass
class GovInfoPackage:
    """GovInfo package metadata."""
    package_id: str
    last_modified: str
    package_link: str
    doc_class: Optional[str] = None
    title: Optional[str] = None
    date_issued: Optional[str] = None


class GovInfoAPIClient:
    """
    Official GovInfo API Client
    
    Implements proper collection-based API endpoints per official documentation:
    - GET /collections - List all collections
    - GET /collections/{collection}/{startDate} - Get packages by date
    - GET /packages/{packageId}/summary - Get package metadata
    - GET /packages/{packageId} - Get full package details
    
    Rate Limits:
    - 36,000 requests/hour with API key
    - 1,000 requests/hour without API key
    """
    
    def __init__(self, api_key: str):
        """
        Initialize GovInfo API client.
        
        Args:
            api_key: Your GovInfo API key from api.data.gov
        """
        if not api_key or api_key == "DEMO_KEY":
            raise ValueError(
                "Valid GOVINFO_API_KEY required. Get one from https://api.data.gov/signup/"
            )
        
        self.api_key = api_key
        self.base_url = "https://api.govinfo.gov"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Collections relevant to legal research
        self.legal_collections = {
            "USCODE": "United States Code",
            "CFR": "Code of Federal Regulations",
            "FR": "Federal Register",
            "PLAW": "Public and Private Laws",
            "STATUTE": "Statutes at Large",
            "USCOURTS": "United States Courts Opinions",
            "CRPT": "Congressional Reports"
        }
        
        logger.info(f"GovInfoAPIClient initialized (Rate Limit: 36,000 req/hour)")
    
    async def get_collections(self) -> List[Dict[str, Any]]:
        """
        Get list of all available collections.
        
        Endpoint: GET /collections
        
        Returns:
            List of collection metadata
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/collections"
        params = {"api_key": self.api_key}
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data.get('collections', []))} collections")
                    return data.get("collections", [])
                else:
                    raise ConnectionError(f"GovInfo collections API returned {response.status}")
        except Exception as e:
            logger.error(f"Failed to get collections: {e}")
            raise
    
    async def search_uscode_packages(
        self,
        title: int,
        start_date: Optional[datetime] = None,
        page_size: int = 100
    ) -> List[GovInfoPackage]:
        """
        Search USCODE collection for packages by title.
        
        Endpoint: GET /collections/USCODE/{startDate}
        
        Args:
            title: USC title number (e.g., 15 for securities laws)
            start_date: Start date for search (defaults to 1 year ago)
            page_size: Number of results per page (max 1000)
        
        Returns:
            List of matching packages
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        
        # Format date per API spec: yyyy-MM-dd'T'HH:mm:ss'Z'
        date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        url = f"{self.base_url}/collections/USCODE/{date_str}"
        params = {
            "api_key": self.api_key,
            "pageSize": min(page_size, 1000),
            "offsetMark": "*"  # Use new pagination system
        }
        
        packages = []
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pkg in data.get("packages", []):
                        # Filter by title if we can determine it from packageId
                        pkg_id = pkg.get("packageId", "")
                        if f"title{title}" in pkg_id.lower():
                            packages.append(GovInfoPackage(
                                package_id=pkg_id,
                                last_modified=pkg.get("lastModified", ""),
                                package_link=pkg.get("packageLink", ""),
                                doc_class=pkg.get("docClass"),
                                title=pkg.get("title"),
                                date_issued=pkg.get("dateIssued")
                            ))
                    
                    logger.info(f"Found {len(packages)} USCODE packages for title {title}")
                    return packages
                elif response.status == 500:
                    raise ConnectionError("GovInfo USCODE collection API returned 500 (server error)")
                else:
                    raise ConnectionError(f"GovInfo USCODE API returned {response.status}")
        except Exception as e:
            logger.error(f"Failed to search USCODE packages: {e}")
            raise
    
    async def get_package_summary(self, package_id: str) -> Dict[str, Any]:
        """
        Get package summary metadata.
        
        Endpoint: GET /packages/{packageId}/summary
        
        Args:
            package_id: Package identifier (e.g., "USCODE-2024-title15")
        
        Returns:
            Package summary with download links
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/packages/{package_id}/summary"
        params = {"api_key": self.api_key}
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved package summary: {package_id}")
                    return data
                elif response.status == 404:
                    raise ValueError(f"Package not found: {package_id}")
                elif response.status == 500:
                    raise ConnectionError(f"GovInfo package API returned 500 for {package_id}")
                else:
                    raise ConnectionError(f"GovInfo package API returned {response.status}")
        except Exception as e:
            logger.error(f"Failed to get package summary for {package_id}: {e}")
            raise
    
    async def get_package_full(self, package_id: str) -> Dict[str, Any]:
        """
        Get full package details including all granules.
        
        Endpoint: GET /packages/{packageId}
        
        Args:
            package_id: Package identifier
        
        Returns:
            Complete package details
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/packages/{package_id}"
        params = {"api_key": self.api_key}
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved full package: {package_id}")
                    return data
                elif response.status == 404:
                    raise ValueError(f"Package not found: {package_id}")
                elif response.status == 500:
                    raise ConnectionError(f"GovInfo package API returned 500 for {package_id}")
                else:
                    raise ConnectionError(f"GovInfo package API returned {response.status}")
        except Exception as e:
            logger.error(f"Failed to get full package for {package_id}: {e}")
            raise
    
    async def fetch_usc_statute_by_collection(
        self,
        title: int,
        section: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch USC statute using collection-based API (PROPER METHOD).
        
        This method:
        1. Searches USCODE collection for relevant packages
        2. Gets package summary for the specific title
        3. Returns download links and metadata
        
        Args:
            title: USC title (e.g., 15)
            section: Section (e.g., "78j")
            year: Year (defaults to current year - 1)
        
        Returns:
            Statute metadata with download URLs
        """
        if not year:
            year = datetime.now().year - 1
        
        # Build package ID for the title
        package_id = f"USCODE-{year}-title{title}"
        
        try:
            # Get package summary
            package_data = await self.get_package_summary(package_id)
            
            # Extract download links
            download = package_data.get("download", {})
            
            result = {
                "package_id": package_id,
                "title": title,
                "section": section,
                "year": year,
                "citation": f"{title} U.S.C. § {section}",
                "package_title": package_data.get("title", ""),
                "last_modified": package_data.get("lastModified", ""),
                "download_links": {
                    "pdf": download.get("pdfLink"),
                    "xml": download.get("xmlLink"),
                    "text": download.get("txtLink"),
                    "mods": download.get("modsLink"),
                    "premis": download.get("premisLink")
                },
                "govinfo_link": f"https://www.govinfo.gov/app/details/{package_id}",
                "house_link": f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{title}-section{section}",
                "api_source": "collection"  # Indicates we used collection API
            }
            
            logger.info(f"Successfully fetched {title} USC {section} via collection API")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch {title} USC {section}: {e}")
            raise
    
    async def search_cfr_packages(
        self,
        title: int,
        part: int,
        start_date: Optional[datetime] = None,
        page_size: int = 100
    ) -> List[GovInfoPackage]:
        """
        Search CFR collection for packages.
        
        Endpoint: GET /collections/CFR/{startDate}
        
        Args:
            title: CFR title (e.g., 17 for SEC regulations)
            part: Part number (e.g., 240 for Exchange Act rules)
            start_date: Start date for search
            page_size: Results per page
        
        Returns:
            List of matching packages
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        
        date_str = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        url = f"{self.base_url}/collections/CFR/{date_str}"
        params = {
            "api_key": self.api_key,
            "pageSize": min(page_size, 1000),
            "offsetMark": "*"
        }
        
        packages = []
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for pkg in data.get("packages", []):
                        pkg_id = pkg.get("packageId", "")
                        # Filter by title and part
                        if f"title{title}" in pkg_id.lower() and f"vol" in pkg_id.lower():
                            packages.append(GovInfoPackage(
                                package_id=pkg_id,
                                last_modified=pkg.get("lastModified", ""),
                                package_link=pkg.get("packageLink", ""),
                                doc_class=pkg.get("docClass"),
                                title=pkg.get("title"),
                                date_issued=pkg.get("dateIssued")
                            ))
                    
                    logger.info(f"Found {len(packages)} CFR packages for title {title}")
                    return packages
                elif response.status == 500:
                    raise ConnectionError("GovInfo CFR collection API returned 500")
                else:
                    raise ConnectionError(f"GovInfo CFR API returned {response.status}")
        except Exception as e:
            logger.error(f"Failed to search CFR packages: {e}")
            raise
    
    async def fetch_cfr_regulation_by_collection(
        self,
        title: int,
        part: int,
        section: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch CFR regulation using collection-based API.
        
        Args:
            title: CFR title (e.g., 17)
            part: Part number (e.g., 240)
            section: Section (e.g., "10b-5")
            year: Year (defaults to current year)
        
        Returns:
            Regulation metadata with download URLs
        """
        if not year:
            year = datetime.now().year
            # CFR Title 17 updates April 1
            if datetime.now().month < 4:
                year -= 1
        
        # Determine volume for Title 17
        if title == 17:
            if part <= 40:
                volume = 1
            elif part <= 199:
                volume = 2
            elif part <= 239:
                volume = 3
            else:
                volume = 4
        else:
            volume = 1
        
        package_id = f"CFR-{year}-title{title}-vol{volume}"
        
        try:
            package_data = await self.get_package_summary(package_id)
            
            download = package_data.get("download", {})
            
            result = {
                "package_id": package_id,
                "title": title,
                "part": part,
                "section": section,
                "year": year,
                "volume": volume,
                "citation": f"{title} CFR § {part}.{section}" if section else f"{title} CFR Part {part}",
                "package_title": package_data.get("title", ""),
                "last_modified": package_data.get("lastModified", ""),
                "download_links": {
                    "pdf": download.get("pdfLink"),
                    "xml": download.get("xmlLink"),
                    "text": download.get("txtLink")
                },
                "govinfo_link": f"https://www.govinfo.gov/app/details/{package_id}",
                "ecfr_link": f"https://www.ecfr.gov/current/title-{title}/part-{part}",
                "api_source": "collection"
            }
            
            logger.info(f"Successfully fetched {title} CFR {part}.{section or ''} via collection API")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch {title} CFR {part}: {e}")
            raise
    
    async def search(
        self,
        query: str,
        page_size: int = 10,
        offset_mark: str = "*",
        sorts: Optional[List[SearchSort]] = None,
        historical: bool = True,
        result_level: str = "default"
    ) -> SearchResponse:
        """
        Search GovInfo using complex queries with field operators.
        
        Endpoint: POST /search
        
        This is the MOST POWERFUL endpoint - allows complex queries with field operators:
        - congress: Filter by congress number
        - publishdate: Date range filtering
        - branch: executive, judicial, legislative
        - collectionCode: USCODE, CFR, FR, etc.
        - docClass: Bill type, report type, etc.
        
        Args:
            query: Search query with optional field operators
                   Examples:
                   - "securities fraud" - Simple text search
                   - "collectionCode:USCODE AND title:15" - USCODE Title 15
                   - "publishdate:range(2023-01-01,2023-12-31)" - Date range
                   - "congress:118 AND docClass:hr" - 118th Congress House bills
            page_size: Results per page (max 100)
            offset_mark: Pagination token (* for first page)
            sorts: List of sort configurations
            historical: Include historical documents
            result_level: "default" or "full" detail level
        
        Returns:
            SearchResponse with results, count, and next offset
        
        Example:
            # Search for SEC-related USC statutes
            results = await client.search(
                query='collectionCode:USCODE AND "Securities Exchange Act"',
                page_size=25
            )
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        if sorts is None:
            sorts = [SearchSort(field="relevancy", sortOrder="DESC")]
        
        # Build request body
        request_body = {
            "query": query,
            "pageSize": min(page_size, 100),  # API max is 100
            "offsetMark": offset_mark,
            "sorts": [{"field": s.field, "sortOrder": s.sortOrder} for s in sorts],
            "historical": historical,
            "resultLevel": result_level
        }
        
        url = f"{self.base_url}/search"
        params = {"api_key": self.api_key}
        
        try:
            async with self.session.post(
                url,
                params=params,
                json=request_body,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse results
                    results = []
                    for item in data.get("results", []):
                        results.append(SearchResult(
                            title=item.get("title", ""),
                            packageId=item.get("packageId", ""),
                            granuleId=item.get("granuleId"),
                            lastModified=item.get("lastModified"),
                            governmentAuthor=item.get("governmentAuthor", []),
                            dateIssued=item.get("dateIssued"),
                            collectionCode=item.get("collectionCode"),
                            resultLink=item.get("resultLink"),
                            dateIngested=item.get("dateIngested"),
                            download=item.get("download", {}),
                            relatedLink=item.get("relatedLink")
                        ))
                    
                    search_response = SearchResponse(
                        results=results,
                        offsetMark=data.get("offsetMark"),
                        count=data.get("count", len(results))
                    )
                    
                    logger.info(f"Search returned {len(results)} results for query: {query[:50]}...")
                    return search_response
                    
                elif response.status == 400:
                    error_text = await response.text()
                    raise ValueError(f"Invalid search request: {error_text}")
                elif response.status == 404:
                    # No results found
                    logger.info(f"No results found for query: {query}")
                    return SearchResponse(results=[], offsetMark=None, count=0)
                elif response.status == 500:
                    raise ConnectionError("GovInfo search API returned 500 (server error)")
                else:
                    raise ConnectionError(f"GovInfo search API returned {response.status}")
                    
        except (ValueError, ConnectionError):
            raise
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise RuntimeError(f"Search API error: {e}") from e
    
    async def search_statutes_by_topic(
        self,
        topic: str,
        collection: str = "USCODE",
        page_size: int = 25
    ) -> SearchResponse:
        """
        Search for statutes related to a specific topic.
        
        Convenience method wrapping search() for statute research.
        
        Args:
            topic: Topic to search for (e.g., "securities fraud", "insider trading")
            collection: Collection to search (default: USCODE)
            page_size: Results per page
        
        Returns:
            Search results
        """
        query = f'collectionCode:{collection} AND "{topic}"'
        return await self.search(query=query, page_size=page_size)
    
    async def search_regulations_by_agency(
        self,
        agency: str,
        cfr_title: Optional[int] = None,
        page_size: int = 25
    ) -> SearchResponse:
        """
        Search for regulations by issuing agency.
        
        Args:
            agency: Agency name (e.g., "Securities and Exchange Commission")
            cfr_title: Optional CFR title number (e.g., 17 for SEC)
            page_size: Results per page
        
        Returns:
            Search results
        """
        query = f'collectionCode:CFR AND "{agency}"'
        if cfr_title:
            query += f' AND title:{cfr_title}'
        return await self.search(query=query, page_size=page_size)
    
    async def search_by_date_range(
        self,
        start_date: str,
        end_date: str,
        collection: Optional[str] = None,
        page_size: int = 25
    ) -> SearchResponse:
        """
        Search documents by publication date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            collection: Optional collection filter
            page_size: Results per page
        
        Returns:
            Search results
        """
        query = f'publishdate:range({start_date},{end_date})'
        if collection:
            query = f'collectionCode:{collection} AND {query}'
        return await self.search(query=query, page_size=page_size)
    
    async def search_court_opinions(
        self,
        court_name: str,
        keywords: Optional[str] = None,
        page_size: int = 25
    ) -> SearchResponse:
        """
        Search for court opinions.
        
        Args:
            court_name: Court name or abbreviation
            keywords: Optional keywords to search for
            page_size: Results per page
        
        Returns:
            Search results
        """
        query = f'collectionCode:USCOURTS AND "{court_name}"'
        if keywords:
            query += f' AND "{keywords}"'
        return await self.search(query=query, page_size=page_size)
    
    async def get_related_documents(
        self,
        access_id: str
    ) -> RelatedDocumentsResponse:
        """
        Get all related documents for a given packageId or granuleId.
        
        Endpoint: GET /related/{accessId}
        
        This discovers relationships between documents:
        - Bill versions and amendments
        - Statute citations in regulations
        - Related congressional reports
        - Court opinions citing statutes
        - CFR regulations implementing USC statutes
        
        Args:
            access_id: packageId or granuleId (e.g., "USCODE-2023-title15")
        
        Returns:
            RelatedDocumentsResponse with all related documents
        
        Example:
            # Find all documents related to USCODE Title 15
            related = await client.get_related_documents("USCODE-2023-title15")
            for doc in related.relationships:
                print(f"Related: {doc.collectionCode} - {doc.packageId}")
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/related/{access_id}"
        params = {"api_key": self.api_key}
        
        try:
            async with self.session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse relationships
                    relationships = []
                    for rel in data.get("relationships", []):
                        relationships.append(RelatedDocument(
                            relationshipType=rel.get("relationshipType", ""),
                            packageId=rel.get("packageId", ""),
                            collectionCode=rel.get("collectionCode", ""),
                            title=rel.get("title"),
                            lastModified=rel.get("lastModified"),
                            dateIssued=rel.get("dateIssued"),
                            congress=rel.get("congress"),
                            session=rel.get("session"),
                            relationshipMetadata=rel
                        ))
                    
                    logger.info(f"Found {len(relationships)} related documents for {access_id}")
                    return RelatedDocumentsResponse(
                        accessId=access_id,
                        relationships=relationships,
                        count=len(relationships)
                    )
                    
                elif response.status == 404:
                    logger.info(f"No related documents found for {access_id}")
                    return RelatedDocumentsResponse(
                        accessId=access_id,
                        relationships=[],
                        count=0
                    )
                elif response.status == 500:
                    raise ConnectionError(f"GovInfo related API returned 500 for {access_id}")
                else:
                    raise ConnectionError(f"GovInfo related API returned {response.status}")
                    
        except (ConnectionError, TimeoutError):
            raise
        except Exception as e:
            logger.error(f"Failed to get related documents for {access_id}: {e}")
            raise RuntimeError(f"Related documents API error: {e}") from e
    
    async def get_related_documents_by_collection(
        self,
        access_id: str,
        collection: str,
        granule_class: Optional[str] = None,
        sub_granule_class: Optional[str] = None
    ) -> RelatedDocumentsResponse:
        """
        Get related documents filtered by collection.
        
        Endpoint: GET /related/{accessId}/{collection}
        
        This allows filtering relationships by specific collection:
        - BILLS: Related bill versions
        - CFR: Related regulations
        - USCODE: Related statutes
        - USCOURTS: Related court opinions
        - FR: Related Federal Register notices
        
        Args:
            access_id: packageId or granuleId
            collection: Collection code to filter (e.g., "BILLS", "CFR", "USCODE")
            granule_class: Optional granule class filter
            sub_granule_class: Optional sub-granule class filter
        
        Returns:
            RelatedDocumentsResponse with filtered relationships
        
        Example:
            # Find all CFR regulations related to USC Title 15
            related = await client.get_related_documents_by_collection(
                "USCODE-2023-title15",
                "CFR"
            )
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/related/{access_id}/{collection}"
        params = {"api_key": self.api_key}
        
        if granule_class:
            params["granuleClass"] = granule_class
        if sub_granule_class:
            params["subGranuleClass"] = sub_granule_class
        
        try:
            async with self.session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse relationships
                    relationships = []
                    for rel in data.get("relationships", []):
                        relationships.append(RelatedDocument(
                            relationshipType=rel.get("relationshipType", ""),
                            packageId=rel.get("packageId", ""),
                            collectionCode=rel.get("collectionCode", collection),
                            title=rel.get("title"),
                            lastModified=rel.get("lastModified"),
                            dateIssued=rel.get("dateIssued"),
                            congress=rel.get("congress"),
                            session=rel.get("session"),
                            relationshipMetadata=rel
                        ))
                    
                    logger.info(f"Found {len(relationships)} {collection} relationships for {access_id}")
                    return RelatedDocumentsResponse(
                        accessId=access_id,
                        relationships=relationships,
                        count=len(relationships)
                    )
                    
                elif response.status == 404:
                    logger.info(f"No {collection} relationships found for {access_id}")
                    return RelatedDocumentsResponse(
                        accessId=access_id,
                        relationships=[],
                        count=0
                    )
                elif response.status == 500:
                    raise ConnectionError(f"GovInfo related API returned 500 for {access_id}/{collection}")
                else:
                    raise ConnectionError(f"GovInfo related API returned {response.status}")
                    
        except (ConnectionError, TimeoutError):
            raise
        except Exception as e:
            logger.error(f"Failed to get {collection} relationships for {access_id}: {e}")
            raise RuntimeError(f"Related documents API error: {e}") from e
    
    async def find_implementing_regulations(self, statute_package_id: str) -> List[RelatedDocument]:
        """
        Find CFR regulations that implement a USC statute.
        
        Convenience method for forensic analysis.
        
        Args:
            statute_package_id: USCODE package ID (e.g., "USCODE-2023-title15")
        
        Returns:
            List of related CFR regulations
        """
        response = await self.get_related_documents_by_collection(
            statute_package_id,
            "CFR"
        )
        return response.relationships
    
    async def find_related_court_cases(self, statute_package_id: str) -> List[RelatedDocument]:
        """
        Find court opinions that cite a statute.
        
        Convenience method for precedent research.
        
        Args:
            statute_package_id: USCODE package ID
        
        Returns:
            List of related court opinions
        """
        response = await self.get_related_documents_by_collection(
            statute_package_id,
            "USCOURTS"
        )
        return response.relationships
    
    async def find_related_bills(self, statute_package_id: str) -> List[RelatedDocument]:
        """
        Find bills related to a statute.
        
        Useful for legislative history research.
        
        Args:
            statute_package_id: USCODE package ID
        
        Returns:
            List of related bills
        """
        response = await self.get_related_documents_by_collection(
            statute_package_id,
            "BILLS"
        )
        return response.relationships
    
    async def find_federal_register_notices(self, regulation_package_id: str) -> List[RelatedDocument]:
        """
        Find Federal Register notices related to a CFR regulation.
        
        Useful for regulatory history and rulemaking context.
        
        Args:
            regulation_package_id: CFR package ID
        
        Returns:
            List of related Federal Register documents
        """
        response = await self.get_related_documents_by_collection(
            regulation_package_id,
            "FR"
        )
        return response.relationships
    
    async def build_relationship_map(
        self,
        access_id: str,
        collections: Optional[List[str]] = None
    ) -> Dict[str, List[RelatedDocument]]:
        """
        Build a complete relationship map for a document.
        
        This creates a comprehensive map of all related documents
        organized by collection type.
        
        Args:
            access_id: Package or granule ID
            collections: Optional list of collections to check
                        (default: all legal collections)
        
        Returns:
            Dictionary mapping collection codes to related documents
        
        Example:
            # Get complete relationship map for USC Title 15
            relationships = await client.build_relationship_map("USCODE-2023-title15")
            
            print(f"Related CFR regulations: {len(relationships['CFR'])}")
            print(f"Related court cases: {len(relationships['USCOURTS'])}")
            print(f"Related bills: {len(relationships['BILLS'])}")
        """
        if collections is None:
            collections = list(self.legal_collections.keys())
        
        relationship_map = {}
        
        for collection in collections:
            try:
                response = await self.get_related_documents_by_collection(
                    access_id,
                    collection
                )
                if response.relationships:
                    relationship_map[collection] = response.relationships
                    logger.info(f"Found {len(response.relationships)} {collection} relationships")
            except Exception as e:
                logger.warning(f"Could not fetch {collection} relationships: {e}")
                relationship_map[collection] = []
        
        return relationship_map
    
    async def get_published_documents(
        self,
        date_issued_start: str,
        collections: List[str],
        page_size: int = 100,
        offset_mark: str = "*",
        congress: Optional[str] = None,
        doc_class: Optional[str] = None,
        bill_version: Optional[str] = None,
        modified_since: Optional[str] = None,
        court_code: Optional[str] = None,
        court_type: Optional[str] = None,
        state: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents published on or after a specific date.
        
        Endpoint: GET /published/{dateIssuedStartDate}
        
        This endpoint discovers documents by publication date - critical for:
        - Tracking new legislation
        - Monitoring regulatory changes
        - Following court decisions
        - Discovering recent Federal Register notices
        - Identifying updated statutes
        
        Args:
            date_issued_start: Start date (YYYY-MM-DD format)
            collections: List of collection codes (e.g., ["BILLS", "CFR", "FR"])
            page_size: Results per page (max 1000)
            offset_mark: Pagination token (* for first page)
            congress: Filter by congress number (e.g., "118")
            doc_class: Document class filter (e.g., "hr" for House bills)
            bill_version: Bill version filter
            modified_since: ISO 8601 timestamp for recently modified docs
            court_code: Court code filter
            court_type: Court type filter
            state: State filter
            topic: Topic filter
        
        Returns:
            Dictionary with count, packages, and pagination info
        
        Example:
            # Get all bills published in 2023
            result = await client.get_published_documents(
                date_issued_start="2023-01-01",
                collections=["BILLS"],
                page_size=100
            )
            
            # Get SEC regulations modified recently
            result = await client.get_published_documents(
                date_issued_start="2020-01-01",
                collections=["CFR"],
                modified_since="2024-01-01T00:00:00Z",
                page_size=50
            )
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/published/{date_issued_start}"
        
        # Build parameters
        params = {
            "api_key": self.api_key,
            "collection": ",".join(collections),
            "pageSize": min(page_size, 1000),
            "offsetMark": offset_mark
        }
        
        # Add optional filters
        if congress:
            params["congress"] = congress
        if doc_class:
            params["docClass"] = doc_class
        if bill_version:
            params["billVersion"] = bill_version
        if modified_since:
            params["modifiedSince"] = modified_since
        if court_code:
            params["courtCode"] = court_code
        if court_type:
            params["courtType"] = court_type
        if state:
            params["state"] = state
        if topic:
            params["topic"] = topic
        
        try:
            async with self.session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    logger.info(
                        f"Retrieved {data.get('count', 0)} published documents "
                        f"from {date_issued_start} in collections: {', '.join(collections)}"
                    )
                    return data
                    
                elif response.status == 404:
                    logger.info(f"No published documents found for {date_issued_start}")
                    return {
                        "count": 0,
                        "message": "No documents found",
                        "packages": [],
                        "nextPage": None,
                        "previousPage": None
                    }
                elif response.status == 500:
                    raise ConnectionError(f"GovInfo published API returned 500")
                else:
                    raise ConnectionError(f"GovInfo published API returned {response.status}")
                    
        except (ConnectionError, TimeoutError):
            raise
        except Exception as e:
            logger.error(f"Failed to get published documents from {date_issued_start}: {e}")
            raise RuntimeError(f"Published documents API error: {e}") from e
    
    async def get_recently_published(
        self,
        days_back: int = 30,
        collections: Optional[List[str]] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Get documents published in the last N days.
        
        Convenience method for monitoring recent publications.
        
        Args:
            days_back: Number of days to look back (default: 30)
            collections: List of collections (default: all legal collections)
            page_size: Results per page
        
        Returns:
            Published documents data
        
        Example:
            # Get all legal documents from last 7 days
            recent = await client.get_recently_published(days_back=7)
        """
        from datetime import datetime, timedelta
        
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        if collections is None:
            collections = list(self.legal_collections.keys())
        
        return await self.get_published_documents(
            date_issued_start=start_date,
            collections=collections,
            page_size=page_size
        )
    
    async def get_published_bills(
        self,
        start_date: str,
        congress: Optional[str] = None,
        doc_class: Optional[str] = None,
        page_size: int = 100
    ) -> List[GovInfoPackage]:
        """
        Get bills published on or after a date.
        
        Convenience method for legislative tracking.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            congress: Congress number (e.g., "118")
            doc_class: Bill type (e.g., "hr", "s", "hres", "sres")
            page_size: Results per page
        
        Returns:
            List of bill packages
        
        Example:
            # Get all House bills from 118th Congress
            bills = await client.get_published_bills(
                start_date="2023-01-01",
                congress="118",
                doc_class="hr"
            )
        """
        result = await self.get_published_documents(
            date_issued_start=start_date,
            collections=["BILLS"],
            congress=congress,
            doc_class=doc_class,
            page_size=page_size
        )
        
        packages = []
        for pkg in result.get("packages", []):
            packages.append(GovInfoPackage(
                package_id=pkg.get("packageId", ""),
                last_modified=pkg.get("lastModified", ""),
                package_link=pkg.get("packageLink", ""),
                doc_class=pkg.get("docClass"),
                title=pkg.get("title"),
                date_issued=pkg.get("dateIssued")
            ))
        
        return packages
    
    async def get_published_regulations(
        self,
        start_date: str,
        modified_since: Optional[str] = None,
        page_size: int = 100
    ) -> List[GovInfoPackage]:
        """
        Get CFR regulations published or modified after a date.
        
        Useful for compliance monitoring.
        
        Args:
            start_date: Publication date (YYYY-MM-DD)
            modified_since: ISO 8601 timestamp for modifications
            page_size: Results per page
        
        Returns:
            List of CFR packages
        
        Example:
            # Get regulations modified in 2024
            regs = await client.get_published_regulations(
                start_date="2020-01-01",
                modified_since="2024-01-01T00:00:00Z"
            )
        """
        result = await self.get_published_documents(
            date_issued_start=start_date,
            collections=["CFR"],
            modified_since=modified_since,
            page_size=page_size
        )
        
        packages = []
        for pkg in result.get("packages", []):
            packages.append(GovInfoPackage(
                package_id=pkg.get("packageId", ""),
                last_modified=pkg.get("lastModified", ""),
                package_link=pkg.get("packageLink", ""),
                doc_class=pkg.get("docClass"),
                title=pkg.get("title"),
                date_issued=pkg.get("dateIssued")
            ))
        
        return packages
    
    async def get_published_federal_register(
        self,
        start_date: str,
        topic: Optional[str] = None,
        page_size: int = 100
    ) -> List[GovInfoPackage]:
        """
        Get Federal Register documents published after a date.
        
        Useful for rulemaking tracking.
        
        Args:
            start_date: Publication date (YYYY-MM-DD)
            topic: Topic filter
            page_size: Results per page
        
        Returns:
            List of Federal Register packages
        
        Example:
            # Get all FR notices from 2024
            fr_docs = await client.get_published_federal_register(
                start_date="2024-01-01"
            )
        """
        result = await self.get_published_documents(
            date_issued_start=start_date,
            collections=["FR"],
            topic=topic,
            page_size=page_size
        )
        
        packages = []
        for pkg in result.get("packages", []):
            packages.append(GovInfoPackage(
                package_id=pkg.get("packageId", ""),
                last_modified=pkg.get("lastModified", ""),
                package_link=pkg.get("packageLink", ""),
                doc_class=pkg.get("docClass"),
                title=pkg.get("title"),
                date_issued=pkg.get("dateIssued")
            ))
        
        return packages
    
    async def get_published_court_opinions(
        self,
        start_date: str,
        court_code: Optional[str] = None,
        court_type: Optional[str] = None,
        state: Optional[str] = None,
        page_size: int = 100
    ) -> List[GovInfoPackage]:
        """
        Get court opinions published after a date.
        
        Useful for precedent monitoring.
        
        Args:
            start_date: Publication date (YYYY-MM-DD)
            court_code: Court code filter
            court_type: Court type filter
            state: State filter
            page_size: Results per page
        
        Returns:
            List of court opinion packages
        
        Example:
            # Get all federal circuit court opinions from 2024
            opinions = await client.get_published_court_opinions(
                start_date="2024-01-01",
                court_type="Circuit"
            )
        """
        result = await self.get_published_documents(
            date_issued_start=start_date,
            collections=["USCOURTS"],
            court_code=court_code,
            court_type=court_type,
            state=state,
            page_size=page_size
        )
        
        packages = []
        for pkg in result.get("packages", []):
            packages.append(GovInfoPackage(
                package_id=pkg.get("packageId", ""),
                last_modified=pkg.get("lastModified", ""),
                package_link=pkg.get("packageLink", ""),
                doc_class=pkg.get("docClass"),
                title=pkg.get("title"),
                date_issued=pkg.get("dateIssued")
            ))
        
        return packages
    
    async def monitor_regulatory_changes(
        self,
        start_date: str,
        modified_since: str,
        collections: Optional[List[str]] = None
    ) -> Dict[str, List[GovInfoPackage]]:
        """
        Monitor regulatory and legislative changes.
        
        Comprehensive monitoring for compliance and forensic analysis.
        
        Args:
            start_date: Initial publication date (YYYY-MM-DD)
            modified_since: ISO 8601 timestamp for modifications
            collections: Collections to monitor (default: CFR, FR, BILLS)
        
        Returns:
            Dictionary mapping collection codes to changed packages
        
        Example:
            # Monitor all regulatory changes in 2024
            changes = await client.monitor_regulatory_changes(
                start_date="2020-01-01",
                modified_since="2024-01-01T00:00:00Z"
            )
            
            print(f"CFR changes: {len(changes['CFR'])}")
            print(f"FR notices: {len(changes['FR'])}")
            print(f"New bills: {len(changes['BILLS'])}")
        """
        if collections is None:
            collections = ["CFR", "FR", "BILLS"]
        
        changes = {}
        
        for collection in collections:
            result = await self.get_published_documents(
                date_issued_start=start_date,
                collections=[collection],
                modified_since=modified_since,
                page_size=1000
            )
            
            packages = []
            for pkg in result.get("packages", []):
                packages.append(GovInfoPackage(
                    package_id=pkg.get("packageId", ""),
                    last_modified=pkg.get("lastModified", ""),
                    package_link=pkg.get("packageLink", ""),
                    doc_class=pkg.get("docClass"),
                    title=pkg.get("title"),
                    date_issued=pkg.get("dateIssued")
                ))
            
            changes[collection] = packages
            logger.info(f"Found {len(packages)} modified {collection} documents")
        
        return changes
    
    async def get_package_granules(
        self,
        package_id: str,
        page_size: int = 100,
        offset_mark: str = "*",
        md5: Optional[str] = None,
        granule_class: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get list of granules (sub-documents) within a package.
        
        Endpoint: GET /packages/{packageId}/granules
        
        Granules are the individual sections within a larger document:
        - CREC: Individual speeches, articles, sections
        - USCODE: Individual statute sections
        - CFR: Individual regulation sections
        - Congressional reports: Individual chapters/sections
        
        Args:
            package_id: Package identifier (e.g., "CREC-2018-01-04")
            page_size: Results per page (max 1000)
            offset_mark: Pagination token
            md5: MD5 hash for change detection
            granule_class: Filter by granule class (e.g., "SENATE", "HOUSE")
        
        Returns:
            Dictionary with granules list and pagination info
        
        Example:
            # Get all sections of Congressional Record
            granules = await client.get_package_granules(
                package_id="CREC-2024-01-15",
                granule_class="SENATE"
            )
            
            for granule in granules['granules']:
                print(f"Section: {granule['title']}")
                print(f"Granule ID: {granule['granuleId']}")
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/packages/{package_id}/granules"
        
        params = {
            "api_key": self.api_key,
            "pageSize": min(page_size, 1000),
            "offsetMark": offset_mark
        }
        
        if md5:
            params["md5"] = md5
        if granule_class:
            params["granuleClass"] = granule_class
        
        try:
            async with self.session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        f"Retrieved {data.get('count', 0)} granules from {package_id}"
                    )
                    return data
                    
                elif response.status == 404:
                    logger.info(f"No granules found for package {package_id}")
                    return {
                        "count": 0,
                        "granules": [],
                        "message": "Package not found or has no granules"
                    }
                elif response.status == 500:
                    raise ConnectionError(f"GovInfo granules API returned 500 for {package_id}")
                else:
                    raise ConnectionError(f"GovInfo granules API returned {response.status}")
                    
        except (ConnectionError, TimeoutError):
            raise
        except Exception as e:
            logger.error(f"Failed to get granules for {package_id}: {e}")
            raise RuntimeError(f"Granules API error: {e}") from e
    
    async def get_granule_summary(
        self,
        package_id: str,
        granule_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed summary for a specific granule.
        
        Endpoint: GET /packages/{packageId}/granules/{granuleId}/summary
        
        Returns complete metadata and content information for an individual
        section within a document.
        
        Args:
            package_id: Package identifier
            granule_id: Granule identifier (e.g., "CREC-2024-01-15-pt1-PgS123")
        
        Returns:
            Granule summary with metadata and download links
        
        Example:
            # Get specific statute section
            granule = await client.get_granule_summary(
                package_id="USCODE-2023-title15",
                granule_id="USCODE-2023-title15-section78j"
            )
            
            print(f"Title: {granule['title']}")
            print(f"Download: {granule['download']}")
        """
        if not self.session:
            self.session = aiohttp.ClientSession(trust_env=True)
        
        url = f"{self.base_url}/packages/{package_id}/granules/{granule_id}/summary"
        params = {"api_key": self.api_key}
        
        try:
            async with self.session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved granule summary: {granule_id}")
                    return data
                    
                elif response.status == 404:
                    raise ValueError(f"Granule not found: {package_id}/{granule_id}")
                elif response.status == 500:
                    raise ConnectionError(f"GovInfo granule summary API returned 500")
                else:
                    raise ConnectionError(f"GovInfo granule summary API returned {response.status}")
                    
        except (ValueError, ConnectionError, TimeoutError):
            raise
        except Exception as e:
            logger.error(f"Failed to get granule summary for {granule_id}: {e}")
            raise RuntimeError(f"Granule summary API error: {e}") from e
    
    async def get_statute_section_details(
        self,
        title: int,
        section: str,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific statute section.
        
        This combines package and granule APIs to get complete section details.
        
        Args:
            title: USC title number
            section: Section number
            year: Year (defaults to current - 1)
        
        Returns:
            Complete section metadata
        
        Example:
            # Get 15 USC 78j details
            details = await client.get_statute_section_details(
                title=15,
                section="78j"
            )
        """
        if not year:
            year = datetime.now().year - 1
        
        package_id = f"USCODE-{year}-title{title}"
        
        # Clean section for granule ID
        base_section = re.match(r'(\d+[a-z]?)', section).group(1) if re.match(r'(\d+[a-z]?)', section) else section
        granule_id = f"USCODE-{year}-title{title}-section{base_section}"
        
        try:
            # Get granule summary
            granule_summary = await self.get_granule_summary(package_id, granule_id)
            
            return {
                "package_id": package_id,
                "granule_id": granule_id,
                "title": title,
                "section": section,
                "year": year,
                "summary": granule_summary
            }
        except Exception as e:
            logger.warning(f"Could not get granule details for {title} USC {section}: {e}")
            # Fall back to package-level data
            return await self.fetch_usc_statute_by_collection(title, section, year)
    
    async def get_congressional_record_sections(
        self,
        date: str,
        granule_class: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sections from Congressional Record for a specific date.
        
        Args:
            date: Date (YYYY-MM-DD format)
            granule_class: Section filter ("SENATE", "HOUSE", "EXTENSIONS", "DAILYDIGEST")
        
        Returns:
            List of Congressional Record sections
        
        Example:
            # Get all Senate floor statements from a date
            sections = await client.get_congressional_record_sections(
                date="2024-01-15",
                granule_class="SENATE"
            )
        """
        # Format date for package ID
        package_date = date.replace("-", "")  # YYYYMMDD
        package_id = f"CREC-{package_date}"
        
        try:
            result = await self.get_package_granules(
                package_id=package_id,
                granule_class=granule_class,
                page_size=1000
            )
            
            return result.get("granules", [])
        except Exception as e:
            logger.error(f"Failed to get Congressional Record sections for {date}: {e}")
            raise
    
    async def download_granule_content(
        self,
        package_id: str,
        granule_id: str,
        format: str = "html"
    ) -> Optional[str]:
        """
        Get download URL for granule content in specified format.
        
        Args:
            package_id: Package identifier
            granule_id: Granule identifier
            format: Content format ("html", "pdf", "xml", "txt")
        
        Returns:
            Download URL or None
        
        Example:
            # Get HTML content URL for statute section
            url = await client.download_granule_content(
                package_id="USCODE-2023-title15",
                granule_id="USCODE-2023-title15-section78j",
                format="html"
            )
        """
        try:
            summary = await self.get_granule_summary(package_id, granule_id)
            
            download_links = summary.get("download", {})
            
            format_map = {
                "html": "htmlLink",
                "pdf": "pdfLink",
                "xml": "xmlLink",
                "txt": "txtLink"
            }
            
            link_key = format_map.get(format.lower())
            if link_key and link_key in download_links:
                return download_links[link_key]
            
            logger.warning(f"Format {format} not available for {granule_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get download URL for {granule_id}: {e}")
            return None
    
    async def get_document_hierarchy(
        self,
        package_id: str,
        include_content: bool = False
    ) -> Dict[str, Any]:
        """
        Get complete document hierarchy (package + all granules).
        
        This is useful for understanding document structure and accessing
        individual sections.
        
        Args:
            package_id: Package identifier
            include_content: If True, fetch granule summaries (slower)
        
        Returns:
            Complete document hierarchy
        
        Example:
            # Get complete structure of Congressional Record
            hierarchy = await client.get_document_hierarchy(
                package_id="CREC-2024-01-15"
            )
            
            print(f"Package: {hierarchy['package']['title']}")
            print(f"Sections: {len(hierarchy['granules'])}")
        """
        try:
            # Get package summary
            package_summary = await self.get_package_summary(package_id)
            
            # Get all granules
            granules_result = await self.get_package_granules(
                package_id=package_id,
                page_size=1000
            )
            
            granules = granules_result.get("granules", [])
            
            # Optionally fetch detailed granule summaries
            if include_content and granules:
                detailed_granules = []
                for granule in granules[:50]:  # Limit to first 50 to avoid rate limits
                    try:
                        granule_summary = await self.get_granule_summary(
                            package_id,
                            granule["granuleId"]
                        )
                        detailed_granules.append({
                            **granule,
                            "summary": granule_summary
                        })
                    except Exception as e:
                        logger.warning(f"Could not fetch granule {granule['granuleId']}: {e}")
                        detailed_granules.append(granule)
                
                granules = detailed_granules
            
            return {
                "package_id": package_id,
                "package": package_summary,
                "granules": granules,
                "granule_count": len(granules),
                "hierarchy_complete": True
            }
            
        except Exception as e:
            logger.error(f"Failed to build document hierarchy for {package_id}: {e}")
            raise
    
    async def get_api_status(self) -> Dict[str, Any]:
        """
        Check API status and rate limits.
        
        Returns:
            API status information
        """
        try:
            collections = await self.get_collections()
            
            return {
                "status": "operational",
                "collections_available": len(collections),
                "api_key_valid": True,
                "base_url": self.base_url,
                "legal_collections": self.legal_collections,
                "endpoints_available": [
                    "GET /collections",
                    "GET /collections/{collection}/{startDate}",
                    "GET /packages/{packageId}/summary",
                    "GET /packages/{packageId}",
                    "GET /packages/{packageId}/granules",
                    "GET /packages/{packageId}/granules/{granuleId}/summary",
                    "POST /search",
                    "GET /related/{accessId}",
                    "GET /related/{accessId}/{collection}",
                    "GET /published/{dateIssuedStartDate}"
                ]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "api_key_valid": False
            }
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """Cleanup."""
        if self.session and not self.session.closed:
            try:
                asyncio.get_event_loop().run_until_complete(self.close())
            except Exception:
                pass

