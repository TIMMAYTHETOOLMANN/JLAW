#!/usr/bin/env python3
"""Build chain-of-custody evidence manifests from local evidence directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_CONFIDENTIALITY_LEVEL = "restricted_local"
DEFAULT_EVIDENCE_STRENGTH = "unscored"
DEFAULT_FIRSTHAND_OBSERVATION = False
DEFAULT_DOCUMENTARY_SUPPORT = True
DEFAULT_INFERENCE_REQUIRED = "unknown"
DEFAULT_VERIFICATION_NEEDED = True


def compute_sha256(path: Path) -> str:
    """Return the SHA-256 hash for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_mime_category(path: Path) -> str:
    """Return a broad MIME-style category for a file path."""
    mime, _ = mimetypes.guess_type(str(path))
    if not mime:
        return "application/octet-stream"
    return mime


def infer_source_type(path: Path, input_root: Path) -> str:
    """Infer source type from the input root directory name."""
    root_name = input_root.name.lower()
    mapping = {
        "raw": "RAW_EVIDENCE",
        "sec_filings": "SEC_PUBLIC_FILING",
        "whistleblower_exhibits": "WHISTLEBLOWER_EXHIBIT",
        "generated_reports": "GENERATED_ANALYSIS",
    }
    return mapping.get(root_name, f"LOCAL_{root_name.upper()}")


def relative_posix(path: Path, base: Path) -> str:
    """Return path relative to base when possible, otherwise absolute POSIX path."""
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_manifest_entry(file_path: Path, input_root: Path, repo_root: Path) -> dict[str, Any]:
    """Build one manifest entry for a file."""
    stat = file_path.stat()
    file_hash = compute_sha256(file_path)
    timestamp = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()
    date_obtained = datetime.now(tz=UTC).date().isoformat()

    return {
        "evidence_id": f"EVID-{file_hash[:12].upper()}",
        "title": file_path.stem.replace("_", " ").replace("-", " ").strip() or file_path.name,
        "source_type": infer_source_type(file_path, input_root),
        "source_origin": "local_evidence_workspace",
        "date_created": timestamp,
        "date_obtained": date_obtained,
        "custodian": "local_case_team",
        "file_path": relative_posix(file_path, repo_root),
        "file_extension": file_path.suffix.lower(),
        "mime_category": get_mime_category(file_path),
        "hash_sha256": file_hash,
        "confidentiality_level": DEFAULT_CONFIDENTIALITY_LEVEL,
        "legal_domain": ["unclassified"],
        "related_claims": [],
        "related_entities": [],
        "evidence_strength": DEFAULT_EVIDENCE_STRENGTH,
        "firsthand_observation": DEFAULT_FIRSTHAND_OBSERVATION,
        "documentary_support": DEFAULT_DOCUMENTARY_SUPPORT,
        "inference_required": DEFAULT_INFERENCE_REQUIRED,
        "verification_needed": DEFAULT_VERIFICATION_NEEDED,
        "notes": "Auto-generated manifest entry. Review before external use.",
    }


def iter_files(input_root: Path) -> list[Path]:
    """Return all files under an input root recursively."""
    return sorted([path for path in input_root.rglob("*") if path.is_file()])


def build_manifest(inputs: list[Path], output: Path, repo_root: Path) -> dict[str, Any]:
    """Build and write a manifest JSON document."""
    evidence_items: list[dict[str, Any]] = []
    for input_root in inputs:
        for file_path in iter_files(input_root):
            evidence_items.append(build_manifest_entry(file_path=file_path, input_root=input_root, repo_root=repo_root))

    manifest = {
        "manifest_version": "1.0",
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "input_directories": [relative_posix(path, repo_root) for path in inputs],
        "evidence_items": evidence_items,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Build a chain-of-custody evidence manifest")
    parser.add_argument("--input", action="append", required=True, help="Input evidence directory (repeatable)")
    parser.add_argument("--output", required=True, help="Output manifest JSON path")
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    repo_root = Path.cwd()
    inputs = [Path(value).resolve() for value in args.input]

    missing = [path for path in inputs if not path.exists() or not path.is_dir()]
    if missing:
        for path in missing:
            print(f"ERROR: input directory not found: {path}")
        return 1

    output = Path(args.output).resolve()
    manifest = build_manifest(inputs=inputs, output=output, repo_root=repo_root)
    print(f"Manifest written: {output}")
    print(f"Evidence files indexed: {len(manifest['evidence_items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
