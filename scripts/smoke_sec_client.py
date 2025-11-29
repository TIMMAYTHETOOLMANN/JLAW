"""
SEC EDGAR Client Smoke (CPU-friendly)
Runs a tiny fetch using the Phase 2 SecClient:
 - Get company submissions JSON
 - List recent filings filtered to 10-K/8-K
 - Download the primary document for the first returned filing

Artifacts are written under:
  forensic_storage/smoke/sec_client/

Usage:
  python scripts/smoke_sec_client.py [CIK]

If CIK is omitted, uses Apple Inc (0000320193) as a small, well-cached example.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional


OUT_DIR = Path("forensic_storage") / "smoke" / "sec_client"


async def run(cik: str) -> int:
    from src.intelligence_gathering import SecClient

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sc = SecClient()

    # Submissions
    subs = await sc.get_company_submissions(cik)
    (OUT_DIR / f"{cik}_submissions.json").write_text(
        json.dumps(subs, indent=2), encoding="utf-8"
    )

    # Filings (10-K/8-K limited)
    filings = await sc.list_filings(cik, form_types=["10-K", "8-K"], limit=5)
    (OUT_DIR / f"{cik}_filings.json").write_text(
        json.dumps(filings, indent=2), encoding="utf-8"
    )

    if filings:
        f0 = filings[0]
        try:
            path = await sc.download_primary_document(
                cik=cik,
                accession=f0["accession"],
                primary_document=f0["primary_document"],
            )
            # Copy a small excerpt to smoke dir for easy inspection
            content = Path(path).read_text(encoding="utf-8", errors="ignore")
            (OUT_DIR / f"{cik}_doc_excerpt.txt").write_text(content[:2000], encoding="utf-8")
        except Exception as e:
            (OUT_DIR / f"{cik}_download_error.txt").write_text(str(e), encoding="utf-8")

    print(f"Smoke outputs written to: {OUT_DIR}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    cik = argv[0] if argv else "0000320193"  # Apple Inc by default
    return asyncio.run(run(cik))


if __name__ == "__main__":
    raise SystemExit(main())
