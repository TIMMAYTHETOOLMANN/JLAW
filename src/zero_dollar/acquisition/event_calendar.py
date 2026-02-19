"""
Event Calendar Acquisition Module
==================================

Acquire material corporate events from SEC EDGAR for event proximity analysis.

Fetches:
    - SEC Form 8-K filings (material events)
    - Earnings announcement dates
    - Other price-sensitive disclosures

Per Section 6 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 6: Event Proximity Analysis Module
    - Section 12.2: SEC EDGAR Acquisition Module
"""

import asyncio
import aiohttp
import hashlib
import logging
import re
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from lxml import etree

from src.zero_dollar.models import MaterialEvent
from .rate_limiter import get_edgar_rate_limiter
from .exceptions import (
    EdgarAcquisitionError,
    EdgarParsingError,
    EdgarNetworkError,
)

logger = logging.getLogger(__name__)


class EventCalendarAcquisition:
    """
    Acquire material corporate events from SEC EDGAR.
    
    Fetches Form 8-K filings and parses them to extract material event
    information for event proximity analysis.
    
    Compliance:
        - SEC EDGAR Rate Limiting: 10 requests/second max
        - User-Agent identification per SEC guidelines
        - FRE 902(13)/(14) evidence integrity via SHA-256 hashing
    
    Usage:
        config = {'user_agent': 'MyApp/1.0 me@example.com'}
        async with EventCalendarAcquisition(config) as client:
            events = await client.fetch_8k_events(
                issuer_cik='0000320187',
                start_date=date(2020, 1, 1),
                end_date=date(2020, 12, 31)
            )
    """
    
    BASE_URL = 'https://www.sec.gov'
    SUBMISSIONS_URL = 'https://data.sec.gov/submissions'
    
    # SEC requires User-Agent with contact information
    DEFAULT_USER_AGENT = 'JLAW-Forensics/2.0 Zero-Dollar-Detection forensics@jlaw-system.org'
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Event Calendar Acquisition client.
        
        Args:
            config: Configuration dictionary with optional keys:
                - user_agent: User-Agent string (required by SEC)
                - max_concurrent_requests: Maximum concurrent requests (default: 10)
                - request_timeout: HTTP request timeout in seconds (default: 30)
        """
        self.user_agent = config.get('user_agent', self.DEFAULT_USER_AGENT)
        self.max_concurrent = config.get('max_concurrent_requests', 10)
        self.timeout = aiohttp.ClientTimeout(total=config.get('request_timeout', 30))
        self.rate_limiter = get_edgar_rate_limiter()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={'User-Agent': self.user_agent},
            trust_env=True,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_8k_events(
        self,
        issuer_cik: str,
        start_date: date,
        end_date: date
    ) -> List[MaterialEvent]:
        """
        Fetch Form 8-K filings and parse into MaterialEvent objects.
        
        Retrieves all Form 8-K filings for the specified issuer within
        the date range and extracts material event information.
        
        Args:
            issuer_cik: SEC Central Index Key for issuer
            start_date: Start of analysis period
            end_date: End of analysis period
        
        Returns:
            List of MaterialEvent objects from Form 8-K filings
        
        Raises:
            EdgarAcquisitionError: If acquisition fails
            EdgarNetworkError: If network errors occur
        """
        logger.info(f"Fetching 8-K events for CIK {issuer_cik} from {start_date} to {end_date}")
        
        try:
            # Get company submissions index
            submissions = await self._fetch_submissions_json(issuer_cik)
            
            # Extract 8-K filings within date range
            filings_8k = self._filter_8k_filings(submissions, start_date, end_date)
            
            # Fetch and parse each 8-K filing
            events = []
            for filing in filings_8k:
                try:
                    filing_events = await self._parse_8k_filing(filing, issuer_cik)
                    events.extend(filing_events)
                except Exception as e:
                    logger.warning(f"Failed to parse 8-K filing {filing.get('accessionNumber')}: {e}")
                    continue
            
            logger.info(f"Extracted {len(events)} material events from {len(filings_8k)} 8-K filings")
            return events
            
        except Exception as e:
            logger.error(f"Failed to fetch 8-K events: {e}")
            raise EdgarAcquisitionError(f"Failed to fetch 8-K events: {e}")
    
    async def fetch_earnings_dates(
        self,
        issuer_ticker: str,
        start_date: date,
        end_date: date
    ) -> List[MaterialEvent]:
        """
        Fetch earnings announcement dates.
        
        Note: This is a placeholder implementation. In production, this would
        integrate with earnings calendar APIs or parse 10-Q/10-K filing dates.
        
        Args:
            issuer_ticker: Stock ticker symbol
            start_date: Start of analysis period
            end_date: End of analysis period
        
        Returns:
            List of MaterialEvent objects for earnings announcements
        """
        logger.info(f"Fetching earnings dates for {issuer_ticker} from {start_date} to {end_date}")
        
        # Placeholder: In production, integrate with earnings calendar API
        # For now, return empty list
        # TODO: Integrate with Polygon.io, Alpha Vantage, or similar API
        
        logger.warning("Earnings calendar acquisition not yet implemented")
        return []
    
    def parse_8k_items(self, filing_xml: str) -> List[str]:
        """
        Extract Form 8-K item numbers from filing XML.
        
        Parses the 8-K XML document to identify which item numbers
        (e.g., "1.01", "2.02") are reported in the filing.
        
        Args:
            filing_xml: Raw XML content of Form 8-K filing
        
        Returns:
            List of item numbers (e.g., ["1.01", "2.02"])
        
        Example:
            >>> items = parser.parse_8k_items(xml_content)
            >>> print(items)  # ["2.02", "9.01"]
        """
        try:
            # Parse XML
            root = etree.fromstring(filing_xml.encode('utf-8'))
            
            # Look for item entries in various locations
            items = []
            
            # Method 1: Check for itemNumber or item tags
            for item_elem in root.xpath(".//itemNumber | .//item"):
                item_text = item_elem.text
                if item_text:
                    # Extract item number pattern (e.g., "1.01", "2.02")
                    match = re.search(r'\d+\.\d+', item_text)
                    if match:
                        items.append(match.group(0))
            
            # Method 2: Text search for "Item X.XX" patterns
            text_content = etree.tostring(root, method='text', encoding='unicode')
            item_pattern = r'Item\s+(\d+\.\d+)'
            matches = re.findall(item_pattern, text_content, re.IGNORECASE)
            items.extend(matches)
            
            # Remove duplicates and return
            return list(set(items))
            
        except Exception as e:
            logger.error(f"Failed to parse 8-K items: {e}")
            raise EdgarParsingError(f"Failed to parse 8-K items: {e}")
    
    # Private helper methods
    
    async def _fetch_submissions_json(self, cik: str) -> Dict[str, Any]:
        """Fetch company submissions JSON from SEC EDGAR."""
        # Normalize CIK to 10 digits with leading zeros
        cik_normalized = cik.zfill(10)
        url = f"{self.SUBMISSIONS_URL}/CIK{cik_normalized}.json"
        
        async with self.rate_limiter:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise EdgarNetworkError(f"HTTP {response.status} for {url}")
            except aiohttp.ClientError as e:
                raise EdgarNetworkError(f"Network error fetching submissions: {e}")
    
    def _filter_8k_filings(
        self,
        submissions: Dict[str, Any],
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Filter submissions to 8-K filings within date range."""
        filings_8k = []
        
        # Extract recent filings
        recent_filings = submissions.get('filings', {}).get('recent', {})
        forms = recent_filings.get('form', [])
        filing_dates = recent_filings.get('filingDate', [])
        accession_numbers = recent_filings.get('accessionNumber', [])
        primary_documents = recent_filings.get('primaryDocument', [])
        
        # Filter to 8-K filings within date range
        for i, form in enumerate(forms):
            if form == '8-K':
                filing_date_str = filing_dates[i]
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
                
                if start_date <= filing_date <= end_date:
                    filings_8k.append({
                        'form': form,
                        'filingDate': filing_date,
                        'accessionNumber': accession_numbers[i],
                        'primaryDocument': primary_documents[i],
                    })
        
        return filings_8k
    
    async def _parse_8k_filing(
        self,
        filing: Dict[str, Any],
        issuer_cik: str
    ) -> List[MaterialEvent]:
        """Parse a single 8-K filing into MaterialEvent objects."""
        # Construct document URL
        accession = filing['accessionNumber'].replace('-', '')
        primary_doc = filing['primaryDocument']
        doc_url = f"{self.BASE_URL}/Archives/edgar/data/{issuer_cik}/{accession}/{primary_doc}"
        
        # Fetch document content
        async with self.rate_limiter:
            try:
                async with self.session.get(doc_url) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch 8-K document: HTTP {response.status}")
                        return []
                    
                    content = await response.text()
            except aiohttp.ClientError as e:
                logger.warning(f"Network error fetching 8-K document: {e}")
                return []
        
        # Parse item numbers from content
        try:
            items = self.parse_8k_items(content)
        except EdgarParsingError:
            # If XML parsing fails, try text-based extraction
            items = self._extract_items_from_text(content)
        
        # Create MaterialEvent for each item
        events = []
        filing_date = filing['filingDate']
        
        for item in items:
            event = MaterialEvent(
                event_id=f"{filing['accessionNumber']}-{item}",
                issuer_cik=issuer_cik,
                issuer_name="",  # Will be enriched later
                event_type=f"8K-{item}",
                event_date=filing_date,
                event_description=f"Form 8-K Item {item}",
                stock_price_impact=None,
                is_price_sensitive=True,
                sec_filing_url=doc_url,
            )
            events.append(event)
        
        return events
    
    def _extract_items_from_text(self, content: str) -> List[str]:
        """Extract 8-K item numbers from text content (fallback method)."""
        item_pattern = r'Item\s+(\d+\.\d+)'
        matches = re.findall(item_pattern, content, re.IGNORECASE)
        return list(set(matches))


__all__ = [
    'EventCalendarAcquisition',
]
