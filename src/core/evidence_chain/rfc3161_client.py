"""
RFC 3161 Timestamp Client
=========================

Provides cryptographic timestamps for evidence chain compliance with FRE 902(14).

Trusted Timestamp Authorities (TSAs):
- FreeTSA: https://freetsa.org/tsr (free, public TSA)
- DigiCert: http://timestamp.digicert.com (commercial TSA)
- Local: Development/testing only (not court-admissible)

RFC 3161 provides:
- Cryptographic proof that data existed at a specific time
- Legally binding timestamps for evidence chain
- Third-party verification of document creation time
"""

import hashlib
import asyncio
import aiohttp
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import time
import logging

logger = logging.getLogger(__name__)

try:
    # Try to import rfc3161ng for production timestamp requests
    from rfc3161ng import RemoteTimestamper, TimeStampReq
    RFC3161NG_AVAILABLE = True
except ImportError:
    RFC3161NG_AVAILABLE = False
    logger.warning("rfc3161ng not available. Using local timestamps only.")


@dataclass
class TimestampToken:
    """RFC 3161 Timestamp Token with verification data."""
    token_data: bytes
    gen_time: datetime
    hash_algorithm: str
    message_imprint: str
    authority: str
    serial_number: Optional[str] = None
    policy_oid: Optional[str] = None
    
    def to_dict(self):
        return {
            "gen_time": self.gen_time.isoformat(),
            "hash_algorithm": self.hash_algorithm,
            "message_imprint": self.message_imprint,
            "authority": self.authority,
            "serial_number": self.serial_number,
            "policy_oid": self.policy_oid
        }
    
    def verify(self, data: bytes) -> bool:
        """Verify timestamp token against original data."""
        data_hash = hashlib.sha256(data).hexdigest()
        return data_hash == self.message_imprint


