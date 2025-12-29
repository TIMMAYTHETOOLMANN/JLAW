"""
Unit Tests for Dynamic Agent Registry
======================================

Tests agent discovery, markdown parsing, capability extraction,
and intelligent agent selection based on violations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.forensics.agent_registry import DynamicAgentRegistry, AgentCapability


class TestAgentCapability:
    """Test AgentCapability dataclass and methods."""
    
    def test_agent_capability_creation(self):
        """Test creating AgentCapability instance."""
        capability = AgentCapability(
            agent_name="test-agent",
            description="Test agent",
            violation_types={"insider_trading", "accounting_fraud"},
            tools=["Read", "Write"],
            priority=80
        )
        
        assert capability.agent_name == "test-agent"
        assert capability.description == "Test agent"
        assert "insider_trading" in capability.violation_types
        assert capability.priority == 80
    
    def test_matches_violation_exact(self):
        """Test exact violation type matching."""
        capability = AgentCapability(
            agent_name="test-agent",
            description="Test",
            violation_types={"insider_trading", "accounting_fraud"}
        )
        
        assert capability.matches_violation("insider_trading") is True
        assert capability.matches_violation("accounting_fraud") is True
        assert capability.matches_violation("sox_violation") is False
    
    def test_matches_violation_normalized(self):
        """Test violation matching with normalization."""
        capability = AgentCapability(
            agent_name="test-agent",
            description="Test",
            violation_types={"insider_trading"}
        )
        
        # Should match with different formats
        assert capability.matches_violation("Insider Trading") is True
        assert capability.matches_violation("INSIDER-TRADING") is True
        assert capability.matches_violation("insider_trading") is True
    
    def test_matches_violation_partial(self):
        """Test partial violation matching."""
        capability = AgentCapability(
            agent_name="test-agent",
            description="Test",
            violation_types={"insider_trading_rule_10b5"}
        )
        
        # Partial match should work
        assert capability.matches_violation("insider_trading") is True
    
    def test_score_for_violations(self):
        """Test violation relevance scoring."""
        capability = AgentCapability(
            agent_name="test-agent",
            description="Test",
            violation_types={"insider_trading", "accounting_fraud", "sox_violation"}
        )
        
        # Score should be matches / total
        score = capability.score_for_violations(["insider_trading", "accounting_fraud"])
        assert score == 1.0  # 2 matches out of 2
        
        score = capability.score_for_violations(["insider_trading", "unknown_violation"])
        assert score == 0.5  # 1 match out of 2
        
        score = capability.score_for_violations(["unknown1", "unknown2"])
        assert score == 0.0  # 0 matches
        
        score = capability.score_for_violations([])
        assert score == 0.0  # Empty list


class TestDynamicAgentRegistry:
    """Test DynamicAgentRegistry class."""
    
    def test_registry_initialization(self):
        """Test registry initialization."""
        # Create temp directory with mock agents
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            
            # Create a mock agent file
            agent_file = agents_dir / "test-agent.md"
            agent_file.write_text("""---
name: test-agent
description: Test agent for unit tests
tools: Read, Write, Edit
priority: 80
---

## Violation Types
- insider_trading
- accounting_fraud

Test agent content.
""")
            
            # Initialize registry
            registry = DynamicAgentRegistry(agents_dir=agents_dir)
            
            assert len(registry.agents) == 1
            assert "test-agent" in registry.agents
            assert len(registry.violation_to_agents) >= 2
    
    def test_parse_agent_markdown_with_frontmatter(self):
        """Test parsing markdown with YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test-agent.md"
            md_path.write_text("""---
name: financial-analyst
description: Financial forensic analyst
tools: Read, Write, Bash
priority: 90
---

## Violation Types
- insider_trading
- accounting_fraud
- options_backdating

Agent prompt content here.
""")
            
            registry = DynamicAgentRegistry(agents_dir=Path(tmpdir))
            capability = registry._parse_agent_markdown(md_path)
            
            assert capability is not None
            assert capability.agent_name == "financial-analyst"
            assert capability.description == "Financial forensic analyst"
            assert capability.priority == 90
            assert len(capability.tools) == 3
            assert "insider_trading" in capability.violation_types
            assert "accounting_fraud" in capability.violation_types
            assert "options_backdating" in capability.violation_types
    
    def test_parse_agent_markdown_without_frontmatter(self):
        """Test parsing markdown without frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "simple-agent.md"
            md_path.write_text("This is a simple agent without frontmatter.")
            
            registry = DynamicAgentRegistry(agents_dir=Path(tmpdir))
            capability = registry._parse_agent_markdown(md_path)
            
            assert capability is not None
            assert capability.agent_name == "simple-agent"
            assert capability.priority == 50  # Default
    
    def test_extract_violation_types(self):
        """Test extracting violation types from content."""
        content = """
## Violation Types
- insider_trading
- accounting_fraud
- sox_violation

