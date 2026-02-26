"""
Tests for Forensic Sufficiency Layer (FSL)
==========================================

Covers:
- Code C price_required=False + conversion_terms_required logic
- Late filing calendar + business day detail
- Verbatim retained_control_snippets extraction from footnotes
- CrossFormReconciliationPanel construction and rendering
"""

import pytest
from src.detection.forensic_sufficiency import (
    PRICE_REQUIRED_BY_CODE,
    CONVERSION_TERMS_REQUIRED_BY_CODE,
    FSLDisposition,
    FSL_LABELS,
    FootnoteClassification,
    CrossFormReconciliationPanel,
    classify_footnotes,
    classify_fsl,
    determine_price_required,
    determine_conversion_terms_required,
    build_cross_form_reconciliation_panel,
    format_reconciliation_panels,
    format_top_signals_report,
    FSLAssessment,
)


# ──────────────────────────────────────────────────────────────────
# Code C: price_required vs conversion_terms_required
# ──────────────────────────────────────────────────────────────────

class TestCodeCPriceLogic:
    """Code C should NOT require a market price; it requires conversion terms."""

    def test_code_c_price_not_required(self):
        """PRICE_REQUIRED_BY_CODE['C'] must be False."""
        assert PRICE_REQUIRED_BY_CODE['C'] is False

    def test_code_c_conversion_terms_required(self):
        """CONVERSION_TERMS_REQUIRED_BY_CODE['C'] must be True."""
        assert CONVERSION_TERMS_REQUIRED_BY_CODE['C'] is True

    def test_determine_price_required_code_c(self):
        """determine_price_required() returns False for Code C."""
        assert determine_price_required('C', is_derivative=True) is False
        assert determine_price_required('C', is_derivative=False) is False

    def test_determine_conversion_terms_required_code_c(self):
        """determine_conversion_terms_required() returns True for Code C."""
        assert determine_conversion_terms_required('C') is True

    def test_determine_conversion_terms_required_other_codes(self):
        """Other codes do not require conversion terms."""
        for code in ('S', 'P', 'G', 'A', 'M', 'J'):
            assert determine_conversion_terms_required(code) is False

    def test_fsl_label_c_updated(self):
        """FSL label for C must reference 'conversion terms' not just 'price'."""
        label = FSL_LABELS[FSLDisposition.C_NEEDS_PRICE_RECON]
        assert 'conversion' in label.lower() or 'terms' in label.lower()
        assert 'price may be na' in label.lower() or 'price may be' in label.lower()

    def test_code_c_no_terms_triggers_disposition_c(self):
        """Code C with missing conversion terms → FSL disposition C."""
        txn = {
            'transaction_code': 'C',
            'is_derivative': True,
            'shares': 100000,
            'price_per_share': 0.0,
            'exercise_price': None,
            'transaction_date': '2020-07-17',
            'reporting_owner': 'Philip Knight',
            'security_title': 'Class B Common Stock',
            'is_late_filed': False,
            'days_late': 0,
        }
        fn_cls = FootnoteClassification()  # No conversion ratio
        assessment = classify_fsl(txn, fn_cls)
        assert assessment.disposition == FSLDisposition.C_NEEDS_PRICE_RECON.value
        assert assessment.conversion_terms_missing is True
        # The reason must mention conversion terms, not just "price"
        combined_reasons = ' '.join(assessment.disposition_reasons).lower()
        assert 'conversion' in combined_reasons

    def test_code_c_with_terms_in_footnote_no_disposition_c(self):
        """Code C with conversion ratio in footnotes should NOT trigger disposition C."""
        txn = {
            'transaction_code': 'C',
            'is_derivative': True,
            'shares': 100000,
            'price_per_share': 0.0,
            'exercise_price': None,
            'transaction_date': '2020-07-17',
            'reporting_owner': 'Philip Knight',
            'security_title': 'Class B Common Stock',
            'is_late_filed': False,
            'days_late': 0,
        }
        # Footnote contains conversion ratio
        fn_cls = classify_footnotes([
            "Converted at a ratio of 1:1 into Class A Common Stock."
        ])
        assert fn_cls.conversion_ratio_present is True
        assessment = classify_fsl(txn, fn_cls)
        # With conversion terms present, disposition should NOT be C
        assert assessment.disposition != FSLDisposition.C_NEEDS_PRICE_RECON.value
        assert assessment.conversion_terms_missing is False

    def test_code_c_with_exercise_price_no_disposition_c(self):
        """Code C with exercise_price present should NOT trigger disposition C."""
        txn = {
            'transaction_code': 'C',
            'is_derivative': True,
            'shares': 50000,
            'price_per_share': 0.0,
            'exercise_price': 10.50,  # Exercise/conversion price present
            'transaction_date': '2020-07-17',
            'reporting_owner': 'Philip Knight',
            'security_title': 'Class B Common Stock',
            'is_late_filed': False,
            'days_late': 0,
        }
        fn_cls = FootnoteClassification()
        assessment = classify_fsl(txn, fn_cls)
        assert assessment.disposition != FSLDisposition.C_NEEDS_PRICE_RECON.value
        assert assessment.conversion_terms_missing is False


