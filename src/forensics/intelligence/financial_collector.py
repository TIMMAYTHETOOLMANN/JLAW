"""
Financial Data Collector - Market Data Intelligence
==================================================

Multi-source financial data aggregation:
- Yahoo Finance (yfinance) - Free historical and real-time data
- Polygon.io - Professional market data
- Alpha Vantage - Free API with rate limits
- Unusual Whales - Options flow data

Features:
- Price history and technical indicators
- Options flow analysis
- Institutional holdings tracking
- Dark pool activity monitoring
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Market data point"""
    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None


@dataclass
class OptionsFlow:
    """Options flow data"""
    ticker: str
    timestamp: datetime
    option_type: str  # 'call' or 'put'
    strike: float
    expiration: datetime
    premium: float
    volume: int
    open_interest: int
    implied_volatility: float
    sentiment: str  # 'bullish', 'bearish', 'neutral'


class FinancialDataCollector:
    """
    Multi-source financial data collector
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API keys from config
        self.polygon_api_key = self.config.get('polygon_api_key')
        self.alpha_vantage_key = self.config.get('alpha_vantage_key')
        
        # Statistics
        self.stats = {
            'price_data_points': 0,
            'options_flow_items': 0,
            'api_calls': 0
        }
    
    async def gather(
        self,
        target: str,
        lookback_days: int = 90,
        max_items: int = 1000
    ) -> List[Any]:
        """
        Gather financial market intelligence
        
        Args:
            target: Ticker symbol
            lookback_days: Historical data window
            max_items: Maximum data points
        
        Returns:
            List of IntelligenceItem objects
        """
        logger.info(f"💰 Gathering financial data for: {target}")
        
        # Gather price history
        price_data = await self._get_price_history(
            target,
            lookback_days
        )
        
        # Gather options flow (if available)
        options_data = await self._get_options_flow(
            target,
            lookback_days
        )
        
        # Convert to intelligence items
        intelligence_items = await self._convert_to_intelligence(
            target,
            price_data,
            options_data
        )
        
        logger.info(f"✓ Collected {len(intelligence_items)} financial intelligence items")
        
        return intelligence_items
    
    async def _get_price_history(
        self,
        ticker: str,
        lookback_days: int
    ) -> List[MarketData]:
        """Get historical price data"""
        try:
            # Try yfinance first (free)
            import yfinance as yf
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            # Download data
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)
            
            # Convert to MarketData objects
            market_data = []
            for timestamp, row in hist.iterrows():
                data = MarketData(
                    ticker=ticker,
                    timestamp=timestamp,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    close=row['Close'],
                    volume=int(row['Volume']),
                    adj_close=row.get('Adj Close')
                )
                market_data.append(data)
            
            self.stats['price_data_points'] += len(market_data)
            logger.info(f"✓ Retrieved {len(market_data)} price data points")
            
            return market_data
            
        except Exception as e:
            logger.error(f"❌ Price data collection failed: {e}")
            return []
    
    async def _get_options_flow(
        self,
        ticker: str,
        lookback_days: int
    ) -> List[OptionsFlow]:
        """Get options flow data"""
        # Placeholder - requires premium data subscription
        logger.info("📊 Options flow collection not implemented (requires premium data)")
        return []
    
    async def _convert_to_intelligence(
        self,
        ticker: str,
        price_data: List[MarketData],
        options_data: List[OptionsFlow]
    ) -> List[Any]:
        """Convert financial data to intelligence items"""
        from .omniscient_gatherer import IntelligenceItem
        
        intelligence_items = []
        
        # Price movement intelligence
        if len(price_data) >= 2:
            # Calculate significant movements
            for i in range(1, len(price_data)):
                prev = price_data[i-1]
                curr = price_data[i]
                
                # Calculate daily return
                daily_return = (curr.close - prev.close) / prev.close
                
                # Flag significant movements (>5%)
                if abs(daily_return) > 0.05:
                    content = (
                        f"{ticker} moved {daily_return*100:.2f}% "
                        f"from ${prev.close:.2f} to ${curr.close:.2f} "
                        f"on volume {curr.volume:,}"
                    )
                    
                    item = IntelligenceItem(
                        content=content,
                        source='yfinance',
                        timestamp=curr.timestamp,
                        entities=[ticker],
                        confidence=0.95,
                        category='price_movement',
                        metadata={
                            'daily_return': daily_return,
                            'volume': curr.volume,
                            'open': curr.open,
                            'close': curr.close,
                            'high': curr.high,
                            'low': curr.low
                        }
                    )
                    
                    intelligence_items.append(item)
        
        # Volume anomalies
        if price_data:
            avg_volume = sum(d.volume for d in price_data) / len(price_data)
            
            for data in price_data:
                # Flag unusual volume (>2x average)
                if data.volume > avg_volume * 2:
                    content = (
                        f"{ticker} unusual volume: {data.volume:,} "
                        f"({data.volume/avg_volume:.1f}x average)"
                    )
                    
                    item = IntelligenceItem(
                        content=content,
                        source='yfinance',
                        timestamp=data.timestamp,
                        entities=[ticker],
                        confidence=0.85,
                        category='volume_anomaly',
                        metadata={
                            'volume': data.volume,
                            'average_volume': avg_volume,
                            'ratio': data.volume / avg_volume
                        }
                    )
                    
                    intelligence_items.append(item)
        
        return intelligence_items
    
    def calculate_technical_indicators(
        self,
        price_data: List[MarketData]
    ) -> Dict[str, Any]:
        """
        Calculate technical indicators
        """
        if len(price_data) < 20:
            return {}
        
        closes = [d.close for d in price_data]
        
        indicators = {}
        
        # Simple Moving Average (SMA)
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        
        indicators['sma_20'] = sma_20
        indicators['sma_50'] = sma_50
        
        # Current price vs SMA
        current_price = closes[-1]
        indicators['price_vs_sma20'] = (current_price - sma_20) / sma_20
        
        if sma_50:
            indicators['price_vs_sma50'] = (current_price - sma_50) / sma_50
        
        # Volatility (standard deviation)
        mean_price = sum(closes) / len(closes)
        variance = sum((p - mean_price) ** 2 for p in closes) / len(closes)
        std_dev = variance ** 0.5
        
        indicators['volatility'] = std_dev / mean_price
        
        # Trend (linear regression slope)
        n = len(closes)
        x_mean = (n - 1) / 2
        y_mean = mean_price
        
        numerator = sum((i - x_mean) * (closes[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator != 0:
            slope = numerator / denominator
            indicators['trend_slope'] = slope
            indicators['trend_direction'] = 'bullish' if slope > 0 else 'bearish'
        
        return indicators
    
    def detect_price_anomalies(
        self,
        price_data: List[MarketData],
        threshold_sigma: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect price anomalies using statistical methods
        """
        if len(price_data) < 20:
            return []
        
        # Calculate returns
        returns = []
        for i in range(1, len(price_data)):
            ret = (price_data[i].close - price_data[i-1].close) / price_data[i-1].close
            returns.append(ret)
        
        # Calculate mean and std dev
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        # Detect anomalies
        anomalies = []
        
        for i, ret in enumerate(returns):
            z_score = (ret - mean_return) / std_dev if std_dev != 0 else 0
            
            if abs(z_score) > threshold_sigma:
                anomalies.append({
                    'date': price_data[i+1].timestamp,
                    'return': ret,
                    'z_score': z_score,
                    'price': price_data[i+1].close,
                    'volume': price_data[i+1].volume,
                    'severity': 'high' if abs(z_score) > 3.0 else 'medium'
                })
        
        return anomalies


if __name__ == "__main__":
    # Demo
    async def demo():
        collector = FinancialDataCollector()
        
        items = await collector.gather('AAPL', lookback_days=30)
        print(f"Collected {len(items)} financial intelligence items")
    
    asyncio.run(demo())

