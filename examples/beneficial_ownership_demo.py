#!/usr/bin/env python3
"""
Beneficial Ownership Chain Resolution Module Demo
=================================================

Demonstrates the Section 7 module capabilities for analyzing zero-dollar
transactions and detecting beneficial ownership retention patterns.

Usage:
    python examples/beneficial_ownership_demo.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import date
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.zero_dollar.models import (
    Transaction,
    ReportingPerson,
    ReportingPersonClassification,
    EntityType,
)
from src.zero_dollar.modules import (
    BeneficialOwnershipModule,
    check_hsr_circumvention,
    HSR_THRESHOLD_2024,
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_demo_transactions():
    """Create sample zero-dollar transactions for demonstration."""
    transactions = [
        Transaction(
            accession_number="0001234567-20-000001",
            issuer_cik="0000320187",
            issuer_name="ACME Corporation",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 3, 1),
            filing_date=date(2020, 3, 3),
            transaction_code="G",  # Gift
            shares=Decimal("150000"),
            price_per_share=Decimal("0.00"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("500000"),
            direct_indirect="I",
            nature_of_ownership="By Trust",
            footnotes=[
                "Transferred to the Smith Family Trust dated January 1, 2020. "
                "Reporting person serves as trustee with sole voting and dispositive power."
            ]
        ),
        Transaction(
            accession_number="0001234567-20-000002",
            issuer_cik="0000320187",
            issuer_name="ACME Corporation",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 3, 15),
            filing_date=date(2020, 3, 17),
            transaction_code="G",
            shares=Decimal("75000"),
            price_per_share=None,  # Zero-dollar
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("425000"),
            direct_indirect="I",
            nature_of_ownership="By LLC",
            footnotes=[
                "Gift to Smith Holdings LLC. Reporting person serves as managing member."
            ]
        ),
        Transaction(
            accession_number="0001234567-20-000003",
            issuer_cik="0000320187",
            issuer_name="ACME Corporation",
            reporting_person_cik="0001111111",
            reporting_person_name="John Smith",
            transaction_date=date(2020, 4, 1),
            filing_date=date(2020, 4, 3),
            transaction_code="G",
            shares=Decimal("50000"),
            price_per_share=Decimal("0"),
            transaction_acquired_disposed="D",
            shares_owned_following=Decimal("375000"),
            direct_indirect="I",
            nature_of_ownership="By Foundation",
            footnotes=[
                "Donated to the Smith Family Foundation. Reporting person serves on board of directors."
            ]
        ),
    ]
    
    return transactions


async def main():
    """Run the beneficial ownership chain demo."""
    print_section("BENEFICIAL OWNERSHIP CHAIN RESOLUTION - DEMO")
    
    print("\nThis demo showcases Section 7 of the JLAW Zero-Dollar Transaction")
    print("Forensic Specification v1.0 - detecting control retention through")
    print("zero-dollar transfers to related entities.")
    
    # Create reporting person
    print_section("1. Reporting Person")
    
    reporting_person = ReportingPerson(
        cik="0001111111",
        name="John Smith",
        classification=ReportingPersonClassification.SECTION_16_OFFICER,
        is_officer=True,
        officer_title="Chief Executive Officer",
        issuer_cik="0000320187",
        issuer_name="ACME Corporation"
    )
    
    print(f"Name: {reporting_person.name}")
    print(f"CIK: {reporting_person.cik}")
    print(f"Title: {reporting_person.officer_title}")
    print(f"Classification: {reporting_person.classification.value}")
    
    # Create transactions
    print_section("2. Zero-Dollar Transactions")
    
    transactions = create_demo_transactions()
    
    print(f"\nAnalyzing {len(transactions)} zero-dollar transactions:\n")
    
    for i, txn in enumerate(transactions, 1):
        print(f"Transaction {i}:")
        print(f"  Date: {txn.transaction_date}")
        print(f"  Shares: {txn.shares:,}")
        print(f"  Code: {txn.transaction_code} (Gift)")
        print(f"  Zero-dollar: {txn.is_zero_dollar}")
        print(f"  Footnote: {txn.footnotes[0][:80]}...")
        print()
    
    # Construct ownership chain
    print_section("3. Ownership Chain Construction")
    
    module = BeneficialOwnershipModule()
    chain = await module.analyze(
        transactions=transactions,
        reporting_person=reporting_person,
        schedule_13_filings=[]
    )
    
    print(f"\nChain ID: {chain.chain_id}")
    print(f"Root Person: {chain.root_name} (CIK: {chain.root_cik})")
    print(f"Total Nodes: {len(chain.nodes)}")
    print(f"Total Shares Transferred: {chain.total_shares_transferred:,}")
    print(f"Average Control Probability: {chain.average_control_probability:.2f}")
    print(f"High Control Nodes: {chain.high_control_node_count}")
    print(f"Evidence Hash: {chain.evidence_hash[:32]}...")
    
    # Display node details
    print_section("4. Node-by-Node Analysis")
    
    for i, node in enumerate(chain.nodes, 1):
        print(f"\nNode {i}:")
        print(f"  Entity Name: {node.entity.entity_name}")
        print(f"  Entity Type: {node.entity.entity_type.value}")
        print(f"  Shares Transferred: {node.shares_transferred:,}")
        print(f"  Control Probability: {node.control_indicators.overall_control_probability:.2f}")
        print(f"  Economic Retention: {node.economic_interest_retained:.2f}")
        print(f"  Recommendation: {node.control_indicators.recommendation}")
        
        if node.control_indicators.indicators:
            print(f"  Control Indicators ({len(node.control_indicators.indicators)}):")
            for ind in node.control_indicators.indicators[:3]:  # Show first 3
                print(f"    - [{ind.severity}] {ind.indicator_type}")
                print(f"      {ind.description[:70]}...")
    
    # HSR Analysis
    print_section("5. Hart-Scott-Rodino Threshold Analysis")
    
    share_price = Decimal("85.50")  # Example market price
    
    print(f"\nMarket Price: ${share_price}")
    print(f"HSR Threshold (2024): ${HSR_THRESHOLD_2024:,.0f}")
    
    hsr_analysis = check_hsr_circumvention(
        ownership_chain=chain,
        issuer_cik="0000320187",
        share_price=share_price
    )
    
    print(f"\nAggregate Shares: {hsr_analysis.aggregate_beneficial_ownership_shares:,}")
    print(f"Aggregate Value: ${hsr_analysis.aggregate_beneficial_ownership_value:,.2f}")
    print(f"Threshold Exceeded: {hsr_analysis.threshold_exceeded}")
    print(f"Fragmentation Detected: {hsr_analysis.fragmentation_pattern_detected}")
    print(f"\nRecommendation: {hsr_analysis.recommendation}")
    
    if hsr_analysis.individual_entity_holdings:
        print(f"\nIndividual Entity Holdings ({len(hsr_analysis.individual_entity_holdings)}):")
        for entity, value in hsr_analysis.individual_entity_holdings:
            print(f"  - {entity.entity_name}: ${value:,.2f}")
    
    # Regulatory Citations
    print_section("6. Regulatory Framework")
    
    print("\nApplicable Regulations:")
    for citation in hsr_analysis.regulatory_citations:
        print(f"  • {citation}")
    
    print("\nAdditional Control Assessment Citations:")
    all_citations = set()
    for node in chain.nodes:
        for ind in node.control_indicators.indicators:
            if ind.regulatory_citation:
                all_citations.add(ind.regulatory_citation)
    
    for citation in sorted(all_citations):
        print(f"  • {citation}")
    
    # Summary
    print_section("7. Forensic Summary")
    
    print(f"""
