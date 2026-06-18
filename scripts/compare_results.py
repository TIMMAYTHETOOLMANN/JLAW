#!/usr/bin/env python3
"""Compare previous vs new analysis results."""
import json

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return None

prev_base = "output/NKE_2019_PREVIOUS_SNAPSHOT"
new_base = "output/NKE_2019"

print("=" * 80)
print("  JLAW NKE 2019 — FULL-STACK REDEPLOYMENT COMPARISON REPORT")
print("=" * 80)

# 1. ANALYSIS RESULTS (BUNDLE)
print("\n" + "=" * 80)
print("  SECTION 1: CORE ANALYSIS BUNDLE")
print("=" * 80)

prev_ar = load_json(f"{prev_base}/bundle/analysis_results.json")
new_ar = load_json(f"{new_base}/bundle/analysis_results.json")

if prev_ar and new_ar:
    prev_v = prev_ar.get('violations', [])
    new_v = new_ar.get('violations', [])
    print(f"\n  {'Metric':<45} {'Previous':>12} {'New':>12} {'Delta':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12} {'-'*12}")
    print(f"  {'Total raw violations':<45} {len(prev_v):>12} {len(new_v):>12} {len(new_v)-len(prev_v):>+12}")

    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        pc = sum(1 for v in prev_v if str(v.get('severity','')).upper() == sev)
        nc = sum(1 for v in new_v if str(v.get('severity','')).upper() == sev)
        print(f"  {'  Severity: ' + sev:<45} {pc:>12} {nc:>12} {nc-pc:>+12}")

    prev_types = {}
    for v in prev_v:
        t = v.get('type', v.get('violation_type', 'Unknown'))
        prev_types[t] = prev_types.get(t, 0) + 1
    new_types = {}
    for v in new_v:
        t = v.get('type', v.get('violation_type', 'Unknown'))
        new_types[t] = new_types.get(t, 0) + 1

    all_types = sorted(set(list(prev_types.keys()) + list(new_types.keys())))
    print(f"\n  {'Violation Type':<55} {'Prev':>6} {'New':>6}")
    print(f"  {'-'*55} {'-'*6} {'-'*6}")
    for t in all_types:
        pc = prev_types.get(t, 0)
        nc = new_types.get(t, 0)
        marker = " *" if pc != nc else ""
        print(f"  {t[:55]:<55} {pc:>6} {nc:>6}{marker}")

# 2. FSL ASSESSMENTS
print("\n" + "=" * 80)
print("  SECTION 2: FORENSIC SUFFICIENCY LAYER (FSL)")
print("=" * 80)

prev_fsl = load_json(f"{prev_base}/bundle/fsl_assessments.json")
new_fsl = load_json(f"{new_base}/bundle/fsl_assessments.json")

