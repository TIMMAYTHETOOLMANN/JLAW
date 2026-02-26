#!/usr/bin/env python3
"""
JLAW Setup Verification Script

This script checks that all necessary components are configured
before running JLAW_UNIFIED.py commands.
"""

import sys
import os
from pathlib import Path

def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    print("\n" + "=" * 70)
    print("1. Checking Environment Configuration")
    print("=" * 70)
    
    if env_path.exists():
        print("✓ .env file exists")
        
        # Check for SEC_USER_AGENT
        with open(env_path, 'r') as f:
            content = f.read()
            
        if "SEC_USER_AGENT=" in content:
            # Extract the value
            for line in content.split('\n'):
                if line.startswith('SEC_USER_AGENT='):
                    value = line.split('=', 1)[1].strip()
                    if value and "your-email@company.com" not in value.lower():
                        print(f"✓ SEC_USER_AGENT is configured: {value[:50]}...")
                        return True
                    else:
                        print("✗ SEC_USER_AGENT needs to be configured")
                        print("  Please edit .env and set your organization name and email")
                        print("  Example: SEC_USER_AGENT=YourCompany/1.0 (your-email@company.com)")
                        return False
        else:
            print("✗ SEC_USER_AGENT not found in .env")
            return False
    else:
        print("✗ .env file not found")
        if env_example_path.exists():
            print("  → Run: cp .env.example .env")
            print("  → Then edit .env to set SEC_USER_AGENT")
        else:
            print("  → .env.example not found either!")
        return False

def check_dependencies():
    """Check if critical dependencies are installed."""
    print("\n" + "=" * 70)
    print("2. Checking Critical Dependencies")
    print("=" * 70)
    
    # Map package names to their import names
    # These are critical dependencies for basic JLAW operation
    critical_deps = {
        "aiohttp": "aiohttp",           # SEC API client
        "pandas": "pandas",              # Data analysis
        "numpy": "numpy",                # Numerical computing
        "psutil": "psutil",              # System monitoring
        "python-dotenv": "dotenv",       # Environment configuration
        "beautifulsoup4": "bs4",         # HTML/XML parsing (SEC filings)
        "aiolimiter": "aiolimiter",      # Rate limiting for SEC API
    }
    
    missing = []
    
    for package_name, import_name in critical_deps.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"✗ {package_name} (missing)")
            missing.append(package_name)
    
    if missing:
        print(f"\n✗ {len(missing)} dependencies missing")
        print("  → Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All critical dependencies installed")
        return True

def check_output_directory():
    """Check/create output directory."""
    print("\n" + "=" * 70)
    print("3. Checking Output Directory")
    print("=" * 70)
    
    output_dir = Path("output")
    
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            print("✓ Created output directory")
            return True
        except Exception as e:
            print(f"✗ Could not create output directory: {e}")
            return False
    else:
        print("✓ Output directory exists")
        return True

def print_example_commands():
    """Print example commands."""
    print("\n" + "=" * 70)
    print("Example Commands")
    print("=" * 70)
    
    print("\n# Interactive mode (recommended for first-time users)")
    print("python JLAW_UNIFIED.py")
    
    print("\n# CLI mode with NIKE")
    print("python JLAW_UNIFIED.py --cik 320187 --company \"NIKE\" --year 2019 --auto")
    
    print("\n# CLI mode with Apple")
    print("python JLAW_UNIFIED.py --cik 320193 --company \"APPLE\" --year 2019 --auto")
    
    print("\n# Strict mode (DOJ-grade with phase gates)")
    print("python JLAW_UNIFIED.py --cik 320187 --company \"NIKE\" --year 2019 --strict --auto")

def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("JLAW Setup Verification")
    print("=" * 70)
    
    checks = [
        check_env_file(),
        check_dependencies(),
        check_output_directory(),
    ]
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    if all(checks):
        print("\n✓ All checks PASSED")
        print("\nYour JLAW installation is ready to use!")
        print_example_commands()
        return 0
    else:
        print("\n✗ Some checks FAILED")
        print("\nPlease fix the issues above before running JLAW_UNIFIED.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
