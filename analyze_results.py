"""
Analyze Nike 2019 Production Results from Log File
"""
import re
from collections import defaultdict

log_file = 'nike_2019_comprehensive_20251126_025700.log'

with open(log_file, 'r', encoding='utf-8') as f:
    log = f.read()

# Count violations by type
zero_dollar = len(re.findall(r'zero_dollar_transaction', log))
late_form4 = len(re.findall(r'late_form4', log))

# Count filings analyzed
form4_count = len(re.findall(r'\[\d+/86\] 4 \(', log))
form3_count = len(re.findall(r'\[\d+/86\] 3 \(', log))
tenk_count = len(re.findall(r'\[\d+/86\] 10-K \(', log))
tenq_count = len(re.findall(r'\[\d+/86\] 10-Q \(', log))
eightk_count = len(re.findall(r'\[\d+/86\] 8-K \(', log))

# Count violations detected per filing
summary_matches = re.findall(r'SUMMARY: (\d+) violations? detected', log)
total_violations = sum(int(x) for x in summary_matches)
filings_with_violations = len([x for x in summary_matches if int(x) > 0])

# Extract transaction counts
tx_found = re.findall(r'Found (\d+) transactions via lxml', log)
total_tx_parsed = sum(int(x) for x in tx_found)

print('='*70)
print('NIKE 2019 COMPREHENSIVE FORENSIC ANALYSIS - FINAL RESULTS')
print('='*70)
print()
print('FILINGS ANALYZED:')
print(f'  Total Filings Collected: 86')
print(f'  Form 4: {form4_count}')
print(f'  Form 3: {form3_count}')
print(f'  10-K: {tenk_count}')
print(f'  10-Q: {tenq_count}')
print(f'  8-K: {eightk_count}')
print()
print('TRANSACTION PARSING:')
print(f'  Total Transactions Parsed: {total_tx_parsed}')
print(f'  Average per Form 4: {total_tx_parsed/form4_count if form4_count > 0 else 0:.1f}')
print()
print('VIOLATIONS DETECTED:')
print(f'  Total Violations: {total_violations}')
print(f'  Filings with Violations: {filings_with_violations}')
print(f'  Zero-Dollar Transactions: {zero_dollar}')
print(f'  Late Form 4 Filings: {late_form4}')
print()
print('BENCHMARK COMPARISON:')
print(f'  Gold Standard Target: 54+ violations')
print(f'  Current System Detected: {total_violations} violations')
if total_violations >= 54:
    print(f'  Status: EXCEEDS BENCHMARK by {total_violations - 54}')
else:
    print(f'  Status: BELOW BENCHMARK by {54 - total_violations}')
print('='*70)

# Save results to file
with open('nike_2019_analysis_summary.txt', 'w') as f:
    f.write('NIKE 2019 COMPREHENSIVE FORENSIC ANALYSIS - FINAL RESULTS\n')
    f.write('='*70 + '\n\n')
    f.write(f'Total Filings: 86\n')
    f.write(f'Total Violations: {total_violations}\n')
    f.write(f'Filings with Violations: {filings_with_violations}\n')
    f.write(f'Zero-Dollar Transactions: {zero_dollar}\n')
    f.write(f'Late Form 4: {late_form4}\n')
    f.write(f'\nBenchmark Status: {"EXCEEDS" if total_violations >= 54 else "BELOW"}\n')

print('\nResults saved to: nike_2019_analysis_summary.txt')

