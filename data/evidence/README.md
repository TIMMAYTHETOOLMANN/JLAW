# Evidence Directory

This directory is the primary evidence workspace for the JLAW forensic analysis platform.

## Subdirectory Guide

| Directory | Purpose |
|-----------|---------|
| `raw/` | Original, unmodified source documents as obtained. Do not alter files placed here. |
| `processed/` | Structured analytical outputs including claim verification matrices and scored findings. |
| `sec_filings/` | SEC EDGAR filings (10-K, 10-Q, DEF 14A, Form 4, 8-K, ESG disclosures, etc.). |
| `whistleblower_exhibits/` | Exhibits submitted by or on behalf of whistleblowers. Handle with strict confidentiality. |
| `vendor_subpoena_targets/` | Documentation and target lists related to third-party records requests. |
| `generated_reports/` | Forensic dossiers and analysis reports produced by the JLAW engine. |
| `chain_of_custody/` | Evidence manifests, integrity records, and schema definitions. |

## Chain-of-Custody Discipline

Every piece of evidence added to this directory should be registered in the evidence manifest (`chain_of_custody/evidence_manifest.template.json`). Required fields include:

- Unique evidence ID
- SHA-256 hash of the file
- Source origin and acquisition date
- Custodian name
- Confidentiality level

## Analytical Standards

- Separate verified documentary evidence from firsthand testimony, inference, and speculation.
- Do not summarize unverified allegations as established facts.
- Use the claim verification matrix (`processed/claim_verification_matrix.template.json`) to score and track claims before reporting.
- Apply the investigative language guide (`docs/reporting/INVESTIGATIVE_LANGUAGE_GUIDE.md`) when drafting any narrative.
