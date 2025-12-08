# Quick Start — JLAW Unified Forensic System (NIKE 2019 example)

Status: Operational & Verified (Multi‑Tier Fetcher 7/7 pass)

## 1) Install dependencies

```powershell
pip install -r requirements.txt
```

Notes:
- NumPy is pinned to `< 2.0` (currently `1.26.4`) to avoid ABI warnings.
- No external Benford dependency required; internal analyzer is used.

## 2) Run verifications (recommended)

```powershell
python verify_api_keys.py
python verify_multi_tier_sec.py   # Expect 7/7 PASS
python scripts/gen_health_snapshot.py
```

Artifacts are saved to `forensic_reports/`.

## 3) Run the unified analysis (NIKE 2019)

Option A — One‑click, interactive:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\one_click_analyze.ps1
```

Option B — One‑click, non‑interactive (no prompts):

```powershell
PowerShell -ExecutionPolicy Bypass -File .\one_click_analyze.ps1 -Ticker NKE -Year 2019 -OutputDir output -Verbose
```

Option C — Direct Python entrypoint:

```powershell
python jlaw_forensic.py --ticker NKE --year 2019 --verbose --output-dir output
```

Expected: 100% filing coverage, full report stack under `output/NIKE_..._FORENSIC_ANALYSIS_<timestamp>/`.

## 4) Inspect outputs

- Human report: `FORENSIC_REPORT.md`
- Machine data (JSON): `machine_readable/`
- Evidence: `evidence/` (with chain‑of‑custody)

## 5) Troubleshooting

- Ensure SEC‑compliant `User‑Agent` is set (handled by code by default).
- If network is constrained, re‑run after cache warms; cache at `forensic_storage/sec_cache_v3`.
- For GovInfo‑dependent tests, set `GOVINFO_API_KEY` or tests will skip.
