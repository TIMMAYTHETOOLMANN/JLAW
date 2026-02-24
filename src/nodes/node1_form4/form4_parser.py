"""
Node 1: Form 4 Parser
=====================

Implements complete SEC Form 4 XML parsing with all 16 transaction codes
and automatic classification into general trades, Rule 16b-3 exempt 
transactions, derivative conversions, and other Section 16 exempt transfers.

Transaction Codes:
- General: P (Purchase), S (Sale)
- Rule 16b-3: A (Award), D (Disposition to issuer), F (Payment of tax), I (Discretionary)
- Derivative: M (Exercise), C (Conversion), E (Expiration)
- Gifts: G (Gift)
- Other: J (Other), H (Expiration short), O (Out-of-money), X (In-the-money), L (Small), W (Will)
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class TransactionCode(Enum):
    """SEC Form 4 Transaction Codes - Complete taxonomy."""
    # Open Market Transactions
    P = "Open market or private purchase"
    S = "Open market or private sale"
    
    # Rule 16b-3 Exempt Transactions
    A = "Grant, award, or other acquisition from issuer"
    D = "Disposition to issuer"
    F = "Payment of exercise price or tax liability by delivering securities"
    I = "Discretionary transaction"
    V = "Voluntary reporting of transaction - RSU vesting, tax withholding"

    # Derivative Securities
    M = "Exercise or conversion of derivative security"
    C = "Conversion of derivative security"
    E = "Expiration of short derivative position"
    H = "Expiration of long derivative position"
    O = "Exercise of out-of-the-money derivative"
    X = "Exercise of in-the-money derivative"
    
    # Gifts and Transfers
    G = "Gift"
    J = "Other acquisition or disposition"
    L = "Small acquisition"
    W = "Acquisition or disposition by will or succession"
    Z = "Deposit into or withdrawal from voting trust"
    K = "Equity swap or similar transaction"

    # Unknown
    U = "Unknown transaction code"


class TransactionCategory(Enum):
    """Transaction classification categories."""
    GENERAL = "General Trade"
    RULE_16B3 = "Rule 16b-3 Exempt"
    DERIVATIVE = "Derivative Transaction"
    GIFT = "Gift/Transfer"
    OTHER_EXEMPT = "Other Section 16 Exempt"
    UNKNOWN = "Unknown"


@dataclass
class Form4Transaction:
    """Parsed Form 4 transaction with full detail."""
    transaction_code: str
    transaction_code_description: str
    transaction_category: TransactionCategory
    transaction_date: Optional[date]
    shares: float
    price_per_share: float
    total_value: float
    acquired_disposed: str  # 'A' or 'D'
    direct_indirect: str  # 'D' or 'I'
    security_title: str
    is_derivative: bool = False
    underlying_security: Optional[str] = None
    exercise_price: Optional[float] = None
    expiration_date: Optional[date] = None
    ownership_nature: Optional[str] = None
    footnotes: List[str] = field(default_factory=list)
    
    # Calculated fields
    is_zero_dollar: bool = False
    is_gift: bool = False
    is_late_filed: bool = False
    days_late: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_code": self.transaction_code,
            "transaction_code_description": self.transaction_code_description,
            "transaction_category": self.transaction_category.value,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "shares": self.shares,
            "price_per_share": self.price_per_share,
            "total_value": self.total_value,
            "acquired_disposed": self.acquired_disposed,
            "security_title": self.security_title,
            "is_derivative": self.is_derivative,
            "is_zero_dollar": self.is_zero_dollar,
            "is_gift": self.is_gift,
            "is_late_filed": self.is_late_filed,
            "days_late": self.days_late
        }


@dataclass
class Form4Filing:
    """Complete parsed Form 4 filing."""
    accession_number: str
    filing_date: date
    period_of_report: Optional[date]
    issuer_cik: str
    issuer_name: str
    reporting_owner_cik: str
    reporting_owner_name: str
    is_director: bool
    is_officer: bool
    is_ten_percent_owner: bool
    officer_title: Optional[str]
    transactions: List[Form4Transaction]
    
    # Computed analysis
    total_acquired: float = 0.0
    total_disposed: float = 0.0
    net_change: float = 0.0
    zero_dollar_transactions: List[Form4Transaction] = field(default_factory=list)
    gift_transactions: List[Form4Transaction] = field(default_factory=list)
    late_transactions: List[Form4Transaction] = field(default_factory=list)
    filing_footnotes: Dict[str, str] = field(default_factory=dict)  # id → text
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accession_number": self.accession_number,
            "filing_date": self.filing_date.isoformat(),
            "period_of_report": self.period_of_report.isoformat() if self.period_of_report else None,
            "issuer_name": self.issuer_name,
            "reporting_owner_name": self.reporting_owner_name,
            "is_director": self.is_director,
            "is_officer": self.is_officer,
            "is_ten_percent_owner": self.is_ten_percent_owner,
            "officer_title": self.officer_title,
            "transaction_count": len(self.transactions),
            "total_acquired": self.total_acquired,
            "total_disposed": self.total_disposed,
            "net_change": self.net_change,
            "zero_dollar_count": len(self.zero_dollar_transactions),
            "gift_count": len(self.gift_transactions),
            "late_count": len(self.late_transactions),
            "transactions": [t.to_dict() for t in self.transactions]
        }


class Form4Parser:
    """
    Complete Form 4 XML parser with all 16 transaction codes.
    
    Parses SEC Form 4 XML filings and extracts:
    - All transaction details with full code taxonomy
    - Reporting owner information
    - Derivative vs non-derivative securities
    - Late filing detection (> 2 business days)
    - Zero-dollar transaction flagging
    - Gift transaction identification
    """
    
    # Transaction code classification
    GENERAL_CODES = {'P', 'S'}
    RULE_16B3_CODES = {'A', 'D', 'F', 'I', 'V'}  # V = RSU vesting/tax withholding
    DERIVATIVE_CODES = {'M', 'C', 'E', 'H', 'O', 'X', 'K'}  # K = equity swap
    GIFT_CODES = {'G'}
    OTHER_EXEMPT_CODES = {'J', 'L', 'W', 'Z'}  # Z = voting trust

    def __init__(self):
        self.ns = {
            'xbrl': 'http://www.xbrl.org/2003/instance',
            'link': 'http://www.xbrl.org/2003/linkbase'
        }
    
    def classify_transaction_code(self, code: str) -> Tuple[TransactionCategory, str]:
        """
        Classify transaction code into category.
        
        Args:
            code: Single-letter transaction code
            
        Returns:
            Tuple of (category, description)
        """
        code = code.upper() if code else 'U'
        
        try:
            description = TransactionCode[code].value
        except KeyError:
            description = f"Unknown code: {code}"
            code = 'U'
        
        if code in self.GENERAL_CODES:
            return TransactionCategory.GENERAL, description
        elif code in self.RULE_16B3_CODES:
            return TransactionCategory.RULE_16B3, description
        elif code in self.DERIVATIVE_CODES:
            return TransactionCategory.DERIVATIVE, description
        elif code in self.GIFT_CODES:
            return TransactionCategory.GIFT, description
        elif code in self.OTHER_EXEMPT_CODES:
            return TransactionCategory.OTHER_EXEMPT, description
        else:
            return TransactionCategory.UNKNOWN, description
    
    def parse_xml(self, xml_content: str, accession_number: str, filing_date: date) -> Form4Filing:
        """
        Parse Form 4 XML content.
        
        Args:
            xml_content: Raw XML string
            accession_number: SEC accession number
            filing_date: Date the form was filed
            
        Returns:
            Parsed Form4Filing object
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
            return self._create_empty_filing(accession_number, filing_date)
        
        # Extract issuer info
        issuer = root.find('.//issuer')
        issuer_cik = self._get_text(issuer, 'issuerCik') if issuer else ''
        issuer_name = self._get_text(issuer, 'issuerName') if issuer else ''
        
        # Extract reporting owner info
        owner = root.find('.//reportingOwner')
        owner_id = owner.find('reportingOwnerId') if owner else None
        owner_cik = self._get_text(owner_id, 'rptOwnerCik') if owner_id else ''
        owner_name = self._get_text(owner_id, 'rptOwnerName') if owner_id else ''
        
        # Extract relationship
        relationship = owner.find('reportingOwnerRelationship') if owner else None
        is_director = self._get_bool(relationship, 'isDirector') if relationship else False
        is_officer = self._get_bool(relationship, 'isOfficer') if relationship else False
        is_ten_percent = self._get_bool(relationship, 'isTenPercentOwner') if relationship else False
        officer_title = self._get_text(relationship, 'officerTitle') if relationship else None
        
        # Extract period of report
        period_of_report = self._parse_date(self._get_text(root, 'periodOfReport'))
        
        # Extract filing-level footnotes (id → text)
        filing_footnotes = {}
        footnotes_elem = root.find('footnotes')
        if footnotes_elem is not None:
            for fn in footnotes_elem.findall('footnote'):
                fn_id = fn.get('id', '')
                fn_text = (fn.text or '').strip()
                if fn_id and fn_text:
                    filing_footnotes[fn_id] = fn_text

        # Parse non-derivative transactions
        transactions = []
        for trans in root.findall('.//nonDerivativeTransaction'):
            parsed = self._parse_non_derivative_transaction(trans, filing_date)
            if parsed:
                # Resolve footnote IDs from transactionCoding and transactionAmounts
                fn_ids = self._extract_footnote_ids(trans)
                parsed.footnotes = [
                    filing_footnotes.get(fid, fid) for fid in fn_ids
                ]
                transactions.append(parsed)

        # Parse derivative transactions
        for trans in root.findall('.//derivativeTransaction'):
            parsed = self._parse_derivative_transaction(trans, filing_date)
            if parsed:
                fn_ids = self._extract_footnote_ids(trans)
                parsed.footnotes = [
                    filing_footnotes.get(fid, fid) for fid in fn_ids
                ]
                transactions.append(parsed)

        # Create filing object
        filing = Form4Filing(
            accession_number=accession_number,
            filing_date=filing_date,
            period_of_report=period_of_report,
            issuer_cik=issuer_cik,
            issuer_name=issuer_name,
            reporting_owner_cik=owner_cik,
            reporting_owner_name=owner_name,
            is_director=is_director,
            is_officer=is_officer,
            is_ten_percent_owner=is_ten_percent,
            officer_title=officer_title,
            transactions=transactions,
            filing_footnotes=filing_footnotes,
        )
        
        # Compute aggregates
        self._compute_aggregates(filing)
        
        return filing
    
    def _parse_non_derivative_transaction(
        self, 
        trans: ET.Element,
        filing_date: date
    ) -> Optional[Form4Transaction]:
        """Parse a non-derivative transaction element."""
        try:
            # Security title
            security_title = self._get_text(trans, './/securityTitle/value')
            
            # Transaction date
            trans_date = self._parse_date(self._get_text(trans, './/transactionDate/value'))
            
            # Transaction coding
            coding = trans.find('.//transactionCoding')
            trans_code = self._get_text(coding, 'transactionCode') if coding else 'U'
            
            # Classify transaction
            category, description = self.classify_transaction_code(trans_code)
            
            # Transaction amounts
            amounts = trans.find('.//transactionAmounts')
            shares = self._get_float(amounts, './/transactionShares/value') if amounts else 0.0
            price = self._get_float(amounts, './/transactionPricePerShare/value') if amounts else 0.0
            acq_disp = self._get_text(amounts, './/transactionAcquiredDisposedCode/value') if amounts else 'A'
            
            # Ownership nature
            ownership = trans.find('.//ownershipNature')
            direct_indirect = self._get_text(ownership, 'directOrIndirectOwnership/value') if ownership else 'D'
            
            # Calculate total value
            total_value = shares * price
            
            # Check for late filing (> 2 business days per Section 16(a))
            # More accurate business day calculation:
            # - Must account for weekends (not just divide by 7)
            # - Holidays would require a holiday calendar (not implemented here)
            is_late = False
            days_late = 0
            if trans_date:
                days_diff = (filing_date - trans_date).days
                
                # Calculate actual business days between transaction and filing
                business_days = 0
                current = trans_date
                while current < filing_date:
                    current = current + timedelta(days=1)
                    # Monday=0, Sunday=6; Skip weekends
                    if current.weekday() < 5:
                        business_days += 1
                
                # SEC requires filing within 2 business days after transaction
                # So if business_days > 2, it's late
                if business_days > 2:
                    is_late = True
                    days_late = business_days - 2
            
            # Create transaction object
            # Zero-dollar detection: Flag ALL zero-dollar transactions for scrutiny
            # ANY Form 4 transaction listed at $0 is suspicious and warrants investigation
            # However, suspicion level varies by transaction code:
            #   - HIGH SUSPICION: S (sale), P (purchase) at $0 = extremely abnormal
            #   - MEDIUM SUSPICION: G (gift), J (other), W (will) at $0 = requires scrutiny
            #   - REQUIRES REVIEW: V, A, F, M, X, etc. at $0 = may be legitimate but still needs review
            is_zero_dollar_transaction = (price == 0.0 and shares > 0)
            
            transaction = Form4Transaction(
                transaction_code=trans_code,
                transaction_code_description=description,
                transaction_category=category,
                transaction_date=trans_date,
                shares=shares,
                price_per_share=price,
                total_value=total_value,
                acquired_disposed=acq_disp,
                direct_indirect=direct_indirect,
                security_title=security_title or "Unknown Security",
                is_derivative=False,
                is_zero_dollar=is_zero_dollar_transaction,  # Flag ALL zero-dollar transactions
                is_gift=(trans_code == 'G'),
                is_late_filed=is_late,
                days_late=days_late
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error parsing non-derivative transaction: {e}")
            return None
    
    def _parse_derivative_transaction(
        self,
        trans: ET.Element,
        filing_date: date
    ) -> Optional[Form4Transaction]:
        """Parse a derivative transaction element."""
        try:
            # Security title
            security_title = self._get_text(trans, './/securityTitle/value')
            
            # Transaction date
            trans_date = self._parse_date(self._get_text(trans, './/transactionDate/value'))
            
            # Transaction coding
            coding = trans.find('.//transactionCoding')
            trans_code = self._get_text(coding, 'transactionCode') if coding else 'U'
            
            # Classify transaction
            category, description = self.classify_transaction_code(trans_code)
            
            # Transaction amounts
            amounts = trans.find('.//transactionAmounts')
            shares = self._get_float(amounts, './/transactionShares/value') if amounts else 0.0
            price = self._get_float(amounts, './/transactionPricePerShare/value') if amounts else 0.0
            acq_disp = self._get_text(amounts, './/transactionAcquiredDisposedCode/value') if amounts else 'A'
            
            # Exercise price and expiration (derivative-specific)
            exercise_price = self._get_float(trans, './/conversionOrExercisePrice/value')
            expiration = self._parse_date(self._get_text(trans, './/expirationDate/value'))
            
            # Underlying security
            underlying = self._get_text(trans, './/underlyingSecurity/underlyingSecurityTitle/value')
            
            # Calculate total value
            total_value = shares * price
            
            # Check for late filing (> 2 business days per Section 16(a))
            is_late = False
            days_late = 0
            if trans_date:
                # Calculate actual business days between transaction and filing
                business_days = 0
                current = trans_date
                while current < filing_date:
                    current = current + timedelta(days=1)
                    # Monday=0, Sunday=6; Skip weekends
                    if current.weekday() < 5:
                        business_days += 1
                
                # SEC requires filing within 2 business days after transaction
                if business_days > 2:
                    is_late = True
                    days_late = business_days - 2
            
            # Flag ALL zero-dollar derivative transactions for scrutiny
            is_zero_dollar_derivative = (price == 0.0 and shares > 0)
            
            transaction = Form4Transaction(
                transaction_code=trans_code,
                transaction_code_description=description,
                transaction_category=category,
                transaction_date=trans_date,
                shares=shares,
                price_per_share=price,
                total_value=total_value,
                acquired_disposed=acq_disp,
                direct_indirect='D',
                security_title=security_title or "Derivative Security",
                is_derivative=True,
                underlying_security=underlying,
                exercise_price=exercise_price,
                expiration_date=expiration,
                # Flag ALL zero-dollar transactions for scrutiny
                is_zero_dollar=is_zero_dollar_derivative,
                is_gift=(trans_code == 'G'),
                is_late_filed=is_late,
                days_late=days_late
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error parsing derivative transaction: {e}")
            return None
    
    def _compute_aggregates(self, filing: Form4Filing):
        """Compute aggregate values for filing."""
        for trans in filing.transactions:
            if trans.acquired_disposed == 'A':
                filing.total_acquired += trans.shares
            else:
                filing.total_disposed += trans.shares
            
            if trans.is_zero_dollar:
                filing.zero_dollar_transactions.append(trans)
            
            if trans.is_gift:
                filing.gift_transactions.append(trans)
            
            if trans.is_late_filed:
                filing.late_transactions.append(trans)
        
        filing.net_change = filing.total_acquired - filing.total_disposed
    
    def _create_empty_filing(self, accession_number: str, filing_date: date) -> Form4Filing:
        """Create empty filing for parse failures."""
        return Form4Filing(
            accession_number=accession_number,
            filing_date=filing_date,
            period_of_report=None,
            issuer_cik='',
            issuer_name='',
            reporting_owner_cik='',
            reporting_owner_name='',
            is_director=False,
            is_officer=False,
            is_ten_percent_owner=False,
            officer_title=None,
            transactions=[]
        )
    
    def _get_text(self, element: Optional[ET.Element], path: str) -> Optional[str]:
        """Safely get text from element path."""
        if element is None:
            return None
        found = element.find(path)
        return found.text.strip() if found is not None and found.text else None
    
    def _get_float(self, element: Optional[ET.Element], path: str) -> float:
        """Safely get float from element path."""
        text = self._get_text(element, path)
        if text:
            try:
                return float(text.replace(',', ''))
            except ValueError:
                return 0.0
        return 0.0
    
    def _get_bool(self, element: Optional[ET.Element], path: str) -> bool:
        """Safely get boolean from element path."""
        text = self._get_text(element, path)
        if text:
            return text.lower() in ('1', 'true', 'yes')
        return False
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%m/%d/%Y').date()
            except ValueError:
                return None

    @staticmethod
    def _extract_footnote_ids(trans_element: ET.Element) -> List[str]:
        """
        Extract all footnoteId references from a transaction element.

        Form 4 XML uses <footnoteId id="F1"/> refs inside transaction
        sub-elements (transactionCoding, transactionAmounts, ownershipNature,
        postTransactionAmounts, etc.).
        """
        ids = []
        seen = set()
        for fn_ref in trans_element.iter('footnoteId'):
            fid = fn_ref.get('id', '')
            if fid and fid not in seen:
                ids.append(fid)
                seen.add(fid)
        return ids

