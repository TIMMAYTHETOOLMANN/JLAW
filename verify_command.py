#!/usr/bin/env python3
"""
Verification script for JLAW_UNIFIED.py command-line interface.

This script verifies that the company lookup functionality works correctly
for the command:
    python JLAW_UNIFIED.py --cik 320187 --company "NIKE" --year 2019 --auto
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import COMPANY_LOOKUP from JLAW_UNIFIED.py (single source of truth)
try:
    from JLAW_UNIFIED import COMPANY_LOOKUP
except ImportError as e:
    print(f"ERROR: Could not import COMPANY_LOOKUP from JLAW_UNIFIED.py: {e}")
    print("This script must be run from the JLAW root directory.")
    sys.exit(1)

def verify_company_lookup():
    """Verify company lookup works for common cases."""
    
    print("=" * 70)
    print("JLAW Company Lookup Verification")
    print("=" * 70)
    print()
    
    # Test case 1: --company "NIKE"
    test_cases = [
        ("NIKE", "320187", "NIKE, Inc."),
        ("nike", "320187", "NIKE, Inc."),  # Test case insensitive
        ("NKE", "320187", "NIKE, Inc."),   # Test ticker
        ("APPLE", "320193", "Apple Inc."),
        ("AAPL", "320193", "Apple Inc."),
    ]
    
    all_passed = True
    
    for company_input, expected_cik, expected_name in test_cases:
        if company_input.upper() in COMPANY_LOOKUP:
            cik, company_name = COMPANY_LOOKUP[company_input.upper()]
            
            if cik == expected_cik and company_name == expected_name:
                print(f"✓ PASS: '{company_input}' -> CIK={cik}, Name='{company_name}'")
            else:
                print(f"✗ FAIL: '{company_input}' -> Expected CIK={expected_cik}, Name='{expected_name}'")
                print(f"         Got CIK={cik}, Name='{company_name}'")
                all_passed = False
        else:
            print(f"✗ FAIL: '{company_input}' not found in COMPANY_LOOKUP")
            all_passed = False
    
    print()
    print("=" * 70)
    
    if all_passed:
        print("✓ All tests PASSED")
        print()
        print("The command should work correctly:")
        print("  python JLAW_UNIFIED.py --cik 320187 --company \"NIKE\" --year 2019 --auto")
        print()
        print("This will use:")
        print("  - CIK: 320187")
        print("  - Company Name: NIKE, Inc.")
        print("  - Year: 2019")
        print("  - Auto mode: enabled")
        return 0
    else:
        print("✗ Some tests FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(verify_company_lookup())
