#!/usr/bin/env python3
"""
JLAW Production Deployment Entry Point
======================================
Main entry point for containerized JLAW deployment.

This script serves as the Docker container entry point and provides:
- System health checks on startup
- Prometheus metrics endpoint on METRICS_PORT (default: 8000)
- Graceful shutdown handling via SIGINT/SIGTERM
"""

import os
import signal
import sys
import asyncio
import logging
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from forensics.deployment.health_checker import HealthChecker, HealthStatus
    from forensics.deployment.metrics_collector import start_metrics_server, get_metrics
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}", file=sys.stderr)
    print("Ensure the forensics package is properly installed.", file=sys.stderr)
    sys.exit(1)

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
    
    # Increment start counter (metrics may fail if prometheus_client not available)
    try:
        get_metrics().app_starts.inc()
    except ImportError:
        logger.debug("Prometheus client not available, skipping metrics increment")

    # Set up shutdown event for graceful termination
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, initiating graceful shutdown")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Main service loop - keeps container alive and serves metrics
        # Production deployments should configure orchestration via API or job scheduler
        while not shutdown_event.is_set():
            await asyncio.sleep(60)
            logger.debug("Service heartbeat - system operational")
    except Exception as e:
        logger.error(f"Production error: {e}")
        raise
    finally:
        logger.info("JLAW Production service shutting down")


if __name__ == "__main__":
    asyncio.run(main())
