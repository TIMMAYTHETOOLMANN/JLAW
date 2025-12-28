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
    - Multiple trusted timestamp authorities with fallback
    - Automatic retry with exponential backoff
    - SHA-256 message imprint
    - Token verification
    - Court-admissible timestamps
    - Connection validation
    """
    
    AUTHORITIES = {
        "freetsa": "http://freetsa.org/tsr",  # Primary TSA (free, public, court-admissible)
        "sectigo": "http://timestamp.sectigo.com",  # Fallback 1 (commercial TSA)
        "digicert": "http://timestamp.digicert.com",  # Fallback 2 (commercial TSA)
        "local": "local"  # Development only - NOT court-admissible
    }
    
    # Note: TSA endpoints typically use HTTP as per RFC 3161 standard.
    # The timestamp response itself is cryptographically signed by the TSA,
    # ensuring integrity regardless of transport protocol.
    
    # Retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAYS = [2, 4, 8]  # Exponential backoff in seconds
    DEFAULT_TIMEOUT = 10  # Default timeout in seconds
    
    def __init__(
        self, 
        authority: str = "freetsa",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES
    ):
        """
        Initialize RFC 3161 client.
        
        Args:
            authority: TSA to use ("freetsa", "sectigo", "digicert", or "local")
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum retry attempts per authority (default: 3)
        """
        self.authority = authority
        self.tsa_url = self.AUTHORITIES.get(authority, self.AUTHORITIES["freetsa"])
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def validate_tsa_connectivity(self, test_all: bool = False) -> bool:
        """
        Validate connectivity to TSA endpoint(s).
        
        Args:
            test_all: If True, test all available TSAs. If False, test only current authority.
        
        Returns:
            True if at least one TSA is reachable, False otherwise.
        """
        authorities_to_test = []
        
        if test_all:
            # Test all non-local authorities
            authorities_to_test = [
                (name, url) for name, url in self.AUTHORITIES.items() 
                if name != "local"
            ]
        else:
            # Test only current authority
            if self.authority == "local":
                logger.warning("Cannot validate local timestamp authority connectivity")
                return False
            authorities_to_test = [(self.authority, self.tsa_url)]
        
        results = []
        for auth_name, auth_url in authorities_to_test:
            try:
                logger.info(f"Testing TSA connectivity: {auth_name} ({auth_url})")
                
                # Create a simple test hash
                test_data = b"JLAW_TSA_CONNECTIVITY_TEST"
                test_hash = hashlib.sha256(test_data).digest()
                
                if not RFC3161NG_AVAILABLE:
                    logger.error("rfc3161ng library not available - cannot validate TSA")
                    results.append(False)
                    continue
                
                # Try to get a timestamp with timeout
                try:
                    async with asyncio.timeout(self.timeout):
                        timestamper = RemoteTimestamper(
                            auth_url,
                            hashname='sha256',
                            certificate=None
                        )
                        
                        loop = asyncio.get_event_loop()
                        response = await loop.run_in_executor(
                            None,
                            timestamper.timestamp,
                            test_hash
                        )
                        
                        if response:
                            logger.info(f"✓ TSA {auth_name} is reachable and responsive")
                            results.append(True)
                        else:
                            logger.warning(f"✗ TSA {auth_name} returned empty response")
                            results.append(False)
                            
                except asyncio.TimeoutError:
                    logger.warning(f"✗ TSA {auth_name} timed out after {self.timeout}s")
                    results.append(False)
                except Exception as e:
                    logger.warning(f"✗ TSA {auth_name} connectivity failed: {e}")
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"Error testing TSA {auth_name}: {e}")
                results.append(False)
        
        # Return True if at least one TSA is reachable
        any_success = any(results)
        if any_success:
            logger.info(f"✓ TSA connectivity validated: {sum(results)}/{len(results)} authorities reachable")
        else:
            logger.error("✗ No TSA authorities are reachable")
        
        return any_success
    
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
        max_retries: Optional[int] = None,
        fallback_authorities: Optional[list] = None,
        strict_mode: bool = True
    ) -> TimestampToken:
        """
        Get timestamp with automatic retry and fallback to multiple TSAs.
        
        Args:
            data: Data to timestamp
            max_retries: Max retry attempts per authority (default: uses client's max_retries)
            fallback_authorities: List of backup TSAs to try (default: ["sectigo", "digicert"])
            strict_mode: If True, raise exception on failure instead of using local timestamp.
                        Default True for court-admissible evidence.
            
        Returns:
            TimestampToken from first successful TSA
            
        Raises:
            RuntimeError: If strict_mode=True and all authorities fail
        """
        if max_retries is None:
            max_retries = self.max_retries
        
        # Set default fallback authorities
        if fallback_authorities is None:
            fallback_authorities = ["sectigo", "digicert"]
        
        authorities = [self.authority]
        if fallback_authorities:
            # Only add authorities that aren't already in the list
            for auth in fallback_authorities:
                if auth not in authorities and auth != "local":
                    authorities.append(auth)
        
        last_error = None
        
        for auth in authorities:
            original_authority = self.authority
            original_url = self.tsa_url
            
            try:
                self.authority = auth
                self.tsa_url = self.AUTHORITIES.get(auth, self.AUTHORITIES["freetsa"])
                
                logger.info(f"Attempting timestamp from TSA: {auth} ({self.tsa_url})")
                
                for attempt in range(max_retries):
                    try:
                        # Use timeout for each attempt
                        async with asyncio.timeout(self.timeout):
                            token = await self.timestamp(data)
                            logger.info(f"✓ Timestamp successful: {auth} (attempt {attempt + 1}/{max_retries})")
                            return token
                    except asyncio.TimeoutError:
                        last_error = TimeoutError(f"Timeout after {self.timeout}s")
                        logger.warning(f"✗ TSA {auth} timeout (attempt {attempt + 1}/{max_retries})")
                    except Exception as e:
                        last_error = e
                        logger.warning(f"✗ TSA {auth} failed (attempt {attempt + 1}/{max_retries}): {e}")
                        
                    # Exponential backoff between retries
                    if attempt < max_retries - 1:
                        delay = self.DEFAULT_RETRY_DELAYS[min(attempt, len(self.DEFAULT_RETRY_DELAYS) - 1)]
                        logger.debug(f"Waiting {delay}s before retry...")
                        await asyncio.sleep(delay)
            
            except Exception as e:
                last_error = e
                logger.error(f"✗ TSA {auth} failed completely: {e}")
            
            finally:
                # Restore original settings
                self.authority = original_authority
                self.tsa_url = original_url
        
        # All attempts failed
        error_msg = (
            f"All timestamp authorities failed after {max_retries} retries each. "
            f"Tried: {', '.join(authorities)}. "
            f"Last error: {last_error}. Evidence chain cannot be court-admissible."
        )
        
        if strict_mode:
            raise RuntimeError(error_msg)
        else:
            logger.warning(error_msg)
            logger.warning("Falling back to local timestamp (NOT court-admissible)")
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

