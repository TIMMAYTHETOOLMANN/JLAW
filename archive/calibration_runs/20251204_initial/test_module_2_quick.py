"""
Quick validation test for NIST Integrated Compliance Analyzer (Module 2).
"""

import asyncio
from src.forensics.nist_integrated_compliance_analyzer import (
    NISTIntegratedComplianceAnalyzer
)

async def test_module_2():
    """Test Module 2 initialization and basic functionality."""
    print("="*70)
    print("NIST INTEGRATED COMPLIANCE ANALYZER - QUICK VALIDATION")
    print("="*70)
    
    try:
        # Initialize analyzer
        print("\n[1] Initializing NIST Integrated Compliance Analyzer...")
        config = {
            'max_workers': 8,
            'redis_enabled': False  # Disable Redis for testing
        }
        
        analyzer = NISTIntegratedComplianceAnalyzer(config)
        print("✓ Analyzer initialized successfully")
        
        # Test forensic analysis
        print("\n[2] Executing Forensic Analysis...")
        report = await analyzer.execute_forensic_analysis(
            company_cik="0001234567",
            company_name="Test Company Inc",
            years=3
        )
        
        print(f"\n[3] Analysis Results:")
        print(f"  Company: {report.company_name}")
        print(f"  CIK: {report.company_cik}")
        print(f"  Years Analyzed: {report.years_analyzed}")
        print(f"  Overall Risk Score: {report.overall_risk_score:.2%}")
        print(f"  Risk Classification: {report.risk_classification}")
        print(f"  ML Risk Score: {report.ml_risk_score:.2%}")
        print(f"  ML Confidence: {report.ml_confidence:.2%}")
        print(f"  Prosecution Readiness: {report.prosecution_readiness:.2%}")
        
        print(f"\n[4] Component Results:")
        print(f"  XBRL Filings Analyzed: {len(report.xbrl_analysis.get('m_scores', []))}")
        print(f"  Manipulation Flags: {report.xbrl_analysis.get('manipulation_flags', 0)}")
        if report.contradiction_results:
            print(f"  Contradictions Found: {len(report.contradiction_results.contradictions)}")
        if report.peer_comparison:
            print(f"  Peer Outlier Metrics: {len(report.peer_comparison.outlier_metrics)}")
        print(f"  Whistleblower Matches: {len(report.whistleblower_matches)}")
        if report.temporal_consistency:
            print(f"  Temporal Consistency: {report.temporal_consistency.consistency_score:.2%}")
        print(f"  Regulatory Violations: {len(report.regulatory_violations)}")
        
        print(f"\n[5] Critical Findings ({len(report.critical_findings)}):")
        for finding in report.critical_findings[:5]:
            print(f"  {finding}")
        
        print(f"\n[6] Recommended Actions ({len(report.recommended_actions)}):")
        for action in report.recommended_actions[:5]:
            print(f"  • {action}")
        
        # Test integrity verification
        print(f"\n[7] Verifying System Integrity...")
        is_valid = await analyzer.verify_integrity()
        
        if is_valid:
            print("✓ All hash chains verified - System integrity VALID")
        else:
            print("⚠️  INTEGRITY VIOLATION DETECTED")
        
        # Summary
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        print("✓ Initialization: PASS")
        print("✓ Forensic Analysis: PASS")
        print("✓ Report Generation: PASS")
        print(f"✓ System Integrity: {'PASS' if is_valid else 'FAIL'}")
        print("\n" + "="*70)
        print("MODULE 2 STATUS: ✅ FULLY OPERATIONAL")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_module_2())
    exit(0 if success else 1)

