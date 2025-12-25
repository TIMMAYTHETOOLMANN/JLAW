"""
SEC EDGAR Client for 13F-HR Filings
===================================

Fetches and parses 13F-HR institutional holdings filings from SEC EDGAR API.
Complies with SEC rate limiting (10 requests/second).
Uses shared rate limiter from src.integrations.sec_edgar.rate_limiter.

SEC Reference: https://www.sec.gov/edgar/sec-api-documentation
"""

import asyncio
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import xml.etree.ElementTree as ET
import aiohttp

# Import shared rate limiter from central module
from src.integrations.sec_edgar.rate_limiter import get_shared_rate_limiter

logger = logging.getLogger(__name__)


@dataclass
class Institution13FHoldingV2:
    """Enhanced 13F holding record with quarterly comparison."""
    cik: str
    institution_name: str
    filing_date: date
    reporting_period: date
    quarter: str  # "2024Q4"
    cusip: str
    issuer_name: str
    shares: int
    value_thousands: int
    investment_discretion: str  # SOLE, SHARED, DFND
    voting_authority_sole: int
    voting_authority_shared: int
    voting_authority_none: int
    
    # Enhanced fields
    previous_quarter_shares: Optional[int] = None
    quarter_over_quarter_change: Optional[float] = None
    sector: Optional[str] = None
    market_cap_category: Optional[str] = None  # Large/Mid/Small
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cik": self.cik,
            "institution_name": self.institution_name,
            "filing_date": self.filing_date.isoformat(),
            "reporting_period": self.reporting_period.isoformat(),
            "quarter": self.quarter,
            "cusip": self.cusip,
            "issuer_name": self.issuer_name,
            "shares": self.shares,
            "value_thousands": self.value_thousands,
            "investment_discretion": self.investment_discretion,
            "previous_quarter_shares": self.previous_quarter_shares,
            "quarter_over_quarter_change": self.quarter_over_quarter_change,
            "sector": self.sector,
            "market_cap_category": self.market_cap_category
        }


