"""
Tests for LinearExecutionOrchestrator Deprecation
=================================================

Validates that deprecation warnings are properly emitted and migration
helpers work correctly.
"""

import pytest
import warnings
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestDeprecationWarnings:
    """Test that deprecation warnings are raised."""
    
    def test_init_raises_deprecation_warning(self):
        """Test that instantiation raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            orchestrator = LinearExecutionOrchestrator()
            
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            print("✓ __init__ raises DeprecationWarning")
    
    @pytest.mark.asyncio
    async def test_execute_raises_deprecation_warning(self):
        """Test that execute() raises DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            orchestrator = LinearExecutionOrchestrator()
            
            # Clear warnings from init
            w.clear()
            
            # Mock the controller to avoid actual execution
            with patch('src.core.master_execution_controller.MasterExecutionController') as mock_controller:
                mock_instance = MagicMock()
                mock_instance.execute_full_analysis = AsyncMock(return_value=MagicMock(
                    cik="test",
                    company_name="Test",
                    analysis_start=MagicMock(isoformat=lambda: "2019-01-01"),
                    analysis_end=MagicMock(isoformat=lambda: "2019-12-31"),
                    phase_results=[],
                    node_results={},
                    total_violations=0,
                    total_alerts=0,
                    dossier_path="",
                    merkle_root=""
                ))
                mock_controller.return_value = mock_instance
                
                try:
                    await orchestrator.execute(
                        cik="test",
                        company_name="Test",
                        start_date=date(2019, 1, 1),
                        end_date=date(2019, 12, 31)
                    )
                except Exception:
                    pass  # We only care about warnings, not execution
                
                # Should have at least one deprecation warning
                deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
                assert len(deprecation_warnings) >= 1
                assert any("execute" in str(warning.message).lower() for warning in deprecation_warnings)
                print("✓ execute() raises DeprecationWarning")
    
    def test_deprecation_message_mentions_migration(self):
        """Test that deprecation warning mentions migration path."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            orchestrator = LinearExecutionOrchestrator()
            
            warning_message = str(w[0].message)
            assert "MasterExecutionController" in warning_message or "master" in warning_message.lower()
            print("✓ Deprecation message mentions migration path")


class TestMigrationHelper:
    """Test migration helper functionality."""
    
    def test_create_migrated_controller_returns_master_controller(self):
        """Test that migration helper returns MasterExecutionController."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            
            with patch('src.core.master_execution_controller.MasterExecutionController') as mock_controller:
                controller = LinearExecutionOrchestrator.create_migrated_controller(
                    cik="320187",
                    company_name="Test Corp",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31)
                )
                
                mock_controller.assert_called_once()
                call_kwargs = mock_controller.call_args[1]
                
                assert call_kwargs['cik'] == "320187"
                assert call_kwargs['company_name'] == "Test Corp"
                assert call_kwargs['enable_optimization'] == False
                assert call_kwargs['strict_mode'] == False
                print("✓ create_migrated_controller returns MasterExecutionController")
    
    def test_migration_helper_raises_warning(self):
        """Test that migration helper raises deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            
            with patch('src.core.master_execution_controller.MasterExecutionController'):
                LinearExecutionOrchestrator.create_migrated_controller(
                    cik="320187",
                    company_name="Test",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31)
                )
            
            warning_messages = [str(warning.message) for warning in w]
            assert any("migration" in msg.lower() for msg in warning_messages)
            print("✓ Migration helper raises warning")
    
    def test_migration_helper_creates_temp_output_dir(self):
        """Test that migration helper creates temp output dir if not provided."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            
            with patch('src.core.master_execution_controller.MasterExecutionController') as mock_controller:
                with patch('src.core.linear_orchestrator.tempfile.mkdtemp') as mock_mkdtemp:
                    mock_mkdtemp.return_value = "/tmp/jlaw_test_123"
                    
                    LinearExecutionOrchestrator.create_migrated_controller(
                        cik="320187",
                        company_name="Test",
                        start_date=date(2019, 1, 1),
                        end_date=date(2019, 12, 31),
                        output_dir=None  # Not provided
                    )
                    
                    mock_mkdtemp.assert_called_once()
                    call_kwargs = mock_controller.call_args[1]
                    assert "output_dir" in call_kwargs
                    print("✓ Migration helper creates temp output dir when not provided")
    
    def test_migration_helper_uses_provided_output_dir(self):
        """Test that migration helper uses provided output dir."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            
            with patch('src.core.master_execution_controller.MasterExecutionController') as mock_controller:
                custom_dir = Path("/custom/output")
                
                LinearExecutionOrchestrator.create_migrated_controller(
                    cik="320187",
                    company_name="Test",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31),
                    output_dir=custom_dir
                )
                
                call_kwargs = mock_controller.call_args[1]
                assert call_kwargs['output_dir'] == custom_dir
                print("✓ Migration helper uses provided output dir")


class TestBackwardsCompatibility:
    """Test backwards compatibility of deprecated methods."""
    
    @pytest.mark.asyncio
    async def test_execute_returns_dict(self):
        """Test that execute() returns dictionary for backwards compatibility."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            
            orchestrator = LinearExecutionOrchestrator()
            
            with patch.object(orchestrator, 'create_migrated_controller') as mock_create:
                mock_controller = MagicMock()
                mock_result = MagicMock(
                    cik="320187",
                    company_name="Test",
                    analysis_start=MagicMock(isoformat=lambda: "2019-01-01T00:00:00"),
                    analysis_end=MagicMock(isoformat=lambda: "2019-12-31T00:00:00"),
                    phase_results=[],
                    node_results={},
                    total_violations=5,
                    total_alerts=10,
                    dossier_path="/path/to/dossier.json",
                    merkle_root="abc123"
                )
                mock_controller.execute_full_analysis = AsyncMock(return_value=mock_result)
                mock_create.return_value = mock_controller
                
                result = await orchestrator.execute(
                    cik="320187",
                    company_name="Test",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31)
                )
                
                assert isinstance(result, dict)
                assert result["cik"] == "320187"
                assert result["total_violations"] == 5
                assert "_migrated_from" in result
                print("✓ execute() returns dict for backwards compatibility")
    
    @pytest.mark.asyncio
    async def test_execute_includes_migration_notice(self):
        """Test that execute() result includes migration notice."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            
            orchestrator = LinearExecutionOrchestrator()
            
            with patch.object(orchestrator, 'create_migrated_controller') as mock_create:
                mock_controller = MagicMock()
                mock_result = MagicMock(
                    cik="test",
                    company_name="Test",
                    analysis_start=MagicMock(isoformat=lambda: "2019-01-01"),
                    analysis_end=MagicMock(isoformat=lambda: "2019-12-31"),
                    phase_results=[],
                    node_results={},
                    total_violations=0,
                    total_alerts=0,
                    dossier_path="",
                    merkle_root=""
                )
                mock_controller.execute_full_analysis = AsyncMock(return_value=mock_result)
                mock_create.return_value = mock_controller
                
                result = await orchestrator.execute(
                    cik="test",
                    company_name="Test",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31)
                )
                
                assert "_migrated_from" in result
                assert result["_migrated_from"] == "LinearExecutionOrchestrator"
                assert "_migration_notice" in result
                print("✓ execute() includes migration notice in result")
    
    @pytest.mark.asyncio
    async def test_execute_delegates_to_controller(self):
        """Test that execute() properly delegates to MasterExecutionController."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            from src.core.linear_orchestrator import LinearExecutionOrchestrator
            
            orchestrator = LinearExecutionOrchestrator()
            
            with patch.object(orchestrator, 'create_migrated_controller') as mock_create:
                mock_controller = MagicMock()
                mock_result = MagicMock(
                    cik="test",
                    company_name="Test",
                    analysis_start=MagicMock(isoformat=lambda: "2019-01-01"),
                    analysis_end=MagicMock(isoformat=lambda: "2019-12-31"),
                    phase_results=[],
                    node_results={},
                    total_violations=0,
                    total_alerts=0,
                    dossier_path="",
                    merkle_root=""
                )
                mock_controller.execute_full_analysis = AsyncMock(return_value=mock_result)
                mock_create.return_value = mock_controller
                
                await orchestrator.execute(
                    cik="test",
                    company_name="Test",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31)
                )
                
                # Verify create_migrated_controller was called
                mock_create.assert_called_once()
                # Verify execute_full_analysis was called
                mock_controller.execute_full_analysis.assert_called_once()
                print("✓ execute() properly delegates to MasterExecutionController")


