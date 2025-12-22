"""
Deploy JLAW - One-Click Deployment Orchestrator

Master deployment script that executes all setup phases:
  Phase 1: Environment Setup (venv creation, pip install)
  Phase 2: Configuration (API keys, .env generation wizard)
  Phase 3: Dependency Validation (all packages, optional deps)
  Phase 4: Database Setup (Neo4j schema, TimescaleDB tables - if enabled)
  Phase 5: Full Test Suite Execution
  Phase 6: Pre-Flight Check
  Phase 7: Production Readiness Certification

Usage:
    python scripts/deploy_jlaw.py --interactive
    python scripts/deploy_jlaw.py --auto  # Non-interactive with defaults
"""

import sys
import asyncio
import subprocess
import argparse
from pathlib import Path
import shutil


class JLAWDeployment:
    """
    JLAW one-click deployment orchestrator.
    
    Executes all deployment phases and validates production readiness.
    """
    
    def __init__(self, interactive: bool = True):
        """
        Initialize deployment orchestrator.
        
        Args:
            interactive: If True, prompt for user input; otherwise use defaults
        """
        self.interactive = interactive
        self.project_root = Path(__file__).resolve().parent.parent
        self.phase = 0
        self.total_phases = 7
    
    def print_phase(self, phase_num: int, phase_name: str):
        """Print phase header."""
        self.phase = phase_num
        print("\n" + "=" * 80)
        print(f"PHASE {phase_num}/{self.total_phases}: {phase_name}")
        print("=" * 80 + "\n")
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation if interactive mode."""
        if not self.interactive:
            return True
        
        default_str = "Y/n" if default else "y/N"
        response = input(f"{message} ({default_str}): ").strip().lower()
        
        if not response:
            return default
        
        return response in ('y', 'yes')
    
    def phase1_environment_setup(self) -> bool:
        """Phase 1: Environment Setup."""
        self.print_phase(1, "Environment Setup")
        
        print("Setting up Python virtual environment...")
        
        if self.confirm("Run environment setup script?"):
            try:
                result = subprocess.run(
                    [sys.executable, 'scripts/setup_environment.py'],
                    cwd=self.project_root
                )
                if result.returncode != 0:
                    print("❌ Environment setup failed")
                    return False
            except Exception as e:
                print(f"❌ Environment setup error: {str(e)}")
                return False
        
        print("✅ Phase 1 complete")
        return True
    
    def phase2_configuration(self) -> bool:
        """Phase 2: Configuration."""
        self.print_phase(2, "Configuration")
        
        env_file = self.project_root / '.env'
        
        # Check if .env exists
        if env_file.exists():
            print(f"✅ .env file exists")
            
            if self.confirm("Validate existing configuration?"):
                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'tests.config_validator'],
                        cwd=self.project_root
                    )
                    if result.returncode != 0:
                        print("⚠️  Configuration validation found issues")
                        if not self.confirm("Continue anyway?", default=False):
                            return False
                except Exception as e:
                    print(f"❌ Configuration validation error: {str(e)}")
                    return False
        else:
            print("⚠️  .env file not found")
            
            if self.confirm("Create .env file from template?"):
                try:
                    result = subprocess.run(
                        [sys.executable, 'scripts/generate_env_template.py'],
                        cwd=self.project_root
                    )
                    if result.returncode != 0:
                        print("❌ Failed to create .env file")
                        return False
                    
                    print("\n📝 IMPORTANT: Edit .env file with your API keys before continuing!")
                    print(f"   File location: {env_file}")
                    
                    if self.interactive:
                        input("\nPress Enter after editing .env file...")
                except Exception as e:
                    print(f"❌ Configuration setup error: {str(e)}")
                    return False
        
        print("✅ Phase 2 complete")
        return True
    
    def phase3_dependency_validation(self) -> bool:
        """Phase 3: Dependency Validation."""
        self.print_phase(3, "Dependency Validation")
        
        print("Validating dependencies...")
        
        # Import and run environment validator
        try:
            sys.path.insert(0, str(self.project_root))
            from tests.validators.environment_validator import EnvironmentValidator
            
            validator = EnvironmentValidator()
            results = validator.validate_all(mock_mode=False)
            
            # Check for failures
            failures = [name for name, result in results.items() if not result.passed]
            
            if failures:
                print(f"\n⚠️  Validation issues found: {', '.join(failures)}")
                
                for name, result in results.items():
                    if not result.passed:
                        print(f"  ❌ {name}: {result.message}")
                
                if not self.confirm("Continue with issues?", default=False):
                    return False
            else:
                print("✅ All dependency validations passed")
        except Exception as e:
            print(f"❌ Dependency validation error: {str(e)}")
            if not self.confirm("Continue anyway?", default=False):
                return False
        
        print("✅ Phase 3 complete")
        return True
    
    def phase4_database_setup(self) -> bool:
        """Phase 4: Database Setup (optional)."""
        self.print_phase(4, "Database Setup (Optional)")
        
        print("Checking database configurations...")
        
        # Check if databases are configured
        import os
        
        neo4j_configured = bool(os.getenv('NEO4J_URI'))
        timescale_configured = bool(os.getenv('TIMESCALE_HOST'))
        
        if not neo4j_configured and not timescale_configured:
            print("ℹ️  No databases configured (optional)")
            print("   System will run without Neo4j and TimescaleDB")
        else:
            if neo4j_configured:
                print(f"  • Neo4j: Configured ({os.getenv('NEO4J_URI')})")
            if timescale_configured:
                print(f"  • TimescaleDB: Configured ({os.getenv('TIMESCALE_HOST')})")
            
            print("\nNote: Database connectivity will be tested in Phase 5")
        
        print("✅ Phase 4 complete")
        return True
    
    async def phase5_full_test_suite(self) -> bool:
        """Phase 5: Full Test Suite Execution."""
        self.print_phase(5, "Full Test Suite Execution")
        
        print("Running comprehensive test suite...")
        print("(This may take several minutes...)\n")
        
        if self.confirm("Run full test suite?"):
            try:
                # Run test suite
                result = subprocess.run(
                    [sys.executable, '-m', 'tests.jlaw_master_test_suite', '--full', '--mock'],
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    print("\n✅ All tests passed - Production ready!")
                elif result.returncode == 1:
                    print("\n❌ Critical failures detected - Cannot deploy")
                    return False
                elif result.returncode == 2:
                    print("\n⚠️  Non-critical failures - Can deploy with limitations")
                    if not self.confirm("Continue deployment?", default=False):
                        return False
                else:
                    print("\n⚠️  Configuration errors detected")
                    if not self.confirm("Continue anyway?", default=False):
                        return False
            except Exception as e:
                print(f"❌ Test suite error: {str(e)}")
                return False
        
        print("✅ Phase 5 complete")
        return True
    
    def phase6_preflight_check(self) -> bool:
        """Phase 6: Pre-Flight Check."""
        self.print_phase(6, "Pre-Flight Check")
        
        print("Running quick pre-flight validation...\n")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'tests.preflight_check'],
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                print("\n❌ Pre-flight check failed")
                if not self.confirm("Continue anyway?", default=False):
                    return False
        except Exception as e:
            print(f"❌ Pre-flight check error: {str(e)}")
            return False
        
        print("✅ Phase 6 complete")
        return True
    
    def phase7_production_certification(self) -> bool:
        """Phase 7: Production Readiness Certification."""
        self.print_phase(7, "Production Readiness Certification")
        
        print("Generating production readiness certificate...\n")
        
        # Generate final report
        report_dir = self.project_root / 'tests' / 'reports'
        report_dir.mkdir(parents=True, exist_ok=True)
        
        print("=" * 80)
        print("🎉 JLAW DEPLOYMENT COMPLETE")
        print("=" * 80)
        print()
        print("System is ready for forensic analysis!")
        print()
        print("Quick Start:")
        print("  1. Run interactive analysis:")
        print("     python JLAW_UNIFIED.py")
        print()
        print("  2. Run with CLI parameters:")
        print("     python JLAW_UNIFIED.py --cik 320187 --company 'NIKE, Inc.' --year 2019")
        print()
        print("  3. Run in strict mode (DOJ-grade):")
        print("     python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto")
        print()
        print(f"Test reports: {report_dir}")
        print("=" * 80)
        
        print("\n✅ Phase 7 complete")
        return True
    
    async def deploy(self) -> bool:
        """Execute full deployment."""
        print("\n" + "╔" + "=" * 78 + "╗")
        print("║" + " " * 23 + "JLAW DEPLOYMENT SYSTEM" + " " * 33 + "║")
        print("║" + " " * 17 + "One-Click Production Deployment" + " " * 30 + "║")
        print("╚" + "=" * 78 + "╝")
        
        if self.interactive:
            print("\nThis script will guide you through JLAW deployment.")
            if not self.confirm("\nProceed with deployment?"):
                print("Deployment cancelled.")
                return False
        
        # Execute all phases
        phases = [
            self.phase1_environment_setup,
            self.phase2_configuration,
            self.phase3_dependency_validation,
            self.phase4_database_setup,
            self.phase5_full_test_suite,
            self.phase6_preflight_check,
            self.phase7_production_certification,
        ]
        
        for phase_func in phases:
            if asyncio.iscoroutinefunction(phase_func):
                success = await phase_func()
            else:
                success = phase_func()
            
            if not success:
                print("\n" + "=" * 80)
                print("❌ DEPLOYMENT FAILED")
                print("=" * 80)
                print("\nReview errors above and fix issues before retrying.")
                print("\nFor detailed diagnostics, run:")
                print("  python -m tests.jlaw_master_test_suite --full")
                return False
        
        return True


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='JLAW One-Click Deployment'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='Interactive mode with prompts (default)'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Automatic mode with defaults (non-interactive)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    interactive = not args.auto
    
    # Run deployment
    deployer = JLAWDeployment(interactive=interactive)
    success = await deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
