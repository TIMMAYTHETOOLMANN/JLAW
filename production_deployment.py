#!/usr/bin/env python3
"""
JLAW Production Deployment Entry Point
======================================
Main entry point for containerized JLAW deployment.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from forensics import ForensicOrchestrator
from forensics.deployment.health_checker import HealthChecker, HealthStatus
from forensics.deployment.metrics_collector import start_metrics_server, get_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger("JLAW.Production")


async def run_health_checks():
    """Run system health checks."""
    checker = HealthChecker()
    results = await checker.check_all_components()

    for check, result in results.items():
        level = logging.INFO if result.status == HealthStatus.HEALTHY else logging.WARNING
        logger.log(level, f"Health check [{check}]: {result.message}")

    overall = checker.get_overall_health(results)
    return overall == HealthStatus.HEALTHY


async def main():
    """Main production entry point."""
    logger.info("=" * 60)
    logger.info("JLAW Forensic Intelligence System - Production Mode")
    logger.info("=" * 60)

    # Ensure required directories exist
    Path("logs").mkdir(exist_ok=True)
    Path("forensic_storage").mkdir(exist_ok=True)

    # Run health checks
    healthy = await run_health_checks()
    if not healthy:
        logger.warning("Some health checks failed - proceeding with caution")

    # Start metrics server
    metrics_port = int(os.environ.get("METRICS_PORT", "8000"))
    try:
        start_metrics_server(metrics_port)
        logger.info(f"Metrics server started on port {metrics_port}")
    except Exception as e:
        logger.warning(f"Metrics server failed to start: {e}")

    # Log that system is ready
    logger.info("JLAW Production service ready - awaiting analysis requests")
    
    # Increment start counter
    try:
        get_metrics().app_starts.inc()
    except Exception:
        pass

    try:
        # In production, this would listen for incoming analysis requests
        # For now, keep alive and serve metrics
        while True:
            await asyncio.sleep(60)
            logger.debug("Service heartbeat - system operational")
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Production error: {e}")
        raise
    finally:
        logger.info("JLAW Production service shutting down")


if __name__ == "__main__":
    asyncio.run(main())
