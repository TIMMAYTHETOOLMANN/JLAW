"""
SEC EDGAR API Client
====================

Rate-limited SEC EDGAR API client with full form coverage.
Implements 10 requests/second limit with mandatory User-Agent.

Endpoints:
- Submissions: data.sec.gov/submissions/
- XBRL Facts: data.sec.gov/api/xbrl/companyfacts/
- Daily Index: sec.gov/cgi-bin/browse-edgar

Form Coverage:
- Form 4 XML (all 16 transaction codes)
- DEF 14A (executive compensation)
- 10-K/10-Q XBRL financial statements
- 8-K material events
- Schedule 13D/13G beneficial ownership
- 13F-HR institutional holdings
"""

import asyncio
import aiohttp
import re
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
import time
import json
import os

logger = logging.getLogger(__name__)


class FormType(Enum):
    """SEC form types."""
    FORM_3 = "3"
    FORM_4 = "4"
    FORM_5 = "5"
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    DEF_14A = "DEF 14A"
    SCHEDULE_13D = "SC 13D"
    SCHEDULE_13G = "SC 13G"
    FORM_13F = "13F-HR"


@dataclass
class SECFiling:
    """Parsed SEC filing metadata."""
    accession_number: str
    form_type: str
    filing_date: date
    report_date: Optional[date]
    primary_document: str
    file_number: str
    cik: str
    company_name: str
    document_url: str
    index_url: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "form_type": self.form_type,
            "filing_date": self.filing_date.isoformat(),
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "primary_document": self.primary_document,
            "document_url": self.document_url,
            "cik": self.cik,
            "company_name": self.company_name
        }


@dataclass
class XBRLFact:
    """Single XBRL fact from SEC API."""
    concept: str
    value: Any
    unit: Optional[str]
    start_date: Optional[date]
    end_date: date
    fiscal_year: int
    fiscal_period: str
    form: str
    filed: date
    accession_number: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept": self.concept,
            "value": self.value,
            "unit": self.unit,
            "end_date": self.end_date.isoformat(),
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "form": self.form
        }


