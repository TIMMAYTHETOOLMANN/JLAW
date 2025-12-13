"""
Polygon.io WebSocket Client
===========================

Real-time market data streaming via WebSocket.
Supports stocks, options, forex, and crypto feeds.

WebSocket Documentation: https://polygon.io/docs/stocks/ws_getting-started
"""

import asyncio
import websockets
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    TRADE = "T"
    QUOTE = "Q"
    AGGREGATE = "A"
    AGGREGATE_MINUTE = "AM"


@dataclass
class Trade:
    """Real-time trade data."""
    symbol: str
    timestamp: datetime
    price: float
    size: int
    exchange: Optional[str] = None
    conditions: Optional[List[int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "size": self.size,
            "exchange": self.exchange,
            "conditions": self.conditions
        }


@dataclass
class Quote:
    """Real-time quote data."""
    symbol: str
    timestamp: datetime
    bid_price: float
    bid_size: int
    ask_price: float
    ask_size: int
    bid_exchange: Optional[str] = None
    ask_exchange: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "bid_price": self.bid_price,
            "bid_size": self.bid_size,
            "ask_price": self.ask_price,
            "ask_size": self.ask_size,
            "bid_exchange": self.bid_exchange,
            "ask_exchange": self.ask_exchange
        }


@dataclass
class AggregateBar:
    """Real-time aggregate bar."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "vwap": self.vwap
        }


class PolygonWebSocketClient:
    """
    Polygon.io WebSocket streaming client.
    
    Features:
    - Real-time trades, quotes, and aggregates
    - Automatic reconnection on disconnect
    - Subscription management
    - Message filtering and callbacks
    """
    
    WS_URL = "wss://socket.polygon.io"
    
    def __init__(
        self,
        api_key: str,
        clusters: Optional[List[str]] = None
    ):
        """
        Initialize WebSocket client.
        
        Args:
            api_key: Polygon.io API key
            clusters: Market clusters (default: ["stocks"])
        """
        self.api_key = api_key
        self.clusters = clusters or ["stocks"]
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscriptions: Set[str] = set()
        self.running = False
        
        # Callbacks for different message types
        self.trade_callback: Optional[Callable[[Trade], None]] = None
        self.quote_callback: Optional[Callable[[Quote], None]] = None
        self.aggregate_callback: Optional[Callable[[AggregateBar], None]] = None
    
    async def connect(self):
        """Establish WebSocket connection and authenticate."""
        ws_url = f"{self.WS_URL}/{self.clusters[0]}"
        
        try:
            self.ws = await websockets.connect(ws_url)
            logger.info(f"Connected to Polygon WebSocket: {ws_url}")
            
            # Authenticate
            auth_msg = {"action": "auth", "params": self.api_key}
            await self.ws.send(json.dumps(auth_msg))
            
            # Wait for auth response
            response = await self.ws.recv()
            data = json.loads(response)
            
            if data[0].get("status") == "auth_success":
                logger.info("WebSocket authentication successful")
            else:
                logger.error(f"WebSocket auth failed: {data}")
                raise ConnectionError("Authentication failed")
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close WebSocket connection."""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
            logger.info("WebSocket disconnected")
    
    async def subscribe(self, symbols: List[str], message_types: Optional[List[str]] = None):
        """
        Subscribe to real-time data for symbols.
        
        Args:
            symbols: List of ticker symbols
            message_types: Message types to subscribe to (default: ["T"] for trades)
                          Options: "T" (trades), "Q" (quotes), "A" (second aggs), "AM" (minute aggs)
        
        Example:
            await client.subscribe(["AAPL", "GOOGL"], ["T", "Q"])
        """
        if not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if message_types is None:
            message_types = ["T"]
        
        # Build subscription strings
        subs = []
        for msg_type in message_types:
            for symbol in symbols:
                sub_str = f"{msg_type}.{symbol}"
                subs.append(sub_str)
                self.subscriptions.add(sub_str)
        
        # Send subscription message
        sub_msg = {"action": "subscribe", "params": ",".join(subs)}
        await self.ws.send(json.dumps(sub_msg))
        logger.info(f"Subscribed to: {subs}")
    
    async def unsubscribe(self, symbols: List[str], message_types: Optional[List[str]] = None):
        """
        Unsubscribe from symbols.
        
        Args:
            symbols: List of ticker symbols
            message_types: Message types to unsubscribe from
        """
        if not self.ws:
            return
        
        if message_types is None:
            message_types = ["T"]
        
        subs = []
        for msg_type in message_types:
            for symbol in symbols:
                sub_str = f"{msg_type}.{symbol}"
                subs.append(sub_str)
                self.subscriptions.discard(sub_str)
        
        unsub_msg = {"action": "unsubscribe", "params": ",".join(subs)}
        await self.ws.send(json.dumps(unsub_msg))
        logger.info(f"Unsubscribed from: {subs}")
    
    def _parse_trade(self, msg: Dict) -> Trade:
        """Parse trade message."""
        return Trade(
            symbol=msg.get("sym", ""),
            timestamp=datetime.fromtimestamp(msg.get("t", 0) / 1000),
            price=msg.get("p", 0.0),
            size=msg.get("s", 0),
            exchange=msg.get("x"),
            conditions=msg.get("c")
        )
    
    def _parse_quote(self, msg: Dict) -> Quote:
        """Parse quote message."""
        return Quote(
            symbol=msg.get("sym", ""),
            timestamp=datetime.fromtimestamp(msg.get("t", 0) / 1000),
            bid_price=msg.get("bp", 0.0),
            bid_size=msg.get("bs", 0),
            ask_price=msg.get("ap", 0.0),
            ask_size=msg.get("as", 0),
            bid_exchange=msg.get("bx"),
            ask_exchange=msg.get("ax")
        )
    
    def _parse_aggregate(self, msg: Dict) -> AggregateBar:
        """Parse aggregate bar message."""
        return AggregateBar(
            symbol=msg.get("sym", ""),
            timestamp=datetime.fromtimestamp(msg.get("s", 0) / 1000),
            open=msg.get("o", 0.0),
            high=msg.get("h", 0.0),
            low=msg.get("l", 0.0),
            close=msg.get("c", 0.0),
            volume=msg.get("v", 0),
            vwap=msg.get("vw")
        )
    
    async def _handle_message(self, msg: Dict):
        """Handle incoming WebSocket message."""
        ev_type = msg.get("ev")
        
        if ev_type == "T":  # Trade
            if self.trade_callback:
                trade = self._parse_trade(msg)
                self.trade_callback(trade)
        
        elif ev_type == "Q":  # Quote
            if self.quote_callback:
                quote = self._parse_quote(msg)
                self.quote_callback(quote)
        
        elif ev_type in ["A", "AM"]:  # Aggregate
            if self.aggregate_callback:
                aggregate = self._parse_aggregate(msg)
                self.aggregate_callback(aggregate)
        
        elif ev_type == "status":
            logger.info(f"Status: {msg.get('message')}")
    
    async def start_streaming(self):
        """
        Start streaming messages.
        
        This will continuously listen for messages and call registered callbacks.
        Run this in a background task after subscribing.
        
        Example:
            client = PolygonWebSocketClient(api_key)
            await client.connect()
            await client.subscribe(["AAPL"])
            
            # Run streaming in background
            task = asyncio.create_task(client.start_streaming())
            
            # ... do other work ...
            
            # Stop streaming
            await client.disconnect()
        """
        if not self.ws:
            raise RuntimeError("Not connected. Call connect() first.")
        
        self.running = True
        logger.info("Started streaming messages")
        
        try:
            while self.running:
                try:
                    message = await asyncio.wait_for(self.ws.recv(), timeout=60)
                    data = json.loads(message)
                    
                    # Handle array of messages
                    if isinstance(data, list):
                        for msg in data:
                            await self._handle_message(msg)
                    else:
                        await self._handle_message(data)
                
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    if self.ws:
                        await self.ws.ping()
                    continue
                
                except websockets.exceptions.ConnectionClosed:
                    logger.warning("WebSocket connection closed, attempting reconnect...")
                    await asyncio.sleep(5)
                    try:
                        await self.connect()
                        # Re-subscribe to previous subscriptions
                        if self.subscriptions:
                            sub_msg = {"action": "subscribe", "params": ",".join(self.subscriptions)}
                            await self.ws.send(json.dumps(sub_msg))
                    except Exception as e:
                        logger.error(f"Reconnection failed: {e}")
                        break
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        
        finally:
            self.running = False
            logger.info("Stopped streaming")
    
    def on_trade(self, callback: Callable[[Trade], None]):
        """Register callback for trade messages."""
        self.trade_callback = callback
    
    def on_quote(self, callback: Callable[[Quote], None]):
        """Register callback for quote messages."""
        self.quote_callback = callback
    
    def on_aggregate(self, callback: Callable[[AggregateBar], None]):
        """Register callback for aggregate messages."""
        self.aggregate_callback = callback
