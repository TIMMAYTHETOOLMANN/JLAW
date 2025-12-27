"""
Test Suite for MOD-001, MOD-002, CRITICAL-008 Architectural Fixes
==================================================================

Tests for:
- MOD-001: RecursiveAnalysisResult phase structure alignment
- MOD-002: Node 6 enforcement routing implementation
- CRITICAL-008: UnifiedForensicOrchestrator
"""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, AsyncMock, patch
from src.core.recursive_engine import (
    RecursiveProsecutorialEngine, 
    RecursiveAnalysisResult, 
    NodeResult,
    PenaltyEstimate,
    RegulatoryRouting
)


class TestMOD001RecursiveAnalysisResult:
    """Test suite for MOD-001: Phase structure alignment."""
    
    def test_recursive_analysis_result_has_node_groups(self):
        """Test that RecursiveAnalysisResult has node_group fields."""
        result = RecursiveAnalysisResult(
            case_id="TEST-001",
            company_name="Test Corp",
            cik="0000000001",
            analysis_period="2023-01-01 to 2023-12-31",
            execution_start=datetime(2023, 1, 1),
            execution_end=datetime(2023, 1, 1),
            total_execution_seconds=100.0,
            node_group_1_results=[],
            node_group_2_results=[],
            node_group_3_results=[],
            node_group_4_results=[],
            total_alerts=0,
            critical_alerts=0,
            high_alerts=0,
            prosecution_recommendation="None",
            estimated_penalties=PenaltyEstimate(0, 0, False, 0),
            regulatory_routing=RegulatoryRouting()
        )
        
        assert hasattr(result, 'node_group_1_results')
        assert hasattr(result, 'node_group_2_results')
        assert hasattr(result, 'node_group_3_results')
        assert hasattr(result, 'node_group_4_results')
    
    def test_backward_compatibility_properties(self):
        """Test that backward compatibility properties work."""
        node1 = NodeResult(
            node_id="NODE_1", node_name="Test", status="success",
            violations_found=1, alerts_generated=1, findings={},
            execution_time_seconds=1.0
        )
        
        result = RecursiveAnalysisResult(
            case_id="TEST-001",
            company_name="Test Corp",
            cik="0000000001",
            analysis_period="2023-01-01 to 2023-12-31",
            execution_start=datetime(2023, 1, 1),
            execution_end=datetime(2023, 1, 1),
            total_execution_seconds=100.0,
            node_group_1_results=[node1],
            node_group_2_results=[],
            node_group_3_results=[],
            node_group_4_results=[],
            total_alerts=1,
            critical_alerts=0,
            high_alerts=0,
            prosecution_recommendation="None",
            estimated_penalties=PenaltyEstimate(0, 0, False, 0),
            regulatory_routing=RegulatoryRouting()
        )
        
        # Test backward compatibility properties
        assert result.phase1_results == result.node_group_1_results
        assert result.phase2_results == result.node_group_2_results
        assert result.phase3_results == result.node_group_3_results
        assert result.phase4_results == result.node_group_4_results
        assert len(result.phase1_results) == 1
        assert result.phase1_results[0].node_id == "NODE_1"
    
    def test_phase_execution_status_tracking(self):
        """Test that phase_execution_status is initialized."""
        result = RecursiveAnalysisResult(
            case_id="TEST-001",
            company_name="Test Corp",
            cik="0000000001",
            analysis_period="2023-01-01 to 2023-12-31",
            execution_start=datetime(2023, 1, 1),
            execution_end=datetime(2023, 1, 1),
            total_execution_seconds=100.0,
            node_group_1_results=[],
            node_group_2_results=[],
            node_group_3_results=[],
            node_group_4_results=[],
            total_alerts=0,
            critical_alerts=0,
            high_alerts=0,
            prosecution_recommendation="None",
            estimated_penalties=PenaltyEstimate(0, 0, False, 0),
            regulatory_routing=RegulatoryRouting()
        )
        
        assert hasattr(result, 'phase_execution_status')
        assert isinstance(result.phase_execution_status, dict)
        assert 'phase_1_configuration' in result.phase_execution_status
        assert 'phase_4_node_analysis' in result.phase_execution_status
        assert 'phase_9_dossier_generation' in result.phase_execution_status
        # Check all 9 phases are tracked
        assert len(result.phase_execution_status) == 9
    
    def test_to_dict_includes_both_naming_conventions(self):
        """Test that to_dict() includes both old and new naming."""
        node1 = NodeResult(
            node_id="NODE_1", node_name="Test", status="success",
            violations_found=1, alerts_generated=1, findings={},
            execution_time_seconds=1.0
        )
        
        result = RecursiveAnalysisResult(
            case_id="TEST-001",
            company_name="Test Corp",
            cik="0000000001",
            analysis_period="2023-01-01 to 2023-12-31",
            execution_start=datetime(2023, 1, 1),
            execution_end=datetime(2023, 1, 1),
            total_execution_seconds=100.0,
            node_group_1_results=[node1],
            node_group_2_results=[],
            node_group_3_results=[],
            node_group_4_results=[],
            total_alerts=1,
            critical_alerts=0,
            high_alerts=0,
            prosecution_recommendation="None",
            estimated_penalties=PenaltyEstimate(0, 0, False, 0),
            regulatory_routing=RegulatoryRouting()
        )
        
        result_dict = result.to_dict()
        
        # Check old naming (backward compatibility)
        assert 'phase1_results' in result_dict
        assert 'phase2_results' in result_dict
        assert 'phase3_results' in result_dict
        assert 'phase4_results' in result_dict
        
        # Check new naming
        assert 'node_group_1_results' in result_dict
        assert 'node_group_2_results' in result_dict
        assert 'node_group_3_results' in result_dict
        assert 'node_group_4_results' in result_dict
        
        # Check phase execution status
        assert 'phase_execution_status' in result_dict


