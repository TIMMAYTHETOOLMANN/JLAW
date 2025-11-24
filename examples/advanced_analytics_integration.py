"""
Advanced Forensic Analytics Integration Example
Demonstrates integration of Module 1 with existing JLAW system.
"""

import asyncio
import os
from datetime import datetime
import json

from src.forensics import (
    # Existing JLAW components
    ForensicOrchestrator,
    SECForensicAnalyzer,
    AdvancedFraudDetector,
    StorageConfig,
    
    # New Advanced Analytics Module
    AdvancedForensicAnalyzer,
    SemanticContradictionGraph,
    EnhancedFinancialForensics
)


async def demonstrate_advanced_analytics():
    """
    Complete demonstration of advanced forensic analytics integration.
    Shows how to combine traditional JLAW analysis with new capabilities.
    """
    
    print("="*80)
    print("JLAW Advanced Forensic Analytics - Integration Demo")
    print("="*80)
    
    # ========================================================================
    # SETUP: Initialize all analyzers
    # ========================================================================
    
    print("\n[1] Initializing JLAW Forensic System...")
    
    # Traditional JLAW components
    storage_config = StorageConfig(
        provider="LOCAL",
        retention_days=2555,
        compliance_mode=True
    )
    
    orchestrator = ForensicOrchestrator(
        govinfo_api_key=os.getenv("GOVINFO_API_KEY", "DEMO_KEY"),
        storage_config=storage_config
    )
    
    ml_detector = AdvancedFraudDetector()
    
    # NEW: Advanced analytics module
    advanced_analyzer = AdvancedForensicAnalyzer()
    
    print("✓ All components initialized")
    
    # ========================================================================
    # SCENARIO 1: Full Investigation with Advanced Analytics
    # ========================================================================
    
    print("\n[2] Starting Full Investigation with Advanced Analytics...")
    
    cik = "0001318605"  # Tesla Inc
    company_name = "Tesla Inc"
    
    # Initiate investigation
    case_id = await orchestrator.initiate_investigation(
        cik=cik,
        company_name=company_name,
        investigator="DEMO_SYSTEM",
        case_notes="Demonstration of advanced analytics integration"
    )
    
    print(f"✓ Investigation initiated: {case_id}")
    
    # Sample filing for demonstration
    sample_filing = {
        "cik": cik,
        "accession": "0001564590-24-000123",
        "filing_type": "10-K",
        "full_text": """
        Management's Discussion and Analysis:
        
        Revenue Performance:
        The company achieved record revenue growth of 45% in fiscal year 2024, 
        driven by strong demand across all segments. This represents our strongest 
        performance to date.
        
        However, the company experienced significant revenue challenges in 2024,
        with sales declining 12% year-over-year due to market conditions.
        
        Financial Position:
        Our cash position strengthened considerably with $5.2 billion in cash and
        equivalents at year end. The company faced severe liquidity constraints
        throughout the year.
        
        Margins and Profitability:
        Gross margins expanded to 28%, reflecting operational improvements and
        cost efficiencies. Gross margins contracted to 18% due to increased
        production costs and pricing pressures.
        
        Future Outlook:
        Management expects continued growth momentum in 2025 with projected
        revenue increases of 30-40%. We anticipate further revenue declines
        in the coming year.
        """
    }
    
    # Sample financial data (would normally be extracted from XBRL)
    current_financials = {
        'receivables': 800000000,      # High receivables growth
        'sales': 2500000000,
        'cogs': 1700000000,            # Deteriorating margins
        'current_assets': 900000000,
        'ppe': 1200000000,
        'total_assets': 3500000000,
        'depreciation': 80000000,       # Low depreciation
        'sga': 550000000,
        'debt': 1800000000,            # High leverage
        'income_continuing': 400000000,
        'cash_flow': 250000000         # High accruals
    }
    
    prior_financials = {
        'receivables': 450000000,
        'sales': 2000000000,
        'cogs': 1200000000,
        'current_assets': 850000000,
        'ppe': 1150000000,
        'total_assets': 3300000000,
        'depreciation': 110000000,
        'sga': 450000000,
        'debt': 1200000000,
        'income_continuing': 350000000,
        'cash_flow': 340000000
    }
    
    # ========================================================================
    # TRADITIONAL JLAW ANALYSIS
    # ========================================================================
    
    print("\n[3] Running Traditional JLAW Analysis...")
    
    # Traditional SEC analysis
    # (In production, this would fetch and parse real filings)
    traditional_risk = 0.72  # Simulated
    
    # ML fraud detection
    ml_prediction = await ml_detector.detect_fraud({
        "cik": cik,
        "filing_type": "10-K",
        "financials": current_financials,
        "mda": sample_filing["full_text"],
        "delay_days": 0
    })
    
    print(f"✓ Traditional Risk Score: {traditional_risk:.2%}")
    print(f"✓ ML Fraud Probability: {ml_prediction.probability:.2%}")
    
    # ========================================================================
    # ADVANCED ANALYTICS
    # ========================================================================
    
    print("\n[4] Running Advanced Forensic Analytics...")
    
    advanced_result = await advanced_analyzer.analyze_filing(
        filing_text=sample_filing["full_text"],
        current_financials=current_financials,
        prior_financials=prior_financials,
        cik=cik,
        filing_type="10-K"
    )
    
    print(f"✓ Advanced Analytics Risk Score: {advanced_result.overall_risk_score:.2%}")
    print(f"✓ Contradictions Detected: {len(advanced_result.contradictions)}")
    
    # Display Beneish M-Score
    if advanced_result.beneish_analysis:
        m_score = advanced_result.beneish_analysis
        print(f"\n  Beneish M-Score Analysis:")
        print(f"  • M-Score: {m_score.score:.3f}")
        print(f"  • Manipulation Probability: {m_score.probability:.2%}")
        print(f"  • Risk Level: {m_score.risk_level}")
        print(f"  • Manipulation Flag: {'YES' if m_score.manipulation_flag else 'NO'}")
        
        print(f"\n  Key Components:")
        for component, value in list(m_score.components.items())[:4]:
            print(f"  • {component}: {value:.3f}")
    
    # Display contradictions
    if advanced_result.contradictions:
        print(f"\n  Semantic Contradictions:")
        for i, contradiction in enumerate(advanced_result.contradictions[:3], 1):
            print(f"\n  Contradiction #{i} [{contradiction.severity}]:")
            print(f"  • Similarity: {contradiction.similarity_score:.2%}")
            print(f"  • Type: {contradiction.contradiction_type}")
            print(f"  • Explanation: {contradiction.explanation}")
    
    # Display critical findings
    if advanced_result.critical_findings:
        print(f"\n  Critical Findings:")
        for finding in advanced_result.critical_findings:
            print(f"  {finding}")
    
    # ========================================================================
    # ENSEMBLE RISK ASSESSMENT
    # ========================================================================
    
    print("\n[5] Generating Ensemble Risk Assessment...")
    
    # Combine all risk scores with weighted average
    ensemble_risk = (
        traditional_risk * 0.30 +         # Traditional forensic analysis
        ml_prediction.probability * 0.30 +  # ML fraud detection
        advanced_result.overall_risk_score * 0.40  # Advanced analytics
    )
    
    print(f"\n  Risk Score Breakdown:")
    print(f"  • Traditional Forensics: {traditional_risk:.2%} (weight: 30%)")
    print(f"  • ML Fraud Detection:    {ml_prediction.probability:.2%} (weight: 30%)")
    print(f"  • Advanced Analytics:    {advanced_result.overall_risk_score:.2%} (weight: 40%)")
    print(f"  • ENSEMBLE RISK SCORE:   {ensemble_risk:.2%}")
    
    # Risk classification
    if ensemble_risk >= 0.85:
        risk_class = "CRITICAL"
    elif ensemble_risk >= 0.70:
        risk_class = "HIGH"
    elif ensemble_risk >= 0.50:
        risk_class = "MEDIUM"
    else:
        risk_class = "LOW"
    
    print(f"\n  Risk Classification: {risk_class}")
    
    # ========================================================================
    # STORE RESULTS
    # ========================================================================
    
    print("\n[6] Storing Evidence and Results...")
    
    # Store advanced analytics results
    await orchestrator.storage.store_evidence(
        case_id=case_id,
        evidence_type="ADVANCED_ANALYTICS",
        data={
            "timestamp": datetime.now().isoformat(),
            "cik": cik,
            "filing_type": "10-K",
            "traditional_risk": traditional_risk,
            "ml_fraud_probability": ml_prediction.probability,
            "advanced_risk": advanced_result.overall_risk_score,
            "ensemble_risk": ensemble_risk,
            "risk_classification": risk_class,
            "contradictions_count": len(advanced_result.contradictions),
            "beneish_m_score": advanced_result.beneish_analysis.score if advanced_result.beneish_analysis else None,
            "manipulation_flag": advanced_result.beneish_analysis.manipulation_flag if advanced_result.beneish_analysis else None,
            "critical_findings": advanced_result.critical_findings
        }
    )
    
    print("✓ Evidence stored in immutable storage")
    
    # ========================================================================
    # VERIFY INTEGRITY
    # ========================================================================
    
    print("\n[7] Verifying System Integrity...")
    
    # Verify all hash chains
    chains_valid = await advanced_analyzer.verify_integrity()
    orchestrator_valid = await orchestrator.master_chain.verify_chain()
    
    if chains_valid and orchestrator_valid:
        print("✓ All hash chains verified - System integrity VALID")
    else:
        print("⚠️  INTEGRITY VIOLATION DETECTED")
    
    # ========================================================================
    # SCENARIO 2: Standalone Contradiction Detection
    # ========================================================================
    
    print("\n[8] Demonstrating Standalone Contradiction Detection...")
    
    contradiction_detector = SemanticContradictionGraph()
    
    await contradiction_detector.build_filing_graph(
        sample_filing["full_text"],
        section_name="MD&A"
    )
    
    contradictions = await contradiction_detector.detect_contradictions(threshold=0.80)
    
    print(f"✓ Found {len(contradictions)} contradictions")
    
    graph_metrics = contradiction_detector.get_graph_metrics()
    print(f"✓ Knowledge Graph: {graph_metrics['node_count']} nodes, "
          f"density: {graph_metrics['density']:.3f}")
    
    # ========================================================================
    # SCENARIO 3: Standalone Beneish M-Score
    # ========================================================================
    
    print("\n[9] Demonstrating Standalone Beneish M-Score...")
    
    financial_forensics = EnhancedFinancialForensics()
    
    m_score_result = await financial_forensics.calculate_beneish_mscore(
        current_financials,
        prior_financials
    )
    
    print(f"✓ M-Score: {m_score_result.score:.3f}")
    print(f"✓ Risk Level: {m_score_result.risk_level}")
    print(f"\nInterpretation:\n{m_score_result.interpretation}")
    
    # ========================================================================
    # FINAL REPORT
    # ========================================================================
    
    print("\n" + "="*80)
    print("INVESTIGATION SUMMARY")
    print("="*80)
    
    summary = {
        "case_id": case_id,
        "company": company_name,
        "cik": cik,
        "timestamp": datetime.now().isoformat(),
        "analysis": {
            "traditional_risk": f"{traditional_risk:.2%}",
            "ml_fraud_probability": f"{ml_prediction.probability:.2%}",
            "advanced_analytics_risk": f"{advanced_result.overall_risk_score:.2%}",
            "ensemble_risk": f"{ensemble_risk:.2%}",
            "risk_classification": risk_class
        },
        "findings": {
            "contradictions": len(advanced_result.contradictions),
            "critical_contradictions": sum(
                1 for c in advanced_result.contradictions if c.severity == "CRITICAL"
            ),
            "beneish_m_score": m_score_result.score,
            "manipulation_flag": m_score_result.manipulation_flag,
            "critical_findings": len(advanced_result.critical_findings)
        },
        "integrity": {
            "advanced_analytics_chain": "VALID" if chains_valid else "INVALID",
            "orchestrator_chain": "VALID" if orchestrator_valid else "INVALID"
        }
    }
    
    print(json.dumps(summary, indent=2))
    
    print("\n" + "="*80)
    print("✓ Advanced Forensic Analytics Integration - COMPLETE")
    print("="*80)
    
    return summary


