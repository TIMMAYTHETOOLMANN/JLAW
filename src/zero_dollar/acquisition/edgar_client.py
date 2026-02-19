"""
SEC EDGAR Acquisition Module
=============================

Acquire Form 4 filings from SEC EDGAR system for zero-dollar transaction analysis.

Key Features:
- Async HTTP with aiohttp
- SEC EDGAR rate limiting (10 requests/second max)
- Form 4 XML parsing for derivative and non-derivative transactions
- SHA-256 hash computation for evidence integrity
- Proper User-Agent identification per SEC guidelines

Compliance:
- SEC EDGAR Rate Limiting: 10 requests/second max
- User-Agent identification required per SEC guidelines
- FRE 902(13)/(14) evidence integrity tracking

Reference:
- JLAW Zero-Dollar Transaction Forensic Specification v1.0
- Section 12.2: SEC EDGAR Acquisition Module
- Section 4.2: Data Flow Specification (Stages 1-4)
"""

import asyncio
import aiohttp
import hashlib
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from lxml import etree
import logging
import re

from src.zero_dollar.models import Transaction
from .form4_parser import (
    FilingMetadata,
    Form4Filing,
    parse_issuer_element,
    parse_reporting_owner,
    parse_transaction_amounts,
    parse_ownership_nature,
    extract_footnotes,
    link_footnotes_to_transactions,
)
from .rate_limiter import get_edgar_rate_limiter
from .exceptions import (
    EdgarAcquisitionError,
    EdgarRateLimitError,
    EdgarParsingError,
    EdgarNetworkError,
)

logger = logging.getLogger(__name__)


