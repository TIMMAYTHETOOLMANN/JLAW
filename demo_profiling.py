#!/usr/bin/env python3
"""
JLAW Performance Profiling Demonstration
=========================================

Demonstrates the performance profiling capabilities with a simulated investigation.

This script showcases:
1. Performance metrics collection
2. Cost tracking and calculation
3. Optimization analysis
4. Budget enforcement
5. Timeline visualization
6. Report generation

Usage:
    python demo_profiling.py
"""

import asyncio
import time
from pathlib import Path

from src.profiling import (
    PerformanceMetricsCollector,
    OptimizationAnalyzer,
    TimelineVisualizer,
    BudgetEnforcer,
    BudgetExceededError
)


def simulate_agent_execution(name: str, duration: float, tokens: tuple):
    """Simulate agent execution with sleep."""
    time.sleep(duration)
    return {"input_tokens": tokens[0], "output_tokens": tokens[1]}


def main():
    """Run profiling demonstration."""
    
    print("=" * 80)
    print("  JLAW PERFORMANCE PROFILING DEMONSTRATION")
    print("=" * 80)
    print()
    
    # ========================================================================
    # 1. Initialize Components
    # ========================================================================
    
    print("📊 Initializing profiling components...")
    
    collector = PerformanceMetricsCollector()
    analyzer = OptimizationAnalyzer()
    visualizer = TimelineVisualizer()
    budget = BudgetEnforcer(
        max_tokens=50000,
        max_cost_usd=2.50,
        strict_mode=False  # Warning mode
    )
    
    print(f"   ✓ Performance metrics collector: {collector.investigation_id[:8]}...")
    print(f"   ✓ Budget enforcer: {budget}")
    print()
    
    # ========================================================================
    # 2. Simulate Investigation with Profiling
    # ========================================================================
    
    print("🔍 Simulating forensic investigation...")
    print()
    
    # Start investigation phase
    collector.start_phase("investigation", "Simulated Forensic Investigation")
    
    # Tier 1: Primary agents (expensive but thorough)
    print("└─ TIER 1: Primary Agents")
    
    agents = [
        ("openai-gpt4o", "openai", "gpt-4o", 0.3, (8000, 2000)),
        ("anthropic-sonnet", "anthropic", "claude-sonnet-3.5", 0.4, (7000, 1500)),
    ]
    
    for agent_name, agent_type, model, duration, tokens in agents:
        # Check budget
        input_tokens, output_tokens = tokens
        
        # Estimate cost for budget check
        if agent_type == "openai":
            cost_estimate = (input_tokens / 1000) * 0.0025 + (output_tokens / 1000) * 0.01
        else:
            cost_estimate = (input_tokens / 1000) * 0.003 + (output_tokens / 1000) * 0.015
        
        try:
            budget.check_budget(
                tokens=input_tokens + output_tokens,
                cost=cost_estimate,
                agent_name=agent_name
            )
        except BudgetExceededError as e:
            print(f"   ⚠️ Budget exceeded: {e}")
            continue
        
        # Start tracking
        collector.start_agent(agent_name, agent_type, "primary", model=model)
        print(f"   ├─ {agent_name} ({model})...", end="", flush=True)
        
        # Simulate execution
        result = simulate_agent_execution(agent_name, duration, tokens)
        
        # End tracking
        violations_found = 3 if "gpt4o" in agent_name else 2
        collector.end_agent(
            agent_name,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            model=model,
            violations_found=violations_found,
            status="success"
        )
        
        # Record budget usage
        budget.record_usage(
            tokens=input_tokens + output_tokens,
            cost=cost_estimate,
            agent_name=agent_name
        )
        
        print(f" ✓ ({duration:.1f}s, {input_tokens + output_tokens:,} tokens)")
    
    print()
    
    # Tier 2: Subagents (intelligent routing)
    print("└─ TIER 2: Subagents")
    
    subagents = [
        ("forensic-financial", "anthropic", "claude-sonnet-3.5", 0.5, (10000, 3000)),
        ("sec-compliance", "anthropic", "claude-haiku-3", 0.2, (5000, 1000)),
        ("tax-exposure", "anthropic", "claude-sonnet-3.5", 0.4, (8000, 2000)),
    ]
    
    for agent_name, agent_type, model, duration, tokens in subagents:
        input_tokens, output_tokens = tokens
        
        # Estimate cost
        if "haiku" in model:
            cost_estimate = (input_tokens / 1000) * 0.00025 + (output_tokens / 1000) * 0.00125
        else:
            cost_estimate = (input_tokens / 1000) * 0.003 + (output_tokens / 1000) * 0.015
        
        try:
            budget.check_budget(
                tokens=input_tokens + output_tokens,
                cost=cost_estimate,
                agent_name=agent_name
            )
        except BudgetExceededError as e:
            print(f"   ⚠️ Budget exceeded: {e}")
            continue
        
        collector.start_agent(agent_name, agent_type, "subagent", model=model)
        print(f"   ├─ {agent_name} ({model})...", end="", flush=True)
        
        result = simulate_agent_execution(agent_name, duration, tokens)
        
        violations_found = 4 if "financial" in agent_name else (1 if "haiku" in model else 2)
        collector.end_agent(
            agent_name,
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
            model=model,
            violations_found=violations_found,
            status="success"
        )
        
        budget.record_usage(
            tokens=input_tokens + output_tokens,
            cost=cost_estimate,
            agent_name=agent_name
        )
        
        print(f" ✓ ({duration:.1f}s, {input_tokens + output_tokens:,} tokens)")
    
    print()
    
    # End investigation phase
    collector.end_phase("investigation", status="success")
    
    # ========================================================================
    # 3. Generate Performance Summary
    # ========================================================================
    
    print("=" * 80)
    print("📈 PERFORMANCE SUMMARY")
    print("=" * 80)
    
    summary = collector.get_summary()
    
    print(f"\n⏱️  Execution Metrics:")
    print(f"   Total duration: {summary['total_duration_seconds']:.2f}s")
    print(f"   Agents invoked: {summary['total_agents_invoked']}")
    print(f"   Violations found: {summary['total_violations_found']}")
    
    print(f"\n💰 Cost Analysis:")
    print(f"   Total tokens: {summary['total_tokens']:,}")
    print(f"   Total cost: ${summary['total_cost_usd']:.4f}")
    print(f"   Cost per token: ${summary['cost_per_token']:.6f}")
    
    print(f"\n📊 Tier Breakdown:")
    for tier, data in summary['tier_breakdown'].items():
        print(f"   {tier.upper()}: {data['agents']} agents, "
              f"{data['tokens']:,} tokens, ${data['cost']:.4f}")
    
    # ========================================================================
    # 4. Generate Optimization Recommendations
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("🎯 OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    
    optimizations = analyzer.analyze(collector)
    
    if optimizations['recommendations']:
        print()
        for i, rec in enumerate(optimizations['recommendations'], 1):
            print(f"{i}. [{rec['severity'].upper()}] {rec['message']}")
            print(f"   → {rec['suggestion']}")
            if rec.get('agents'):
                print(f"   Agents: {len(rec['agents'])}")
            print()
    else:
        print("\n✅ No optimization recommendations - system is already optimized!\n")
    
    opt_summary = optimizations['summary']
    print(f"💡 Potential Savings:")
    print(f"   Current cost: ${opt_summary['current_cost']:.4f}")
    print(f"   Potential savings: ${opt_summary['potential_savings']:.4f} "
          f"({opt_summary['savings_percentage']:.1f}%)")
    print(f"   Optimized cost: ${opt_summary['optimized_cost']:.4f}")
    
    # ========================================================================
    # 5. Generate Timeline
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("📅 TIMELINE ANALYSIS")
    print("=" * 80)
    
    timeline = visualizer.generate_timeline(collector)
    
    print(f"\n⏱️  Execution Timeline:")
    print(f"   Total duration: {timeline['total_duration']:.2f}s")
    print(f"   Phases: {len(timeline['phases'])}")
    print(f"   Agents: {len(timeline['agents'])}")
    
    if timeline.get('parallelization_opportunities'):
        print(f"\n🚀 Parallelization Opportunities:")
        for opp in timeline['parallelization_opportunities']:
            print(f"   Tier {opp['tier']}: {len(opp['agents'])} agents")
            print(f"   → Could save {opp['time_savings']:.1f}s "
                  f"({opp['savings_percentage']:.1f}%)")
    
    overlap = timeline['overlap_analysis']
    print(f"\n📊 Overlap Analysis:")
    print(f"   Total agent time: {overlap['total_agent_time']:.2f}s")
    print(f"   Actual wall time: {overlap['actual_wall_time']:.2f}s")
    print(f"   Parallelization factor: {overlap['parallelization_factor']:.2f}x")
    print(f"   Overlap: {overlap['overlap_percentage']:.1f}%")
    
    # ========================================================================
    # 6. Budget Status
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("💵 BUDGET STATUS")
    print("=" * 80)
    
    budget_status = budget.get_status()
    
    print(f"\n📊 Token Budget:")
    print(f"   Used: {budget_status.tokens_used:,} / {budget_status.tokens_limit:,}")
    print(f"   Remaining: {budget_status.tokens_remaining:,}")
    print(f"   Usage: {budget_status.tokens_percentage:.1f}%")
    
    print(f"\n💰 Cost Budget:")
    print(f"   Used: ${budget_status.cost_used:.4f} / ${budget_status.cost_limit:.2f}")
    print(f"   Remaining: ${budget_status.cost_remaining:.4f}")
    print(f"   Usage: {budget_status.cost_percentage:.1f}%")
    
    print(f"\n⚠️  Status:")
    print(f"   At risk: {'Yes' if budget_status.at_risk else 'No'}")
    print(f"   Exceeded: {'Yes' if budget_status.exceeded else 'No'}")
    
    # ========================================================================
    # 7. Export Reports
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("💾 EXPORTING REPORTS")
    print("=" * 80)
    
    output_dir = Path("output/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export performance report
    perf_report_path = output_dir / "performance_metrics.json"
    collector.export_detailed_report(perf_report_path)
    print(f"\n✓ Performance report: {perf_report_path}")
    
    # Export timeline
    timeline_path = output_dir / "timeline.json"
    visualizer.export_json(timeline, timeline_path)
    print(f"✓ Timeline report: {timeline_path}")
    
    # Export Gantt chart
    gantt_path = output_dir / "gantt_chart.html"
    visualizer.generate_gantt_html(timeline, gantt_path)
    print(f"✓ Gantt chart: {gantt_path}")
    
    print("\n" + "=" * 80)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("1. Complete visibility into token usage and costs per agent")
    print("2. Real-time budget enforcement prevents runaway costs")
    print("3. Optimization recommendations identify 40-50% cost savings")
    print("4. Timeline analysis reveals parallelization opportunities")
    print("5. Detailed reports enable data-driven optimization decisions")
    print()


if __name__ == "__main__":
    main()
