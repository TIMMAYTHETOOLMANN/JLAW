"""
Tests for MasterExecutionController with IntelligentOrchestrator integration.
=============================================================================

Tests that the MasterExecutionController correctly integrates with the
IntelligentOrchestrator for optimized node execution.
"""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from src.core.master_execution_controller import MasterExecutionController
from src.core.intelligent_orchestrator import InvestigationType


class TestMasterExecutionControllerOptimization:
    """Test suite for MasterExecutionController optimization features."""
    
    def test_enable_optimization_parameter_default_true(self):
        """Test that enable_optimization defaults to True."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        assert controller.enable_optimization is True
        assert controller.intelligent_orchestrator is not None
    
    def test_enable_optimization_parameter_false(self):
        """Test that optimization can be disabled."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            enable_optimization=False
        )
        
        assert controller.enable_optimization is False
        assert controller.intelligent_orchestrator is None
    
    def test_enable_optimization_parameter_explicit_true(self):
        """Test that optimization can be explicitly enabled."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            enable_optimization=True
        )
        
        assert controller.enable_optimization is True
        assert controller.intelligent_orchestrator is not None
    
    def test_detect_investigation_type_insider_trading(self):
        """Test detection of insider trading investigation type."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        filings = [
            {"form_type": "4"},
            {"form_type": "144"},
        ]
        
        inv_type = controller._detect_investigation_type(filings)
        
        assert inv_type == InvestigationType.INSIDER_TRADING
    
    def test_detect_investigation_type_financial_fraud(self):
        """Test detection of financial fraud investigation type."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        filings = [
            {"form_type": "10-K"},
            {"form_type": "DEF 14A"},
        ]
        
        inv_type = controller._detect_investigation_type(filings)
        
        assert inv_type == InvestigationType.FINANCIAL_FRAUD
    
    def test_detect_investigation_type_compliance(self):
        """Test detection of compliance investigation type."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        filings = [
            {"form_type": "10-K"},
            {"form_type": "10-Q"},
        ]
        
        inv_type = controller._detect_investigation_type(filings)
        
        assert inv_type == InvestigationType.COMPLIANCE
    
    def test_detect_investigation_type_comprehensive(self):
        """Test detection of comprehensive investigation type (default)."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        filings = [
            {"form_type": "8-K"},
        ]
        
        inv_type = controller._detect_investigation_type(filings)
        
        assert inv_type == InvestigationType.COMPREHENSIVE
    
    def test_detect_investigation_type_empty_filings(self):
        """Test detection with empty filings list."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        filings = []
        
        inv_type = controller._detect_investigation_type(filings)
        
        # Should default to COMPREHENSIVE
        assert inv_type == InvestigationType.COMPREHENSIVE
    
    def test_detect_investigation_type_case_insensitive(self):
        """Test that form type detection is case insensitive."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        filings = [
            {"form_type": "4"},  # lowercase
            {"form_type": "144"},  # uppercase
        ]
        
        inv_type = controller._detect_investigation_type(filings)
        
        assert inv_type == InvestigationType.INSIDER_TRADING
    
    def test_detect_investigation_type_with_type_key(self):
        """Test that detection works with 'type' key instead of 'form_type'."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output")
        )
        
        filings = [
            {"type": "4"},  # Use 'type' instead of 'form_type'
            {"type": "144"},
        ]
        
        inv_type = controller._detect_investigation_type(filings)
        
        assert inv_type == InvestigationType.INSIDER_TRADING
    
    def test_controller_logs_optimization_status(self, caplog):
        """Test that controller logs optimization status during initialization."""
        import logging
        caplog.set_level(logging.INFO)
        
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            enable_optimization=True
        )
        
        # Check that optimization status is logged
        log_messages = [record.message for record in caplog.records]
        assert any("Optimization: True" in msg for msg in log_messages)
    
    @pytest.mark.asyncio
    async def test_phase_4_optimization_enabled_with_filings(self):
        """Test that Phase 4 uses optimization when enabled and filings are available."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            enable_optimization=True
        )
        
        # Set up filings
        controller.filings = [
            {"form_type": "4"},
            {"form_type": "144"},
        ]
        
        # Mock the recursive engine to avoid actual execution
        with patch('src.core.recursive_engine.RecursiveProsecutorialEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            # Mock the run_full_analysis result
            mock_result = MagicMock()
            mock_result.phase1_results = []
            mock_result.phase2_results = []
            mock_result.phase3_results = []
            mock_result.phase4_results = []
            mock_engine.run_full_analysis = AsyncMock(return_value=mock_result)
            
            # Execute Phase 4
            await controller._execute_phase_4_node_analysis()
            
            # Verify that the engine was called
            mock_engine.run_full_analysis.assert_called_once()
            
            # Verify phase result contains optimization info
            phase_result = controller.phase_results[-1]
            assert "optimization_enabled" in phase_result.data
            assert phase_result.data["optimization_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_phase_4_optimization_disabled(self):
        """Test that Phase 4 runs all nodes when optimization is disabled."""
        controller = MasterExecutionController(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            enable_optimization=False
        )
        
        # Set up filings
        controller.filings = [
            {"form_type": "4"},
            {"form_type": "144"},
        ]
        
        # Mock the recursive engine
        with patch('src.core.recursive_engine.RecursiveProsecutorialEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            # Mock the run_full_analysis result
            mock_result = MagicMock()
            mock_result.phase1_results = []
            mock_result.phase2_results = []
            mock_result.phase3_results = []
            mock_result.phase4_results = []
            mock_engine.run_full_analysis = AsyncMock(return_value=mock_result)
            
            # Execute Phase 4
            await controller._execute_phase_4_node_analysis()
            
            # Verify that the engine was called
            mock_engine.run_full_analysis.assert_called_once()
            
            # Verify phase result indicates optimization was disabled
            phase_result = controller.phase_results[-1]
            assert "optimization_enabled" in phase_result.data
            assert phase_result.data["optimization_enabled"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
