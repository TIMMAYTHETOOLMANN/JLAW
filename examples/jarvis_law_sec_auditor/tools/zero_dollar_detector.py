"""
MODULE 1: Zero-Dollar Pattern Amplifier
Detects high-volume zero-dollar transactions (grants, awards, gifts)
that could represent insider enrichment schemes
"""

def detect_zero_dollar_risk(transactions):
    """
    Identify high-risk zero-dollar transactions that exceed typical compensation thresholds
    
    Args:
        transactions: List of transaction dictionaries
        
    Returns:
        List of high-risk findings
    """
    high_risk = []
    
    for txn in transactions:
        transaction_code = txn.get("transaction_code", "")
        shares = txn.get("shares", "0")
        price = txn.get("price_per_share", "0")
        
        # Convert shares to int/float
        try:
            shares_num = float(str(shares).replace(',', ''))
        except (ValueError, AttributeError):
            continue
        
        # Convert price to float
        try:
            price_num = float(str(price).replace('$', '').replace(',', ''))
        except (ValueError, AttributeError):
            price_num = 0.0
        
        # Flag zero-dollar high-volume transactions
        if transaction_code in ["A", "G"] and price_num == 0.0 and shares_num > 20000:
            high_risk.append({
                "insider": txn.get("reporting_owner", "Unknown"),
                "shares": int(shares_num),
                "type": transaction_code,
                "type_meaning": "Grant/Award" if transaction_code == "A" else "Gift",
                "flag": "Zero-Dollar Enrichment Suspected",
                "severity": "HIGH",
                "description": f"High-volume zero-cost transaction: {int(shares_num):,} shares",
                "recommendation": "Verify against typical compensation benchmarks and board authorization"
            })
        
        # Also flag medium-risk zero-dollar transactions (10K-20K shares)
        elif transaction_code in ["A", "G"] and price_num == 0.0 and 10000 <= shares_num <= 20000:
            high_risk.append({
                "insider": txn.get("reporting_owner", "Unknown"),
                "shares": int(shares_num),
                "type": transaction_code,
                "type_meaning": "Grant/Award" if transaction_code == "A" else "Gift",
                "flag": "Elevated Zero-Dollar Transaction",
                "severity": "MEDIUM",
                "description": f"Significant zero-cost transaction: {int(shares_num):,} shares",
                "recommendation": "Review against compensation committee records"
            })
    
    return high_risk


def analyze_zero_dollar_patterns(all_transactions_by_insider):
    """
    Analyze patterns across multiple zero-dollar transactions for same insider
    
    Args:
        all_transactions_by_insider: Dict of {insider_name: [transactions]}
        
    Returns:
        Pattern analysis results
    """
    patterns = []
    
    for insider, transactions in all_transactions_by_insider.items():
        zero_dollar_txns = []
        
        for txn in transactions:
            price = txn.get("price_per_share", "0")
            try:
                price_num = float(str(price).replace('$', '').replace(',', ''))
            except (ValueError, AttributeError):
                price_num = 0.0
            
            if price_num == 0.0:
                zero_dollar_txns.append(txn)
        
        if len(zero_dollar_txns) >= 2:
            total_shares = sum(float(str(t.get("shares", "0")).replace(',', '')) for t in zero_dollar_txns)
            
            patterns.append({
                "insider": insider,
                "pattern": "REPEATED_ZERO_DOLLAR_GRANTS",
                "occurrences": len(zero_dollar_txns),
                "total_shares": int(total_shares),
                "severity": "MEDIUM" if total_shares < 50000 else "HIGH",
                "description": f"Multiple zero-cost grants detected: {len(zero_dollar_txns)} transactions totaling {int(total_shares):,} shares",
                "recommendation": "Investigate executive compensation structure and board approval process"
            })
    
    return patterns

