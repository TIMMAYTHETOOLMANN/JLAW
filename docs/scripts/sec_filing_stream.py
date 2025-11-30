"""
SEC Filing Stream - Real-Time Intelligence Module
=================================================

Real-time monitoring of SEC EDGAR filings with instant alerting
on target entities and configurable triggers.

Features:
- RSS feed polling from SEC EDGAR
- Configurable watchlist by CIK, ticker, or company name
- Form type filtering (8-K, 10-K, 10-Q, 4, etc.)
- Alert prioritization based on filing type
- Webhook and callback notification support
- Filing content prefetch and analysis

Usage:
    stream = SECFilingStream(watchlist=["AAPL", "MSFT", "GOOGL"])
    stream.add_alert_handler(my_callback)
    await stream.start_monitoring()

Note: SEC EDGAR limits requests to 10/second. This module
implements rate limiting to ensure compliance.
"""

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import re
from collections import deque
import logging


# Configure logging
logger = logging.getLogger(__name__)


class FilingPriority(Enum):
    """Priority levels for filing alerts."""
    CRITICAL = "critical"    # 8-K material events, restatements
    HIGH = "high"           # 10-K, 10-Q, Form 4 insider transactions
    MEDIUM = "medium"       # Proxy statements, S-1
    LOW = "low"             # Routine filings
    INFO = "info"           # All other filings


class FormType(Enum):
    """Common SEC form types."""
    FORM_8K = "8-K"
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_4 = "4"
    FORM_SC13D = "SC 13D"
    FORM_SC13G = "SC 13G"
    DEF_14A = "DEF 14A"
    FORM_S1 = "S-1"
    FORM_424B = "424B"
    FORM_13F = "13F-HR"
    OTHER = "OTHER"


@dataclass
class SECFiling:
    """Represents a single SEC filing."""
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filed_date: str
    accepted_datetime: str
    url: str
    description: str = ""
    size: int = 0
    
    # Enriched fields
    primary_document_url: Optional[str] = None
    items_reported: List[str] = field(default_factory=list)  # For 8-K items
    
    @property
    def filing_id(self) -> str:
        """Unique identifier for this filing."""
        return f"{self.cik}-{self.accession_number}"
    
    @property
    def edgar_url(self) -> str:
        """Full EDGAR URL for the filing."""
        acc_no_dashes = self.accession_number.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{self.cik}/{acc_no_dashes}/{self.accession_number}-index.html"


@dataclass
class FilingAlert:
    """Alert generated when a watchlist entity files."""
    alert_id: str
    filing: SECFiling
    priority: FilingPriority
    triggered_at: str
    watchlist_match: str  # Which watchlist entry triggered
    alert_reasons: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "alert_id": self.alert_id,
            "filing_id": self.filing.filing_id,
            "company": self.filing.company_name,
            "cik": self.filing.cik,
            "form_type": self.filing.form_type,
            "priority": self.priority.value,
            "filed_date": self.filing.filed_date,
            "url": self.filing.edgar_url,
            "triggered_at": self.triggered_at,
            "watchlist_match": self.watchlist_match,
            "alert_reasons": self.alert_reasons
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class WatchlistEntry:
    """A single entry in the watchlist."""
    identifier: str  # CIK, ticker, or company name
    identifier_type: str  # "cik", "ticker", "name"
    priority_boost: int = 0  # Additional priority (0-2)
    form_types: Optional[List[str]] = None  # Filter specific form types
    notes: str = ""
    
    @property
    def normalized_cik(self) -> Optional[str]:
        """Return normalized CIK if identifier is CIK."""
        if self.identifier_type == "cik":
            return self.identifier.zfill(10)
        return None


class RateLimiter:
    """Rate limiter for SEC EDGAR API compliance (10 req/sec)."""
    
    def __init__(self, requests_per_second: int = 10):
        self.requests_per_second = requests_per_second
        self.request_times: deque = deque(maxlen=requests_per_second)
    
    async def acquire(self):
        """Wait until a request slot is available."""
        now = datetime.utcnow()
        
        if len(self.request_times) >= self.requests_per_second:
            oldest = self.request_times[0]
            elapsed = (now - oldest).total_seconds()
            
            if elapsed < 1.0:
                wait_time = 1.0 - elapsed + 0.01  # Small buffer
                await asyncio.sleep(wait_time)
        
        self.request_times.append(datetime.utcnow())


