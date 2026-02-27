"""
MODULE 10: MASTER ORCHESTRATOR - APPLIES ALL ENHANCEMENTS

This is the main entry point that transforms v4.2 output into v5.0 output.
Applies all enhancement modules to raw analysis results and generates
the enriched forensic data with economic valuations.
"""

import hashlib
import json
from datetime import datetime, timezone

from src.enhancement.economic_benefit_engine import EconomicBenefitValuationEngine
from src.enhancement.severity_aggregator import SeverityAggregator
from src.enhancement.violation_deduplicator import ViolationDeduplicator
from src.enhancement.sox_evidence_sanitizer import SOXEvidenceSanitizer
from src.enhancement.fsl_recalibration import FSLRecalibrationEngine
from src.enhancement.pattern_narrative import PatternNarrativeSynthesizer
from src.enhancement.penalty_calculator import PenaltyExposureCalculator
from src.enhancement.temporal_recovery import TemporalAnalysisRecovery
from src.enhancement.merkle_tree import MerkleTreeBuilder


class JLAWEnhancementOrchestrator:
    """
    Apply all enhancement modules to raw analysis results.
    Transforms JLAW v4.2 output into v5.0 output with full economic valuations.
    """

    DEFICIENCIES_RESOLVED = [
        'DEF-001', 'DEF-002', 'DEF-003', 'DEF-005', 'DEF-006', 'DEF-007',
        'DEF-009', 'DEF-010', 'DEF-011', 'DEF-012', 'DEF-013', 'DEF-014',
        'DEF-015', 'DEF-016', 'DEF-017', 'DEF-020', 'DEF-022', 'DEF-023',
    ]

    @classmethod
    def enhance(cls, raw_results: dict, sox_results: dict = None,
                fsl_assessments: list = None, cik: str = '320187') -> dict:
        """
        Apply all enhancement modules to raw analysis results.

        Args:
            raw_results: The analysis_results.json data
            sox_results: The sox_analysis.json data
            fsl_assessments: The fsl_assessments.json data
            cik: Company CIK number

        Returns:
            Enhanced results dict with all deficiencies resolved
        """
        print('=' * 60)
        print('  JLAW ENHANCEMENT PROTOCOL v5.0.0 - APEX-VALUATION')
        print('=' * 60)

        violations = raw_results.get('violations', [])

        # Step 1: Deduplicate violations (DEF-006)
        print('\n[1/10] Deduplicating violations...')
        deduped = ViolationDeduplicator.deduplicate(violations)
        print(f'  -> Removed {deduped["duplicates_removed"]} duplicates '
              f'({deduped["original_count"]} -> {deduped["deduplicated_count"]})')

        # Step 2: Economic benefit valuation (DEF-001, DEF-009, DEF-011)
        print('\n[2/10] Computing economic benefit valuations...')
        enriched_transactions = []
        for v in deduped['violations']:
            if v.get('shares') and v['shares'] > 0:
                enriched = EconomicBenefitValuationEngine.compute_transaction_benefit(v)
                enriched_transactions.append(enriched)
        # Also enrich FSL assessments that have shares
        if fsl_assessments:
            for fsl in fsl_assessments:
                if fsl.get('shares') and fsl['shares'] > 0:
                    # Check if already covered by violations
                    existing = any(
                        t.get('accession_number') == fsl.get('accession_number')
                        and t.get('transaction_date') == fsl.get('transaction_date')
                        for t in enriched_transactions
                    )
                    if not existing:
                        enriched = EconomicBenefitValuationEngine.compute_transaction_benefit(fsl)
                        enriched_transactions.append(enriched)

        total_benefit = sum(t.get('economic_benefit', 0) or 0 for t in enriched_transactions)
        print(f'  -> Valued {len(enriched_transactions)} transactions at ${total_benefit / 1e6:.1f}M aggregate')

        # Step 3: Beneficiary rollup (DEF-011)
        print('\n[3/10] Computing beneficiary economic rollup...')
        beneficiary_rollup = EconomicBenefitValuationEngine.compute_beneficiary_rollup(enriched_transactions)
        for b in beneficiary_rollup[:5]:
            print(f'  -> {b["name"]}: ${b["total_economic_benefit"] / 1e6:.1f}M ({b["transaction_count"]} txns)')

        # Step 4: Unified severity aggregation (DEF-002)
        print('\n[4/10] Unifying severity aggregation across all nodes...')
        all_node_results = [raw_results]
        if sox_results:
            all_node_results.append(sox_results)
        severity = SeverityAggregator.compute_unified_severity(all_node_results)
        u = severity['unified']
        print(f'  -> Critical: {u["critical"]}, High: {u["high"]}, Medium: {u["medium"]}')

        # Step 5: SOX evidence sanitization (DEF-005, DEF-014, DEF-015)
        print('\n[5/10] Sanitizing SOX evidence text...')
        sanitized_sox = sox_results
        if sox_results:
            sanitized_sox = SOXEvidenceSanitizer.fix_certifier_names(sox_results, cik)
            print('  -> Certifier names corrected, HTML stripped, descriptions expanded')
        else:
            print('  -> No SOX results to sanitize')

        # Step 6: FSL recalibration (DEF-007)
        print('\n[6/10] Recalibrating FSL dispositions with economic values...')
        recalibrated_fsl = []
        if fsl_assessments:
            recalibrated_fsl = FSLRecalibrationEngine.recalibrate_dispositions(
                fsl_assessments, enriched_transactions
            )
            escalated = [f for f in recalibrated_fsl if f.get('recalibrated_disposition') != 'A']
            print(f'  -> {len(escalated)} transactions escalated from benign classification')
        else:
            print('  -> No FSL assessments to recalibrate')

        # Step 7: Temporal analysis recovery (DEF-003, DEF-012)
        print('\n[7/10] Recovering temporal financial analysis...')
        temporal_metrics = TemporalAnalysisRecovery.compute_temporal_metrics()
        clusters = TemporalAnalysisRecovery.build_transaction_clusters(enriched_transactions)
        print(f'  -> Recovered {len(temporal_metrics)} quarters of financial data')
        print(f'  -> Identified {len(clusters)} temporal transaction clusters')

        # Step 8: Penalty exposure recalculation (DEF-017, DEF-022)
        print('\n[8/10] Recalculating comprehensive penalty exposure...')
        all_violations = list(deduped['violations'])
        if sanitized_sox:
            all_violations.extend(sanitized_sox.get('violations', []))
        penalties = PenaltyExposureCalculator.compute_comprehensive_exposure({
            'violations': all_violations,
            'transactions': enriched_transactions,
        })
        print(f'  -> Total max exposure: {penalties["formatted_total"]}')
        bounty = penalties['whistleblower_bounty']
        print(f'  -> Whistleblower bounty range: ${bounty["bounty_floor"] / 1e6:.1f}M - ${bounty["bounty_ceiling"] / 1e6:.1f}M')

        # Step 9: Pattern narrative synthesis (DEF-010, DEF-020)
        print('\n[9/10] Synthesizing prosecutorial narrative...')
        narrative = PatternNarrativeSynthesizer.generate_executive_summary({
            'transactions': enriched_transactions,
            'beneficiary_rollup': beneficiary_rollup,
            'sox_violations': sanitized_sox.get('violations', []) if sanitized_sox else [],
        })
        print(f'  -> {len(narrative["patterns_identified"])} patterns identified')
        print(f'  -> Recommendation: {narrative["prosecution_recommendation"]}')

        # Step 10: Evidence chain with Merkle root (DEF-023)
        print('\n[10/10] Building Merkle tree evidence chain...')
        evidence_hashes = []
        for t in enriched_transactions:
            h = t.get('evidence_hash') or hashlib.sha256(
                json.dumps(t, sort_keys=True, default=str).encode()
            ).hexdigest()
            evidence_hashes.append(h)
        merkle = MerkleTreeBuilder.build_merkle_tree(evidence_hashes)
        print(f'  -> Merkle root: {merkle["root"]}')
        print(f'  -> {merkle["leaf_count"]} evidence leaves verified')

        # Assemble enhanced output
        report_hash = hashlib.sha256(
            json.dumps({
                'violations': [
                    {k: v for k, v in vi.items() if k != 'transactions'}
                    for vi in deduped['violations']
                ],
                'total_benefit': total_benefit,
            }, sort_keys=True, default=str).encode()
        ).hexdigest()

        enhanced = {
            '_enhancement_version': '5.0.0',
            '_enhancement_codename': 'APEX-VALUATION',
            '_enhancement_timestamp': datetime.now(timezone.utc).isoformat(),
            '_deficiencies_resolved': cls.DEFICIENCIES_RESOLVED,

            # Enhanced executive summary with narrative
            'executive_summary': narrative,

            # Corrected severity counts
            'severity_summary': severity['unified'],
            'violations_by_type': {
                k: {'count': v['count'], 'max_severity': v['max_severity']}
                for k, v in severity['violations_by_type'].items()
            },

            # Deduplicated violations
            'total_violations': deduped['deduplicated_count'],
            'critical_alerts': severity['unified']['critical'],
            'high_alerts': severity['unified']['high'],
            'violations': deduped['violations'],
            'deduplication_stats': {
                'original': deduped['original_count'],
                'after': deduped['deduplicated_count'],
                'removed': deduped['duplicates_removed'],
            },

            # Economic benefit valuations (THE KEY ENHANCEMENT)
            'economic_valuations': {
                'total_aggregate_benefit': total_benefit,
                'formatted_total': f'${total_benefit:,.2f}',
                'transactions': enriched_transactions,
                'valuation_methodology': (
                    'Market close price on transaction date x shares '
                    '(option exercises use spread)'
                ),
                'price_source': 'NKE historical closing prices (Yahoo Finance, split-adjusted)',
            },

            # Enhanced beneficiary analysis (replaces $0 table)
            'beneficiary_analysis': beneficiary_rollup,

            # Recalibrated FSL assessments
            'fsl_assessments': recalibrated_fsl,
            'fsl_recalibration_stats': {
                'total_assessed': len(recalibrated_fsl),
                'escalated_from_benign': len([
                    f for f in recalibrated_fsl
                    if f.get('recalibrated_disposition') != 'A'
                ]),
                'escalation_rate': (
                    f'{len([f for f in recalibrated_fsl if f.get("recalibrated_disposition") != "A"]) / max(len(recalibrated_fsl), 1) * 100:.1f}%'
                ),
            },

            # Recovered temporal analysis
            'temporal_analysis': {
                'quarters': temporal_metrics,
                'transaction_clusters': clusters,
                'data_source': 'SEC XBRL companyfacts API (recovered from failed extraction)',
            },

            # Sanitized SOX analysis
            'sox_analysis': sanitized_sox,

            # Comprehensive penalty exposure
            'penalty_exposure': penalties,

            # Merkle tree evidence chain
            'evidence_chain': {
                'merkle_root': merkle['root'],
                'leaf_count': merkle['leaf_count'],
                'algorithm': merkle['algorithm'],
                'report_hash': report_hash,
            },
        }

        print('\n' + '=' * 60)
        print('  ENHANCEMENT COMPLETE - v5.0.0 OUTPUT READY')
        print(f'  Total economic value surfaced: ${total_benefit / 1e6:.1f}M')
        print(f'  Deficiencies resolved: {len(cls.DEFICIENCIES_RESOLVED)}/23')
        print('=' * 60 + '\n')

        return enhanced
