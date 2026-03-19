"""
Legislative Brief Generator — Congressional Briefing Documents
================================================================

Wires to JLAW's production-grade ExecutiveBriefingFormatter for
generating congressional briefing documents and legislative analysis
packages.

Architecture:
    Track A: Modular Tactical Bundles → Congressional
        → ExecutiveBriefingFormatter (executive intelligence briefing)
        → Enriched with legislative context and policy recommendations

Source Integration:
    JLAW formatters/executive_briefing.py (235 LOC) → Executive briefing format
    SEC-AGENT submission_targets.yaml → Congressional recipient contacts
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.reporting.formatters.executive_briefing import ExecutiveBriefingFormatter

logger = logging.getLogger(__name__)


@dataclass
class CongressionalRecipient:
    """Congressional recipient configuration."""

    name: str
    title: str
    committee: str
    chamber: str  # "Senate" or "House"
    subcommittee: Optional[str] = None
    priority: str = "standard"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "title": self.title,
            "committee": self.committee,
            "chamber": self.chamber,
            "subcommittee": self.subcommittee,
            "priority": self.priority,
        }


@dataclass
class LegislativeBriefOutput:
    """Output from legislative brief generation."""

    brief_id: str
    case_id: str
    company_name: str
    cik: str
    generated_at: datetime
    executive_briefing: Optional[str] = None
    policy_analysis: Optional[str] = None
    output_paths: Dict[str, Path] = field(default_factory=dict)
    recipients: List[CongressionalRecipient] = field(default_factory=list)
    total_violations: int = 0
    systemic_issues: List[str] = field(default_factory=list)
    policy_recommendations: List[str] = field(default_factory=list)
    status: str = "generated"
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "brief_id": self.brief_id,
            "case_id": self.case_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "generated_at": self.generated_at.isoformat(),
            "output_paths": {k: str(v) for k, v in self.output_paths.items()},
            "recipients": [r.to_dict() for r in self.recipients],
            "total_violations": self.total_violations,
            "systemic_issues": self.systemic_issues,
            "policy_recommendations": self.policy_recommendations,
            "status": self.status,
            "error_count": len(self.errors),
        }


# Default Congressional recipients
DEFAULT_CONGRESSIONAL_RECIPIENTS: List[CongressionalRecipient] = [
    CongressionalRecipient(
        name="Senate Banking Committee",
        title="Chairman",
        committee="Committee on Banking, Housing, and Urban Affairs",
        chamber="Senate",
        priority="standard",
    ),
    CongressionalRecipient(
        name="House Financial Services Committee",
        title="Chairman",
        committee="Committee on Financial Services",
        chamber="House",
        priority="standard",
    ),
]


class LegislativeBriefGenerator:
    """
    Generate congressional briefing documents and legislative analysis.

    Wraps JLAW's ExecutiveBriefingFormatter with congressional context,
    policy analysis, and legislative recommendation generation.

    Args:
        output_dir: Directory for generated briefs.
        recipients: Congressional recipient configurations.
    """

    def __init__(
        self,
        output_dir: str = "./output/legislative_briefs",
        recipients: Optional[List[CongressionalRecipient]] = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recipients = recipients or DEFAULT_CONGRESSIONAL_RECIPIENTS

        logger.info(
            "LegislativeBriefGenerator initialized: output=%s, recipients=%d",
            self.output_dir,
            len(self.recipients),
        )

    def generate_brief(
        self,
        case_id: str,
        company_name: str,
        cik: str,
        exec_summary: Dict[str, Any],
        analysis_results: Optional[Dict[str, Any]] = None,
        include_policy_analysis: bool = True,
    ) -> LegislativeBriefOutput:
        """
        Generate a complete congressional briefing package.

        Args:
            case_id: Unique case identifier.
            company_name: Target company name.
            cik: Target company CIK.
            exec_summary: Executive summary data for briefing format.
            analysis_results: Full analysis results (optional).
            include_policy_analysis: Whether to generate policy recommendations.

        Returns:
            LegislativeBriefOutput with all generated files and metadata.
        """
        brief_id = f"LEG-{case_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        output = LegislativeBriefOutput(
            brief_id=brief_id,
            case_id=case_id,
            company_name=company_name,
            cik=cik,
            generated_at=datetime.utcnow(),
            recipients=self.recipients,
        )

        # ── Component 1: Executive Intelligence Briefing ────────────────
        try:
            # Enrich exec summary with company context
            enriched_summary = {
                **exec_summary,
                "company_name": company_name,
                "cik": cik,
                "case_id": case_id,
            }

            # Generate formatted briefing via JLAW's ExecutiveBriefingFormatter
            briefing_text = ExecutiveBriefingFormatter.format(enriched_summary)
            output.executive_briefing = briefing_text

            # Export briefing
            briefing_path = self.output_dir / f"{brief_id}_executive_briefing.txt"
            with open(briefing_path, "w", encoding="utf-8") as f:
                f.write(briefing_text)
            output.output_paths["executive_briefing"] = briefing_path

            # Extract violation count
            output.total_violations = exec_summary.get("total_violations", 0)

            logger.info("Executive briefing generated: %s", briefing_path)

        except Exception as e:
            logger.error("Executive briefing generation failed: %s", e)
            output.errors.append(f"Executive briefing: {e}")

        # ── Component 2: Policy Analysis ────────────────────────────────
        if include_policy_analysis:
            try:
                policy_text = self._generate_policy_analysis(
                    brief_id=brief_id,
                    company_name=company_name,
                    cik=cik,
                    exec_summary=exec_summary,
                    analysis_results=analysis_results,
                )
                output.policy_analysis = policy_text

                policy_path = self.output_dir / f"{brief_id}_policy_analysis.md"
                with open(policy_path, "w", encoding="utf-8") as f:
                    f.write(policy_text)
                output.output_paths["policy_analysis"] = policy_path

                logger.info("Policy analysis generated: %s", policy_path)

            except Exception as e:
                logger.error("Policy analysis generation failed: %s", e)
                output.errors.append(f"Policy analysis: {e}")

        # ── Component 3: Legislative Markdown Brief ─────────────────────
        try:
            brief_path = self._generate_legislative_markdown(
                brief_id=brief_id,
                company_name=company_name,
                cik=cik,
                output=output,
                exec_summary=exec_summary,
            )
            output.output_paths["legislative_brief"] = brief_path

        except Exception as e:
            logger.error("Legislative brief generation failed: %s", e)
            output.errors.append(f"Legislative brief: {e}")

        output.status = "success" if not output.errors else "partial"

        # ── Export manifest ─────────────────────────────────────────────
        manifest_path = self.output_dir / f"{brief_id}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(output.to_dict(), f, indent=2, default=str)
        output.output_paths["manifest"] = manifest_path

        logger.info(
            "Legislative brief generated: %s (%d violations)",
            brief_id,
            output.total_violations,
        )

        return output

    def _generate_policy_analysis(
        self,
        brief_id: str,
        company_name: str,
        cik: str,
        exec_summary: Dict[str, Any],
        analysis_results: Optional[Dict[str, Any]],
    ) -> str:
        """Generate policy analysis and legislative recommendations."""
        violations = exec_summary.get("violations", [])
        total_violations = exec_summary.get("total_violations", len(violations))

        # Identify systemic issues based on violation patterns
        systemic_issues = self._identify_systemic_issues(violations)

        # Generate policy recommendations
        recommendations = self._generate_recommendations(
            systemic_issues, total_violations
        )

        lines = [
            "# POLICY ANALYSIS AND LEGISLATIVE RECOMMENDATIONS",
            "",
            f"**Brief ID:** {brief_id}",
            f"**Company:** {company_name} (CIK: {cik})",
            f"**Date:** {datetime.utcnow().strftime('%B %d, %Y')}",
            "",
            "---",
            "",
            "## Systemic Issues Identified",
            "",
        ]

        if systemic_issues:
            for i, issue in enumerate(systemic_issues, 1):
                lines.append(f"{i}. {issue}")
            lines.append("")
        else:
            lines.extend(["*No systemic issues identified.*", ""])

        lines.extend([
            "## Policy Recommendations",
            "",
        ])

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        else:
            lines.extend(["*No specific policy recommendations at this time.*", ""])

        lines.extend([
            "## Regulatory Gap Analysis",
            "",
            f"This analysis identified {total_violations} potential violations "
            f"affecting {company_name}. The patterns observed suggest areas where "
            "current regulatory frameworks may benefit from legislative attention.",
            "",
            "---",
            "",
            "*This analysis is provided for informational purposes to support "
            "congressional oversight of securities regulation.*",
        ])

        return "\n".join(lines)

    def _generate_legislative_markdown(
        self,
        brief_id: str,
        company_name: str,
        cik: str,
        output: LegislativeBriefOutput,
        exec_summary: Dict[str, Any],
    ) -> Path:
        """Generate the main legislative brief as Markdown."""
        brief_path = self.output_dir / f"{brief_id}_brief.md"

        content = f"""# CONGRESSIONAL BRIEFING: SECURITIES COMPLIANCE ANALYSIS

