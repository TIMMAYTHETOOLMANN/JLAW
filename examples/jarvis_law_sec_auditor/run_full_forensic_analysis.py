"""
JARVIS:LAW - COMPLETE FORENSIC ANALYSIS
Full analysis of 10 Form 4 filings from 2019 with:
- Surgical data extraction
- CORE ENHANCEMENT MODULES (MANDATORY):
  * Zero-Dollar Pattern Amplifier
  * 10b5-1 Compliance Verifier
  * Insider Role Risk Weighting
  * Earnings Event Correlator
- Fraud pattern detection
- Visual analytics (timeline, heatmaps)
- Human-readable reports
- JSON forensic receipts
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import re

sys.path.insert(0, str(Path(__file__).parent))

from form4_html_parser import Form4HTMLParser

# CORE ENHANCEMENT MODULES - MANDATORY IMPORTS
from tools.zero_dollar_detector import detect_zero_dollar_risk, analyze_zero_dollar_patterns
from tools.verify_10b5_plan import check_10b5_plan, verify_cooling_off_period
from tools.risk_weighting import (
    weight_risk_score, 
    extract_role_from_relationship, 
    assess_role_specific_risk, 
    rank_insiders_by_risk
)
from tools.earnings_window import (
    load_earnings_calendar,
    correlate_all_transactions,
    analyze_earnings_proximity,
    detect_clustered_trading
)

# Configuration
OUTPUT_DIR = Path(__file__).parent / "memory/forensic_analysis"
CALIBRATION_DIR = Path(__file__).parent / "memory/calibration_runs"
FILING_DIR = Path(__file__).parent / "memory/sec_filings_archive"
DATA_DIR = Path(__file__).parent / "data"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONTROL_GROUP = [
    "0000320187_4_2019-12-31_000112760219035995.xml",
    "0000320187_4_2019-12-26_000112760219035842.xml",
    "0000320187_4_2019-12-26_000112760219035840.xml",
    "0000320187_4_2019-12-03_000112760219034173.xml",
    "0000320187_4_2019-11-15_000112760219032863.xml",
    "0000320187_4_2019-10-31_000112760219031375.xml",
    "0000320187_4_2019-10-31_000112760219031373.xml",
    "0000320187_4_2019-10-31_000112760219031371.xml",
    "0000320187_4_2019-10-31_000112760219031367.xml",
    "0000320187_4_2019-10-31_000032018719000077.xml",
]

class FraudPatternDetector:
    """
    ENHANCED Fraud Pattern Detector with Core Enhancement Modules
    ALL MODULES ARE MANDATORY AND INTEGRATED
    """
    
    @staticmethod
    def analyze_transaction_patterns(transactions: List[Dict], 
                                    owner_data: Dict = None,
                                    footnotes: List[Dict] = None,
                                    earnings_dates: List[str] = None) -> Dict:
        """
        Analyze transactions for suspicious patterns
        NOW INCLUDES ALL CORE ENHANCEMENT MODULES
        """
        findings = {
            'suspicious_patterns': [],
            'red_flags': [],
            'risk_score': 0.0,
            'analysis': {},
            'enhancement_flags': {
                'zero_dollar': [],
                'plan_compliance': [],
                'role_risk': {},
                'earnings_correlation': {}
            }
        }
        
        if not transactions:
            return findings
        
        # CORE MODULE 1: Zero-Dollar Pattern Detection (MANDATORY)
        zero_dollar_findings = detect_zero_dollar_risk(transactions)
        findings['enhancement_flags']['zero_dollar'] = zero_dollar_findings
        
        for zf in zero_dollar_findings:
            findings['suspicious_patterns'].append({
                'type': 'ZERO_DOLLAR_ENRICHMENT',
                'description': zf['description'],
                'severity': zf['severity']
            })
            if zf['severity'] in ['HIGH', 'CRITICAL']:
                findings['risk_score'] += 0.3
        
        # CORE MODULE 2: 10b5-1 Compliance Verification (MANDATORY)
        if footnotes:
            footnotes_text = " ".join(fn.get('text', '') for fn in footnotes)
            plan_findings = check_10b5_plan(footnotes_text, datetime.now().strftime("%Y-%m-%d"))
            findings['enhancement_flags']['plan_compliance'] = plan_findings
            
            for pf in plan_findings:
                if pf['severity'] in ['HIGH', 'CRITICAL', 'MEDIUM']:
                    findings['suspicious_patterns'].append({
                        'type': f"10B5_1_{pf['type']}",
                        'description': pf['description'],
                        'severity': pf['severity']
                    })
                    if pf['severity'] == 'MEDIUM':
                        findings['risk_score'] += 0.15
                    elif pf['severity'] == 'HIGH':
                        findings['risk_score'] += 0.25
        
        # CORE MODULE 3: Role-Based Risk Weighting (MANDATORY)
        if owner_data:
            role = extract_role_from_relationship(owner_data.get('relationship', {}))
            owner_name = owner_data.get('name', 'Unknown')
            role_assessment = assess_role_specific_risk(owner_name, role, transactions)
            findings['enhancement_flags']['role_risk'] = role_assessment
            
            # Apply role multiplier to base risk
            findings['risk_score'] = weight_risk_score(role, findings['risk_score'])
            
            # Add role-specific concerns
            for concern in role_assessment.get('elevated_concerns', []):
                findings['red_flags'].append(concern)
        
        # CORE MODULE 4: Earnings Correlation (MANDATORY)
        if earnings_dates:
            earnings_analysis = correlate_all_transactions(transactions, earnings_dates)
            findings['enhancement_flags']['earnings_correlation'] = earnings_analysis
            
            # Add earnings correlation to risk score
            findings['risk_score'] += earnings_analysis.get('overall_risk', 0.0)
            
            # Flag pre-earnings trades
            for flagged in earnings_analysis.get('flagged_transactions', []):
                prox = flagged['proximity_analysis']
                if prox['severity'] in ['HIGH', 'CRITICAL']:
                    findings['suspicious_patterns'].append({
                        'type': prox['flag_type'],
                        'description': prox['description'],
                        'severity': prox['severity']
                    })
            
            # Flag clusters
            for cluster in earnings_analysis.get('clusters', []):
                findings['suspicious_patterns'].append({
                    'type': 'EARNINGS_CLUSTER',
                    'description': cluster['description'],
                    'severity': cluster['severity']
                })
        
        # Pattern 1: Large volume trades before price movements
        total_shares = sum(float(t.get('shares', 0)) for t in transactions if t.get('shares'))
        if total_shares > 100000:
            findings['suspicious_patterns'].append({
                'type': 'HIGH_VOLUME_TRADING',
                'description': f'Large volume trade detected: {total_shares:,.0f} shares',
                'severity': 'MEDIUM'
            })
            findings['risk_score'] += 0.3
        
        # Pattern 2: Same-day acquisition and disposal (potential wash trading)
        dates = {}
        for trans in transactions:
            date = trans.get('transaction_date')
            if date:
                if date not in dates:
                    dates[date] = []
                dates[date].append(trans)
        
        for date, date_trans in dates.items():
            codes = [t.get('transaction_code') for t in date_trans]
            if 'M' in codes and 'S' in codes:
                findings['suspicious_patterns'].append({
                    'type': 'SAME_DAY_EXERCISE_AND_SALE',
                    'description': f'Option exercised and shares sold same day: {date}',
                    'severity': 'LOW',
                    'note': 'Common for 10b5-1 plans, but requires verification'
                })
        
        # Pattern 3: Unusual price differences
        prices = [float(t.get('price_per_share', 0)) for t in transactions if t.get('price_per_share')]
        if len(prices) >= 2:
            max_price = max(prices)
            min_price = min(prices)
            if min_price > 0:
                price_spread = ((max_price - min_price) / min_price) * 100
                if price_spread > 50:
                    findings['suspicious_patterns'].append({
                        'type': 'UNUSUAL_PRICE_SPREAD',
                        'description': f'Large price spread: {price_spread:.1f}%',
                        'min_price': f'${min_price:.2f}',
                        'max_price': f'${max_price:.2f}',
                        'severity': 'MEDIUM'
                    })
                    findings['risk_score'] += 0.2
        
        # Pattern 4: Transaction timing analysis
        findings['analysis'] = {
            'total_transactions': len(transactions),
            'total_shares_traded': total_shares,
            'unique_dates': len(dates),
            'transaction_codes': list(set(t.get('transaction_code') for t in transactions if t.get('transaction_code')))
        }
        
        return findings
    
    @staticmethod
    def check_10b5_1_compliance(transactions: List[Dict], footnotes: List[Dict]) -> Dict:
        """Check for 10b5-1 trading plan compliance"""
        compliance = {
            'has_10b5_1_mention': False,
            'compliant': False,
            'notes': []
        }
        
        # Check footnotes for 10b5-1 mention
        for fn in footnotes:
            text = fn.get('text', '').lower()
            if '10b5-1' in text or '10b5' in text:
                compliance['has_10b5_1_mention'] = True
                compliance['compliant'] = True
                compliance['notes'].append(f"Found 10b5-1 reference in footnote: {fn.get('id')}")
        
        if not compliance['has_10b5_1_mention']:
            # Check for window trading (after earnings release)
            compliance['notes'].append("No 10b5-1 plan mentioned - requires verification of trading window compliance")
        
        return compliance

class VisualTimelineGenerator:
    """Generate visual timeline representation"""
    
    @staticmethod
    def generate_timeline(all_transactions: List[Tuple[str, str, List[Dict]]]) -> str:
        """
        Generate ASCII timeline of all transactions
        all_transactions: List of (owner_name, filing_date, transactions)
        """
        lines = []
        lines.append("\n" + "=" * 120)
        lines.append("TRANSACTION TIMELINE - CHRONOLOGICAL VIEW")
        lines.append("=" * 120)
        
        # Flatten and sort all transactions by date
        timeline_items = []
        for owner_name, filing_date, transactions in all_transactions:
            for trans in transactions:
                date = trans.get('transaction_date', filing_date)
                timeline_items.append({
                    'date': date,
                    'owner': owner_name,
                    'trans': trans
                })
        
        timeline_items.sort(key=lambda x: x['date'] if x['date'] else '9999-99-99')
        
        if not timeline_items:
            lines.append("\nNo transactions to display")
            return "\n".join(lines)
        
        # Group by date
        by_date = {}
        for item in timeline_items:
            date = item['date']
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(item)
        
        # Generate timeline
        for date in sorted(by_date.keys()):
            items = by_date[date]
            lines.append(f"\n{date}")
            lines.append("  |")
            
            for item in items:
                trans = item['trans']
                owner = item['owner'][:20]  # Truncate long names
                code = trans.get('transaction_code', '?')
                shares = trans.get('shares', '0')
                price = trans.get('price_per_share', '0')
                action = trans.get('acquired_disposed', 'Unknown')
                
                # Create visual indicator
                if action == 'Acquired':
                    indicator = ">>>"
                else:
                    indicator = "<<<"
                
                lines.append(f"  +-- {indicator} {owner:20s} | Code:{code} | {shares:>10s} shares @ ${price:>8s} | {action}")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_heatmap(all_transactions: List[Tuple[str, str, List[Dict]]]) -> str:
        """Generate trading activity heatmap"""
        lines = []
        lines.append("\n" + "=" * 120)
        lines.append("TRADING ACTIVITY HEATMAP")
        lines.append("=" * 120)
        
        # Count transactions per owner
        owner_counts = {}
        owner_volumes = {}
        
        for owner_name, filing_date, transactions in all_transactions:
            if owner_name not in owner_counts:
                owner_counts[owner_name] = 0
                owner_volumes[owner_name] = 0.0
            
            owner_counts[owner_name] += len(transactions)
            for trans in transactions:
                shares = float(trans.get('shares', 0))
                owner_volumes[owner_name] += shares
        
        # Sort by volume
        sorted_owners = sorted(owner_volumes.items(), key=lambda x: x[1], reverse=True)
        
        lines.append(f"\n{'Owner':<30} {'Transactions':<15} {'Total Shares':<20} Activity")
        lines.append("-" * 120)
        
        max_volume = max(owner_volumes.values()) if owner_volumes else 1
        
        for owner, volume in sorted_owners:
            count = owner_counts[owner]
            # Create bar chart
            bar_length = int((volume / max_volume) * 40)
            bar = "#" * bar_length
            
            lines.append(f"{owner:<30} {count:<15} {volume:>18,.0f}  {bar}")
        
        return "\n".join(lines)

def generate_comprehensive_report(filing_num: int, filename: str, data: Dict, 
                                 fraud_analysis: Dict, compliance: Dict) -> str:
    """Generate comprehensive human-readable forensic report"""
    lines = []
    lines.append("=" * 120)
    lines.append(f"JARVIS:LAW COMPREHENSIVE FORENSIC ANALYSIS - FILING #{filing_num}")
    lines.append("=" * 120)
    
    lines.append(f"\nFiling: {filename}")
    lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Forensic Classification: INSIDER TRADING DISCLOSURE")
    
    # SECTION 1: PARTIES INVOLVED
    lines.append("\n" + "=" * 120)
    lines.append("SECTION 1: PARTIES INVOLVED")
    lines.append("=" * 120)
    
    owner = data.get('reporting_owner', {})
    lines.append(f"\nReporting Person:")
    lines.append(f"  Name: {owner.get('name', 'ERROR')}")
    lines.append(f"  CIK: {owner.get('cik', 'ERROR')}")
    
    if 'address' in owner:
        addr = owner['address']
        lines.append(f"  Address: {addr.get('street', 'N/A')}")
        lines.append(f"           {addr.get('city', 'N/A')}, {addr.get('state', 'N/A')} {addr.get('zipcode', 'N/A')}")
    
    if 'relationship' in owner:
        lines.append(f"\n  Relationship to Issuer:")
        rel = owner['relationship']
        for key, value in rel.items():
            lines.append(f"    - {key.replace('is_', '').replace('_', ' ').title()}: {value}")
    
    issuer = data.get('issuer', {})
    lines.append(f"\nIssuer (Company):")
    lines.append(f"  Name: {issuer.get('name', 'ERROR')}")
    lines.append(f"  CIK: {issuer.get('cik', 'ERROR')}")
    lines.append(f"  Trading Symbol: {issuer.get('trading_symbol', 'ERROR')}")
    
    # SECTION 2: TRANSACTION DETAILS
    lines.append("\n" + "=" * 120)
    lines.append("SECTION 2: TRANSACTION DETAILS")
    lines.append("=" * 120)
    
    transactions = data.get('transactions', [])
    lines.append(f"\nTotal Transactions: {len(transactions)}")
    
    for i, trans in enumerate(transactions, 1):
        lines.append(f"\n{'*' * 100}")
        lines.append(f"TRANSACTION #{i}")
        lines.append('*' * 100)
        
        lines.append(f"\n  Security Information:")
        lines.append(f"    Title: {trans.get('security_title', 'N/A')}")
        lines.append(f"    Type: {trans.get('type', 'unknown').upper().replace('_', ' ')}")
        
        lines.append(f"\n  Transaction Details:")
        lines.append(f"    Date: {trans.get('transaction_date', 'N/A')}")
        lines.append(f"    Code: {trans.get('transaction_code', 'N/A')}")
        
        # Decode transaction code
        code = trans.get('transaction_code', '')
        code_meanings = {
            'P': 'Open Market Purchase',
            'S': 'Open Market Sale',
            'M': 'Exercise of Option',
            'A': 'Grant/Award',
            'D': 'Disposition to Issuer',
            'F': 'Payment of Exercise Price or Tax',
            'G': 'Gift',
            'I': 'Discretionary Transaction',
            'J': 'Other Acquisition/Disposition'
        }
        if code in code_meanings:
            lines.append(f"    Meaning: {code_meanings[code]}")
        
        lines.append(f"\n  Volume:")
        lines.append(f"    Shares Transacted: {trans.get('shares', 'N/A')}")
        lines.append(f"    Price Per Share: ${trans.get('price_per_share', 'N/A')}")
        
        # Calculate transaction value
        if trans.get('shares') and trans.get('price_per_share'):
            try:
                shares = float(trans.get('shares'))
                price = float(trans.get('price_per_share'))
                value = shares * price
                lines.append(f"    Transaction Value: ${value:,.2f}")
            except:
                pass
        
        lines.append(f"\n  Action:")
        lines.append(f"    Type: {trans.get('acquired_disposed', 'N/A')}")
        
        lines.append(f"\n  Post-Transaction Holdings:")
        lines.append(f"    Shares Owned After: {trans.get('shares_owned_after', 'N/A')}")
        lines.append(f"    Ownership Form: {trans.get('direct_indirect', 'N/A')}")
        
        if trans.get('nature_of_indirect'):
            lines.append(f"    Nature: {trans.get('nature_of_indirect')}")
        
        if trans.get('underlying_security_title'):
            lines.append(f"\n  Derivative Details:")
            lines.append(f"    Exercise Price: ${trans.get('exercise_price', 'N/A')}")
            lines.append(f"    Underlying Security: {trans.get('underlying_security_title')}")
            lines.append(f"    Underlying Shares: {trans.get('underlying_security_shares', 'N/A')}")
            if trans.get('expiration_date'):
                lines.append(f"    Expiration Date: {trans.get('expiration_date')}")
    
    # SECTION 3: ENHANCED FRAUD PATTERN ANALYSIS (WITH CORE MODULES)
    lines.append("\n" + "=" * 120)
    lines.append("SECTION 3: ENHANCED FORENSIC FRAUD PATTERN ANALYSIS")
    lines.append("=" * 120)
    lines.append("\n  [CORE ENHANCEMENT MODULES ACTIVE]")
    
    lines.append(f"\n  Overall Risk Score: {fraud_analysis['risk_score']:.2f}/1.0")
    
    # Display enhancement module findings
    enhancement_flags = fraud_analysis.get('enhancement_flags', {})
    
    # Module 1: Zero-Dollar Findings
    if enhancement_flags.get('zero_dollar'):
        lines.append(f"\n  [MODULE 1: ZERO-DOLLAR DETECTION]")
        for zf in enhancement_flags['zero_dollar']:
            lines.append(f"    [{zf['severity']}] {zf['flag']}: {zf['shares']:,} shares")
            lines.append(f"        {zf['description']}")
    
    # Module 2: 10b5-1 Compliance
    if enhancement_flags.get('plan_compliance'):
        lines.append(f"\n  [MODULE 2: 10b5-1 COMPLIANCE]")
        for pf in enhancement_flags['plan_compliance']:
            lines.append(f"    [{pf['severity']}] {pf['type']}")
            lines.append(f"        {pf['description']}")
    
    # Module 3: Role Risk Assessment
    if enhancement_flags.get('role_risk'):
        role_risk = enhancement_flags['role_risk']
        lines.append(f"\n  [MODULE 3: ROLE-BASED RISK WEIGHTING]")
        lines.append(f"    Role: {role_risk.get('role', 'Unknown')}")
        lines.append(f"    Risk Multiplier: {role_risk.get('risk_multiplier', 1.0)}x")
        if role_risk.get('risk_factors'):
            lines.append(f"    Risk Factors Identified: {len(role_risk['risk_factors'])}")
        if role_risk.get('elevated_concerns'):
            lines.append(f"    Elevated Concerns: {len(role_risk['elevated_concerns'])}")
    
    # Module 4: Earnings Correlation
    if enhancement_flags.get('earnings_correlation'):
        ec = enhancement_flags['earnings_correlation']
        lines.append(f"\n  [MODULE 4: EARNINGS EVENT CORRELATION]")
        lines.append(f"    Transactions Within Earnings Window: {ec.get('within_window', 0)}/{ec.get('total_transactions', 0)}")
        lines.append(f"    Earnings Risk Score: {ec.get('overall_risk', 0.0)}")
        if ec.get('clusters'):
            lines.append(f"    Transaction Clusters Detected: {len(ec['clusters'])}")
    
    if fraud_analysis['suspicious_patterns']:
        lines.append(f"\n  Suspicious Patterns Detected: {len(fraud_analysis['suspicious_patterns'])}")
        for pattern in fraud_analysis['suspicious_patterns']:
            lines.append(f"\n    [{pattern['severity']}] {pattern['type']}")
            lines.append(f"    Description: {pattern['description']}")
            if pattern.get('note'):
                lines.append(f"    Note: {pattern['note']}")
    else:
        lines.append("\n  No suspicious patterns detected")
    
    # SECTION 4: COMPLIANCE ANALYSIS
    lines.append("\n" + "=" * 120)
    lines.append("SECTION 4: REGULATORY COMPLIANCE ANALYSIS")
    lines.append("=" * 120)
    
    lines.append(f"\n  10b5-1 Trading Plan:")
    lines.append(f"    Status: {'COMPLIANT' if compliance['compliant'] else 'REQUIRES REVIEW'}")
    lines.append(f"    10b5-1 Mentioned: {'YES' if compliance['has_10b5_1_mention'] else 'NO'}")
    
    if compliance['notes']:
        lines.append(f"\n  Compliance Notes:")
        for note in compliance['notes']:
            lines.append(f"    - {note}")
    
    # SECTION 5: EXPLANATORY FOOTNOTES
    if data.get('footnotes'):
        lines.append("\n" + "=" * 120)
        lines.append("SECTION 5: EXPLANATORY FOOTNOTES")
        lines.append("=" * 120)
        
        for fn in data['footnotes']:
            lines.append(f"\n  {fn.get('id')}: {fn.get('text')}")
    
    # SECTION 6: FORENSIC SUMMARY
    lines.append("\n" + "=" * 120)
    lines.append("SECTION 6: FORENSIC SUMMARY & RECOMMENDATIONS")
    lines.append("=" * 120)
    
    analysis = fraud_analysis.get('analysis', {})
    lines.append(f"\n  Transaction Summary:")
    lines.append(f"    Total Transactions: {analysis.get('total_transactions', 0)}")
    lines.append(f"    Total Shares Traded: {analysis.get('total_shares_traded', 0):,.0f}")
    lines.append(f"    Unique Trading Dates: {analysis.get('unique_dates', 0)}")
    lines.append(f"    Transaction Types: {', '.join(analysis.get('transaction_codes', []))}")
    
    lines.append(f"\n  Forensic Assessment:")
    if fraud_analysis['risk_score'] < 0.3:
        lines.append(f"    Overall Risk Level: LOW")
        lines.append(f"    Recommendation: Standard monitoring")
    elif fraud_analysis['risk_score'] < 0.7:
        lines.append(f"    Overall Risk Level: MEDIUM")
        lines.append(f"    Recommendation: Enhanced monitoring, verify trading window compliance")
    else:
        lines.append(f"    Overall Risk Level: HIGH")
        lines.append(f"    Recommendation: Immediate review required, potential SEC inquiry")
    
    lines.append("\n" + "=" * 120)
    lines.append("END OF FORENSIC ANALYSIS")
    lines.append("=" * 120)
    
    return "\n".join(lines)

def validate_core_modules():
    """Validate all core enhancement modules are operational"""
    print("\n[SYSTEM CHECK] Validating Core Enhancement Modules...")
    
    modules_status = {
        "Module 1 (Zero-Dollar)": False,
        "Module 2 (10b5-1)": False,
        "Module 3 (Risk Weighting)": False,
        "Module 4 (Earnings)": False
    }
    
    try:
        # Test Module 1
        test_txn = [{"transaction_code": "A", "shares": "25000", "price_per_share": "0"}]
        result = detect_zero_dollar_risk(test_txn)
        modules_status["Module 1 (Zero-Dollar)"] = True
        
        # Test Module 2
        result = check_10b5_plan("test text", "2019-01-01")
        modules_status["Module 2 (10b5-1)"] = True
        
        # Test Module 3
        result = weight_risk_score("CEO", 0.3)
        modules_status["Module 3 (Risk Weighting)"] = True
        
        # Test Module 4
        result = load_earnings_calendar(None, "NKE")
        modules_status["Module 4 (Earnings)"] = True
        
    except Exception as e:
        print(f"[ERROR] Core module validation failed: {e}")
        return False
    
    # Display results
    for module, status in modules_status.items():
        status_str = "[OK OPERATIONAL]" if status else "[X FAILED]"
        print(f"  {status_str} {module}")
    
    all_operational = all(modules_status.values())
    
    if all_operational:
        print("[SYSTEM CHECK] OK All core modules operational")
    else:
        print("[SYSTEM CHECK] X One or more core modules failed - analysis cannot proceed")
        sys.exit(1)
    
    return all_operational


def main():
    """Execute comprehensive forensic analysis with CORE ENHANCEMENT MODULES"""
    print("=" * 120)
    print("JARVIS:LAW COMPREHENSIVE FORENSIC ANALYSIS")
    print("CORE ENHANCEMENT MODULES: ACTIVE AND MANDATORY")
    print("Control Group: First 10 Form 4 Filings from Nike Inc - 2019")
    print("=" * 120)
    
    # Validate all core modules are operational
    validate_core_modules()
    
    # Load earnings calendar (MANDATORY for Module 4)
    earnings_file = DATA_DIR / "earnings_calendar.json"
    earnings_dates = load_earnings_calendar(str(earnings_file), "NKE")
    print(f"\n[CORE MODULE 4] Loaded {len(earnings_dates)} earnings dates for correlation")
    
    all_results = []
    all_transactions_for_timeline = []
    all_insiders_data = {}  # For cross-filing analysis
    successful = 0
    failed = 0
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Process each filing
    for i, filename in enumerate(CONTROL_GROUP, 1):
        print(f"\n[{i}/10] Processing: {filename}")
        
        file_path = FILING_DIR / filename
        
        if not file_path.exists():
            print(f"  [ERROR] File not found")
            failed += 1
            continue
        
        try:
            # Parse Form 4
            parser = Form4HTMLParser(file_path)
            data = parser.extract_all()
            
            # Track insider data for cross-filing analysis
            owner_name = data.get('reporting_owner', {}).get('name', 'Unknown')
            if owner_name not in all_insiders_data:
                all_insiders_data[owner_name] = {
                    'transactions': [],
                    'filings': [],
                    'owner_data': data.get('reporting_owner', {})
                }
            all_insiders_data[owner_name]['transactions'].extend(data.get('transactions', []))
            all_insiders_data[owner_name]['filings'].append(filename)
            
            # Run ENHANCED fraud analysis with ALL CORE MODULES
            fraud_analysis = FraudPatternDetector.analyze_transaction_patterns(
                transactions=data.get('transactions', []),
                owner_data=data.get('reporting_owner', {}),
                footnotes=data.get('footnotes', []),
                earnings_dates=earnings_dates
            )
            
            # Legacy compliance check (now integrated into core modules)
            compliance = FraudPatternDetector.check_10b5_1_compliance(data.get('transactions', []), data.get('footnotes', []))
            
            # Generate comprehensive report
            report = generate_comprehensive_report(i, filename, data, fraud_analysis, compliance)
            
            # Save individual report
            accession = filename.split('_')[3].replace('.xml', '')
            report_file = OUTPUT_DIR / f"FORENSIC_REPORT_{i:02d}_{accession}_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"  [OK] Forensic report: {report_file.name}")
            
            # Collect for timeline
            owner_name = data.get('reporting_owner', {}).get('name', 'Unknown')
            filing_date = filename.split('_')[2]
            all_transactions_for_timeline.append((owner_name, filing_date, data.get('transactions', [])))
            
            # Store result
            all_results.append({
                'filing_number': i,
                'filename': filename,
                'accession': accession,
                'data': data,
                'fraud_analysis': fraud_analysis,
                'compliance': compliance,
                'report_file': str(report_file)
            })
            
            successful += 1
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            failed += 1
    
    # Generate visual analytics
    print(f"\n[ANALYTICS] Generating visual timeline and heatmap...")
    
    timeline = VisualTimelineGenerator.generate_timeline(all_transactions_for_timeline)
    heatmap = VisualTimelineGenerator.generate_heatmap(all_transactions_for_timeline)
    
    # Generate comprehensive insider risk rankings (CORE MODULE 3)
    print(f"\n[CORE MODULE 3] Ranking all insiders by composite risk...")
    insider_assessments = []
    for insider_name, insider_data in all_insiders_data.items():
        role = extract_role_from_relationship(insider_data['owner_data'].get('relationship', {}))
        assessment = assess_role_specific_risk(
            insider_name,
            role,
            insider_data['transactions']
        )
        insider_assessments.append(assessment)
    
    ranked_insiders = rank_insiders_by_risk(insider_assessments)
    
    # Generate master summary
    lines = []
    lines.append("=" * 120)
    lines.append("JARVIS:LAW MASTER FORENSIC SUMMARY")
    lines.append("=" * 120)
    lines.append(f"\nGenerated: {datetime.now().isoformat()}")
    lines.append(f"Analysis ID: {timestamp}")
    lines.append(f"Scope: Nike Inc (CIK 0000320187) - First 10 Form 4 Filings from 2019")
    lines.append(f"\n[CORE ENHANCEMENT MODULES: ALL ACTIVE AND INTEGRATED]")
    
    master_lines.append("\n" + "=" * 120)
    master_lines.append("EXECUTIVE SUMMARY")
    master_lines.append("=" * 120)
    master_lines.append(f"\nFilings Analyzed: {successful}/10")
    master_lines.append(f"Failed Extractions: {failed}/10")
    
    total_trans = sum(len(r['data'].get('transactions', [])) for r in all_results)
    total_red_flags = sum(len(r['fraud_analysis'].get('suspicious_patterns', [])) for r in all_results)
    avg_risk = sum(r['fraud_analysis'].get('risk_score', 0) for r in all_results) / len(all_results) if all_results else 0
    
    master_lines.append(f"\nTotal Transactions: {total_trans}")
    master_lines.append(f"Suspicious Patterns Found: {total_red_flags}")
    master_lines.append(f"Average Risk Score: {avg_risk:.2f}/1.0")
    
    # Add insider risk rankings (CORE MODULE 3 OUTPUT)
    master_lines.append("\n" + "=" * 120)
    master_lines.append("INSIDER RISK RANKINGS (CORE MODULE 3: ROLE-WEIGHTED ANALYSIS)")
    master_lines.append("=" * 120)
    
    for rank, insider in enumerate(ranked_insiders, 1):
        master_lines.append(f"\n#{rank} - {insider['insider']}")
        master_lines.append(f"  Role: {insider['role']}")
        master_lines.append(f"  Composite Risk Score: {insider['composite_risk']} [{insider['priority']}]")
        master_lines.append(f"  Risk Multiplier: {insider['risk_multiplier']}x")
        master_lines.append(f"  Risk Factors: {insider['risk_factors']}")
        master_lines.append(f"  Elevated Concerns: {insider['elevated_concerns']}")
    
    # Add timeline and heatmap
    master_lines.append(timeline)
    master_lines.append(heatmap)
    
    # Add individual summaries
    master_lines.append("\n" + "=" * 120)
    master_lines.append("INDIVIDUAL FILING SUMMARIES")
    master_lines.append("=" * 120)
    
    for result in all_results:
        data = result['data']
        fraud = result['fraud_analysis']
        
        master_lines.append(f"\n{'#' * 100}")
        master_lines.append(f"Filing #{result['filing_number']:02d} - {data.get('reporting_owner', {}).get('name', 'Unknown')}")
        master_lines.append('#' * 100)
        master_lines.append(f"  Transactions: {len(data.get('transactions', []))}")
        master_lines.append(f"  Risk Score: {fraud['risk_score']:.2f}")
        master_lines.append(f"  Red Flags: {len(fraud.get('suspicious_patterns', []))}")
        master_lines.append(f"  Report: {Path(result['report_file']).name}")
    
    master_lines.append("\n" + "=" * 120)
    master_lines.append("ANALYSIS COMPLETE")
    master_lines.append("=" * 120)
    
    # Save master summary
    master_file = OUTPUT_DIR / f"MASTER_FORENSIC_SUMMARY_{timestamp}.txt"
    with open(master_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(master_lines))
    
    # Save JSON
    json_file = OUTPUT_DIR / f"forensic_analysis_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 120)
    print("FORENSIC ANALYSIS COMPLETE")
    print("=" * 120)
    print(f"\nMaster Summary: {master_file}")
    print(f"JSON Data: {json_file}")
    print(f"Individual Reports: {OUTPUT_DIR}/*.txt")
    print("\n" + "=" * 120)
    
    # Print the master summary to console
    print("\n".join(master_lines))

if __name__ == "__main__":
    main()

