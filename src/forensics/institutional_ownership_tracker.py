#!/usr/bin/env python3
"""
================================================================================
INSTITUTIONAL OWNERSHIP TRACKER - 13F/13D/13G ANALYSIS
================================================================================

Version: 4.0.0-PRODUCTION
Authority: JARVIS NEXUS

Production-grade institutional ownership tracking system for:
- Form 13F-HR quarterly holdings analysis
- Schedule 13D/13G beneficial ownership monitoring
- Cross-institutional accumulation detection
- 13G-to-13D conversion signals
- Coordinated trading pattern identification

REGULATORY FRAMEWORK:
====================
- 17 CFR § 240.13f-1: Form 13F institutional holdings (quarterly, $100M+ AUM)
- 17 CFR § 240.13d-1: Schedule 13D/13G beneficial ownership (5%+ threshold)
- December 2024 XML mandate for 13D/13G filings

DETECTION CAPABILITIES:
======================
1. Rapid accumulation across multiple institutions
2. Concentrated selling by sector specialists
3. New position initiations by major funds
4. 13G-to-13D conversions (passive to activist)
5. Ownership threshold crossings (5%, 10%)
"""

import asyncio
import aiohttp
import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
import re

logger = logging.getLogger(__name__)

SEC_USER_AGENT = "JLAW-Forensics-NEXUS/4.0 (Institutional Analysis; legal@jlaw-nexus.org)"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class OwnershipType(Enum):
    """Types of beneficial ownership filings."""
    SCHEDULE_13D = "13D"      # Active/activist investor
    SCHEDULE_13D_A = "13D/A"  # 13D amendment
    SCHEDULE_13G = "13G"      # Passive investor
    SCHEDULE_13G_A = "13G/A"  # 13G amendment
    FORM_13F = "13F-HR"       # Quarterly institutional holdings


class InvestmentDiscretion(Enum):
    """Investment discretion types for 13F holdings."""
    SOLE = "SOLE"       # Manager has sole discretion
    SHARED = "SHARED"   # Shared discretion with others
    DEFINED = "DFND"    # Defined/none
    NONE = "NONE"


@dataclass
class Form13FHolding:
    """Individual holding from Form 13F-HR."""
    cusip: str
    issuer_name: str
    class_title: str
    shares: int
    market_value: float  # In thousands
    investment_discretion: str
    voting_authority_sole: int
    voting_authority_shared: int
    voting_authority_none: int
    put_call: Optional[str]  # PUT, CALL, or None
    
    # Filing metadata
    manager_cik: str
    manager_name: str
    report_date: str
    filing_date: str
    accession_number: str


@dataclass
class ScheduleFilingRecord:
    """Schedule 13D/13G filing record."""
    filer_name: str
    filer_cik: str
    filing_type: str  # 13D, 13D/A, SC 13G, SC 13G/A
    issuer_name: str
    issuer_cik: str
    issuer_cusip: str
    
    # Ownership details
    shares_beneficially_owned: int
    percent_of_class: float
    sole_voting_power: int
    shared_voting_power: int
    sole_dispositive_power: int
    shared_dispositive_power: int
    
    # Filing metadata
    filing_date: str
    event_date: Optional[str]
    accession_number: str
    document_url: str
    
    # Change tracking
    prior_shares: Optional[int] = None
    shares_change: Optional[int] = None
    shares_change_pct: Optional[float] = None
    
    # Flags
    is_initial_filing: bool = False
    is_amendment: bool = False
    crossed_5_percent: bool = False
    crossed_10_percent: bool = False


@dataclass
class InstitutionalAccumulationSignal:
    """Signal indicating coordinated institutional accumulation."""
    cusip: str
    issuer_name: str
    signal_type: str  # ACCUMULATION, DISTRIBUTION, CONCENTRATED_SELLING
    institutions_involved: int
    total_shares_change: int
    average_change_pct: float
    time_window_days: int
    detection_date: str
    confidence: float
    participating_managers: List[str]
    interpretation: str


@dataclass
class ThirteenGToThirteenDConversion:
    """Detection of 13G to 13D conversion (passive to activist)."""
    filer_name: str
    filer_cik: str
    issuer_name: str
    issuer_cik: str
    original_13g_date: str
    conversion_date: str
    shares_at_conversion: int
    percent_at_conversion: float
    days_as_passive: int
    significance: str


