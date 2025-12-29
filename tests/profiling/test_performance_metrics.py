"""
Tests for Performance Metrics Collector
========================================

Comprehensive tests for performance metrics collection, cost calculation,
and reporting functionality.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock

from src.profiling.performance_metrics import (
    PerformanceMetricsCollector,
    AgentMetrics,
    PhaseMetrics
)


class TestAgentMetrics:
    """Test AgentMetrics dataclass."""
    
    def test_agent_metrics_creation(self):
        """Test creating agent metrics."""
        metrics = AgentMetrics(
            agent_name="test-agent",
            agent_type="anthropic",
            tier="subagent",
            start_time=time.time()
        )
        
        assert metrics.agent_name == "test-agent"
        assert metrics.agent_type == "anthropic"
        assert metrics.tier == "subagent"
        assert metrics.status == "pending"
        assert metrics.total_tokens == 0
        print("✓ AgentMetrics created successfully")
    
    def test_agent_metrics_to_dict(self):
        """Test converting agent metrics to dictionary."""
        metrics = AgentMetrics(
            agent_name="test-agent",
            agent_type="openai",
            tier="primary",
            start_time=time.time(),
            input_tokens=1000,
            output_tokens=500,
            violations_found=3
        )
        
        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["agent_name"] == "test-agent"
        assert metrics_dict["input_tokens"] == 1000
        assert metrics_dict["output_tokens"] == 500
        print("✓ AgentMetrics to_dict works correctly")


class TestPhaseMetrics:
    """Test PhaseMetrics dataclass."""
    
    def test_phase_metrics_creation(self):
        """Test creating phase metrics."""
        metrics = PhaseMetrics(
            phase_id="phase-1",
            phase_name="Test Phase",
            start_time=time.time()
        )
        
        assert metrics.phase_id == "phase-1"
        assert metrics.phase_name == "Test Phase"
        assert metrics.status == "pending"
        assert len(metrics.agent_metrics) == 0
        print("✓ PhaseMetrics created successfully")


class TestPerformanceMetricsCollector:
    """Test PerformanceMetricsCollector."""
    
    def test_collector_initialization(self):
        """Test that collector initializes correctly."""
        collector = PerformanceMetricsCollector()
        
        assert collector.investigation_id is not None
        assert len(collector.phase_metrics) == 0
        assert len(collector.agent_metrics) == 0
        assert collector.start_time > 0
        print("✓ PerformanceMetricsCollector initialized")
    
    def test_start_end_phase(self):
        """Test phase tracking."""
        collector = PerformanceMetricsCollector()
        
        # Start phase
        phase = collector.start_phase("phase-1", "Test Phase")
        assert phase.phase_id == "phase-1"
        assert phase.phase_name == "Test Phase"
        assert len(collector.phase_metrics) == 1
        
        # End phase
        time.sleep(0.1)  # Small delay
        collector.end_phase("phase-1", status="success")
        
        assert phase.end_time is not None
        assert phase.duration_seconds > 0
        assert phase.status == "success"
        print("✓ Phase tracking works correctly")
    
    def test_start_end_agent(self):
        """Test agent tracking."""
        collector = PerformanceMetricsCollector()
        
        # Start agent
        agent = collector.start_agent(
            "test-agent",
            "anthropic",
            "subagent",
            model="claude-sonnet-3.5"
        )
        
        assert agent.agent_name == "test-agent"
        assert agent.agent_type == "anthropic"
        assert len(collector.agent_metrics) == 1
        
        # End agent
        time.sleep(0.1)  # Small delay
        collector.end_agent(
            "test-agent",
            input_tokens=5000,
            output_tokens=1500,
            model="claude-sonnet-3.5",
            violations_found=3,
            status="success"
        )
        
        assert agent.end_time is not None
        assert agent.duration_seconds > 0
        assert agent.input_tokens == 5000
        assert agent.output_tokens == 1500
        assert agent.total_tokens == 6500
        assert agent.violations_found == 3
        assert agent.status == "success"
        print("✓ Agent tracking works correctly")
    
    def test_cost_calculation_anthropic(self):
        """Test cost calculation for Anthropic models."""
        collector = PerformanceMetricsCollector()
        
        # Test Claude Sonnet
        collector.start_agent("sonnet-agent", "anthropic", "subagent", model="claude-sonnet-3.5")
        collector.end_agent(
            "sonnet-agent",
            input_tokens=10000,
            output_tokens=2000,
            model="claude-sonnet-3.5"
        )
        
        agent = collector.agent_metrics[0]
        # Sonnet: $0.003/1K input, $0.015/1K output
        expected_input_cost = (10000 / 1000) * 0.003  # $0.03
        expected_output_cost = (2000 / 1000) * 0.015  # $0.03
        expected_total = expected_input_cost + expected_output_cost  # $0.06
        
        assert abs(agent.input_cost - expected_input_cost) < 0.001
        assert abs(agent.output_cost - expected_output_cost) < 0.001
        assert abs(agent.total_cost - expected_total) < 0.001
        print(f"✓ Anthropic cost calculation correct: ${agent.total_cost:.4f}")
    
    def test_cost_calculation_openai(self):
        """Test cost calculation for OpenAI models."""
        collector = PerformanceMetricsCollector()
        
        # Test GPT-4o
        collector.start_agent("gpt4o-agent", "openai", "primary", model="gpt-4o")
        collector.end_agent(
            "gpt4o-agent",
            input_tokens=10000,
            output_tokens=2000,
            model="gpt-4o"
        )
        
        agent = collector.agent_metrics[0]
        # GPT-4o: $0.0025/1K input, $0.01/1K output
        expected_input_cost = (10000 / 1000) * 0.0025  # $0.025
        expected_output_cost = (2000 / 1000) * 0.01    # $0.02
        expected_total = expected_input_cost + expected_output_cost  # $0.045
        
        assert abs(agent.input_cost - expected_input_cost) < 0.001
        assert abs(agent.output_cost - expected_output_cost) < 0.001
        assert abs(agent.total_cost - expected_total) < 0.001
        print(f"✓ OpenAI cost calculation correct: ${agent.total_cost:.4f}")
    
    def test_agent_ranking(self):
        """Test agent ranking by cost."""
        collector = PerformanceMetricsCollector()
        
        # Create multiple agents with different costs
        agents_data = [
            ("expensive-agent", 20000, 5000, "claude-opus-4"),
            ("cheap-agent", 5000, 1000, "claude-haiku-3"),
            ("medium-agent", 10000, 2000, "claude-sonnet-3.5")
        ]
        
        for name, input_tokens, output_tokens, model in agents_data:
            collector.start_agent(name, "anthropic", "subagent", model=model)
            collector.end_agent(
                name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
                violations_found=2
            )
        
        ranking = collector._get_agent_ranking()
        
        assert len(ranking) == 3
        # Most expensive should be first (opus)
        assert ranking[0]["agent_name"] == "expensive-agent"
        # Cheapest should be last (haiku)
        assert ranking[-1]["agent_name"] == "cheap-agent"
        print("✓ Agent ranking works correctly")
    
    def test_get_summary(self):
        """Test getting performance summary."""
        collector = PerformanceMetricsCollector()
        
        # Create some metrics
        collector.start_phase("phase-1", "Test Phase")
        
        collector.start_agent("agent-1", "anthropic", "subagent", model="claude-sonnet-3.5")
        collector.end_agent("agent-1", input_tokens=5000, output_tokens=1000, violations_found=3)
        
        collector.start_agent("agent-2", "openai", "primary", model="gpt-4o")
        collector.end_agent("agent-2", input_tokens=3000, output_tokens=500, violations_found=1)
        
        collector.end_phase("phase-1", status="success")
        
        summary = collector.get_summary()
        
        assert summary["total_phases"] == 1
        assert summary["total_agents_invoked"] == 2
        assert summary["total_tokens"] == 9500  # 5000+1000+3000+500
        assert summary["total_violations_found"] == 4  # 3+1
        assert summary["success_count"] == 2
        assert "tier_breakdown" in summary
        assert "phase_breakdown" in summary
        print("✓ Summary generation works correctly")
    
    def test_export_detailed_report(self, tmp_path):
        """Test exporting detailed report."""
        collector = PerformanceMetricsCollector()
        
        # Create some metrics
        collector.start_phase("phase-1", "Test Phase")
        collector.start_agent("agent-1", "anthropic", "subagent", model="claude-sonnet-3.5")
        collector.end_agent("agent-1", input_tokens=5000, output_tokens=1000, violations_found=3)
        collector.end_phase("phase-1", status="success")
        
        # Export report
        output_path = tmp_path / "metrics.json"
        collector.export_detailed_report(output_path)
        
        assert output_path.exists()
        
        import json
        with open(output_path) as f:
            report = json.load(f)
        
        assert "investigation_id" in report
        assert "summary" in report
        assert "phases" in report
        assert "agent_ranking" in report
        print("✓ Detailed report export works correctly")
    
    def test_phase_agent_association(self):
        """Test that agents are correctly associated with phases."""
        collector = PerformanceMetricsCollector()
        
        # Start phase
        phase = collector.start_phase("phase-1", "Test Phase")
        
        # Start and end agent within phase
        collector.start_agent("agent-1", "anthropic", "subagent")
        collector.end_agent("agent-1", input_tokens=1000, output_tokens=500)
        
        # End phase
        collector.end_phase("phase-1")
        
        # Check association
        assert len(phase.agent_metrics) == 1
        assert phase.agent_metrics[0].agent_name == "agent-1"
        assert phase.total_tokens == 1500
        print("✓ Phase-agent association works correctly")
    
    def test_multiple_agents_same_name(self):
        """Test handling multiple invocations of same agent."""
        collector = PerformanceMetricsCollector()
        
        # First invocation
        collector.start_agent("repeated-agent", "anthropic", "subagent")
        collector.end_agent("repeated-agent", input_tokens=1000, output_tokens=500)
        
        # Second invocation
        collector.start_agent("repeated-agent", "anthropic", "subagent")
        collector.end_agent("repeated-agent", input_tokens=2000, output_tokens=1000)
        
        # Should have 2 separate metrics
        assert len(collector.agent_metrics) == 2
        assert collector.agent_metrics[0].input_tokens == 1000
        assert collector.agent_metrics[1].input_tokens == 2000
        print("✓ Multiple same-name agents tracked separately")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