class RateLimiter:
    """
    Token bucket rate limiter for SEC EDGAR API.
    
    SEC allows 10 requests/second maximum.
    We use 9 req/sec (111ms minimum interval) for safety buffer.
    
    This is a singleton instance shared across all SECEdgarClient instances
    to prevent concurrent rate violations.
    """
    
    _instance = None
    
    def __new__(cls, requests_per_second: float = 9.0):
        """Ensure singleton pattern for rate limiter."""
        if cls._instance is None:
            cls._instance = super(RateLimiter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, requests_per_second: float = 9.0):
        """Initialize rate limiter (only once due to singleton)."""
        if getattr(self, '_initialized', False):
            return
        
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0
        self._lock = asyncio.Lock()
        self.request_count = 0
        self._initialized = True
        logger.info(f"Initialized shared SEC rate limiter: {requests_per_second} req/sec (min interval: {self.min_interval:.3f}s)")
    
    async def acquire(self):
        """Wait until rate limit allows next request."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_request
            
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                await asyncio.sleep(sleep_time)
            
            self.last_request = time.time()
            self.request_count += 1
            
            if self.request_count % 100 == 0:
                logger.debug(f"Rate limiter: {self.request_count} requests processed")


# Global singleton rate limiter instance shared across all clients
_SHARED_RATE_LIMITER = RateLimiter(requests_per_second=9.0)


class SECEdgarClient:
    """
    SEC EDGAR API Client with rate limiting and retry logic.
    
    Implements all required endpoints for forensic analysis:
    - Company submissions history
    - XBRL financial facts
    - Form 4 XML content
    - Full-text filing retrieval
    
    Features:
    - Shared rate limiter across all instances (9 req/sec)
    - Exponential backoff for 429 (rate limit) errors
    - Mock mode for testing without API access
    - User-Agent validation
    """
    
    BASE_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    
    # Default User-Agent (MUST be customized for production)
    # SEC requires format: <Company>/<Version> <Name> <email>
    DEFAULT_USER_AGENT = "JLAW-Forensics/2.0 Timothy_Johnson forensics@jlaw-system.org"
    
    # Retry configuration for 429 errors
    MAX_RETRIES = 4
    RETRY_DELAYS = [1, 2, 4, 8]  # Exponential backoff in seconds
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        requests_per_second: float = 9.0,
        mock_mode: bool = False
    ):
        """
        Initialize SEC EDGAR client.
        
        Args:
            user_agent: Contact information for SEC (required, must include email)
            requests_per_second: Rate limit (ignored - shared limiter uses 9 req/sec)
            mock_mode: If True, return mock data instead of making real API calls
        """
        # Check for mock mode from environment
        self.mock_mode = mock_mode or os.environ.get('SEC_MOCK_MODE', '').lower() in ('true', '1', 'yes')
        
        # Get user agent from parameter or environment
        if user_agent is None:
            user_agent = os.environ.get('SEC_USER_AGENT') or os.environ.get('SEC_EDGAR_USER_AGENT')
        
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        
        # Use the shared global rate limiter (singleton)
        self.rate_limiter = _SHARED_RATE_LIMITER
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Log initialization
        if self.mock_mode:
            logger.info("SEC EDGAR Client initialized in MOCK MODE - no real API calls will be made")
        else:
            logger.debug(f"SEC EDGAR Client initialized with User-Agent: {self.user_agent[:50]}...")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent}
        )
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _fetch(self, url: str) -> Optional[str]:
        """
        Fetch URL with rate limiting and exponential backoff for 429 errors.
        
        Args:
            url: URL to fetch
            
        Returns:
            Response text or None if failed
        """
        # Mock mode - return sample data
        if self.mock_mode:
            logger.debug(f"Mock mode: simulating fetch for {url}")
            return self._get_mock_response(url)
        
        # Retry loop with exponential backoff
        for attempt in range(self.MAX_RETRIES):
            await self.rate_limiter.acquire()
            
            try:
                async with self.session.get(url, timeout=30) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:
                        # Rate limited - use exponential backoff
                        if attempt < self.MAX_RETRIES - 1:
                            delay = self.RETRY_DELAYS[attempt]
                            logger.warning(
                                f"SEC API rate limit (429) hit for {url}. "
                                f"Retry {attempt + 1}/{self.MAX_RETRIES - 1} after {delay}s delay"
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            logger.error(
                                f"SEC API rate limit (429) - max retries exceeded for {url}. "
                                f"Consider reducing request rate or checking User-Agent configuration."
                            )
                            return None
                    elif response.status == 403:
                        logger.error(
                            f"SEC API access forbidden (403) for {url}. "
                            f"This usually indicates:\n"
                            f"  1. User-Agent header not compliant with SEC requirements\n"
                            f"  2. IP address may be blocked\n"
                            f"  3. User-Agent must include: Company Name + Contact Name + Valid Email\n"
                            f"Current User-Agent: {self.user_agent}\n"
                            f"SEC Requirement: '<Company> <Name> <email@example.com>'"
                        )
                        return None
                    else:
                        logger.warning(f"SEC fetch failed: {url} -> HTTP {response.status}")
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"SEC fetch timeout: {url}")
                return None
            except Exception as e:
                logger.error(f"SEC fetch error: {url} -> {e}")
                return None
        
        return None
    
    def _get_mock_response(self, url: str) -> str:
        """
        Return mock data for testing.
        
        Args:
            url: URL being requested
            
        Returns:
            Mock JSON or XML response
        """
        if "submissions/CIK" in url:
            # Mock submissions response
            return json.dumps({
                "name": "Mock Company Inc.",
                "filings": {
                    "recent": {
                        "accessionNumber": ["0001234567-24-000001"],
                        "form": ["10-K"],
                        "filingDate": ["2024-01-15"],
                        "reportDate": ["2023-12-31"],
                        "primaryDocument": ["mock-10k.htm"],
                        "fileNumber": ["001-12345"]
                    }
                }
            })
        elif "companyfacts/CIK" in url:
            # Mock XBRL facts response
            return json.dumps({
                "entityName": "Mock Company Inc.",
                "facts": {
                    "us-gaap": {
                        "Revenues": {
                            "units": {
                                "USD": [
                                    {
                                        "val": 1000000,
                                        "fy": 2023,
                                        "form": "10-K",
                                        "fp": "FY"
                                    }
                                ]
                            }
                        }
                    }
                }
            })
        elif "company_tickers.json" in url:
            # Mock ticker mapping
            return json.dumps({
                "0": {"ticker": "MOCK", "cik_str": "1234567", "title": "Mock Company Inc."}
            })
        else:
            # Mock document content
            return "<?xml version='1.0'?><document>Mock filing content</document>"
    
    async def _fetch_json(self, url: str) -> Optional[Dict]:
        """Fetch JSON from URL."""
        content = await self._fetch(url)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        return None
    
    async def _resolve_xml_from_index(self, filing) -> Optional[str]:
        """
        Resolve actual XML document URL using index.json.
        
        SEC EDGAR blocks XSL-transformed URLs (xslF345X03/form4.xml).
        This method fetches the filing index.json to find the actual XML file.
        
        Args:
            filing: SECFiling object with index_url
            
        Returns:
            Actual XML document URL or None if not found
        """
        try:
            index_data = await self._fetch_json(filing.index_url)
            if not index_data:
                return None
            
            # Look for XML files in the directory listing
            directory = index_data.get("directory", {})
            items = directory.get("item", [])
            
            # For Form 4, look for the actual form XML file
            xml_candidates = []
            for item in items:
                name = item.get("name", "")
                if name.endswith(".xml") and not name.startswith("xsl"):
                    # Prefer files that match form naming conventions
                    if any(pattern in name.lower() for pattern in ["form4", "form3", "form5", "edgardoc"]):
                        xml_candidates.insert(0, name)  # Higher priority
                    else:
                        xml_candidates.append(name)
            
            # Try the primary document without XSL prefix if it's XML
            primary_doc = filing.primary_document
            if "xsl" in primary_doc.lower():
                # Extract actual filename from xslF345X03/form4.xml -> form4.xml
                match = re.search(r'xsl[^/]+/(.+\.xml)$', primary_doc, re.IGNORECASE)
                if match:
                    actual_filename = match.group(1)
                    if actual_filename in [item.get("name", "") for item in items]:
                        xml_candidates.insert(0, actual_filename)
            
            if xml_candidates:
                # Build URL for the first candidate
                accession_clean = filing.accession_number.replace("-", "")
                cik_clean = filing.cik.lstrip("0") or "0"
                return f"{self.ARCHIVES_URL}/{cik_clean}/{accession_clean}/{xml_candidates[0]}"
            
            return None
        except Exception as e:
            logger.warning(f"Failed to resolve XML from index: {e}")
            return None
    
    async def _fetch_with_fallback(self, filing, is_xml: bool = False) -> Optional[str]:
        """
        Fetch document with fallback to index.json resolution.
        
        Args:
            filing: SECFiling object
            is_xml: Whether to look for XML files specifically
            
        Returns:
            Document content or None
        """
        # First try the direct URL
        content = await self._fetch(filing.document_url)
        if content:
            return content
        
        logger.info(f"Direct fetch failed for {filing.document_url}, trying index.json resolution")
        
        # For XML files (Form 4, etc.), try resolving via index.json
        if is_xml or filing.form_type in ["3", "4", "5"]:
            resolved_url = await self._resolve_xml_from_index(filing)
            if resolved_url and resolved_url != filing.document_url:
                logger.info(f"Resolved URL via index.json: {resolved_url}")
                content = await self._fetch(resolved_url)
                if content:
                    return content
        
        # Try additional fallback patterns for Form 4
        if filing.form_type in ["3", "4", "5"]:
            accession_clean = filing.accession_number.replace("-", "")
            cik_clean = filing.cik.lstrip("0") or "0"
            
            fallback_patterns = [
                f"{self.ARCHIVES_URL}/{cik_clean}/{accession_clean}/form4.xml",
                f"{self.ARCHIVES_URL}/{cik_clean}/{accession_clean}/edgardoc.xml",
                f"{self.ARCHIVES_URL}/{cik_clean}/{accession_clean}/doc4.xml",
            ]
            
            for fallback_url in fallback_patterns:
                if fallback_url != filing.document_url:
                    content = await self._fetch(fallback_url)
                    if content:
                        logger.info(f"Fetched via fallback pattern: {fallback_url}")
                        return content
        
        return None
    
    async def get_company_submissions(self, cik: str) -> Optional[Dict]:
        """
        Get company filing history.
        
        Args:
            cik: Company CIK (with or without leading zeros)
            
        Returns:
            Full submissions JSON including all filings
        """
        cik_padded = cik.zfill(10)
        url = f"{self.BASE_URL}/submissions/CIK{cik_padded}.json"
        return await self._fetch_json(url)
    
    async def get_filings(
        self,
        cik: str,
        form_types: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[SECFiling]:
        """
        Get filtered list of filings for a company.
        
        Args:
            cik: Company CIK
            form_types: Filter to specific form types
            start_date: Filter to filings on/after this date
            end_date: Filter to filings on/before this date
            limit: Maximum number of filings to return
            
        Returns:
            List of SECFiling objects
        """
        submissions = await self.get_company_submissions(cik)
        if not submissions:
            return []
        
        company_name = submissions.get("name", "")
        cik_clean = cik.lstrip("0") or "0"
        
        filings = []
        recent = submissions.get("filings", {}).get("recent", {})
        
        accessions = recent.get("accessionNumber", [])
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        primary_docs = recent.get("primaryDocument", [])
        file_numbers = recent.get("fileNumber", [])
        
        for i in range(len(accessions)):
            form = forms[i] if i < len(forms) else ""
            
            # Filter by form type
            if form_types and form not in form_types:
                continue
            
            # Parse filing date
            filing_date_str = filing_dates[i] if i < len(filing_dates) else ""
            try:
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
            except ValueError:
                continue
            
            # Filter by date range
            if start_date and filing_date < start_date:
                continue
            if end_date and filing_date > end_date:
                continue
            
            # Parse report date
            report_date = None
            report_date_str = report_dates[i] if i < len(report_dates) else ""
            if report_date_str:
                try:
                    report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            accession = accessions[i]
            accession_clean = accession.replace("-", "")
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""
            file_number = file_numbers[i] if i < len(file_numbers) else ""
            
            filings.append(SECFiling(
                accession_number=accession,
                form_type=form,
                filing_date=filing_date,
                report_date=report_date,
                primary_document=primary_doc,
                file_number=file_number,
                cik=cik_clean,
                company_name=company_name,
                document_url=f"{self.ARCHIVES_URL}/{cik_clean}/{accession_clean}/{primary_doc}",
                index_url=f"{self.ARCHIVES_URL}/{cik_clean}/{accession_clean}/index.json"
            ))
            
            # Check limit
            if limit and len(filings) >= limit:
                break
        
        return filings
    
    async def get_form4_xml(self, filing: SECFiling) -> Optional[str]:
        """
        Get Form 4 XML content.
        
        Uses index.json resolution to find actual XML files when
        XSL-transformed URLs return 403 errors.
        
        Args:
            filing: SECFiling object for a Form 4
            
        Returns:
            Raw XML content string
        """
        if filing.form_type not in ["3", "4", "5"]:
            return None
        
        # Use fallback mechanism to handle XSL-transformed URLs that return 403
        return await self._fetch_with_fallback(filing, is_xml=True)
    
    async def get_filing_text(self, filing: SECFiling) -> Optional[str]:
        """
        Get filing text content.
        
        Uses fallback mechanism to handle 403 errors from XSL-transformed URLs.
        
        Args:
            filing: SECFiling object
            
        Returns:
            Raw text content string
        """
        # Use fallback mechanism for Form 4 and similar filings
        if filing.form_type in ["3", "4", "5"]:
            return await self._fetch_with_fallback(filing, is_xml=True)
        
        return await self._fetch(filing.document_url)
    
    async def get_filing_content(self, filing: SECFiling) -> Optional[str]:
        """
        Get filing content (alias for get_filing_text).
        
        Args:
            filing: SECFiling object
            
        Returns:
            Raw content string
        """
        return await self.get_filing_text(filing)
    
    async def get_xbrl_facts(self, cik: str) -> Optional[Dict]:
        """
        Get XBRL company facts.
        
        Args:
            cik: Company CIK
            
        Returns:
            Complete XBRL facts JSON
        """
        cik_padded = cik.zfill(10)
        url = f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik_padded}.json"
        return await self._fetch_json(url)
    
    async def extract_financials(
        self,
        cik: str,
        fiscal_year: int
    ) -> Dict[str, float]:
        """
        Extract key financial metrics from XBRL for a fiscal year.
        
        Args:
            cik: Company CIK
            fiscal_year: Fiscal year to extract
            
        Returns:
            Dictionary of financial metrics
        """
        facts = await self.get_xbrl_facts(cik)
        if not facts:
            return {}
        
        # Standard US-GAAP concepts to extract
        concepts = {
            "us-gaap:Revenues": "sales",
            "us-gaap:NetIncomeLoss": "net_income",
            "us-gaap:Assets": "total_assets",
            "us-gaap:AccountsReceivableNetCurrent": "receivables",
            "us-gaap:PropertyPlantAndEquipmentNet": "ppe",
            "us-gaap:GrossProfit": "gross_profit",
            "us-gaap:CostOfRevenue": "cost_of_revenue",
            "us-gaap:OperatingExpenses": "operating_expenses",
            "us-gaap:NetCashProvidedByUsedInOperatingActivities": "cfo",
            "us-gaap:LongTermDebt": "long_term_debt",
            "us-gaap:ShortTermBorrowings": "short_term_debt",
            "us-gaap:StockholdersEquity": "equity",
            "us-gaap:Depreciation": "depreciation",
            "us-gaap:SellingGeneralAndAdministrativeExpense": "sga",
        }
        
        financials = {}
        facts_data = facts.get("facts", {})
        
        for namespace in ["us-gaap", "ifrs-full"]:
            ns_facts = facts_data.get(namespace, {})
            
            for concept, metric_name in concepts.items():
                concept_name = concept.split(":")[1] if ":" in concept else concept
                
                if concept_name in ns_facts:
                    units = ns_facts[concept_name].get("units", {})
                    usd_facts = units.get("USD", [])
                    
                    # Find the fact for the requested fiscal year (10-K)
                    for fact in usd_facts:
                        if (fact.get("fy") == fiscal_year and 
                            fact.get("form") == "10-K" and
                            fact.get("fp") == "FY"):
                            financials[metric_name] = fact.get("val", 0)
                            break
        
        # Calculate derived metrics
        if "sales" in financials and "gross_profit" in financials:
            financials["gross_margin"] = financials["gross_profit"] / financials["sales"]
        
        if "long_term_debt" in financials or "short_term_debt" in financials:
            financials["total_debt"] = (
                financials.get("long_term_debt", 0) + 
                financials.get("short_term_debt", 0)
            )
        
        return financials
    
    async def get_form4_filings(
        self,
        cik: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SECFiling]:
        """Convenience method to get Form 4 filings."""
        return await self.get_filings(
            cik,
            form_types=["3", "4", "5"],
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_annual_reports(
        self,
        cik: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SECFiling]:
        """Convenience method to get 10-K filings."""
        return await self.get_filings(
            cik,
            form_types=["10-K", "10-K/A"],
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_proxy_statements(
        self,
        cik: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SECFiling]:
        """Convenience method to get DEF 14A filings."""
        return await self.get_filings(
            cik,
            form_types=["DEF 14A", "DEFA14A"],
            start_date=start_date,
            end_date=end_date
        )
    
    async def get_company_concept(
        self,
        cik: str,
        taxonomy: str,
        concept: str
    ) -> Optional[Dict]:
        """
        Get company concept data from XBRL API.
        
        Args:
            cik: Company CIK
            taxonomy: Taxonomy (e.g., "us-gaap", "ifrs-full")
            concept: Concept tag (e.g., "Revenues", "AccountsReceivableNetCurrent")
            
        Returns:
            Company concept JSON with time series data
            
        Example:
            concept = await client.get_company_concept(
                "320193", "us-gaap", "Revenues"
            )
        """
        cik_padded = cik.zfill(10)
        url = f"{self.BASE_URL}/api/xbrl/companyconcept/CIK{cik_padded}/{taxonomy}/{concept}.json"
        return await self._fetch_json(url)
    
    async def get_frames(
        self,
        taxonomy: str,
        concept: str,
        unit: str,
        period: str
    ) -> Optional[Dict]:
        """
        Get frames data (all companies for a given concept/period).
        
        Args:
            taxonomy: Taxonomy (e.g., "us-gaap")
            concept: Concept tag (e.g., "Revenues")
            unit: Unit (e.g., "USD")
            period: Period in format CY2023Q4I or CY2023
            
        Returns:
            Frames JSON with all companies reporting that concept
            
        Example:
            frames = await client.get_frames(
                "us-gaap", "Revenues", "USD", "CY2023"
            )
        """
        url = f"{self.BASE_URL}/api/xbrl/frames/{taxonomy}/{concept}/{unit}/{period}.json"
        return await self._fetch_json(url)
    
    async def get_ticker_cik_mapping(self) -> Optional[Dict[str, str]]:
        """
        Get ticker to CIK mapping from SEC.
        
        Returns:
            Dictionary mapping ticker symbols to CIKs
            
        Example:
            mapping = await client.get_ticker_cik_mapping()
            cik = mapping.get("AAPL")  # Returns "320193"
        """
        url = "https://www.sec.gov/files/company_tickers.json"
        data = await self._fetch_json(url)
        if not data:
            return None
        
        # Convert to simple ticker -> CIK mapping
        mapping = {}
        for entry in data.values():
            ticker = entry.get("ticker", "").upper()
            cik = str(entry.get("cik_str", ""))
            if ticker and cik:
                mapping[ticker] = cik
        
        return mapping
    
    async def cik_from_ticker(self, ticker: str) -> Optional[str]:
        """
        Get CIK from ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            
        Returns:
            CIK string or None if not found
        """
        mapping = await self.get_ticker_cik_mapping()
        if mapping:
            return mapping.get(ticker.upper())
        return None
    
    async def extract_xbrl_concepts(
        self,
        cik: str,
        fiscal_year: int,
        concepts: List[str],
        taxonomy: str = "us-gaap"
    ) -> Dict[str, Any]:
        """
        Extract multiple XBRL concepts for a fiscal year.
        
        Args:
            cik: Company CIK
            fiscal_year: Fiscal year
            concepts: List of concept names (e.g., ["Revenues", "Assets"])
            taxonomy: Taxonomy to use (default: "us-gaap")
            
        Returns:
            Dictionary mapping concept names to values
        """
        results = {}
        
        for concept in concepts:
            data = await self.get_company_concept(cik, taxonomy, concept)
            if data and "units" in data:
                # Try to find USD values
                units = data.get("units", {})
                usd_values = units.get("USD", [])
                
                # Find value for the requested fiscal year
                for fact in usd_values:
                    if (fact.get("fy") == fiscal_year and 
                        fact.get("form") in ["10-K", "10-Q"]):
                        results[concept] = fact.get("val")
                        break
        
        return results

    
    # Backward compatibility methods
    async def get_submissions(self, cik: str) -> Optional[Dict]:
        """Alias for get_company_submissions (backward compatibility)."""
        return await self.get_company_submissions(cik)
    
    async def get_filings_by_type(
        self,
        cik: str,
        form_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[SECFiling]:
        """Get filings by single form type (backward compatibility)."""
        return await self.get_filings(
            cik,
            form_types=[form_type],
            start_date=start_date,
            end_date=end_date
        )
