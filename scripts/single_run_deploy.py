#!/usr/bin/env python3
"""
JLAW Single-Run Deployment Script
==================================

A comprehensive, self-contained script that:
1. Validates the Python environment
2. Installs all required dependencies
3. Creates a minimal .env configuration file (if not present)
4. Validates configuration  
5. Runs forensic analysis on a target company

This is the canonical entry point for first-time JLAW deployment.

Usage:
    python scripts/single_run_deploy.py
    python scripts/single_run_deploy.py --cik 320187 --company "NIKE, Inc." --year 2019
    python scripts/single_run_deploy.py --auto  # Non-interactive mode with defaults
    python scripts/single_run_deploy.py --setup-only  # Only configure, don't run analysis

Environment Variables (optional - can be passed or set in .env):
    SEC_USER_AGENT: Required for SEC EDGAR API access
    OPENAI_API_KEY: Optional for AI cross-validation
    ANTHROPIC_API_KEY: Optional for AI cross-validation

Exit Codes:
    0: Success
    1: Configuration error
    2: Dependency installation error
    3: Validation error
    4: Analysis execution error
"""

import asyncio
import argparse
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent.absolute()


@dataclass
class DeploymentConfig:
    """Configuration for the deployment."""
    cik: Optional[str] = None
    company_name: Optional[str] = None
    year: int = 2019
    auto_mode: bool = False
    strict_mode: bool = False
    setup_only: bool = False
    skip_deps: bool = False
    verbose: bool = False


