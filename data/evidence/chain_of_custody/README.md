# Chain of Custody

This directory contains the evidence manifest schema, templates, and integrity records for all evidence items tracked by this investigation.

## Files

| File | Purpose |
|------|---------|
| `evidence_manifest.schema.json` | JSON Schema defining the structure of an evidence record |
| `evidence_manifest.template.json` | Blank template for registering a new evidence item |

## Chain-of-Custody Discipline

Every piece of evidence used in any claim verification or analytical report must be registered here. Registration requires:

1. A unique `evidence_id` assigned at intake.
2. A `hash_sha256` computed from the file at the time of acquisition.
3. A `custodian` name and `date_obtained` entry.
4. A `confidentiality_level` designation.

Do not modify a registered file after hashing. If analysis requires annotation, copy the file to `processed/` and register the annotated version as a derivative with a reference to the original `evidence_id`.

## Verification

To verify file integrity after acquisition:

```bash
sha256sum <file>
```

Compare the output against the `hash_sha256` field in the manifest. Any mismatch indicates the file has been altered since intake and must be investigated before use.
