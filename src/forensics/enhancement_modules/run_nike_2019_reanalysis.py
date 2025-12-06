#!/usr/bin/env python3
"""
================================================================================
NIKE 2019 COMPREHENSIVE FORENSIC REANALYSIS
================================================================================

Version: 4.0.0-PRODUCTION
Authority: JARVIS NEXUS
Classification: PROSECUTORIAL-GRADE REANALYSIS

This script performs a comprehensive forensic reanalysis of Nike Inc. (NKE)
2019 SEC filings using the complete production-grade forensic system.

ENHANCED CAPABILITIES:
=====================
1. Complete Form 4 insider transaction parsing
2. Enhanced zero-dollar transaction classification and investigation
3. Beneish M-Score manipulation detection
4. Benford's Law anomaly detection
5. Section 16(b) short-swing profit calculation
6. Late filing detection with penalty estimation
7. Dual-agent AI analysis (if configured)
8. FRE 902(13)/(14) compliant evidence chains

NIKE INC. INVESTIGATION PARAMETERS:
==================================
- CIK: 0000320187
- Ticker: NKE
- Analysis Period: 2019-01-01 to 2019-12-31
- Focus: Zero-dollar transactions, insider trading patterns
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"forensic_reports/nike_2019_reanalysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import forensic modules
sys.path.insert(0, str(PROJECT_ROOT / "src" / "forensics"))

try:
    from src.forensics.unified_forensic_orchestrator import (
        UnifiedForensicOrchestrator,
        run_unified_analysis
    )
    from src.forensics.institutional_ownership_tracker import (
        InstitutionalOwnershipTracker,
        track_institutional_ownership
    )
except ImportError as e:
    logger.warning(f"Could not import from src.forensics: {e}, trying direct import")
    try:
        from unified_forensic_orchestrator import (
            UnifiedForensicOrchestrator,
            run_unified_analysis
        )
        from institutional_ownership_tracker import (
            InstitutionalOwnershipTracker,
            track_institutional_ownership
        )
    except ImportError as e2:
        logger.error(f"Failed to import forensic modules: {e2}")
        raise


# Nike Inc. Investigation Parameters
NIKE_CIK = "320187"
NIKE_TICKER = "NKE"
NIKE_COMPANY_NAME = "Nike Inc."
NIKE_CUSIP = "654106103"  # Nike common stock CUSIP
ANALYSIS_START = "2019-01-01"
ANALYSIS_END = "2019-12-31"

# Filing types to analyze
FILING_TYPES = [
    "10-K", "10-K/A",  # Annual reports
    "10-Q", "10-Q/A",  # Quarterly reports
    "8-K", "8-K/A",    # Current reports
    "4", "4/A",        # Form 4 insider transactions
    "3", "3/A",        # Form 3 initial ownership
    "5", "5/A",        # Form 5 annual insider
    "SC 13G", "SC 13G/A",  # Beneficial ownership (passive)
    "SC 13D", "SC 13D/A",  # Beneficial ownership (active)
    "DEF 14A",         # Proxy statements
]


async def run_nike_2019_reanalysis():
    """
    Execute comprehensive Nike 2019 forensic reanalysis.
    """
    print("=" * 100)
    print("NIKE INC. 2019 COMPREHENSIVE FORENSIC REANALYSIS")
    print("Production-Grade SEC Forensic Financial Analysis System v4.0")
    print("=" * 100)
    print()
    print(f"Company: {NIKE_COMPANY_NAME} ({NIKE_TICKER})")
    print(f"CIK: {NIKE_CIK}")
    print(f"CUSIP: {NIKE_CUSIP}")
    print(f"Analysis Period: {ANALYSIS_START} to {ANALYSIS_END}")
    print("=" * 100)
    print()
    
    # Create output directory
    output_dir = Path("forensic_reports") / "nike_2019_production_reanalysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # =========================================================================
    # PHASE 1: Unified Forensic Analysis
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 1: UNIFIED FORENSIC ANALYSIS")
    print("=" * 80)
    
    try:
        unified_results = await run_unified_analysis(
            cik=NIKE_CIK,
            start_date=ANALYSIS_START,
            end_date=ANALYSIS_END,
            company_name=NIKE_COMPANY_NAME,
            output_dir=str(output_dir),
            enable_ai=True
        )
        results["unified_analysis"] = unified_results
        
        # Print summary
        violation_summary = unified_results.get("violation_summary", {})
        insider_summary = unified_results.get("insider_transaction_analysis", {})
        zero_dollar = unified_results.get("zero_dollar_analysis", {}).get("summary", {})
        
        print(f"\n✅ Unified Analysis Complete")
        print(f"   Total Filings Analyzed: {unified_results.get('filing_summary', {}).get('total_filings', 0)}")
        print(f"   Total Insider Transactions: {insider_summary.get('total_transactions', 0)}")
        print(f"   Late Filings: {insider_summary.get('late_filings', 0)}")
        print(f"   Zero-Dollar Transactions: {insider_summary.get('zero_dollar_transactions', 0)}")
        print(f"   Total Violations: {violation_summary.get('total_violations', 0)}")
        print(f"   Critical/High Violations: {violation_summary.get('by_severity', {}).get('CRITICAL', 0) + violation_summary.get('by_severity', {}).get('HIGH', 0)}")
        
        # Zero-dollar breakdown
        print(f"\n   📊 Zero-Dollar Transaction Analysis:")
        print(f"      RSU Vestings: {zero_dollar.get('rsu_vestings', 0)}")
        print(f"      Gift Transactions: {zero_dollar.get('gift_transactions', 0)}")
        print(f"      Requiring Investigation: {zero_dollar.get('requiring_investigation', 0)}")
        print(f"      Red Flags Identified: {zero_dollar.get('red_flag_count', 0)}")
        
    except Exception as e:
        logger.error(f"Unified analysis failed: {e}", exc_info=True)
        results["unified_analysis"] = {"error": str(e)}
    
    # =========================================================================
    # PHASE 2: Institutional Ownership Tracking
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 2: INSTITUTIONAL OWNERSHIP TRACKING")
    print("=" * 80)
    
    try:
        institutional_results = await track_institutional_ownership(
            cusip=NIKE_CUSIP,
            issuer_cik=NIKE_CIK,
            start_date=ANALYSIS_START,
            end_date=ANALYSIS_END,
            output_dir=str(output_dir)
        )
        results["institutional_ownership"] = institutional_results
        
        print(f"\n✅ Institutional Ownership Analysis Complete")
        print(f"   Total Schedule Filings: {institutional_results.get('total_schedule_filings', 0)}")
        print(f"   Initial Filings: {institutional_results.get('initial_filings', 0)}")
        print(f"   5% Threshold Crossings: {institutional_results.get('threshold_crossings', {}).get('5_percent', 0)}")
        print(f"   10% Threshold Crossings: {institutional_results.get('threshold_crossings', {}).get('10_percent', 0)}")
        print(f"   13G→13D Conversions: {len(institutional_results.get('conversions', []))}")
        
    except Exception as e:
        logger.error(f"Institutional tracking failed: {e}", exc_info=True)
        results["institutional_ownership"] = {"error": str(e)}
    
    # =========================================================================
    # PHASE 3: Generate Comprehensive Report
    # =========================================================================
    print("\n" + "=" * 80)
    print("PHASE 3: COMPREHENSIVE REPORT GENERATION")
    print("=" * 80)
    
    # Generate final report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    final_report = {
        "report_metadata": {
            "report_id": f"NIKE_2019_REANALYSIS_{timestamp}",
            "company": NIKE_COMPANY_NAME,
            "ticker": NIKE_TICKER,
            "cik": NIKE_CIK,
            "cusip": NIKE_CUSIP,
            "analysis_period": {"start": ANALYSIS_START, "end": ANALYSIS_END},
            "generated_at": datetime.now().isoformat(),
            "system_version": "4.0.0-PRODUCTION",
            "authority": "JARVIS NEXUS"
        },
        "executive_summary": generate_executive_summary(results),
        "detailed_findings": results
    }
    
    # Save JSON report
    json_file = output_dir / f"nike_2019_complete_reanalysis_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, default=str)
    print(f"\n✅ JSON Report saved: {json_file}")
    
    # Save Markdown report
    md_file = output_dir / f"nike_2019_reanalysis_report_{timestamp}.md"
    md_content = generate_markdown_report(final_report)
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"✅ Markdown Report saved: {md_file}")
    
    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 100)
    print("NIKE 2019 FORENSIC REANALYSIS COMPLETE")
    print("=" * 100)
    
    exec_summary = final_report.get("executive_summary", {})
    print(f"\n📊 EXECUTIVE SUMMARY:")
    print(f"   Total Violations Detected: {exec_summary.get('total_violations', 0)}")
    print(f"   Critical/High Priority: {exec_summary.get('critical_high_violations', 0)}")
    print(f"   Zero-Dollar Transactions Analyzed: {exec_summary.get('zero_dollar_transactions', 0)}")
    print(f"   Transactions Requiring Investigation: {exec_summary.get('requiring_investigation', 0)}")
    print(f"   Short-Swing Profits Detected: {exec_summary.get('short_swing_profits_detected', 0)}")
    print(f"   Estimated Total Damages: ${exec_summary.get('estimated_damages', 0):,.2f}")
    print(f"\n📁 Reports saved to: {output_dir}")
    print("=" * 100)
    
    return final_report


def generate_executive_summary(results: dict) -> dict:
    """Generate executive summary from analysis results."""
    unified = results.get("unified_analysis", {})
    institutional = results.get("institutional_ownership", {})
    
    violation_summary = unified.get("violation_summary", {})
    insider = unified.get("insider_transaction_analysis", {})
    zero_dollar = unified.get("zero_dollar_analysis", {}).get("summary", {})
    short_swing = unified.get("short_swing_profits", [])
    
    total_damages = violation_summary.get("total_estimated_damages", 0)
    for ss in short_swing:
        total_damages += ss.get("profit", 0)
    
    return {
        "total_filings_analyzed": unified.get("filing_summary", {}).get("total_filings", 0),
        "total_insider_transactions": insider.get("total_transactions", 0),
        "late_filings": insider.get("late_filings", 0),
        "zero_dollar_transactions": insider.get("zero_dollar_transactions", 0),
        "requiring_investigation": zero_dollar.get("requiring_investigation", 0),
        "total_violations": violation_summary.get("total_violations", 0),
        "critical_high_violations": (
            violation_summary.get("by_severity", {}).get("CRITICAL", 0) +
            violation_summary.get("by_severity", {}).get("HIGH", 0)
        ),
        "short_swing_profits_detected": len([s for s in short_swing if s.get("disgorgement_required")]),
        "institutional_filings": institutional.get("total_schedule_filings", 0),
        "thirteeng_to_thirteend_conversions": len(institutional.get("conversions", [])),
        "estimated_damages": total_damages,
        "prosecution_recommendation": determine_prosecution_recommendation(violation_summary)
    }


def determine_prosecution_recommendation(violation_summary: dict) -> str:
    """Determine prosecution recommendation based on violations."""
    critical = violation_summary.get("by_severity", {}).get("CRITICAL", 0)
    high = violation_summary.get("by_severity", {}).get("HIGH", 0)
    total = violation_summary.get("total_violations", 0)
    
    if critical > 0:
        return "IMMEDIATE DOJ REFERRAL RECOMMENDED - Critical violations detected"
    elif high >= 3:
        return "HIGH PRIORITY - Multiple high-severity violations warrant escalation"
    elif total >= 5:
        return "MODERATE PRIORITY - Pattern of violations suggests further investigation"
    else:
        return "STANDARD REVIEW - Continue monitoring for additional violations"


def generate_markdown_report(report: dict) -> str:
    """Generate comprehensive Markdown report."""
    meta = report.get("report_metadata", {})
    summary = report.get("executive_summary", {})
    findings = report.get("detailed_findings", {})
    
    unified = findings.get("unified_analysis", {})
    zero_dollar = unified.get("zero_dollar_analysis", {})
    violations = unified.get("violations", [])
    short_swing = unified.get("short_swing_profits", [])
    
    md = f"""# NIKE INC. 2019 COMPREHENSIVE FORENSIC REANALYSIS REPORT

