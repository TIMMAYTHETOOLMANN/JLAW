"""
SEC EDGAR Integrator - Deep SEC Filing Analysis
===============================================

Advanced SEC EDGAR integration with:
- Complete filing retrieval (10-K, 10-Q, 8-K, DEF 14A, Form 4, Form 3, Form 5)
- XBRL parsing and financial data extraction
- SEC compliance (10 req/sec limit, User-Agent requirements)
- Filing history analysis and trend detection
- Insider trading pattern analysis (Form 4/Form 3/Form 5)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import re
import time
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class SECFiling:
    """SEC Filing metadata and content"""
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filing_date: datetime
    report_date: Optional[datetime] = None
    file_number: str = ""
    
    # Content
    full_text: str = ""
    exhibits: Dict[str, str] = field(default_factory=dict)
    financial_data: Dict[str, Any] = field(default_factory=dict)
    
    # Analysis
    confidence: float = 0.0
    extraction_method: str = ""
    parsed_successfully: bool = False


@dataclass
class InsiderTransaction:
    """Form 4 insider transaction"""
    transaction_date: datetime
    person_name: str
    person_relationship: str  # Officer, Director, 10% Owner
    security_title: str
    transaction_code: str  # P=Purchase, S=Sale, A=Award, etc.
    shares: float
    price_per_share: float
    shares_owned_after: float
    transaction_value: float
    is_direct: bool
    
    def __post_init__(self):
        self.transaction_value = self.shares * self.price_per_share


class SECEdgarIntegrator:
    """
    Advanced SEC EDGAR integration with compliance and intelligence features
    """
    
    BASE_URL = "https://www.sec.gov"
    RATE_LIMIT = 10  # requests per second (SEC requirement)
    
    def __init__(self, user_agent: str = "JLAW Forensic System forensics@jlaw.ai"):
        """
        Initialize SEC EDGAR integrator
        
        Args:
            user_agent: User-Agent header (SEC requires company name + email)
        """
        self.user_agent = user_agent
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = asyncio.Semaphore(self.RATE_LIMIT)
        self._last_request_time = 0.0
        
        # Statistics
        self.stats = {
            'filings_retrieved': 0,
            'xbrl_parsed': 0,
            'insider_transactions': 0,
            'rate_limit_delays': 0,
            'errors': 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limited_request(self, url: str) -> str:
        """Execute rate-limited HTTP request"""
        async with self._rate_limiter:
            # Enforce minimum delay between requests
            current_time = time.time()
            elapsed = current_time - self._last_request_time
            min_delay = 1.0 / self.RATE_LIMIT
            
            if elapsed < min_delay:
                await asyncio.sleep(min_delay - elapsed)
                self.stats['rate_limit_delays'] += 1
            
            self._last_request_time = time.time()
            
            # Execute request
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    logger.warning("⚠️ SEC rate limit hit, backing off...")
                    await asyncio.sleep(10)
                    return await self._rate_limited_request(url)
                else:
                    logger.error(f"❌ SEC request failed: {response.status}")
                    self.stats['errors'] += 1
                    return ""
    
    async def get_company_filings(
        self,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        form_types: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        max_filings: int = 100
    ) -> List[SECFiling]:
        """
        Retrieve company filings from SEC EDGAR
        
        Args:
            ticker: Company ticker symbol
            cik: Company CIK number (alternative to ticker)
            form_types: List of form types to retrieve (e.g., ['10-K', '10-Q', '8-K'])
            date_from: Start date for filing search
            date_to: End date for filing search
            max_filings: Maximum number of filings to retrieve
        
        Returns:
            List of SECFiling objects
        """
        if not ticker and not cik:
            raise ValueError("Must provide either ticker or CIK")
        
        # Get CIK if ticker provided
        if ticker and not cik:
            cik = await self._get_cik_from_ticker(ticker)
            if not cik:
                logger.error(f"❌ Could not resolve ticker {ticker} to CIK")
                return []
        
        # Pad CIK to 10 digits
        cik = cik.zfill(10)
        
        logger.info(f"📄 Retrieving SEC filings for CIK {cik}")
        
        # Get filing index
        filings_url = f"{self.BASE_URL}/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'CIK': cik,
            'type': '',
            'dateb': '',
            'owner': 'exclude',
            'count': max_filings,
            'output': 'atom'
        }
        
        # Build URL with params
        param_str = '&'.join(f"{k}={v}" for k, v in params.items())
        index_url = f"{filings_url}?{param_str}"
        
        # Retrieve filing index
        index_xml = await self._rate_limited_request(index_url)
        if not index_xml:
            return []
        
        # Parse filing index
        filings = self._parse_filing_index(index_xml, form_types, date_from, date_to)
        
        logger.info(f"✓ Found {len(filings)} filings matching criteria")
        
        # Retrieve full filing content (in parallel with rate limiting)
        tasks = [self._retrieve_filing_content(filing) for filing in filings]
        await asyncio.gather(*tasks)
        
        self.stats['filings_retrieved'] += len(filings)
        
        return filings
    
    async def _get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Resolve ticker symbol to CIK using SEC company tickers JSON"""
        url = f"{self.BASE_URL}/files/company_tickers.json"
        
        try:
            data = await self._rate_limited_request(url)
            if data:
                tickers_data = json.loads(data)
                
                # Search for ticker
                for entry in tickers_data.values():
                    if entry.get('ticker', '').upper() == ticker.upper():
                        return str(entry['cik_str'])
        except Exception as e:
            logger.error(f"❌ Ticker resolution failed: {e}")
        
        return None
    
    def _parse_filing_index(
        self,
        xml_content: str,
        form_types: Optional[List[str]],
        date_from: Optional[datetime],
        date_to: Optional[datetime]
    ) -> List[SECFiling]:
        """Parse ATOM feed of filing index"""
        filings = []
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # ATOM namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # Extract entries
            for entry in root.findall('.//atom:entry', ns):
                # Extract fields
                filing_type = entry.find('.//atom:category', ns)
                filing_type = filing_type.get('term') if filing_type is not None else ""
                
                # Filter by form type
                if form_types and filing_type not in form_types:
                    continue
                
                # Extract filing date
                filing_date_str = entry.find('.//atom:updated', ns)
                if filing_date_str is not None:
                    filing_date = datetime.fromisoformat(filing_date_str.text.replace('Z', '+00:00'))
                else:
                    continue
                
                # Filter by date
                if date_from and filing_date < date_from:
                    continue
                if date_to and filing_date > date_to:
                    continue
                
                # Extract other fields
                title = entry.find('.//atom:title', ns)
                company_name = title.text if title is not None else ""
                
                # Extract accession number from link
                link = entry.find('.//atom:link', ns)
                url = link.get('href') if link is not None else ""
                
                # Parse accession number from URL
                accession_match = re.search(r'data/(\d+)/(\d+-\d+-\d+)', url)
                if accession_match:
                    cik = accession_match.group(1)
                    accession_number = accession_match.group(2)
                else:
                    continue
                
                filing = SECFiling(
                    accession_number=accession_number,
                    cik=cik,
                    company_name=company_name,
                    form_type=filing_type,
                    filing_date=filing_date
                )
                
                filings.append(filing)
        
        except ET.ParseError as e:
            logger.error(f"❌ XML parsing failed: {e}")
        
        return filings
    
    async def _retrieve_filing_content(self, filing: SECFiling):
        """Retrieve full content of a filing"""
        # Build filing URL
        accession_no_dashes = filing.accession_number.replace('-', '')
        filing_url = f"{self.BASE_URL}/Archives/edgar/data/{filing.cik}/{accession_no_dashes}/{filing.accession_number}.txt"
        
        # Retrieve content
        content = await self._rate_limited_request(filing_url)
        
        if content:
            filing.full_text = content
            filing.parsed_successfully = True
            
            # Extract XBRL data if available
            if filing.form_type in ['10-K', '10-Q']:
                await self._extract_xbrl_data(filing)
    
    async def _extract_xbrl_data(self, filing: SECFiling):
        """Extract financial data from XBRL"""
        # Build XBRL instance document URL
        accession_no_dashes = filing.accession_number.replace('-', '')
        
        # Try common XBRL file patterns
        xbrl_patterns = [
            f"{accession_no_dashes}.xml",
            f"{filing.cik}-{filing.filing_date.strftime('%Y%m%d')}.xml",
        ]
        
        for pattern in xbrl_patterns:
            xbrl_url = f"{self.BASE_URL}/Archives/edgar/data/{filing.cik}/{accession_no_dashes}/{pattern}"
            
            xbrl_content = await self._rate_limited_request(xbrl_url)
            
            if xbrl_content and '<xbrli:xbrl' in xbrl_content:
                financial_data = self._parse_xbrl(xbrl_content)
                if financial_data:
                    filing.financial_data = financial_data
                    filing.extraction_method = "XBRL"
                    filing.confidence = 0.95
                    self.stats['xbrl_parsed'] += 1
                    break
    
    def _parse_xbrl(self, xbrl_content: str) -> Dict[str, Any]:
        """Parse XBRL instance document for financial data"""
        financial_data = {}
        
        try:
            root = ET.fromstring(xbrl_content)
            
            # Common XBRL namespaces
            namespaces = {
                'xbrli': 'http://www.xbrl.org/2003/instance',
                'us-gaap': 'http://fasb.org/us-gaap/2023',
                'dei': 'http://xbrl.sec.gov/dei/2023'
            }
            
            # Extract common financial metrics
            metrics = {
                'Revenues': ['us-gaap:Revenues', 'us-gaap:SalesRevenueNet'],
                'NetIncomeLoss': ['us-gaap:NetIncomeLoss', 'us-gaap:ProfitLoss'],
                'Assets': ['us-gaap:Assets'],
                'Liabilities': ['us-gaap:Liabilities'],
                'StockholdersEquity': ['us-gaap:StockholdersEquity'],
                'OperatingCashFlow': ['us-gaap:NetCashProvidedByUsedInOperatingActivities'],
                'EarningsPerShare': ['us-gaap:EarningsPerShareBasic']
            }
            
            for metric_name, xbrl_tags in metrics.items():
                for tag in xbrl_tags:
                    # Search for tag
                    elements = root.findall(f".//{tag}", namespaces)
                    if elements:
                        # Get most recent value
                        value = elements[0].text
                        if value:
                            try:
                                financial_data[metric_name] = float(value)
                                break
                            except ValueError:
                                pass
        
        except ET.ParseError as e:
            logger.error(f"❌ XBRL parsing failed: {e}")
        
        return financial_data
    
    async def get_insider_transactions(
        self,
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        date_from: Optional[datetime] = None,
        lookback_days: int = 365
    ) -> List[InsiderTransaction]:
        """
        Retrieve insider transactions (Form 4, Form 3, Form 5)
        
        Returns:
            List of InsiderTransaction objects
        """
        if not date_from:
            date_from = datetime.now() - timedelta(days=lookback_days)
        
        # Get Form 4 filings
        form_4_filings = await self.get_company_filings(
            ticker=ticker,
            cik=cik,
            form_types=['4', '3', '5'],
            date_from=date_from
        )
        
        logger.info(f"📊 Processing {len(form_4_filings)} insider transaction filings")
        
        # Parse transactions
        transactions = []
        for filing in form_4_filings:
            filing_transactions = self._parse_form4(filing)
            transactions.extend(filing_transactions)
        
        self.stats['insider_transactions'] += len(transactions)
        
        logger.info(f"✓ Extracted {len(transactions)} insider transactions")
        
        return transactions
    
    def _parse_form4(self, filing: SECFiling) -> List[InsiderTransaction]:
        """Parse Form 4 insider transaction filing"""
        transactions = []
        
        try:
            # Extract XML portion (Form 4 has XML embedded)
            xml_match = re.search(r'<ownershipDocument>.*?</ownershipDocument>', 
                                 filing.full_text, re.DOTALL)
            
            if not xml_match:
                return []
            
            root = ET.fromstring(xml_match.group(0))
            
            # Extract reporting owner
            owner_name = ""
            owner_relationship = []
            
            reporting_owner = root.find('.//reportingOwner')
            if reporting_owner:
                name_elem = reporting_owner.find('.//rptOwnerName')
                if name_elem is not None:
                    owner_name = name_elem.text or ""
                
                # Get relationship
                rel_info = reporting_owner.find('.//reportingOwnerRelationship')
                if rel_info is not None:
                    if rel_info.find('.//isDirector') is not None:
                        owner_relationship.append('Director')
                    if rel_info.find('.//isOfficer') is not None:
                        owner_relationship.append('Officer')
                    if rel_info.find('.//isTenPercentOwner') is not None:
                        owner_relationship.append('10% Owner')
            
            relationship_str = ', '.join(owner_relationship) if owner_relationship else 'Unknown'
            
            # Extract transactions
            for txn_elem in root.findall('.//nonDerivativeTransaction'):
                try:
                    # Transaction date
                    date_elem = txn_elem.find('.//transactionDate/value')
                    if date_elem is None:
                        continue
                    txn_date = datetime.strptime(date_elem.text, '%Y-%m-%d')
                    
                    # Security title
                    security_elem = txn_elem.find('.//securityTitle/value')
                    security_title = security_elem.text if security_elem is not None else ""
                    
                    # Transaction code
                    code_elem = txn_elem.find('.//transactionCoding/transactionCode')
                    txn_code = code_elem.text if code_elem is not None else ""
                    
                    # Shares
                    shares_elem = txn_elem.find('.//transactionAmounts/transactionShares/value')
                    shares = float(shares_elem.text) if shares_elem is not None else 0.0
                    
                    # Price per share
                    price_elem = txn_elem.find('.//transactionAmounts/transactionPricePerShare/value')
                    price = float(price_elem.text) if price_elem is not None else 0.0
                    
                    # Shares owned after
                    owned_elem = txn_elem.find('.//postTransactionAmounts/sharesOwnedFollowingTransaction/value')
                    owned_after = float(owned_elem.text) if owned_elem is not None else 0.0
                    
                    # Direct/indirect
                    ownership_elem = txn_elem.find('.//ownershipNature/directOrIndirectOwnership/value')
                    is_direct = ownership_elem.text == 'D' if ownership_elem is not None else True
                    
                    transaction = InsiderTransaction(
                        transaction_date=txn_date,
                        person_name=owner_name,
                        person_relationship=relationship_str,
                        security_title=security_title,
                        transaction_code=txn_code,
                        shares=shares,
                        price_per_share=price,
                        shares_owned_after=owned_after,
                        transaction_value=shares * price,
                        is_direct=is_direct
                    )
                    
                    transactions.append(transaction)
                
                except Exception as e:
                    logger.warning(f"⚠️ Failed to parse transaction: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"❌ Form 4 parsing failed: {e}")
        
        return transactions
    
    def analyze_insider_patterns(
        self,
        transactions: List[InsiderTransaction],
        threshold_value: float = 1000000.0
    ) -> Dict[str, Any]:
        """
        Analyze insider trading patterns for suspicious activity
        
        Returns:
            Analysis report with anomalies and patterns
        """
        if not transactions:
            return {}
        
        # Group by person
        by_person = defaultdict(list)
        for txn in transactions:
            by_person[txn.person_name].append(txn)
        
        # Detect patterns
        patterns = {
            'large_sales': [],
            'cluster_activity': [],
            'unusual_timing': [],
            'total_value_traded': 0.0
        }
        
        for person, person_txns in by_person.items():
            # Large sales
            large_sales = [t for t in person_txns 
                          if t.transaction_code == 'S' and t.transaction_value > threshold_value]
            
            if large_sales:
                patterns['large_sales'].append({
                    'person': person,
                    'transactions': len(large_sales),
                    'total_value': sum(t.transaction_value for t in large_sales)
                })
            
            # Cluster detection (multiple transactions within short period)
            sorted_txns = sorted(person_txns, key=lambda t: t.transaction_date)
            for i in range(len(sorted_txns) - 2):
                window_txns = sorted_txns[i:i+3]
                time_span = (window_txns[-1].transaction_date - window_txns[0].transaction_date).days
                
                if time_span <= 7:  # 3+ transactions within 7 days
                    patterns['cluster_activity'].append({
                        'person': person,
                        'start_date': window_txns[0].transaction_date,
                        'end_date': window_txns[-1].transaction_date,
                        'transaction_count': len(window_txns),
                        'total_value': sum(t.transaction_value for t in window_txns)
                    })
        
        # Calculate total value traded
        patterns['total_value_traded'] = sum(abs(t.transaction_value) for t in transactions)
        
        return patterns
    
    def get_statistics(self) -> Dict[str, Any]:
        """Return statistics"""
        return self.stats.copy()


if __name__ == "__main__":
    # Demo usage
    async def demo():
        async with SECEdgarIntegrator() as integrator:
            # Get recent 10-K filings for Apple
            filings = await integrator.get_company_filings(
                ticker="AAPL",
                form_types=['10-K', '10-Q'],
                max_filings=5
            )
            
            print(f"Retrieved {len(filings)} filings")
            for filing in filings:
                print(f"  {filing.form_type}: {filing.filing_date} - {filing.company_name}")
                if filing.financial_data:
                    print(f"    Financial data: {list(filing.financial_data.keys())}")
            
            # Get insider transactions
            transactions = await integrator.get_insider_transactions(
                ticker="AAPL",
                lookback_days=90
            )
            
            print(f"\nInsider transactions: {len(transactions)}")
            
            # Analyze patterns
            patterns = integrator.analyze_insider_patterns(transactions)
            print(f"Large sales detected: {len(patterns.get('large_sales', []))}")
            print(f"Total value traded: ${patterns.get('total_value_traded', 0):,.2f}")
    
    asyncio.run(demo())