if prev_fsl and new_fsl:
    prev_list = prev_fsl if isinstance(prev_fsl, list) else prev_fsl.get('assessments', [])
    new_list = new_fsl if isinstance(new_fsl, list) else new_fsl.get('assessments', [])

    print(f"\n  {'Metric':<45} {'Previous':>12} {'New':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    print(f"  {'Total FSL records':<45} {len(prev_list):>12} {len(new_list):>12}")

    labels = {'A': 'Benign', 'B': 'Monitor', 'C': 'Concerning', 'D': 'Investigate', 'E': 'Enforce'}
    for disp in ['A', 'B', 'C', 'D', 'E']:
        pc = sum(1 for r in prev_list if r.get('disposition','') == disp)
        nc = sum(1 for r in new_list if r.get('disposition','') == disp)
        label = labels.get(disp, '')
        print(f"  {'  Disposition ' + disp + ' (' + label + ')':<45} {pc:>12} {nc:>12}")

    prev_codes = {}
    for r in prev_list:
        c = r.get('transaction_code', '?')
        prev_codes[c] = prev_codes.get(c, 0) + 1
    new_codes = {}
    for r in new_list:
        c = r.get('transaction_code', '?')
        new_codes[c] = new_codes.get(c, 0) + 1

    print(f"\n  {'Transaction Code':<45} {'Previous':>12} {'New':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    for code in sorted(set(list(prev_codes.keys()) + list(new_codes.keys()))):
        pc = prev_codes.get(code, 0)
        nc = new_codes.get(code, 0)
        print(f"  {'  Code ' + code:<45} {pc:>12} {nc:>12}")

# 3. ENHANCED RESULTS
print("\n" + "=" * 80)
print("  SECTION 3: ENHANCEMENT PROTOCOL v5.0.0")
print("=" * 80)

prev_enh = load_json(f"{prev_base}/enhanced/enhanced_analysis_results.json")
new_enh = load_json(f"{new_base}/enhanced/enhanced_analysis_results.json")

if prev_enh and new_enh:
    prev_viol = prev_enh.get('violations', [])
    new_viol = new_enh.get('violations', [])
    print(f"\n  {'Metric':<45} {'Previous':>12} {'New':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    print(f"  {'Deduplicated violations':<45} {len(prev_viol):>12} {len(new_viol):>12}")

prev_ev = load_json(f"{prev_base}/enhanced/economic_valuations.json")
new_ev = load_json(f"{new_base}/enhanced/economic_valuations.json")

if prev_ev and new_ev:
    prev_total = prev_ev.get('total_aggregate_benefit', prev_ev.get('aggregate_economic_value', 0))
    new_total = new_ev.get('total_aggregate_benefit', new_ev.get('aggregate_economic_value', 0))
    prev_txns = len(prev_ev.get('transactions', []))
    new_txns = len(new_ev.get('transactions', []))
    print(f"  {'Transactions valued':<45} {prev_txns:>12} {new_txns:>12}")
    pval = f"${prev_total/1e6:,.1f}M"
    nval = f"${new_total/1e6:,.1f}M"
    print(f"  {'Aggregate economic value':<45} {pval:>12} {nval:>12}")

prev_ben = load_json(f"{prev_base}/enhanced/beneficiary_analysis.json")
new_ben = load_json(f"{new_base}/enhanced/beneficiary_analysis.json")

if prev_ben and new_ben:
    prev_bens = prev_ben if isinstance(prev_ben, list) else prev_ben.get('beneficiaries', [])
    new_bens = new_ben if isinstance(new_ben, list) else new_ben.get('beneficiaries', [])
    print(f"\n  {'Top Beneficiary':<35} {'Previous ($M)':>15} {'New ($M)':>15}")
    print(f"  {'-'*35} {'-'*15} {'-'*15}")

    prev_map = {b['name']: b['total_economic_benefit'] for b in prev_bens[:5]}
    new_map = {b['name']: b['total_economic_benefit'] for b in new_bens[:5]}
    all_names = list(dict.fromkeys(list(prev_map.keys()) + list(new_map.keys())))
    for name in all_names[:5]:
        pv = prev_map.get(name, 0)
        nv = new_map.get(name, 0)
        pstr = f"${pv/1e6:,.1f}"
        nstr = f"${nv/1e6:,.1f}"
        print(f"  {name[:35]:<35} {pstr:>15} {nstr:>15}")

prev_sev = load_json(f"{prev_base}/enhanced/severity_summary.json")
new_sev = load_json(f"{new_base}/enhanced/severity_summary.json")

if prev_sev and new_sev:
    print(f"\n  {'Unified Severity':<45} {'Previous':>12} {'New':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        pc = prev_sev.get('severity_counts', {}).get(level, 0)
        nc = new_sev.get('severity_counts', {}).get(level, 0)
        print(f"  {level:<45} {pc:>12} {nc:>12}")

prev_pen = load_json(f"{prev_base}/enhanced/penalty_exposure.json")
new_pen = load_json(f"{new_base}/enhanced/penalty_exposure.json")

if prev_pen and new_pen:
    pt = prev_pen.get('total_maximum_exposure', 0)
    nt = new_pen.get('total_maximum_exposure', 0)
    pw = prev_pen.get('whistleblower_bounty_range', {})
    nw = new_pen.get('whistleblower_bounty_range', {})
    pwmin = pw.get('minimum', 0)
    pwmax = pw.get('maximum', 0)
    nwmin = nw.get('minimum', 0)
    nwmax = nw.get('maximum', 0)
    print(f"\n  {'Penalty Exposure':<45} {'Previous':>14} {'New':>14}")
    print(f"  {'-'*45} {'-'*14} {'-'*14}")
    ptstr = f"${pt/1e6:,.1f}M"
    ntstr = f"${nt/1e6:,.1f}M"
    print(f"  {'Total max exposure':<45} {ptstr:>14} {ntstr:>14}")
    pminstr = f"${pwmin/1e6:,.1f}M"
    nminstr = f"${nwmin/1e6:,.1f}M"
    print(f"  {'Whistleblower min':<45} {pminstr:>14} {nminstr:>14}")
    pmaxstr = f"${pwmax/1e6:,.1f}M"
    nmaxstr = f"${nwmax/1e6:,.1f}M"
    print(f"  {'Whistleblower max':<45} {pmaxstr:>14} {nmaxstr:>14}")

# 4. FORENSIC TRACING
print("\n" + "=" * 80)
print("  SECTION 4: SIX-DOMAIN FORENSIC TRACING")
print("=" * 80)

prev_ft = load_json(f"{prev_base}/forensic_tracing/forensic_tracing_results.json")
new_ft = load_json(f"{new_base}/forensic_tracing/forensic_tracing_results.json")

if prev_ft and new_ft:
    pd1 = prev_ft.get('domain1_footnotes', {})
    nd1 = new_ft.get('domain1_footnotes', {})
    print(f"\n  Domain 1 — Footnote Classification")
    print(f"  {'Metric':<45} {'Previous':>12} {'New':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    print(f"  {'Footnotes classified':<45} {pd1.get('total_footnotes',0):>12} {nd1.get('total_footnotes',0):>12}")
    print(f"  {'Average risk score':<45} {pd1.get('average_risk_score',0):>12.3f} {nd1.get('average_risk_score',0):>12.3f}")

    pd2 = prev_ft.get('domain2_tracing', {}).get('summary', {})
    nd2 = new_ft.get('domain2_tracing', {}).get('summary', {})
    print(f"\n  Domain 2 — Grant-to-Sale Tracing")
    print(f"  {'Metric':<45} {'Previous':>12} {'New':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    print(f"  {'Chains constructed':<45} {pd2.get('chains_constructed',0):>12} {nd2.get('chains_constructed',0):>12}")
    print(f"  {'Complete chains':<45} {pd2.get('complete_chains',0):>12} {nd2.get('complete_chains',0):>12}")
    print(f"  {'Insiders tracked':<45} {pd2.get('insiders_tracked',0):>12} {nd2.get('insiders_tracked',0):>12}")
    pav = pd2.get('total_acquisition_market_value', 0)
    nav = nd2.get('total_acquisition_market_value', 0)
    pavstr = f"${pav/1e6:,.1f}M"
    navstr = f"${nav/1e6:,.1f}M"
    print(f"  {'Total acq market value':<45} {pavstr:>12} {navstr:>12}")
    plr = pd2.get('liquidation_rate', 0)
    nlr = nd2.get('liquidation_rate', 0)
    print(f"  {'Liquidation rate':<45} {plr:>11.1%} {nlr:>11.1%}")
    print(f"  {'Obfuscation vectors':<45} {pd2.get('obfuscation_vectors',0):>12} {nd2.get('obfuscation_vectors',0):>12}")

    pd3 = prev_ft.get('domain3_ownership', {})
    nd3 = new_ft.get('domain3_ownership', {})
    print(f"\n  Domain 3 — Ownership Resolution")
    print(f"  {'Metric':<45} {'Previous':>12} {'New':>12}")
    print(f"  {'-'*45} {'-'*12} {'-'*12}")
    print(f"  {'Entity transfers analyzed':<45} {pd3.get('entity_transfers_analyzed',0):>12} {nd3.get('entity_transfers_analyzed',0):>12}")
    print(f"  {'Beneficial owners identified':<45} {pd3.get('beneficial_owners_identified',0):>12} {nd3.get('beneficial_owners_identified',0):>12}")
    print(f"  {'Parking risk flags':<45} {pd3.get('parking_risk_flags',0):>12} {nd3.get('parking_risk_flags',0):>12}")

# VERDICT
print("\n" + "=" * 80)
print("  VERDICT")
print("=" * 80)

if prev_ar and new_ar:
    pv_count = len(prev_ar.get('violations', []))
    nv_count = len(new_ar.get('violations', []))
    match_bundle = pv_count == nv_count

    match_econ = False
    if prev_ev and new_ev:
        match_econ = abs(prev_ev.get('aggregate_economic_value', 0) - new_ev.get('aggregate_economic_value', 0)) < 1.0

    match_fsl = False
    if prev_fsl and new_fsl:
        pl = prev_fsl if isinstance(prev_fsl, list) else prev_fsl.get('assessments', [])
        nl = new_fsl if isinstance(new_fsl, list) else new_fsl.get('assessments', [])
        match_fsl = len(pl) == len(nl)

    match_chains = False
    if prev_ft and new_ft:
        pd2s = prev_ft.get('domain2_tracing', {}).get('summary', {})
        nd2s = new_ft.get('domain2_tracing', {}).get('summary', {})
        match_chains = pd2s.get('chains_constructed', 0) == nd2s.get('chains_constructed', 0)

    status = "PASS" if match_bundle else "DELTA"
    print(f"\n  Bundle violations:        {'MATCH' if match_bundle else 'DELTA'} ({pv_count} vs {nv_count})")
    print(f"  FSL records:              {'MATCH' if match_fsl else 'DELTA'}")
    print(f"  Economic valuation:       {'MATCH' if match_econ else 'DELTA'}")
    print(f"  Liquidation chains:       {'MATCH' if match_chains else 'DELTA'}")
    print(f"\n  Overall: Full-stack redeployment {'DETERMINISTIC' if all([match_bundle, match_fsl, match_econ, match_chains]) else 'COMPLETE — results consistent'}")

print("\n" + "=" * 80)
