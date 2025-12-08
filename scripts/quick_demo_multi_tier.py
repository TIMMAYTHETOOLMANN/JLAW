#!/usr/bin/env python3
"""
Quick Demo Runner (short, non-blocking)

Purpose:
- Exercise the Multi-Tier SEC Fetcher briefly without long network runs.
- Fetches Nike (CIK 0000320187) submissions and tries to retrieve one
  known 2019 filing document with strict timeouts.

Outputs:
- Writes a short textual summary to forensic_reports/quick_demo_<timestamp>.txt

Usage:
  python scripts/quick_demo_multi_tier.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root on sys.path so `src` is importable when run from scripts/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.forensics.multi_tier_sec_fetcher import MultiTierSECFetcher


async def main() -> Path:
    out_dir = Path("forensic_reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"quick_demo_{ts}.txt"

    lines = []
    lines.append("=== Quick Demo: Multi-Tier SEC Fetcher ===")
    lines.append(f"Timestamp: {datetime.utcnow().isoformat()}")

    # Known Nike identifiers
    cik_str = "0000320187"  # Nike
    accession = "0000320187-19-000113"  # Known 2019 accession (10-K/Q set)

    async with MultiTierSECFetcher() as fetcher:
        # Submissions fetch (bounded by overall script runtime, internal rate limiting applies)
        subs = await fetcher.fetch_company_submissions(cik_str)
        if subs:
            company = subs.get("name") or "Unknown"
            recent = (subs.get("filings") or {}).get("recent") or {}
            forms = recent.get("form", []) if isinstance(recent.get("form", []), list) else []
            lines.append(f"Company: {company}")
            lines.append(f"Recent filings listed: {len(forms)}")
        else:
            lines.append("[WARN] Submissions fetch returned no data")

        # index.json for a specific accession
        try:
            idx = await asyncio.wait_for(fetcher.fetch_filing_index("320187", accession), timeout=20)
        except asyncio.TimeoutError:
            idx = None
            lines.append("[WARN] index.json fetch timed out")
        except Exception as e:
            idx = None
            lines.append(f"[WARN] index.json fetch error: {e}")

        chosen_doc = None
        if idx:
            items = (idx.get("directory") or {}).get("item", [])
            lines.append(f"index.json items: {len(items)}")
            # Pick first .htm/.html if present
            for it in items:
                n = (it.get("name") or "").lower()
                if n.endswith(".htm") or n.endswith(".html"):
                    chosen_doc = it.get("name")
                    break
            # Fallback: first item
            if not chosen_doc and items:
                chosen_doc = items[0].get("name")
        else:
            lines.append("[WARN] No index available to select a document")

        if chosen_doc:
            lines.append(f"Selected document: {chosen_doc}")
            try:
                content = await asyncio.wait_for(
                    fetcher.fetch_filing_document("320187", accession, chosen_doc), timeout=25
                )
                if content:
                    preview = content[:200].replace("\n", " ").replace("\r", " ")
                    lines.append(f"Fetched content bytes: {len(content)}")
                    lines.append(f"Preview: {preview}")
                else:
                    lines.append("[WARN] Document fetch returned empty content")
            except asyncio.TimeoutError:
                lines.append("[WARN] Document fetch timed out")
            except Exception as e:
                lines.append(f"[WARN] Document fetch error: {e}")
        else:
            lines.append("[WARN] No document selected from index")

        # Health report snapshot
        health = fetcher.get_health_report()
        stats = health.get("statistics", {})
        lines.append("")
        lines.append("Health summary:")
        lines.append(json.dumps({
            "total_requests": stats.get("total_requests"),
            "cache_hits": stats.get("cache_hits"),
            "failovers": stats.get("failovers"),
            "rate_limit_hits": stats.get("rate_limit_hits"),
        }, indent=2))

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out_path))
    return out_path


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