# =============================================================================
# FORM 13F PARSER
# =============================================================================

class Form13FParser:
    """
    Parser for Form 13F-HR institutional holdings.
    
    Form 13F is required from institutional investment managers with
    $100M+ in qualifying assets, due 45 days after quarter-end.
    """
    
    # 13F XML namespaces
    NAMESPACES = {
        'ns': 'http://www.sec.gov/edgar/thirteenffiler',
        'ns1': 'http://www.sec.gov/edgar/document/thirteenf/informationtable'
    }
    
    def parse_information_table(
        self,
        xml_content: str,
        manager_cik: str,
        manager_name: str,
        report_date: str,
        filing_date: str,
        accession_number: str
    ) -> List[Form13FHolding]:
        """
        Parse 13F information table XML.
        
        Args:
            xml_content: Raw XML content of information table
            manager_cik: Manager's CIK
            manager_name: Manager's name
            report_date: Report period date
            filing_date: Filing date
            accession_number: SEC accession number
            
        Returns:
            List of Form13FHolding records
        """
        holdings = []
        
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.warning(f"13F XML parse error: {e}")
            return holdings
        
        # Find all infoTable entries
        for entry in root.iter():
            if 'infoTable' in entry.tag:
                holding = self._parse_info_table_entry(
                    entry, manager_cik, manager_name,
                    report_date, filing_date, accession_number
                )
                if holding:
                    holdings.append(holding)
        
        return holdings
    
    def _parse_info_table_entry(
        self,
        entry,
        manager_cik: str,
        manager_name: str,
        report_date: str,
        filing_date: str,
        accession_number: str
    ) -> Optional[Form13FHolding]:
        """Parse individual infoTable entry."""
        try:
            # Extract fields
            cusip = self._get_text(entry, './/cusip')
            if not cusip:
                return None
            
            issuer_name = self._get_text(entry, './/nameOfIssuer') or ""
            class_title = self._get_text(entry, './/titleOfClass') or ""
            
            # Shares and value
            shares_str = self._get_text(entry, './/shrsOrPrnAmt/sshPrnamt')
            shares = int(float(shares_str)) if shares_str else 0
            
            value_str = self._get_text(entry, './/value')
            value = float(value_str) if value_str else 0.0
            
            # Investment discretion
            discretion = self._get_text(entry, './/investmentDiscretion') or "SOLE"
            
            # Voting authority
            sole_vote_str = self._get_text(entry, './/votingAuthority/Sole')
            shared_vote_str = self._get_text(entry, './/votingAuthority/Shared')
            none_vote_str = self._get_text(entry, './/votingAuthority/None')
            
            sole_vote = int(float(sole_vote_str)) if sole_vote_str else 0
            shared_vote = int(float(shared_vote_str)) if shared_vote_str else 0
            none_vote = int(float(none_vote_str)) if none_vote_str else 0
            
            # Put/Call
            put_call = self._get_text(entry, './/putCall')
            
            return Form13FHolding(
                cusip=cusip,
                issuer_name=issuer_name,
                class_title=class_title,
                shares=shares,
                market_value=value,
                investment_discretion=discretion,
                voting_authority_sole=sole_vote,
                voting_authority_shared=shared_vote,
                voting_authority_none=none_vote,
                put_call=put_call,
                manager_cik=manager_cik,
                manager_name=manager_name,
                report_date=report_date,
                filing_date=filing_date,
                accession_number=accession_number
            )
        except Exception as e:
            logger.debug(f"13F entry parse error: {e}")
            return None
    
    def _get_text(self, elem, path: str) -> str:
        """Get text from element by path."""
        for tag in elem.iter():
            if path.split('/')[-1] in tag.tag or path.split('//')[-1] in tag.tag:
                if tag.text:
                    return tag.text.strip()
        return ""


# =============================================================================
# SCHEDULE 13D/13G PARSER
# =============================================================================

