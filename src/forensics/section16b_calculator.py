"""
Section 16(b) Short-Swing Profit Calculator
============================================

Implements dual algorithms for calculating short-swing profits under
Section 16(b) of the Securities Exchange Act of 1934:

1. Gratz v. Claughton "lowest-in, highest-out" method
2. Transportation algorithm for maximum profit calculation

Critical Features:
- 183-day window calculations (not calendar months)
- Transaction matching optimization
- Buy-sell pair identification
- Profit recovery computation

Reference: 15 U.S.C. § 78p(b)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Transaction types for Section 16(b) analysis."""
    BUY = "buy"
    SELL = "sell"
    GRANT = "grant"
    EXERCISE = "exercise"


@dataclass
class Transaction:
    """Insider transaction for 16(b) analysis."""
    date: datetime
    transaction_type: TransactionType
    shares: float
    price_per_share: float
    transaction_code: str
    filing_date: Optional[datetime] = None
    
    @property
    def total_value(self) -> float:
        """Total transaction value."""
        return self.shares * self.price_per_share


@dataclass
class ShortSwingPair:
    """Matched buy-sell pair within 183-day window."""
    buy_transaction: Transaction
    sell_transaction: Transaction
    days_apart: int
    profit: float
    shares_matched: float
    
    @property
    def is_within_window(self) -> bool:
        """Check if pair is within 183-day window."""
        return self.days_apart <= 183


@dataclass
class Section16bAnalysis:
    """Complete Section 16(b) analysis result."""
    insider_name: str
    cik: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    total_transactions: int
    matched_pairs: List[ShortSwingPair]
    total_recoverable_profit: float
    gratz_method_profit: float
    transportation_method_profit: float
    algorithm_used: str
    violations_detected: bool
    analysis_timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


