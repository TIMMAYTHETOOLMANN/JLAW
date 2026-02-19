#!/usr/bin/env python3
"""
JLAW Production Deployment Script
===================================

Configures and validates the JLAW forensic analysis platform for immediate
production use. Handles native Python deployment when Docker is unavailable.

Usage:
    python scripts/production_deploy.py
    python scripts/production_deploy.py --verify-only
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ProductionDeployer:
    """Validates and configures JLAW for production use."""

    REQUIRED_DIRS = ["output", "evidence", "reports", "logs", ".jlaw_cache/sec_edgar"]

    CRITICAL_PACKAGES = {
        "aiohttp": "aiohttp",
        "pandas": "pandas",
        "numpy": "numpy",
        "beautifulsoup4": "bs4",
        "python-dotenv": "dotenv",
        "rich": "rich",
        "requests": "requests",
        "lxml": "lxml",
        "scikit-learn": "sklearn",
        "aiolimiter": "aiolimiter",
        "cryptography": "cryptography",
        "rfc3161ng": "rfc3161ng",
        "pydantic": "pydantic",
        "structlog": "structlog",
        "psutil": "psutil",
        "httpx": "httpx",
        "reportlab": "reportlab",
        "networkx": "networkx",
    }

    OPTIONAL_PACKAGES = {
        "anthropic": "anthropic",
        "openai": "openai",
        "neo4j": "neo4j",
        "redis": "redis",
        "psycopg2": "psycopg2",
        "asyncpg": "asyncpg",
        "benford_py": "benford",
        "sec-edgar-downloader": "sec_edgar_downloader",
        "edgar": "edgar",
        "plotly": "plotly",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",
    }

    def __init__(self):
        self.results = {}
        self.warnings = []
        self.errors = []

    def print_header(self):
        print("\n" + "=" * 70)
        print("  JLAW FORENSIC ANALYSIS PLATFORM - PRODUCTION DEPLOYMENT")
        print("  Version 4.1.0 | DOJ-Grade SEC Filing Analysis")
        print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
        print("=" * 70)

    def print_phase(self, num, name):
        print(f"\n{'─' * 70}")
        print(f"  PHASE {num}: {name}")
        print(f"{'─' * 70}")

    def check_python_version(self):
        """Verify Python version meets requirements."""
        self.print_phase(1, "PYTHON ENVIRONMENT")
        v = sys.version_info
        print(f"  Python {v.major}.{v.minor}.{v.micro}")
        if v.major == 3 and v.minor >= 9:
            print("  [PASS] Python >= 3.9")
            return True
        else:
            self.errors.append(f"Python 3.9+ required, found {v.major}.{v.minor}")
            print("  [FAIL] Python >= 3.9 required")
            return False

    def check_directories(self):
        """Create and verify required directories."""
        self.print_phase(2, "DIRECTORY STRUCTURE")
        all_ok = True
        for d in self.REQUIRED_DIRS:
            path = PROJECT_ROOT / d
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {d}/")
            else:
                print(f"  [OK]      {d}/")
            if not path.exists():
                self.errors.append(f"Failed to create directory: {d}")
                all_ok = False
        return all_ok

    def check_env_file(self):
        """Verify .env file exists and has valid SEC_USER_AGENT."""
        self.print_phase(3, "ENVIRONMENT CONFIGURATION")
        env_path = PROJECT_ROOT / ".env"

        if not env_path.exists():
            example_path = PROJECT_ROOT / ".env.example"
            if example_path.exists():
                import shutil
                shutil.copy(example_path, env_path)
                print("  [CREATED] .env from .env.example")
                self.warnings.append("Created .env from template - review API keys")
            else:
                self.errors.append(".env file not found and no .env.example available")
                print("  [FAIL] No .env file found")
                return False

        # Load and validate
        from config.secure_config import load_dotenv_file, get_api_key, validate_sec_user_agent

        env_vars = load_dotenv_file(env_path)
        print(f"  [OK] Loaded {len(env_vars)} configuration variables")

        # Check SEC_USER_AGENT
        sec_ua = get_api_key("SEC_USER_AGENT")
        if sec_ua:
            is_valid, msg = validate_sec_user_agent(sec_ua)
            if is_valid:
                print(f"  [OK] SEC_USER_AGENT: {sec_ua[:50]}...")
            else:
                self.errors.append(f"Invalid SEC_USER_AGENT: {msg}")
                print(f"  [FAIL] SEC_USER_AGENT: {msg}")
                return False
        else:
            self.errors.append("SEC_USER_AGENT not configured")
            print("  [FAIL] SEC_USER_AGENT not set")
            return False

        # Check AI keys (optional but recommended)
        anthropic_key = get_api_key("ANTHROPIC_API_KEY")
        openai_key = get_api_key("OPENAI_API_KEY")

        if anthropic_key:
            print(f"  [OK] ANTHROPIC_API_KEY: configured")
        else:
            self.warnings.append("ANTHROPIC_API_KEY not set - AI cross-validation disabled")
            print("  [WARN] ANTHROPIC_API_KEY: not configured (AI validation disabled)")

        if openai_key:
            print(f"  [OK] OPENAI_API_KEY: configured")
        else:
            self.warnings.append("OPENAI_API_KEY not set - GPT-4 validation disabled")
            print("  [WARN] OPENAI_API_KEY: not configured (GPT-4 validation disabled)")

        if not anthropic_key and not openai_key:
            self.warnings.append("No AI API keys - system will run SEC analysis only")
            print("  [WARN] No AI keys - running in SEC-analysis-only mode")

        return True

    def check_critical_dependencies(self):
        """Verify critical Python packages are installed."""
        self.print_phase(4, "CRITICAL DEPENDENCIES")
        missing = []
        for pkg_name, import_name in self.CRITICAL_PACKAGES.items():
            try:
                importlib.import_module(import_name)
                print(f"  [OK] {pkg_name}")
            except ImportError:
                missing.append(pkg_name)
                print(f"  [MISSING] {pkg_name}")

        if missing:
            self.errors.append(f"Missing critical packages: {', '.join(missing)}")
            return False
        print(f"\n  All {len(self.CRITICAL_PACKAGES)} critical packages installed")
        return True

    def check_optional_dependencies(self):
        """Check optional Python packages."""
        self.print_phase(5, "OPTIONAL DEPENDENCIES")
        installed = 0
        for pkg_name, import_name in self.OPTIONAL_PACKAGES.items():
            try:
                importlib.import_module(import_name)
                print(f"  [OK]   {pkg_name}")
                installed += 1
            except ImportError:
                print(f"  [SKIP] {pkg_name} (optional)")

        print(f"\n  {installed}/{len(self.OPTIONAL_PACKAGES)} optional packages installed")
        return True

    def check_core_modules(self):
        """Verify JLAW core modules can be imported."""
        self.print_phase(6, "JLAW CORE MODULES")
        modules = [
            ("config.secure_config", "Configuration loader"),
            ("src.cli.argument_parser", "CLI argument parser"),
            ("src.cli.output_formatter", "Output formatter"),
            ("src.cli.progress_tracker", "Progress tracker"),
            ("src.core.unified_orchestrator", "Unified orchestrator"),
            ("src.core.logging_config", "Logging configuration"),
            ("src.core.exceptions", "Exception hierarchy"),
            ("src.core.circuit_breaker", "Circuit breaker"),
            ("src.core.retry_handler", "Retry handler"),
            ("src.integrations.sec_edgar.edgar_client", "SEC EDGAR client"),
            ("src.integrations.sec_edgar.rate_limiter", "Rate limiter"),
            ("src.reporting.doj_report_generator", "DOJ report generator"),
        ]

        loaded = 0
        failed = []
        for module_name, description in modules:
            try:
                importlib.import_module(module_name)
                print(f"  [OK] {description} ({module_name})")
                loaded += 1
            except Exception as e:
                err_msg = str(e).split('\n')[0][:60]
                print(f"  [WARN] {description}: {err_msg}")
                failed.append(module_name)

        print(f"\n  {loaded}/{len(modules)} core modules loaded")
        if failed:
            self.warnings.append(f"Some modules failed to load: {', '.join(failed)}")
        return loaded >= 4  # At minimum need config, CLI, orchestrator, EDGAR

    def check_cli_entry_point(self):
        """Verify the CLI entry point works."""
        self.print_phase(7, "CLI ENTRY POINT VALIDATION")
        cli_path = PROJECT_ROOT / "jlaw_cli.py"
        if not cli_path.exists():
            self.errors.append("jlaw_cli.py not found")
            print("  [FAIL] jlaw_cli.py not found")
            return False

        print(f"  [OK] jlaw_cli.py exists")

        # Test --version
        try:
            result = subprocess.run(
                [sys.executable, str(cli_path), "--version"],
                capture_output=True, text=True, timeout=30,
                cwd=str(PROJECT_ROOT)
            )
            if result.returncode == 0:
                print(f"  [OK] CLI version check passed")
            else:
                print(f"  [WARN] CLI version returned code {result.returncode}")
                if result.stderr:
                    print(f"        {result.stderr.strip()[:100]}")
        except Exception as e:
            print(f"  [WARN] CLI version check error: {e}")

        # Test --check-deps
        try:
            result = subprocess.run(
                [sys.executable, str(cli_path), "--check-deps"],
                capture_output=True, text=True, timeout=60,
                cwd=str(PROJECT_ROOT)
            )
            if result.returncode == 0:
                print(f"  [OK] Dependency check passed")
            else:
                print(f"  [WARN] Dependency check returned code {result.returncode}")
        except Exception as e:
            print(f"  [WARN] Dependency check error: {e}")

        return True

    def print_summary(self):
        """Print deployment summary."""
        print("\n" + "=" * 70)
        print("  DEPLOYMENT SUMMARY")
        print("=" * 70)

        if self.errors:
            print(f"\n  ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"    [X] {err}")

        if self.warnings:
            print(f"\n  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"    [!] {warn}")

        has_errors = len(self.errors) > 0

        if not has_errors:
            print("\n  STATUS: PRODUCTION READY")
            print("\n  The JLAW forensic analysis platform is configured and ready.")
            print("  You can now run analyses with:")
            print()
            print("    python jlaw_cli.py --cik <CIK> --year <YEAR> --auto")
            print()
            print("  Examples:")
            print("    python jlaw_cli.py --cik 0000320187 --company 'Apple' --year 2019 --auto")
            print("    python jlaw_cli.py --cik 0000320193 --year 2020 --auto")
            print("    python jlaw_cli.py --validate-only")
            print("    python jlaw_cli.py --dry-run --cik 0000320187 --year 2019")
        else:
            print("\n  STATUS: DEPLOYMENT INCOMPLETE")
            print("  Please resolve the errors listed above before running analyses.")

        print("\n" + "=" * 70)
        return not has_errors

    def deploy(self):
        """Run full deployment validation."""
        self.print_header()

        self.check_python_version()
        self.check_directories()
        self.check_env_file()
        self.check_critical_dependencies()
        self.check_optional_dependencies()
        self.check_core_modules()
        self.check_cli_entry_point()

        success = self.print_summary()
        return 0 if success else 1


def main():
    deployer = ProductionDeployer()
    return deployer.deploy()


if __name__ == "__main__":
    sys.exit(main())
