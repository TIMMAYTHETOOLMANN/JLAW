#!/usr/bin/env python3
"""
Zero-Dollar Transaction Foundation Validation
==============================================

Validates that all models, constants, and schemas are correctly implemented
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
        # Test main package import
        import src.zero_dollar
        print("✓ Main package imports successfully")
        
        # Test models
        from src.zero_dollar.models import (
            Transaction, TransactionCluster,
            ReportingPerson, ReportingPersonClassification,
            AnomalyType, AnomalySeverity, EntityType,
            AnomalyFlag, MaterialEvent, EventProximityFlag,
            EntityReference, ControlIndicator, ControlAssessment,
            OwnershipNode, OwnershipChain,
            BehavioralScoreComponents, BehavioralRiskAssessment,
            EvidenceArtifact, MerkleProof, TrustedTimestamp, ChainOfCustodyRecord,
        )
        print("✓ All models import successfully")
        
        # Test constants
        from src.zero_dollar.constants import (
            TransactionCode, TransactionCodeInfo, TRANSACTION_CODE_TAXONOMY,
            get_transaction_code_info, is_zero_dollar_suspicious,
            TemporalWindow, TemporalWindowDefinition, TEMPORAL_WINDOWS,
            TEMPORAL_CLUSTER_WEIGHTS, CLUSTERING_THRESHOLD,
            EVENT_PROXIMITY_WINDOWS, MAX_LATE_FILING_DAYS, MIN_CLUSTER_SIZE,
            calculate_cluster_score, get_applicable_windows,
            MagnitudeTier, MagnitudeThreshold, MAGNITUDE_THRESHOLDS,
            classify_magnitude, get_magnitude_threshold,
            calculate_magnitude_risk_score, get_tier_display_name,
        )
        print("✓ All constants import successfully")
        
        # Test schema
        from src.zero_dollar.schema import get_schema_sql, SCHEMA_FILE
        print("✓ Schema utilities import successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transaction_model():
    """Test Transaction model functionality."""
    print("\nTesting Transaction model...")
    
    try:
        from src.zero_dollar.models import Transaction
        
        # Create a test transaction
        txn = Transaction(
            accession_number="0001234567-20-000123",
            issuer_cik="0000320187",
            issuer_name="NIKE, Inc.",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 1, 15),
            filing_date=date(2020, 1, 17),
            transaction_code="P",
            shares=Decimal("10000"),
            price_per_share=Decimal("0"),
            transaction_acquired_disposed="A",
            shares_owned_following=Decimal("50000"),
            direct_indirect="D",
        )
        
        # Test computed properties
        assert txn.is_zero_dollar == True, "Zero-dollar detection failed"
        assert txn.days_to_filing == 2, "Days to filing calculation failed"
        assert txn.is_late_filing == False, "Late filing detection failed"
        
        print(f"  ✓ Transaction created: {txn.accession_number}")
        print(f"  ✓ Zero-dollar detection: {txn.is_zero_dollar}")
        print(f"  ✓ Days to filing: {txn.days_to_filing}")
        
        return True
    except Exception as e:
        print(f"  ✗ Transaction model error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transaction_codes():
    """Test transaction code taxonomy."""
    print("\nTesting transaction codes...")
    
    try:
        from src.zero_dollar.constants import (
            TransactionCode, 
            get_transaction_code_info,
            is_zero_dollar_suspicious,
        )
        
        # Test transaction code info
        info = get_transaction_code_info("A")
        assert info.code == "A", "Transaction code lookup failed"
        print(f"  ✓ Transaction code A: {info.description}")
        print(f"    - Zero-dollar legitimacy: {info.zero_dollar_legitimacy}")
        print(f"    - Forensic scrutiny level: {info.forensic_scrutiny_level}")
        
        # Test suspicious detection
        suspicious = is_zero_dollar_suspicious("P", magnitude_tier=4)
        print(f"  ✓ Code P with Tier 4 suspicious: {suspicious}")
        
        return True
    except Exception as e:
        print(f"  ✗ Transaction code error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_magnitude_classification():
    """Test magnitude tier classification."""
    print("\nTesting magnitude classification...")
    
    try:
        from src.zero_dollar.constants import classify_magnitude, MagnitudeTier
        
        # Test various magnitudes
        tier1 = classify_magnitude(5000)
        assert tier1 == MagnitudeTier.TIER_1_ROUTINE, "Tier 1 classification failed"
        print(f"  ✓ 5,000 shares: {tier1.value}")
        
        tier2 = classify_magnitude(25000, Decimal("1000000"))
        assert tier2 == MagnitudeTier.TIER_2_MODERATE, "Tier 2 classification failed"
        print(f"  ✓ 25,000 shares / $1M: {tier2.value}")
        
        tier4 = classify_magnitude(500000)
        assert tier4 == MagnitudeTier.TIER_4_EXTRAORDINARY, "Tier 4 classification failed"
        print(f"  ✓ 500,000 shares: {tier4.value}")
        
        return True
    except Exception as e:
        print(f"  ✗ Magnitude classification error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_temporal_clustering():
    """Test temporal clustering functions."""
    print("\nTesting temporal clustering...")
    
    try:
        from src.zero_dollar.constants import (
            calculate_cluster_score,
            get_applicable_windows,
            TemporalWindow,
        )
        
        # Test cluster score calculation
        score = calculate_cluster_score(
            transaction_count=5,
            zero_dollar_count=4,
            span_days=2,
            total_shares=100000,
            max_shares=50000,
            late_filing_count=1,
        )
        print(f"  ✓ Cluster score calculated: {score:.2f}")
        
        # Test applicable windows
        windows = get_applicable_windows(span_days=5)
        print(f"  ✓ Applicable windows for 5 days: {[w.value for w in windows]}")
        
        return True
    except Exception as e:
        print(f"  ✗ Temporal clustering error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schema():
    """Test schema SQL loading."""
    print("\nTesting database schema...")
    
    try:
        from src.zero_dollar.schema import get_schema_sql, SCHEMA_FILE
        
        # Load schema
        schema_sql = get_schema_sql()
        
        # Basic validation
        assert "CREATE TABLE" in schema_sql, "Schema missing table definitions"
        assert "transactions" in schema_sql, "Schema missing transactions table"
        assert "anomaly_flags" in schema_sql, "Schema missing anomaly_flags table"
        assert "evidence_artifacts" in schema_sql, "Schema missing evidence_artifacts table"
        
        print(f"  ✓ Schema file exists: {SCHEMA_FILE}")
        print(f"  ✓ Schema SQL loaded: {len(schema_sql)} bytes")
        print(f"  ✓ Contains required tables")
        
        return True
    except Exception as e:
        print(f"  ✗ Schema error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enums():
    """Test all enum types."""
    print("\nTesting enums...")
    
    try:
        from src.zero_dollar.models import (
            ReportingPersonClassification,
            AnomalyType,
            AnomalySeverity,
            EntityType,
        )
        from src.zero_dollar.constants import (
            TransactionCode,
            TemporalWindow,
            MagnitudeTier,
        )
        
        # Test enum counts
        print(f"  ✓ TransactionCode: {len(TransactionCode)} values")
        print(f"  ✓ ReportingPersonClassification: {len(ReportingPersonClassification)} values")
        print(f"  ✓ AnomalyType: {len(AnomalyType)} values")
        print(f"  ✓ AnomalySeverity: {len(AnomalySeverity)} values")
        print(f"  ✓ EntityType: {len(EntityType)} values")
        print(f"  ✓ TemporalWindow: {len(TemporalWindow)} values")
        print(f"  ✓ MagnitudeTier: {len(MagnitudeTier)} values")
        
        return True
    except Exception as e:
        print(f"  ✗ Enum error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dataclass_serialization():
    """Test dataclass to_dict() methods."""
    print("\nTesting dataclass serialization...")
    
    try:
        from src.zero_dollar.models import (
            Transaction,
            ReportingPerson,
            ReportingPersonClassification,
            AnomalyFlag,
            AnomalyType,
            AnomalySeverity,
        )
        
        # Test Transaction serialization
        txn = Transaction(
            accession_number="0001234567-20-000123",
            issuer_cik="0000320187",
            issuer_name="NIKE, Inc.",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 1, 15),
            filing_date=date(2020, 1, 17),
            transaction_code="A",
            shares=Decimal("10000"),
            price_per_share=None,
            transaction_acquired_disposed="A",
            shares_owned_following=Decimal("50000"),
            direct_indirect="D",
        )
        txn_dict = txn.to_dict()
        assert isinstance(txn_dict, dict), "Transaction to_dict() failed"
        assert txn_dict['is_zero_dollar'] == True, "Serialization missing computed field"
        print(f"  ✓ Transaction.to_dict() works")
        
        # Test ReportingPerson serialization
        person = ReportingPerson(
            cik="0001111111",
            name="John Smith",
            classification=ReportingPersonClassification.SECTION_16_OFFICER,
            is_officer=True,
        )
        person_dict = person.to_dict()
        assert isinstance(person_dict, dict), "ReportingPerson to_dict() failed"
        print(f"  ✓ ReportingPerson.to_dict() works")
        
        # Test AnomalyFlag serialization
        flag = AnomalyFlag(
            flag_id="test-flag",
            anomaly_type=AnomalyType.ZERO_DOLLAR_MAGNITUDE_DISPROPORTION,
            severity=AnomalySeverity.HIGH,
            transaction_accession="0001234567-20-000123",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            issuer_cik="0000320187",
            issuer_name="NIKE, Inc.",
            detection_date=datetime.now(),
            transaction_date=date(2020, 1, 15),
            shares_involved=Decimal("10000"),
            notional_value=Decimal("500000"),
            description="Test anomaly",
        )
        flag_dict = flag.to_dict()
        assert isinstance(flag_dict, dict), "AnomalyFlag to_dict() failed"
        print(f"  ✓ AnomalyFlag.to_dict() works")
        
        return True
    except Exception as e:
        print(f"  ✗ Serialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("Zero-Dollar Transaction Foundation Validation")
    print("=" * 70)
    
    tests = [
        ("Import Test", test_imports),
        ("Transaction Model", test_transaction_model),
        ("Transaction Codes", test_transaction_codes),
        ("Magnitude Classification", test_magnitude_classification),
        ("Temporal Clustering", test_temporal_clustering),
        ("Database Schema", test_schema),
        ("Enums", test_enums),
        ("Dataclass Serialization", test_dataclass_serialization),
    ]
    
    results = []
    for name, test_func in tests:
        success = test_func()
        results.append((name, success))
    
    print("\n" + "=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validations passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} validation(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
