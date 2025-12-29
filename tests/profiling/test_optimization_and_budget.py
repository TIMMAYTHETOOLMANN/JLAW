"""
Tests for Optimization Analyzer and Budget Enforcer
====================================================

Tests for optimization analysis, budget enforcement, and timeline visualization.
"""

import pytest
import time
from pathlib import Path

from src.profiling.performance_metrics import PerformanceMetricsCollector
from src.profiling.optimization_analyzer import OptimizationAnalyzer
from src.profiling.budget_enforcer import BudgetEnforcer, BudgetExceededError
from src.profiling.timeline_visualizer import TimelineVisualizer


class TestOptimizationAnalyzer:
    """Test OptimizationAnalyzer."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = OptimizationAnalyzer()
        assert analyzer is not None
        print("✓ OptimizationAnalyzer initialized")
    
    def test_identify_token_heavy_agents(self):
        """Test identifying token-heavy agents."""
        collector = PerformanceMetricsCollector()
        analyzer = OptimizationAnalyzer()
        
        # Create token-heavy agent
        collector.start_agent("heavy-agent", "anthropic", "subagent")
        collector.end_agent("heavy-agent", input_tokens=15000, output_tokens=5000)
        
        # Create normal agent
        collector.start_agent("normal-agent", "anthropic", "subagent")
        collector.end_agent("normal-agent", input_tokens=3000, output_tokens=1000)
        
        token_heavy = analyzer._identify_token_heavy_agents(collector)
        
        assert len(token_heavy) == 1
        assert token_heavy[0]["agent"] == "heavy-agent"
        print("✓ Token-heavy agent identification works")
    
    def test_identify_cost_heavy_agents(self):
        """Test identifying cost-heavy agents."""
        collector = PerformanceMetricsCollector()
        analyzer = OptimizationAnalyzer()
        
        # Create expensive agent (using opus)
        collector.start_agent("expensive", "anthropic", "subagent", model="claude-opus-4")
        collector.end_agent("expensive", input_tokens=20000, output_tokens=5000, model="claude-opus-4")
        
        # Create cheap agent
        collector.start_agent("cheap", "anthropic", "subagent", model="claude-haiku-3")
        collector.end_agent("cheap", input_tokens=5000, output_tokens=1000, model="claude-haiku-3")
        
        cost_heavy = analyzer._identify_cost_heavy_agents(collector)
        
        assert len(cost_heavy) >= 1
        assert cost_heavy[0]["agent"] == "expensive"
        print("✓ Cost-heavy agent identification works")
    
    def test_identify_low_value_agents(self):
        """Test identifying low-value agents."""
        collector = PerformanceMetricsCollector()
        analyzer = OptimizationAnalyzer()
        
        # Create low-value agent (high cost, few violations)
        # Use expensive model (opus) to ensure cost > $0.20
        collector.start_agent("low-value", "anthropic", "subagent", model="claude-opus-4")
        collector.end_agent(
            "low-value",
            input_tokens=10000,
            output_tokens=3000,
            model="claude-opus-4",
            violations_found=1  # Only 1 violation
        )
        
        low_value = analyzer._identify_low_value_agents(collector)
        
        assert len(low_value) >= 1
        assert low_value[0]["violations"] == 1
        print("✓ Low-value agent identification works")
    
    def test_analyze_generates_recommendations(self):
        """Test that analyze generates recommendations."""
        collector = PerformanceMetricsCollector()
        analyzer = OptimizationAnalyzer()
        
        # Create various types of agents
        collector.start_agent("heavy", "anthropic", "subagent", model="claude-opus-4")
        collector.end_agent("heavy", input_tokens=20000, output_tokens=5000, model="claude-opus-4", violations_found=1)
        
        collector.start_agent("slow", "anthropic", "subagent")
        slow_start = time.time()
        agent = collector.agent_metrics[-1]
        agent.start_time = slow_start - 65  # Make it appear 65 seconds old
        collector.end_agent("slow", input_tokens=5000, output_tokens=1000)
        
        result = analyzer.analyze(collector)
        
        assert "recommendations" in result
        assert "potential_savings" in result
        assert "summary" in result
        assert isinstance(result["recommendations"], list)
        print(f"✓ Analysis generated {len(result['recommendations'])} recommendations")
    
    def test_estimate_savings(self):
        """Test savings estimation."""
        collector = PerformanceMetricsCollector()
        analyzer = OptimizationAnalyzer()
        
        # Create expensive agents
        for i in range(3):
            collector.start_agent(f"agent-{i}", "anthropic", "subagent", model="claude-opus-4")
            collector.end_agent(
                f"agent-{i}",
                input_tokens=10000,
                output_tokens=3000,
                model="claude-opus-4",
                violations_found=2
            )
        
        result = analyzer.analyze(collector)
        savings = result["potential_savings"]
        
        assert "total" in savings
        assert savings["total"] >= 0
        print(f"✓ Estimated savings: ${savings['total']:.4f}")


class TestBudgetEnforcer:
    """Test BudgetEnforcer."""
    
    def test_enforcer_initialization(self):
        """Test budget enforcer initialization."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=1.0)
        
        assert enforcer.max_tokens == 10000
        assert enforcer.max_cost_usd == 1.0
        assert enforcer.current_tokens == 0
        assert enforcer.current_cost == 0.0
        print("✓ BudgetEnforcer initialized")
    
    def test_check_budget_within_limits(self):
        """Test budget check when within limits."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=1.0)
        
        # Should not raise
        enforcer.check_budget(tokens=5000, cost=0.5)
        print("✓ Budget check passed when within limits")
    
    def test_check_budget_exceeds_tokens(self):
        """Test budget check when exceeding token limit."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=10.0, strict_mode=True)
        
        with pytest.raises(BudgetExceededError) as exc_info:
            enforcer.check_budget(tokens=15000, cost=0.5)
        
        assert exc_info.value.budget_type == "tokens"
        print("✓ Token budget exceeded error raised correctly")
    
    def test_check_budget_exceeds_cost(self):
        """Test budget check when exceeding cost limit."""
        enforcer = BudgetEnforcer(max_tokens=100000, max_cost_usd=1.0, strict_mode=True)
        
        with pytest.raises(BudgetExceededError) as exc_info:
            enforcer.check_budget(tokens=5000, cost=2.0)
        
        assert exc_info.value.budget_type == "cost"
        print("✓ Cost budget exceeded error raised correctly")
    
    def test_record_usage(self):
        """Test recording usage."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=1.0)
        
        enforcer.record_usage(tokens=3000, cost=0.3)
        
        assert enforcer.current_tokens == 3000
        assert enforcer.current_cost == 0.3
        
        enforcer.record_usage(tokens=2000, cost=0.2)
        
        assert enforcer.current_tokens == 5000
        assert enforcer.current_cost == 0.5
        print("✓ Usage recording works correctly")
    
    def test_get_status(self):
        """Test getting budget status."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=1.0)
        enforcer.record_usage(tokens=5000, cost=0.5)
        
        status = enforcer.get_status()
        
        assert status.tokens_used == 5000
        assert status.tokens_remaining == 5000
        assert status.tokens_percentage == 50.0
        assert status.cost_used == 0.5
        assert status.cost_remaining == 0.5
        assert status.cost_percentage == 50.0
        assert not status.at_risk
        assert not status.exceeded
        print("✓ Budget status calculated correctly")
    
    def test_at_risk_detection(self):
        """Test at-risk detection (>80% budget used)."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=1.0)
        enforcer.record_usage(tokens=8500, cost=0.85)
        
        status = enforcer.get_status()
        
        assert status.at_risk
        assert not status.exceeded
        print("✓ At-risk detection works correctly")
    
    def test_exceeded_detection(self):
        """Test exceeded detection (>100% budget used)."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=1.0, strict_mode=False)
        enforcer.record_usage(tokens=11000, cost=1.1)
        
        status = enforcer.get_status()
        
        assert status.exceeded
        print("✓ Exceeded detection works correctly")
    
    def test_reset(self):
        """Test resetting budget counters."""
        enforcer = BudgetEnforcer(max_tokens=10000, max_cost_usd=1.0)
        enforcer.record_usage(tokens=5000, cost=0.5)
        
        enforcer.reset()
        
        assert enforcer.current_tokens == 0
        assert enforcer.current_cost == 0.0
        print("✓ Budget reset works correctly")


