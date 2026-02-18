"""
Unit Tests for Zero Value Transaction Analyzer and Gift Pattern Detector enhancements.

Tests beneficial ownership detection infrastructure:
- $0 transaction classification and detection
- Gift pattern suspicious timing detection
- Gift-material event correlation
- Beneficial ownership chain mapping
"""

import pytest
from datetime import date
from src.nodes.node1_form4.zero_value_detector import (
    ZeroValueTransactionAnalyzer,
    ZeroValueAnalysis,
    ZeroValueAlert,
    ZeroValuePattern,
    ZeroValueSeverity,
)
from src.nodes.node1_form4.gift_pattern_detector import (
    GiftPatternDetector,
    GiftPatternAlert,
)


class TestZeroValueTransactionAnalyzer:
    """Test $0 transaction detection and classification."""

    def setup_method(self):
        self.analyzer = ZeroValueTransactionAnalyzer()

    def test_empty_transactions(self):
        """No transactions should produce empty analysis."""
        result = self.analyzer.analyze([])
        assert result.total_zero_value == 0
        assert result.suspicious_count == 0
        assert result.aggregate_risk_score == 0.0

    def test_legitimate_gift_classified(self):
        """Gift code G with $0 price is legitimate."""
        txns = [
            {
                "transaction_code": "G",
                "price_per_share": 0.0,
                "shares": 10000,
                "transaction_date": "2019-06-15",
                "security_title": "Common Stock",
                "owner_name": "Test Insider",
                "is_derivative": False,
            }
        ]
        result = self.analyzer.analyze(txns)
        assert result.total_zero_value == 1
        assert result.legitimate_count == 1
        assert result.suspicious_count == 0
        assert "legitimate_gift" in result.patterns_detected

    def test_stock_award_classified(self):
        """Award code A with $0 price is legitimate."""
        txns = [
            {
                "transaction_code": "A",
                "price_per_share": 0.0,
                "shares": 5000,
                "transaction_date": "2019-03-01",
                "security_title": "Common Stock",
                "owner_name": "Executive",
                "is_derivative": False,
            }
        ]
        result = self.analyzer.analyze(txns)
        assert result.legitimate_count == 1
        assert "stock_award_grant" in result.patterns_detected

    def test_zero_price_non_gift_suspicious(self):
        """$0 sale (code S) without gift code is suspicious."""
        txns = [
            {
                "transaction_code": "S",
                "price_per_share": 0.0,
                "shares": 50000,
                "transaction_date": "2019-07-10",
                "security_title": "Common Stock",
                "owner_name": "Suspicious Insider",
                "is_derivative": False,
            }
        ]
        result = self.analyzer.analyze(txns)
        assert result.suspicious_count == 1
        assert len(result.alerts) >= 1
        alert = result.alerts[0]
        assert alert.pattern == ZeroValuePattern.ZERO_PRICE_NON_GIFT
        assert alert.severity == ZeroValueSeverity.HIGH
        assert len(alert.statutory_references) > 0

    def test_derivative_exercise_at_zero(self):
        """Derivative exercise at $0 should flag as suspicious."""
        txns = [
            {
                "transaction_code": "M",
                "price_per_share": 0.0,
                "shares": 20000,
                "transaction_date": "2019-05-20",
                "security_title": "Stock Option",
                "owner_name": "Option Holder",
                "is_derivative": True,
                "exercise_price": 0.0,
            }
        ]
        result = self.analyzer.analyze(txns)
        assert result.suspicious_count >= 1
        has_derivative_alert = any(
            a.pattern == ZeroValuePattern.DERIVATIVE_EXERCISE_ADVANTAGE
            for a in result.alerts
        )
        assert has_derivative_alert

    def test_timing_anomaly_near_material_event(self):
        """$0 transaction near 8-K filing should flag timing anomaly."""
        txns = [
            {
                "transaction_code": "S",
                "price_per_share": 0.0,
                "shares": 10000,
                "transaction_date": "2019-08-01",
                "security_title": "Common Stock",
                "owner_name": "Timed Insider",
                "is_derivative": False,
            }
        ]
        events = [
            {"event_date": "2019-08-05", "event_type": "earnings announcement"}
        ]
        result = self.analyzer.analyze(txns, material_events=events)
        timing_alerts = [
            a for a in result.alerts
            if a.pattern == ZeroValuePattern.TIMING_ANOMALY
        ]
        assert len(timing_alerts) >= 1
        assert timing_alerts[0].severity in (ZeroValueSeverity.CRITICAL, ZeroValueSeverity.HIGH)

    def test_non_zero_price_excluded(self):
        """Transactions with nonzero prices should not be analyzed."""
        txns = [
            {
                "transaction_code": "S",
                "price_per_share": 85.50,
                "shares": 10000,
                "transaction_date": "2019-06-15",
                "security_title": "Common Stock",
                "owner_name": "Normal Seller",
                "is_derivative": False,
            }
        ]
        result = self.analyzer.analyze(txns)
        assert result.total_zero_value == 0

    def test_mixed_transactions(self):
        """Mix of legitimate and suspicious $0 transactions."""
        txns = [
            {
                "transaction_code": "G",
                "price_per_share": 0.0,
                "shares": 5000,
                "transaction_date": "2019-03-01",
                "security_title": "Common Stock",
                "owner_name": "Donor",
                "is_derivative": False,
            },
            {
                "transaction_code": "P",
                "price_per_share": 0.0,
                "shares": 30000,
                "transaction_date": "2019-03-15",
                "security_title": "Common Stock",
                "owner_name": "Suspicious Buyer",
                "is_derivative": False,
            },
        ]
        result = self.analyzer.analyze(txns)
        assert result.total_zero_value == 2
        assert result.legitimate_count == 1
        assert result.suspicious_count >= 1

    def test_analysis_serialization(self):
        """Verify to_dict works on ZeroValueAnalysis."""
        txns = [
            {
                "transaction_code": "S",
                "price_per_share": 0.0,
                "shares": 10000,
                "transaction_date": "2019-06-15",
                "security_title": "Common Stock",
                "owner_name": "Test",
                "is_derivative": False,
            }
        ]
        result = self.analyzer.analyze(txns)
        d = result.to_dict()
        assert "summary" in d
        assert "alerts" in d
        assert d["summary"]["total_zero_value"] == 1


