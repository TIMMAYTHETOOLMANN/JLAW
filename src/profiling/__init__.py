"""
JLAW Runtime Profiling Framework
=================================

Comprehensive performance profiling, cost tracking, and optimization
recommendations for JLAW forensic analysis investigations.

Modules:
- performance_metrics: Enhanced metrics collection with cost tracking
- optimization_analyzer: Optimization recommendations engine
- timeline_visualizer: Execution timeline and Gantt chart generation
- budget_enforcer: Token and cost budget enforcement

Usage:
    from src.profiling import PerformanceMetricsCollector, OptimizationAnalyzer
    
    collector = PerformanceMetricsCollector()
    # ... run investigation ...
    analyzer = OptimizationAnalyzer()
    recommendations = analyzer.analyze(collector)
"""

from .performance_metrics import (
    PerformanceMetricsCollector,
    AgentMetrics,
    PhaseMetrics
)
from .optimization_analyzer import OptimizationAnalyzer
from .timeline_visualizer import TimelineVisualizer
from .budget_enforcer import BudgetEnforcer, BudgetExceededError

__all__ = [
    "PerformanceMetricsCollector",
    "AgentMetrics",
    "PhaseMetrics",
    "OptimizationAnalyzer",
    "TimelineVisualizer",
    "BudgetEnforcer",
    "BudgetExceededError",
]
