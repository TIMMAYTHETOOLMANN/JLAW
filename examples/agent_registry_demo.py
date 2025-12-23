#!/usr/bin/env python
"""
Agent Registry Demonstration
============================

Demonstrates the new agent registry functionality for ForensicMetaOrchestrator.
This script shows how agents are automatically registered and can be dynamically
selected based on violation types.

Usage:
    python examples/agent_registry_demo.py
"""

import asyncio
from src.core.forensic_meta_orchestrator import ForensicMetaOrchestrator
from src.core.agent_registry import (
    get_all_violation_types,
    get_agents_for_violations,
    VIOLATION_AGENT_MAP
)


def main():
    print("=" * 80)
    print("JLAW Agent Registry Demonstration")
    print("=" * 80)
    
    # ========================================================================
    # DEMO 1: Auto-Registration on Initialization
    # ========================================================================
    print("\n📦 DEMO 1: Auto-Registration on Initialization")
    print("-" * 80)
    
    orchestrator = ForensicMetaOrchestrator(auto_register_agents=True)
    stats = orchestrator.get_agent_statistics()
    
    print(f"✓ Total agents registered: {stats['total_agents_registered']}")
    print(f"\nAgent Distribution by Type:")
    for agent_type, count in stats['agents_by_type'].items():
        if count > 0:
            print(f"  • {agent_type:30} : {count:2} agents")
    
    # ========================================================================
    # DEMO 2: Violation Types Catalog
    # ========================================================================
    print("\n\n🔍 DEMO 2: Violation Types Catalog")
    print("-" * 80)
    
    violation_types = get_all_violation_types()
    print(f"✓ Total violation types supported: {len(violation_types)}\n")
    
    for idx, vtype in enumerate(violation_types, 1):
        agents = VIOLATION_AGENT_MAP[vtype]
        print(f"{idx:2}. {vtype:30} → {len(agents):2} agents")
    
    # ========================================================================
    # DEMO 3: Dynamic Agent Selection
    # ========================================================================
    print("\n\n⚙️  DEMO 3: Dynamic Agent Selection")
    print("-" * 80)
    
    # Scenario 1: Insider Trading Investigation
    print("\nScenario 1: Insider Trading Investigation")
    agents = get_agents_for_violations(["insider_trading"])
    print(f"  Selected agents ({len(agents)}):")
    for agent in sorted(agents):
        print(f"    • {agent}")
    
    # Scenario 2: Multi-Violation Investigation
    print("\nScenario 2: Multi-Violation Investigation (Insider Trading + Accounting Fraud)")
    agents = get_agents_for_violations(["insider_trading", "accounting_fraud"])
    print(f"  Selected agents ({len(agents)}):")
    for agent in sorted(agents):
        print(f"    • {agent}")
    
    # Scenario 3: Financial Distress Analysis
    print("\nScenario 3: Financial Distress Analysis")
    agents = get_agents_for_violations(["financial_distress"])
    print(f"  Selected agents ({len(agents)}):")
    for agent in sorted(agents):
        print(f"    • {agent}")
    
    # ========================================================================
    # DEMO 4: Disabling Auto-Registration
    # ========================================================================
    print("\n\n🔧 DEMO 4: Manual Control (Disabled Auto-Registration)")
    print("-" * 80)
    
    orchestrator_manual = ForensicMetaOrchestrator(auto_register_agents=False)
    stats_manual = orchestrator_manual.get_agent_statistics()
    
    print(f"✓ Agents registered: {stats_manual['total_agents_registered']} (manual mode)")
    print("  (Agents must be registered manually for custom configurations)")
    
    # ========================================================================
    # DEMO 5: Agent Priority Levels
    # ========================================================================
    print("\n\n🎯 DEMO 5: Agent Priority Distribution")
    print("-" * 80)
    
    from src.core.forensic_meta_orchestrator import AgentPriority
    
    priority_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }
    
    # Count agents by priority (from registered agents)
    for agent_name, (config, handler) in orchestrator._agents.items():
        priority_name = config.priority.name
        priority_counts[priority_name] += 1
    
    print("Agent Priority Distribution:")
    for priority, count in priority_counts.items():
        if count > 0:
            bar = "█" * count
            print(f"  {priority:10} [{count:2}]: {bar}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("✅ SUMMARY")
    print("=" * 80)
    print(f"✓ {stats['total_agents_registered']} agents registered automatically")
    print(f"✓ {len(violation_types)} violation types supported")
    print(f"✓ Dynamic agent selection based on investigation type")
    print(f"✓ Dependency resolution and parallel execution ready")
    print("\n🚀 ForensicMetaOrchestrator is ready for advanced investigations!")
    print("=" * 80)


if __name__ == "__main__":
    main()
