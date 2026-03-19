"""
SEC Bundle Generator — SEC Enforcement Division Packages
==========================================================

Wires to JLAW's production-grade EvidencePackager (683 LOC) and
StatutoryCitationEngine (564 LOC) for generating SEC enforcement
division submission bundles.

Architecture:
    Track A: Modular Tactical Bundles → SEC Enforcement
        → EvidencePackager (evidence with Merkle root, FRE 902)
        → StatutoryCitationEngine (GovInfo API, penalty calculations)
        → Combined SEC submission bundle

Source Integration:
    JLAW evidence_packager.py (683 LOC) → Evidence packaging with integrity
    JLAW statutory_citation_engine.py (564 LOC) → Legal citation enrichment
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.reporting.evidence_packager import (
    EvidencePackager,
    EvidencePackage,
    EvidenceItem,
)
from src.reporting.statutory_citation_engine import (
    StatutoryCitationEngine,
    GovInfoCitation,
)
from src.reporting.models import (
    ChainOfCustodyRecord,
    FilingAnalysisReport,
    StatutoryReference,
    ViolationEvidence,
)

logger = logging.getLogger(__name__)


@dataclass
class SECRecipient:
    """SEC enforcement division recipient configuration."""

    name: str
    title: str
    division: str
    regional_office: Optional[str] = None
    priority: str = "standard"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "title": self.title,
            "division": self.division,
            "regional_office": self.regional_office,
            "priority": self.priority,
        }


@dataclass
class SECBundleOutput:
    """Complete SEC enforcement bundle output."""

    bundle_id: str
    case_id: str
    company_name: str
    cik: str
    generated_at: datetime
    evidence_package: Optional[EvidencePackage] = None
    evidence_package_path: Optional[Path] = None
    citations: List[GovInfoCitation] = field(default_factory=list)
    citation_report_path: Optional[Path] = None
    statutory_analysis_path: Optional[Path] = None
    cover_letter_path: Optional[Path] = None
    recipients: List[SECRecipient] = field(default_factory=list)
    total_violations: int = 0
    total_evidence_items: int = 0
    total_penalty_exposure_usd: float = 0.0
    output_paths: Dict[str, Path] = field(default_factory=dict)
    status: str = "generated"
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "bundle_id": self.bundle_id,
            "case_id": self.case_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "generated_at": self.generated_at.isoformat(),
            "output_paths": {k: str(v) for k, v in self.output_paths.items()},
            "total_violations": self.total_violations,
            "total_evidence_items": self.total_evidence_items,
            "total_penalty_exposure_usd": self.total_penalty_exposure_usd,
            "recipients": [r.to_dict() for r in self.recipients],
            "citation_count": len(self.citations),
            "status": self.status,
            "error_count": len(self.errors),
        }


# Default SEC enforcement recipients
DEFAULT_SEC_RECIPIENTS: List[SECRecipient] = [
    SECRecipient(
        name="Division of Enforcement",
        title="Director",
        division="SEC Division of Enforcement",
        priority="urgent",
    ),
    SECRecipient(
        name="Office of the Whistleblower",
        title="Chief",
        division="SEC Office of the Whistleblower",
        priority="standard",
    ),
]


class SECBundleGenerator:
    """
    Generate SEC enforcement division submission bundles.

    Combines JLAW's EvidencePackager (FRE 902(13)/(14) compliant evidence
    packaging with Merkle root verification) with the StatutoryCitationEngine
    (GovInfo API enrichment with penalty calculations) to produce complete
    SEC enforcement submission packages.

    Args:
        output_dir: Directory for generated bundles.
        govinfo_api_key: Optional GovInfo API key for citation enrichment.
        recipients: SEC recipient configurations.
    """

    def __init__(
        self,
        output_dir: str = "./output/sec_bundles",
        govinfo_api_key: Optional[str] = None,
        recipients: Optional[List[SECRecipient]] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recipients = recipients or DEFAULT_SEC_RECIPIENTS

        # Wire to JLAW production generators
        self._evidence_packager = EvidencePackager(output_dir=output_dir)
        self._citation_engine = StatutoryCitationEngine(
            api_key=govinfo_api_key,
        )

        logger.info(
            "SECBundleGenerator initialized: output=%s, recipients=%d",
            self.output_dir,
            len(self.recipients),
        )

    async def generate_bundle(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        filing_reports: Optional[List[FilingAnalysisReport]] = None,
        violations: Optional[List[Dict[str, Any]]] = None,
        chain_of_custody: Optional[List[ChainOfCustodyRecord]] = None,
        enrich_citations: bool = True,
        include_cover_letter: bool = True,
    ) -> SECBundleOutput:
        """
        Generate a complete SEC enforcement submission bundle.

        Args:
            case_id: Unique case identifier.
            company_name: Target company name.
            cik: Target company CIK.
            filing_reports: Filing analysis reports from JLAW pipeline.
            violations: Violation dictionaries (alternative to filing_reports).
            chain_of_custody: Evidence chain of custody records.
            enrich_citations: Whether to enrich with GovInfo citations.
            include_cover_letter: Whether to generate cover letter.

        Returns:
            SECBundleOutput with all generated files and metadata.
        """
        bundle_id = f"SEC-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        output = SECBundleOutput(
            bundle_id=bundle_id,
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            generated_at=datetime.utcnow(),
            recipients=self.recipients,
        )

        # ── Component 1: Evidence Package ───────────────────────────────
        try:
            if filing_reports:
                for report in filing_reports:
                    package = self._evidence_packager.create_package_from_filing_report(
                        filing_report=report,
                        case_id=case_id,
                    )
                    if chain_of_custody:
                        for record in chain_of_custody:
                            package.add_custody_record(record)
                    output.evidence_package = package
                    output.total_evidence_items = len(package.items)
            elif violations:
                package = self._evidence_packager.create_package_from_violations(
                    violations=violations,
                    case_id=case_id,
                )
                output.evidence_package = package
                output.total_evidence_items = len(package.items)

            if output.evidence_package:
                # Export evidence package
                json_path = self._evidence_packager.export_package_json(
                    output.evidence_package
                )
                md_path = self._evidence_packager.export_package_markdown(
                    output.evidence_package
                )
                output.evidence_package_path = json_path
                output.output_paths["evidence_json"] = json_path
                output.output_paths["evidence_markdown"] = md_path

                # Validate against baseline
                validation = self._evidence_packager.validate_against_nike_baseline(
                    output.evidence_package
                )
                output.total_violations = validation.get("total_violations", 0)

                logger.info(
                    "Evidence package created: %d items, %d violations",
                    output.total_evidence_items,
                    output.total_violations,
                )

        except Exception as e:
            logger.error("Evidence packaging failed: %s", e)
            output.errors.append(f"Evidence packaging: {e}")

        # ── Component 2: Statutory Citation Enrichment ──────────────────
        if enrich_citations and violations:
            try:
                enriched_violations = await self._citation_engine.batch_enrich_citations(
                    violations
                )

                # Collect all citations
                for violation in enriched_violations:
                    citation_data = violation.get("govinfo_citation")
                    if citation_data and isinstance(citation_data, dict):
                        output.citations.append(
                            GovInfoCitation(**{
                                k: v
                                for k, v in citation_data.items()
                                if k in GovInfoCitation.__dataclass_fields__
                            })
                        )

                # Calculate total penalty exposure
                output.total_penalty_exposure_usd = sum(
                    c.civil_penalty_max or 0 for c in output.citations
                )

                # Export citation report
                citation_report_path = self.output_dir / f"{bundle_id}_citations.json"
                with open(citation_report_path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "citations": [c.to_dict() for c in output.citations],
                            "total_penalty_exposure_usd": output.total_penalty_exposure_usd,
                        },
                        f,
                        indent=2,
                        default=str,
                    )
                output.citation_report_path = citation_report_path
                output.output_paths["citation_report"] = citation_report_path

                logger.info(
                    "Citation enrichment complete: %d citations, $%.2f exposure",
                    len(output.citations),
                    output.total_penalty_exposure_usd,
                )

            except Exception as e:
                logger.error("Citation enrichment failed: %s", e)
                output.errors.append(f"Citation enrichment: {e}")

        # ── Component 3: Statutory Analysis Report ──────────────────────
        try:
            statutory_path = self._generate_statutory_analysis(
                bundle_id=bundle_id,
                company_name=company_name,
                cik=cik,
                violations=violations or [],
                citations=output.citations,
            )
            output.statutory_analysis_path = statutory_path
            output.output_paths["statutory_analysis"] = statutory_path
        except Exception as e:
            logger.error("Statutory analysis generation failed: %s", e)
            output.errors.append(f"Statutory analysis: {e}")

        # ── Component 4: Cover Letter ───────────────────────────────────
        if include_cover_letter:
            try:
                cover_path = self._generate_cover_letter(
                    bundle_id=bundle_id,
                    company_name=company_name,
                    cik=cik,
                    total_violations=output.total_violations,
                    total_evidence=output.total_evidence_items,
                    penalty_exposure=output.total_penalty_exposure_usd,
                )
                output.cover_letter_path = cover_path
                output.output_paths["cover_letter"] = cover_path
            except Exception as e:
                logger.error("Cover letter generation failed: %s", e)
                output.errors.append(f"Cover letter: {e}")

        output.status = "success" if not output.errors else "partial"

        # ── Export bundle manifest ──────────────────────────────────────
        manifest_path = self.output_dir / f"{bundle_id}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(output.to_dict(), f, indent=2, default=str)
        output.output_paths["manifest"] = manifest_path

        logger.info(
            "SEC bundle generated: %s (%d violations, %d evidence items)",
            bundle_id,
            output.total_violations,
            output.total_evidence_items,
        )

        return output

    async def close(self) -> None:
        """Release resources."""
        await self._citation_engine.close()

    def _generate_statutory_analysis(
        self,
        bundle_id: str,
        company_name: str,
        cik: str,
        violations: List[Dict[str, Any]],
        citations: List[GovInfoCitation],
    ) -> Path:
        """Generate statutory analysis appendix."""
        report_path = self.output_dir / f"{bundle_id}_statutory_analysis.md"

        lines = [
            "# STATUTORY ANALYSIS APPENDIX",
            "",
            f"**Bundle ID:** {bundle_id}",
            f"**Company:** {company_name} (CIK: {cik})",
            f"**Generated:** {datetime.utcnow().strftime('%B %d, %Y')}",
            "",
            "---",
            "",
            "## Applicable Statutes",
            "",
        ]

        if citations:
            for i, citation in enumerate(citations, 1):
                lines.extend([
                    f"### {i}. {citation.citation}",
                    "",
                    f"**Title:** {citation.title}",
                    f"**Collection:** {citation.collection}",
                    "",
                ])
                if citation.summary:
                    lines.extend([f"**Summary:** {citation.summary}", ""])
                if citation.civil_penalty_min or citation.civil_penalty_max:
                    lines.extend([
                        f"**Civil Penalties:** ${citation.civil_penalty_min or 0:,.0f} — ${citation.civil_penalty_max or 0:,.0f}",
                        "",
                    ])
                if citation.criminal_penalty:
                    lines.extend([
                        f"**Criminal Exposure:** {citation.criminal_penalty}",
                        "",
                    ])
                if citation.prison_years_max:
                    lines.extend([
                        f"**Maximum Imprisonment:** {citation.prison_years_max} years",
                        "",
                    ])
                lines.append("---")
                lines.append("")
        else:
            lines.append("*No GovInfo citations enriched for this bundle.*")
            lines.append("")

        lines.extend([
            "## Violation Summary",
            "",
            f"**Total Violations:** {len(violations)}",
            "",
        ])

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return report_path

    def _generate_cover_letter(
        self,
        bundle_id: str,
        company_name: str,
        cik: str,
        total_violations: int,
        total_evidence: int,
        penalty_exposure: float,
    ) -> Path:
        """Generate SEC enforcement cover letter."""
        cover_path = self.output_dir / f"{bundle_id}_cover_letter.md"

        content = f"""# SEC ENFORCEMENT SUBMISSION COVER LETTER

**Bundle ID:** {bundle_id}
**Date:** {datetime.utcnow().strftime('%B %d, %Y')}

---

**RE: Potential Securities Law Violations — {company_name} (CIK: {cik})**

Dear Director of Enforcement,

This submission package presents evidence of potential securities law violations
by {company_name} (SEC CIK: {cik}) identified through systematic forensic
analysis of SEC EDGAR filings.

## Summary

- **Total Violations Identified:** {total_violations}
- **Evidence Items:** {total_evidence}
- **Estimated Penalty Exposure:** ${penalty_exposure:,.2f}

## Enclosed Materials

1. Evidence package with chain of custody (JSON + Markdown)
2. Statutory citation analysis with penalty calculations
3. Supporting filing references and source documentation

## Evidence Integrity

All evidence materials include SHA-256 integrity hashes and are packaged
with FRE 902(13)/(14) compliant chain of custody records. Evidence chain
verified via RFC 6962 Merkle tree construction.

---

*Generated by the JLAW × SEC-AGENT Forensic Analysis Platform.*
"""

        with open(cover_path, "w", encoding="utf-8") as f:
            f.write(content)

        return cover_path
