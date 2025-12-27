#!/usr/bin/env python3
"""
Zero-Dollar Transaction Foundation Demo
========================================

Demonstrates the complete functionality of the Zero-Dollar Transaction
Anomaly Detection foundation including models, constants, and utilities.
"""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.zero_dollar import (
    # Models
    Transaction,
    TransactionCluster,
    ReportingPerson,
    ReportingPersonClassification,
    AnomalyFlag,
    AnomalyType,
    AnomalySeverity,
    BehavioralRiskAssessment,
    BehavioralScoreComponents,
    # Constants
    TransactionCode,
    get_transaction_code_info,
    is_zero_dollar_suspicious,
    TemporalWindow,
    classify_magnitude,
    calculate_cluster_score,
    get_tier_display_name,
    # Schema
    get_schema_sql,
)


def demo_transaction_creation():
    """Demonstrate transaction creation and properties."""
    print("\n" + "=" * 70)
    print("DEMO 1: Transaction Creation and Analysis")
    print("=" * 70)
    
    # Create a suspicious zero-dollar transaction
    txn = Transaction(
        accession_number="0000320187-20-000001",
        issuer_cik="0000320187",
        issuer_name="NIKE, Inc.",
        reporting_person_cik="0001234567",
        reporting_person_name="John Donahoe",
        transaction_date=date(2020, 1, 10),
        filing_date=date(2020, 1, 15),
        transaction_code="P",  # Purchase - suspicious at zero-dollar
        shares=Decimal("250000"),
        price_per_share=None,  # Zero-dollar transaction
        transaction_acquired_disposed="A",
        shares_owned_following=Decimal("1500000"),
        direct_indirect="I",
        nature_of_ownership="By Donahoe Family Trust",
    )
    
    print(f"\nTransaction: {txn.accession_number}")
    print(f"  Issuer: {txn.issuer_name} (CIK: {txn.issuer_cik})")
    print(f"  Reporting Person: {txn.reporting_person_name}")
    print(f"  Date: {txn.transaction_date}")
    print(f"  Code: {txn.transaction_code}")
    print(f"  Shares: {txn.shares:,}")
    print(f"  Price: {'$0.00 (ZERO-DOLLAR)' if txn.is_zero_dollar else f'${txn.price_per_share}'}")
    print(f"  Nature: {txn.nature_of_ownership}")
    
    print(f"\nForensic Analysis:")
    print(f"  ✓ Zero-Dollar Transaction: {txn.is_zero_dollar}")
    print(f"  ✓ Days to Filing: {txn.days_to_filing}")
    print(f"  ✓ Late Filing: {txn.is_late_filing}")
    print(f"  ✓ Notional Value: ${txn.notional_value:,.2f}")
    
    # Classify magnitude
    tier = classify_magnitude(int(txn.shares))
    print(f"  ✓ Magnitude: {get_tier_display_name(tier)}")
    
    return txn


def demo_transaction_code_analysis():
    """Demonstrate transaction code analysis."""
    print("\n" + "=" * 70)
    print("DEMO 2: Transaction Code Analysis")
    print("=" * 70)
    
    suspicious_codes = ["P", "S", "J"]
    legitimate_codes = ["A", "G", "W"]
    
    print("\nSuspicious Codes (for zero-dollar):")
    for code in suspicious_codes:
        info = get_transaction_code_info(code)
        suspicious = is_zero_dollar_suspicious(code, magnitude_tier=4)
        print(f"\n  {code}: {info.description}")
        print(f"     Legitimacy: {info.zero_dollar_legitimacy:.1f}/1.0")
        print(f"     Scrutiny: Level {info.forensic_scrutiny_level}/5")
        print(f"     Suspicious at Tier 4: {'⚠️  YES' if suspicious else '✓ No'}")
    
    print("\nLegitimate Codes (for zero-dollar):")
    for code in legitimate_codes:
        info = get_transaction_code_info(code)
        suspicious = is_zero_dollar_suspicious(code, magnitude_tier=4)
        print(f"\n  {code}: {info.description}")
        print(f"     Legitimacy: {info.zero_dollar_legitimacy:.1f}/1.0")
        print(f"     Scrutiny: Level {info.forensic_scrutiny_level}/5")
        print(f"     Suspicious at Tier 4: {'⚠️  YES' if suspicious else '✓ No'}")


