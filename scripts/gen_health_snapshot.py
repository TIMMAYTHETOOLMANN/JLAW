#!/usr/bin/env python3
"""
Generate a real-time Multi-Tier SEC Fetcher health report snapshot.

This script performs a single submissions fetch (Nike CIK by default) to
exercise the fetcher and then writes the health report JSON to
forensic_reports/multi_tier_health_report_<timestamp>.json.

Usage (PowerShell):
  python scripts/gen_health_snapshot.py
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from pathlib import Path as _Path

# Ensure project root is on sys.path so `src` package is importable when run from scripts/
PROJECT_ROOT = _Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.forensics.multi_tier_sec_fetcher import MultiTierSECFetcher


async def main():
    out_dir = Path("forensic_reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    async with MultiTierSECFetcher() as fetcher:
        # Exercise the fetcher with a simple call
        await fetcher.fetch_company_submissions("0000320187")  # Nike

        health = fetcher.get_health_report()
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"multi_tier_health_report_{ts}.json"
        out_path.write_text(json.dumps(health, indent=2), encoding="utf-8")
        print(str(out_path))


if __name__ == "__main__":
    asyncio.run(main())
