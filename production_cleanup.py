"""
Production Pre-Deployment Cleanup Script
=========================================

Removes all non-essential files:
- Old markdown documentation
- Previous analysis logs and results
- Test/demo scripts
- Interim summaries and status reports

KEEPS:
- Core src/ modules (latest production code)
- BENCHMARK_GOLDSTANDARD.md (for comparison)
- Production scripts (nike_2019_comprehensive_production.py)
- Configuration files (.env, requirements.txt)
- Evidence-backed reporting documentation (latest)

Author: JARVIS NEXUS
Date: November 26, 2025
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Root directory
ROOT = Path("C:/Users/timot/IdeaProjects/JLAW")

# Files/directories to DELETE
DELETE_PATTERNS = {
    # Old markdown documentation (interim summaries)
    "markdown_docs": [
        "ADVANCED_ANALYTICS_MODULE_1_SUMMARY.md",
        "ADVANCED_STATUTE_INTEGRATION_CHECKLIST.md",
        "ADVANCED_STATUTE_INTEGRATION_COMPLETE.md",
        "ADVANCED_STATUTE_INTEGRATION_QUICK_REFERENCE.md",
        "ADVANCED_STATUTE_INTEGRATION_SUMMARY.md",
        "AGENT_SDK_PHASE_2_3_COMPLETE.md",
        "AGENT_SDK_QUICK_STATUS.md",
        "AGENTS.md",
        "ALL_6_PHASES_COMPLETE.md",
        "ALL_7_PHASES_COMPLETE.md",
        "ALL_8_PHASES_COMPLETE.md",
        "ALL_9_PHASES_COMPLETE.md",
        "ALL_PHASES_100_PERCENT.md",
        "API_SETUP.md",
        "CLAUDE.md",
        "COMPLETE_INTEGRATION_MAP.md",
        "COMPLETE_REQUIREMENT_VERIFICATION.md",
        "COMPLIANCE_ANALYZER_ENHANCEMENT.md",
        "COMPLIANCE_ENHANCEMENT_SUMMARY.md",
        "CONFIG_SUMMARY.md",
        "ENCODING_ISSUE_RESOLUTION.md",
        "ENHANCEMENT_SUMMARY.md",
        "ENHANCEMENT_VERIFICATION_COMPLETE.md",
        "GOVINFO_API_500_ERROR_RESOLUTION.md",
        "GOVINFO_COMPLETE_INTEGRATION_MASTER.md",
        "GOVINFO_IMPLEMENTATION_SUMMARY.md",
        "GOVINFO_OFFICIAL_API_IMPLEMENTATION.md",
        "GOVINFO_PACKAGES_API_COMPLETE.md",
        "GOVINFO_PUBLISHED_API_INTEGRATION.md",
        "GOVINFO_RELATED_API_INTEGRATION.md",
        "GOVINFO_SEARCH_API_GUIDE.md",
        "GOVINFO_SEARCH_API_INTEGRATION_SUMMARY.md",
        "HOLY_GRAIL_INTEGRATION.md",
        "IMPLEMENTATION_COMPLETE_SUMMARY.md",
        "MASTER_STATUS.md",
        "MISSING_OPENAI_AGENT_SDK_ANALYSIS.md",
        "MISSION_ACCOMPLISHED.md",
        "MODULES_1_AND_2_COMPLETE.md",
        "MODULES_3_AND_4_COMPLETE.md",
        "MODULE_2_OPTIMIZATIONS_COMPLETE.md",
        "MULTIAGENT_AI_INTEGRATION_COMPLETE.md",
        "MULTIAGENT_QUICK_REFERENCE.md",
        "NIKE_2019_FINAL_VERIFIED_RESULTS.md",
        "NIKE_2019_MISSION_REPORT.md",
        "NIST_MODULE_2_SUMMARY.md",
        "NITS_VANTABLACK_IMPLEMENTATION_SUMMARY.md",
        "OPENAI_AGENT_SDK_INTEGRATION_COMPLETE.md",
        "OPENAI_AGENT_SDK_QUICK_REFERENCE.md",
        "PHASE_1_COMPLETE_STATUS.md",
        "PHASE_1_DEPLOYMENT_COMPLETE.md",
        "PHASE_1_QUICK_REFERENCE.md",
        "PHASE_1_REALWORLD_VALIDATION.md",
        "PHASE_2_COMPLETE.md",
        "PHASE_2_COMPLETE_SUMMARY.md",
        "PHASE_2_INTELLIGENCE_README.md",
        "PHASE_2_QUICK_REFERENCE.md",
        "PHASE_3_COMPLETE.md",
        "PHASE_4_COMPLETE.md",
        "PHASE_4_FINAL_SUMMARY.md",
        "PHASE_4_INITIALIZATION_SUMMARY.md",
        "PHASE_4_QUICK_REFERENCE.md",
        "PHASE_5_DEPLOYMENT_COMPLETE.md",
        "PHASE_6_DEPLOYMENT_COMPLETE.md",
        "PHASE_7_DEPLOYMENT_COMPLETE.md",
        "PHASE_8_DEPLOYMENT_COMPLETE.md",
        "PHASE_9_DEPLOYMENT_COMPLETE.md",
        "PHASE_TESTING_STATUS.md",
        "PRIORITY_1_ENHANCEMENTS_COMPLETE.md",
        "QUICK_REFERENCE.md",
        "QUICK_START_OPERATIONAL_GUIDE.md",
        "SEC_EXTRACTION_ENHANCEMENT.md",
        "STRICT_API_MODE_NO_FALLBACK.md",
        "SYSTEM_VALIDATION_COMPLETE_100_PERCENT.md",
        "UNIFIED_SYSTEM_STATUS.md",
    ],
    
    # Previous analysis results/logs
    "old_results": [
        "benchmark_analysis.txt",
        "forensic_20251123.log",
        "forensic_20251124.log",
        "forensic_20251125.log",
        "full_integration_validation_20251125_012335.log",
        "full_integration_validation_20251125_012424.log",
        "full_integration_validation_20251125_012530.log",
        "full_integration_validation_20251125_012616.log",
        "latest_results_formatted.json",
        "nike_2019_comprehensive_20251126_024716.log",
        "nike_2019_comprehensive_20251126_025700.log",
        "nike_2019_final_analysis.json",
        "nike_2019_production_results.json",
        "nike_2019_production_results_run1.json",
        "nike_2019_production_results_run2.json",
        "nike_2019_production_v2.json",
        "nike_2019_run.log",
        "nike_2019_run_log.txt",
        "phase6_output.txt",
        "validation_report_20251125_012356.json",
        "validation_report_20251125_012438.json",
        "validation_report_20251125_012544.json",
        "validation_report_20251125_012630.json",
    ],
    
    # Test/demo scripts (old)
    "old_scripts": [
        "analyze_results.py",
        "count_violations.py",
        "create_phase2_modules.py",
        "demo_phase1_parsing.py",
        "demo_phase2_intelligence.py",
        "demo_phase4_temporal.py",
        "demo_phase5_decision.py",
        "demo_phase6_contradictions.py",
        "demo_phase7_reporting.py",
        "demo_phase8_integration.py",
        "demo_phase9_deployment.py",
        "examples_enhanced_forensics.py",
        "jlaw_enhanced.py",
        "nike_2019_investigation.py",
        "nike_2019_production_run.py",
        "test_advanced_statute_integrator.py",
        "test_compliance_analyzer.py",
        "test_filing_collection.py",
        "test_form4_diagnostic.py",
        "test_form4_fix.py",
        "test_full_integration.py",
        "test_govinfo_api.py",
        "test_govinfo_official_api.py",
        "test_govinfo_packages_api.py",
        "test_govinfo_published_api.py",
        "test_govinfo_related_api.py",
        "test_govinfo_search_api.py",
        "test_holy_grail_single.py",
        "test_modules_3_and_4.py",
        "test_module_2_optimizations.py",
        "test_module_2_quick.py",
        "test_module_quick.py",
        "test_phase1_complete.py",
        "test_phase1_realworld.py",
        "test_phase1_sync.py",
        "test_phase2_intelligence.py",
        "test_phase3_comprehensive.py",
        "test_phase6_quick.py",
        "test_phase7_quick.py",
        "test_phase8_quick.py",
        "test_phase9_quick.py",
        "test_sec_api_key.py",
        "test_sec_connection.py",
        "test_sec_extraction.py",
        "test_single_filing.py",
        "test_strict_api_mode.py",
        "test_temporal_reconciliation.py",
        "validate_enhancements.py",
        "validate_full_integration.py",
        "validate_phase1.py",
        "verify_agent_integration.py",
        "verify_directive_visibility.py",
        "verify_multiagent_integration.py",
        "verify_phase1.py",
        "verify_phase1_fast.py",
        "verify_phase2.py",
        "verify_phase3.py",
        "verify_phase4.py",
        "verify_phase5.py",
    ],
    
    # Interim status files
    "status_files": [
        "MASTER_IMPLEMENTATION_STATUS.txt",
        "MISSION_ACCOMPLISHED_100_PERCENT.txt",
        "PHASE_2_MISSION_ACCOMPLISHED.txt",
        "PHASE_2_STATUS_PLAIN.txt",
        "STATUS_REPORT.txt",
        "STATUS_REPORT_PHASE_2.txt",
    ],
    
    # Sample/test data
    "sample_data": [
        "edgar_search.html",
        "sample_form4.xml",
        "sample_form4_raw.txt",
    ],
    
    # Old backend/frontend (if not using MCP)
    "old_mcp": [
        "mcp_forensics_backend",
        "mcp_forensics_frontend",
    ]
}

# Files to KEEP (explicit whitelist)
KEEP_FILES = {
    # Core documentation
    "BENCHMARK_GOLDSTANDARD.md",  # ← For comparison
    "EVIDENCE_BACKED_REPORTING_SYSTEM.md",  # ← Latest evidence framework
    "EVIDENCE_BACKED_SYSTEM_IMPLEMENTATION_GUIDE.md",  # ← Latest guide
    "README.md",
    "LICENSE",
    
    # Production scripts
    "nike_2019_comprehensive_production.py",
    "jlaw_forensics.py",
    "convert_nike_to_evidence_backed.py",
    
    # Configuration
    ".env",
    ".gitignore",
    "requirements.txt",
    "requirements_enhancements.txt",
    "pyproject.toml",
    "uv.lock",
    
    # Essential directories
    "src",
    "docs",
    "examples",
    "tests",
    "dossiers",
    "forensic_storage",
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
}

def should_delete(path: Path) -> bool:
    """Determine if a file/directory should be deleted."""
    name = path.name
    
    # Never delete whitelisted items
    if name in KEEP_FILES:
        return False
    
    # Check if in any delete pattern
    for category, patterns in DELETE_PATTERNS.items():
        if name in patterns:
            return True
    
    return False

def cleanup():
    """Execute cleanup operation."""
    print("="*80)
    print(" " * 20 + "PRODUCTION CLEANUP - PRE-DEPLOYMENT")
    print("="*80)
    print()
    
    # Track statistics
    deleted_files = []
    deleted_dirs = []
    kept_files = []
    errors = []
    
    # Get all items in root
    items = list(ROOT.iterdir())
    
    print(f"📂 Scanning {len(items)} items in repository root...")
    print()
    
    for item in items:
        try:
            if should_delete(item):
                if item.is_file():
                    print(f"❌ DELETE FILE: {item.name}")
                    item.unlink()
                    deleted_files.append(item.name)
                elif item.is_dir():
                    print(f"❌ DELETE DIR:  {item.name}/")
                    shutil.rmtree(item)
                    deleted_dirs.append(item.name)
            else:
                if item.is_file():
                    print(f"✅ KEEP:        {item.name}")
                    kept_files.append(item.name)
                elif item.is_dir():
                    print(f"✅ KEEP:        {item.name}/")
        except Exception as e:
            error_msg = f"Error processing {item.name}: {e}"
            print(f"⚠️  ERROR:      {error_msg}")
            errors.append(error_msg)
    
    # Summary
    print()
    print("="*80)
    print(" " * 30 + "CLEANUP SUMMARY")
    print("="*80)
    print()
    print(f"📊 STATISTICS:")
    print(f"   Files Deleted:       {len(deleted_files)}")
    print(f"   Directories Deleted: {len(deleted_dirs)}")
    print(f"   Files Kept:          {len(kept_files)}")
    print(f"   Errors:              {len(errors)}")
    print()
    
    if deleted_files:
        print(f"🗑️  DELETED FILES ({len(deleted_files)}):")
        for f in sorted(deleted_files)[:20]:  # Show first 20
            print(f"   - {f}")
        if len(deleted_files) > 20:
            print(f"   ... and {len(deleted_files) - 20} more")
        print()
    
    if deleted_dirs:
        print(f"🗑️  DELETED DIRECTORIES ({len(deleted_dirs)}):")
        for d in sorted(deleted_dirs):
            print(f"   - {d}/")
        print()
    
    if errors:
        print(f"⚠️  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"   - {e}")
        print()
    
    print("✅ CLEANUP COMPLETE - REPOSITORY STREAMLINED")
    print()
    print("📋 KEPT ESSENTIAL FILES:")
    print("   - BENCHMARK_GOLDSTANDARD.md (for comparison)")
    print("   - EVIDENCE_BACKED_REPORTING_SYSTEM.md (latest framework)")
    print("   - nike_2019_comprehensive_production.py (production script)")
    print("   - jlaw_forensics.py (main entry point)")
    print("   - src/ (core modules)")
    print("   - .env, requirements.txt (configuration)")
    print()
    print("🚀 READY FOR PRODUCTION DEPLOYMENT")
    print()
    print("="*80)
    
    # Save cleanup report
    report_file = ROOT / f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write("PRODUCTION CLEANUP REPORT\n")
        f.write("="*80 + "\n\n")
        f.write(f"Date: {datetime.now().isoformat()}\n\n")
        f.write(f"Files Deleted: {len(deleted_files)}\n")
        f.write(f"Directories Deleted: {len(deleted_dirs)}\n")
        f.write(f"Files Kept: {len(kept_files)}\n")
        f.write(f"Errors: {len(errors)}\n\n")
        f.write("DELETED FILES:\n")
        for f_name in sorted(deleted_files):
            f.write(f"  - {f_name}\n")
        f.write("\nDELETED DIRECTORIES:\n")
        for d_name in sorted(deleted_dirs):
            f.write(f"  - {d_name}/\n")
        if errors:
            f.write("\nERRORS:\n")
            for err in errors:
                f.write(f"  - {err}\n")
    
    print(f"📄 Cleanup report saved: {report_file.name}")
    print()

if __name__ == "__main__":
    try:
        response = input("⚠️  WARNING: This will DELETE files and directories. Continue? (yes/no): ")
        if response.lower() == 'yes':
            cleanup()
        else:
            print("❌ Cleanup cancelled")
    except KeyboardInterrupt:
        print("\n❌ Cleanup cancelled")

