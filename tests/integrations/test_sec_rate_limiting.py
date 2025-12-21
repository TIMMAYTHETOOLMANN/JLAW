"""
Test Suite for SEC EDGAR Rate Limiting and Configuration Validation
===================================================================

Tests for:
- Shared rate limiter singleton
- Exponential backoff for 429 errors
- User-Agent validation
- Mock mode
"""

import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

from src.integrations.sec_edgar.edgar_client import (
    SECEdgarClient, 
    RateLimiter, 
    _SHARED_RATE_LIMITER
)
from config.secure_config import (
    validate_sec_user_agent,
    validate_sec_configuration
)


class TestRateLimiterSingleton:
    """Test that RateLimiter is properly shared across instances."""
    
    def test_rate_limiter_is_singleton(self):
        """Test that all RateLimiter instances are the same object."""
        limiter1 = RateLimiter()
        limiter2 = RateLimiter()
        limiter3 = RateLimiter(requests_per_second=8.0)  # Should ignore parameter
        
        assert limiter1 is limiter2
        assert limiter2 is limiter3
        assert limiter1 is _SHARED_RATE_LIMITER
    
    def test_multiple_clients_share_rate_limiter(self):
        """Test that multiple SECEdgarClient instances share the same rate limiter."""
        client1 = SECEdgarClient(mock_mode=True)
        client2 = SECEdgarClient(mock_mode=True)
        client3 = SECEdgarClient(mock_mode=True)
        
        assert client1.rate_limiter is client2.rate_limiter
        assert client2.rate_limiter is client3.rate_limiter
        assert client1.rate_limiter is _SHARED_RATE_LIMITER
    
    @pytest.mark.asyncio
    async def test_rate_limiter_tracks_requests(self):
        """Test that rate limiter tracks request count."""
        limiter = RateLimiter()
        initial_count = limiter.request_count
        
        # Acquire 5 times
        for _ in range(5):
            await limiter.acquire()
        
        assert limiter.request_count == initial_count + 5


class TestExponentialBackoff:
    """Test exponential backoff for 429 errors."""
    
    @pytest.mark.asyncio
    async def test_fetch_retries_on_429(self):
        """Test that _fetch retries with exponential backoff on 429 errors."""
        client = SECEdgarClient()
        
        # Mock session to return 429, then 200
        mock_response_429 = MagicMock()
        mock_response_429.status = 429
        mock_response_429.__aenter__ = AsyncMock(return_value=mock_response_429)
        mock_response_429.__aexit__ = AsyncMock(return_value=None)
        
        mock_response_200 = MagicMock()
        mock_response_200.status = 200
        mock_response_200.text = AsyncMock(return_value='{"success": true}')
        mock_response_200.__aenter__ = AsyncMock(return_value=mock_response_200)
        mock_response_200.__aexit__ = AsyncMock(return_value=None)
        
        # First call returns 429, second call returns 200
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[mock_response_429, mock_response_200])
        
        client.session = mock_session
        
        # Mock asyncio.sleep to avoid actual delays
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await client._fetch("https://test.url")
        
        assert result == '{"success": true}'
        assert mock_session.get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_fetch_fails_after_max_retries(self):
        """Test that _fetch fails after max retries on persistent 429."""
        client = SECEdgarClient()
        
        # Mock session to always return 429
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        
        client.session = mock_session
        
        # Mock asyncio.sleep to avoid actual delays
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await client._fetch("https://test.url")
        
        assert result is None
        # Should attempt MAX_RETRIES times
        assert mock_session.get.call_count == client.MAX_RETRIES
    
    @pytest.mark.asyncio
    async def test_fetch_uses_correct_backoff_delays(self):
        """Test that exponential backoff uses correct delay sequence."""
        client = SECEdgarClient()
        
        # Mock session to always return 429
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        client.session = mock_session
        
        sleep_calls = []
        
        async def mock_sleep(delay):
            sleep_calls.append(delay)
        
        # Patch sleep in the edgar_client module specifically
        with patch('src.integrations.sec_edgar.edgar_client.asyncio.sleep', new=mock_sleep):
            await client._fetch("https://test.url")
        
        # Should have delays of 1, 2, 4 seconds (exponential backoff for 429)
        # Plus rate limiter delays (approximately 0.11 seconds each)
        # Filter to delays >= 1 second (the backoff delays)
        backoff_delays = [d for d in sleep_calls if d >= 1]
        expected_delays = [1, 2, 4]
        assert backoff_delays == expected_delays


