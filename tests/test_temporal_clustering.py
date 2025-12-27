#!/usr/bin/env python3
"""
Temporal Clustering Detection Module Tests
===========================================

Comprehensive validation of the Temporal Clustering Detection Module
per JLAW Zero-Dollar Transaction Forensic Specification v1.0, Section 5.

Test Coverage:
    1. Module imports and initialization
    2. Pairwise temporal distance calculation
    3. DBSCAN clustering integration
    4. Composite anomaly scoring (all 4 components)
    5. Escalation threshold mapping
    6. Integration with Transaction model
    7. Evidence hash computation
    8. Regulatory citations
"""

import sys
import asyncio
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all temporal clustering modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test module imports
        from src.zero_dollar.modules import (
            TemporalClusteringModule,
            TemporalClusteringOutput,
            calculate_temporal_distances,
            get_issuer_historical_median,
            calculate_cluster_anomaly_score,
            determine_escalation_recommendation,
            detect_temporal_clusters,
            DBSCANClusteringAdapter,
        )
        print("✓ All temporal clustering modules import successfully")
        
        # Test Transaction model import
        from src.zero_dollar.models import Transaction, TransactionCluster
        print("✓ Transaction models import successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_temporal_distance_calculation():
    """Test pairwise temporal distance matrix calculation."""
    print("\nTesting temporal distance calculation...")
    
    try:
        from src.zero_dollar.models import Transaction
        from src.zero_dollar.modules import calculate_temporal_distances
        import numpy as np
        
        # Create test transactions with known temporal separations
        transactions = [
            Transaction(
                accession_number="0001234567-20-000001",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("10000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("50000"),
                direct_indirect="D",
            ),
            Transaction(
                accession_number="0001234567-20-000002",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),  # Same day
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("5000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("55000"),
                direct_indirect="D",
            ),
            Transaction(
                accession_number="0001234567-20-000003",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 5),  # 4 days after first
                filing_date=date(2020, 1, 7),
                transaction_code="P",
                shares=Decimal("8000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("63000"),
                direct_indirect="D",
            ),
        ]
        
        # Calculate distance matrix
        distance_matrix, zero_dollar_txns = calculate_temporal_distances(transactions)
        
        # Validate matrix properties
        assert distance_matrix.shape == (3, 3), "Distance matrix should be 3x3"
        assert distance_matrix[0][1] == 0, "Same-day transactions should have 0 distance"
        assert distance_matrix[0][2] == 4, "Distance should be 4 days"
        assert distance_matrix[2][0] == 4, "Matrix should be symmetric"
        assert np.allclose(distance_matrix, distance_matrix.T), "Matrix should be symmetric"
        assert len(zero_dollar_txns) == 3, "Should filter to zero-dollar transactions"
        
        print(f"  ✓ Distance matrix calculated: {distance_matrix.shape}")
        print(f"  ✓ Same-day distance: {distance_matrix[0][1]} days")
        print(f"  ✓ Multi-day distance: {distance_matrix[0][2]} days")
        print(f"  ✓ Matrix symmetry validated")
        
        return True
    except Exception as e:
        print(f"✗ Temporal distance calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dbscan_clustering():
    """Test DBSCAN clustering integration."""
    print("\nTesting DBSCAN clustering...")
    
    try:
        from src.zero_dollar.models import Transaction
        from src.zero_dollar.modules import (
            calculate_temporal_distances,
            detect_temporal_clusters,
        )
        
        # Create transactions with clear clustering pattern
        # Cluster 1: Two same-day transactions
        # Cluster 2: Two transactions 10 days later
        transactions = [
            # Cluster 1
            Transaction(
                accession_number="0001234567-20-000001",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("10000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("50000"),
                direct_indirect="D",
            ),
            Transaction(
                accession_number="0001234567-20-000002",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("5000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("55000"),
                direct_indirect="D",
            ),
            # Cluster 2
            Transaction(
                accession_number="0001234567-20-000003",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 11),
                filing_date=date(2020, 1, 13),
                transaction_code="P",
                shares=Decimal("8000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("63000"),
                direct_indirect="D",
            ),
            Transaction(
                accession_number="0001234567-20-000004",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 11),
                filing_date=date(2020, 1, 13),
                transaction_code="P",
                shares=Decimal("3000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("66000"),
                direct_indirect="D",
            ),
        ]
        
        # Calculate distance matrix
        distance_matrix, zero_dollar_txns = calculate_temporal_distances(transactions)
        
        # Apply DBSCAN clustering
        clusters = detect_temporal_clusters(
            distance_matrix,
            zero_dollar_txns,
            eps_days=1,  # Same-day clustering
            min_samples=2
        )
        
        # Validate clustering results
        assert len(clusters) == 2, f"Should detect 2 clusters, got {len(clusters)}"
        
        for cluster in clusters:
            assert len(cluster.transactions) >= 2, "Each cluster should have at least 2 transactions"
            assert cluster.cluster_id, "Cluster should have unique ID"
            assert cluster.reporting_person_cik == "0001111111", "CIK should match"
            assert cluster.total_shares > 0, "Total shares should be positive"
            assert cluster.zero_dollar_count >= 2, "Should have zero-dollar transactions"
        
        print(f"  ✓ Detected {len(clusters)} clusters")
        print(f"  ✓ Cluster 1: {len(clusters[0].transactions)} transactions")
        print(f"  ✓ Cluster 2: {len(clusters[1].transactions)} transactions")
        print(f"  ✓ Cluster IDs generated: {[c.cluster_id[:8] for c in clusters]}")
        
        return True
    except Exception as e:
        print(f"✗ DBSCAN clustering failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cluster_anomaly_scoring():
    """Test composite anomaly scoring with all 4 components."""
    print("\nTesting cluster anomaly scoring...")
    
    try:
        from src.zero_dollar.models import Transaction
        from src.zero_dollar.modules import calculate_cluster_anomaly_score
        
        # Create high-risk cluster: same-day, large volume, all zero-dollar
        high_risk_transactions = [
            Transaction(
                accession_number=f"0001234567-20-00000{i}",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("50000"),  # Large volume
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("50000") * (i + 1),
                direct_indirect="D",
            )
            for i in range(3)
        ]
        
        # Calculate score
        score = calculate_cluster_anomaly_score(
            high_risk_transactions,
            issuer_historical_median=Decimal("10000")
        )
        
        # Validate score
        assert isinstance(score, Decimal), "Score should be Decimal type"
        assert Decimal('0.0') <= score <= Decimal('100.0'), "Score should be 0-100"
        assert score > Decimal('50.0'), f"High-risk cluster should score > 50, got {score}"
        
        print(f"  ✓ High-risk cluster score: {score}")
        
        # Create low-risk cluster: spread out, small volume
        # Use different months to avoid day overflow
        low_risk_dates = [
            (date(2020, 1, 15), date(2020, 1, 17)),
            (date(2020, 2, 15), date(2020, 2, 17)),
            (date(2020, 3, 15), date(2020, 3, 17)),
        ]
        low_risk_transactions = [
            Transaction(
                accession_number=f"0001234567-20-00010{i}",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=low_risk_dates[i][0],  # Spread over 60 days
                filing_date=low_risk_dates[i][1],
                transaction_code="P",
                shares=Decimal("1000"),  # Small volume
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("1000") * (i + 1),
                direct_indirect="D",
            )
            for i in range(3)
        ]
        
        low_score = calculate_cluster_anomaly_score(
            low_risk_transactions,
            issuer_historical_median=Decimal("10000")
        )
        
        assert low_score < score, "Low-risk should score lower than high-risk"
        
        print(f"  ✓ Low-risk cluster score: {low_score}")
        print(f"  ✓ Score differentiation validated (high > low)")
        
        return True
    except Exception as e:
        print(f"✗ Cluster scoring failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_escalation_thresholds():
    """Test escalation threshold mapping."""
    print("\nTesting escalation thresholds...")
    
    try:
        from src.zero_dollar.modules import determine_escalation_recommendation
        
        # Test threshold boundaries
        test_cases = [
            (Decimal('0.0'), 'NONE'),
            (Decimal('24.99'), 'NONE'),
            (Decimal('25.0'), 'ENHANCED_MONITORING'),
            (Decimal('49.99'), 'ENHANCED_MONITORING'),
            (Decimal('50.0'), 'INVESTIGATION'),
            (Decimal('74.99'), 'INVESTIGATION'),
            (Decimal('75.0'), 'REFERRAL'),
            (Decimal('100.0'), 'REFERRAL'),
        ]
        
        for score, expected_level in test_cases:
            result = determine_escalation_recommendation(score)
            assert result == expected_level, \
                f"Score {score} should map to {expected_level}, got {result}"
        
        print(f"  ✓ All threshold mappings validated")
        print(f"  ✓ NONE: 0.00 - 24.99")
        print(f"  ✓ ENHANCED_MONITORING: 25.00 - 49.99")
        print(f"  ✓ INVESTIGATION: 50.00 - 74.99")
        print(f"  ✓ REFERRAL: 75.00 - 100.00+")
        
        return True
    except Exception as e:
        print(f"✗ Escalation threshold test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_temporal_clustering_module():
    """Test complete TemporalClusteringModule workflow."""
    print("\nTesting TemporalClusteringModule...")
    
    try:
        from src.zero_dollar.models import Transaction
        from src.zero_dollar.modules import TemporalClusteringModule
        
        # Create test transactions
        transactions = [
            Transaction(
                accession_number=f"0001234567-20-00000{i}",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("50000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("50000") * (i + 1),
                direct_indirect="D",
            )
            for i in range(3)
        ]
        
        # Initialize module
        module = TemporalClusteringModule(config={
            'eps_days': 1,
            'min_samples': 2,
            'issuer_historical_median': Decimal('10000'),
        })
        
        # Run analysis
        output = asyncio.run(module.analyze(transactions))
        
        # Validate output
        assert output is not None, "Output should not be None"
        assert output.reporting_person_cik == "0001111111", "CIK should match"
        assert output.issuer_cik == "0000320187", "Issuer CIK should match"
        assert output.cluster_count >= 1, "Should detect at least 1 cluster"
        assert output.total_anomaly_score >= Decimal('0.0'), "Score should be non-negative"
        assert output.escalation_recommendation in [
            'NONE', 'ENHANCED_MONITORING', 'INVESTIGATION', 'REFERRAL'
        ], "Should have valid escalation level"
        assert len(output.regulatory_citations) > 0, "Should have regulatory citations"
        assert output.evidence_hash, "Should have evidence hash"
        
        print(f"  ✓ Module initialized successfully")
        print(f"  ✓ Analysis completed")
        print(f"  ✓ Clusters detected: {output.cluster_count}")
        print(f"  ✓ Total anomaly score: {output.total_anomaly_score}")
        print(f"  ✓ Escalation: {output.escalation_recommendation}")
        print(f"  ✓ Evidence hash: {output.evidence_hash[:16]}...")
        print(f"  ✓ Regulatory citations: {len(output.regulatory_citations)}")
        
        return True
    except Exception as e:
        print(f"✗ TemporalClusteringModule test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\nTesting edge cases...")
    
    try:
        from src.zero_dollar.models import Transaction
        from src.zero_dollar.modules import (
            TemporalClusteringModule,
            calculate_temporal_distances,
        )
        
        module = TemporalClusteringModule()
        
        # Test 1: Empty transaction list
        output = asyncio.run(module.analyze([]))
        assert output.cluster_count == 0, "Empty input should return 0 clusters"
        assert output.escalation_recommendation == 'NONE', "Should be NONE"
        print(f"  ✓ Empty transaction list handled")
        
        # Test 2: No zero-dollar transactions
        non_zero_transactions = [
            Transaction(
                accession_number="0001234567-20-000001",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("10000"),
                price_per_share=Decimal("50.00"),  # Non-zero price
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("50000"),
                direct_indirect="D",
            )
        ]
        output = asyncio.run(module.analyze(non_zero_transactions))
        assert output.cluster_count == 0, "Non-zero transactions should return 0 clusters"
        print(f"  ✓ Non-zero transactions filtered correctly")
        
        # Test 3: Single transaction
        single_txn = [
            Transaction(
                accession_number="0001234567-20-000001",
                issuer_cik="0000320187",
                issuer_name="NIKE, Inc.",
                reporting_person_cik="0001111111",
                reporting_person_name="John Smith",
                transaction_date=date(2020, 1, 1),
                filing_date=date(2020, 1, 3),
                transaction_code="P",
                shares=Decimal("10000"),
                price_per_share=Decimal("0.00"),
                transaction_acquired_disposed="A",
                shares_owned_following=Decimal("50000"),
                direct_indirect="D",
            )
        ]
        output = asyncio.run(module.analyze(single_txn))
        assert output.cluster_count == 0, "Single transaction should not form cluster"
        print(f"  ✓ Single transaction handled (no cluster formed)")
        
        return True
    except Exception as e:
        print(f"✗ Edge case test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all temporal clustering tests."""
    print("=" * 70)
    print("TEMPORAL CLUSTERING DETECTION MODULE TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Temporal Distance Calculation", test_temporal_distance_calculation),
        ("DBSCAN Clustering", test_dbscan_clustering),
        ("Cluster Anomaly Scoring", test_cluster_anomaly_scoring),
        ("Escalation Thresholds", test_escalation_thresholds),
        ("Temporal Clustering Module", test_temporal_clustering_module),
        ("Edge Cases", test_edge_cases),
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8} | {test_name}")
    
    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed ({100*passed//total}%)")
    print("=" * 70)
    
    return all(success for _, success in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
