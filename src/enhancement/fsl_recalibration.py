"""
MODULE 5: FSL DISPOSITION RECALIBRATION ENGINE (DEF-007)

The current FSL system classifies virtually everything as "A" (likely benign).
Knight family's 17.1M share J-code transfers worth ~$1.63B at $95.20/share
are rated "D" (benign). Recalibrates dispositions based on:
  1. Transaction value thresholds
  2. Temporal clustering (multiple insiders, same date)
  3. Entity relationship patterns (J-code transfers)
  4. Year-end gift timing
  5. Late filing + repeat offender compounding
  6. 10b5-1 plan references without adoption dates
"""

from datetime import datetime
from collections import defaultdict


class FSLRecalibrationEngine:
    """Recalibrate FSL dispositions with economic value awareness."""

    FSL_LABELS = {
        'E': 'ESCALATE - Enforcement referral recommended',
        'D+': 'DEEP INVESTIGATION - Significant anomalies detected',
        'C': 'CONCERNING - Further forensic review warranted',
        'B': 'MONITOR - Ongoing pattern surveillance',
        'A': 'Likely benign (comp/admin) - document why',
    }

    @classmethod
    def build_date_clusters(cls, assessments: list) -> dict:
        """Build temporal cluster map from assessments."""
        clusters = defaultdict(lambda: {'insiders': set(), 'total_shares': 0, 'transactions': []})

        for a in assessments:
            d = a.get('transaction_date', '')
            if not d:
                continue
            clusters[d]['insiders'].add(a.get('insider_name', ''))
            clusters[d]['total_shares'] += abs(a.get('shares', 0) or 0)
            clusters[d]['transactions'].append(a)

        result = {}
        for d, c in clusters.items():
            result[d] = {
                'unique_insiders': len(c['insiders']),
                'insiders': list(c['insiders']),
                'total_shares': c['total_shares'],
                'transactions': c['transactions'],
            }
        return result

    @classmethod
    def recalibrate_dispositions(cls, fsl_assessments: list, enriched_transactions: list) -> list:
        """Recalibrate FSL dispositions with economic value awareness."""
        recalibrated = []
        date_clusters = cls.build_date_clusters(fsl_assessments)

        # Build lookup for enriched transactions
        enriched_lookup = {}
        for t in enriched_transactions:
            key = (t.get('accession_number', ''), t.get('transaction_date', ''))
            enriched_lookup[key] = t

        for assessment in fsl_assessments:
            lookup_key = (assessment.get('accession_number', ''), assessment.get('transaction_date', ''))
            enriched = enriched_lookup.get(lookup_key, {})

            new_score = assessment.get('signal_score', 0)
            escalation_reasons = list(assessment.get('disposition_reasons', []))

            # FACTOR 1: Economic value threshold escalation
            economic_benefit = enriched.get('economic_benefit', 0) or 0
            if economic_benefit > 100_000_000:
                new_score += 0.50
                escalation_reasons.append(
                    f'CRITICAL: Transaction economic value ${economic_benefit/1e6:.1f}M exceeds $100M threshold'
                )
            elif economic_benefit > 10_000_000:
                new_score += 0.35
                escalation_reasons.append(
                    f'HIGH: Transaction economic value ${economic_benefit/1e6:.1f}M exceeds $10M threshold'
                )
            elif economic_benefit > 1_000_000:
                new_score += 0.20
                escalation_reasons.append(
                    f'ELEVATED: Transaction economic value ${economic_benefit/1e3:.0f}K exceeds $1M threshold'
                )

            # FACTOR 2: Temporal clustering
            cluster = date_clusters.get(assessment.get('transaction_date', ''))
            if cluster and cluster['unique_insiders'] > 2:
                new_score += 0.15
                escalation_reasons.append(
                    f"Temporal cluster: {cluster['unique_insiders']} insiders transacted on same date "
                    f"({cluster['total_shares']:,.0f} total shares)"
                )

            # FACTOR 3: Entity relationship patterns (J-code)
            if assessment.get('transaction_code') == 'J':
                new_score += 0.25
                escalation_reasons.append(
                    'J-code entity transfer - ownership restructuring requires beneficial ownership verification'
                )

            # FACTOR 4: Large gift transactions near year-end
            if assessment.get('transaction_code') == 'G':
                try:
                    month = datetime.strptime(
                        assessment.get('transaction_date', ''), '%Y-%m-%d'
                    ).month
                    if month >= 10:  # Oct-Dec
                        new_score += 0.10
                        escalation_reasons.append(
                            'Year-end gift timing - potential tax optimization strategy'
                        )
                except (ValueError, TypeError):
                    pass

            # FACTOR 5: Late filing + repeat offender compound
            if assessment.get('is_late') and assessment.get('is_repeat_offender'):
                new_score += 0.15
                escalation_reasons.append(
                    'Compound risk: late filing by repeat offender indicates systemic compliance failure'
                )

            # FACTOR 6: 10b5-1 plan without adoption date
            if assessment.get('mentions_10b5_1') and not assessment.get('plan_adoption_date_present'):
                new_score += 0.10
                escalation_reasons.append(
                    '10b5-1 plan referenced but no adoption date disclosed - potential plan manipulation'
                )

            # Cap score at 1.0
            new_score = min(new_score, 1.0)

            # Recalculate disposition
            if new_score >= 0.70:
                new_disposition = 'E'
            elif new_score >= 0.50:
                new_disposition = 'D+'
            elif new_score >= 0.35:
                new_disposition = 'C'
            elif new_score >= 0.20:
                new_disposition = 'B'
            else:
                new_disposition = 'A'

            recalibrated.append({
                **assessment,
                'original_signal_score': assessment.get('signal_score', 0),
                'original_disposition': assessment.get('disposition', 'A'),
                'recalibrated_signal_score': round(new_score, 3),
                'recalibrated_disposition': new_disposition,
                'recalibrated_disposition_label': cls.FSL_LABELS.get(new_disposition, ''),
                'escalation_reasons': escalation_reasons,
                'economic_benefit': economic_benefit,
                'valuation_enriched': True,
            })

        return recalibrated
