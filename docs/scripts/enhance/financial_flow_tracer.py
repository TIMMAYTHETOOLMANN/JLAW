#!/usr/bin/env python3
"""
JLAW/NITS SUBSYSTEM: Enhanced Financial Flow Tracer
═══════════════════════════════════════════════════════════════════════════════
Traces financial flows from $0. 00 gift transactions through subsequent
liquidation events, detecting potential insider trading violations.

This module integrates:
- ZeroDollarDetector for initial transaction identification
- SECEdgarClient for data acquisition
- Temporal analysis for pre/post material event correlation
- Compliance mapping for regulatory violation detection
- NITSAdapter for core system handoff

Author: JLAW Forensic Analysis System
Version: 2.0. 0
═══════════════════════════════════════════════════════════════════════════════
"""

import hashlib
import json
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import requests
import pandas as pd

# Configure logging
logging. basicConfig(level=logging.INFO)
logger = logging. getLogger("JLAW. FinancialFlowTracer")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class TracerConfig:
    """Central configuration for Financial Flow Tracer"""
    MIN_GIFT_VALUE_SHARES = 10000       # Minimum shares to trigger deep analysis
    HIGH_VALUE_THRESHOLD = 100000       # High-value gift threshold (shares)
    CRITICAL_VALUE_THRESHOLD = 500000   # Critical value threshold (shares)
    
    TIMEOUT = 30                        # API request timeout
    RETRY_LIMIT = 3                     # Max retries for failed API calls
    
    TRACE_LOOKAHEAD_DAYS = 180          # Days forward to trace financial events
    TRACE_LOOKBACK_DAYS = 30            # Days backward for pre-gift correlation
    MATERIAL_EVENT_WINDOW = 14          # Days around material events to flag
    
    SEC_USER_AGENT = "JLAW-Forensic-System forensic@jlaw.example.com"
    SEC_RATE_LIMIT = 8                  # Requests per second (SEC limit: 10)


class FlowEventType(Enum):
    """Types of financial flow events"""
    GIFT_INITIATION = "GIFT_INITIATION"
    SUBSEQUENT_SALE = "SUBSEQUENT_SALE"
    DERIVATIVE_EXERCISE = "DERIVATIVE_EXERCISE"
    MATERIAL_DISCLOSURE = "MATERIAL_DISCLOSURE"
    PRICE_MOVEMENT = "PRICE_MOVEMENT"
    RELATED_PARTY_ACTIVITY = "RELATED_PARTY_ACTIVITY"
    BENEFICIAL_OWNERSHIP_CHANGE = "BENEFICIAL_OWNERSHIP_CHANGE"


class ViolationSeverity(Enum):
    """Severity levels for detected violations"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GiftTransaction:
    """Represents an identified gift transaction for tracing"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    insider_cik: str = ""
    insider_name: str = ""
    issuer_cik: str = ""
    issuer_name: str = ""
    issuer_ticker: str = ""
    
    transaction_date: datetime = field(default_factory=datetime.now)
    filing_date: datetime = field(default_factory=datetime.now)
    accession_number: str = ""
    
    shares: float = 0. 0
    estimated_value: float = 0.0
    recipient: str = ""
    relationship_to_insider: str = ""
    
    footnotes: List[str] = field(default_factory=list)
    source_url: str = ""
    content_hash: str = ""
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash for evidence integrity"""
        data = f"{self.accession_number}|{self.transaction_date}|{self.insider_cik}|{self.shares}"
        self.content_hash = hashlib.sha256(data.encode()). hexdigest()
        return self.content_hash
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self. transaction_id,
            "insider": {
                "cik": self.insider_cik,
                "name": self.insider_name
            },
            "issuer": {
                "cik": self.issuer_cik,
                "name": self. issuer_name,
                "ticker": self.issuer_ticker
            },
            "transaction_date": self. transaction_date.isoformat() if self.transaction_date else None,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "accession_number": self.accession_number,
            "shares": self.shares,
            "estimated_value": self.estimated_value,
            "recipient": self.recipient,
            "relationship_to_insider": self.relationship_to_insider,
            "footnotes": self. footnotes,
            "evidence": {
                "source_url": self. source_url,
                "content_hash": self.content_hash
            }
        }


@dataclass
class FlowEvent:
    """Represents an event in the financial flow chain"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: FlowEventType = FlowEventType. GIFT_INITIATION
    event_date: datetime = field(default_factory=datetime.now)
    
    description: str = ""
    related_cik: str = ""
    related_entity: str = ""
    
    monetary_value: float = 0.0
    share_volume: float = 0.0
    
    source_document: str = ""
    source_url: str = ""
    accession_number: str = ""
    
    forensic_flags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type. value,
            "event_date": self.event_date. isoformat() if self.event_date else None,
            "description": self. description,
            "related_entity": {
                "cik": self.related_cik,
                "name": self.related_entity
            },
            "financial": {
                "monetary_value": self. monetary_value,
                "share_volume": self.share_volume
            },
            "source": {
                "document": self.source_document,
                "url": self.source_url,
                "accession": self.accession_number
            },
            "forensic_flags": self.forensic_flags
        }


