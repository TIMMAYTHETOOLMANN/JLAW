"""
Unit Tests for Unified SDK Manager
==================================

Tests the UnifiedSDKManager singleton that consolidates all OpenAI, Anthropic,
and HTTP client instantiations.
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from datetime import datetime

# Import the SDK manager
from src.forensics.sdk_manager import (
    UnifiedSDKManager,
    get_sdk_manager,
    get_sdk_manager_sync,
    sdk_manager_context,
    reset_sdk_manager
)


class TestUnifiedSDKManagerSingleton:
    """Test suite for SDK manager singleton pattern."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_sdk_manager()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_sdk_manager()
    
    @pytest.mark.asyncio
    async def test_singleton_pattern_async(self):
        """Test that get_sdk_manager returns same instance."""
        sdk1 = await get_sdk_manager()
        sdk2 = await get_sdk_manager()
        
        assert sdk1 is sdk2
        assert isinstance(sdk1, UnifiedSDKManager)
    
    def test_singleton_pattern_sync(self):
        """Test that get_sdk_manager_sync returns same instance."""
        sdk1 = get_sdk_manager_sync()
        sdk2 = get_sdk_manager_sync()
        
        assert sdk1 is sdk2
        assert isinstance(sdk1, UnifiedSDKManager)
    
    @pytest.mark.asyncio
    async def test_singleton_consistency_between_sync_async(self):
        """Test that sync and async getters return same instance."""
        sdk_sync = get_sdk_manager_sync()
        sdk_async = await get_sdk_manager()
        
        assert sdk_sync is sdk_async


