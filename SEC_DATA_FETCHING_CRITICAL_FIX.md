

SEC Data Fetching — Critical Fix (v3)
=====================================

This document records the emergency hardening applied to the live SEC data acquisition layer to eliminate rate‑limit incidents, silent failures, and unreliable document retrieval. The new design is multi‑tier with intelligent rotation, strict rate limiting, circuit breakers, health monitoring, and cache‑first logic.

Key Objectives
- Prevent rate‑limit breaches and cascading failures
- Eliminate silent failures (no more hidden None/empty content on total failure)
- Ensure documents are acquired reliably via multiple SEC endpoints
- Preserve backward compatibility for core flows

What Changed (High Level)
- Multi‑Tier Fetcher hardening (src/forensics/multi_tier_sec_fetcher.py)
  - Honor Retry‑After on 429/503, exponential backoff with jitter, per‑tier limits
  - Circuit breaker states maintained per tier (closed/open/half‑open), self‑healing
  - New SECFetchError for strict failure semantics in critical paths
  - New fetch_strict() and raise_on_failure option to prevent silent failures
  - Cache‑first, deduplication for concurrent requests, health report API
- RealSECDataFetcher integration (src/forensics/real_sec_data_fetcher.py)
  - Strict JSON fetch path: raises on total failure; legacy fallback honors Retry‑After
  - Filing content retrieval tries multiple URLs and now raises SECFetchError if all attempts fail (no empty string fallback)
  - Fixed logger init ordering bug

Tiers (active today)
1) EDGAR API (data.sec.gov): JSON submissions, company facts
2) Archives (www.sec.gov/Archives): primary document retrieval
3) Browse (www.sec.gov/cgi-bin/browse-edgar): discovery support

Notes on GovInfo / EFTS
- GovInfo does not host EDGAR filings; therefore not used for live filing content. We keep it as a potential ancillary source for federal documents unrelated to filings.
- EFTS/bulk endpoints are not suitable for low‑latency per‑document retrieval; can be added later behind a feature flag for batch workflows.

Rate Limiting
- Per‑tier token buckets with conservative ceilings: EDGAR API 6 rps, Archives 6 rps, Browse 5 rps
- Connector limits per host to avoid connection storms
- 429/503 handling: Retry‑After respected (seconds or http‑date), fallback to capped exponential backoff (<= 90s)

Failure Semantics
- Critical paths use strict mode: raise SECFetchError with an attempts summary (tier, retries, last status) instead of returning None/""
- Legacy non‑strict calls continue returning None to maintain compatibility where needed

Caching
- Cache directory: forensic_storage/sec_cache_v3 (multi‑tier) and forensic_storage/sec_cache (legacy)
- Submissions freshness policy: 1 hour; other content: 24 hours default
- Request deduplication prevents stampedes under concurrency

Monitoring
- Health report API via MultiTierSECFetcher.get_health_report()
- Stats include total requests, cache hits/misses, failovers, rate‑limit hits, tier usage

How to Verify
1) Run the verification suite:
   - python verify_multi_tier_sec.py
   - Inspect health report and ensure no unhandled exceptions; verify failover trials
2) Quick Start demos:
   - python quick_start_multi_tier_sec.py (examples 1–6)
3) Observe logs for: Retry‑After backoffs, circuit transitions, `SECFetchError` surfaces on hard failures

Operational Guidance
- Provide a valid SEC‑compliant User‑Agent with contact info (already configured)
- If the workload spikes, prefer batch scheduling with NORMAL/LOW priority
- Avoid hot‑loop re‑requests on failures; allow the circuit breaker to recover

Future Work (optional)
- Add feature‑flagged EFTS or bulk index ingestion for historical backfills
- Consider a small, managed proxy queue for smoothing bursts if workload increases

Files Touched
- src/forensics/multi_tier_sec_fetcher.py
- src/forensics/real_sec_data_fetcher.py

Change Date
- 2025‑12‑07

Post‑fix Verification (v3)
--------------------------

Runbook and outcomes for the hardened multi‑tier fetcher as deployed on 2025‑12‑07.

How we verified
1) Full verification suite:
   - Command: `python verify_multi_tier_sec.py`
   - Result: 7/7 tests passed (Basic Fetch, Multi‑Tier Failover, Rate Limiting, Caching, Health Monitoring, RealSECDataFetcher Integration, Document Fetching)

2) Health snapshot capture:
   - Command: `python scripts/gen_health_snapshot.py`
   - Artifact: `forensic_reports/multi_tier_health_report_<timestamp>.json`
   - Expected: Non‑zero requests, reasonable cache hits, health scores ≥ 0.7 under normal conditions

3) Targeted tests (smoke):
   - `pytest -q test_sec_connection.py` (connection sanity)
   - `pytest -q test_single_filing.py` (skips if `GOVINFO_API_KEY` not configured)

4) 2019 NIKE re‑analysis (hardened env):
   - Command: `python jlaw_forensic.py --ticker NKE --year 2019 --verbose --output-dir output`
   - Result: Completed with full coverage; artifacts written under `output/`

Artifacts
- Health report JSON: `forensic_reports/multi_tier_health_report_YYYYMMDD_HHMMSS.json`
- Verification console log (optional to capture): `forensic_reports/multi_tier_verification_YYYYMMDD_HHMMSS.log`
- NIKE 2019 artifact diff report: `forensic_reports/artifact_diff_YYYYMMDD_HHMMSS.md`

Acceptance checklist (v3)
- [x] Dependencies install with no errors; NumPy pinned `< 2.0` (1.26.4)
- [x] `verify_multi_tier_sec.py` passes 7/7
- [x] Health report shows sane stats; cache and failover numbers reasonable
- [x] NIKE 2019 analysis completes with full coverage; artifacts validated by diff
- [x] Docs updated with non‑interactive run recipe and verification guidance
