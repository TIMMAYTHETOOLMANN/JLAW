"""
Forensic Output Documentation Configuration
==========================================

Central configuration and quality controls for all report outputs
(JSON/Markdown/HTML/PDF and companion manifests).

This module codifies the NIKE 2019 baseline and HOLY_GRAIL pipeline
expectations into a single profile that generators can embed and enforce.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class SectionRequirement:
    """Required documentation section and why it exists."""
    name: str
    objective: str
    minimum_fields: List[str]


@dataclass(frozen=True)
class VisualRequirement:
    """Expected visual artifacts for forensic presentation quality."""
    key: str
    title: str
    rationale: str


@dataclass(frozen=True)
class DocumentationProfile:
    """Single profile for output documentation behavior and quality gates."""
    profile_id: str
    reference_document: str
    profile_version: str
    required_sections: List[SectionRequirement]
    visual_requirements: List[VisualRequirement]
    quality_thresholds: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "reference_document": self.reference_document,
            "profile_version": self.profile_version,
            "required_sections": [
                {
                    "name": s.name,
                    "objective": s.objective,
                    "minimum_fields": s.minimum_fields,
                }
                for s in self.required_sections
            ],
            "visual_requirements": [
                {
                    "key": v.key,
                    "title": v.title,
                    "rationale": v.rationale,
                }
                for v in self.visual_requirements
            ],
            "quality_thresholds": self.quality_thresholds,
        }


FORENSIC_OUTPUT_DOCUMENTATION_PROFILE = DocumentationProfile(
    profile_id="JLAW-FORENSIC-OUTPUT-DOCCONFIG",
    reference_document="NIKE 2019 baseline dossier + HOLY_GRAIL_PIPELINE.md",
    profile_version="2.0",
    required_sections=[
        SectionRequirement(
            name="Executive Summary",
            objective="Lead with prosecutorially relevant findings and routing.",
            minimum_fields=["threat_level", "violation_totals", "routing"],
        ),
        SectionRequirement(
            name="Per-Filing Analysis",
            objective="Preserve filing-granular evidence and context.",
            minimum_fields=["accession_number", "violations", "exact_quotes"],
        ),
        SectionRequirement(
            name="Violation Details with Statutory Citations",
            objective="Bind each violation to legal authority and penalties.",
            minimum_fields=["violation_id", "citation", "damage_estimate"],
        ),
        SectionRequirement(
            name="Dual-Agent Consensus",
            objective="Document AI corroboration and disagreement controls.",
            minimum_fields=["overlap", "confidence", "disagreements"],
        ),
        SectionRequirement(
            name="Evidence Chain",
            objective="Maintain FRE 902-ready integrity and provenance.",
            minimum_fields=["sha256", "collector", "verification_status"],
        ),
        SectionRequirement(
            name="Financial Impact Assessment",
            objective="Quantify civil/criminal exposure and disgorgement.",
            minimum_fields=["civil_range", "disgorgement", "criminal_exposure"],
        ),
        SectionRequirement(
            name="Regulatory Routing Recommendations",
            objective="Explicitly route to SEC/DOJ/IRS with rationale.",
            minimum_fields=["sec_referral", "doj_referral", "irs_referral"],
        ),
    ],
    visual_requirements=[
        VisualRequirement(
            key="severity_distribution",
            title="Severity distribution chart",
            rationale="Instantly communicates case posture and enforcement urgency.",
        ),
        VisualRequirement(
            key="transaction_timeline",
            title="Transaction timeline",
            rationale="Shows sequence linkage between transactions and events.",
        ),
        VisualRequirement(
            key="beneficiary_profits",
            title="Beneficiary profit waterfall",
            rationale="Surfaces concentration of gains and likely beneficiaries.",
        ),
        VisualRequirement(
            key="actor_network",
            title="Actor relationship network",
            rationale="Visual evidence of actor coordination and control paths.",
        ),
    ],
    quality_thresholds={
        "exact_quotes_per_violation": 1,
        "statutory_citations_per_violation": 1,
        "chain_of_custody_records_required": True,
        "dual_agent_validation_required": True,
        "minimum_overall_confidence": 0.70,
    },
)


def get_output_documentation_profile() -> DocumentationProfile:
    """Return the active output documentation profile."""
    return FORENSIC_OUTPUT_DOCUMENTATION_PROFILE
