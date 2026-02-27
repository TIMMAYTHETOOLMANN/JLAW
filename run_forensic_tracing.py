#!/usr/bin/env python3
"""
JLAW Forensic Tracing System Runner
=====================================

Executes the six-domain forensic tracing pipeline against existing
JLAW output data, tracing insider economic benefit from $0 acquisition
through entity transfer to ultimate liquidation.

Usage:
    python run_forensic_tracing.py [--input-dir INPUT_DIR] [--output-dir OUTPUT_DIR]
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.forensic_tracing.orchestrator import ForensicTracingOrchestrator


def load_json(filepath: str) -> dict:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f'  WARNING: Not found: {filepath}')
        return {}
    except json.JSONDecodeError as e:
        print(f'  WARNING: Invalid JSON in {filepath}: {e}')
        return {}


def save_json(data, filepath: str):
    """Save JSON with formatting."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    size = os.path.getsize(filepath)
    print(f'  Saved: {filepath} ({size:,} bytes)')


def main():
    parser = argparse.ArgumentParser(description='JLAW Forensic Tracing System')
    parser.add_argument(
        '--input-dir', default='output/NKE_2019',
        help='Input directory containing analysis results',
    )
    parser.add_argument(
        '--output-dir', default=None,
        help='Output directory (default: <input-dir>/forensic_tracing)',
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir / 'forensic_tracing'

    print('\n' + '=' * 64)
    print('  JLAW FORENSIC TRACING SYSTEM')
    print('  Six-Domain Insider Economic Benefit Analysis')
    print('=' * 64)
    print(f'\n  Input:  {input_dir}')
    print(f'  Output: {output_dir}')

    # Load enhanced results (from previous Enhancement Protocol run)
    print('\n--- Loading analysis data ---')

    enhanced_path = input_dir / 'enhanced' / 'enhanced_analysis_results.json'
    if enhanced_path.exists():
        enhanced_results = load_json(str(enhanced_path))
        print(f'  Enhanced results: {len(enhanced_results.get("violations", []))} violations')
    else:
        # Fall back to raw results
        enhanced_results = load_json(str(input_dir / 'bundle' / 'analysis_results.json'))
        print(f'  Raw results: {len(enhanced_results.get("violations", []))} violations')

    # Load FSL assessments
    fsl_data = load_json(str(input_dir / 'bundle' / 'fsl_assessments.json'))
    fsl_assessments = fsl_data if isinstance(fsl_data, list) else fsl_data.get('assessments', [])
    print(f'  FSL assessments: {len(fsl_assessments)}')

    # Run the full forensic tracing pipeline
    print('\n--- Executing Six-Domain Analysis ---')
    results = ForensicTracingOrchestrator.run_full_analysis(
        enhanced_results=enhanced_results,
        fsl_assessments=fsl_assessments,
        form144_notices=None,  # No Form 144 data for pre-2023 period
    )

    # Save outputs
    print('\n--- Saving Forensic Tracing Outputs ---')
    os.makedirs(str(output_dir), exist_ok=True)

    # Complete results
    save_json(results, str(output_dir / 'forensic_tracing_results.json'))

    # Domain-specific outputs
    save_json(
        results['domain1_footnotes'],
        str(output_dir / 'domain1_footnote_classification.json'),
    )
    save_json(
        results['domain2_tracing'],
        str(output_dir / 'domain2_grant_to_sale_tracing.json'),
    )
    save_json(
        results['domain3_ownership'],
        str(output_dir / 'domain3_ownership_resolution.json'),
    )
    save_json(
        results['domain4_form144'],
        str(output_dir / 'domain4_form144_correlation.json'),
    )
    save_json(
        results['domain5_documentation'],
        str(output_dir / 'domain5_documentation_framework.json'),
    )
    save_json(
        results['domain6_visualization'],
        str(output_dir / 'domain6_visualization_specs.json'),
    )

    # Generate human-readable summary
    summary = generate_summary(results)
    summary_path = str(output_dir / 'FORENSIC_TRACING_SUMMARY.txt')
    with open(summary_path, 'w') as f:
        f.write(summary)
    print(f'  Saved: {summary_path}')

    print('\n' + '=' * 64)
    print('  FORENSIC TRACING OUTPUTS SAVED')
    print(f'  Directory: {output_dir}')
    print('=' * 64 + '\n')

    return results


def generate_summary(results: dict) -> str:
    """Generate human-readable summary."""
    lines = []
    lines.append('=' * 72)
    lines.append('JLAW FORENSIC TRACING SYSTEM — SIX-DOMAIN ANALYSIS REPORT')
    lines.append(f'Generated: {results["_timestamp"]}')
    lines.append('=' * 72)

    # Domain 1
    d1 = results['domain1_footnotes']
    lines.append(f'\nDOMAIN 1: FORM 4 FOOTNOTE CLASSIFICATION')
    lines.append(f'  Total footnotes classified: {d1.get("total_footnotes", 0)}')
    lines.append(f'  Average risk score: {d1.get("average_risk_score", 0)}')
    lines.append(f'  Risk distribution: {d1.get("risk_distribution", {})}')
    lines.append(f'  Code J missing explanations: {d1.get("code_j_missing_explanations", 0)}')
    entities = d1.get('all_extracted_entities', [])
    if entities:
        lines.append(f'  Extracted entities: {", ".join(entities[:10])}')

    # Domain 2
    d2 = results['domain2_tracing']['summary']
    lines.append(f'\nDOMAIN 2: GRANT-TO-SALE TRACING')
    lines.append(f'  Insiders tracked: {d2.get("insiders_tracked", 0)}')
    lines.append(f'  Chains constructed: {d2.get("chains_constructed", 0)}')
    lines.append(f'  Complete chains: {d2.get("complete_chains", 0)}')
    lines.append(f'  Total shares acquired: {d2.get("total_shares_acquired", 0):,.0f}')
    acq_val = d2.get("total_acquisition_market_value", 0)
    lines.append(f'  Total acquisition market value: ${acq_val:,.2f}')
    lines.append(f'  Total shares disposed (traced): {d2.get("total_shares_sold", 0):,.0f}')
    lines.append(f'  Liquidation rate: {d2.get("liquidation_rate", 0):.1%}')
    econ_val = d2.get("total_economic_value_transferred", 0)
    lines.append(f'  Economic value transferred (FMV): ${econ_val:,.2f}')
    cash_val = d2.get("total_cash_proceeds", 0)
    lines.append(f'  Cash proceeds (Code S sales): ${cash_val:,.2f}')
    lines.append(f'  Total profit (econ value - cost basis): ${d2.get("total_profit", 0):,.2f}')
    lines.append(f'  Obfuscation vector chains: {d2.get("obfuscation_vectors", 0)}')
    if d2.get('note'):
        lines.append(f'  Note: {d2["note"]}')
    if d2.get('chain_type_distribution'):
        lines.append(f'  Chain type distribution:')
        for ct, count in d2['chain_type_distribution'].items():
            lines.append(f'    {ct}: {count}')

    # Domain 3
    d3 = results['domain3_ownership']
    lines.append(f'\nDOMAIN 3: BENEFICIAL OWNERSHIP RESOLUTION')
    lines.append(f'  Entity transfers analyzed: {d3.get("entity_transfers_analyzed", 0)}')
    lines.append(f'  Beneficial owners identified: {d3.get("beneficial_owners_identified", 0)}')
    lines.append(f'  Parking risk flags: {d3.get("parking_risk_flags", 0)}')
    for pa in d3.get('parking_analyses', []):
        if pa.get('risk_score', 0) > 0.2:
            lines.append(f'  PARKING ALERT: {pa.get("entity_a", "")} <-> {pa.get("entity_b", "")} '
                         f'(risk: {pa.get("risk_score", 0):.2f})')

    # Domain 4
    d4 = results['domain4_form144']
    lines.append(f'\nDOMAIN 4: FORM 144 CORRELATION')
    lines.append(f'  Notices available: {d4.get("total_notices", 0)}')
    if d4.get('note'):
        lines.append(f'  Note: {d4["note"][:100]}')

    # Domain 5
    d5 = results['domain5_documentation']
    lines.append(f'\nDOMAIN 5: TWO-TIER DOCUMENTATION')
    lines.append(f'  TCR exhibits: {d5.get("tcr_exhibit_count", 0)}')
    lines.append(f'  Violation types: {len(d5.get("tcr_violation_types", []))}')
    lines.append(f'  Statutory references: {len(d5.get("tcr_statutory_references", []))}')
    lines.append(f'  Work product documents: {d5.get("work_product_count", 0)}')
    for ref in d5.get('tcr_statutory_references', [])[:5]:
        lines.append(f'    - {ref}')

    # Domain 6
    d6 = results['domain6_visualization']
    lines.append(f'\nDOMAIN 6: VISUALIZATION SPECIFICATIONS')
    lines.append(f'  Chart specifications: {len(d6.get("chart_specs", []))}')
    for spec in d6.get('chart_specs', []):
        lines.append(f'    - {spec.get("chart_id", "")}: {spec.get("title", "")}')
    lines.append(f'  New PDF sections: {len(d6.get("new_sections", []))}')
    lines.append(f'  Palette: {d6.get("palette", {}).get("name", "")} (colorblind-safe)')

    lines.append('\n' + '=' * 72)
    lines.append('END OF FORENSIC TRACING SUMMARY')
    lines.append('=' * 72)

    return '\n'.join(lines)


if __name__ == '__main__':
    main()