class TestMockMode:
    """Test mock mode functionality."""
    
    def test_mock_mode_from_constructor(self):
        """Test that mock mode can be set via constructor."""
        client = SECEdgarClient(mock_mode=True)
        assert client.mock_mode is True
    
    def test_mock_mode_from_environment(self):
        """Test that mock mode can be set via environment variable."""
        with patch.dict(os.environ, {'SEC_MOCK_MODE': 'true'}):
            client = SECEdgarClient()
            assert client.mock_mode is True
        
        with patch.dict(os.environ, {'SEC_MOCK_MODE': '1'}):
            client = SECEdgarClient()
            assert client.mock_mode is True
        
        with patch.dict(os.environ, {'SEC_MOCK_MODE': 'false'}):
            client = SECEdgarClient()
            assert client.mock_mode is False
    
    @pytest.mark.asyncio
    async def test_mock_mode_returns_sample_data(self):
        """Test that mock mode returns sample data without API calls."""
        client = SECEdgarClient(mock_mode=True)
        
        # Mock mode should return data without needing a session
        submissions_url = "https://data.sec.gov/submissions/CIK0000320193.json"
        result = await client._fetch(submissions_url)
        
        assert result is not None
        assert "Mock Company" in result
    
    @pytest.mark.asyncio
    async def test_mock_mode_submissions(self):
        """Test that mock mode works for submissions endpoint."""
        async with SECEdgarClient(mock_mode=True) as client:
            result = await client.get_company_submissions("320193")
            
            assert result is not None
            assert "name" in result
            assert "filings" in result
    
    @pytest.mark.asyncio
    async def test_mock_mode_xbrl_facts(self):
        """Test that mock mode works for XBRL facts endpoint."""
        async with SECEdgarClient(mock_mode=True) as client:
            result = await client.get_xbrl_facts("320193")
            
            assert result is not None
            assert "facts" in result


class TestUserAgentValidation:
    """Test User-Agent validation."""
    
    def test_valid_user_agent_with_email(self):
        """Test that valid User-Agent with email passes validation."""
        valid_agents = [
            "CompanyName/1.0 (admin@company.com)",
            "MyProject contact@university.edu",
            "Research/2.0 (support@organization.org)",
        ]
        
        for agent in valid_agents:
            is_valid, error = validate_sec_user_agent(agent)
            assert is_valid, f"Should be valid: {agent}. Error: {error}"
            assert error == ""
    
    def test_invalid_user_agent_missing_email(self):
        """Test that User-Agent without email fails validation."""
        invalid_agents = [
            "CompanyName/1.0",
            "MyProject",
            "Research (no email here)",
        ]
        
        for agent in invalid_agents:
            is_valid, error = validate_sec_user_agent(agent)
            assert not is_valid, f"Should be invalid: {agent}"
            assert "email" in error.lower()
    
    def test_invalid_user_agent_placeholder(self):
        """Test that placeholder User-Agent values fail validation."""
        placeholders = [
            "YourProject contact@your-email.org",
            "YOUR_PROJECT admin@example.com",
            "MyApp contact@your-domain.com",
        ]
        
        for agent in placeholders:
            is_valid, error = validate_sec_user_agent(agent)
            assert not is_valid, f"Should reject placeholder: {agent}"
            assert "placeholder" in error.lower()
    
    def test_invalid_user_agent_too_short(self):
        """Test that too-short User-Agent fails validation."""
        is_valid, error = validate_sec_user_agent("a@b.c")
        assert not is_valid
        # Could fail on email validation or length check - either is fine
        assert "email" in error.lower() or "too short" in error.lower()
    
    def test_invalid_user_agent_none(self):
        """Test that None User-Agent fails validation."""
        is_valid, error = validate_sec_user_agent(None)
        assert not is_valid
        assert "not set" in error.lower()


