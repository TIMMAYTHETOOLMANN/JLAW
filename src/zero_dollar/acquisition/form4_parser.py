"""
Form 4 Parser
=============

Parse SEC Form 4 XML documents into Transaction objects.

Form 4 Structure:
- <ownershipDocument> - Root element
  - <issuer> - Company information
  - <reportingOwner> - Insider information
  - <nonDerivativeTable> - Non-derivative transactions
  - <derivativeTable> - Derivative transactions
  - <footnotes> - Explanatory notes

Reference:
- JLAW Zero-Dollar Transaction Forensic Specification v1.0
- Section 12.2: SEC EDGAR Acquisition Module
- Section 4.2: Data Flow Specification
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional, Any
from lxml import etree
import logging

from src.zero_dollar.models import Transaction

logger = logging.getLogger(__name__)


@dataclass
class FilingMetadata:
    """
    Metadata from EDGAR filing index.
    
    Extracted from EDGAR Atom feed or submissions API before
    retrieving the full Form 4 document.
    
    Attributes:
        accession_number: SEC EDGAR accession number (NNNNNNNNNN-NN-NNNNNN)
        cik: Central Index Key of the issuer
        filing_date: Date the form was filed with SEC
        primary_document: Primary document filename (e.g., 'doc4.xml')
        form_type: Form type ('4', '4/A' for amendments)
    """
    accession_number: str
    cik: str
    filing_date: date
    primary_document: str
    form_type: str


@dataclass
class Form4Filing:
    """
    Parsed Form 4 filing with all transactions.
    
    Represents a complete Form 4 filing after XML parsing,
    containing all transactions (both derivative and non-derivative),
    issuer information, reporting owner details, and footnotes.
    
    Attributes:
        accession_number: SEC EDGAR accession number
        filing_date: Date form was filed
        issuer_cik: CIK of issuing company
        issuer_name: Official company name
        issuer_ticker: Trading symbol (if available)
        reporting_owner_cik: CIK of reporting insider
        reporting_owner_name: Full name of reporting person
        is_director: Whether reporting owner is a director
        is_officer: Whether reporting owner is an officer
        is_ten_percent_owner: Whether reporting owner owns 10%+ of shares
        officer_title: Job title if reporting owner is an officer
        transactions: List of all transactions (derivative + non-derivative)
        footnotes: Dictionary mapping footnote IDs to text
        xml_hash: SHA-256 hash of source XML for evidence integrity
    """
    accession_number: str
    filing_date: date
    issuer_cik: str
    issuer_name: str
    issuer_ticker: str
    reporting_owner_cik: str
    reporting_owner_name: str
    is_director: bool
    is_officer: bool
    is_ten_percent_owner: bool
    officer_title: Optional[str]
    transactions: List[Transaction]
    footnotes: Dict[str, str]
    xml_hash: str


def parse_issuer_element(issuer_elem: etree.Element) -> Dict[str, str]:
    """
    Extract issuer information from <issuer> element.
    
    Args:
        issuer_elem: The <issuer> XML element
        
    Returns:
        Dictionary with keys: cik, name, ticker
        
    Example XML:
        <issuer>
            <issuerCik>0000320187</issuerCik>
            <issuerName>NIKE, Inc.</issuerName>
            <issuerTradingSymbol>NKE</issuerTradingSymbol>
        </issuer>
    """
    cik_elem = issuer_elem.find('issuerCik')
    name_elem = issuer_elem.find('issuerName')
    ticker_elem = issuer_elem.find('issuerTradingSymbol')
    
    return {
        'cik': cik_elem.text.strip() if cik_elem is not None and cik_elem.text else '',
        'name': name_elem.text.strip() if name_elem is not None and name_elem.text else '',
        'ticker': ticker_elem.text.strip() if ticker_elem is not None and ticker_elem.text else '',
    }


def parse_reporting_owner(owner_elem: etree.Element) -> Dict[str, Any]:
    """
    Extract reporting owner information and relationship to issuer.
    
    Args:
        owner_elem: The <reportingOwner> XML element
        
    Returns:
        Dictionary with owner info and relationship flags
        
    Example XML:
        <reportingOwner>
            <reportingOwnerId>
                <rptOwnerCik>0001234567</rptOwnerCik>
                <rptOwnerName>John Donahoe</rptOwnerName>
            </reportingOwnerId>
            <reportingOwnerRelationship>
                <isDirector>0</isDirector>
                <isOfficer>1</isOfficer>
                <isTenPercentOwner>0</isTenPercentOwner>
                <officerTitle>President and CEO</officerTitle>
            </reportingOwnerRelationship>
        </reportingOwner>
    """
    owner_id = owner_elem.find('reportingOwnerId')
    relationship = owner_elem.find('reportingOwnerRelationship')
    
    cik_elem = owner_id.find('rptOwnerCik') if owner_id is not None else None
    name_elem = owner_id.find('rptOwnerName') if owner_id is not None else None
    
    result = {
        'cik': cik_elem.text.strip() if cik_elem is not None and cik_elem.text else '',
        'name': name_elem.text.strip() if name_elem is not None and name_elem.text else '',
        'is_director': False,
        'is_officer': False,
        'is_ten_percent_owner': False,
        'officer_title': None,
    }
    
    if relationship is not None:
        is_director = relationship.find('isDirector')
        is_officer = relationship.find('isOfficer')
        is_ten_percent = relationship.find('isTenPercentOwner')
        title_elem = relationship.find('officerTitle')
        
        result['is_director'] = is_director is not None and is_director.text == '1'
        result['is_officer'] = is_officer is not None and is_officer.text == '1'
        result['is_ten_percent_owner'] = is_ten_percent is not None and is_ten_percent.text == '1'
        result['officer_title'] = title_elem.text.strip() if title_elem is not None and title_elem.text else None
    
    return result


def parse_transaction_amounts(amounts_elem: etree.Element) -> Dict[str, Any]:
    """
    Extract transaction amounts (shares, price, acquired/disposed).
    
    Args:
        amounts_elem: The <transactionAmounts> XML element
        
    Returns:
        Dictionary with shares, price_per_share, acquired_disposed
        
    Example XML:
        <transactionAmounts>
            <transactionShares>
                <value>10000</value>
            </transactionShares>
            <transactionPricePerShare>
                <value>0</value>
            </transactionPricePerShare>
            <transactionAcquiredDisposedCode>
                <value>A</value>
            </transactionAcquiredDisposedCode>
        </transactionAmounts>
    """
    result = {
        'shares': Decimal('0'),
        'price_per_share': None,
        'acquired_disposed': 'A',
    }
    
    shares_elem = amounts_elem.find('.//transactionShares/value')
    if shares_elem is not None and shares_elem.text:
        try:
            result['shares'] = Decimal(shares_elem.text.strip())
        except Exception as e:
            logger.warning(f"Failed to parse shares: {shares_elem.text} - {e}")
    
    price_elem = amounts_elem.find('.//transactionPricePerShare/value')
    if price_elem is not None and price_elem.text:
        price_text = price_elem.text.strip()
        if price_text and price_text not in ('0', '0.0', '0.00'):
            try:
                result['price_per_share'] = Decimal(price_text)
            except Exception as e:
                logger.warning(f"Failed to parse price: {price_text} - {e}")
        # If price is 0 or empty, leave as None (zero-dollar transaction)
    
    acq_disp_elem = amounts_elem.find('.//transactionAcquiredDisposedCode/value')
    if acq_disp_elem is not None and acq_disp_elem.text:
        result['acquired_disposed'] = acq_disp_elem.text.strip()
    
    return result


def parse_ownership_nature(ownership_elem: etree.Element) -> Dict[str, Any]:
    """
    Extract ownership nature (direct/indirect, nature of ownership).
    
    Args:
        ownership_elem: The <postTransactionAmounts> or <ownershipNature> XML element
        
    Returns:
        Dictionary with shares_owned_following, direct_indirect, nature_of_ownership
        
    Example XML:
        <postTransactionAmounts>
            <sharesOwnedFollowingTransaction>
                <value>50000</value>
            </sharesOwnedFollowingTransaction>
        </postTransactionAmounts>
        <ownershipNature>
            <directOrIndirectOwnership>
                <value>I</value>
            </directOrIndirectOwnership>
            <natureOfOwnership>
                <value>By Family Trust</value>
            </natureOfOwnership>
        </ownershipNature>
    """
    result = {
        'shares_owned_following': Decimal('0'),
        'direct_indirect': 'D',
        'nature_of_ownership': None,
    }
    
    # Handle both structure variations
    if ownership_elem.tag == 'postTransactionAmounts':
        shares_elem = ownership_elem.find('.//sharesOwnedFollowingTransaction/value')
        if shares_elem is not None and shares_elem.text:
            try:
                result['shares_owned_following'] = Decimal(shares_elem.text.strip())
            except Exception as e:
                logger.warning(f"Failed to parse shares owned: {shares_elem.text} - {e}")
    
    elif ownership_elem.tag == 'ownershipNature':
        direct_elem = ownership_elem.find('.//directOrIndirectOwnership/value')
        if direct_elem is not None and direct_elem.text:
            result['direct_indirect'] = direct_elem.text.strip()
        
        nature_elem = ownership_elem.find('.//natureOfOwnership/value')
        if nature_elem is not None and nature_elem.text:
            result['nature_of_ownership'] = nature_elem.text.strip()
    
    return result


def extract_footnotes(root: etree.Element) -> Dict[str, str]:
    """
    Parse all footnotes into a dictionary.
    
    Args:
        root: The root XML element (<ownershipDocument>)
        
    Returns:
        Dictionary mapping footnote IDs to footnote text
        
    Example XML:
        <footnotes>
            <footnote id="F1">This transaction was executed pursuant to a Rule 10b5-1 trading plan.</footnote>
            <footnote id="F2">Indirect ownership through family trust.</footnote>
        </footnotes>
    """
    footnotes = {}
    footnotes_elem = root.find('footnotes')
    
    if footnotes_elem is not None:
        for footnote in footnotes_elem.findall('footnote'):
            footnote_id = footnote.get('id', '')
            footnote_text = footnote.text.strip() if footnote.text else ''
            if footnote_id and footnote_text:
                footnotes[footnote_id] = footnote_text
    
    return footnotes


def link_footnotes_to_transactions(
    transactions: List[Transaction],
    footnotes: Dict[str, str]
) -> List[Transaction]:
    """
    Associate footnote IDs with their text in transaction objects.
    
    Args:
        transactions: List of Transaction objects
        footnotes: Dictionary mapping footnote IDs to text
        
    Returns:
        Updated list of transactions with footnote text populated
    """
    for txn in transactions:
        if txn.footnotes:
            # Replace footnote IDs with full text
            resolved_footnotes = []
            for footnote_id in txn.footnotes:
                if footnote_id in footnotes:
                    resolved_footnotes.append(f"{footnote_id}: {footnotes[footnote_id]}")
                else:
                    resolved_footnotes.append(footnote_id)
            txn.footnotes = resolved_footnotes
    
    return transactions
