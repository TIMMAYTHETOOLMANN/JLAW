"""Deterministic local-only claim verification runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.claim_verification import (  # noqa: E402
    extract_claims_from_text,
    generate_verification_hitlist,
    is_public_claim_source,
    match_claim_to_evidence,
    sanitize_text,
    scan_text,
    score_claim_verification,
)

PROCESSED_ROOT = REPO_ROOT / "data" / "evidence" / "processed"
CLAIM_OUTPUT_DIR = PROCESSED_ROOT / "claim_outputs"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=False)
    parser.add_argument("--extracted-text", type=Path, required=False)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--public-claims-only", action="store_true")
    parser.add_argument("--min-confidence", type=int, default=2)
    parser.add_argument("--include-unverified", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--hostile-review", action="store_true")
    parser.add_argument("--allow-external-output", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    """Load JSON from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalise_path(path: str) -> str:
    return Path(path).name.lower()


def load_manifest_records(manifest_path: Path) -> list[dict[str, Any]]:
    """Load manifest records from a flexible JSON structure."""
    manifest = load_json(manifest_path)
    if isinstance(manifest, list):
        return [dict(item) for item in manifest]
    for key in ("evidence_items", "evidence_records", "records", "items", "documents"):
        value = manifest.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value]
    return []


def load_extracted_texts(directory: Path) -> dict[str, str]:
    """Load extracted text files from a directory."""
    texts: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".text"}:
            texts[str(path)] = path.read_text(encoding="utf-8")
    return texts