class SingleRunDeployer:
    """
    Single-run deployment orchestrator for JLAW.
    
    Handles complete setup and first-run execution in a single operation.
    """
    
    # Default company for demo/test runs
    DEFAULT_CIK = "320187"
    DEFAULT_COMPANY = "NIKE, Inc."
    DEFAULT_YEAR = 2019
    
    # Companies with built-in lookup support
    COMPANY_LOOKUP = {
        "NIKE": ("320187", "NIKE, Inc."),
        "NKE": ("320187", "NIKE, Inc."),
        "APPLE": ("320193", "Apple Inc."),
        "AAPL": ("320193", "Apple Inc."),
        "MICROSOFT": ("789019", "Microsoft Corporation"),
        "MSFT": ("789019", "Microsoft Corporation"),
        "TESLA": ("1318605", "Tesla, Inc."),
        "TSLA": ("1318605", "Tesla, Inc."),
        "AMAZON": ("1018724", "Amazon.com, Inc."),
        "AMZN": ("1018724", "Amazon.com, Inc."),
        "META": ("1326801", "Meta Platforms, Inc."),
        "FB": ("1326801", "Meta Platforms, Inc."),
        "GOOGLE": ("1652044", "Alphabet Inc."),
        "GOOGL": ("1652044", "Alphabet Inc."),
        "NETFLIX": ("1065280", "Netflix, Inc."),
        "NFLX": ("1065280", "Netflix, Inc."),
        "NVIDIA": ("1045810", "NVIDIA Corporation"),
        "NVDA": ("1045810", "NVIDIA Corporation"),
    }
    
    def __init__(self, config: DeploymentConfig):
        """
        Initialize the deployer.
        
        Args:
            config: Deployment configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging."""
        level = logging.DEBUG if self.config.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger('JLAW-Deploy')
    
    def print_banner(self):
        """Print deployment banner."""
        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "JLAW SINGLE-RUN DEPLOYMENT" + " " * 32 + "║")
        print("║" + " " * 15 + "DOJ-Grade SEC Forensic Analysis Platform" + " " * 23 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
    
    def print_phase(self, phase_num: int, title: str, total: int = 5):
        """Print phase header."""
        print(f"\n{'═' * 80}")
        print(f"PHASE {phase_num}/{total}: {title}")
        print(f"{'═' * 80}\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: Environment Validation
    # ═══════════════════════════════════════════════════════════════════════════
    
    def phase1_validate_environment(self) -> bool:
        """
        Validate Python environment.
        
        Returns:
            bool: True if environment is valid
        """
        self.print_phase(1, "Environment Validation")
        
        # Check Python version
        version = sys.version_info
        print(f"Python version: {version.major}.{version.minor}.{version.micro}")
        
        if version < (3, 9):
            print(f"❌ Python 3.9+ required (you have {version.major}.{version.minor})")
            return False
        
        print("✅ Python version compatible")
        
        # Check project structure
        required_files = [
            'requirements.txt',
            'pyproject.toml',
            '.env.example',
            'jlaw_cli.py',
        ]
        
        required_dirs = [
            'src',
            'src/core',
            'src/nodes',
            'config',
        ]
        
        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                print(f"❌ Missing required file: {file_path}")
                return False
            print(f"✅ Found: {file_path}")
        
        for dir_path in required_dirs:
            full_path = PROJECT_ROOT / dir_path
            if not full_path.is_dir():
                print(f"❌ Missing required directory: {dir_path}")
                return False
            print(f"✅ Found: {dir_path}/")
        
        print("\n✅ Phase 1 complete: Environment is valid")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: Dependency Installation
    # ═══════════════════════════════════════════════════════════════════════════
    
    def phase2_install_dependencies(self) -> bool:
        """
        Install Python dependencies.
        
        Returns:
            bool: True if installation successful
        """
        self.print_phase(2, "Dependency Installation")
        
        if self.config.skip_deps:
            print("⏭️  Skipping dependency installation (--skip-deps)")
            return True
        
        requirements_file = PROJECT_ROOT / 'requirements.txt'
        
        print("Installing dependencies from requirements.txt...")
        print("(This may take several minutes on first run...)\n")
        
        try:
            # Upgrade pip first
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
                capture_output=not self.config.verbose,
                text=True
            )
            
            # Install requirements
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)],
                capture_output=not self.config.verbose,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Dependency installation failed")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")
                return False
            
            print("✅ Dependencies installed successfully")
            
        except Exception as e:
            print(f"❌ Dependency installation error: {e}")
            return False
        
        # Verify critical imports
        print("\nVerifying critical imports...")
        critical_imports = [
            ('aiohttp', 'aiohttp'),
            ('pandas', 'pandas'),
            ('numpy', 'numpy'),
            ('beautifulsoup4', 'bs4'),
            ('python-dotenv', 'dotenv'),
        ]
        
        for package_name, import_name in critical_imports:
            try:
                __import__(import_name)
                print(f"  ✅ {package_name}")
            except ImportError:
                print(f"  ❌ {package_name} (import failed)")
                return False
        
        print("\n✅ Phase 2 complete: Dependencies installed")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: Configuration Setup
    # ═══════════════════════════════════════════════════════════════════════════
    
    def phase3_setup_configuration(self) -> bool:
        """
        Set up .env configuration file.
        
        Returns:
            bool: True if configuration is valid
        """
        self.print_phase(3, "Configuration Setup")
        
        env_file = PROJECT_ROOT / '.env'
        env_example = PROJECT_ROOT / '.env.example'
        
        # Check if .env exists
        if env_file.exists():
            print("✅ .env file exists")
        else:
            print("📝 Creating .env file from template...")
            
            if not env_example.exists():
                print("❌ .env.example not found!")
                return False
            
            # Read template
            with open(env_example, 'r') as f:
                template_content = f.read()
            
            # Check for environment variables that might override defaults
            sec_user_agent = os.environ.get('SEC_USER_AGENT')
            openai_key = os.environ.get('OPENAI_API_KEY')
            anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
            
            # Replace placeholders with env vars if available
            if sec_user_agent:
                template_content = template_content.replace(
                    'SEC_USER_AGENT="YourCompany/1.0 (your-email@company.com)"',
                    f'SEC_USER_AGENT="{sec_user_agent}"'
                )
                print(f"  ✅ Using SEC_USER_AGENT from environment")
            
            if openai_key:
                template_content = template_content.replace(
                    'OPENAI_API_KEY="sk-proj-YOUR_OPENAI_API_KEY_HERE"',
                    f'OPENAI_API_KEY="{openai_key}"'
                )
                print(f"  ✅ Using OPENAI_API_KEY from environment")
            
            if anthropic_key:
                template_content = template_content.replace(
                    'ANTHROPIC_API_KEY="sk-ant-api03-YOUR_ANTHROPIC_KEY_HERE"',
                    f'ANTHROPIC_API_KEY="{anthropic_key}"'
                )
                print(f"  ✅ Using ANTHROPIC_API_KEY from environment")
            
            # Write .env file
            with open(env_file, 'w') as f:
                f.write(template_content)
            
            print("✅ .env file created")
        
        # Validate configuration
        print("\nValidating configuration...")
        
        # Add project root to path for imports
        sys.path.insert(0, str(PROJECT_ROOT))
        
        try:
            from config.secure_config import (
                load_dotenv_file,
                get_api_key,
                validate_sec_user_agent
            )
            
            # Load environment
            load_dotenv_file()
            
            # Check SEC User-Agent
            sec_user_agent = get_api_key('SEC_USER_AGENT')
            
            if not sec_user_agent:
                print("⚠️  SEC_USER_AGENT not configured")
                print("\n📝 SEC API requires a User-Agent header with:")
                print("   - Your organization name")
                print("   - Contact email address")
                print("\nExample: SEC_USER_AGENT=JLAW/1.0 (your-email@example.com)")
                
                if not self.config.auto_mode:
                    print("\nPlease edit the .env file and set SEC_USER_AGENT")
                    print(f"Location: {env_file}")
                    input("\nPress Enter after updating .env file...")
                    
                    # Reload configuration
                    load_dotenv_file()
                    sec_user_agent = get_api_key('SEC_USER_AGENT')
                
                if not sec_user_agent:
                    print("❌ SEC_USER_AGENT is required for SEC EDGAR API access")
                    return False
            
            # Validate the SEC User-Agent
            is_valid, msg = validate_sec_user_agent(sec_user_agent)
            if not is_valid:
                print(f"⚠️  SEC_USER_AGENT validation issue: {msg}")
                if self.config.strict_mode:
                    return False
            else:
                print(f"✅ SEC_USER_AGENT is valid: {sec_user_agent[:50]}...")
            
            # Check optional API keys
            openai_key = get_api_key('OPENAI_API_KEY')
            anthropic_key = get_api_key('ANTHROPIC_API_KEY')
            
            if openai_key:
                print("✅ OPENAI_API_KEY configured")
            else:
                print("⚠️  OPENAI_API_KEY not set (AI cross-validation limited)")
            
            if anthropic_key:
                print("✅ ANTHROPIC_API_KEY configured")
            else:
                print("⚠️  ANTHROPIC_API_KEY not set (AI cross-validation limited)")
            
            if not openai_key and not anthropic_key:
                print("\n⚠️  No AI API keys configured. Analysis will proceed without")
                print("   dual-agent validation (reduced accuracy).")
            
        except ImportError as e:
            print(f"❌ Configuration import error: {e}")
            return False
        except Exception as e:
            print(f"❌ Configuration validation error: {e}")
            return False
        
        # Create output directory
        output_dir = PROJECT_ROOT / 'output'
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Output directory ready: {output_dir}")
        
        print("\n✅ Phase 3 complete: Configuration is valid")
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 4: System Health Check
    # ═══════════════════════════════════════════════════════════════════════════
    
    def phase4_health_check(self) -> bool:
        """
        Run system health check.
        
        Returns:
            bool: True if health check passes
        """
        self.print_phase(4, "System Health Check")
        
        # Add project root to path
        sys.path.insert(0, str(PROJECT_ROOT))
        
        print("Testing core component imports...\n")
        
        # Test critical imports
        components = [
            ("src.core.recursive_engine", "RecursiveProsecutorialEngine", "Core Engine"),
            ("src.core.evidence_chain.hash_service", "HashService", "Evidence Chain"),
            ("src.nodes", "Form4Parser", "Node 1: Form 4 Parser"),
            ("src.nodes", "DEF14ACompensationAnalyzer", "Node 2: DEF 14A Analyzer"),
        ]
        
        all_passed = True
        for module_path, class_name, description in components:
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                print(f"  ✅ {description}")
            except ImportError as e:
                print(f"  ❌ {description}: Import error - {e}")
                all_passed = False
            except AttributeError as e:
                print(f"  ❌ {description}: Class not found - {e}")
                all_passed = False
            except Exception as e:
                print(f"  ⚠️  {description}: {e}")
        
        if not all_passed:
            print("\n⚠️  Some components failed to import.")
            print("   The system may still work with reduced functionality.")
        
        print("\n✅ Phase 4 complete: Health check finished")
        return True  # Don't fail on import errors; system may still work
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 5: Run Analysis
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def phase5_run_analysis(self) -> bool:
        """
        Run forensic analysis on target company.
        
        Returns:
            bool: True if analysis successful
        """
        self.print_phase(5, "Forensic Analysis Execution")
        
        if self.config.setup_only:
            print("⏭️  Skipping analysis (--setup-only mode)")
            print("\nTo run analysis later, use:")
            print(f"  python jlaw_cli.py --cik {self.config.cik or self.DEFAULT_CIK} --year {self.config.year} --auto")
            return True
        
        # Resolve company
        cik = self.config.cik
        company_name = self.config.company_name
        
        if not cik and company_name:
            # Try to resolve from lookup
            company_upper = company_name.upper()
            if company_upper in self.COMPANY_LOOKUP:
                cik, company_name = self.COMPANY_LOOKUP[company_upper]
                print(f"✅ Resolved {self.config.company_name} → CIK: {cik} ({company_name})")
        
        if not cik:
            # Use default
            cik = self.DEFAULT_CIK
            company_name = self.DEFAULT_COMPANY
            print(f"📌 Using default target: {company_name} (CIK: {cik})")
        
        year = self.config.year or self.DEFAULT_YEAR
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        print(f"\n📊 Target Company: {company_name}")
        print(f"📊 CIK: {cik}")
        print(f"📊 Date Range: {start_date} to {end_date}")
        print(f"📊 Mode: {'Strict' if self.config.strict_mode else 'Standard'}")
        print()
        
        # Build command
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / 'jlaw_cli.py'),
            '--cik', cik,
            '--year', str(year),
        ]
        
        if company_name:
            cmd.extend(['--company', company_name])
        
        if self.config.auto_mode:
            cmd.append('--auto')
        
        if self.config.strict_mode:
            cmd.append('--strict')
        
        if self.config.verbose:
            cmd.append('--verbose')
        
        print(f"Executing: {' '.join(cmd)}\n")
        print("=" * 80)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT
            )
            
            if result.returncode == 0:
                print("\n" + "=" * 80)
                print("✅ ANALYSIS COMPLETE")
                print("=" * 80)
                print(f"\nResults saved to: {PROJECT_ROOT / 'output'}")
                return True
            else:
                print("\n" + "=" * 80)
                print(f"❌ Analysis returned exit code: {result.returncode}")
                print("=" * 80)
                return False
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Analysis interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Analysis execution error: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Main Deployment Flow
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def deploy(self) -> int:
        """
        Execute full deployment.
        
        Returns:
            int: Exit code (0 = success)
        """
        self.print_banner()
        
        # Phase 1: Environment Validation
        if not self.phase1_validate_environment():
            print("\n❌ DEPLOYMENT FAILED: Environment validation error")
            return 1
        
        # Phase 2: Dependency Installation
        if not self.phase2_install_dependencies():
            print("\n❌ DEPLOYMENT FAILED: Dependency installation error")
            return 2
        
        # Phase 3: Configuration Setup
        if not self.phase3_setup_configuration():
            print("\n❌ DEPLOYMENT FAILED: Configuration error")
            return 1
        
        # Phase 4: Health Check
        if not self.phase4_health_check():
            print("\n⚠️  Health check had warnings (continuing)")
        
        # Phase 5: Run Analysis
        if not await self.phase5_run_analysis():
            print("\n❌ DEPLOYMENT FAILED: Analysis execution error")
            return 4
        
        # Success
        print("\n" + "╔" + "═" * 78 + "╗")
        print("║" + " " * 25 + "DEPLOYMENT SUCCESSFUL" + " " * 32 + "║")
        print("╚" + "═" * 78 + "╝")
        
        print("\n📖 Quick Reference:")
        print("   Run analysis:  python jlaw_cli.py --cik 320187 --year 2019 --auto")
        print("   Health check:  python scripts/health_check.py")
        print("   Validation:    python jlaw_cli.py --validate-only")
        print()
        
        return 0


