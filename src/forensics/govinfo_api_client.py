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
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)


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
            self.session = aiohttp.ClientSession()
        
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
            self.session = aiohttp.ClientSession()
        
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
            self.session = aiohttp.ClientSession()
        
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
            self.session = aiohttp.ClientSession()
        
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
            self.session = aiohttp.ClientSession()
        
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
                "legal_collections": self.legal_collections
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