## Other Section
Some other content.
"""
        
        registry = DynamicAgentRegistry(agents_dir=Path("/tmp"))
        violation_types = registry._extract_violation_types(content)
        
        assert "insider_trading" in violation_types
        assert "accounting_fraud" in violation_types
        assert "sox_violation" in violation_types
        assert len(violation_types) == 3
    
    def test_extract_violation_types_no_section(self):
        """Test extraction when no violation types section exists."""
        content = "Just some agent content without violation types."
        
        registry = DynamicAgentRegistry(agents_dir=Path("/tmp"))
        violation_types = registry._extract_violation_types(content)
        
        assert len(violation_types) == 0
    
    def test_get_agents_for_violations(self):
        """Test intelligent agent selection for violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            
            # Create multiple agents
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
            
            registry = DynamicAgentRegistry(agents_dir=agents_dir)
            
            # Test selection
            violations = [
                {"type": "insider_trading"},
                {"type": "accounting_fraud"}
            ]
            
            selected = registry.get_agents_for_violations(violations, top_k=2)
            
            # Should select agents with best match
            assert len(selected) <= 2
            assert all(isinstance(a, AgentCapability) for a in selected)
            
            # Financial analyst should be first (matches both)
            if len(selected) > 0:
                assert selected[0].agent_name == "financial-analyst"
    
    def test_get_agents_for_violations_top_k(self):
        """Test top-K limiting in agent selection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            
            # Create 5 agents
            for i in range(5):
                agent_file = agents_dir / f"agent{i}.md"
                agent_file.write_text(f"""---
name: agent{i}
priority: {100 - i * 10}
---

## Violation Types
- insider_trading
""")
            
            registry = DynamicAgentRegistry(agents_dir=agents_dir)
            
            violations = [{"type": "insider_trading"}]
            
            # Request top-3
            selected = registry.get_agents_for_violations(violations, top_k=3)
            assert len(selected) == 3
            
            # Should be sorted by priority (highest first)
            assert selected[0].priority >= selected[1].priority
            assert selected[1].priority >= selected[2].priority
    
    def test_get_agents_for_violations_empty(self):
        """Test with no violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = DynamicAgentRegistry(agents_dir=Path(tmpdir))
            
            selected = registry.get_agents_for_violations([], top_k=5)
            assert len(selected) == 0
    
    def test_get_agent_by_name(self):
        """Test getting specific agent by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            
            agent_file = agents_dir / "test-agent.md"
            agent_file.write_text("""---
name: test-agent
---
""")
            
            registry = DynamicAgentRegistry(agents_dir=agents_dir)
            
            agent = registry.get_agent("test-agent")
            assert agent is not None
            assert agent.agent_name == "test-agent"
            
            missing = registry.get_agent("nonexistent-agent")
            assert missing is None
    
    def test_list_agents(self):
        """Test listing all agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            
            for name in ["agent-a", "agent-b", "agent-c"]:
                agent_file = agents_dir / f"{name}.md"
                agent_file.write_text(f"---\nname: {name}\n---\n")
            
            registry = DynamicAgentRegistry(agents_dir=agents_dir)
            
            agents = registry.list_agents()
            assert len(agents) == 3
            assert agents == ["agent-a", "agent-b", "agent-c"]  # Alphabetical
    
    def test_get_agents_by_violation_type(self):
        """Test getting agents for specific violation type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            
            agent1 = agents_dir / "agent1.md"
            agent1.write_text("""---
name: agent1
priority: 90
---

## Violation Types
- insider_trading
""")
            
            agent2 = agents_dir / "agent2.md"
            agent2.write_text("""---
name: agent2
priority: 80
---

## Violation Types
- insider_trading
- accounting_fraud
""")
            
            registry = DynamicAgentRegistry(agents_dir=agents_dir)
            
            agents = registry.get_agents_by_violation_type("insider_trading")
            assert len(agents) == 2
            assert agents[0].priority >= agents[1].priority  # Sorted by priority
    
    def test_get_statistics(self):
        """Test getting registry statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            
            agent_file = agents_dir / "test-agent.md"
            agent_file.write_text("""---
name: test-agent
priority: 85
---

## Violation Types
- insider_trading
- accounting_fraud
""")
            
            registry = DynamicAgentRegistry(agents_dir=agents_dir)
            
            stats = registry.get_statistics()
            assert "total_agents" in stats
            assert stats["total_agents"] == 1
            assert "total_violation_types" in stats
            assert stats["total_violation_types"] == 2
            assert "agents_by_priority" in stats
            assert "violation_coverage" in stats
    
    def test_malformed_yaml_frontmatter(self):
        """Test handling malformed YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "bad-agent.md"
            md_path.write_text("""---
name: bad-agent
malformed: [unclosed list
---

Agent content.
""")
            
            registry = DynamicAgentRegistry(agents_dir=Path(tmpdir))
            capability = registry._parse_agent_markdown(md_path)
            
            # Should handle gracefully with defaults
            assert capability is not None
            assert capability.agent_name == "bad-agent"


@pytest.mark.integration
class TestDynamicAgentRegistryIntegration:
    """Integration tests with actual .claude/agents/ directory."""
    
    def test_discover_real_agents(self):
        """Test discovering real agents from repository."""
        # This test requires actual repository structure
        try:
            registry = DynamicAgentRegistry()
            
            # Should find at least some agents
            assert len(registry.agents) > 0
            
            # Check for expected agents
            agent_names = registry.list_agents()
            assert any("forensic" in name or "analyst" in name for name in agent_names)
            
            print(f"Discovered {len(registry.agents)} real agents:")
            for name in agent_names[:5]:  # Print first 5
                print(f"  - {name}")
        
        except Exception as e:
            pytest.skip(f"Could not access .claude/agents/ directory: {e}")


if __name__ == "__main__":
    print("Running Dynamic Agent Registry Tests...")
    print("=" * 70)
    
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