class Schedule13Parser:
    """
    Parser for Schedule 13D and 13G filings.
    
    Key thresholds:
    - 5%: Initial filing required
    - 10%: Enhanced reporting requirements
    
    December 2024 changes:
    - Mandatory XML formatting
    - 5 business day deadline (reduced from 10 calendar days)
    - 2 business day amendment deadline for material changes
    """
    
    def parse_schedule_13(
        self,
        xml_content: str,
        filing_type: str,
        filing_date: str,
        accession_number: str,
        document_url: str
    ) -> Optional[ScheduleFilingRecord]:
        """
        Parse Schedule 13D or 13G filing.
        
        Args:
            xml_content: Raw filing content (XML or text)
            filing_type: Filing type (SC 13D, SC 13G, etc.)
            filing_date: Filing date
            accession_number: SEC accession number
            document_url: Document URL
            
        Returns:
            ScheduleFilingRecord or None
        """
        # Try XML parsing first (December 2024+ filings)
        record = self._parse_xml_schedule(
            xml_content, filing_type, filing_date,
            accession_number, document_url
        )
        
        if not record:
            # Fallback to regex parsing for older filings
            record = self._parse_text_schedule(
                xml_content, filing_type, filing_date,
                accession_number, document_url
            )
        
        return record
    
    def _parse_xml_schedule(
        self,
        xml_content: str,
        filing_type: str,
        filing_date: str,
        accession_number: str,
        document_url: str
    ) -> Optional[ScheduleFilingRecord]:
        """Parse XML-formatted Schedule 13D/13G."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            return None
        
        try:
            # Extract filer information
            filer_name = self._find_text(root, ['reportingPersonName', 'nameOfReportingPerson'])
            filer_cik = self._find_text(root, ['reportingPersonCik', 'cik'])
            
            # Issuer information
            issuer_name = self._find_text(root, ['issuerName', 'nameOfIssuer', 'subjectCompany'])
            issuer_cik = self._find_text(root, ['issuerCik', 'subjectCompanyCik'])
            issuer_cusip = self._find_text(root, ['cusipNumber', 'cusip'])
            
            # Ownership details
            shares = self._find_number(root, ['amountBeneficiallyOwned', 'sharesOwned', 'aggregateAmount'])
            percent = self._find_number(root, ['percentOfClass', 'percentOwned']) or 0.0
            
            # Voting/dispositive power
            sole_vote = self._find_number(root, ['soleVotingPower']) or 0
            shared_vote = self._find_number(root, ['sharedVotingPower']) or 0
            sole_disp = self._find_number(root, ['soleDispositivePower']) or 0
            shared_disp = self._find_number(root, ['sharedDispositivePower']) or 0
            
            if not filer_name or not shares:
                return None
            
            return ScheduleFilingRecord(
                filer_name=filer_name,
                filer_cik=filer_cik or "",
                filing_type=filing_type,
                issuer_name=issuer_name or "",
                issuer_cik=issuer_cik or "",
                issuer_cusip=issuer_cusip or "",
                shares_beneficially_owned=int(shares),
                percent_of_class=percent,
                sole_voting_power=int(sole_vote),
                shared_voting_power=int(shared_vote),
                sole_dispositive_power=int(sole_disp),
                shared_dispositive_power=int(shared_disp),
                filing_date=filing_date,
                event_date=None,
                accession_number=accession_number,
                document_url=document_url,
                is_initial_filing="/A" not in filing_type,
                is_amendment="/A" in filing_type,
                crossed_5_percent=percent >= 5.0 and percent < 10.0,
                crossed_10_percent=percent >= 10.0
            )
        except Exception as e:
            logger.debug(f"XML schedule parse error: {e}")
            return None
    
    def _parse_text_schedule(
        self,
        content: str,
        filing_type: str,
        filing_date: str,
        accession_number: str,
        document_url: str
    ) -> Optional[ScheduleFilingRecord]:
        """Parse text-formatted Schedule 13D/13G using regex."""
        # Extract filer name
        filer_match = re.search(r'NAMES? OF REPORTING PERSONS?[:\s]*\n*([^\n]+)', content, re.I)
        filer_name = filer_match.group(1).strip() if filer_match else ""
        
        # Extract shares
        shares_match = re.search(r'AGGREGATE AMOUNT[^\d]*(\d[\d,]*)', content, re.I)
        shares = int(shares_match.group(1).replace(',', '')) if shares_match else 0
        
        # Extract percent
        percent_match = re.search(r'PERCENT OF CLASS[^\d]*(\d+\.?\d*)', content, re.I)
        percent = float(percent_match.group(1)) if percent_match else 0.0
        
        # Extract issuer
        issuer_match = re.search(r'NAMES? OF ISSUERS?[:\s]*\n*([^\n]+)', content, re.I)
        issuer_name = issuer_match.group(1).strip() if issuer_match else ""
        
        # CUSIP
        cusip_match = re.search(r'CUSIP[^\w]*(\w{9})', content, re.I)
        cusip = cusip_match.group(1) if cusip_match else ""
        
        if not filer_name:
            return None
        
        return ScheduleFilingRecord(
            filer_name=filer_name,
            filer_cik="",
            filing_type=filing_type,
            issuer_name=issuer_name,
            issuer_cik="",
            issuer_cusip=cusip,
            shares_beneficially_owned=shares,
            percent_of_class=percent,
            sole_voting_power=0,
            shared_voting_power=0,
            sole_dispositive_power=0,
            shared_dispositive_power=0,
            filing_date=filing_date,
            event_date=None,
            accession_number=accession_number,
            document_url=document_url,
            is_initial_filing="/A" not in filing_type,
            is_amendment="/A" in filing_type,
            crossed_5_percent=percent >= 5.0 and percent < 10.0,
            crossed_10_percent=percent >= 10.0
        )
    
    def _find_text(self, root, tags: List[str]) -> str:
        """Find text by multiple possible tag names."""
        for tag in tags:
            for elem in root.iter():
                if tag.lower() in elem.tag.lower():
                    if elem.text:
                        return elem.text.strip()
        return ""
    
    def _find_number(self, root, tags: List[str]) -> Optional[float]:
        """Find numeric value by multiple possible tag names."""
        text = self._find_text(root, tags)
        if text:
            # Clean and parse number
            cleaned = re.sub(r'[^\d.]', '', text)
            try:
                return float(cleaned)
            except ValueError:
                pass
        return None


# =============================================================================
# INSTITUTIONAL OWNERSHIP TRACKER
# =============================================================================

class InstitutionalOwnershipTracker:
    """
    Production-grade institutional ownership tracking system.
    
    Tracks 13F holdings, 13D/13G filings, and detects:
    - Accumulation patterns
    - 13G-to-13D conversions
    - Threshold crossings
    - Coordinated activity
    """
    
    SEC_BASE_URL = "https://data.sec.gov"
    SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("forensic_reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Parsers
        self.form_13f_parser = Form13FParser()
        self.schedule_parser = Schedule13Parser()
        
        # Storage
        self.holdings: Dict[str, List[Form13FHolding]] = defaultdict(list)  # By CUSIP
        self.schedules: Dict[str, List[ScheduleFilingRecord]] = defaultdict(list)  # By issuer CIK
        self.accumulation_signals: List[InstitutionalAccumulationSignal] = []
        self.conversions: List[ThirteenGToThirteenDConversion] = []
        
        # Session
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request = 0
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": SEC_USER_AGENT}
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Apply SEC rate limiting."""
        import time
        elapsed = time.time() - self.last_request
        if elapsed < 0.125:  # 8 req/sec
            await asyncio.sleep(0.125 - elapsed)
        self.last_request = time.time()
    
    async def _fetch(self, url: str) -> Optional[str]:
        """Fetch URL with rate limiting."""
        await self._rate_limit()
        try:
            async with self.session.get(url, timeout=30) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception as e:
            logger.debug(f"Fetch failed: {url} - {e}")
        return None
    
    async def _fetch_json(self, url: str) -> Optional[Dict]:
        """Fetch JSON from URL."""
        content = await self._fetch(url)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
        return None
    
    async def track_security(
        self,
        cusip: str,
        issuer_cik: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Track institutional ownership for a specific security.
        
        Args:
            cusip: Security CUSIP
            issuer_cik: Issuer's CIK
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Tracking results with holdings and signals
        """
        logger.info(f"Tracking institutional ownership for CUSIP {cusip}")
        
        # Collect 13D/13G filings for the issuer
        schedule_filings = await self._collect_schedule_filings(issuer_cik, start_date, end_date)
        
        # Detect 13G to 13D conversions
        self._detect_conversions(schedule_filings)
        
        # Detect accumulation patterns
        accumulation = self._detect_accumulation_patterns(cusip, schedule_filings)
        
        results = {
            "cusip": cusip,
            "issuer_cik": issuer_cik,
            "analysis_period": {"start": start_date, "end": end_date},
            "schedule_filings": [asdict(s) for s in schedule_filings],
            "total_schedule_filings": len(schedule_filings),
            "initial_filings": sum(1 for s in schedule_filings if s.is_initial_filing),
            "threshold_crossings": {
                "5_percent": sum(1 for s in schedule_filings if s.crossed_5_percent),
                "10_percent": sum(1 for s in schedule_filings if s.crossed_10_percent)
            },
            "conversions": [asdict(c) for c in self.conversions],
            "accumulation_signals": [asdict(a) for a in accumulation]
        }
        
        return results
    
    async def _collect_schedule_filings(
        self,
        issuer_cik: str,
        start_date: str,
        end_date: str
    ) -> List[ScheduleFilingRecord]:
        """Collect Schedule 13D/13G filings for an issuer."""
        filings = []
        cik_padded = issuer_cik.zfill(10)
        
        url = f"{self.SEC_BASE_URL}/submissions/CIK{cik_padded}.json"
        data = await self._fetch_json(url)
        
        if not data:
            return filings
        
        recent = data.get("filings", {}).get("recent", {})
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        for i in range(len(recent.get("accessionNumber", []))):
            filing_date_str = recent.get("filingDate", [])[i] if i < len(recent.get("filingDate", [])) else ""
            if not filing_date_str:
                continue
            
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
            if filing_date < start_dt or filing_date > end_dt:
                continue
            
            form = recent.get("form", [])[i] if i < len(recent.get("form", [])) else ""
            
            # Only 13D/13G filings
            if form not in ["SC 13D", "SC 13D/A", "SC 13G", "SC 13G/A"]:
                continue
            
            acc = recent.get("accessionNumber", [])[i]
            acc_clean = acc.replace("-", "")
            primary_doc = recent.get("primaryDocument", [])[i] if i < len(recent.get("primaryDocument", [])) else ""
            
            doc_url = f"{self.SEC_ARCHIVES_URL}/{issuer_cik.lstrip('0')}/{acc_clean}/{primary_doc}"
            
            content = await self._fetch(doc_url)
            if content:
                record = self.schedule_parser.parse_schedule_13(
                    content, form, filing_date_str, acc, doc_url
                )
                if record:
                    filings.append(record)
        
        # Sort by date
        filings.sort(key=lambda x: x.filing_date)
        
        return filings
    
    def _detect_conversions(self, filings: List[ScheduleFilingRecord]):
        """Detect 13G to 13D conversions."""
        by_filer = defaultdict(list)
        for f in filings:
            by_filer[f.filer_cik or f.filer_name].append(f)
        
        for filer_id, filer_filings in by_filer.items():
            filer_filings.sort(key=lambda x: x.filing_date)
            
            last_13g_date = None
            
            for f in filer_filings:
                if "13G" in f.filing_type:
                    last_13g_date = f.filing_date
                elif "13D" in f.filing_type and last_13g_date:
                    # Conversion detected
                    original_dt = datetime.strptime(last_13g_date, "%Y-%m-%d")
                    conversion_dt = datetime.strptime(f.filing_date, "%Y-%m-%d")
                    days_as_passive = (conversion_dt - original_dt).days
                    
                    conversion = ThirteenGToThirteenDConversion(
                        filer_name=f.filer_name,
                        filer_cik=f.filer_cik,
                        issuer_name=f.issuer_name,
                        issuer_cik=f.issuer_cik,
                        original_13g_date=last_13g_date,
                        conversion_date=f.filing_date,
                        shares_at_conversion=f.shares_beneficially_owned,
                        percent_at_conversion=f.percent_of_class,
                        days_as_passive=days_as_passive,
                        significance="HIGH - Indicates shift from passive to activist intent"
                    )
                    self.conversions.append(conversion)
                    logger.warning(f"🔴 13G→13D CONVERSION: {f.filer_name} on {f.filing_date}")
    
    def _detect_accumulation_patterns(
        self,
        cusip: str,
        filings: List[ScheduleFilingRecord]
    ) -> List[InstitutionalAccumulationSignal]:
        """Detect coordinated accumulation patterns."""
        signals = []
        
        if len(filings) < 2:
            return signals
        
        # Group by 30-day windows
        windows = defaultdict(list)
        for f in filings:
            dt = datetime.strptime(f.filing_date, "%Y-%m-%d")
            window_key = dt.strftime("%Y-%m")  # Monthly windows
            windows[window_key].append(f)
        
        for window, window_filings in windows.items():
            if len(window_filings) >= 3:
                # Multiple filings in same window - potential coordination
                total_shares = sum(f.shares_beneficially_owned for f in window_filings)
                managers = [f.filer_name for f in window_filings]
                
                signal = InstitutionalAccumulationSignal(
                    cusip=cusip,
                    issuer_name=window_filings[0].issuer_name,
                    signal_type="ACCUMULATION",
                    institutions_involved=len(window_filings),
                    total_shares_change=total_shares,
                    average_change_pct=sum(f.percent_of_class for f in window_filings) / len(window_filings),
                    time_window_days=30,
                    detection_date=datetime.now().strftime("%Y-%m-%d"),
                    confidence=0.7 + (len(window_filings) * 0.05),
                    participating_managers=managers,
                    interpretation=f"{len(window_filings)} institutions filed in {window}"
                )
                signals.append(signal)
                self.accumulation_signals.append(signal)
        
        return signals
    
    def detect_accumulation_across_managers(
        self,
        cusip: str,
        threshold_pct: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        Flag securities being accumulated by multiple institutions.
        
        Args:
            cusip: Security CUSIP
            threshold_pct: Percentage change threshold
            
        Returns:
            List of accumulation signals
        """
        accumulations = []
        
        # Group holdings by manager
        by_manager = defaultdict(list)
        for holding in self.holdings.get(cusip, []):
            by_manager[holding.manager_cik].append(holding)
        
        # Check for significant increases
        for manager_cik, manager_holdings in by_manager.items():
            if len(manager_holdings) < 2:
                continue
            
            # Sort by report date
            sorted_holdings = sorted(manager_holdings, key=lambda x: x.report_date)
            
            for i in range(1, len(sorted_holdings)):
                prev = sorted_holdings[i-1]
                curr = sorted_holdings[i]
                
                if prev.shares > 0:
                    pct_change = ((curr.shares - prev.shares) / prev.shares) * 100
                    
                    if pct_change >= threshold_pct:
                        accumulations.append({
                            "manager": curr.manager_name,
                            "manager_cik": manager_cik,
                            "previous_shares": prev.shares,
                            "current_shares": curr.shares,
                            "change_pct": pct_change,
                            "report_date": curr.report_date
                        })
        
        return accumulations


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def track_institutional_ownership(
    cusip: str,
    issuer_cik: str,
    start_date: str,
    end_date: str,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Track institutional ownership for a security.
    
    Args:
        cusip: Security CUSIP
        issuer_cik: Issuer's CIK
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        output_dir: Optional output directory
        
    Returns:
        Tracking results
    """
    output_path = Path(output_dir) if output_dir else None
    
    async with InstitutionalOwnershipTracker(output_dir=output_path) as tracker:
        return await tracker.track_security(cusip, issuer_cik, start_date, end_date)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Institutional Ownership Tracker")
    parser.add_argument("--cusip", required=True, help="Security CUSIP")
    parser.add_argument("--issuer-cik", required=True, help="Issuer CIK")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default="forensic_reports", help="Output directory")
    
    args = parser.parse_args()
    
    result = asyncio.run(track_institutional_ownership(
        cusip=args.cusip,
        issuer_cik=args.issuer_cik,
        start_date=args.start,
        end_date=args.end,
        output_dir=args.output
    ))
    
    print(f"\nTotal Schedule Filings: {result['total_schedule_filings']}")
    print(f"5% Threshold Crossings: {result['threshold_crossings']['5_percent']}")
    print(f"13G→13D Conversions: {len(result['conversions'])}")

