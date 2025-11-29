"""
JLAW Phase 8: Master Orchestrator
=================================

Unified workflow engine for complete investigation management.

Components:
- InvestigationOrchestrator: Master workflow coordinator
- WorkflowEngine: Job queue and task management
- CaseManager: Multi-case management system
- ProgressTracker: Real-time progress monitoring
- ResultAggregator: Cross-phase data correlation
- APIServer: RESTful API endpoints
"""

from .orchestrator import InvestigationOrchestrator
from .workflow_engine import WorkflowEngine
from .case_manager import CaseManager
from .progress_tracker import ProgressTracker
from .result_aggregator import ResultAggregator

__all__ = [
    'InvestigationOrchestrator',
    'WorkflowEngine',
    'CaseManager',
    'ProgressTracker',
    'ResultAggregator',
]

__version__ = '8.0.0'
__phase__ = 8