# ──────────────────────────────────────────────────────────────────
# Late filing: calendar + business day detail
# ──────────────────────────────────────────────────────────────────

class TestLateFilingDetail:
    """Late filing output must show calendar days AND business days."""

    def _make_late_txn(self, calendar_days: int, days_late: int) -> dict:
        return {
            'transaction_code': 'J',
            'is_derivative': False,
            'shares': 1_500_000,
            'price_per_share': 0.0,
            'exercise_price': None,
            'transaction_date': '2020-07-17',
            'filing_date': '2020-12-05',
            'calendar_days_after_transaction': calendar_days,
            'reporting_owner': 'Travis Knight',
            'security_title': 'Common Stock',
            'is_late_filed': True,
            'days_late': days_late,
        }

    def test_assessment_stores_calendar_days(self):
        """FSLAssessment must store calendar_days_after_transaction."""
        txn = self._make_late_txn(calendar_days=141, days_late=139)
        fn_cls = FootnoteClassification()
        assessment = classify_fsl(txn, fn_cls)
        assert assessment.calendar_days_after_transaction == 141
        assert assessment.days_late == 139
        assert assessment.is_late is True

    def test_late_filing_reason_includes_calendar_days(self):
        """When calendar_days > 0 the reason string must mention them."""
        txn = self._make_late_txn(calendar_days=141, days_late=139)
        fn_cls = FootnoteClassification()
        assessment = classify_fsl(txn, fn_cls)
        combined = ' '.join(assessment.disposition_reasons).lower()
        assert '141 calendar days' in combined
        assert 'required within 2 business days' in combined

    def test_late_filing_report_includes_calendar_days(self):
        """format_top_signals_report must include calendar-day detail."""
        txn = self._make_late_txn(calendar_days=141, days_late=139)
        fn_cls = FootnoteClassification()
        assessment = classify_fsl(txn, fn_cls)
        report = format_top_signals_report([assessment])
        assert '141 calendar days' in report
        assert 'required within 2 business days' in report

    def test_late_filing_business_days_only_fallback(self):
        """When calendar_days=0 the reason still shows business day count."""
        txn = self._make_late_txn(calendar_days=0, days_late=139)
        fn_cls = FootnoteClassification()
        assessment = classify_fsl(txn, fn_cls)
        combined = ' '.join(assessment.disposition_reasons).lower()
        # days_late=139 means 139+2=141 total business days; check that appears
        assert '141 business days' in combined
        assert 'required within 2 business days' in combined

    def test_filing_date_stored_in_assessment(self):
        """filing_date must be stored in the assessment dict."""
        txn = self._make_late_txn(calendar_days=141, days_late=139)
        fn_cls = FootnoteClassification()
        assessment = classify_fsl(txn, fn_cls)
        assert assessment.filing_date == '2020-12-05'
        d = assessment.to_dict()
        assert d['filing_date'] == '2020-12-05'


# ──────────────────────────────────────────────────────────────────
# Footnote extraction: retained_control_snippets
# ──────────────────────────────────────────────────────────────────

