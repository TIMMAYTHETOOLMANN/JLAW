"""
Forensic Tracing Orchestrator
==============================

Coordinates all six forensic tracing domains into a unified analysis pipeline.
Processes existing JLAW forensic output files and generates comprehensive
tracing results.

Pipeline stages:
  1. Load and enrich existing analysis results
  2. Domain 1: Classify all footnotes by risk category
  3. Domain 2: Trace grant-to-sale liquidation chains
  4. Domain 3: Resolve beneficial ownership with dual test + parking detection
  5. Domain 4: Correlate Form 144 notices (when available)
  6. Domain 5: Build two-tier documentation (TCR + work product)
  7. Domain 6: Generate visualization specifications
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.forensic_tracing.domain1_footnote_classifier import FootnoteClassifier
from src.forensic_tracing.domain2_grant_to_sale import GrantToSaleTracer
from src.forensic_tracing.domain3_ownership_resolver import (
    EnhancedOwnershipResolver,
    ParkingDetector,
)
from src.forensic_tracing.domain4_form144 import Form144CorrelationEngine
from src.forensic_tracing.domain5_documentation import TwoTierDocumentationFramework
from src.forensic_tracing.domain6_visualization import CourtroomVisualizationSpec


class ForensicTracingOrchestrator:
    """
    Master orchestrator for the six-domain forensic tracing system.
    """

    @classmethod
    def run_full_analysis(cls, enhanced_results: dict,
                          fsl_assessments: list = None,
                          form144_notices: list = None) -> dict:
        """
        Run the complete forensic tracing pipeline.

        Args:
            enhanced_results: Output from JLAWEnhancementOrchestrator.enhance()
            fsl_assessments: FSL assessment records (with footnotes, entity data)
            form144_notices: Optional Form 144 notice records

        Returns:
            Complete forensic tracing results across all six domains
        """
        print('\n' + '=' * 64)
        print('  FORENSIC TRACING SYSTEM — SIX-DOMAIN ANALYSIS')
        print('  From $0 Acquisition to Cash Liquidation')
        print('=' * 64)

        # Collect all transactions from enhanced results
        transactions = enhanced_results.get('economic_valuations', {}).get('transactions', [])
        violations = enhanced_results.get('violations', [])
        all_records = fsl_assessments or []

        # ===============================================================
        # DOMAIN 1: Footnote Classification
        # ===============================================================
        print('\n[Domain 1] Classifying Form 4 footnotes...')
        footnote_results = cls._run_domain1(all_records)
        print(f'  -> {footnote_results["total_footnotes"]} footnotes classified')
        print(f'  -> Risk distribution: {footnote_results.get("risk_distribution", {})}')

        # ===============================================================
        # DOMAIN 2: Grant-to-Sale Tracing
        # ===============================================================
        print('\n[Domain 2] Tracing grant-to-sale liquidation chains...')
        # Use FSL records as primary (they have transaction_code field).
        # Enrich FSL records with economic benefit data from enhanced transactions.
        enriched_lookup = {}
        for t in transactions:
            key = (t.get('accession_number', ''), t.get('transaction_date', ''))
            enriched_lookup[key] = t

        all_txns = []
        seen_keys = set()
        for r in all_records:
            key = (r.get('accession_number', ''), r.get('transaction_date', ''))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            # Enrich with economic data if available
            enriched = enriched_lookup.get(key, {})
            merged = {**r}
            if enriched.get('economic_benefit'):
                merged['economic_benefit'] = enriched['economic_benefit']
                merged['market_price_on_date'] = enriched.get('market_price_on_date')
            all_txns.append(merged)

        # Add any enhanced transactions not in FSL
        for t in transactions:
            key = (t.get('accession_number', ''), t.get('transaction_date', ''))
            if key not in seen_keys:
                all_txns.append(t)
                seen_keys.add(key)

        tracing_results = GrantToSaleTracer.trace_all(all_txns)
        print(f'  -> {tracing_results["chains_constructed"]} chains constructed')
        print(f'  -> {tracing_results["complete_chains"]} complete, '
              f'{tracing_results["incomplete_chains"]} incomplete')
        print(f'  -> Total acquisition market value: ${tracing_results["total_acquisition_market_value"]:,.2f}')
        print(f'  -> Liquidation rate: {tracing_results["overall_liquidation_rate"]:.1%}')
        if tracing_results['obfuscation_vector_chains'] > 0:
            print(f'  -> Obfuscation vectors (A->G/J): {tracing_results["obfuscation_vector_chains"]}')

        # ===============================================================
        # DOMAIN 3: Beneficial Ownership Resolution
        # ===============================================================
        print('\n[Domain 3] Resolving beneficial ownership chains...')
        ownership_results = cls._run_domain3(all_records, transactions)
        print(f'  -> {len(ownership_results["dual_test_results"])} entity relationships tested')
        print(f'  -> {len(ownership_results["parking_analyses"])} parking analyses performed')
        bo_count = sum(
            1 for t in ownership_results['dual_test_results']
            if t.get('overall_beneficial_owner')
        )
        print(f'  -> {bo_count} determined beneficial owners')

        # ===============================================================
        # DOMAIN 4: Form 144 Correlation
        # ===============================================================
        print('\n[Domain 4] Correlating Form 144 notices...')
        if form144_notices:
            form144_parsed = cls._parse_form144(form144_notices)
            form144_results = Form144CorrelationEngine.correlate(
                form144_parsed, all_txns
            )
            print(f'  -> {form144_results["total_notices"]} notices correlated')
            print(f'  -> Execution rate: {form144_results["execution_rate"]:.1%}')
        else:
            form144_results = {
                'total_notices': 0,
                'note': 'No Form 144 notices provided. Form 144 electronic filing '
                        'became mandatory April 13, 2023. For pre-2023 analysis periods, '
                        'Form 144 data is limited to paper filings.',
                'correlations': [],
            }
            print('  -> No Form 144 notices available (pre-electronic filing era)')

        # ===============================================================
        # DOMAIN 5: Two-Tier Documentation
        # ===============================================================
        print('\n[Domain 5] Building two-tier documentation framework...')
        tcr = TwoTierDocumentationFramework.build_tcr_from_analysis(enhanced_results)
        work_products = TwoTierDocumentationFramework.build_work_product(enhanced_results)
        print(f'  -> TCR submission built with {tcr.exhibit_count} exhibits')
        print(f'  -> {len(work_products)} work product documents generated')
        print(f'  -> Statutory references: {len(tcr.statutory_references)}')

        # ===============================================================
        # DOMAIN 6: Visualization Specifications
        # ===============================================================
        print('\n[Domain 6] Generating visualization specifications...')
        chart_specs = CourtroomVisualizationSpec.get_all_chart_specs()
        cover_spec = CourtroomVisualizationSpec.get_cover_page_spec()
        new_sections = CourtroomVisualizationSpec.get_new_sections()
        mpl_config = CourtroomVisualizationSpec.get_matplotlib_config()
        print(f'  -> {len(chart_specs)} chart specifications generated')
        print(f'  -> {len(new_sections)} new PDF sections specified')

        # ===============================================================
        # Assemble complete results
        # ===============================================================
        report_hash = hashlib.sha256(
            json.dumps({
                'footnotes': footnote_results.get('total_footnotes'),
                'chains': tracing_results.get('chains_constructed'),
                'ownership': len(ownership_results.get('dual_test_results', [])),
            }, default=str).encode()
        ).hexdigest()

        result = {
            '_system': 'JLAW Forensic Tracing System',
            '_version': '1.0.0',
            '_timestamp': datetime.now(timezone.utc).isoformat(),
            '_domains': [
                'D1: Form 4 Footnote Classification',
                'D2: Grant-to-Sale Transaction Tracing',
                'D3: Beneficial Ownership Chain Resolution',
                'D4: Form 144 Correlation',
                'D5: Two-Tier Documentation Framework',
                'D6: Courtroom-Grade Visualization',
            ],
            '_report_hash': report_hash,

            'domain1_footnotes': footnote_results,
            'domain2_tracing': {
                'summary': {
                    'chains_constructed': tracing_results['chains_constructed'],
                    'complete_chains': tracing_results['complete_chains'],
                    'incomplete_chains': tracing_results['incomplete_chains'],
                    'acquisition_only_chains': tracing_results['acquisition_only_chains'],
                    'insiders_tracked': tracing_results['insiders_tracked'],
                    'total_shares_acquired': tracing_results['total_shares_acquired'],
                    'total_acquisition_market_value': tracing_results['total_acquisition_market_value'],
                    'total_shares_sold': tracing_results['total_shares_sold'],
                    'liquidation_rate': tracing_results['overall_liquidation_rate'],
                    'total_profit': tracing_results['total_profit'],
                    'chain_type_distribution': tracing_results['chain_type_distribution'],
                    'obfuscation_vectors': tracing_results['obfuscation_vector_chains'],
                    'note': tracing_results.get('note', ''),
                },
                'chains': tracing_results['chains'],
            },
            'domain3_ownership': ownership_results,
            'domain4_form144': form144_results,
            'domain5_documentation': {
                'tcr_submission': tcr.to_dict(),
                'tcr_exhibit_count': tcr.exhibit_count,
                'tcr_violation_types': tcr.violation_types,
                'tcr_statutory_references': tcr.statutory_references,
                'work_product_count': len(work_products),
                'work_product_ids': [wp.document_id for wp in work_products],
                'tier_separation_note': (
                    'Tier 1 (TCR) contains only verified factual findings. '
                    'Tier 2 (work product) contains scoring, bounty estimates, '
                    'and strategic analysis — never submitted to SEC.'
                ),
            },
            'domain6_visualization': {
                'chart_specs': [s.to_dict() for s in chart_specs],
                'cover_page_spec': cover_spec,
                'new_sections': new_sections,
                'matplotlib_config': mpl_config,
                'palette': {
                    'name': 'Okabe-Ito',
                    'wcag_compliant': True,
                    'grayscale_safe': True,
                },
            },
        }

        print('\n' + '=' * 64)
        print('  FORENSIC TRACING ANALYSIS COMPLETE')
        print(f'  Domains executed:       6/6')
        print(f'  Footnotes classified:   {footnote_results["total_footnotes"]}')
        print(f'  Chains constructed:     {tracing_results["chains_constructed"]}')
        print(f'  Ownership tests:        {len(ownership_results["dual_test_results"])}')
        print(f'  TCR exhibits:           {tcr.exhibit_count}')
        print(f'  Chart specs:            {len(chart_specs)}')
        print('=' * 64 + '\n')

        return result

    @classmethod
    def _run_domain1(cls, fsl_assessments: list) -> dict:
        """Run Domain 1 footnote classification on FSL assessment records."""
        all_classifications = []

        for record in fsl_assessments:
            # Extract footnotes from the record
            footnotes = {}
            raw_footnotes = record.get('footnotes', [])
            if isinstance(raw_footnotes, list):
                for i, fn in enumerate(raw_footnotes):
                    if isinstance(fn, str):
                        footnotes[f'F{i+1}'] = fn
            elif isinstance(raw_footnotes, dict):
                footnotes = raw_footnotes

            if not footnotes:
                # Create synthetic footnote entry for records with footnote_present flag
                if record.get('footnote_present'):
                    footnotes = {'F1': f'Footnote present but text not extracted for '
                                       f'{record.get("insider_name", "unknown")} '
                                       f'{record.get("transaction_code", "")} transaction'}

            code = record.get('transaction_code', '')
            codes_map = {fid: code for fid in footnotes}

            classifications = FootnoteClassifier.classify_all_footnotes(
                footnotes, codes_map
            )
            all_classifications.extend(classifications)

        return FootnoteClassifier.generate_risk_summary(all_classifications)

    @classmethod
    def _run_domain3(cls, fsl_assessments: list, transactions: list) -> dict:
        """Run Domain 3 ownership resolution and parking detection."""
        dual_test_results = []
        parking_analyses = []

        # Identify entity transfers (J-code and G-code)
        entity_transfers = [
            t for t in (transactions + fsl_assessments)
            if (t.get('transaction_code') or '').upper() in ('J', 'G')
        ]

        for txn in entity_transfers:
            name = txn.get('reporting_owner') or txn.get('insider_name') or ''
            cik = txn.get('reporting_owner_cik') or txn.get('insider_cik') or ''
            shares = abs(txn.get('shares', 0) or 0)
            code = (txn.get('transaction_code') or '').upper()

            # Determine entity type from available data
            entity_type = 'LLC'  # Default
            security_title = txn.get('security_title', '')
            if 'trust' in name.lower():
                entity_type = 'Trust_Revocable'
            elif 'llc' in name.lower() or 'swoosh' in name.lower():
                entity_type = 'LLC'
            elif 'foundation' in name.lower():
                entity_type = 'Foundation'
            elif 'lp' in name.lower() or 'partnership' in name.lower():
                entity_type = 'FLP'
            elif 'grat' in name.lower():
                entity_type = 'GRAT'

            # Apply dual beneficial ownership test
            test = EnhancedOwnershipResolver.apply_dual_test(
                entity_name=name,
                entity_type=entity_type,
                insider_name=name,
                insider_cik=cik,
                shares=shares,
                footnotes=txn.get('footnotes', []),
            )
            dual_test_results.append(test.to_dict())

        # Run parking detection
        parking = ParkingDetector.analyze_for_parking(entity_transfers)
        parking_analyses = [p.to_dict() for p in parking]

        return {
            'dual_test_results': dual_test_results,
            'parking_analyses': parking_analyses,
            'entity_transfers_analyzed': len(entity_transfers),
            'beneficial_owners_identified': sum(
                1 for t in dual_test_results if t.get('overall_beneficial_owner')
            ),
            'parking_risk_flags': sum(
                len(p.get('red_flags', [])) for p in parking_analyses
            ),
        }

    @classmethod
    def _parse_form144(cls, notices: list):
        """Parse raw Form 144 notice data into Form144Notice objects."""
        from src.forensic_tracing.domain4_form144 import Form144Notice

        parsed = []
        for n in notices:
            parsed.append(Form144Notice(
                accession_number=n.get('accession_number', ''),
                filing_date=n.get('filing_date', ''),
                filer_cik=n.get('filer_cik', ''),
                filer_name=n.get('filer_name', ''),
                issuer_cik=n.get('issuer_cik', ''),
                issuer_name=n.get('issuer_name', ''),
                security_title=n.get('security_title', ''),
                shares_to_be_sold=n.get('shares_to_be_sold', 0),
                approximate_sale_date=n.get('approximate_sale_date'),
                aggregate_market_value=n.get('aggregate_market_value', 0),
                date_acquired=n.get('date_acquired'),
                nature_of_acquisition=n.get('nature_of_acquisition'),
                acquired_from=n.get('acquired_from'),
                broker_name=n.get('broker_name'),
                has_10b5_1_plan=n.get('has_10b5_1_plan', False),
                plan_adoption_date=n.get('plan_adoption_date'),
                prior_3month_shares_sold=n.get('prior_3month_shares_sold', 0),
            ))
        return parsed
