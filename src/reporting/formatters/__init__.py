"""
Output Formatters for Phase 4 Enhanced Reporting
=================================================

This package provides specialized formatters for different sections of the
prosecutorial dossier output.

Modules:
- cover_sheet.py: Confidential cover sheet with case metadata
- executive_briefing.py: Visual threat assessment with progress bars
- actor_dossier.py: Individual actor profiles with activity summaries
- violation_category.py: Deduplicated, aggregated violation findings
- appendix_generator.py: Appendices A-D generation
"""

from .cover_sheet import CoverSheetFormatter
from .executive_briefing import ExecutiveBriefingFormatter
from .actor_dossier import ActorDossierFormatter
from .violation_category import ViolationCategoryFormatter
from .appendix_generator import AppendixGenerator

__all__ = [
    "CoverSheetFormatter",
    "ExecutiveBriefingFormatter",
    "ActorDossierFormatter",
    "ViolationCategoryFormatter",
    "AppendixGenerator",
]
