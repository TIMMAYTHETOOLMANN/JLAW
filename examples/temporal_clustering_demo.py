#!/usr/bin/env python3
"""
Temporal Clustering Detection Demo
===================================

Demonstrates the Temporal Clustering Detection Module functionality
with realistic zero-dollar transaction scenarios.

This demo shows:
1. Same-day clustering detection (high-risk)
2. Multi-day clustering detection (moderate-risk)
3. Anomaly scoring with all 4 components
4. Escalation recommendations
5. Evidence hash generation
"""

import sys
import asyncio
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.zero_dollar.models import Transaction
from src.zero_dollar.modules import TemporalClusteringModule


def create_high_risk_scenario():
    """
    Create a high-risk scenario: Same-day zero-dollar transactions with large volume.
    
    Scenario: Executive transfers 150,000 shares via 3 same-day zero-dollar transactions
    to related entities (typical structuring pattern).
    """
    print("=" * 70)
    print("SCENARIO 1: HIGH RISK - Same-Day Clustered Structuring")
    print("=" * 70)
    print("\nExecutive: John Smith (CIK: 0001111111)")
    print("Issuer: ACME Corp (CIK: 0000999999)")
    print("Pattern: 3 same-day zero-dollar transactions totaling 150,000 shares")
    print("Date: January 15, 2020")
    print()
    
    transactions = [
        Transaction(
            accession_number="0001234567-20-000001",
            issuer_cik="0000999999",
            issuer_name="ACME Corp",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 1, 15),
            filing_date=date(2020, 1, 17),
            transaction_code="G",  # Gift
            shares=Decimal("50000"),
            price_per_share=Decimal("0.00"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("950000"),
            direct_indirect="D",
        ),
        Transaction(
            accession_number="0001234567-20-000002",
            issuer_cik="0000999999",
            issuer_name="ACME Corp",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 1, 15),
            filing_date=date(2020, 1, 17),
            transaction_code="G",
            shares=Decimal("50000"),
            price_per_share=Decimal("0.00"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("900000"),
            direct_indirect="D",
        ),
        Transaction(
            accession_number="0001234567-20-000003",
            issuer_cik="0000999999",
            issuer_name="ACME Corp",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 1, 15),
            filing_date=date(2020, 1, 17),
            transaction_code="G",
            shares=Decimal("50000"),
            price_per_share=Decimal("0.00"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("850000"),
            direct_indirect="D",
        ),
    ]
    
    return transactions


