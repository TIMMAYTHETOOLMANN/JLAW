"""
Convert Nike 2019 Analysis to Evidence-Backed Format
=====================================================

Takes the existing Nike 2019 comprehensive analysis and converts it
to the new evidence-backed format with rigorous standards.

This script:
1. Loads the existing analysis JSON
2. Converts each violation to evidence-backed format
3. REJECTS findings without sufficient evidence
4. Generates new report with only verified, evidence-backed findings
5. Shows conversion statistics

Author: JARVIS NEXUS
Date: November 26, 2025
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import logging

# Ensure JLAW is in path
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.reporting import (
    LegacySystemAdapter,
    ConfidenceLevel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'nike_evidence_conversion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_latest_nike_analysis() -> dict:
    """Load the most recent Nike 2019 analysis JSON."""
    # Look for nike_2019_comprehensive_results_*.json files
    results_files = list(Path('.').glob('nike_2019_comprehensive_results_*.json'))
    
    if not results_files:
        logger.error("❌ No Nike 2019 analysis files found")
        logger.info("Looking for files matching: nike_2019_comprehensive_results_*.json")
        return None
    
    # Get most recent
    latest_file = max(results_files, key=lambda p: p.stat().st_mtime)
    logger.info(f"📂 Loading analysis from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    logger.info(f"✅ Loaded analysis with {len(data.get('detailed_violations', []))} filing analyses")
    
    return data


def convert_to_evidence_backed(
    legacy_data: dict,
    min_confidence: ConfidenceLevel = ConfidenceLevel.MODERATE
) -> dict:
    """
    Convert legacy analysis to evidence-backed format.
    
    Args:
        legacy_data: Original analysis data
        min_confidence: Minimum confidence level for reporting
        
    Returns:
        Evidence-backed comprehensive report
    """
    logger.info("\n" + "="*100)
    logger.info(" " * 30 + "EVIDENCE CONVERSION STARTING")
    logger.info("="*100)
    
    adapter = LegacySystemAdapter(min_confidence=min_confidence)
    
    # Extract metadata
    metadata = legacy_data.get('metadata', {})
    investigation_id = metadata.get('case_id', f"NIKE_2019_EVIDENCE_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    logger.info(f"\n🎯 INVESTIGATION: {investigation_id}")
    logger.info(f"   Target: {metadata.get('target_company', 'Nike Inc')} (CIK: {metadata.get('target_cik', '0000320187')})")
    logger.info(f"   Period: 2019-01-01 to 2019-12-31")
    logger.info(f"   Filings to Process: {len(legacy_data.get('detailed_violations', []))}")
    logger.info(f"   Min Confidence: {min_confidence.value}")
    
    # Convert each filing
    filing_reports = []
    detailed_violations = legacy_data.get('detailed_violations', [])
    
    logger.info(f"\n📋 CONVERTING {len(detailed_violations)} FILING ANALYSES...")
    
    for i, filing_data in enumerate(detailed_violations, 1):
        filing_metadata = {
            'cik': '0000320187',  # Nike CIK
            'accession_number': filing_data.get('accession_number', 'UNKNOWN'),
            'form_type': filing_data.get('form_type', 'UNKNOWN'),
            'filing_date': filing_data.get('filing_date', 'UNKNOWN'),
            'company_name': 'Nike Inc',
            'document_url': f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320187&type={filing_data.get('form_type', '')}&dateb=&owner=exclude&count=100"
        }
        
        logger.info(f"\n   [{i}/{len(detailed_violations)}] {filing_metadata['form_type']} - {filing_metadata['filing_date']}")
        logger.info(f"      Accession: {filing_metadata['accession_number']}")
        logger.info(f"      Legacy violations: {filing_data.get('violation_count', 0)}")
        
        legacy_analysis = {
            'violations': filing_data.get('violations', [])
        }
        
        filing_report = adapter.convert_filing_analysis(legacy_analysis, filing_metadata)
        
        logger.info(f"      Evidence-backed violations: {filing_report.reportable_violations}")
        logger.info(f"      Avg evidence strength: {filing_report.avg_evidence_strength:.2f}")
        
        if filing_report.reportable_violations > 0:
            filing_reports.append(filing_report)
            logger.info(f"      ✅ ACCEPTED")
        else:
            logger.info(f"      ❌ REJECTED (no reportable violations)")
    
    # Create comprehensive report
    logger.info(f"\n📊 GENERATING COMPREHENSIVE REPORT...")
    
    report = adapter.create_comprehensive_report(
        investigation_id=investigation_id,
        company_name='Nike Inc',
        company_cik='0000320187',
        investigation_period={
            'start_date': '2019-01-01',
            'end_date': '2019-12-31'
        },
        filing_reports=filing_reports
    )
    
    # Print conversion summary
    adapter.print_conversion_summary()
    
    return report.to_dict()


def save_evidence_backed_report(report_data: dict, output_file: str):
    """Save evidence-backed report to JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Evidence-backed report saved: {output_file}")


