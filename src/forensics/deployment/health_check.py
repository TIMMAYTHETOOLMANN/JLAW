"""
System Health Check - Phase 9
=============================
Lightweight health check primitives used by deployment and research runs.

Design goals:
- No hard dependency on external services. All integrations are optional.
- Fail-safe: missing libraries or services should not crash the process.
"""

from __future__ import annotations

import socket
import time
import shutil
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class HealthStatus:
    OK = "OK"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class ComponentHealth:
    name: str
    status: str
    details: Dict[str, str] = field(default_factory=dict)


class SystemHealthCheck:
    """Basic health checks for filesystem, network, and optional services."""

    def __init__(self):
        logger.info("✅ SystemHealthCheck initialized")

    def check_filesystem(self, path: str = ".", min_free_mb: int = 100) -> ComponentHealth:
        try:
            usage = shutil.disk_usage(path)
            free_mb = usage.free // (1024 * 1024)
            status = HealthStatus.OK if free_mb >= min_free_mb else HealthStatus.WARN
            return ComponentHealth(
                name="filesystem",
                status=status,
                details={"path": path, "free_mb": str(free_mb)}
            )
        except Exception as e:
            return ComponentHealth(name="filesystem", status=HealthStatus.FAIL, details={"error": str(e)})

    def check_network(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 1.5) -> ComponentHealth:
        """DNS-style ping using TCP connect to avoid ICMP requirements."""
        start = time.time()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                elapsed_ms = int((time.time() - start) * 1000)
                return ComponentHealth(
                    name="network",
                    status=HealthStatus.OK,
                    details={"host": host, "port": str(port), "latency_ms": str(elapsed_ms)}
                )
        except Exception as e:
            return ComponentHealth(name="network", status=HealthStatus.WARN, details={"error": str(e)})

    def check_http(self, url: str, timeout: float = 3.0) -> ComponentHealth:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "JLAW-HealthCheck/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return ComponentHealth(
                    name="http",
                    status=HealthStatus.OK if 200 <= resp.status < 400 else HealthStatus.WARN,
                    details={"url": url, "status": str(resp.status)}
                )
        except Exception as e:
            return ComponentHealth(name="http", status=HealthStatus.WARN, details={"url": url, "error": str(e)})

    def check_optional_service(self, name: str, host: str, port: int, timeout: float = 1.0) -> ComponentHealth:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return ComponentHealth(name=name, status=HealthStatus.OK, details={"host": host, "port": str(port)})
        except Exception as e:
            # WARN rather than FAIL for research environment
            return ComponentHealth(name=name, status=HealthStatus.WARN, details={"host": host, "port": str(port), "error": str(e)})

    def run_all(self, checks: Optional[List[str]] = None) -> Dict[str, ComponentHealth]:
        """Execute a standard suite of checks. 'checks' may include: filesystem, network.
        Returns a dict mapping component name to ComponentHealth.
        """
        selected = checks or ["filesystem", "network"]
        results: Dict[str, ComponentHealth] = {}
        if "filesystem" in selected:
            results["filesystem"] = self.check_filesystem()
        if "network" in selected:
            results["network"] = self.check_network()
        return results
