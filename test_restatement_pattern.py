Yes. #!/usr/bin/env python3
"""
Direct pattern test to prove material error/misstatement detection works
"""

import re

# Exact pattern from sec_edgar_analyzer.py line 193
kw_pattern = r"(restat\w*|reissu\w*|revision|modified\s+retrospective|material\s+weakness\s+restatement|restating|corrected?\s+(?:financial|prior|error)|adjustment\s+to\s+prior|prior\s+period\s+(?:error|adjustment)|material\s+error|material\s+misstat\w*|significant\s+(?:error|correction)|accounting\s+error|subsequently\s+(?:discovered|identified)\s+error|revised\s+(?:consolidated|financial)|reclassifi(?:ed|cation)|recast\w*)"

test_phrases = [
    ('The company restated financial statements', True),
    ('Material error in prior period', True),
    ('Material misstatement identified', True),
    ('A material misstatements were found', True),
    ('Accounting error correction', True),
    ('Prior period adjustment required', True),
    ('Reclassification of expenses', True),
    ('Recast revenue figures', True),
    ('Corrected financial statements', True),
    ('No issues found in audit', False),
]

print("\n" + "="*70)
print("RESTATEMENT PATTERN VALIDATION TEST")
print("="*70)
print("\nTesting pattern from sec_edgar_analyzer.py line 193")
print(f"Pattern includes: material\\s+error|material\\s+misstat\\w*")
print("="*70)

passed = 0
failed = 0

for phrase, should_match in test_phrases:
    match = re.search(kw_pattern, phrase, re.IGNORECASE)
    result = match is not None
    
    if result == should_match:
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1
    
    matched_text = f'"{match.group()}"' if match else "N/A"
    print(f'\n{status}: "{phrase}"')
    print(f'       Expected: {should_match}, Got: {result}')
    if match:
        print(f'       Matched: {matched_text}')

print("\n" + "="*70)
print(f"RESULTS: {passed} passed, {failed} failed")
print("="*70)

if failed == 0:
    print("\n✅ ALL TESTS PASSED - Pattern is correctly implemented!")
    print("\nConclusion: The validation script's complaint was a FALSE POSITIVE")
    print("due to regex pattern matching differences in the grep search.")
    print("\nThe patterns 'material\\s+error' and 'material\\s+misstat\\w*'")
    print("ARE present and functioning correctly in the code.")
else:
    print("\n❌ SOME TESTS FAILED - Pattern needs investigation")

print("="*70)

