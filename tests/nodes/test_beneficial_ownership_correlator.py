"""
Unit Tests for Beneficial Ownership Correlator.

Tests cross-node correlation for beneficial ownership changes:
- Threshold breach detection (Node 1 + Node 8)
- Information asymmetry detection (Node 1 + Node 7)
- Material event correlation (Node 1 + Node 9)
- Restricted sale intent (Node 1 + Node 10)
- Compensation verification (Node 1 + Node 2)
"""

import pytest
from datetime import date
from src.nodes.cross_node.beneficial_ownership_correlator import (
    BeneficialOwnershipCorrelator,
    OwnershipCorrelationReport,
    OwnershipCorrelationAlert,
    AsymmetryAlert,
    OwnershipAlertType,
    OwnershipSeverity,
)


class TestBeneficialOwnershipCorrelator:
    """Test cross-node beneficial ownership correlation."""

    def setup_method(self):
        self.correlator = BeneficialOwnershipCorrelator()

    def test_empty_inputs(self):
        """No data should produce empty report."""
        report = self.correlator.correlate_ownership_changes(
            cik="320187",
            company_name="NIKE, Inc.",
            date_range=(date(2019, 1, 1), date(2019, 12, 31)),
        )
        assert isinstance(report, OwnershipCorrelationReport)
        assert report.total_correlations == 0
        assert report.aggregate_risk_score == 0.0

    def test_threshold_breach_detection(self):
        """Detect 5% threshold crossing with correlated insider trades."""
        insider_trades = [
            {
                "transaction_code": "S",
                "transaction_date": "2019-06-10",
                "shares": 50000,
                "price_per_share": 85.0,
                "owner_name": "Insider A",
                "acquired_disposed": "D",
            }
        ]
        ownership_filings = [
            {
                "filing_date": "2019-06-15",
                "filer_name": "Activist Fund",
                "percent_owned": 5.5,
                "previous_ownership": 4.8,
            }
        ]
        report = self.correlator.correlate_ownership_changes(
            cik="320187",
            company_name="NIKE, Inc.",
            date_range=(date(2019, 1, 1), date(2019, 12, 31)),
            insider_trades=insider_trades,
            ownership_filings=ownership_filings,
        )
        threshold_alerts = [
            a for a in report.alerts
            if a.alert_type == OwnershipAlertType.THRESHOLD_BREACH
        ]
        assert len(threshold_alerts) >= 1
        assert threshold_alerts[0].source_nodes == [1, 8]

    def test_information_asymmetry_detection(self):
        """Detect insider selling before institutional exit."""
        insider_trades = [
            {
                "transaction_code": "S",
                "transaction_date": "2019-06-01",
                "shares": 100000,
                "price_per_share": 85.0,
                "owner_name": "CEO",
                "acquired_disposed": "D",
            }
        ]
        institutional_holdings = [
            {
                "institution_name": "Vanguard Group",
                "reporting_period": "2019-06-30",
                "percent_change": -25.0,
            }
        ]
        alerts = self.correlator.detect_information_asymmetry(
            insider_trades, institutional_holdings
        )
        assert len(alerts) >= 1
        assert alerts[0].alert_type == OwnershipAlertType.INFORMATION_ASYMMETRY

    def test_no_asymmetry_when_institutional_increase(self):
        """No alert when institution is increasing, not decreasing."""
        insider_trades = [
            {
                "transaction_code": "S",
                "transaction_date": "2019-06-01",
                "shares": 10000,
                "owner_name": "Insider",
                "acquired_disposed": "D",
            }
        ]
        institutional_holdings = [
            {
                "institution_name": "Fidelity",
                "reporting_period": "2019-09-30",
                "percent_change": 15.0,
            }
        ]
        alerts = self.correlator.detect_information_asymmetry(
            insider_trades, institutional_holdings
        )
        assert len(alerts) == 0

    def test_material_event_correlation(self):
        """Detect insider trades before material events."""
        insider_trades = [
            {
                "transaction_code": "S",
                "transaction_date": "2019-07-01",
                "shares": 50000,
                "owner_name": "CFO",
                "acquired_disposed": "D",
            }
        ]
        material_events = [
            {"event_date": "2019-07-20", "event_type": "earnings warning"}
        ]
        report = self.correlator.correlate_ownership_changes(
            cik="320187",
            company_name="NIKE, Inc.",
            date_range=(date(2019, 1, 1), date(2019, 12, 31)),
            insider_trades=insider_trades,
            material_events=material_events,
        )
        event_alerts = [
            a for a in report.alerts
            if a.alert_type == OwnershipAlertType.MATERIAL_EVENT_CORRELATION
        ]
        assert len(event_alerts) >= 1
        assert event_alerts[0].severity == OwnershipSeverity.CRITICAL

    def test_restricted_sale_correlation(self):
        """Detect Form 144 intent followed by Form 4 trades."""
        insider_trades = [
            {
                "transaction_code": "S",
                "transaction_date": "2019-08-10",
                "shares": 20000,
                "owner_name": "VP Sales",
            }
        ]
        restricted_sales = [
            {
                "filing_date": "2019-08-01",
                "filer_name": "VP Sales",
            }
        ]
        report = self.correlator.correlate_ownership_changes(
            cik="320187",
            company_name="NIKE, Inc.",
            date_range=(date(2019, 1, 1), date(2019, 12, 31)),
            insider_trades=insider_trades,
            restricted_sales=restricted_sales,
        )
        intent_alerts = [
            a for a in report.alerts
            if a.alert_type == OwnershipAlertType.RESTRICTED_SALE_INTENT
        ]
        assert len(intent_alerts) >= 1

    def test_compensation_mismatch(self):
        """Detect $0 awards not disclosed in proxy."""
        insider_trades = [
            {
                "transaction_code": "A",
                "price_per_share": 0.0,
                "transaction_date": "2019-04-01",
                "shares": 10000,
                "owner_name": "Undisclosed Executive",
            }
        ]
        compensation_data = {
            "stock_awards": [
                {"executive_name": "Known Executive"}
            ]
        }
        report = self.correlator.correlate_ownership_changes(
            cik="320187",
            company_name="NIKE, Inc.",
            date_range=(date(2019, 1, 1), date(2019, 12, 31)),
            insider_trades=insider_trades,
            compensation_data=compensation_data,
        )
        comp_alerts = [
            a for a in report.alerts
            if a.alert_type == OwnershipAlertType.COMPENSATION_MISMATCH
        ]
        assert len(comp_alerts) >= 1

    def test_report_serialization(self):
        """Verify to_dict works on OwnershipCorrelationReport."""
        report = self.correlator.correlate_ownership_changes(
            cik="320187",
            company_name="NIKE, Inc.",
            date_range=(date(2019, 1, 1), date(2019, 12, 31)),
        )
        d = report.to_dict()
        assert "company" in d
        assert d["company"]["cik"] == "320187"
        assert "total_correlations" in d
        assert "alerts" in d

    def test_multi_source_report(self):
        """Full multi-source correlation produces comprehensive report."""
        insider_trades = [
            {
                "transaction_code": "S",
                "transaction_date": "2019-06-01",
                "shares": 100000,
                "price_per_share": 85.0,
                "owner_name": "CEO",
                "acquired_disposed": "D",
            }
        ]
        ownership_filings = [
            {
                "filing_date": "2019-06-10",
                "filer_name": "Activist Fund",
                "percent_owned": 6.0,
                "previous_ownership": 4.5,
            }
        ]
        institutional_holdings = [
            {
                "institution_name": "Large Fund",
                "reporting_period": "2019-06-30",
                "percent_change": -20.0,
            }
        ]
        material_events = [
            {"event_date": "2019-06-20", "event_type": "SEC investigation"}
        ]
        report = self.correlator.correlate_ownership_changes(
            cik="320187",
            company_name="NIKE, Inc.",
            date_range=(date(2019, 1, 1), date(2019, 12, 31)),
            insider_trades=insider_trades,
            ownership_filings=ownership_filings,
            institutional_holdings=institutional_holdings,
            material_events=material_events,
        )
        assert report.total_correlations > 0
        assert report.aggregate_risk_score > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
