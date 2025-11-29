"""
Phase 1 Smoke Runner (CPU-friendly)
Runs the UniversalDocumentProcessor on a few tiny samples and writes
artifacts to forensic_storage/smoke/phase1/.

Usage:
  python scripts/smoke_phase1.py
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path


def _out_dir() -> Path:
    p = Path("forensic_storage") / "smoke" / "phase1"
    p.mkdir(parents=True, exist_ok=True)
    return p


async def run_samples() -> int:
    from src.forensics.enhanced_parsing import UniversalDocumentProcessor

    udp = UniversalDocumentProcessor()
    out = _out_dir()

    samples = {
        "plain_text": "Some plain text with a simple table\ncol1|col2\na|b\n1|2",
        "html_table": (
            "<html><body><table><tr><th>A</th><th>B</th></tr>"
            "<tr><td>10</td><td>20</td></tr></table></body></html>"
        ),
    }

    for name, content in samples.items():
        res = await udp.process(content)
        payload = {
            "text_length": len(res.text or ""),
            "tables": res.tables,
            "entities": res.entities,
            "confidence": res.confidence,
            "metadata": res.metadata,
        }
        (out / f"{name}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"Smoke outputs written to: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_samples()))
