"""
Unit Tests for JLAW CLI Argument Parser
========================================

Tests the CLI argument parsing and validation logic.
"""

import pytest
from datetime import date
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cli.argument_parser import JLAWArgumentParser


class TestJLAWArgumentParser:
    """Test cases for JLAWArgumentParser."""
    
    def test_basic_argument_parsing(self):
        """Test basic CLI argument parsing."""
        parser = JLAWArgumentParser()
        args = parser.parse_args([
            '--cik', '0000320187',
            '--company', 'Apple Inc.',
            '--year', '2019'
        ])
        
        assert args.cik == '0000320187'
        assert args.company_name == 'Apple Inc.'
        assert args.start_date == date(2019, 1, 1)
        assert args.end_date == date(2019, 12, 31)
    
    def test_date_range_parsing(self):
        """Test date range argument parsing."""
        parser = JLAWArgumentParser()
        args = parser.parse_args([
            '--cik', '0000320187',
            '--start-date', '2019-01-01',
            '--end-date', '2019-12-31'
        ])
        
        assert args.start_date == date(2019, 1, 1)
        assert args.end_date == date(2019, 12, 31)
    
    def test_execution_mode_selection(self):
        """Test execution mode flag handling."""
        parser = JLAWArgumentParser()
        
        modes = ['auto', 'standard', 'forensic', 'batch', 'daemon']
        for mode in modes:
            args = parser.parse_args([
                '--mode', mode,
                '--cik', '0000320187'
            ])
            assert args.mode == mode
    
    def test_strict_mode_flag(self):
        """Test strict mode flag."""
        parser = JLAWArgumentParser()
        args = parser.parse_args([
            '--cik', '0000320187',
            '--strict'
        ])
        
        assert args.strict_mode is True
    
    def test_auto_mode_flag(self):
        """Test auto mode flag."""
        parser = JLAWArgumentParser()
        args = parser.parse_args([
            '--cik', '0000320187',
            '--auto'
        ])
        
        assert args.auto_mode is True
    
    def test_output_directory(self):
        """Test output directory argument."""
        parser = JLAWArgumentParser()
        args = parser.parse_args([
            '--cik', '0000320187',
            '--output-dir', 'custom_output'
        ])
        
        assert args.output_dir == Path('custom_output')
    
    def test_validate_only_flag(self):
        """Test validate-only flag."""
        parser = JLAWArgumentParser()
        args = parser.parse_args(['--validate-only'])
        
        assert args.validate_only is True
    
    def test_dry_run_flag(self):
        """Test dry-run flag."""
        parser = JLAWArgumentParser()
        args = parser.parse_args([
            '--cik', '0000320187',
            '--dry-run'
        ])
        
        assert args.dry_run is True
    
    def test_model_management_flags(self):
        """Test model management flags."""
        parser = JLAWArgumentParser()
        
        # Download models
        args = parser.parse_args(['--download-models'])
        assert args.download_models is True
        
        # Verify models
        args = parser.parse_args(['--verify-models'])
        assert args.verify_models is True
        
        # Clear cache
        args = parser.parse_args(['--clear-model-cache'])
        assert args.clear_model_cache is True
    
    def test_demo_mode(self):
        """Test demo mode flag."""
        parser = JLAWArgumentParser()
        args = parser.parse_args(['--demo'])
        
        assert args.demo is True
    
    def test_invalid_date_range(self):
        """Test that invalid date ranges are rejected."""
        parser = JLAWArgumentParser()
        
        with pytest.raises(SystemExit):
            # Start date after end date
            parser.parse_args([
                '--cik', '0000320187',
                '--start-date', '2019-12-31',
                '--end-date', '2019-01-01'
            ])
    
    def test_batch_mode_incompatibility(self):
        """Test that batch mode is incompatible with CIK/company."""
        parser = JLAWArgumentParser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([
                '--batch', 'targets.json',
                '--cik', '0000320187'
            ])
    
    def test_daemon_requires_watchlist(self):
        """Test that daemon mode requires watchlist."""
        parser = JLAWArgumentParser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--daemon'])
    
    def test_investigation_type_selection(self):
        """Test investigation type argument."""
        parser = JLAWArgumentParser()
        args = parser.parse_args([
            '--cik', '0000320187',
            '--investigation', 'insider-trading'
        ])
        
        assert args.investigation_type == 'insider-trading'
    
    def test_verbose_and_debug_flags(self):
        """Test verbose and debug logging flags."""
        parser = JLAWArgumentParser()
        
        # Verbose
        args = parser.parse_args([
            '--cik', '0000320187',
            '--verbose'
        ])
        assert args.verbose is True
        
        # Debug
        args = parser.parse_args([
            '--cik', '0000320187',
            '--debug'
        ])
        assert args.debug is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
