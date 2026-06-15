"""Conservative extraction of public corporate claims from local text."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

CLAIM_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "safety claim": ("safe workplace", "worker safety", "safety", "injury prevention"),
    "ESG claim": ("esg", "environmental, social", "governance"),
    "sustainability claim": ("sustainable", "sustainability", "climate", "carbon"),
    "waste/recycling claim": ("zero waste", "recycling", "recycled materials", "nike grind", "waste"),
    "labor/human-rights claim": ("human rights", "responsible manufacturing", "code of conduct", "labor"),
    "financial/materiality claim": ("material", "materiality", "financial impact", "financial condition"),
    "operational-efficiency claim": ("efficiency", "operational excellence", "uptime", "throughput"),
    "product-origin claim": ("made in", "product origin", "sourced", "country of origin"),
    "compliance claim": ("we comply", "compliance", "internal controls", "code of conduct"),
    "risk-disclosure claim": ("risk factors", "risk management", "internal controls", "controls"),
    "insider-transaction claim": ("form 4", "insider", "beneficial ownership", "trading policy"),
}

TRIGGER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bwe are committed to\b", re.IGNORECASE),
    re.compile(r"\bwe maintain\b", re.IGNORECASE),
    re.compile(r"\bwe comply\b", re.IGNORECASE),
    re.compile(r"\bsustainable\b", re.IGNORECASE),
    re.compile(r"\bzero waste\b", re.IGNORECASE),
    re.compile(r"\bsafe workplace\b", re.IGNORECASE),
    re.compile(r"\bworker safety\b", re.IGNORECASE),
    re.compile(r"\bresponsible manufacturing\b", re.IGNORECASE),
    re.compile(r"\bNike Grind\b", re.IGNORECASE),
    re.compile(r"\brecycled materials\b", re.IGNORECASE),
    re.compile(r"\brisk factors\b", re.IGNORECASE),
    re.compile(r"\binternal controls\b", re.IGNORECASE),
    re.compile(r"\bESG\b", re.IGNORECASE),
    re.compile(r"\bsupply chain\b", re.IGNORECASE),
    re.compile(r"\bhuman rights\b", re.IGNORECASE),
    re.compile(r"\bCode of Conduct\b", re.IGNORECASE),
)

PUBLIC_SOURCE_HINTS = (
    "10-k",
    "10-q",
    "sec",
    "filing",
    "annual report",
    "proxy",
    "investor",
    "esg",
    "sustainability",
    "press release",
    "corporate",
    "website",
)

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class ExtractedClaim:
    """Structured public claim extracted from source text."""

    claim_id: str
    claim_text: str
    claim_source: str
    claim_date: str
    claim_type: str
    corporate_speaker: str
    filing_type: str
    public_statement_context: str
    source_file: str
    line_reference: str
    extraction_confidence: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize the extracted claim."""
        return asdict(self)


def is_public_claim_source(metadata: Mapping[str, Any] | None) -> bool:
    """Return True when source metadata looks like a public corporate statement."""
    if not metadata:
        return False
    haystack = " ".join(
        str(metadata.get(key, ""))
        for key in ("source_type", "title", "source_origin", "filing_type", "public_statement_context")
    ).lower()
    return any(hint in haystack for hint in PUBLIC_SOURCE_HINTS)


def classify_claim_type(text: str) -> tuple[str, int]:
    """Classify a sentence into a conservative claim category."""
    normalized = text.lower()
    best_type = "unknown claim"
    best_score = 0
    for claim_type, keywords in CLAIM_TYPE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword.lower() in normalized)
        if score > best_score:
            best_type = claim_type
            best_score = score
    return best_type, best_score


def _iter_sentences(text: str) -> Iterable[tuple[str, int]]:
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        for sentence in SENTENCE_SPLIT_RE.split(stripped):
            sentence = sentence.strip()
            if sentence:
                yield sentence, line_number


def _should_extract(sentence: str) -> tuple[bool, int, str]:
    matched_trigger = any(pattern.search(sentence) for pattern in TRIGGER_PATTERNS)
    claim_type, keyword_score = classify_claim_type(sentence)
    confidence = 0
    if matched_trigger:
        confidence += 2
    confidence += min(keyword_score, 3)
    if sentence.lower().startswith(("we ", "our ")):
        confidence += 1
    return confidence >= 3, min(confidence, 5), claim_type


def extract_claims_from_text(
    text: str,
    source_metadata: Mapping[str, Any] | None = None,
    source_file: str = "",
) -> list[ExtractedClaim]:
    """Extract conservative public corporate claims from text."""
    metadata = dict(source_metadata or {})
    claims: list[ExtractedClaim] = []
    seen_sentences: set[str] = set()
    claim_source = str(metadata.get("title") or metadata.get("source_origin") or source_file or "unknown source")
    claim_date = str(metadata.get("claim_date") or metadata.get("date_created") or metadata.get("date_obtained") or "")
    corporate_speaker = str(metadata.get("corporate_speaker") or metadata.get("company_name") or "Unknown corporate speaker")
    filing_type = str(metadata.get("filing_type") or metadata.get("source_type") or "Unknown filing type")
    context = str(metadata.get("public_statement_context") or metadata.get("title") or claim_source)
    source_name = source_file or str(metadata.get("file_path") or metadata.get("text_path") or "")

    for sentence, line_number in _iter_sentences(text):
        normalized = re.sub(r"\s+", " ", sentence.lower())
        if normalized in seen_sentences:
            continue
        should_extract, confidence, claim_type = _should_extract(sentence)
        if not should_extract:
            continue
        seen_sentences.add(normalized)
        digest = hashlib.sha256(f"{source_name}:{line_number}:{normalized}".encode("utf-8")).hexdigest()[:12]
        claims.append(
            ExtractedClaim(
                claim_id=f"claim-{digest}",
                claim_text=sentence,
                claim_source=claim_source,
                claim_date=claim_date,
                claim_type=claim_type,
                corporate_speaker=corporate_speaker,
                filing_type=filing_type,
                public_statement_context=context,
                source_file=Path(source_name).name if source_name else "",
                line_reference=f"line {line_number}",
                extraction_confidence=confidence,
            )
        )
    return claims
