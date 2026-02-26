#!/usr/bin/env python3
"""
Final Verification Script for Zero-Failure Deployment System

Verifies that all components are properly installed and functional.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def verify_structure():
    """Verify directory structure."""
    print("Verifying directory structure...")
    
    required_dirs = [
        'tests/validators',
        'tests/utils',
        'tests/reports',
        'scripts',
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not (PROJECT_ROOT / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"  ✗ Missing directories: {', '.join(missing)}")
        return False
    
    print(f"  ✓ All directories present")
    return True


def verify_test_files():
    """Verify test files exist."""
    print("\nVerifying test files...")
    
    required_files = {
        'Master Test Suite': 'tests/jlaw_master_test_suite.py',
        'Pre-Flight Check': 'tests/preflight_check.py',
        'Config Validator': 'tests/config_validator.py',
        'Infrastructure Test': 'tests/test_infrastructure.py',
    }
    
    missing = []
    for name, path in required_files.items():
        if not (PROJECT_ROOT / path).exists():
            missing.append(f"{name} ({path})")
    
    if missing:
        print(f"  ✗ Missing files: {', '.join(missing)}")
        return False
    
    print(f"  ✓ All test files present")
    return True


def verify_validators():
    """Verify validator modules."""
    print("\nVerifying validators...")
    
    validators = [
        'environment_validator.py',
        'api_key_validator.py',
        'node_validator.py',
        'detection_validator.py',
        'agent_validator.py',
        'evidence_chain_validator.py',
        'reporting_validator.py',
    ]
    
    validators_dir = PROJECT_ROOT / 'tests' / 'validators'
    missing = []
    for validator in validators:
        if not (validators_dir / validator).exists():
            missing.append(validator)
    
    if missing:
        print(f"  ✗ Missing validators: {', '.join(missing)}")
        return False
    
    print(f"  ✓ All {len(validators)} validators present")
    return True


def verify_utils():
    """Verify utility modules."""
    print("\nVerifying utilities...")
    
    utils = [
        'test_reporter.py',
        'remediation_engine.py',
        'dependency_resolver.py',
    ]
    
    utils_dir = PROJECT_ROOT / 'tests' / 'utils'
    missing = []
    for util in utils:
        if not (utils_dir / util).exists():
            missing.append(util)
    
    if missing:
        print(f"  ✗ Missing utilities: {', '.join(missing)}")
        return False
    
    print(f"  ✓ All {len(utils)} utilities present")
    return True


def verify_scripts():
    """Verify deployment scripts."""
    print("\nVerifying deployment scripts...")
    
    scripts = {
        'Deploy JLAW': 'deploy_jlaw.py',
        'Setup Environment': 'setup_environment.py',
        'Generate .env': 'generate_env_template.py',
    }
    
    scripts_dir = PROJECT_ROOT / 'scripts'
    missing = []
    for name, script in scripts.items():
        if not (scripts_dir / script).exists():
            missing.append(f"{name} ({script})")
    
    if missing:
        print(f"  ✗ Missing scripts: {', '.join(missing)}")
        return False
    
    print(f"  ✓ All {len(scripts)} deployment scripts present")
    return True


def verify_documentation():
    """Verify documentation files."""
    print("\nVerifying documentation...")
    
    docs = {
        'Test Suite README': 'tests/README.md',
        'Quick Reference': 'tests/QUICK_REFERENCE.md',
        'Implementation Summary': 'ZERO_FAILURE_DEPLOYMENT_SUMMARY.md',
    }
    
    missing = []
    for name, path in docs.items():
        if not (PROJECT_ROOT / path).exists():
            missing.append(f"{name} ({path})")
    
    if missing:
        print(f"  ✗ Missing documentation: {', '.join(missing)}")
        return False
    
    print(f"  ✓ All documentation present")
    return True


def verify_imports():
    """Verify that key modules can be imported."""
    print("\nVerifying module imports...")
    
    try:
        from tests.utils import test_reporter
        from tests.utils import remediation_engine
        from tests.utils import dependency_resolver
        print("  ✓ All utility modules importable")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {str(e)}")
        return False


def main():
    """Run all verifications."""
    print("=" * 80)
    print("ZERO-FAILURE DEPLOYMENT SYSTEM - FINAL VERIFICATION")
    print("=" * 80)
    print()
    
    checks = [
        ("Directory Structure", verify_structure),
        ("Test Files", verify_test_files),
        ("Validators", verify_validators),
        ("Utilities", verify_utils),
        ("Deployment Scripts", verify_scripts),
        ("Documentation", verify_documentation),
        ("Module Imports", verify_imports),
    ]
    
    results = []
    for check_name, check_func in checks:
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nChecks: {passed}/{total} passed")
    
    for check_name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
    
    if passed == total:
        print("\n" + "=" * 80)
        print("✅ ZERO-FAILURE DEPLOYMENT SYSTEM VERIFICATION PASSED")
        print("=" * 80)
        print("\nSystem is ready for deployment validation!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Configure API keys: python scripts/generate_env_template.py")
        print("  3. Run pre-flight: python -m tests.preflight_check")
        print("  4. Full test suite: python -m tests.jlaw_master_test_suite --full --mock")
        print("  5. Deploy: python scripts/deploy_jlaw.py --auto")
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ VERIFICATION FAILED")
        print("=" * 80)
        print("\nSome components are missing. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
