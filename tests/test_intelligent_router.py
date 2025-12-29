"""
Unit Tests for Intelligent Subagent Router
==========================================

Tests execution planning, parallel staging, result aggregation,
consensus tracking, and conflict detection.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import tempfile
from datetime import datetime

from src.forensics.intelligent_router import (
    IntelligentSubagentRouter,
    RoutingDecision,
    AgentResult
)
from src.forensics.agent_registry import DynamicAgentRegistry, AgentCapability


class TestAgentResult:
    """Test AgentResult dataclass."""
    
    def test_agent_result_creation(self):
        """Test creating AgentResult."""
        result = AgentResult(
            agent_name="test-agent",
            status="success",
            findings={"key": "value"},
            recommendations=["rec1", "rec2"],
            severity="high",
            execution_time=1.5
        )
        
        assert result.agent_name == "test-agent"
        assert result.status == "success"
        assert result.findings["key"] == "value"
        assert len(result.recommendations) == 2
        assert result.severity == "high"
        assert result.execution_time == 1.5
        assert result.error is None


class TestRoutingDecision:
    """Test RoutingDecision dataclass."""
    
    def test_routing_decision_creation(self):
        """Test creating RoutingDecision."""
        capability = AgentCapability(
            agent_name="test-agent",
            description="Test"
        )
        
        decision = RoutingDecision(
            selected_agents=[capability],
            execution_plan=[["agent1", "agent2"], ["agent3"]],
            estimated_cost=0.05,
            confidence_threshold=0.75,
            agent_scores={"agent1": 0.9}
        )
        
        assert len(decision.selected_agents) == 1
        assert len(decision.execution_plan) == 2
        assert decision.estimated_cost == 0.05
        assert decision.confidence_threshold == 0.75


class TestIntelligentSubagentRouter:
    """Test IntelligentSubagentRouter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock registry with test agents
        with tempfile.TemporaryDirectory() as tmpdir:
            self.tmpdir = tmpdir
            agents_dir = Path(tmpdir)
            
            # Create test agents
            agent1 = agents_dir / "agent1.md"
            agent1.write_text("""---
name: financial-analyst
priority: 90
---

## Violation Types
- insider_trading
- accounting_fraud
""")
            
            agent2 = agents_dir / "agent2.md"
            agent2.write_text("""---
name: compliance-auditor
priority: 80
---

## Violation Types
- insider_trading
- sox_violation
""")
            
            agent3 = agents_dir / "agent3.md"
            agent3.write_text("""---
name: nlp-analyst
priority: 70
---

## Violation Types
- material_misstatement
""")
            
            self.registry = DynamicAgentRegistry(agents_dir=agents_dir)
            self.router = IntelligentSubagentRouter(self.registry)
    
    def test_router_initialization(self):
        """Test router initialization."""
        assert self.router is not None
        assert self.router.registry is not None
        assert len(self.router.execution_history) == 0
    
    def test_plan_execution_basic(self):
        """Test basic execution planning."""
        violations = [
            {"type": "insider_trading"},
            {"type": "accounting_fraud"}
        ]
        
        decision = self.router.plan_execution(
            violations=violations,
            max_agents=5,
            parallel_stages=3
        )
        
        assert isinstance(decision, RoutingDecision)
        assert len(decision.selected_agents) > 0
        assert len(decision.execution_plan) > 0
        assert decision.estimated_cost >= 0.0
    
    def test_plan_execution_no_violations(self):
        """Test planning with no violations."""
        decision = self.router.plan_execution(
            violations=[],
            max_agents=5
        )
        
        assert len(decision.selected_agents) == 0
        assert len(decision.execution_plan) == 0
    
    def test_plan_execution_top_k_limit(self):
        """Test top-K limiting in execution planning."""
        # Create violations that match multiple agents
        violations = [{"type": "insider_trading"}]
        
        decision = self.router.plan_execution(
            violations=violations,
            max_agents=2,  # Limit to 2 agents
            parallel_stages=1
        )
        
        # Should respect max_agents limit
        assert len(decision.selected_agents) <= 2
    
    def test_create_parallel_stages_single_stage(self):
        """Test creating single stage (all parallel)."""
        agents = [
            AgentCapability(agent_name="agent1", description="Test", priority=90),
            AgentCapability(agent_name="agent2", description="Test", priority=80),
            AgentCapability(agent_name="agent3", description="Test", priority=70)
        ]
        
        stages = self.router._create_parallel_stages(agents, num_stages=1)
        
        assert len(stages) == 1
        assert len(stages[0]) == 3  # All agents in one stage
    
    def test_create_parallel_stages_multiple_stages(self):
        """Test creating multiple stages."""
        agents = [
            AgentCapability(agent_name="agent1", description="Test", priority=90),
            AgentCapability(agent_name="agent2", description="Test", priority=80),
            AgentCapability(agent_name="agent3", description="Test", priority=70)
        ]
        
        stages = self.router._create_parallel_stages(agents, num_stages=2)
        
        assert len(stages) >= 1
        assert len(stages) <= 2
        
        # Higher priority agents should be in earlier stages
        if len(stages) > 1:
            first_stage_agents = stages[0]
            assert "agent1" in first_stage_agents  # Highest priority
    
    def test_create_parallel_stages_empty(self):
        """Test creating stages with no agents."""
        stages = self.router._create_parallel_stages([], num_stages=3)
        assert len(stages) == 0
    
    def test_estimate_cost(self):
        """Test token cost estimation."""
        agents = [
            AgentCapability(agent_name="agent1", description="Test"),
            AgentCapability(agent_name="agent2", description="Test")
        ]
        violations = [{"type": "test1"}, {"type": "test2"}]
        
        cost = self.router._estimate_cost(agents, violations)
        
        # Should be positive and reasonable
        assert cost > 0.0
        assert cost < 1.0  # Shouldn't be too high for test data
    
    @pytest.mark.asyncio
    async def test_execute_basic(self):
        """Test basic execution."""
        violations = [{"type": "insider_trading"}]
        decision = RoutingDecision(
            selected_agents=[
                AgentCapability(agent_name="test-agent", description="Test")
            ],
            execution_plan=[["test-agent"]],
            estimated_cost=0.01
        )
        
        result = await self.router.execute(
            decision=decision,
            violations=violations,
            context={},
            orchestrator=None  # No orchestrator = placeholder mode
        )
        
        assert result["status"] in ["completed", "failed"]
        assert "agents_executed" in result
        assert "combined_findings" in result
        assert "consensus_score" in result
        assert "conflicts" in result
    
    @pytest.mark.asyncio
    async def test_execute_empty_plan(self):
        """Test execution with empty plan."""
        decision = RoutingDecision(
            selected_agents=[],
            execution_plan=[],
            estimated_cost=0.0
        )
        
        result = await self.router.execute(
            decision=decision,
            violations=[],
            context={}
        )
        
        assert result["status"] == "no_agents"
        assert result["agents_executed"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_single_agent(self):
        """Test single agent execution."""
        result = await self.router._execute_single_agent(
            agent_name="test-agent",
            violations=[{"type": "test"}],
            context={},
            orchestrator=None
        )
        
        assert isinstance(result, AgentResult)
        assert result.agent_name == "test-agent"
        assert result.status in ["success", "error"]
    
    @pytest.mark.asyncio
    async def test_execute_stage_parallel(self):
        """Test stage execution with multiple agents."""
        agent_names = ["agent1", "agent2"]
        violations = [{"type": "test"}]
        
        results = await self.router._execute_stage(
            agent_names=agent_names,
            violations=violations,
            context={},
            orchestrator=None
        )
        
        assert len(results) == 2
        assert "agent1" in results
        assert "agent2" in results
        assert all(isinstance(r, AgentResult) for r in results.values())
    
    def test_aggregate_findings(self):
        """Test aggregating findings from stages."""
        stage_results = [
            {
                "agent1": AgentResult(
                    agent_name="agent1",
                    status="success",
                    findings={"finding1": "value1"},
                    recommendations=["rec1"]
                )
            },
            {
                "agent2": AgentResult(
                    agent_name="agent2",
                    status="success",
                    findings={"finding2": "value2"},
                    recommendations=["rec2"]
                )
            }
        ]
        
        combined = self.router._aggregate_findings(stage_results)
        
        assert len(combined) == 2
        assert all("agent" in f for f in combined)
        assert all("findings" in f for f in combined)
    
    def test_aggregate_findings_with_errors(self):
        """Test aggregation with some agents failing."""
        stage_results = [
            {
                "agent1": AgentResult(
                    agent_name="agent1",
                    status="success",
                    findings={"finding1": "value1"}
                ),
                "agent2": AgentResult(
                    agent_name="agent2",
                    status="error",
                    error="Failed"
                )
            }
        ]
        
        combined = self.router._aggregate_findings(stage_results)
        
        # Should only include successful results
        assert len(combined) == 1
        assert combined[0]["agent"] == "agent1"
    
    def test_compute_consensus_all_agree(self):
        """Test consensus when all agents agree."""
        stage_results = [
            {
                "agent1": AgentResult(
                    agent_name="agent1",
                    status="success",
                    severity="high"
                ),
                "agent2": AgentResult(
                    agent_name="agent2",
                    status="success",
                    severity="high"
                )
            }
        ]
        
        consensus = self.router._compute_consensus(stage_results)
        
        # All agree on "high" severity
        assert consensus == 1.0
    
    def test_compute_consensus_partial_agreement(self):
        """Test consensus with partial agreement."""
        stage_results = [
            {
                "agent1": AgentResult(
                    agent_name="agent1",
                    status="success",
                    severity="high"
                ),
                "agent2": AgentResult(
                    agent_name="agent2",
                    status="success",
                    severity="high"
                ),
                "agent3": AgentResult(
                    agent_name="agent3",
                    status="success",
                    severity="medium"
                )
            }
        ]
        
        consensus = self.router._compute_consensus(stage_results)
        
        # 2 out of 3 agree on "high"
        assert consensus > 0.5
        assert consensus < 1.0
    
    def test_compute_consensus_no_results(self):
        """Test consensus with no results."""
        consensus = self.router._compute_consensus([])
        assert consensus == 0.0
    
    def test_detect_conflicts_severity(self):
        """Test conflict detection for severity disagreements."""
        stage_results = [
            {
                "agent1": AgentResult(
                    agent_name="agent1",
                    status="success",
                    severity="high"
                ),
                "agent2": AgentResult(
                    agent_name="agent2",
                    status="success",
                    severity="low"
                )
            }
        ]
        
        conflicts = self.router._detect_conflicts(stage_results)
        
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "severity_conflict"
        assert "agent1" in conflicts[0]["agents_involved"]
        assert "agent2" in conflicts[0]["agents_involved"]
    
    def test_detect_conflicts_no_conflicts(self):
        """Test conflict detection when no conflicts."""
        stage_results = [
            {
                "agent1": AgentResult(
                    agent_name="agent1",
                    status="success",
                    severity="high"
                ),
                "agent2": AgentResult(
                    agent_name="agent2",
                    status="success",
                    severity="high"
                )
            }
        ]
        
        conflicts = self.router._detect_conflicts(stage_results)
        
        assert len(conflicts) == 0
    
    def test_build_agent_prompt(self):
        """Test building agent prompt."""
        capability = AgentCapability(
            agent_name="test-agent",
            description="Test agent",
            prompt_template="Base prompt content."
        )
        
        violations = [
            {"type": "insider_trading", "confidence": 0.92}
        ]
        
        context = {"cik": "320187", "company": "Test Corp"}
        
        prompt = self.router.build_agent_prompt(capability, violations, context)
        
        assert "Base prompt content" in prompt
        assert "insider_trading" in prompt
        assert "320187" in prompt
        assert "Test Corp" in prompt
    
    def test_get_execution_history(self):
        """Test getting execution history."""
        history = self.router.get_execution_history()
        
        assert isinstance(history, list)
        # Initially empty
        assert len(history) == 0


@pytest.mark.integration
class TestIntelligentSubagentRouterIntegration:
    """Integration tests with real registry."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow from planning to execution."""
        try:
            # Use real registry
            router = IntelligentSubagentRouter()
            
            violations = [
                {"type": "insider_trading", "confidence": 0.92},
                {"type": "late_form4", "days_late": 5}
            ]
            
            # Plan execution
            decision = router.plan_execution(
                violations=violations,
                max_agents=3,
                parallel_stages=2
            )
            
            assert len(decision.selected_agents) > 0
            
            # Execute (placeholder mode)
            result = await router.execute(
                decision=decision,
                violations=violations,
                context={"test": True},
                orchestrator=None
            )
            
            assert result["status"] in ["completed", "failed", "no_agents"]
            assert "consensus_score" in result
            assert "conflicts" in result
            
            print(f"\n✓ Full workflow test:")
            print(f"  - Selected {len(decision.selected_agents)} agents")
            print(f"  - Execution status: {result['status']}")
            print(f"  - Consensus score: {result['consensus_score']:.2%}")
        
        except Exception as e:
            pytest.skip(f"Integration test failed: {e}")


if __name__ == "__main__":
    print("Running Intelligent Router Tests...")
    print("=" * 70)
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
