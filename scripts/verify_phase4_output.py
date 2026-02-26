#!/usr/bin/env python
"""
Sample Output Verification Script
==================================

Generates sample DOJ-grade forensic output using the Phase 4 enhanced formatters
to verify Unicode rendering and overall format quality.
"""

from datetime import datetime, date
from pathlib import Path

from src.reporting.formatters import (
    CoverSheetFormatter,
    ExecutiveBriefingFormatter,
    InsiderDossierFormatter,
    ViolationCategoryFormatter,
    EvidenceChainFormatter,
    AppendixGenerator,
)


def generate_sample_output():
    """Generate complete sample output."""
    lines = []
    
    # ═══════════════════════════════════════════════════════════════════
    # 1. COVER SHEET
    # ═══════════════════════════════════════════════════════════════════
    
    print("Generating Cover Sheet...")
    cover_data = {
        'case_id': 'JLAW-320187-20240101-120000',
        'company_name': 'NIKE, Inc.',
        'cik': '0000320187',
        'generation_date': datetime(2024, 1, 1, 12, 0, 0),
        'dossier_type': 'DOJ-GRADE',
        'start_date': '2019-01-01',
        'end_date': '2019-12-31',
    }
    lines.append(CoverSheetFormatter.format(cover_data))
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════
    # 2. EXECUTIVE INTELLIGENCE BRIEFING
    # ═══════════════════════════════════════════════════════════════════
    
    print("Generating Executive Intelligence Briefing...")
    exec_summary = {
        'threat_level': 'CRITICAL',
        'threat_statement': (
            'This investigation establishes 15 CRITICAL violations of federal '
            'securities law by 5 actors at NIKE, Inc. The pattern and frequency '
            'indicate systematic non-compliance with SEC reporting requirements '
            'and potential tax evasion through zero-dollar option exercises.'
        ),
        'total_violations': 25,
        'critical_violations': 15,
        'high_violations': 8,
        'total_actors': 5,
        'enforcement_recommendation': (
            'IMMEDIATE DOJ CRIMINAL REFERRAL RECOMMENDED - Evidence establishes '
            'criminal violations of 18 USC § 1348 (securities fraud) and IRC § 83 '
            '(tax evasion). Pattern indicates intentional misconduct warranting '
            'criminal prosecution.'
        ),
        'primary_enforcement_agencies': ['DOJ Criminal Division', 'SEC Enforcement', 'IRS-CI'],
        'key_findings': [
            {
                'finding': '15 critical violations of §16(a) reporting requirements',
                'relevance': 'Establishes systematic non-compliance, not isolated incidents'
            },
            {
                'finding': '12 zero-dollar option exercises totaling $8.5M in unreported income',
                'relevance': 'Constitutes criminal tax evasion under IRC § 83'
            },
            {
                'finding': 'Trading patterns correlate with material non-public information',
                'relevance': 'Establishes probable cause for insider trading prosecution'
            },
        ],
        'priority_matrix': {
            'CRITICAL': 15,
            'HIGH': 8,
            'MEDIUM': 2,
            'LOW': 0,
        }
    }
    lines.append(ExecutiveBriefingFormatter.format(exec_summary))
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════
    # 3. VIOLATION ANALYSIS BY CATEGORY
    # ═══════════════════════════════════════════════════════════════════
    
    print("Generating Violation Analysis...")
    violations = [
        {
            'violation_id': 'V001',
            'violation_type': 'LATE_FORM4_FILING',
            'confidence': 0.95,
            'severity': 'CRITICAL',
            'statutes': [
                {'code': '17 CFR § 240.16a-3', 'title': 'Form 4 Filing Requirements'},
                {'code': '15 USC § 78p(a)', 'title': 'Directors, Officers, Principal Stockholders'}
            ],
            'transaction_date': '2019-06-15',
            'filing_date': '2019-07-20',
            'reporting_person': 'John Doe',
            'shares': 50000,
            'transaction_code': 'S',
            'days_late': 33,
            'penalty_min': 50000,
            'penalty_max': 200000,
        },
        {
            'violation_id': 'V002',
            'violation_type': 'LATE_FORM4_FILING',
            'confidence': 0.92,
            'severity': 'HIGH',
            'statutes': [
                {'code': '17 CFR § 240.16a-3', 'title': 'Form 4 Filing Requirements'}
            ],
            'transaction_date': '2019-08-10',
            'filing_date': '2019-08-28',
            'reporting_person': 'Jane Smith',
            'shares': 25000,
            'transaction_code': 'P',
            'days_late': 16,
            'penalty_min': 25000,
            'penalty_max': 100000,
        },
        {
            'violation_id': 'V003',
            'violation_type': 'ZERO_DOLLAR_OPTION_EXERCISE',
            'confidence': 0.98,
            'severity': 'CRITICAL',
            'statutes': [
                {'code': 'IRC § 83', 'title': 'Property Transferred in Connection with Services'},
                {'code': '26 CFR § 1.83-7', 'title': 'Taxation of Nonqualified Stock Options'}
            ],
            'transaction_date': '2019-09-15',
            'reporting_person': 'John Doe',
            'shares': 100000,
            'transaction_code': 'M',
            'exercise_price': 0.00,
            'market_price': 85.00,
            'unreported_income': 8500000,
        },
    ]
    lines.append(ViolationCategoryFormatter.format(violations))
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════
    # 4. REPORTING PERSON DOSSIERS
    # ═══════════════════════════════════════════════════════════════════
    
    print("Generating Insider Dossiers...")
    insiders = [
        {
            'name': 'John Doe',
            'risk_score': 92.5,
            'roles': ['CEO', 'Director'],
            'relationship': 'Officer and Director',
            'cik': '1234567',
            'total_transactions': 45,
            'zero_dollar_transactions': 12,
            'late_filings': 8,
            'transactions': [
                {'transaction_date': '2019-09-15', 'transaction_code': 'M', 'shares': 100000, 'price_per_share': 0.00},
                {'transaction_date': '2019-06-15', 'transaction_code': 'S', 'shares': 50000, 'price_per_share': 82.50},
            ],
            'pattern_analysis': (
                '12 zero-dollar option exercises totaling $8.5M in unreported compensation income '
                'constitute systematic tax evasion under IRC § 83. 8 late Form 4 filings establish '
                'willful non-compliance with §16(a) requirements. Transaction timing correlates with '
                'material earnings announcements, suggesting exploitation of insider knowledge.'
            ),
        },
        {
            'name': 'Jane Smith',
            'risk_score': 74.0,
            'roles': ['CFO'],
            'relationship': 'Officer',
            'cik': '1234568',
            'total_transactions': 28,
            'zero_dollar_transactions': 0,
            'late_filings': 5,
            'transactions': [
                {'transaction_date': '2019-08-10', 'transaction_code': 'P', 'shares': 25000, 'price_per_share': 75.00},
            ],
            'pattern_analysis': (
                '5 late Form 4 filings establish pattern of non-compliance with §16(a) requirements. '
                'No zero-dollar transactions detected. Transaction volume elevated compared to peer '
                'executives, warranting detailed review.'
            ),
        },
    ]
    lines.append(InsiderDossierFormatter.format_all(insiders))
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════
    # 5. EVIDENCE CHAIN & CRYPTOGRAPHIC ATTESTATION
    # ═══════════════════════════════════════════════════════════════════
    
    print("Generating Evidence Chain...")
    evidence_data = {
        'merkle_root': 'f7c3bc1d808e04732adf679965ccc34ca7ae3441',
        'total_evidence_items': 250,
        'hash_algorithm': 'SHA-256',
        'secondary_hash': 'SHA3-512',
        'tertiary_hash': 'BLAKE2b',
        'fre_902_compliant': True,
        'rfc_6962_compliant': True,
        'timestamp_token': 'TST-2024-01-01-120000',
        'chain_of_custody_records': 125,
        'hash_verified': True,
        'merkle_verified': True,
    }
    lines.append(EvidenceChainFormatter.format(evidence_data))
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════
    # 6. APPENDICES
    # ═══════════════════════════════════════════════════════════════════
    
    print("Generating Appendices...")
    appendices_data = {
        'appendix_a': {
            'violations': violations[:2],  # Include first 2 for brevity
        },
        'appendix_b': {
            'execution_summary': {
                'total_nodes': 15,
                'successful_nodes': 14,
                'failed_nodes': 1,
            },
            'node_results': {
                'Node 1: Form 4 Insider Trading': {
                    'status': 'success',
                    'violations_found': 15,
                    'execution_time': 3.24,
                },
                'Node 2: DEF 14A Compensation': {
                    'status': 'success',
                    'violations_found': 8,
                    'execution_time': 5.67,
                },
            }
        },
        'appendix_c': {
            'filings': [
                {'filing_date': '2019-12-15', 'form_type': 'FORM 4', 'accession_number': '0001234567-19-000123'},
                {'filing_date': '2019-11-20', 'form_type': 'FORM 4', 'accession_number': '0001234567-19-000122'},
            ]
        },
        'appendix_d': {
            'algorithms': {
                'Options Backdating Detection': {
                    'status': 'success',
                    'detections': 3,
                    'execution_time': 2.15,
                },
                'Spring Loading Detection': {
                    'status': 'success',
                    'detections': 5,
                    'execution_time': 1.89,
                },
            }
        }
    }
    lines.append(AppendixGenerator.format_all(appendices_data))
    lines.append("")
    
    # ═══════════════════════════════════════════════════════════════════
    # 7. FOOTER
    # ═══════════════════════════════════════════════════════════════════
    
    lines.append("═" * 80)
    lines.append("  END OF DOJ-GRADE FORENSIC DOSSIER")
    lines.append("═" * 80)
    
    return "\n".join(lines)


def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("JLAW Phase 4 Enhanced Reporting - Sample Output Generator")
    print("=" * 80 + "\n")
    
    # Generate output
    output = generate_sample_output()
    
    # Save to file
    output_dir = Path("output/samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "sample_doj_grade_dossier.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"\n✓ Sample output generated: {output_file}")
    print(f"  File size: {len(output):,} characters")
    print(f"  Lines: {len(output.splitlines()):,}")
    
    # Display preview
    print("\n" + "=" * 80)
    print("PREVIEW (First 50 lines):")
    print("=" * 80 + "\n")
    preview_lines = output.splitlines()[:50]
    for line in preview_lines:
        print(line)
    
    if len(output.splitlines()) > 50:
        print("\n... (see full output in file) ...")
    
    print("\n" + "=" * 80)
    print("✓ Verification Complete")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())
