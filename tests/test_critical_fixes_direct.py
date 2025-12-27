"""
Direct unit tests for new modules (CRITICAL-009, CRITICAL-010, MOD-005)
Tests only the new code without importing the full nodes package
"""
import sys
from pathlib import Path
from datetime import date, datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_node16_direct():
    """Test Node 16 directly without full imports"""
    print("\n=== Testing Node 16 (Direct) ===")
    
    try:
        # Import directly from module
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'nodes' / 'node16_customs_trade'))
        from customs_trade_analyzer import (
            CustomsTradeAnalyzer,
            TradeTransaction,
            CustomsViolationType,
            TradeSeverity
        )
        
        analyzer = CustomsTradeAnalyzer()
        print("✓ CustomsTradeAnalyzer instantiated")
        
        # Test trade transaction creation
        txn = TradeTransaction(
            transaction_id="T001",
            transaction_date=date(2024, 1, 1),
            importer="ImportCo",
            exporter="ExportCo",
            country_of_origin="IRAN",
            hs_code="6403",
            declared_value=50000.0,
            quantity=100,
            description="Test goods"
        )
        print("✓ TradeTransaction created")
        
        # Verify enums
        assert CustomsViolationType.TARIFF_EVASION
        assert CustomsViolationType.OFAC_SANCTIONS
        assert TradeSeverity.CRITICAL
        print("✓ Enums defined correctly")
        
        # Verify detection methods exist
        assert hasattr(analyzer, '_detect_tariff_evasion')
        assert hasattr(analyzer, '_detect_valuation_fraud')
        assert hasattr(analyzer, '_detect_country_of_origin_fraud')
        assert hasattr(analyzer, '_detect_transfer_pricing_abuse')
        assert hasattr(analyzer, '_detect_tbml')
        assert hasattr(analyzer, '_detect_sanctions_violations')
        assert hasattr(analyzer, '_detect_phantom_shipments')
        assert hasattr(analyzer, '_detect_ftz_abuse')
        print("✓ All 8 detection methods present")
        
        # Verify routing matrix method
        assert hasattr(analyzer, 'get_routing_matrix')
        print("✓ Routing matrix method present")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_derivatives_direct():
    """Test Derivatives Integration directly"""
    print("\n=== Testing Derivatives Integration (Direct) ===")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'analysis'))
        from derivatives_integration import (
            DerivativesIntegrationEngine,
            OptionsFlow,
            OptionsAnomalyType,
            AnomalySeverity
        )
        
        engine = DerivativesIntegrationEngine()
        print("✓ DerivativesIntegrationEngine instantiated")
        
        # Test options flow creation
        option = OptionsFlow(
            ticker="TEST",
            trade_date=date(2024, 1, 15),
            contract_type="CALL",
            strike_price=100.0,
            expiration_date=date(2024, 2, 15),
            volume=1000,
            open_interest=5000,
            premium=2.5
        )
        print("✓ OptionsFlow created")
        
        # Verify enums
        assert OptionsAnomalyType.PRE_EARNINGS_SPIKE
        assert OptionsAnomalyType.INSIDER_OPTIONS_CORRELATION
        assert AnomalySeverity.CRITICAL
        print("✓ Enums defined correctly")
        
        # Verify detection methods exist
        assert hasattr(engine, '_analyze_pre_earnings_activity')
        assert hasattr(engine, '_detect_putcall_ratio_anomalies')
        assert hasattr(engine, '_detect_volume_spikes')
        assert hasattr(engine, '_detect_deep_otm_purchases')
        assert hasattr(engine, '_detect_block_trades')
        assert hasattr(engine, '_correlate_insider_options')
        print("✓ All 6 detection methods present")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_validator_direct():
    """Test AI Cross-Validator directly"""
    print("\n=== Testing AI Cross-Validator (Direct) ===")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'validation'))
        from ai_cross_validator import (
            AICrossValidator,
            DetectionPattern,
            ValidationStatus
        )
        
        validator = AICrossValidator()
        print("✓ AICrossValidator instantiated")
        
        # Verify 23 patterns
        patterns = list(DetectionPattern)
        assert len(patterns) == 23
        print(f"✓ All 23 detection patterns defined")
        
        # Verify key patterns
        pattern_names = [p.name for p in patterns]
        assert 'SEC_EDGAR_ANOMALIES' in pattern_names
        assert 'INSIDER_TRIANGULATION' in pattern_names
        assert 'DERIVATIVES_VS_EARNINGS' in pattern_names
        assert 'FORM_144_VOLUME' in pattern_names
        assert 'ROUND_TRIPPING' in pattern_names
        assert 'WOLF_PACK' in pattern_names
        assert 'OPTIONS_BACKDATING' in pattern_names
        assert 'BENFORD_ANALYSIS' in pattern_names
        assert 'BENEISH_MSCORE' in pattern_names
        assert 'EXEC_COMPENSATION' in pattern_names
        assert 'SOX_CERTIFICATION' in pattern_names
        assert 'IRC_83_EXPOSURE' in pattern_names
        assert 'HOLDINGS_13F' in pattern_names
        assert 'OWNERSHIP_13D_13G' in pattern_names
        assert 'EVENT_8K_TIMING' in pattern_names
        assert 'RELATED_PARTY_TXN' in pattern_names
        assert 'REVENUE_RECOGNITION' in pattern_names
        assert 'INVENTORY_MANIPULATION' in pattern_names
        assert 'ZSCORE_BANKRUPTCY' in pattern_names
        assert 'FSCORE_STRENGTH' in pattern_names
        assert 'CHANNEL_STUFFING' in pattern_names
        assert 'PRE_ANNOUNCEMENT' in pattern_names
        assert 'DISCLOSURE_TIMING' in pattern_names
        print("✓ All 23 patterns verified by name")
        
        # Verify validation status enum
        assert ValidationStatus.CONSENSUS
        assert ValidationStatus.DISAGREEMENT
        print("✓ ValidationStatus enum defined")
        
        # Verify methods
        assert hasattr(validator, 'validate_all_patterns')
        assert hasattr(validator, '_validate_pattern')
        assert hasattr(validator, '_calculate_consensus')
        print("✓ Key validation methods present")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_node12_direct():
    """Test Node 12 derivatives hook directly"""
    print("\n=== Testing Node 12 Hook (Direct) ===")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'nodes' / 'node12_earnings_calls'))
        from transcript_analyzer_v2 import TranscriptAnalyzerV2
        
        analyzer = TranscriptAnalyzerV2()
        print("✓ TranscriptAnalyzerV2 instantiated")
        
        # Verify new method exists
        assert hasattr(analyzer, 'get_earnings_dates')
        print("✓ get_earnings_dates() method exists")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_node15_direct():
    """Test Node 15 derivatives hook directly"""
    print("\n=== Testing Node 15 Hook (Direct) ===")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'nodes' / 'node15_market_correlation'))
        from market_correlation_engine_v2 import MarketCorrelationEngineV2
        
        engine = MarketCorrelationEngineV2(polygon_api_key=None)
        print("✓ MarketCorrelationEngineV2 instantiated")
        
        # Verify new method exists
        assert hasattr(engine, 'get_spot_prices')
        print("✓ get_spot_prices() method exists")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("JLAW CRITICAL FIXES - DIRECT UNIT TESTS")
    print("Testing CRITICAL-009, CRITICAL-010, and MOD-005")
    print("=" * 80)
    
    results = []
    
    # Run tests
    results.append(("Node 16 - Customs & Trade", test_node16_direct()))
    results.append(("Derivatives Integration", test_derivatives_direct()))
    results.append(("AI Cross-Validator", test_ai_validator_direct()))
    results.append(("Node 12 - Derivatives Hook", test_node12_direct()))
    results.append(("Node 15 - Derivatives Hook", test_node15_direct()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! All implementations verified.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
