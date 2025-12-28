"""
Prosecutorial Narrative Generation Module
==========================================

Generates legally precise narratives from forensic analysis outputs.

Modules:
    - generator: ProsecutorialNarrativeGenerator class
    - citation_matrix: Regulatory citation database
"""

from .generator import ProsecutorialNarrativeGenerator
from .citation_matrix import (
    Citation,
    SECURITIES_CITATIONS,
    TAX_CITATIONS,
    ANTITRUST_CITATIONS,
    EVIDENCE_CITATIONS,
    get_citations_for_anomaly,
    get_citations_for_risk_tier,
    format_citation,
    compile_regulatory_citations,
    get_all_citations,
)

__all__ = [
    # Generator
    'ProsecutorialNarrativeGenerator',
    # Citations
    'Citation',
    'SECURITIES_CITATIONS',
    'TAX_CITATIONS',
    'ANTITRUST_CITATIONS',
    'EVIDENCE_CITATIONS',
    'get_citations_for_anomaly',
    'get_citations_for_risk_tier',
    'format_citation',
    'compile_regulatory_citations',
    'get_all_citations',
]
