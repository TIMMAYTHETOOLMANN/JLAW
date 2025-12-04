#!/usr/bin/env python3
"""
Quick validation to check that all remediation patches were applied correctly
"""

import re
from pathlib import Path

def check_file_contains(filepath, patterns, description):
    """Check if file contains all expected patterns"""
    print(f"\n{'='*60}")
    print(f"Checking: {description}")
    print(f"File: {filepath.name}")
    print(f"{'='*60}")
    
    content = filepath.read_text(encoding='utf-8')
    
    passed = 0
    for pattern, name in patterns:
        if re.search(pattern, content, re.DOTALL):
            print(f"  ✓ Found: {name}")
            passed += 1
        else:
            print(f"  ✗ Missing: {name}")
    
    print(f"\nResult: {passed}/{len(patterns)} checks passed")
    return passed == len(patterns)

def main():
    print("\n" + "="*60)
    print("JLAW REMEDIATION PATCH VALIDATION")
    print("="*60)
    
    project_root = Path(__file__).parent
    
    # Test 1: insider_form4_analyzer.py
    form4_file = project_root / "src" / "forensics" / "insider_form4_analyzer.py"
    form4_patterns = [
        (r"FEDERAL_HOLIDAYS_2019\s*=\s*\{", "FEDERAL_HOLIDAYS_2019 constant"),
        (r"FEDERAL_HOLIDAYS\s*=\s*\{", "FEDERAL_HOLIDAYS constant"),
        (r"datetime\(2019,\s*1,\s*21\)", "MLK Day 2019 in holidays"),
        (r"datetime\(2019,\s*11,\s*28\)", "Thanksgiving 2019 in holidays"),
        (r"def _is_federal_holiday\(self, dt: datetime\)", "_is_federal_holiday method"),
        (r"def _business_days_between.*?not self\._is_federal_holiday\(cur\)", "business_days with holiday check"),
        (r'filedAt.*?FILED-DATE.*?ACCEPTANCE-DATETIME', "Enhanced filing date extraction"),
        (r'periodOfReport as fallback - may be inaccurate', "Warning for periodOfReport fallback"),
    ]
    
    test1 = check_file_contains(form4_file, form4_patterns, "Fix 1: Late Form 4 Detection")
    
    # Test 2: sec_edgar_analyzer.py - Restatement patterns
    sec_file = project_root / "src" / "forensics" / "sec_edgar_analyzer.py"
    sec_patterns = [
        (r"corrected\?\\s\+\(\?:financial\|prior\|error\)", "Expanded restatement keywords - corrected"),
        (r"material\s\+error\|material\s\+misstat", "material error/misstatement"),
        (r"reclassifi\(\?:ed\|cation\)", "reclassification pattern"),
        (r"recast\\w\*", "recast pattern"),
        (r"ex311_patterns\s*=\s*\[", "ex311_patterns list"),
        (r"nke-ex311.*nke_ex311.*nkeex311", "Company-prefixed exhibit patterns"),
        (r"certceo.*ceocert.*302ceo", "Alternate CEO cert naming"),
        (r"ex312_patterns\s*=\s*\[", "ex312_patterns list"),
        (r"certcfo.*cfocert.*302cfo", "Alternate CFO cert naming"),
        (r"Fallback logic should trigger on pattern mismatch", "Fixed fallback logic comment"),
    ]
    
    test2 = check_file_contains(sec_file, sec_patterns, "Fix 2 & 3: Restatement & SOX 302 Detection")
    
    # Test 3: forensic_orchestrator.py
    orchestrator_file = project_root / "src" / "forensics" / "forensic_orchestrator.py"
    orchestrator_patterns = [
        (r'"8-K",\s*"8-K/A"', "8-K filing types"),
        (r'"SC 13G",\s*"SC 13G/A"', "SC 13G filing types"),
        (r'"SC 13D",\s*"SC 13D/A"', "SC 13D filing types"),
        (r'"DEF 14A",\s*"DEFA14A"', "DEF 14A filing types"),
        (r'"11-K",\s*"11-K/A"', "11-K filing types"),
        (r'"S-8",\s*"S-8/A"', "S-8 filing types"),
        (r'"424B2",\s*"424B5"', "424B prospectus types"),
        (r'"FWP"', "FWP filing type"),
        (r'EXPANDED.*comprehensive filing types', "Expanded filing types comment"),
    ]
    
    test3 = check_file_contains(orchestrator_file, orchestrator_patterns, "Fix 4: Filing Collection Gap")
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    results = {
        "Fix 1: Late Form 4 Detection (Federal Holidays)": test1,
        "Fix 2 & 3: Restatement & SOX 302 Detection": test2,
        "Fix 4: Filing Collection Gap": test3,
    }
    
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {status}: {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
        print("="*60)
        print("\nAll remediation patches have been successfully applied!")
        print("\nExpected improvements:")
        print("  • Late Form 4: 7 → 25-30 violations")
        print("  • Restatements: 0 → 4-6 violations")
        print("  • SOX 302: 0 → 1 violation")
        print("  • Filing Coverage: 71 → 85-90 filings")
        print("  • TOTAL: 77 → 100+ violations (30%+ improvement)")
        print("\nNext steps:")
        print("  1. Run: python jlaw_forensics.py --config config/nike_2019.yaml")
        print("  2. Compare results against baseline")
        print("  3. Verify enhanced detection rates")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("="*60)
        print("\nPlease review the output above for details.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

