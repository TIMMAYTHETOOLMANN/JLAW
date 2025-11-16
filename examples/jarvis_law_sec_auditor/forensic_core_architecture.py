"""
NITS Forensic Document Analysis Platform - Core Architecture
Zero-tolerance cryptographic integrity with full USC/CFR statute mapping
"""

import hashlib
import hmac
import json
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import deque
import logging
from functools import wraps
import boto3
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
import redis
from kafka import KafkaProducer, KafkaConsumer
import numpy as np
from scipy import stats

# Configure structured logging for forensic audit trails
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('forensic_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('NITS_FORENSIC')

# Critical System Constants
MAX_RETRY_ATTEMPTS = 5
BASE_RETRY_DELAY = 1.0  # seconds
MAX_BACKOFF_DELAY = 64.0  # seconds
CIRCUIT_BREAKER_THRESHOLD = 0.5  # 50% failure rate
CIRCUIT_BREAKER_WINDOW = 10  # requests
CIRCUIT_BREAKER_TIMEOUT = 30  # seconds
SEC_RATE_LIMIT = 10  # requests per second
GOVINFO_RATE_LIMIT = 0.28  # requests per second (1000/hour)
HASH_ALGORITHM = hashlib.sha256
EVIDENCE_RETENTION_DAYS = 2555  # 7 years

class ViolationType(Enum):
    """USC/CFR violation classifications for enforcement priorities"""
    # 15 USC - Securities Laws
    USC_15_77g = "Securities Act Registration Violation"
    USC_15_78j_b = "Anti-Fraud Provision (Rule 10b-5)"
    USC_15_78m = "Periodic Reporting Requirements"
    
    # 17 CFR - SEC Regulations
    CFR_17_229_303 = "MD&A Deficiency"
    CFR_17_210 = "Regulation S-X Financial Statement Violation"
    CFR_17_240_10b5 = "Rule 10b-5 Fraud"
    CFR_17_240_12b25 = "Late Filing Notification Failure"
    
    # 18 USC - Criminal Provisions
    USC_18_1001 = "False Statements (5 years)"
    USC_18_1341 = "Mail Fraud (20 years)"
    USC_18_1343 = "Wire Fraud (20 years)"
    USC_18_1348 = "Securities Fraud (25 years)"
    USC_18_1350 = "CEO/CFO Certification Failure (20 years)"
    USC_18_1519 = "Document Destruction (20 years)"
    
    # 26 USC - Tax Code
    USC_26_6103 = "Tax Disclosure Violation"
    
    # 31 USC - Bank Secrecy Act
    USC_31_5322 = "BSA Criminal Violation (10 years)"
    
    # 12 USC - Banking
    USC_12_1817 = "Bank Reporting Violation"

class HardFailureException(Exception):
    """Critical failure requiring system halt for evidence integrity"""
    def __init__(self, code: str, message: str, evidence_hash: Optional[str] = None):
        self.code = code
        self.message = message
        self.evidence_hash = evidence_hash
        self.timestamp = datetime.utcnow().isoformat()
        super().__init__(f"HARD_FAILURE [{code}]: {message}")

@dataclass
class ChainOfCustody:
    """Immutable chain of custody for courtroom admissibility (FRE 902)"""
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str = ""
    collected_by: Dict[str, str] = field(default_factory=dict)
    initial_hash: str = ""
    custody_chain: List[Dict] = field(default_factory=list)
    hash_chain: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def add_transfer(self, from_party: str, to_party: str, method: str) -> str:
        """Add custody transfer with cryptographic verification"""
        transfer = {
            "sequence": len(self.custody_chain) + 1,
            "from": from_party,
            "to": to_party,
            "method": method,
            "timestamp": datetime.utcnow().isoformat(),
            "verification_hash": self._compute_transfer_hash()
        }
        self.custody_chain.append(transfer)
        return transfer["verification_hash"]
    
    def _compute_transfer_hash(self) -> str:
        """Compute SHA-256 hash of custody state"""
        state = json.dumps({
            "evidence_id": self.evidence_id,
            "chain_length": len(self.custody_chain),
            "last_hash": self.hash_chain[-1] if self.hash_chain else self.initial_hash
        }, sort_keys=True)
        return HASH_ALGORITHM(state.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify complete chain integrity for court admissibility"""
        if not self.initial_hash:
            raise HardFailureException("501-001-01", "Missing initial hash")
        
        for i, transfer in enumerate(self.custody_chain):
            expected_hash = self._compute_transfer_hash()
            if transfer["verification_hash"] != expected_hash:
                raise HardFailureException(
                    "501-002-01",
                    f"Chain broken at sequence {i+1}",
                    transfer["verification_hash"]
                )
        return True

class BlockchainAuditTrail:
    """Blockchain-style immutable audit trail for forensic integrity"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.chain_key = "forensic:audit:chain"
        self._initialize_genesis()
    
    def _initialize_genesis(self):
        """Create genesis block if not exists"""
        if not self.redis.exists(f"{self.chain_key}:0"):
            genesis = {
                "sequence": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "data": "GENESIS_BLOCK",
                "previous_hash": "0" * 64,
                "current_hash": ""
            }
            genesis["current_hash"] = self._compute_hash(genesis)
            self.redis.hset(f"{self.chain_key}:0", mapping=genesis)
            self.redis.set(f"{self.chain_key}:length", 1)
    
    def add_entry(self, event_type: str, data: Dict) -> str:
        """Add immutable entry to audit chain"""
        length = int(self.redis.get(f"{self.chain_key}:length"))
        previous_block = self.redis.hgetall(f"{self.chain_key}:{length-1}")
        previous_hash = previous_block[b'current_hash'].decode()
        
        entry = {
            "sequence": length,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": json.dumps(data, sort_keys=True),
            "previous_hash": previous_hash,
            "current_hash": ""
        }
        entry["current_hash"] = self._compute_hash(entry)
        
        # Atomic operation to prevent race conditions
        pipe = self.redis.pipeline()
        pipe.hset(f"{self.chain_key}:{length}", mapping=entry)
        pipe.incr(f"{self.chain_key}:length")
        pipe.execute()
        
        return entry["current_hash"]
    
    def _compute_hash(self, block: Dict) -> str:
        """Compute SHA-256 hash of block content"""
        content = json.dumps({
            k: v for k, v in block.items() if k != "current_hash"
        }, sort_keys=True)
        return HASH_ALGORITHM(content.encode()).hexdigest()
    
    def verify_chain(self) -> bool:
        """Verify entire chain integrity"""
        length = int(self.redis.get(f"{self.chain_key}:length"))
        
        for i in range(length):
            block = {k.decode(): v.decode() for k, v in
                     self.redis.hgetall(f"{self.chain_key}:{i}").items()}
            
            # Verify current hash
            computed = self._compute_hash(block)
            if block["current_hash"] != computed:
                raise HardFailureException(
                    "500-001-01",
                    f"Hash mismatch at block {i}",
                    block["current_hash"]
                )
            
            # Verify chain linkage
            if i > 0:
                prev_block = {k.decode(): v.decode() for k, v in
                              self.redis.hgetall(f"{self.chain_key}:{i-1}").items()}
                if block["previous_hash"] != prev_block["current_hash"]:
                    raise HardFailureException(
                        "500-002-01",
                        f"Chain broken between blocks {i-1} and {i}"
                    )
        
        return True

class CircuitBreaker:
    """Circuit breaker pattern preventing cascade failures"""
    
    class State(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"
    
    def __init__(self, failure_threshold: float = CIRCUIT_BREAKER_THRESHOLD,
                 window_size: int = CIRCUIT_BREAKER_WINDOW,
                 timeout: int = CIRCUIT_BREAKER_TIMEOUT):
        self.failure_threshold = failure_threshold
        self.window_size = window_size
        self.timeout = timeout
        self.state = self.State.CLOSED
        self.failures = deque(maxlen=window_size)
        self.last_failure_time = None
        self.half_open_attempts = 0
    
    def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker"""
        if self.state == self.State.OPEN:
            if self._should_attempt_reset():
                self.state = self.State.HALF_OPEN
                self.half_open_attempts = 0
            else:
                raise Exception(f"Circuit breaker OPEN until {self.last_failure_time + timedelta(seconds=self.timeout)}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == self.State.HALF_OPEN:
            self.half_open_attempts += 1
            if self.half_open_attempts >= 3:
                self.state = self.State.CLOSED
                self.failures.clear()
        elif self.state == self.State.CLOSED:
            self.failures.append(0)
    
    def _on_failure(self):
        """Handle failed call"""
        self.failures.append(1)
        self.last_failure_time = datetime.utcnow()
        
        if self.state == self.State.HALF_OPEN:
            self.state = self.State.OPEN
        elif self.state == self.State.CLOSED:
            if len(self.failures) >= self.window_size:
                failure_rate = sum(self.failures) / len(self.failures)
                if failure_rate >= self.failure_threshold:
                    self.state = self.State.OPEN
                    logger.warning(f"Circuit breaker opened: {failure_rate:.2%} failure rate")
    
    def _should_attempt_reset(self) -> bool:
        """Check if timeout expired for reset attempt"""
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.timeout

class RateLimiter:
    """Token bucket rate limiter for API compliance"""
    
    def __init__(self, rate: float, capacity: Optional[int] = None):
        self.rate = rate  # tokens per second
        self.capacity = capacity or rate
        self.tokens = self.capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """Acquire tokens, returning wait time if needed"""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            wait_time = (tokens - self.tokens) / self.rate
            return wait_time

class ForensicAPIClient:
    """Resilient API client with forensic-grade error handling"""
    
    def __init__(self, audit_trail: BlockchainAuditTrail):
        self.audit = audit_trail
        self.sec_limiter = RateLimiter(SEC_RATE_LIMIT)
        self.govinfo_limiter = RateLimiter(GOVINFO_RATE_LIMIT)
        self.circuit_breakers = {}
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "NITS-Forensic-Platform forensic@nits.ai",
                "X-Request-ID": str(uuid.uuid4()),
                "X-Forensic-Classification": "CRITICAL"
            },
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_with_retry(self, url: str, service: str = "sec") -> Dict:
        """Fetch with exponential backoff and circuit breaker"""
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = CircuitBreaker()
        
        limiter = self.sec_limiter if service == "sec" else self.govinfo_limiter
        wait_time = await limiter.acquire()
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                response = await self.circuit_breakers[service].call(
                    self._make_request, url
                )
                
                # Audit successful fetch
                self.audit.add_entry("API_FETCH_SUCCESS", {
                    "url": url,
                    "service": service,
                    "attempt": attempt + 1,
                    "status": response.status
                })
                
                return response
                
            except Exception as e:
                # Calculate exponential backoff with jitter
                delay = min(
                    MAX_BACKOFF_DELAY,
                    BASE_RETRY_DELAY * (2 ** attempt) + np.random.uniform(-1, 1)
                )
                
                logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay:.2f}s")
                
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(delay)
                else:
                    # Final failure - log to audit trail
                    self.audit.add_entry("API_FETCH_FAILURE", {
                        "url": url,
                        "service": service,
                        "attempts": MAX_RETRY_ATTEMPTS,
                        "error": str(e)
                    })
                    raise
    
    async def _make_request(self, url: str) -> Dict:
        """Make HTTP request with integrity verification"""
        request_id = str(uuid.uuid4())
        
        async with self.session.get(url, headers={"X-Request-ID": request_id}) as response:
            if response.status == 429:
                raise Exception("Rate limit exceeded")
            elif response.status == 503:
                retry_after = int(response.headers.get("Retry-After", 30))
                raise Exception(f"Service unavailable, retry after {retry_after}s")
            elif response.status >= 400:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
            
            content = await response.read()
            
            # Compute content hash for integrity
            content_hash = HASH_ALGORITHM(content).hexdigest()
            
            return {
                "status": response.status,
                "headers": dict(response.headers),
                "content": content,
                "content_hash": content_hash,
                "request_id": request_id
            }