class Section16bCalculator:
    """
    Section 16(b) Short-Swing Profit Calculator.
    
    Implements both Gratz v. Claughton and Transportation algorithms
    for maximum profit calculation within 6-month window.
    """
    
    # 6 months = 183 days (not calendar months)
    WINDOW_DAYS = 183
    
    def __init__(self):
        """Initialize Section 16(b) calculator."""
        self.logger = logging.getLogger("Section16bCalculator")
    
    def analyze_transactions(
        self,
        transactions: List[Transaction],
        insider_name: str,
        cik: str,
        use_transportation: bool = True
    ) -> Section16bAnalysis:
        """
        Analyze transactions for Section 16(b) violations.
        
        Args:
            transactions: List of insider transactions
            insider_name: Name of insider
            cik: Company CIK
            use_transportation: Use transportation algorithm (more accurate)
        
        Returns:
            Complete Section 16(b) analysis
        """
        if not transactions:
            return self._empty_analysis(insider_name, cik)
        
        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda t: t.date)
        
        # Separate buys and sells
        buys = [t for t in sorted_transactions 
                if t.transaction_type in [TransactionType.BUY, TransactionType.GRANT, TransactionType.EXERCISE]]
        sells = [t for t in sorted_transactions 
                 if t.transaction_type == TransactionType.SELL]
        
        self.logger.info(
            f"Analyzing {len(sorted_transactions)} transactions "
            f"({len(buys)} buys, {len(sells)} sells)"
        )
        
        # Calculate using both methods
        gratz_pairs, gratz_profit = self._gratz_method(buys, sells)
        
        if use_transportation:
            transport_pairs, transport_profit = self._transportation_method(buys, sells)
            matched_pairs = transport_pairs
            total_profit = transport_profit
            algorithm = "Transportation Algorithm"
        else:
            matched_pairs = gratz_pairs
            total_profit = gratz_profit
            algorithm = "Gratz v. Claughton"
        
        violations_detected = total_profit > 0
        
        return Section16bAnalysis(
            insider_name=insider_name,
            cik=cik,
            analysis_period_start=sorted_transactions[0].date,
            analysis_period_end=sorted_transactions[-1].date,
            total_transactions=len(sorted_transactions),
            matched_pairs=matched_pairs,
            total_recoverable_profit=total_profit,
            gratz_method_profit=gratz_profit,
            transportation_method_profit=transport_profit,
            algorithm_used=algorithm,
            violations_detected=violations_detected
        )
    
    def _gratz_method(
        self,
        buys: List[Transaction],
        sells: List[Transaction]
    ) -> Tuple[List[ShortSwingPair], float]:
        """
        Gratz v. Claughton "lowest-in, highest-out" method.
        
        Matches lowest-priced purchases with highest-priced sales
        within 183-day window to maximize recoverable profit.
        
        Returns:
            (matched_pairs, total_profit)
        """
        if not buys or not sells:
            return [], 0.0
        
        # Sort: buys by price (ascending), sells by price (descending)
        sorted_buys = sorted(buys, key=lambda t: t.price_per_share)
        sorted_sells = sorted(sells, key=lambda t: t.price_per_share, reverse=True)
        
        matched_pairs = []
        total_profit = 0.0
        
        # Track remaining shares for each transaction
        buy_remaining = {id(b): b.shares for b in sorted_buys}
        sell_remaining = {id(s): s.shares for s in sorted_sells}
        
        # Match lowest buys with highest sells
        for buy in sorted_buys:
            if buy_remaining[id(buy)] <= 0:
                continue
            
            for sell in sorted_sells:
                if sell_remaining[id(sell)] <= 0:
                    continue
                
                # Check 183-day window (both directions)
                days_apart = abs((sell.date - buy.date).days)
                if days_apart > self.WINDOW_DAYS:
                    continue
                
                # Match shares
                shares_to_match = min(
                    buy_remaining[id(buy)],
                    sell_remaining[id(sell)]
                )
                
                if shares_to_match <= 0:
                    continue
                
                # Calculate profit
                profit = shares_to_match * (sell.price_per_share - buy.price_per_share)
                
                # Only count actual profits (not losses)
                if profit > 0:
                    matched_pairs.append(ShortSwingPair(
                        buy_transaction=buy,
                        sell_transaction=sell,
                        days_apart=days_apart,
                        profit=profit,
                        shares_matched=shares_to_match
                    ))
                    total_profit += profit
                
                # Update remaining shares
                buy_remaining[id(buy)] -= shares_to_match
                sell_remaining[id(sell)] -= shares_to_match
                
                if buy_remaining[id(buy)] <= 0:
                    break
        
        self.logger.info(
            f"Gratz method: {len(matched_pairs)} pairs, "
            f"${total_profit:,.2f} recoverable profit"
        )
        
        return matched_pairs, total_profit
    
    def _transportation_method(
        self,
        buys: List[Transaction],
        sells: List[Transaction]
    ) -> Tuple[List[ShortSwingPair], float]:
        """
        Transportation algorithm for maximum profit calculation.
        
        Uses linear programming approach to find optimal matching
        that maximizes recoverable profit under 16(b).
        
        This is a simplified greedy implementation. Full implementation
        would use scipy.optimize.linprog or similar.
        
        Returns:
            (matched_pairs, total_profit)
        """
        if not buys or not sells:
            return [], 0.0
        
        # Build profit matrix for all valid pairs
        valid_pairs = []
        
        for buy in buys:
            for sell in sells:
                days_apart = abs((sell.date - buy.date).days)
                
                # Must be within 183-day window
                if days_apart > self.WINDOW_DAYS:
                    continue
                
                # Calculate profit per share
                profit_per_share = sell.price_per_share - buy.price_per_share
                
                # Only consider profitable pairs
                if profit_per_share > 0:
                    valid_pairs.append({
                        'buy': buy,
                        'sell': sell,
                        'profit_per_share': profit_per_share,
                        'max_shares': min(buy.shares, sell.shares),
                        'days_apart': days_apart
                    })
        
        # Sort by profit per share (descending)
        valid_pairs.sort(key=lambda p: p['profit_per_share'], reverse=True)
        
        matched_pairs = []
        total_profit = 0.0
        
        # Track remaining shares
        buy_remaining = {id(b): b.shares for b in buys}
        sell_remaining = {id(s): s.shares for s in sells}
        
        # Greedy matching: highest profit pairs first
        for pair in valid_pairs:
            buy = pair['buy']
            sell = pair['sell']
            
            # Check remaining shares
            shares_available = min(
                buy_remaining[id(buy)],
                sell_remaining[id(sell)]
            )
            
            if shares_available <= 0:
                continue
            
            # Match shares
            profit = shares_available * pair['profit_per_share']
            
            matched_pairs.append(ShortSwingPair(
                buy_transaction=buy,
                sell_transaction=sell,
                days_apart=pair['days_apart'],
                profit=profit,
                shares_matched=shares_available
            ))
            
            total_profit += profit
            
            # Update remaining
            buy_remaining[id(buy)] -= shares_available
            sell_remaining[id(sell)] -= shares_available
        
        self.logger.info(
            f"Transportation method: {len(matched_pairs)} pairs, "
            f"${total_profit:,.2f} recoverable profit"
        )
        
        return matched_pairs, total_profit
    
    def _empty_analysis(
        self,
        insider_name: str,
        cik: str
    ) -> Section16bAnalysis:
        """Create empty analysis for no transactions."""
        now = datetime.utcnow()
        return Section16bAnalysis(
            insider_name=insider_name,
            cik=cik,
            analysis_period_start=now,
            analysis_period_end=now,
            total_transactions=0,
            matched_pairs=[],
            total_recoverable_profit=0.0,
            gratz_method_profit=0.0,
            transportation_method_profit=0.0,
            algorithm_used="N/A",
            violations_detected=False
        )


