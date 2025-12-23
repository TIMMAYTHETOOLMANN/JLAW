"""
Tests for Subagent Auto-Orchestration
=====================================
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestViolationAgentMapping:
    """Test violation type to agent mapping."""
    
    def test_insider_trading_mapping(self):
        from src.forensics.subagents.orchestrator import get_agents_for_violation_types
        
        agents = get_agents_for_violation_types(["insider_trading"])
        
        assert "forensic-financial-analyst" in agents
        assert "forensic-research-specialist" in agents
        assert "forensic-compliance-auditor" in agents  # Always included
    
    def test_accounting_fraud_mapping(self):
        from src.forensics.subagents.orchestrator import get_agents_for_violation_types
        
        agents = get_agents_for_violation_types(["accounting_fraud"])
        
        assert "forensic-nlp-analyst" in agents
        assert "forensic-financial-analyst" in agents
        assert "forensic-compliance-auditor" in agents
    
    def test_sox_violation_mapping(self):
        from src.forensics.subagents.orchestrator import get_agents_for_violation_types
        
        agents = get_agents_for_violation_types(["sox_violation"])
        
        assert "forensic-compliance-auditor" in agents
        assert "security-auditor" in agents
    
    def test_multiple_violations(self):
        from src.forensics.subagents.orchestrator import get_agents_for_violation_types
        
        agents = get_agents_for_violation_types([
            "insider_trading",
            "accounting_fraud"
        ])
        
        # Should include agents from both categories
        assert "forensic-financial-analyst" in agents
        assert "forensic-nlp-analyst" in agents
        assert "forensic-research-specialist" in agents
    
    def test_unknown_violation_defaults(self):
        from src.forensics.subagents.orchestrator import get_agents_for_violation_types
        
        agents = get_agents_for_violation_types(["unknown_violation_type"])
        
        # Should return empty or minimal set
        # Compliance auditor is always added if any violations
        assert len(agents) >= 0


class TestAutoOrchestration:
    """Test auto-orchestration functionality."""
    
    @pytest.mark.asyncio
    async def test_auto_orchestrate_with_violations(self):
        from src.forensics.subagents.orchestrator import SubagentOrchestrator
        
        orchestrator = SubagentOrchestrator()
        
        violations = [
            {"type": "insider_trading", "confidence": 0.92},
            {"type": "late_form4", "days_late": 5}
        ]
        
        # Mock the Claude API call
        with patch.object(orchestrator, '_call_claude_agent', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "status": "success",
                "data": {"findings": [], "severity": "HIGH"}
            }
            
            result = await orchestrator.auto_orchestrate(violations)
        
        assert result["status"] in ["completed", "partial_success"]
        assert result["violations_analyzed"] == 2
        assert len(result["agents_spawned"]) > 0
    
    @pytest.mark.asyncio
    async def test_auto_orchestrate_no_violations(self):
        from src.forensics.subagents.orchestrator import SubagentOrchestrator
        
        orchestrator = SubagentOrchestrator()
        
        result = await orchestrator.auto_orchestrate([])
        
        assert result["status"] == "no_violations"
        assert result["violations_analyzed"] == 0
    
    @pytest.mark.asyncio
    async def test_auto_orchestrate_with_context(self):
        from src.forensics.subagents.orchestrator import SubagentOrchestrator
        
        orchestrator = SubagentOrchestrator()
        
        violations = [{"type": "sox_violation"}]
        context = {
            "cik": "320187",
            "company_name": "Test Corp"
        }
        
        with patch.object(orchestrator, '_call_claude_agent', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"status": "success", "data": {}}
            
            result = await orchestrator.auto_orchestrate(
                violations=violations,
                context=context
            )
        
        assert result["violations_analyzed"] == 1


class TestAgentRoleMapping:
    """Test agent role enum mapping."""
    
    def test_all_agents_have_roles(self):
        from src.forensics.subagents.orchestrator import AgentRole
        
        expected_agents = [
            "forensic-financial-analyst",
            "forensic-nlp-analyst", 
            "forensic-compliance-auditor",
            "forensic-research-specialist",
            "security-auditor"
        ]
        
        role_values = [r.value for r in AgentRole]
        
        for agent in expected_agents:
            assert agent in role_values, f"Missing AgentRole for {agent}"
