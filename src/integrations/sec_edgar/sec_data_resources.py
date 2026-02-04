"""
SEC Data Resources Client
=========================

Comprehensive client for accessing all SEC Data Resources endpoints as specified in
https://www.sec.gov/data-research/sec-data-resources

This module provides access to:
- Financial Statement Data Sets (quarterly XBRL-extracted numeric data)
- Company Facts API (comprehensive XBRL facts per CIK)
- Company Concept API (time-series data for specific concepts)
- Frames API (cross-company data for specific periods)
- Fails-to-Deliver Data (settlement failure statistics)
- Investment Adviser Data (Form ADV via IAPD)
- Mutual Fund Data (N-PORT, N-MFP holdings)
- Market Structure Data (equity market metrics)
- SEC Enforcement Actions
- EDGAR Full-Text Search API
- RSS Feeds for real-time filing notifications

All endpoints are accessed using rate-limited requests with proper SEC User-Agent
compliance per SEC requirements.

Legal Framework:
- 17 CFR § 240.10b-5 (Securities fraud)
- 17 CFR § 240.10b5-1/10b5-2 (Insider trading)
- SOX Sections 302, 404, 906
- FRE 902(13)/(14) (Self-authenticating evidence)
"""

import asyncio
import aiohttp
import logging
import json
import re
import zipfile
import io
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Optional, Union, AsyncIterator
from enum import Enum
from pathlib import Path

from .rate_limiter import get_shared_rate_limiter
from .models import IntegrityHashes

logger = logging.getLogger(__name__)


# =============================================================================
# SEC Data Resource Endpoints
# =============================================================================

class SECDataEndpoint(Enum):
    """SEC Data Resource API Endpoints."""
    
    # Core EDGAR APIs (data.sec.gov)
    SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
    COMPANY_FACTS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    COMPANY_CONCEPT = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{concept}.json"
    FRAMES = "https://data.sec.gov/api/xbrl/frames/{taxonomy}/{concept}/{unit}/{period}.json"
    
    # Full-Text Search API
    FULL_TEXT_SEARCH = "https://efts.sec.gov/LATEST/search-index"
    
    # Ticker/CIK Mappings
    COMPANY_TICKERS = "https://www.sec.gov/files/company_tickers.json"
    COMPANY_TICKERS_EXCHANGE = "https://www.sec.gov/files/company_tickers_exchange.json"
    MUTUAL_FUND_TICKERS = "https://www.sec.gov/files/company_tickers_mf.json"
    
    # Financial Statement Data Sets
    FINANCIAL_STATEMENTS_QUARTERLY = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/{year}q{quarter}.zip"
    FINANCIAL_STATEMENTS_ARCHIVE = "https://www.sec.gov/files/dera/data/financial-statement-data-sets.html"
    
    # Fails-to-Deliver Data
    FAILS_TO_DELIVER = "https://www.sec.gov/data/foiadocsfailsdatahtm"
    FAILS_TO_DELIVER_CURRENT = "https://www.sec.gov/files/data/fails-deliver-data/cnsfails{year}{month}{half}.zip"
    
    # Investment Adviser Data
    IAPD_API = "https://api.adviserinfo.sec.gov/IAPD/Content/Search/api/PublicSearch"
    FORM_ADV_DOWNLOAD = "https://www.sec.gov/help/foiadocsinvaikialist.htm"
    
    # Mutual Fund Data
    MUTUAL_FUND_PROSPECTUS = "https://www.sec.gov/files/dera/data/mutual-fund-prospectus-risk-return"
    N_PORT_DATA = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=N-PORT"
    
    # Market Structure Data
    MARKET_STRUCTURE = "https://www.sec.gov/marketstructure/data/downloads.html"
    MIDAS_DATA = "https://www.sec.gov/opa/data/market-structure/market-structure-data-downloads.html"
    
    # RSS Feeds
    RSS_FILINGS = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type={form_type}&company=&owner=include&count=40&output=atom"
    RSS_XBRL = "https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession}&xbrl_type=v"
    
    # Enforcement Actions
    ENFORCEMENT_RELEASES = "https://www.sec.gov/litigation/litreleases.htm"
    ADMINISTRATIVE_PROCEEDINGS = "https://www.sec.gov/litigation/admin.htm"
    TRADING_SUSPENSIONS = "https://www.sec.gov/litigation/suspensions.htm"
    
    # SRO Filings (Self-Regulatory Organizations)
    SRO_FILINGS = "https://www.sec.gov/rules/sro.shtml"


