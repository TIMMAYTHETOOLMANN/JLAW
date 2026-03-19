"""
SEC-AGENT Ingestion Pipeline
==============================

Modules for scanning, classifying, and indexing the raw SEC EDGAR
filing corpus into the JLAW analysis pipeline.

Modules:
    corpus_scanner  — Scan raw EDGAR file trees (PDF/XLS/JSON)
    xbrl_indexer    — Index CIK XBRL Company Facts JSON
"""

from src.sec_agent.ingestion.corpus_scanner import CorpusScanner, CorpusManifest
from src.sec_agent.ingestion.xbrl_indexer import XBRLIndexer, XBRLIndex

__all__ = [
    "CorpusScanner",
    "CorpusManifest",
    "XBRLIndexer",
    "XBRLIndex",
]