def create_moderate_risk_scenario():
    """
    Create a moderate-risk scenario: Weekly zero-dollar transactions.
    
    Scenario: Executive transfers shares weekly over 3 weeks, smaller volume.
    """
    print("=" * 70)
    print("SCENARIO 2: MODERATE RISK - Weekly Pattern")
    print("=" * 70)
    print("\nExecutive: Jane Doe (CIK: 0002222222)")
    print("Issuer: Beta Industries (CIK: 0000888888)")
    print("Pattern: 3 weekly zero-dollar transactions totaling 30,000 shares")
    print("Dates: January 8, 15, 22, 2020")
    print()
    
    transactions = [
        Transaction(
            accession_number="0002345678-20-000001",
            issuer_cik="0000888888",
            issuer_name="Beta Industries",
            reporting_person_cik="0002222222",
            reporting_person_name="Jane Doe",
            transaction_date=date(2020, 1, 8),
            filing_date=date(2020, 1, 10),
            transaction_code="G",
            shares=Decimal("10000"),
            price_per_share=Decimal("0.00"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("290000"),
            direct_indirect="D",
        ),
        Transaction(
            accession_number="0002345678-20-000002",
            issuer_cik="0000888888",
            issuer_name="Beta Industries",
            reporting_person_cik="0002222222",
            reporting_person_name="Jane Doe",
            transaction_date=date(2020, 1, 15),
            filing_date=date(2020, 1, 17),
            transaction_code="G",
            shares=Decimal("10000"),
            price_per_share=Decimal("0.00"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("280000"),
            direct_indirect="D",
        ),
        Transaction(
            accession_number="0002345678-20-000003",
            issuer_cik="0000888888",
            issuer_name="Beta Industries",
            reporting_person_cik="0002222222",
            reporting_person_name="Jane Doe",
            transaction_date=date(2020, 1, 22),
            filing_date=date(2020, 1, 24),
            transaction_code="G",
            shares=Decimal("10000"),
            price_per_share=Decimal("0.00"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("270000"),
            direct_indirect="D",
        ),
    ]
    
    return transactions


async def analyze_scenario(scenario_name: str, transactions: list):
    """Analyze a scenario and print detailed results."""
    
    # Initialize module with default configuration
    module = TemporalClusteringModule(config={
        'eps_days': 1,  # Same-day clustering
        'min_samples': 2,
        'issuer_historical_median': Decimal('10000'),
    })
    
    # Run analysis
    print("Running temporal clustering analysis...")
    output = await module.analyze(transactions)
    
    # Print results
    print("\n" + "-" * 70)
    print("ANALYSIS RESULTS")
    print("-" * 70)
    print(f"\nClusters Detected: {output.cluster_count}")
    print(f"Total Transactions in Clusters: {output.total_transactions_in_clusters}")
    print(f"\nTotal Anomaly Score: {output.total_anomaly_score}")
    print(f"Escalation Recommendation: {output.escalation_recommendation}")
    
    if output.escalation_recommendation == 'REFERRAL':
        print("  ⚠️  AUTOMATIC ESCALATION TO ENFORCEMENT QUEUE")
    elif output.escalation_recommendation == 'INVESTIGATION':
        print("  ⚠️  MANUAL ANALYST REVIEW REQUIRED WITHIN 48 HOURS")
    elif output.escalation_recommendation == 'ENHANCED_MONITORING':
        print("  ⚠️  ADD TO WATCHLIST - QUARTERLY RE-ANALYSIS")
    else:
        print("  ✓  STANDARD ARCHIVAL - NO ESCALATION")
    
    print(f"\nEvidence Hash: {output.evidence_hash}")
    print(f"Analysis Period: {output.analysis_period[0]} to {output.analysis_period[1]}")
    
    # Print cluster details
    for i, cluster in enumerate(output.clusters_detected, 1):
        print(f"\n--- Cluster {i} Details ---")
        print(f"  Cluster ID: {cluster.cluster_id}")
        print(f"  Transactions: {len(cluster.transactions)}")
        print(f"  Date Range: {cluster.start_date} to {cluster.end_date}")
        print(f"  Span: {cluster.cluster_span_days} days")
        print(f"  Total Shares: {cluster.total_shares:,}")
        print(f"  Zero-Dollar Count: {cluster.zero_dollar_count}")
        print(f"  Zero-Dollar Ratio: {cluster.zero_dollar_ratio:.1%}")
        print(f"  Cluster Anomaly Score: {cluster.cluster_score:.2f}")
    
    # Print regulatory citations
    print("\nApplicable Regulatory Citations:")
    for citation in output.regulatory_citations:
        print(f"  • {citation}")
    
    print("\n" + "=" * 70)
    print()


async def main():
    """Run demonstration of temporal clustering detection."""
    
    print("\n")
    print("*" * 70)
    print("TEMPORAL CLUSTERING DETECTION MODULE DEMONSTRATION")
    print("JLAW Zero-Dollar Transaction Forensic Analysis")
    print("*" * 70)
    print("\n")
    
    # Scenario 1: High Risk
    high_risk_txns = create_high_risk_scenario()
    await analyze_scenario("High Risk", high_risk_txns)
    
    # Wait for user to review
    print("\nPress Enter to continue to next scenario...")
    input()
    
    # Scenario 2: Moderate Risk
    moderate_risk_txns = create_moderate_risk_scenario()
    await analyze_scenario("Moderate Risk", moderate_risk_txns)
    
    # Summary
    print("\n" + "*" * 70)
    print("DEMONSTRATION COMPLETE")
    print("*" * 70)
    print("\nKey Takeaways:")
    print("  1. Same-day clustering (Scenario 1) → REFERRAL (Score: ~85)")
    print("  2. Weekly pattern (Scenario 2) → Lower risk (Score: ~30-50)")
    print("  3. Anomaly scores incorporate 4 components: TDS, MCS, CHS, ZCS")
    print("  4. Escalation thresholds automatically route cases")
    print("  5. Evidence hashes provide tamper-evident audit trail")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
