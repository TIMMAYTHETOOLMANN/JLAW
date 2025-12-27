#!/usr/bin/env python3
"""
Beneficial Ownership Chain Resolution Module Tests
==================================================

Validates the implementation of Section 7 modules:
- Entity Classifier
- Footnote Parser
- Control Assessment
- Ownership Chain
- HSR Analysis

Per JLAW Zero-Dollar Transaction Forensic Specification v1.0.
"""

import sys
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all Section 7 modules can be imported."""
    print("Testing Section 7 module imports...")
    
    try:
        # Entity Classifier
        from src.zero_dollar.modules import (
            EntityTypeInfo,
            ENTITY_TYPE_TAXONOMY,
            get_entity_type_info,
            get_control_presumption,
            classify_entity_by_description,
        )
        print("✓ Entity classifier imports successfully")
        
        # Footnote Parser
        from src.zero_dollar.modules import (
            parse_ownership_footnotes,
            calculate_parse_confidence,
            extract_entity_names,
            detect_ownership_transfer,
            extract_control_indicators,
        )
        print("✓ Footnote parser imports successfully")
        
        # Control Assessment
        from src.zero_dollar.modules import (
            ControlIndicator,
            ControlAssessment,
            assess_control_indicators,
            calculate_control_probability,
            generate_control_recommendation,
            assess_voting_control,
            assess_dispositive_control,
        )
        print("✓ Control assessment imports successfully")
        
        # Ownership Chain
        from src.zero_dollar.modules import (
            BeneficialOwnershipModule,
            OwnershipChain,
            OwnershipNode,
            construct_ownership_chain,
        )
        print("✓ Ownership chain imports successfully")
        
        # HSR Analysis
        from src.zero_dollar.modules import (
            HSRAnalysis,
            check_hsr_circumvention,
            HSR_THRESHOLD_2024,
            HSR_SIZE_OF_PERSON_2024,
            calculate_hsr_threshold_distance,
            detect_threshold_fragmentation,
            get_hsr_filing_requirements,
        )
        print("✓ HSR analysis imports successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_entity_taxonomy():
    """Test entity classification taxonomy."""
    print("\nTesting entity classification taxonomy...")
    
    try:
        from src.zero_dollar.models import EntityType
        from src.zero_dollar.modules import ENTITY_TYPE_TAXONOMY, get_control_presumption
        
        # Verify all 10 entity types are in taxonomy
        expected_types = [
            EntityType.RLT, EntityType.IRT, EntityType.GRAT, EntityType.FLP,
            EntityType.LLC, EntityType.DAF, EntityType.PF, EntityType.CRT,
            EntityType.SPOUSE, EntityType.CHILD
        ]
        
        for entity_type in expected_types:
            assert entity_type in ENTITY_TYPE_TAXONOMY, f"Missing {entity_type}"
            info = ENTITY_TYPE_TAXONOMY[entity_type]
            assert info.description, f"Missing description for {entity_type}"
            assert info.control_presumption in ['HIGH', 'MODERATE', 'LOW']
            
        print(f"  ✓ All 10 entity types present in taxonomy")
        
        # Test control presumption
        assert get_control_presumption(EntityType.RLT) == 'HIGH'
        assert get_control_presumption(EntityType.DAF) == 'LOW'
        print("  ✓ Control presumptions correct")
        
        return True
    except Exception as e:
        print(f"✗ Entity taxonomy error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_footnote_parser():
    """Test footnote parsing functionality."""
    print("\nTesting footnote parser...")
    
    try:
        from src.zero_dollar.modules import (
            parse_ownership_footnotes,
            detect_ownership_transfer,
            extract_control_indicators,
        )
        from src.zero_dollar.models import EntityType
        
        # Test trust pattern
        footnotes = [
            "Transferred to the Smith Family Trust",
            "Gift to Smith Foundation",
            "Shares held by Smith Holdings LLC",
        ]
        
        entities = parse_ownership_footnotes(
            footnotes=footnotes,
            reporting_person_cik="0001234567",
            transaction_accession="0001234567-20-000001"
        )
        
        assert len(entities) >= 3, f"Expected at least 3 entities, got {len(entities)}"
        print(f"  ✓ Parsed {len(entities)} entity references")
        
        # Test ownership transfer detection
        assert detect_ownership_transfer(footnotes) == True
        print("  ✓ Ownership transfer detected")
        
        # Test control indicator extraction
        control_footnotes = [
            "Reporting person serves as trustee with sole voting power",
            "As general partner with investment control"
        ]
        indicators = extract_control_indicators(control_footnotes)
        assert len(indicators) > 0, "Should detect control indicators"
        print(f"  ✓ Extracted {len(indicators)} control indicators")
        
        return True
    except Exception as e:
        print(f"✗ Footnote parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_control_assessment():
    """Test control assessment logic."""
    print("\nTesting control assessment...")
    
    try:
        from src.zero_dollar.modules import (
            assess_control_indicators,
            calculate_control_probability,
            ControlIndicator,
        )
        from src.zero_dollar.models import EntityType, EntityReference
        
        # Create test entity
        entity = EntityReference(
            entity_id="test-001",
            entity_name="Test Family Trust",
            entity_type=EntityType.RLT,
            transaction_accession="0001234567-20-000001",
            reporting_person_cik="0001234567",
            confidence_score=0.95,
            raw_text="Transferred to Test Family Trust"
        )
        
        # Assess control indicators
        assessment = assess_control_indicators(entity, schedule_13=None)
        
        assert assessment.entity == entity
        assert len(assessment.indicators) > 0, "Should have control indicators"
        assert assessment.overall_control_probability >= Decimal('0'), "Probability should be non-negative"
        assert assessment.recommendation, "Should have recommendation"
        print(f"  ✓ Control assessment: probability={assessment.overall_control_probability}")
        print(f"  ✓ Recommendation: {assessment.recommendation}")
        
        # Test probability calculation
        test_indicators = [
            ControlIndicator(
                indicator_type='TEST_HIGH',
                description='Test high severity',
                severity='HIGH'
            ),
            ControlIndicator(
                indicator_type='TEST_CRITICAL',
                description='Test critical severity',
                severity='CRITICAL'
            ),
        ]
        
        prob = calculate_control_probability(test_indicators)
        assert prob > Decimal('0.5'), "High+Critical should give >0.5 probability"
        print(f"  ✓ Probability calculation: {prob}")
        
        return True
    except Exception as e:
        print(f"✗ Control assessment error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ownership_chain():
    """Test ownership chain construction."""
    print("\nTesting ownership chain construction...")
    
    try:
        from src.zero_dollar.modules import (
            BeneficialOwnershipModule,
            OwnershipChain,
        )
        from src.zero_dollar.models import (
            Transaction,
            ReportingPerson,
            ReportingPersonClassification,
        )
        
        # Create test data
        reporting_person = ReportingPerson(
            cik="0001234567",
            name="John Smith",
            classification=ReportingPersonClassification.SECTION_16_OFFICER,
            is_officer=True,
            officer_title="Chief Executive Officer"
        )
        
        transaction = Transaction(
            accession_number="0001234567-20-000001",
            issuer_cik="0000320187",
            issuer_name="Test Company",
            reporting_person_cik="0001234567",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 1, 15),
            filing_date=date(2020, 1, 17),
            transaction_code="G",
            shares=Decimal("10000"),
            price_per_share=Decimal("0"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("40000"),
            direct_indirect="I",
            nature_of_ownership="By Trust",
            footnotes=["Transferred to Smith Family Trust"]
        )
        
        # Test module
        module = BeneficialOwnershipModule()
        chain = module.construct_ownership_chain(
            reporting_person=reporting_person,
            transactions=[transaction],
            schedule_13_filings=[]
        )
        
        assert chain.root_cik == "0001234567"
        assert chain.root_name == "John Smith"
        print(f"  ✓ Chain constructed with {len(chain.nodes)} nodes")
        print(f"  ✓ Chain ID: {chain.chain_id}")
        
        # Test evidence hash
        chain.evidence_hash = module.compute_chain_hash(chain)
        assert chain.evidence_hash, "Should have evidence hash"
        assert len(chain.evidence_hash) == 64, "SHA-256 should be 64 hex chars"
        print(f"  ✓ Evidence hash: {chain.evidence_hash[:16]}...")
        
        # Test serialization
        chain_dict = chain.to_dict()
        assert 'chain_id' in chain_dict
        assert 'nodes' in chain_dict
        print("  ✓ Serialization to dict successful")
        
        return True
    except Exception as e:
        print(f"✗ Ownership chain error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hsr_analysis():
    """Test HSR threshold analysis."""
    print("\nTesting HSR threshold analysis...")
    
    try:
        from src.zero_dollar.modules import (
            check_hsr_circumvention,
            HSR_THRESHOLD_2024,
            calculate_hsr_threshold_distance,
            get_hsr_filing_requirements,
        )
        from decimal import Decimal
        
        # Verify threshold constant
        assert HSR_THRESHOLD_2024 == Decimal('119500000'), "Incorrect 2024 threshold"
        print(f"  ✓ HSR threshold: ${HSR_THRESHOLD_2024:,.0f}")
        
        # Test threshold distance calculation
        test_value = Decimal('100000000')
        distance, percentage = calculate_hsr_threshold_distance(test_value)
        assert distance > 0, "Distance should be positive when below threshold"
        assert percentage < 100, "Percentage should be <100 when below threshold"
        print(f"  ✓ Threshold distance: ${distance:,.0f} ({percentage:.1f}%)")
        
        # Test filing requirements
        requirements = get_hsr_filing_requirements(Decimal('150000000'))
        assert requirements['filing_required'] == True, "Should require filing above threshold"
        print(f"  ✓ Filing requirements calculated")
        
        # Test below threshold
        requirements_low = get_hsr_filing_requirements(Decimal('50000000'))
        assert requirements_low['filing_required'] == False, "Should not require filing below threshold"
        print(f"  ✓ Below-threshold detection works")
        
        return True
    except Exception as e:
        print(f"✗ HSR analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration of all components."""
    print("\nTesting full integration...")
    
    try:
        from src.zero_dollar.modules import BeneficialOwnershipModule
        from src.zero_dollar.models import (
            Transaction,
            ReportingPerson,
            ReportingPersonClassification,
        )
        import asyncio
        
        # Create test data
        reporting_person = ReportingPerson(
            cik="0001111111",
            name="Jane Doe",
            classification=ReportingPersonClassification.SECTION_16_DIRECTOR,
            is_director=True
        )
        
        transactions = [
            Transaction(
                accession_number="0001111111-20-000001",
                issuer_cik="0000320187",
                issuer_name="Test Corp",
                reporting_person_cik="0001111111",
                reporting_person_name="Jane Doe",
                transaction_date=date(2020, 3, 1),
                filing_date=date(2020, 3, 3),
                transaction_code="G",
                shares=Decimal("50000"),
                price_per_share=None,
                transaction_acquired_disposed="D",
                shares_owned_following=Decimal("100000"),
                direct_indirect="I",
                footnotes=["Gift to Doe Family Foundation", "Donor retains advisory privileges"]
            ),
            Transaction(
                accession_number="0001111111-20-000002",
                issuer_cik="0000320187",
                issuer_name="Test Corp",
                reporting_person_cik="0001111111",
                reporting_person_name="Jane Doe",
                transaction_date=date(2020, 3, 5),
                filing_date=date(2020, 3, 7),
                transaction_code="G",
                shares=Decimal("25000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="D",
                shares_owned_following=Decimal("75000"),
                direct_indirect="I",
                footnotes=["Transferred to Doe Family LLC", "Reporting person serves as manager"]
            ),
        ]
        
        # Test async analyze method
        module = BeneficialOwnershipModule()
        chain = asyncio.run(module.analyze(
            transactions=transactions,
            reporting_person=reporting_person,
            schedule_13_filings=[]
        ))
        
        assert chain.root_cik == "0001111111"
        assert len(chain.nodes) >= 2, f"Expected at least 2 nodes, got {len(chain.nodes)}"
        assert chain.evidence_hash, "Should have evidence hash"
        
        print(f"  ✓ Integration test successful")
        print(f"  ✓ Nodes: {len(chain.nodes)}")
        print(f"  ✓ Total shares: {chain.total_shares_transferred}")
        print(f"  ✓ Avg control prob: {chain.average_control_probability}")
        print(f"  ✓ High control nodes: {chain.high_control_node_count}")
        
        return True
    except Exception as e:
        print(f"✗ Integration test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("BENEFICIAL OWNERSHIP CHAIN RESOLUTION MODULE - VALIDATION")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Entity Taxonomy", test_entity_taxonomy),
        ("Footnote Parser", test_footnote_parser),
        ("Control Assessment", test_control_assessment),
        ("Ownership Chain", test_ownership_chain),
        ("HSR Analysis", test_hsr_analysis),
        ("Full Integration", test_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - Module implementation successful!")
        return 0
    else:
        print(f"\n✗ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
