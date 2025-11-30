"""
SEC Filing Stream - Real-time SEC EDGAR Monitoring System
==========================================================

Real-time monitoring system for SEC EDGAR RSS feeds with watchlist alerts,
Form 4/8-K prioritization, and webhook integration.

Features:
- Real-time RSS feed polling (SEC-compliant 10 req/sec rate limiting)
- Configurable watchlist by CIK, ticker, or company name
- Priority-based alerting (CRITICAL/HIGH/MEDIUM/LOW)
- 8-K material event item detection
- Webhook and callback notification support
- Form type filtering and prioritization

Usage:
    # Basic monitoring
    stream = SECFilingStream(watchlist=["AAPL", "TSLA", "NVDA"])
    stream.add_alert_handler(lambda alert: print(f"ALERT: {alert.filing.company_name}"))
    await stream.start_monitoring()
    
    # With webhook
    stream = SECFilingStream(
        watchlist=["0000320193"],  # Apple CIK
        webhook_url="https://example.com/webhook"
    )
"""

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urljoin

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Priority level for filing alerts."""
    CRITICAL = "critical"  # 8-K material events, Form 4 insider selling
    HIGH = "high"          # 10-K, 10-Q annual/quarterly reports
    MEDIUM = "medium"      # Form 4 (non-selling), 13F
    LOW = "low"           # Other filings


class FilingType(Enum):
    """SEC filing types with priority mappings."""
    FORM_8K = "8-K"
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_4 = "4"
    FORM_13F = "13F-HR"
    FORM_S1 = "S-1"
    FORM_DEF14A = "DEF 14A"
    FORM_SC13D = "SC 13D"
    FORM_SC13G = "SC 13G"
    OTHER = "OTHER"


# 8-K item codes that indicate material events
MATERIAL_8K_ITEMS = {
    "1.01": "Entry into Material Agreement",
    "1.02": "Termination of Material Agreement",
    "1.03": "Bankruptcy",
    "2.01": "Completion of Acquisition/Disposition",
    "2.03": "Obligation Under Off-Balance Sheet",
    "2.04": "Triggering Event (Default)",
    "2.05": "Exit Activities",
    "2.06": "Material Impairment",
    "3.01": "Delisting/Transfer of Securities",
    "3.03": "Material Modification to Rights",
    "4.01": "Change in Accountants",
    "4.02": "Non-Reliance on Prior Financial Statements",
    "5.01": "Changes in Control",
    "5.02": "Change in CEO/CFO/Directors",
    "5.03": "Amendments to Articles/Bylaws",
    "6.01": "ABS Servicer Change",
    "6.02": "ABS Credit Enhancement Change",
    "6.03": "ABS Master Trust Event",
    "6.04": "Failure to Make Distribution",
    "6.05": "Securities Act Updating Disclosure",
}


@dataclass
class SECFiling:
    """Represents an SEC filing."""
    accession_number: str
    cik: str
    company_name: str
    form_type: str
    filing_date: datetime
    accepted_date: Optional[datetime] = None
    file_number: Optional[str] = None
    film_number: Optional[str] = None
    items: List[str] = field(default_factory=list)  # For 8-K items
    documents_url: Optional[str] = None
    filing_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_material_8k(self) -> bool:
        """Check if this is an 8-K with material items."""
        if "8-K" not in self.form_type:
            return False
        return any(item in MATERIAL_8K_ITEMS for item in self.items)
    
    @property
    def form_type_enum(self) -> FilingType:
        """Get filing type enum."""
        form = self.form_type.upper().replace("/A", "")
        for ft in FilingType:
            if ft.value in form:
                return ft
        return FilingType.OTHER


@dataclass
class FilingAlert:
    """Alert for a new filing."""
    alert_id: str
    filing: SECFiling
    priority: AlertPriority
    matched_watchlist: List[str]
    timestamp: datetime
    alert_reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WatchlistEntry:
    """Entry in the filing watchlist."""
    identifier: str  # CIK, ticker, or company name
    identifier_type: str  # 'cik', 'ticker', 'name'
    priority_override: Optional[AlertPriority] = None
    form_types: Optional[Set[str]] = None  # Filter by form type


@dataclass
class StreamStats:
    """Statistics for the filing stream."""
    filings_processed: int = 0
    alerts_generated: int = 0
    errors: int = 0
    last_poll_time: Optional[datetime] = None
    uptime_seconds: float = 0.0
    rate_limit_delays: int = 0


class SECFilingStream:
    """
    Real-time SEC EDGAR filing stream monitor.
    
    Monitors SEC EDGAR RSS feeds for new filings and generates alerts
    based on a configurable watchlist.
    
    Example:
        stream = SECFilingStream(watchlist=["AAPL", "TSLA"])
        stream.add_alert_handler(my_handler)
        await stream.start_monitoring(poll_interval=60)
    """
    
    # SEC EDGAR RSS feed URL
    RSS_FEED_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    COMPANY_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type=&dateb=&owner=include&count=40&output=atom"
    FULL_INDEX_URL = "https://www.sec.gov/cgi-bin/srch-ia?text=form-type%3D*&first=1&last=40"
    
    # Rate limiting: SEC allows 10 requests per second
    MIN_REQUEST_INTERVAL = 0.1  # 100ms between requests
    
    # Default form type priorities
    FORM_PRIORITIES = {
        "8-K": AlertPriority.HIGH,
        "10-K": AlertPriority.HIGH,
        "10-Q": AlertPriority.HIGH,
        "4": AlertPriority.MEDIUM,
        "13F-HR": AlertPriority.MEDIUM,
        "S-1": AlertPriority.MEDIUM,
        "DEF 14A": AlertPriority.MEDIUM,
        "SC 13D": AlertPriority.HIGH,
        "SC 13G": AlertPriority.MEDIUM,
    }
    
    def __init__(
        self,
        watchlist: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        poll_interval: int = 60,
        user_agent: str = "JLAW-Forensics/1.0 (contact@example.com)",
    ):
        """
        Initialize the SEC Filing Stream.
        
        Args:
            watchlist: List of CIKs, tickers, or company names to monitor
            webhook_url: Optional webhook URL for notifications
            poll_interval: Seconds between RSS feed polls
            user_agent: User-Agent header (SEC requires identification)
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for SEC Filing Stream")
        
        self.webhook_url = webhook_url
        self.poll_interval = max(poll_interval, 30)  # Minimum 30 seconds
        self.user_agent = user_agent
        
        self._watchlist: Dict[str, WatchlistEntry] = {}
        self._alert_handlers: List[Callable[[FilingAlert], None]] = []
        self._seen_filings: Set[str] = set()
        self._stats = StreamStats()
        self._running = False
        self._last_request_time = 0.0
        
        # CIK to ticker mapping cache
        self._cik_ticker_cache: Dict[str, str] = {}
        
        # Add initial watchlist
        if watchlist:
            for item in watchlist:
                self.add_to_watchlist(item)
        
        logger.info(f"SECFilingStream initialized with {len(self._watchlist)} watchlist entries")
    
    def add_to_watchlist(
        self,
        identifier: str,
        priority_override: Optional[AlertPriority] = None,
        form_types: Optional[Set[str]] = None,
    ) -> None:
        """
        Add an entity to the watchlist.
        
        Args:
            identifier: CIK, ticker, or company name
            priority_override: Override default priority for this entity
            form_types: Only alert for these form types
        """
        identifier = identifier.strip()
        
        # Determine identifier type
        if identifier.isdigit() or identifier.startswith("000"):
            id_type = "cik"
            # Pad CIK to 10 digits
            identifier = identifier.zfill(10)
        elif len(identifier) <= 5 and identifier.isalpha():
            id_type = "ticker"
            identifier = identifier.upper()
        else:
            id_type = "name"
            identifier = identifier.upper()
        
        entry = WatchlistEntry(
            identifier=identifier,
            identifier_type=id_type,
            priority_override=priority_override,
            form_types=form_types,
        )
        
        self._watchlist[identifier] = entry
        logger.debug(f"Added to watchlist: {identifier} (type: {id_type})")
    
    def remove_from_watchlist(self, identifier: str) -> bool:
        """Remove an entity from the watchlist."""
        normalized = identifier.strip()
        
        # Try different normalizations
        for key in [normalized, normalized.upper(), normalized.zfill(10)]:
            if key in self._watchlist:
                del self._watchlist[key]
                logger.debug(f"Removed from watchlist: {key}")
                return True
        
        return False
    
    def add_alert_handler(self, handler: Callable[[FilingAlert], None]) -> None:
        """Add a callback handler for filing alerts."""
        self._alert_handlers.append(handler)
    
    def get_stats(self) -> StreamStats:
        """Get stream statistics."""
        return self._stats
    
    async def start_monitoring(self, duration: Optional[int] = None) -> None:
        """
        Start monitoring SEC filings.
        
        Args:
            duration: Optional duration in seconds (None = run indefinitely)
        """
        self._running = True
        start_time = time.time()
        
        logger.info(f"Starting SEC filing stream monitoring (interval: {self.poll_interval}s)")
        
        async with aiohttp.ClientSession() as session:
            while self._running:
                try:
                    await self._poll_filings(session)
                    self._stats.last_poll_time = datetime.now()
                except Exception as e:
                    logger.error(f"Error polling filings: {e}")
                    self._stats.errors += 1
                
                # Check duration
                if duration:
                    elapsed = time.time() - start_time
                    self._stats.uptime_seconds = elapsed
                    if elapsed >= duration:
                        logger.info("Duration reached, stopping monitoring")
                        break
                
                await asyncio.sleep(self.poll_interval)
        
        self._running = False
    
    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._running = False
        logger.info("Stopping SEC filing stream")
    
    async def _poll_filings(self, session: aiohttp.ClientSession) -> None:
        """Poll for new filings for all watched entities."""
        for identifier, entry in self._watchlist.items():
            await self._rate_limit()
            
            try:
                if entry.identifier_type == "cik":
                    filings = await self._fetch_company_filings(session, entry.identifier)
                else:
                    # For tickers/names, we need to resolve to CIK first
                    cik = await self._resolve_to_cik(session, entry.identifier)
                    if cik:
                        filings = await self._fetch_company_filings(session, cik)
                    else:
                        logger.warning(f"Could not resolve {entry.identifier} to CIK")
                        continue
                
                for filing in filings:
                    await self._process_filing(filing, entry)
                    
            except Exception as e:
                logger.error(f"Error fetching filings for {identifier}: {e}")
                self._stats.errors += 1
    
    async def _rate_limit(self) -> None:
        """Enforce SEC rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            delay = self.MIN_REQUEST_INTERVAL - elapsed
            await asyncio.sleep(delay)
            self._stats.rate_limit_delays += 1
        self._last_request_time = time.time()
    
    async def _fetch_company_filings(
        self, 
        session: aiohttp.ClientSession,
        cik: str,
    ) -> List[SECFiling]:
        """Fetch recent filings for a company."""
        url = self.COMPANY_RSS_URL.format(cik)
        headers = {"User-Agent": self.user_agent}
        
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch filings for CIK {cik}: {response.status}")
                return []
            
            content = await response.text()
            return self._parse_atom_feed(content, cik)
    
    def _parse_atom_feed(self, content: str, cik: str) -> List[SECFiling]:
        """Parse SEC EDGAR Atom feed."""
        filings = []
        
        # Simple regex parsing for Atom feed
        entry_pattern = r'<entry>(.*?)</entry>'
        title_pattern = r'<title[^>]*>([^<]+)</title>'
        link_pattern = r'<link[^>]*href="([^"]+)"'
        updated_pattern = r'<updated>([^<]+)</updated>'
        accession_pattern = r'/Archives/edgar/data/\d+/(\d+)'
        
        for entry_match in re.finditer(entry_pattern, content, re.DOTALL):
            entry = entry_match.group(1)
            
            # Extract title (contains form type and company name)
            title_match = re.search(title_pattern, entry)
            if not title_match:
                continue
            
            title = title_match.group(1)
            
            # Parse form type from title
            form_type_match = re.match(r'(\d+-[A-Z/]+|[A-Z\d-]+)', title)
            form_type = form_type_match.group(1) if form_type_match else "UNKNOWN"
            
            # Extract company name (after form type)
            company_parts = title.split(" - ")
            company_name = company_parts[1] if len(company_parts) > 1 else title
            
            # Extract link
            link_match = re.search(link_pattern, entry)
            filing_url = link_match.group(1) if link_match else None
            
            # Extract accession number from URL
            if filing_url:
                accession_match = re.search(accession_pattern, filing_url)
                accession = accession_match.group(1) if accession_match else ""
            else:
                accession = ""
            
            # Extract date
            updated_match = re.search(updated_pattern, entry)
            if updated_match:
                try:
                    filing_date = datetime.fromisoformat(updated_match.group(1).replace('Z', '+00:00'))
                except ValueError:
                    filing_date = datetime.now()
            else:
                filing_date = datetime.now()
            
            filing = SECFiling(
                accession_number=accession,
                cik=cik,
                company_name=company_name.strip(),
                form_type=form_type,
                filing_date=filing_date,
                filing_url=filing_url,
            )
            
            filings.append(filing)
        
        return filings
    
    async def _resolve_to_cik(
        self, 
        session: aiohttp.ClientSession,
        identifier: str,
    ) -> Optional[str]:
        """Resolve ticker or company name to CIK."""
        # Check cache first
        if identifier in self._cik_ticker_cache:
            return self._cik_ticker_cache[identifier]
        
        # Use SEC company search
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={identifier}&type=&dateb=&owner=include&count=10&output=atom"
        headers = {"User-Agent": self.user_agent}
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None
                
                content = await response.text()
                
                # Extract CIK from response
                cik_match = re.search(r'CIK=(\d+)', content)
                if cik_match:
                    cik = cik_match.group(1).zfill(10)
                    self._cik_ticker_cache[identifier] = cik
                    return cik
                    
        except Exception as e:
            logger.error(f"Error resolving {identifier}: {e}")
        
        return None
    
    async def _process_filing(
        self, 
        filing: SECFiling,
        watchlist_entry: WatchlistEntry,
    ) -> None:
        """Process a new filing and generate alerts if needed."""
        # Skip if we've seen this filing
        filing_key = f"{filing.cik}-{filing.accession_number}"
        if filing_key in self._seen_filings:
            return
        
        self._seen_filings.add(filing_key)
        self._stats.filings_processed += 1
        
        # Check form type filter
        if watchlist_entry.form_types:
            if not any(ft in filing.form_type for ft in watchlist_entry.form_types):
                return
        
        # Determine priority
        priority = self._determine_priority(filing, watchlist_entry)
        
        # Generate alert
        alert = FilingAlert(
            alert_id=f"alert-{filing_key}-{int(time.time())}",
            filing=filing,
            priority=priority,
            matched_watchlist=[watchlist_entry.identifier],
            timestamp=datetime.now(),
            alert_reason=self._generate_alert_reason(filing, priority),
        )
        
        self._stats.alerts_generated += 1
        
        # Call handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        # Send webhook if configured
        if self.webhook_url:
            await self._send_webhook(alert)
    
    def _determine_priority(
        self, 
        filing: SECFiling,
        entry: WatchlistEntry,
    ) -> AlertPriority:
        """Determine alert priority for a filing."""
        # Use override if specified
        if entry.priority_override:
            return entry.priority_override
        
        # Check for material 8-K
        if filing.is_material_8k:
            return AlertPriority.CRITICAL
        
        # Check Form 4 for insider selling
        if "4" in filing.form_type:
            # Would need to parse filing to determine if selling
            # For now, mark as medium
            return AlertPriority.MEDIUM
        
        # Use form type default priority
        for form_key, priority in self.FORM_PRIORITIES.items():
            if form_key in filing.form_type:
                return priority
        
        return AlertPriority.LOW
    
    def _generate_alert_reason(
        self, 
        filing: SECFiling,
        priority: AlertPriority,
    ) -> str:
        """Generate human-readable alert reason."""
        reasons = []
        
        reasons.append(f"New {filing.form_type} filing from {filing.company_name}")
        
        if filing.is_material_8k:
            material_items = [
                MATERIAL_8K_ITEMS.get(item, item) 
                for item in filing.items 
                if item in MATERIAL_8K_ITEMS
            ]
            if material_items:
                reasons.append(f"Material items: {', '.join(material_items)}")
        
        if priority == AlertPriority.CRITICAL:
            reasons.append("CRITICAL: Immediate attention recommended")
        elif priority == AlertPriority.HIGH:
            reasons.append("HIGH: Review within 24 hours recommended")
        
        return " | ".join(reasons)
    
    async def _send_webhook(self, alert: FilingAlert) -> None:
        """Send alert to webhook URL."""
        if not self.webhook_url:
            return
        
        payload = {
            "alert_id": alert.alert_id,
            "priority": alert.priority.value,
            "timestamp": alert.timestamp.isoformat(),
            "alert_reason": alert.alert_reason,
            "filing": {
                "cik": alert.filing.cik,
                "company_name": alert.filing.company_name,
                "form_type": alert.filing.form_type,
                "filing_date": alert.filing.filing_date.isoformat(),
                "filing_url": alert.filing.filing_url,
                "accession_number": alert.filing.accession_number,
            },
            "matched_watchlist": alert.matched_watchlist,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status >= 400:
                        logger.warning(f"Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    async def get_recent_filings(
        self,
        cik: str,
        form_types: Optional[List[str]] = None,
        days_back: int = 30,
    ) -> List[SECFiling]:
        """
        Get recent filings for a specific CIK.
        
        Args:
            cik: Company CIK number
            form_types: Filter by form types
            days_back: Number of days to look back
            
        Returns:
            List of recent filings
        """
        async with aiohttp.ClientSession() as session:
            filings = await self._fetch_company_filings(session, cik.zfill(10))
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filings = [f for f in filings if f.filing_date >= cutoff_date]
        
        # Filter by form type
        if form_types:
            filings = [
                f for f in filings 
                if any(ft in f.form_type for ft in form_types)
            ]
        
        return filings
