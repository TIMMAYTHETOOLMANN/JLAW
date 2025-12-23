"""
JLAW AI Cross-Validation and SupremeOrchestrator Examples
=========================================================

This file demonstrates the usage of the new features:
1. AI Cross-Validation for Detection Patterns
2. SupremeOrchestrator Meta-Controller

Run with: python examples/ai_cross_validation_example.py
"""

import asyncio
from datetime import date
from pathlib import Path

# Example 1: Using SupremeOrchestrator for different priorities
async def example_supreme_orchestrator():
    """Demonstrate SupremeOrchestrator usage."""
    from src.core.supreme_orchestrator import SupremeOrchestrator
    
    print("=" * 80)
    print("EXAMPLE 1: SupremeOrchestrator - Unified Meta-Controller")
    print("=" * 80)
    
    supreme = SupremeOrchestrator()
    
    # Get all available strategies
    print("\n1. Available Execution Strategies:")
    strategies = supreme.get_available_strategies()
    for strategy in strategies:
        print(f"\n  Priority: {strategy['priority'].upper()}")
        print(f"  Orchestrator: {strategy['orchestrator_name']}")
        print(f"  Duration: {strategy['estimated_duration_minutes']} min")
        print(f"  Nodes: {strategy['node_count']}")
        print(f"  AI Validation: {strategy['enable_ai_validation']}")
        print(f"  Description: {strategy['description']}")
    
    # Select strategy for different scenarios
    print("\n2. Strategy Selection Examples:")
    
    # Scenario A: Quick triage for initial assessment
    triage = supreme.select_strategy("triage", filings=[])
    print(f"\n  TRIAGE: {triage.orchestrator_name}")
    print(f"  → Use when: Need quick 5-10 min initial assessment")
    print(f"  → Executes: {triage.node_count} critical nodes only")
    
    # Scenario B: Standard investigation
    standard = supreme.select_strategy("standard", filings=[])
    print(f"\n  STANDARD: {standard.orchestrator_name}")
    print(f"  → Use when: Full investigation required (15-30 min)")
    print(f"  → Executes: {standard.node_count} nodes with AI validation")
    
    # Scenario C: DOJ referral preparation
    doj = supreme.select_strategy("doj_referral", filings=[])
    print(f"\n  DOJ_REFERRAL: {doj.orchestrator_name}")
    print(f"  → Use when: Preparing DOJ-grade referral (30-60 min)")
    print(f"  → Executes: {doj.node_count} nodes with parallel agents")


async def example_ai_cross_validation():
    """Demonstrate AI cross-validation of detection patterns."""
    from src.detection.patterns.advanced_patterns import (
        cross_validate_pattern_with_ai,
        batch_cross_validate_patterns,
        PatternSeverity
    )
    from unittest.mock import MagicMock, AsyncMock
    
    print("\n" + "=" * 80)
    print("EXAMPLE 2: AI Cross-Validation of Detection Patterns")
    print("=" * 80)
    
    # Mock DualAgentCoordinator for demonstration
    mock_dual_agent = MagicMock()
    mock_dual_agent.analyze_text = AsyncMock(return_value={
        "status": "OK",
        "openai": {
            "status": "success",
            "violations": [
                {
                    "type": "accounting_manipulation",
                    "confidence": 0.87,
                    "description": "Beneish M-Score indicates earnings manipulation",
                    "recommendation": "Detailed forensic accounting review required"
                }
            ]
        },
        "anthropic": {
            "status": "success",
            "violations": [
                {
                    "type": "accounting_manipulation",
                    "confidence": 0.92,
                    "description": "M-Score significantly above threshold (-2.22)",
                    "recommendation": "Priority investigation recommended"
                }
            ]
        },
        "consensus": {
            "overlap": 1,
            "openai_only": 0,
            "anthropic_only": 0
        }
    })
    
    # Example 1: Single pattern validation
    print("\n1. Single Pattern Cross-Validation:")
    print("   Testing: Beneish M-Score = -2.8 (manipulation threshold: -2.22)")
    
    validation_result = await cross_validate_pattern_with_ai(
        pattern_name="Beneish M-Score",
        score=-2.8,
        evidence={
            "dsri": 1.465,  # Days Sales Receivable Index (high = red flag)
            "gmi": 1.193,   # Gross Margin Index
            "aqi": 1.254,   # Asset Quality Index
            "sgi": 1.607,   # Sales Growth Index
            "depi": 0.972,  # Depreciation Index
            "sgai": 1.001,  # SG&A Index
            "lvgi": 1.037,  # Leverage Index
            "tata": 0.031   # Total Accruals to Total Assets
        },
        dual_agent=mock_dual_agent,
        threshold=0.7
    )
    
    print(f"\n   Results:")
    print(f"   → AI Confidence: {validation_result['ai_confidence']:.1f}%")
    print(f"   → Validation Status: {validation_result['validation_status'].upper()}")
    print(f"   → Reasoning: {validation_result['reasoning']}")
    print(f"   → Supporting Factors: {len(validation_result['supporting_factors'])}")
    print(f"   → Recommendations: {len(validation_result['recommendations'])}")
    
    # Example 2: Batch validation
    print("\n2. Batch Pattern Cross-Validation:")
    print("   Testing: 3 patterns (1 CRITICAL, 2 HIGH severity)")
    
    pattern_results = [
        {
            "pattern_name": "Beneish M-Score",
            "severity": "CRITICAL",
            "score": -2.8,
            "confidence": 0.92,
            "evidence": {"dsri": 1.465, "gmi": 1.193}
        },
        {
            "pattern_name": "Altman Z-Score",
            "severity": "HIGH",
            "score": 1.2,  # Below 1.8 = distress zone
            "confidence": 0.85,
            "evidence": {"working_capital_ratio": 0.15}
        },
        {
            "pattern_name": "Days Sales Outstanding Spike",
            "severity": "HIGH",
            "score": 2.3,  # 2.3x increase
            "confidence": 0.88,
            "evidence": {"dso_current": 67, "dso_prior": 29}
        }
    ]
    
    batch_result = await batch_cross_validate_patterns(
        pattern_results=pattern_results,
        dual_agent=mock_dual_agent,
        severity_filter=["HIGH", "CRITICAL"]
    )
    
    print(f"\n   Results:")
    print(f"   → Total Patterns: {batch_result['total_patterns']}")
    print(f"   → Evaluated: {batch_result['patterns_evaluated']}")
    print(f"   → Validated: {batch_result['validated_count']}")
    print(f"   → Rejected: {batch_result['rejected_count']}")
    print(f"   → Uncertain: {batch_result['uncertain_count']}")
    print(f"   → Avg AI Confidence: {batch_result['average_ai_confidence']:.1f}%")
    print(f"   → High Confidence (>85%): {batch_result['high_confidence_count']}")


