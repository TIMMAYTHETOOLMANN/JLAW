"""
RFC 3161 Timestamp Authority Integration Tests
==============================================

Integration tests for court-admissible timestamp generation with
FRE 902(13)/(14) compliance validation.

These tests verify:
1. TSA connectivity validation
2. Timestamp token generation
3. Token verification against source data
4. Fallback mechanism with multiple TSAs
5. Retry logic with exponential backoff
"""

import pytest
import asyncio
import hashlib
from datetime import datetime

# Import the RFC3161 client
from src.core.evidence_chain.rfc3161_client import RFC3161Client, TimestampToken


class TestRFC3161Integration:
    """Integration tests for RFC 3161 timestamp functionality."""
    
    @pytest.mark.asyncio
    async def test_library_availability(self):
        """Verify RFC 3161 libraries are available."""
        try:
            import rfc3161ng
            import cryptography
            assert True, "RFC 3161 libraries available"
        except ImportError as e:
            pytest.skip(f"RFC 3161 libraries not installed: {e}")
    
    @pytest.mark.asyncio
    async def test_rfc3161_timestamp_generation(self):
        """Verify RFC 3161 timestamp token generation and validation."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        client = RFC3161Client(authority="freetsa", timeout=15, max_retries=3)
        
        # Test connectivity first (with timeout)
        try:
            connectivity = await asyncio.wait_for(
                client.validate_tsa_connectivity(test_all=False),
                timeout=30
            )
            if not connectivity:
                pytest.skip("TSA connectivity failed - may be network/firewall issue")
        except asyncio.TimeoutError:
            pytest.skip("TSA connectivity test timed out")
        
        # Generate timestamp
        test_hash = "a" * 64  # Mock SHA-256 hash
        test_data = bytes.fromhex(test_hash)
        
        try:
            token = await asyncio.wait_for(
                client.timestamp_with_retry(
                    test_data,
                    fallback_authorities=["sectigo", "digicert"],
                    strict_mode=True
                ),
                timeout=45
            )
        except asyncio.TimeoutError:
            pytest.skip("Timestamp generation timed out")
        except RuntimeError as e:
            if "All timestamp authorities failed" in str(e):
                pytest.skip(f"All TSAs unavailable: {e}")
            raise
        
        assert token is not None, "Timestamp token generation failed"
        assert len(token.token_data) > 0, "Empty timestamp token"
        assert token.authority in ["freetsa", "sectigo", "digicert"], f"Unexpected authority: {token.authority}"
        assert token.hash_algorithm == "SHA-256", "Wrong hash algorithm"
        
        # Validate token structure
        is_valid = RFC3161Client.verify_timestamp(token, test_data)
        assert is_valid, "Token verification failed"
    
    @pytest.mark.asyncio
    async def test_validate_tsa_connectivity(self):
        """Test TSA connectivity validation method."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        client = RFC3161Client(authority="freetsa", timeout=15)
        
        try:
            # Test single authority
            connectivity = await asyncio.wait_for(
                client.validate_tsa_connectivity(test_all=False),
                timeout=30
            )
            # We don't assert True here because TSA might be down
            # Just verify the method runs without error
            assert isinstance(connectivity, bool), "Connectivity check should return boolean"
            
        except asyncio.TimeoutError:
            pytest.skip("TSA connectivity test timed out")
    
    @pytest.mark.asyncio
    async def test_multiple_tsa_fallback(self):
        """Test fallback mechanism across multiple TSAs."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        client = RFC3161Client(authority="freetsa", timeout=15, max_retries=2)
        
        test_data = b"JLAW_FALLBACK_TEST"
        
        try:
            token = await asyncio.wait_for(
                client.timestamp_with_retry(
                    test_data,
                    fallback_authorities=["sectigo", "digicert"],
                    strict_mode=False  # Allow fallback to local if all TSAs fail
                ),
                timeout=60
            )
            
            assert token is not None, "Should receive token (even if local fallback)"
            assert len(token.token_data) > 0, "Token should have data"
            
            # If we got a network timestamp, verify it
            if token.authority != "fallback_local":
                is_valid = RFC3161Client.verify_timestamp(token, test_data)
                assert is_valid, "Network timestamp should verify correctly"
            
        except asyncio.TimeoutError:
            pytest.skip("Timestamp generation with fallback timed out")
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Test retry logic with exponential backoff."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        client = RFC3161Client(authority="freetsa", timeout=10, max_retries=3)
        
        # Check retry delays are configured
        assert hasattr(client, 'DEFAULT_RETRY_DELAYS'), "Retry delays should be configured"
        assert len(client.DEFAULT_RETRY_DELAYS) >= 3, "Should have at least 3 retry delays"
        assert client.DEFAULT_RETRY_DELAYS == [2, 4, 8], "Should use exponential backoff (2s, 4s, 8s)"
    
    @pytest.mark.asyncio
    async def test_timestamp_token_verification(self):
        """Test timestamp token verification against data."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        test_data = b"JLAW_VERIFICATION_TEST"
        
        # Create a local timestamp for testing verification logic
        token = RFC3161Client.create_local_timestamp(test_data, "test")
        
        # Verify with correct data
        is_valid = RFC3161Client.verify_timestamp(token, test_data)
        assert is_valid, "Token should verify with correct data"
        
        # Verify with incorrect data
        wrong_data = b"WRONG_DATA"
        is_invalid = RFC3161Client.verify_timestamp(token, wrong_data)
        assert not is_invalid, "Token should NOT verify with incorrect data"
    
    @pytest.mark.asyncio
    async def test_timeout_configuration(self):
        """Test timeout configuration is respected."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        # Create client with custom timeout
        custom_timeout = 5
        client = RFC3161Client(authority="freetsa", timeout=custom_timeout)
        
        assert client.timeout == custom_timeout, f"Timeout should be {custom_timeout}s"
    
    @pytest.mark.asyncio
    async def test_strict_mode_enforcement(self):
        """Test that strict mode raises exception on failure."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        # Use an invalid authority to force failure
        client = RFC3161Client(authority="local", timeout=5)
        
        test_data = b"STRICT_MODE_TEST"
        
        # strict_mode=True should raise RuntimeError when using local authority
        with pytest.raises(RuntimeError, match="NOT court-admissible"):
            await client.timestamp(test_data)
    
    @pytest.mark.asyncio
    async def test_all_tsa_connectivity(self):
        """Test connectivity to all configured TSAs."""
        try:
            import rfc3161ng
        except ImportError:
            pytest.skip("rfc3161ng not installed")
        
        client = RFC3161Client(timeout=15)
        
        try:
            # Test all TSAs
            connectivity = await asyncio.wait_for(
                client.validate_tsa_connectivity(test_all=True),
                timeout=60
            )
            
            # We expect at least one to be reachable
            # but don't fail if none are (could be network issue)
            assert isinstance(connectivity, bool), "Should return boolean result"
            
        except asyncio.TimeoutError:
            pytest.skip("All TSA connectivity test timed out")