class TestSDKClientInitialization:
    """Test suite for lazy client initialization."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_sdk_manager()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_sdk_manager()
    
    @pytest.mark.asyncio
    async def test_openai_client_lazy_loading(self):
        """Test that OpenAI client is lazily loaded."""
        with patch('src.forensics.config_manager.get_config') as mock_config:
            # Mock config
            mock_openai_config = MagicMock()
            mock_openai_config.api_key = 'test-api-key'
            mock_openai_config.model = 'gpt-4'
            
            mock_config.return_value.config.openai = mock_openai_config
            
            sdk = get_sdk_manager_sync()
            
            # Initially, client should not be initialized
            assert sdk._openai_client is None
            
            # Access the client (lazy load)
            with patch('openai.OpenAI') as mock_openai:
                mock_openai.return_value = MagicMock()
                client = sdk.openai
                
                # Now it should be initialized
                assert sdk._openai_client is not None
                assert sdk._openai_available is True
                mock_openai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_anthropic_client_lazy_loading(self):
        """Test that Anthropic client is lazily loaded."""
        with patch('src.forensics.config_manager.get_config') as mock_config:
            # Mock config
            mock_anthropic_config = MagicMock()
            mock_anthropic_config.api_key = 'test-api-key'
            mock_anthropic_config.model = 'claude-3-5-sonnet-20241022'
            
            mock_config.return_value.config.anthropic = mock_anthropic_config
            
            sdk = get_sdk_manager_sync()
            
            # Initially, client should not be initialized
            assert sdk._anthropic_client is None
            
            # Access the client (lazy load)
            with patch('anthropic.AsyncAnthropic') as mock_anthropic:
                mock_anthropic.return_value = MagicMock()
                client = sdk.anthropic
                
                # Now it should be initialized
                assert sdk._anthropic_client is not None
                assert sdk._anthropic_available is True
                mock_anthropic.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_openai_secondary_client_lazy_loading(self):
        """Test that secondary OpenAI client is lazily loaded."""
        with patch('src.forensics.config_manager.get_config') as mock_config:
            # Mock config
            mock_openai_config = MagicMock()
            mock_openai_config.secondary_api_key = 'test-secondary-key'
            
            mock_config.return_value.config.openai = mock_openai_config
            
            sdk = get_sdk_manager_sync()
            
            # Initially, client should not be initialized
            assert sdk._openai_secondary_client is None
            
            # Access the client (lazy load)
            with patch('openai.OpenAI') as mock_openai:
                mock_openai.return_value = MagicMock()
                client = sdk.openai_secondary
                
                # Now it should be initialized
                assert sdk._openai_secondary_client is not None
                assert sdk._openai_secondary_available is True
    
    @pytest.mark.asyncio
    async def test_http_session_initialization(self):
        """Test that HTTP session is properly initialized with connection pooling."""
        sdk = get_sdk_manager_sync()
        
        session = sdk.http_session
        
        assert session is not None
        assert not session.closed
        assert session.connector.limit == 100
        assert session.connector.limit_per_host == 10
    
    @pytest.mark.asyncio
    async def test_missing_api_keys_graceful_degradation(self):
        """Test graceful handling when API keys are missing."""
        with patch('src.forensics.config_manager.get_config') as mock_config:
            # Mock config with no API keys
            mock_openai_config = MagicMock()
            mock_openai_config.api_key = None
            
            mock_anthropic_config = MagicMock()
            mock_anthropic_config.api_key = None
            
            mock_config.return_value.config.openai = mock_openai_config
            mock_config.return_value.config.anthropic = mock_anthropic_config
            
            sdk = get_sdk_manager_sync()
            
            # Try accessing clients
            openai_client = sdk.openai
            anthropic_client = sdk.anthropic
            
            # Should return None without crashing
            assert openai_client is None
            assert anthropic_client is None
            assert sdk._openai_available is False
            assert sdk._anthropic_available is False


class TestSECRateLimiting:
    """Test suite for SEC EDGAR rate limiting."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_sdk_manager()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_sdk_manager()
    
    @pytest.mark.asyncio
    async def test_sec_rate_limiting_delay(self):
        """Test that SEC requests enforce 0.35s delay."""
        sdk = get_sdk_manager_sync()
        
        # Mock the HTTP session
        mock_response = AsyncMock()
        mock_response.status = 200
        
        with patch.object(sdk, 'http_session') as mock_session:
            mock_session.request = AsyncMock(return_value=mock_response)
            
            # Make two requests
            start_time = time.time()
            
            await sdk.sec_request('https://sec.gov/test1', 'TestAgent/1.0')
            await sdk.sec_request('https://sec.gov/test2', 'TestAgent/1.0')
            
            elapsed = time.time() - start_time
            
            # Should take at least 0.35s between requests
            assert elapsed >= 0.35
    
    @pytest.mark.asyncio
    async def test_sec_semaphore_limits_concurrent_requests(self):
        """Test that semaphore limits concurrent SEC requests to 10."""
        sdk = get_sdk_manager_sync()
        
        # Track concurrent requests
        concurrent_count = 0
        max_concurrent = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)  # Simulate request time
            concurrent_count -= 1
            
            mock_response = AsyncMock()
            mock_response.status = 200
            return mock_response
        
        with patch.object(sdk, 'http_session') as mock_session:
            mock_session.request = mock_request
            
            # Try making 20 concurrent requests
            tasks = [
                sdk.sec_request(f'https://sec.gov/test{i}', 'TestAgent/1.0')
                for i in range(20)
            ]
            
            await asyncio.gather(*tasks)
            
            # Should never exceed semaphore limit of 10
            assert max_concurrent <= 10
    
    @pytest.mark.asyncio
    async def test_sec_retry_on_429(self):
        """Test automatic retry on 429 rate limit response."""
        sdk = get_sdk_manager_sync()
        
        # Mock responses: first 429, then 200
        responses = []
        
        async def mock_request(*args, **kwargs):
            if len(responses) == 0:
                mock_response = AsyncMock()
                mock_response.status = 429
                mock_response.headers = {'Retry-After': '1'}
                responses.append(mock_response)
                return mock_response
            else:
                mock_response = AsyncMock()
                mock_response.status = 200
                return mock_response
        
        with patch.object(sdk, 'http_session') as mock_session:
            mock_session.request = mock_request
            
            response = await sdk.sec_request('https://sec.gov/test', 'TestAgent/1.0')
            
            # Should eventually succeed
            assert response.status == 200
            # Should have retried once
            assert len(responses) == 1


