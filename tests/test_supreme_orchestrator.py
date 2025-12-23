"""
Tests for SupremeOrchestrator Meta-Controller
============================================

Tests the SupremeOrchestrator that intelligently selects execution strategy
based on investigation priority.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date, datetime
from pathlib import Path
from src.core.supreme_orchestrator import (
    SupremeOrchestrator,
    InvestigationPriority,
    ExecutionStrategy,
    SupremeExecutionResult
)


class TestStrategySelection:
    """Test suite for strategy selection logic."""
    
    def test_select_triage_strategy(self):
        """Test selection of TRIAGE strategy."""
        orchestrator = SupremeOrchestrator()
        
        strategy = orchestrator.select_strategy(
            priority="triage",
            filings=[]
        )
        
        assert strategy.orchestrator_name == "IntelligentOrchestrator"
        assert strategy.priority == InvestigationPriority.TRIAGE
        assert strategy.enable_strict_gates is False
        assert strategy.enable_ai_validation is False
        assert strategy.optimization_level == "aggressive"
        assert strategy.estimated_duration_seconds < 15 * 60  # Less than 15 min
    
    def test_select_standard_strategy(self):
        """Test selection of STANDARD strategy."""
        orchestrator = SupremeOrchestrator()
        
        strategy = orchestrator.select_strategy(
            priority="standard",
            filings=[]
        )
        
        assert strategy.orchestrator_name == "MasterExecutionController"
        assert strategy.priority == InvestigationPriority.STANDARD
        assert strategy.enable_strict_gates is True
        assert strategy.enable_ai_validation is True
        assert strategy.node_count == 15
        assert 15 * 60 <= strategy.estimated_duration_seconds <= 30 * 60
    
    def test_select_doj_referral_strategy(self):
        """Test selection of DOJ_REFERRAL strategy."""
        orchestrator = SupremeOrchestrator()
        
        strategy = orchestrator.select_strategy(
            priority="doj_referral",
            filings=[]
        )
        
        assert strategy.orchestrator_name == "ForensicMetaOrchestrator"
        assert strategy.priority == InvestigationPriority.DOJ_REFERRAL
        assert strategy.enable_strict_gates is True
        assert strategy.enable_ai_validation is True
        assert strategy.enable_parallel_execution is True
        assert strategy.node_count == 15
        assert 30 * 60 <= strategy.estimated_duration_seconds <= 60 * 60
    
    def test_select_strategy_invalid_priority(self):
        """Test strategy selection with invalid priority defaults to STANDARD."""
        orchestrator = SupremeOrchestrator()
        
        strategy = orchestrator.select_strategy(
            priority="invalid_priority",
            filings=[]
        )
        
        # Should default to STANDARD
        assert strategy.priority == InvestigationPriority.STANDARD
        assert strategy.orchestrator_name == "MasterExecutionController"
    
    def test_strategy_caching(self):
        """Test that strategies are cached for repeated calls."""
        orchestrator = SupremeOrchestrator()
        
        # First call
        strategy1 = orchestrator.select_strategy("standard", filings=[])
        
        # Second call with same parameters
        strategy2 = orchestrator.select_strategy("standard", filings=[])
        
        # Should return the same cached instance
        assert strategy1 is strategy2
    
    def test_strategy_to_dict(self):
        """Test ExecutionStrategy.to_dict() method."""
        orchestrator = SupremeOrchestrator()
        strategy = orchestrator.select_strategy("standard", filings=[])
        
        strategy_dict = strategy.to_dict()
        
        assert isinstance(strategy_dict, dict)
        assert "orchestrator_name" in strategy_dict
        assert "priority" in strategy_dict
        assert "estimated_duration_seconds" in strategy_dict
        assert "estimated_duration_minutes" in strategy_dict
        assert "node_count" in strategy_dict
        assert "enable_strict_gates" in strategy_dict


class TestAutoExecute:
    """Test suite for auto_execute method."""
    
    @pytest.mark.asyncio
    async def test_auto_execute_triage(self):
        """Test auto_execute with TRIAGE priority."""
        orchestrator = SupremeOrchestrator()
        
        # Mock _collect_filing_metadata
        with patch.object(
            orchestrator,
            '_collect_filing_metadata',
            return_value=[]
        ):
            # Mock _execute_triage
            with patch.object(
                orchestrator,
                '_execute_triage',
                return_value={
                    "success": True,
                    "node_results": {},
                    "detection_results": {},
                    "evidence_chain": {},
                    "total_violations": 0,
                    "total_alerts": 0
                }
            ) as mock_execute:
                result = await orchestrator.auto_execute(
                    cik="0000320193",
                    company_name="Test Company",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31),
                    output_dir=Path("/tmp/test"),
                    priority="triage"
                )
                
                # Should call _execute_triage
                mock_execute.assert_called_once()
                
                # Check result
                assert isinstance(result, SupremeExecutionResult)
                assert result.priority == InvestigationPriority.TRIAGE
                assert result.success is True
    
    @pytest.mark.asyncio
    async def test_auto_execute_standard(self):
        """Test auto_execute with STANDARD priority."""
        orchestrator = SupremeOrchestrator()
        
        # Mock dependencies
        with patch.object(
            orchestrator,
            '_collect_filing_metadata',
            return_value=[]
        ):
            with patch.object(
                orchestrator,
                '_execute_standard',
                return_value={
                    "success": True,
                    "node_results": {},
                    "detection_results": {},
                    "ai_validation_results": {},
                    "evidence_chain": {},
                    "dossier_path": "/tmp/test/dossier.json",
                    "total_violations": 5,
                    "total_alerts": 10
                }
            ) as mock_execute:
                result = await orchestrator.auto_execute(
                    cik="0000320193",
                    company_name="Test Company",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31),
                    output_dir=Path("/tmp/test"),
                    priority="standard"
                )
                
                # Should call _execute_standard
                mock_execute.assert_called_once()
                
                # Check result
                assert result.priority == InvestigationPriority.STANDARD
                assert result.total_violations == 5
                assert result.total_alerts == 10
    
    @pytest.mark.asyncio
    async def test_auto_execute_doj_referral(self):
        """Test auto_execute with DOJ_REFERRAL priority."""
        orchestrator = SupremeOrchestrator()
        
        with patch.object(
            orchestrator,
            '_collect_filing_metadata',
            return_value=[{"form_type": "10-K"}]
        ):
            with patch.object(
                orchestrator,
                '_execute_doj_referral',
                return_value={
                    "success": True,
                    "node_results": {},
                    "detection_results": {},
                    "ai_validation_results": {},
                    "evidence_chain": {},
                    "dossier_path": "/tmp/test/dossier.json",
                    "total_violations": 15,
                    "total_alerts": 25
                }
            ) as mock_execute:
                result = await orchestrator.auto_execute(
                    cik="0000320193",
                    company_name="Test Company",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31),
                    output_dir=Path("/tmp/test"),
                    priority="doj_referral"
                )
                
                # Should call _execute_doj_referral
                mock_execute.assert_called_once()
                
                # Check result
                assert result.priority == InvestigationPriority.DOJ_REFERRAL
                assert result.strategy.enable_parallel_execution is True
    
    @pytest.mark.asyncio
    async def test_auto_execute_error_handling(self):
        """Test auto_execute error handling."""
        orchestrator = SupremeOrchestrator()
        
        # Mock _collect_filing_metadata to succeed
        with patch.object(
            orchestrator,
            '_collect_filing_metadata',
            return_value=[]
        ):
            # But make execution fail
            with patch.object(
                orchestrator,
                '_execute_standard',
                side_effect=Exception("Execution error")
            ):
                result = await orchestrator.auto_execute(
                    cik="0000320193",
                    company_name="Test Company",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31),
                    output_dir=Path("/tmp/test"),
                    priority="standard"
                )
                
                # Should return error result
                assert result.success is False
                assert len(result.errors) > 0
                assert "Execution error" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_auto_execute_result_to_dict(self):
        """Test SupremeExecutionResult.to_dict() method."""
        orchestrator = SupremeOrchestrator()
        
        with patch.object(
            orchestrator,
            '_collect_filing_metadata',
            return_value=[]
        ):
            with patch.object(
                orchestrator,
                '_execute_triage',
                return_value={
                    "success": True,
                    "node_results": {},
                    "detection_results": {},
                    "evidence_chain": {},
                    "total_violations": 0,
                    "total_alerts": 0
                }
            ):
                result = await orchestrator.auto_execute(
                    cik="0000320193",
                    company_name="Test Company",
                    start_date=date(2019, 1, 1),
                    end_date=date(2019, 12, 31),
                    output_dir=Path("/tmp/test"),
                    priority="triage"
                )
                
                result_dict = result.to_dict()
                
                assert isinstance(result_dict, dict)
                assert "cik" in result_dict
                assert "company_name" in result_dict
                assert "priority" in result_dict
                assert "strategy" in result_dict
                assert "total_duration_seconds" in result_dict


class TestExecutionStrategy:
    """Test suite for ExecutionStrategy dataclass."""
    
    def test_execution_strategy_creation(self):
        """Test ExecutionStrategy can be created with all fields."""
        strategy = ExecutionStrategy(
            orchestrator_name="TestOrchestrator",
            priority=InvestigationPriority.STANDARD,
            estimated_duration_seconds=1200,
            node_count=15,
            enable_strict_gates=True,
            enable_ai_validation=True,
            enable_parallel_execution=False,
            optimization_level="moderate",
            description="Test strategy"
        )
        
        assert strategy.orchestrator_name == "TestOrchestrator"
        assert strategy.priority == InvestigationPriority.STANDARD
        assert strategy.estimated_duration_seconds == 1200
        assert strategy.node_count == 15


class TestAvailableStrategies:
    """Test suite for get_available_strategies method."""
    
    def test_get_available_strategies(self):
        """Test get_available_strategies returns all strategies."""
        orchestrator = SupremeOrchestrator()
        
        strategies = orchestrator.get_available_strategies()
        
        # Should return 3 strategies (one for each priority level)
        assert len(strategies) == 3
        
        # Each should be a dict
        for strategy in strategies:
            assert isinstance(strategy, dict)
            assert "orchestrator_name" in strategy
            assert "priority" in strategy
            assert "estimated_duration_seconds" in strategy
        
        # Check that all priorities are covered
        priorities = [s["priority"] for s in strategies]
        assert "triage" in priorities
        assert "standard" in priorities
        assert "doj_referral" in priorities
    
    def test_strategies_have_descriptions(self):
        """Test that all strategies have descriptions."""
        orchestrator = SupremeOrchestrator()
        
        strategies = orchestrator.get_available_strategies()
        
        for strategy in strategies:
            assert "description" in strategy
            assert len(strategy["description"]) > 0
    
    def test_strategies_have_duration_estimates(self):
        """Test that strategies have increasing duration estimates."""
        orchestrator = SupremeOrchestrator()
        
        strategies = orchestrator.get_available_strategies()
        
        # Sort by priority
        triage = next(s for s in strategies if s["priority"] == "triage")
        standard = next(s for s in strategies if s["priority"] == "standard")
        doj = next(s for s in strategies if s["priority"] == "doj_referral")
        
        # Duration should increase: triage < standard < doj_referral
        assert triage["estimated_duration_seconds"] < standard["estimated_duration_seconds"]
        assert standard["estimated_duration_seconds"] < doj["estimated_duration_seconds"]
