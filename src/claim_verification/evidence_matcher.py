"""Conservative evidence matching for deterministic claim review."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "have",
    "has",
    "into",
    "about",
    "their",
    "they",
    "them",
    "were",
    "will",
    "would",
    "there",
    "which",
    "while",
    "where",
    "when",
    "what",
    "said",
    "says",
    "maintain",
    "committed",
    "company",
    "public",
    "claim",
}

CONTRADICTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bfailed to\b", re.IGNORECASE),
    re.compile(r"\bdid not\b", re.IGNORECASE),
    re.compile(r"\black(?:ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bunsafe\b", re.IGNORECASE),
    re.compile(r"\bhazard\b", re.IGNORECASE),
    re.compile(r"\bcitation\b", re.IGNORECASE),
    re.compile(r"\bspill\b", re.IGNORECASE),
    re.compile(r"\bnoncompliance\b", re.IGNORECASE),
    re.compile(r"\bfault log\b", re.IGNORECASE),
    re.compile(r"\binjury\b", re.IGNORECASE),
)

SUPPORT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bpolicy\b", re.IGNORECASE),
    re.compile(r"\btraining\b", re.IGNORECASE),
    re.compile(r"\baudit\b", re.IGNORECASE),
    re.compile(r"\bmaintained?\b", re.IGNORECASE),
    re.compile(r"\bcomplied?\b", re.IGNORECASE),
    re.compile(r"\bcertified?\b", re.IGNORECASE),
    re.compile(r"\binspection\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class EvidenceMatchResult:
    """Structured relationship between one claim and one evidence record."""

    evidence_id: str
    evidence_title: str
    relationship: str
    relationship_score: int
    direct_textual_alignment: bool
    matched_keywords: list[str]
    evidence_classification: str
    legal_domain: str
    source_type: str
    related_entities: list[str]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the match result."""
        return asdict(self)


def infer_evidence_classification(record: Mapping[str, Any]) -> str:
    """Infer the evidence classification required by the claim matrix."""
    haystack = " ".join(
        str(record.get(key, ""))
        for key in ("source_type", "title", "source_origin", "legal_domain", "notes")
    ).lower()
    if any(token in haystack for token in ("testimony", "witness", "whistleblower", "interview")):
        return "firsthand testimony"
    if any(token in haystack for token in ("generated", "analysis", "summary")):
        return "generated analysis"
    if any(
        token in haystack
        for token in ("osha", "epa", "sec", "board", "audit", "filing", "log", "record", "minutes", "document")
    ):
        return "verified documentary fact"
    return "unverified lead"


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


def _normalise_path(value: str) -> str:
    return Path(value).name.lower()


def _related_entities(record: Mapping[str, Any]) -> set[str]:
    raw_entities = record.get("related_entities") or []
    if isinstance(raw_entities, str):
        raw_entities = [raw_entities]
    return {str(entity).lower() for entity in raw_entities if str(entity).strip()}


def _build_record_text(record: Mapping[str, Any], evidence_texts: Mapping[str, str]) -> str:
    parts = [
        str(record.get("title", "")),
        str(record.get("notes", "")),
        str(record.get("source_origin", "")),
        str(record.get("summary", "")),
    ]
    candidate_paths = {
        str(record.get("file_path", "")),
        str(record.get("text_path", "")),
        str(record.get("source_file", "")),
    }
    lowered = {_normalise_path(path) for path in candidate_paths if path}
    for path_name, text in evidence_texts.items():
        if _normalise_path(path_name) in lowered:
            parts.append(text)
    return "\n".join(part for part in parts if part)


def match_claim_to_evidence(
    claim: Mapping[str, Any],
    evidence_records: Sequence[Mapping[str, Any]],
    evidence_texts: Mapping[str, str],
) -> list[EvidenceMatchResult]:
    """Match one claim against evidence records using conservative heuristics."""
    claim_text = str(claim.get("claim_text", ""))
    claim_tokens = _tokenize(claim_text)
    claim_entities = {str(claim.get("corporate_speaker", "")).lower()} if claim.get("corporate_speaker") else set()
    claim_category = str(claim.get("claim_type", ""))
    category_anchor = claim_category.split(" ")[0].lower() if claim_category else ""
    results: list[EvidenceMatchResult] = []

    for record in evidence_records:
        evidence_text = _build_record_text(record, evidence_texts)
        evidence_tokens = _tokenize(evidence_text)
        overlap = sorted(claim_tokens & evidence_tokens)
        entity_overlap = claim_entities & _related_entities(record)
        legal_domain = str(record.get("legal_domain", ""))
        classification = infer_evidence_classification(record)
        source_type = str(record.get("source_type", ""))
        category_match = bool(category_anchor and category_anchor in legal_domain.lower())
        direct_alignment = len(overlap) >= 3 and category_match
        has_contradiction_cue = any(pattern.search(evidence_text) for pattern in CONTRADICTION_PATTERNS)
        has_support_cue = any(pattern.search(evidence_text) for pattern in SUPPORT_PATTERNS)
        score = min(len(overlap), 3)
        if category_match:
            score += 1
        if entity_overlap:
            score += 1
        relationship = "unrelated"
        rationale = "No meaningful overlap detected."

        if overlap or category_match or entity_overlap:
            if has_contradiction_cue and (len(overlap) >= 1 or category_match):
                relationship = "contradicts"
                score = min(max(score, 2) + 1, 4 if direct_alignment else 3)
                rationale = "Evidence text contains relevant overlap and contradiction cues."
            elif has_support_cue and (len(overlap) >= 2 or category_match):
                relationship = "supports"
                score = min(max(score, 2) + 1, 4)
                rationale = "Evidence text contains relevant overlap and documentary support cues."
            elif len(overlap) >= 2 or entity_overlap or category_match:
                relationship = "contextualizes"
                score = min(max(score, 2), 3)
                rationale = "Evidence appears related but does not directly support or contradict the claim."
            else:
                relationship = "requires verification"
                score = min(max(score, 1), 2)
                rationale = "Evidence may be related but requires additional records to verify relevance."

        evidence_id = str(record.get("evidence_id") or record.get("id") or record.get("title") or "unknown-evidence")
        results.append(
            EvidenceMatchResult(
                evidence_id=evidence_id,
                evidence_title=str(record.get("title") or evidence_id),
                relationship=relationship,
                relationship_score=score if relationship != "unrelated" else 0,
                direct_textual_alignment=direct_alignment,
                matched_keywords=overlap[:8],
                evidence_classification=classification,
                legal_domain=legal_domain,
                source_type=source_type,
                related_entities=sorted(_related_entities(record)),
                rationale=rationale,
            )
        )

    return sorted(results, key=lambda item: item.relationship_score, reverse=True)
