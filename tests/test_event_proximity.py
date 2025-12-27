#!/usr/bin/env python3
"""
Event Proximity Analysis Module Tests
======================================

Test suite for Event Proximity Analysis Module implementation.

Tests:
    - Material Event Taxonomy
    - MNPI Scoring Algorithm
    - Event Calendar Acquisition
    - Event Proximity Detection
    - Evidence Hash Computation
    - Regulatory Citations

Reference:
    - Section 6: Event Proximity Analysis Module
    - JLAW Zero-Dollar Transaction Forensic Specification v1.0
"""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from src.zero_dollar.models import Transaction, MaterialEvent
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


class TestMaterialEventTaxonomy:
    """Test Material Event Taxonomy implementation."""
    
    def test_form_8k_events_count(self):
        """Test that all 16 Form 8-K event types are defined."""
        assert len(FORM_8K_EVENTS) == 16, "Should have 16 Form 8-K event types"
    
    def test_earnings_events_count(self):
        """Test that all 5 earnings event types are defined."""
        assert len(EARNINGS_EVENTS) == 5, "Should have 5 earnings event types"
    
    def test_critical_event_sensitivity(self):
        """Test CRITICAL sensitivity events."""
        critical_events = ['1.03', '2.02', '2.06', '3.01', '4.02', '5.01']
        for item in critical_events:
            category = FORM_8K_EVENTS[item]
            assert category.mnpi_sensitivity == 'CRITICAL', f"Item {item} should be CRITICAL"
    
    def test_high_event_sensitivity(self):
        """Test HIGH sensitivity events."""
        high_events = ['1.01', '1.02', '2.01', '2.04', '2.05', '4.01']
        for item in high_events:
            category = FORM_8K_EVENTS[item]
            assert category.mnpi_sensitivity == 'HIGH', f"Item {item} should be HIGH"
    
    def test_moderate_event_sensitivity(self):
        """Test MODERATE sensitivity events."""
        moderate_events = ['2.03', '5.02', '5.03']
        for item in moderate_events:
            category = FORM_8K_EVENTS[item]
            assert category.mnpi_sensitivity == 'MODERATE', f"Item {item} should be MODERATE"
    
    def test_event_category_structure(self):
        """Test EventCategory dataclass structure."""
        category = FORM_8K_EVENTS['2.02']
        assert category.item == '2.02'
        assert category.description == 'Results of Operations and Financial Condition'
        assert category.mnpi_sensitivity == 'CRITICAL'
        assert category.lookback_days == 14
        assert category.lookforward_days == 2
    
    def test_get_event_category(self):
        """Test get_event_category function."""
        category = get_event_category('1.01')
        assert category.description == 'Entry into Material Definitive Agreement'
        
        earnings_category = get_event_category('QUARTERLY_EARNINGS')
        assert earnings_category.mnpi_sensitivity == 'CRITICAL'
    
    def test_get_event_category_invalid(self):
        """Test get_event_category with invalid event type."""
        with pytest.raises(KeyError):
            get_event_category('INVALID_EVENT')


