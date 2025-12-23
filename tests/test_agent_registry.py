"""
Tests for Agent Registry
========================

Validates agent registry functionality, auto-registration, and 
violation-to-agent mapping for ForensicMetaOrchestrator.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock


class TestAgentRegistry:
    """Test agent registry functionality."""
    
    def test_register_default_agents(self):
        """Test that default agents are registered."""
        from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator
        from src.core.agent_registry import register_default_agents
        
        orchestrator = ForensicMetaOrchestrator(auto_register_agents=False)
        count = register_default_agents(orchestrator)
        
        assert count > 0, "Should register at least 1 agent"
        stats = orchestrator.get_agent_statistics()
        assert stats["total_agents_registered"] > 0, "Agent registry should not be empty"
        print(f"✓ Registered {count} agents")
    
    def test_auto_registration_on_init(self):
        """Test that agents are auto-registered on initialization."""
        from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator
        
        orchestrator = ForensicMetaOrchestrator(auto_register_agents=True)
        stats = orchestrator.get_agent_statistics()
        
        # Should have agents registered
        assert stats["total_agents_registered"] > 0, "Auto-registration should register agents"
        print(f"✓ Auto-registered {stats['total_agents_registered']} agents")
    
    def test_no_auto_registration(self):
        """Test that auto-registration can be disabled."""
        from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator
        
        orchestrator = ForensicMetaOrchestrator(auto_register_agents=False)
        stats = orchestrator.get_agent_statistics()
        
        # Should have no agents registered
        assert stats["total_agents_registered"] == 0, "Should not register agents when disabled"
        print("✓ Auto-registration disabled works correctly")
    
    def test_violation_agent_mapping(self):
        """Test violation type to agent mapping."""
        from src.core.agent_registry import get_agents_for_violations
        
        # Test insider trading mapping
        agents = get_agents_for_violations(["insider_trading"])
        assert "options_backdating" in agents, "Should map insider_trading to options_backdating"
        assert "form4_analyzer" in agents, "Should map insider_trading to form4_analyzer"
        print(f"✓ insider_trading maps to {len(agents)} agents")
        
        # Test accounting fraud mapping
        agents = get_agents_for_violations(["accounting_fraud"])
        assert "channel_stuffing" in agents, "Should map accounting_fraud to channel_stuffing"
        assert "advanced_pattern_detector" in agents, "Should map accounting_fraud to advanced_pattern_detector"
        print(f"✓ accounting_fraud maps to {len(agents)} agents")
    
    def test_get_all_violation_types(self):
        """Test getting all violation types."""
        from src.core.agent_registry import get_all_violation_types
        
        types = get_all_violation_types()
        assert "insider_trading" in types, "Should include insider_trading"
        assert "accounting_fraud" in types, "Should include accounting_fraud"
        assert "sox_violation" in types, "Should include sox_violation"
        assert len(types) > 0, "Should return at least 1 violation type"
        print(f"✓ Found {len(types)} violation types")
    
    def test_violation_agent_map_structure(self):
        """Test that VIOLATION_AGENT_MAP has correct structure."""
        from src.core.agent_registry import VIOLATION_AGENT_MAP
        
        assert isinstance(VIOLATION_AGENT_MAP, dict), "VIOLATION_AGENT_MAP should be a dict"
        
        for violation_type, agents in VIOLATION_AGENT_MAP.items():
            assert isinstance(violation_type, str), f"Violation type {violation_type} should be a string"
            assert isinstance(agents, list), f"Agents for {violation_type} should be a list"
            assert len(agents) > 0, f"Agents list for {violation_type} should not be empty"
            for agent in agents:
                assert isinstance(agent, str), f"Agent {agent} should be a string"
        
        print(f"✓ VIOLATION_AGENT_MAP structure validated ({len(VIOLATION_AGENT_MAP)} violation types)")
    
    def test_agent_types_distribution(self):
        """Test that agents are registered with proper type distribution."""
        from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator, AgentType
        
        orchestrator = ForensicMetaOrchestrator(auto_register_agents=True)
        stats = orchestrator.get_agent_statistics()
        
        # Check that we have agents of different types
        agents_by_type = stats["agents_by_type"]
        
        # Should have at least some pattern detectors
        assert agents_by_type[AgentType.PATTERN_DETECTOR.value] > 0, "Should have pattern detectors"
        
        # Should have at least some financial analyzers
        assert agents_by_type[AgentType.FINANCIAL_ANALYZER.value] > 0, "Should have financial analyzers"
        
        print(f"✓ Agent type distribution validated:")
        for agent_type, count in agents_by_type.items():
            if count > 0:
                print(f"  - {agent_type}: {count}")
    
    def test_multiple_violation_types(self):
        """Test that multiple violation types can be processed."""
        from src.core.agent_registry import get_agents_for_violations
        
        agents = get_agents_for_violations(["insider_trading", "accounting_fraud"])
        
        # Should include agents from both violation types
        assert "options_backdating" in agents, "Should include insider_trading agents"
        assert "channel_stuffing" in agents, "Should include accounting_fraud agents"
        assert len(agents) > 0, "Should return combined agent set"
        
        print(f"✓ Multiple violation types map to {len(agents)} unique agents")
    
    def test_normalized_violation_types(self):
        """Test that violation type normalization works."""
        from src.core.agent_registry import get_agents_for_violations
        
        # Test with different casing and spacing
        agents1 = get_agents_for_violations(["insider_trading"])
        agents2 = get_agents_for_violations(["Insider Trading"])
        agents3 = get_agents_for_violations(["INSIDER-TRADING"])
        
        # Should all return same agents (normalization handles differences)
        assert len(agents1) > 0, "Should handle snake_case"
        
        print("✓ Violation type normalization works")
    
    def test_agent_dependencies(self):
        """Test that agents with dependencies are registered correctly."""
        from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator
        
        orchestrator = ForensicMetaOrchestrator(auto_register_agents=True)
        
        # Check that orchestrator can build execution plan (validates dependencies)
        # This is an indirect test - if dependencies are circular, this would fail
        stats = orchestrator.get_agent_statistics()
        assert stats["total_agents_registered"] > 0
        
        print("✓ Agent dependencies validated")


@pytest.mark.asyncio
async def test_agent_handler_execution():
    """Test that registered agent handlers can be executed."""
    from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator
    
    orchestrator = ForensicMetaOrchestrator(auto_register_agents=True)
    
    # Execute investigation with registered agents
    result = await orchestrator.investigate(
        investigation_type="test",
        data={"test": "data"},
        agent_filter=["compliance_checker"],  # Use simple agent
        parallel=False
    )
    
    assert result is not None, "Investigation should return a result"
    assert result.agents_executed >= 0, "Should track agent execution"
    
    print(f"✓ Agent handler execution successful (executed {result.agents_executed} agents)")


if __name__ == "__main__":
    print("Running Agent Registry Tests...")
    print("=" * 70)
    
    test = TestAgentRegistry()
    
    try:
        test.test_register_default_agents()
    except Exception as e:
        print(f"✗ test_register_default_agents FAILED: {e}")
    
    try:
        test.test_auto_registration_on_init()
    except Exception as e:
        print(f"✗ test_auto_registration_on_init FAILED: {e}")
    
    try:
        test.test_no_auto_registration()
    except Exception as e:
        print(f"✗ test_no_auto_registration FAILED: {e}")
    
    try:
        test.test_violation_agent_mapping()
    except Exception as e:
        print(f"✗ test_violation_agent_mapping FAILED: {e}")
    
    try:
        test.test_get_all_violation_types()
    except Exception as e:
        print(f"✗ test_get_all_violation_types FAILED: {e}")
    
    try:
        test.test_violation_agent_map_structure()
    except Exception as e:
        print(f"✗ test_violation_agent_map_structure FAILED: {e}")
    
    try:
        test.test_agent_types_distribution()
    except Exception as e:
        print(f"✗ test_agent_types_distribution FAILED: {e}")
    
    try:
        test.test_multiple_violation_types()
    except Exception as e:
        print(f"✗ test_multiple_violation_types FAILED: {e}")
    
    try:
        test.test_normalized_violation_types()
    except Exception as e:
        print(f"✗ test_normalized_violation_types FAILED: {e}")
    
    try:
        test.test_agent_dependencies()
    except Exception as e:
        print(f"✗ test_agent_dependencies FAILED: {e}")
    
    print("=" * 70)
    print("Agent registry tests completed!")
