# Forensic Output Documentation Configuration (v3.0)

## Why This Overhaul Exists

The prior output strategy was format-centric (PDF/JSON/Markdown) but did not enforce a
**single documentation profile** tying together:

- baseline legal sections aligned to the 9-phase pipeline,
- visual evidence requirements mapped to every visualization module,
- quality gates with quantitative thresholds,
- compliance standards (FRE 902, NIST SP 800-86, ISO 27037, RFC 3161/6962),
- output file manifest requirements,
- and pipeline stage audit expectations.

This document defines that control plane and aligns directly with:

1. `HOLY_GRAIL_PIPELINE.md` — the master 15-node pipeline specification
2. NIKE 2019 baseline expectations in `src/reporting/constants.py`

---

## Canonical Profile Location

| Artifact | Path |
|----------|------|
| Profile definition | `src/reporting/output_documentation_config.py` |
| Primary consumer | `src/reporting/doj_report_generator.py` |
| PDF dossier consumer | `src/reporting/forensic_dossier.py` |
| Visual report consumer | `src/reporting/visual_report_generator.py` |

### Profile ID

`JLAW-FORENSIC-OUTPUT-DOCCONFIG` version **3.0**

### Reference Standards

- NIKE 2019 baseline dossier expectations
- HOLY\_GRAIL pipeline detail density and prosecutorial posture

---

## Required Sections (15 — aligned to 9-phase pipeline)

| # | Section | Objective | Pipeline Phase |
|---|---------|-----------|----------------|
| 1 | Executive Summary | Lead with findings, threat level, routing, and confidence | Phase 9 |
| 2 | Target Company Profile | Company identity, CIK, ticker, filing history, analysis window | Phase 1 |
| 3 | Per-Filing Analysis | Filing-granular evidence with accession numbers and exact quotes | Phase 2/3 |
| 4 | Violation Details with Statutory Citations | Bind violations to legal authority and penalties | Phase 4 |
| 5 | Detection Pattern Analysis | Results from 23 detection algorithms with accuracy and matches | Phase 5 |
| 6 | Dual-Agent Consensus | AI corroboration, disagreements, and agreement ratio | Phase 6 |
| 7 | Subagent Specialized Findings | Deep-dive results from 10 Claude forensic subagents | Phase 7 |
| 8 | Contradiction Analysis | Discrepancies between public claims and SEC findings | Phase 4 (cross-node) |
| 9 | Financial Impact Assessment | Civil/criminal exposure, disgorgement, prejudgment interest | Phase 4 (Nodes 13-14) |
| 10 | Penalty Assessment Matrix | Per-violation and aggregate penalty estimates with statutory authority | Phase 9 |
| 11 | Regulatory Routing Recommendations | SEC/DOJ/IRS referral with rationale and priority ordering | Phase 4 (Node 6) |
| 12 | Evidence Chain & Integrity Verification | Triple-hash provenance (SHA-256 + SHA3-512 + BLAKE2b) and Merkle root | Phase 8 |
| 13 | Pipeline Execution Audit | 9-phase timing, gate results, node success rates, exit code | Phases 1-9 |
| 14 | Compliance Standards Declaration | FRE 902(13)/(14), NIST SP 800-86, ISO 27037, RFC 3161/6962 adherence | Phase 8 |
| 15 | Appendices & Exhibits | Standalone charts, source document inventories, methodology references | Phase 9 |

---

## Visual Representation Matrix (8 visuals)

The profile now declares **8 mandatory visual categories** mapped to the visualization
modules in `src/reporting/visualizations/`:

| Visual | Generator Module | Purpose |
|--------|------------------|---------|
| Severity distribution chart | embedded matplotlib | Case posture and enforcement urgency |
| Transaction timeline | `timeline_generator` | Sequence linkage between transactions and events |
| Beneficiary profit waterfall | `beneficiary_profit_chart` | Concentration of gains for disgorgement |
| Actor relationship network | `network_graph` | Coordination, board interlocks, control paths |
| Filing compliance heatmap | `heat_map` | Temporal filing patterns and deadline adherence |
| Comparative bubble chart | `bubble_chart` | Multi-dimensional severity/frequency/impact |
| Filing deadline compliance | `filing_deadline_chart` | SEC filing deadline compliance patterns |
| Merkle tree evidence | `merkle_tree_viz` | RFC 6962 evidence integrity tree for court |

Missing visuals are explicitly flagged in the report's **Visual Representation Matrix**
rather than silently omitted.

---

## Quality Gates (12 thresholds)

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| Exact quotes per violation | ≥ 1 | Direct evidence from source document |
| Statutory citations per violation | ≥ 1 | Legal authority binding |
| Chain of custody records | Required | FRE 902 compliance |
| Evidence hash algorithms | 3 | SHA-256 + SHA3-512 + BLAKE2b |
| Dual-agent validation | Required | Cross-AI corroboration |
| Minimum overall confidence | 0.70 | Prosecutorial threshold |
| Minimum pipeline phases completed | 7 | Coverage assurance |
| Minimum node success rate | 80% | 12/15 nodes |
| Minimum detection patterns executed | 20 | 20/23 patterns |
| Minimum filings analyzed | 5 | Evidence breadth |
| Compliance standards referenced | 4 | FRE 902 + NIST + ISO + RFC 3161 |
| Required output files | 5 | MD + JSON + PDF + manifest + analysis_results |

