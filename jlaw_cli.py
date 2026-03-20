#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                              ║
║                    JLAW - Justice Law Analytics Workbench                                    ║
║                                                                                              ║
║                  DOJ-Grade SEC Forensic Analysis Platform v3.0                               ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

Unified CLI Entry Point (v3.0)

This is the canonical command-line interface for JLAW forensic analysis.
Replaces the monolithic JLAW_UNIFIED.py with a modular, maintainable architecture.

Usage:
    jlaw_cli.py --cik 0000320187 --company "Apple Inc." --year 2019
    jlaw_cli.py --validate-only
    jlaw_cli.py --dry-run --cik 0000320187 --year 2019
    jlaw_cli.py --download-models

For complete documentation, see docs/CLI_REFERENCE.md
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import date
from typing import Optional, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import CLI components
from src.cli.argument_parser import JLAWArgumentParser
from src.cli.output_formatter import OutputFormatter
from src.cli.progress_tracker import ProgressTracker, PhaseProgressTracker

# Try to import Rich, fallback gracefully
try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

# Version
__version__ = "3.0.0"


def setup_logging(debug: bool = False, verbose: bool = False) -> logging.Logger:
    """
    Configure logging based on verbosity flags.
    
    Args:
        debug: Enable debug logging
        verbose: Enable verbose logging
        
    Returns:
        Configured logger
    """
    # Use centralized logging configuration
    try:
        from src.core.logging_config import setup_logging as configure_logging
        
        # Determine log level
        if debug:
            log_level = 'DEBUG'
        elif verbose:
            log_level = 'INFO'
        else:
            log_level = os.getenv('LOG_LEVEL', 'WARNING')
        
        # Configure logging
        configure_logging(
            log_level=log_level,
            console_output=True
        )
        
        return logging.getLogger('JLAW')
    
    except ImportError:
        # Fallback to basic logging if centralized config not available
        level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        return logging.getLogger('JLAW')


async def run_validation_only(console: Optional[Console] = None) -> int:
    """
    Run pre-flight validation checks only (no analysis).
    
    Args:
        console: Rich console instance
        
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    OutputFormatter.print_info("Running pre-flight validation checks...", console)
    
    try:
        # Load and validate configuration
        from config.secure_config import (
            load_dotenv_file,
            get_api_key,
            validate_sec_user_agent
        )
        
        # Load environment variables
        env_vars = load_dotenv_file()
        OutputFormatter.print_success(
            f"Loaded {len(env_vars)} environment variables", 
            console
        )
        
        # Check SEC user agent
        sec_user_agent = get_api_key('SEC_USER_AGENT')
        if sec_user_agent:
            is_valid, msg = validate_sec_user_agent(sec_user_agent)
            if is_valid:
                OutputFormatter.print_success("SEC User-Agent: Valid", console)
            else:
                OutputFormatter.print_error(f"SEC User-Agent: {msg}", console)
                return 1
        else:
            OutputFormatter.print_warning("SEC User-Agent not configured", console)
        
        # Check API keys
        api_keys = {
            'OPENAI_API_KEY': get_api_key('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': get_api_key('ANTHROPIC_API_KEY'),
            'POLYGON_API_KEY': get_api_key('POLYGON_API_KEY'),
        }
        
        for key_name, key_value in api_keys.items():
            if key_value:
                OutputFormatter.print_success(f"{key_name}: Configured", console)
            else:
                OutputFormatter.print_warning(f"{key_name}: Not configured (optional)", console)
        
        # Check ML models (if model management is implemented)
        try:
            from src.ml.model_registry import ModelRegistry
            registry = ModelRegistry()
            
            missing_models = []
            for model_name in registry.MODELS.keys():
                if not registry.is_model_cached(model_name):
                    missing_models.append(model_name)
            
            if missing_models:
                OutputFormatter.print_warning(
                    f"Missing ML models: {', '.join(missing_models)}\n"
                    "  Run: jlaw_cli.py --download-models",
                    console
                )
            else:
                OutputFormatter.print_success("All ML models cached", console)
        except ImportError:
            OutputFormatter.print_info("ML model management not yet implemented", console)
        
        OutputFormatter.print_success("All pre-flight checks passed!", console)
        return 0
        
    except Exception as e:
        OutputFormatter.print_error(f"Validation failed: {e}", console)
        return 1


async def export_config(output_path: str, console: Optional[Console] = None) -> int:
    """
    Export effective configuration to file.
    
    Args:
        output_path: Output file path
        console: Rich console instance
        
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        from config.secure_config import load_dotenv_file
        import json
        
        # Load configuration
        env_vars = load_dotenv_file()
        
        # Remove sensitive values
        safe_vars = {}
        for key, value in env_vars.items():
            if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key:
                safe_vars[key] = '***REDACTED***'
            else:
                safe_vars[key] = value
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(safe_vars, f, indent=2)
        
        OutputFormatter.print_success(
            f"Configuration exported to {output_path}",
            console
        )
        return 0
        
    except Exception as e:
        OutputFormatter.print_error(f"Export failed: {e}", console)
        return 1