class TestRetainedControlSnippets:
    """classify_footnotes() must extract verbatim sentences for beneficial control."""

    def test_no_snippets_when_no_beneficial_control(self):
        """Plain gift footnote should yield no retained_control_snippets."""
        fn_cls = classify_footnotes(["This transaction was a charitable gift."])
        assert fn_cls.beneficial_control_retained is False
        assert fn_cls.retained_control_snippets == []

    def test_snippets_extracted_for_indirect_ownership(self):
        """Sentence mentioning indirect ownership must appear as a snippet."""
        footnote = (
            "The shares were transferred to a family trust. "
            "The reporting person indirectly owns and controls the trust assets. "
            "No consideration was paid."
        )
        fn_cls = classify_footnotes([footnote])
        assert fn_cls.beneficial_control_retained is True
        assert len(fn_cls.retained_control_snippets) >= 1
        snippet = fn_cls.retained_control_snippets[0]
        assert 'indirectly owns' in snippet.lower() or 'controls' in snippet.lower()

    def test_snippets_deduped_across_footnotes(self):
        """Same sentence appearing in two footnotes should appear only once."""
        sentence = "The reporting person is deemed to be the beneficial owner."
        fn_cls = classify_footnotes([sentence, sentence])
        # Should appear only once in snippets
        assert fn_cls.retained_control_snippets.count(sentence) == 1

    def test_snippets_limited_to_two_per_footnote(self):
        """At most 2 matching sentences per footnote."""
        footnote = (
            "The reporting person indirectly owns the shares through a trust. "
            "The reporting person retains voting control over the trust. "
            "The reporting person is deemed to be the beneficial owner of all trust shares. "
            "This is a fourth sentence about beneficial ownership."
        )
        fn_cls = classify_footnotes([footnote])
        assert fn_cls.beneficial_control_retained is True
        # Should have no more than 2 snippets from this single footnote
        assert len(fn_cls.retained_control_snippets) <= 2

    def test_snippets_appear_in_fsl_reasons(self):
        """FSL disposition D reasons must include evidence snippets."""
        footnote = (
            "The reporting person transferred shares to Swoosh LLC. "
            "The reporting person retains beneficial control over Swoosh LLC."
        )
        fn_cls = classify_footnotes([footnote])
        assert fn_cls.beneficial_control_retained is True
        txn = {
            'transaction_code': 'J',
            'is_derivative': False,
            'shares': 2_000_000,
            'price_per_share': 0.0,
            'exercise_price': None,
            'transaction_date': '2020-07-17',
            'reporting_owner': 'Philip Knight',
            'security_title': 'Common Stock',
            'is_late_filed': False,
            'days_late': 0,
        }
        assessment = classify_fsl(txn, fn_cls)
        assert assessment.disposition == FSLDisposition.D_NEEDS_CROSS_FORM.value
        assert assessment.retained_control_snippets  # At least one snippet
        # Snippets must appear in reason list
        combined_reasons = ' '.join(assessment.disposition_reasons)
        assert 'Evidence snippet' in combined_reasons

    def test_snippets_in_report_output(self):
        """format_top_signals_report must include evidence snippets."""
        footnote = "The reporting person is deemed beneficial owner of the transferred shares."
        fn_cls = classify_footnotes([footnote])
        txn = {
            'transaction_code': 'D',
            'is_derivative': False,
            'shares': 1_000_000,
            'price_per_share': 0.0,
            'exercise_price': None,
            'transaction_date': '2020-07-17',
            'reporting_owner': 'Travis Knight',
            'security_title': 'Common Stock',
            'is_late_filed': False,
            'days_late': 0,
        }
        assessment = classify_fsl(txn, fn_cls)
        report = format_top_signals_report([assessment])
        assert 'Beneficial Control Evidence Snippets' in report


# ──────────────────────────────────────────────────────────────────
# CrossFormReconciliationPanel
# ──────────────────────────────────────────────────────────────────

