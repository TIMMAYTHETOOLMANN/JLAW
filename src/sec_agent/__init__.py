"""
JLAW × SEC-AGENT Unified Integration Layer
============================================

Bridge module connecting the SEC-AGENT deployment platform (9,462 LOC + 469MB
EDGAR corpus) with the JLAW prosecutorial engine (122,255 LOC, 16-node
recursive pipeline, 23 detection patterns).

Architecture:
    SEC-AGENT raw corpus (2,254+ filings, 469MB)
        → filing_classifier.py   (classify UUID-named PDFs/XLS)
        → cik_validator.py       (validate/resolve CIK identifiers)
        → claude_compositor.py   (orchestrate Claude forensic agents)
        → JLAW 16-Node Pipeline  (full forensic analysis)
        → reports/               (DOJ, SEC, Congressional, Master output)
        → pipeline.py            (unified data flow orchestration)

Modules:
    filing_classifier   — SEC filing type classification from raw EDGAR corpus
    cik_validator       — CIK validation and resolution via EDGAR API
    claude_compositor   — Claude agent composition and orchestration bridge
    pipeline            — Unified SEC-AGENT → JLAW data flow controller

Sub-packages:
    reports/            — Report generators wired to JLAW production modules
    ingestion/          — EDGAR corpus scanning and XBRL indexing
"""

from src.sec_agent.filing_classifier import FilingClassifier, FilingClassification
from src.sec_agent.cik_validator import CIKValidator, CIKValidationResult
from src.sec_agent.claude_compositor import ClaudeCompositor, CompositorResult
from src.sec_agent.pipeline import SecAgentPipeline, PipelineResult

__all__ = [
    # Core modules
    "FilingClassifier",
    "FilingClassification",
    "CIKValidator",
    "CIKValidationResult",
    "ClaudeCompositor",
    "CompositorResult",
    # Pipeline
    "SecAgentPipeline",
    "PipelineResult",
]
