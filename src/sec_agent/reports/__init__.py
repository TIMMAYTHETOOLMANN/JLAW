"""
SEC-AGENT Report Generators
=============================

Report generation modules wired to JLAW production-grade generators.

Modules:
    doj_referral        — DOJ criminal referral (→ JLAW DOJReportGenerator)
    master_report       — Master archival dossier (→ JLAW ProsecutorialDossierGenerator + ForensicDossierGenerator)
    sec_bundle          — SEC enforcement bundle (→ JLAW EvidencePackager + StatutoryCitationEngine)
    legislative_brief   — Congressional briefing (→ JLAW ExecutiveBriefingFormatter)
"""

from src.sec_agent.reports.doj_referral import DOJReferralGenerator
from src.sec_agent.reports.master_report import MasterReportGenerator
from src.sec_agent.reports.sec_bundle import SECBundleGenerator
from src.sec_agent.reports.legislative_brief import LegislativeBriefGenerator

__all__ = [
    "DOJReferralGenerator",
    "MasterReportGenerator",
    "SECBundleGenerator",
    "LegislativeBriefGenerator",
]