@pytest.mark.asyncio
async def test_rfc3161_integration_full_workflow():
    """
    Full workflow integration test for RFC 3161.
    
    This test simulates the complete evidence chain workflow:
    1. Validate TSA connectivity
    2. Generate timestamp for evidence
    3. Verify timestamp integrity
    4. Confirm court-admissibility criteria
    """
    try:
        import rfc3161ng
    except ImportError:
        pytest.skip("rfc3161ng not installed")
    
    # Simulate evidence data
    evidence_data = b"JLAW_EVIDENCE_CHAIN_TEST_DOCUMENT"
    evidence_hash = hashlib.sha256(evidence_data).digest()
    
    # Initialize client with production settings
    client = RFC3161Client(
        authority="freetsa",
        timeout=15,
        max_retries=3
    )
    
    try:
        # Step 1: Validate connectivity
        connectivity = await asyncio.wait_for(
            client.validate_tsa_connectivity(test_all=False),
            timeout=30
        )
        
        if not connectivity:
            pytest.skip("TSA not available for full workflow test")
        
        # Step 2: Generate timestamp
        token = await asyncio.wait_for(
            client.timestamp_with_retry(
                evidence_hash,
                fallback_authorities=["sectigo", "digicert"],
                strict_mode=True
            ),
            timeout=45
        )
        
        # Step 3: Verify token
        assert token is not None, "Token should be generated"
        assert token.token_data, "Token should have data"
        assert isinstance(token.gen_time, datetime), "Token should have generation time"
        
        # Step 4: Verify integrity
        is_valid = RFC3161Client.verify_timestamp(token, evidence_hash)
        assert is_valid, "Token integrity verification should pass"
        
        # Step 5: Confirm court-admissibility criteria
        assert token.authority != "local", "Should use network TSA for court-admissibility"
        assert token.authority != "fallback_local", "Should not fall back to local"
        assert token.hash_algorithm == "SHA-256", "Should use SHA-256 per FRE 902(13)"
        
    except asyncio.TimeoutError:
        pytest.skip("Full workflow test timed out")
    except RuntimeError as e:
        if "All timestamp authorities failed" in str(e):
            pytest.skip(f"TSAs unavailable: {e}")
        raise
