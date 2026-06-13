# Local Evidence Workflow (Local-Only by Default)

## Place evidence files
- SEC filings: `data/evidence/sec_filings/`
- Whistleblower exhibits: `data/evidence/whistleblower_exhibits/`
- Generated reports (local outputs): `data/evidence/generated_reports/`
- Other raw source files: `data/evidence/raw/`

## Build a manifest
```bash
python scripts/evidence_manifest_builder.py \
  --input data/evidence/raw \
  --output data/evidence/processed/manifests/raw_manifest.json
```

Multiple inputs:
```bash
python scripts/evidence_manifest_builder.py \
  --input data/evidence/raw \
  --input data/evidence/sec_filings \
  --input data/evidence/whistleblower_exhibits \
  --output data/evidence/processed/manifests/master_manifest.json
```

## Verify hashes
1. Run the manifest builder.
2. Re-run the builder and compare `hash_sha256` values.
3. For one file spot-check manually:
```bash
python - <<'PY'
import hashlib
from pathlib import Path
p = Path("data/evidence/raw/README.md")
print(hashlib.sha256(p.read_bytes()).hexdigest())
PY
```

## Text extraction
```bash
python scripts/extract_evidence_text.py \
  --input data/evidence/whistleblower_exhibits \
  --output data/evidence/processed/extracted_text
```

## Keep evidence local-only
- Raw evidence paths are Git-ignored by default in `.gitignore`.
- Commit only tooling, schemas, templates, and dummy examples.
- Never commit confidential files unless explicitly authorized.

## Packaging for regulators (outside Git)
- Export evidence from local storage into an encrypted archive.
- Include manifests and hash logs with the archive.
- Share through approved secure channels only (not Git history).
