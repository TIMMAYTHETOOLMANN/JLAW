"""
Database Connectivity Integration Tests
========================================

Integration tests for JLAW external database connectivity:
- Neo4j graph database
- TimescaleDB time-series database
- Redis cache

These tests verify database connectivity, health checks, and basic operations
before forensic analysis begins.
"""

import pytest
import asyncio
import os

from src.database.db_health_checker import DatabaseHealthChecker, HealthCheckResult


class TestDatabaseConnectivity:
    """Integration tests for database connectivity."""
    
    @pytest.mark.asyncio
    async def test_neo4j_connectivity(self):
        """Verify Neo4j connectivity and APOC availability."""
        checker = DatabaseHealthChecker()
        
        try:
            result = await asyncio.wait_for(
                checker.check_neo4j(),
                timeout=30
            )
        except asyncio.TimeoutError:
            pytest.skip("Neo4j health check timed out")
        
        # Check if Neo4j driver is available
        if result.error and "not installed" in result.error:
            pytest.skip("Neo4j driver not installed")
        
        # Check if password is configured
        if result.error and "not configured" in result.error:
            pytest.skip("Neo4j password not configured")
        
        # If Neo4j is running, verify health
        if result.is_healthy:
            assert result.is_healthy, f"Neo4j health check failed: {result.error}"
            assert result.latency_ms < 5000, f"Neo4j latency too high: {result.latency_ms}ms"
            
            # Check details
            assert "can_write" in result.details, "Missing can_write detail"
            assert result.details["can_write"], "Cannot write to Neo4j"
            
            # APOC is optional but recommended
            if "has_apoc" in result.details:
                if not result.details["has_apoc"]:
                    pytest.skip("APOC plugin not available (optional for testing)")
        else:
            pytest.skip(f"Neo4j not available: {result.error}")
    
    @pytest.mark.asyncio
    async def test_timescaledb_connectivity(self):
        """Verify TimescaleDB connectivity and extension availability."""
        checker = DatabaseHealthChecker()
        
        try:
            result = await asyncio.wait_for(
                checker.check_timescaledb(),
                timeout=30
            )
        except asyncio.TimeoutError:
            pytest.skip("TimescaleDB health check timed out")
        
        # Check if asyncpg is available
        if result.error and "not installed" in result.error:
            pytest.skip("asyncpg not installed")
        
        # Check if password is configured
        if result.error and "not configured" in result.error:
            pytest.skip("TimescaleDB password not configured")
        
        # If TimescaleDB is running, verify health
        if result.is_healthy:
            assert result.is_healthy, f"TimescaleDB health check failed: {result.error}"
            assert result.latency_ms < 3000, f"TimescaleDB latency too high: {result.latency_ms}ms"
            
            # Check details
            assert "can_query" in result.details, "Missing can_query detail"
            assert result.details["can_query"], "Cannot query TimescaleDB"
            
            # TimescaleDB extension is optional but recommended
            if "has_timescaledb_extension" in result.details:
                if not result.details["has_timescaledb_extension"]:
                    pytest.skip("TimescaleDB extension not enabled (optional for testing)")
        else:
            pytest.skip(f"TimescaleDB not available: {result.error}")
    
    @pytest.mark.asyncio
    async def test_redis_connectivity(self):
        """Verify Redis connectivity and operations."""
        checker = DatabaseHealthChecker()
        
        try:
            result = await asyncio.wait_for(
                checker.check_redis(),
                timeout=30
            )
        except asyncio.TimeoutError:
            pytest.skip("Redis health check timed out")
        
        # Check if redis is available
        if result.error and "not installed" in result.error:
            pytest.skip("redis not installed")
        
        # If Redis is running, verify health
        if result.is_healthy:
            assert result.is_healthy, f"Redis health check failed: {result.error}"
            assert result.latency_ms < 1000, f"Redis latency too high: {result.latency_ms}ms"
            
            # Check details
            assert "can_write" in result.details, "Missing can_write detail"
            assert "can_read" in result.details, "Missing can_read detail"
            assert result.details["can_write"], "Cannot write to Redis"
            assert result.details["can_read"], "Cannot read from Redis"
            assert result.details["ping"], "Redis PING failed"
        else:
            pytest.skip(f"Redis not available: {result.error}")
    
    @pytest.mark.asyncio
    async def test_all_databases_health_check(self):
        """Test health check for all databases concurrently."""
        checker = DatabaseHealthChecker()
        
        try:
            results = await asyncio.wait_for(
                checker.check_all(),
                timeout=60
            )
        except asyncio.TimeoutError:
            pytest.skip("All databases health check timed out")
        
        # Verify we got results for all databases
        assert "neo4j" in results, "Missing Neo4j result"
        assert "timescaledb" in results, "Missing TimescaleDB result"
        assert "redis" in results, "Missing Redis result"
        
        # Each result should be a HealthCheckResult
        for db_name, result in results.items():
            assert isinstance(result, HealthCheckResult), f"{db_name} result is not HealthCheckResult"
            assert result.database == db_name, f"Database name mismatch for {db_name}"
    
    @pytest.mark.asyncio
    async def test_database_graceful_degradation(self):
        """Test that system handles unavailable databases gracefully."""
        # Create checker with invalid configuration
        invalid_config = {
            'neo4j': {
                'uri': 'bolt://invalid-host:7687',
                'user': 'neo4j',
                'password': 'invalid_password',
                'database': 'neo4j'
            },
            'timescaledb': {
                'host': 'invalid-host',
                'port': 5432,
                'database': 'jlaw_forensics',
                'user': 'jlaw',
                'password': 'invalid_password'
            },
            'redis': {
                'host': 'invalid-host',
                'port': 6379,
                'password': '',
                'db': 0
            }
        }
        
        checker = DatabaseHealthChecker(config=invalid_config)
        
        try:
            results = await asyncio.wait_for(
                checker.check_all(),
                timeout=30
            )
            
            # All should fail but not raise exceptions
            for db_name, result in results.items():
                assert not result.is_healthy, f"{db_name} should be unhealthy with invalid config"
                assert result.error is not None, f"{db_name} should have error message"
        
        except asyncio.TimeoutError:
            pytest.skip("Graceful degradation test timed out")
    
    @pytest.mark.asyncio
    async def test_password_placeholder_detection(self):
        """Test that placeholder passwords are detected."""
        config_with_placeholders = {
            'neo4j': {
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': 'CHANGE_ME_SECURE_NEO4J_PASSWORD',
                'database': 'neo4j'
            },
            'timescaledb': {
                'host': 'localhost',
                'port': 5432,
                'database': 'jlaw_forensics',
                'user': 'jlaw',
                'password': 'your_timescale_password_here'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'password': 'CHANGE_ME_REDIS_PASSWORD',
                'db': 0
            }
        }
        
        checker = DatabaseHealthChecker(config=config_with_placeholders)
        
        # Test Neo4j
        neo4j_result = await checker.check_neo4j()
        assert not neo4j_result.is_healthy, "Should detect Neo4j password placeholder"
        assert "not configured" in neo4j_result.error, "Should indicate password not configured"
        
        # Test TimescaleDB
        timescaledb_result = await checker.check_timescaledb()
        assert not timescaledb_result.is_healthy, "Should detect TimescaleDB password placeholder"
        assert "not configured" in timescaledb_result.error, "Should indicate password not configured"


@pytest.mark.asyncio
async def test_database_health_summary_output():
    """Test that health summary can be printed without errors."""
    checker = DatabaseHealthChecker()
    
    try:
        results = await asyncio.wait_for(
            checker.check_all(),
            timeout=60
        )
        
        # Should not raise exception when printing
        checker.print_health_summary(results)
        
    except asyncio.TimeoutError:
        pytest.skip("Health summary test timed out")


@pytest.mark.asyncio
async def test_database_latency_reporting(self):
    """Test that database latency is properly reported."""
    checker = DatabaseHealthChecker()
    
    try:
        results = await asyncio.wait_for(
            checker.check_all(),
            timeout=60
        )
        
        for db_name, result in results.items():
            # Latency should be non-negative
            assert result.latency_ms >= 0, f"{db_name} latency should be non-negative"
            
            # If healthy, latency should be reasonable
            if result.is_healthy:
                assert result.latency_ms < 10000, f"{db_name} latency unreasonably high: {result.latency_ms}ms"
    
    except asyncio.TimeoutError:
        pytest.skip("Latency reporting test timed out")
