"""
Tests for Polygon.io Market Data Client
"""

import pytest
from datetime import date, datetime
from src.integrations.market_data.polygon_client import (
    PolygonClient,
    Timespan,
    Aggregate,
    OptionContract
)


@pytest.mark.asyncio
async def test_polygon_client_initialization():
    """Test PolygonClient initialization."""
    client = PolygonClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert client.rate_limiter is not None


@pytest.mark.asyncio
async def test_aggregate_creation():
    """Test Aggregate dataclass."""
    agg = Aggregate(
        symbol="AAPL",
        timestamp=datetime(2023, 1, 1, 9, 30),
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=1000000
    )
    
    assert agg.symbol == "AAPL"
    assert agg.open == 150.0
    assert agg.volume == 1000000
    
    # Test to_dict
    agg_dict = agg.to_dict()
    assert agg_dict["symbol"] == "AAPL"
    assert agg_dict["open"] == 150.0


@pytest.mark.asyncio
async def test_option_contract_creation():
    """Test OptionContract dataclass."""
    contract = OptionContract(
        ticker="AAPL240119C00150000",
        underlying_ticker="AAPL",
        strike_price=150.0,
        expiration_date=date(2024, 1, 19),
        contract_type="call",
        bid=5.0,
        ask=5.5,
        last_price=5.25
    )
    
    assert contract.underlying_ticker == "AAPL"
    assert contract.strike_price == 150.0
    assert contract.contract_type == "call"
    
    # Test to_dict
    contract_dict = contract.to_dict()
    assert contract_dict["underlying_ticker"] == "AAPL"
    assert "greeks" in contract_dict


def test_timespan_enum():
    """Test Timespan enum."""
    assert Timespan.DAY.value == "day"
    assert Timespan.MINUTE.value == "minute"
    assert Timespan.WEEK.value == "week"
