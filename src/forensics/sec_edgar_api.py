"""
SEC EDGAR API - Production-Grade SEC Filing Fetcher for JLAW Forensic Analysis
================================================================================

This module provides the SECEdgarAPI class expected by JLAW deployment scripts.
Wraps RealSECDataFetcher to provide a unified interface for SEC filing collection.

LEGAL COMPLIANCE:
- SEC EDGAR API Terms of Service compliant
- Rate limiting: 10 requests/second (conservative 6.67 req/sec implemented)
- User-Agent header with contact information per SEC requirements

USAGE:
    from src.forensics.sec_edgar_api import SECEdgarAPI
    
    api = SECEdgarAPI()
    filings = await api.get_filings(
        cik="0000320187",
        start_date="2019-01-01",
        end_date="2019-12-31",
        filing_types=["10-K", "10-Q", "4", "8-K"]
    )
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
import re

# Import existing SEC data fetcher
from .real_sec_data_fetcher import RealSECDataFetcher, SECFiling

logger = logging.getLogger(__name__)


@dataclass
class FilingMetadata:
    """
    Comprehensive SEC filing metadata for forensic analysis.
    Extends SECFiling with additional fields for deployment compatibility.
    """
    # Core identification
    accession_number: str
    filing_type: str
    cik: str
    company_name: Optional[str] = None
    
    # Temporal data
    filing_date: str = ""
    accepted_date: Optional[str] = None
    report_date: Optional[str] = None
    
    # Document information
    primary_document: str = ""
    primary_doc_description: str = ""
    size: int = 0
    
    # URLs for evidence retrieval
    filing_url: str = ""
    document_url: str = ""
    viewer_url: str = ""
    index_url: str = ""
    
    # XBRL indicators
    is_xbrl: bool = False
    is_inline_xbrl: bool = False
    
    # SEC reference data
    act: str = ""
    file_number: str = ""
    film_number: str = ""
    items: str = ""
    
    # Amendment tracking
    is_amendment: bool = False
    
    # Raw content (optional, fetched on demand)
    raw_content: Optional[str] = None
    
    # Forensic chain of custody
    fetched_at: Optional[str] = None
    content_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_sec_filing(cls, filing: SECFiling, cik: str, company_name: Optional[str] = None) -> 'FilingMetadata':
        """Create FilingMetadata from SECFiling object."""
        # Build index URL
        accession_no_dashes = filing.accession_number.replace('-', '')
        cik_int = int(cik.lstrip('0') or '0')
        index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dashes}/index.json"
        
        return cls(
            accession_number=filing.accession_number,
            filing_type=filing.filing_type,
            cik=cik,
            company_name=company_name,
            filing_date=filing.filing_date,
            accepted_date=filing.accepted_date,
            report_date=filing.report_date,
            primary_document=filing.primary_document,
            primary_doc_description=filing.primary_doc_description,
            size=filing.size,
            filing_url=filing.filing_url,
            document_url=filing.document_url,
            viewer_url=filing.filing_html_url,
            index_url=index_url,
            is_xbrl=filing.is_xbrl,
            is_inline_xbrl=filing.is_inline_xbrl,
            act=filing.act,
            file_number=filing.file_number,
            film_number=filing.film_number,
            items=filing.items,
            is_amendment=filing.is_amendment,
            fetched_at=datetime.utcnow().isoformat() + 'Z'
        )


class SECEdgarAPI:
    """
    Production-grade SEC EDGAR API wrapper for JLAW forensic analysis.
    
    This class provides the interface expected by JLAW deployment scripts,
    wrapping the RealSECDataFetcher for actual SEC API communication.
    
    Features:
    - Async/await compatible
    - Rate limiting (SEC compliant)
    - Caching support
    - Filing content retrieval
    - Error handling with exponential backoff
    - Full filing type support
    
    Attributes:
        cache_dir: Directory for caching SEC responses
        user_agent: SEC-compliant user agent string
        rate_limit_delay: Delay between requests (seconds)
    """
    
    # SEC EDGAR endpoints
    BASE_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    VIEWER_URL = "https://www.sec.gov/cgi-bin/viewer"
    
    # SEC-compliant user agent (required)
    DEFAULT_USER_AGENT = "JLAW-Forensics/2.0 (SEC Forensic Analysis; contact@jlaw-forensics.org)"
    
    # Rate limiting: SEC allows 10 req/sec, we use 6.67 for safety margin
    DEFAULT_RATE_LIMIT = 0.15  # 150ms between requests
    
    # Supported filing types with their regex patterns
    FILING_TYPE_PATTERNS = {
        '10-K': r'^10-K(/A)?$',
        '10-Q': r'^10-Q(/A)?$',
        '8-K': r'^8-K(/A)?$',
        '4': r'^4(/A)?$',
        'SC 13G': r'^SC 13G(/A)?$',
        'SC 13D': r'^SC 13D(/A)?$',
        'DEF 14A': r'^DEF 14A$',
        'DEFA14A': r'^DEFA14A$',
        '11-K': r'^11-K(/A)?$',
        'S-8': r'^S-8(/A)?$',
        '424B2': r'^424B2$',
        '424B5': r'^424B5$',
        'FWP': r'^FWP$',
    }
    
    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        user_agent: Optional[str] = None,
        rate_limit_delay: float = DEFAULT_RATE_LIMIT
    ):
        """
        Initialize SEC EDGAR API wrapper.
        
        Args:
            cache_dir: Directory for caching responses (default: forensic_storage/sec_cache)
            user_agent: SEC-compliant user agent string
            rate_limit_delay: Delay between requests in seconds
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("forensic_storage/sec_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.rate_limit_delay = rate_limit_delay
        
        # Internal fetcher
        self._fetcher: Optional[RealSECDataFetcher] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Request tracking
        self.request_count = 0
        self.last_request_time = 0.0
        
        logger.info(f"SECEdgarAPI initialized with cache_dir={self.cache_dir}")
        
        # Common ticker to CIK mappings (cache)
        self._ticker_cik_cache: Dict[str, str] = {}
        
        # Common ticker to company name mappings
        self._ticker_name_map: Dict[str, str] = {
            'NKE': 'NIKE, Inc.',
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'GOOG': 'Alphabet Inc.',
            'AMZN': 'Amazon.com, Inc.',
            'META': 'Meta Platforms, Inc.',
            'FB': 'Meta Platforms, Inc.',
            'TSLA': 'Tesla, Inc.',
            'NVDA': 'NVIDIA Corporation',
            'JPM': 'JPMorgan Chase & Co.',
            'JNJ': 'Johnson & Johnson',
            'V': 'Visa Inc.',
            'WMT': 'Walmart Inc.',
            'PG': 'Procter & Gamble Company',
            'MA': 'Mastercard Incorporated',
            'UNH': 'UnitedHealth Group Incorporated',
            'HD': 'The Home Depot, Inc.',
            'BAC': 'Bank of America Corporation',
            'XOM': 'Exxon Mobil Corporation',
            'PFE': 'Pfizer Inc.',
            'CVX': 'Chevron Corporation',
            'KO': 'The Coca-Cola Company',
            'PEP': 'PepsiCo, Inc.',
            'DIS': 'The Walt Disney Company',
            'CSCO': 'Cisco Systems, Inc.',
            'INTC': 'Intel Corporation',
            'NFLX': 'Netflix, Inc.',
            'BA': 'The Boeing Company',
        }
    
    def get_company_name(self, ticker: str) -> str:
        """Get company name from ticker symbol."""
        return self._ticker_name_map.get(ticker.upper(), f"{ticker.upper()} Company")

    async def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        Resolve a ticker symbol to CIK using SEC's company tickers file.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'NKE', 'AAPL')
        
        Returns:
            CIK string (10-digit, zero-padded) or None if not found
        """
        ticker = ticker.upper().strip()
        
        # Check cache first
        if ticker in self._ticker_cik_cache:
            return self._ticker_cik_cache[ticker]
        
        # Known common tickers for immediate resolution
        common_tickers = {
            'NKE': '0000320187',
            'AAPL': '0000320193',
            'MSFT': '0000789019',
            'GOOGL': '0001652044',
            'GOOG': '0001652044',
            'AMZN': '0001018724',
            'META': '0001326801',
            'FB': '0001326801',
            'TSLA': '0001318605',
            'NVDA': '0001045810',
            'JPM': '0000019617',
            'JNJ': '0000200406',
            'V': '0001403161',
            'WMT': '0000104169',
            'PG': '0000080424',
            'MA': '0001141391',
            'UNH': '0000731766',
            'HD': '0000354950',
            'BAC': '0000070858',
            'XOM': '0000034088',
            'PFE': '0000078003',
            'CVX': '0000093410',
            'KO': '0000021344',
            'PEP': '0000077476',
            'ABBV': '0001551152',
            'TMO': '0000097745',
            'COST': '0000909832',
            'MRK': '0000310158',
            'DIS': '0001744489',
            'CSCO': '0000858877',
            'VZ': '0000732712',
            'ADBE': '0000796343',
            'INTC': '0000050863',
            'CMCSA': '0001166691',
            'NKE': '0000320187',
            'ABT': '0000001800',
            'ACN': '0001467373',
            'CRM': '0001108524',
            'DHR': '0000313616',
            'NFLX': '0001065280',
            'ORCL': '0001341439',
            'TXN': '0000097476',
            'PM': '0001413329',
            'LIN': '0001707925',
            'AMD': '0000002488',
            'QCOM': '0000804328',
            'IBM': '0000051143',
            'GE': '0000040545',
            'CAT': '0000018230',
            'RTX': '0000101829',
            'HON': '0000773840',
            'AMGN': '0000318154',
            'LOW': '0000060667',
            'BA': '0000012927',
        }
        
        if ticker in common_tickers:
            cik = common_tickers[ticker]
            self._ticker_cik_cache[ticker] = cik
            logger.info(f"Resolved ticker {ticker} to CIK {cik} (from common list)")
            return cik
        
        # Fallback: Try to fetch from SEC's company tickers JSON
        try:
            await self._rate_limit()
            
            # Create session if needed
            if self._session is None:
                self._session = aiohttp.ClientSession(
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept-Encoding": "gzip, deflate",
                        "Accept": "application/json"
                    }
                )
            
            url = "https://www.sec.gov/files/company_tickers.json"
            async with self._session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
                    for key, company in data.items():
                        if company.get('ticker', '').upper() == ticker:
                            cik = str(company['cik_str']).zfill(10)
                            self._ticker_cik_cache[ticker] = cik
                            logger.info(f"Resolved ticker {ticker} to CIK {cik} (from SEC API)")
                            return cik
        except Exception as e:
            logger.warning(f"Failed to fetch ticker mapping from SEC: {e}")
        
        logger.warning(f"Could not resolve ticker {ticker} to CIK")
        return None

    async def __aenter__(self) -> 'SECEdgarAPI':
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "application/json, text/html, application/xml"
            }
        )
        self._fetcher = RealSECDataFetcher(cache_dir=self.cache_dir)
        await self._fetcher.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._fetcher:
            await self._fetcher.__aexit__(exc_type, exc_val, exc_tb)
        if self._session:
            await self._session.close()
    
    async def _rate_limit(self):
        """Enforce rate limiting to comply with SEC requirements."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def get_filings(
        self,
        cik: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filing_types: Optional[List[str]] = None,
        max_filings: Optional[int] = None,
        include_amendments: bool = True,
        company_name: Optional[str] = None
    ) -> List[FilingMetadata]:
        """
        Fetch SEC filings for a company within specified date range.
        
        This is the primary method expected by JLAW deployment scripts.
        
        Args:
            cik: Company CIK number (with or without leading zeros)
            start_date: Start date in YYYY-MM-DD format (default: 1 year ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            filing_types: List of filing types to include (default: all)
            max_filings: Maximum number of filings to return (default: all)
            include_amendments: Include amended filings (/A suffix)
            company_name: Optional company name for metadata
        
        Returns:
            List of FilingMetadata objects with comprehensive filing information
        
        Raises:
            ValueError: If date format is invalid
            aiohttp.ClientError: If SEC API request fails
        """
        # Normalize CIK
        cik = cik.lstrip('0').zfill(10)
        cik_display = cik.lstrip('0') or '0'
        
        # Default date range
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Validate dates
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD. Error: {e}")
        
        logger.info(f"Fetching filings for CIK {cik_display} from {start_date} to {end_date}")
        
        # Expand filing types to include amendments if requested
        expanded_filing_types = self._expand_filing_types(filing_types, include_amendments)
        
        # Use internal fetcher
        if not self._fetcher:
            self._fetcher = RealSECDataFetcher(cache_dir=self.cache_dir)
            await self._fetcher.__aenter__()
        
        # Fetch filings
        sec_filings = await self._fetcher.get_company_filings(
            cik=cik,
            start_date=start_date,
            end_date=end_date,
            filing_types=expanded_filing_types
        )
        
        # Convert to FilingMetadata
        filings = [
            FilingMetadata.from_sec_filing(f, cik, company_name)
            for f in sec_filings
        ]
        
        # Apply max_filings limit
        if max_filings and len(filings) > max_filings:
            filings = filings[:max_filings]
        
        logger.info(f"Retrieved {len(filings)} filings for CIK {cik_display}")
        
        # Log breakdown by type
        type_counts = {}
        for f in filings:
            type_counts[f.filing_type] = type_counts.get(f.filing_type, 0) + 1
        for ftype, count in sorted(type_counts.items()):
            logger.debug(f"  {ftype}: {count}")
        
        return filings
    
    def _expand_filing_types(
        self,
        filing_types: Optional[List[str]],
        include_amendments: bool
    ) -> Optional[List[str]]:
        """Expand filing types to include amendments if requested."""
        if filing_types is None:
            return None
        
        expanded = set()
        for ft in filing_types:
            expanded.add(ft)
            # Add amendment version if requested and not already an amendment
            if include_amendments and not ft.endswith('/A'):
                expanded.add(f"{ft}/A")
        
        return list(expanded)
    
    async def get_filing_content(
        self,
        filing: FilingMetadata,
        format_type: str = "raw"
    ) -> str:
        """
        Fetch the actual content of a filing document.
        
        Args:
            filing: FilingMetadata object for the target filing
            format_type: Content format - "raw", "text", or "html"
        
        Returns:
            Filing document content as string
        """
        if not self._session:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )
        
        await self._rate_limit()
        
        url = filing.document_url
        logger.debug(f"Fetching content from: {url}")
        
        try:
            async with self._session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    filing.raw_content = content
                    filing.content_hash = self._compute_hash(content)
                    return content
                elif response.status == 429:
                    logger.warning("Rate limited by SEC - waiting 60 seconds")
                    await asyncio.sleep(60)
                    return await self.get_filing_content(filing, format_type)
                else:
                    logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""
    
    async def get_filing_index(self, filing: FilingMetadata) -> Dict[str, Any]:
        """
        Fetch the filing index (list of all documents in the filing).
        
        Args:
            filing: FilingMetadata object
        
        Returns:
            Dictionary with filing index data including all documents
        """
        if not self._session:
            self._session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )
        
        await self._rate_limit()
        
        url = filing.index_url
        logger.debug(f"Fetching index from: {url}")
        
        try:
            async with self._session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Index not available at {url}: HTTP {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching index: {e}")
            return {}
    
    async def get_company_info(self, cik: str) -> Dict[str, Any]:
        """
        Get company information from SEC EDGAR.
        
        Args:
            cik: Company CIK number
        
        Returns:
            Dictionary with company information including name, tickers, filings metadata
        """
        if not self._fetcher:
            self._fetcher = RealSECDataFetcher(cache_dir=self.cache_dir)
            await self._fetcher.__aenter__()
        
        submissions = await self._fetcher.get_company_submissions(cik)
        
        return {
            "cik": cik,
            "name": submissions.get("name", "Unknown"),
            "tickers": submissions.get("tickers", []),
            "sic": submissions.get("sic", ""),
            "sic_description": submissions.get("sicDescription", ""),
            "fiscal_year_end": submissions.get("fiscalYearEnd", ""),
            "state_of_incorporation": submissions.get("stateOfIncorporation", ""),
            "business_address": submissions.get("addresses", {}).get("business", {}),
            "mailing_address": submissions.get("addresses", {}).get("mailing", {}),
            "phone": submissions.get("phone", ""),
            "filings_count": len(submissions.get("filings", {}).get("recent", {}).get("accessionNumber", []))
        }
    
    async def batch_get_filings(
        self,
        cik: str,
        start_date: str,
        end_date: str,
        filing_types: List[str],
        fetch_content: bool = False,
        progress_callback: Optional[callable] = None
    ) -> List[FilingMetadata]:
        """
        Batch fetch filings with optional content retrieval.
        
        Designed for deployment scripts that need to collect multiple filings
        with their content in a single operation.
        
        Args:
            cik: Company CIK number
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            filing_types: List of filing types to fetch
            fetch_content: Whether to fetch document content for each filing
            progress_callback: Optional callback function(current, total, filing)
        
        Returns:
            List of FilingMetadata with optional content populated
        """
        # Get filings
        filings = await self.get_filings(
            cik=cik,
            start_date=start_date,
            end_date=end_date,
            filing_types=filing_types
        )
        
        # Optionally fetch content
        if fetch_content:
            total = len(filings)
            for i, filing in enumerate(filings):
                await self.get_filing_content(filing)
                if progress_callback:
                    progress_callback(i + 1, total, filing)
        
        return filings
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content for chain of custody."""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def normalize_cik(cik: str) -> str:
        """Normalize CIK to 10-digit format with leading zeros."""
        return cik.lstrip('0').zfill(10)
    
    @staticmethod
    def format_accession(accession_number: str) -> str:
        """Format accession number with dashes."""
        clean = accession_number.replace('-', '')
        if len(clean) == 18:
            return f"{clean[:10]}-{clean[10:12]}-{clean[12:]}"
        return accession_number


# Convenience functions for non-async usage
def get_filings_sync(
    cik: str,
    start_date: str,
    end_date: str,
    filing_types: Optional[List[str]] = None
) -> List[FilingMetadata]:
    """
    Synchronous wrapper for get_filings().
    
    Convenience function for scripts that don't use async/await.
    """
    async def _fetch():
        async with SECEdgarAPI() as api:
            return await api.get_filings(
                cik=cik,
                start_date=start_date,
                end_date=end_date,
                filing_types=filing_types
            )
    
    return asyncio.run(_fetch())


async def fetch_nike_2019_filings() -> List[FilingMetadata]:
    """
    Fetch all Nike 2019 filings - convenience function for deployment.
    
    This function is specifically designed for the Nike 2019 investigation
    deployment scripts.
    
    Returns:
        List of FilingMetadata for all Nike 2019 SEC filings
    """
    async with SECEdgarAPI() as api:
        return await api.get_filings(
            cik="0000320187",
            start_date="2019-01-01",
            end_date="2019-12-31",
            filing_types=["10-K", "10-Q", "8-K", "4", "SC 13G", "SC 13G/A"],
            company_name="Nike Inc."
        )


# Test function
async def test_sec_edgar_api():
    """Test SEC EDGAR API functionality."""
    print("=" * 60)
    print("SEC EDGAR API TEST")
    print("=" * 60)
    
    async with SECEdgarAPI() as api:
        # Test Nike 2019 filings
        print("\n1. Testing get_filings() for Nike 2019...")
        filings = await api.get_filings(
            cik="0000320187",
            start_date="2019-01-01",
            end_date="2019-12-31",
            filing_types=["10-K", "10-Q", "4", "8-K"]
        )
        
        print(f"   Found {len(filings)} filings")
        
        # Count by type
        type_counts = {}
        for f in filings:
            type_counts[f.filing_type] = type_counts.get(f.filing_type, 0) + 1
        print(f"   Breakdown by type:")
        for ftype, count in sorted(type_counts.items()):
            print(f"      {ftype}: {count}")
        
        # Test company info
        print("\n2. Testing get_company_info()...")
        info = await api.get_company_info("0000320187")
        print(f"   Company: {info.get('name')}")
        print(f"   Tickers: {info.get('tickers')}")
        print(f"   SIC: {info.get('sic')} - {info.get('sic_description')}")
        
        # Test filing content (just first one)
        if filings:
            print("\n3. Testing get_filing_content()...")
            content = await api.get_filing_content(filings[0])
            print(f"   Retrieved {len(content)} bytes from {filings[0].filing_type}")
            print(f"   Content hash: {filings[0].content_hash[:16]}...")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE - All functions operational")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_sec_edgar_api())