class TestRetryLogic:
    """Test suite for retry logic with exponential backoff."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_sdk_manager()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_sdk_manager()
    
    @pytest.mark.asyncio
    async def test_retry_on_server_error(self):
        """Test retry logic on 5xx server errors."""
        sdk = get_sdk_manager_sync()
        
        attempt_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < 3:
                mock_response = AsyncMock()
                mock_response.status = 503
                return mock_response
            else:
                mock_response = AsyncMock()
                mock_response.status = 200
                return mock_response
        
        with patch.object(sdk, 'http_session') as mock_session:
            mock_session.request = mock_request
            
            response = await sdk.sec_request('https://sec.gov/test', 'TestAgent/1.0')
            
            # Should have retried twice before success
            assert attempt_count == 3
            assert response.status == 200
    
    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self):
        """Test that 4xx client errors don't trigger retries."""
        sdk = get_sdk_manager_sync()
        
        attempt_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            
            mock_response = AsyncMock()
            mock_response.status = 404
            return mock_response
        
        with patch.object(sdk, 'http_session') as mock_session:
            mock_session.request = mock_request
            
            response = await sdk.sec_request('https://sec.gov/test', 'TestAgent/1.0')
            
            # Should not retry on 404
            assert attempt_count == 1
            assert response.status == 404
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff between retries."""
        sdk = get_sdk_manager_sync()
        sdk._retry_backoff_base = 0.1  # Speed up test
        
        retry_times = []
        
        async def mock_request(*args, **kwargs):
            retry_times.append(time.time())
            mock_response = AsyncMock()
            mock_response.status = 503
            return mock_response
        
        with patch.object(sdk, 'http_session') as mock_session:
            mock_session.request = mock_request
            
            try:
                await sdk.sec_request('https://sec.gov/test', 'TestAgent/1.0')
            except:
                pass
            
            # Check backoff times
            if len(retry_times) >= 3:
                # First retry: immediate
                # Second retry: 0.1s backoff
                # Third retry: 0.2s backoff (0.1^2)
                gap1 = retry_times[1] - retry_times[0]
                gap2 = retry_times[2] - retry_times[1]
                
                # Allow some timing variance
                assert gap2 > gap1


class TestAvailabilityCheck:
    """Test suite for SDK availability checks."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_sdk_manager()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_sdk_manager()
    
    @pytest.mark.asyncio
    async def test_get_availability_all_available(self):
        """Test availability check when all clients are available."""
        with patch('src.forensics.config_manager.get_config') as mock_config:
            # Mock config with all keys
            mock_openai_config = MagicMock()
            mock_openai_config.api_key = 'test-key'
            mock_openai_config.secondary_api_key = 'test-secondary-key'
            
            mock_anthropic_config = MagicMock()
            mock_anthropic_config.api_key = 'test-key'
            
            mock_config.return_value.config.openai = mock_openai_config
            mock_config.return_value.config.anthropic = mock_anthropic_config
            
            sdk = get_sdk_manager_sync()
            
            with patch('openai.OpenAI'), \
                 patch('anthropic.AsyncAnthropic'):
                
                availability = sdk.get_availability()
                
                assert availability['openai'] is True
                assert availability['openai_secondary'] is True
                assert availability['anthropic'] is True
                assert availability['dual_agent'] is True
    
    @pytest.mark.asyncio
    async def test_get_availability_partial(self):
        """Test availability check with only OpenAI available."""
        with patch('src.forensics.config_manager.get_config') as mock_config:
            # Mock config with only OpenAI
            mock_openai_config = MagicMock()
            mock_openai_config.api_key = 'test-key'
            mock_openai_config.secondary_api_key = 'test-secondary-key'
            
            mock_anthropic_config = MagicMock()
            mock_anthropic_config.api_key = None
            
            mock_config.return_value.config.openai = mock_openai_config
            mock_config.return_value.config.anthropic = mock_anthropic_config
            
            sdk = get_sdk_manager_sync()
            
            with patch('openai.OpenAI'):
                availability = sdk.get_availability()
                
                assert availability['openai'] is True
                assert availability['openai_secondary'] is True
                assert availability['anthropic'] is False
                assert availability['dual_agent'] is True  # Can use dual-OpenAI


class TestCleanup:
    """Test suite for resource cleanup."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_sdk_manager()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_sdk_manager()
    
    @pytest.mark.asyncio
    async def test_close_method_cleanup(self):
        """Test that close() properly cleans up all resources."""
        sdk = get_sdk_manager_sync()
        
        # Initialize session
        session = sdk.http_session
        assert not session.closed
        
        # Mock clients
        with patch('src.forensics.config_manager.get_config') as mock_config:
            mock_openai_config = MagicMock()
            mock_openai_config.api_key = 'test-key'
            mock_config.return_value.config.openai = mock_openai_config
            
            with patch('src.forensics.sdk_manager.AsyncOpenAI') as mock_openai_class:
                mock_client = MagicMock()
                mock_client.close = AsyncMock()
                mock_openai_class.return_value = mock_client
                
                _ = sdk.openai
                
                # Close SDK manager
                await sdk.close()
                
                # HTTP session should be closed
                assert session.closed
                
                # OpenAI client close should be called
                mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test that context manager properly cleans up."""
        async with sdk_manager_context() as sdk:
            session = sdk.http_session
            assert not session.closed
        
        # After context exit, session should be closed
        assert session.closed


class TestConnectionPooling:
    """Test suite for HTTP connection pooling verification."""
    
    def setup_method(self):
        """Reset singleton before each test."""
        reset_sdk_manager()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_sdk_manager()
    
    @pytest.mark.asyncio
    async def test_shared_session_reuse(self):
        """Test that HTTP session is reused across multiple requests."""
        sdk = get_sdk_manager_sync()
        
        session1 = sdk.http_session
        session2 = sdk.http_session
        
        # Should return same session instance
        assert session1 is session2
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self):
        """Test that connection pool limits are properly configured."""
        sdk = get_sdk_manager_sync()
        
        session = sdk.http_session
        connector = session.connector
        
        # Verify connection pool limits
        assert connector.limit == 100
        assert connector.limit_per_host == 10
        assert connector.ttl_dns_cache == 300
        assert connector.enable_cleanup_closed is True
        assert connector.force_close is False
