import re

# Read log file
with open('nike_2019_comprehensive_20251126_025700.log', 'r', encoding='utf-8', errors='ignore') as f:
    log = f.read()

# Count violations
summaries = re.findall(r'SUMMARY: (\d+) violations? detected', log)
total_violations = sum(int(x) for x in summaries)
filings_with_violations = len([x for x in summaries if int(x) > 0])

# Count by type
zero_dollar = len(re.findall(r'- zero_dollar_transaction:', log))
late_form4 = len(re.findall(r'- late_form4:', log))

# Count filings
form4_analyzed = len(re.findall(r'\[\d+/86\] 4 \(', log))

print("="*60)
print("NIKE 2019 COMPREHENSIVE FORENSIC ANALYSIS - FINAL RESULTS")
print("="*60)
print()
print(f"FILINGS ANALYZED:")
print(f"  Form 4 Filings: {form4_analyzed}")
print(f"  Filings with Violations: {filings_with_violations}")
print()
print(f"VIOLATIONS DETECTED:")
print(f"  Total Violations: {total_violations}")
print(f"  Zero-Dollar Transactions: {zero_dollar}")
print(f"  Late Form 4 Filings: {late_form4}")
print()
print(f"BENCHMARK COMPARISON:")
print(f"  Gold Standard Target: 54+ violations")
print(f"  Current System: {total_violations} violations")
print(f"  Status: {'EXCEEDS BENCHMARK' if total_violations >= 54 else 'BELOW BENCHMARK'}")
print()
print("="*60)

# Write to file
with open('FINAL_RESULTS.txt', 'w') as f:
    f.write(f"Total Violations: {total_violations}\n")
    f.write(f"Zero-Dollar: {zero_dollar}\n")
    f.write(f"Late Form 4: {late_form4}\n")
    f.write(f"Status: {'EXCEEDS' if total_violations >= 54 else 'BELOW'}\n")

print("\nResults saved to FINAL_RESULTS.txt")

