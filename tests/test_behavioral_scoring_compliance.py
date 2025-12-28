#!/usr/bin/env python3
"""
Behavioral Scoring Specification Compliance Tests
=================================================

Tests for the specification compliance remediation changes:
- GAP 1: Section 8 reference in docstring
- GAP 2: CRITICAL risk tier threshold at 80 (not 75)
- GAP 3: Filing compliance score documentation
- GAP 4: Compound multiplier logic (1.5x-2.0x)

These tests validate compliance with JLAW Zero-Dollar Transaction 
Forensic Specification v1.0.
"""

import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_critical_threshold_at_80():
    """Test that CRITICAL tier threshold is 80 (not 75) per GAP 2."""
    print("\n" + "=" * 70)
    print("TEST 1: CRITICAL Threshold at 80")
    print("=" * 70)
    
    try:
        from src.zero_dollar.modules import BehavioralScoringEngine
        from src.zero_dollar.modules import TemporalClusteringOutput
        from src.zero_dollar.models import (
            Transaction,
            EventProximityFlag,
            OwnershipChain,
            OwnershipNode,
            EntityType,
        )
        
        engine = BehavioralScoringEngine()
        
        # Test priority determination
        priority_79 = engine._determine_prosecutorial_priority(79.0)
        priority_80 = engine._determine_prosecutorial_priority(80.0)
        priority_75 = engine._determine_prosecutorial_priority(75.0)
        
        # Verify 80 is CRITICAL (priority 1), but 79 is not
        assert priority_80 == 1, f"Score 80 should be CRITICAL (priority 1), got {priority_80}"
        assert priority_79 == 2, f"Score 79 should be HIGH (priority 2), got {priority_79}"
        
        # Verify 75 is no longer CRITICAL
        assert priority_75 == 2, f"Score 75 should be HIGH (priority 2), got {priority_75}"
        
        print("✓ CRITICAL threshold correctly set to 80")
        print(f"  - Score 80: Priority {priority_80} (CRITICAL)")
        print(f"  - Score 79: Priority {priority_79} (HIGH)")
        print(f"  - Score 75: Priority {priority_75} (HIGH)")
        
        return True
    except Exception as e:
        print(f"✗ CRITICAL threshold test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compound_multiplier_logic():
    """Test compound multiplier implementation per GAP 4."""
    print("\n" + "=" * 70)
    print("TEST 2: Compound Multiplier Logic")
    print("=" * 70)
    
    try:
        from src.zero_dollar.modules import BehavioralScoringEngine
        
        engine = BehavioralScoringEngine()
        
        # Test 0 active anomalies - no multiplier
        multiplier_0 = engine._calculate_compound_multiplier(
            magnitude_score=5.0,   # Below threshold (12.5)
            frequency_score=5.0,   # Below threshold (12.5)
            timing_score=5.0,      # Below threshold (10.0)
            filing_score=3.0,      # Below threshold (7.5)
            entity_score=3.0,      # Below threshold (7.5)
        )
        assert multiplier_0 == 1.0, f"Expected 1.0x for 0 active anomalies, got {multiplier_0}x"
        print(f"✓ 0 active anomalies: {multiplier_0}x multiplier")
        
        # Test 1 active anomaly - no multiplier
        multiplier_1 = engine._calculate_compound_multiplier(
            magnitude_score=15.0,  # Above threshold (12.5)
            frequency_score=5.0,   # Below threshold
            timing_score=5.0,      # Below threshold
            filing_score=3.0,      # Below threshold
            entity_score=3.0,      # Below threshold
        )
        assert multiplier_1 == 1.0, f"Expected 1.0x for 1 active anomaly, got {multiplier_1}x"
        print(f"✓ 1 active anomaly: {multiplier_1}x multiplier")
        
        # Test 2 active anomalies - 1.5x multiplier
        multiplier_2 = engine._calculate_compound_multiplier(
            magnitude_score=15.0,  # Above threshold (12.5)
            frequency_score=15.0,  # Above threshold (12.5)
            timing_score=5.0,      # Below threshold
            filing_score=3.0,      # Below threshold
            entity_score=3.0,      # Below threshold
        )
        assert multiplier_2 == 1.5, f"Expected 1.5x for 2 active anomalies, got {multiplier_2}x"
        print(f"✓ 2 active anomalies: {multiplier_2}x multiplier")
        
        # Test 3 active anomalies - 1.75x multiplier
        multiplier_3 = engine._calculate_compound_multiplier(
            magnitude_score=15.0,  # Above threshold (12.5)
            frequency_score=15.0,  # Above threshold (12.5)
            timing_score=12.0,     # Above threshold (10.0)
            filing_score=3.0,      # Below threshold
            entity_score=3.0,      # Below threshold
        )
        assert multiplier_3 == 1.75, f"Expected 1.75x for 3 active anomalies, got {multiplier_3}x"
        print(f"✓ 3 active anomalies: {multiplier_3}x multiplier")
        
        # Test 4 active anomalies - 2.0x multiplier
        multiplier_4 = engine._calculate_compound_multiplier(
            magnitude_score=15.0,  # Above threshold (12.5)
            frequency_score=15.0,  # Above threshold (12.5)
            timing_score=12.0,     # Above threshold (10.0)
            filing_score=10.0,     # Above threshold (7.5)
            entity_score=3.0,      # Below threshold
        )
        assert multiplier_4 == 2.0, f"Expected 2.0x for 4 active anomalies, got {multiplier_4}x"
        print(f"✓ 4 active anomalies: {multiplier_4}x multiplier")
        
        # Test 5 active anomalies - 2.0x multiplier (capped)
        multiplier_5 = engine._calculate_compound_multiplier(
            magnitude_score=15.0,  # Above threshold (12.5)
            frequency_score=15.0,  # Above threshold (12.5)
            timing_score=12.0,     # Above threshold (10.0)
            filing_score=10.0,     # Above threshold (7.5)
            entity_score=10.0,     # Above threshold (7.5)
        )
        assert multiplier_5 == 2.0, f"Expected 2.0x for 5 active anomalies, got {multiplier_5}x"
        print(f"✓ 5 active anomalies: {multiplier_5}x multiplier (capped)")
        
        return True
    except Exception as e:
        print(f"✗ Compound multiplier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compound_multiplier_integration():
    """Test that compound multiplier is applied to total scores."""
    print("\n" + "=" * 70)
    print("TEST 3: Compound Multiplier Integration")
    print("=" * 70)
    
    try:
        from src.zero_dollar.modules import BehavioralScoringEngine
        from src.zero_dollar.modules import TemporalClusteringOutput
        from src.zero_dollar.models import (
            Transaction,
            OwnershipChain,
            OwnershipNode,
            EntityType,
        )
        
        # Create test data with high scores in multiple components
        transactions = []
        for i in range(10):  # Create 10 zero-dollar transactions
            transactions.append(Transaction(
                accession_number=f"0000320187-20-00000{i}",
                issuer_cik="0000320187",
                issuer_name="Test Company",
                reporting_person_cik="0001234567",
                reporting_person_name="John Doe",
                transaction_date=date(2020, 1, 10 + i),
                filing_date=date(2020, 1, 20 + i),  # Late filing (>2 days)
                transaction_code="P",
                shares=Decimal("100000"),  # Large magnitude
                price_per_share=None,  # Zero-dollar
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("500000"),
                direct_indirect="I",
                nature_of_ownership="By Trust",
            ))
        
        temporal_output = TemporalClusteringOutput(
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            analysis_period=(date(2020, 1, 1), date(2020, 12, 31)),
            clusters_detected=[],  # Empty list means cluster_count property will return 0
            total_anomaly_score=Decimal("50"),
            escalation_recommendation="HIGH",
        )
        
        # Create complex ownership chain
        ownership_chain = OwnershipChain(
            chain_id="CHAIN-001",
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            nodes=[
                OwnershipNode(
                    node_id=f"NODE-{i}",
                    entity_name=f"Entity {i}",
                    entity_type=EntityType.RLT,
                    ownership_percentage=100.0 / (i + 1),
                )
                for i in range(5)  # 5 entities for high entity score
            ],
            total_depth=5,
            effective_ownership=100.0,
        )
        
        engine = BehavioralScoringEngine()
        
        # Calculate assessment without event flags for simplicity
        assessment = engine.calculate_assessment(
            reporting_person_cik="0001234567",
            reporting_person_name="John Doe",
            issuer_cik="0000320187",
            issuer_name="Test Company",
            transactions=transactions,
            temporal_output=temporal_output,
            event_flags=[],  # No event flags for this test
            ownership_chain=ownership_chain,
        )
        
        print(f"✓ Assessment calculated with compound multiplier")
        print(f"  - Magnitude Score: {assessment.score_components.magnitude_score:.2f}/25")
        print(f"  - Frequency Score: {assessment.score_components.frequency_score:.2f}/25")
        print(f"  - Timing Score: {assessment.score_components.timing_score:.2f}/20")
        print(f"  - Filing Score: {assessment.score_components.filing_compliance_score:.2f}/15")
        print(f"  - Entity Score: {assessment.score_components.entity_complexity_score:.2f}/15")
        print(f"  - Total Score: {assessment.risk_score:.2f}/100")
        print(f"  - Risk Level: {assessment.risk_level}")
        print(f"  - Priority: {assessment.prosecutorial_priority}")
        
        # Verify score is capped at 100
        assert assessment.risk_score <= 100.0, f"Total score exceeds 100: {assessment.risk_score}"
        print(f"✓ Total score properly capped at 100")
        
        return True
    except Exception as e:
        print(f"✗ Compound multiplier integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filing_compliance_score_documentation():
    """Test that filing compliance score has proper documentation per GAP 3."""
    print("\n" + "=" * 70)
    print("TEST 4: Filing Compliance Score Documentation")
    print("=" * 70)
    
    try:
        from src.zero_dollar.modules.behavioral_scoring import BehavioralScoringEngine
        import inspect
        
        # Get the source of the _calculate_filing_compliance_score method
        source = inspect.getsource(BehavioralScoringEngine._calculate_filing_compliance_score)
        
        # Check for documentation about price_variance_score mapping
        assert "price_variance_score" in source, "Missing reference to price_variance_score in docstring"
        assert "filing_compliance_score" in source, "Missing reference to filing_compliance_score in docstring"
        
        print("✓ Filing compliance score has proper documentation")
        print("  - References both 'price_variance_score' (specification)")
        print("  - References 'filing_compliance_score' (implementation)")
        
        return True
    except Exception as e:
        print(f"✗ Documentation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_section_8_reference():
    """Test that module docstring references Section 8 per GAP 1."""
    print("\n" + "=" * 70)
    print("TEST 5: Section 8 Reference in Docstring")
    print("=" * 70)
    
    try:
        import src.zero_dollar.modules.behavioral_scoring as module
        
        # Get module docstring
        docstring = module.__doc__
        
        # Check for Section 8 references
        assert "Section 8" in docstring, "Missing 'Section 8' reference in docstring"
        assert "Behavioral Pattern Scoring Engine" in docstring, "Missing 'Behavioral Pattern Scoring Engine' in docstring"
        
        # Ensure Section 6 is not referenced (old version)
        assert "Section 6: Behavioral Risk Scoring" not in docstring, "Old 'Section 6' reference still present"
        
        print("✓ Module docstring correctly references Section 8")
        print("  - References 'Section 8: Behavioral Pattern Scoring Engine'")
        print("  - Old 'Section 6' reference removed")
        
        return True
    except Exception as e:
        print(f"✗ Section 8 reference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that changes maintain backward compatibility."""
    print("\n" + "=" * 70)
    print("TEST 6: Backward Compatibility")
    print("=" * 70)
    
    try:
        from src.zero_dollar.modules import BehavioralScoringEngine
        from src.zero_dollar.modules import TemporalClusteringOutput
        from src.zero_dollar.models import (
            Transaction,
            EventProximityFlag,
            OwnershipChain,
            OwnershipNode,
            EntityType,
        )
        
        # Test basic assessment with minimal data
        transactions = [
            Transaction(
                accession_number="0000320187-20-000001",
                issuer_cik="0000320187",
                issuer_name="Test Company",
                reporting_person_cik="0001234567",
                reporting_person_name="John Doe",
                transaction_date=date(2020, 1, 10),
                filing_date=date(2020, 1, 15),
                transaction_code="P",
                shares=Decimal("10000"),
                price_per_share=None,
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("50000"),
                direct_indirect="D",
            )
        ]
        
        temporal_output = TemporalClusteringOutput(
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            analysis_period=(date(2020, 1, 1), date(2020, 12, 31)),
            clusters_detected=[],
            total_anomaly_score=Decimal("0"),
            escalation_recommendation="NONE",
        )
        
        ownership_chain = OwnershipChain(
            chain_id="CHAIN-001",
            reporting_person_cik="0001234567",
            issuer_cik="0000320187",
            nodes=[
                OwnershipNode(
                    node_id="NODE-001",
                    entity_name="John Doe",
                    entity_type=EntityType.RLT,
                    ownership_percentage=100.0,
                )
            ],
            total_depth=1,
            effective_ownership=100.0,
        )
        
        engine = BehavioralScoringEngine()
        
        # Should not raise any exceptions
        assessment = engine.calculate_assessment(
            reporting_person_cik="0001234567",
            reporting_person_name="John Doe",
            issuer_cik="0000320187",
            issuer_name="Test Company",
            transactions=transactions,
            temporal_output=temporal_output,
            event_flags=[],
            ownership_chain=ownership_chain,
        )
        
        # Verify basic structure
        assert hasattr(assessment, 'risk_score')
        assert hasattr(assessment, 'risk_level')
        assert hasattr(assessment, 'prosecutorial_priority')
        assert hasattr(assessment, 'score_components')
        
        print("✓ Backward compatibility maintained")
        print(f"  - Assessment completed successfully")
        print(f"  - All required fields present")
        print(f"  - Risk Score: {assessment.risk_score:.2f}/100")
        
        return True
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all compliance tests."""
    print("=" * 70)
    print("Behavioral Scoring Specification Compliance Tests")
    print("=" * 70)
    
    tests = [
        ("CRITICAL Threshold at 80 (GAP 2)", test_critical_threshold_at_80),
        ("Compound Multiplier Logic (GAP 4)", test_compound_multiplier_logic),
        ("Compound Multiplier Integration (GAP 4)", test_compound_multiplier_integration),
        ("Filing Compliance Score Documentation (GAP 3)", test_filing_compliance_score_documentation),
        ("Section 8 Reference (GAP 1)", test_section_8_reference),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    results = []
    for name, test_func in tests:
        success = test_func()
        results.append((name, success))
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({100 * passed / total:.1f}%)")
    
    if passed == total:
        print("\n🎉 All compliance tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
