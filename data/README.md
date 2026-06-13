# Data Directory

This directory holds all evidence packages, forensic outputs, and structured data used by the JLAW investigative analysis platform.

## Structure

```
data/
  evidence/           — primary evidence workspace
    raw/              — original, unmodified source documents
    processed/        — structured analysis outputs and claim verification data
    sec_filings/      — SEC EDGAR filings retrieved for analysis
    whistleblower_exhibits/  — exhibits submitted by or on behalf of whistleblowers
    vendor_subpoena_targets/ — documentation related to vendor records requests
    generated_reports/       — forensic dossiers and analysis reports produced by the engine
    chain_of_custody/        — evidence manifests and integrity records
```

## Important Notes

- Do not add real evidence files to this repository without authorization.
- All files placed here should be listed in an evidence manifest (`chain_of_custody/evidence_manifest.template.json`).
- Confidential materials must be labeled with the appropriate `confidentiality_level` in the manifest.
- No allegations should be treated as established facts until supported by documentary evidence and independent verification.
