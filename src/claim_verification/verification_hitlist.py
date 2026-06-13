"""Generate record request hit lists for claim verification."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

HITLIST_MAP = {
    "safety claim": ["OSHA logs", "internal maintenance logs", "HMI/PLC telemetry", "machine fault logs"],
    "ESG claim": ["ESG disclosure backup", "SEC filing support documents", "supplier records"],
    "sustainability claim": ["ESG disclosure backup", "EPA waste records", "waste classification documentation"],
    "waste/recycling claim": ["EPA waste records", "waste classification documentation", "vendor service records"],
    "labor/human-rights claim": ["supplier records", "board minutes", "audit committee materials"],
    "financial/materiality claim": ["SEC filing support documents", "audit committee materials", "board minutes"],
    "operational-efficiency claim": ["production/OEE records", "internal maintenance logs", "HMI/PLC telemetry"],
    "product-origin claim": ["supplier records", "vendor service records"],
    "compliance claim": ["SEC filing support documents", "board minutes", "audit committee materials"],
    "risk-disclosure claim": ["SEC filing support documents", "board minutes", "audit committee materials"],
    "insider-transaction claim": ["Form 4 footnotes", "board minutes", "audit committee materials"],
    "unknown claim": ["SEC filing support documents"],
}


def generate_verification_hitlist(claim_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Generate a conservative verification hit list for each claim."""
    items: list[dict[str, Any]] = []
    for claim in claim_records:
        claim_type = str(claim.get("claim_type") or "unknown claim")
        required_records = list(HITLIST_MAP.get(claim_type, HITLIST_MAP["unknown claim"]))
        missing = list(claim.get("verification_needed") or [])
        items.append(
            {
                "claim_id": claim.get("claim_id"),
                "claim_text": claim.get("claim_text"),
                "claim_type": claim_type,
                "required_records": required_records,
                "priority": "high" if int(claim.get("confidence_score", 0)) >= 3 else "medium",
                "rationale": "Additional records are needed to verify or disprove the public claim.",
                "evidence_gap": missing,
            }
        )
    return {
        "output_type": "verification_hitlist",
        "claims": items,
    }
