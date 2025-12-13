"""
Market Data Client for Node 9 v2.0
==================================

Provides interface for fetching real-time and historical market data
for 8-K material event correlation.

Supports Polygon.io API (primary) with Protocol interface for extensibility.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Protocol, Any
from dataclasses import dataclass
import aiohttp
from aiolimiter import AsyncLimiter

logger = logging.getLogger(__name__)


@dataclass
class Bar:
    """Price/volume bar data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None  # Volume-weighted average price
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap
        }


@dataclass
class Quote:
    """Real-time quote data."""
    ticker: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    last_price: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "timestamp": self.timestamp.isoformat(),
            "bid": self.bid,
            "ask": self.ask,
            "bid_size": self.bid_size,
            "ask_size": self.ask_size,
            "last_price": self.last_price
        }


class MarketDataClient(Protocol):
    """
    Protocol for market data clients.
    
    Allows for multiple implementations (Polygon.io, Alpha Vantage, etc.)
    """
    
    async def get_daily_bars(
        self,
        ticker: str,
        start: date,
        end: date
    ) -> List[Bar]:
        """
        Fetch daily bars for ticker.
        
        Args:
            ticker: Stock ticker symbol
            start: Start date
            end: End date
            
        Returns:
            List of daily bars
        """
        ...
    
    async def get_intraday_bars(
        self,
        ticker: str,
        date: date,
        timespan: str = "minute"
    ) -> List[Bar]:
        """
        Fetch intraday bars for ticker.
        
        Args:
            ticker: Stock ticker symbol
            date: Trading date
            timespan: Bar timespan (minute, hour)
            
        Returns:
            List of intraday bars
        """
        ...
    
    async def get_quote(self, ticker: str) -> Optional[Quote]:
        """
        Get real-time quote for ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current quote or None
        """
        ...


