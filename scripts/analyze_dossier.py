#!/usr/bin/env python3
"""Analyze dossier for penalty breakdown."""

import json
import sys

def analyze_dossier(filepath):
    with open(filepath, 'r') as f:
        d = json.load(f)

    violations = d.get('violations', [])
    print(f'Total violations: {len(violations)}')

    print('\nSearching for Section 10(b) / restatement / SOX violations:')
    found_high_value = False
    for v in violations:
        vtype = v.get('violation_type', '')
        if 'Section 10' in vtype or 'restatement' in vtype.lower() or 'SOX' in vtype or 'Material' in vtype:
            print(f"  Found: {vtype} - ${v.get('estimated_penalty', 0):,.0f}")
            found_high_value = True

    if not found_high_value:
        print("  None found - this is why penalties are low!")

    print('\nPenalty summary by violation type:')
    penalty_types = {}
    for v in violations:
        vt = v.get('violation_type', 'Unknown')
        penalty = v.get('estimated_penalty', 0)
        if vt not in penalty_types:
            penalty_types[vt] = {'count': 0, 'total': 0}
        penalty_types[vt]['count'] += 1
        penalty_types[vt]['total'] += penalty

    for vt, data in sorted(penalty_types.items(), key=lambda x: -x[1]['total']):
        print(f"  {vt}: {data['count']} violations, ${data['total']:,.0f}")

    print(f"\nTotal estimated penalties: ${sum(v.get('estimated_penalty', 0) for v in violations):,.0f}")

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'output/DOSSIER_320187_20251225_204409.json'
    analyze_dossier(filepath)

