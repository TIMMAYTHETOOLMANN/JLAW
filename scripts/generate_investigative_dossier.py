#!/usr/bin/env python3
"""
JLAW Investigative Dossier Assembler
=====================================

Reads all raw analysis output from a completed JLAW investigation and
produces a comprehensive, Wall-Street-Journal-style PDF dossier that
consolidates findings into an easy-to-digest, human-readable document.

The script:
  1. Loads enhanced analysis results, violations, and severity data.
  2. Loads penalty exposure calculations.
  3. Loads forensic tracing results (with corrected anomaly counts).
  4. Loads SOX, temporal, beneficiary, and evidence-chain data.
  5. Optionally re-runs the forensic tracing executive-profile builder
     to cross-reference violations with insider profiles.
  6. Passes everything into ForensicDossierGenerator.generate_investigative_dossier().

Usage:
    python scripts/generate_investigative_dossier.py \\
        --input-dir output/NKE_2019 \\
        --company "NIKE, Inc." \\
        --cik 320187

    # Regenerate forensic tracing with corrected anomaly counts:
    python scripts/generate_investigative_dossier.py \\
        --input-dir output/NKE_2019 \\
        --company "NIKE, Inc." \\
        --cik 320187 \\
        --fix-anomalies
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.reporting.forensic_dossier import ForensicDossierGenerator  # noqa: E402


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _load_json(filepath: Path) -> dict | list:
    """Load a JSON file with error handling; return empty dict on failure."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"  [WARN] Not found: {filepath}")
        return {}
    except json.JSONDecodeError as exc:
        print(f"  [WARN] Invalid JSON in {filepath}: {exc}")
        return {}


