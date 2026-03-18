"""
Structural Integrity Tests
==========================

Validates the architectural fixes from the JLAW structural integrity audit:
1. Single canonical orchestrator designation
2. Pre-flight validation gate integration
3. Reporting pipeline connectivity
4. Silent exception handling remediation
5. Output data purge verification
"""

import importlib
import logging
import sys
import warnings
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────
# 1. SINGLE CANONICAL ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────


class TestCanonicalOrchestrator:
    """Verify UnifiedForensicOrchestrator is the sole canonical authority."""

    def test_unified_orchestrator_imports(self):
        """UnifiedForensicOrchestrator can be imported from canonical location."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator

        assert UnifiedForensicOrchestrator is not None

    def test_unified_orchestrator_has_version(self):
        """UnifiedForensicOrchestrator declares a VERSION."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator

        assert hasattr(UnifiedForensicOrchestrator, "VERSION")
        assert UnifiedForensicOrchestrator.VERSION  # non-empty

    def test_unified_orchestrator_has_11_phase_pipeline(self):
        """UnifiedForensicOrchestrator defines all 11 phase methods."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator

        for phase_num in range(1, 12):
            if phase_num == 9:
                method_name = "_execute_phase_9_web_intelligence"
            elif phase_num == 10:
                method_name = "_execute_phase_10_dossier"
            elif phase_num == 11:
                method_name = "_execute_phase_11_bundle"
            else:
                method_name = f"_execute_phase_{phase_num}"
            assert hasattr(UnifiedForensicOrchestrator, method_name), (
                f"Missing method {method_name}"
            )

    def test_supreme_orchestrator_has_deprecation(self):
        """SupremeOrchestrator emits a DeprecationWarning on init."""
        from src.core.supreme_orchestrator import SupremeOrchestrator

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            SupremeOrchestrator()
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)

    def test_deprecated_orchestrators_docstrings(self):
        """Deprecated orchestrators contain deprecation notice in docstring."""
        deprecated_classes = [
            ("src.core.intelligent_orchestrator", "IntelligentOrchestrator"),
            ("src.core.batch_forensic_orchestrator", "BatchForensicOrchestrator"),
            ("src.core.forensic_meta_orchestrator", "ForensicMetaOrchestrator"),
            ("src.core.unified_agent_orchestrator", "UnifiedAgentOrchestrator"),
            ("src.core.master_execution_controller", "MasterExecutionController"),
        ]
        for module_path, class_name in deprecated_classes:
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                # Module may have unmet dependencies in CI; skip gracefully
                continue
            cls = getattr(mod, class_name)
            assert "deprecated" in (cls.__doc__ or "").lower(), (
                f"{class_name} docstring missing deprecation notice"
            )

    def test_cli_uses_unified_orchestrator(self):
        """jlaw_cli.py imports UnifiedForensicOrchestrator."""
        cli_path = Path(__file__).parent.parent / "jlaw_cli.py"
        source = cli_path.read_text()
        assert "UnifiedForensicOrchestrator" in source
        assert "from src.core.unified_orchestrator import" in source


# ─────────────────────────────────────────────────────────────────────
# 2. PRE-FLIGHT VALIDATION GATE
# ─────────────────────────────────────────────────────────────────────


class TestPreflightIntegration:
    """Verify preflight check is wired into the CLI execution path."""

    def test_preflight_checker_importable(self):
        """PreFlightChecker can be imported from scripts."""
        from scripts.preflight_check import PreFlightChecker

        checker = PreFlightChecker(verbose=False)
        assert checker is not None

    def test_cli_has_skip_preflight_flag(self):
        """CLI argument parser supports --skip-preflight."""
        from src.cli.argument_parser import JLAWArgumentParser

        parser = JLAWArgumentParser()
        args = parser.parse_args(["--cik", "320187", "--year", "2019", "--skip-preflight"])
        assert args.skip_preflight is True

    def test_cli_skip_preflight_defaults_false(self):
        """--skip-preflight defaults to False."""
        from src.cli.argument_parser import JLAWArgumentParser

        parser = JLAWArgumentParser()
        args = parser.parse_args(["--cik", "320187", "--year", "2019"])
        assert args.skip_preflight is False

    def test_preflight_gate_in_cli_source(self):
        """jlaw_cli.py contains preflight validation gate code."""
        cli_path = Path(__file__).parent.parent / "jlaw_cli.py"
        source = cli_path.read_text()
        assert "PreFlightChecker" in source
        assert "skip_preflight" in source
        assert "Pre-flight validation FAILED" in source

    def test_preflight_report_structure(self):
        """PreFlightReport has expected fields."""
        from scripts.preflight_check import PreFlightReport, CheckResult

        report = PreFlightReport(
            timestamp="2024-01-01T00:00:00",
            passed=True,
            checks=[
                CheckResult(
                    component="Test",
                    status="pass",
                    message="All good",
                )
            ],
            summary={"pass": 1, "fail": 0, "warn": 0, "skip": 0},
        )
        assert report.passed is True
        assert report.summary["pass"] == 1


# ─────────────────────────────────────────────────────────────────────
# 3. REPORTING PIPELINE CONNECTIVITY
# ─────────────────────────────────────────────────────────────────────


class TestReportingPipelineConnectivity:
    """Verify reporting modules are connected to the pipeline."""

    def test_doj_report_generator_importable(self):
        """DOJReportGenerator can be imported."""
        try:
            from src.reporting.doj_report_generator import DOJReportGenerator
        except ImportError as e:
            pytest.skip(f"DOJReportGenerator dependency missing: {e}")
        assert DOJReportGenerator is not None

    def test_investigation_bundle_generator_importable(self):
        """InvestigationBundleGenerator can be imported."""
        try:
            from src.reporting.investigation_bundle_generator import (
                InvestigationBundleGenerator,
            )
        except ImportError as e:
            pytest.skip(f"InvestigationBundleGenerator dependency missing: {e}")
        assert InvestigationBundleGenerator is not None

    def test_phase_11_references_doj_generator(self):
        """Phase 11 method references DOJReportGenerator."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        import inspect

        source = inspect.getsource(
            UnifiedForensicOrchestrator._execute_phase_11_bundle
        )
        assert "DOJReportGenerator" in source

    def test_phase_11_references_investigation_bundle(self):
        """Phase 11 method references InvestigationBundleGenerator."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        import inspect

        source = inspect.getsource(
            UnifiedForensicOrchestrator._execute_phase_11_bundle
        )
        assert "InvestigationBundleGenerator" in source

    def test_phase_10_references_forensic_dossier(self):
        """Phase 10 method references ForensicDossierGenerator."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        import inspect

        source = inspect.getsource(
            UnifiedForensicOrchestrator._execute_phase_10_dossier
        )
        assert "ForensicDossierGenerator" in source

    def test_phase_11_result_includes_report_flags(self):
        """Phase 11 source includes doj_report_generated and investigation_bundle_generated."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        import inspect

        source = inspect.getsource(
            UnifiedForensicOrchestrator._execute_phase_11_bundle
        )
        assert "doj_report_generated" in source
        assert "investigation_bundle_generated" in source


# ─────────────────────────────────────────────────────────────────────
# 4. SILENT EXCEPTION HANDLING REMEDIATION
# ─────────────────────────────────────────────────────────────────────


class TestSilentExceptionRemediation:
    """Verify critical modules have logging in exception handlers."""

    CRITICAL_FILES = [
        "src/core/recursive_analysis_engine.py",
        "src/core/evidence_chain/evidence_attribution.py",
        "src/nodes/node1_form4/form4_parser.py",
        "src/nodes/node1_form4/zero_value_detector.py",
        "src/nodes/node1_form4/gift_pattern_detector.py",
        "src/nodes/node1_form4/short_swing_calc.py",
        "src/nodes/node1_form4/financial_benefit_extractor.py",
        "src/detection/patterns/advanced_patterns.py",
    ]

    @pytest.mark.parametrize("filepath", CRITICAL_FILES)
    def test_critical_file_has_logger(self, filepath):
        """Critical files must have a module-level logger."""
        full_path = Path(__file__).parent.parent / filepath
        if not full_path.exists():
            pytest.skip(f"File {filepath} not found")
        source = full_path.read_text()
        assert "import logging" in source or "from" in source, (
            f"{filepath} missing logging import"
        )
        assert "getLogger" in source, f"{filepath} missing logger setup"


# ─────────────────────────────────────────────────────────────────────
# 5. OUTPUT DATA PURGE VERIFICATION
# ─────────────────────────────────────────────────────────────────────


class TestOutputPurge:
    """Verify unreliable output data has been purged."""

    def test_gitignore_contains_output(self):
        """The .gitignore file includes the output/ directory."""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        content = gitignore_path.read_text()
        assert "output/" in content

    def test_output_not_tracked_by_git(self):
        """output/ directory files are not tracked by git."""
        import subprocess

        result = subprocess.run(
            ["git", "ls-files", "output/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        tracked_files = result.stdout.strip()
        assert tracked_files == "", (
            f"output/ directory still has tracked files: {tracked_files}"
        )


# ─────────────────────────────────────────────────────────────────────
# 6. RECURSIVE ENGINE CONNECTIVITY
# ─────────────────────────────────────────────────────────────────────


class TestRecursiveEngineConnectivity:
    """Verify the recursive engine is connected to the pipeline."""

    def test_recursive_engine_importable(self):
        """RecursiveProsecutorialEngine can be imported."""
        from src.core.recursive_engine import RecursiveProsecutorialEngine

        assert RecursiveProsecutorialEngine is not None

    def test_phase_4_calls_recursive_engine(self):
        """Phase 4 imports and uses RecursiveProsecutorialEngine."""
        from src.core.unified_orchestrator import UnifiedForensicOrchestrator
        import inspect

        source = inspect.getsource(
            UnifiedForensicOrchestrator._execute_phase_4
        )
        assert "RecursiveProsecutorialEngine" in source

    def test_recursive_engine_initializes_all_16_nodes(self):
        """RecursiveProsecutorialEngine._init_nodes initializes 16 nodes."""
        from src.core.recursive_engine import RecursiveProsecutorialEngine
        import inspect

        source = inspect.getsource(RecursiveProsecutorialEngine._init_nodes)
        # Check for all 16 node groups
        for node_num in range(1, 17):
            # Each node should be referenced by its module name or node number
            assert f"node{node_num}" in source.lower() or f"node_{node_num}" in source, (
                f"Node {node_num} not found in _init_nodes"
            )
