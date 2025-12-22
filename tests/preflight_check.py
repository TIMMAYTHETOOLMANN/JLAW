"""
Pre-Flight Check - Quick GO/NO-GO validation (< 30 seconds)

Validates critical dependencies, API keys, and core modules before deployment.
Returns GO/NO-GO status with summary.

Usage:
    python -m tests.preflight_check
"""

import sys
import asyncio
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.validators.environment_validator import EnvironmentValidator
from tests.validators.api_key_validator import APIKeyValidator


class PreFlightCheck:
    """
    Quick pre-flight validation system.
    
    Validates:
    - Python version
    - Critical dependencies
    - SEC EDGAR configuration
    - Core module imports
    - Minimum system requirements
    
    Target: < 30 seconds execution time
    """
    
    def __init__(self):
        """Initialize pre-flight check."""
        self.env_validator = EnvironmentValidator()
        self.api_validator = APIKeyValidator(mock_mode=True)  # Mock mode for speed
        self.issues = []
        self.warnings = []
    
    def check_python_version(self) -> bool:
        """Check Python version."""
        result = self.env_validator.validate_python_version()
        if not result.passed:
            self.issues.append(f"❌ {result.message}")
            return False
        print(f"✅ {result.message}")
        return True
    
    def check_critical_dependencies(self) -> bool:
        """Check critical dependencies only."""
        critical_deps = [
            'aiohttp',
            'httpx',
            'requests',
            'pandas',
            'numpy',
            'scikit-learn',
            'cryptography',
            'python-dotenv',
        ]
        
        missing = []
        for dep in critical_deps:
            if not self.env_validator.test_import(dep.replace('-', '_')):
                missing.append(dep)
        
        if missing:
            self.issues.append(f"❌ Missing critical dependencies: {', '.join(missing)}")
            return False
        
        print(f"✅ All {len(critical_deps)} critical dependencies available")
        return True
    
    def check_sec_configuration(self) -> bool:
        """Check SEC EDGAR configuration."""
        result = self.api_validator.validate_sec_user_agent()
        if not result.passed:
            self.issues.append(f"❌ SEC Configuration: {result.message}")
            return False
        print(f"✅ SEC EDGAR configured")
        return True
    
    def check_core_modules(self) -> bool:
        """Check core module imports."""
        core_modules = [
            'src.core.master_execution_controller',
            'src.core.recursive_engine',
            'src.nodes',
            'src.detection',
            'src.reporting',
        ]
        
        failed = []
        for module in core_modules:
            try:
                __import__(module)
            except ImportError as e:
                failed.append(f"{module}: {str(e)}")
        
        if failed:
            self.issues.append(f"❌ Core module import failures: {len(failed)}")
            for failure in failed[:3]:  # Show first 3
                self.issues.append(f"   - {failure}")
            return False
        
        print(f"✅ All {len(core_modules)} core modules importable")
        return True
    
    def check_system_resources(self) -> bool:
        """Check system resources."""
        result = self.env_validator.validate_system_resources()
        if not result.passed:
            self.warnings.append(f"⚠️  {result.message}")
            return True  # Warning, not failure
        print(f"✅ System resources sufficient")
        return True
    
    def check_optional_apis(self):
        """Check optional API configurations (warnings only)."""
        import os
        
        openai_key = os.getenv('OPENAI_API_KEY', '')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
        
        if not openai_key or 'YOUR_' in openai_key:
            self.warnings.append("⚠️  OpenAI API not configured (optional - Dual-Agent validation disabled)")
        
        if not anthropic_key or 'YOUR_' in anthropic_key:
            self.warnings.append("⚠️  Anthropic API not configured (optional - Subagent orchestration disabled)")
    
    def run(self) -> bool:
        """
        Run pre-flight check.
        
        Returns:
            True if GO, False if NO-GO
        """
        print("\n" + "=" * 80)
        print("JLAW PRE-FLIGHT CHECK - Quick Validation")
        print("=" * 80 + "\n")
        
        start_time = time.time()
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Critical Dependencies", self.check_critical_dependencies),
            ("SEC Configuration", self.check_sec_configuration),
            ("Core Modules", self.check_core_modules),
            ("System Resources", self.check_system_resources),
        ]
        
        results = []
        for check_name, check_func in checks:
            try:
                result = check_func()
                results.append(result)
            except Exception as e:
                self.issues.append(f"❌ {check_name}: {str(e)}")
                results.append(False)
        
        # Check optional APIs
        self.check_optional_apis()
        
        duration = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        passed = sum(results)
        total = len(results)
        
        print(f"\nChecks: {passed}/{total} passed")
        print(f"Duration: {duration:.2f}s")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.issues:
            print(f"\n❌ Issues ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")
            print("\n🛑 Status: NO-GO - Fix issues before deployment")
            print("\nRun full test suite for detailed diagnostics:")
            print("  python -m tests.jlaw_master_test_suite --full")
            return False
        else:
            print("\n✅ Status: GO - Ready for deployment")
            if self.warnings:
                print("   (Some optional features will be disabled)")
            return True


def main():
    """Main entry point."""
    checker = PreFlightCheck()
    is_go = checker.run()
    
    sys.exit(0 if is_go else 1)


if __name__ == '__main__':
    main()
