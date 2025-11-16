"""MODULE 4: Earnings Correlation"""

from datetime import datetime

def is_within_earnings_window(txn_date, earnings_dates, window_days=14):
    try:
        txn_dt = datetime.strptime(txn_date, "%Y-%m-%d")
        for event_date in earnings_dates:
            event_dt = datetime.strptime(event_date, "%Y-%m-%d")
            days_diff = (txn_dt - event_dt).days
            if abs(days_diff) <= window_days:
                return True
        return False
    except (ValueError, TypeError):
        return False

def analyze_earnings_proximity(txn_date, earnings_dates, window_days=14):
    try:
        txn_dt = datetime.strptime(txn_date, "%Y-%m-%d")
        closest_event = None
        closest_days = float('inf')
        for event_date in earnings_dates:
            event_dt = datetime.strptime(event_date, "%Y-%m-%d")
            days_diff = (txn_dt - event_dt).days
            if abs(days_diff) < abs(closest_days):
                closest_days = days_diff
                closest_event = event_date
        if closest_event and abs(closest_days) <= window_days:
            if closest_days < 0:
                timing = "BEFORE"
                severity = "CRITICAL" if closest_days >= -7 else "HIGH"
                flag_type = "PRE_EARNINGS_TRADING"
            elif closest_days == 0:
                timing = "ON"
                severity = "CRITICAL"
                flag_type = "EARNINGS_DAY_TRADING"
            else:
                timing = "AFTER"
                severity = "MEDIUM" if closest_days <= 2 else "LOW"
                flag_type = "POST_EARNINGS_TRADING"
            return {
                "within_window": True,
                "closest_event": closest_event,
                "days_difference": closest_days,
                "timing": timing,
                "severity": severity,
                "flag_type": flag_type,
                "description": f"Transaction {abs(closest_days)} days {timing.lower()} earnings on {closest_event}",
                "recommendation": "Verify no access to preliminary financial results" if timing == "BEFORE" else "Review for selective disclosure violations"
            }
        return {"within_window": False}
    except (ValueError, TypeError):
        return {"within_window": False, "error": "Date parsing failed"}

def detect_clustered_trading(transactions, earnings_dates, cluster_window=7):
    clusters = []
    for earnings_date in earnings_dates:
        try:
            earnings_dt = datetime.strptime(earnings_date, "%Y-%m-%d")
            clustered_txns = []
            for txn in transactions:
                txn_date = txn.get('transaction_date')
                if not txn_date:
                    continue
                txn_dt = datetime.strptime(txn_date, "%Y-%m-%d")
                days_diff = (txn_dt - earnings_dt).days
                if -cluster_window <= days_diff <= cluster_window:
                    clustered_txns.append({"transaction": txn, "days_from_earnings": days_diff})
            if len(clustered_txns) >= 2:
                total_shares = 0
                total_value = 0
                for ct in clustered_txns:
                    t = ct["transaction"]
                    try:
                        shares = float(str(t.get('shares', '0')).replace(',', ''))
                        price = float(str(t.get('price_per_share', '0')).replace('$', '').replace(',', ''))
                        total_shares += shares
                        total_value += shares * price
                    except (ValueError, TypeError):
                        pass
                clusters.append({
                    "earnings_date": earnings_date,
                    "transaction_count": len(clustered_txns),
                    "total_shares": int(total_shares),
                    "total_value": total_value,
                    "severity": "HIGH" if len(clustered_txns) >= 3 else "MEDIUM",
                    "flag": "EARNINGS_CLUSTER_TRADING",
                    "description": f"{len(clustered_txns)} transactions within {cluster_window} days of earnings",
                    "recommendation": "Investigate for coordinated insider activity or MNPI abuse"
                })
        except (ValueError, TypeError):
            continue
    return clusters

def load_earnings_calendar(file_path=None, ticker="NKE"):
    default_nike_2019 = ["2019-09-24", "2019-12-19"]
    if file_path:
        try:
            import json
            with open(file_path, 'r') as f:
                calendar = json.load(f)
                return calendar.get(ticker, default_nike_2019)
        except:
            pass
    return default_nike_2019

def correlate_all_transactions(transactions, earnings_dates, window_days=14):
    correlations = {
        "total_transactions": len(transactions),
        "within_window": 0,
        "flagged_transactions": [],
        "clusters": [],
        "overall_risk": 0.0
    }
    for txn in transactions:
        txn_date = txn.get('transaction_date')
        if not txn_date:
            continue
        proximity = analyze_earnings_proximity(txn_date, earnings_dates, window_days)
        if proximity.get('within_window'):
            correlations["within_window"] += 1
            correlations["flagged_transactions"].append({"transaction": txn, "proximity_analysis": proximity})
            if proximity['severity'] == 'CRITICAL':
                correlations["overall_risk"] += 0.3
            elif proximity['severity'] == 'HIGH':
                correlations["overall_risk"] += 0.2
            elif proximity['severity'] == 'MEDIUM':
                correlations["overall_risk"] += 0.1
    correlations["clusters"] = detect_clustered_trading(transactions, earnings_dates)
    correlations["overall_risk"] += len(correlations["clusters"]) * 0.2
    correlations["overall_risk"] = min(round(correlations["overall_risk"], 2), 1.0)
    return correlations

