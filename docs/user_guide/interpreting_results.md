# Interpreting Results Guide

Understanding JLAW forensic dossier output.

## Dossier Structure

```
output/CompanyName_CIK_YEAR/
├── dossier_CompanyName_CIK_YEAR.json    # Complete report
├── summary_report.txt                    # Human-readable summary
├── evidence_chain/                       # Evidence integrity
│   ├── custody_log.json
│   ├── merkle_tree.json
│   └── timestamps/
└── node_reports/                         # Individual node outputs
    ├── node1_form4.json
    └── ...
```

## Key Metrics

### Violation Scores
- **High** (8-10): Likely violation, recommend investigation
- **Medium** (5-7): Suspicious pattern, requires review
- **Low** (1-4): Minor anomaly, may be explainable

### Evidence Chain
- **Merkle Root**: Single hash representing all evidence
- **Timestamp Tokens**: Cryptographic proof of acquisition time
- **Custody Log**: Complete provenance tracking

## Node Results

Each node returns:
- `violations_found`: Count of violations detected
- `violations`: List of specific violations with details
- `alerts`: Warning messages
- `findings`: Summary of analysis

---

See [15-Node Pipeline](../architecture/15_node_pipeline.md) for node descriptions.
