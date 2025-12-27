#!/usr/bin/env python3
"""
Event Proximity Analysis Module Validation
===========================================

Validates that all Event Proximity modules are correctly implemented
and can be imported without errors.
"""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test Event Proximity modules
        from src.zero_dollar.modules import (
            EventProximityModule,
            EventProximityOutput,
            EventCategory,
            FORM_8K_EVENTS,
            EARNINGS_EVENTS,
            get_event_category,
            calculate_mnpi_score,
            get_event_citations,
            determine_mnpi_severity,
            detect_event_proximity,
        )
        print("✓ Event Proximity modules import successfully")
        
        # Test Event Calendar Acquisition
        from src.zero_dollar.acquisition import EventCalendarAcquisition
        print("✓ Event Calendar Acquisition imports successfully")
        
        # Test updated model
        from src.zero_dollar.models import EventProximityFlag
        print("✓ Updated EventProximityFlag model imports successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_material_event_taxonomy():
    """Test Material Event Taxonomy."""
    print("\nTesting Material Event Taxonomy...")
    
    try:
        from src.zero_dollar.modules import FORM_8K_EVENTS, EARNINGS_EVENTS, get_event_category
        
        # Test Form 8-K events count
        assert len(FORM_8K_EVENTS) == 16, "Should have 16 Form 8-K event types"
        print(f"  ✓ Form 8-K events: {len(FORM_8K_EVENTS)} types defined")
        
        # Test earnings events count
        assert len(EARNINGS_EVENTS) == 5, "Should have 5 earnings event types"
        print(f"  ✓ Earnings events: {len(EARNINGS_EVENTS)} types defined")
        
        # Test critical events
        critical_events = ['1.03', '2.02', '2.06', '3.01', '4.02', '5.01']
        for item in critical_events:
            category = FORM_8K_EVENTS[item]
            assert category.mnpi_sensitivity == 'CRITICAL', f"Item {item} should be CRITICAL"
        print(f"  ✓ CRITICAL sensitivity events: {len(critical_events)} verified")
        
        # Test high events
        high_events = ['1.01', '1.02', '2.01', '2.04', '2.05', '4.01']
        for item in high_events:
            category = FORM_8K_EVENTS[item]
            assert category.mnpi_sensitivity == 'HIGH', f"Item {item} should be HIGH"
        print(f"  ✓ HIGH sensitivity events: {len(high_events)} verified")
        
        # Test moderate events
        moderate_events = ['2.03', '5.02', '5.03']
        for item in moderate_events:
            category = FORM_8K_EVENTS[item]
            assert category.mnpi_sensitivity == 'MODERATE', f"Item {item} should be MODERATE"
        print(f"  ✓ MODERATE sensitivity events: {len(moderate_events)} verified")
        
        # Test get_event_category
        category = get_event_category('2.02')
        assert category.description == 'Results of Operations and Financial Condition'
        assert category.lookback_days == 14
        assert category.lookforward_days == 2
        print("  ✓ get_event_category() works correctly")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mnpi_scoring():
    """Test MNPI Scoring Algorithm."""
    print("\nTesting MNPI Scoring Algorithm...")
    
    try:
        from src.zero_dollar.models import MaterialEvent
        from src.zero_dollar.modules import (
            calculate_mnpi_score,
            get_event_citations,
            determine_mnpi_severity,
        )
        
        # Create test event
        event = MaterialEvent(
            event_id='TEST-001',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='2.02',
            event_date=date(2020, 1, 15),
            event_description='Earnings Release',
            is_price_sensitive=True,
        )
        
        # Test CRITICAL PRE event score
        score_critical = calculate_mnpi_score(event, 3, 'PRE', 'CRITICAL')
        assert score_critical >= Decimal('0.70'), "CRITICAL PRE should have high score"
        print(f"  ✓ CRITICAL PRE event score: {score_critical:.3f} (expected >= 0.70)")
        
        # Test HIGH PRE event score
        score_high = calculate_mnpi_score(event, 5, 'PRE', 'HIGH')
        assert Decimal('0.40') <= score_high <= Decimal('0.50'), "HIGH PRE should be moderate"
        print(f"  ✓ HIGH PRE event score: {score_high:.3f} (expected 0.40-0.50)")
        
        # Test POST event score (lower)
        score_post = calculate_mnpi_score(event, 1, 'POST', 'CRITICAL')
        assert score_post < Decimal('0.30'), "POST event should have lower score"
        print(f"  ✓ POST event score: {score_post:.3f} (expected < 0.30)")
        
        # Test exponential decay
        score_1day = calculate_mnpi_score(event, 1, 'PRE', 'CRITICAL')
        score_7days = calculate_mnpi_score(event, 7, 'PRE', 'CRITICAL')
        score_14days = calculate_mnpi_score(event, 14, 'PRE', 'CRITICAL')
        assert score_1day > score_7days > score_14days, "Score should decay with distance"
        print(f"  ✓ Exponential decay: {score_1day:.3f} > {score_7days:.3f} > {score_14days:.3f}")
        
        # Test severity classification
        assert determine_mnpi_severity(Decimal('0.75')) == 'CRITICAL'
        assert determine_mnpi_severity(Decimal('0.60')) == 'HIGH'
        assert determine_mnpi_severity(Decimal('0.40')) == 'MODERATE'
        assert determine_mnpi_severity(Decimal('0.20')) == 'LOW'
        print("  ✓ MNPI severity classification works correctly")
        
        # Test regulatory citations
        citations = get_event_citations(event, 'CRITICAL')
        assert '15 U.S.C. § 78j(b)' in citations
        assert '17 CFR § 240.10b-5' in citations
        assert '17 CFR § 240.10b5-1' in citations
        print(f"  ✓ Regulatory citations: {len(citations)} citations generated")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_proximity_module():
    """Test Event Proximity Module."""
    print("\nTesting Event Proximity Module...")
    
    try:
        from src.zero_dollar.models import Transaction, MaterialEvent
        from src.zero_dollar.modules import EventProximityModule, detect_event_proximity
        
        # Create test transaction
        txn = Transaction(
            accession_number='TEST-ACC-001',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            reporting_person_cik='0001111111',
            reporting_person_name='John Smith',
            transaction_date=date(2020, 1, 10),
            filing_date=date(2020, 1, 10),
            transaction_code='P',
            shares=Decimal('10000'),
            price_per_share=None,  # Zero-dollar
            transaction_acquired_disposed='A',
            shares_owned_following=Decimal('50000'),
            direct_indirect='D',
        )
        
        # Create test event
        event = MaterialEvent(
            event_id='TEST-EVT-001',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='8K-2.02',
            event_date=date(2020, 1, 15),
            event_description='Form 8-K Item 2.02',
            is_price_sensitive=True,
        )
        
        # Test module initialization
        module = EventProximityModule()
        assert module.event_buffer_days == 60
        assert module.mnpi_threshold == Decimal('0.3')
        print("  ✓ EventProximityModule initialized successfully")
        
        # Test detect_event_proximity
        flags = module.detect_event_proximity(txn, [event])
        assert len(flags) > 0, "Should detect proximity"
        print(f"  ✓ Detected {len(flags)} proximity flags")
        
        # Validate flag structure
        flag = flags[0]
        assert flag.flag_id is not None
        assert flag.transaction_id == 'TEST-ACC-001'
        assert flag.proximity_type == 'PRE_EVENT'
        assert flag.days_delta == 5
        assert flag.mnpi_inference_score > Decimal('0')
        assert len(flag.regulatory_citations) > 0
        assert flag.narrative is not None
        assert len(flag.evidence_hash) == 64  # SHA-256 hash
        print("  ✓ Flag structure validated")
        print(f"    - Proximity type: {flag.proximity_type}")
        print(f"    - Days delta: {flag.days_delta}")
        print(f"    - MNPI score: {flag.mnpi_inference_score:.3f}")
        print(f"    - Citations: {len(flag.regulatory_citations)}")
        
        # Test convenience function
        flags2 = detect_event_proximity([txn], [event])
        assert len(flags2) > 0
        print("  ✓ Convenience function works correctly")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_calendar_acquisition():
    """Test Event Calendar Acquisition structure."""
    print("\nTesting Event Calendar Acquisition...")
    
    try:
        from src.zero_dollar.acquisition import EventCalendarAcquisition
        
        # Test initialization
        config = {'user_agent': 'Test/1.0 test@example.com'}
        client = EventCalendarAcquisition(config)
        assert client.user_agent == 'Test/1.0 test@example.com'
        print("  ✓ EventCalendarAcquisition initialized successfully")
        
        # Test parse_8k_items
        sample_content = """
        <root>
            Item 2.02 Results of Operations
            Item 9.01 Financial Statements
        </root>
        """
        items = client._extract_items_from_text(sample_content)
        assert '2.02' in items or '9.01' in items
        print(f"  ✓ 8-K item parsing works: extracted {len(items)} items")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_validation():
    """Run all validation tests."""
    print("\n" + "=" * 70)
    print("EVENT PROXIMITY ANALYSIS MODULE VALIDATION")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Material Event Taxonomy", test_material_event_taxonomy),
        ("MNPI Scoring", test_mnpi_scoring),
        ("Event Proximity Module", test_event_proximity_module),
        ("Event Calendar Acquisition", test_event_calendar_acquisition),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


if __name__ == '__main__':
    success = run_validation()
    sys.exit(0 if success else 1)
