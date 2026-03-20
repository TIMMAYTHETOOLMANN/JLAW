"""
Test Phase Gate Enforcement (Critical Finding 5)
==================================================

Verifies that _enforce_phase_gate halts execution for ALL phases,
not just a critical subset.  Every phase in the 11-phase pipeline
must halt on non-success status — no exceptions.
"""

from datetime import date

import pytest

from src.core.exceptions import PhaseGateFailure
from src.core.unified_orchestrator import UnifiedForensicOrchestrator


@pytest.fixture
def orchestrator():
    """Create orchestrator for testing phase gates."""
    return UnifiedForensicOrchestrator(
        cik="320187",
        company_name="Test Corp",
        start_date=date(2019, 1, 1),
        end_date=date(2019, 12, 31),
    )


class TestPhaseGateEnforcement:
    """All 11 phases must halt on non-success status."""

    ALL_PHASES = [f"phase_{i}" for i in range(1, 12)]

    @pytest.mark.parametrize("phase_key", ALL_PHASES)
    def test_error_status_halts_pipeline(self, orchestrator, phase_key):
        """Any phase returning status='error' must raise PhaseGateFailure."""
        result = {"status": "error", "error": "something went wrong"}
        with pytest.raises(PhaseGateFailure, match=phase_key):
            orchestrator._enforce_phase_gate(phase_key, result)

    @pytest.mark.parametrize("phase_key", ALL_PHASES)
    def test_degraded_status_halts_pipeline(self, orchestrator, phase_key):
        """Any phase returning status='degraded' must raise PhaseGateFailure."""
        result = {"status": "degraded", "reason": "fallback used"}
        with pytest.raises(PhaseGateFailure, match=phase_key):
            orchestrator._enforce_phase_gate(phase_key, result)

    @pytest.mark.parametrize("phase_key", ALL_PHASES)
    def test_unknown_status_halts_pipeline(self, orchestrator, phase_key):
        """Any phase returning an unknown status must raise PhaseGateFailure."""
        result = {"status": "partial"}
        with pytest.raises(PhaseGateFailure, match=phase_key):
            orchestrator._enforce_phase_gate(phase_key, result)

    @pytest.mark.parametrize("phase_key", ALL_PHASES)
    def test_missing_status_halts_pipeline(self, orchestrator, phase_key):
        """A phase result with no status key must raise PhaseGateFailure."""
        result = {"some_data": 42}
        with pytest.raises(PhaseGateFailure, match=phase_key):
            orchestrator._enforce_phase_gate(phase_key, result)

    @pytest.mark.parametrize("phase_key", ALL_PHASES)
    def test_success_status_passes(self, orchestrator, phase_key):
        """status='success' must not raise."""
        result = {"status": "success"}
        orchestrator._enforce_phase_gate(phase_key, result)  # no exception

    @pytest.mark.parametrize("phase_key", ALL_PHASES)
    def test_skipped_status_passes(self, orchestrator, phase_key):
        """status='skipped' must not raise."""
        result = {"status": "skipped", "reason": "disabled"}
        orchestrator._enforce_phase_gate(phase_key, result)  # no exception


class TestCriticalPhasesCoversAll:
    """_CRITICAL_PHASES must contain all 11 phases."""

    def test_all_11_phases_are_critical(self):
        expected = {f"phase_{i}" for i in range(1, 12)}
        assert UnifiedForensicOrchestrator._CRITICAL_PHASES == expected

    def test_critical_phases_count(self):
        assert len(UnifiedForensicOrchestrator._CRITICAL_PHASES) == 11


class TestPhaseGateFailureAttributes:
    """PhaseGateFailure carries phase_id and rule metadata."""

    def test_phase_gate_failure_has_phase_id(self, orchestrator):
        result = {"status": "error", "error": "boom"}
        with pytest.raises(PhaseGateFailure) as exc_info:
            orchestrator._enforce_phase_gate("phase_7", result)
        assert exc_info.value.phase_id == "phase_7"

    def test_phase_gate_failure_has_rule(self, orchestrator):
        result = {"status": "error", "error": "boom"}
        with pytest.raises(PhaseGateFailure) as exc_info:
            orchestrator._enforce_phase_gate("phase_7", result)
        assert exc_info.value.rule == "phase_success_required"

    def test_phase_gate_failure_message_includes_halt(self, orchestrator):
        result = {"status": "degraded", "error": "fallback"}
        with pytest.raises(PhaseGateFailure, match="Pipeline halted"):
            orchestrator._enforce_phase_gate("phase_10", result)
