"""
Test the test infrastructure itself - validate that all test modules can be imported.

This validates the test suite implementation without requiring external dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_utils_import():
    """Test utils module imports."""
    print("Testing utils imports...")
    try:
        from tests.utils import test_reporter
        from tests.utils import remediation_engine
        from tests.utils import dependency_resolver
        print("  ✓ All utils modules importable")
        return True
    except Exception as e:
        print(f"  ✗ Utils import failed: {str(e)}")
        return False


def test_validators_structure():
    """Test validators module structure."""
    print("Testing validators structure...")
    try:
        validators_dir = PROJECT_ROOT / 'tests' / 'validators'
        expected_files = [
            'environment_validator.py',
            'api_key_validator.py',
            'node_validator.py',
            'detection_validator.py',
            'agent_validator.py',
            'evidence_chain_validator.py',
            'reporting_validator.py',
        ]
        
        missing = []
        for file in expected_files:
            if not (validators_dir / file).exists():
                missing.append(file)
        
        if missing:
            print(f"  ✗ Missing validators: {', '.join(missing)}")
            return False
        
        print(f"  ✓ All {len(expected_files)} validators present")
        return True
    except Exception as e:
        print(f"  ✗ Validators structure check failed: {str(e)}")
        return False


def test_master_suite_structure():
    """Test master test suite structure."""
    print("Testing master test suite...")
    try:
        suite_file = PROJECT_ROOT / 'tests' / 'jlaw_master_test_suite.py'
        preflight_file = PROJECT_ROOT / 'tests' / 'preflight_check.py'
        config_validator_file = PROJECT_ROOT / 'tests' / 'config_validator.py'
        
        if not suite_file.exists():
            print("  ✗ Master test suite not found")
            return False
        
        if not preflight_file.exists():
            print("  ✗ Preflight check not found")
            return False
        
        if not config_validator_file.exists():
            print("  ✗ Config validator not found")
            return False
        
        print("  ✓ All test suite components present")
        return True
    except Exception as e:
        print(f"  ✗ Test suite structure check failed: {str(e)}")
        return False


def test_scripts_structure():
    """Test scripts structure."""
    print("Testing scripts structure...")
    try:
        scripts_dir = PROJECT_ROOT / 'scripts'
        expected_files = [
            'deploy_jlaw.py',
            'setup_environment.py',
            'generate_env_template.py',
        ]
        
        missing = []
        for file in expected_files:
            if not (scripts_dir / file).exists():
                missing.append(file)
        
        if missing:
            print(f"  ✗ Missing scripts: {', '.join(missing)}")
            return False
        
        print(f"  ✓ All {len(expected_files)} deployment scripts present")
        return True
    except Exception as e:
        print(f"  ✗ Scripts structure check failed: {str(e)}")
        return False


def test_directory_structure():
    """Test directory structure."""
    print("Testing directory structure...")
    try:
        expected_dirs = [
            'tests/validators',
            'tests/utils',
            'tests/reports',
            'scripts',
        ]
        
        missing = []
        for dir_path in expected_dirs:
            if not (PROJECT_ROOT / dir_path).exists():
                missing.append(dir_path)
        
        if missing:
            print(f"  ✗ Missing directories: {', '.join(missing)}")
            return False
        
        print(f"  ✓ All required directories present")
        return True
    except Exception as e:
        print(f"  ✗ Directory structure check failed: {str(e)}")
        return False


def main():
    """Run all infrastructure tests."""
    print("=" * 80)
    print("JLAW TEST INFRASTRUCTURE VALIDATION")
    print("=" * 80)
    print()
    
    tests = [
        test_directory_structure,
        test_utils_import,
        test_validators_structure,
        test_master_suite_structure,
        test_scripts_structure,
    ]
    
    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests: {passed}/{total} passed")
    
    if passed == total:
        print("\n✅ Test infrastructure validation PASSED")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Create .env file: python scripts/generate_env_template.py")
        print("  3. Run pre-flight check: python -m tests.preflight_check")
        print("  4. Run full test suite: python -m tests.jlaw_master_test_suite --full --mock")
        return 0
    else:
        print("\n❌ Test infrastructure validation FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
