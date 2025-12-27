#!/usr/bin/env python3
"""
Event Proximity Analysis Module Demo
=====================================

Demonstrates the complete functionality of the Event Proximity Analysis Module
for detecting MNPI exploitation patterns in zero-dollar transactions.

Per Section 6 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.
"""

import sys
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.zero_dollar.models import Transaction, MaterialEvent
from src.zero_dollar.modules import (
    EventProximityModule,
    FORM_8K_EVENTS,
    EARNINGS_EVENTS,
    calculate_mnpi_score,
    determine_mnpi_severity,
)


def demo_material_event_taxonomy():
    """Demonstrate Material Event Taxonomy."""
    print("\n" + "=" * 70)
    print("DEMO 1: Material Event Taxonomy")
    print("=" * 70)
    
    print(f"\nForm 8-K Event Categories: {len(FORM_8K_EVENTS)} types")
    print("\nCRITICAL Sensitivity Events:")
    for item, category in FORM_8K_EVENTS.items():
        if category.mnpi_sensitivity == 'CRITICAL':
            print(f"  • Item {item}: {category.description}")
            print(f"    Lookback: {category.lookback_days} days, "
                  f"Lookforward: {category.lookforward_days} days")
    
    print(f"\nEarnings Event Categories: {len(EARNINGS_EVENTS)} types")
    for key, category in EARNINGS_EVENTS.items():
        print(f"  • {category.description} ({category.mnpi_sensitivity})")
        print(f"    Lookback: {category.lookback_days} days, "
              f"Lookforward: {category.lookforward_days} days")


def demo_mnpi_scoring():
    """Demonstrate MNPI Scoring Algorithm."""
    print("\n" + "=" * 70)
    print("DEMO 2: MNPI Scoring Algorithm")
    print("=" * 70)
    
    event = MaterialEvent(
        event_id='DEMO-001',
        issuer_cik='0000320187',
        issuer_name='NIKE, Inc.',
        event_type='2.02',
        event_date=date(2020, 1, 15),
        event_description='Quarterly Earnings Release',
        is_price_sensitive=True,
    )
    
    print(f"\nMaterial Event: {event.event_description}")
    print(f"Event Date: {event.event_date}")
    print(f"Event Type: Form 8-K Item {event.event_type}")
    
    print("\nMNPI Scores by Temporal Distance (CRITICAL event, PRE proximity):")
    for days in [1, 3, 7, 14, 21]:
        score = calculate_mnpi_score(event, days, 'PRE', 'CRITICAL')
        severity = determine_mnpi_severity(score)
        print(f"  {days:2d} days before: {score:.3f} ({severity})")
    
    print("\nDirection Factor Comparison (3 days from event, CRITICAL):")
    score_pre = calculate_mnpi_score(event, 3, 'PRE', 'CRITICAL')
    score_post = calculate_mnpi_score(event, 3, 'POST', 'CRITICAL')
    print(f"  PRE_EVENT:  {score_pre:.3f} (higher suspicion)")
    print(f"  POST_EVENT: {score_post:.3f} (lower suspicion)")
    print(f"  Ratio: {(score_pre / score_post):.1f}x more suspicious pre-event")
    
    print("\nSensitivity Level Comparison (3 days PRE):")
    for sensitivity in ['CRITICAL', 'HIGH', 'MODERATE', 'LOW']:
        score = calculate_mnpi_score(event, 3, 'PRE', sensitivity)
        print(f"  {sensitivity:10s}: {score:.3f}")


def demo_event_proximity_detection():
    """Demonstrate Event Proximity Detection."""
    print("\n" + "=" * 70)
    print("DEMO 3: Event Proximity Detection")
    print("=" * 70)
    
    # Create zero-dollar transaction
    txn = Transaction(
        accession_number='0000320187-20-000001',
        issuer_cik='0000320187',
        issuer_name='NIKE, Inc.',
        reporting_person_cik='0001234567',
        reporting_person_name='John Donahoe',
        transaction_date=date(2020, 1, 10),
        filing_date=date(2020, 1, 12),
        transaction_code='G',  # Gift
        shares=Decimal('500000'),
        price_per_share=None,  # Zero-dollar
        transaction_acquired_disposed='D',
        shares_owned_following=Decimal('2500000'),
        direct_indirect='I',
        nature_of_ownership='By Donahoe Family Trust',
    )
    
    # Create material event
    event = MaterialEvent(
        event_id='0000320187-20-8K-001',
        issuer_cik='0000320187',
        issuer_name='NIKE, Inc.',
        event_type='8K-2.02',
        event_date=date(2020, 1, 15),
        event_description='Form 8-K Item 2.02 - Quarterly Earnings Release',
        stock_price_impact=-8.5,
        is_price_sensitive=True,
        sec_filing_url='https://www.sec.gov/...',
    )
    
    print("\nZero-Dollar Transaction:")
    print(f"  Reporting Person: {txn.reporting_person_name}")
    print(f"  Transaction Date: {txn.transaction_date}")
    print(f"  Transaction Code: {txn.transaction_code} (Gift)")
    print(f"  Shares: {txn.shares:,}")
    print(f"  Price: $0.00 (ZERO-DOLLAR)")
    print(f"  Ownership: {txn.nature_of_ownership}")
    
    print(f"\nMaterial Event:")
    print(f"  Event Type: {event.event_description}")
    print(f"  Event Date: {event.event_date}")
    print(f"  Stock Impact: {event.stock_price_impact}%")
    
    # Detect proximity
    module = EventProximityModule()
    flags = module.detect_event_proximity(txn, [event])
    
    print(f"\n🚩 PROXIMITY FLAGS DETECTED: {len(flags)}")
    
    for flag in flags:
        print(f"\nFlag ID: {flag.flag_id}")
        print(f"Proximity Type: {flag.proximity_type}")
        print(f"Days Delta: {flag.days_delta} days before event")
        print(f"MNPI Inference Score: {flag.mnpi_inference_score:.3f} "
              f"({determine_mnpi_severity(flag.mnpi_inference_score)})")
        print(f"\nNarrative:")
        print(f"  {flag.narrative}")
        print(f"\nRegulatory Citations ({len(flag.regulatory_citations)}):")
        for citation in flag.regulatory_citations:
            print(f"  • {citation}")
        print(f"\nEvidence Hash: {flag.evidence_hash[:16]}...{flag.evidence_hash[-16:]}")