@dataclass
class FinancialFlowChain:
    """Complete traced financial flow from gift to subsequent events"""
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    
    # Origin
    origin_gift: Optional[GiftTransaction] = None
    
    # Flow events (chronologically ordered)
    events: List[FlowEvent] = field(default_factory=list)
    
    # Analysis results
    total_gain_realized: float = 0.0
    material_disclosure_gap: bool = False
    days_to_first_sale: Optional[int] = None
    
    # Violations detected
    potential_violations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Risk assessment
    risk_score: float = 0.0
    severity: ViolationSeverity = ViolationSeverity.LOW
    
    # Evidence chain
    chain_hash: str = ""
    
    def compute_chain_hash(self) -> str:
        """Compute hash for entire flow chain"""
        data = json.dumps({
            "chain_id": self.chain_id,
            "origin_hash": self.origin_gift.content_hash if self. origin_gift else "",
            "event_count": len(self. events),
            "total_gain": self.total_gain_realized
        }, sort_keys=True)
        self.chain_hash = hashlib.sha256(data.encode()). hexdigest()
        return self.chain_hash
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self. chain_id,
            "created_at": self.created_at,
            "origin_gift": self.origin_gift. to_dict() if self.origin_gift else None,
            "events": [e.to_dict() for e in self. events],
            "analysis": {
                "total_gain_realized": self.total_gain_realized,
                "material_disclosure_gap": self.material_disclosure_gap,
                "days_to_first_sale": self. days_to_first_sale
            },
            "violations": self.potential_violations,
            "risk": {
                "score": self.risk_score,
                "severity": self.severity.name
            },
            "evidence_chain": {
                "chain_hash": self. chain_hash
            }
        }


@dataclass
class ComplianceViolation:
    """Structured compliance violation record"""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    violation_type: str = ""
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    
    statute: str = ""
    cfr_citation: str = ""
    description: str = ""
    
    evidence_references: List[str] = field(default_factory=list)
    recommended_action: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_id": self. violation_id,
            "type": self.violation_type,
            "severity": self.severity.name,
            "legal": {
                "statute": self.statute,
                "cfr_citation": self. cfr_citation
            },
            "description": self.description,
            "evidence_references": self.evidence_references,
            "recommended_action": self.recommended_action
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE FRAMEWORK
# ═══════════════════════════════════════════════════════════════════════════════

