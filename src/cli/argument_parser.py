"""
JLAW CLI Argument Parser
=========================

Centralized CLI argument parsing for JLAW entry points.
Supports all legacy JLAW_UNIFIED.py flags plus new features.
"""

import argparse
from datetime import date
from pathlib import Path
from typing import Optional


class JLAWArgumentParser:
    """Centralized argument parser for JLAW CLI."""
    
    EXECUTION_MODES = ['auto', 'standard', 'forensic', 'batch', 'daemon']
    INVESTIGATION_TYPES = [
        'comprehensive', 'insider-trading', 'compensation',
        'sox-compliance', 'tax-exposure', 'market-timing'
    ]
    EXECUTION_STRATEGIES = ['speed', 'accuracy', 'balanced', 'standard']
    
    def __init__(self):
        """Initialize argument parser with comprehensive options."""
        self.parser = argparse.ArgumentParser(
            description='JLAW - Justice Law Analytics Workbench\n'
                       'DOJ-Grade SEC Forensic Analysis Platform',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_epilog()
        )
        self._add_arguments()
    
    def _add_arguments(self):
        """Add all CLI arguments."""
        
        # ═══ Target Selection ═══
        target_group = self.parser.add_argument_group('Target Selection')
        target_group.add_argument(
            '--cik',
            type=str,
            help='Company CIK number (e.g., 0000320187 for Apple)'
        )
        target_group.add_argument(
            '--company',
            dest='company_name',
            type=str,
            help='Company name or ticker (e.g., NIKE, AAPL)'
        )
        
        # ═══ Date Range ═══
        date_group = self.parser.add_argument_group('Date Range')
        date_group.add_argument(
            '--year',
            type=int,
            help='Analysis year (e.g., 2019 for Jan 1 - Dec 31, 2019)'
        )
        date_group.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format'
        )
        date_group.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format'
        )
        
        # ═══ Execution Mode ═══
        exec_group = self.parser.add_argument_group('Execution Mode')
        exec_group.add_argument(
            '--mode',
            choices=self.EXECUTION_MODES,
            default='standard',
            help='Execution mode: '
                 'auto (intelligent triage), '
                 'standard (full analysis), '
                 'forensic (DOJ-grade), '
                 'batch (multiple targets), '
                 'daemon (continuous monitoring)'
        )
        exec_group.add_argument(
            '--auto',
            dest='auto_mode',
            action='store_true',
            help='Auto mode (no user confirmations)'
        )
        exec_group.add_argument(
            '--strict',
            dest='strict_mode',
            action='store_true',
            help='Strict execution mode (enforce phase gates, halt on failures)'
        )
        
        # ═══ Investigation Type (Legacy compatibility) ═══
        investigation_group = self.parser.add_argument_group('Investigation Focus')
        investigation_group.add_argument(
            '--investigation',
            '--type',
            dest='investigation_type',
            choices=self.INVESTIGATION_TYPES,
            default='comprehensive',
            help='Investigation focus area (optimizes node execution)'
        )
        investigation_group.add_argument(
            '--strategy',
            choices=self.EXECUTION_STRATEGIES,
            default='standard',
            help='Execution strategy for resource/time tradeoffs'
        )
        
        # ═══ New Features ═══
        features_group = self.parser.add_argument_group('Advanced Features')
        features_group.add_argument(
            '--validate-only',
            action='store_true',
            help='Run pre-flight validation checks only (no analysis)'
        )
        features_group.add_argument(
            '--dry-run',
            action='store_true',
            help='Generate execution plan without running analysis'
        )
        features_group.add_argument(
            '--profile',
            action='store_true',
            help='Enable performance profiling and metrics collection'
        )
        features_group.add_argument(
            '--export-config',
            type=str,
            metavar='PATH',
            help='Export effective configuration to file and exit'
        )
        
        # ═══ Output Configuration ═══
        output_group = self.parser.add_argument_group('Output Configuration')
        output_group.add_argument(
            '--output-dir',
            type=str,
            default='output',
            help='Output directory for results (default: output)'
        )
        output_group.add_argument(
            '--no-pdf',
            action='store_true',
            help='Skip PDF report generation'
        )
        output_group.add_argument(
            '--verbose',
            '-v',
            action='store_true',
            help='Enable verbose output'
        )
        output_group.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug logging'
        )
        
        # ═══ Batch Mode ═══
        batch_group = self.parser.add_argument_group('Batch Processing')
        batch_group.add_argument(
            '--batch',
            type=str,
            metavar='FILE',
            help='Batch mode: process multiple targets from JSON/YAML file'
        )
        
        # ═══ Daemon Mode ═══
        daemon_group = self.parser.add_argument_group('Daemon Mode')
        daemon_group.add_argument(
            '--daemon',
            action='store_true',
            help='Run in daemon mode (continuous monitoring)'
        )
        daemon_group.add_argument(
            '--watchlist',
            type=str,
            metavar='FILE',
            help='Watchlist file for daemon mode (CIKs to monitor)'
        )
        
        # ═══ Model Management (Hidden Commands) ═══
        models_group = self.parser.add_argument_group('Model Management')
        models_group.add_argument(
            '--download-models',
            action='store_true',
            help='Download all required ML models and exit'
        )
        models_group.add_argument(
            '--verify-models',
            action='store_true',
            help='Verify cached ML models and exit'
        )
        models_group.add_argument(
            '--clear-model-cache',
            action='store_true',
            help='Clear ML model cache and exit'
        )
        
        # ═══ System Checks ═══
        system_group = self.parser.add_argument_group('System Checks')
        system_group.add_argument(
            '--check-deps',
            action='store_true',
            help='Check dependencies and exit'
        )
        system_group.add_argument(
            '--version',
            action='store_true',
            help='Print version and exit'
        )
        
        # ═══ Demo Mode ═══
        self.parser.add_argument(
            '--demo',
            action='store_true',
            help='Run demo analysis with test data'
        )
    
    def parse_args(self, args=None):
        """
        Parse command line arguments.
        
        Args:
            args: List of arguments to parse (for testing). If None, uses sys.argv.
            
        Returns:
            Parsed arguments namespace
        """
        parsed = self.parser.parse_args(args)
        
        # Post-processing: Convert date strings to date objects
        if parsed.start_date:
            try:
                parsed.start_date = date.fromisoformat(parsed.start_date)
            except ValueError as e:
                self.parser.error(f"Invalid start-date format: {e}")
        
        if parsed.end_date:
            try:
                parsed.end_date = date.fromisoformat(parsed.end_date)
            except ValueError as e:
                self.parser.error(f"Invalid end-date format: {e}")
        
        # Convert year to date range
        if parsed.year:
            parsed.start_date = date(parsed.year, 1, 1)
            parsed.end_date = date(parsed.year, 12, 31)
        
        # Convert output_dir to Path
        if hasattr(parsed, 'output_dir'):
            parsed.output_dir = Path(parsed.output_dir)
        
        # Validation
        self._validate_args(parsed)
        
        return parsed
    
    def _validate_args(self, args):
        """Validate argument combinations."""
        
        # Require CIK or company (unless special modes)
        if not any([args.cik, args.company_name, args.demo, args.batch,
                   args.check_deps, args.version, args.validate_only,
                   args.download_models, args.verify_models, args.clear_model_cache]):
            self.parser.error(
                'Either --cik or --company is required '
                '(or use --demo, --batch, or --check-deps)'
            )
        
        # Date range validation
        if args.start_date and args.end_date:
            if args.start_date > args.end_date:
                self.parser.error('--start-date must be before --end-date')
        
        # Batch mode incompatibilities
        if args.batch and (args.cik or args.company_name):
            self.parser.error('--batch cannot be used with --cik or --company')
        
        # Daemon mode requirements
        if args.daemon and not args.watchlist:
            self.parser.error('--daemon requires --watchlist')
    
    def _get_epilog(self) -> str:
        """Get epilog text with examples."""
        return """
Examples:
  # Interactive mode
  jlaw_cli.py
  
  # Analyze company by CIK
  jlaw_cli.py --cik 0000320187 --company "Apple Inc." --year 2019
  
  # Strict forensic analysis
  jlaw_cli.py --cik 0000320187 --year 2019 --mode forensic --strict --auto
  
  # Pre-flight validation only
  jlaw_cli.py --validate-only
  
  # Dry run (show execution plan)
  jlaw_cli.py --cik 0000320187 --year 2019 --dry-run
  
  # Download ML models
  jlaw_cli.py --download-models
  
  # Batch processing
  jlaw_cli.py --batch targets.json --mode batch

For more information, see docs/CLI_REFERENCE.md
        """
