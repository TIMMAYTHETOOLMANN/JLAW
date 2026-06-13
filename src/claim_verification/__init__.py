"""Deterministic claim verification tooling for local-only evidence review."""

from .claim_extractor import ExtractedClaim, extract_claims_from_text, is_public_claim_source
from .confidence_scoring import ConfidenceAssessment, score_claim_verification
from .evidence_matcher import EvidenceMatchResult, match_claim_to_evidence
from .language_guard import LanguageGuardResult, guard_payload, sanitize_text, scan_text
from .verification_hitlist import generate_verification_hitlist

__all__ = [
    "ConfidenceAssessment",
    "EvidenceMatchResult",
    "ExtractedClaim",
    "LanguageGuardResult",
    "extract_claims_from_text",
    "generate_verification_hitlist",
    "guard_payload",
    "is_public_claim_source",
    "match_claim_to_evidence",
    "sanitize_text",
    "scan_text",
    "score_claim_verification",
]
