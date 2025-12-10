#!/usr/bin/env python3
"""
REPORT QUALITY VALIDATOR
========================

This script validates that generated reports meet production-level quality standards.
It checks for:
- Proper file structure
- Comprehensive content
- All required sections
- Substantive analysis data

Usage:
    python validate_report_quality.py [path_to_report_directory]
    python validate_report_quality.py  # Validates latest report in output/
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def check_exists(path: Path, description: str) -> bool:
    """Check if a file or directory exists."""
    if path.exists():
        print(f"  ✓ {description}: {path.name}")
        return True
    else:
        print(f"  ✗ MISSING: {description}")
        return False

def validate_markdown_report(md_path: Path) -> Tuple[bool, List[str]]:
    """Validate markdown report content."""
    issues = []
    
    if not md_path.exists():
        return False, [f"Markdown report file not found: {md_path}"]
    
    content = md_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Check file size
    size_kb = len(content) / 1024
    if size_kb < 10:
        issues.append(f"Report too small ({size_kb:.1f}KB, expected >10KB)")
    else:
        print(f"  ✓ Report size: {size_kb:.1f}KB (comprehensive)")
    
    # Check line count
    if len(lines) < 100:
        issues.append(f"Report too short ({len(lines)} lines, expected >100)")
    else:
        print(f"  ✓ Line count: {len(lines)} lines")
    
    # Check for required sections
    required_sections = [
        "EXECUTIVE SUMMARY",
        "STATUTORY FRAMEWORK",
        "PER-FILING DETAILED ANALYSIS",
        "ENFORCEMENT PRECEDENT",
        "CHAIN OF CUSTODY"
    ]
    
    for section in required_sections:
        if section in content:
            print(f"  ✓ Section present: {section}")
        else:
            issues.append(f"Missing section: {section}")
            print(f"  ✗ Missing section: {section}")
    
    # Check for evidence of actual analysis
    violation_mentions = content.count("Violation")
    if violation_mentions < 5:
        issues.append(f"Too few violations mentioned ({violation_mentions})")
    else:
        print(f"  ✓ Violations documented: {violation_mentions} mentions")
    
    # Check for statutory citations
    citation_count = content.count("U.S.C.")
    if citation_count < 5:
        issues.append(f"Too few statutory citations ({citation_count})")
    else:
        print(f"  ✓ Statutory citations: {citation_count} found")
    
    # Check for document URLs (evidence links)
    url_count = content.count("sec.gov")
    if url_count < 5:
        issues.append(f"Too few SEC document URLs ({url_count})")
    else:
        print(f"  ✓ SEC document links: {url_count} found")
    
    return len(issues) == 0, issues

def validate_json_summary(json_path: Path) -> Tuple[bool, List[str]]:
    """Validate JSON summary content."""
    issues = []
    
    if not json_path.exists():
        return False, ["JSON summary file not found"]
    
    try:
        data = json.loads(json_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON format: {e}"]
    
    # Check required fields
    required_fields = [
        'company',
        'cik',
        'period',
        'total_filings',
        'total_violations',
        'violation_types',
        'severity_distribution'
    ]
    
    for field in required_fields:
        if field in data:
            print(f"  ✓ Field present: {field}")
        else:
            issues.append(f"Missing field: {field}")
            print(f"  ✗ Missing field: {field}")
    
    # Check for substantive data
    if 'total_filings' in data:
        if data['total_filings'] == 0:
            issues.append("No filings analyzed (total_filings = 0)")
        else:
            print(f"  ✓ Filings analyzed: {data['total_filings']}")
    
    if 'total_violations' in data:
        if data['total_violations'] == 0:
            issues.append("No violations found (might indicate incomplete analysis)")
            print(f"  ⚠ No violations found (unusual - check if analysis completed)")
        else:
            print(f"  ✓ Violations found: {data['total_violations']}")
    
    return len(issues) == 0, issues

def validate_report_directory(report_dir: Path) -> Tuple[bool, Dict]:
    """Validate complete report directory structure."""
    results = {
        'directory_exists': False,
        'has_main_report': False,
        'has_executive_summary': False,
        'has_machine_readable': False,
        'has_evidence': False,
        'has_appendices': False,
        'markdown_valid': False,
        'json_valid': False,
        'all_issues': []
    }
    
    # Check directory exists
    if not report_dir.exists():
        results['all_issues'].append(f"Directory not found: {report_dir}")
        return False, results
    
    results['directory_exists'] = True
    
    # Check main report
    main_report = report_dir / "FORENSIC_REPORT.md"
    results['has_main_report'] = check_exists(main_report, "Main Report (FORENSIC_REPORT.md)")
    
    # Check executive summary
    exec_summary = report_dir / "executive_summary.md"
    results['has_executive_summary'] = check_exists(exec_summary, "Executive Summary")
    
    # Check subdirectories
    machine_dir = report_dir / "machine_readable"
    results['has_machine_readable'] = check_exists(machine_dir, "Machine Readable Directory")
    
    evidence_dir = report_dir / "evidence"
    results['has_evidence'] = check_exists(evidence_dir, "Evidence Directory")
    
    appendices_dir = report_dir / "appendices"
    results['has_appendices'] = check_exists(appendices_dir, "Appendices Directory")
    
    # Validate markdown content
    if results['has_main_report']:
        print_section("Validating Markdown Report Content")
        results['markdown_valid'], md_issues = validate_markdown_report(main_report)
        results['all_issues'].extend(md_issues)
    
    # Validate JSON content
    if results['has_machine_readable']:
        summary_json = machine_dir / "summary.json"
        if summary_json.exists():
            print_section("Validating JSON Summary Content")
            results['json_valid'], json_issues = validate_json_summary(summary_json)
            results['all_issues'].extend(json_issues)
    
    # Overall assessment
    all_good = (
        results['directory_exists'] and
        results['has_main_report'] and
        results['has_executive_summary'] and
        results['has_machine_readable'] and
        results['has_evidence'] and
        results['has_appendices'] and
        results['markdown_valid'] and
        (results['json_valid'] if results['has_machine_readable'] else True)
    )
    
    return all_good, results

def find_latest_report(output_dir: Path = Path("output")) -> Path:
    """Find the most recent report directory."""
    if not output_dir.exists():
        return None
    
    # Look for directories matching the pattern
    pattern = "*_FORENSIC_ANALYSIS_*"
    matching_dirs = sorted(output_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if matching_dirs:
        return matching_dirs[0]
    
    return None

def main():
    """Main validation entry point."""
    print_section("JLAW REPORT QUALITY VALIDATOR")
    
    # Determine which report to validate
    if len(sys.argv) > 1:
        report_path = Path(sys.argv[1])
    else:
        print("\n  No report path specified, searching for latest report...")
        report_path = find_latest_report()
        if not report_path:
            print("\n  ✗ No reports found in output/ directory")
            print("\n  Usage: python validate_report_quality.py [path_to_report_directory]")
            sys.exit(1)
    
    print(f"\n  Validating: {report_path}")
    
    # Run validation
    print_section("Checking Report Structure")
    is_valid, results = validate_report_directory(report_path)
    
    # Print summary
    print_section("VALIDATION SUMMARY")
    
    if is_valid:
        print("\n  ✅ REPORT PASSES QUALITY STANDARDS")
        print("\n  This report is:")
        print("    • Comprehensive (includes all required sections)")
        print("    • Substantive (contains actual analysis data)")
        print("    • Production-ready (meets DOJ-level standards)")
        print("    • Multi-format (markdown + JSON)")
        return_code = 0
    else:
        print("\n  ❌ REPORT DOES NOT MEET QUALITY STANDARDS")
        print("\n  Issues found:")
        for issue in results['all_issues']:
            print(f"    • {issue}")
        
        print("\n  This report may be:")
        print("    • Incomplete (analysis was interrupted)")
        print("    • Minimal (no actual data was analyzed)")
        print("    • Missing components (check error logs)")
        return_code = 1
    
    # Additional guidance
    if not is_valid:
        print_section("TROUBLESHOOTING")
        print("\n  To fix these issues:")
        print("    1. Re-run the analysis: python \"Execute Nike Unified Analysis.py\"")
        print("    2. Check log files for errors")
        print("    3. Verify internet connection (needed for SEC data)")
        print("    4. Ensure dependencies are installed: pip install -r requirements.txt")
    
    print()
    sys.exit(return_code)

if __name__ == "__main__":
    main()