async def example_integrated_workflow():
    """Demonstrate integrated workflow with both features."""
    from src.core.supreme_orchestrator import SupremeOrchestrator
    
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Integrated Workflow")
    print("=" * 80)
    
    print("\nScenario: NIKE Inc (CIK: 320187) - Standard Investigation")
    print("\n1. Initialize SupremeOrchestrator")
    supreme = SupremeOrchestrator()
    
    print("\n2. Select optimal strategy based on priority")
    strategy = supreme.select_strategy("standard", filings=[])
    print(f"   → Selected: {strategy.orchestrator_name}")
    print(f"   → AI Cross-Validation: {'ENABLED' if strategy.enable_ai_validation else 'DISABLED'}")
    
    print("\n3. Execution Flow (if run):")
    print("   Phase 1: Configuration & Target Acquisition")
    print("   Phase 2: SEC EDGAR Data Collection")
    print("   Phase 3: Document Parsing & Indexing")
    print("   Phase 4: 15-Node Recursive Analysis")
    print("   Phase 5: Advanced Detection Patterns (23 algorithms)")
    print("   ↓")
    print("   Phase 5.1: AI Cross-Validation (NEW!)")
    print("   → Validates HIGH/CRITICAL patterns with dual agents")
    print("   → Returns ai_confidence, validation_status, reasoning")
    print("   ↓")
    print("   Phase 6: Dual-Agent AI Cross-Validation")
    print("   Phase 7: Subagent Orchestration")
    print("   Phase 8: Evidence Chain Finalization")
    print("   Phase 9: DOJ-Grade Dossier Generation")
    
    print("\n4. Expected Output:")
    print("   → Quantitative fraud scores VALIDATED by AI reasoning")
    print("   → High-confidence findings (>85% AI confidence) highlighted")
    print("   → Rejected patterns (low AI confidence) filtered")
    print("   → Action recommendations from dual agents")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("JLAW - AI Cross-Validation & SupremeOrchestrator Examples")
    print("=" * 80)
    
    # Run examples
    await example_supreme_orchestrator()
    await example_ai_cross_validation()
    await example_integrated_workflow()
    
    print("\n" + "=" * 80)
    print("Examples Complete!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("1. SupremeOrchestrator provides unified entry point for all execution modes")
    print("2. AI cross-validation adds human-like reasoning to quantitative scores")
    print("3. Dual agents (OpenAI + Anthropic) validate HIGH/CRITICAL patterns")
    print("4. Integration is seamless with existing Phase 5 detection")
    print("\nFor actual execution:")
    print("  supreme = SupremeOrchestrator()")
    print("  result = await supreme.auto_execute(..., priority='standard')")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
