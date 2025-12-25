"""
SEC Filing Acquisition System - Usage Examples
==============================================

This file demonstrates the enhanced SEC filing acquisition system
with all the remediation features implemented:

1. Rate limiting with automatic cooldown
2. Triple-hash integrity verification
3. CIK/accession normalization
4. Enhanced XBRL parsing with contexts
5. User-Agent validation

Run this file to verify the system is working correctly.
"""

import asyncio
import logging
from datetime import date
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def example_1_rate_limiter():
    """Example 1: Using the shared rate limiter."""
    from src.integrations.sec_edgar.rate_limiter import get_shared_rate_limiter
    
    logger.info("=" * 60)
    logger.info("Example 1: Shared Rate Limiter")
    logger.info("=" * 60)
    
    rate_limiter = get_shared_rate_limiter()
    
    # Get stats
    stats = rate_limiter.get_stats()
    logger.info(f"Rate Limiter Stats: {stats.to_dict()}")
    
    # Make a few requests
    logger.info("Making 3 rate-limited requests...")
    for i in range(3):
        await rate_limiter.acquire()
        logger.info(f"  Request {i+1} completed")
    
    # Check if in cooldown
    logger.info(f"In cooldown: {rate_limiter.is_in_cooldown()}")
    
    logger.info("✅ Rate limiter example completed\n")


def example_2_cik_normalization():
    """Example 2: CIK and accession number normalization."""
    from src.integrations.sec_edgar.utils import (
        normalize_cik,
        strip_cik_leading_zeros,
        format_accession_number,
        build_edgar_document_url,
        validate_cik
    )
    
    logger.info("=" * 60)
    logger.info("Example 2: CIK & Accession Normalization")
    logger.info("=" * 60)
    
    # CIK normalization
    cik_variants = ['320193', '0000320193', 320193]
    logger.info("CIK Normalization:")
    for variant in cik_variants:
        normalized = normalize_cik(variant)
        stripped = strip_cik_leading_zeros(variant)
        valid = validate_cik(variant)
        logger.info(f"  {variant} -> normalized: {normalized}, stripped: {stripped}, valid: {valid}")
    
    # Accession normalization
    logger.info("\nAccession Number Formatting:")
    accession = '0001234567-24-000001'
    with_dashes = format_accession_number(accession, with_dashes=True)
    without_dashes = format_accession_number(accession, with_dashes=False)
    logger.info(f"  Original: {accession}")
    logger.info(f"  With dashes: {with_dashes}")
    logger.info(f"  Without dashes: {without_dashes}")
    
    # URL building
    logger.info("\nURL Building:")
    url = build_edgar_document_url('320193', accession, 'form4.xml')
    logger.info(f"  Document URL: {url}")
    
    logger.info("✅ Normalization example completed\n")


def example_3_integrity_hashes():
    """Example 3: Triple-hash integrity verification."""
    from src.integrations.sec_edgar.models import IntegrityHashes
    import hashlib
    
    logger.info("=" * 60)
    logger.info("Example 3: Triple-Hash Integrity Verification")
    logger.info("=" * 60)
    
    # Sample content
    content = "This is a sample SEC filing document."
    content_bytes = content.encode('utf-8')
    
    # Compute triple-hash
    hashes = IntegrityHashes(
        sha256=hashlib.sha256(content_bytes).hexdigest(),
        sha3_512=hashlib.sha3_512(content_bytes).hexdigest(),
        blake2b=hashlib.blake2b(content_bytes).hexdigest()
    )
    
    logger.info(f"Content: {content}")
    logger.info(f"Triple-Hash:")
    logger.info(f"  SHA-256:   {hashes.sha256[:32]}...")
    logger.info(f"  SHA3-512:  {hashes.sha3_512[:32]}...")
    logger.info(f"  BLAKE2b:   {hashes.blake2b[:32]}...")
    
    # Verify integrity
    hashes2 = IntegrityHashes(
        sha256=hashlib.sha256(content_bytes).hexdigest(),
        sha3_512=hashlib.sha3_512(content_bytes).hexdigest(),
        blake2b=hashlib.blake2b(content_bytes).hexdigest()
    )
    
    logger.info(f"\nIntegrity verification: {hashes.verify(hashes2)}")
    logger.info("✅ Integrity hash example completed\n")


