#!/usr/bin/env python3
"""
Artifact Diff Generator for NIKE 2019 Analysis

Finds the two most recent NIKE_2019_FORENSIC_ANALYSIS_*.json (and .md if present)
in the project root and produces a summary diff report under:
  forensic_reports/artifact_diff_<timestamp>.md

The report compares key headline metrics when available, and falls back to
simple file size and hash comparisons when the schema differs.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "forensic_reports"


def sha256_text(p: Path) -> str:
    try:
        data = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        data = p.read_bytes().decode("utf-8", errors="ignore")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def pick_latest_two(prefix: str) -> List[Path]:
    files = sorted(ROOT.glob(f"{prefix}_*.json"))
    return files[-2:] if len(files) >= 2 else files


def extract_headline_metrics(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort extraction of headline metrics from report JSON.
    Supports multiple schema variants by checking common fields.
    """
    metrics: Dict[str, Any] = {}

    # Try direct fields commonly present
    for key in [
        "Total Filings Analyzed",
        "Total Violations Identified",
        "Estimated Total Damages",
        "Criminal Referrals Recommended",
        "coverage",
        "filings_analyzed",
    ]:
        if key in obj:
            metrics[key] = obj[key]

    # Try nested summary block
    summary = obj.get("summary") if isinstance(obj, dict) else None
    if isinstance(summary, dict):
        for k in [
            "total_filings_analyzed",
            "total_violations",
            "estimated_damages_total",
            "criminal_violations",
            "coverage",
        ]:
            if k in summary:
                metrics[k] = summary[k]

    # Fallback counts
    if "violations" in obj and isinstance(obj["violations"], list):
        metrics.setdefault("violations_list_count", len(obj["violations"]))

    return metrics


def generate_diff() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    json_candidates = pick_latest_two("NIKE_2019_FORENSIC_ANALYSIS")
    if len(json_candidates) < 2:
        raise SystemExit("Not enough NIKE_2019_FORENSIC_ANALYSIS_*.json files to diff")

    a, b = json_candidates[-2], json_candidates[-1]

    def load_json(p: Path) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None

    ja, jb = load_json(a), load_json(b)
    ma, mb = extract_headline_metrics(ja or {}), extract_headline_metrics(jb or {})

    # Companion MD files (optional)
    mda = a.with_suffix(".md")
    mdb = b.with_suffix(".md")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = OUT_DIR / f"artifact_diff_{ts}.md"

    lines: List[str] = []
    lines.append(f"### Artifact Diff — NIKE 2019\n")
    lines.append(f"- Older: `{a.name}`\n")
    lines.append(f"- Newer: `{b.name}`\n")
    lines.append("")

    lines.append("#### Headline metrics (best effort)\n")
    if ma or mb:
        all_keys = sorted(set(ma.keys()) | set(mb.keys()))
        for k in all_keys:
            lines.append(f"- {k}: {ma.get(k, '—')} → {mb.get(k, '—')}")
    else:
        lines.append("(No structured metrics found; see file hashes below.)")
    lines.append("")

    lines.append("#### Integrity\n")
    lines.append(f"- SHA-256 (older JSON): `{sha256_text(a)}`")
    lines.append(f"- SHA-256 (newer JSON): `{sha256_text(b)}`")
    if mda.exists():
        lines.append(f"- SHA-256 (older MD): `{sha256_text(mda)}`")
    if mdb.exists():
        lines.append(f"- SHA-256 (newer MD): `{sha256_text(mdb)}`")
    lines.append("")

    lines.append("#### Sizes\n")
    lines.append(f"- Size (older JSON): {a.stat().st_size:,} bytes")
    lines.append(f"- Size (newer JSON): {b.stat().st_size:,} bytes")
    if mda.exists():
        lines.append(f"- Size (older MD): {mda.stat().st_size:,} bytes")
    if mdb.exists():
        lines.append(f"- Size (newer MD): {mdb.stat().st_size:,} bytes")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = generate_diff()
    print(str(path))