class TestDocumentation:
    """Test that documentation is properly updated."""
    
    def test_module_docstring_has_deprecation_notice(self):
        """Test that module docstring includes deprecation notice."""
        import src.core.linear_orchestrator as module
        
        docstring = module.__doc__
        assert docstring is not None
        assert "deprecated" in docstring.lower()
        assert "MasterExecutionController" in docstring
        print("✓ Module docstring has deprecation notice")
    
    def test_class_docstring_has_deprecation_notice(self):
        """Test that class docstring includes deprecation notice."""
        from src.core.linear_orchestrator import LinearExecutionOrchestrator
        
        docstring = LinearExecutionOrchestrator.__doc__
        assert docstring is not None
        assert "DEPRECATED" in docstring.upper()
        assert "MasterExecutionController" in docstring
        print("✓ Class docstring has deprecation notice")
    
    def test_init_docstring_has_deprecation_notice(self):
        """Test that __init__ docstring includes deprecation notice."""
        from src.core.linear_orchestrator import LinearExecutionOrchestrator
        
        docstring = LinearExecutionOrchestrator.__init__.__doc__
        assert docstring is not None
        assert "deprecated" in docstring.lower()
        print("✓ __init__ docstring has deprecation notice")
    
    def test_migration_guide_exists(self):
        """Test that migration guide documentation exists."""
        import os
        guide_path = "/home/runner/work/JLAW/JLAW/docs/MIGRATION_LINEAR_TO_MASTER.md"
        assert os.path.exists(guide_path), f"Migration guide not found at {guide_path}"
        print("✓ Migration guide exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