class TestConfigurationValidation:
    """Test SEC configuration validation."""
    
    def test_validate_configuration_with_valid_user_agent(self):
        """Test configuration validation with valid User-Agent."""
        with patch.dict(os.environ, {'SEC_USER_AGENT': 'Company/1.0 (admin@company.com)'}):
            is_valid, errors = validate_sec_configuration()
            assert is_valid
            assert len(errors) == 0
    
    def test_validate_configuration_with_invalid_user_agent(self):
        """Test configuration validation with invalid User-Agent."""
        with patch.dict(os.environ, {'SEC_USER_AGENT': 'YourProject contact@your-email.org'}):
            is_valid, errors = validate_sec_configuration()
            assert not is_valid
            assert len(errors) > 0
            assert any("placeholder" in err.lower() for err in errors)
    
    def test_validate_configuration_with_missing_user_agent(self):
        """Test configuration validation with missing User-Agent."""
        with patch.dict(os.environ, {}, clear=True):
            is_valid, errors = validate_sec_configuration()
            assert not is_valid
            assert len(errors) > 0


class TestClientInitialization:
    """Test SECEdgarClient initialization."""
    
    def test_client_uses_environment_user_agent(self):
        """Test that client uses User-Agent from environment."""
        with patch.dict(os.environ, {'SEC_USER_AGENT': 'EnvAgent/1.0 (env@test.com)'}):
            client = SECEdgarClient()
            assert client.user_agent == 'EnvAgent/1.0 (env@test.com)'
    
    def test_client_uses_parameter_user_agent_over_env(self):
        """Test that parameter User-Agent overrides environment."""
        with patch.dict(os.environ, {'SEC_USER_AGENT': 'EnvAgent/1.0 (env@test.com)'}):
            client = SECEdgarClient(user_agent='ParamAgent/1.0 (param@test.com)')
            assert client.user_agent == 'ParamAgent/1.0 (param@test.com)'
    
    def test_client_falls_back_to_default_user_agent(self):
        """Test that client falls back to default User-Agent if none provided."""
        with patch.dict(os.environ, {}, clear=True):
            client = SECEdgarClient()
            assert client.user_agent == SECEdgarClient.DEFAULT_USER_AGENT
    
    def test_client_checks_sec_edgar_user_agent_env(self):
        """Test that client checks SEC_EDGAR_USER_AGENT environment variable."""
        # Clear both potential env vars to ensure clean test
        env_override = {
            'SEC_EDGAR_USER_AGENT': 'Edgar/1.0 (edgar@test.com)',
            'SEC_USER_AGENT': ''
        }
        with patch.dict(os.environ, env_override, clear=False):
            # Also need to clear the cached env var by creating fresh client
            os.environ['SEC_EDGAR_USER_AGENT'] = 'Edgar/1.0 (edgar@test.com)'
            os.environ.pop('SEC_USER_AGENT', None)
            client = SECEdgarClient()
            assert client.user_agent == 'Edgar/1.0 (edgar@test.com)'


class TestRateLimiterBehavior:
    """Test rate limiter timing behavior."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_enforces_minimum_interval(self):
        """Test that rate limiter enforces minimum interval between requests."""
        # Note: Parameter is ignored due to singleton - uses global 9 req/sec (111ms interval)
        limiter = RateLimiter(requests_per_second=10.0)
        
        start_time = asyncio.get_event_loop().time()
        
        # Make 3 requests
        for _ in range(3):
            await limiter.acquire()
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Should take at least 222ms (2 intervals of 111ms for 3 requests with 9 req/sec)
        assert elapsed >= 0.2
    
    @pytest.mark.asyncio
    async def test_rate_limiter_uses_shared_instance(self):
        """Test that rate limiter uses shared singleton instance."""
        limiter = RateLimiter(requests_per_second=5.0)  # Parameter ignored due to singleton
        
        # Due to singleton pattern, all instances share the same configuration
        # The global limiter is configured for 9 req/sec
        assert limiter.min_interval == pytest.approx(1.0 / 9.0, rel=0.01)
        assert limiter is _SHARED_RATE_LIMITER