def parse_args() -> DeploymentConfig:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='JLAW Single-Run Deployment - Configure and Run in One Command',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default deployment with NIKE 2019
  python scripts/single_run_deploy.py
  
  # Specify target company
  python scripts/single_run_deploy.py --cik 320187 --company "NIKE" --year 2019
  
  # Auto mode (no prompts)
  python scripts/single_run_deploy.py --auto
  
  # Setup only (no analysis)
  python scripts/single_run_deploy.py --setup-only
  
  # Strict mode
  python scripts/single_run_deploy.py --strict --auto
        """
    )
    
    parser.add_argument(
        '--cik',
        type=str,
        help='Company CIK number (default: NIKE 320187)'
    )
    parser.add_argument(
        '--company',
        dest='company_name',
        type=str,
        help='Company name or ticker (e.g., NIKE, AAPL)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2019,
        help='Analysis year (default: 2019)'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Auto mode (no user prompts)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Strict mode (enforce phase gates)'
    )
    parser.add_argument(
        '--setup-only',
        action='store_true',
        help='Only run setup phases, skip analysis'
    )
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Skip dependency installation'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    return DeploymentConfig(
        cik=args.cik,
        company_name=args.company_name,
        year=args.year,
        auto_mode=args.auto,
        strict_mode=args.strict,
        setup_only=args.setup_only,
        skip_deps=args.skip_deps,
        verbose=args.verbose
    )


async def main() -> int:
    """Main entry point."""
    config = parse_args()
    deployer = SingleRunDeployer(config)
    return await deployer.deploy()


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nDeployment interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