## Report Identification

| Field | Value |
|-------|-------|
| Report ID | {meta.get('report_id', 'N/A')} |
| Company | {meta.get('company')} ({meta.get('ticker')}) |
| CIK | {meta.get('cik')} |
| CUSIP | {meta.get('cusip')} |
| Analysis Period | {meta.get('analysis_period', {}).get('start')} to {meta.get('analysis_period', {}).get('end')} |
| Generated | {meta.get('generated_at')} |
| System Version | {meta.get('system_version')} |
| Authority | {meta.get('authority')} |

---

## EXECUTIVE SUMMARY

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Filings Analyzed | {summary.get('total_filings_analyzed', 0)} |
| Total Insider Transactions | {summary.get('total_insider_transactions', 0)} |
| Late Filings Detected | {summary.get('late_filings', 0)} |
| Zero-Dollar Transactions | {summary.get('zero_dollar_transactions', 0)} |
| Requiring Investigation | {summary.get('requiring_investigation', 0)} |
| Total Violations | {summary.get('total_violations', 0)} |
| Critical/High Violations | {summary.get('critical_high_violations', 0)} |
| Short-Swing Profits | {summary.get('short_swing_profits_detected', 0)} |
| Estimated Damages | ${summary.get('estimated_damages', 0):,.2f} |

