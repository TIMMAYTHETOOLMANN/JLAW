"""
Enhanced JLAW Forensic System - Quick Start Example
Demonstrates how to use all Priority 1 enhancements.
"""

import asyncio
import sys
from pathlib import Path

# Add JLAW to path
sys.path.insert(0, str(Path(__file__).parent))


async def example_1_contradiction_detection():
    """Example 1: Enhanced Contradiction Detection with DeBERTa-v3"""
    print("\n" + "="*80)
    print("EXAMPLE 1: ENHANCED CONTRADICTION DETECTION")
    print("="*80)
    
    from src.forensics.enhanced_contradiction_detector import EnhancedContradictionDetector
    
    # Initialize detector
    detector = EnhancedContradictionDetector(
        use_finbert=True,
        use_gpu=True,
        fallback_enabled=True
    )
    
    # Sample claims from SEC filing
    claims = [
        "Total revenue for fiscal year 2024 increased to $96.8 billion, up 19% year-over-year",
        "The company experienced declining sales in several key markets during 2024",
        "Operating margin improved from 13.5% to 18.2% in fiscal 2024",
        "Significant cost pressures resulted in margin contraction throughout the year",
        "Cash flow from operations reached $13.3 billion, the highest in company history"
    ]
    
    print(f"\nAnalyzing {len(claims)} claims from SEC filing...")
    
    result = await detector.analyze_document(
        document_id="SEC-10K-EXAMPLE-2024",
        cik="0000000001",
        filing_type="10-K",
        claims=claims
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   Total Claims Analyzed: {result.total_claims_analyzed}")
    print(f"   Contradictions Detected: {len(result.contradictions_detected)}")
    print(f"   High Confidence: {result.high_confidence_count}")
    print(f"   Medium Confidence: {result.medium_confidence_count}")
    print(f"   Overall Risk Score: {result.overall_risk_score:.1%}")
    print(f"   Analysis Method: {result.analysis_method}")
    print(f"   Processing Time: {result.processing_time_seconds:.2f}s")
    
    if result.contradictions_detected:
        print(f"\n🔍 CONTRADICTIONS FOUND:")
        for i, c in enumerate(result.contradictions_detected[:3], 1):  # Show top 3
            print(f"\n   #{i} [{c.confidence_level}] Score: {c.contradiction_score:.1%}")
            print(f"      Claim A: {c.claim1[:80]}...")
            print(f"      Claim B: {c.claim2[:80]}...")


async def example_2_benfords_law():
    """Example 2: Benford's Law Statistical Analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 2: BENFORD'S LAW STATISTICAL ANALYSIS")
    print("="*80)
    
    from src.forensics.benfords_law_analyzer import BenfordsLawAnalyzer
    import numpy as np
    
    # Initialize analyzer
    analyzer = BenfordsLawAnalyzer(strict_mode=False)
    
    # Simulate financial transaction data
    print("\nGenerating sample financial datasets...")
    
    # Natural data (should pass Benford's Law)
    natural_transactions = [np.random.exponential(scale=1000) for _ in range(1000)]
    
    # Suspicious data (uniform distribution - should fail)
    suspicious_transactions = [np.random.uniform(1000, 9999) for _ in range(1000)]
    
    datasets = {
        'Revenue Transactions (Natural)': natural_transactions,
        'Expense Transactions (Suspicious)': suspicious_transactions
    }
    
    result = await analyzer.analyze_multiple_datasets(
        datasets=datasets,
        cik="0000000001",
        company_name="Example Corp",
        filing_type="10-K"
    )
    
    print(f"\n📊 RESULTS:")
    print(f"   Overall Risk Score: {result.overall_risk_score:.1%}")
    print(f"   Datasets Analyzed: {len(result.datasets_analyzed)}")
    print(f"   High-Risk Datasets: {len(result.high_risk_datasets)}")
    
    print(f"\n🔍 DATASET ANALYSIS:")
    for dataset_name, analysis in result.datasets_analyzed.items():
        print(f"\n   📁 {dataset_name}")
        print(f"      Passed: {analysis.passed}")
        print(f"      Chi-square: {analysis.chi_square:.2f} (critical: {analysis.chi_square_critical})")
        print(f"      MAD: {analysis.mad:.6f}")
        print(f"      Manipulation Probability: {analysis.manipulation_probability:.1%}")
        print(f"      Risk Level: {analysis.manipulation_risk.value}")
        
        if analysis.significant_digits:
            print(f"      ⚠️  Significant Digit Deviations: {analysis.significant_digits}")


async def example_3_rfc3161_timestamping():
    """Example 3: RFC 3161 Cryptographic Timestamping"""
    print("\n" + "="*80)
    print("EXAMPLE 3: RFC 3161 CRYPTOGRAPHIC TIMESTAMPING")
    print("="*80)
    
    from src.forensics.rfc3161_timestamper import RFC3161Timestamper, TSAProvider
    
    # Initialize timestamper
    timestamper = RFC3161Timestamper(
        tsa_provider=TSAProvider.FREETSA,
        hash_algorithm='sha256',
        fallback_enabled=True
    )
    
    # Evidence to timestamp
    evidence = b"Critical forensic evidence: Company XYZ financial manipulation detected"
    evidence_id = "EVIDENCE-MANIPULATION-001"
    
    print(f"\nTimestamping forensic evidence...")
    print(f"   Evidence ID: {evidence_id}")
    print(f"   TSA Provider: {TSAProvider.FREETSA.value}")
    
    timestamp = await timestamper.timestamp_evidence(
        content=evidence,
        evidence_id=evidence_id,
        metadata={
            'case_id': 'CASE-2024-001',
            'evidence_type': 'financial_analysis',
            'criticality': 'HIGH'
        }
    )
    
    print(f"\n📊 TIMESTAMP RESULT:")
    print(f"   Timestamp (UTC): {timestamp.timestamp_utc.isoformat()}")
    print(f"   Content Hash: {timestamp.content_hash}")
    print(f"   Verification Status: {timestamp.verification_status.value}")
    print(f"   TSA URL: {timestamp.tsa_url}")
    
    # Verify timestamp
    print(f"\nVerifying timestamp...")
    verification = await timestamper.verify_timestamp(
        content=evidence,
        timestamp=timestamp
    )
    
    print(f"\n✅ VERIFICATION RESULT:")
    print(f"   Valid: {verification.is_valid}")
    print(f"   Content Hash Matches: {verification.content_hash_matches}")
    print(f"   Details: {verification.verification_details}")


async def example_4_entity_extraction():
    """Example 4: Financial Entity Extraction with FinBERT"""
    print("\n" + "="*80)
    print("EXAMPLE 4: FINANCIAL ENTITY EXTRACTION")
    print("="*80)
    
    from src.forensics.financial_entity_extractor import (
        FinancialEntityExtractor,
        EntityType
    )
    
    # Initialize extractor
    extractor = FinancialEntityExtractor(
        use_finbert=True,
        use_spacy=True,
        use_gpu=True
    )
    
    # Sample SEC filing text
    filing_text = """
    Tesla, Inc. (CIK: 0001318605) reported fourth quarter revenue of $25.7 billion, 
    representing a 15% increase year-over-year. The company's EBITDA margin improved 
    to 18.2%, while diluted EPS reached $2.45 per share, exceeding analyst expectations 
    of $2.20. CEO Elon Musk announced the acquisition of a lithium battery manufacturing 
    subsidiary for approximately $500 million, expected to close in Q1 2025. The company 
    also reported free cash flow of $3.1 billion for the quarter, with total assets 
    reaching $92.4 billion. Operating margin expanded from 13.5% to 15.8% compared to 
    the prior year period. The board of directors authorized a $10 billion share 
    repurchase program.
    """
    
    print(f"\nExtracting entities from SEC filing text...")
    
    result = await extractor.extract_entities(
        text=filing_text,
        document_id="SEC-10K-TSLA-2024",
        filing_context={'cik': '0001318605', 'company': 'Tesla, Inc.'}
    )
    
    print(f"\n📊 EXTRACTION RESULTS:")
    print(f"   Total Entities: {len(result.entities)}")
    print(f"   Organizations: {result.entity_counts.get(EntityType.ORG, 0)}")
    print(f"   Persons: {result.entity_counts.get(EntityType.PERSON, 0)}")
    print(f"   Money: {result.entity_counts.get(EntityType.MONEY, 0)}")
    print(f"   Financial Metrics: {result.entity_counts.get(EntityType.FINANCIAL_METRIC, 0)}")
    print(f"   Transactions: {result.entity_counts.get(EntityType.TRANSACTION, 0)}")
    print(f"   Processing Time: {result.processing_time_seconds:.2f}s")
    
    print(f"\n🔍 SAMPLE ENTITIES:")
    entity_types_shown = set()
    for entity in result.entities[:10]:  # Show first 10
        if entity.entity_type not in entity_types_shown:
            print(f"\n   [{entity.entity_type.value}] {entity.text}")
            print(f"      Confidence: {entity.confidence:.1%}")
            if entity.normalized_value:
                print(f"      Normalized: {entity.normalized_value}")
            entity_types_shown.add(entity.entity_type)


async def example_5_ensemble_investigation():
    """Example 5: Complete Enhanced Forensic Investigation"""
    print("\n" + "="*80)
    print("EXAMPLE 5: COMPLETE ENHANCED FORENSIC INVESTIGATION")
    print("="*80)
    
    from src.forensics.enhanced_forensic_system import EnhancedForensicOrchestrator
    from src.forensics.immutable_storage import StorageConfig
    import tempfile
    import os
    import numpy as np
    
    print("\nInitializing Enhanced Forensic System...")
    
    # Setup
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_config = StorageConfig(
            base_path=tmpdir,
            enable_compression=True,
            compression_level=6
        )
        
        audit_key = os.urandom(32)
        
        orchestrator = EnhancedForensicOrchestrator(
            govinfo_api_key="DEMO_KEY",
            storage_config=storage_config,
            audit_signing_key=audit_key,
            enable_all_enhancements=True,
            enable_gpu=False
        )
        
        print(f"\n✅ System Initialized:")
        print(f"   Active Enhancements: {len(orchestrator.active_enhancements)}")
        for enhancement in orchestrator.active_enhancements:
            print(f"      • {enhancement}")
        
        # Generate sample financial data for Benford's Law
        print(f"\nGenerating sample financial datasets...")
        financial_datasets = {
            'Q4_Revenue_Transactions': [np.random.exponential(scale=5000) for _ in range(500)],
            'Accounts_Receivable': [np.random.exponential(scale=10000) for _ in range(800)],
        }
        
        # Run enhanced investigation
        print(f"\n🔍 Running enhanced forensic investigation...")
        print(f"   Target: Example Corp (CIK: 0000000001)")
        print(f"   Scope: 3 years, 10-K/10-Q filings")
        
        result = await orchestrator.investigate_enhanced(
            cik="0000000001",
            company_name="Example Corp",
            filing_types=["10-K", "10-Q"],
            years=3,
            financial_datasets=financial_datasets
        )
        
        print(f"\n📊 INVESTIGATION RESULTS:")
        print(f"   Case ID: {result.case_id}")
        print(f"   Overall Risk Score: {result.overall_risk_score:.1%}")
        print(f"   Risk Level: {result.risk_level}")
        print(f"   Critical Findings: {len(result.high_severity_findings)}")
        print(f"   Processing Time: {result.processing_time_seconds:.2f}s")
        print(f"   Evidence Chain Hash: {result.evidence_chain_hash[:32]}...")
        
        if result.high_severity_findings:
            print(f"\n⚠️  CRITICAL FINDINGS:")
            for i, finding in enumerate(result.high_severity_findings[:5], 1):
                print(f"   {i}. {finding}")
        
        if result.recommendations:
            print(f"\n📋 RECOMMENDATIONS:")
            for i, rec in enumerate(result.recommendations[:5], 1):
                print(f"   {i}. {rec}")
        
        # Generate prosecution package
        print(f"\n📦 Generating prosecution package...")
        package = orchestrator.generate_prosecution_package(result)
        
        print(f"\n✅ Prosecution Package Generated:")
        print(f"   Package Type: {package['package_type']}")
        print(f"   Package Version: {package['package_version']}")
        print(f"   Risk Assessment: {package['risk_assessment']['risk_level']}")
        print(f"   Evidence Items: {len(package['evidence'])}")


async def main():
    """Run all examples."""
    print("\n" + "🚀" * 40)
    print("JLAW ENHANCED FORENSIC SYSTEM - COMPREHENSIVE EXAMPLES")
    print("🚀" * 40)
    
    examples = [
        example_1_contradiction_detection,
        example_2_benfords_law,
        example_3_rfc3161_timestamping,
        example_4_entity_extraction,
        example_5_ensemble_investigation,
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("✅ ALL EXAMPLES COMPLETE")
    print("="*80)
    print("\nFor more information:")
    print("  • Documentation: PRIORITY_1_ENHANCEMENTS_COMPLETE.md")
    print("  • Enhancement Report: docs/scripts/JLAW_Forensic_Enhancement_Report.md")
    print("  • Requirements: requirements_enhancements.txt")
    print()


if __name__ == "__main__":
    asyncio.run(main())

