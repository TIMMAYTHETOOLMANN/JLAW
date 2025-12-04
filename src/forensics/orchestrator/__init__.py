"""
Phase 8: Master Forensic Controller
Ultimate integration orchestrator for all 7 phases.
"""

from .master_controller import (
    MasterForensicController,
    InvestigationConfig,
    InvestigationResult,
    FullSpectrumAnalysis
)

from .config_manager import (
    SystemConfiguration,
    PhaseConfig,
    OutputConfig
)

from .integration_test import (
    IntegrationTestSuite,
    TestResult,
    SystemHealth
)

__all__ = [
    'MasterForensicController',
    'InvestigationConfig',
    'InvestigationResult',
    'FullSpectrumAnalysis',
    'SystemConfiguration',
    'PhaseConfig',
    'OutputConfig',
    'IntegrationTestSuite',
    'TestResult',
    'SystemHealth'
]