class PolygonMarketDataClient:
    """
    Polygon.io market data client implementation.
    
    API Documentation: https://polygon.io/docs/stocks
    """
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self, api_key: str):
        """
        Initialize Polygon.io client.
        
        Args:
            api_key: Polygon.io API key
        """
        self.api_key = api_key
        # Polygon.io rate limits vary by plan; using conservative 5 req/sec
        self.rate_limiter = AsyncLimiter(5, 1.0)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_daily_bars(
        self,
        ticker: str,
        start: date,
        end: date
    ) -> List[Bar]:
        """
        Fetch daily bars from Polygon.io.
        
        Endpoint: /v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}
        """
        logger.info(f"Fetching daily bars for {ticker} from {start} to {end}")
        
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start.isoformat()}/{end.isoformat()}"
        
        async with self.rate_limiter:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            try:
                async with self.session.get(
                    url,
                    params={"apiKey": self.api_key, "adjusted": "true"}
                ) as response:
                    if response.status != 200:
                        logger.error(f"Polygon.io API error: {response.status} for {ticker}")
                        return []
                    
                    data = await response.json()
                    
                    if data.get("status") != "OK" or not data.get("results"):
                        logger.warning(f"No data returned for {ticker}")
                        return []
                    
                    bars = []
                    for result in data["results"]:
                        bars.append(Bar(
                            timestamp=datetime.fromtimestamp(result["t"] / 1000),
                            open=result["o"],
                            high=result["h"],
                            low=result["l"],
                            close=result["c"],
                            volume=result["v"],
                            vwap=result.get("vw")
                        ))
                    
                    logger.info(f"Fetched {len(bars)} daily bars for {ticker}")
                    return bars
                    
            except Exception as e:
                logger.error(f"Error fetching daily bars for {ticker}: {e}")
                return []
    
    async def get_intraday_bars(
        self,
        ticker: str,
        date: date,
        timespan: str = "minute"
    ) -> List[Bar]:
        """
        Fetch intraday bars from Polygon.io.
        
        Endpoint: /v2/aggs/ticker/{ticker}/range/1/{timespan}/{from}/{to}
        """
        logger.info(f"Fetching intraday {timespan} bars for {ticker} on {date}")
        
        # Polygon expects same start and end date for intraday
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/{timespan}/{date.isoformat()}/{date.isoformat()}"
        
        async with self.rate_limiter:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            try:
                async with self.session.get(
                    url,
                    params={"apiKey": self.api_key, "adjusted": "true"}
                ) as response:
                    if response.status != 200:
                        logger.error(f"Polygon.io API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    if data.get("status") != "OK" or not data.get("results"):
                        logger.warning(f"No intraday data for {ticker} on {date}")
                        return []
                    
                    bars = []
                    for result in data["results"]:
                        bars.append(Bar(
                            timestamp=datetime.fromtimestamp(result["t"] / 1000),
                            open=result["o"],
                            high=result["h"],
                            low=result["l"],
                            close=result["c"],
                            volume=result["v"],
                            vwap=result.get("vw")
                        ))
                    
                    logger.info(f"Fetched {len(bars)} intraday bars for {ticker}")
                    return bars
                    
            except Exception as e:
                logger.error(f"Error fetching intraday bars: {e}")
                return []
    
    async def get_quote(self, ticker: str) -> Optional[Quote]:
        """
        Get real-time quote from Polygon.io.
        
        Endpoint: /v2/last/nbbo/{ticker}
        """
        logger.info(f"Fetching quote for {ticker}")
        
        url = f"{self.BASE_URL}/v2/last/nbbo/{ticker}"
        
        async with self.rate_limiter:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            try:
                async with self.session.get(
                    url,
                    params={"apiKey": self.api_key}
                ) as response:
                    if response.status != 200:
                        logger.error(f"Polygon.io API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    if data.get("status") != "OK" or not data.get("results"):
                        return None
                    
                    result = data["results"]
                    
                    return Quote(
                        ticker=ticker,
                        timestamp=datetime.fromtimestamp(result.get("t", 0) / 1000000000),
                        bid=result.get("p", 0),
                        ask=result.get("P", 0),
                        bid_size=result.get("s", 0),
                        ask_size=result.get("S", 0),
                        last_price=result.get("p", 0)
                    )
                    
            except Exception as e:
                logger.error(f"Error fetching quote for {ticker}: {e}")
                return None
    
    async def get_snapshot(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker snapshot (current day stats).
        
        Endpoint: /v2/snapshot/locale/us/markets/stocks/tickers/{ticker}
        """
        url = f"{self.BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker}"
        
        async with self.rate_limiter:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            try:
                async with self.session.get(
                    url,
                    params={"apiKey": self.api_key}
                ) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    if data.get("status") != "OK":
                        return None
                    
                    return data.get("ticker")
                    
            except Exception as e:
                logger.error(f"Error fetching snapshot for {ticker}: {e}")
                return None


class MockMarketDataClient:
    """
    Mock market data client for testing without API key.
    
    Returns realistic but fabricated data.
    """
    
    def __init__(self):
        """Initialize mock client."""
        pass
    
    async def get_daily_bars(
        self,
        ticker: str,
        start: date,
        end: date
    ) -> List[Bar]:
        """Generate mock daily bars."""
        bars = []
        current = start
        base_price = 100.0
        
        while current <= end:
            # Skip weekends
            if current.weekday() < 5:
                # Generate realistic-looking bars
                open_price = base_price + (hash(str(current)) % 100 - 50) / 10
                high_price = open_price + (hash(str(current) + "high") % 50) / 10
                low_price = open_price - (hash(str(current) + "low") % 50) / 10
                close_price = (open_price + high_price + low_price) / 3
                volume = 1000000 + (hash(str(current) + "vol") % 5000000)
                
                bars.append(Bar(
                    timestamp=datetime.combine(current, datetime.min.time()),
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                    vwap=(high_price + low_price + close_price) / 3
                ))
                
                base_price = close_price
            
            current += timedelta(days=1)
        
        logger.info(f"Generated {len(bars)} mock daily bars for {ticker}")
        return bars
    
    async def get_intraday_bars(
        self,
        ticker: str,
        date: date,
        timespan: str = "minute"
    ) -> List[Bar]:
        """Generate mock intraday bars."""
        bars = []
        base_price = 100.0
        
        # Generate bars for 9:30 AM - 4:00 PM
        for minute in range(390):  # 6.5 hours = 390 minutes
            timestamp = datetime.combine(date, datetime.min.time())
            timestamp = timestamp.replace(hour=9, minute=30) + timedelta(minutes=minute)
            
            open_price = base_price + (hash(str(minute)) % 20 - 10) / 100
            high_price = open_price + (hash(str(minute) + "h") % 10) / 100
            low_price = open_price - (hash(str(minute) + "l") % 10) / 100
            close_price = (open_price + high_price + low_price) / 3
            volume = 1000 + (hash(str(minute) + "v") % 10000)
            
            bars.append(Bar(
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            ))
            
            base_price = close_price
        
        logger.info(f"Generated {len(bars)} mock intraday bars for {ticker}")
        return bars
    
    async def get_quote(self, ticker: str) -> Optional[Quote]:
        """Generate mock quote."""
        return Quote(
            ticker=ticker,
            timestamp=datetime.now(),
            bid=100.0,
            ask=100.1,
            bid_size=1000,
            ask_size=1000,
            last_price=100.05
        )