**Brief ID:** {brief_id}
**Date:** {datetime.utcnow().strftime('%B %d, %Y')}
**Classification:** UNCLASSIFIED // FOR OFFICIAL USE ONLY

---

## Subject: {company_name} (SEC CIK: {cik})

### Executive Summary

This briefing presents findings from a systematic forensic analysis of SEC
filings by {company_name}. The analysis identified {output.total_violations}
potential securities law violations warranting regulatory attention.

### Key Findings

{output.executive_briefing or '*Executive briefing pending.*'}

### Systemic Issues

{chr(10).join(f'- {issue}' for issue in output.systemic_issues) if output.systemic_issues else '*None identified.*'}

### Policy Recommendations

{chr(10).join(f'- {rec}' for rec in output.policy_recommendations) if output.policy_recommendations else '*None at this time.*'}

---

### Distribution

{chr(10).join(f'- {r.committee} ({r.chamber})' for r in output.recipients)}

---

*Generated by the JLAW × SEC-AGENT Forensic Analysis Platform.*
*This document is intended for congressional oversight purposes.*
"""

        with open(brief_path, "w", encoding="utf-8") as f:
            f.write(content)

        return brief_path

    @staticmethod
    def _identify_systemic_issues(
        violations: List[Dict[str, Any]],
    ) -> List[str]:
        """Identify systemic regulatory issues from violation patterns."""
        issues = []

        # Analyze violation type distribution
        violation_types: Dict[str, int] = {}
        for v in violations:
            vtype = v.get("violation_type", v.get("type", "unknown"))
            violation_types[vtype] = violation_types.get(vtype, 0) + 1

        # Check for recurring patterns
        for vtype, count in violation_types.items():
            if count >= 3:
                issues.append(
                    f"Recurring {vtype} violations ({count} instances) suggest "
                    "systematic compliance deficiency"
                )

        # Check for cross-cutting issues
        if "LATE_FORM4" in violation_types and "SHORT_SWING_PROFIT" in violation_types:
            issues.append(
                "Combined late filing and short-swing profit violations suggest "
                "inadequate Section 16 compliance infrastructure"
            )

        if "SOX_302_CERTIFICATION_FAILURE" in violation_types:
            issues.append(
                "SOX certification failures indicate potential gaps in "
                "internal control frameworks"
            )

        return issues

    @staticmethod
    def _generate_recommendations(
        systemic_issues: List[str],
        total_violations: int,
    ) -> List[str]:
        """Generate policy recommendations based on systemic issues."""
        recommendations = []

        if total_violations > 10:
            recommendations.append(
                "Consider enhanced SEC enforcement funding for systematic "
                "compliance monitoring"
            )

        if total_violations > 20:
            recommendations.append(
                "Evaluate adequacy of current penalty structures as deterrent "
                "against repeated violations"
            )

        if any("Section 16" in issue for issue in systemic_issues):
            recommendations.append(
                "Review Section 16 filing deadlines and consider mandatory "
                "electronic filing requirements"
            )

        if any("SOX" in issue for issue in systemic_issues):
            recommendations.append(
                "Assess Sarbanes-Oxley internal control requirements and "
                "consider expanding auditor oversight mandates"
            )

        if not recommendations:
            recommendations.append(
                "Continue routine oversight of SEC enforcement activities "
                "related to this matter"
            )

        return recommendations
