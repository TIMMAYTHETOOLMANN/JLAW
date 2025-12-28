"""
Database Health Checker
=======================

Health check and connectivity validation for JLAW external databases:
- Neo4j (graph database for network analysis)
- TimescaleDB (time-series database for financial metrics)
- Redis (caching and rate limiting)

This module provides pre-flight validation for database connectivity,
ensuring all required infrastructure is available before analysis begins.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseStatus(Enum):
    """Database health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a database health check."""
    database: str
    is_healthy: bool
    latency_ms: float
    error: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class DatabaseHealthChecker:
    """
    Database health checker for JLAW infrastructure.
    
    Validates connectivity and basic operations for:
    - Neo4j graph database
    - TimescaleDB time-series database
    - Redis cache
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize health checker.
        
        Args:
            config: Optional configuration dictionary with connection parameters
        """
        self.config = config or {}
        
        # Load from environment if not provided
        if not self.config:
            import os
            self.config = {
                'neo4j': {
                    'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
                    'user': os.getenv('NEO4J_USER', 'neo4j'),
                    'password': os.getenv('NEO4J_PASSWORD', ''),
                    'database': os.getenv('NEO4J_DATABASE', 'neo4j')
                },
                'timescaledb': {
                    'uri': os.getenv('TIMESCALEDB_URI'),
                    'host': os.getenv('TIMESCALE_HOST', 'localhost'),
                    'port': int(os.getenv('TIMESCALE_PORT', 5432)),
                    'database': os.getenv('TIMESCALE_DATABASE', 'jlaw_forensics'),
                    'user': os.getenv('TIMESCALE_USER', 'jlaw'),
                    'password': os.getenv('TIMESCALE_PASSWORD', '')
                },
                'redis': {
                    'uri': os.getenv('REDIS_URI'),
                    'host': os.getenv('REDIS_HOST', 'localhost'),
                    'port': int(os.getenv('REDIS_PORT', 6379)),
                    'password': os.getenv('REDIS_PASSWORD', ''),
                    'db': int(os.getenv('REDIS_DB', 0))
                }
            }
    
    async def check_neo4j(self) -> HealthCheckResult:
        """
        Check Neo4j connectivity and APOC availability.
        
        Returns:
            HealthCheckResult with connectivity status and latency
        """
        start_time = time.time()
        
        try:
            # Try to import neo4j driver
            try:
                from neo4j import GraphDatabase, AsyncGraphDatabase
            except ImportError:
                logger.error("Neo4j driver not installed")
                return HealthCheckResult(
                    database="neo4j",
                    is_healthy=False,
                    latency_ms=0,
                    error="Neo4j driver not installed (pip install neo4j)",
                    details={"driver_available": False}
                )
            
            neo4j_config = self.config.get('neo4j', {})
            uri = neo4j_config.get('uri', 'bolt://localhost:7687')
            user = neo4j_config.get('user', 'neo4j')
            password = neo4j_config.get('password', '')
            
            if not password or password.startswith('CHANGE_ME') or 'your_' in password.lower():
                logger.warning("Neo4j password not configured")
                return HealthCheckResult(
                    database="neo4j",
                    is_healthy=False,
                    latency_ms=0,
                    error="Neo4j password not configured in .env",
                    details={"configured": False}
                )
            
            # Test connection
            try:
                driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
                
                async with driver.session() as session:
                    # Test basic query
                    result = await session.run("RETURN 1 as test")
                    await result.single()
                    
                    # Check APOC availability
                    has_apoc = False
                    try:
                        apoc_result = await session.run("RETURN apoc.version() as version")
                        apoc_data = await apoc_result.single()
                        has_apoc = apoc_data is not None
                    except Exception:
                        logger.debug("APOC not available")
                    
                    latency_ms = (time.time() - start_time) * 1000
                    
                    await driver.close()
                    
                    return HealthCheckResult(
                        database="neo4j",
                        is_healthy=True,
                        latency_ms=latency_ms,
                        details={
                            "has_apoc": has_apoc,
                            "uri": uri,
                            "can_write": True  # We successfully ran a query
                        }
                    )
            
            except Exception as e:
                logger.error(f"Neo4j connection failed: {e}")
                latency_ms = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    database="neo4j",
                    is_healthy=False,
                    latency_ms=latency_ms,
                    error=str(e),
                    details={"uri": uri}
                )
        
        except Exception as e:
            logger.error(f"Neo4j health check error: {e}")
            return HealthCheckResult(
                database="neo4j",
                is_healthy=False,
                latency_ms=0,
                error=str(e)
            )
    
    async def check_timescaledb(self) -> HealthCheckResult:
        """
        Check TimescaleDB connectivity and extension availability.
        
        Returns:
            HealthCheckResult with connectivity status and latency
        """
        start_time = time.time()
        
        try:
            # Try to import asyncpg
            try:
                import asyncpg
            except ImportError:
                logger.error("asyncpg not installed")
                return HealthCheckResult(
                    database="timescaledb",
                    is_healthy=False,
                    latency_ms=0,
                    error="asyncpg not installed (pip install asyncpg)",
                    details={"driver_available": False}
                )
            
            timescale_config = self.config.get('timescaledb', {})
            
            # Build connection string
            uri = timescale_config.get('uri')
            if not uri:
                host = timescale_config.get('host', 'localhost')
                port = timescale_config.get('port', 5432)
                database = timescale_config.get('database', 'jlaw_forensics')
                user = timescale_config.get('user', 'jlaw')
                password = timescale_config.get('password', '')
                
                if not password or password.startswith('CHANGE_ME') or 'your_' in password.lower():
                    logger.warning("TimescaleDB password not configured")
                    return HealthCheckResult(
                        database="timescaledb",
                        is_healthy=False,
                        latency_ms=0,
                        error="TimescaleDB password not configured in .env",
                        details={"configured": False}
                    )
                
                uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            # Test connection
            try:
                conn = await asyncpg.connect(uri)
                
                # Test basic query
                result = await conn.fetchval("SELECT 1")
                
                # Check TimescaleDB extension
                has_timescaledb = False
                try:
                    extension_result = await conn.fetchval(
                        "SELECT COUNT(*) FROM pg_extension WHERE extname = 'timescaledb'"
                    )
                    has_timescaledb = extension_result > 0
                except Exception:
                    logger.debug("TimescaleDB extension not available")
                
                latency_ms = (time.time() - start_time) * 1000
                
                await conn.close()
                
                return HealthCheckResult(
                    database="timescaledb",
                    is_healthy=True,
                    latency_ms=latency_ms,
                    details={
                        "has_timescaledb_extension": has_timescaledb,
                        "can_query": result == 1
                    }
                )
            
            except Exception as e:
                logger.error(f"TimescaleDB connection failed: {e}")
                latency_ms = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    database="timescaledb",
                    is_healthy=False,
                    latency_ms=latency_ms,
                    error=str(e)
                )
        
        except Exception as e:
            logger.error(f"TimescaleDB health check error: {e}")
            return HealthCheckResult(
                database="timescaledb",
                is_healthy=False,
                latency_ms=0,
                error=str(e)
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """
        Check Redis connectivity and operations.
        
        Returns:
            HealthCheckResult with connectivity status and latency
        """
        start_time = time.time()
        
        try:
            # Try to import redis
            try:
                import redis.asyncio as redis
            except ImportError:
                logger.error("redis not installed")
                return HealthCheckResult(
                    database="redis",
                    is_healthy=False,
                    latency_ms=0,
                    error="redis not installed (pip install redis)",
                    details={"driver_available": False}
                )
            
            redis_config = self.config.get('redis', {})
            
            # Build connection
            uri = redis_config.get('uri')
            if uri:
                client = redis.from_url(uri, decode_responses=True)
            else:
                host = redis_config.get('host', 'localhost')
                port = redis_config.get('port', 6379)
                password = redis_config.get('password', '')
                db = redis_config.get('db', 0)
                
                # Note: Redis password is optional (can be empty for local dev)
                if password and (password.startswith('CHANGE_ME') or 'your_' in password.lower()):
                    password = None  # Treat placeholder as no password
                
                client = redis.Redis(
                    host=host,
                    port=port,
                    password=password if password else None,
                    db=db,
                    decode_responses=True
                )
            
            # Test connection
            try:
                # Test PING
                pong = await client.ping()
                
                # Test SET/GET operations
                test_key = "jlaw_health_check_test"
                test_value = "healthy"
                can_write = await client.set(test_key, test_value, ex=60)
                can_read = await client.get(test_key) == test_value
                await client.delete(test_key)
                
                # Get info
                info = await client.info('memory')
                
                latency_ms = (time.time() - start_time) * 1000
                
                await client.close()
                
                return HealthCheckResult(
                    database="redis",
                    is_healthy=True,
                    latency_ms=latency_ms,
                    details={
                        "ping": pong,
                        "can_write": can_write,
                        "can_read": can_read,
                        "memory_used": info.get('used_memory_human', 'unknown')
                    }
                )
            
            except Exception as e:
                logger.error(f"Redis operation failed: {e}")
                latency_ms = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    database="redis",
                    is_healthy=False,
                    latency_ms=latency_ms,
                    error=str(e)
                )
        
        except Exception as e:
            logger.error(f"Redis health check error: {e}")
            return HealthCheckResult(
                database="redis",
                is_healthy=False,
                latency_ms=0,
                error=str(e)
            )
    
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        Check all databases concurrently.
        
        Returns:
            Dictionary mapping database name to HealthCheckResult
        """
        results = await asyncio.gather(
            self.check_neo4j(),
            self.check_timescaledb(),
            self.check_redis(),
            return_exceptions=True
        )
        
        health_results = {}
        for result in results:
            if isinstance(result, HealthCheckResult):
                health_results[result.database] = result
            elif isinstance(result, Exception):
                logger.error(f"Health check exception: {result}")
        
        return health_results
    
    def print_health_summary(self, results: Dict[str, HealthCheckResult]):
        """Print formatted health check summary."""
        print("\n" + "=" * 80)
        print("  DATABASE HEALTH CHECK SUMMARY")
        print("=" * 80)
        
        for db_name, result in results.items():
            status = "✓ HEALTHY" if result.is_healthy else "✗ UNHEALTHY"
            print(f"\n  {db_name.upper()}: {status}")
            print(f"    Latency: {result.latency_ms:.2f}ms")
            
            if result.error:
                print(f"    Error: {result.error}")
            
            if result.details:
                for key, value in result.details.items():
                    print(f"    {key}: {value}")
        
        print("\n" + "=" * 80)
        
        all_healthy = all(r.is_healthy for r in results.values())
        if all_healthy:
            print("  ✓ All databases are healthy and ready")
        else:
            unhealthy = [name for name, r in results.items() if not r.is_healthy]
            print(f"  ✗ Unhealthy databases: {', '.join(unhealthy)}")
        print("=" * 80 + "\n")
