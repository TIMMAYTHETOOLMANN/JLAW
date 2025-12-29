#!/usr/bin/env python3
"""
JLAW Health Check Script
========================

Validates system readiness for forensic analysis operations.
Tests critical imports and verifies core components are available.

Exit Codes:
    0: Health check passed - system ready
    1: Health check failed - system not ready

Usage:
    python scripts/health_check.py
    docker run <image> python scripts/health_check.py
"""
import sys
import os
from pathlib import Path


def main() -> int:
    """
    Execute JLAW health check validating all critical components.
    
    Returns:
        int: 0 for success, 1 for failure
    """
    try:
        # Add app to path (support both Docker and local execution)
        app_path = Path(__file__).parent.parent.absolute()
        if str(app_path) not in sys.path:
            sys.path.insert(0, str(app_path))
        
        print("=" * 60)
        print("JLAW FORENSIC SYSTEM HEALTH CHECK")
        print("=" * 60)
        
        # Test 1: Core Engine Components
        print("\n[1/5] Testing Core Engine Components...")
        from src.core.recursive_engine import RecursiveProsecutorialEngine
        print("  ✓ RecursiveProsecutorialEngine")
        
        from src.core.evidence_chain.hash_service import HashService
        print("  ✓ HashService (Triple-hash integrity)")
        
        from src.core.evidence_chain.merkle_tree import MerkleTree
        print("  ✓ MerkleTree (RFC 6962 compliant)")
        
        # Test 2: Critical Node Imports (Phase 1: Nodes 1-6)
        print("\n[2/5] Testing Phase 1 Nodes (Core SEC Filing Analysis)...")
        from src.nodes import (
            Form4Parser,
            DEF14ACompensationAnalyzer,
            TemporalConsistencyValidator,
            SOXCertificationAnalyzer,
            IRC83TaxCalculator,
            EnforcementRouter
        )
        print("  ✓ Node 1: Form4Parser (Insider Trading)")
        print("  ✓ Node 2: DEF14ACompensationAnalyzer (Executive Compensation)")
        print("  ✓ Node 3: TemporalConsistencyValidator (10-Q Consistency)")
        print("  ✓ Node 4: SOXCertificationAnalyzer (10-K SOX)")
        print("  ✓ Node 5: IRC83TaxCalculator (Tax Exposure)")
        print("  ✓ Node 6: EnforcementRouter (Routing)")
        
        # Test 3: Phase 2 Nodes (Extended Intelligence)
        print("\n[3/5] Testing Phase 2 Nodes (Extended Intelligence)...")
        from src.nodes import (
            InstitutionalHoldingsAnalyzer,
            BeneficialOwnershipTracker,
            MaterialEventCorrelator
        )
        print("  ✓ Node 7: InstitutionalHoldingsAnalyzer (13F-HR)")
        print("  ✓ Node 8: BeneficialOwnershipTracker (13D/13G)")
        print("  ✓ Node 9: MaterialEventCorrelator (8-K Events)")
        
        # Test 4: Phase 3 & 4 Nodes (Financial Health & Market)
        print("\n[4/5] Testing Phase 3/4 Nodes (Quantitative Scoring)...")
        from src.nodes import (
            BankruptcyPredictorV2,
            FinancialStrengthAnalyzerV2,
            MarketCorrelationEngineV2
        )
        print("  ✓ Node 13: BankruptcyPredictorV2 (Z-Score)")
        print("  ✓ Node 14: FinancialStrengthAnalyzerV2 (F-Score)")
        print("  ✓ Node 15: MarketCorrelationEngineV2 (Market Correlation)")
        
        # Test 5: Detection & Analysis Components
        print("\n[5/5] Testing Detection & Analysis Components...")
        from src.detection.patterns.advanced_patterns import AdvancedPatternDetector
        print("  ✓ AdvancedPatternDetector (23 fraud patterns)")
        
        from src.detection.financial.beneish_mscore import BeneishMScoreCalculator
        print("  ✓ BeneishMScoreCalculator (Earnings manipulation)")
        
        from src.nodes import NodeCorrelator
        print("  ✓ NodeCorrelator (Cross-node correlation)")
        
        # Success
        print("\n" + "=" * 60)
        print("✓ JLAW HEALTH CHECK PASSED")
        print("  System is ready for forensic analysis operations")
        print("=" * 60)
        return 0
        
    except ImportError as e:
        print(f"\n✗ JLAW Health Check FAILED: Import Error", file=sys.stderr)
        print(f"  Missing module: {e}", file=sys.stderr)
        print("\n  This may indicate:")
        print("    - Missing dependencies (run: pip install -r requirements.txt)")
        print("    - Incorrect PYTHONPATH")
        print("    - Incomplete installation")
        print("=" * 60, file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"\n✗ JLAW Health Check FAILED: {type(e).__name__}", file=sys.stderr)
        print(f"  Error: {e}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