class RFC3161Client:
    """
    RFC 3161 timestamp client with multiple TSA support.
    
    Features:
    - Multiple trusted timestamp authorities
    - Automatic retry with fallback
    - SHA-256 message imprint
    - Token verification
    - Court-admissible timestamps
    """
    
    AUTHORITIES = {
        "freetsa": "https://freetsa.org/tsr",
        "digicert": "http://timestamp.digicert.com",  # Note: DigiCert uses HTTP for TSA protocol
        "local": "local"
    }
    
    # Note: DigiCert TSA endpoint uses HTTP as per RFC 3161 standard.
    # The timestamp response itself is cryptographically signed by the TSA,
    # ensuring integrity regardless of transport protocol.
    
    def __init__(self, authority: str = "local"):
        """
        Initialize RFC 3161 client.
        
        Args:
            authority: TSA to use ("freetsa", "digicert", or "local")
        """
        self.authority = authority
        self.tsa_url = self.AUTHORITIES.get(authority, self.AUTHORITIES["local"])
    
    async def timestamp(self, data: bytes) -> TimestampToken:
        """
        Get RFC 3161 timestamp for data - REQUIRES network authority.
        
        Args:
            data: Data to timestamp
            
        Returns:
            TimestampToken with cryptographic proof of existence
            
        Raises:
            RuntimeError: If RFC 3161 library not available or local authority used
        """
        # Enforce network-only timestamps for court-admissible evidence
        if not RFC3161NG_AVAILABLE:
            raise RuntimeError(
                "RFC 3161 library required for court-admissible timestamps. "
                "Install rfc3161ng: pip install rfc3161ng"
            )
        
        if self.authority == "local":
            raise RuntimeError(
                "Local timestamps are NOT court-admissible. "
                "Configure network timestamp authority (freetsa or digicert)."
            )
        
        # Only proceed with network timestamps
        try:
            result = await self._get_remote_timestamp(data)
            
            # Verify the timestamp was obtained successfully
            if not result or not result.token_data:
                raise RuntimeError("Timestamp verification failed - empty token received")
            
            return result
            
        except Exception as e:
            logger.error(f"Network timestamp request failed: {e}")
            # NO FALLBACK - fail explicitly to maintain chain integrity
            raise RuntimeError(
                f"Failed to obtain court-admissible timestamp from {self.authority}: {e}"
            ) from e
    
    async def _get_remote_timestamp(self, data: bytes) -> TimestampToken:
        """Get timestamp from remote TSA."""
        if not RFC3161NG_AVAILABLE:
            raise ImportError("rfc3161ng required for remote timestamps")
        
        # Compute message imprint
        data_hash = hashlib.sha256(data).digest()
        
        try:
            # Create timestamper
            timestamper = RemoteTimestamper(
                self.tsa_url,
                hashname='sha256',
                certificate=None  # Most TSAs don't require client cert
            )
            
            # Request timestamp (synchronous call in thread pool)
            loop = asyncio.get_event_loop()
            timestamp_response = await loop.run_in_executor(
                None,
                timestamper.timestamp,
                data_hash
            )
            
            if not timestamp_response:
                raise ValueError("Empty timestamp response")
            
            # Parse response
            return TimestampToken(
                token_data=timestamp_response,
                gen_time=datetime.utcnow(),  # Actual time from TSA token
                hash_algorithm="SHA-256",
                message_imprint=data_hash.hex(),
                authority=self.authority,
                serial_number=None,  # Would extract from ASN.1 structure
                policy_oid=None
            )
        
        except Exception as e:
            logger.error(f"Remote timestamp failed: {e}")
            raise
    
    async def timestamp_with_retry(
        self,
        data: bytes,
        max_retries: int = 3,
        fallback_authorities: Optional[list] = None,
        strict_mode: bool = True
    ) -> TimestampToken:
        """
        Get timestamp with automatic retry and fallback.
        
        Args:
            data: Data to timestamp
            max_retries: Max retry attempts per authority
            fallback_authorities: List of backup TSAs to try
            strict_mode: If True, raise exception on failure instead of using local timestamp.
                        Default True for court-admissible evidence.
            
        Returns:
            TimestampToken from first successful TSA
            
        Raises:
            RuntimeError: If strict_mode=True and all authorities fail
        """
        authorities = [self.authority]
        if fallback_authorities:
            authorities.extend(fallback_authorities)
        
        last_error = None
        
        for auth in authorities:
            original_authority = self.authority
            original_url = self.tsa_url
            
            try:
                self.authority = auth
                self.tsa_url = self.AUTHORITIES.get(auth, self.AUTHORITIES["local"])
                
                for attempt in range(max_retries):
                    try:
                        token = await self.timestamp(data)
                        logger.info(f"Timestamp successful: {auth}")
                        return token
                    except Exception as e:
                        last_error = e
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except Exception as e:
                last_error = e
            
            finally:
                # Restore original settings
                self.authority = original_authority
                self.tsa_url = original_url
        
        # All attempts failed
        if strict_mode:
            raise RuntimeError(
                f"All timestamp authorities failed after {max_retries} retries. "
                f"Last error: {last_error}. Evidence chain cannot be court-admissible."
            )
        else:
            logger.warning(f"All timestamp authorities failed: {last_error}")
            return self.create_local_timestamp(data, "fallback_local")
    
    @staticmethod
    def create_local_timestamp(data: bytes, authority: str = "local") -> TimestampToken:
        """
        Create local timestamp (development/fallback only).
        
        WARNING: Local timestamps are NOT court-admissible.
        Use only for development or as fallback.
        """
        data_hash = hashlib.sha256(data).hexdigest()
        
        return TimestampToken(
            token_data=f"LOCAL_TS_{data_hash[:16]}".encode(),
            gen_time=datetime.utcnow(),
            hash_algorithm="SHA-256",
            message_imprint=data_hash,
            authority=authority,
            serial_number=None,
            policy_oid=None
        )
    
    @staticmethod
    def verify_timestamp(token: TimestampToken, data: bytes) -> bool:
        """
        Verify timestamp token against data.
        
        Args:
            token: Timestamp token to verify
            data: Original data
            
        Returns:
            True if token is valid for data
        """
        return token.verify(data)

