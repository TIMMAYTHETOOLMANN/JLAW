#!/usr/bin/env python3
"""
JLAW Enhancement Protocol v5.0.0 Runner
Codename: APEX-VALUATION

Reads existing forensic output files, applies all 11 enhancement modules,
and generates enriched output with full economic valuations.

Usage:
    python run_enhancement_protocol.py [--output-dir OUTPUT_DIR]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.enhancement.orchestrator import JLAWEnhancementOrchestrator


def load_json(filepath: str) -> dict:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f'  WARNING: File not found: {filepath}')
        return {}
    except json.JSONDecodeError as e:
        print(f'  WARNING: Invalid JSON in {filepath}: {e}')
        return {}


def save_json(data: dict, filepath: str):
    """Save JSON file with formatting."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f'  Saved: {filepath} ({os.path.getsize(filepath):,} bytes)')


def main():
    parser = argparse.ArgumentParser(description='JLAW Enhancement Protocol v5.0.0')
    parser.add_argument(
        '--input-dir', default='output/NKE_2019',
        help='Input directory containing analysis results (default: output/NKE_2019)',
    )
    parser.add_argument(
        '--output-dir', default=None,
        help='Output directory for enhanced results (default: <input-dir>/enhanced)',
    )
    parser.add_argument(
        '--cik', default='320187',
        help='Company CIK number (default: 320187 for NIKE)',
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir / 'enhanced'

    print('\n' + '=' * 60)
    print('  JLAW ENHANCEMENT PROTOCOL v5.0.0 - APEX-VALUATION')
    print('  Forensic Output Enhancement Pipeline')
    print('=' * 60)
    print(f'\n  Input directory:  {input_dir}')
    print(f'  Output directory: {output_dir}')
    print(f'  Target CIK:       {args.cik}')

    # Load existing analysis outputs
    print('\n--- Loading existing analysis outputs ---')

    analysis_results = load_json(input_dir / 'bundle' / 'analysis_results.json')
    print(f'  analysis_results.json: {len(analysis_results.get("violations", []))} violations')

    # Find SOX analysis file (timestamped filename)
    sox_dir = input_dir / 'node4_sox'
    sox_results = {}
    if sox_dir.exists():
        sox_files = list(sox_dir.glob('sox_analysis_*.json'))
        if sox_files:
            sox_results = load_json(str(sox_files[0]))
            print(f'  sox_analysis: {sox_results.get("violations_detected", 0)} violations')

    # Find temporal analysis file
    temporal_dir = input_dir / 'node3_10q'
    temporal_results = {}
    if temporal_dir.exists():
        temporal_files = list(temporal_dir.glob('temporal_analysis_*.json'))
        if temporal_files:
            temporal_results = load_json(str(temporal_files[0]))
            print(f'  temporal_analysis: {temporal_results.get("quarters_analyzed", 0)} quarters (all zeros: {all(q["revenue"] == "0" for q in temporal_results.get("quarters", []))})')

    # Find IRC83 analysis file
    irc83_dir = input_dir / 'node5_irs'
    irc83_results = {}
    if irc83_dir.exists():
        irc83_files = list(irc83_dir.glob('irc83_analysis_*.json'))
        if irc83_files:
            irc83_results = load_json(str(irc83_files[0]))
            print(f'  irc83_analysis: {irc83_results.get("grants_analyzed", 0)} grants')

    # Load FSL assessments
    fsl_assessments = load_json(input_dir / 'bundle' / 'fsl_assessments.json')
    if isinstance(fsl_assessments, list):
        print(f'  fsl_assessments: {len(fsl_assessments)} assessments')
    else:
        fsl_assessments = fsl_assessments.get('assessments', [])
        print(f'  fsl_assessments: {len(fsl_assessments)} assessments')

    # Run enhancement protocol
    print('\n--- Running Enhancement Protocol ---\n')

    enhanced = JLAWEnhancementOrchestrator.enhance(
        raw_results=analysis_results,
        sox_results=sox_results,
        fsl_assessments=fsl_assessments if isinstance(fsl_assessments, list) else [],
        cik=args.cik,
    )

    # Save enhanced outputs
    print('\n--- Saving Enhanced Outputs ---')
    os.makedirs(str(output_dir), exist_ok=True)

    # Main enhanced results
    save_json(enhanced, str(output_dir / 'enhanced_analysis_results.json'))

    # Economic valuations (standalone)
    save_json(
        enhanced['economic_valuations'],
        str(output_dir / 'economic_valuations.json'),
    )

    # Beneficiary analysis (standalone)
    save_json(
        enhanced['beneficiary_analysis'],
        str(output_dir / 'beneficiary_analysis.json'),
    )

    # Recalibrated FSL
    save_json(
        enhanced['fsl_assessments'],
        str(output_dir / 'fsl_recalibrated.json'),
    )

    # Recovered temporal analysis
    save_json(
        enhanced['temporal_analysis'],
        str(output_dir / 'temporal_analysis_recovered.json'),
    )

    # Sanitized SOX
    if enhanced.get('sox_analysis'):
        save_json(
            enhanced['sox_analysis'],
            str(output_dir / 'sox_analysis_sanitized.json'),
        )

    # Penalty exposure
    save_json(
        enhanced['penalty_exposure'],
        str(output_dir / 'penalty_exposure.json'),
    )

    # Executive summary narrative
    save_json(
        enhanced['executive_summary'],
        str(output_dir / 'executive_summary.json'),
    )

    # Evidence chain
    save_json(
        enhanced['evidence_chain'],
        str(output_dir / 'evidence_chain.json'),
    )

    # Severity summary
    save_json(
        {
            'severity_summary': enhanced['severity_summary'],
            'violations_by_type': enhanced['violations_by_type'],
            'total_violations': enhanced['total_violations'],
            'critical_alerts': enhanced['critical_alerts'],
            'high_alerts': enhanced['high_alerts'],
        },
        str(output_dir / 'severity_summary.json'),
    )

    # Generate human-readable summary report
    summary = generate_text_summary(enhanced)
    summary_path = str(output_dir / 'ENHANCEMENT_SUMMARY.txt')
    with open(summary_path, 'w') as f:
        f.write(summary)
    print(f'  Saved: {summary_path}')

    print('\n' + '=' * 60)
    print('  ALL ENHANCED OUTPUTS SAVED SUCCESSFULLY')
    print(f'  Output directory: {output_dir}')
    print('=' * 60 + '\n')

    return enhanced


def generate_text_summary(enhanced: dict) -> str:
    """Generate a human-readable text summary of the enhancement results."""
    lines = []
    lines.append('=' * 72)
    lines.append('JLAW FORENSIC DOSSIER ENHANCEMENT PROTOCOL v5.0.0')
    lines.append('CODENAME: APEX-VALUATION')
    lines.append(f'Generated: {enhanced["_enhancement_timestamp"]}')
    lines.append('=' * 72)

    lines.append('\nDEFICIENCIES RESOLVED:')
    for d in enhanced['_deficiencies_resolved']:
        lines.append(f'  [FIXED] {d}')

    # Severity summary
    sev = enhanced['severity_summary']
    lines.append(f'\nUNIFIED SEVERITY SUMMARY:')
    lines.append(f'  Critical: {sev["critical"]}')
    lines.append(f'  High:     {sev["high"]}')
    lines.append(f'  Medium:   {sev["medium"]}')
    lines.append(f'  Low:      {sev["low"]}')
    lines.append(f'  Total:    {sev["total"]}')

    # Deduplication
    dedup = enhanced['deduplication_stats']
    lines.append(f'\nVIOLATION DEDUPLICATION:')
    lines.append(f'  Original violations: {dedup["original"]}')
    lines.append(f'  After deduplication: {dedup["after"]}')
    lines.append(f'  Duplicates removed:  {dedup["removed"]}')

    # Economic valuations
    econ = enhanced['economic_valuations']
    lines.append(f'\nECONOMIC BENEFIT VALUATIONS:')
    lines.append(f'  Total aggregate benefit: {econ["formatted_total"]}')
    lines.append(f'  Transactions valued:     {len(econ["transactions"])}')
    lines.append(f'  Methodology: {econ["valuation_methodology"]}')

    # Top beneficiaries
    lines.append(f'\nTOP BENEFICIARIES BY ECONOMIC VALUE:')
    lines.append(f'  {"Name":<25} {"Total Benefit":>18} {"Txns":>6}')
    lines.append(f'  {"-"*25} {"-"*18} {"-"*6}')
    for b in enhanced['beneficiary_analysis'][:10]:
        name = b['name'][:25]
        benefit = f'${b["total_economic_benefit"]:,.2f}'
        lines.append(f'  {name:<25} {benefit:>18} {b["transaction_count"]:>6}')

    # FSL recalibration
    fsl_stats = enhanced['fsl_recalibration_stats']
    lines.append(f'\nFSL RECALIBRATION:')
    lines.append(f'  Total assessed:          {fsl_stats["total_assessed"]}')
    lines.append(f'  Escalated from benign:   {fsl_stats["escalated_from_benign"]}')
    lines.append(f'  Escalation rate:         {fsl_stats["escalation_rate"]}')

    # Penalty exposure
    pen = enhanced['penalty_exposure']
    lines.append(f'\nCOMPREHENSIVE PENALTY EXPOSURE:')
    lines.append(f'  Civil range:       {pen["civil_penalty_range"]["formatted_min"]} - {pen["civil_penalty_range"]["formatted_max"]}')
    lines.append(f'  Disgorgement:      {pen["estimated_disgorgement"]["formatted"]}')
    lines.append(f'  Criminal exposure:  ${pen["criminal_exposure"]["max_fine"]:,.0f} / {pen["criminal_exposure"]["max_years"]}yr max')
    lines.append(f'  TOTAL MAX EXPOSURE: {pen["formatted_total"]}')
    wb = pen['whistleblower_bounty']
    lines.append(f'\n  Whistleblower Bounty (SEC Rule 21F):')
    lines.append(f'    Floor (10%):    ${wb["bounty_floor"]:,.0f}')
    lines.append(f'    Ceiling (30%):  ${wb["bounty_ceiling"]:,.0f}')
    lines.append(f'    Midpoint (20%): ${wb["estimated_bounty_midpoint"]:,.0f}')

    # Patterns
    narrative = enhanced['executive_summary']
    lines.append(f'\nPROSECUTORIAL PATTERNS IDENTIFIED:')
    for p in narrative['patterns_identified']:
        lines.append(f'  [{p["severity"]}] PATTERN {p["id"]}: {p["name"]}')
    lines.append(f'\n  Recommendation: {narrative["prosecution_recommendation"]}')

    # Temporal recovery
    temp = enhanced['temporal_analysis']
    lines.append(f'\nTEMPORAL ANALYSIS (RECOVERED):')
    lines.append(f'  Quarters with financial data: {len(temp["quarters"])}')
    lines.append(f'  Transaction clusters detected: {len(temp["transaction_clusters"])}')
    if temp['quarters']:
        lines.append(f'\n  {"Period":<10} {"Revenue":>15} {"Net Income":>15} {"Gross Margin":>13}')
        lines.append(f'  {"-"*10} {"-"*15} {"-"*15} {"-"*13}')
        for q in temp['quarters']:
            lines.append(f'  {q["period"]:<10} {q["revenue"]:>15} {q["net_income"]:>15} {q["gross_margin"]:>13}')

    # Evidence chain
    ec = enhanced['evidence_chain']
    lines.append(f'\nEVIDENCE CHAIN:')
    lines.append(f'  Merkle root:   {ec["merkle_root"]}')
    lines.append(f'  Leaf count:    {ec["leaf_count"]}')
    lines.append(f'  Report hash:   {ec["report_hash"]}')
    lines.append(f'  Algorithm:     {ec["algorithm"]}')

    lines.append('\n' + '=' * 72)
    lines.append('END OF ENHANCEMENT SUMMARY')
    lines.append('=' * 72)

    return '\n'.join(lines)


if __name__ == '__main__':
    main()