def demo_multiple_events():
    """Demonstrate analysis with multiple events."""
    print("\n" + "=" * 70)
    print("DEMO 4: Multiple Event Proximity Analysis")
    print("=" * 70)
    
    # Create multiple zero-dollar transactions
    transactions = [
        Transaction(
            accession_number=f'0000320187-20-00000{i}',
            issuer_cik='0000320187',
            issuer_name='NIKE, Inc.',
            reporting_person_cik='0001234567',
            reporting_person_name='John Donahoe',
            transaction_date=date(2020, 1, 5 + i),
            filing_date=date(2020, 1, 5 + i),
            transaction_code='G',
            shares=Decimal('100000'),
            price_per_share=None,
            transaction_acquired_disposed='D',
            shares_owned_following=Decimal('2000000'),
            direct_indirect='I',
        )
        for i in range(3)
    ]
    
    # Create multiple events
    events = [
        MaterialEvent(
            event_id='EVT-001',
            issuer_cik='0000320187',
            issuer_name='NIKE, Inc.',
            event_type='8K-2.02',
            event_date=date(2020, 1, 10),
            event_description='Earnings Release',
            is_price_sensitive=True,
        ),
        MaterialEvent(
            event_id='EVT-002',
            issuer_cik='0000320187',
            issuer_name='NIKE, Inc.',
            event_type='8K-5.02',
            event_date=date(2020, 1, 15),
            event_description='Officer Departure',
            is_price_sensitive=True,
        ),
    ]
    
    module = EventProximityModule()
    
    print(f"\nAnalyzing {len(transactions)} zero-dollar transactions")
    print(f"Against {len(events)} material events")
    
    all_flags = []
    for txn in transactions:
        flags = module.detect_event_proximity(txn, events)
        all_flags.extend(flags)
    
    print(f"\nTotal Proximity Flags: {all_flags.__len__()}")
    
    # Aggregate statistics
    high_risk = sum(1 for f in all_flags if f.mnpi_inference_score >= Decimal('0.5'))
    critical = sum(1 for f in all_flags 
                  if determine_mnpi_severity(f.mnpi_inference_score) == 'CRITICAL')
    
    print(f"High-Risk Flags (score >= 0.5): {high_risk}")
    print(f"Critical Severity: {critical}")
    
    print("\nFlag Distribution by Proximity Type:")
    pre_count = sum(1 for f in all_flags if f.proximity_type == 'PRE_EVENT')
    post_count = sum(1 for f in all_flags if f.proximity_type == 'POST_EVENT')
    print(f"  PRE_EVENT:  {pre_count}")
    print(f"  POST_EVENT: {post_count}")


def run_all_demos():
    """Run all demonstration functions."""
    print("\n" + "=" * 70)
    print("EVENT PROXIMITY ANALYSIS MODULE DEMONSTRATION")
    print("JLAW Zero-Dollar Transaction Forensic Specification v1.0")
    print("Section 6: Event Proximity Analysis Module")
    print("=" * 70)
    
    demo_material_event_taxonomy()
    demo_mnpi_scoring()
    demo_event_proximity_detection()
    demo_multiple_events()
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  ✓ 16 Form 8-K event categories with MNPI sensitivity levels")
    print("  ✓ 5 Earnings event categories")
    print("  ✓ Exponential decay MNPI scoring (λ = 0.1)")
    print("  ✓ Direction factor (PRE=1.0, POST=0.25)")
    print("  ✓ Sensitivity mapping (CRITICAL=1.0, HIGH=0.75, MODERATE=0.5, LOW=0.25)")
    print("  ✓ Event proximity detection with temporal windows")
    print("  ✓ Regulatory citations per event type")
    print("  ✓ SHA-256 evidence hash computation")
    print("  ✓ Human-readable narratives")
    print("\n")


if __name__ == '__main__':
    run_all_demos()