class SECFilingStream:
    """
    Real-time SEC EDGAR filing monitor with alerting.
    
    Implements continuous polling of SEC RSS feeds with intelligent
    deduplication and priority-based alerting.
    """
    
    # SEC EDGAR RSS feed URLs
    RSS_FEEDS = {
        "company": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK={cik}&type=&dateb=&owner=include&count=40&output=atom",
        "all_filings": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&dateb=&owner=include&count=100&output=atom",
        "form_specific": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type={form_type}&dateb=&owner=include&count=100&output=atom"
    }
    
    # Form type to priority mapping
    FORM_PRIORITY = {
        "8-K": FilingPriority.CRITICAL,
        "8-K/A": FilingPriority.CRITICAL,
        "10-K": FilingPriority.HIGH,
        "10-K/A": FilingPriority.HIGH,
        "10-Q": FilingPriority.HIGH,
        "10-Q/A": FilingPriority.HIGH,
        "4": FilingPriority.HIGH,
        "4/A": FilingPriority.HIGH,
        "SC 13D": FilingPriority.HIGH,
        "SC 13D/A": FilingPriority.HIGH,
        "SC 13G": FilingPriority.MEDIUM,
        "SC 13G/A": FilingPriority.MEDIUM,
        "DEF 14A": FilingPriority.MEDIUM,
        "S-1": FilingPriority.MEDIUM,
        "S-1/A": FilingPriority.MEDIUM,
        "13F-HR": FilingPriority.LOW,
        "13F-HR/A": FilingPriority.LOW
    }
    
    # 8-K items that indicate material events
    MATERIAL_8K_ITEMS = {
        "1.01": "Entry into Material Agreement",
        "1.02": "Termination of Material Agreement",
        "1.03": "Bankruptcy",
        "2.01": "Acquisition/Disposition of Assets",
        "2.02": "Results of Operations",
        "2.03": "Creation of Obligation",
        "2.04": "Triggering Events",
        "2.05": "Exit/Disposal Activities",
        "2.06": "Material Impairments",
        "3.01": "Delisting",
        "4.01": "Change in Accountant",
        "4.02": "Non-Reliance on Financial Statements",
        "5.01": "Change in Control",
        "5.02": "Officer Departure/Appointment",
        "5.03": "Charter Amendment"
    }
    
    def __init__(
        self,
        watchlist: Optional[List[str]] = None,
        poll_interval: int = 60,
        user_agent: str = "JLAW-Forensics research@example.com"
    ):
        """
        Initialize the SEC filing stream.
        
        Args:
            watchlist: List of CIKs, tickers, or company names to monitor
            poll_interval: Seconds between polling (min 60 recommended)
            user_agent: User agent string (SEC requires identification)
        """
        self.poll_interval = max(poll_interval, 30)  # Minimum 30 seconds
        self.user_agent = user_agent
        
        self.watchlist: Dict[str, WatchlistEntry] = {}
        self.alert_handlers: List[Callable[[FilingAlert], Any]] = []
        self.seen_filings: Set[str] = set()
        self.rate_limiter = RateLimiter(requests_per_second=8)  # Conservative
        
        self._running = False
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Initialize watchlist
        if watchlist:
            for item in watchlist:
                self.add_to_watchlist(item)
    
    def add_to_watchlist(
        self,
        identifier: str,
        identifier_type: Optional[str] = None,
        priority_boost: int = 0,
        form_types: Optional[List[str]] = None,
        notes: str = ""
    ):
        """
        Add an entity to the watchlist.
        
        Args:
            identifier: CIK, ticker symbol, or company name
            identifier_type: "cik", "ticker", or "name" (auto-detected if None)
            priority_boost: Additional priority level (0-2)
            form_types: Specific form types to monitor (None = all)
            notes: Optional notes about this watchlist entry
        """
        # Auto-detect identifier type
        if identifier_type is None:
            if identifier.isdigit():
                identifier_type = "cik"
            elif len(identifier) <= 5 and identifier.isalpha():
                identifier_type = "ticker"
            else:
                identifier_type = "name"
        
        # Normalize CIK
        if identifier_type == "cik":
            identifier = identifier.zfill(10)
        
        entry = WatchlistEntry(
            identifier=identifier,
            identifier_type=identifier_type,
            priority_boost=priority_boost,
            form_types=form_types,
            notes=notes
        )
        
        self.watchlist[identifier.upper()] = entry
        logger.info(f"Added to watchlist: {identifier} ({identifier_type})")
    
    def remove_from_watchlist(self, identifier: str):
        """Remove an entity from the watchlist."""
        key = identifier.upper()
        if key in self.watchlist:
            del self.watchlist[key]
            logger.info(f"Removed from watchlist: {identifier}")
    
    def add_alert_handler(self, handler: Callable[[FilingAlert], Any]):
        """
        Add a callback function to handle alerts.
        
        Handler will be called with FilingAlert when watchlist entity files.
        """
        self.alert_handlers.append(handler)
    
    async def start_monitoring(self):
        """Start the filing monitoring loop."""
        if self._running:
            logger.warning("Monitoring already running")
            return
        
        self._running = True
        logger.info(f"Starting SEC filing monitor with {len(self.watchlist)} watchlist entries")
        
        async with aiohttp.ClientSession() as session:
            self._session = session
            
            while self._running:
                try:
                    await self._poll_filings()
                except Exception as e:
                    logger.error(f"Error polling filings: {e}")
                
                await asyncio.sleep(self.poll_interval)
        
        self._session = None
    
    def stop_monitoring(self):
        """Stop the filing monitoring loop."""
        self._running = False
        logger.info("Stopping SEC filing monitor")
    
    async def _poll_filings(self):
        """Poll SEC feeds for new filings."""
        # Poll general filings feed
        filings = await self._fetch_recent_filings()
        
        for filing in filings:
            # Check if we've seen this filing
            if filing.filing_id in self.seen_filings:
                continue
            
            self.seen_filings.add(filing.filing_id)
            
            # Check against watchlist
            watchlist_match = self._check_watchlist(filing)
            if watchlist_match:
                alert = await self._create_alert(filing, watchlist_match)
                await self._dispatch_alert(alert)
    
    async def _fetch_recent_filings(self) -> List[SECFiling]:
        """Fetch recent filings from SEC RSS feed."""
        await self.rate_limiter.acquire()
        
        url = self.RSS_FEEDS["all_filings"]
        headers = {"User-Agent": self.user_agent}
        
        try:
            async with self._session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"SEC feed returned status {response.status}")
                    return []
                
                content = await response.text()
                return self._parse_atom_feed(content)
        
        except Exception as e:
            logger.error(f"Error fetching SEC feed: {e}")
            return []
    
    def _parse_atom_feed(self, content: str) -> List[SECFiling]:
        """Parse SEC Atom RSS feed."""
        filings = []
        
        try:
            # Remove namespace for easier parsing
            content = re.sub(r'xmlns="[^"]+"', '', content)
            root = ET.fromstring(content)
            
            for entry in root.findall('.//entry'):
                try:
                    filing = self._parse_entry(entry)
                    if filing:
                        filings.append(filing)
                except Exception as e:
                    logger.debug(f"Error parsing entry: {e}")
                    continue
        
        except ET.ParseError as e:
            logger.error(f"Error parsing feed XML: {e}")
        
        return filings
    
    def _parse_entry(self, entry: ET.Element) -> Optional[SECFiling]:
        """Parse a single entry from the Atom feed."""
        title = entry.findtext('title', '')
        updated = entry.findtext('updated', '')
        link = entry.find('link')
        link_href = link.get('href', '') if link is not None else ''
        summary = entry.findtext('summary', '')
        
        # Parse title: "Form Type - Company Name (CIK)"
        title_match = re.match(r'(.+?)\s*-\s*(.+?)\s*\((\d+)\)', title)
        if not title_match:
            return None
        
        form_type = title_match.group(1).strip()
        company_name = title_match.group(2).strip()
        cik = title_match.group(3).strip().zfill(10)
        
        # Extract accession number from link
        acc_match = re.search(r'/(\d{10}-\d{2}-\d{6})', link_href)
        if not acc_match:
            return None
        
        accession_number = acc_match.group(1)
        
        # Parse filed date from updated
        try:
            filed_date = updated[:10] if updated else datetime.utcnow().strftime('%Y-%m-%d')
        except:
            filed_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        return SECFiling(
            accession_number=accession_number,
            cik=cik,
            company_name=company_name,
            form_type=form_type,
            filed_date=filed_date,
            accepted_datetime=updated,
            url=link_href,
            description=summary
        )
    
    def _check_watchlist(self, filing: SECFiling) -> Optional[WatchlistEntry]:
        """Check if filing matches any watchlist entry."""
        # Check by CIK
        cik_key = filing.cik.upper()
        if cik_key in self.watchlist:
            return self.watchlist[cik_key]
        
        # Check by company name (partial match)
        company_upper = filing.company_name.upper()
        for key, entry in self.watchlist.items():
            if entry.identifier_type == "name":
                if entry.identifier.upper() in company_upper:
                    return entry
            elif entry.identifier_type == "ticker":
                # Would need ticker->CIK mapping (external lookup)
                # For now, check if ticker appears in company name
                if entry.identifier.upper() in company_upper:
                    return entry
        
        return None
    
    async def _create_alert(
        self,
        filing: SECFiling,
        watchlist_entry: WatchlistEntry
    ) -> FilingAlert:
        """Create an alert for a watchlist match."""
        # Determine base priority
        base_priority = self.FORM_PRIORITY.get(filing.form_type, FilingPriority.INFO)
        
        # Apply priority boost
        priority_order = [
            FilingPriority.INFO,
            FilingPriority.LOW,
            FilingPriority.MEDIUM,
            FilingPriority.HIGH,
            FilingPriority.CRITICAL
        ]
        
        current_idx = priority_order.index(base_priority)
        boosted_idx = min(current_idx + watchlist_entry.priority_boost, len(priority_order) - 1)
        final_priority = priority_order[boosted_idx]
        
        # Generate alert reasons
        alert_reasons = [
            f"Watchlist match: {watchlist_entry.identifier}",
            f"Form type: {filing.form_type}"
        ]
        
        # For 8-K, try to identify material items
        if filing.form_type.startswith("8-K"):
            material_items = await self._check_8k_items(filing)
            if material_items:
                alert_reasons.extend(material_items)
                if any("4.02" in item or "2.06" in item or "5.02" in item for item in material_items):
                    final_priority = FilingPriority.CRITICAL
        
        # Generate alert ID
        alert_id = hashlib.sha256(
            f"{filing.filing_id}|{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return FilingAlert(
            alert_id=alert_id,
            filing=filing,
            priority=final_priority,
            triggered_at=datetime.utcnow().isoformat() + "Z",
            watchlist_match=watchlist_entry.identifier,
            alert_reasons=alert_reasons
        )
    
    async def _check_8k_items(self, filing: SECFiling) -> List[str]:
        """Check which items are reported in an 8-K filing."""
        # Would fetch and parse the 8-K document
        # For now, return empty (would need additional SEC fetch)
        return []
    
    async def _dispatch_alert(self, alert: FilingAlert):
        """Dispatch alert to all registered handlers."""
        logger.info(
            f"ALERT [{alert.priority.value.upper()}]: {alert.filing.company_name} "
            f"filed {alert.filing.form_type}"
        )
        
        for handler in self.alert_handlers:
            try:
                result = handler(alert)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    async def fetch_filing_content(self, filing: SECFiling) -> Optional[str]:
        """Fetch the full text content of a filing."""
        await self.rate_limiter.acquire()
        
        headers = {"User-Agent": self.user_agent}
        
        try:
            async with self._session.get(filing.edgar_url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching filing content: {e}")
        
        return None
    
    def get_watchlist_status(self) -> Dict[str, Any]:
        """Get current watchlist status."""
        return {
            "entries": len(self.watchlist),
            "monitoring": self._running,
            "filings_seen": len(self.seen_filings),
            "watchlist": [
                {
                    "identifier": e.identifier,
                    "type": e.identifier_type,
                    "priority_boost": e.priority_boost
                }
                for e in self.watchlist.values()
            ]
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def monitor_entities(
    entities: List[str],
    callback: Callable[[FilingAlert], Any],
    poll_interval: int = 60
) -> SECFilingStream:
    """
    Convenience function to start monitoring entities.
    
    Args:
        entities: List of CIKs, tickers, or company names
        callback: Function to call when alert is triggered
        poll_interval: Seconds between polling
        
    Returns:
        SECFilingStream instance (call stop_monitoring() to stop)
    """
    stream = SECFilingStream(
        watchlist=entities,
        poll_interval=poll_interval
    )
    stream.add_alert_handler(callback)
    
    # Start monitoring in background task
    asyncio.create_task(stream.start_monitoring())
    
    return stream


def create_webhook_handler(webhook_url: str) -> Callable[[FilingAlert], Any]:
    """
    Create an alert handler that posts to a webhook URL.
    
    Args:
        webhook_url: URL to POST alert JSON to
        
    Returns:
        Handler function
    """
    async def handler(alert: FilingAlert):
        async with aiohttp.ClientSession() as session:
            try:
                await session.post(
                    webhook_url,
                    json=alert.to_dict(),
                    headers={"Content-Type": "application/json"}
                )
            except Exception as e:
                logger.error(f"Webhook error: {e}")
    
    return handler


# Module exports
__all__ = [
    "SECFilingStream",
    "SECFiling",
    "FilingAlert",
    "FilingPriority",
    "FormType",
    "WatchlistEntry",
    "monitor_entities",
    "create_webhook_handler"
]