def _save_json(data, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  [SAVED] {filepath} ({filepath.stat().st_size:,} bytes)")


# ────────────────────────────────────────────────────────────────────
# Fix zero anomalies in forensic tracing
# ────────────────────────────────────────────────────────────────────

def _fix_anomalies(
    input_dir: Path,
    enhanced_results: dict,
    insider_trades: list,
    fsl_assessments: list,
) -> dict:
    """
    Re-run the executive profile builder with violation
    cross-referencing enabled.  Returns updated forensic_tracing dict.
    """
    from src.forensic_tracing.executive_profile import (
        build_executive_profiles_from_pipeline,
    )

    print("\n--- Re-building executive profiles with violation cross-reference ---")
    ep = build_executive_profiles_from_pipeline(
        enhanced_results=enhanced_results,
        insider_trades=insider_trades,
        fsl_assessments=fsl_assessments,
    )
    total_anomalies = ep.get("summary", {}).get("total_anomalies", 0)
    print(f"  Cross-reference anomalies detected: {total_anomalies}")

    # Write corrected files
    tracing_dir = input_dir / "forensic_tracing"
    tracing_dir.mkdir(parents=True, exist_ok=True)

    _save_json(ep, tracing_dir / "executive_financial_profiles.json")

    # Reload full forensic tracing and patch executive_profiles
    tracing_path = tracing_dir / "forensic_tracing_results.json"
    tracing = _load_json(tracing_path) if tracing_path.exists() else {}
    if isinstance(tracing, dict):
        tracing["executive_profiles"] = ep
        _save_json(tracing, tracing_path)

    # Regenerate human-readable summary
    _regenerate_tracing_summary(tracing, tracing_dir)

    return tracing


def _regenerate_tracing_summary(tracing: dict, output_dir: Path) -> None:
    """Regenerate FORENSIC_TRACING_SUMMARY.txt with corrected counts."""
    lines = []
    lines.append("=" * 72)
    lines.append("JLAW FORENSIC TRACING SYSTEM — SIX-DOMAIN ANALYSIS REPORT")
    lines.append(f"Regenerated: {datetime.now().isoformat()}Z")
    lines.append("=" * 72)

    # Domain 1
    d1 = tracing.get("domain1_footnotes", {})
    lines.append("\nDOMAIN 1: FORM 4 FOOTNOTE CLASSIFICATION")
    lines.append(f"  Total footnotes classified: {d1.get('total_footnotes', 0)}")
    lines.append(f"  Average risk score: {d1.get('average_risk_score', 0)}")

    # Domain 2
    d2_raw = tracing.get("domain2_tracing", {})
    d2 = d2_raw.get("summary", d2_raw)
    lines.append("\nDOMAIN 2: GRANT-TO-SALE TRACING")
    lines.append(f"  Chains constructed: {d2.get('chains_constructed', 0)}")
    econ_val = d2.get("total_economic_value_transferred", 0)
    lines.append(f"  Economic value transferred: ${econ_val:,.2f}")

    # Domain 3
    d3 = tracing.get("domain3_ownership", {})
    lines.append("\nDOMAIN 3: BENEFICIAL OWNERSHIP RESOLUTION")
    lines.append(f"  Entity transfers analyzed: {d3.get('entity_transfers_analyzed', 0)}")
    lines.append(f"  Parking risk flags: {d3.get('parking_risk_flags', 0)}")

    # Executive profiles
    ep = tracing.get("executive_profiles", {})
    ep_s = ep.get("summary", {})
    lines.append("\nEXECUTIVE FINANCIAL PROFILES (Cross-Reference)")
    lines.append(f"  Insiders profiled: {ep_s.get('total_insiders_profiled', 0)}")
    lines.append(f"  Officers: {ep_s.get('officers', 0)}")
    lines.append(f"  Directors: {ep_s.get('directors', 0)}")
    lines.append(f"  10%+ owners: {ep_s.get('ten_percent_owners', 0)}")
    lines.append(f"  Cross-reference anomalies: {ep_s.get('total_anomalies', 0)}")
    for atype, acount in ep_s.get("anomaly_types", {}).items():
        lines.append(f"    {atype}: {acount}")
    for cik, profile in ep.get("profiles", {}).items():
        name = profile.get("insider_name", "Unknown")
        txns = profile.get("form4_summary", {}).get("total_transactions", 0)
        anom_count = profile.get("anomaly_count", 0)
        lines.append(f"  [{cik}] {name}: {txns} transactions, {anom_count} anomalies")

    lines.append("\n" + "=" * 72)

    summary_path = output_dir / "FORENSIC_TRACING_SUMMARY.txt"
    summary_path.write_text("\n".join(lines))
    print(f"  [SAVED] {summary_path}")


# ────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="JLAW Investigative Dossier Assembler",
    )
    parser.add_argument(
        "--input-dir", default="output/NKE_2019",
        help="Root directory of the investigation output",
    )
    parser.add_argument(
        "--company", default="NIKE, Inc.",
        help="Company name for the dossier cover",
    )
    parser.add_argument("--cik", default="320187", help="SEC CIK")
    parser.add_argument(
        "--fix-anomalies", action="store_true",
        help="Re-run executive profile builder to fix zero-anomaly counts",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Directory for PDF output (default: <input-dir>/reports)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir) if args.output_dir else input_dir / "reports"

    print("\n" + "=" * 68)
    print("  JLAW INVESTIGATIVE DOSSIER ASSEMBLER")
    print("  Comprehensive forensic analysis → publication-ready PDF")
    print("=" * 68)
    print(f"\n  Input:   {input_dir}")
    print(f"  Output:  {output_dir}")
    print(f"  Company: {args.company}")
    print(f"  CIK:     {args.cik}")

    # ── 1. Load core analysis results ──────────────────────────────
    print("\n--- Loading analysis data ---")

    enhanced_path = input_dir / "enhanced" / "enhanced_analysis_results.json"
    raw_path = input_dir / "bundle" / "analysis_results.json"

    if enhanced_path.exists():
        analysis_results = _load_json(enhanced_path)
        print(f"  Enhanced results: {len(analysis_results.get('violations', []))} violations")
    elif raw_path.exists():
        analysis_results = _load_json(raw_path)
        print(f"  Raw results: {len(analysis_results.get('violations', []))} violations")
    else:
        print("  [ERROR] No analysis results found. Aborting.")
        sys.exit(1)

    # ── 2. Load supplementary datasets ─────────────────────────────
    exec_summary = _load_json(input_dir / "enhanced" / "executive_summary.json")
    penalty_exposure = _load_json(input_dir / "enhanced" / "penalty_exposure.json")
    evidence_chain = _load_json(input_dir / "enhanced" / "evidence_chain.json")
    severity_summary = _load_json(input_dir / "enhanced" / "severity_summary.json")
    beneficiary_analysis_raw = _load_json(input_dir / "enhanced" / "beneficiary_analysis.json")

    beneficiary_analysis = (
        beneficiary_analysis_raw
        if isinstance(beneficiary_analysis_raw, list)
        else beneficiary_analysis_raw.get("beneficiaries", [])
    )

    # SOX analysis (take newest)
    sox_dir = input_dir / "node4_sox"
    sox_analysis = {}
    if sox_dir.exists():
        sox_files = sorted(sox_dir.glob("sox_analysis_*.json"), reverse=True)
        if sox_files:
            sox_analysis = _load_json(sox_files[0])
            print(f"  SOX analysis: {sox_files[0].name}")

    # Temporal analysis (take newest)
    temporal_dir = input_dir / "node3_10q"
    temporal_analysis = {}
    if temporal_dir.exists():
        temporal_files = sorted(temporal_dir.glob("temporal_analysis_*.json"), reverse=True)
        if temporal_files:
            temporal_analysis = _load_json(temporal_files[0])
            print(f"  Temporal analysis: {temporal_files[0].name}")

    # FSL assessments
    fsl_data = _load_json(input_dir / "bundle" / "fsl_assessments.json")
    fsl_assessments = fsl_data if isinstance(fsl_data, list) else fsl_data.get("assessments", [])

    # Insider trades
    insider_trades_data = _load_json(input_dir / "bundle" / "insider_trades.json")
    insider_trades = (
        insider_trades_data if isinstance(insider_trades_data, list)
        else insider_trades_data.get("trades", [])
    )
    if not insider_trades:
        raw = _load_json(raw_path) if raw_path.exists() else {}
        insider_trades = [v for v in raw.get("violations", []) if v.get("reporting_owner")]
    print(f"  Insider trades for profiles: {len(insider_trades)}")

    # Forensic tracing
    tracing_path = input_dir / "forensic_tracing" / "forensic_tracing_results.json"
    forensic_tracing = _load_json(tracing_path) if tracing_path.exists() else {}

    # ── 3. Fix zero anomalies (optional) ───────────────────────────
    if args.fix_anomalies:
        forensic_tracing = _fix_anomalies(
            input_dir, analysis_results, insider_trades, fsl_assessments,
        )

    # ── 4. Merge supplementary data into analysis_results ──────────
    # Ensure penalties are available at top level
    if penalty_exposure and "estimated_penalties" not in analysis_results:
        analysis_results["estimated_penalties"] = {
            "civil_minimum": penalty_exposure.get("categories", [{}])[0].get("minimum_penalty", 0)
            if penalty_exposure.get("categories") else 0,
            "civil_maximum": penalty_exposure.get("total_maximum_exposure", 0),
            "disgorgement": penalty_exposure.get("disgorgement_estimate", 0),
            "criminal_exposure": bool(penalty_exposure.get("criminal_exposure")),
            "prison_years_maximum": (
                penalty_exposure.get("criminal_exposure", {}).get("maximum_imprisonment", "0")
                if isinstance(penalty_exposure.get("criminal_exposure"), dict) else 0
            ),
        }

    # Inject severity counts if not present
    if severity_summary and "critical_alerts" not in analysis_results:
        analysis_results["critical_alerts"] = severity_summary.get("critical", 0)
        analysis_results["high_alerts"] = severity_summary.get("high", 0)

    # Inject executive summary narrative text
    if exec_summary:
        if "executive_summary_text" not in analysis_results:
            narrative = exec_summary.get("narrative", exec_summary.get("executive_summary", ""))
            if narrative:
                analysis_results["executive_summary_text"] = narrative

    # ── 5. Generate the investigative dossier ──────────────────────
    print("\n--- Generating Investigative Dossier ---")

    case_id = f"CASE-{args.cik}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    generator = ForensicDossierGenerator(output_dir=str(output_dir))

    pdf_path, charts = generator.generate_investigative_dossier(
        case_id=case_id,
        company_name=args.company,
        cik=args.cik,
        analysis_results=analysis_results,
        penalty_exposure=penalty_exposure if penalty_exposure else None,
        executive_summary_narrative=exec_summary if exec_summary else None,
        forensic_tracing=forensic_tracing if forensic_tracing else None,
        evidence_chain_data=evidence_chain if evidence_chain else None,
        severity_summary=severity_summary if severity_summary else None,
        sox_analysis=sox_analysis if sox_analysis else None,
        temporal_analysis=temporal_analysis if temporal_analysis else None,
        beneficiary_analysis=beneficiary_analysis if beneficiary_analysis else None,
    )

    print(f"\n  PDF Generated: {pdf_path}")
    print(f"  File size: {pdf_path.stat().st_size:,} bytes")
    print(f"  Standalone charts: {len(charts)}")
    for chart in charts:
        print(f"    - {chart}")

    print("\n" + "=" * 68)
    print("  INVESTIGATIVE DOSSIER COMPLETE")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    main()