class TestTimelineVisualizer:
    """Test TimelineVisualizer."""
    
    def test_visualizer_initialization(self):
        """Test timeline visualizer initialization."""
        visualizer = TimelineVisualizer()
        assert visualizer is not None
        print("✓ TimelineVisualizer initialized")
    
    def test_generate_timeline_empty(self):
        """Test generating timeline with no data."""
        collector = PerformanceMetricsCollector()
        visualizer = TimelineVisualizer()
        
        timeline = visualizer.generate_timeline(collector)
        
        assert timeline["investigation_id"] == collector.investigation_id
        assert timeline["total_duration"] == 0.0
        assert len(timeline["phases"]) == 0
        assert len(timeline["agents"]) == 0
        print("✓ Empty timeline generation works")
    
    def test_generate_timeline_with_data(self):
        """Test generating timeline with data."""
        collector = PerformanceMetricsCollector()
        visualizer = TimelineVisualizer()
        
        # Add some metrics
        collector.start_phase("phase-1", "Test Phase")
        collector.start_agent("agent-1", "anthropic", "subagent")
        time.sleep(0.1)
        collector.end_agent("agent-1", input_tokens=1000, output_tokens=500)
        collector.end_phase("phase-1")
        
        timeline = visualizer.generate_timeline(collector)
        
        assert len(timeline["phases"]) == 1
        assert len(timeline["agents"]) == 1
        assert timeline["phases"][0]["name"] == "Test Phase"
        assert timeline["agents"][0]["name"] == "agent-1"
        print("✓ Timeline generation with data works")
    
    def test_export_json(self, tmp_path):
        """Test exporting timeline to JSON."""
        collector = PerformanceMetricsCollector()
        visualizer = TimelineVisualizer()
        
        collector.start_agent("agent-1", "anthropic", "subagent")
        collector.end_agent("agent-1", input_tokens=1000, output_tokens=500)
        
        timeline = visualizer.generate_timeline(collector)
        output_path = tmp_path / "timeline.json"
        visualizer.export_json(timeline, output_path)
        
        assert output_path.exists()
        
        import json
        with open(output_path) as f:
            data = json.load(f)
        
        assert "investigation_id" in data
        assert "agents" in data
        print("✓ Timeline JSON export works")
    
    def test_generate_gantt_html(self, tmp_path):
        """Test generating Gantt chart HTML."""
        collector = PerformanceMetricsCollector()
        visualizer = TimelineVisualizer()
        
        collector.start_phase("phase-1", "Test Phase")
        collector.start_agent("agent-1", "anthropic", "subagent")
        collector.end_agent("agent-1", input_tokens=1000, output_tokens=500)
        collector.end_phase("phase-1")
        
        timeline = visualizer.generate_timeline(collector)
        output_path = tmp_path / "gantt.html"
        visualizer.generate_gantt_html(timeline, output_path)
        
        assert output_path.exists()
        
        with open(output_path) as f:
            html = f.read()
        
        assert "JLAW Execution Timeline" in html
        assert "Test Phase" in html
        print("✓ Gantt chart HTML generation works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