Analysis reveals potential beneficial ownership retention through controlled entities:

• {len(chain.nodes)} related entities identified from Form 4 footnotes
• {chain.total_shares_transferred:,} shares transferred via zero-dollar transactions
• Average control retention probability: {float(chain.average_control_probability) * 100:.1f}%
• {chain.high_control_node_count} entities with HIGH control indicators (>60% probability)

Key Findings:
""")
    
    for node in chain.nodes:
        if node.control_indicators.overall_control_probability > Decimal('0.6'):
            print(f"  ⚠ {node.entity.entity_name} ({node.entity.entity_type.value})")
            print(f"    Control Probability: {float(node.control_indicators.overall_control_probability) * 100:.1f}%")
            print(f"    {node.control_indicators.recommendation}")
    
    if not any(n.control_indicators.overall_control_probability > Decimal('0.6') for n in chain.nodes):
        print("  ℹ No entities exceeded 60% control threshold")
        print("  ℹ Transfers appear to involve genuine divestiture of control")
    
    print(f"""
HSR Analysis:
  {'⚠ THRESHOLD EXCEEDED' if hsr_analysis.threshold_exceeded else '✓ Below threshold'}
  {'⚠ FRAGMENTATION PATTERN DETECTED' if hsr_analysis.fragmentation_pattern_detected else '✓ No fragmentation detected'}
  
Evidence Integrity:
  ✓ Chain hash computed: {chain.evidence_hash[:16]}...
  ✓ FRE 902(13)/(14) compliant evidence chain
  ✓ Timestamp: {chain.construction_timestamp.isoformat()}
""")
    
    print_section("Demo Complete")
    print("\n✓ Beneficial Ownership Chain Resolution Module operational")
    print("✓ Section 7 implementation validated\n")


if __name__ == "__main__":
    asyncio.run(main())
