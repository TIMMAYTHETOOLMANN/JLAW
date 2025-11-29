"""
CLI for running JLAW end-to-end pipeline (CPU-friendly, research mode).

Usage examples:
  python -m src.forensics.orchestrator.cli --input "Some text with a|b\n1|2" --profile lite
  python -m src.forensics.orchestrator.cli --input C:\\path\\to\\doc.pdf --out forensic_storage\\runs --profile full
  python -m src.forensics.orchestrator.cli --health
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from .master_controller import MasterForensicController
from ..runtime_profile import apply_high_sophistication_defaults


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="JLAW Forensic Pipeline CLI")
    p.add_argument("--input", dest="input_value", type=str, default=None,
                   help="Path to a document or raw text to analyze")
    p.add_argument("--profile", dest="profile", type=str, default="full",
                   choices=["lite", "full"], help="Execution profile (lite=CPU friendly)")
    p.add_argument("--out", dest="out_dir", type=str, default=None,
                   help="Base directory for run artifacts (default: forensic_storage\\runs)")
    p.add_argument("--no-report", dest="no_report", action="store_true",
                   help="Skip report generation")
    p.add_argument("--health", dest="health", action="store_true",
                   help="Run baseline health checks and exit")
    p.add_argument("--require-dual", dest="require_dual", action="store_true",
                   help="Require dual-agent (OpenAI + Anthropic) stage to succeed; exit non-zero if not OK")
    p.add_argument("--enable-ml-tables", dest="enable_ml_tables", action="store_true",
                   help="Enable optional ML table detection path (layoutparser/Table Transformer if available)")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    # Apply high-sophistication defaults at CLI startup (non-invasive)
    apply_high_sophistication_defaults()
    mc = MasterForensicController()

    if args.health:
        res = mc.run_health_check()
        print("JLAW Health Check:")
        for k, v in (res or {}).items():
            print(f"  - {k}: {v}")
        return 0

    if not args.input_value:
        print("[ERROR] --input is required unless --health is used", file=sys.stderr)
        return 2

    async def run():
        result = await mc.run_full_pipeline(
            content_or_path=args.input_value,
            profile=args.profile,
            out_base_dir=args.out_dir,
            generate_report=not args.no_report,
            enable_ml_tables=args.enable_ml_tables,
            require_dual=args.require_dual,
        )
        print("\nRun complete")
        print(f"  run_id: {result.get('run_id')}")
        print(f"  out_dir: {result.get('out_dir')}")
        print("  stages:")
        for s in result.get("stages", []):
            name = s.get("name")
            status = s.get("status")
            print(f"    - {name}: {status}")
        # Print concise dual-agent summary if present
        dual = next((s for s in result.get("stages", []) if s.get("name") == "dual_agents"), None)
        if dual:
            summary = dual.get("summary", {})
            print("  dual_agents summary:")
            print(f"    openai: {summary.get('openai')}, anthropic: {summary.get('anthropic')}, overlap: {summary.get('overlap')}")
        return 0 if not result.get("require_dual_failed") else 1

    exit_code = asyncio.run(run())
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