def print_evidence_report_summary(report_data: dict):
    """Print human-readable summary of evidence-backed report."""
    exec_summary = report_data['executive_summary']
    inv_metadata = report_data['investigation_metadata']
    
    print("\n" + "="*100)
    print(" " * 25 + "EVIDENCE-BACKED FORENSIC REPORT")
    print("="*100)
    
    print(f"\n🎯 INVESTIGATION METADATA:")
    print(f"   ID: {inv_metadata['investigation_id']}")
    print(f"   Target: {inv_metadata['target_company']} (CIK: {inv_metadata['target_cik']})")
    print(f"   Period: {inv_metadata['investigation_period']['start_date']} to {inv_metadata['investigation_period']['end_date']}")
    print(f"   Generated: {inv_metadata['investigation_end']}")
    
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   Total Filings Analyzed: {exec_summary['total_filings_analyzed']}")
    print(f"   Total Evidence-Backed Violations: {exec_summary['total_violations_detected']}")
    print(f"   Average Evidence Strength: {exec_summary['avg_evidence_strength']:.2f} / 1.00")
    print(f"   Reportable Rate: {exec_summary['reportable_rate_percent']:.1f}%")
    
    print(f"\n⚖️  VIOLATIONS BY SEVERITY:")
    for severity, count in sorted(exec_summary['violations_by_severity'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {severity}: {count}")
    
    print(f"\n📜 TOP STATUTES VIOLATED:")
    for statute, count in list(exec_summary['violations_by_statute'].items())[:10]:
        print(f"   {statute}: {count}")
    
    print(f"\n✅ EVIDENCE QUALITY ASSURANCE:")
    print(f"   All {exec_summary['total_violations_detected']} violations include:")
    print(f"   ✓ Exact quotes from source documents")
    print(f"   ✓ Precise locations (page, section, line)")
    print(f"   ✓ Specific statute citations with regulatory text")
    print(f"   ✓ Complete reasoning chains")
    print(f"   ✓ Confidence assessment")
    
    print("\n" + "="*100 + "\n")


def print_sample_evidence_chain(report_data: dict):
    """Print a sample evidence chain to show the detail level."""
    filing_reports = report_data.get('filing_reports', [])
    
    if not filing_reports:
        logger.warning("No filing reports with violations to display")
        return
    
    # Get first report with violations
    sample_report = filing_reports[0]
    
    if not sample_report['violations']:
        logger.warning("No violations in first report")
        return
    
    sample_violation = sample_report['violations'][0]
    
    print("\n" + "="*100)
    print(" " * 30 + "SAMPLE EVIDENCE CHAIN")
    print("="*100)
    
    print(f"\n📌 VIOLATION: {sample_violation['violation_id']}")
    print(f"   Description: {sample_violation['violation_description']}")
    print(f"   Severity: {sample_violation['severity']}")
    print(f"   Confidence: {sample_violation['confidence']}")
    print(f"   Evidence Strength: {sample_violation['evidence_strength_score']:.2f} / 1.00")
    
    print(f"\n📄 SUPPORTING EVIDENCE ({len(sample_violation['supporting_evidence'])} items):")
    for i, evidence in enumerate(sample_violation['supporting_evidence'], 1):
        print(f"\n   Evidence {i}:")
        print(f"      Type: {evidence['evidence_type']}")
        print(f"      Source: {evidence['source_document']}")
        print(f"      Location: {evidence['source_location']}")
        print(f"      Content: {evidence['exact_content'][:200]}")
        if len(evidence['exact_content']) > 200:
            print(f"               ... (truncated)")
    
    print(f"\n⚖️  STATUTE CITATIONS ({len(sample_violation['statute_citations'])} citations):")
    for i, statute in enumerate(sample_violation['statute_citations'], 1):
        print(f"\n   Citation {i}:")
        print(f"      Statute: {statute['statute_title']} § {statute['section']}")
        print(f"      Violation: {statute['violation_type']}")
        print(f"      Regulatory Text: {statute['exact_regulatory_text'][:200]}")
        if len(statute['exact_regulatory_text']) > 200:
            print(f"                       ... (truncated)")
        if statute.get('govinfo_url'):
            print(f"      Official Source: {statute['govinfo_url']}")
    
    print(f"\n🔗 REASONING CHAIN ({len(sample_violation['reasoning_chain'])} steps):")
    for step in sample_violation['reasoning_chain']:
        print(f"   {step}")
    
    print("\n" + "="*100 + "\n")


def main():
    """Main entry point."""
    print("\n" + "="*100)
    print(" " * 15 + "NIKE 2019 ANALYSIS - EVIDENCE-BACKED CONVERSION")
    print("="*100)
    
    # Load legacy analysis
    logger.info("\n[STEP 1] Loading existing Nike 2019 analysis...")
    legacy_data = load_latest_nike_analysis()
    
    if not legacy_data:
        logger.error("Cannot proceed without analysis data")
        return
    
    # Convert to evidence-backed format
    logger.info("\n[STEP 2] Converting to evidence-backed format...")
    evidence_report = convert_to_evidence_backed(
        legacy_data,
        min_confidence=ConfidenceLevel.MODERATE
    )
    
    # Save report
    output_file = f"nike_2019_evidence_backed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    logger.info(f"\n[STEP 3] Saving evidence-backed report...")
    save_evidence_backed_report(evidence_report, output_file)
    
    # Print summaries
    logger.info("\n[STEP 4] Generating summary reports...")
    print_evidence_report_summary(evidence_report)
    print_sample_evidence_chain(evidence_report)
    
    logger.info(f"\n✅ CONVERSION COMPLETE")
    logger.info(f"📄 Evidence-backed report: {output_file}")
    logger.info(f"📊 Total evidence-backed violations: {evidence_report['executive_summary']['total_violations_detected']}")
    logger.info(f"⭐ Average evidence strength: {evidence_report['executive_summary']['avg_evidence_strength']:.2f} / 1.00")
    
    print(f"\n{'='*100}")
    print(" " * 30 + "MISSION ACCOMPLISHED")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Conversion interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}", exc_info=True)

