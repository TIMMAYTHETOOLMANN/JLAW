"""
Tests for Intelligent Orchestrator - Phase 3 System Audit
==========================================================

Tests the IntelligentOrchestrator's ability to:
- Create optimized execution plans based on investigation type
- Map filing types to nodes correctly
- Dynamically skip nodes based on prior results
- Calculate optimization percentages correctly
"""

import pytest
from src.core.intelligent_orchestrator import (
    IntelligentOrchestrator,
    InvestigationType,
    ExecutionPlan
)


class TestIntelligentOrchestrator:
    """Test suite for IntelligentOrchestrator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.orchestrator = IntelligentOrchestrator()
    
    def test_investigation_type_enum(self):
        """Test that all investigation types are defined."""
        assert InvestigationType.INSIDER_TRADING.value == "insider_trading"
        assert InvestigationType.FINANCIAL_FRAUD.value == "financial_fraud"
        assert InvestigationType.COMPLIANCE.value == "compliance"
        assert InvestigationType.COMPREHENSIVE.value == "comprehensive"
    
    def test_node_priorities_structure(self):
        """Test that NODE_PRIORITIES is correctly structured."""
        priorities = self.orchestrator.NODE_PRIORITIES
        
        # All investigation types present
        assert InvestigationType.INSIDER_TRADING in priorities
        assert InvestigationType.FINANCIAL_FRAUD in priorities
        assert InvestigationType.COMPLIANCE in priorities
        assert InvestigationType.COMPREHENSIVE in priorities
        
        # Each type has required, recommended, optional
        for inv_type in InvestigationType:
            assert "required" in priorities[inv_type]
            assert "recommended" in priorities[inv_type]
            assert "optional" in priorities[inv_type]
        
        # Comprehensive has all nodes as required
        comp = priorities[InvestigationType.COMPREHENSIVE]
        assert len(comp["required"]) == 15
        assert list(range(1, 16)) == comp["required"]
    
    def test_filing_node_map(self):
        """Test that FILING_NODE_MAP contains expected mappings."""
        node_map = self.orchestrator.FILING_NODE_MAP
        
        # Form 4 maps to Node 1
        assert "4" in node_map
        assert 1 in node_map["4"]
        
        # 10-K maps to Nodes 4, 13, 14
        assert "10-K" in node_map
        assert 4 in node_map["10-K"]
        assert 13 in node_map["10-K"]
        assert 14 in node_map["10-K"]
        
        # DEF 14A maps to Nodes 2, 11
        assert "DEF 14A" in node_map
        assert 2 in node_map["DEF 14A"]
        assert 11 in node_map["DEF 14A"]
    
    def test_create_execution_plan_insider_trading(self):
        """Test execution plan for insider trading investigation."""
        available_filings = [
            {"form_type": "4"},
            {"form_type": "144"},
            {"form_type": "10-K"},
        ]
        
        plan = self.orchestrator.create_execution_plan(
            investigation_type=InvestigationType.INSIDER_TRADING,
            available_filings=available_filings,
            resource_constraints=None
        )
        
        # Required nodes for insider trading: 1, 10, 15
        assert 1 in plan.required_nodes  # Form 4
        assert 10 in plan.required_nodes  # Form 144
        assert 15 in plan.required_nodes  # Market correlation
        
        # Plan has less than 15 nodes (optimized)
        total_nodes = len(plan.required_nodes) + len(plan.optional_nodes)
        assert total_nodes < 15
        
        # Optimization percentage should be positive
        assert plan.optimization_percentage > 0
        
        # Investigation type is set correctly
        assert plan.investigation_type == "insider_trading"
    
    def test_create_execution_plan_financial_fraud(self):
        """Test execution plan for financial fraud investigation."""
        available_filings = [
            {"form_type": "10-K"},
            {"form_type": "10-Q"},
            {"form_type": "DEF 14A"},
        ]
        
        plan = self.orchestrator.create_execution_plan(
            investigation_type=InvestigationType.FINANCIAL_FRAUD,
            available_filings=available_filings,
            resource_constraints=None
        )
        
        # Required nodes for financial fraud: 2, 3, 4, 5, 13, 14
        assert 2 in plan.required_nodes  # DEF 14A
        assert 3 in plan.required_nodes  # 10-Q
        assert 4 in plan.required_nodes  # 10-K
        # Node 5 is derived data, should be required
        assert 5 in plan.required_nodes  # IRC
        assert 13 in plan.required_nodes  # Z-score
        assert 14 in plan.required_nodes  # F-score
        
        assert plan.investigation_type == "financial_fraud"
    
    def test_create_execution_plan_compliance(self):
        """Test execution plan for compliance investigation."""
        available_filings = [
            {"form_type": "10-K"},
            {"form_type": "10-Q"},
            {"form_type": "8-K"},
        ]
        
        plan = self.orchestrator.create_execution_plan(
            investigation_type=InvestigationType.COMPLIANCE,
            available_filings=available_filings,
            resource_constraints=None
        )
        
        # Required nodes for compliance: 3, 4, 9
        assert 3 in plan.required_nodes  # 10-Q
        assert 4 in plan.required_nodes  # 10-K SOX
        assert 9 in plan.required_nodes  # 8-K
        
        assert plan.investigation_type == "compliance"
    
    def test_create_execution_plan_comprehensive(self):
        """Test execution plan for comprehensive investigation."""
        available_filings = [
            {"form_type": "10-K"},
        ]
        
        plan = self.orchestrator.create_execution_plan(
            investigation_type=InvestigationType.COMPREHENSIVE,
            available_filings=available_filings,
            resource_constraints=None
        )
        
        # Comprehensive should include all 15 nodes
        total_nodes = len(plan.required_nodes) + len(plan.optional_nodes)
        assert total_nodes == 15
        
        # No optimization for comprehensive
        assert plan.optimization_percentage == 0
        
        assert plan.investigation_type == "comprehensive"
    
    def test_resource_constraints(self):
        """Test that resource constraints are respected."""
        available_filings = [
            {"form_type": "4"},
            {"form_type": "10-K"},
            {"form_type": "10-Q"},
            {"form_type": "DEF 14A"},
            {"form_type": "8-K"},
        ]
        
        # Limit to max 10 nodes (more than required, less than all with optional)
        plan = self.orchestrator.create_execution_plan(
            investigation_type=InvestigationType.FINANCIAL_FRAUD,
            available_filings=available_filings,
            resource_constraints={"max_nodes": 10}
        )
        
        total_nodes = len(plan.required_nodes) + len(plan.optional_nodes)
        assert total_nodes <= 10
        
        # Test with INSIDER_TRADING which has fewer required nodes
        plan2 = self.orchestrator.create_execution_plan(
            investigation_type=InvestigationType.INSIDER_TRADING,
            available_filings=available_filings,
            resource_constraints={"max_nodes": 5}
        )
        
        total_nodes2 = len(plan2.required_nodes) + len(plan2.optional_nodes)
        assert total_nodes2 <= 5
    
    def test_should_skip_node_form_144(self):
        """Test Node 10 (Form 144) skipping logic."""
        # No trades in Node 1 - should skip Node 10
        prior_results = {
            1: {"trades": [], "transactions": []}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(10, prior_results)
        assert should_skip is True
        assert "No insider trades" in reason
        
        # Has trades in Node 1 - should not skip Node 10
        prior_results = {
            1: {"trades": [{"trade_id": 1}]}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(10, prior_results)
        assert should_skip is False
    
    def test_should_skip_node_irc(self):
        """Test Node 5 (IRC) skipping logic."""
        # No compensation data - should skip Node 5
        prior_results = {
            1: {"grants": []},
            2: {"compensation": {}}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(5, prior_results)
        assert should_skip is True
        assert "No compensation data" in reason
        
        # Has compensation data - should not skip Node 5
        prior_results = {
            1: {"grants": [{"grant_id": 1}]},
            2: {"compensation": {}}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(5, prior_results)
        assert should_skip is False
    
    def test_should_skip_node_network(self):
        """Test Node 11 (Network) skipping logic."""
        # No executive data - should skip Node 11
        prior_results = {
            1: {},
            2: {}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(11, prior_results)
        assert should_skip is True
        assert "No executive data" in reason
        
        # Has executive data - should not skip Node 11
        prior_results = {
            1: {"insiders": [{"name": "John Doe"}]}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(11, prior_results)
        assert should_skip is False
    
    def test_should_skip_node_market(self):
        """Test Node 15 (Market) skipping logic."""
        # No trades or events - should skip Node 15
        prior_results = {
            1: {"trades": []},
            9: {"events": []}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(15, prior_results)
        assert should_skip is True
        assert "No trades or events" in reason
        
        # Has trades - should not skip Node 15
        prior_results = {
            1: {"trades": [{"trade_id": 1}]}
        }
        
        should_skip, reason = self.orchestrator.should_skip_node(15, prior_results)
        assert should_skip is False
    
    def test_get_nodes_with_data(self):
        """Test filing type to node mapping."""
        available_types = {"4", "10-K", "DEF 14A"}
        
        nodes = self.orchestrator._get_nodes_with_data(available_types)
        
        # Form 4 -> Node 1
        assert 1 in nodes
        # 10-K -> Nodes 4, 13, 14
        assert 4 in nodes
        assert 13 in nodes
        assert 14 in nodes
        # DEF 14A -> Nodes 2, 11
        assert 2 in nodes
        assert 11 in nodes
    
    def test_get_investigation_summary(self):
        """Test summary generation."""
        plan = ExecutionPlan(
            required_nodes=[1, 2, 3],
            optional_nodes=[4, 5],
            skipped_nodes=[6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            estimated_duration_seconds=30.0,
            reason="Test investigation",
            investigation_type="insider_trading",
            optimization_percentage=66.7
        )
        
        summary = self.orchestrator.get_investigation_summary(plan)
        
        assert "INTELLIGENT ORCHESTRATOR" in summary
        assert "INSIDER_TRADING" in summary  # Uppercase version of investigation_type
        assert "66.7%" in summary
        assert "30.0s" in summary
        assert "Required Nodes (3)" in summary
        assert "Optional Nodes (2)" in summary
        assert "Skipped Nodes (10)" in summary
    
    def test_estimation_calculation(self):
        """Test that duration estimation is calculated."""
        available_filings = [
            {"form_type": "4"},
            {"form_type": "10-K"},
        ]
        
        plan = self.orchestrator.create_execution_plan(
            investigation_type=InvestigationType.INSIDER_TRADING,
            available_filings=available_filings,
            resource_constraints=None
        )
        
        # Should have some estimated duration
        assert plan.estimated_duration_seconds > 0
        
        # Rough estimate: 5s per required, 3s per optional
        expected_min = len(plan.required_nodes) * 5
        expected_max = (len(plan.required_nodes) * 5) + (len(plan.optional_nodes) * 3)
        assert plan.estimated_duration_seconds >= expected_min
        assert plan.estimated_duration_seconds <= expected_max + 1  # Allow small margin
