"""MODULE 2: 10b5-1 Compliance Verifier"""
import re
from datetime import datetime

def check_10b5_plan(text_block, filing_date, plan_date_lookup=None):
    findings = []
    if not text_block:
        return findings
    text_lower = text_block.lower()
    if "10b5-1" in text_lower or "10b5" in text_lower:
        findings.append({"type": "PLAN_MENTIONED", "severity": "INFO", "description": "10b5-1 trading plan referenced", "recommendation": "Verify plan documentation"})
    else:
        findings.append({"type": "NO_PLAN_MENTIONED", "severity": "MEDIUM", "description": "No 10b5-1 plan mentioned", "recommendation": "Verify trading window compliance"})
    return findings

def verify_cooling_off_period(plan_adoption_date, transaction_date, role="Officer"):
    try:
        plan_dt = datetime.strptime(plan_adoption_date, "%Y-%m-%d")
        txn_dt = datetime.strptime(transaction_date, "%Y-%m-%d")
        days_diff = (txn_dt - plan_dt).days
        required_days = 90 if role in ["Officer", "Director", "CEO", "CFO"] else 30
        compliant = days_diff >= required_days
        return {"compliant": compliant, "days_elapsed": days_diff, "required_days": required_days, "severity": "NONE" if compliant else "HIGH"}
    except:
        return {"compliant": None, "error": "Date parsing failed"}

def analyze_plan_consistency(transactions_with_plans):
    return None

