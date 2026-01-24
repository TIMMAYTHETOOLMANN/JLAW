"""
Integration Tests for IntelligentOrchestrator with JLAW_UNIFIED
================================================================

Tests the integration between IntelligentOrchestrator and UnifiedForensicEngine.

NOTE: This test imports from JLAW_UNIFIED_DEPRECATED.py as the new JLAW_UNIFIED.py
is a redirect script. The actual classes are in the deprecated module.
"""

import pytest
from datetime import date
from pathlib import Path
from JLAW_UNIFIED_DEPRECATED import UnifiedForensicEngine, TargetConfig
from src.core.intelligent_orchestrator import IntelligentOrchestrator, InvestigationType


class TestIntelligentOrchestratorIntegration:
    """Test suite for integration with JLAW_UNIFIED."""
    
    def test_engine_has_orchestrator_field(self):
        """Test that UnifiedForensicEngine has orchestrator field."""
        config = TargetConfig(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            auto_mode=True
        )
        
        engine = UnifiedForensicEngine(config)
        
        # Orchestrator is None until Phase 1 initialization
        assert hasattr(engine, '_intelligent_orchestrator')
        assert engine._intelligent_orchestrator is None
        
        # Execution plan field exists
        assert hasattr(engine, '_execution_plan')
        assert engine._execution_plan is None
    
    def test_engine_has_execute_optimized_method(self):
        """Test that UnifiedForensicEngine has execute_optimized method."""
        config = TargetConfig(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            auto_mode=True
        )
        
        engine = UnifiedForensicEngine(config)
        
        assert hasattr(engine, 'execute_optimized')
        assert callable(engine.execute_optimized)
    
    def test_engine_has_optimized_phase_4_method(self):
        """Test that UnifiedForensicEngine has optimized Phase 4 method."""
        config = TargetConfig(
            cik="0000320193",
            company_name="Test Company",
            start_date=date(2019, 1, 1),
            end_date=date(2019, 12, 31),
            output_dir=Path("/tmp/test_output"),
            auto_mode=True
        )
        
        engine = UnifiedForensicEngine(config)
        
        assert hasattr(engine, '_execute_phase_4_node_analysis_optimized')
        assert callable(engine._execute_phase_4_node_analysis_optimized)
    
    def test_investigation_type_mapping(self):
        """Test that investigation type mapping works."""
        from src.core.intelligent_orchestrator import InvestigationType
        
        type_map = {
            "insider_trading": InvestigationType.INSIDER_TRADING,
            "financial_fraud": InvestigationType.FINANCIAL_FRAUD,
            "compliance": InvestigationType.COMPLIANCE,
            "comprehensive": InvestigationType.COMPREHENSIVE
        }
        
        # All types map correctly
        assert type_map["insider_trading"].value == "insider_trading"
        assert type_map["financial_fraud"].value == "financial_fraud"
        assert type_map["compliance"].value == "compliance"
        assert type_map["comprehensive"].value == "comprehensive"
    
    def test_orchestrator_can_be_instantiated(self):
        """Test that IntelligentOrchestrator can be instantiated independently."""
        orchestrator = IntelligentOrchestrator()
        
        assert orchestrator is not None
        assert hasattr(orchestrator, 'create_execution_plan')
        assert hasattr(orchestrator, 'should_skip_node')
        assert hasattr(orchestrator, 'get_investigation_summary')
