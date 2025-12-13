"""
Unit Tests for Node 9 v2.0 (8-K Material Event Correlator)
"""

import pytest
from datetime import date, datetime
from src.nodes.node9_8k_events.material_event_correlator_v2 import (
    MaterialEventCorrelatorV2,
    MaterialEvent8KV2,
    MarketImpactAnalysis,
    MarketHoursStatus,
    EventAlertType
)
from src.nodes.node9_8k_events.market_data_client import (
    MockMarketDataClient,
    Bar,
    Quote
)


class TestMarketDataClient:
    """Test market data client."""
    
    @pytest.mark.asyncio
    async def test_mock_client_daily_bars(self):
        """Test mock client daily bars generation."""
        client = MockMarketDataClient()
        
        start = date(2024, 1, 2)  # Tuesday
        end = date(2024, 1, 5)  # Friday
        
        bars = await client.get_daily_bars("TEST", start, end)
        
        # Should have 4 bars (Tue-Fri, no weekend)
        assert len(bars) == 4
        assert all(isinstance(b, Bar) for b in bars)
        assert all(b.volume > 0 for b in bars)
    
    @pytest.mark.asyncio
    async def test_mock_client_intraday_bars(self):
        """Test mock client intraday bars generation."""
        client = MockMarketDataClient()
        
        trade_date = date(2024, 1, 2)
        
        bars = await client.get_intraday_bars("TEST", trade_date)
        
        # Should have 390 1-minute bars (6.5 hours)
        assert len(bars) == 390
        assert all(isinstance(b, Bar) for b in bars)
    
    @pytest.mark.asyncio
    async def test_mock_client_quote(self):
        """Test mock client quote generation."""
        client = MockMarketDataClient()
        
        quote = await client.get_quote("TEST")
        
        assert quote is not None
        assert isinstance(quote, Quote)
        assert quote.ticker == "TEST"
        assert quote.bid > 0
        assert quote.ask > quote.bid


