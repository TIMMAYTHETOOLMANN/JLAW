"""
Domain 4: Form 144 Correlation Engine
=======================================

Form 144 (Notice of Proposed Sale under Rule 144) is the early warning system
for insider liquidation. Since April 13, 2023, Form 144 must be filed
electronically on EDGAR in structured XML format.

The forensic time-series chain:
  Form 4 Acquisition -> Form 144 Notice -> Form 4 Disposition

Matching dimensions:
  1. Issuer CIK
  2. Filer/reporting person CIK
  3. Security class title
  4. Acquisition date cross-referenced against Table I "Date Acquired"
  5. Nature of acquisition matching Form 4 transaction codes

Key metrics:
  - Liquidation rate: % of acquired shares subsequently noticed for sale
  - Execution rate: % of Form 144 notices followed by actual Form 4 dispositions
  - Time-to-liquidation: days from acquisition to Form 144 filing
  - Opacity rate: 52.4% of aborted Form 144 signals are statistically
    indistinguishable from routine executions (Neupane 2026, arXiv)

Unique Form 144 intelligence not in Form 4:
  - Table I: date acquired, nature of acquisition, person from whom acquired
  - Broker/dealer information
  - Rule 10b5-1 plan adoption dates
  - Approximate date of sale and aggregate market value
  - Table II: all securities sold in preceding 3 months

References:
  - SEC Rule 144 (17 CFR 230.144)
  - EDGAR 144 Submission Taxonomy Version 2.0
  - Neupane (2026) "Opacity in Form 144" arXiv
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict


@dataclass
class Form144Notice:
    """Parsed Form 144 filing data."""
    accession_number: str
    filing_date: str
    filer_cik: str
    filer_name: str
    issuer_cik: str
    issuer_name: str
    security_title: str
    shares_to_be_sold: float
    approximate_sale_date: Optional[str] = None
    aggregate_market_value: float = 0

    # Table I fields (unique to Form 144)
    date_acquired: Optional[str] = None
    nature_of_acquisition: Optional[str] = None  # e.g., "Stock option exercise"
    acquired_from: Optional[str] = None  # Person/entity from whom acquired

    # Broker information
    broker_name: Optional[str] = None
    broker_address: Optional[str] = None

    # 10b5-1 plan info
    has_10b5_1_plan: bool = False
    plan_adoption_date: Optional[str] = None

    # Table II: prior 3-month sales
    prior_3month_shares_sold: float = 0
    prior_3month_sale_dates: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'accession_number': self.accession_number,
            'filing_date': self.filing_date,
            'filer_name': self.filer_name,
            'filer_cik': self.filer_cik,
            'issuer_name': self.issuer_name,
            'security_title': self.security_title,
            'shares_to_be_sold': self.shares_to_be_sold,
            'approximate_sale_date': self.approximate_sale_date,
            'aggregate_market_value': self.aggregate_market_value,
            'date_acquired': self.date_acquired,
            'nature_of_acquisition': self.nature_of_acquisition,
            'acquired_from': self.acquired_from,
            'broker_name': self.broker_name,
            'has_10b5_1_plan': self.has_10b5_1_plan,
            'plan_adoption_date': self.plan_adoption_date,
            'prior_3month_shares_sold': self.prior_3month_shares_sold,
        }


@dataclass
class Form144Correlation:
    """Correlation between Form 144 notice, Form 4 acquisition, and Form 4 disposition."""
    correlation_id: str
    form_144: Form144Notice
    form4_acquisition: Optional[dict] = None  # Matched Form 4 acquisition event
    form4_disposition: Optional[dict] = None  # Matched Form 4 sale event
    match_confidence: float = 0.0  # 0.0 to 1.0

    # Computed metrics
    days_acquisition_to_notice: Optional[int] = None
    days_notice_to_sale: Optional[int] = None
    was_executed: bool = False  # Did the noticed sale actually occur?
    execution_share_ratio: float = 0.0  # Shares sold / shares noticed
    profit_on_sale: float = 0.0

    # Risk signals
    signals: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'correlation_id': self.correlation_id,
            'form_144': self.form_144.to_dict(),
            'form4_acquisition_accession': (
                self.form4_acquisition.get('accession_number', '')
                if self.form4_acquisition else None
            ),
            'form4_disposition_accession': (
                self.form4_disposition.get('accession_number', '')
                if self.form4_disposition else None
            ),
            'match_confidence': round(self.match_confidence, 3),
            'days_acquisition_to_notice': self.days_acquisition_to_notice,
            'days_notice_to_sale': self.days_notice_to_sale,
            'was_executed': self.was_executed,
            'execution_share_ratio': round(self.execution_share_ratio, 4),
            'profit_on_sale': round(self.profit_on_sale, 2),
            'signals': self.signals,
        }


class Form144CorrelationEngine:
    """
    Cross-correlate Form 144 notices with Form 4 filings to trace
    the complete acquisition -> notice -> sale chain.
    """

    @classmethod
    def correlate(cls, form144_notices: List[Form144Notice],
                  form4_transactions: list) -> Dict:
        """
        Match Form 144 notices to Form 4 transactions.

        Args:
            form144_notices: List of parsed Form 144 filings
            form4_transactions: List of Form 4 transaction records

        Returns:
            Dict with correlations and summary statistics
        """
        correlations = []
        correlation_counter = 0

        # Index Form 4 transactions by insider
        by_insider = {}
        for txn in form4_transactions:
            name = (txn.get('reporting_owner') or txn.get('insider_name') or '').upper()
            cik = txn.get('reporting_owner_cik') or txn.get('insider_cik') or ''
            by_insider.setdefault(name, []).append(txn)
            if cik:
                by_insider.setdefault(cik, []).append(txn)

        for notice in form144_notices:
            correlation_counter += 1
            correlation = Form144Correlation(
                correlation_id=f'F144-CORR-{correlation_counter:04d}',
                form_144=notice,
            )

            # Find matching Form 4 transactions
            insider_key = notice.filer_name.upper()
            insider_txns = by_insider.get(insider_key, [])
            if not insider_txns:
                insider_txns = by_insider.get(notice.filer_cik, [])

            # Match acquisition event
            acq_match = cls._match_acquisition(notice, insider_txns)
            if acq_match:
                correlation.form4_acquisition = acq_match['transaction']
                correlation.match_confidence += acq_match['confidence']

                # Compute days from acquisition to notice
                try:
                    acq_date = datetime.strptime(
                        acq_match['transaction'].get('transaction_date', ''), '%Y-%m-%d'
                    )
                    notice_date = datetime.strptime(notice.filing_date, '%Y-%m-%d')
                    correlation.days_acquisition_to_notice = (notice_date - acq_date).days
                except (ValueError, TypeError):
                    pass

            # Match disposition event (sale within 90 days of notice)
            disp_match = cls._match_disposition(notice, insider_txns)
            if disp_match:
                correlation.form4_disposition = disp_match['transaction']
                correlation.was_executed = True
                correlation.match_confidence += disp_match['confidence']

                disp_shares = abs(
                    disp_match['transaction'].get('shares', 0) or 0
                )
                if notice.shares_to_be_sold > 0:
                    correlation.execution_share_ratio = (
                        disp_shares / notice.shares_to_be_sold
                    )

                # Compute days from notice to sale
                try:
                    notice_date = datetime.strptime(notice.filing_date, '%Y-%m-%d')
                    sale_date = datetime.strptime(
                        disp_match['transaction'].get('transaction_date', ''), '%Y-%m-%d'
                    )
                    correlation.days_notice_to_sale = (sale_date - notice_date).days
                except (ValueError, TypeError):
                    pass

                # Compute profit
                sale_price = disp_match['transaction'].get('price_per_share', 0) or 0
                acq_price = 0
                if acq_match:
                    acq_price = (
                        acq_match['transaction'].get('exercise_price', 0)
                        or acq_match['transaction'].get('price_per_share', 0)
                        or 0
                    )
                correlation.profit_on_sale = (sale_price - acq_price) * disp_shares

            # Risk signals
            cls._assess_signals(correlation)

            correlation.match_confidence = min(correlation.match_confidence, 1.0)
            correlations.append(correlation)

        # Summary statistics
        executed = [c for c in correlations if c.was_executed]
        aborted = [c for c in correlations if not c.was_executed]

        return {
            'total_notices': len(form144_notices),
            'correlations': [c.to_dict() for c in correlations],
            'execution_rate': (
                len(executed) / len(correlations) if correlations else 0
            ),
            'abort_rate': (
                len(aborted) / len(correlations) if correlations else 0
            ),
            'average_days_to_notice': cls._safe_avg([
                c.days_acquisition_to_notice for c in correlations
                if c.days_acquisition_to_notice is not None
            ]),
            'average_days_notice_to_sale': cls._safe_avg([
                c.days_notice_to_sale for c in executed
                if c.days_notice_to_sale is not None
            ]),
            'total_shares_noticed': sum(n.shares_to_be_sold for n in form144_notices),
            'total_shares_executed': sum(
                abs(c.form4_disposition.get('shares', 0) or 0)
                for c in executed if c.form4_disposition
            ),
            'total_profit': sum(c.profit_on_sale for c in executed),
            'high_risk_correlations': [
                c.to_dict() for c in correlations if len(c.signals) >= 2
            ],
        }

    @classmethod
    def _match_acquisition(cls, notice: Form144Notice,
                           transactions: list) -> Optional[dict]:
        """Match Form 144 to its originating Form 4 acquisition."""
        best_match = None
        best_confidence = 0.0

        for txn in transactions:
            code = (txn.get('transaction_code') or '').upper()
            if code not in ('A', 'M', 'G', 'J', 'P', 'C'):
                continue

            confidence = 0.0

            # Match security title
            txn_title = (txn.get('security_title') or '').lower()
            notice_title = (notice.security_title or '').lower()
            if txn_title and notice_title and (
                txn_title in notice_title or notice_title in txn_title
            ):
                confidence += 0.30

            # Match acquisition date to Form 144 Table I
            if notice.date_acquired and txn.get('transaction_date') == notice.date_acquired:
                confidence += 0.40

            # Match acquisition type
            nature = (notice.nature_of_acquisition or '').lower()
            if code == 'M' and ('option' in nature or 'exercise' in nature):
                confidence += 0.20
            elif code == 'A' and ('award' in nature or 'grant' in nature):
                confidence += 0.20
            elif code == 'G' and 'gift' in nature:
                confidence += 0.20

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {'transaction': txn, 'confidence': confidence}

        return best_match

    @classmethod
    def _match_disposition(cls, notice: Form144Notice,
                           transactions: list) -> Optional[dict]:
        """Match Form 144 to the actual Form 4 sale within 90 days."""
        best_match = None
        best_confidence = 0.0

        try:
            notice_date = datetime.strptime(notice.filing_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

        window_end = notice_date + timedelta(days=90)

        for txn in transactions:
            code = (txn.get('transaction_code') or '').upper()
            if code not in ('S', 'F', 'D'):
                continue

            try:
                txn_date = datetime.strptime(
                    txn.get('transaction_date', ''), '%Y-%m-%d'
                )
            except (ValueError, TypeError):
                continue

            # Must be within 90-day window after notice
            if txn_date < notice_date or txn_date > window_end:
                continue

            confidence = 0.30  # Base confidence for date match

            # Match security title
            txn_title = (txn.get('security_title') or '').lower()
            notice_title = (notice.security_title or '').lower()
            if txn_title and notice_title and (
                txn_title in notice_title or notice_title in txn_title
            ):
                confidence += 0.30

            # Share count similarity
            noticed_shares = notice.shares_to_be_sold
            actual_shares = abs(txn.get('shares', 0) or 0)
            if noticed_shares > 0 and actual_shares > 0:
                ratio = min(actual_shares, noticed_shares) / max(actual_shares, noticed_shares)
                confidence += ratio * 0.30

            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {'transaction': txn, 'confidence': confidence}

        return best_match

    @classmethod
    def _assess_signals(cls, correlation: Form144Correlation):
        """Assess risk signals for a correlation."""
        notice = correlation.form_144

        # Signal: rapid liquidation after acquisition
        if (correlation.days_acquisition_to_notice is not None
                and correlation.days_acquisition_to_notice <= 30):
            correlation.signals.append(
                f'Rapid liquidation: only {correlation.days_acquisition_to_notice} days '
                f'from acquisition to Form 144 notice'
            )

        # Signal: large sale volume
        if notice.shares_to_be_sold > 100_000:
            correlation.signals.append(
                f'Large sale volume: {notice.shares_to_be_sold:,.0f} shares noticed'
            )

        # Signal: no 10b5-1 plan
        if not notice.has_10b5_1_plan:
            correlation.signals.append(
                'No 10b5-1 plan referenced — discretionary sale'
            )

        # Signal: aborted sale (noticed but not executed)
        if not correlation.was_executed:
            correlation.signals.append(
                'Form 144 notice filed but sale NOT executed within 90 days — '
                'aborted signal (52.4% opacity rate per Neupane 2026)'
            )

        # Signal: partial execution (significantly less than noticed)
        if correlation.was_executed and correlation.execution_share_ratio < 0.50:
            correlation.signals.append(
                f'Partial execution: only {correlation.execution_share_ratio:.1%} '
                f'of noticed shares actually sold'
            )

        # Signal: significant prior 3-month sales
        if notice.prior_3month_shares_sold > 50_000:
            correlation.signals.append(
                f'Significant prior sales: {notice.prior_3month_shares_sold:,.0f} shares '
                f'sold in preceding 3 months'
            )

    @staticmethod
    def _safe_avg(values: list) -> float:
        """Safely compute average, returning 0 for empty lists."""
        return round(sum(values) / len(values), 1) if values else 0
