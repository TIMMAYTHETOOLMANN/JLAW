import json
import subprocess
from pathlib import Path

from jsonschema import validate


def test_runner_produces_schema_compatible_json(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest = tmp_path / "manifest.json"
    extracted_dir = tmp_path / "texts"
    output = tmp_path / "claim_verification_matrix.json"
    extracted_dir.mkdir()

    manifest.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "evidence_id": "PUB-1",
                        "title": "Dummy ESG Report",
                        "source_type": "esg report",
                        "date_created": "2025-01-01",
                        "company_name": "Example Fabrication",
                        "corporate_speaker": "Example Fabrication",
                        "filing_type": "ESG Report",
                        "public_statement_context": "Dummy annual report",
                        "file_path": "dummy_report.txt",
                        "legal_domain": "sustainability",
                        "related_entities": ["Example Fabrication"],
                    },
                    {
                        "evidence_id": "DOC-1",
                        "title": "Dummy safety record",
                        "source_type": "osha log",
                        "date_created": "2025-02-01",
                        "file_path": "osha.txt",
                        "legal_domain": "safety",
                        "related_entities": ["Example Fabrication"],
                        "custodian": "local counsel",
                        "notes": "The record says the company did not maintain guarding.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (extracted_dir / "dummy_report.txt").write_text(
        "We are committed to worker safety and sustainable manufacturing.",
        encoding="utf-8",
    )
    (extracted_dir / "osha.txt").write_text(
        "Inspectors found the company did not maintain guarding and cited one hazard.",
        encoding="utf-8",
    )

    command = [
        "python",
        str(repo_root / "scripts" / "claim_verifier_runner.py"),
        "--manifest",
        str(manifest),
        "--extracted-text",
        str(extracted_dir),
        "--output",
        str(output),
        "--allow-external-output",
        "--include-unverified",
    ]
    subprocess.run(command, check=True, cwd=repo_root)

    payload = json.loads(output.read_text(encoding="utf-8"))
    schema = json.loads(
        (repo_root / "data" / "evidence" / "processed" / "claim_verification_matrix.schema.json").read_text(encoding="utf-8")
    )
    validate(payload, schema)
    assert payload["summary"]["included_claims"] >= 1


def test_hostile_review_excludes_weak_claims(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    manifest = tmp_path / "manifest.json"
    extracted_dir = tmp_path / "texts"
    output = tmp_path / "claim_verification_matrix.json"
    extracted_dir.mkdir()

    manifest.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "evidence_id": "PUB-2",
                        "title": "Dummy website copy",
                        "source_type": "corporate website",
                        "file_path": "broad_claim.txt",
                        "company_name": "Example Fabrication",
                        "corporate_speaker": "Example Fabrication",
                        "public_statement_context": "Marketing page"
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (extracted_dir / "broad_claim.txt").write_text(
        "We are committed to excellence everywhere.",
        encoding="utf-8",
    )

    command = [
        "python",
        str(repo_root / "scripts" / "claim_verifier_runner.py"),
        "--manifest",
        str(manifest),
        "--extracted-text",
        str(extracted_dir),
        "--output",
        str(output),
        "--allow-external-output",
        "--include-unverified",
        "--hostile-review",
    ]
    subprocess.run(command, check=True, cwd=repo_root)

    excluded = json.loads((tmp_path / "excluded_claims.json").read_text(encoding="utf-8"))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["included_claims"] == 0
    assert excluded["claims"]
