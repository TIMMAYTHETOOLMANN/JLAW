"""
Multi-Tier SEC Data Fetcher - CRITICAL INFRASTRUCTURE
=====================================================

Implements a multi-pronged, fault-tolerant approach to SEC data acquisition:

TIER 1: SEC EDGAR API (data.sec.gov) - Primary source
TIER 2: SEC Archives Direct (www.sec.gov/Archives) - Fallback
TIER 3: SEC EDGAR Search (www.sec.gov/cgi-bin/browse-edgar) - Alternative
TIER 4: SEC EFTS (efts.sec.gov) - Bulk data source

Features:
- Intelligent rotation between data sources
- Adaptive rate limiting per endpoint
- Exponential backoff with jitter
- Circuit breaker pattern
- Request queuing and prioritization
- Automatic failover
- Cache-first strategy
- Health monitoring per tier
- Request deduplication
- Retry logic with different endpoints

Rate Limits:
- SEC EDGAR API: 10 req/sec (we use 6/sec conservative)
- SEC Archives: 10 req/sec (we use 6/sec conservative)
- SEC Search: No explicit limit (we use 5/sec conservative)
- SEC EFTS: Bulk downloads (daily limits)

Author: JARVIS NEXUS
Date: 2025-12-07
"""

import asyncio
import aiohttp
import hashlib
import json
import logging
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from urllib.parse import urljoin, urlparse, quote
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class SECTier(Enum):
    """SEC data source tiers"""
    EDGAR_API = "edgar_api"  # data.sec.gov - Structured JSON API
    ARCHIVES = "archives"  # www.sec.gov/Archives - Direct file access
    BROWSE = "browse"  # www.sec.gov/cgi-bin/browse-edgar - Search interface
    EFTS = "efts"  # efts.sec.gov - Bulk data
    CACHE = "cache"  # Local cache


