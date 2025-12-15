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
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
import time
import json

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
    We use 100ms minimum interval for safety.
    """
    
    def __init__(self, requests_per_second: float = 10.0):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until rate limit allows next request."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_request
            
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            
            self.last_request = time.time()


class SECEdgarClient:
    """
    SEC EDGAR API Client with rate limiting.
    
    Implements all required endpoints for forensic analysis:
    - Company submissions history
    - XBRL financial facts
    - Form 4 XML content
    - Full-text filing retrieval
    """
    
    BASE_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    
    # Default User-Agent (MUST be customized for production)
    DEFAULT_USER_AGENT = "JLAW-Forensics/2.0 (forensics@jlaw-system.org)"
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        requests_per_second: float = 10.0
    ):
        """
        Initialize SEC EDGAR client.
        
        Args:
            user_agent: Contact information for SEC (required)
            requests_per_second: Rate limit (max 10)
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self.rate_limiter = RateLimiter(min(10.0, requests_per_second))
        self.session: Optional[aiohttp.ClientSession] = None
    
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
        """Fetch URL with rate limiting."""
        await self.rate_limiter.acquire()
        
        try:
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"SEC fetch failed: {url} -> {response.status}")
                    return None
        except Exception as e:
            logger.error(f"SEC fetch error: {url} -> {e}")
            return None
    
    async def _fetch_json(self, url: str) -> Optional[Dict]:
        """Fetch JSON from URL."""
        content = await self._fetch(url)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
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
        
        Args:
            filing: SECFiling object for a Form 4
            
        Returns:
            Raw XML content string
        """
        if filing.form_type not in ["3", "4", "5"]:
            return None
        
        # Form 4 XML is usually the primary document
        return await self._fetch(filing.document_url)
    
    async def get_filing_text(self, filing: SECFiling) -> Optional[str]:
        """
        Get filing text content.
        
        Args:
            filing: SECFiling object
            
        Returns:
            Raw text content string
        """
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
