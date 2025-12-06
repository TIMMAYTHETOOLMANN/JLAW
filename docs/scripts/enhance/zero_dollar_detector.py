#!/usr/bin/env python3
"""
JLAW Zero-Dollar Transaction Detector (Integrated Version)
═══════════════════════════════════════════════════════════════════════════════

Detects and analyzes $0. 00 transactions in SEC Form 4 filings. 
This is the integrated version for the financial_forensics subpackage. 

Author: JLAW Forensic Analysis System
Version: 1.0.0
═══════════════════════════════════════════════════════════════════════════════
"""

import hashlib
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("JLAW. ZeroDollarDetector")


class TransactionCode(Enum):
    """SEC Form 4 Transaction Codes with forensic significance"""
    P = ("Open market purchase", 1)
    S = ("Open market sale", 2)
    A = ("Grant/Award", 4)
    M = ("Exercise of derivative", 3)
    G = ("Gift", 5)  # CRITICAL
    J = ("Other acquisition/disposition", 5)  # CRITICAL
    F = ("Tax withholding", 3)
    C = ("Conversion of derivative", 3)
    D = ("Disposition to issuer", 2)
    E = ("Expiration of derivative", 2)
    H = ("Expiration of short derivative", 2)
    I = ("Discretionary transaction", 4)
    K = ("Equity swap", 4)
    L = ("Small acquisition", 2)
    U = ("Disposition pursuant to tender", 2)
    W = ("Acquisition pursuant to divorce", 4)
    X = ("Exercise of in-the-money derivative", 3)
    Z = ("Deposit into voting trust", 3)
    
    def __init__(self, description: str, forensic_priority: int):
        self.description = description
        self.forensic_priority = forensic_priority


@dataclass
class ZeroDollarTransaction:
    """Represents a $0.00 transaction from Form 4"""
    transaction_id: str = field(default_factory=lambda: str(uuid. uuid4()))
    accession_number: str = ""
    filing_date: datetime = field(default_factory=datetime.now)
    transaction_date: datetime = field(default_factory=datetime.now)
    
    issuer_cik: str = ""
    issuer_name: str = ""
    issuer_ticker: str = ""
    
    owner_cik: str = ""
    owner_name: str = ""
    owner_relationship: str = ""
    owner_title: str = ""
    
    transaction_code: str = ""
    transaction_code_description: str = ""
    shares: float = 0.0
    price_per_share: float = 0.0
    
    is_derivative: bool = False
    exercise_price: float = 0.0
    
    footnotes: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    forensic_priority: int = 0
    anomaly_score: float = 0.0
    
    content_hash: str = ""
    source_url: str = ""
    
    def compute_hash(self) -> str:
        data = f"{self. accession_number}|{self.transaction_date}|{self.owner_cik}|{self.shares}|{self. transaction_code}"
        self.content_hash = hashlib.sha256(data.encode()). hexdigest()
        return self.content_hash
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "transaction_code": self. transaction_code,
            "shares": self.shares,
            "price_per_share": self.price_per_share,
            "owner_name": self.owner_name,
            "issuer_name": self.issuer_name,
            "forensic_priority": self.forensic_priority,
            "anomaly_score": self.anomaly_score,
            "red_flags": self. red_flags,
            "source_url": self. source_url
        }


class ZeroDollarDetector:
    """Detects $0.00 transactions in Form 4 filings"""
    
    RED_FLAG_PATTERNS = {
        'LARGE_GIFT_NO_FOOTNOTE': 'Large gift transaction without explanatory footnote',
        'J_CODE_MISSING_FOOTNOTE': 'J-code transaction missing required footnote',
        'GIFT_BEFORE_EVENT': 'Gift transaction preceding material event',
        'ZERO_STRIKE_DERIVATIVE': 'Zero-strike derivative security'
    }
    
    def parse_form4_xml(self, xml_content: str, source_url: str = "") -> List[ZeroDollarTransaction]:
        """Parse Form 4 XML and extract $0.00 transactions"""
        transactions = []
        
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"XML Parse Error: {e}")
            return transactions
        
        # Extract issuer info
        issuer_cik = self._get_text(root, '. //issuerCik') or ""
        issuer_name = self._get_text(root, './/issuerName') or ""
        issuer_ticker = self._get_text(root, './/issuerTradingSymbol') or ""
        
        # Extract owner info
        owner_cik = self._get_text(root, './/rptOwnerCik') or ""
        owner_name = self._get_text(root, './/rptOwnerName') or ""
        
        # Get relationships
        relationships = []
        if self._get_text(root, './/isDirector') == '1':
            relationships.append('Director')
        if self._get_text(root, './/isOfficer') == '1':
            relationships. append('Officer')
        if self._get_text(root, './/isTenPercentOwner') == '1':
            relationships.append('10% Owner')
        owner_relationship = ', '.join(relationships) if relationships else 'Unknown'
        owner_title = self._get_text(root, './/officerTitle') or ""
        
        # Get footnotes
        footnotes_map = {}
        for footnote in root.findall('.//footnote'):
            fn_id = footnote.get('id', '')
            fn_text = footnote.text or ""
            if fn_id:
                footnotes_map[fn_id] = fn_text
        
        # Process non-derivative transactions
        for txn in root.findall('.//nonDerivativeTransaction'):
            price = self._parse_price(txn)
            if price == 0.0:
                zero_txn = self._extract_transaction(
                    txn, False, issuer_cik, issuer_name, issuer_ticker,
                    owner_cik, owner_name, owner_relationship, owner_title,
                    footnotes_map, source_url
                )
                if zero_txn:
                    transactions. append(zero_txn)
        
        # Process derivative transactions
        for txn in root.findall('.//derivativeTransaction'):
            price = self._parse_price(txn)
            exercise = self._parse_exercise_price(txn)
            if price == 0.0 or exercise == 0. 0:
                zero_txn = self._extract_transaction(
                    txn, True, issuer_cik, issuer_name, issuer_ticker,
                    owner_cik, owner_name, owner_relationship, owner_title,
                    footnotes_map, source_url
                )
                if zero_txn:
                    transactions.append(zero_txn)
        
        return transactions
    
    def _extract_transaction(
        self, txn_element: ET.Element, is_derivative: bool,
        issuer_cik: str, issuer_name: str, issuer_ticker: str,
        owner_cik: str, owner_name: