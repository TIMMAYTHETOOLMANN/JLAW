"""
Unit Tests for Cross-Node Correlator
"""

import pytest
from datetime import date, datetime
from src.nodes.cross_node.node_correlator import (
    NodeCorrelator,
    CrossNodeAlert,
    CrossNodeAlertType,
    Severity
)


class MockWolfPackAlert:
    """Mock wolf pack alert for testing."""
    def __init__(self, pack_id, cusip, issuer_name, institutions, coordination_score):
        self.pack_id = pack_id
        self.cusip = cusip
        self.issuer_name = issuer_name
        self.institutions = institutions
        self.coordination_score = coordination_score
        self.aggregate_ownership_percent = 15.0
        self.filing_window_start = date(2024, 6, 1)
        self.filing_window_end = date(2024, 6, 30)
    
    def to_dict(self):
        return {
            'pack_id': self.pack_id,
            'cusip': self.cusip,
            'issuer_name': self.issuer_name
        }


class MockOwnershipAlert:
    """Mock ownership alert for testing."""
    def __init__(self, alert_type_value, subject_cik, subject_name, parties, ownership):
        class AlertType:
            def __init__(self, value):
                self.value = value
        
        class IntentAnalysis:
            def __init__(self):
                self.intent_score = 0.7
        
        self.alert_type = AlertType(alert_type_value)
        self.subject_company_cik = subject_cik
        self.subject_company_name = subject_name
        self.involved_parties = [{'name': p} for p in parties]
        self.aggregate_ownership = ownership
        self.intent_analysis = IntentAnalysis()
        self.timestamp = datetime(2024, 6, 15)
    
    def to_dict(self):
        return {
            'alert_type': self.alert_type.value,
            'subject_company': self.subject_company_name
        }


class MockNode7Output:
    """Mock Node 7 output."""
    def __init__(self, wolf_packs):
        self.wolf_pack_alerts = wolf_packs
        self.alerts = []
        self.high_severity_count = len(wolf_packs)


class MockNode8Output:
    """Mock Node 8 output."""
    def __init__(self, alerts):
        self.alerts = alerts
        self.conversions_detected = 0
        self.high_severity_count = len(alerts)


class MockNode9Output:
    """Mock Node 9 output."""
    def __init__(self, alerts):
        self.alerts = alerts
        self.critical_events = 2
        self.events_analyzed = 10


