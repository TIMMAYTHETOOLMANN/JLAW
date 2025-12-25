"""
Test Suite for SEC Acquisition System Enhancements
==================================================

Tests for:
- Rate limiter behavior and cooldown
- CIK/accession normalization
- Triple-hash integrity verification
- XBRL namespace handling
- Mock mode functionality
"""

import pytest
import asyncio
import time
from datetime import datetime

# Import modules to test
from src.integrations.sec_edgar.rate_limiter import RateLimiter, get_shared_rate_limiter
from src.integrations.sec_edgar.utils import (
    normalize_cik,
    strip_cik_leading_zeros,
    format_accession_number,
    build_edgar_document_url,
    build_edgar_index_url,
    validate_cik,
    validate_accession_number
)
from src.integrations.sec_edgar.models import IntegrityHashes


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def test_singleton_pattern(self):
        """Test that RateLimiter is a singleton."""
        limiter1 = RateLimiter()
        limiter2 = RateLimiter()
        assert limiter1 is limiter2, "RateLimiter should be a singleton"
    
    def test_get_shared_rate_limiter(self):
        """Test that get_shared_rate_limiter returns the singleton."""
        limiter1 = get_shared_rate_limiter()
        limiter2 = get_shared_rate_limiter()
        assert limiter1 is limiter2, "Should return same singleton instance"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiter enforces minimum interval."""
        limiter = RateLimiter()
        
        start_time = time.time()
        
        # Make 3 requests
        for _ in range(3):
            await limiter.acquire()
        
        elapsed = time.time() - start_time
        
        # Should take at least 2 * min_interval (111ms * 2 = 222ms)
        expected_min = 2 * limiter.MIN_INTERVAL
        assert elapsed >= expected_min, f"Rate limiter should enforce {expected_min}s minimum, but took {elapsed}s"
    
    def test_cooldown_activation(self):
        """Test cooldown activation."""
        limiter = RateLimiter()
        
        # Activate cooldown
        limiter.activate_cooldown("Test cooldown")
        
        # Check cooldown state
        assert limiter.is_in_cooldown(), "Should be in cooldown after activation"
        assert limiter.stats.cooldown_activations >= 1, "Should track cooldown activation"
    
    @pytest.mark.asyncio
    async def test_cooldown_enforcement(self):
        """Test that cooldown blocks requests."""
        limiter = RateLimiter()
        
        # Set a short cooldown for testing (override class constant)
        original_cooldown = limiter.COOLDOWN_PERIOD
        limiter.COOLDOWN_PERIOD = 1  # 1 second for testing
        
        try:
            limiter.activate_cooldown("Test cooldown")
            
            start_time = time.time()
            await limiter.acquire()
            elapsed = time.time() - start_time
            
            # Should wait at least the cooldown period
            assert elapsed >= 0.9, f"Should wait at least {limiter.COOLDOWN_PERIOD}s during cooldown"
        finally:
            # Restore original cooldown period
            limiter.COOLDOWN_PERIOD = original_cooldown


class TestCIKNormalization:
    """Test CIK normalization utilities."""
    
    def test_normalize_cik_with_zeros(self):
        """Test normalizing CIK that already has zeros."""
        assert normalize_cik('0000320193') == '0000320193'
    
    def test_normalize_cik_without_zeros(self):
        """Test normalizing CIK without leading zeros."""
        assert normalize_cik('320193') == '0000320193'
    
    def test_normalize_cik_from_integer(self):
        """Test normalizing CIK from integer."""
        assert normalize_cik(320193) == '0000320193'
    
    def test_strip_cik_leading_zeros(self):
        """Test stripping leading zeros from CIK."""
        assert strip_cik_leading_zeros('0000320193') == '320193'
        assert strip_cik_leading_zeros('0000000000') == '0'
    
    def test_validate_cik(self):
        """Test CIK validation."""
        assert validate_cik('0000320193') == True
        assert validate_cik('320193') == True
        assert validate_cik('invalid') == False
        assert validate_cik('12345678901') == False  # Too long


class TestAccessionNormalization:
    """Test accession number normalization."""
    
    def test_format_with_dashes(self):
        """Test formatting accession number with dashes."""
        result = format_accession_number('000123456724000001', with_dashes=True)
        assert result == '0001234567-24-000001'
    
    def test_format_without_dashes(self):
        """Test formatting accession number without dashes."""
        result = format_accession_number('0001234567-24-000001', with_dashes=False)
        assert result == '000123456724000001'
    
    def test_format_idempotent(self):
        """Test that formatting is idempotent."""
        original = '0001234567-24-000001'
        result1 = format_accession_number(original, with_dashes=True)
        result2 = format_accession_number(result1, with_dashes=True)
        assert result1 == result2
    
    def test_validate_accession_number(self):
        """Test accession number validation."""
        assert validate_accession_number('0001234567-24-000001') == True
        assert validate_accession_number('000123456724000001') == True
        assert validate_accession_number('invalid') == False
        assert validate_accession_number('123') == False  # Too short


class TestURLBuilders:
    """Test URL building utilities."""
    
    def test_build_edgar_document_url(self):
        """Test building EDGAR document URL."""
        url = build_edgar_document_url('320193', '0001234567-24-000001', 'form4.xml')
        expected = 'https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/form4.xml'
        assert url == expected
    
    def test_build_edgar_index_url(self):
        """Test building EDGAR index.json URL."""
        url = build_edgar_index_url('320193', '0001234567-24-000001')
        expected = 'https://www.sec.gov/Archives/edgar/data/320193/000123456724000001/index.json'
        assert url == expected


class TestIntegrityHashes:
    """Test triple-hash integrity verification."""
    
    def test_integrity_hashes_creation(self):
        """Test creating integrity hashes."""
        hashes = IntegrityHashes(
            sha256='a' * 64,
            sha3_512='b' * 128,
            blake2b='c' * 128
        )
        assert hashes.sha256 == 'a' * 64
        assert hashes.sha3_512 == 'b' * 128
        assert hashes.blake2b == 'c' * 128
    
    def test_integrity_hashes_verify_match(self):
        """Test verifying matching hashes."""
        hashes1 = IntegrityHashes(
            sha256='a' * 64,
            sha3_512='b' * 128,
            blake2b='c' * 128
        )
        hashes2 = IntegrityHashes(
            sha256='a' * 64,
            sha3_512='b' * 128,
            blake2b='c' * 128
        )
        assert hashes1.verify(hashes2) == True
    
    def test_integrity_hashes_verify_mismatch(self):
        """Test verifying mismatched hashes."""
        hashes1 = IntegrityHashes(
            sha256='a' * 64,
            sha3_512='b' * 128,
            blake2b='c' * 128
        )
        hashes2 = IntegrityHashes(
            sha256='x' * 64,
            sha3_512='b' * 128,
            blake2b='c' * 128
        )
        assert hashes1.verify(hashes2) == False
    
    def test_integrity_hashes_to_dict(self):
        """Test converting integrity hashes to dict."""
        hashes = IntegrityHashes(
            sha256='a' * 64,
            sha3_512='b' * 128,
            blake2b='c' * 128
        )
        result = hashes.to_dict()
        assert result['sha256'] == 'a' * 64
        assert result['sha3_512'] == 'b' * 128
        assert result['blake2b'] == 'c' * 128


class TestXBRLNamespaces:
    """Test XBRL namespace handling."""
    
    def test_xbrl_namespaces_defined(self):
        """Test that XBRL namespaces are properly defined."""
        from src.forensics.docsgpt.document_parser import XBRLParser
        
        parser = XBRLParser()
        assert 'xbrli' in parser.XBRL_NAMESPACES
        assert 'us-gaap' in parser.XBRL_NAMESPACES
        assert 'dei' in parser.XBRL_NAMESPACES
        assert 'link' in parser.XBRL_NAMESPACES
        assert 'ifrs-full' in parser.XBRL_NAMESPACES
    
    def test_xbrl_namespace_urls(self):
        """Test that XBRL namespace URLs are correct."""
        from src.forensics.docsgpt.document_parser import XBRLParser
        
        parser = XBRLParser()
        assert parser.XBRL_NAMESPACES['xbrli'] == 'http://www.xbrl.org/2003/instance'
        assert 'fasb.org/us-gaap' in parser.XBRL_NAMESPACES['us-gaap']
        assert 'xbrl.sec.gov/dei' in parser.XBRL_NAMESPACES['dei']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