---

## Compliance Standards (6)

| Standard | Description |
|----------|-------------|
| FRE 902(13) | Self-authentication via qualified person certification |
| FRE 902(14) | Forensic copies with hash value verification |
| NIST SP 800-86 | Digital forensics collection, examination, analysis, reporting |
| ISO/IEC 27037 | Digital evidence collection and preservation |
| RFC 3161 | Trusted timestamping protocol |
| RFC 6962 | Merkle tree construction for evidence integrity |

---

## Output File Requirements

| File Key | Format | Required | Description |
|----------|--------|----------|-------------|
| markdown\_report | `.md` | ✓ | Human-readable forensic dossier |
| json\_report | `.json` | ✓ | Machine-readable structured dossier |
| pdf\_dossier | `.pdf` | ✓ | Court-ready PDF with embedded charts |
| output\_manifest | `.manifest.json` | ✓ | Documentation governance manifest |
| analysis\_results | `.json` | ✓ | Raw analysis results bundle |
| chart\_severity | `.png` | ○ | Severity distribution chart |
| chart\_timeline | `.png` | ○ | Transaction timeline chart |
| chart\_network | `.png` | ○ | Actor relationship network |
| chart\_beneficiary | `.png` | ○ | Beneficiary profit waterfall |

---

## Pipeline Stage Audit Expectations

| Stage | Name | Gate | Exit Code |
|-------|------|------|-----------|
| 1 | Configuration & Target Acquisition | SEC API config valid, 6+ modules loaded | 1 |
| 2 | SEC EDGAR Data Collection | Minimum 5 filings collected | 2 |
| 3 | Document Parsing & Indexing | 80% documents parsed successfully | 3 |
| 4 | 15-Node Recursive Analysis | 12/15 nodes successful (80%) | 4 |
| 5 | Advanced Detection Patterns | 20/23 patterns executed (87%) | 5 |
| 6 | Dual-Agent AI Cross-Validation | At least 1 AI agent responsive | 0 |
| 7 | Subagent Orchestration | Subagent results collected | 0 |
| 8 | Evidence Chain Finalization | 100% hash match, Merkle root computed | 6 |
| 9 | DOJ-Grade Dossier Generation | Report generated successfully | 7 |

---

## Output Manifest (enhanced)

Every DOJ report run emits a companion `*.manifest.json` containing:

- **Documentation profile**: Full v3.0 profile with all sections, visuals, thresholds
- **Coverage**: Required sections list with section numbers, files generated, filing/custody counts
- **Quality metrics**: Per-violation quote/citation ratios, confidence, filing count, violation count
- **Visual representation**: All 8 visuals with generator module and output formats
- **Compliance standards**: Referenced standards with IDs and titles
- **Pipeline stage audits**: Gate expectations per phase

---

## Markdown / JSON Enhancements (v3.0)

### Markdown

Now includes:

- **Documentation Profile header** with version identifier
- **OUTPUT DOCUMENTATION CONTROL PLANE** with required section table (numbered), visual matrix (with generator modules), quality gate snapshot, compliance standards table, and pipeline gate requirements table
- **DETECTION PATTERN ANALYSIS** section covering 23 algorithms
- **PENALTY ASSESSMENT MATRIX** with per-violation statutory authority
- **COMPLIANCE STANDARDS DECLARATION** with all referenced frameworks

### JSON

`metadata` now embeds:

- Full v3.0 documentation profile
- `compliance_standards` array with standard IDs and descriptions
- `pipeline_stage_audits` array with gate expectations and exit codes

---

## Operational Guidance

When modifying reporting outputs, always change profile and generators together:

1. Update `output_documentation_config.py`
2. Ensure `doj_report_generator.py` reflects new fields/sections
3. Verify `forensic_dossier.py` and `visual_report_generator.py` remain compatible
4. Add tests validating profile integrity and manifest generation
5. Update this document to reflect changes

This prevents format drift and preserves NIKE 2019 + HOLY\_GRAIL alignment.

---

## Data Classes Reference

| Class | Purpose |
|-------|---------|
| `SectionRequirement` | Required doc section (name, objective, minimum fields, section number, phase alignment) |
| `VisualRequirement` | Required visual artifact (key, title, rationale, generator module, output formats) |
| `ComplianceStandard` | Referenced legal/technical standard (ID, title, description, applicable sections) |
| `OutputFileRequirement` | Expected output file (key, description, format, required flag) |
| `PipelineStageAudit` | Pipeline stage gate (stage number, name, gate description, failure exit code) |
| `DocumentationProfile` | Top-level profile aggregating all of the above |