### Prosecution Recommendation

**{summary.get('prosecution_recommendation', 'N/A')}**

---

## ZERO-DOLLAR TRANSACTION ANALYSIS

Zero-dollar transactions represent transfers of securities at $0 price per share. 
These require heightened scrutiny per "Insider Trading by Other Means" (2024) research
documenting $100B+ in potential concealment strategies.

### Summary Statistics

"""
    
    zero_summary = zero_dollar.get("summary", {})
    md += f"""| Classification | Count |
|----------------|-------|
| Total $0 Transactions | {zero_summary.get('total_zero_dollar_transactions', 0)} |
| Total Shares Transferred | {zero_summary.get('total_shares_transferred', 0):,.0f} |
| RSU Vestings | {zero_summary.get('rsu_vestings', 0)} |
| Gift Transactions | {zero_summary.get('gift_transactions', 0)} |
| Red Flags Identified | {zero_summary.get('red_flag_count', 0)} |
| Requiring Investigation | {zero_summary.get('requiring_investigation', 0)} |

### Classification Breakdown

"""
    
    for cls, count in zero_summary.get("by_classification", {}).items():
        md += f"- **{cls}:** {count}\n"
    
    # Add detailed zero-dollar classifications
    classifications = zero_dollar.get("classifications", [])
    if classifications:
        md += "\n### Transactions Requiring Investigation\n\n"
        
        for c in classifications[:20]:  # Limit to first 20
            if c.get("requires_investigation"):
                md += f"""#### {c.get('filer', 'Unknown')} - {c.get('date', 'N/A')}
