"""
Dual-Agent Smoke Test (CPU-friendly)
Runs a short analysis using DualAgentCoordinator on a tiny text sample.

Artifacts are written under:
  forensic_storage/smoke/dual_agents/

Usage:
  python scripts/smoke_dual_agents.py
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path


OUT_DIR = Path("forensic_storage") / "smoke" / "dual_agents"


async def run() -> int:
    from src.forensics.dual_agent import DualAgentCoordinator

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = (
        "On March 3, 2019, the officer sold 10,000 shares at $0.00 per share. "
        "The Form 4 was filed on March 10, 2019."
    )

    coord = DualAgentCoordinator()
    availability = coord.availability()
    res = await coord.analyze_text(text, context={"filing_type": "TEXT"})

    (OUT_DIR / "availability.json").write_text(
        json.dumps(availability, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "result.json").write_text(
        json.dumps(res, indent=2), encoding="utf-8"
    )

    print(f"Smoke outputs written to: {OUT_DIR}")
    # Exit code: 0 normally; if strict dual is desired, caller can inspect result.json
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