class SECEDGARClient:
    """
    SEC EDGAR API client for 13F-HR filings.
    
    Features:
    - Rate limiting compliance (10 requests/second)
    - Historical and real-time filing retrieval
    - XML/JSON parsing
    - Quarterly holdings comparison
    """
    
    BASE_URL = "https://data.sec.gov"
    SUBMISSIONS_ENDPOINT = "/submissions/CIK{cik}.json"
    
    def __init__(self, user_agent: str = "JLAW-Forensics/2.0 Timothy_Johnson forensics@jlaw-system.org"):
        """
        Initialize SEC EDGAR client.
        
        Args:
            user_agent: Required SEC user agent string
        """
        self.user_agent = user_agent
        # Use shared rate limiter (singleton) to coordinate with all other SEC API clients
        self.rate_limiter = get_shared_rate_limiter()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_13f_filings(
        self,
        cik: str,
        quarters: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Fetch 13F-HR filings for an institution.
        
        Args:
            cik: Central Index Key (CIK) for the institution
            quarters: Number of quarters to retrieve (default: 4)
            
        Returns:
            List of 13F filing metadata dictionaries
        """
        logger.info(f"Fetching 13F filings for CIK {cik}, last {quarters} quarters")
        
        # Normalize CIK (10 digits with leading zeros)
        cik_normalized = cik.zfill(10)
        
        async with self.rate_limiter:
            url = f"{self.BASE_URL}{self.SUBMISSIONS_ENDPOINT.format(cik=cik_normalized)}"
            
            if not self.session:
                self.session = aiohttp.ClientSession(
                    headers={"User-Agent": self.user_agent}
                )
            
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"SEC API error: {response.status} for CIK {cik}")
                        return []
                    
                    data = await response.json()
                    
                    # Extract 13F-HR filings
                    filings_13f = []
                    recent = data.get("filings", {}).get("recent", {})
                    
                    if not recent:
                        logger.warning(f"No recent filings found for CIK {cik}")
                        return []
                    
                    forms = recent.get("form", [])
                    filing_dates = recent.get("filingDate", [])
                    accession_numbers = recent.get("accessionNumber", [])
                    primary_docs = recent.get("primaryDocument", [])
                    
                    for i, form in enumerate(forms):
                        if form in ["13F-HR", "13F-HR/A"]:
                            filings_13f.append({
                                "form": form,
                                "filing_date": filing_dates[i],
                                "accession_number": accession_numbers[i],
                                "primary_document": primary_docs[i] if i < len(primary_docs) else None,
                                "cik": cik
                            })
                            
                            if len(filings_13f) >= quarters:
                                break
                    
                    logger.info(f"Found {len(filings_13f)} 13F filings for CIK {cik}")
                    return filings_13f
                    
            except Exception as e:
                logger.error(f"Error fetching 13F filings for CIK {cik}: {e}")
                return []
    
    async def fetch_latest_13f(self, cik: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the latest 13F-HR filing for an institution.
        
        Args:
            cik: Central Index Key (CIK)
            
        Returns:
            Latest 13F filing metadata or None
        """
        filings = await self.fetch_13f_filings(cik, quarters=1)
        return filings[0] if filings else None
    
    async def search_13f_by_cusip(
        self,
        cusip: str,
        institutions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search 13F filings for specific CUSIP across multiple institutions.
        
        Args:
            cusip: CUSIP identifier
            institutions: List of institution CIKs to search
            
        Returns:
            List of holdings matching the CUSIP
        """
        logger.info(f"Searching for CUSIP {cusip} across {len(institutions)} institutions")
        
        results = []
        for cik in institutions:
            filings = await self.fetch_13f_filings(cik, quarters=1)
            if filings:
                # In a real implementation, we would fetch and parse the filing XML
                # to extract holdings with matching CUSIP
                results.append({
                    "cik": cik,
                    "cusip": cusip,
                    "filing": filings[0]
                })
        
        return results
    
    def parse_13f_xml(self, xml_content: str, cik: str) -> List[Institution13FHoldingV2]:
        """
        Parse 13F-HR XML filing to extract holdings.
        
        Args:
            xml_content: XML content string
            cik: Institution CIK
            
        Returns:
            List of Institution13FHoldingV2 objects
        """
        holdings = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Extract reporting period
            reporting_period_elem = root.find(".//{*}reportingPeriodEndDate")
            if reporting_period_elem is not None:
                reporting_period_str = reporting_period_elem.text
                reporting_period = datetime.strptime(reporting_period_str, "%Y-%m-%d").date()
            else:
                reporting_period = date.today()
            
            # Calculate quarter
            quarter = self._get_quarter_string(reporting_period)
            
            # Extract filing date
            filing_date_elem = root.find(".//{*}filingDate")
            if filing_date_elem is not None:
                filing_date = datetime.strptime(filing_date_elem.text, "%Y-%m-%d").date()
            else:
                filing_date = date.today()
            
            # Extract institution name
            filer_elem = root.find(".//{*}filerInfo/{*}filerName")
            institution_name = filer_elem.text if filer_elem is not None else "Unknown"
            
            # Extract individual holdings (infoTable entries)
            for info_table in root.findall(".//{*}infoTable"):
                try:
                    # Extract holding details
                    cusip_elem = info_table.find("{*}cusip")
                    issuer_elem = info_table.find("{*}nameOfIssuer")
                    shares_elem = info_table.find("{*}shrsOrPrnAmt/{*}sshPrnamt")
                    value_elem = info_table.find("{*}value")
                    discretion_elem = info_table.find("{*}investmentDiscretion")
                    
                    # Voting authority
                    voting_sole_elem = info_table.find("{*}votingAuthority/{*}Sole")
                    voting_shared_elem = info_table.find("{*}votingAuthority/{*}Shared")
                    voting_none_elem = info_table.find("{*}votingAuthority/{*}None")
                    
                    if cusip_elem is None or shares_elem is None:
                        continue
                    
                    holding = Institution13FHoldingV2(
                        cik=cik,
                        institution_name=institution_name,
                        filing_date=filing_date,
                        reporting_period=reporting_period,
                        quarter=quarter,
                        cusip=cusip_elem.text,
                        issuer_name=issuer_elem.text if issuer_elem is not None else "Unknown",
                        shares=int(shares_elem.text),
                        value_thousands=int(value_elem.text) if value_elem is not None else 0,
                        investment_discretion=discretion_elem.text if discretion_elem is not None else "SOLE",
                        voting_authority_sole=int(voting_sole_elem.text) if voting_sole_elem is not None else 0,
                        voting_authority_shared=int(voting_shared_elem.text) if voting_shared_elem is not None else 0,
                        voting_authority_none=int(voting_none_elem.text) if voting_none_elem is not None else 0
                    )
                    
                    holdings.append(holding)
                    
                except Exception as e:
                    logger.warning(f"Error parsing individual holding: {e}")
                    continue
            
            logger.info(f"Parsed {len(holdings)} holdings from 13F XML")
            return holdings
            
        except Exception as e:
            logger.error(f"Error parsing 13F XML: {e}")
            return []
    
    def _get_quarter_string(self, d: date) -> str:
        """
        Convert date to quarter string (e.g., "2024Q4").
        
        Args:
            d: Date object
            
        Returns:
            Quarter string
        """
        quarter = (d.month - 1) // 3 + 1
        return f"{d.year}Q{quarter}"
    
    async def fetch_and_parse_filing(
        self,
        accession_number: str,
        cik: str
    ) -> List[Institution13FHoldingV2]:
        """
        Fetch and parse a specific 13F filing.
        
        Args:
            accession_number: SEC accession number
            cik: Institution CIK
            
        Returns:
            List of holdings from the filing
        """
        # Remove hyphens from accession number for URL
        acc_no_url = accession_number.replace("-", "")
        
        # Construct primary document URL
        # Format: https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{primary_doc}
        url = f"{self.BASE_URL}/Archives/edgar/data/{cik}/{acc_no_url}/{accession_number}.txt"
        
        async with self.rate_limiter:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    headers={"User-Agent": self.user_agent}
                )
            
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching filing: {response.status}")
                        return []
                    
                    content = await response.text()
                    return self.parse_13f_xml(content, cik)
                    
            except Exception as e:
                logger.error(f"Error fetching/parsing filing {accession_number}: {e}")
                return []
