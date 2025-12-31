"""
Output Formatters for Phase 4 Enhanced Reporting
=================================================

This package provides specialized formatters for different sections of the
prosecutorial dossier output.

Modules:
- format_constants.py: Reusable formatting constants and helper functions
- cover_sheet.py: Confidential cover sheet with case metadata (enhanced)
- executive_briefing.py: Visual threat assessment with progress bars (enhanced)
- insider_dossier_formatter.py: Individual reporting person dossiers (NEW)
- actor_dossier.py: Individual actor profiles with activity summaries
- violation_category.py: Deduplicated, aggregated violation findings (enhanced)
- evidence_chain_formatter.py: Cryptographic attestation and FRE compliance (NEW)
- appendix_generator.py: Appendices A-D generation (enhanced)
"""

from .cover_sheet import CoverSheetFormatter
from .executive_briefing import ExecutiveBriefingFormatter
from .actor_dossier import ActorDossierFormatter
from .insider_dossier_formatter import InsiderDossierFormatter
from .violation_category import ViolationCategoryFormatter
from .evidence_chain_formatter import EvidenceChainFormatter
from .appendix_generator import AppendixGenerator

__all__ = [
    "CoverSheetFormatter",
    "ExecutiveBriefingFormatter",
    "ActorDossierFormatter",
    "InsiderDossierFormatter",
    "ViolationCategoryFormatter",
    "EvidenceChainFormatter",
    "AppendixGenerator",
]
