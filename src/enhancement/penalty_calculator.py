"""
MODULE 7: PENALTY EXPOSURE RECALCULATOR (DEF-017, DEF-022)

Current penalty estimation is flat ($25K per late filing, nothing else).
Must account for: per-violation SOX criminal exposure, disgorgement of
economic benefit, treble damages, whistleblower bounty estimation.
"""


class PenaltyExposureCalculator:
    """Compute comprehensive penalty exposure including disgorgement and bounty."""

    @classmethod
    def compute_comprehensive_exposure(cls, enriched_results: dict) -> dict:
        civil_minimum = 0
        civil_maximum = 0
        criminal_exposure = {'max_fine': 0, 'max_years': 0}
        estimated_disgorgement = 0
        penalty_breakdown = []

        violations = enriched_results.get('violations', [])
        transactions = enriched_results.get('transactions', [])

        # Section 16(a) late filing penalties
        late_filings = [
            v for v in violations
            if v.get('type') == 'Section 16(a) Late Form 4 Filing'
            or v.get('violation_type') == 'Section 16(a) Late Form 4 Filing'
        ]
        if late_filings:
            late_min = len(late_filings) * 5_000
            late_max = len(late_filings) * 25_000
            civil_minimum += late_min
            civil_maximum += late_max
            penalty_breakdown.append({
                'category': 'Section 16(a) Late Filing',
                'count': len(late_filings),
                'min_per_violation': 5_000,
                'max_per_violation': 25_000,
                'total_min': late_min,
                'total_max': late_max,
                'statutory_basis': '15 U.S.C. 78u-2(b)',
            })

        # SOX 302 certification omissions
        sox302 = [
            v for v in violations
            if 'section_302' in (v.get('violation_type') or v.get('type') or '')
        ]
        if sox302:
            civil_minimum += len(sox302) * 100_000
            civil_maximum += len(sox302) * 500_000
            penalty_breakdown.append({
                'category': 'SOX 302 Certification Omission',
                'count': len(sox302),
                'total_min': len(sox302) * 100_000,
                'total_max': len(sox302) * 500_000,
                'statutory_basis': 'SOX 302, 17 CFR 240.13a-14(a)',
            })

        # SOX 906 criminal exposure
        sox906 = [
            v for v in violations
            if 'section_906' in (v.get('violation_type') or v.get('type') or '')
        ]
        if sox906:
            criminal_exposure['max_fine'] += 5_000_000
            criminal_exposure['max_years'] = max(criminal_exposure['max_years'], 20)
            penalty_breakdown.append({
                'category': 'SOX 906 Certification - Criminal',
                'count': len(sox906),
                'criminal_knowing': '$1M fine, up to 10 years',
                'criminal_willful': '$5M fine, up to 20 years',
                'statutory_basis': '18 USC 1350',
            })

        # Disgorgement based on economic benefit
        total_economic_benefit = sum(t.get('economic_benefit', 0) or 0 for t in transactions)
        estimated_disgorgement = total_economic_benefit
        if total_economic_benefit > 0:
            penalty_breakdown.append({
                'category': 'Estimated Disgorgement',
                'amount': total_economic_benefit,
                'basis': 'Total economic benefit from insider transactions',
                'note': 'Disgorgement limited to net profits per Liu v. SEC (2020)',
            })

        # Civil penalty multiplier (SEC can seek up to 3x disgorgement)
        treble_damages = total_economic_benefit * 3
        civil_maximum += treble_damages
        if treble_damages > 0:
            penalty_breakdown.append({
                'category': 'Civil Penalty (3x Disgorgement)',
                'amount': treble_damages,
                'statutory_basis': '15 U.S.C. 78u-1(a)(2) - treble damages',
            })

        # Whistleblower bounty estimation
        total_sanctions = civil_maximum + estimated_disgorgement
        bounty_estimate = {
            'sanctions_basis': total_sanctions,
            'bounty_floor': round(total_sanctions * 0.10, 2),
            'bounty_ceiling': round(total_sanctions * 0.30, 2),
            'estimated_bounty_midpoint': round(total_sanctions * 0.20, 2),
            'eligibility_note': (
                'SEC Rule 21F - bounty requires original information leading '
                'to successful enforcement action with sanctions exceeding $1M'
            ),
        }

        total_max = civil_maximum + estimated_disgorgement + criminal_exposure['max_fine']

        return {
            'civil_penalty_range': {
                'minimum': civil_minimum,
                'maximum': civil_maximum,
                'formatted_min': f'${civil_minimum:,.0f}',
                'formatted_max': f'${civil_maximum:,.0f}',
            },
            'criminal_exposure': criminal_exposure,
            'estimated_disgorgement': {
                'amount': estimated_disgorgement,
                'formatted': f'${estimated_disgorgement:,.0f}',
            },
            'whistleblower_bounty': bounty_estimate,
            'penalty_breakdown': penalty_breakdown,
            'total_maximum_exposure': total_max,
            'formatted_total': f'${total_max:,.0f}',
        }
