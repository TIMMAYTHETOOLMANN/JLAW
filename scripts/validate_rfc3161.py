#!/usr/bin/env python3
"""
RFC 3161 Timestamp Authority Validation Script
==============================================

This script validates RFC 3161 timestamp authority connectivity and
functionality to ensure court-admissible evidence chain integrity.

Usage:
    python scripts/validate_rfc3161.py

Features:
    - Library import validation
    - TSA endpoint connectivity testing
    - Test timestamp generation
    - Token parsing and validation
    - Hash verification

Exit Codes:
    0: All validations passed
    1: Library import failed
    2: No TSA connectivity
    3: Timestamp generation failed
    4: Token validation failed
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_status(message: str, success: bool = True):
    """Print status message with emoji."""
    symbol = "✓" if success else "✗"
    print(f"  {symbol} {message}")


async def validate_rfc3161_library():
    """Validate RFC 3161 library imports."""
    print_header("STEP 1: Library Import Validation")
    
    try:
        import rfc3161ng
        print_status(f"rfc3161ng library imported successfully (version: {rfc3161ng.__version__ if hasattr(rfc3161ng, '__version__') else 'unknown'})")
        
        import cryptography
        print_status(f"cryptography library imported successfully (version: {cryptography.__version__})")
        
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        print_status("RFC3161Client imported successfully")
        
        return True, None
        
    except ImportError as e:
        print_status(f"Library import failed: {e}", success=False)
        print("\n  SOLUTION:")
        print("    pip install -r requirements.txt")
        print("    # or")
        print("    pip install rfc3161ng>=2.1.3 cryptography>=41.0.0")
        return False, str(e)


async def validate_tsa_connectivity():
    """Validate TSA endpoint connectivity."""
    print_header("STEP 2: TSA Endpoint Connectivity")
    
    try:
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        # Test primary TSA
        client = RFC3161Client(authority="freetsa", timeout=15)
        
        print("  Testing all available TSA endpoints...")
        connectivity = await client.validate_tsa_connectivity(test_all=True)
        
        if connectivity:
            print_status("At least one TSA endpoint is reachable")
            return True, None
        else:
            print_status("No TSA endpoints are reachable", success=False)
            print("\n  TROUBLESHOOTING:")
            print("    1. Check internet connectivity")
            print("    2. Verify firewall allows HTTP/HTTPS traffic")
            print("    3. Try different TSA: freetsa, sectigo, digicert")
            print("    4. Check if TSA services are operational")
            return False, "No TSA connectivity"
            
    except Exception as e:
        print_status(f"Connectivity test failed: {e}", success=False)
        return False, str(e)


async def validate_timestamp_generation():
    """Validate timestamp token generation."""
    print_header("STEP 3: Timestamp Token Generation")
    
    try:
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        client = RFC3161Client(authority="freetsa", timeout=15, max_retries=3)
        
        # Generate test data
        test_data = b"JLAW_RFC3161_VALIDATION_TEST_DATA"
        print(f"  Generating timestamp for test data: {test_data[:40]}...")
        
        # Try with fallback
        token = await client.timestamp_with_retry(
            test_data,
            fallback_authorities=["sectigo", "digicert"],
            strict_mode=True
        )
        
        if token and token.token_data:
            print_status("Timestamp token generated successfully")
            print(f"    Authority: {token.authority}")
            print(f"    Generation Time: {token.gen_time}")
            print(f"    Hash Algorithm: {token.hash_algorithm}")
            print(f"    Message Imprint: {token.message_imprint[:32]}...")
            return True, token
        else:
            print_status("Empty timestamp token received", success=False)
            return False, "Empty token"
            
    except Exception as e:
        print_status(f"Timestamp generation failed: {e}", success=False)
        return False, str(e)


async def validate_token_verification(token, test_data: bytes):
    """Validate timestamp token verification."""
    print_header("STEP 4: Token Validation and Hash Verification")
    
    try:
        from src.core.evidence_chain.rfc3161_client import RFC3161Client
        
        # Verify token against original data
        is_valid = RFC3161Client.verify_timestamp(token, test_data)
        
        if is_valid:
            print_status("Token verification passed")
            print_status("Hash verification passed")
            return True, None
        else:
            print_status("Token verification failed", success=False)
            return False, "Token verification failed"
            
    except Exception as e:
        print_status(f"Verification failed: {e}", success=False)
        return False, str(e)


async def main():
    """Main validation workflow."""
    print("\n" + "█" * 80)
    print("  JLAW RFC 3161 TIMESTAMP AUTHORITY VALIDATION")
    print("  Court-Admissible Evidence Chain Integrity Check")
    print("█" * 80)
    
    results = []
    
    # Step 1: Library Import
    success, error = await validate_rfc3161_library()
    results.append(("Library Import", success, error))
    if not success:
        print_header("VALIDATION FAILED")
        print_status("Cannot proceed without rfc3161ng library", success=False)
        return 1
    
    # Step 2: TSA Connectivity
    success, error = await validate_tsa_connectivity()
    results.append(("TSA Connectivity", success, error))
    if not success:
        print_header("VALIDATION FAILED")
        print_status("Cannot proceed without TSA connectivity", success=False)
        return 2
    
    # Step 3: Timestamp Generation
    test_data = b"JLAW_RFC3161_VALIDATION_TEST_DATA"
    success, token = await validate_timestamp_generation()
    results.append(("Timestamp Generation", success, token if not success else None))
    if not success:
        print_header("VALIDATION FAILED")
        print_status("Timestamp generation failed", success=False)
        return 3
    
    # Step 4: Token Verification
    success, error = await validate_token_verification(token, test_data)
    results.append(("Token Verification", success, error))
    if not success:
        print_header("VALIDATION FAILED")
        print_status("Token verification failed", success=False)
        return 4
    
    # Summary
    print_header("VALIDATION SUMMARY")
    all_passed = all(r[1] for r in results)
    
    for check_name, passed, _ in results:
        print_status(f"{check_name}: {'PASSED' if passed else 'FAILED'}", success=passed)
    
    if all_passed:
        print("\n" + "█" * 80)
        print("  ✓ RFC 3161 VALIDATION COMPLETE - ALL CHECKS PASSED")
        print("  ✓ System ready for court-admissible timestamp generation")
        print("  ✓ Evidence chain integrity can be maintained")
        print("█" * 80 + "\n")
        return 0
    else:
        print("\n" + "█" * 80)
        print("  ✗ RFC 3161 VALIDATION FAILED")
        print("  ✗ Court-admissible timestamps cannot be generated")
        print("  ✗ Review errors above and apply suggested fixes")
        print("█" * 80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