def build_source_index(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index manifest records by likely source path names."""
    index: dict[str, dict[str, Any]] = {}
    for record in records:
        for key in ("file_path", "text_path", "source_file", "title"):
            value = str(record.get(key, "")).strip()
            if value:
                index[_normalise_path(value)] = record
    return index


def ensure_output_path(output_path: Path, allow_external_output: bool) -> Path:
    """Reject non-local output paths unless the caller explicitly opts in."""
    resolved = output_path.resolve()
    if allow_external_output:
        return resolved
    processed_root = PROCESSED_ROOT.resolve()
    try:
        resolved.relative_to(processed_root)
    except ValueError as exc:
        raise ValueError(
            f"Output path must remain inside {processed_root} unless --allow-external-output is provided."
        ) from exc
    return resolved


def write_json_output(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON output to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Security note: these JSON artifacts may contain sensitive local manifest metadata and must only be
    # written to local Git-ignored evidence paths unless the caller explicitly provides --allow-external-output.
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def create_sample_inputs() -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Create dummy local-only sample inputs."""
    manifest_records = [
        {
            "evidence_id": "PUB-001",
            "title": "Acme Fabrication Sustainability Report",
            "source_type": "esg report",
            "date_created": "2025-01-15",
            "company_name": "Acme Fabrication",
            "corporate_speaker": "Acme Fabrication",
            "filing_type": "ESG Report",
            "public_statement_context": "Annual sustainability summary",
            "file_path": "acme_esg.txt",
            "legal_domain": "sustainability",
            "related_entities": ["Acme Fabrication"],
        },
        {
            "evidence_id": "OSHA-001",
            "title": "Sample OSHA inspection summary",
            "source_type": "osha log",
            "date_created": "2025-02-02",
            "file_path": "osha_summary.txt",
            "legal_domain": "safety",
            "custodian": "local safety counsel",
            "related_entities": ["Acme Fabrication"],
            "notes": "The inspection noted the company did not maintain guarding on one press line.",
        },
        {
            "evidence_id": "WIT-001",
            "title": "Sample witness interview",
            "source_type": "whistleblower testimony",
            "date_obtained": "2025-02-04",
            "file_path": "witness_note.txt",
            "legal_domain": "safety",
            "custodian": "local review team",
            "related_entities": ["Acme Fabrication"],
            "notes": "The witness said workers raised concerns about guarding and lockout procedures.",
        },
    ]
    texts = {
        "acme_esg.txt": (
            "We are committed to worker safety across all facilities. "
            "Our sustainability program emphasizes recycled materials and zero waste practices."
        ),
        "osha_summary.txt": "The inspection noted the company did not maintain guarding and recorded one hazard citation.",
        "witness_note.txt": "A witness described repeated concerns about guarding on the press line.",
    }
    return manifest_records, texts


def _metadata_for_claim_file(path_name: str, source_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return dict(source_index.get(_normalise_path(path_name), {}))


def _is_claim_too_broad(claim: dict[str, Any]) -> bool:
    text = claim.get("claim_text", "").lower()
    return len(text.split()) < 6 or any(token in text for token in ("always", "never", "all facilities"))


def _missing_record_metadata(matches: list[dict[str, Any]]) -> bool:
    for match in matches:
        if match.get("relationship") == "unrelated":
            continue
        if not match.get("evidence_id") or not match.get("source_type"):
            return True
    return False


def evaluate_hostile_review(
    claim: dict[str, Any],
    matches: list[dict[str, Any]],
    assessment: dict[str, Any],
    language_flags: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return exclusion metadata when hostile review rejects a claim."""
    if assessment["score"] < 3:
        return {
            "original_claim": claim,
            "reason_for_exclusion": "Speculative or weakly supported contradiction under hostile review.",
            "evidence_gap": assessment["missing_verification"],
            "remediation_needed": "Obtain stronger documentary records or firsthand corroboration.",
            "can_be_revived_later": True,
        }
    if not claim.get("claim_source") or not claim.get("claim_date"):
        return {
            "original_claim": claim,
            "reason_for_exclusion": "Source or date metadata is incomplete.",
            "evidence_gap": ["Claim provenance must be tied to a dated public statement."],
            "remediation_needed": "Confirm the originating document, speaker, and date.",
            "can_be_revived_later": True,
        }
    if _is_claim_too_broad(claim):
        return {
            "original_claim": claim,
            "reason_for_exclusion": "Claim wording is too broad for hostile review use.",
            "evidence_gap": ["The claim should be narrowed to a discrete dated statement."],
            "remediation_needed": "Rewrite the claim around a specific statement or filing excerpt.",
            "can_be_revived_later": True,
        }
    if _missing_record_metadata(matches):
        return {
            "original_claim": claim,
            "reason_for_exclusion": "Matched evidence lacks enough provenance metadata.",
            "evidence_gap": ["Evidence date, source, or custodian is incomplete."],
            "remediation_needed": "Record the source, date, and custodian for each matched exhibit.",
            "can_be_revived_later": True,
        }
    if not any(match.get("relationship") in {"supports", "contradicts", "contextualizes"} for match in matches):
        return {
            "original_claim": claim,
            "reason_for_exclusion": "Matched evidence is not sufficiently related to the claim.",
            "evidence_gap": ["No related documentary or firsthand record was identified."],
            "remediation_needed": "Locate records directly tied to the claim topic or entities.",
            "can_be_revived_later": True,
        }
    if language_flags:
        return {
            "original_claim": claim,
            "reason_for_exclusion": "Generated wording required language-guard intervention.",
            "evidence_gap": ["Narrative phrasing overstated what the evidence shows."],
            "remediation_needed": "Use only guarded wording and verify the underlying evidence basis.",
            "can_be_revived_later": True,
        }
    return None


def _apply_language_guard(entry: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    flags: list[dict[str, Any]] = []
    for field_name in ("confidence_rationale", "safe_report_language"):
        result = scan_text(str(entry.get(field_name, "")), field_name=field_name)
        entry[field_name] = sanitize_text(result.sanitized_text)
        flags.extend(flag.to_dict() for flag in result.flags)
    return entry, flags


def build_matrix(
    manifest_records: list[dict[str, Any]],
    extracted_texts: dict[str, str],
    public_claims_only: bool,
    min_confidence: int,
    include_unverified: bool,
    hostile_review: bool,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build the claim verification matrix, hit list, and hostile-review exclusions."""
    source_index = build_source_index(manifest_records)
    extracted_claims: list[dict[str, Any]] = []
    for path_name, text in extracted_texts.items():
        metadata = _metadata_for_claim_file(path_name, source_index)
        if public_claims_only and not is_public_claim_source(metadata):
            continue
        extracted_claims.extend(
            claim.to_dict()
            for claim in extract_claims_from_text(text=text, source_metadata=metadata, source_file=path_name)
        )

    matrix_claims: list[dict[str, Any]] = []
    excluded_claims: list[dict[str, Any]] = []
    for claim in extracted_claims:
        matches = [
            match.to_dict()
            for match in match_claim_to_evidence(claim, manifest_records, extracted_texts)
            if match.relationship != "unrelated"
        ]
        assessment = score_claim_verification(claim, matches).to_dict()
        if assessment["score"] < min_confidence and not include_unverified:
            continue
        entry = {
            **claim,
            "claim_classification": "public corporate claim",
            "analysis_bucket": "generated analysis",
            "inference_bucket": (
                "reasonable inference"
                if assessment["score"] >= 3
                else "unverified lead"
                if assessment["score"] == 2
                else "unsupported/speculative claim"
            ),
            "supporting_evidence_ids": [match["evidence_id"] for match in matches if match["relationship"] == "supports"],
            "contradictory_evidence_ids": [match["evidence_id"] for match in matches if match["relationship"] == "contradicts"],
            "contextual_evidence_ids": [match["evidence_id"] for match in matches if match["relationship"] == "contextualizes"],
            "matched_evidence": matches,
            "confidence_score": assessment["score"],
            "confidence_rationale": assessment["rationale"],
            "evidence_basis": assessment["evidence_basis"],
            "verification_needed": assessment["missing_verification"],
            "safe_wording_level": assessment["safe_wording_level"],
            "safe_report_language": assessment["safe_report_language"],
            "verification_status": assessment["verification_status"],
            "defamation_risk": "elevated" if assessment["score"] >= 4 else "moderate" if assessment["score"] >= 2 else "low",
        }
        entry, language_flags = _apply_language_guard(entry)
        entry["language_guard_flags"] = language_flags
        exclusion = evaluate_hostile_review(claim, matches, assessment, language_flags) if hostile_review else None
        if exclusion is not None:
            excluded_claims.append(exclusion)
            continue
        matrix_claims.append(entry)

    hitlist = generate_verification_hitlist(matrix_claims)
    matrix = {
        "output_type": "claim_verification_matrix",
        "hostile_review": hostile_review,
        "claims": matrix_claims,
        "summary": {
            "total_extracted_claims": len(extracted_claims),
            "included_claims": len(matrix_claims),
            "excluded_claims": len(excluded_claims),
        },
    }
    excluded = {"output_type": "excluded_claims", "claims": excluded_claims}
    return matrix, hitlist, excluded


def main() -> int:
    """CLI entrypoint."""
    args = parse_args()
    output_path = ensure_output_path(args.output, args.allow_external_output)

    if args.sample:
        manifest_records, extracted_texts = create_sample_inputs()
    else:
        if not args.manifest or not args.extracted_text:
            raise SystemExit("--manifest and --extracted-text are required unless --sample is used.")
        manifest_records = load_manifest_records(args.manifest)
        extracted_texts = load_extracted_texts(args.extracted_text)

    matrix, hitlist, excluded = build_matrix(
        manifest_records=manifest_records,
        extracted_texts=extracted_texts,
        public_claims_only=args.public_claims_only,
        min_confidence=args.min_confidence,
        include_unverified=args.include_unverified,
        hostile_review=args.hostile_review,
    )

    if args.dry_run:
        print(json.dumps(matrix["summary"], indent=2, sort_keys=True))
        return 0

    write_json_output(output_path, matrix)
    auxiliary_dir = output_path.parent if output_path.parent != output_path else CLAIM_OUTPUT_DIR
    write_json_output(auxiliary_dir / "verification_hitlist.json", hitlist)
    if args.hostile_review:
        write_json_output(auxiliary_dir / "excluded_claims.json", excluded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
