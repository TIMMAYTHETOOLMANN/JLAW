"""Confidence scoring for deterministic claim verification outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

SAFE_WORDING_LEVELS = {
    5: 'LEVEL 5: "records reviewed indicate"',
    4: 'LEVEL 4: "available documents appear inconsistent with"',
    3: 'LEVEL 3: "testimony and supporting records raise questions"',
    2: 'LEVEL 2: "this is an investigative lead requiring verification"',
    1: 'LEVEL 1: "excluded from report pending corroboration"',
    0: 'LEVEL 0: "not relevant"',
}


@dataclass(frozen=True)
class ConfidenceAssessment:
    """Scored view of one claim after evidence matching."""

    score: int
    rationale: str
    evidence_basis: list[str]
    missing_verification: list[str]
    safe_wording_level: str
    safe_report_language: str
    verification_status: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the confidence assessment."""
        return asdict(self)


def score_claim_verification(
    claim: Mapping[str, Any],
    matches: Sequence[Mapping[str, Any]],
) -> ConfidenceAssessment:
    """Assign a conservative confidence score to a claim/evidence bundle."""
    relevant = [match for match in matches if match.get("relationship") != "unrelated"]
    documentary = [match for match in relevant if match.get("evidence_classification") == "verified documentary fact"]
    firsthand = [match for match in relevant if match.get("evidence_classification") == "firsthand testimony"]
    contradictory = [match for match in relevant if match.get("relationship") == "contradicts"]
    supporting = [match for match in relevant if match.get("relationship") == "supports"]
    broad_claim = len(str(claim.get("claim_text", "")).split()) < 4
    direct_documentary = any(
        match.get("relationship") == "contradicts"
        and match.get("evidence_classification") == "verified documentary fact"
        and match.get("direct_textual_alignment")
        for match in relevant
    )

    if direct_documentary:
        score = 5
        rationale = "Direct documentary contradiction with aligned text was identified."
        status = "appears inconsistent"
    elif documentary and firsthand and (contradictory or supporting):
        score = 4
        rationale = "Documentary evidence is reinforced by firsthand corroboration."
        status = "requires focused verification"
    elif firsthand and (documentary or any(match.get("relationship") == "contextualizes" for match in relevant)):
        score = 3
        rationale = "Firsthand testimony is supported by related records, but not direct documentary contradiction."
        status = "raises questions"
    elif relevant:
        score = 1 if broad_claim else 2
        rationale = "The available evidence suggests a lead but requires independent verification."
        status = "requires verification"
    else:
        score = 0
        rationale = "No usable relationship between the claim and supplied evidence was identified."
        status = "not relevant"

    evidence_basis = [f"{match.get('evidence_id')}: {match.get('relationship')}" for match in relevant[:5]]
    missing_verification: list[str] = []
    if not documentary:
        missing_verification.append("Independent documentary records are still needed.")
    if not firsthand and score >= 2:
        missing_verification.append("No firsthand corroboration has been identified.")
    if not claim.get("claim_date"):
        missing_verification.append("Claim date should be confirmed from the originating public statement.")
    if broad_claim:
        missing_verification.append("Claim wording is broad and should be narrowed to a specific statement.")

    safe_report_language = {
        5: f"records reviewed indicate the statement '{claim.get('claim_text', '')}' is directly contradicted by identified documents.",
        4: f"available documents appear inconsistent with the statement '{claim.get('claim_text', '')}'.",
        3: f"testimony and supporting records raise questions about the statement '{claim.get('claim_text', '')}'.",
        2: f"this is an investigative lead requiring verification concerning the statement '{claim.get('claim_text', '')}'.",
        1: f"excluded from report pending corroboration for the statement '{claim.get('claim_text', '')}'.",
        0: f"not relevant to the statement '{claim.get('claim_text', '')}'.",
    }[score]

    return ConfidenceAssessment(
        score=score,
        rationale=rationale,
        evidence_basis=evidence_basis,
        missing_verification=missing_verification,
        safe_wording_level=SAFE_WORDING_LEVELS[score],
        safe_report_language=safe_report_language,
        verification_status=status,
    )