class TestGiftPatternDetectorEnhancements:
    """Test enhanced gift pattern detection methods."""

    def setup_method(self):
        self.detector = GiftPatternDetector()

    def test_detect_suspicious_gifts_serial_pattern(self):
        """Serial gifting by same donor should flag."""
        txns = [
            {
                "transaction_code": "G",
                "transaction_date": "2019-01-15",
                "filing_date": "2019-01-17",
                "shares": 5000,
                "price_per_share": 0.0,
                "owner_name": "Serial Donor",
                "value": 0,
            },
            {
                "transaction_code": "G",
                "transaction_date": "2019-03-10",
                "filing_date": "2019-03-12",
                "shares": 3000,
                "price_per_share": 0.0,
                "owner_name": "Serial Donor",
                "value": 0,
            },
            {
                "transaction_code": "G",
                "transaction_date": "2019-06-20",
                "filing_date": "2019-06-22",
                "shares": 7000,
                "price_per_share": 0.0,
                "owner_name": "Serial Donor",
                "value": 0,
            },
        ]
        alerts = self.detector.detect_suspicious_gifts(txns)
        serial_alerts = [a for a in alerts if a.alert_type == "SERIAL_GIFT_PATTERN"]
        assert len(serial_alerts) >= 1

    def test_detect_suspicious_gifts_large(self):
        """Large single gift should flag."""
        txns = [
            {
                "transaction_code": "G",
                "transaction_date": "2019-06-15",
                "filing_date": "2019-06-17",
                "shares": 500000,
                "price_per_share": 0.0,
                "owner_name": "Big Donor",
                "value": 0,
            }
        ]
        alerts = self.detector.detect_suspicious_gifts(txns)
        large_alerts = [a for a in alerts if a.alert_type == "LARGE_GIFT"]
        assert len(large_alerts) >= 1

    def test_detect_suspicious_gifts_non_gift_ignored(self):
        """Non-gift transactions are filtered out."""
        txns = [
            {
                "transaction_code": "S",
                "transaction_date": "2019-06-15",
                "filing_date": "2019-06-17",
                "shares": 10000,
                "price_per_share": 85.0,
                "owner_name": "Seller",
                "value": 850000,
            }
        ]
        alerts = self.detector.detect_suspicious_gifts(txns)
        assert len(alerts) == 0

    def test_correlate_with_material_events(self):
        """Gift before material event should flag."""
        gifts = [
            {
                "transaction_code": "G",
                "transaction_date": "2019-07-01",
                "filing_date": "2019-07-03",
                "shares": 10000,
                "owner_name": "Pre-Event Donor",
                "value": 0,
            }
        ]
        events = [
            {"event_date": "2019-07-10", "event_type": "negative earnings"}
        ]
        alerts = self.detector.correlate_with_material_events(gifts, events)
        assert len(alerts) >= 1
        assert alerts[0].alert_type == "PRE_EVENT_GIFT"
        assert "MNPI" in alerts[0].evidence_summary

    def test_correlate_with_no_events(self):
        """No events should return no alerts."""
        gifts = [
            {
                "transaction_code": "G",
                "transaction_date": "2019-07-01",
                "filing_date": "2019-07-03",
                "shares": 10000,
                "owner_name": "Donor",
                "value": 0,
            }
        ]
        alerts = self.detector.correlate_with_material_events(gifts, [])
        assert len(alerts) == 0

    def test_map_beneficial_ownership_chain_simple(self):
        """Simple direct gift maps correctly."""
        gift = {
            "owner_name": "CEO Smith",
            "shares": 10000,
            "transaction_date": "2019-06-15",
            "ownership_nature": "direct",
        }
        chain = self.detector.map_beneficial_ownership_chain(gift)
        assert chain["donor"] == "CEO Smith"
        assert chain["obfuscation_risk"] == "LOW"

    def test_map_beneficial_ownership_chain_trust(self):
        """Gift through trust entity flags higher risk."""
        gift = {
            "owner_name": "CEO Smith",
            "shares": 10000,
            "transaction_date": "2019-06-15",
            "ownership_nature": "indirect",
            "indirect_entity": "Smith Family Trust",
        }
        chain = self.detector.map_beneficial_ownership_chain(gift)
        assert chain["obfuscation_risk"] == "HIGH"
        assert len(chain["chain_links"]) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
