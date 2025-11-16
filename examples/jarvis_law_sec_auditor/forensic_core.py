"""
JARVIS:LAW Black Site Protocol - Enhanced Forensic Core
Integrated from comprehensive SEC fraud detection framework
Zero-tolerance cryptographic integrity with statute mapping
"""

import hashlib
import hmac
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import deque
import logging
import numpy as np
from scipy import stats

# Configure forensic audit logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('memory/forensic_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('JARVIS_FORENSIC')

# Critical System Constants
MAX_RETRY_ATTEMPTS = 5
BASE_RETRY_DELAY = 1.0
MAX_BACKOFF_DELAY = 64.0
CIRCUIT_BREAKER_THRESHOLD = 0.5
CIRCUIT_BREAKER_WINDOW = 10
CIRCUIT_BREAKER_TIMEOUT = 30
SEC_RATE_LIMIT = 10
GOVINFO_RATE_LIMIT = 0.28
HASH_ALGORITHM = hashlib.sha256
EVIDENCE_RETENTION_DAYS = 2555  # 7 years

class ViolationType(Enum):
    """USC/CFR violation classifications"""
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

@dataclass
class StatuteReference:
    """Legal statute reference with enforcement details"""
    title: int
    section: str
    subsection: Optional[str] = None
    usc_or_cfr: str = "USC"
    description: str = ""
    criminal_penalty: Optional[str] = None
    civil_penalty: Optional[str] = None
    enforcement_priority: int = 1  # 1=highest, 5=lowest
    
    @property
    def citation(self) -> str:
        """Format legal citation"""
        if self.subsection:
            return f"{self.title} {self.usc_or_cfr} § {self.section}({self.subsection})"
        return f"{self.title} {self.usc_or_cfr} § {self.section}"

class StatuteMapper:
    """Maps violations to specific USC/CFR statutes"""
    
    STATUTES = {
        # 15 USC - Securities Laws
        ViolationType.USC_15_77g: StatuteReference(
            15, "77g", None, "USC",
            "Securities Act Registration Requirements",
            criminal_penalty="5 years",
            civil_penalty="Disgorgement + penalties",
            enforcement_priority=2
        ),
        ViolationType.USC_15_78j_b: StatuteReference(
            15, "78j", "b", "USC",
            "Anti-fraud provisions (Rule 10b-5 authority)",
            criminal_penalty="20 years",
            civil_penalty="Treble damages",
            enforcement_priority=1
        ),
        ViolationType.USC_15_78m: StatuteReference(
            15, "78m", None, "USC",
            "Periodic reporting requirements (10-K, 10-Q, 8-K)",
            criminal_penalty="10 years",
            civil_penalty="$100,000-$1,000,000",
            enforcement_priority=2
        ),
        
        # 17 CFR - SEC Regulations
        ViolationType.CFR_17_229_303: StatuteReference(
            17, "229.303", None, "CFR",
            "MD&A requirements (Regulation S-K Item 303)",
            criminal_penalty=None,
            civil_penalty="Cease-and-desist + penalties",
            enforcement_priority=3
        ),
        ViolationType.CFR_17_240_10b5: StatuteReference(
            17, "240.10b-5", None, "CFR",
            "Employment of manipulative and deceptive devices",
            criminal_penalty="25 years (via 18 USC 1348)",
            civil_penalty="Disgorgement + treble damages",
            enforcement_priority=1
        ),
        
        # 18 USC - Criminal Statutes
        ViolationType.USC_18_1348: StatuteReference(
            18, "1348", None, "USC",
            "Securities fraud (Sarbanes-Oxley)",
            criminal_penalty="25 years",
            civil_penalty="Restitution + forfeiture",
            enforcement_priority=1
        ),
        ViolationType.USC_18_1350: StatuteReference(
            18, "1350", None, "USC",
            "CEO/CFO certification violations",
            criminal_penalty="10 years knowing, 20 years willful",
            civil_penalty="$1M-$5M fines",
            enforcement_priority=1
        ),
    }
    
    @classmethod
    def get_statute(cls, violation_type: ViolationType) -> StatuteReference:
        """Retrieve statute reference for violation type"""
        return cls.STATUTES.get(violation_type)
    
    @classmethod
    def get_criminal_statutes(cls) -> List[StatuteReference]:
        """Get all criminal statute references"""
        return [s for s in cls.STATUTES.values() if s.criminal_penalty]

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

# Export key components
__all__ = [
    'ViolationType',
    'HardFailureException',
    'ChainOfCustody',
    'StatuteReference',
    'StatuteMapper',
    'CircuitBreaker',
    'logger'
]

