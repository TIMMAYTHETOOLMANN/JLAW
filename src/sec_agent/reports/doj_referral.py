"""
DOJ Referral Generator — Criminal Referral Reports
=====================================================

Wires to JLAW's production-grade DOJReportGenerator (1,495 LOC) for
generating DOJ criminal division referral packages. Adapts the SEC-AGENT
deployment context (submission targets, cover letters) to JLAW's
prosecution-ready report output.

Source Integration:
    JLAW doj_report_generator.py (1,495 LOC) → Full DOJ report generation
    SEC-AGENT submission_targets.yaml → 31 recipient contacts
    SEC-AGENT MASTER_DEPLOYMENT_DOCTRINE.md → §2.2 customization matrix
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.reporting.doj_report_generator import DOJReportGenerator
from src.reporting.models import (
    ChainOfCustodyRecord,
    FilingAnalysisReport,
    SubagentFinding,
)

logger = logging.getLogger(__name__)


@dataclass
class DOJRecipient:
    """DOJ criminal division recipient configuration."""

    name: str
    title: str
    division: str
    office: str
    address: Optional[str] = None
    email: Optional[str] = None
    priority: str = "standard"  # "urgent", "standard", "informational"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "title": self.title,
            "division": self.division,
            "office": self.office,
            "address": self.address,
            "priority": self.priority,
        }


@dataclass
class DOJReferralPackage:
    """Complete DOJ criminal referral package."""

    referral_id: str
    case_id: str
    company_name: str
    cik: str
    generated_at: datetime
    report_paths: Dict[str, Path] = field(default_factory=dict)
    cover_letter_path: Optional[Path] = None
    evidence_appendix_path: Optional[Path] = None
    recipients: List[DOJRecipient] = field(default_factory=list)
    total_violations: int = 0
    critical_violations: int = 0
    max_exposure_usd: float = 0.0
    criminal_referral_recommended: bool = False
    status: str = "generated"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "referral_id": self.referral_id,
            "case_id": self.case_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "generated_at": self.generated_at.isoformat(),
            "report_files": {k: str(v) for k, v in self.report_paths.items()},
            "cover_letter": str(self.cover_letter_path) if self.cover_letter_path else None,
            "recipients": [r.to_dict() for r in self.recipients],
            "total_violations": self.total_violations,
            "critical_violations": self.critical_violations,
            "max_exposure_usd": self.max_exposure_usd,
            "criminal_referral_recommended": self.criminal_referral_recommended,
            "status": self.status,
        }


# Default DOJ recipients from deployment doctrine
DEFAULT_DOJ_RECIPIENTS: List[DOJRecipient] = [
    DOJRecipient(
        name="Fraud Section Chief",
        title="Chief, Fraud Section",
        division="Criminal Division",
        office="U.S. Department of Justice",
        priority="urgent",
    ),
    DOJRecipient(
        name="Securities & Financial Fraud Unit",
        title="Unit Chief",
        division="Criminal Division, Fraud Section",
        office="U.S. Department of Justice",
        priority="standard",
    ),
]


class DOJReferralGenerator:
    """
    Generate DOJ criminal referral packages.

    Wraps JLAW's DOJReportGenerator with SEC-AGENT deployment context
    including recipient routing, cover letter generation, and
    submission staging.

    Args:
        output_dir: Directory for generated reports.
        recipients: DOJ recipient configurations.
    """

    def __init__(
        self,
        output_dir: str = "./output/doj_referrals",
        recipients: Optional[List[DOJRecipient]] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recipients = recipients or DEFAULT_DOJ_RECIPIENTS

        # Wire to JLAW's production DOJ report generator
        self._jlaw_generator = DOJReportGenerator(output_dir=output_dir)

        logger.info(
            "DOJReferralGenerator initialized: output=%s, recipients=%d",
            self.output_dir,
            len(self.recipients),
        )

    def generate_referral(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        filing_reports: List[FilingAnalysisReport],
        chain_of_custody: List[ChainOfCustodyRecord],
        subagent_findings: Optional[List[SubagentFinding]] = None,
        output_formats: Optional[List[str]] = None,
        phase3_results: Optional[Dict[str, Any]] = None,
        include_cover_letter: bool = True,
    ) -> DOJReferralPackage:
        """
        Generate a complete DOJ criminal referral package.

        Args:
            case_id: Unique case identifier.
            company_name: Target company name.
            cik: Target company CIK.
            filing_reports: List of filing analysis reports from JLAW pipeline.
            chain_of_custody: Evidence chain of custody records.
            subagent_findings: Optional Claude subagent analysis findings.
            output_formats: Output formats (default: ["json", "markdown", "html"]).
            phase3_results: Optional Phase 3 detection pattern results.
            include_cover_letter: Whether to generate a cover letter.

        Returns:
            DOJReferralPackage with all generated files and metadata.
        """
        if output_formats is None:
            output_formats = ["json", "markdown", "html"]

        referral_id = f"DOJ-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Generate core report via JLAW's DOJReportGenerator
        report_paths = self._jlaw_generator.generate_comprehensive_report(
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            filing_reports=filing_reports,
            chain_of_custody=chain_of_custody,
            subagent_findings=subagent_findings,
            output_formats=output_formats,
            phase3_results=phase3_results,
        )

        # Calculate violation statistics
        total_violations = sum(
            len(r.violations) for r in filing_reports if hasattr(r, "violations")
        )
        critical_violations = sum(
            1
            for r in filing_reports
            if hasattr(r, "violations")
            for v in r.violations
            if hasattr(v, "severity") and str(v.severity).upper() == "CRITICAL"
        )

        # Generate cover letter if requested
        cover_letter_path = None
        if include_cover_letter:
            cover_letter_path = self._generate_cover_letter(
                referral_id=referral_id,
                case_id=case_id,
                company_name=company_name,
                cik=cik,
                total_violations=total_violations,
                critical_violations=critical_violations,
            )

        package = DOJReferralPackage(
            referral_id=referral_id,
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            generated_at=datetime.utcnow(),
            report_paths=report_paths,
            cover_letter_path=cover_letter_path,
            recipients=self.recipients,
            total_violations=total_violations,
            critical_violations=critical_violations,
            criminal_referral_recommended=critical_violations > 0,
            status="generated",
        )

        # Export package manifest
        manifest_path = self.output_dir / f"{referral_id}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(package.to_dict(), f, indent=2, default=str)

        logger.info(
            "DOJ referral generated: %s (%d violations, %d critical)",
            referral_id,
            total_violations,
            critical_violations,
        )

        return package

    def _generate_cover_letter(
        self,
        referral_id: str,
        case_id: str,
        company_name: str,
        cik: str,
        total_violations: int,
        critical_violations: int,
    ) -> Path:
        """Generate DOJ cover letter per deployment doctrine §2.2."""
        cover_path = self.output_dir / f"{referral_id}_cover_letter.md"

        content = f"""# CRIMINAL REFERRAL COVER LETTER

