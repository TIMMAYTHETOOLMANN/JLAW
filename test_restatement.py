#!/usr/bin/env python3
"""Test restatement detection patterns."""

import re

test_text = '''
The Company has restated its financial statements for the year ended December 31, 2019 due to errors 
in revenue recognition. This restatement resulted in a material misstatement of approximately $50 million.
'''

restatement_patterns = [
    r'(?i)(?:financial\s+)?restatement\s+of\s+(?:financial\s+)?(?:statements?|results|earnings)',
    r'(?i)correction\s+of\s+(?:an?\s+)?error\s+in\s+(?:previously\s+)?(?:issued|reported)',
    r'(?i)restated\s+(?:financial\s+)?statements?\s+for\s+(?:the\s+)?(?:year|quarter|period)',
    r'(?i)(?:we|the\s+company)\s+(?:have\s+)?restated\s+(?:our|its)\s+(?:financial|prior)',
    r'(?i)material\s+misstatement.*(?:restat|correct)',
]

print('Testing restatement detection patterns...')
for i, pattern in enumerate(restatement_patterns):
    match = re.search(pattern, test_text)
    if match:
        print(f'  Pattern {i+1} MATCHED: {match.group()}')

# Test on NIKE-like text with Restated Articles
false_positive_text = '''
3.1 Restated Articles of Incorporation, as amended (incorporated by reference to Exhibit 3.1)
3.2 Fifth Restated Bylaws, as amended (incorporated by reference to Exhibit 3.2)
'''

print()
print('Testing on NIKE-like text (should NOT match):')
for i, pattern in enumerate(restatement_patterns):
    match = re.search(pattern, false_positive_text)
    if match:
        print(f'  Pattern {i+1} MATCHED (FALSE POSITIVE): {match.group()}')
    else:
        print(f'  Pattern {i+1}: No match (correct)')

