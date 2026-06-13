"""Tests for evidence manifest builder."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts import evidence_manifest_builder as builder


REQUIRED_ENTRY_FIELDS = {
    "evidence_id",
    "title",
    "source_type",
    "source_origin",
    "date_created",
    "date_obtained",
    "custodian",
    "file_path",
    "hash_sha256",
    "confidentiality_level",
    "legal_domain",
    "related_claims",
    "related_entities",
    "evidence_strength",
    "firsthand_observation",
    "documentary_support",
    "inference_required",
    "verification_needed",
    "notes",
}


def test_compute_sha256_matches_python_hashlib(tmp_path: Path) -> None:
    """SHA-256 output should match hashlib behavior."""
    sample = tmp_path / "sample.txt"
    sample.write_text("hello evidence\n", encoding="utf-8")

    expected = hashlib.sha256(sample.read_bytes()).hexdigest()
    assert builder.compute_sha256(sample) == expected


def test_build_manifest_contains_required_fields(tmp_path: Path) -> None:
    """Manifest entries should include all required schema fields."""
    input_dir = tmp_path / "raw"
    input_dir.mkdir(parents=True)
    (input_dir / "doc.txt").write_text("local evidence", encoding="utf-8")

    output = tmp_path / "manifest.json"
    manifest = builder.build_manifest(inputs=[input_dir], output=output, repo_root=tmp_path)

    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["manifest_version"] == "1.0"
    assert isinstance(payload["evidence_items"], list)
    assert len(payload["evidence_items"]) == 1

    entry = payload["evidence_items"][0]
    assert REQUIRED_ENTRY_FIELDS.issubset(entry.keys())
    assert entry["confidentiality_level"] == "restricted_local"
    assert entry["evidence_strength"] == "unscored"
    assert entry["firsthand_observation"] is False
    assert entry["documentary_support"] is True
    assert entry["inference_required"] == "unknown"
    assert entry["verification_needed"] is True

    assert manifest["evidence_items"][0]["hash_sha256"] == entry["hash_sha256"]