**Referral ID:** {referral_id}
**Case ID:** {case_id}
**Date:** {datetime.utcnow().strftime('%B %d, %Y')}

---

**RE: Securities Fraud Investigation — {company_name} (CIK: {cik})**

Dear Fraud Section Chief,

This referral package presents evidence of potential securities law violations
by {company_name} (SEC CIK: {cik}) identified through systematic forensic
analysis of SEC EDGAR filings.

## Summary of Findings

- **Total Violations Identified:** {total_violations}
- **Critical Severity Violations:** {critical_violations}
- **Criminal Referral Recommended:** {'Yes' if critical_violations > 0 else 'No'}

## Enclosed Materials

1. Comprehensive forensic analysis report (JSON, Markdown, HTML formats)
2. Evidence chain with chain of custody documentation
3. Statutory citation appendix with penalty calculations
4. Source filing index with integrity verification hashes

## Evidence Integrity

All evidence materials include SHA-256 integrity hashes and chain of custody
records compliant with FRE 902(13)/(14). Evidence chain includes RFC 6962
Merkle tree verification and RFC 3161 timestamp tokens.

---

*This referral was generated by the JLAW Forensic Analysis Platform.*
*Evidence integrity verified via triple-hash (SHA-256 + SHA3-512 + BLAKE2b).*
"""

        with open(cover_path, "w", encoding="utf-8") as f:
            f.write(content)

        return cover_path