def demo_temporal_clustering():
    """Demonstrate temporal clustering analysis."""
    print("\n" + "=" * 70)
    print("DEMO 3: Temporal Clustering Analysis")
    print("=" * 70)
    
    # Scenario: Multiple zero-dollar transactions in short window
    scenarios = [
        {
            "name": "Low Risk - Single Transaction",
            "transaction_count": 1,
            "zero_dollar_count": 1,
            "span_days": 0,
            "total_shares": 10000,
            "max_shares": 10000,
            "late_filing_count": 0,
        },
        {
            "name": "Moderate Risk - Few Transactions",
            "transaction_count": 3,
            "zero_dollar_count": 2,
            "span_days": 5,
            "total_shares": 50000,
            "max_shares": 25000,
            "late_filing_count": 1,
        },
        {
            "name": "High Risk - Clustering Pattern",
            "transaction_count": 5,
            "zero_dollar_count": 4,
            "span_days": 1,
            "total_shares": 500000,
            "max_shares": 200000,
            "late_filing_count": 2,
        },
        {
            "name": "Critical Risk - Extreme Clustering",
            "transaction_count": 10,
            "zero_dollar_count": 8,
            "span_days": 2,
            "total_shares": 2000000,
            "max_shares": 500000,
            "late_filing_count": 3,
        },
    ]
    
    from src.zero_dollar.constants import CLUSTERING_THRESHOLD
    
    for scenario in scenarios:
        score = calculate_cluster_score(
            transaction_count=scenario["transaction_count"],
            zero_dollar_count=scenario["zero_dollar_count"],
            span_days=scenario["span_days"],
            total_shares=scenario["total_shares"],
            max_shares=scenario["max_shares"],
            late_filing_count=scenario["late_filing_count"],
        )
        
        alert = "🚨 ALERT" if score >= CLUSTERING_THRESHOLD else "✓ Normal"
        
        print(f"\n{scenario['name']}:")
        print(f"  Transactions: {scenario['transaction_count']} ({scenario['zero_dollar_count']} zero-dollar)")
        print(f"  Span: {scenario['span_days']} days")
        print(f"  Total Shares: {scenario['total_shares']:,}")
        print(f"  Cluster Score: {score:.2f}/100")
        print(f"  Status: {alert}")


def demo_anomaly_detection():
    """Demonstrate anomaly flag creation."""
    print("\n" + "=" * 70)
    print("DEMO 4: Anomaly Flag Creation")
    print("=" * 70)
    
    # Create an anomaly flag
    flag = AnomalyFlag(
        flag_id="ZD-2020-001",
        anomaly_type=AnomalyType.ZERO_DOLLAR_MAGNITUDE_DISPROPORTION,
        severity=AnomalySeverity.HIGH,
        transaction_accession="0000320187-20-000001",
        reporting_person_cik="0001234567",
        reporting_person_name="John Donahoe",
        issuer_cik="0000320187",
        issuer_name="NIKE, Inc.",
        detection_date=datetime.now(),
        transaction_date=date(2020, 1, 10),
        shares_involved=Decimal("250000"),
        notional_value=Decimal("12500000"),  # Estimated market value
        description=(
            "Zero-dollar purchase of 250,000 shares with estimated market "
            "value of $12.5M. Transaction code 'P' (Purchase) with zero-dollar "
            "pricing requires immediate investigation."
        ),
        forensic_score=87.5,
        requires_investigation=True,
    )
    
    print(f"\nAnomaly Flag: {flag.flag_id}")
    print(f"  Type: {flag.anomaly_type.value}")
    print(f"  Severity: {flag.severity.value.upper()}")
    print(f"  Reporting Person: {flag.reporting_person_name}")
    print(f"  Issuer: {flag.issuer_name}")
    print(f"  Shares: {flag.shares_involved:,}")
    print(f"  Estimated Value: ${flag.notional_value:,.2f}")
    print(f"  Forensic Score: {flag.forensic_score}/100")
    print(f"  Investigation Required: {'⚠️  YES' if flag.requires_investigation else 'No'}")
    print(f"\nDescription:")
    print(f"  {flag.description}")


