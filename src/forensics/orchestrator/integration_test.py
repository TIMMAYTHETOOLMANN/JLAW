"""Integration Test Suite for Phase 8 Master Forensic Controller.

Provides test infrastructure and system health checks for validation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test execution status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of an individual test.

    Attributes:
        name: Test name.
        status: Test status.
        message: Optional message or error details.
        duration_ms: Test duration in milliseconds.
    """

    name: str
    status: TestStatus
    message: Optional[str] = None
    duration_ms: float = 0.0

    @property
    def passed(self) -> bool:
        """Check if test passed."""
        return self.status == TestStatus.PASSED


@dataclass
class SystemHealth:
    """Overall system health status.

    Attributes:
        healthy: Whether all critical components are healthy.
        components: Health status of individual components.
        warnings: List of warning messages.
        errors: List of error messages.
    """

    healthy: bool = True
    components: Dict[str, bool] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_component(self, name: str, is_healthy: bool, message: Optional[str] = None):
        """Add a component health status."""
        self.components[name] = is_healthy
        if not is_healthy:
            self.healthy = False
            if message:
                self.errors.append(f"{name}: {message}")


class IntegrationTestSuite:
    """Integration test suite for forensic system validation.

    Provides automated testing of all system phases and components.
    """

    def __init__(self):
        self.results: List[TestResult] = []
        self.health = SystemHealth()

    def run_all_tests(self) -> SystemHealth:
        """Run all integration tests and return system health."""
        self._test_phase_imports()
        self._test_core_components()
        return self.health

    def _test_phase_imports(self):
        """Test that all phase modules can be imported."""
        phases = [
            ("phase_1", "src.forensics.sec_forensic_extraction_system"),
            ("phase_2", "src.forensics.intelligence"),
            ("phase_3", "src.forensics.legal"),
            ("phase_4", "src.forensics.temporal_analysis"),
            ("phase_5", "src.forensics.decision_engine"),
            ("phase_6", "src.forensics.contradiction_detection"),
            ("phase_7", "src.forensics.reporting"),
            ("phase_8", "src.forensics.orchestrator"),
            ("phase_9", "src.forensics.deployment"),
        ]

        for phase_name, module_path in phases:
            try:
                __import__(module_path)
                self.results.append(
                    TestResult(name=f"import_{phase_name}", status=TestStatus.PASSED)
                )
                self.health.add_component(phase_name, True)
            except ImportError as e:
                self.results.append(
                    TestResult(
                        name=f"import_{phase_name}",
                        status=TestStatus.FAILED,
                        message=str(e),
                    )
                )
                self.health.add_component(phase_name, False, str(e))

    def _test_core_components(self):
        """Test core system components."""
        try:
            from src.forensics import SECForensicAnalyzer

            self.results.append(
                TestResult(name="sec_analyzer_available", status=TestStatus.PASSED)
            )
            self.health.add_component("sec_analyzer", True)
        except Exception as e:
            self.results.append(
                TestResult(
                    name="sec_analyzer_available",
                    status=TestStatus.FAILED,
                    message=str(e),
                )
            )
            self.health.add_component("sec_analyzer", False, str(e))

    def get_summary(self) -> Dict[str, int]:
        """Get summary of test results."""
        summary = {status.value: 0 for status in TestStatus}
        for result in self.results:
            summary[result.status.value] += 1
        return summary
