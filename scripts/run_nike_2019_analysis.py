#!/usr/bin/env python3
"""
Nike 2019 Full-Depth Forensic Investigation
============================================

Executes the complete JLAW 9-phase forensic pipeline on NIKE, Inc.
(CIK: 320187) for all SEC filings in calendar year 2019.

Usage:
    python scripts/run_nike_2019_analysis.py

This script:
1. Validates environment configuration
2. Initializes the UnifiedForensicOrchestrator
3. Executes all 9 phases of the forensic pipeline
4. Generates a DOJ-grade visual dossier PDF
5. Outputs analysis summary with alerts and violations
"""

import asyncio
import sys
import os
import json
import logging
from pathlib import Path
from datetime import date, datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_environment():
    """Validate and set up the execution environment."""
    from config.secure_config import load_dotenv_file, get_api_key, validate_sec_user_agent

    # Load .env
    env_vars = load_dotenv_file()
    print(f"✅ Loaded {len(env_vars)} environment variables")

    # Validate SEC User-Agent
    sec_ua = get_api_key("SEC_USER_AGENT")
    if not sec_ua:
        print("❌ SEC_USER_AGENT not configured. Set it in .env file.")
        sys.exit(1)

    is_valid, msg = validate_sec_user_agent(sec_ua)
    if not is_valid:
        print(f"❌ SEC_USER_AGENT invalid: {msg}")
        sys.exit(1)

    print(f"✅ SEC User-Agent: {sec_ua[:30]}...")

    # Check optional services
    ai_keys = []
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        val = get_api_key(key)
        if val:
            ai_keys.append(key)
    if ai_keys:
        print(f"✅ AI keys configured: {', '.join(ai_keys)}")
    else:
        print("⚠️  No AI API keys configured - Phase 6 (AI validation) will be skipped")

    polygon = get_api_key("POLYGON_API_KEY")
    if polygon:
        print("✅ Polygon.io API key configured")
    else:
        print("⚠️  Polygon.io key not configured - Node 15 runs in degraded mode")


async def run_investigation():
    """Execute the full Nike 2019 forensic investigation."""
    from src.core.unified_orchestrator import UnifiedForensicOrchestrator

    # Target configuration
    CIK = "320187"
    COMPANY = "NIKE, Inc."
    START = date(2019, 1, 1)
    END = date(2019, 12, 31)
    OUTPUT = PROJECT_ROOT / "output"

    print("\n" + "=" * 70)
    print("  JLAW FORENSIC INVESTIGATION")
    print(f"  Target: {COMPANY} (CIK: {CIK})")
    print(f"  Period: {START} to {END}")
    print("=" * 70 + "\n")

    # Initialize orchestrator
    orchestrator = UnifiedForensicOrchestrator(
        cik=CIK,
        company_name=COMPANY,
        start_date=START,
        end_date=END,
        output_dir=OUTPUT,
        strict_mode=False,
        auto_mode=True,
        enable_dual_agent=True,
        enable_subagents=True,
    )

    # Execute full analysis
    result = await orchestrator.execute_full_analysis()

    # Print summary
    print("\n" + "=" * 70)
    print("  INVESTIGATION RESULTS")
    print("=" * 70)
    print(f"  Status: {result.status}")
    print(f"  Phases completed: {len(result.phases)}")

    for phase_name, phase_data in result.phases.items():
        status = phase_data.get("status", "unknown")
        icon = "✅" if status == "success" else "⚠️" if status in ("skipped", "degraded") else "❌"
        print(f"  {icon} {phase_name}: {status}")

    # Phase 4 details
    p4 = result.phases.get("phase_4", {})
    if p4:
        print(f"\n  📊 Phase 4 Node Analysis:")
        print(f"     Total Alerts: {p4.get('total_alerts', 'N/A')}")
        print(f"     Total Violations: {p4.get('total_violations', 'N/A')}")
        print(f"     Case ID: {p4.get('case_id', 'N/A')}")

    # Phase 9 dossier
    p9 = result.phases.get("phase_9", {})
    if p9 and p9.get("dossier_generated"):
        print(f"\n  📄 Dossier: {p9.get('pdf_path', 'N/A')}")

    print("=" * 70)

    # Save full results as JSON
    results_path = OUTPUT / "nike_2019_investigation_results.json"
    OUTPUT.mkdir(parents=True, exist_ok=True)

    results_json = {
        "target_cik": result.target_cik,
        "target_company": result.target_company,
        "status": result.status,
        "phases": {},
        "execution_log_count": len(result.execution_log),
    }
    for k, v in result.phases.items():
        # Convert to JSON-serializable format
        phase_copy = {}
        for pk, pv in v.items():
            try:
                json.dumps(pv)
                phase_copy[pk] = pv
            except (TypeError, ValueError):
                phase_copy[pk] = str(pv)
        results_json["phases"][k] = phase_copy

    with open(results_path, "w") as f:
        json.dump(results_json, f, indent=2, default=str)

    print(f"\n  📁 Full results saved to: {results_path}")
    return result


def main():
    """Main entry point."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  JLAW - Nike 2019 Full-Depth Forensic Investigation           ║")
    print("║  15-Node Recursive Prosecutorial Engine                       ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")

    # Step 1: Validate environment
    print("📋 Step 1: Validating environment...")
    setup_environment()

    # Step 2: Run investigation
    print("\n🔍 Step 2: Executing forensic investigation...")
    result = asyncio.run(run_investigation())

    # Exit code
    if result.status == "complete":
        print("\n✅ Investigation completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Investigation failed: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