def example_4_xbrl_namespaces():
    """Example 4: XBRL namespace handling."""
    from src.forensics.docsgpt.document_parser import XBRLParser
    
    logger.info("=" * 60)
    logger.info("Example 4: XBRL Namespace Handling")
    logger.info("=" * 60)
    
    parser = XBRLParser()
    
    logger.info("Supported XBRL Namespaces:")
    for prefix, uri in parser.XBRL_NAMESPACES.items():
        logger.info(f"  {prefix:15s} -> {uri}")
    
    logger.info("\n✅ XBRL namespace example completed\n")


def example_5_sec_validation():
    """Example 5: SEC configuration validation."""
    from config.secure_config import validate_sec_configuration, validate_sec_user_agent
    
    logger.info("=" * 60)
    logger.info("Example 5: SEC Configuration Validation")
    logger.info("=" * 60)
    
    # Test various User-Agent formats
    test_agents = [
        "MyCompany/1.0 (admin@company.com)",
        "TestApp admin@test.org",
        "InvalidAgent",  # No email
        "YourCompany contact@your-email.org",  # Placeholder
    ]
    
    logger.info("User-Agent Validation Tests:")
    for agent in test_agents:
        is_valid, error = validate_sec_user_agent(agent)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        logger.info(f"  {status}: {agent[:40]}...")
        if error:
            logger.info(f"    Error: {error[:80]}...")
    
    # Validate full SEC configuration
    logger.info("\nFull SEC Configuration Validation:")
    is_valid, errors = validate_sec_configuration()
    if is_valid:
        logger.info("  ✅ SEC configuration is valid")
    else:
        logger.info("  ❌ SEC configuration has errors:")
        for error in errors[:3]:  # Show first 3 errors
            logger.info(f"    - {error[:80]}...")
    
    logger.info("\n✅ SEC validation example completed\n")


def example_6_ai_analyzer():
    """Example 6: AI analyzer for SEC filings."""
    from src.forensics.ai_analyzer import SECFilingAnalyzer, SDKProvider
    
    logger.info("=" * 60)
    logger.info("Example 6: AI-Powered SEC Filing Analysis")
    logger.info("=" * 60)
    
    analyzer = SECFilingAnalyzer(provider=SDKProvider.OPENAI)
    
    # Sample 10-K content
    sample_content = """
    ITEM 1. BUSINESS
    We are a technology company...
    
    ITEM 1A. RISK FACTORS
    Our business faces significant risks including:
    - Market competition may impact our revenue
    - Regulatory changes could affect operations
    - Cybersecurity threats pose ongoing challenges
    
    ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS
    Revenue increased by 15% year-over-year...
    """
    
    # Token counting
    token_count = analyzer.count_tokens(sample_content)
    logger.info(f"Sample content token count: {token_count}")
    
    # Section chunking
    chunks = analyzer.chunk_by_sections(sample_content, max_chunk_size=1000)
    logger.info(f"\nChunked into {len(chunks)} sections:")
    for chunk in chunks:
        logger.info(f"  - {chunk.section}: {chunk.token_count} tokens")
    
    # Extract risk factors
    risk_factors = analyzer.extract_risk_factors(sample_content)
    logger.info(f"\nExtracted {len(risk_factors)} risk factors:")
    for i, risk in enumerate(risk_factors[:3], 1):
        logger.info(f"  {i}. {risk[:60]}...")
    
    logger.info("\n✅ AI analyzer example completed\n")


async def main():
    """Run all examples."""
    logger.info("=" * 60)
    logger.info("SEC Filing Acquisition System - Usage Examples")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # Run examples
        await example_1_rate_limiter()
        example_2_cik_normalization()
        example_3_integrity_hashes()
        example_4_xbrl_namespaces()
        example_5_sec_validation()
        example_6_ai_analyzer()
        
        logger.info("=" * 60)
        logger.info("✅ All examples completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
