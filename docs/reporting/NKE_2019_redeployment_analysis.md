# NKE 2019 Full Pipeline Redeployment Analysis (Post-Purge)

## Execution scope

- Target: **NKE**
- CIK: **0000320187**
- Period: **2019-01-01 → 2019-12-31**
- Mode: **forensic + strict + auto**
- Output path used for this redeployment: `runtime_output/`

## Purge action completed

Prior analysis artifacts were purged before rerun (operationally) and the pipeline was redeployed against NKE 2019.

## Pipeline execution result

The 11-phase pipeline completed successfully end-to-end after hardening node initialization fallback.

- ✅ phase_1
- ✅ phase_2
- ✅ phase_3
- ✅ phase_4
- ✅ phase_5
- ⚠️ phase_6 (no violations available for escalation)
- ✅ phase_7
- ✅ phase_8
- ✅ phase_9
- ✅ phase_10
- ✅ phase_11

## Output document inventory (redeployment run)

- `runtime_output/bundle/analysis_results.json`
- `runtime_output/node5_irs/irc83_analysis_*.json`
- `runtime_output/reports/FORENSIC_DOSSIER_CASE-0000320187-*.pdf`

## Output document analysis

### 1) `analysis_results.json`

Observed key facts:

- `total_violations`: **0**
- `critical_alerts`: **0**
- `high_alerts`: **0**
- `regulatory_routing`: `SEC=False`, `DOJ=False`, `IRS=False`
- `estimated_penalties`: all **0** with no criminal exposure
- Executive summary text marks case as **INSUFFICIENT - No actionable violations**

### 2) Node 5 tax output (`irc83_analysis_*.json`)

- Grants analyzed: **0**
- Violations detected: **0**
- Total tax exposure: **0**
- Total penalty exposure: **0**

### 3) Forensic dossier PDF

- File generated successfully
- Approximate size: **10 KB**
- Charts generated: **0** (reflects no underlying extracted evidence stream)

## Root-cause constraints impacting evidence yield

1. **SEC endpoint access blocked in this runtime**
   - `https://data.sec.gov/submissions/CIK0000320187.json` returned **403 Forbidden** via `http://proxy:8080`.
2. **Web-intelligence SEC searches also blocked**
   - `efts.sec.gov` requests returned **403 Forbidden**.
3. **Optional dependency gaps degrade enrichment depth**
   - DeBERTa stack unavailable (`transformers/torch`) and some market/graph dependencies absent.

Because ingestion returned effectively zero source material, downstream detection and visual sections remained sparse.

## Hardening implemented during redeployment

A fatal initialization defect was fixed so pipeline execution no longer aborts when Node 9 V2 is unavailable:

- `MaterialEventCorrelatorV2` now safely falls back to `MaterialEventCorrelator` (V1) in `RecursiveProsecutorialEngine._init_nodes`.

This converted the run from **hard failure** to **complete execution with explicit environmental warnings**.

## Recommended next step to obtain substantive NKE 2019 findings

To produce meaningful violations/visuals/statutory routing (Nike baseline quality), rerun in an environment with:

- SEC access allowed (no 403 through proxy), and
- optional NLP/market dependencies installed where required.

Then re-run the same command used here and compare:

```bash
SEC_USER_AGENT='JLAW Research Bot (research@forensicanalysis.edu)' \
SEC_EMAIL='research@forensicanalysis.edu' \
PYTHONPATH=. python jlaw_cli.py \
  --cik 0000320187 --company "NKE" --year 2019 \
  --mode forensic --strict --auto --output-dir runtime_output --verbose
```
