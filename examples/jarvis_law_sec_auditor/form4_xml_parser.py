"""
JARVIS:LAW - Form 4 XML Parser
Extracts REAL data from SEC Form 4 XML files with ZERO tolerance for N/A
"""

from lxml import etree
from typing import Dict, List, Optional
from pathlib import Path


class Form4XMLParser:
    """Parse Form 4 XML files to extract structured transaction data"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.tree = None
        self.root = None
        self._load_xml()
    
    def _load_xml(self):
        """Load and parse XML file"""
        try:
            with open(self.file_path, 'rb') as f:
                self.tree = etree.parse(f)
                self.root = self.tree.getroot()
        except Exception as e:
            raise Exception(f"Failed to load XML: {e}")
    
    def _get_text(self, element, xpath: str, default: str = None) -> Optional[str]:
        """Safely extract text from XML element"""
        try:
            result = element.xpath(xpath)
            if result and len(result) > 0:
                text = result[0].text if hasattr(result[0], 'text') else str(result[0])
                return text.strip() if text else default
            return default
        except:
            return default
    
    def extract_reporting_owner(self) -> Dict:
        """Extract reporting owner information"""
        owner = {}
        
        # Find reportingOwner element
        reporting_owner = self.root.find('.//reportingOwner')
        if reporting_owner is None:
            return owner
        
        # Owner name
        owner_id = reporting_owner.find('.//reportingOwnerId')
        if owner_id is not None:
            owner['cik'] = self._get_text(owner_id, './rptOwnerCik')
            owner['name'] = self._get_text(owner_id, './rptOwnerName')
        
        # Owner address
        address = {}
        owner_addr = reporting_owner.find('.//reportingOwnerAddress')
        if owner_addr is not None:
            address['street1'] = self._get_text(owner_addr, './rptOwnerStreet1')
            address['street2'] = self._get_text(owner_addr, './rptOwnerStreet2')
            address['city'] = self._get_text(owner_addr, './rptOwnerCity')
            address['state'] = self._get_text(owner_addr, './rptOwnerState')
            address['zipcode'] = self._get_text(owner_addr, './rptOwnerZipCode')
        
        owner['address'] = address
        
        # Relationship
        relationship = {}
        owner_rel = reporting_owner.find('.//reportingOwnerRelationship')
        if owner_rel is not None:
            relationship['is_director'] = self._get_text(owner_rel, './isDirector') == '1'
            relationship['is_officer'] = self._get_text(owner_rel, './isOfficer') == '1'
            relationship['is_ten_percent_owner'] = self._get_text(owner_rel, './isTenPercentOwner') == '1'
            relationship['is_other'] = self._get_text(owner_rel, './isOther') == '1'
            relationship['officer_title'] = self._get_text(owner_rel, './officerTitle')
        
        owner['relationship'] = relationship
        
        return owner
    
    def extract_issuer(self) -> Dict:
        """Extract issuer (company) information"""
        issuer = {}
        
        issuer_elem = self.root.find('.//issuer')
        if issuer_elem is not None:
            issuer['cik'] = self._get_text(issuer_elem, './issuerCik')
            issuer['name'] = self._get_text(issuer_elem, './issuerName')
            issuer['trading_symbol'] = self._get_text(issuer_elem, './issuerTradingSymbol')
        
        return issuer
    
    def extract_non_derivative_transactions(self) -> List[Dict]:
        """Extract non-derivative transactions (Table I)"""
        transactions = []
        
        # Find all nonDerivativeTransaction elements
        for trans_elem in self.root.findall('.//nonDerivativeTransaction'):
            transaction = {}
            
            # Security title
            security = trans_elem.find('.//securityTitle')
            if security is not None:
                transaction['security_title'] = self._get_text(security, './value')
            
            # Transaction date
            trans_date = trans_elem.find('.//transactionDate')
            if trans_date is not None:
                transaction['transaction_date'] = self._get_text(trans_date, './value')
            
            # Transaction coding
            coding = trans_elem.find('.//transactionCoding')
            if coding is not None:
                transaction['transaction_code'] = self._get_text(coding, './transactionCode')
                transaction['equity_swap_involved'] = self._get_text(coding, './equitySwapInvolved') == '1'
            
            # Transaction amounts
            amounts = trans_elem.find('.//transactionAmounts')
            if amounts is not None:
                transaction['shares'] = self._get_text(amounts, './transactionShares/value')
                transaction['price_per_share'] = self._get_text(amounts, './transactionPricePerShare/value')
                transaction['acquired_disposed'] = self._get_text(amounts, './transactionAcquiredDisposedCode/value')
            
            # Post-transaction amounts
            post_trans = trans_elem.find('.//postTransactionAmounts')
            if post_trans is not None:
                transaction['shares_owned_after'] = self._get_text(post_trans, './sharesOwnedFollowingTransaction/value')
            
            # Ownership nature
            ownership = trans_elem.find('.//ownershipNature')
            if ownership is not None:
                transaction['direct_indirect'] = self._get_text(ownership, './directOrIndirectOwnership/value')
                transaction['nature_of_ownership'] = self._get_text(ownership, './natureOfOwnership/value')
            
            transactions.append(transaction)
        
        return transactions
    
    def extract_derivative_transactions(self) -> List[Dict]:
        """Extract derivative transactions (Table II)"""
        transactions = []
        
        # Find all derivativeTransaction elements
        for trans_elem in self.root.findall('.//derivativeTransaction'):
            transaction = {}
            
            # Security title
            security = trans_elem.find('.//securityTitle')
            if security is not None:
                transaction['security_title'] = self._get_text(security, './value')
            
            # Conversion/exercise price
            conv_price = trans_elem.find('.//conversionOrExercisePrice')
            if conv_price is not None:
                transaction['exercise_price'] = self._get_text(conv_price, './value')
            
            # Transaction date
            trans_date = trans_elem.find('.//transactionDate')
            if trans_date is not None:
                transaction['transaction_date'] = self._get_text(trans_date, './value')
            
            # Transaction coding
            coding = trans_elem.find('.//transactionCoding')
            if coding is not None:
                transaction['transaction_code'] = self._get_text(coding, './transactionCode')
            
            # Transaction amounts
            amounts = trans_elem.find('.//transactionAmounts')
            if amounts is not None:
                transaction['shares'] = self._get_text(amounts, './transactionShares/value')
                transaction['price_per_share'] = self._get_text(amounts, './transactionPricePerShare/value')
                transaction['acquired_disposed'] = self._get_text(amounts, './transactionAcquiredDisposedCode/value')
            
            # Post-transaction
            post_trans = trans_elem.find('.//postTransactionAmounts')
            if post_trans is not None:
                transaction['shares_owned_after'] = self._get_text(post_trans, './sharesOwnedFollowingTransaction/value')
            
            # Underlying security
            underlying = trans_elem.find('.//underlyingSecurity')
            if underlying is not None:
                transaction['underlying_security_title'] = self._get_text(underlying, './underlyingSecurityTitle/value')
                transaction['underlying_security_shares'] = self._get_text(underlying, './underlyingSecurityShares/value')
            
            # Ownership nature
            ownership = trans_elem.find('.//ownershipNature')
            if ownership is not None:
                transaction['direct_indirect'] = self._get_text(ownership, './directOrIndirectOwnership/value')
            
            transactions.append(transaction)
        
        return transactions
    
    def extract_footnotes(self) -> List[Dict]:
        """Extract footnotes"""
        footnotes = []
        
        for footnote in self.root.findall('.//footnote'):
            fn = {}
            fn['id'] = footnote.get('id', '')
            fn['text'] = footnote.text.strip() if footnote.text else ''
            footnotes.append(fn)
        
        return footnotes
    
    def extract_all(self) -> Dict:
        """Extract all data from Form 4 XML"""
        return {
            'reporting_owner': self.extract_reporting_owner(),
            'issuer': self.extract_issuer(),
            'non_derivative_transactions': self.extract_non_derivative_transactions(),
            'derivative_transactions': self.extract_derivative_transactions(),
            'footnotes': self.extract_footnotes()
        }


# Export
__all__ = ['Form4XMLParser']