async def handle_model_management(args, console: Optional[Console] = None) -> int:
    """
    Handle ML model management commands.
    
    Args:
        args: Parsed arguments
        console: Rich console instance
        
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        from src.ml.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        
        if args.download_models:
            # Download all models
            from scripts.download_ml_models import download_all_models
            return await download_all_models(force=False)
        
        elif args.verify_models:
            # Verify cached models
            OutputFormatter.print_info("Verifying cached ML models...", console)
            all_valid = True
            
            for model_name, model_info in registry.MODELS.items():
                if registry.is_model_cached(model_name):
                    OutputFormatter.print_success(f"{model_name}: Cached", console)
                else:
                    OutputFormatter.print_warning(f"{model_name}: Not cached", console)
                    all_valid = False
            
            return 0 if all_valid else 1
        
        elif args.clear_model_cache:
            # Clear model cache
            import shutil
            cache_dir = registry.get_cache_dir()
            
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                OutputFormatter.print_success("Model cache cleared", console)
            else:
                OutputFormatter.print_info("Model cache already empty", console)
            
            return 0
        
    except ImportError:
        OutputFormatter.print_error(
            "ML model management not yet implemented",
            console
        )
        return 1
    except Exception as e:
        OutputFormatter.print_error(f"Model management failed: {e}", console)
        return 1


async def main() -> int:
    """
    Main entry point for JLAW CLI.
    
    Returns:
        Exit code (0 = success, non-zero = failure)
    """
    # Initialize console
    console = Console() if RICH_AVAILABLE else None
    
    # Print header
    OutputFormatter.print_header(console)
    
    # Parse arguments
    parser = JLAWArgumentParser()
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(debug=args.debug, verbose=args.verbose)
    
    # Handle version
    if args.version:
        version_text = f"JLAW v{__version__}"
        if console:
            console.print(f"[bold cyan]{version_text}[/bold cyan]")
        else:
            print(version_text)
        return 0
    
    # Handle dependency check
    if args.check_deps:
        return await run_validation_only(console)
    
    # Handle validation-only mode
    if args.validate_only:
        return await run_validation_only(console)
    
    # Handle config export
    if args.export_config:
        return await export_config(args.export_config, console)
    
    # Handle model management
    if args.download_models or args.verify_models or args.clear_model_cache:
        return await handle_model_management(args, console)
    
    # Initialize configuration
    try:
        from config.secure_config import load_dotenv_file, get_api_key
        
        # Load environment variables
        load_dotenv_file()
        
        # Validate SEC user agent (required for SEC API)
        sec_user_agent = get_api_key('SEC_USER_AGENT')
        if not sec_user_agent:
            OutputFormatter.print_error(
                "SEC_USER_AGENT not configured. "
                "Please set SEC_USER_AGENT in .env file.",
                console
            )
            return 1
        
    except Exception as e:
        OutputFormatter.print_error(f"Configuration error: {e}", console)
        return 1

    # ── Pre-flight validation gate ──
    # Validates environment variables, API keys, and critical dependencies
    # before any analysis work begins.  Full stop on failure.
    if not getattr(args, 'skip_preflight', False):
        try:
            from scripts.preflight_check import PreFlightChecker
            OutputFormatter.print_info(
                "Running pre-flight validation (use --skip-preflight to bypass)...",
                console,
            )
            checker = PreFlightChecker(verbose=getattr(args, 'verbose', False))
            preflight_report = await checker.run_all_checks()

            if not preflight_report.passed:
                failed = [
                    c for c in preflight_report.checks if c.status == "fail"
                ]
                OutputFormatter.print_error(
                    f"Pre-flight validation FAILED — {len(failed)} critical "
                    f"check(s) did not pass.  Resolve the issues above before "
                    f"running analysis.",
                    console,
                )
                for c in failed:
                    OutputFormatter.print_error(
                        f"  ✗ {c.component}: {c.message}"
                        + (f" — {c.error}" if c.error else ""),
                        console,
                    )
                return 1

            OutputFormatter.print_success(
                "Pre-flight validation passed — all systems green.", console
            )
        except Exception as e:
            # If the preflight module itself fails to load, warn but continue
            logger.warning(f"Pre-flight check module error (non-fatal): {e}")
            OutputFormatter.print_warning(
                f"Pre-flight check unavailable: {e}. Proceeding with caution.",
                console,
            )
    
    # Prepare target configuration
    try:
        # Resolve CIK and company name
        cik = args.cik
        company_name = args.company_name
        
        # Handle company lookup
        if company_name and not cik:
            from src.cli.company_lookup import COMPANY_LOOKUP
            company_upper = company_name.upper()
            if company_upper in COMPANY_LOOKUP:
                cik, company_name = COMPANY_LOOKUP[company_upper]
                OutputFormatter.print_info(
                    f"Resolved {args.company_name} → CIK: {cik}",
                    console
                )
        
        if not cik:
            OutputFormatter.print_error(
                "CIK not specified. Use --cik or --company with known ticker.",
                console
            )
            return 1
        
        # Determine date range
        start_date = args.start_date
        end_date = args.end_date
        
        if not start_date or not end_date:
            # Default to full year analysis
            start_date = date(2019, 1, 1)
            end_date = date(2019, 12, 31)
            OutputFormatter.print_info(
                f"Using default date range: {start_date} to {end_date}",
                console
            )
        
        # Prepare output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
    except Exception as e:
        OutputFormatter.print_error(f"Configuration error: {e}", console)
        return 1
    
    # Initialize orchestrator
    try:
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        
        # Derive ticker from company name if not explicitly provided
        ticker = getattr(args, 'ticker', '') or ''
        if not ticker and company_name:
            # Common ticker derivation for well-known companies
            ticker = company_name.split(',')[0].split(' ')[0].upper()

        orchestrator = UnifiedForensicOrchestrator(
            cik=cik,
            company_name=company_name or f"CIK-{cik}",
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            output_dir=output_dir,
            strict_mode=args.strict_mode,
            auto_mode=args.auto_mode,
            enable_dual_agent=True,
            enable_subagents=True,
            enable_web_intelligence=True,
        )
        
        OutputFormatter.print_success(
            f"Initialized UnifiedForensicOrchestrator v{orchestrator.VERSION}",
            console
        )
        
    except Exception as e:
        OutputFormatter.print_error(f"Orchestrator initialization failed: {e}", console)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    
    # Handle dry-run mode
    if args.dry_run:
        OutputFormatter.print_info("Dry-run mode: Generating execution plan...", console)
        
        # Generate execution plan (simplified)
        class ExecutionPlan:
            def __init__(self):
                self.phases = [
                    {'name': 'Phase 1: Configuration', 'node_count': 0, 'estimated_time': 5},
                    {'name': 'Phase 2: SEC Data Collection', 'node_count': 0, 'estimated_time': 120},
                    {'name': 'Phase 3: Document Parsing', 'node_count': 0, 'estimated_time': 60},
                    {'name': 'Phase 4: 15-Node Analysis', 'node_count': 15, 'estimated_time': 300},
                    {'name': 'Phase 5: Pattern Detection', 'node_count': 23, 'estimated_time': 180},
                    {'name': 'Phase 6: AI Validation', 'node_count': 2, 'estimated_time': 60},
                    {'name': 'Phase 7: Subagents', 'node_count': 10, 'estimated_time': 120},
                    {'name': 'Phase 8: Evidence Chain', 'node_count': 0, 'estimated_time': 30},
                    {'name': 'Phase 9: Web Intelligence & Contradiction Mapping', 'node_count': 5, 'estimated_time': 60},
                    {'name': 'Phase 10: Forensic Dossier Generation', 'node_count': 0, 'estimated_time': 45},
                    {'name': 'Phase 11: Analysis Bundle Export', 'node_count': 0, 'estimated_time': 10},
                ]
                self.nodes = [f"Node {i}" for i in range(1, 16)]
        
        plan = ExecutionPlan()
        OutputFormatter.print_execution_plan(plan, console)
        
        return 0
    
    # Execute analysis with progress tracking
    with ProgressTracker(console) as tracker:
        try:
            OutputFormatter.print_info(
                f"Starting forensic analysis: {company_name} (CIK: {cik})",
                console
            )
            
            # Execute full analysis
            result = await orchestrator.execute_full_analysis()
            
            # Display results
            OutputFormatter.print_analysis_summary(result, console)
            
            # Determine exit code
            if result.status == 'complete':
                OutputFormatter.print_success("Analysis completed successfully!", console)
                return 0
            else:
                OutputFormatter.print_error(
                    f"Analysis failed at phase {result.failed_at_phase}: {result.error}",
                    console
                )
                return 1
            
        except KeyboardInterrupt:
            OutputFormatter.print_warning("Analysis interrupted by user", console)
            return 130
        
        except Exception as e:
            OutputFormatter.print_error(f"Analysis failed: {e}", console)
            if args.verbose or args.debug:
                import traceback
                traceback.print_exc()
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
