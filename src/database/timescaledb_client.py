"""
TimescaleDB Integration for Market Data
=======================================

High-performance time-series database for market data storage.

TimescaleDB Features:
- Automatic partitioning (hypertables with chunk_time_interval)
- Compression (90%+ storage savings)
- Continuous aggregates for pre-computed rollups
- Time-based retention policies
- Parallel query execution

Schema:
```sql
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT
);

SELECT create_hypertable('market_data', 'time', chunk_time_interval => INTERVAL '1 day');
```

Use Cases:
- Store historical market data (price, volume)
- Fast time-range queries
- Efficient storage with compression
- Real-time data ingestion
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logger.warning("asyncpg not available. Using mock mode.")

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available.")


@dataclass
class MarketBar:
    """Market data bar (OHLCV)."""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }


class TimescaleDBClient:
    """
    Async TimescaleDB client for market data.
    
    Features:
    - Async operations using asyncpg
    - Bulk insert optimization
    - Time-range queries
    - Compression management
    - Retention policies
    
    Example:
        client = TimescaleDBClient(
            "localhost", 5432, "market_data_db", "user", "password"
        )
        
        await client.connect()
        
        # Insert market data
        bars = [MarketBar(...), MarketBar(...)]
        await client.insert_bars(bars)
        
        # Query data
        bars = await client.get_bars(
            "AAPL",
            start_time=datetime(2023, 1, 1),
            end_time=datetime(2023, 12, 31)
        )
        
        await client.close()
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "market_data",
        user: str = "postgres",
        password: str = "password"
    ):
        """
        Initialize TimescaleDB client.
        
        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        
        self.pool: Optional[Any] = None
        self.mock_mode = not ASYNCPG_AVAILABLE
    
    async def connect(self):
        """Establish connection pool."""
        if self.mock_mode:
            logger.info("Mock mode: Simulating TimescaleDB connection")
            return
        
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=5,
                max_size=20
            )
            logger.info(f"Connected to TimescaleDB at {self.host}:{self.port}")
        
        except Exception as e:
            logger.error(f"Failed to connect to TimescaleDB: {e}")
            raise
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("TimescaleDB connection closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit."""
        await self.close()
    
    async def initialize_schema(self, chunk_interval: str = "1 day"):
        """
        Initialize database schema with hypertable.
        
        Args:
            chunk_interval: Chunk time interval (e.g., "1 day", "1 week")
        """
        if self.mock_mode:
            return
        
        # Create table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS market_data (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume BIGINT,
            PRIMARY KEY (time, symbol)
        );
        """
        
        # Create hypertable
        create_hypertable_sql = f"""
        SELECT create_hypertable(
            'market_data',
            'time',
            chunk_time_interval => INTERVAL '{chunk_interval}',
            if_not_exists => TRUE
        );
        """
        
        # Create index on symbol
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_market_data_symbol
        ON market_data (symbol, time DESC);
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(create_table_sql)
                await conn.execute(create_hypertable_sql)
                await conn.execute(create_index_sql)
                logger.info("TimescaleDB schema initialized")
        
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise
    
    async def enable_compression(
        self,
        segment_by: str = "symbol",
        orderby: str = "time DESC"
    ):
        """
        Enable compression on hypertable.
        
        Args:
            segment_by: Column to segment by (default: symbol)
            orderby: Order by clause (default: time DESC)
        """
        if self.mock_mode:
            return
        
        # Enable compression
        enable_compression_sql = f"""
        ALTER TABLE market_data SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = '{segment_by}',
            timescaledb.compress_orderby = '{orderby}'
        );
        """
        
        # Add compression policy (compress chunks older than 7 days)
        add_policy_sql = """
        SELECT add_compression_policy(
            'market_data',
            INTERVAL '7 days',
            if_not_exists => TRUE
        );
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(enable_compression_sql)
                await conn.execute(add_policy_sql)
                logger.info("Compression enabled on market_data")
        
        except Exception as e:
            logger.error(f"Compression setup failed: {e}")
    
    async def insert_bar(self, bar: MarketBar):
        """Insert single market bar."""
        await self.insert_bars([bar])
    
    async def insert_bars(self, bars: List[MarketBar]):
        """
        Insert multiple market bars (bulk insert).
        
        Args:
            bars: List of MarketBar objects
        """
        if self.mock_mode or not bars:
            return
        
        # Prepare data for bulk insert
        values = [
            (
                bar.timestamp,
                bar.symbol,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume
            )
            for bar in bars
        ]
        
        insert_sql = """
        INSERT INTO market_data (time, symbol, open, high, low, close, volume)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (time, symbol) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.executemany(insert_sql, values)
                logger.debug(f"Inserted {len(bars)} market bars")
        
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    async def get_bars(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[MarketBar]:
        """
        Get market bars for symbol in time range.
        
        Args:
            symbol: Stock symbol
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of MarketBar objects
        """
        if self.mock_mode:
            return []
        
        query = """
        SELECT time, symbol, open, high, low, close, volume
        FROM market_data
        WHERE symbol = $1 AND time >= $2 AND time <= $3
        ORDER BY time ASC
        """
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, symbol, start_time, end_time)
                
                return [
                    MarketBar(
                        timestamp=row['time'],
                        symbol=row['symbol'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    for row in rows
                ]
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    async def get_latest_bar(self, symbol: str) -> Optional[MarketBar]:
        """
        Get latest market bar for symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest MarketBar or None
        """
        if self.mock_mode:
            return None
        
        query = """
        SELECT time, symbol, open, high, low, close, volume
        FROM market_data
        WHERE symbol = $1
        ORDER BY time DESC
        LIMIT 1
        """
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, symbol)
                
                if row:
                    return MarketBar(
                        timestamp=row['time'],
                        symbol=row['symbol'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                return None
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return None
    
    async def delete_old_data(self, older_than_days: int = 365):
        """
        Delete data older than specified days.
        
        Args:
            older_than_days: Delete data older than this many days
        """
        if self.mock_mode:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)
        
        delete_sql = """
        DELETE FROM market_data
        WHERE time < $1
        """
        
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute(delete_sql, cutoff_time)
                logger.info(f"Deleted old data: {result}")
        
        except Exception as e:
            logger.error(f"Delete failed: {e}")
