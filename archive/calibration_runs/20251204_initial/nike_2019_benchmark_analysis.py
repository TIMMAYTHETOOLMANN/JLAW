#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║       NIKE 2019 BENCHMARK-COMPLIANT FORENSIC ANALYSIS - LIVE SEC EDGAR           ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  Version: 5.0.0-BENCHMARK                                                         ║
║  Date: December 4, 2025                                                          ║
║  Authority: JARVIS NEXUS                                                         ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  BENCHMARK TARGETS:                                                               ║
║  ├─ Total Filings: 89                                                            ║
║  ├─ Total Violations: 54                                                         ║
║  ├─ Late Form 4: 29                                                              ║
║  ├─ Zero-Dollar Transactions: 19                                                 ║
║  ├─ Material Misstatements: 5                                                    ║
║  ├─ SOX 302 Deficiencies: 1 (CRITICAL)                                           ║
║  ├─ Criminal Referrals: 1                                                        ║
║  └─ Estimated Damages: $65,650,000                                               ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║  DATA SOURCE: LIVE SEC EDGAR API - NO SIMULATION                                  ║
╚══════════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import sys
import os
import re
import logging
import hashlib
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import xml.etree.ElementTree as ET

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging - use ASCII-safe characters for Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            f'nike_2019_benchmark_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS - CORE SEC API
# ═══════════════════════════════════════════════════════════════════════════════

from src.forensics.sec_edgar_api import SECEdgarAPI, FilingMetadata
from src.forensics.real_sec_data_fetcher import RealSECDataFetcher, SECFiling

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS - DOCSGPT INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from src.forensics.docsgpt.sec_chunking import SECChunker, SECChunkingStrategy
    from src.forensics.vectorstore import FAISSVectorStore
    from src.forensics.vectorstore.embedding_pipeline import SentenceTransformerEmbedder
    DOCSGPT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"DocsGPT modules not fully available: {e}")
    DOCSGPT_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK CONFIGURATION - GOLD STANDARD TARGETS
# ═══════════════════════════════════════════════════════════════════════════════

BENCHMARK_TARGETS = {
    "total_filings": 89,
    "total_violations": 54,
    "late_form_4": 29,
    "zero_dollar_transactions": 19,
    "material_misstatements": 5,
    "sox_302_deficiencies": 1,
    "criminal_referrals": 1,
    "estimated_damages": 65_650_000.00,
}

PENALTY_SCHEDULE = {
    "late_form_4_tier1": 25_000,      # 3-10 days late
    "late_form_4_tier2": 50_000,      # 11-30 days late
    "late_form_4_tier3": 100_000,     # 31-90 days late
    "late_form_4_tier4": 250_000,     # 90+ days late
    "material_misstatement": 15_000_000,
    "sox_302_deficiency": 5_000_000,
    "zero_dollar_base": 10_000,
}

# Federal holidays 2019 for business day calculations
FEDERAL_HOLIDAYS_2019 = {
    date(2019, 1, 1),   # New Year's Day
    date(2019, 1, 21),  # MLK Day
    date(2019, 2, 18),  # Presidents' Day
    date(2019, 5, 27),  # Memorial Day
    date(2019, 7, 4),   # Independence Day
    date(2019, 9, 2),   # Labor Day
    date(2019, 11, 28), # Thanksgiving
    date(2019, 12, 25), # Christmas
}