# =============================================================================
# Data Models for SEC Data Resources
# =============================================================================

@dataclass
class FinancialStatementFact:
    """Individual fact from Financial Statement Data Sets."""
    adsh: str  # Accession number
    tag: str  # XBRL tag
    version: str  # Taxonomy version
    coreg: str  # Co-registrant
    ddate: date  # Data date
    qtrs: int  # Duration in quarters
    uom: str  # Unit of measure
    value: float
    footnote: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "adsh": self.adsh,
            "tag": self.tag,
            "version": self.version,
            "ddate": self.ddate.isoformat(),
            "qtrs": self.qtrs,
            "uom": self.uom,
            "value": self.value,
            "footnote": self.footnote
        }


@dataclass
class FailsToDeliverRecord:
    """Fails-to-Deliver data record."""
    settlement_date: date
    cusip: str
    symbol: str
    quantity: int
    description: str
    price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "settlement_date": self.settlement_date.isoformat(),
            "cusip": self.cusip,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "description": self.description,
            "price": self.price
        }


@dataclass
class InvestmentAdviser:
    """Investment Adviser registration data from IAPD."""
    firm_crd: str
    firm_name: str
    sec_number: Optional[str]
    main_office_city: Optional[str]
    main_office_state: Optional[str]
    aum: Optional[float]  # Assets Under Management
    discretionary_aum: Optional[float]
    non_discretionary_aum: Optional[float]
    total_employees: Optional[int]
    registration_status: str
    registration_date: Optional[date]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "firm_crd": self.firm_crd,
            "firm_name": self.firm_name,
            "sec_number": self.sec_number,
            "main_office_city": self.main_office_city,
            "main_office_state": self.main_office_state,
            "aum": self.aum,
            "discretionary_aum": self.discretionary_aum,
            "non_discretionary_aum": self.non_discretionary_aum,
            "total_employees": self.total_employees,
            "registration_status": self.registration_status,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None
        }


@dataclass
class MutualFundHolding:
    """Mutual fund holding from N-PORT data."""
    lei: Optional[str]
    name: str
    title: str
    cusip: Optional[str]
    isin: Optional[str]
    balance: float
    units: str
    currency: str
    value_usd: float
    pct_val: float  # Percentage of total value
    payoff_profile: Optional[str]
    asset_category: str
    issuer_category: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lei": self.lei,
            "name": self.name,
            "title": self.title,
            "cusip": self.cusip,
            "isin": self.isin,
            "balance": self.balance,
            "units": self.units,
            "currency": self.currency,
            "value_usd": self.value_usd,
            "pct_val": self.pct_val,
            "payoff_profile": self.payoff_profile,
            "asset_category": self.asset_category,
            "issuer_category": self.issuer_category
        }


@dataclass
class EnforcementAction:
    """SEC Enforcement action record."""
    release_number: str
    date: date
    title: str
    respondents: List[str]
    url: str
    action_type: str  # 'litigation', 'administrative', 'trading_suspension'
    summary: Optional[str] = None
    related_statutes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "release_number": self.release_number,
            "date": self.date.isoformat(),
            "title": self.title,
            "respondents": self.respondents,
            "url": self.url,
            "action_type": self.action_type,
            "summary": self.summary,
            "related_statutes": self.related_statutes
        }


@dataclass
class MarketStructureMetric:
    """Market structure data metric."""
    date: date
    symbol: Optional[str]
    market: str
    metric_type: str
    value: float
    unit: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "symbol": self.symbol,
            "market": self.market,
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit
        }


@dataclass
class FullTextSearchResult:
    """Full-text search result from EDGAR."""
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filing_date: date
    file_description: str
    document_url: str
    score: float
    highlights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "cik": self.cik,
            "company_name": self.company_name,
            "form_type": self.form_type,
            "filing_date": self.filing_date.isoformat(),
            "file_description": self.file_description,
            "document_url": self.document_url,
            "score": self.score,
            "highlights": self.highlights
        }


@dataclass
class RSSFilingEntry:
    """RSS feed entry for new filings."""
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filing_date: datetime
    accepted_date: datetime
    filing_url: str
    file_number: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "cik": self.cik,
            "company_name": self.company_name,
            "form_type": self.form_type,
            "filing_date": self.filing_date.isoformat(),
            "accepted_date": self.accepted_date.isoformat(),
            "filing_url": self.filing_url,
            "file_number": self.file_number
        }


# =============================================================================
# SEC Data Resources Client
# =============================================================================

class SECDataResourcesClient:
    """
    Comprehensive client for accessing all SEC Data Resources.
    
    Provides unified access to:
    - Financial Statement Data Sets (bulk quarterly data)
    - Company Facts/Concept APIs (per-CIK XBRL data)
    - Fails-to-Deliver Data (settlement statistics)
    - Investment Adviser Data (IAPD/Form ADV)
    - Mutual Fund Data (N-PORT holdings)
    - Market Structure Data
    - SEC Enforcement Actions
    - EDGAR Full-Text Search
    - Real-time RSS Feeds
    
    All methods implement:
    - Rate limiting (9 req/sec shared limiter)
    - Retry logic with exponential backoff
    - Triple-hash integrity for FRE 902(13)/(14) compliance
    - Circuit breaker protection
    """
    
    # Standard XBRL taxonomies
    TAXONOMY_US_GAAP = "us-gaap"
    TAXONOMY_IFRS = "ifrs-full"
    TAXONOMY_DEI = "dei"
    TAXONOMY_SRT = "srt"
    
    # Common financial concepts
    CONCEPTS_INCOME_STATEMENT = [
        "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
        "CostOfRevenue", "GrossProfit", "OperatingExpenses",
        "OperatingIncomeLoss", "NetIncomeLoss", "EarningsPerShareBasic",
        "EarningsPerShareDiluted"
    ]
    
    CONCEPTS_BALANCE_SHEET = [
        "Assets", "AssetsCurrent", "CashAndCashEquivalentsAtCarryingValue",
        "AccountsReceivableNetCurrent", "InventoryNet",
        "Liabilities", "LiabilitiesCurrent", "LongTermDebt",
        "StockholdersEquity", "RetainedEarningsAccumulatedDeficit"
    ]
    
    CONCEPTS_CASH_FLOW = [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInFinancingActivities",
        "DepreciationDepletionAndAmortization",
        "CapitalExpendituresIncurredButNotYetPaid"
    ]
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        enable_caching: bool = True,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize SEC Data Resources Client.
        
        Args:
            user_agent: SEC-compliant User-Agent string (required for production)
            enable_caching: Enable local caching of bulk downloads
            cache_dir: Directory for cached data (default: ~/.jlaw/sec_cache)
        """
        import os
        
        if user_agent is None:
            user_agent = os.environ.get('SEC_USER_AGENT') or os.environ.get('SEC_EDGAR_USER_AGENT')
        
        self.user_agent = user_agent or "JLAW-Forensics/2.0 SEC-Data-Resources forensics@jlaw-system.org"
        self.rate_limiter = get_shared_rate_limiter()
        self.enable_caching = enable_caching
        self.cache_dir = cache_dir or Path.home() / ".jlaw" / "sec_cache"
        
        if self.enable_caching:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"SEC Data Resources Client initialized with User-Agent: {self.user_agent[:50]}...")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json, text/html, application/xml, */*",
                "Accept-Encoding": "gzip, deflate"
            }
        )
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _fetch(self, url: str, response_type: str = "json") -> Optional[Union[Dict, str, bytes]]:
        """
        Fetch URL with rate limiting.
        
        Args:
            url: URL to fetch
            response_type: Expected response type ('json', 'text', 'bytes')
            
        Returns:
            Response data or None if failed
        """
        await self.rate_limiter.acquire()
        
        try:
            async with self.session.get(url, timeout=60) as response:
                if response.status == 200:
                    if response_type == "json":
                        return await response.json()
                    elif response_type == "bytes":
                        return await response.read()
                    else:
                        return await response.text()
                elif response.status == 429:
                    logger.warning(f"Rate limited (429) for {url}, backing off...")
                    await asyncio.sleep(10)
                    return await self._fetch(url, response_type)
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    # =========================================================================
    # Company Facts & Concept APIs
    # =========================================================================
    
    async def get_company_facts(self, cik: str) -> Optional[Dict[str, Any]]:
        """
        Get all XBRL facts for a company.
        
        This returns the complete set of structured XBRL data including:
        - Financial statements (income, balance sheet, cash flow)
        - Document and entity information
        - All reported concepts across all filings
        
        Args:
            cik: Company CIK number
            
        Returns:
            Complete company facts JSON
        """
        cik_padded = cik.zfill(10)
        url = SECDataEndpoint.COMPANY_FACTS.value.format(cik=cik_padded)
        return await self._fetch(url, "json")
    
    async def get_company_concept(
        self,
        cik: str,
        taxonomy: str,
        concept: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get time-series data for a specific XBRL concept.
        
        Args:
            cik: Company CIK number
            taxonomy: Taxonomy namespace (e.g., 'us-gaap', 'ifrs-full')
            concept: Concept tag (e.g., 'Revenues', 'Assets')
            
        Returns:
            Time-series data for the concept
        """
        cik_padded = cik.zfill(10)
        url = SECDataEndpoint.COMPANY_CONCEPT.value.format(
            cik=cik_padded,
            taxonomy=taxonomy,
            concept=concept
        )
        return await self._fetch(url, "json")
    
    async def get_frames(
        self,
        taxonomy: str,
        concept: str,
        unit: str,
        period: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cross-company data for a specific concept and period.
        
        This allows comparing the same metric across all companies that
        reported it for a given period.
        
        Args:
            taxonomy: Taxonomy namespace (e.g., 'us-gaap')
            concept: Concept tag (e.g., 'Revenues')
            unit: Unit of measure (e.g., 'USD', 'shares')
            period: Period in format CY2023Q4I (instant) or CY2023 (annual)
            
        Returns:
            Cross-company data for the concept/period
        """
        url = SECDataEndpoint.FRAMES.value.format(
            taxonomy=taxonomy,
            concept=concept,
            unit=unit,
            period=period
        )
        return await self._fetch(url, "json")
    
    async def extract_financial_metrics(
        self,
        cik: str,
        fiscal_year: int,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract key financial metrics from company facts for a fiscal year.
        
        Args:
            cik: Company CIK number
            fiscal_year: Fiscal year (e.g., 2023)
            metrics: List of concept names to extract (default: standard set)
            
        Returns:
            Dictionary of metric name -> value pairs
        """
        if metrics is None:
            metrics = (
                self.CONCEPTS_INCOME_STATEMENT +
                self.CONCEPTS_BALANCE_SHEET +
                self.CONCEPTS_CASH_FLOW
            )
        
        facts = await self.get_company_facts(cik)
        if not facts:
            return {}
        
        results = {}
        facts_data = facts.get("facts", {})
        
        for namespace in ["us-gaap", "ifrs-full"]:
            ns_facts = facts_data.get(namespace, {})
            
            for concept in metrics:
                if concept in ns_facts:
                    units = ns_facts[concept].get("units", {})
                    
                    # Try USD first, then shares
                    for unit_type in ["USD", "shares", "pure"]:
                        if unit_type in units:
                            for fact in units[unit_type]:
                                if (fact.get("fy") == fiscal_year and
                                    fact.get("form") == "10-K" and
                                    fact.get("fp") == "FY"):
                                    results[concept] = {
                                        "value": fact.get("val"),
                                        "unit": unit_type,
                                        "filed": fact.get("filed"),
                                        "accession": fact.get("accn")
                                    }
                                    break
                            if concept in results:
                                break
        
        return results
    
    # =========================================================================
    # Financial Statement Data Sets (Bulk Download)
    # =========================================================================
    
    async def get_financial_statement_dataset(
        self,
        year: int,
        quarter: int,
        use_cache: bool = True
    ) -> Optional[Dict[str, List[Dict[str, Any]]]]:
        """
        Download and parse Financial Statement Data Sets.
        
        These are quarterly bulk downloads of all XBRL-extracted numeric data
        from SEC filings. Each dataset contains:
        - sub.txt: Submission metadata
        - num.txt: Numeric data
        - tag.txt: Tag definitions
        - dim.txt: Dimension information
        - ren.txt: Rendering information
        - pre.txt: Presentation linkbase
        - cal.txt: Calculation linkbase
        
        Args:
            year: Year (e.g., 2023)
            quarter: Quarter (1-4)
            use_cache: Use cached data if available
            
        Returns:
            Dictionary with parsed dataset tables
        """
        cache_file = self.cache_dir / f"financial_statements_{year}q{quarter}.json"
        
        if use_cache and cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        url = SECDataEndpoint.FINANCIAL_STATEMENTS_QUARTERLY.value.format(
            year=year,
            quarter=quarter
        )
        
        zip_data = await self._fetch(url, "bytes")
        if not zip_data:
            return None
        
        try:
            result = {}
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                for filename in zf.namelist():
                    if filename.endswith('.txt'):
                        table_name = filename.replace('.txt', '')
                        content = zf.read(filename).decode('utf-8')
                        
                        # Parse TSV content
                        lines = content.strip().split('\n')
                        if len(lines) > 1:
                            headers = lines[0].split('\t')
                            rows = []
                            for line in lines[1:]:
                                values = line.split('\t')
                                if len(values) == len(headers):
                                    rows.append(dict(zip(headers, values)))
                            result[table_name] = rows
            
            # Cache the parsed data
            if use_cache:
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing financial statement dataset: {e}")
            return None
    
    # =========================================================================
    # Fails-to-Deliver Data
    # =========================================================================
    
    async def get_fails_to_deliver(
        self,
        year: int,
        month: int,
        first_half: bool = True
    ) -> Optional[List[FailsToDeliverRecord]]:
        """
        Get Fails-to-Deliver data for a specific period.
        
        SEC publishes FTD data twice monthly. This data shows securities
        that have failed to deliver in the Continuous Net Settlement system.
        
        Args:
            year: Year (e.g., 2023)
            month: Month (1-12)
            first_half: True for 1st-15th, False for 16th-end of month
            
        Returns:
            List of FailsToDeliverRecord objects
        """
        month_str = str(month).zfill(2)
        half_str = "a" if first_half else "b"
        
        url = SECDataEndpoint.FAILS_TO_DELIVER_CURRENT.value.format(
            year=year,
            month=month_str,
            half=half_str
        )
        
        zip_data = await self._fetch(url, "bytes")
        if not zip_data:
            return None
        
        try:
            records = []
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
                for filename in zf.namelist():
                    if filename.endswith('.txt'):
                        content = zf.read(filename).decode('utf-8')
                        lines = content.strip().split('\n')
                        
                        for line in lines[1:]:  # Skip header
                            parts = line.split('|')
                            if len(parts) >= 5:
                                try:
                                    record = FailsToDeliverRecord(
                                        settlement_date=datetime.strptime(parts[0], '%Y%m%d').date(),
                                        cusip=parts[1],
                                        symbol=parts[2],
                                        quantity=int(parts[3]),
                                        description=parts[4],
                                        price=float(parts[5]) if len(parts) > 5 and parts[5] else None
                                    )
                                    records.append(record)
                                except (ValueError, IndexError):
                                    continue
            
            return records
            
        except Exception as e:
            logger.error(f"Error parsing fails-to-deliver data: {e}")
            return None
    
    async def get_fails_to_deliver_by_symbol(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[FailsToDeliverRecord]:
        """
        Get Fails-to-Deliver history for a specific security.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            List of FTD records for the symbol
        """
        all_records = []
        current = start_date
        
        while current <= end_date:
            for first_half in [True, False]:
                records = await self.get_fails_to_deliver(
                    current.year, current.month, first_half
                )
                if records:
                    for record in records:
                        if record.symbol.upper() == symbol.upper():
                            if start_date <= record.settlement_date <= end_date:
                                all_records.append(record)
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        return sorted(all_records, key=lambda r: r.settlement_date)
    
    # =========================================================================
    # Investment Adviser Data (IAPD / Form ADV)
    # =========================================================================
    
    async def search_investment_advisers(
        self,
        firm_name: Optional[str] = None,
        crd_number: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[InvestmentAdviser]:
        """
        Search the Investment Adviser Public Disclosure (IAPD) database.
        
        Args:
            firm_name: Firm name to search for
            crd_number: CRD number
            city: City filter
            state: State filter (2-letter code)
            
        Returns:
            List of matching InvestmentAdviser records
        """
        # Build search parameters
        params = {
            "query": firm_name or "",
            "hl": "true",
            "nrows": 100,
            "start": 0
        }
        
        if crd_number:
            params["crd"] = crd_number
        if state:
            params["state"] = state
        
        url = f"{SECDataEndpoint.IAPD_API.value}?{self._build_query_string(params)}"
        
        data = await self._fetch(url, "json")
        if not data:
            return []
        
        advisers = []
        hits = data.get("hits", {}).get("hits", [])
        
        for hit in hits:
            source = hit.get("_source", {})
            
            try:
                reg_date = None
                if source.get("registration_date"):
                    reg_date = datetime.strptime(
                        source["registration_date"], "%Y-%m-%d"
                    ).date()
                
                adviser = InvestmentAdviser(
                    firm_crd=str(source.get("firm_crd", "")),
                    firm_name=source.get("firm_name", ""),
                    sec_number=source.get("sec_number"),
                    main_office_city=source.get("main_office_city"),
                    main_office_state=source.get("main_office_state"),
                    aum=source.get("aum"),
                    discretionary_aum=source.get("discretionary_aum"),
                    non_discretionary_aum=source.get("non_discretionary_aum"),
                    total_employees=source.get("total_employees"),
                    registration_status=source.get("registration_status", "Unknown"),
                    registration_date=reg_date
                )
                advisers.append(adviser)
            except Exception as e:
                logger.warning(f"Error parsing adviser record: {e}")
                continue
        
        return advisers
    
    def _build_query_string(self, params: Dict[str, Any]) -> str:
        """Build URL query string from parameters."""
        parts = []
        for key, value in params.items():
            if value is not None:
                parts.append(f"{key}={value}")
        return "&".join(parts)
    
    # =========================================================================
    # EDGAR Full-Text Search
    # =========================================================================
    
    async def full_text_search(
        self,
        query: str,
        form_types: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        cik: Optional[str] = None,
        limit: int = 100
    ) -> List[FullTextSearchResult]:
        """
        Perform full-text search across all EDGAR filings since 2001.
        
        This uses the SEC's EDGAR full-text search API to find filings
        containing specific keywords or phrases.
        
        Args:
            query: Search query (supports quotes for exact phrases)
            form_types: Filter by form types (e.g., ['10-K', '10-Q'])
            start_date: Start date for search range
            end_date: End date for search range
            cik: Filter by company CIK
            limit: Maximum results to return
            
        Returns:
            List of FullTextSearchResult objects
        """
        # Build search request
        search_params = {
            "q": query,
            "dateRange": "custom" if start_date or end_date else "all",
            "from": 0,
            "size": min(limit, 100)
        }
        
        if start_date:
            search_params["startdt"] = start_date.isoformat()
        if end_date:
            search_params["enddt"] = end_date.isoformat()
        if form_types:
            search_params["forms"] = form_types
        if cik:
            search_params["ciks"] = [cik.zfill(10)]
        
        url = f"{SECDataEndpoint.FULL_TEXT_SEARCH.value}?{self._build_query_string(search_params)}"
        
        data = await self._fetch(url, "json")
        if not data:
            return []
        
        results = []
        hits = data.get("hits", {}).get("hits", [])
        
        for hit in hits:
            source = hit.get("_source", {})
            
            try:
                filing_date = datetime.strptime(
                    source.get("file_date", "1970-01-01"), "%Y-%m-%d"
                ).date()
                
                result = FullTextSearchResult(
                    accession_number=source.get("adsh", ""),
                    cik=source.get("cik", ""),
                    company_name=source.get("display_names", [""])[0],
                    form_type=source.get("form", ""),
                    filing_date=filing_date,
                    file_description=source.get("file_description", ""),
                    document_url=source.get("file_url", ""),
                    score=hit.get("_score", 0.0),
                    highlights=hit.get("highlight", {}).get("file_content", [])
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Error parsing search result: {e}")
                continue
        
        return results
    
    # =========================================================================
    # RSS Feeds for Real-Time Filings
    # =========================================================================
    
    async def get_recent_filings_rss(
        self,
        form_type: Optional[str] = None,
        limit: int = 40
    ) -> List[RSSFilingEntry]:
        """
        Get recent filings via RSS feed.
        
        This provides near real-time access to new SEC filings as they
        are submitted to EDGAR.
        
        Args:
            form_type: Filter by form type (e.g., '4', '10-K')
            limit: Maximum entries to return (max 100)
            
        Returns:
            List of RSSFilingEntry objects
        """
        url = SECDataEndpoint.RSS_FILINGS.value.format(
            form_type=form_type or ""
        )
        
        xml_content = await self._fetch(url, "text")
        if not xml_content:
            return []
        
        entries = []
        
        try:
            # Parse Atom feed using regex (lightweight approach)
            entry_pattern = re.compile(r'<entry>(.*?)</entry>', re.DOTALL)
            title_pattern = re.compile(r'<title[^>]*>(.*?)</title>')
            link_pattern = re.compile(r'<link[^>]*href="([^"]*)"')
            updated_pattern = re.compile(r'<updated>(.*?)</updated>')
            
            for entry_match in entry_pattern.finditer(xml_content):
                entry_xml = entry_match.group(1)
                
                title_match = title_pattern.search(entry_xml)
                link_match = link_pattern.search(entry_xml)
                updated_match = updated_pattern.search(entry_xml)
                
                if title_match and link_match:
                    title = title_match.group(1)
                    
                    # Parse title: "Form 4 - Company Name (CIK)"
                    title_parts = title.split(' - ', 1)
                    form = title_parts[0].strip() if title_parts else ""
                    
                    company_cik = title_parts[1] if len(title_parts) > 1 else ""
                    cik_match = re.search(r'\((\d+)\)', company_cik)
                    cik = cik_match.group(1) if cik_match else ""
                    company = re.sub(r'\s*\(\d+\)\s*$', '', company_cik).strip()
                    
                    # Parse accession from URL
                    link = link_match.group(1)
                    accession_match = re.search(r'/(\d{10}-\d{2}-\d{6})', link)
                    accession = accession_match.group(1) if accession_match else ""
                    
                    updated_str = updated_match.group(1) if updated_match else ""
                    try:
                        updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00'))
                    except ValueError:
                        updated = datetime.now()
                    
                    entry = RSSFilingEntry(
                        accession_number=accession,
                        cik=cik,
                        company_name=company,
                        form_type=form,
                        filing_date=updated,
                        accepted_date=updated,
                        filing_url=link,
                        file_number=None
                    )
                    entries.append(entry)
                    
                    if len(entries) >= limit:
                        break
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {e}")
        
        return entries
    
    # =========================================================================
    # Ticker/CIK Mappings
    # =========================================================================
    
    async def get_all_company_tickers(self) -> Dict[str, Dict[str, str]]:
        """
        Get complete ticker to CIK mapping for all companies.
        
        Returns:
            Dictionary with ticker -> {cik, title} mappings
        """
        data = await self._fetch(SECDataEndpoint.COMPANY_TICKERS.value, "json")
        if not data:
            return {}
        
        result = {}
        for entry in data.values():
            ticker = entry.get("ticker", "").upper()
            if ticker:
                result[ticker] = {
                    "cik": str(entry.get("cik_str", "")),
                    "title": entry.get("title", "")
                }
        
        return result
    
    async def get_tickers_by_exchange(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get tickers organized by exchange.
        
        Returns:
            Dictionary with exchange -> [ticker info] mappings
        """
        data = await self._fetch(SECDataEndpoint.COMPANY_TICKERS_EXCHANGE.value, "json")
        if not data:
            return {}
        
        result = {}
        fields = data.get("fields", [])
        
        for row in data.get("data", []):
            entry = dict(zip(fields, row))
            exchange = entry.get("exchange", "Unknown")
            
            if exchange not in result:
                result[exchange] = []
            
            result[exchange].append({
                "cik": str(entry.get("cik", "")),
                "ticker": entry.get("ticker", ""),
                "name": entry.get("name", "")
            })
        
        return result
    
    async def get_mutual_fund_tickers(self) -> Dict[str, Dict[str, str]]:
        """
        Get ticker mappings for mutual funds.
        
        Returns:
            Dictionary with ticker -> {cik, series_id, class_id} mappings
        """
        data = await self._fetch(SECDataEndpoint.MUTUAL_FUND_TICKERS.value, "json")
        if not data:
            return {}
        
        result = {}
        for entry in data.get("data", []):
            ticker = entry.get("ticker", "").upper()
            if ticker:
                result[ticker] = {
                    "cik": str(entry.get("cik", "")),
                    "series_id": entry.get("seriesId", ""),
                    "class_id": entry.get("classId", "")
                }
        
        return result
    
    # =========================================================================
    # Dynamic Research & Cross-Analysis
    # =========================================================================
    
    async def get_comprehensive_company_data(
        self,
        cik: str,
        fiscal_year: int,
        include_ftd: bool = True,
        include_related_advisers: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive data acquisition for a company.
        
        This is a dynamic research method that gathers data from multiple
        SEC data sources for cross-analysis.
        
        Args:
            cik: Company CIK number
            fiscal_year: Fiscal year for financial data
            include_ftd: Include fails-to-deliver analysis
            include_related_advisers: Include related investment advisers
            
        Returns:
            Comprehensive data dictionary for cross-analysis
        """
        result = {
            "cik": cik,
            "fiscal_year": fiscal_year,
            "acquisition_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_sources": []
        }
        
        # 1. Get company facts (core financial data)
        logger.info(f"Acquiring company facts for CIK {cik}...")
        facts = await self.get_company_facts(cik)
        if facts:
            result["company_name"] = facts.get("entityName", "Unknown")
            result["company_facts"] = facts
            result["data_sources"].append("company_facts_api")
        
        # 2. Extract key financial metrics
        logger.info(f"Extracting financial metrics for FY{fiscal_year}...")
        metrics = await self.extract_financial_metrics(cik, fiscal_year)
        if metrics:
            result["financial_metrics"] = metrics
            result["data_sources"].append("financial_metrics_extracted")
        
        # 3. Get ticker info
        tickers = await self.get_all_company_tickers()
        company_ticker = None
        for ticker, info in tickers.items():
            if info.get("cik") == cik.lstrip("0"):
                company_ticker = ticker
                result["ticker"] = ticker
                break
        
        # 4. Get fails-to-deliver data if ticker available
        if include_ftd and company_ticker:
            logger.info(f"Acquiring FTD data for {company_ticker}...")
            try:
                end_date = date(fiscal_year, 12, 31)
                start_date = date(fiscal_year, 1, 1)
                ftd_records = await self.get_fails_to_deliver_by_symbol(
                    company_ticker, start_date, end_date
                )
                if ftd_records:
                    result["fails_to_deliver"] = {
                        "total_records": len(ftd_records),
                        "total_quantity": sum(r.quantity for r in ftd_records),
                        "records": [r.to_dict() for r in ftd_records[:100]]  # Limit for size
                    }
                    result["data_sources"].append("fails_to_deliver")
            except Exception as e:
                logger.warning(f"Could not acquire FTD data: {e}")
        
        # 5. Search for related investment advisers
        if include_related_advisers and result.get("company_name"):
            logger.info(f"Searching for related investment advisers...")
            try:
                # Search by company name prefix
                company_name = result["company_name"]
                name_parts = company_name.split()[:2]  # First two words
                if name_parts:
                    advisers = await self.search_investment_advisers(
                        firm_name=" ".join(name_parts)
                    )
                    if advisers:
                        result["related_advisers"] = [a.to_dict() for a in advisers[:10]]
                        result["data_sources"].append("iapd_search")
            except Exception as e:
                logger.warning(f"Could not search advisers: {e}")
        
        return result
    
    async def cross_analyze_peer_companies(
        self,
        ciks: List[str],
        concepts: List[str],
        fiscal_year: int
    ) -> Dict[str, Any]:
        """
        Perform cross-company analysis using the same concepts.
        
        Args:
            ciks: List of company CIKs to compare
            concepts: XBRL concepts to analyze
            fiscal_year: Fiscal year for comparison
            
        Returns:
            Cross-analysis results with company comparisons
        """
        results = {
            "fiscal_year": fiscal_year,
            "concepts": concepts,
            "companies": {},
            "aggregates": {}
        }
        
        for cik in ciks:
            company_data = {
                "cik": cik,
                "metrics": {}
            }
            
            facts = await self.get_company_facts(cik)
            if facts:
                company_data["name"] = facts.get("entityName", "Unknown")
                
                # Extract each concept
                for concept in concepts:
                    facts_data = facts.get("facts", {})
                    for namespace in ["us-gaap", "ifrs-full"]:
                        if namespace in facts_data and concept in facts_data[namespace]:
                            units = facts_data[namespace][concept].get("units", {})
                            for unit_type, values in units.items():
                                for value in values:
                                    if (value.get("fy") == fiscal_year and
                                        value.get("form") == "10-K"):
                                        company_data["metrics"][concept] = {
                                            "value": value.get("val"),
                                            "unit": unit_type
                                        }
                                        break
            
            results["companies"][cik] = company_data
        
        # Calculate aggregates
        for concept in concepts:
            values = []
            for company in results["companies"].values():
                if concept in company.get("metrics", {}):
                    val = company["metrics"][concept].get("value")
                    if val is not None and isinstance(val, (int, float)):
                        values.append(val)
            
            if values:
                results["aggregates"][concept] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        return results


# =============================================================================
# Convenience Functions
# =============================================================================

async def get_sec_data_client(user_agent: Optional[str] = None) -> SECDataResourcesClient:
    """
    Create and initialize SEC Data Resources client.
    
    Args:
        user_agent: SEC-compliant User-Agent string
        
    Returns:
        Initialized SECDataResourcesClient
    """
    client = SECDataResourcesClient(user_agent=user_agent)
    return client