class SECEdgarAcquisition:
    """
    Acquire Form 4 filings from SEC EDGAR system.
    
    This client specializes in acquiring and parsing Form 4 insider trading
    filings for zero-dollar transaction detection. It handles:
    - Querying EDGAR filing index by CIK and date range
    - Fetching Form 4 XML documents
    - Parsing both derivative and non-derivative transactions
    - Computing SHA-256 hashes for evidence integrity
    
    Compliance:
        - SEC EDGAR Rate Limiting: 10 requests/second max
        - User-Agent identification required per SEC guidelines
        - FRE 902(13)/(14) evidence integrity via SHA-256 hashing
    
    Usage:
        config = {'user_agent': 'MyApp/1.0 me@example.com'}
        async with SECEdgarAcquisition(config) as client:
            filings = await client.get_form4_filings(
                issuer_cik='0000320187',
                start_date=date(2020, 1, 1),
                end_date=date(2020, 12, 31)
            )
    """
    
    BASE_URL = 'https://www.sec.gov'
    FULL_INDEX_URL = f'{BASE_URL}/cgi-bin/browse-edgar'
    SUBMISSIONS_URL = 'https://data.sec.gov/submissions'
    
    # SEC requires User-Agent with contact information
    DEFAULT_USER_AGENT = 'JLAW-Forensics/2.0 Zero-Dollar-Detection forensics@jlaw-system.org'
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SEC EDGAR acquisition client.
        
        Args:
            config: Configuration dictionary with optional keys:
                - user_agent: User-Agent string (required by SEC)
                - max_concurrent_requests: Maximum concurrent requests (default: 10)
                - request_timeout: HTTP request timeout in seconds (default: 30)
        """
        self.user_agent = config.get('user_agent', self.DEFAULT_USER_AGENT)
        self.max_concurrent = config.get('max_concurrent_requests', 10)
        self.request_timeout = config.get('request_timeout', 30)
        
        # Use shared rate limiter from SEC EDGAR integration
        self.rate_limiter = get_edgar_rate_limiter()
        
        # HTTP session (initialized in __aenter__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(
            f"SEC EDGAR Acquisition initialized "
            f"(rate: 10 req/sec, timeout: {self.request_timeout}s)"
        )
    
    async def __aenter__(self):
        """Async context manager entry - create HTTP session."""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/xml, text/xml, */*',
        }
        
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            trust_env=True,
        )
        
        logger.debug(f"HTTP session created with User-Agent: {self.user_agent[:50]}...")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP session."""
        if self.session:
            await self.session.close()
            logger.debug("HTTP session closed")
    
    async def get_form4_filings(
        self,
        issuer_cik: str,
        start_date: date,
        end_date: date
    ) -> List[Form4Filing]:
        """
        Query EDGAR filing index and return list of Form 4 filings.
        
        Args:
            issuer_cik: CIK of the issuing company (e.g., '0000320187')
            start_date: Start date for filing search (inclusive)
            end_date: End date for filing search (inclusive)
            
        Returns:
            List of Form4Filing objects with parsed transactions
            
        Raises:
            EdgarNetworkError: On HTTP/network errors
            EdgarRateLimitError: On rate limit violations
            EdgarParsingError: On XML parsing failures
        """
        logger.info(
            f"Fetching Form 4 filings for CIK {issuer_cik} "
            f"from {start_date} to {end_date}"
        )
        
        # Step 1: Get filing metadata from submissions API
        filing_metadata = await self._get_filing_metadata(
            issuer_cik, start_date, end_date
        )
        
        logger.info(f"Found {len(filing_metadata)} Form 4 filings in index")
        
        # Step 2: Fetch and parse each Form 4 document
        filings = []
        for meta in filing_metadata:
            try:
                filing = await self.fetch_form4_document(meta)
                filings.append(filing)
            except EdgarParsingError as e:
                logger.warning(
                    f"Failed to parse Form 4 {meta.accession_number}: {e}"
                )
                # Continue processing other filings
            except Exception as e:
                logger.error(
                    f"Unexpected error processing Form 4 {meta.accession_number}: {e}"
                )
                # Continue processing other filings
        
        logger.info(f"Successfully parsed {len(filings)} Form 4 filings")
        return filings
    
    async def _get_filing_metadata(
        self,
        cik: str,
        start_date: date,
        end_date: date
    ) -> List[FilingMetadata]:
        """
        Query SEC submissions API for Form 4 filing metadata.
        
        Args:
            cik: CIK of the issuer
            start_date: Start date for search
            end_date: End date for search
            
        Returns:
            List of FilingMetadata objects
        """
        # Normalize CIK (remove leading zeros for API)
        cik_normalized = cik.lstrip('0')
        
        url = f"{self.SUBMISSIONS_URL}/CIK{cik.zfill(10)}.json"
        
        try:
            async with self.rate_limiter.throttle():
                async with self.session.get(url) as response:
                    if response.status == 429:
                        raise EdgarRateLimitError("Rate limit exceeded (429)")
                    elif response.status == 403:
                        # Activate cooldown in shared rate limiter
                        self.rate_limiter.activate_cooldown("403 rate limit response")
                        raise EdgarRateLimitError("Rate limit exceeded (403)")
                    elif response.status != 200:
                        raise EdgarNetworkError(
                            f"Failed to fetch submissions: HTTP {response.status}",
                            response.status
                        )
                    
                    data = await response.json()
        except aiohttp.ClientError as e:
            raise EdgarNetworkError(f"Network error fetching submissions: {e}")
        
        # Parse filings from response
        metadata_list = []
        filings = data.get('filings', {}).get('recent', {})
        
        accession_numbers = filings.get('accessionNumber', [])
        filing_dates = filings.get('filingDate', [])
        form_types = filings.get('form', [])
        primary_docs = filings.get('primaryDocument', [])
        
        for i in range(len(accession_numbers)):
            form_type = form_types[i] if i < len(form_types) else ''
            
            # Filter for Form 4 only
            if not form_type.startswith('4'):
                continue
            
            filing_date_str = filing_dates[i] if i < len(filing_dates) else ''
            try:
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Invalid filing date: {filing_date_str}")
                continue
            
            # Filter by date range
            if not (start_date <= filing_date <= end_date):
                continue
            
            accession = accession_numbers[i].replace('-', '')
            primary_doc = primary_docs[i] if i < len(primary_docs) else 'doc4.xml'
            
            metadata_list.append(
                FilingMetadata(
                    accession_number=accession,
                    cik=cik,
                    filing_date=filing_date,
                    primary_document=primary_doc,
                    form_type=form_type,
                )
            )
        
        return metadata_list
    
    async def fetch_form4_document(self, meta: FilingMetadata) -> Form4Filing:
        """
        Retrieve and parse individual Form 4 XML document.
        
        Args:
            meta: FilingMetadata with accession number and document info
            
        Returns:
            Form4Filing object with parsed transactions
            
        Raises:
            EdgarNetworkError: On HTTP/network errors
            EdgarParsingError: On XML parsing failures
        """
        # Build document URL
        # Format: https://www.sec.gov/Archives/edgar/data/CIK/ACCESSION/doc4.xml
        cik_stripped = meta.cik.lstrip('0')
        accession_formatted = meta.accession_number.replace('-', '')
        
        url = (
            f"{self.BASE_URL}/Archives/edgar/data/{cik_stripped}/"
            f"{accession_formatted}/{meta.primary_document}"
        )
        
        logger.debug(f"Fetching Form 4 document: {url}")
        
        try:
            async with self.rate_limiter.throttle():
                async with self.session.get(url) as response:
                    if response.status == 429:
                        raise EdgarRateLimitError("Rate limit exceeded (429)")
                    elif response.status == 403:
                        self.rate_limiter.activate_cooldown("403 rate limit response")
                        raise EdgarRateLimitError("Rate limit exceeded (403)")
                    elif response.status != 200:
                        raise EdgarNetworkError(
                            f"Failed to fetch Form 4: HTTP {response.status}",
                            response.status
                        )
                    
                    xml_content = await response.text()
        except aiohttp.ClientError as e:
            raise EdgarNetworkError(f"Network error fetching Form 4: {e}")
        
        # Compute SHA-256 hash for evidence integrity
        xml_hash = hashlib.sha256(xml_content.encode('utf-8')).hexdigest()
        
        # Parse XML into Form4Filing
        filing = self.parse_form4_xml(xml_content, meta, xml_hash)
        
        return filing
    
    def parse_form4_xml(
        self,
        xml_content: str,
        meta: FilingMetadata,
        xml_hash: str
    ) -> Form4Filing:
        """
        Parse Form 4 XML into structured Form4Filing object.
        
        Args:
            xml_content: Raw XML content
            meta: Filing metadata
            xml_hash: SHA-256 hash of XML content
            
        Returns:
            Form4Filing with all transactions parsed
            
        Raises:
            EdgarParsingError: On XML parsing failures
        """
        try:
            # Parse XML with lxml
            root = etree.fromstring(xml_content.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            raise EdgarParsingError(
                f"Invalid XML syntax: {e}",
                meta.accession_number
            )
        
        # Extract issuer information
        issuer_elem = root.find('issuer')
        if issuer_elem is None:
            raise EdgarParsingError(
                "Missing <issuer> element",
                meta.accession_number
            )
        
        issuer_info = parse_issuer_element(issuer_elem)
        
        # Extract reporting owner information
        owner_elem = root.find('reportingOwner')
        if owner_elem is None:
            raise EdgarParsingError(
                "Missing <reportingOwner> element",
                meta.accession_number
            )
        
        owner_info = parse_reporting_owner(owner_elem)
        
        # Extract footnotes
        footnotes = extract_footnotes(root)
        
        # Parse transactions
        transactions = []
        
        # Parse non-derivative transactions
        non_deriv_table = root.find('nonDerivativeTable')
        if non_deriv_table is not None:
            for txn_elem in non_deriv_table.findall('nonDerivativeTransaction'):
                try:
                    txn = self.parse_non_derivative_transaction(
                        txn_elem, meta, issuer_info, owner_info
                    )
                    transactions.append(txn)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse non-derivative transaction: {e}"
                    )
        
        # Parse derivative transactions
        deriv_table = root.find('derivativeTable')
        if deriv_table is not None:
            for txn_elem in deriv_table.findall('derivativeTransaction'):
                try:
                    txn = self.parse_derivative_transaction(
                        txn_elem, meta, issuer_info, owner_info
                    )
                    transactions.append(txn)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse derivative transaction: {e}"
                    )
        
        # Link footnotes to transactions
        transactions = link_footnotes_to_transactions(transactions, footnotes)
        
        # Create Form4Filing object
        filing = Form4Filing(
            accession_number=meta.accession_number,
            filing_date=meta.filing_date,
            issuer_cik=issuer_info['cik'],
            issuer_name=issuer_info['name'],
            issuer_ticker=issuer_info['ticker'],
            reporting_owner_cik=owner_info['cik'],
            reporting_owner_name=owner_info['name'],
            is_director=owner_info['is_director'],
            is_officer=owner_info['is_officer'],
            is_ten_percent_owner=owner_info['is_ten_percent_owner'],
            officer_title=owner_info['officer_title'],
            transactions=transactions,
            footnotes=footnotes,
            xml_hash=xml_hash,
        )
        
        return filing
    
    def parse_non_derivative_transaction(
        self,
        elem: etree.Element,
        meta: FilingMetadata,
        issuer_info: Dict[str, str],
        owner_info: Dict[str, Any]
    ) -> Transaction:
        """
        Parse non-derivative transaction element.
        
        Args:
            elem: <nonDerivativeTransaction> XML element
            meta: Filing metadata
            issuer_info: Issuer information
            owner_info: Reporting owner information
            
        Returns:
            Transaction object
        """
        # Extract security title
        security_elem = elem.find('securityTitle/value')
        security_title = security_elem.text.strip() if security_elem is not None and security_elem.text else 'Common Stock'
        
        # Extract transaction date
        txn_date_elem = elem.find('.//transactionDate/value')
        if txn_date_elem is None or not txn_date_elem.text:
            raise EdgarParsingError("Missing transaction date")
        
        try:
            transaction_date = datetime.strptime(
                txn_date_elem.text.strip(), '%Y-%m-%d'
            ).date()
        except ValueError as e:
            raise EdgarParsingError(f"Invalid transaction date: {txn_date_elem.text}")
        
        # Extract transaction code
        code_elem = elem.find('.//transactionCode')
        transaction_code = code_elem.text.strip() if code_elem is not None and code_elem.text else 'P'
        
        # Extract transaction amounts
        amounts_elem = elem.find('transactionAmounts')
        if amounts_elem is None:
            raise EdgarParsingError("Missing <transactionAmounts>")
        
        amounts = parse_transaction_amounts(amounts_elem)
        
        # Extract post-transaction amounts
        post_txn_elem = elem.find('postTransactionAmounts')
        ownership_elem = elem.find('ownershipNature')
        
        shares_owned_following = Decimal('0')
        direct_indirect = 'D'
        nature_of_ownership = None
        
        if post_txn_elem is not None:
            post_data = parse_ownership_nature(post_txn_elem)
            shares_owned_following = post_data['shares_owned_following']
        
        if ownership_elem is not None:
            ownership_data = parse_ownership_nature(ownership_elem)
            direct_indirect = ownership_data['direct_indirect']
            nature_of_ownership = ownership_data['nature_of_ownership']
        
        # Extract footnote references
        footnote_ids = []
        for footnote_ref in elem.findall('.//footnoteId'):
            if footnote_ref.get('id'):
                footnote_ids.append(footnote_ref.get('id'))
        
        # Build document URL
        cik_stripped = meta.cik.lstrip('0')
        accession_formatted = meta.accession_number.replace('-', '')
        document_url = (
            f"{self.BASE_URL}/Archives/edgar/data/{cik_stripped}/"
            f"{accession_formatted}/{meta.primary_document}"
        )
        
        # Create Transaction object
        return Transaction(
            accession_number=meta.accession_number,
            issuer_cik=issuer_info['cik'],
            issuer_name=issuer_info['name'],
            reporting_person_cik=owner_info['cik'],
            reporting_person_name=owner_info['name'],
            transaction_date=transaction_date,
            filing_date=meta.filing_date,
            transaction_code=transaction_code,
            shares=amounts['shares'],
            price_per_share=amounts['price_per_share'],
            transaction_acquired_disposed=amounts['acquired_disposed'],
            shares_owned_following=shares_owned_following,
            direct_indirect=direct_indirect,
            nature_of_ownership=nature_of_ownership,
            footnotes=footnote_ids,
            security_title=security_title,
            form_type=meta.form_type,
            document_url=document_url,
            derivative_security=False,
        )
    
    def parse_derivative_transaction(
        self,
        elem: etree.Element,
        meta: FilingMetadata,
        issuer_info: Dict[str, str],
        owner_info: Dict[str, Any]
    ) -> Transaction:
        """
        Parse derivative transaction element.
        
        Args:
            elem: <derivativeTransaction> XML element
            meta: Filing metadata
            issuer_info: Issuer information
            owner_info: Reporting owner information
            
        Returns:
            Transaction object
        """
        # Extract security title
        security_elem = elem.find('securityTitle/value')
        security_title = security_elem.text.strip() if security_elem is not None and security_elem.text else 'Stock Option'
        
        # Extract transaction date
        txn_date_elem = elem.find('.//transactionDate/value')
        if txn_date_elem is None or not txn_date_elem.text:
            raise EdgarParsingError("Missing transaction date")
        
        try:
            transaction_date = datetime.strptime(
                txn_date_elem.text.strip(), '%Y-%m-%d'
            ).date()
        except ValueError:
            raise EdgarParsingError(f"Invalid transaction date: {txn_date_elem.text}")
        
        # Extract transaction code
        code_elem = elem.find('.//transactionCode')
        transaction_code = code_elem.text.strip() if code_elem is not None and code_elem.text else 'A'
        
        # Extract transaction amounts
        amounts_elem = elem.find('transactionAmounts')
        if amounts_elem is None:
            raise EdgarParsingError("Missing <transactionAmounts>")
        
        amounts = parse_transaction_amounts(amounts_elem)
        
        # Extract conversion/exercise price
        conversion_elem = elem.find('.//conversionOrExercisePrice/value')
        conversion_price = None
        if conversion_elem is not None and conversion_elem.text:
            try:
                conversion_price = Decimal(conversion_elem.text.strip())
            except Exception as e:
                logger.warning(f"Failed to parse conversion price: {e}")
        
        # Extract exercise/expiration dates
        exercise_date = None
        expiration_date = None
        
        exercise_elem = elem.find('.//exerciseDate/value')
        if exercise_elem is not None and exercise_elem.text:
            try:
                exercise_date = datetime.strptime(
                    exercise_elem.text.strip(), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        expiration_elem = elem.find('.//expirationDate/value')
        if expiration_elem is not None and expiration_elem.text:
            try:
                expiration_date = datetime.strptime(
                    expiration_elem.text.strip(), '%Y-%m-%d'
                ).date()
            except ValueError:
                pass
        
        # Extract post-transaction amounts
        post_txn_elem = elem.find('postTransactionAmounts')
        ownership_elem = elem.find('ownershipNature')
        
        shares_owned_following = Decimal('0')
        direct_indirect = 'D'
        nature_of_ownership = None
        
        if post_txn_elem is not None:
            post_data = parse_ownership_nature(post_txn_elem)
            shares_owned_following = post_data['shares_owned_following']
        
        if ownership_elem is not None:
            ownership_data = parse_ownership_nature(ownership_elem)
            direct_indirect = ownership_data['direct_indirect']
            nature_of_ownership = ownership_data['nature_of_ownership']
        
        # Extract footnote references
        footnote_ids = []
        for footnote_ref in elem.findall('.//footnoteId'):
            if footnote_ref.get('id'):
                footnote_ids.append(footnote_ref.get('id'))
        
        # Build document URL
        cik_stripped = meta.cik.lstrip('0')
        accession_formatted = meta.accession_number.replace('-', '')
        document_url = (
            f"{self.BASE_URL}/Archives/edgar/data/{cik_stripped}/"
            f"{accession_formatted}/{meta.primary_document}"
        )
        
        # Create Transaction object
        return Transaction(
            accession_number=meta.accession_number,
            issuer_cik=issuer_info['cik'],
            issuer_name=issuer_info['name'],
            reporting_person_cik=owner_info['cik'],
            reporting_person_name=owner_info['name'],
            transaction_date=transaction_date,
            filing_date=meta.filing_date,
            transaction_code=transaction_code,
            shares=amounts['shares'],
            price_per_share=amounts['price_per_share'],
            transaction_acquired_disposed=amounts['acquired_disposed'],
            shares_owned_following=shares_owned_following,
            direct_indirect=direct_indirect,
            nature_of_ownership=nature_of_ownership,
            footnotes=footnote_ids,
            security_title=security_title,
            form_type=meta.form_type,
            document_url=document_url,
            derivative_security=True,
            conversion_exercise_price=conversion_price,
            exercise_date=exercise_date,
            expiration_date=expiration_date,
        )


async def enrich_with_issuer_metadata(
    transactions: List[Transaction]
) -> List[Transaction]:
    """
    Enrich transactions with issuer metadata.
    
    Stage 3 enrichment per Section 4.2:
    - CIK → Ticker mapping (already included in Form 4 parsing)
    - GICS Sector classification (placeholder for future implementation)
    - Market Cap Tier (placeholder for future implementation)
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        Enriched list of transactions
        
    Note:
        This is a placeholder for future metadata enrichment.
        Current implementation returns transactions unchanged as
        ticker symbol is already extracted from Form 4.
    """
    # Placeholder - ticker already extracted during Form 4 parsing
    # Future enhancements:
    # - Query external API for GICS sector
    # - Determine market cap tier
    # - Add industry classification
    return transactions


def calculate_derived_fields(transaction: Transaction) -> Transaction:
    """
    Calculate derived fields per Stage 4.
    
    Derived fields:
    - Notional Value: shares * price (computed property in Transaction model)
    - Days-to-Filing: filing_date - transaction_date (computed property)
    - VWAP Delta: If market data available (placeholder for future)
    
    Args:
        transaction: Transaction object
        
    Returns:
        Transaction with derived fields calculated
        
    Note:
        Most derived fields are computed properties in the Transaction model.
        This function is provided for future enhancements like VWAP delta.
    """
    # Notional value and days_to_filing are computed properties
    # No additional calculation needed here
    
    # Placeholder for VWAP delta calculation
    # Future enhancement: Query market data API for VWAP on transaction date
    
    return transaction