class TestMNPIScoring:
    """Test MNPI Scoring Algorithm."""
    
    def test_calculate_mnpi_score_critical_pre_event(self):
        """Test MNPI score for CRITICAL event with PRE proximity."""
        event = MaterialEvent(
            event_id='TEST-001',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='2.02',
            event_date=date(2020, 1, 15),
            event_description='Earnings Release',
            is_price_sensitive=True,
        )
        
        # Transaction 3 days before event
        score = calculate_mnpi_score(
            event=event,
            days_delta=3,
            proximity_type='PRE',
            sensitivity='CRITICAL'
        )
        
        # CRITICAL (1.0) * exp(-0.1*3) * 1.0 = 0.741
        assert score >= Decimal('0.70'), "Should be high score for CRITICAL pre-event"
        assert score <= Decimal('0.75')
    
    def test_calculate_mnpi_score_high_pre_event(self):
        """Test MNPI score for HIGH sensitivity event."""
        event = MaterialEvent(
            event_id='TEST-002',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='1.01',
            event_date=date(2020, 1, 15),
            event_description='Material Agreement',
            is_price_sensitive=True,
        )
        
        score = calculate_mnpi_score(
            event=event,
            days_delta=5,
            proximity_type='PRE',
            sensitivity='HIGH'
        )
        
        # HIGH (0.75) * exp(-0.1*5) * 1.0 = 0.455
        assert score >= Decimal('0.40')
        assert score <= Decimal('0.50')
    
    def test_calculate_mnpi_score_post_event(self):
        """Test MNPI score for POST event (lower risk)."""
        event = MaterialEvent(
            event_id='TEST-003',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='2.02',
            event_date=date(2020, 1, 15),
            event_description='Earnings Release',
            is_price_sensitive=True,
        )
        
        score = calculate_mnpi_score(
            event=event,
            days_delta=1,
            proximity_type='POST',
            sensitivity='CRITICAL'
        )
        
        # POST events have direction_factor of 0.25
        assert score < Decimal('0.30'), "POST event should have lower score"
    
    def test_exponential_decay(self):
        """Test that MNPI score decays exponentially with distance."""
        event = MaterialEvent(
            event_id='TEST-004',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='2.02',
            event_date=date(2020, 1, 15),
            event_description='Earnings Release',
            is_price_sensitive=True,
        )
        
        # Score should decay as days increase
        score_1day = calculate_mnpi_score(event, 1, 'PRE', 'CRITICAL')
        score_7days = calculate_mnpi_score(event, 7, 'PRE', 'CRITICAL')
        score_14days = calculate_mnpi_score(event, 14, 'PRE', 'CRITICAL')
        
        assert score_1day > score_7days > score_14days, "Score should decay with distance"
    
    def test_determine_mnpi_severity(self):
        """Test MNPI severity classification."""
        assert determine_mnpi_severity(Decimal('0.75')) == 'CRITICAL'
        assert determine_mnpi_severity(Decimal('0.60')) == 'HIGH'
        assert determine_mnpi_severity(Decimal('0.40')) == 'MODERATE'
        assert determine_mnpi_severity(Decimal('0.20')) == 'LOW'
    
    def test_get_event_citations_critical(self):
        """Test regulatory citations for CRITICAL events."""
        event = MaterialEvent(
            event_id='TEST-005',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='2.02',
            event_date=date(2020, 1, 15),
            event_description='Earnings Release',
            is_price_sensitive=True,
        )
        
        citations = get_event_citations(event, sensitivity='CRITICAL')
        
        assert '15 U.S.C. § 78j(b)' in citations
        assert '17 CFR § 240.10b-5' in citations
        assert '17 CFR § 240.10b5-1' in citations
        assert '18 U.S.C. § 1348' in citations
    
    def test_get_event_citations_earnings(self):
        """Test that earnings events include Regulation FD."""
        event = MaterialEvent(
            event_id='TEST-006',
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type='QUARTERLY_EARNINGS',
            event_date=date(2020, 1, 15),
            event_description='Quarterly Earnings Release',
            is_price_sensitive=True,
        )
        
        citations = get_event_citations(event, sensitivity='CRITICAL')
        
        assert 'Regulation FD (17 CFR § 243)' in citations