- **Shares:** {c.get('shares', 0):,.0f}
- **Classification:** {c.get('classification', 'Unknown')}
- **Confidence:** {c.get('confidence', 0):.1%}
- **Red Flags:** {', '.join(c.get('red_flags', [])) or 'None'}

"""
    
    # Short-swing profits
    if short_swing:
        md += "\n---\n\n## SHORT-SWING PROFIT ANALYSIS (Section 16(b))\n\n"
        md += "The following insiders have potential disgorgeable profits from matched buy/sell transactions within 6 months:\n\n"
        
        for ss in short_swing:
            if ss.get("disgorgement_required"):
                md += f"""### {ss.get('insider', 'Unknown')}
- **Profit:** ${ss.get('profit', 0):,.2f}
- **Matched Transaction Pairs:** {ss.get('matched_pairs', 0)}
- **Disgorgement Required:** Yes

"""
    
    # Violations
    md += "\n---\n\n## VIOLATIONS DETECTED\n\n"
    
    critical_violations = [v for v in violations if v.get("severity") in ["CRITICAL", "HIGH"]]
    
    if critical_violations:
        md += "### Critical/High Severity Violations\n\n"
        for i, v in enumerate(critical_violations[:20], 1):
            md += f"""#### {i}. {v.get('violation_type', 'Unknown')} ({v.get('severity', 'N/A')})
- **Statute:** {v.get('statute_citation', 'N/A')}
- **Description:** {v.get('description', 'N/A')}
- **Filing Date:** {v.get('filing_date', 'N/A')}
- **Document:** {v.get('accession_number', 'N/A')}
- **Estimated Damages:** ${v.get('estimated_damages', 0):,.2f}

"""
    
    md += f"""
---

## LEGAL REFERENCES

### Applicable Statutes
- **15 U.S.C. § 78j(b)** - Section 10(b) Anti-Fraud Provisions
- **15 U.S.C. § 78p(a)** - Section 16(a) Insider Reporting
- **15 U.S.C. § 78p(b)** - Section 16(b) Short-Swing Profits
- **17 CFR § 240.10b-5** - Rule 10b-5 Fraud and Deceit
- **17 CFR § 240.16a-3** - Rule 16a-3 Reporting Transactions

### Methodology
This analysis was conducted using the Production-Grade SEC Forensic Financial Analysis System,
implementing research-validated detection algorithms including:
- Beneish M-Score (Beneish, 1999)
- Benford's Law (Hill, 1995)
- Altman Z-Score (Altman, 1968)
- Short-swing profit calculation (Gratz v. Claughton)

---

*Report generated by JARVIS NEXUS v{meta.get('system_version', '4.0.0')}*
*Classification: PROSECUTORIAL-GRADE*
"""
    
    return md


if __name__ == "__main__":
    # Ensure output directory exists
    Path("forensic_reports").mkdir(exist_ok=True)
    
    # Run the analysis
    result = asyncio.run(run_nike_2019_reanalysis())