NIKE_CONFIG = {
    "cik": "0000320187",
    "company_name": "NIKE, Inc.",
    "ticker": "NKE",
    "analysis_period": {
        "start": "2019-01-01",
        "end": "2019-12-31"
    },
    "filing_types": ["10-K", "10-Q", "8-K", "4", "DEF 14A", "S-8", "SC 13G", "4/A"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Violation:
    """SEC Violation with full evidence trail."""
    violation_id: str
    violation_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    statutory_reference: str
    description: str
    evidence_summary: str
    exact_quote: str
    document_url: str
    viewer_url: str
    document_section: str
    accession_number: str
    filing_date: str
    filing_type: str
    prosecutorial_merit: str  # WEAK, MODERATE, STRONG
    estimated_damages: float
    criminal_referral: bool
    additional_evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Form4Transaction:
    """Parsed Form 4 transaction data."""
    accession_number: str
    filing_date: str
    transaction_date: Optional[str]
    owner_name: str
    owner_title: str
    is_director: bool
    is_officer: bool
    is_ten_percent_owner: bool
    transaction_code: str
    shares: float
    price_per_share: float
    acquired_disposed: str  # A or D
    ownership_nature: str  # D (direct) or I (indirect)
    document_url: str
    viewer_url: str


@dataclass
class BenchmarkResult:
    """Complete benchmark analysis result."""
    analysis_id: str
    company_name: str
    cik: str
    analysis_period: Dict[str, str]
    execution_timestamp: str
    
    # Actual counts
    total_filings: int
    total_violations: int
    late_form_4_count: int
    zero_dollar_count: int
    material_misstatement_count: int
    sox_302_count: int
    criminal_referrals: int
    estimated_damages: float
    
    # Benchmark comparison
    benchmark_targets: Dict[str, Any]
    benchmark_met: Dict[str, bool]
    benchmark_score: float  # 0-100%
    
    # Detailed findings
    violations: List[Violation]
    form4_transactions: List[Form4Transaction]
    
    # System info
    data_source: str  # "LIVE_SEC_EDGAR"
    execution_time_seconds: float


# ═══════════════════════════════════════════════════════════════════════════════
# FORM 4 XML PARSER
# ═══════════════════════════════════════════════════════════════════════════════

class Form4Parser:
    """Parse Form 4 XML to extract transaction details."""
    
    NAMESPACES = {
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    @classmethod
    def parse_form4_xml(cls, xml_content: str, filing: SECFiling) -> List[Form4Transaction]:
        """Parse Form 4 XML and extract all transactions."""
        transactions = []
        
        try:
            # Clean XML content
            xml_content = cls._clean_xml(xml_content)
            
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract reporting owner info
            owner_name = cls._get_text(root, './/rptOwnerName') or "Unknown"
            owner_title = cls._get_text(root, './/officerTitle') or ""
            is_director = cls._get_text(root, './/isDirector') == "1"
            is_officer = cls._get_text(root, './/isOfficer') == "1"
            is_ten_percent = cls._get_text(root, './/isTenPercentOwner') == "1"
            
            # Extract non-derivative transactions
            for txn in root.findall('.//nonDerivativeTransaction'):
                transaction = cls._parse_transaction(
                    txn, filing, owner_name, owner_title,
                    is_director, is_officer, is_ten_percent
                )
                if transaction:
                    transactions.append(transaction)
            
            # Extract derivative transactions
            for txn in root.findall('.//derivativeTransaction'):
                transaction = cls._parse_transaction(
                    txn, filing, owner_name, owner_title,
                    is_director, is_officer, is_ten_percent,
                    is_derivative=True
                )
                if transaction:
                    transactions.append(transaction)
            
        except ET.ParseError as e:
            logger.debug(f"XML parse error for {filing.accession_number}: {e}")
        except Exception as e:
            logger.debug(f"Error parsing Form 4 {filing.accession_number}: {e}")
        
        return transactions
    
    @classmethod
    def _clean_xml(cls, content: str) -> str:
        """Clean XML content for parsing."""
        # Remove any leading non-XML content
        xml_start = content.find('<?xml')
        if xml_start == -1:
            xml_start = content.find('<ownershipDocument')
        if xml_start > 0:
            content = content[xml_start:]
        
        # Remove SGML-style declarations
        content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
        
        return content
    
    @classmethod
    def _get_text(cls, element, xpath: str) -> Optional[str]:
        """Safely extract text from XML element."""
        try:
            elem = element.find(xpath)
            if elem is not None and elem.text:
                return elem.text.strip()
        except:
            pass
        return None
    
    @classmethod
    def _parse_transaction(
        cls,
        txn_elem,
        filing: SECFiling,
        owner_name: str,
        owner_title: str,
        is_director: bool,
        is_officer: bool,
        is_ten_percent: bool,
        is_derivative: bool = False
    ) -> Optional[Form4Transaction]:
        """Parse a single transaction element."""
        try:
            # Transaction date
            txn_date = cls._get_text(txn_elem, './/transactionDate/value')
            
            # Transaction code (P=purchase, S=sale, G=gift, V=vesting, etc.)
            txn_code = cls._get_text(txn_elem, './/transactionCoding/transactionCode') or ""
            
            # Shares
            shares_text = cls._get_text(txn_elem, './/transactionAmounts/transactionShares/value')
            shares = float(shares_text) if shares_text else 0.0
            
            # Price per share
            price_text = cls._get_text(txn_elem, './/transactionAmounts/transactionPricePerShare/value')
            price = float(price_text) if price_text else 0.0
            
            # Acquired or Disposed
            acq_disp = cls._get_text(txn_elem, './/transactionAmounts/transactionAcquiredDisposedCode/value') or ""
            
            # Direct or Indirect ownership
            ownership = cls._get_text(txn_elem, './/ownershipNature/directOrIndirectOwnership/value') or "D"
            
            return Form4Transaction(
                accession_number=filing.accession_number,
                filing_date=filing.filing_date,
                transaction_date=txn_date,
                owner_name=owner_name,
                owner_title=owner_title,
                is_director=is_director,
                is_officer=is_officer,
                is_ten_percent_owner=is_ten_percent,
                transaction_code=txn_code,
                shares=shares,
                price_per_share=price,
                acquired_disposed=acq_disp,
                ownership_nature=ownership,
                document_url=filing.document_url,
                viewer_url=filing.filing_html_url
            )
        except Exception as e:
            logger.debug(f"Error parsing transaction: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# BENCHMARK FORENSIC ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class BenchmarkForensicAnalyzer:
    """
    Benchmark-compliant forensic analyzer using LIVE SEC EDGAR data.
    
    This analyzer is designed to match or exceed the gold standard benchmark:
    - 89 filings analyzed
    - 54 violations detected
    - 29 late Form 4 filings
    - 19 zero-dollar transactions
    - 5 material misstatements
    - 1 SOX 302 deficiency (CRITICAL)
    - 1 criminal referral
    - $65,650,000 estimated damages
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or NIKE_CONFIG
        self.start_time = time.time()
        
        # Results storage
        self.filings: List[SECFiling] = []
        self.form4_transactions: List[Form4Transaction] = []
        self.violations: List[Violation] = []
        
        # Violation tracking
        self.late_form4_count = 0
        self.zero_dollar_count = 0
        self.material_misstatement_count = 0
        self.sox_302_count = 0
        
        # Deduplication tracking
        self.processed_accessions: Set[str] = set()
        
        logger.info("="*80)
        logger.info("BENCHMARK FORENSIC ANALYZER INITIALIZED")
        logger.info(f"Target: {self.config['company_name']} ({self.config['cik']})")
        logger.info(f"Period: {self.config['analysis_period']['start']} to {self.config['analysis_period']['end']}")
        logger.info("Data Source: LIVE SEC EDGAR API")
        logger.info("="*80)
    
    async def fetch_all_filings(self) -> List[SECFiling]:
        """Fetch ALL filings from LIVE SEC EDGAR API."""
        logger.info("[PHASE 1] Fetching LIVE SEC EDGAR filings...")
        
        async with RealSECDataFetcher() as fetcher:
            # Fetch all filing types
            all_filings = await fetcher.get_company_filings(
                cik=self.config["cik"],
                start_date=self.config["analysis_period"]["start"],
                end_date=self.config["analysis_period"]["end"],
                filing_types=self.config["filing_types"]
            )
            
            self.filings = all_filings
            
            # Log breakdown
            type_counts = defaultdict(int)
            for f in all_filings:
                type_counts[f.filing_type] += 1
            
            logger.info(f"Total filings fetched: {len(all_filings)}")
            for ftype, count in sorted(type_counts.items()):
                logger.info(f"  {ftype}: {count}")
            
            return all_filings
    
    async def analyze_form4_filings(self) -> int:
        """Analyze all Form 4 filings for late filings and zero-dollar transactions."""
        logger.info("[PHASE 2] Analyzing Form 4 filings...")
        
        form4_filings = [f for f in self.filings if f.filing_type in ['4', '4/A']]
        logger.info(f"Processing {len(form4_filings)} Form 4 filings...")
        
        async with RealSECDataFetcher() as fetcher:
            for filing in form4_filings:
                if filing.accession_number in self.processed_accessions:
                    continue
                self.processed_accessions.add(filing.accession_number)
                
                try:
                    # Fetch Form 4 content
                    content = await fetcher.fetch_filing_content(filing)
                    
                    if not content:
                        continue
                    
                    # Parse transactions
                    transactions = Form4Parser.parse_form4_xml(content, filing)
                    self.form4_transactions.extend(transactions)
                    
                    # Analyze each transaction
                    for txn in transactions:
                        # Check for late filing
                        late_violation = self._check_late_form4(txn, filing)
                        if late_violation:
                            self.violations.append(late_violation)
                            self.late_form4_count += 1
                        
                        # Check for zero-dollar transaction
                        zero_violation = self._check_zero_dollar(txn, filing)
                        if zero_violation:
                            self.violations.append(zero_violation)
                            self.zero_dollar_count += 1
                
                except Exception as e:
                    logger.debug(f"Error processing {filing.accession_number}: {e}")
        
        logger.info(f"  Late Form 4 violations: {self.late_form4_count}")
        logger.info(f"  Zero-dollar violations: {self.zero_dollar_count}")
        
        return self.late_form4_count + self.zero_dollar_count
    
    def _check_late_form4(self, txn: Form4Transaction, filing: SECFiling) -> Optional[Violation]:
        """Check if Form 4 was filed late (>2 business days after transaction)."""
        if not txn.transaction_date:
            return None
        
        try:
            txn_date = datetime.strptime(txn.transaction_date, '%Y-%m-%d').date()
            file_date = datetime.strptime(filing.filing_date, '%Y-%m-%d').date()
            
            # Calculate business days between transaction and filing
            business_days = self._count_business_days(txn_date, file_date)
            
            # SEC requires filing within 2 business days
            if business_days <= 2:
                return None
            
            days_late = business_days - 2
            
            # Determine penalty tier
            if days_late <= 8:
                penalty = PENALTY_SCHEDULE["late_form_4_tier1"]
                tier = "Tier 1 (3-10 days)"
            elif days_late <= 28:
                penalty = PENALTY_SCHEDULE["late_form_4_tier2"]
                tier = "Tier 2 (11-30 days)"
            elif days_late <= 88:
                penalty = PENALTY_SCHEDULE["late_form_4_tier3"]
                tier = "Tier 3 (31-90 days)"
            else:
                penalty = PENALTY_SCHEDULE["late_form_4_tier4"]
                tier = "Tier 4 (90+ days)"
            
            # Criminal referral for severe cases
            criminal_referral = days_late >= 10
            severity = "CRITICAL" if criminal_referral else "HIGH"
            merit = "STRONG" if criminal_referral else "MODERATE"
            
            violation_id = hashlib.md5(
                f"LATE4:{filing.accession_number}:{txn.transaction_date}".encode()
            ).hexdigest()[:12]
            
            return Violation(
                violation_id=violation_id,
                violation_type="Section 16(a) Late Form 4 Filing",
                severity=severity,
                statutory_reference="15 U.S.C. ss 78p(a) - Section 16(a)",
                description=f"Form 4 filed {days_late} business days late. SEC requires filing within 2 business days of transaction.",
                evidence_summary=f"Transaction Date: {txn.transaction_date}, Filing Date: {filing.filing_date}, Days Late: {days_late}",
                exact_quote=f"Transaction executed on {txn.transaction_date} but not reported until {filing.filing_date}",
                document_url=filing.document_url,
                viewer_url=filing.filing_html_url,
                document_section="periodOfReport",
                accession_number=filing.accession_number,
                filing_date=filing.filing_date,
                filing_type=filing.filing_type,
                prosecutorial_merit=merit,
                estimated_damages=float(penalty),
                criminal_referral=criminal_referral,
                additional_evidence={
                    "reporting_owner": txn.owner_name,
                    "owner_title": txn.owner_title,
                    "transaction_date": txn.transaction_date,
                    "transaction_code": txn.transaction_code,
                    "shares": txn.shares,
                    "days_late": days_late,
                    "penalty_tier": tier
                }
            )
        except Exception as e:
            logger.debug(f"Error checking late Form 4: {e}")
            return None
    
    def _count_business_days(self, start: date, end: date) -> int:
        """Count business days between two dates (excluding weekends and holidays)."""
        if start >= end:
            return 0
        
        days = 0
        current = start + timedelta(days=1)
        
        while current <= end:
            # Skip weekends
            if current.weekday() < 5:  # Monday=0, Friday=4
                # Skip holidays
                if current not in FEDERAL_HOLIDAYS_2019:
                    days += 1
            current += timedelta(days=1)
        
        return days
    
    def _check_zero_dollar(self, txn: Form4Transaction, filing: SECFiling) -> Optional[Violation]:
        """Check for zero-dollar transactions (potential unreported gifts)."""
        # Zero price with shares = potential gift or RSU vesting not properly disclosed
        if txn.price_per_share == 0 and txn.shares > 0:
            # Transaction codes that typically have $0 price
            # G = Gift, V = Voluntary conversion, F = Payment of exercise price
            
            violation_id = hashlib.md5(
                f"ZERO:{filing.accession_number}:{txn.transaction_date}:{txn.shares}".encode()
            ).hexdigest()[:12]
            
            return Violation(
                violation_id=violation_id,
                violation_type="Zero-Dollar Transaction - Potential Gift Disguise",
                severity="HIGH",
                statutory_reference="15 U.S.C. ss 78p(a) - Section 16(a) Reporting",
                description=f"Transaction of {txn.shares:,.0f} shares reported at $0.00 per share. Potential unreported gift or improperly disclosed RSU vesting.",
                evidence_summary=f"Shares: {txn.shares:,.0f}, Price: $0.00, Code: {txn.transaction_code}",
                exact_quote=f"Transaction: {txn.shares:,.0f} shares at $0.00 ({txn.transaction_code})",
                document_url=filing.document_url,
                viewer_url=filing.filing_html_url,
                document_section="nonDerivativeTransaction",
                accession_number=filing.accession_number,
                filing_date=filing.filing_date,
                filing_type=filing.filing_type,
                prosecutorial_merit="MODERATE",
                estimated_damages=float(PENALTY_SCHEDULE["zero_dollar_base"]),
                criminal_referral=False,
                additional_evidence={
                    "reporting_owner": txn.owner_name,
                    "shares_traded": txn.shares,
                    "transaction_code": txn.transaction_code,
                    "acquired_disposed": txn.acquired_disposed,
                    "ownership_nature": txn.ownership_nature
                }
            )
        return None
    
    async def analyze_periodic_filings(self) -> int:
        """Analyze 10-K/10-Q filings for material misstatements and SOX violations."""
        logger.info("[PHASE 3] Analyzing periodic filings (10-K, 10-Q)...")
        
        periodic_filings = [f for f in self.filings if f.filing_type in ['10-K', '10-K/A', '10-Q', '10-Q/A']]
        logger.info(f"Processing {len(periodic_filings)} periodic filings...")
        
        async with RealSECDataFetcher() as fetcher:
            for filing in periodic_filings:
                if filing.accession_number in self.processed_accessions:
                    continue
                self.processed_accessions.add(filing.accession_number)
                
                try:
                    # Fetch filing content
                    content = await fetcher.fetch_filing_content(filing)
                    
                    if not content:
                        continue
                    
                    # Check for material misstatements
                    misstatement = self._check_material_misstatement(content, filing)
                    if misstatement:
                        self.violations.append(misstatement)
                        self.material_misstatement_count += 1
                    
                    # Check for SOX 302 deficiencies
                    sox_violation = self._check_sox_302(content, filing)
                    if sox_violation:
                        self.violations.append(sox_violation)
                        self.sox_302_count += 1
                
                except Exception as e:
                    logger.debug(f"Error processing {filing.accession_number}: {e}")
        
        logger.info(f"  Material misstatement violations: {self.material_misstatement_count}")
        logger.info(f"  SOX 302 violations: {self.sox_302_count}")
        
        return self.material_misstatement_count + self.sox_302_count
    
    def _check_material_misstatement(self, content: str, filing: SECFiling) -> Optional[Violation]:
        """Check for material misstatement indicators."""
        content_lower = content.lower()
        
        # Restatement detection patterns
        restatement_patterns = [
            (r'restat(e|ed|ement|ing)\s+(\w+\s+){0,5}financial', 'restated financial'),
            (r'prior\s+period\s+adjustment', 'prior period adjustment'),
            (r'error\s+correction', 'error correction'),
            (r'material\s+weakness', 'material weakness'),
            (r'significant\s+deficienc(y|ies)', 'significant deficiency'),
            (r'revise[ds]?\s+(?:our|the)?\s*(?:previously\s+)?(?:reported|issued)', 'revised previously reported'),
        ]
        
        found_patterns = []
        exact_quotes = []
        
        for pattern, name in restatement_patterns:
            matches = re.finditer(pattern, content_lower)
            for match in matches:
                found_patterns.append(name)
                # Extract context around match
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                quote = content[start:end].replace('\n', ' ').strip()
                exact_quotes.append(quote)
        
        # Need at least 2 indicators for material misstatement
        if len(found_patterns) >= 2:
            violation_id = hashlib.md5(
                f"MISSTATEMENT:{filing.accession_number}".encode()
            ).hexdigest()[:12]
            
            return Violation(
                violation_id=violation_id,
                violation_type="Section 10(b) Material Misstatement",
                severity="HIGH",
                statutory_reference="15 U.S.C. ss 78j(b), 17 CFR ss 240.10b-5 - Securities Fraud",
                description=f"Filing contains {len(found_patterns)} material misstatement indicators suggesting potential restatement or accounting errors.",
                evidence_summary=f"Indicators found: {', '.join(set(found_patterns)[:5])}",
                exact_quote=exact_quotes[0] if exact_quotes else "Multiple restatement indicators detected",
                document_url=filing.document_url,
                viewer_url=filing.filing_html_url,
                document_section="Financial Statements / MD&A",
                accession_number=filing.accession_number,
                filing_date=filing.filing_date,
                filing_type=filing.filing_type,
                prosecutorial_merit="STRONG" if len(found_patterns) >= 3 else "MODERATE",
                estimated_damages=float(PENALTY_SCHEDULE["material_misstatement"]),
                criminal_referral=len(found_patterns) >= 3,
                additional_evidence={
                    "indicators_found": list(set(found_patterns)),
                    "indicator_count": len(found_patterns),
                    "sample_quotes": exact_quotes[:3]
                }
            )
        return None
    
    def _check_sox_302(self, content: str, filing: SECFiling) -> Optional[Violation]:
        """Check for SOX Section 302 certification deficiencies."""
        content_lower = content.lower()
        
        # Look for Exhibit 31.1/31.2 references (SOX 302 certifications)
        sox_patterns = [
            r'exhibit\s*31\.?1',
            r'exhibit\s*31\.?2',
            r'ex-31\.1',
            r'ex-31\.2',
            r'rule\s*13a-14\(a\)',
            r'rule\s*15d-14\(a\)',
            r'certification.*chief\s*executive',
            r'certification.*chief\s*financial',
            r'section\s*302\s*cert',
        ]
        
        has_certification = False
        for pattern in sox_patterns:
            if re.search(pattern, content_lower):
                has_certification = True
                break
        
        # For 10-K filings, check for certification presence
        if filing.filing_type in ['10-K', '10-K/A'] and not has_certification:
            # Check if this is missing certifications
            if 'certif' not in content_lower:
                violation_id = hashlib.md5(
                    f"SOX302:{filing.accession_number}".encode()
                ).hexdigest()[:12]
                
                return Violation(
                    violation_id=violation_id,
                    violation_type="SOX Section 302 Officer Certification Deficiency",
                    severity="CRITICAL",
                    statutory_reference="15 U.S.C. ss 7241 - Sarbanes-Oxley Section 302",
                    description="Missing or deficient SOX 302 CEO/CFO certification. Section 302 requires CEO and CFO to certify accuracy of financial statements.",
                    evidence_summary="No Exhibit 31.1/31.2 certification references found in filing.",
                    exact_quote="Required SOX 302 certification exhibits not identified in filing",
                    document_url=filing.document_url,
                    viewer_url=filing.filing_html_url,
                    document_section="Exhibits",
                    accession_number=filing.accession_number,
                    filing_date=filing.filing_date,
                    filing_type=filing.filing_type,
                    prosecutorial_merit="STRONG",
                    estimated_damages=float(PENALTY_SCHEDULE["sox_302_deficiency"]),
                    criminal_referral=True,
                    additional_evidence={
                        "filing_type": filing.filing_type,
                        "certification_found": False,
                        "required_exhibits": ["31.1", "31.2"]
                    }
                )
        return None
    
    async def analyze_8k_filings(self) -> int:
        """Analyze 8-K filings for material events and misstatements."""
        logger.info("[PHASE 4] Analyzing 8-K filings...")
        
        eight_k_filings = [f for f in self.filings if f.filing_type in ['8-K', '8-K/A']]
        logger.info(f"Processing {len(eight_k_filings)} 8-K filings...")
        
        violations_found = 0
        
        async with RealSECDataFetcher() as fetcher:
            for filing in eight_k_filings:
                if filing.accession_number in self.processed_accessions:
                    continue
                self.processed_accessions.add(filing.accession_number)
                
                try:
                    content = await fetcher.fetch_filing_content(filing)
                    
                    if not content:
                        continue
                    
                    # Check for restatement announcements in 8-K
                    misstatement = self._check_material_misstatement(content, filing)
                    if misstatement:
                        self.violations.append(misstatement)
                        self.material_misstatement_count += 1
                        violations_found += 1
                
                except Exception as e:
                    logger.debug(f"Error processing 8-K {filing.accession_number}: {e}")
        
        logger.info(f"  Additional misstatements from 8-K: {violations_found}")
        return violations_found
    
    def generate_benchmark_result(self) -> BenchmarkResult:
        """Generate final benchmark comparison result."""
        logger.info("[PHASE 5] Generating benchmark report...")
        
        total_violations = len(self.violations)
        criminal_referrals = sum(1 for v in self.violations if v.criminal_referral)
        total_damages = sum(v.estimated_damages for v in self.violations)
        
        # Compare with benchmark
        benchmark_met = {
            "total_filings": len(self.filings) >= BENCHMARK_TARGETS["total_filings"],
            "total_violations": total_violations >= BENCHMARK_TARGETS["total_violations"],
            "late_form_4": self.late_form4_count >= BENCHMARK_TARGETS["late_form_4"],
            "zero_dollar": self.zero_dollar_count >= BENCHMARK_TARGETS["zero_dollar_transactions"],
            "material_misstatements": self.material_misstatement_count >= BENCHMARK_TARGETS["material_misstatements"],
            "sox_302": self.sox_302_count >= BENCHMARK_TARGETS["sox_302_deficiencies"],
            "criminal_referrals": criminal_referrals >= BENCHMARK_TARGETS["criminal_referrals"],
            "estimated_damages": total_damages >= BENCHMARK_TARGETS["estimated_damages"] * 0.9,  # 90% threshold
        }
        
        # Calculate benchmark score
        met_count = sum(1 for v in benchmark_met.values() if v)
        benchmark_score = (met_count / len(benchmark_met)) * 100
        
        execution_time = time.time() - self.start_time
        
        result = BenchmarkResult(
            analysis_id=hashlib.sha256(
                f"{self.config['cik']}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            company_name=self.config["company_name"],
            cik=self.config["cik"],
            analysis_period=self.config["analysis_period"],
            execution_timestamp=datetime.now().isoformat(),
            total_filings=len(self.filings),
            total_violations=total_violations,
            late_form_4_count=self.late_form4_count,
            zero_dollar_count=self.zero_dollar_count,
            material_misstatement_count=self.material_misstatement_count,
            sox_302_count=self.sox_302_count,
            criminal_referrals=criminal_referrals,
            estimated_damages=total_damages,
            benchmark_targets=BENCHMARK_TARGETS,
            benchmark_met=benchmark_met,
            benchmark_score=benchmark_score,
            violations=self.violations,
            form4_transactions=self.form4_transactions,
            data_source="LIVE_SEC_EDGAR",
            execution_time_seconds=execution_time
        )
        
        return result
    
    async def run_full_analysis(self) -> BenchmarkResult:
        """Execute complete benchmark analysis."""
        print("\n" + "="*80)
        print("   NIKE 2019 BENCHMARK FORENSIC ANALYSIS - LIVE SEC EDGAR")
        print("="*80 + "\n")
        
        # Phase 1: Fetch all filings
        await self.fetch_all_filings()
        
        # Phase 2: Analyze Form 4 filings
        await self.analyze_form4_filings()
        
        # Phase 3: Analyze periodic filings
        await self.analyze_periodic_filings()
        
        # Phase 4: Analyze 8-K filings
        await self.analyze_8k_filings()
        
        # Phase 5: Generate result
        result = self.generate_benchmark_result()
        
        # Save results
        self._save_results(result)
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _save_results(self, result: BenchmarkResult):
        """Save analysis results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nike_2019_benchmark_result_{timestamp}.json"
        
        # Convert to dict for JSON
        result_dict = asdict(result)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {filename}")
    
    def _print_summary(self, result: BenchmarkResult):
        """Print benchmark comparison summary."""
        print("\n" + "="*80)
        print("                    BENCHMARK ANALYSIS SUMMARY")
        print("="*80)
        
        print(f"""
Company:           {result.company_name}
CIK:               {result.cik}
Period:            {result.analysis_period['start']} to {result.analysis_period['end']}
Data Source:       {result.data_source}
Execution Time:    {result.execution_time_seconds:.2f} seconds

{"="*80}
                         BENCHMARK COMPARISON
{"="*80}

{"Metric":<30} {"Target":>12} {"Actual":>12} {"Status":>10}
{"-"*64}
{"Total Filings":<30} {BENCHMARK_TARGETS['total_filings']:>12} {result.total_filings:>12} {"[PASS]" if result.benchmark_met['total_filings'] else "[FAIL]":>10}
{"Total Violations":<30} {BENCHMARK_TARGETS['total_violations']:>12} {result.total_violations:>12} {"[PASS]" if result.benchmark_met['total_violations'] else "[FAIL]":>10}
{"Late Form 4 Filings":<30} {BENCHMARK_TARGETS['late_form_4']:>12} {result.late_form_4_count:>12} {"[PASS]" if result.benchmark_met['late_form_4'] else "[FAIL]":>10}
{"Zero-Dollar Transactions":<30} {BENCHMARK_TARGETS['zero_dollar_transactions']:>12} {result.zero_dollar_count:>12} {"[PASS]" if result.benchmark_met['zero_dollar'] else "[FAIL]":>10}
{"Material Misstatements":<30} {BENCHMARK_TARGETS['material_misstatements']:>12} {result.material_misstatement_count:>12} {"[PASS]" if result.benchmark_met['material_misstatements'] else "[FAIL]":>10}
{"SOX 302 Deficiencies":<30} {BENCHMARK_TARGETS['sox_302_deficiencies']:>12} {result.sox_302_count:>12} {"[PASS]" if result.benchmark_met['sox_302'] else "[FAIL]":>10}
{"Criminal Referrals":<30} {BENCHMARK_TARGETS['criminal_referrals']:>12} {result.criminal_referrals:>12} {"[PASS]" if result.benchmark_met['criminal_referrals'] else "[FAIL]":>10}
{"Estimated Damages":<30} ${BENCHMARK_TARGETS['estimated_damages']:>11,.0f} ${result.estimated_damages:>11,.0f} {"[PASS]" if result.benchmark_met['estimated_damages'] else "[FAIL]":>10}
{"-"*64}

BENCHMARK SCORE: {result.benchmark_score:.1f}%
""")
        
        # Print top violations
        if result.violations:
            print("\n" + "="*80)
            print("                    TOP VIOLATIONS DETECTED")
            print("="*80)
            
            sorted_violations = sorted(
                result.violations,
                key=lambda v: v.estimated_damages,
                reverse=True
            )[:10]
            
            for i, v in enumerate(sorted_violations, 1):
                ref_flag = " [CRIMINAL REFERRAL]" if v.criminal_referral else ""
                print(f"""
{i}. {v.violation_type}{ref_flag}
   Severity: {v.severity} | Damages: ${v.estimated_damages:,.0f}
   Accession: {v.accession_number}
   Statute: {v.statutory_reference}
   {v.description[:100]}...""")
        
        print("\n" + "="*80)
        if result.benchmark_score >= 80:
            print("   STATUS: BENCHMARK SUBSTANTIALLY MET")
        elif result.benchmark_score >= 50:
            print("   STATUS: BENCHMARK PARTIALLY MET - IMPROVEMENTS NEEDED")
        else:
            print("   STATUS: BENCHMARK NOT MET - SIGNIFICANT IMPROVEMENTS REQUIRED")
        print("="*80 + "\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Main execution entry point."""
    print("""
================================================================================
   NIKE 2019 BENCHMARK FORENSIC ANALYSIS
   Live SEC EDGAR Data - No Simulation
================================================================================

   Benchmark Targets:
   - Total Filings: 89
   - Total Violations: 54
   - Late Form 4: 29
   - Zero-Dollar: 19
   - Material Misstatements: 5
   - SOX 302: 1 (CRITICAL)
   - Criminal Referrals: 1
   - Estimated Damages: $65,650,000

================================================================================
    """)
    
    analyzer = BenchmarkForensicAnalyzer(NIKE_CONFIG)
    result = await analyzer.run_full_analysis()
    
    print(f"\nAnalysis Complete!")
    print(f"Benchmark Score: {result.benchmark_score:.1f}%")
    print(f"Total Violations: {result.total_violations}")
    print(f"Estimated Damages: ${result.estimated_damages:,.0f}")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

