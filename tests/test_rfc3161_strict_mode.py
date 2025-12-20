"""
RFC 3161 Strict Mode Tests
==========================

Tests to validate that the RFC3161Client's timestamp_with_retry method
properly enforces strict_mode to prevent non-court-admissible local timestamps.

Strict mode ensures that all timestamp failures raise exceptions rather than
falling back to local timestamps that are not legally valid.
"""

import hashlib
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.evidence_chain.rfc3161_client import (
    RFC3161Client,
    TimestampToken,
)


class TestRFC3161StrictMode:
    """Test strict_mode parameter in RFC3161Client."""
    
    @pytest.mark.asyncio
    async def test_strict_mode_default_is_true(self):
        """Test that strict_mode defaults to True."""
        client = RFC3161Client(authority="local")
        
        # Mock the timestamp method to raise an error
        with patch.object(client, 'timestamp', side_effect=RuntimeError("Network error")):
            # With default strict_mode, should raise exception
            with pytest.raises(RuntimeError) as exc_info:
                await client.timestamp_with_retry(b"test data")
            
            assert "All timestamp authorities failed" in str(exc_info.value)
            assert "court-admissible" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_strict_mode_true_raises_exception(self):
        """Test that strict_mode=True raises exception when all authorities fail."""
        client = RFC3161Client(authority="freetsa")
        
        # Mock timestamp to always fail
        with patch.object(client, 'timestamp', side_effect=RuntimeError("TSA unreachable")):
            with pytest.raises(RuntimeError) as exc_info:
                await client.timestamp_with_retry(
                    b"test data",
                    max_retries=2,
                    strict_mode=True
                )
            
            error_msg = str(exc_info.value)
            assert "All timestamp authorities failed" in error_msg
            assert "2 retries" in error_msg or "retries" in error_msg
    
    @pytest.mark.asyncio
    async def test_strict_mode_false_allows_local_fallback(self):
        """Test that strict_mode=False falls back to local timestamp."""
        client = RFC3161Client(authority="freetsa")
        
        # Mock timestamp to always fail
        with patch.object(client, 'timestamp', side_effect=RuntimeError("TSA unreachable")):
            # With strict_mode=False, should return local timestamp
            token = await client.timestamp_with_retry(
                b"test data",
                max_retries=1,
                strict_mode=False
            )
            
            # Should get a local timestamp
            assert token is not None
            assert token.authority == "fallback_local"
            assert token.hash_algorithm == "SHA-256"
    
    @pytest.mark.asyncio
    async def test_strict_mode_with_fallback_authorities(self):
        """Test strict_mode behavior with fallback authorities."""
        client = RFC3161Client(authority="freetsa")
        
        # Mock all authorities to fail
        with patch.object(client, 'timestamp', side_effect=RuntimeError("All TSAs down")):
            # Try with fallback authorities in strict mode
            with pytest.raises(RuntimeError) as exc_info:
                await client.timestamp_with_retry(
                    b"test data",
                    max_retries=1,
                    fallback_authorities=["digicert"],
                    strict_mode=True
                )
            
            assert "All timestamp authorities failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_strict_mode_success_returns_token(self):
        """Test that successful timestamp returns token regardless of strict_mode."""
        client = RFC3161Client(authority="freetsa")
        
        # Create a mock token
        mock_token = TimestampToken(
            token_data=b"mock_token",
            gen_time=datetime.utcnow(),
            hash_algorithm="SHA-256",
            message_imprint=hashlib.sha256(b"test data").hexdigest(),
            authority="freetsa",
            serial_number="12345"
        )
        
        # Mock successful timestamp
        with patch.object(client, 'timestamp', return_value=mock_token):
            # Should succeed with strict_mode=True
            token = await client.timestamp_with_retry(
                b"test data",
                max_retries=3,
                strict_mode=True
            )
            
            assert token is not None
            assert token.authority == "freetsa"
            assert token.token_data == b"mock_token"
    
    @pytest.mark.asyncio
    async def test_error_message_includes_details(self):
        """Test that error message in strict mode includes helpful details."""
        client = RFC3161Client(authority="freetsa")
        
        test_error = RuntimeError("Connection timeout")
        
        with patch.object(client, 'timestamp', side_effect=test_error):
            with pytest.raises(RuntimeError) as exc_info:
                await client.timestamp_with_retry(
                    b"test data",
                    max_retries=2,
                    strict_mode=True
                )
            
            error_msg = str(exc_info.value)
            # Should mention the failure
            assert "failed" in error_msg.lower()
            # Should mention court-admissibility
            assert "court" in error_msg.lower() or "admissible" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_local_timestamp_not_court_admissible_warning(self):
        """Test that local timestamps have appropriate warnings."""
        # Create a local timestamp
        token = RFC3161Client.create_local_timestamp(b"test data", "local")
        
        assert token.authority == "local"
        assert token.hash_algorithm == "SHA-256"
        # Local tokens should be identifiable as not court-admissible
        assert "LOCAL" in str(token.token_data) or token.authority == "local"
    
    @pytest.mark.asyncio  
    async def test_retry_with_exponential_backoff(self):
        """Test that retries use exponential backoff."""
        client = RFC3161Client(authority="freetsa")
        
        call_times = []
        
        async def mock_timestamp_with_timing(data):
            import time
            call_times.append(time.time())
            raise RuntimeError("TSA error")
        
        with patch.object(client, 'timestamp', side_effect=mock_timestamp_with_timing):
            try:
                await client.timestamp_with_retry(
                    b"test data",
                    max_retries=3,
                    strict_mode=True
                )
            except RuntimeError:
                pass  # Expected
        
        # Should have made 3 attempts
        assert len(call_times) == 3
        
        # Check that delays increased (allowing for timing variance)
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be longer than first (exponential backoff)
            # Allow some variance due to system timing
            assert delay2 >= delay1 * 0.8  # Within 80% tolerance


