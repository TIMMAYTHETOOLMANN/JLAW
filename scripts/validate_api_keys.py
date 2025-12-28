#!/usr/bin/env python3
"""
API Key Configuration Validator
================================

Validates all API key configurations for JLAW system.

Usage:
    python scripts/validate_api_keys.py

Exit Codes:
    0: All required keys are valid
    1: Missing or invalid required keys
    2: Configuration errors
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.secure_config import (
    print_configuration_status,
    validate_all_api_keys,
    load_dotenv_file
)


def main():
    """Main validation workflow."""
    print("\n" + "█" * 80)
    print("  JLAW API KEY CONFIGURATION VALIDATOR")
    print("  Validating API keys and service configurations")
    print("█" * 80)
    
    # Load environment
    load_dotenv_file()
    
    # Print detailed configuration status
    print_configuration_status()
    
    # Validate all keys
    print("\n" + "=" * 80)
    print("  VALIDATION RESULT")
    print("=" * 80 + "\n")
    
    all_valid, validation_results = validate_all_api_keys()
    
    if all_valid:
        print("  ✓ All required API keys are valid")
        print("  ✓ System is ready for forensic analysis")
        print("\n" + "█" * 80 + "\n")
        return 0
    else:
        print("  ✗ Configuration is invalid")
        print("\n  Required fixes:")
        
        # List specific issues
        for key_name, (is_valid, error_msg) in validation_results.items():
            if not is_valid and not os.environ.get(key_name):
                # Skip optional keys that are just not set
                if key_name in ['POLYGON_API_KEY', 'GOVINFO_API_KEY']:
                    continue
                print(f"    • {key_name}: {error_msg}")
            elif not is_valid:
                print(f"    • {key_name}: {error_msg}")
        
        print("\n  Setup instructions:")
        print("    1. Copy .env.example to .env")
        print("    2. Edit .env and replace placeholder values")
        print("    3. Run this script again to verify")
        print("\n" + "█" * 80 + "\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n✗ Validation error: {e}")
        sys.exit(2)