class TestMaterialEventCorrelatorV2:
    """Test material event correlator v2.0."""
    
    def test_timing_anomaly_friday_dump(self):
        """Test detection of Friday afternoon dump."""
        correlator = MaterialEventCorrelatorV2()
        
        events = [
            MaterialEvent8KV2(
                accession_number="0001234567-24-000123",
                cik="0000999999",
                company_name="Test Corp",
                ticker="TEST",
                filing_date=date(2024, 6, 14),  # Friday
                filing_time="16:30:00",
                items=["2.06"],  # Material impairment
                item_descriptions=["Material Impairments"],
                narrative="Material impairment charge",
                market_hours_status=MarketHoursStatus.AFTER_HOURS
            )
        ]
        
        alerts = correlator.detect_timing_anomalies(events)
        
        assert len(alerts) > 0
        alert = alerts[0]
        assert alert.alert_type == EventAlertType.TIMING_ANOMALY
        assert any("Friday" in flag for flag in alert.regulatory_flags)
    
    def test_sequential_adverse_events(self):
        """Test detection of sequential adverse events."""
        correlator = MaterialEventCorrelatorV2()
        
        # Create sequence of adverse events
        events = [
            MaterialEvent8KV2(
                accession_number="0001234567-24-000120",
                cik="0000999999",
                company_name="Test Corp",
                ticker="TEST",
                filing_date=date(2024, 1, 15),
                filing_time="14:00:00",
                items=["4.01"],  # Auditor change
                item_descriptions=["Changes in Certifying Accountant"],
                narrative="Change in auditor",
                market_hours_status=MarketHoursStatus.MARKET_HOURS
            ),
            MaterialEvent8KV2(
                accession_number="0001234567-24-000121",
                cik="0000999999",
                company_name="Test Corp",
                ticker="TEST",
                filing_date=date(2024, 2, 20),
                filing_time="15:00:00",
                items=["2.06"],  # Material impairment
                item_descriptions=["Material Impairments"],
                narrative="Impairment charge",
                market_hours_status=MarketHoursStatus.MARKET_HOURS
            ),
            MaterialEvent8KV2(
                accession_number="0001234567-24-000122",
                cik="0000999999",
                company_name="Test Corp",
                ticker="TEST",
                filing_date=date(2024, 3, 10),
                filing_time="16:00:00",
                items=["5.02"],  # Officer departure
                item_descriptions=["Departure of Directors or Officers"],
                narrative="CFO resignation",
                market_hours_status=MarketHoursStatus.MARKET_HOURS
            )
        ]
        
        alerts = correlator.detect_sequential_adverse_events(events)
        
        assert len(alerts) > 0
        alert = alerts[0]
        assert alert.alert_type == EventAlertType.SEQUENTIAL_EVENTS
        assert "3 adverse events" in " ".join(alert.regulatory_flags)
    
    def test_cybersecurity_event_classification(self):
        """Test Item 1.05 cybersecurity event classification."""
        correlator = MaterialEventCorrelatorV2()
        
        events = [
            MaterialEvent8KV2(
                accession_number="0001234567-24-000123",
                cik="0000999999",
                company_name="Test Corp",
                ticker="TEST",
                filing_date=date(2024, 6, 15),
                filing_time="14:00:00",
                items=["1.05"],  # Cybersecurity incident
                item_descriptions=["Material Cybersecurity Incidents"],
                narrative="Material cybersecurity incident",
                market_hours_status=MarketHoursStatus.MARKET_HOURS
            )
        ]
        
        alerts = correlator.detect_timing_anomalies(events)
        
        # Should flag cybersecurity incident
        assert len(alerts) > 0
        alert = alerts[0]
        assert any("Cybersecurity" in flag or "1.05" in flag for flag in alert.regulatory_flags)
    
    @pytest.mark.asyncio
    async def test_market_impact_calculation(self):
        """Test market impact calculation."""
        mock_client = MockMarketDataClient()
        correlator = MaterialEventCorrelatorV2(market_data_client=mock_client)
        
        event = MaterialEvent8KV2(
            accession_number="0001234567-24-000123",
            cik="0000999999",
            company_name="Test Corp",
            ticker="TEST",
            filing_date=date(2024, 6, 15),
            filing_time="14:00:00",
            items=["2.02"],
            item_descriptions=["Results of Operations"],
            narrative="Quarterly results",
            market_hours_status=MarketHoursStatus.MARKET_HOURS
        )
        
        impact = await correlator.calculate_market_impact(event)
        
        assert impact is not None
        assert isinstance(impact, MarketImpactAnalysis)
        assert impact.ticker == "TEST"
        # Mock data should generate some prices
        assert impact.price_t_0 is not None or impact.price_t_minus_1 is not None
    
    def test_risk_score_calculation(self):
        """Test risk score calculation."""
        correlator = MaterialEventCorrelatorV2()
        
        from src.nodes.node9_8k_events.material_event_correlator_v2 import CorrelatedTrade
        
        # High risk: many sales before negative event
        trades = [
            CorrelatedTrade(
                insider_name="CEO",
                transaction_date=date(2024, 6, 1),
                days_before_event=14,
                shares=10000,
                value=1000000,
                transaction_code="S"
            ),
            CorrelatedTrade(
                insider_name="CFO",
                transaction_date=date(2024, 6, 3),
                days_before_event=12,
                shares=5000,
                value=500000,
                transaction_code="S"
            ),
            CorrelatedTrade(
                insider_name="Director",
                transaction_date=date(2024, 6, 5),
                days_before_event=10,
                shares=3000,
                value=300000,
                transaction_code="S"
            )
        ]
        
        event = MaterialEvent8KV2(
            accession_number="0001234567-24-000123",
            cik="0000999999",
            company_name="Test Corp",
            ticker="TEST",
            filing_date=date(2024, 6, 15),
            filing_time="14:00:00",
            items=["2.06", "4.02"],  # Material impairment + restatement
            item_descriptions=["Material Impairments", "Non-Reliance"],
            narrative="Impairment and restatement",
            market_hours_status=MarketHoursStatus.MARKET_HOURS
        )
        
        risk_score = correlator._calculate_risk_score(trades, event, has_critical=True)
        
        assert 0.0 <= risk_score <= 1.0
        assert risk_score >= 0.5  # Should be high risk


class TestMarketImpactAnalysis:
    """Test market impact analysis data structure."""
    
    def test_market_impact_to_dict(self):
        """Test MarketImpactAnalysis serialization."""
        impact = MarketImpactAnalysis(
            event_date=date(2024, 6, 15),
            ticker="TEST",
            cusip="123456789",
            price_t_minus_5=100.0,
            price_t_minus_1=102.0,
            price_t_0=98.0,
            price_t_plus_1=97.0,
            price_t_plus_5=99.0,
            pre_event_drift=0.02,
            event_day_return=-0.039,
            post_event_drift=0.010,
            cumulative_abnormal_return=-0.009,
            avg_volume_20d=1000000,
            event_day_volume=3000000,
            volume_ratio=3.0,
            is_abnormal_volume=True,
            is_significant_price_move=False
        )
        
        data = impact.to_dict()
        assert data['ticker'] == "TEST"
        assert data['price_metrics']['T-5'] == 100.0
        assert data['impact_metrics']['event_day_return'] == -0.039
        assert data['volume_metrics']['volume_ratio'] == 3.0
        assert data['flags']['abnormal_volume'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