def calculate_short_swing_profit(
    transactions: List[Dict[str, Any]],
    insider_name: str,
    cik: str
) -> Section16bAnalysis:
    """
    Convenience function for Section 16(b) analysis.
    
    Args:
        transactions: List of transaction dicts with keys:
            - date: datetime or ISO string
            - type: 'buy', 'sell', 'grant', or 'exercise'
            - shares: float
            - price: float
            - code: transaction code (optional)
        insider_name: Insider name
        cik: Company CIK
    
    Returns:
        Section16bAnalysis object
    """
    calculator = Section16bCalculator()
    
    # Convert dict transactions to Transaction objects
    transaction_objs = []
    
    for t in transactions:
        # Parse date with error handling
        try:
            if isinstance(t['date'], str):
                # Handle ISO format with optional 'Z' suffix
                date_str = t['date'].replace('Z', '+00:00')
                date = datetime.fromisoformat(date_str)
            elif isinstance(t['date'], datetime):
                date = t['date']
            else:
                logger.warning(f"Invalid date type: {type(t['date'])}, skipping transaction")
                continue
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse date '{t.get('date')}': {e}, skipping transaction")
            continue
        
        # Parse type
        type_str = t['type'].lower()
        if type_str in ['buy', 'purchase']:
            trans_type = TransactionType.BUY
        elif type_str in ['sell', 'sale']:
            trans_type = TransactionType.SELL
        elif type_str == 'grant':
            trans_type = TransactionType.GRANT
        elif type_str == 'exercise':
            trans_type = TransactionType.EXERCISE
        else:
            logger.warning(f"Unknown transaction type: {type_str}, treating as BUY")
            trans_type = TransactionType.BUY
        
        transaction_objs.append(Transaction(
            date=date,
            transaction_type=trans_type,
            shares=float(t['shares']),
            price_per_share=float(t.get('price', 0)),
            transaction_code=t.get('code', ''),
            filing_date=None
        ))
    
    return calculator.analyze_transactions(
        transaction_objs,
        insider_name,
        cik,
        use_transportation=True
    )
