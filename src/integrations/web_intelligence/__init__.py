"""
Web Intelligence Module - OSINT scraping and extraction for forensic analysis.
"""
from .scraper import WebIntelligenceEngine
from .models import (
    PublicStatement, StatementSource, WebIntelligenceResult,
    ContradictionMap, ContradictionEntry,
)

__all__ = [
    "WebIntelligenceEngine",
    "PublicStatement",
    "StatementSource",
    "WebIntelligenceResult",
    "ContradictionMap",
    "ContradictionEntry",
]
