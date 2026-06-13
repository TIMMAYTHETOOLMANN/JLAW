# Scripts

## Evidence Manifest Generation

Single input:
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

## Evidence Text Extraction

```bash
python scripts/extract_evidence_text.py \
  --input data/evidence/whistleblower_exhibits \
  --output data/evidence/processed/extracted_text
```

Optional OCR flag (default is off):
```bash
python scripts/extract_evidence_text.py \
  --input data/evidence/whistleblower_exhibits \
  --output data/evidence/processed/extracted_text \
  --ocr
```

## Local Evidence Workflow

See `data/evidence/LOCAL_EVIDENCE_WORKFLOW.md` for local-only handling, hash checks, and regulator packaging guidance.

## Troubleshooting

- `ERROR: input directory not found` → verify the `--input` path exists.
- Empty manifest/output → confirm files are present under the input directory.
- `.pdf` or `.docx` skipped → install optional dependencies (`pypdf`, `python-docx`).
- Unsupported file warnings are expected for non-supported extensions.
