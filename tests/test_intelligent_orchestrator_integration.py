"""
Integration Tests for IntelligentOrchestrator
==============================================

Tests the IntelligentOrchestrator module independently.

NOTE: The deprecated JLAW_UNIFIED_DEPRECATED.py and its UnifiedForensicEngine/TargetConfig
classes have been removed. These tests now validate IntelligentOrchestrator in isolation.
"""

import pytest
from datetime import date
from pathlib import Path
from src.core.intelligent_orchestrator import IntelligentOrchestrator, InvestigationType


class TestIntelligentOrchestratorIntegration:
    """Test suite for IntelligentOrchestrator."""

    def test_investigation_type_mapping(self):
        """Test that investigation type mapping works."""
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