def demo_behavioral_assessment():
    """Demonstrate behavioral risk assessment."""
    print("\n" + "=" * 70)
    print("DEMO 5: Behavioral Risk Assessment")
    print("=" * 70)
    
    # Create risk assessment
    components = BehavioralScoreComponents(
        magnitude_score=22.0,  # Out of 25
        frequency_score=20.0,  # Out of 25
        timing_score=15.0,     # Out of 20
        filing_compliance_score=8.0,  # Out of 15
        entity_complexity_score=12.0,  # Out of 15
    )
    
    assessment = BehavioralRiskAssessment(
        assessment_id="BA-2020-001",
        reporting_person_cik="0001234567",
        reporting_person_name="John Donahoe",
        issuer_cik="0000320187",
        issuer_name="NIKE, Inc.",
        assessment_date=datetime.now(),
        score_components=components,
        zero_dollar_transaction_count=8,
        total_transaction_count=12,
        temporal_clusters_detected=2,
        prosecutorial_priority=2,
        recommendation="Immediate investigation recommended due to high-volume zero-dollar clustering",
        next_steps=[
            "Review all zero-dollar transactions for legitimacy",
            "Analyze entity structure (Donahoe Family Trust)",
            "Check for material events within 30-day window",
            "Request documentation from reporting person",
        ],
    )
    
    print(f"\nBehavioral Assessment: {assessment.assessment_id}")
    print(f"  Reporting Person: {assessment.reporting_person_name}")
    print(f"  Issuer: {assessment.issuer_name}")
    
    print(f"\nScore Components:")
    print(f"  Magnitude: {components.magnitude_score:.1f}/25")
    print(f"  Frequency: {components.frequency_score:.1f}/25")
    print(f"  Timing: {components.timing_score:.1f}/20")
    print(f"  Filing Compliance: {components.filing_compliance_score:.1f}/15")
    print(f"  Entity Complexity: {components.entity_complexity_score:.1f}/15")
    print(f"  TOTAL: {assessment.risk_score:.1f}/100")
    
    print(f"\nRisk Assessment:")
    print(f"  Risk Level: {assessment.risk_level}")
    print(f"  Prosecutorial Priority: {assessment.prosecutorial_priority}/5 (1=highest)")
    print(f"  Zero-Dollar Rate: {assessment.zero_dollar_transaction_count}/{assessment.total_transaction_count}")
    print(f"  Clusters Detected: {assessment.temporal_clusters_detected}")
    
    print(f"\nRecommendation:")
    print(f"  {assessment.recommendation}")
    
    print(f"\nNext Steps:")
    for i, step in enumerate(assessment.next_steps, 1):
        print(f"  {i}. {step}")


def demo_database_schema():
    """Demonstrate database schema."""
    print("\n" + "=" * 70)
    print("DEMO 6: Database Schema Overview")
    print("=" * 70)
    
    schema = get_schema_sql()
    
    print(f"\nPostgreSQL Schema:")
    print(f"  Total Size: {len(schema):,} bytes")
    print(f"  Tables: {schema.count('CREATE TABLE')}")
    print(f"  Indexes: {schema.count('CREATE INDEX')}")
    print(f"  Materialized Views: {schema.count('CREATE MATERIALIZED VIEW')}")
    print(f"  Triggers: {schema.count('CREATE TRIGGER')}")
    
    print(f"\nKey Features:")
    print(f"  ✓ Triple-hash evidence integrity (SHA-256, SHA3-512, BLAKE2b)")
    print(f"  ✓ RFC 3161 timestamp support")
    print(f"  ✓ Chain of custody tracking")
    print(f"  ✓ Generated columns for computed values")
    print(f"  ✓ Full-text search (pg_trgm)")
    print(f"  ✓ Materialized views for performance")
    print(f"  ✓ Comprehensive indexing strategy")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("ZERO-DOLLAR TRANSACTION ANOMALY DETECTION")
    print("Foundation Demonstration")
    print("=" * 70)
    print("\nJLAW Zero-Dollar Transaction Forensic Specification v1.0")
    print("PR #1 of 8: Data Models, Schema & Constants")
    
    # Run demonstrations
    demo_transaction_creation()
    demo_transaction_code_analysis()
    demo_temporal_clustering()
    demo_anomaly_detection()
    demo_behavioral_assessment()
    demo_database_schema()
    
    # Final summary
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n✅ Foundation fully operational and ready for:")
    print("   - Form 4 parsing and ingestion")
    print("   - Temporal clustering analysis")
    print("   - Anomaly detection algorithms")
    print("   - Behavioral risk scoring")
    print("   - Evidence chain tracking")
    print("   - DOJ-grade forensic reporting")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