class TestEventProximityModule:
    """Test Event Proximity Module functionality."""
    
    def create_test_transaction(
        self,
        accession: str,
        txn_date: date,
        is_zero_dollar: bool = True
    ) -> Transaction:
        """Helper to create test transaction."""
        return Transaction(
            accession_number=accession,
            issuer_cik='0000320187',
            issuer_name='Test Company',
            reporting_person_cik='0001111111',
            reporting_person_name='John Smith',
            transaction_date=txn_date,
            filing_date=txn_date,
            transaction_code='P',
            shares=Decimal('10000'),
            price_per_share=None if is_zero_dollar else Decimal('100.00'),
            transaction_acquired_disposed='A',
            shares_owned_following=Decimal('50000'),
            direct_indirect='D',
        )
    
    def create_test_event(
        self,
        event_id: str,
        event_date: date,
        event_type: str = '2.02'
    ) -> MaterialEvent:
        """Helper to create test material event."""
        return MaterialEvent(
            event_id=event_id,
            issuer_cik='0000320187',
            issuer_name='Test Company',
            event_type=f'8K-{event_type}',
            event_date=event_date,
            event_description=f'Form 8-K Item {event_type}',
            is_price_sensitive=True,
        )
    
    def test_module_initialization(self):
        """Test EventProximityModule initialization."""
        module = EventProximityModule()
        assert module.event_buffer_days == 60
        assert module.mnpi_threshold == Decimal('0.3')
    
    def test_module_custom_config(self):
        """Test module with custom configuration."""
        config = {
            'event_buffer_days': 90,
            'mnpi_threshold': Decimal('0.5'),
        }
        module = EventProximityModule(config)
        assert module.event_buffer_days == 90
        assert module.mnpi_threshold == Decimal('0.5')
    
    def test_detect_event_proximity_pre_event(self):
        """Test detecting transaction before event (PRE_EVENT)."""
        module = EventProximityModule()
        
        # Transaction 5 days before event
        txn = self.create_test_transaction('ACC-001', date(2020, 1, 10))
        event = self.create_test_event('EVT-001', date(2020, 1, 15))
        
        flags = module.detect_event_proximity(txn, [event])
        
        assert len(flags) > 0, "Should detect proximity"
        flag = flags[0]
        assert flag.proximity_type == 'PRE_EVENT'
        assert flag.days_delta == 5
        assert flag.mnpi_inference_score > Decimal('0.3')
    
    def test_detect_event_proximity_post_event(self):
        """Test detecting transaction after event (POST_EVENT)."""
        module = EventProximityModule()
        
        # Transaction 1 day after event
        txn = self.create_test_transaction('ACC-002', date(2020, 1, 16))
        event = self.create_test_event('EVT-002', date(2020, 1, 15))
        
        flags = module.detect_event_proximity(txn, [event])
        
        assert len(flags) > 0, "Should detect proximity"
        flag = flags[0]
        assert flag.proximity_type == 'POST_EVENT'
        assert flag.days_delta == -1
    
    def test_detect_event_proximity_same_day(self):
        """Test detecting transaction on same day as event."""
        module = EventProximityModule()
        
        txn = self.create_test_transaction('ACC-003', date(2020, 1, 15))
        event = self.create_test_event('EVT-003', date(2020, 1, 15))
        
        flags = module.detect_event_proximity(txn, [event])
        
        assert len(flags) > 0, "Should detect same-day proximity"
        flag = flags[0]
        assert flag.proximity_type == 'SAME_DAY'
        assert flag.days_delta == 0
    
    def test_detect_event_proximity_outside_window(self):
        """Test that transactions outside proximity window are not flagged."""
        module = EventProximityModule()
        
        # Transaction 60 days before event (outside lookback window)
        txn = self.create_test_transaction('ACC-004', date(2020, 1, 1))
        event = self.create_test_event('EVT-004', date(2020, 3, 1))
        
        flags = module.detect_event_proximity(txn, [event])
        
        # Should have no flags or very low MNPI score
        assert len(flags) == 0 or all(f.mnpi_inference_score < Decimal('0.1') for f in flags)
    
    def test_detect_event_proximity_multiple_events(self):
        """Test detecting proximity to multiple events."""
        module = EventProximityModule()
        
        txn = self.create_test_transaction('ACC-005', date(2020, 1, 10))
        
        events = [
            self.create_test_event('EVT-005-A', date(2020, 1, 12)),  # 2 days after
            self.create_test_event('EVT-005-B', date(2020, 1, 15)),  # 5 days after
            self.create_test_event('EVT-005-C', date(2020, 1, 20)),  # 10 days after
        ]
        
        flags = module.detect_event_proximity(txn, events)
        
        assert len(flags) >= 2, "Should detect multiple proximities"
    
    def test_evidence_hash_computation(self):
        """Test evidence hash is computed correctly."""
        module = EventProximityModule()
        
        txn = self.create_test_transaction('ACC-006', date(2020, 1, 10))
        event = self.create_test_event('EVT-006', date(2020, 1, 15))
        
        flags = module.detect_event_proximity(txn, [event])
        
        assert len(flags) > 0
        flag = flags[0]
        assert flag.evidence_hash is not None
        assert len(flag.evidence_hash) == 64, "SHA-256 hash should be 64 hex chars"
    
    def test_regulatory_citations(self):
        """Test regulatory citations are included in flags."""
        module = EventProximityModule()
        
        txn = self.create_test_transaction('ACC-007', date(2020, 1, 10))
        event = self.create_test_event('EVT-007', date(2020, 1, 15), '2.02')
        
        flags = module.detect_event_proximity(txn, [event])
        
        assert len(flags) > 0
        flag = flags[0]
        assert len(flag.regulatory_citations) > 0
        assert '15 U.S.C. § 78j(b)' in flag.regulatory_citations
    
    def test_narrative_generation(self):
        """Test narrative is human-readable and informative."""
        module = EventProximityModule()
        
        txn = self.create_test_transaction('ACC-008', date(2020, 1, 10))
        event = self.create_test_event('EVT-008', date(2020, 1, 15))
        
        flags = module.detect_event_proximity(txn, [event])
        
        assert len(flags) > 0
        flag = flags[0]
        assert flag.narrative is not None
        assert len(flag.narrative) > 0
        assert 'MNPI' in flag.narrative or 'material' in flag.narrative.lower()
    
    def test_convenience_function(self):
        """Test detect_event_proximity convenience function."""
        txn = self.create_test_transaction('ACC-009', date(2020, 1, 10))
        event = self.create_test_event('EVT-009', date(2020, 1, 15))
        
        flags = detect_event_proximity([txn], [event])
        
        assert len(flags) > 0
        assert flags[0].transaction_id == 'ACC-009'


def test_imports():
    """Test that all modules can be imported."""
    print("Testing Event Proximity Module imports...")
    
    try:
        from src.zero_dollar.modules import (
            EventProximityModule,
            EventProximityOutput,
            EventCategory,
            FORM_8K_EVENTS,
            EARNINGS_EVENTS,
            calculate_mnpi_score,
            get_event_citations,
        )
        from src.zero_dollar.acquisition import EventCalendarAcquisition
        
        print("✓ All Event Proximity modules import successfully")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("EVENT PROXIMITY ANALYSIS MODULE TEST SUITE")
    print("=" * 70)
    
    # Test imports first
    if not test_imports():
        print("\n✗ Import tests failed. Cannot proceed.")
        return False
    
    # Run pytest
    print("\nRunning pytest tests...\n")
    exit_code = pytest.main([
        __file__,
        '-v',
        '--tb=short',
    ])
    
    return exit_code == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