class TestCrossFormReconciliationPanel:
    """CrossFormReconciliationPanel must produce correct checks for 3 fields."""

    def _make_d_assessment(
        self,
        shares: float = 2_000_000,
        entity_transfer: bool = True,
        beneficial_control: bool = True,
    ) -> FSLAssessment:
        assessment = FSLAssessment(
            insider_name="Philip Knight",
            transaction_date="2020-07-17",
            transaction_code="D",
            shares=shares,
            security_title="Class B Common Stock",
            entity_transfer_fn=entity_transfer,
            beneficial_control_retained_fn=beneficial_control,
            retained_control_snippets=["The reporting person retains beneficial control."],
            is_late=False,
            days_late=0,
            is_repeat_offender=False,
        )
        return assessment

    def test_13dg_expected_large_share_transfer(self):
        """13D/13G expected when shares exceed SCHEDULE_13DG_SHARE_THRESHOLD."""
        assessment = self._make_d_assessment(shares=2_000_000)
        panel = build_cross_form_reconciliation_panel(assessment)
        assert panel.schedule_13dg_expected is True
        assert '2,000,000' in panel.schedule_13dg_expected_reason or \
               'materiality threshold' in panel.schedule_13dg_expected_reason.lower()

    def test_13dg_not_expected_small_transfer(self):
        """13D/13G not expected for tiny share count with no control flags."""
        assessment = FSLAssessment(
            insider_name="Minor Holder",
            transaction_date="2020-07-17",
            transaction_code="J",
            shares=500,  # Below threshold
            security_title="Common Stock",
            entity_transfer_fn=False,
            beneficial_control_retained_fn=False,
        )
        panel = build_cross_form_reconciliation_panel(assessment)
        assert panel.schedule_13dg_expected is False

    def test_13dg_expected_due_to_beneficial_control(self):
        """13D/13G expected when beneficial_control_retained footnote present."""
        assessment = self._make_d_assessment(shares=100, beneficial_control=True)
        panel = build_cross_form_reconciliation_panel(assessment)
        assert panel.schedule_13dg_expected is True
        assert 'beneficial' in panel.schedule_13dg_expected_reason.lower()

    def test_13dg_observed_found(self):
        """When matching 13D/13G filing provided, observed=True."""
        assessment = self._make_d_assessment()
        filings = [
            {
                'accession_number': '0000000000-20-000001',
                'filing_date': '2020-07-22',
                'filer_name': 'Philip Knight',
                'shares_owned': 100_000_000,
                'percent_owned': 35.0,
            }
        ]
        panel = build_cross_form_reconciliation_panel(
            assessment, schedule_13dg_filings=filings
        )
        assert panel.schedule_13dg_observed is True
        assert panel.schedule_13dg_filing_id == '0000000000-20-000001'

    def test_13dg_observed_not_found(self):
        """When 13D/13G list provided but no matching filer, observed=False and flag raised."""
        assessment = self._make_d_assessment()
        filings = [
            {
                'accession_number': '0000000000-20-999999',
                'filing_date': '2020-07-22',
                'filer_name': 'Completely Different Person',
                'shares_owned': 5_000_000,
                'percent_owned': 2.0,
            }
        ]
        panel = build_cross_form_reconciliation_panel(
            assessment, schedule_13dg_filings=filings
        )
        assert panel.schedule_13dg_observed is False
        assert panel.reconciliation_flag is True
        assert any('disclosure gap' in n.lower() for n in panel.reconciliation_notes)

    def test_proxy_reconciled_within_tolerance(self):
        """When proxy pct and post-transfer pct are within 0.5%, reconciled=True."""
        assessment = self._make_d_assessment()
        panel = build_cross_form_reconciliation_panel(
            assessment,
            proxy_ownership_pct=35.10,
            post_transfer_ownership_pct=35.05,
        )
        assert panel.proxy_10k_reconciled is True
        assert panel.reconciliation_flag is False

    def test_proxy_not_reconciled_outside_tolerance(self):
        """When delta > 0.5%, reconciled=False and flag raised."""
        assessment = self._make_d_assessment()
        panel = build_cross_form_reconciliation_panel(
            assessment,
            proxy_ownership_pct=35.10,
            post_transfer_ownership_pct=32.00,  # 3.1% gap
        )
        assert panel.proxy_10k_reconciled is False
        assert panel.reconciliation_flag is True
        assert 'mismatch' in ' '.join(panel.reconciliation_notes).lower()
        assert '3.10%' in panel.proxy_discrepancy_detail

    def test_panel_text_contains_three_checks(self):
        """to_panel_text() must render all three check lines."""
        assessment = self._make_d_assessment()
        panel = build_cross_form_reconciliation_panel(
            assessment,
            schedule_13dg_filings=[],
            proxy_ownership_pct=35.0,
            post_transfer_ownership_pct=35.0,
        )
        text = panel.to_panel_text()
        assert '13D/13G Expected?' in text
        assert '13D/13G Observed?' in text
        assert 'Proxy/10-K Reconciled?' in text

    def test_format_reconciliation_panels_empty(self):
        """format_reconciliation_panels with no panels returns empty string."""
        assert format_reconciliation_panels([]) == ''

    def test_format_reconciliation_panels_nonempty(self):
        """format_reconciliation_panels with panels includes section header."""
        assessment = self._make_d_assessment()
        panel = build_cross_form_reconciliation_panel(assessment)
        result = format_reconciliation_panels([panel])
        assert 'CROSS-FORM RECONCILIATION PANELS' in result

    def test_panel_to_dict(self):
        """CrossFormReconciliationPanel.to_dict() includes all required keys."""
        assessment = self._make_d_assessment()
        panel = build_cross_form_reconciliation_panel(assessment)
        d = panel.to_dict()
        for key in (
            'schedule_13dg_expected', 'schedule_13dg_observed',
            'proxy_10k_reconciled', 'reconciliation_flag',
        ):
            assert key in d
