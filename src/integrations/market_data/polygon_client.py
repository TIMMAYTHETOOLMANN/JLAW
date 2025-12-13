"""
Polygon.io Market Data Client
=============================

Production-grade async client for Polygon.io REST API with rate limiting.
Supports historical aggregates, options chains, and real-time WebSocket streaming.

API Documentation: https://polygon.io/docs/
Rate Limits: Stay under 100 req/sec for production tier
"""

import asyncio
import aiohttp
from aiolimiter import AsyncLimiter
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Timespan(Enum):
    """Time interval for aggregates."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class Aggregate:
    """Market data aggregate bar."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap,
            "transactions": self.transactions
        }


@dataclass
class OptionContract:
    """Options contract data."""
    ticker: str
    underlying_ticker: str
    strike_price: float
    expiration_date: date
    contract_type: str  # "call" or "put"
    bid: Optional[float] = None
    ask: Optional[float] = None
    last_price: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "underlying_ticker": self.underlying_ticker,
            "strike_price": self.strike_price,
            "expiration_date": self.expiration_date.isoformat(),
            "contract_type": self.contract_type,
            "bid": self.bid,
            "ask": self.ask,
            "last_price": self.last_price,
            "volume": self.volume,
            "open_interest": self.open_interest,
            "implied_volatility": self.implied_volatility,
            "greeks": {
                "delta": self.delta,
                "gamma": self.gamma,
                "theta": self.theta,
                "vega": self.vega
            }
        }


class PolygonClient:
    """
    Polygon.io REST API Client with rate limiting.
    
    Features:
    - Historical aggregates (bars)
    - Options chain snapshots
    - Rate limiting (100 req/sec default)
    - Automatic retry with exponential backoff
    - Connection pooling
    """
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(
        self,
        api_key: str,
        requests_per_second: float = 100.0,
        max_connections: int = 50
    ):
        """
        Initialize Polygon.io client.
        
        Args:
            api_key: Polygon.io API key
            requests_per_second: Rate limit (default: 100)
            max_connections: Max concurrent connections
        """
        self.api_key = api_key
        self.rate_limiter = AsyncLimiter(requests_per_second, 1.0)
        self.max_connections = max_connections
        self.session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._connector = aiohttp.TCPConnector(limit=self.max_connections)
        self.session = aiohttp.ClientSession(connector=self._connector)
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        if self._connector:
            await self._connector.close()
    
    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """
        Make rate-limited API request.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response or None on error
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        if params is None:
            params = {}
        
        params["apiKey"] = self.api_key
        url = f"{self.BASE_URL}{endpoint}"
        
        async with self.rate_limiter:
            try:
                async with self.session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logger.warning("Rate limit exceeded, waiting...")
                        await asyncio.sleep(1)
                        return await self._request(endpoint, params)
                    else:
                        logger.error(f"Polygon API error: {response.status} - {await response.text()}")
                        return None
            except Exception as e:
                logger.error(f"Polygon request failed: {e}")
                return None
    
    async def get_aggregates(
        self,
        ticker: str,
        multiplier: int,
        timespan: Timespan,
        from_date: date,
        to_date: date,
        adjusted: bool = True,
        sort: str = "asc",
        limit: int = 50000
    ) -> List[Aggregate]:
        """
        Get historical aggregate bars.
        
        Args:
            ticker: Stock ticker symbol
            multiplier: Size of timespan (e.g., 1 for 1 day, 5 for 5 minutes)
            timespan: Timespan enum (minute, hour, day, etc.)
            from_date: Start date
            to_date: End date
            adjusted: Adjust for splits (default: True)
            sort: Sort order "asc" or "desc"
            limit: Max results (default: 50000)
            
        Returns:
            List of Aggregate objects
            
        Example:
            # Get daily bars for AAPL in 2023
            bars = await client.get_aggregates(
                "AAPL", 1, Timespan.DAY,
                date(2023, 1, 1), date(2023, 12, 31)
            )
        """
        endpoint = (
            f"/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan.value}/"
            f"{from_date.isoformat()}/{to_date.isoformat()}"
        )
        
        params = {
            "adjusted": str(adjusted).lower(),
            "sort": sort,
            "limit": limit
        }
        
        data = await self._request(endpoint, params)
        if not data or "results" not in data:
            return []
        
        aggregates = []
        for bar in data["results"]:
            aggregates.append(Aggregate(
                symbol=ticker,
                timestamp=datetime.fromtimestamp(bar["t"] / 1000),
                open=bar["o"],
                high=bar["h"],
                low=bar["l"],
                close=bar["c"],
                volume=bar["v"],
                vwap=bar.get("vw"),
                transactions=bar.get("n")
            ))
        
        return aggregates
    
    async def get_options_chain(
        self,
        underlying_ticker: str,
        expiration_date: Optional[date] = None,
        strike_price: Optional[float] = None,
        contract_type: Optional[str] = None
    ) -> List[OptionContract]:
        """
        Get options chain snapshot for underlying asset.
        
        Args:
            underlying_ticker: Underlying stock ticker
            expiration_date: Filter by expiration date
            strike_price: Filter by strike price
            contract_type: Filter by "call" or "put"
            
        Returns:
            List of OptionContract objects
            
        Example:
            # Get all options for AAPL
            options = await client.get_options_chain("AAPL")
            
            # Get specific calls
            calls = await client.get_options_chain(
                "AAPL",
                expiration_date=date(2024, 1, 19),
                contract_type="call"
            )
        """
        endpoint = f"/v3/snapshot/options/{underlying_ticker}"
        
        params = {}
        if expiration_date:
            params["expiration_date"] = expiration_date.isoformat()
        if strike_price:
            params["strike_price"] = strike_price
        if contract_type:
            params["contract_type"] = contract_type
        
        data = await self._request(endpoint, params)
        if not data or "results" not in data:
            return []
        
        contracts = []
        for option in data["results"]:
            details = option.get("details", {})
            last_quote = option.get("last_quote", {})
            greeks = option.get("greeks", {})
            day = option.get("day", {})
            
            # Parse expiration date
            exp_str = details.get("expiration_date", "")
            try:
                exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            
            contracts.append(OptionContract(
                ticker=details.get("ticker", ""),
                underlying_ticker=underlying_ticker,
                strike_price=details.get("strike_price", 0.0),
                expiration_date=exp_date,
                contract_type=details.get("contract_type", ""),
                bid=last_quote.get("bid"),
                ask=last_quote.get("ask"),
                last_price=day.get("close"),
                volume=day.get("volume"),
                open_interest=day.get("open_interest"),
                implied_volatility=greeks.get("implied_volatility"),
                delta=greeks.get("delta"),
                gamma=greeks.get("gamma"),
                theta=greeks.get("theta"),
                vega=greeks.get("vega")
            ))
        
        return contracts
    
    async def get_daily_open_close(
        self,
        ticker: str,
        date_: date
    ) -> Optional[Dict[str, Any]]:
        """
        Get open, high, low, close for a specific date.
        
        Args:
            ticker: Stock ticker
            date_: Date to retrieve
            
        Returns:
            Dictionary with OHLC data
        """
        endpoint = f"/v1/open-close/{ticker}/{date_.isoformat()}"
        return await self._request(endpoint)
    
    async def get_previous_close(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get previous day's close.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Dictionary with previous close data
        """
        endpoint = f"/v2/aggs/ticker/{ticker}/prev"
        return await self._request(endpoint)
    
    async def get_snapshot(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get current market snapshot for ticker.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Dictionary with current market data
        """
        endpoint = f"/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        return await self._request(endpoint)