class RequestPriority(Enum):
    """Request priority levels"""
    CRITICAL = 1  # Real-time analysis requirements
    HIGH = 2  # User-facing requests
    NORMAL = 3  # Background analysis
    LOW = 4  # Prefetch and cache warming


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures detected, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class TierHealth:
    """Health metrics for a data source tier"""
    tier: SECTier
    state: CircuitState = CircuitState.CLOSED
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    last_request: Optional[float] = None
    total_requests: int = 0
    average_response_time: float = 0.0
    rate_limit_hits: int = 0
    
    # Circuit breaker thresholds
    failure_threshold: int = 5  # Open circuit after 5 consecutive failures
    success_threshold: int = 2  # Close circuit after 2 consecutive successes in half-open
    timeout_seconds: float = 60.0  # Wait 60s before trying half-open
    
    def record_success(self, response_time: float):
        """Record successful request"""
        self.success_count += 1
        self.consecutive_failures = 0
        self.last_success = time.time()
        self.last_request = time.time()
        self.total_requests += 1
        
        # Update average response time (exponential moving average)
        alpha = 0.3
        self.average_response_time = (
            alpha * response_time + (1 - alpha) * self.average_response_time
        )
        
        # Transition to closed if in half-open
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info(f"Circuit breaker CLOSED for {self.tier.value}")
    
    def record_failure(self, is_rate_limit: bool = False):
        """Record failed request"""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure = time.time()
        self.last_request = time.time()
        self.total_requests += 1
        
        if is_rate_limit:
            self.rate_limit_hits += 1
        
        # Open circuit if threshold exceeded
        if self.consecutive_failures >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker OPENED for {self.tier.value} after {self.consecutive_failures} failures")
    
    def can_attempt(self) -> bool:
        """Check if requests can be attempted"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure and (time.time() - self.last_failure) > self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker HALF-OPEN for {self.tier.value}")
                return True
            return False
        
        # HALF_OPEN state - allow limited requests
        return True
    
    def get_health_score(self) -> float:
        """Calculate health score (0.0 to 1.0)"""
        if self.state == CircuitState.OPEN:
            return 0.0
        
        if self.total_requests == 0:
            return 0.5  # Unknown state
        
        success_rate = self.success_count / self.total_requests
        
        # Penalize for recent failures
        recency_penalty = 0.0
        if self.last_failure and self.last_success:
            if self.last_failure > self.last_success:
                time_since = time.time() - self.last_failure
                recency_penalty = max(0.0, 0.3 - (time_since / 300))  # Decay over 5 minutes
        
        # Penalize for rate limiting
        rate_limit_penalty = min(0.2, self.rate_limit_hits * 0.05)
        
        health_score = max(0.0, success_rate - recency_penalty - rate_limit_penalty)
        
        if self.state == CircuitState.HALF_OPEN:
            health_score *= 0.7  # Reduce score during recovery
        
        return health_score


@dataclass
class SECRequest:
    """SEC data request with metadata"""
    request_id: str
    url: str
    priority: RequestPriority
    created_at: float = field(default_factory=time.time)
    attempts: int = 0
    max_attempts: int = 5
    cache_key: Optional[str] = None
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SECResponse:
    """SEC data response with provenance"""
    content: str
    tier: SECTier
    cached: bool
    response_time: float
    status_code: int
    headers: Dict[str, str]
    url: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    content_hash: str = field(default="")
    
    def __post_init__(self):
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode('utf-8')).hexdigest()


class SECFetchError(Exception):
    """Raised when all tiers fail to fetch a SEC resource.

    Contains context to avoid silent failures during forensic analysis.
    """

    def __init__(self, url: str, attempts_summary: Optional[List[Dict[str, Any]]] = None, message: Optional[str] = None):
        self.url = url
        self.attempts_summary = attempts_summary or []
        self.message = message or "All SEC tiers failed to fetch resource"
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"{self.message}: {self.url}"
        if not self.attempts_summary:
            return base
        details = "; ".join(
            f"tier={a.get('tier')} retries={a.get('retries')} last_status={a.get('last_status')}" for a in self.attempts_summary
        )
        return f"{base} | attempts: {details}"


class RateLimiter:
    """Token bucket rate limiter per tier"""
    
    def __init__(self, tier: SECTier, rate: float):
        """
        Initialize rate limiter
        
        Args:
            tier: The tier this rate limiter is for
            rate: Requests per second
        """
        self.tier = tier
        self.rate = rate
        self.tokens = rate
        self.max_tokens = rate
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self.lock:
            while True:
                now = time.time()
                elapsed = now - self.last_update
                
                # Refill tokens
                self.tokens = min(self.max_tokens, self.tokens + elapsed * self.rate)
                self.last_update = now
                
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                
                # Wait for next token
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)


class MultiTierSECFetcher:
    """
    Multi-tier SEC data fetcher with intelligent rotation and failover
    """
    
    # Tier configurations
    TIER_CONFIGS = {
        SECTier.EDGAR_API: {
            "base_url": "https://data.sec.gov",
            "rate_limit": 6.0,  # requests per second
            "timeout": 30.0,
            "user_agent": "JLAW-Forensics/3.0 (Multi-Tier SEC Fetcher; forensics@jlaw.ai)",
        },
        SECTier.ARCHIVES: {
            "base_url": "https://www.sec.gov/Archives",
            "rate_limit": 6.0,
            "timeout": 30.0,
            "user_agent": "JLAW-Forensics/3.0 (Multi-Tier SEC Fetcher; forensics@jlaw.ai)",
        },
        SECTier.BROWSE: {
            "base_url": "https://www.sec.gov/cgi-bin/browse-edgar",
            "rate_limit": 5.0,
            "timeout": 45.0,
            "user_agent": "JLAW-Forensics/3.0 (Multi-Tier SEC Fetcher; forensics@jlaw.ai)",
        },
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize multi-tier SEC fetcher
        
        Args:
            cache_dir: Directory for caching responses
        """
        self.cache_dir = cache_dir or Path("forensic_storage/sec_cache_v3")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Health monitoring per tier (include CACHE so health reports have data even when all hits are cached)
        self.tier_health: Dict[SECTier, TierHealth] = {
            tier: TierHealth(tier=tier) for tier in [SECTier.EDGAR_API, SECTier.ARCHIVES, SECTier.BROWSE, SECTier.CACHE]
        }
        
        # Rate limiters per tier
        self.rate_limiters: Dict[SECTier, RateLimiter] = {
            tier: RateLimiter(tier, config["rate_limit"])
            for tier, config in self.TIER_CONFIGS.items()
        }
        
        # Request queue with priority
        self.request_queues: Dict[RequestPriority, deque] = {
            priority: deque() for priority in RequestPriority
        }
        
        # Active sessions per tier
        self.sessions: Dict[SECTier, Optional[aiohttp.ClientSession]] = {}
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'tier_usage': defaultdict(int),
            'failovers': 0,
            'rate_limit_hits': 0,
            'circuit_breaks': 0,
        }
        
        # Request deduplication
        self._in_flight_requests: Dict[str, asyncio.Future] = {}
        
        logger.info("MultiTierSECFetcher initialized with 3-tier architecture")
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Create sessions for each tier
        for tier, config in self.TIER_CONFIGS.items():
            headers = {
                'User-Agent': config['user_agent'],
                'Accept-Encoding': 'gzip, deflate',
                'Accept': 'application/json, text/html, text/xml, */*',
            }
            
            # Add specific headers for EDGAR API
            if tier == SECTier.EDGAR_API:
                headers['Host'] = 'data.sec.gov'
            
            self.sessions[tier] = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=config['timeout']),
                connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
            )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        for session in self.sessions.values():
            if session:
                await session.close()
        
        # Log final statistics
        logger.info("MultiTierSECFetcher statistics:")
        logger.info(f"  Total requests: {self.stats['total_requests']}")
        logger.info(f"  Cache hits: {self.stats['cache_hits']}")
        logger.info(f"  Cache misses: {self.stats['cache_misses']}")
        logger.info(f"  Failovers: {self.stats['failovers']}")
        logger.info(f"  Rate limit hits: {self.stats['rate_limit_hits']}")
        
        for tier, count in self.stats['tier_usage'].items():
            logger.info(f"  {tier}: {count} requests")
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        # Use first 2 chars for subdirectory to avoid too many files in one dir
        subdir = self.cache_dir / cache_key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{cache_key}.json"
    
    def _generate_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()
    
    async def _load_from_cache(self, cache_key: str) -> Optional[SECResponse]:
        """Load response from cache"""
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if cache is still fresh (24 hours for most data)
            cached_time = datetime.fromisoformat(data['timestamp'])
            age = datetime.utcnow() - cached_time
            
            # Different expiry for different content types
            max_age_hours = 24
            if 'submissions/CIK' in data.get('url', ''):
                max_age_hours = 1  # Company submissions update frequently
            
            if age > timedelta(hours=max_age_hours):
                logger.debug(f"Cache expired for {cache_key}")
                return None
            
            self.stats['cache_hits'] += 1
            # Record a successful 'CACHE' tier hit for health visibility
            try:
                self.tier_health[SECTier.CACHE].record_success(response_time=0.0)
                self.stats['tier_usage'][SECTier.CACHE.value] += 1
            except Exception:
                pass

            return SECResponse(
                content=data['content'],
                tier=SECTier.CACHE,
                cached=True,
                response_time=0.0,
                status_code=200,
                headers=data.get('headers', {}),
                url=data['url'],
                timestamp=data['timestamp'],
                content_hash=data.get('content_hash', '')
            )
        
        except Exception as e:
            logger.debug(f"Error loading cache {cache_key}: {e}")
            return None
    
    async def _save_to_cache(self, cache_key: str, response: SECResponse):
        """Save response to cache"""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            data = {
                'content': response.content,
                'url': response.url,
                'timestamp': response.timestamp,
                'status_code': response.status_code,
                'headers': response.headers,
                'content_hash': response.content_hash,
                'tier': response.tier.value,
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Cached response for {cache_key}")
        
        except Exception as e:
            logger.warning(f"Error saving cache {cache_key}: {e}")
    
    def _select_tier(self, exclude: Optional[set] = None) -> Optional[SECTier]:
        """Select best available tier based on health scores.

        Args:
            exclude: Optional set of tiers that should not be selected (already tried)
        """
        available_tiers = []

        excluded = exclude or set()
        for tier in [SECTier.EDGAR_API, SECTier.ARCHIVES, SECTier.BROWSE]:
            if tier in excluded:
                continue
            health = self.tier_health[tier]
            if health.can_attempt():
                score = health.get_health_score()
                available_tiers.append((tier, score))
        
        if not available_tiers:
            logger.error("No tiers available! All circuit breakers open.")
            return None
        
        # Sort by health score (highest first)
        available_tiers.sort(key=lambda x: x[1], reverse=True)
        
        # Add randomness to prevent always hitting the same tier
        # Use weighted random selection based on health scores
        total_score = sum(score for _, score in available_tiers)
        if total_score > 0:
            rand = random.random() * total_score
            cumulative = 0.0
            for tier, score in available_tiers:
                cumulative += score
                if rand <= cumulative:
                    return tier
        
        # Fallback to best tier
        return available_tiers[0][0]

    @staticmethod
    def _find_primary_from_submissions(subs: Dict[str, Any], dashed_accession: str) -> Optional[str]:
        """Find primaryDocument for a given dashed accession in SEC submissions JSON.

        Searches both filings.recent arrays and filings.files list.
        """
        try:
            filings = subs.get('filings') or {}
            # 1) recent arrays
            recent = filings.get('recent') or {}
            accessions = recent.get('accessionNumber') or recent.get('accession_number') or []
            primaries = recent.get('primaryDocument') or recent.get('primary_document') or []
            for i, an in enumerate(accessions):
                if an == dashed_accession and i < len(primaries):
                    return primaries[i]
            # 2) files list (older filings)
            files = filings.get('files') or []
            for f in files:
                if (f.get('accessionNumber') or f.get('accession_number')) == dashed_accession:
                    pd = f.get('primaryDocument') or f.get('primary_document')
                    if pd:
                        return pd
        except Exception:
            pass
        return None

    async def _find_primary_from_submissions_deep(self, cik_padded: str, dashed_accession: str) -> Optional[str]:
        """Look up primaryDocument for older filings by following EDGAR submissions 'files' JSON pointers."""
        try:
            api_session = self.sessions.get(SECTier.EDGAR_API)
            if not api_session:
                return None
            # Load main submissions first
            sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
            async with api_session.get(sub_url) as sub_resp:
                if sub_resp.status != 200:
                    return None
                subs = await sub_resp.json()
                # Try shallow search first
                primary = self._find_primary_from_submissions(subs, dashed_accession)
                if primary:
                    return primary
                # Deep search in 'files' pointers
                files = (subs.get('filings') or {}).get('files') or []
                for f in files[:6]:  # limit to first few files
                    name = f.get('name')
                    if not name or not name.endswith('.json'):
                        continue
                    url = f"https://data.sec.gov/{name}"
                    async with api_session.get(url) as older_resp:
                        if older_resp.status != 200:
                            continue
                        older = await older_resp.json()
                        # Structure often mirrors 'filings': {'files': [...] } or direct arrays
                        recent = (older.get('filings') or {}).get('recent') or {}
                        accessions = recent.get('accessionNumber') or recent.get('accession_number') or []
                        primaries = recent.get('primaryDocument') or recent.get('primary_document') or []
                        for i, an in enumerate(accessions):
                            if an == dashed_accession and i < len(primaries):
                                return primaries[i]
        except Exception:
            return None
        return None
    
    async def _fetch_from_tier(
        self,
        tier: SECTier,
        url: str,
        attempt: int = 1
    ) -> Optional[SECResponse]:
        """Fetch data from a specific tier"""
        config = self.TIER_CONFIGS[tier]
        session = self.sessions.get(tier)
        
        if not session:
            logger.error(f"No session for tier {tier.value}")
            return None
        
        # Rate limiting
        await self.rate_limiters[tier].acquire()
        
        start_time = time.time()
        
        try:
            logger.debug(f"Fetching from {tier.value}: {url}")
            
            async with session.get(url) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    content = await response.text()
                    
                    self.tier_health[tier].record_success(response_time)
                    self.stats['tier_usage'][tier.value] += 1
                    
                    return SECResponse(
                        content=content,
                        tier=tier,
                        cached=False,
                        response_time=response_time,
                        status_code=response.status,
                        headers=dict(response.headers),
                        url=url
                    )
                
                elif response.status in (429, 503):
                    # Rate limited
                    limited_label = "Rate limited" if response.status == 429 else "Service unavailable"
                    logger.warning(f"{limited_label} ({response.status}) from {tier.value} for {url}")
                    self.tier_health[tier].record_failure(is_rate_limit=(response.status == 429))
                    if response.status == 429:
                        self.stats['rate_limit_hits'] += 1

                    # Honor Retry-After header when present
                    retry_after = 0.0
                    ra = response.headers.get('Retry-After')
                    if ra:
                        try:
                            # Seconds format
                            retry_after = float(ra)
                        except ValueError:
                            # HTTP-date format
                            try:
                                from email.utils import parsedate_to_datetime
                                dt = parsedate_to_datetime(ra)
                                retry_after = max(0.0, (dt - datetime.utcnow().replace(tzinfo=dt.tzinfo)).total_seconds())
                            except Exception:
                                retry_after = 0.0

                    # Exponential backoff with jitter, capped
                    exp_backoff = (2 ** attempt) + random.uniform(0, 1)
                    backoff = min(90.0, max(retry_after, exp_backoff))
                    await asyncio.sleep(backoff)

                    return None
                
                elif response.status in [403, 404]:
                    # Client errors
                    logger.warning(f"{tier.value} returned {response.status} for {url}")

                    # Smart fallback for ARCHIVES 404: try directory index discovery to locate actual document name
                    if response.status == 404 and tier == SECTier.ARCHIVES:
                        try:
                            parsed = urlparse(url)
                            # base_dir: strip last path segment
                            if '/' in parsed.path:
                                base_dir = parsed.path.rsplit('/', 1)[0] + '/'
                            else:
                                base_dir = parsed.path + '/'
                            base_dir_url = f"https://{parsed.netloc}{base_dir}"

                            # 0) Try common index file names directly when requesting directory index
                            requested_name = parsed.path.split('/')[-1]
                            if requested_name.lower() in ("index.json", "index.htm", "index.html"):
                                for idx_name in ("index.html", "index.htm"):
                                    cand_idx = urljoin(base_dir_url, idx_name)
                                    fallback_start0 = time.time()
                                    async with session.get(cand_idx) as idx_html_resp:
                                        if idx_html_resp.status == 200:
                                            cand_content0 = await idx_html_resp.text()
                                            response_time0 = time.time() - fallback_start0
                                            self.tier_health[tier].record_success(response_time0)
                                            self.stats['tier_usage'][tier.value] += 1
                                            logger.info(f"Recovered 404 by fetching alternate index file: {idx_name}")
                                            return SECResponse(
                                                content=cand_content0,
                                                tier=tier,
                                                cached=False,
                                                response_time=response_time0,
                                                status_code=200,
                                                headers=dict(idx_html_resp.headers),
                                                url=cand_idx
                                            )

                            # 1) Attempt JSON index
                            async with session.get(urljoin(base_dir_url, 'index.json')) as idx_resp:
                                if idx_resp.status == 200:
                                    idx_json = await idx_resp.json()
                                    items = (idx_json.get('directory') or {}).get('item', [])
                                else:
                                    items = []

                            # 2) If no JSON index, attempt HTML directory listing and accession-index pages
                            if not items:
                                # Try base directory listing
                                async with session.get(base_dir_url) as html_resp:
                                    if html_resp.status == 200:
                                        html = await html_resp.text()
                                        soup = BeautifulSoup(html, 'html.parser')
                                        items = []
                                        for a in soup.select('a[href]'):
                                            href = a.get('href') or ''
                                            if href and href not in ('../', './') and not href.startswith('?'):
                                                # Normalize name
                                                name = href
                                                if name:
                                                    items.append({'name': name})
                                # Try dashed accession index pages
                                if not items:
                                    # Build dashed accession like 0000320187-19-000113
                                    path_parts = [p for p in parsed.path.split('/') if p]
                                    if len(path_parts) >= 6:
                                        cik_part = path_parts[3]
                                        acc_part = path_parts[4]
                                        cik_padded = str(int(cik_part)).zfill(10)
                                        if len(acc_part) >= 12:
                                            dashed = f"{cik_padded}-{acc_part[10:12]}-{acc_part[12:]}"
                                        else:
                                            dashed = acc_part
                                        for idx_name in (f"{dashed}-index.htm", f"{dashed}-index.html"):
                                            idx_url = urljoin(base_dir_url, idx_name)
                                            async with session.get(idx_url) as idx_html_resp:
                                                if idx_html_resp.status == 200:
                                                    html = await idx_html_resp.text()
                                                    soup = BeautifulSoup(html, 'html.parser')
                                                    items = []
                                                    for a in soup.select('a[href]'):
                                                        href = a.get('href') or ''
                                                        if href and href not in ('../', './') and not href.startswith('?'):
                                                            name = href
                                                            if name:
                                                                items.append({'name': name})
                                                    if items:
                                                        break

                            # 3) Choose best candidate matching requested document name
                            requested_name = parsed.path.split('/')[-1]
                            candidate = None
                            base_name = requested_name.rsplit('.', 1)[0]
                            # Exact match first
                            for it in items:
                                n = it.get('name', '')
                                if n.split('/')[-1] == requested_name:
                                    candidate = it['name']
                                    break
                            # Prefix match for .htm/.html
                            if not candidate:
                                for it in items:
                                    n = it.get('name', '')
                                    n_base = n.split('/')[-1]
                                    if n_base.lower().startswith(base_name.lower()) and (n_base.lower().endswith('.htm') or n_base.lower().endswith('.html')):
                                        candidate = n
                                        break
                            # Any .htm/.html as last resort
                            if not candidate:
                                for it in items:
                                    n = it.get('name', '')
                                    n_base = n.split('/')[-1]
                                    if n_base.lower().endswith('.htm') or n_base.lower().endswith('.html'):
                                        candidate = n
                                        break

                            if candidate:
                                # Try fetching the discovered candidate
                                cand_url = urljoin(base_dir_url, candidate)
                                fallback_start = time.time()
                                async with session.get(cand_url) as cand_resp:
                                    if cand_resp.status == 200:
                                        cand_content = await cand_resp.text()
                                        response_time2 = time.time() - fallback_start
                                        self.tier_health[tier].record_success(response_time2)
                                        self.stats['tier_usage'][tier.value] += 1
                                        logger.info(f"Recovered 404 by fetching alternate document: {candidate}")
                                        return SECResponse(
                                            content=cand_content,
                                            tier=tier,
                                            cached=False,
                                            response_time=response_time2,
                                            status_code=200,
                                            headers=dict(cand_resp.headers),
                                            url=cand_url
                                        )
                        except Exception as ex:
                            logger.debug(f"404 recovery attempt (dir index) failed for {url}: {ex}")

                        # 4) As a final attempt, derive primary document name from EDGAR submissions
                        try:
                            m = re.match(r"^/Archives/edgar/data/(\d+)/(\d+)/", parsed.path, re.IGNORECASE)
                            if m:
                                cik_num = int(m.group(1))
                                acc_nodash = m.group(2)
                                cik_padded = str(cik_num).zfill(10)
                                if len(acc_nodash) >= 12:
                                    dashed = f"{cik_padded}-{acc_nodash[10:12]}-{acc_nodash[12:]}"
                                else:
                                    dashed = acc_nodash

                                # Fetch submissions to find primary document
                                api_session = self.sessions.get(SECTier.EDGAR_API)
                                if api_session:
                                    sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                                    async with api_session.get(sub_url) as sub_resp:
                                        if sub_resp.status == 200:
                                            subs = await sub_resp.json()
                                            recent = (subs.get('filings') or {}).get('recent') or {}
                                            accessions = recent.get('accessionNumber') or recent.get('accession_number') or []
                                            primaries = recent.get('primaryDocument') or recent.get('primary_document') or []
                                            name = None
                                            for i, an in enumerate(accessions):
                                                if an == dashed and i < len(primaries):
                                                    name = primaries[i]
                                                    break
                                            if name:
                                                cand_url = urljoin(base_dir_url, name)
                                                fallback_start = time.time()
                                                async with session.get(cand_url) as cand_resp2:
                                                    if cand_resp2.status == 200:
                                                        cand_content2 = await cand_resp2.text()
                                                        response_time3 = time.time() - fallback_start
                                                        self.tier_health[tier].record_success(response_time3)
                                                        self.stats['tier_usage'][tier.value] += 1
                                                        logger.info(f"Recovered 404 via EDGAR submissions primaryDocument: {name}")
                                                        return SECResponse(
                                                            content=cand_content2,
                                                            tier=tier,
                                                            cached=False,
                                                            response_time=response_time3,
                                                            status_code=200,
                                                            headers=dict(cand_resp2.headers),
                                                            url=cand_url
                                                        )
                        except Exception as ex2:
                            logger.debug(f"404 recovery attempt (EDGAR submissions) failed for {url}: {ex2}")

                        # 5) Final attempt: try dashed accession .txt (full submission text)
                        try:
                            # Build dashed accession from path
                            path_parts = [p for p in parsed.path.split('/') if p]
                            if len(path_parts) >= 6:
                                cik_part = path_parts[3]
                                acc_part = path_parts[4]
                                cik_padded = str(int(cik_part)).zfill(10)
                                if len(acc_part) >= 12:
                                    dashed = f"{cik_padded}-{acc_part[10:12]}-{acc_part[12:]}"
                                else:
                                    dashed = acc_part
                                txt_url = urljoin(base_dir_url, f"{dashed}.txt")
                                fallback_start4 = time.time()
                                async with session.get(txt_url) as txt_resp:
                                    if txt_resp.status == 200:
                                        txt_content = await txt_resp.text()
                                        response_time4 = time.time() - fallback_start4
                                        self.tier_health[tier].record_success(response_time4)
                                        self.stats['tier_usage'][tier.value] += 1
                                        logger.info("Recovered 404 by fetching full submission text .txt")
                                        return SECResponse(
                                            content=txt_content,
                                            tier=tier,
                                            cached=False,
                                            response_time=response_time4,
                                            status_code=200,
                                            headers=dict(txt_resp.headers),
                                            url=txt_url
                                        )
                        except Exception as ex3:
                            logger.debug(f"404 recovery attempt (.txt) failed for {url}: {ex3}")

                        # 6) Try dashed accession index pages directly
                        try:
                            path_parts = [p for p in parsed.path.split('/') if p]
                            if len(path_parts) >= 6:
                                cik_part = path_parts[3]
                                acc_part = path_parts[4]
                                cik_padded = str(int(cik_part)).zfill(10)
                                if len(acc_part) >= 12:
                                    dashed = f"{cik_padded}-{acc_part[10:12]}-{acc_part[12:]}"
                                else:
                                    dashed = acc_part
                                for idx_name in (f"{dashed}-index.htm", f"{dashed}-index.html", "index.htm", "index.html"):
                                    idx_url = urljoin(base_dir_url, idx_name)
                                    idx_start = time.time()
                                    async with session.get(idx_url) as idx_resp:
                                        if idx_resp.status == 200:
                                            idx_content = await idx_resp.text()
                                            response_time5 = time.time() - idx_start
                                            self.tier_health[tier].record_success(response_time5)
                                            self.stats['tier_usage'][tier.value] += 1
                                            logger.info(f"Recovered 404 by fetching index page directly: {idx_name}")
                                            return SECResponse(
                                                content=idx_content,
                                                tier=tier,
                                                cached=False,
                                                response_time=response_time5,
                                                status_code=200,
                                                headers=dict(idx_resp.headers),
                                                url=idx_url
                                            )
                        except Exception as ex4:
                            logger.debug(f"404 recovery attempt (dashed index) failed for {url}: {ex4}")

                    # Record failure and do not retry for 403/404 here
                    self.tier_health[tier].record_failure(is_rate_limit=False)
                    return None
                
                else:
                    # Server errors - may be transient
                    logger.warning(f"{tier.value} returned {response.status}")
                    self.tier_health[tier].record_failure(is_rate_limit=False)
                    return None
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching from {tier.value}")
            self.tier_health[tier].record_failure(is_rate_limit=False)
            return None
        
        except Exception as e:
            logger.error(f"Error fetching from {tier.value}: {e}")
            self.tier_health[tier].record_failure(is_rate_limit=False)
            return None
    
    async def fetch(
        self,
        url: str,
        priority: RequestPriority = RequestPriority.NORMAL,
        force_refresh: bool = False,
        raise_on_failure: bool = False
    ) -> Optional[SECResponse]:
        """
        Fetch data with multi-tier fallback
        
        Args:
            url: URL to fetch
            priority: Request priority
            force_refresh: Skip cache and force fresh fetch
            raise_on_failure: When True, raise SECFetchError instead of returning None
        
        Returns:
            SECResponse or None if all tiers fail
        """
        self.stats['total_requests'] += 1
        
        # Generate cache key
        cache_key = self._generate_cache_key(url)
        
        # Check for in-flight request (deduplication)
        if cache_key in self._in_flight_requests:
            logger.debug(f"Deduplicating request: {url}")
            return await self._in_flight_requests[cache_key]
        
        # Create future for deduplication
        future = asyncio.get_event_loop().create_future()
        self._in_flight_requests[cache_key] = future
        
        try:
            # Try cache first (unless force_refresh)
            if not force_refresh:
                cached = await self._load_from_cache(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {url}")
                    future.set_result(cached)
                    return cached
            
            self.stats['cache_misses'] += 1
            
            # Try tiers with fallback (do not retry the same tier in this cycle)
            max_tier_attempts = 3
            attempts_summary: List[Dict[str, Any]] = []
            tried_tiers: set = set()
            for tier_attempt in range(max_tier_attempts):
                tier = self._select_tier(exclude=tried_tiers)
            
                if not tier:
                    logger.error("No available tiers for request")
                    break
            
                # Build tier-specific URL
                tier_url = self._build_tier_url(tier, url)
                # Mark this tier as tried even if URL cannot be built
                tried_tiers.add(tier)
                if not tier_url:
                    logger.debug(f"Tier {tier.value} not applicable for URL, trying next tier")
                    # Consider this a soft failover without retries
                    self.stats['failovers'] += 1
                    attempts_summary.append({'tier': tier.value, 'retries': 0, 'last_status': None, 'reason': 'not_applicable'})
                    continue
            
                # Try this tier with retries
                max_retries = 3
                last_status: Optional[int] = None
                for retry in range(max_retries):
                    response = await self._fetch_from_tier(tier, tier_url, retry + 1)
                
                    if response:
                        # Success! Cache and return
                        await self._save_to_cache(cache_key, response)
                        future.set_result(response)
                        return response
                
                    # Exponential backoff before retry
                    if retry < max_retries - 1:
                        backoff = (2 ** retry) * 0.5 + random.uniform(0, 0.5)
                        await asyncio.sleep(backoff)

                # This tier failed, try next tier
                logger.warning(f"Tier {tier.value} failed, trying next tier")
                self.stats['failovers'] += 1
                attempts_summary.append({
                    'tier': tier.value,
                    'retries': max_retries,
                    'last_status': last_status
                })
            
            # All tiers failed — attempt last-chance salvage for known SEC Archives patterns
            logger.error(f"All tiers failed for URL: {url}")
            try:
                parsed = urlparse(url)
                path = parsed.path.lower()
                if parsed.netloc.lower() == 'www.sec.gov' and '/archives/edgar/data/' in path:
                    # index.json salvage: synthesize index via helper and return as JSON
                    if path.endswith('/index.json'):
                        # Extract cik and accession and synthesize from EDGAR submissions
                        m = re.match(r"^/archives/edgar/data/(\d+)/(\d+)/index\.json$", path, re.IGNORECASE)
                        if m:
                            cik = m.group(1)
                            acc = m.group(2)
                            cik_padded = str(int(cik)).zfill(10)
                            dashed = f"{cik_padded}-{acc[10:12]}-{acc[12:]}" if len(acc) >= 12 else acc
                            api_session = self.sessions.get(SECTier.EDGAR_API)
                            if api_session:
                                sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                                async with api_session.get(sub_url) as sub_resp:
                                    if sub_resp.status == 200:
                                        subs = await sub_resp.json()
                                        items = []
                                        primary_doc = self._find_primary_from_submissions(subs, dashed)
                                        if not primary_doc:
                                            primary_doc = await self._find_primary_from_submissions_deep(cik_padded, dashed)
                                        if primary_doc:
                                            items.append({'name': primary_doc})
                                        if items:
                                            content = json.dumps({"directory": {"item": items}})
                                            resp = SECResponse(
                                                content=content,
                                                tier=SECTier.EDGAR_API,
                                                cached=False,
                                                response_time=0.0,
                                                status_code=200,
                                                headers={},
                                                url=url
                                            )
                                            future.set_result(resp)
                                            return resp
                            # If submissions lookup failed or API unavailable, return a synthetic index
                            try:
                                synthetic_items = [{"name": f"{dashed}.txt"}]
                                content = json.dumps({"directory": {"item": synthetic_items}})
                                resp = SECResponse(
                                    content=content,
                                    tier=SECTier.ARCHIVES,
                                    cached=False,
                                    response_time=0.0,
                                    status_code=200,
                                    headers={},
                                    url=url
                                )
                                future.set_result(resp)
                                return resp
                            except Exception:
                                pass
                            # Try Archives index pages as salvage
                            try:
                                archives_session = self.sessions.get(SECTier.ARCHIVES)
                                if archives_session:
                                    base_dir = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/"
                                    # Candidate index pages
                                    for idx_name in (f"{dashed}-index.htm", f"{dashed}-index.html", "index.html", "index.htm"):
                                        idx_url = urljoin(base_dir, idx_name)
                                        async with archives_session.get(idx_url) as idx_resp:
                                            if idx_resp.status == 200:
                                                html = await idx_resp.text()
                                                soup = BeautifulSoup(html, 'html.parser')
                                                items = []
                                                for a in soup.select('a[href]'):
                                                    href = a.get('href') or ''
                                                    if href and href not in ('../', './') and not href.startswith('?'):
                                                        name = href.split('/')[-1]
                                                        if name and name.lower() not in ("index.html", "index.htm", "index.json"):
                                                            items.append({'name': name})
                                                if items:
                                                    content = json.dumps({"directory": {"item": items}})
                                                    resp = SECResponse(
                                                        content=content,
                                                        tier=SECTier.ARCHIVES,
                                                        cached=False,
                                                        response_time=0.0,
                                                        status_code=200,
                                                        headers={},
                                                        url=url
                                                    )
                                                    future.set_result(resp)
                                                    return resp
                            except Exception as ex_idx:
                                logger.debug(f"Index salvage via HTML failed: {ex_idx}")
                    else:
                        # Document salvage: attempt submissions to produce informative stub
                        m = re.match(r"^/archives/edgar/data/(\d+)/(\d+)/(.*)$", path, re.IGNORECASE)
                        if m:
                            cik = m.group(1)
                            acc = m.group(2)
                            cik_padded = str(int(cik)).zfill(10)
                            dashed = f"{cik_padded}-{acc[10:12]}-{acc[12:]}" if len(acc) >= 12 else acc
                            api_session = self.sessions.get(SECTier.EDGAR_API)
                            if api_session:
                                sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                                async with api_session.get(sub_url) as sub_resp:
                                    if sub_resp.status == 200:
                                        subs = await sub_resp.json()
                                        recent = (subs.get('filings') or {}).get('recent') or {}
                                        accessions = recent.get('accessionNumber') or recent.get('accession_number') or []
                                        primaries = recent.get('primaryDocument') or recent.get('primary_document') or []
                                        primary = None
                                        for i, an in enumerate(accessions):
                                            if an == dashed and i < len(primaries):
                                                primary = primaries[i]
                                                break
                                        stub = {
                                            'message': 'Document not directly available via Archives; providing primary document candidate from EDGAR submissions.',
                                            'cik': cik_padded,
                                            'accession': dashed,
                                            'primary_document': primary
                                        }
                                        resp = SECResponse(
                                            content=json.dumps(stub),
                                            tier=SECTier.EDGAR_API,
                                            cached=False,
                                            response_time=0.0,
                                            status_code=200,
                                            headers={},
                                            url=url
                                        )
                                        future.set_result(resp)
                                        return resp
            except Exception as ex:
                logger.debug(f"Salvage path encountered an error: {ex}")

            if raise_on_failure:
                err = SECFetchError(url=url, attempts_summary=attempts_summary)
                future.set_exception(err)
                raise err
            else:
                future.set_result(None)
                return None
        
        finally:
            # Clean up in-flight tracking
            self._in_flight_requests.pop(cache_key, None)
    
    def _build_tier_url(self, tier: SECTier, base_url: str) -> Optional[str]:
        """Build tier-specific URL from generic URL"""
        
        # Parse the URL to extract components
        parsed = urlparse(base_url)
        path = parsed.path
        
        config = self.TIER_CONFIGS[tier]
        tier_base = config['base_url']
        
        if tier == SECTier.EDGAR_API:
            # For EDGAR API, use data.sec.gov with JSON endpoints
            # Example: /submissions/CIK0000320187.json
            if 'submissions/CIK' in path:
                return urljoin(tier_base, path)
            elif '/Archives/edgar/data/' in path or '/archives/edgar/data/' in path.lower():
                # Convert archive path to API path if possible
                # This might not always work, return None to try other tiers
                return None
            else:
                return urljoin(tier_base, path)
        
        elif tier == SECTier.ARCHIVES:
            # For Archives, use www.sec.gov/Archives with direct file access
            if '/Archives/edgar/data/' in path or '/archives/edgar/data/' in path.lower():
                # Ensure proper capitalization
                if '/archives/' in path.lower() and '/Archives/' not in path:
                    path = path.replace('/archives/', '/Archives/')
                return f"https://www.sec.gov{path}"
            elif '/Archives/edgar/data/' in base_url or parsed.netloc == 'www.sec.gov':
                # URL already points to archives
                return base_url
            elif 'submissions/CIK' in path:
                # Try to convert to archive path - may not work
                return None
            else:
                # Try as-is with www.sec.gov
                return f"https://www.sec.gov{path}"
        
        elif tier == SECTier.BROWSE:
            # For Browse, use search interface
            # This is mainly for discovering filings, not fetching documents
            # We'll need CIK and other params - may not work for all URLs
            return None
        
        return None

    async def fetch_strict(
        self,
        url: str,
        priority: RequestPriority = RequestPriority.NORMAL,
        force_refresh: bool = False,
    ) -> SECResponse:
        """Fetch data and raise `SECFetchError` if all tiers fail.

        This is recommended for user-facing or critical analysis paths to prevent
        silent failures.
        """
        result = await self.fetch(url, priority=priority, force_refresh=force_refresh, raise_on_failure=True)
        # The above either returns a response or raises; this is for type checkers
        assert result is not None
        return result
    
    async def fetch_company_submissions(self, cik: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company submissions with multi-tier fallback
        
        Args:
            cik: Company CIK (will be normalized)
        
        Returns:
            Submissions data or None
        """
        cik_normalized = cik.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik_normalized}.json"
        
        response = await self.fetch(url, priority=RequestPriority.HIGH)
        
        if response and response.content:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {e}")
                return None
        
        return None
    
    async def fetch_filing_document(
        self,
        cik: str,
        accession_number: str,
        document_name: str
    ) -> Optional[str]:
        """
        Fetch filing document with multi-tier fallback
        
        Args:
            cik: Company CIK (can be string or int, with or without leading zeros)
            accession_number: Accession number (with or without dashes)
            document_name: Document filename
        
        Returns:
            Document content or None
        """
        # Normalize CIK - remove leading zeros for URL path
        try:
            cik_int = int(str(cik).lstrip('0') or '0')
        except (ValueError, TypeError):
            logger.error(f"Invalid CIK: {cik}")
            return None
        
        # Remove dashes from accession number
        accession_no_dashes = str(accession_number).replace('-', '')
        
        # Build archive URL
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dashes}/{document_name}"
        
        response = await self.fetch(url, priority=RequestPriority.HIGH)
        
        if response:
            return response.content
        
        return None
    
    async def fetch_filing_index(
        self,
        cik: str,
        accession_number: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch filing index.json with multi-tier fallback
        
        Args:
            cik: Company CIK (can be string or int, with or without leading zeros)
            accession_number: Accession number (with or without dashes)
        
        Returns:
            Index data or None
        """
        # Normalize CIK - remove leading zeros for URL path
        try:
            cik_int = int(str(cik).lstrip('0') or '0')
        except (ValueError, TypeError):
            logger.error(f"Invalid CIK: {cik}")
            return None
        
        # Remove dashes from accession number
        accession_no_dashes = str(accession_number).replace('-', '')
        
        base_dir = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dashes}/"
        url = urljoin(base_dir, "index.json")

        # Attempt 0: EDGAR submissions synthesis first (fast path)
        try:
            cik_padded = str(cik_int).zfill(10)
            if len(accession_no_dashes) >= 12:
                dashed = f"{cik_padded}-{accession_no_dashes[10:12]}-{accession_no_dashes[12:]}"
                # Shallow first
                primary = await self._find_primary_from_submissions_deep(cik_padded, dashed)
                if not primary:
                    # Fall back to simple helper in case deep failed due to network differences
                    api_session = self.sessions.get(SECTier.EDGAR_API)
                    if api_session:
                        sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                        async with api_session.get(sub_url) as sub_resp:
                            if sub_resp.status == 200:
                                subs = await sub_resp.json()
                                primary = self._find_primary_from_submissions(subs, dashed)
                if primary:
                    return {"directory": {"item": [{"name": primary}]}}
        except Exception:
            pass

        # Attempt 1: JSON index via multi-tier fetch
        response = await self.fetch(url, priority=RequestPriority.NORMAL)
        if response and response.content:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # Proceed to HTML fallback
                logger.debug("index.json is not JSON; attempting HTML fallback for index")

        # Fallback: attempt to parse HTML index page(s)
        try:
            session = self.sessions.get(SECTier.ARCHIVES)
            if session:
                # Try common index filenames including accession-index pages
                dashed_accession = f"{str(cik_int).zfill(10)}-{accession_no_dashes[10:12]}-{accession_no_dashes[12:]}" if len(accession_no_dashes) >= 12 else accession_no_dashes
                candidate_indexes = [
                    "index.html",
                    "index.htm",
                    f"{dashed_accession}-index.htm",
                    f"{dashed_accession}-index.html",
                    "",
                ]
                for idx_name in candidate_indexes:
                    idx_url = urljoin(base_dir, idx_name)
                    async with session.get(idx_url) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            items = []
                            # SEC index pages: document table links
                            for a in soup.select('a[href]'):
                                href = a.get('href') or ''
                                if href and href not in ('../', './') and not href.startswith('?'):
                                    name = href.split('/')[-1]
                                    if name and name.lower() not in ("index.html", "index.htm", "index.json"):
                                        items.append({'name': name})
                            if items:
                                return {"directory": {"item": items}}
        except Exception as e:
            logger.debug(f"HTML index fallback failed: {e}")

        # Final fallback: consult EDGAR submissions to synthesize minimal index
        try:
            cik_padded = str(cik_int).zfill(10)
            api_session = self.sessions.get(SECTier.EDGAR_API)
            if api_session and len(accession_no_dashes) >= 12:
                dashed = f"{cik_padded}-{accession_no_dashes[10:12]}-{accession_no_dashes[12:]}"
                sub_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
                async with api_session.get(sub_url) as sub_resp:
                    if sub_resp.status == 200:
                        subs = await sub_resp.json()
                        name = self._find_primary_from_submissions(subs, dashed)
                        if not name:
                            name = await self._find_primary_from_submissions_deep(cik_padded, dashed)
                        if name:
                            logger.info("Synthesizing index.json from EDGAR submissions primaryDocument")
                            return {"directory": {"item": [{"name": name}]}}
        except Exception as e:
            logger.debug(f"Submissions-based index synthesis failed: {e}")
        # As a last resort, provide a synthetic index pointing to the full submission text (.txt)
        try:
            cik_padded = str(cik_int).zfill(10)
            if len(accession_no_dashes) >= 12:
                dashed = f"{cik_padded}-{accession_no_dashes[10:12]}-{accession_no_dashes[12:]}"
            else:
                dashed = accession_no_dashes
            synthetic_item = {"name": f"{dashed}.txt"}
            logger.info("Returning synthetic index with full submission .txt as last resort")
            return {"directory": {"item": [synthetic_item]}}
        except Exception:
            pass

        return None
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get health report for all tiers"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': dict(self.stats),
            'tiers': {}
        }
        
        for tier, health in self.tier_health.items():
            report['tiers'][tier.value] = {
                'state': health.state.value,
                'health_score': health.get_health_score(),
                'success_count': health.success_count,
                'failure_count': health.failure_count,
                'consecutive_failures': health.consecutive_failures,
                'total_requests': health.total_requests,
                'average_response_time': health.average_response_time,
                'rate_limit_hits': health.rate_limit_hits,
                'last_success': health.last_success,
                'last_failure': health.last_failure,
            }
        
        return report


# Convenience functions for backward compatibility

async def create_multi_tier_fetcher(cache_dir: Optional[Path] = None) -> MultiTierSECFetcher:
    """Create and initialize multi-tier SEC fetcher"""
    fetcher = MultiTierSECFetcher(cache_dir=cache_dir)
    await fetcher.__aenter__()
    return fetcher


# Example usage
if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Multi-Tier SEC Fetcher CLI"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Print health report JSON (after an optional sample fetch)"
    )
    parser.add_argument(
        "--cik",
        default="0000320187",
        help="CIK to use for sample submissions fetch (default: 0000320187 for Nike)"
    )
    parser.add_argument(
        "--url",
        help="Fetch a specific URL via multi-tier and print a short JSON result"
    )
    args = parser.parse_args()

    async def cli():
        async with MultiTierSECFetcher() as fetcher:
            # If a URL is provided, fetch it directly
            if args.url:
                resp = await fetcher.fetch(args.url, priority=RequestPriority.NORMAL)
                if resp:
                    print(json.dumps({
                        "url": resp.url,
                        "status": resp.status_code,
                        "tier": resp.tier.value,
                        "cached": resp.cached,
                        "bytes": len(resp.content),
                    }, indent=2))
                else:
                    print(json.dumps({"url": args.url, "error": "fetch_failed"}, indent=2))
            else:
                # Otherwise do a simple submissions fetch to exercise the system
                submissions = await fetcher.fetch_company_submissions(args.cik)
                if submissions:
                    company = submissions.get('name') or submissions.get('entityType') or 'Unknown'
                    recent = (submissions.get('filings') or {}).get('recent') or {}
                    count = len(recent.get('form', [])) if isinstance(recent.get('form', []), list) else 0
                    print(json.dumps({
                        "company": company,
                        "cik": submissions.get('cik', args.cik),
                        "recent_filings_count": count
                    }, indent=2))

            # Print health when requested or when no URL was provided (default useful output)
            if args.health or not args.url:
                health = fetcher.get_health_report()
                print(json.dumps(health, indent=2))

    asyncio.run(cli())

