# Forensic Output Documentation Configuration (v2.0)

## Why this overhaul exists

The prior output strategy was format-centric (PDF/JSON/Markdown) but did not enforce a **single documentation profile** tying together:

- baseline legal sections,
- visual evidence requirements,
- quality gates,
- and machine-readable delivery governance.

This document defines that control plane and aligns directly with:

1. `HOLY_GRAIL_PIPELINE.md`
2. NIKE 2019 baseline expectations in `src/reporting/constants.py`

## New control plane

The canonical profile now lives in:

- `src/reporting/output_documentation_config.py`

And is consumed by:

- `src/reporting/doj_report_generator.py`

### Profile id

`JLAW-FORENSIC-OUTPUT-DOCCONFIG` version `2.0`

### Reference standard

- NIKE 2019 baseline dossier expectations
- HOLY_GRAIL pipeline detail density and prosecutorial posture

## Required sections (enforced baseline)

1. Executive Summary
2. Per-Filing Analysis
3. Violation Details with Statutory Citations
4. Dual-Agent Consensus
5. Evidence Chain
6. Financial Impact Assessment
7. Regulatory Routing Recommendations

## Visual representation matrix

The profile now declares mandatory visual categories:

- Severity distribution
- Transaction timeline
- Beneficiary profit waterfall
- Actor relationship network

These are exposed in the reports as a **Visual Representation Matrix** so missing visuals are explicit rather than silently omitted.

## Quality gates

Current minimum thresholds:

- ≥ 1 exact quote per violation
- ≥ 1 statutory citation per violation
- chain-of-custody records required
- dual-agent validation required
- minimum confidence target of 0.70

## Output manifest (new)

Every DOJ report run now emits a companion:

- `*.manifest.json`

It provides:

- generated files,
- profile metadata,
- section coverage summary,
- quantitative quality metrics,
- visual representation requirements.

This gives downstream automation and reviewers a deterministic source of truth for report completeness.

## Markdown / JSON enhancements

### Markdown

Now includes an `OUTPUT DOCUMENTATION CONTROL PLANE` section with:

- required section definitions,
- visual status matrix,
- quality gate snapshot.

### JSON

`metadata` now embeds the active documentation profile to ensure provenance and reproducibility.

## Operational guidance

When modifying reporting outputs, always change profile and generators together:

1. Update `output_documentation_config.py`.
2. Ensure `doj_report_generator.py` reflects new fields/sections.
3. Add tests validating profile integrity and manifest generation.

This prevents format drift and preserves NIKE 2019 + HOLY_GRAIL alignment.
