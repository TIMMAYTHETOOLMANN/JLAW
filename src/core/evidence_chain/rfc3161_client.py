"""
RFC 3161 Timestamp Client
=========================

Provides cryptographic timestamps for evidence chain.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import time


@dataclass
class TimestampToken:
    """RFC 3161 Timestamp Token."""
    token_data: bytes
    gen_time: datetime
    hash_algorithm: str
    message_imprint: str
    authority: str
    
    def to_dict(self):
        return {
            "gen_time": self.gen_time.isoformat(),
            "hash_algorithm": self.hash_algorithm,
            "message_imprint": self.message_imprint,
            "authority": self.authority
        }


class RFC3161Client:
    """RFC 3161 timestamp client."""
    
    AUTHORITIES = {
        "digicert": "http://timestamp.digicert.com",
        "local": "local"
    }
    
    def __init__(self, authority: str = "local"):
        self.authority = authority
    
    @staticmethod
    def create_local_timestamp(data: bytes, authority: str = "local") -> TimestampToken:
        """Create local timestamp (development only)."""
        data_hash = hashlib.sha256(data).hexdigest()
        
        return TimestampToken(
            token_data=f"LOCAL_TS_{data_hash[:16]}".encode(),
            gen_time=datetime.utcnow(),
            hash_algorithm="SHA-256",
            message_imprint=data_hash,
            authority=authority
        )