class TestNodeCorrelator:
    """Test cross-node correlator."""
    
    def test_node7_node8_correlation(self):
        """Test Node 7 ↔ Node 8 correlation."""
        correlator = NodeCorrelator()
        
        # Create mock wolf pack
        wolf_pack = MockWolfPackAlert(
            pack_id="wp123",
            cusip="123456789",
            issuer_name="Target Corp",
            institutions=["Fund A", "Fund B", "Fund C"],
            coordination_score=0.85
        )
        
        # Create mock ownership alert with overlapping parties
        ownership_alert = MockOwnershipAlert(
            alert_type_value="Wolf Pack Formation",
            subject_cik="0000999999",
            subject_name="Target Corp",
            parties=["Fund A", "Fund B"],  # Overlap with wolf pack
            ownership=10.0
        )
        
        node7_output = MockNode7Output([wolf_pack])
        node8_output = MockNode8Output([ownership_alert])
        
        alerts = correlator.correlate_node7_node8(node7_output, node8_output)
        
        assert len(alerts) > 0
        alert = alerts[0]
        assert alert.alert_type == CrossNodeAlertType.WOLF_PACK_13F_13D_CORRELATION
        assert alert.severity == Severity.CRITICAL
        assert alert.node7_data is not None
        assert alert.node8_data is not None
        assert alert.correlation_score >= correlator.MIN_CORRELATION_SCORE
    
    def test_node7_node8_no_overlap(self):
        """Test Node 7 ↔ Node 8 with no overlap."""
        correlator = NodeCorrelator()
        
        wolf_pack = MockWolfPackAlert(
            pack_id="wp123",
            cusip="123456789",
            issuer_name="Target Corp",
            institutions=["Fund X", "Fund Y", "Fund Z"],
            coordination_score=0.85
        )
        
        ownership_alert = MockOwnershipAlert(
            alert_type_value="Wolf Pack Formation",
            subject_cik="0000888888",  # Different company
            subject_name="Other Corp",
            parties=["Fund A", "Fund B"],
            ownership=10.0
        )
        
        node7_output = MockNode7Output([wolf_pack])
        node8_output = MockNode8Output([ownership_alert])
        
        alerts = correlator.correlate_node7_node8(node7_output, node8_output)
        
        # Should have no alerts due to no overlap
        assert len(alerts) == 0
    
    def test_correlation_score_calculation(self):
        """Test correlation score calculation."""
        correlator = NodeCorrelator()
        
        wolf_pack = MockWolfPackAlert(
            pack_id="wp123",
            cusip="123456789",
            issuer_name="Target Corp",
            institutions=["Fund A", "Fund B", "Fund C"],
            coordination_score=0.85
        )
        
        ownership_alert = MockOwnershipAlert(
            alert_type_value="Wolf Pack Formation",
            subject_cik="0000999999",
            subject_name="Target Corp",
            parties=["Fund A", "Fund B"],
            ownership=10.0
        )
        
        overlap = {"Fund A", "Fund B"}
        
        score = correlator._calculate_node7_node8_correlation(
            wolf_pack, ownership_alert, overlap
        )
        
        assert 0.0 <= score <= 1.0
        assert score >= 0.6  # Should be high due to overlap and coordination
    
    def test_unified_analysis_generation(self):
        """Test unified analysis generation."""
        correlator = NodeCorrelator()
        
        wolf_pack = MockWolfPackAlert(
            pack_id="wp123",
            cusip="123456789",
            issuer_name="Target Corp",
            institutions=["Fund A", "Fund B"],
            coordination_score=0.85
        )
        
        ownership_alert = MockOwnershipAlert(
            alert_type_value="13G to 13D Conversion",
            subject_cik="0000999999",
            subject_name="Target Corp",
            parties=["Fund A"],
            ownership=8.0
        )
        
        node7_output = MockNode7Output([wolf_pack])
        node8_output = MockNode8Output([ownership_alert])
        
        analysis = correlator.generate_unified_analysis(
            company_cik="0000999999",
            company_name="Target Corp",
            node7_output=node7_output,
            node8_output=node8_output,
            analysis_start=date(2024, 1, 1),
            analysis_end=date(2024, 12, 31)
        )
        
        assert analysis.company_cik == "0000999999"
        assert analysis.company_name == "Target Corp"
        assert len(analysis.cross_node_alerts) > 0
        assert 0.0 <= analysis.overall_risk_score <= 1.0
        assert len(analysis.risk_factors) > 0
    
    def test_overall_risk_score_calculation(self):
        """Test overall risk score calculation."""
        correlator = NodeCorrelator()
        
        # Create multiple CRITICAL cross-alerts
        cross_alerts = [
            CrossNodeAlert(
                alert_type=CrossNodeAlertType.WOLF_PACK_13F_13D_CORRELATION,
                cusip="123456789",
                company_name="Target Corp",
                company_cik="0000999999",
                correlation_score=0.9,
                severity=Severity.CRITICAL
            ),
            CrossNodeAlert(
                alert_type=CrossNodeAlertType.COORDINATED_CAMPAIGN,
                cusip="123456789",
                company_name="Target Corp",
                company_cik="0000999999",
                correlation_score=0.85,
                severity=Severity.CRITICAL
            )
        ]
        
        wolf_pack = MockWolfPackAlert("wp1", "123456789", "Target", ["A", "B"], 0.9)
        node7_output = MockNode7Output([wolf_pack])
        
        ownership_alert = MockOwnershipAlert("Conversion", "999", "Target", ["A"], 10)
        node8_output = MockNode8Output([ownership_alert])
        
        node9_output = MockNode9Output([])
        
        score = correlator._calculate_overall_risk_score(
            None, node7_output, node8_output, node9_output, cross_alerts
        )
        
        assert 0.0 <= score <= 1.0
        # Should be very high with multiple CRITICAL alerts
        assert score >= 0.8


class TestCrossNodeAlert:
    """Test CrossNodeAlert data structure."""
    
    def test_cross_node_alert_to_dict(self):
        """Test CrossNodeAlert serialization."""
        alert = CrossNodeAlert(
            alert_type=CrossNodeAlertType.WOLF_PACK_13F_13D_CORRELATION,
            cusip="123456789",
            company_name="Target Corp",
            company_cik="0000999999",
            node7_data={'institutions': ['Fund A', 'Fund B']},
            node8_data={'parties': ['Fund A']},
            correlation_score=0.85,
            risk_indicators=['High coordination', 'Overlapping parties'],
            regulatory_implications=['SEC investigation recommended'],
            temporal_window_days=30,
            earliest_signal_date=date(2024, 6, 1),
            latest_signal_date=date(2024, 6, 30),
            severity=Severity.CRITICAL
        )
        
        data = alert.to_dict()
        assert data['alert_type'] == CrossNodeAlertType.WOLF_PACK_13F_13D_CORRELATION.value
        assert data['company']['cik'] == "0000999999"
        assert data['correlation_score'] == 0.85
        assert data['severity'] == "CRITICAL"
        assert data['sources']['node7_institutional_holdings'] is True
        assert data['sources']['node8_beneficial_ownership'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