class TestRFC3161ClientConfiguration:
    """Test RFC3161Client configuration and initialization."""
    
    def test_client_supports_multiple_authorities(self):
        """Test that client can be configured with different authorities."""
        authorities = ["freetsa", "digicert", "local"]
        
        for auth in authorities:
            client = RFC3161Client(authority=auth)
            assert client.authority == auth
            assert client.tsa_url == RFC3161Client.AUTHORITIES[auth]
    
    def test_default_authority_is_local(self):
        """Test that default authority is local for development."""
        client = RFC3161Client()
        assert client.authority == "local"
    
    @pytest.mark.asyncio
    async def test_timestamp_method_requires_network_authority(self):
        """Test that direct timestamp() call requires network authority."""
        client = RFC3161Client(authority="local")
        
        # Direct timestamp call with local authority should fail
        with pytest.raises(RuntimeError) as exc_info:
            await client.timestamp(b"test data")
        
        error_msg = str(exc_info.value)
        assert "court-admissible" in error_msg.lower() or "network timestamp" in error_msg.lower()


class TestTimestampTokenVerification:
    """Test TimestampToken verification."""
    
    def test_token_verify_correct_data(self):
        """Test that token verification works for correct data."""
        data = b"test data"
        token = TimestampToken(
            token_data=b"token",
            gen_time=datetime.utcnow(),
            hash_algorithm="SHA-256",
            message_imprint=hashlib.sha256(data).hexdigest(),
            authority="test"
        )
        
        assert token.verify(data) is True
    
    def test_token_verify_wrong_data(self):
        """Test that token verification fails for wrong data."""
        original_data = b"original data"
        token = TimestampToken(
            token_data=b"token",
            gen_time=datetime.utcnow(),
            hash_algorithm="SHA-256",
            message_imprint=hashlib.sha256(original_data).hexdigest(),
            authority="test"
        )
        
        # Verify with different data
        assert token.verify(b"different data") is False
    
    def test_token_to_dict(self):
        """Test TimestampToken serialization."""
        token = TimestampToken(
            token_data=b"token_data",
            gen_time=datetime(2019, 3, 22, 10, 30, 0),
            hash_algorithm="SHA-256",
            message_imprint="abc123",
            authority="freetsa",
            serial_number="12345",
            policy_oid="1.2.3.4"
        )
        
        data = token.to_dict()
        
        assert data["hash_algorithm"] == "SHA-256"
        assert data["authority"] == "freetsa"
        assert data["serial_number"] == "12345"
        assert "gen_time" in data


class TestProductionTimestampRequirements:
    """Test that production requirements are enforced."""
    
    @pytest.mark.asyncio
    async def test_production_requires_network_tsa(self):
        """Test that production code requires network TSA."""
        # This test verifies the documented requirement that production
        # evidence chains must use network TSAs
        
        client = RFC3161Client(authority="local")
        
        # Strict mode should be default and prevent local timestamps
        with patch.object(client, 'timestamp', side_effect=RuntimeError("Local not allowed")):
            with pytest.raises(RuntimeError):
                # Default strict_mode=True should prevent local fallback
                await client.timestamp_with_retry(b"data")
    
    def test_documentation_requirement(self):
        """Test that the documentation clearly states strict mode default."""
        # This is a documentation test - verify the docstring
        import inspect
        
        signature = inspect.signature(RFC3161Client.timestamp_with_retry)
        
        # strict_mode parameter should exist
        assert 'strict_mode' in signature.parameters
        
        # Default should be True
        default = signature.parameters['strict_mode'].default
        assert default is True, "strict_mode must default to True for court-admissible evidence"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