class ComplianceFramework:
    """Regulatory compliance mapping for insider trading violations"""
    
    STATUTES = {
        "15_USC_78j_b": {
            "statute": "15 U.S.C.  § 78j(b)",
            "title": "Securities Exchange Act - Manipulative and Deceptive Devices",
            "cfr": "17 CFR § 240.10b-5",
            "description": "Prohibits fraud, manipulation, and deception in securities transactions"
        },
        "15_USC_78p_a": {
            "statute": "15 U.S.C. § 78p(a)",
            "title": "Section 16(a) - Beneficial Ownership Reports",
            "cfr": "17 CFR § 240.16a-3",
            "description": "Requires insiders to report transactions within 2 business days"
        },
        "15_USC_78p_b": {
            "statute": "15 U. S.C. § 78p(b)",
            "title": "Section 16(b) - Short-Swing Profit Recovery",
            "cfr": "17 CFR § 240.16b",
            "description": "Allows recovery of profits from paired buy/sell within 6 months"
        },
        "17_CFR_240_10b5_1": {
            "statute": "17 CFR § 240.10b5-1",
            "title": "Trading on Material Nonpublic Information",
            "cfr": "17 CFR § 240. 10b5-1",
            "description": "Affirmative defense requirements for insider trading plans"
        },
        "26_USC_2501": {
            "statute": "26 U.S.C.  § 2501",
            "title": "Imposition of Gift Tax",
            "cfr": "26 CFR § 25",
            "description": "Federal gift tax implications for securities transfers"
        }
    }
    
    TIER_PENALTIES = {
        ViolationSeverity.LOW: {
            "civil_penalty_range": (0, 50000),
            "disgorgement": True,
            "bar_from_industry": False,
            "criminal_referral": False
        },
        ViolationSeverity. MEDIUM: {
            "civil_penalty_range": (50000, 250000),
            "disgorgement": True,
            "bar_from_industry": False,
            "criminal_referral": False
        },
        ViolationSeverity.HIGH: {
            "civil_penalty_range": (250000, 1000000),
            "disgorgement": True,
            "bar_from_industry": True,
            "criminal_referral": False
        },
        ViolationSeverity.CRITICAL: {
            "civil_penalty_range": (1000000, 5000000),
            "disgorgement": True,
            "bar_from_industry": True,
            "criminal_referral": True
        }
    }
    
    @classmethod
    def map_violation(
        cls,
        violation_type: str,
        evidence: List[str],
        severity: ViolationSeverity
    ) -> ComplianceViolation:
        """Map a detected issue to regulatory violations"""
        
        # Default to 10b-5
        statute_key = "15_USC_78j_b"
        
        # Map based on violation type
        if "LATE_FILING" in violation_type:
            statute_key = "15_USC_78p_a"
        elif "SHORT_SWING" in violation_type:
            statute_key = "15_USC_78p_b"
        elif "GIFT_TAX" in violation_type:
            statute_key = "26_USC_2501"
        elif "10B5_1_VIOLATION" in violation_type:
            statute_key = "17_CFR_240_10b5_1"
        
        statute_info = cls. STATUTES[statute_key]
        penalties = cls.TIER_PENALTIES[severity]
        
        recommended_action = "Standard monitoring"
        if severity == ViolationSeverity. CRITICAL:
            recommended_action = "IMMEDIATE: Escalate to enforcement division for criminal referral review"
        elif severity == ViolationSeverity.HIGH:
            recommended_action = "Priority review by compliance team; prepare enforcement referral"
        elif severity == ViolationSeverity. MEDIUM:
            recommended_action = "Schedule detailed investigation within 5 business days"
        
        return ComplianceViolation(
            violation_type=violation_type,
            severity=severity,
            statute=statute_info["statute"],
            cfr_citation=statute_info["cfr"],
            description=statute_info["description"],
            evidence_references=evidence,
            recommended_action=recommended_action
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SEC DATA RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════════

class SECDataRetriever:
    """Handles SEC EDGAR data retrieval with rate limiting"""
    
    BASE_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    
    def __init__(self, user_agent: str = TracerConfig.SEC_USER_AGENT):
        self.user_agent = user_agent
        self. session = requests.Session()
        self. session.headers.update({"User-Agent": user_agent})
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Enforce SEC rate limiting"""
        import time
        elapsed = time.time() - self._last_request_time
        min_interval = 1.0 / TracerConfig.SEC_RATE_LIMIT
        if elapsed < min_interval:
            time. sleep(min_interval - elapsed)
        self._last_request_time = time. time()
    
    def _fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch URL with retry logic"""
        import time
        
        for attempt in range(TracerConfig.RETRY_LIMIT):
            try:
                self._rate_limit()
                response = self.session. get(url, timeout=TracerConfig. TIMEOUT)
                
                if response.status_code == 200:
                    return response. text
                elif response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning(f"Rate limited, waiting {wait}s")
                    time. sleep(wait)
                elif response.status_code == 404:
                    return None
                else:
                    time.sleep(2 ** attempt)
                    
            except requests.RequestException as e:
                logger.warning(f"Request error: {e}")
                time.sleep(2 ** attempt)
        
        return None
    
    def get_insider_filings(
        self,
        insider_cik: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get all Form 4 filings for an insider in date range"""
        cik_padded = insider_cik.zfill(10)
        url = f"{self. BASE_URL}/submissions/CIK{cik_padded}. json"
        
        content = self._fetch_with_retry(url)
        if not content:
            return []
        
        try:
            data = json.loads(content)
            recent = data.get("filings", {}).get("recent", {})
            
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            dates = recent.get("filingDate", [])
            docs = recent.get("primaryDocument", [])
            
            filings = []
            for i, form in enumerate(forms):
                if form not in ["4", "4/A"]:
                    continue
                
                try:
                    filing_date = datetime.strptime(dates[i], "%Y-%m-%d")
                except (ValueError, IndexError):
                    continue
                
                if filing_date < start_date or filing_date > end_date:
                    continue
                
                cik_clean = cik_padded. lstrip("0")
                acc_clean = accessions[i].replace("-", "")
                
                filings.append({
                    "accession_number": accessions[i],
                    "filing_date": filing_date,
                    "form_type": form,
                    "primary_document": docs[i] if i < len(docs) else "",
                    "xml_url": f"{self. ARCHIVES_URL}/{cik_clean}/{acc_clean}/{docs[i] if i < len(docs) else ''}"
                })
            
            return filings
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse filings for CIK {insider_cik}")
            return []
    
    def get_8k_filings(
        self,
        issuer_cik: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get 8-K filings (material events) for an issuer"""
        cik_padded = issuer_cik.zfill(10)
        url = f"{self.BASE_URL}/submissions/CIK{cik_padded}.json"
        
        content = self._fetch_with_retry(url)
        if not content:
            return []
        
        try:
            data = json.loads(content)
            recent = data.get("filings", {}).get("recent", {})
            
            forms = recent. get("form", [])
            accessions = recent.get("accessionNumber", [])
            dates = recent.get("filingDate", [])
            
            filings = []
            for i, form in enumerate(forms):
                if form not in ["8-K", "8-K/A"]:
                    continue
                
                try:
                    filing_date = datetime.strptime(dates[i], "%Y-%m-%d")
                except (ValueError, IndexError):
                    continue
                
                if filing_date < start_date or filing_date > end_date:
                    continue
                
                filings.append({
                    "accession_number": accessions[i],
                    "filing_date": filing_date,
                    "form_type": form
                })
            
            return filings
            
        except json.JSONDecodeError:
            return []
    
    def fetch_filing_content(self, url: str) -> Optional[str]:
        """Fetch raw filing content"""
        return self._fetch_with_retry(url)


# ═══════════════════════════════════════════════════════════════════════════════
# CORE FINANCIAL FLOW TRACER
# ═══════════════════════════════════════════════════════════════════════════════

class FinancialFlowTracer:
    """
    Core engine for tracing financial flows from gift transactions. 
    
    Identifies gift transactions and traces subsequent activity to detect
    potential insider trading violations through indirect means.
    """
    
    def __init__(
        self,
        sec_retriever: Optional[SECDataRetriever] = None,
        output_dir: Optional[Path] = None
    ):
        self.sec_retriever = sec_retriever or SECDataRetriever()
        self.output_dir = Path(output_dir) if output_dir else Path("./flow_trace_reports")
        self. output_dir.mkdir(parents=True, exist_ok=True)
        
        # Import zero dollar detector if available
        self._detector = None
    
    def _get_detector(self):
        """Lazy load ZeroDollarDetector"""
        if self._detector is None:
            try:
                from . zero_dollar_detector import ZeroDollarDetector
                self._detector = ZeroDollarDetector()
            except ImportError:
                logger.warning("ZeroDollarDetector not available, using fallback")
                self._detector = self._FallbackDetector()
        return self._detector
    
    class _FallbackDetector:
        """Fallback detector when main module not available"""
        def parse_form4_xml(self, content: str, url: str = "") -> List[Dict]:
            import xml.etree.ElementTree as ET
            transactions = []
            
            try:
                root = ET.fromstring(content)
                
                # Extract basic gift transactions
                for txn in root.findall(".//nonDerivativeTransaction"):
                    code = txn.findtext(". //transactionCoding/transactionCode", "")
                    if code == "G":
                        shares = float(txn.findtext(".//transactionAmounts/transactionShares/value", "0") or 0)
                        transactions.append({
                            "transaction_code": "G",
                            "shares": shares,
                            "source_url": url
                        })
            except ET.ParseError:
                pass
            
            return transactions
    
    def identify_gift_transactions(
        self,
        form4_data: pd.DataFrame
    ) -> List[GiftTransaction]:
        """
        Identify gift transactions from Form 4 data. 
        
        Args:
            form4_data: DataFrame with Form 4 transaction data
            
        Returns:
            List of identified gift transactions
        """
        gifts = []
        
        for idx, row in form4_data.iterrows():
            # Check for gift indicators
            txn_value = row.get("transaction_value", 0)
            txn_type = str(row.get("transaction_type", "")).lower()
            txn_code = row.get("transaction_code", "")
            shares = row.get("shares", 0)
            
            is_gift = (
                txn_value == 0 and 
                (txn_code == "G" or "gift" in txn_type)
            )
            
            if not is_gift:
                continue
            
            # Skip small transactions
            if shares < TracerConfig.MIN_GIFT_VALUE_SHARES:
                continue
            
            gift = GiftTransaction(
                insider_cik=str(row. get("insider_cik", "")),
                insider_name=row.get("insider_name", ""),
                issuer_cik=str(row.get("issuer_cik", "")),
                issuer_name=row. get("issuer_name", ""),
                issuer_ticker=row.get("ticker", ""),
                transaction_date=row.get("transaction_date", datetime.now()),
                filing_date=row.get("filing_date", datetime.now()),
                accession_number=row. get("accession_number", ""),
                shares=shares,
                recipient=row.get("recipient", "Unknown"),
                footnotes=row.get("footnotes", []),
                source_url=row.get("source_url", "")
            )
            gift.compute_hash()
            gifts.append(gift)
        
        logger.info(f"Identified {len(gifts)} gift transactions for tracing")
        return gifts
    
    def lookup_post_gift_activity(
        self,
        gift: GiftTransaction,
        lookahead_days: int = TracerConfig.TRACE_LOOKAHEAD_DAYS
    ) -> List[FlowEvent]:
        """
        Look up subsequent insider activity after a gift transaction.
        
        Args:
            gift: The origin gift transaction
            lookahead_days: Days to look ahead
            
        Returns:
            List of subsequent flow events
        """
        events = []
        
        start_date = gift. transaction_date
        end_date = start_date + timedelta(days=lookahead_days)
        
        # Get subsequent Form 4 filings
        filings = self.sec_retriever.get_insider_filings(
            gift.insider_cik,
            start_date,
            end_date
        )
        
        for filing in filings:
            # Skip the original gift filing
            if filing["accession_number"] == gift.accession_number:
                continue
            
            # Fetch and analyze filing content
            content = self.sec_retriever.fetch_filing_content(filing. get("xml_url", ""))
            if not content:
                continue
            
            # Detect sales or other dispositions
            detector = self._get_detector()
            transactions = detector.parse_form4_xml(content, filing.get("xml_url", ""))
            
            for txn in transactions:
                code = txn.get("transaction_code", "")
                
                # Look for sales (S), exercises (M), or other dispositions
                if code in ["S", "M", "J", "D"]:
                    event = FlowEvent(
                        event_type=FlowEventType. SUBSEQUENT_SALE if code == "S" else FlowEventType.DERIVATIVE_EXERCISE,
                        event_date=filing["filing_date"],
                        description=f"Post-gift {code}-code transaction",
                        related_cik=gift.insider_cik,
                        related_entity=gift.insider_name,
                        share_volume=txn.get("shares", 0),
                        monetary_value=txn.get("shares", 0) * txn.get("price_per_share", 0),
                        source_document=f"Form 4 - {filing['accession_number']}",
                        accession_number=filing["accession_number"],
                        source_url=filing. get("xml_url", "")
                    )
                    
                    # Flag if close to gift date
                    days_after = (filing["filing_date"] - gift. transaction_date).days
                    if days_after <= 30:
                        event.forensic_flags.append(f"SALE_WITHIN_30_DAYS (day {days_after})")
                    if days_after <= 7:
                        event.forensic_flags.append("SUSPICIOUS_TIMING")
                    
                    events.append(event)
        
        # Get material events (8-K filings)
        material_events = self.sec_retriever.get_8k_filings(
            gift.issuer_cik,
            start_date - timedelta(days=TracerConfig.TRACE_LOOKBACK_DAYS),
            end_date
        )
        
        for me in material_events:
            event = FlowEvent(
                event_type=FlowEventType.MATERIAL_DISCLOSURE,
                event_date=me["filing_date"],
                description=f"Material event disclosure ({me['form_type']})",
                related_cik=gift.issuer_cik,
                related_entity=gift.issuer_name,
                source_document=f"{me['form_type']} - {me['accession_number']}",
                accession_number=me["accession_number"]
            )
            
            # Check if material event is suspiciously timed
            days_from_gift = (me["filing_date"] - gift.transaction_date).days
            if -TracerConfig.MATERIAL_EVENT_WINDOW <= days_from_gift <= TracerConfig. MATERIAL_EVENT_WINDOW:
                event.forensic_flags.append(f"MATERIAL_EVENT_PROXIMITY (day {days_from_gift:+d})")
            
            events.append(event)
        
        # Sort by date
        events. sort(key=lambda e: e.event_date)
        
        return events
    
    def extract_financial_timeline(
        self,
        gift: GiftTransaction,
        events: List[FlowEvent]
    ) -> FinancialFlowChain:
        """
        Build complete financial timeline from gift through subsequent events.
        
        Args:
            gift: Origin gift transaction
            events: Subsequent flow events
            
        Returns:
            Complete FinancialFlowChain
        """
        chain = FinancialFlowChain(origin_gift=gift)
        
        # Add gift initiation event
        init_event = FlowEvent(
            event_type=FlowEventType.GIFT_INITIATION,
            event_date=gift.transaction_date,
            description=f"Gift of {gift.shares:,. 0f} shares",
            related_cik=gift.insider_cik,
            related_entity=gift.insider_name,
            share_volume=gift. shares,
            source_document=f"Form 4 - {gift.accession_number}",
            accession_number=gift.accession_number,
            source_url=gift.source_url
        )
        
        # Add flags for large gifts
        if gift. shares >= TracerConfig.CRITICAL_VALUE_THRESHOLD:
            init_event.forensic_flags.append("CRITICAL_VOLUME_GIFT")
        elif gift.shares >= TracerConfig.HIGH_VALUE_THRESHOLD:
            init_event.forensic_flags.append("HIGH_VOLUME_GIFT")
        
        if not gift.footnotes:
            init_event.forensic_flags.append("GIFT_WITHOUT_FOOTNOTE")
        
        chain.events.append(init_event)
        chain.events.extend(events)
        
        # Calculate metrics
        total_gain = sum(
            e.monetary_value for e in events 
            if e. event_type == FlowEventType. SUBSEQUENT_SALE
        )
        chain.total_gain_realized = total_gain
        
        # Find first sale
        sales = [e for e in events if e. event_type == FlowEventType. SUBSEQUENT_SALE]
        if sales:
            first_sale = min(sales, key=lambda e: e. event_date)
            chain.days_to_first_sale = (first_sale.event_date - gift.transaction_date).days
        
        # Check for material disclosure gap
        material_events = [e for e in events if e.event_type == FlowEventType.MATERIAL_DISCLOSURE]
        for me in material_events:
            days_from_gift = (me.event_date - gift.transaction_date).days
            if days_from_gift > 0 and any(
                s.event_date < me.event_date for s in sales
            ):
                chain. material_disclosure_gap = True
                break
        
        # Calculate risk score
        chain.risk_score = self._calculate_risk_score(chain)
        chain.severity = self._determine_severity(chain. risk_score)
        
        # Identify violations
        chain.potential_violations = self._identify_violations(chain)
        
        # Compute chain hash
        chain. compute_chain_hash()
        
        return chain
    
    def _calculate_risk_score(self, chain: FinancialFlowChain) -> float:
        """Calculate risk score (0-100) for a flow chain"""
        score = 0.0
        
        if not chain.origin_gift:
            return 0.0
        
        # Volume scoring (0-25)
        shares = chain.origin_gift.shares
        if shares >= TracerConfig.CRITICAL_VALUE_THRESHOLD:
            score += 25
        elif shares >= TracerConfig.HIGH_VALUE_THRESHOLD:
            score += 20
        elif shares >= TracerConfig.MIN_GIFT_VALUE_SHARES:
            score += 10
        
        # Timing scoring (0-25)
        if chain.days_to_first_sale is not None:
            if chain.days_to_first_sale <= 7:
                score += 25
            elif chain.days_to_first_sale <= 30:
                score += 20
            elif chain.days_to_first_sale <= 90:
                score += 10
        
        # Material disclosure gap (0-25)
        if chain.material_disclosure_gap:
            score += 25
        
        # Gain realized (0-25)
        if chain.total_gain_realized > 1000000:
            score += 25
        elif chain.total_gain_realized > 500000:
            score += 20
        elif chain.total_gain_realized > 100000:
            score += 15
        elif chain. total_gain_realized > 10000:
            score += 10
        
        # Forensic flag bonus
        total_flags = sum(len(e.forensic_flags) for e in chain.events)
        score += min(total_flags * 2, 10)
        
        return min(score, 100. 0)
    
    def _determine_severity(self, risk_score: float) -> ViolationSeverity:
        """Determine severity level from risk score"""
        if risk_score >= 80:
            return ViolationSeverity.CRITICAL
        elif risk_score >= 60:
            return ViolationSeverity.HIGH
        elif risk_score >= 40:
            return ViolationSeverity. MEDIUM
        else:
            return ViolationSeverity. LOW
    
    def _identify_violations(self, chain: FinancialFlowChain) -> List[Dict[str, Any]]:
        """Identify potential regulatory violations"""
        violations = []
        
        if not chain.origin_gift:
            return violations
        
        # Gift followed by quick sale
        if chain.days_to_first_sale is not None and chain.days_to_first_sale <= 30:
            violation = ComplianceFramework.map_violation(
                "GIFT_THEN_SALE_PATTERN",
                [chain.origin_gift. accession_number],
                ViolationSeverity.HIGH if chain.days_to_first_sale <= 7 else ViolationSeverity.MEDIUM
            )
            violations.append(violation. to_dict())
        
        # Material disclosure gap
        if chain.material_disclosure_gap:
            violation = ComplianceFramework.map_violation(
                "MATERIAL_DISCLOSURE_GAP",
                [e.accession_number for e in chain. events if e.event_type == FlowEventType.MATERIAL_DISCLOSURE],
                ViolationSeverity.HIGH
            )
            violations.append(violation.to_dict())
        
        # Large gain realized
        if chain.total_gain_realized > 100000:
            severity = ViolationSeverity.CRITICAL if chain.total_gain_realized > 1000000 else ViolationSeverity.HIGH
            violation = ComplianceFramework.map_violation(
                "SUSPICIOUS_GAIN_PATTERN",
                [chain.chain_id],
                severity
            )
            violations.append(violation. to_dict())
        
        # Missing footnote on gift
        for event in chain.events:
            if "GIFT_WITHOUT_FOOTNOTE" in event.forensic_flags:
                violation = ComplianceFramework.map_violation(
                    "INCOMPLETE_DISCLOSURE",
                    [event.accession_number],
                    ViolationSeverity. MEDIUM
                )
                violations.append(violation.to_dict())
                break
        
        return violations
    
    def trace_financial_flow(
        self,
        gift: GiftTransaction
    ) -> FinancialFlowChain:
        """
        Complete flow trace for a single gift transaction.
        
        Args:
            gift: Gift transaction to trace
            
        Returns:
            Complete financial flow chain
        """
        logger.info(f"Tracing flow for gift: {gift.shares:,.0f} shares by {gift.insider_name}")
        
        # Get post-gift activity
        events = self.lookup_post_gift_activity(gift)
        
        # Build timeline
        chain = self.extract_financial_timeline(gift, events)
        
        logger.info(f"  Chain complete: {len(chain.events)} events, risk score: {chain. risk_score:.1f}")
        
        return chain
    
    def run_batch_analysis(
        self,
        form4_data: pd.DataFrame,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete financial flow analysis on batch of Form 4 data.
        
        Args:
            form4_data: DataFrame with Form 4 transaction data
            save_results: Whether to save results to disk
            
        Returns:
            Complete analysis results
        """
        logger.info("=" * 60)
        logger. info("JLAW FINANCIAL FLOW TRACER - BATCH ANALYSIS")
        logger.info("=" * 60)
        
        # Identify gifts
        gifts = self.identify_gift_transactions(form4_data)
        
        if not gifts:
            logger.info("No significant gift transactions identified")
            return {
                "status": "complete",
                "gifts_analyzed": 0,
                "flow_chains": [],
                "summary": {"message": "No gift transactions found"}
            }
        
        # Trace each gift
        chains = []
        for gift in gifts:
            try:
                chain = self.trace_financial_flow(gift)
                chains.append(chain)
            except Exception as e:
                logger.error(f"Error tracing gift {gift. transaction_id}: {e}")
        
        # Build results
        results = {
            "status": "complete",
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "gifts_analyzed": len(gifts),
            "flow_chains": [c.to_dict() for c in chains],
            "summary": {
                "total_chains": len(chains),
                "high_risk_chains": sum(1 for c in chains if c.severity in [ViolationSeverity.HIGH, ViolationSeverity.CRITICAL]),
                "total_gain_traced": sum(c. total_gain_realized for c in chains),
                "total_violations": sum(len(c.potential_violations) for c in chains),
                "critical_count": sum(1 for c in chains if c.severity == ViolationSeverity.CRITICAL),
                "high_count": sum(1 for c in chains if c.severity == ViolationSeverity.HIGH)
            },
            "evidence_manifest": {
                "chain_hashes": [c. chain_hash for c in chains],
                "processed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("ANALYSIS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  Gift Transactions Analyzed: {len(gifts)}")
        logger.info(f"  Flow Chains Generated: {len(chains)}")
        logger.info(f"  High-Risk Chains: {results['summary']['high_risk_chains']}")
        logger.info(f"  Total Gain Traced: ${results['summary']['total_gain_traced']:,.2f}")
        logger.info(f"  Violations Identified: {results['summary']['total_violations']}")
        
        # Save results
        if save_results:
            output_file = self.output_dir / f"flow_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"\nResults saved to: {output_file}")
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# NITS INTEGRATION ADAPTER
# ═══════════════════════════════════════════════════════════════════════════════

class FlowTracerNITSAdapter:
    """Adapter for integrating Financial Flow Tracer with NITS core"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self. output_dir = Path(output_dir) if output_dir else Path("./nits_flow_output")
        self. output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert_chain_to_nits_context(
        self,
        chain: FinancialFlowChain
    ) -> Dict[str, Any]:
        """Convert flow chain to NITS investigation context format"""
        
        if not chain.origin_gift:
            return {}
        
        return {
            "docId": f"FLOW_TRACE_{chain.chain_id}",
            "docPath": f"sec://flow-trace/{chain.origin_gift.issuer_cik}/{chain.chain_id}",
            "entity": chain.origin_gift.insider_name,
            "source": "JLAW Financial Flow Tracer",
            "violations": chain.potential_violations,
            "signatureHits": [
                {
                    "signature_id": f"FLOW_{e.event_type.value}",
                    "signature_name": e.event_type.value,
                    "description": e.description,
                    "flags": e.forensic_flags
                }
                for e in chain.events if e.forensic_flags
            ],
            "summary": (
                f"Financial flow trace for {chain. origin_gift.shares:,.0f} share gift by "
                f"{chain.origin_gift. insider_name}. "
                f"Risk: {chain.severity.name}, Score: {chain.risk_score:.1f}/100.  "
                f"Total gain traced: ${chain.total_gain_realized:,.2f}."
            ),
            "riskScore": chain. risk_score
        }
    
    def generate_prosecution_contribution(
        self,
        chains: List[FinancialFlowChain]
    ) -> Dict[str, Any]:
        """Generate prosecution package contribution"""
        
        total_gain = sum(c.total_gain_realized for c in chains)
        all_violations = []
        for chain in chains:
            all_violations. extend(chain.potential_violations)
        
        return {
            "module": "FINANCIAL_FLOW_TRACER",
            "contribution_type": "GIFT_TRANSACTION_FLOW_EVIDENCE",
            "evidence_inventory": [
                {
                    "chain_id": c.chain_id,
                    "origin_gift": c.origin_gift.accession_number if c.origin_gift else "",
                    "events_count": len(c.events),
                    "gain_realized": c.total_gain_realized,
                    "risk_score": c. risk_score,
                    "hash": c.chain_hash
                }
                for c in chains
            ],
            "violation_summary": {
                "total": len(all_violations),
                "critical": sum(1 for c in chains if c. severity == ViolationSeverity. CRITICAL),
                "high": sum(1 for c in chains if c.severity == ViolationSeverity.HIGH)
            },
            "penalty_estimates": {
                "disgorgement_potential": total_gain,
                "civil_penalty_range": (
                    sum(ComplianceFramework. TIER_PENALTIES[c.severity]["civil_penalty_range"][0] for c in chains),
                    sum(ComplianceFramework.TIER_PENALTIES[c.severity]["civil_penalty_range"][1] for c in chains)
                )
            },
            "statute_citations": list(set(
                v.get("legal", {}).get("statute", "") 
                for v in all_violations
            )),
            "chain_of_custody": {
                "chain_hashes": [c. chain_hash for c in chains],
                "collected_at": datetime. utcnow(). isoformat() + "Z",
                "witness": "JLAW Financial Flow Tracer v2.0. 0"
            }
        }
    
    def export_for_nits(
        self,
        chains: List[FinancialFlowChain],
        filename_prefix: str = "flow_trace"
    ) -> Dict[str, str]:
        """Export all NITS-compatible files"""
        
        timestamp = datetime.now(). strftime("%Y%m%d_%H%M%S")
        outputs = {}
        
        # Investigation contexts
        contexts = [self.convert_chain_to_nits_context(c) for c in chains if c.origin_gift]
        contexts_path = self.output_dir / f"{filename_prefix}_contexts_{timestamp}.json"
        with open(contexts_path, "w") as f:
            json.dump(contexts, f, indent=2, default=str)
        outputs["investigation_contexts"] = str(contexts_path)
        
        # Prosecution contribution
        prosecution = self.generate_prosecution_contribution(chains)
        prosecution_path = self. output_dir / f"{filename_prefix}_prosecution_{timestamp}.json"
        with open(prosecution_path, "w") as f:
            json. dump(prosecution, f, indent=2, default=str)
        outputs["prosecution_contribution"] = str(prosecution_path)
        
        logger.info(f"Exported NITS files to {self.output_dir}")
        
        return outputs


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def run_financial_flow_tracer(
    form4_data: pd. DataFrame,
    output_dir: Optional[Path] = None,
    export_nits: bool = True
) -> Dict[str, Any]:
    """
    Main entry point for Financial Flow Tracer. 
    
    Args:
        form4_data: DataFrame containing Form 4 transaction data
        output_dir: Output directory for reports
        export_nits: Whether to export NITS integration files
        
    Returns:
        Complete analysis results
    """
    tracer = FinancialFlowTracer(output_dir=output_dir)
    results = tracer.run_batch_analysis(form4_data)
    
    if export_nits and results. get("flow_chains"):
        # Reconstruct chains for NITS export
        chains = []
        for chain_data in results["flow_chains"]:
            chain = FinancialFlowChain()
            chain.chain_id = chain_data. get("chain_id", "")
            chain.risk_score = chain_data.get("risk", {}).get("score", 0)
            chain.severity = ViolationSeverity[chain_data.get("risk", {}). get("severity", "LOW")]
            chain. total_gain_realized = chain_data.get("analysis", {}).get("total_gain_realized", 0)
            chain.potential_violations = chain_data.get("violations", [])
            chain.chain_hash = chain_data.get("evidence_chain", {}).get("chain_hash", "")
            
            if chain_data.get("origin_gift"):
                og = chain_data["origin_gift"]
                chain.origin_gift = GiftTransaction(
                    insider_name=og. get("insider", {}).get("name", ""),
                    shares=og.get("shares", 0),
                    accession_number=og.get("accession_number", "")
                )
            
            chains.append(chain)
        
        adapter = FlowTracerNITSAdapter(
            output_dir=Path(output_dir or "./nits_flow_output")
        )
        nits_outputs = adapter.export_for_nits(chains)
        results["nits_exports"] = nits_outputs
    
    return results


# Example usage
if __name__ == "__main__":
    # Example with sample data
    sample_data = pd.DataFrame([
        {
            "insider_cik": "0001234567",
            "insider_name": "John Doe",
            "issuer_cik": "0000320187",
            "issuer_name": "Test Corp",
            "ticker": "TEST",
            "transaction_date": datetime(2024, 1, 15),
            "filing_date": datetime(2024, 1, 17),
            "accession_number": "0001234567-24-000001",
            "transaction_code": "G",
            "transaction_type": "Gift",
            "transaction_value": 0,
            "shares": 150000,
            "footnotes": []
        }
    ])
    
    results = run_financial_flow_tracer(sample_data)
    print(json.dumps(results, indent=2, default=str))