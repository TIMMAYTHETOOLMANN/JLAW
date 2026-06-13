# Claim Verification Engine

## Purpose

Phase 4 adds a deterministic claim-verification layer that compares public corporate claims against locally ingested evidence and produces a structured contradiction matrix.

This phase does **not** generate a final investigative article, accusations, or conclusions of wrongdoing.

## Local-Only Evidence Warning

Real evidence, extracted text, manifests, and generated analytical outputs derived from real evidence must remain local-only and Git-ignored.

## Inputs

- Evidence manifest JSON
- Extracted text directory with local text files
- Optional sample mode for dummy data only

## Commands

```bash
python scripts/claim_verifier_runner.py           --manifest data/evidence/processed/manifests/master_manifest.json           --extracted-text data/evidence/processed/extracted_text           --output data/evidence/processed/claim_outputs/claim_verification_matrix.json
```

Optional flags:

- `--public-claims-only`
- `--min-confidence 3`
- `--include-unverified`
- `--dry-run`
- `--sample`
- `--hostile-review`
- `--allow-external-output`

## Confidence Scale

- `5` = direct documentary contradiction
- `4` = documentary support plus firsthand corroboration
- `3` = firsthand testimony plus circumstantial support
- `2` = plausible lead requiring records
- `1` = weak/speculative; do not include in final report
- `0` = unrelated or unusable

## Hostile Review

Hostile review mode excludes claims when the contradiction is speculative, the source is unclear, the evidence lacks provenance, the claim is overly broad, the language overstates the record, or subpoenaed records are still needed before safe use.

## Outputs

- `data/evidence/processed/claim_verification_matrix.schema.json`
- `data/evidence/processed/claim_outputs/claim_verification_matrix.json` (local-only runtime output)
- `data/evidence/processed/claim_outputs/verification_hitlist.json` (local-only runtime output)
- `data/evidence/processed/claim_outputs/excluded_claims.json` (hostile-review runtime output)
- committed dummy sample outputs under `data/evidence/processed/claim_outputs/`

## Later Narrative Generation Support

The matrix is the control layer for later narrative work. Downstream investigative writing should consume the deterministic matrix, hit list, and excluded-claim output before reviewing raw evidence.
