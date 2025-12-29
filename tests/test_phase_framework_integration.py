"""
Integration Test: Phase Execution Framework with Master Controller
==================================================================

Simple integration test demonstrating the Phase Execution Framework
working within the MasterExecutionController context.
"""

import pytest
from pathlib import Path
from datetime import date
from unittest.mock import Mock, AsyncMock, patch


class TestPhaseFrameworkIntegration:
    """Test Phase Execution Framework integration with Master Controller."""
    
    def test_master_controller_initializes_phase_framework(self, tmp_path):
        """Test that MasterExecutionController initializes PhaseExecutionFramework."""
        from src.core.master_execution_controller import MasterExecutionController
        
        controller = MasterExecutionController(
            cik="320187",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=tmp_path,
            strict_mode=True
        )
        
        # Verify phase framework is initialized
        assert hasattr(controller, '_phase_framework')
        assert controller._phase_framework is not None
        assert controller._phase_framework.strict_mode is True
    
    def test_phase_execution_summary_method_exists(self, tmp_path):
        """Test that phase execution summary method exists and is callable."""
        from src.core.master_execution_controller import MasterExecutionController
        
        controller = MasterExecutionController(
            cik="320187",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=tmp_path,
            strict_mode=True
        )
        
        # Verify method exists
        assert hasattr(controller, 'get_phase_execution_summary')
        assert callable(controller.get_phase_execution_summary)
        
        # Call method (should return empty summary initially)
        summary = controller.get_phase_execution_summary()
        assert isinstance(summary, dict)
        assert 'total_phases_executed' in summary
        assert 'strict_mode_enabled' in summary
        assert summary['strict_mode_enabled'] is True
    
    def test_export_phase_audit_trail_method_exists(self, tmp_path):
        """Test that export phase audit trail method exists and is callable."""
        from src.core.master_execution_controller import MasterExecutionController
        
        controller = MasterExecutionController(
            cik="320187",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=tmp_path,
            strict_mode=True
        )
        
        # Verify method exists
        assert hasattr(controller, 'export_phase_audit_trail')
        assert callable(controller.export_phase_audit_trail)
        
        # Export audit trail (should create empty audit trail)
        audit_path = tmp_path / "test_audit_trail.json"
        controller.export_phase_audit_trail(audit_path)
        
        # Verify file was created
        assert audit_path.exists()
        
        # Verify JSON structure
        import json
        with open(audit_path, 'r') as f:
            audit_data = json.load(f)
        
        assert 'audit_trail_version' in audit_data
        assert 'strict_mode' in audit_data
        assert audit_data['strict_mode'] is True
    
    def test_evidence_chain_integrity_error_imported_correctly(self):
        """Test that EvidenceChainIntegrityError is imported from centralized exceptions."""
        from src.core.master_execution_controller import EvidenceChainIntegrityError
        from src.core.exceptions import EvidenceChainIntegrityError as ExceptionsError
        
        # Should be the same class
        assert EvidenceChainIntegrityError is ExceptionsError
    
    def test_phase_framework_registry_accessible(self, tmp_path):
        """Test that phase registry is accessible through framework."""
        from src.core.master_execution_controller import MasterExecutionController
        from src.core.phase_execution_framework import PHASE_REGISTRY
        
        controller = MasterExecutionController(
            cik="320187",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=tmp_path,
            strict_mode=True
        )
        
        # Verify framework has access to registry
        assert controller._phase_framework.phase_registry is PHASE_REGISTRY
        assert len(controller._phase_framework.phase_registry) == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