async def demonstrate_module_features():
    """Demonstrate individual module features."""
    
    print("\n" + "="*80)
    print("MODULE FEATURE DEMONSTRATIONS")
    print("="*80)
    
    # ========================================================================
    # FEATURE 1: Negation Detection
    # ========================================================================
    
    print("\n[Feature 1] Negation Pattern Detection")
    
    detector = SemanticContradictionGraph()
    
    negation_text = """
    The company has strong liquidity and cash reserves.
    The company does not have sufficient cash to meet obligations.
    Revenue growth accelerated in the quarter.
    Revenue growth did not occur as expected.
    """
    
    await detector.build_filing_graph(negation_text)
    contradictions = await detector.detect_contradictions(threshold=0.75)
    
    print(f"Detected {len(contradictions)} negation-based contradictions")
    
    # ========================================================================
    # FEATURE 2: Numerical Contradiction Detection
    # ========================================================================
    
    print("\n[Feature 2] Numerical Contradiction Detection")
    
    numerical_text = """
    Sales increased by 30% year-over-year.
    The company experienced sales declines of 20%.
    Profit margins improved substantially.
    Margins deteriorated significantly during the period.
    """
    
    detector2 = SemanticContradictionGraph()
    await detector2.build_filing_graph(numerical_text)
    num_contradictions = await detector2.detect_contradictions(threshold=0.70)
    
    print(f"Detected {len(num_contradictions)} numerical contradictions")
    
    # ========================================================================
    # FEATURE 3: Temporal Contradiction Detection
    # ========================================================================
    
    print("\n[Feature 3] Temporal Contradiction Detection")
    
    temporal_text = """
    The acquisition was completed before the end of Q3.
    The transaction occurred after Q3 ended.
    Revenue recognition policies were changed in the prior year.
    Policy changes were implemented in the current period.
    """
    
    detector3 = SemanticContradictionGraph()
    await detector3.build_filing_graph(temporal_text)
    temp_contradictions = await detector3.detect_contradictions(threshold=0.70)
    
    print(f"Detected {len(temp_contradictions)} temporal contradictions")
    
    # ========================================================================
    # FEATURE 4: M-Score Component Analysis
    # ========================================================================
    
    print("\n[Feature 4] M-Score Component Analysis")
    
    forensics = EnhancedFinancialForensics()
    
    # Test different manipulation patterns
    patterns = {
        "Channel Stuffing": {
            "current": {
                'receivables': 900000000,  # Very high receivables
                'sales': 2000000000,
                'cogs': 1200000000, 'current_assets': 800000000,
                'ppe': 1000000000, 'total_assets': 3000000000,
                'depreciation': 100000000, 'sga': 400000000,
                'debt': 1000000000, 'income_continuing': 300000000,
                'cash_flow': 280000000
            },
            "prior": {
                'receivables': 400000000,
                'sales': 1900000000,
                'cogs': 1140000000, 'current_assets': 780000000,
                'ppe': 980000000, 'total_assets': 2950000000,
                'depreciation': 98000000, 'sga': 390000000,
                'debt': 980000000, 'income_continuing': 290000000,
                'cash_flow': 285000000
            }
        }
    }
    
    for pattern_name, data in patterns.items():
        result = await forensics.calculate_beneish_mscore(
            data["current"],
            data["prior"]
        )
        print(f"\n  {pattern_name}:")
        print(f"  • M-Score: {result.score:.3f}")
        print(f"  • DSRI (Receivables Index): {result.components['DSRI']:.3f}")
        print(f"  • Risk: {result.risk_level}")
    
    print("\n" + "="*80)
    print("✓ Feature Demonstrations - COMPLETE")
    print("="*80)


async def main():
    """Run all demonstrations."""
    
    print("\n" + "="*80)
    print("JLAW ADVANCED FORENSIC ANALYTICS - MODULE 1")
    print("Complete Integration and Feature Demonstration")
    print("="*80)
    
    # Run main integration demo
    await demonstrate_advanced_analytics()
    
    # Run feature demos
    await demonstrate_module_features()
    
    print("\n✓ All demonstrations complete!")
    print("\nFor production use:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Download spaCy model: python -m spacy download en_core_web_sm")
    print("  3. Import: from src.forensics import AdvancedForensicAnalyzer")
    print("  4. See ADVANCED_FORENSIC_ANALYTICS_README.md for full documentation")


if __name__ == "__main__":
    asyncio.run(main())