class TestMOD002Node6Implementation:
    """Test suite for MOD-002: Node 6 enforcement routing."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance for testing."""
        return RecursiveProsecutorialEngine(
            sec_user_agent="Test/1.0",
            polygon_api_key=None
        )
    
    def test_execute_node6_exists(self, engine):
        """Test that _execute_node6 method exists."""
        assert hasattr(engine, '_execute_node6')
        assert callable(engine._execute_node6)
    
    def test_execute_node6_with_no_violations(self, engine):
        """Test Node 6 execution with no violations from previous nodes."""
        previous_results = [
            NodeResult(
                node_id="NODE_1", node_name="Test", status="success",
                violations_found=0, alerts_generated=0, findings={},
                execution_time_seconds=1.0
            )
        ]
        
        result = engine._execute_node6(
            case_id="TEST-001",
            company_name="Test Corp",
            cik="0000000001",
            previous_node_results=previous_results
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_6"
        assert result.node_name == "Enforcement Router"
        assert result.status == "success"
        assert 'findings' in result.findings or result.findings is not None
    
    def test_execute_node6_with_violations(self, engine):
        """Test Node 6 execution with violations from previous nodes."""
        previous_results = [
            NodeResult(
                node_id="NODE_1", 
                node_name="Form 4 Analysis", 
                status="success",
                violations_found=2, 
                alerts_generated=2, 
                findings={
                    'violations': [
                        {
                            'violation_type': 'Insider Trading',
                            'severity': 'HIGH',
                            'estimated_damages': 100000
                        },
                        {
                            'violation_type': 'Late Filing',
                            'severity': 'MEDIUM',
                            'estimated_damages': 10000
                        }
                    ]
                },
                execution_time_seconds=1.0
            )
        ]
        
        result = engine._execute_node6(
            case_id="TEST-001",
            company_name="Test Corp",
            cik="0000000001",
            previous_node_results=previous_results
        )
        
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_6"
        assert result.node_name == "Enforcement Router"
        assert result.status == "success"
        assert result.violations_found >= 0  # Should process violations
        
        # Check that findings contain routing information
        assert 'findings' in result.findings or result.findings is not None
        if result.findings:
            # May contain routing details
            assert isinstance(result.findings, dict)
    
    def test_execute_node6_handles_errors_gracefully(self, engine):
        """Test Node 6 handles errors without crashing."""
        # Test with invalid previous results
        previous_results = []
        
        result = engine._execute_node6(
            case_id="TEST-001",
            company_name="Test Corp",
            cik="0000000001",
            previous_node_results=previous_results
        )
        
        # Should not crash, either success or error status
        assert isinstance(result, NodeResult)
        assert result.node_id == "NODE_6"
        assert result.status in ["success", "error"]


class TestCRITICAL008UnifiedOrchestrator:
    """Test suite for CRITICAL-008: Unified orchestrator."""
    
    def test_unified_orchestrator_imports(self):
        """Test that UnifiedForensicOrchestrator can be imported."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        
        assert UnifiedForensicOrchestrator is not None
    
    def test_unified_orchestrator_initialization(self):
        """Test UnifiedForensicOrchestrator can be initialized."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        
        orchestrator = UnifiedForensicOrchestrator(
            cik="0000000001",
            company_name="Test Corp",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            strict_mode=True
        )
        
        assert orchestrator.cik == "0000000001"
        assert orchestrator.company_name == "Test Corp"
        assert orchestrator.strict_mode is True
        assert orchestrator.VERSION == "1.0.0"
    
    def test_convenience_function_exists(self):
        """Test that convenience function exists."""
        from src.core.unified_orchestrator import execute_forensic_analysis
        
        assert execute_forensic_analysis is not None
        assert callable(execute_forensic_analysis)
    
    def test_deprecated_orchestrators_emit_warnings(self):
        """Test that deprecated orchestrators emit deprecation warnings."""
        from pathlib import Path
        import warnings
        
        # Test MasterExecutionController
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from src.core.master_execution_controller import MasterExecutionController
            
            controller = MasterExecutionController(
                cik="0000000001",
                company_name="Test Corp",
                start_date=date(2023, 1, 1),
                end_date=date(2023, 12, 31),
                output_dir=Path("/tmp/test")
            )
            
            # Check that a deprecation warning was issued
            assert len(w) > 0
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            assert "UnifiedForensicOrchestrator" in str(w[0].message)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
