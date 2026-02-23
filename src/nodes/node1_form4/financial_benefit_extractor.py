"""
Financial Benefit Extraction Engine
=====================================

Mathematically extracts the actual financial benefit of $0 reported transactions
by computing implied market value from share price data.

For every $0 transaction, this module calculates:
1. shares x market_price_at_date = implied value of transfer
2. For derivatives: (underlying_price - exercise_price) x shares = spread benefit
3. For gifts: donor tax basis vs market value = tax benefit quantification
4. Cumulative per-insider benefit across all $0 transactions
5. Per-issuer aggregate benefit from all zero-dollar activity

This is the mathematical core that answers the question:
"What was the ACTUAL dollar value that changed hands at $0?"

Statutory framework:
- 17 CFR section 229.402: Executive compensation disclosure (Item 402)
- 17 CFR section 229.404: Related party transactions (Item 404)
- 26 USC section 83: Income from property transferred in connection with services
- 15 USC section 78j(b): Rule 10b-5 anti-fraud
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class BenefitExtraction:
    """Extracted financial benefit for a single $0 transaction."""
    transaction_date: Optional[date]
    transaction_code: str
    owner_name: str
    security_title: str
    shares: float
    reported_price: float  # Always 0.0
    market_price: float
    implied_value: float  # shares x market_price
    is_derivative: bool
    exercise_price: float
    derivative_spread: float  # (market - exercise) x shares
    tax_benefit_estimate: float  # For gifts: full market value deduction
    benefit_type: str  # "equity_transfer", "derivative_spread", "tax_benefit"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None,
            "transaction_code": self.transaction_code,
            "owner_name": self.owner_name,
            "security_title": self.security_title,
            "shares": self.shares,
            "reported_price": self.reported_price,
            "market_price": round(self.market_price, 4),
            "implied_value": round(self.implied_value, 2),
            "is_derivative": self.is_derivative,
            "exercise_price": round(self.exercise_price, 4),
            "derivative_spread": round(self.derivative_spread, 2),
            "tax_benefit_estimate": round(self.tax_benefit_estimate, 2),
            "benefit_type": self.benefit_type,
        }


@dataclass
class InsiderBenefitProfile:
    """Cumulative benefit profile for a single insider."""
    owner_name: str
    is_officer: bool = False
    is_director: bool = False
    is_ten_percent_owner: bool = False
    officer_title: str = ""
    total_zero_dollar_transactions: int = 0
    total_shares_at_zero: float = 0.0
    total_implied_value: float = 0.0
    total_derivative_spread: float = 0.0
    total_tax_benefit: float = 0.0
    combined_benefit: float = 0.0
    transaction_codes_used: List[str] = field(default_factory=list)
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None
    extractions: List[BenefitExtraction] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner_name": self.owner_name,
            "role": {
                "is_officer": self.is_officer,
                "is_director": self.is_director,
                "is_ten_percent_owner": self.is_ten_percent_owner,
                "officer_title": self.officer_title,
            },
            "summary": {
                "total_zero_dollar_transactions": self.total_zero_dollar_transactions,
                "total_shares_at_zero": self.total_shares_at_zero,
                "total_implied_value": round(self.total_implied_value, 2),
                "total_derivative_spread": round(self.total_derivative_spread, 2),
                "total_tax_benefit": round(self.total_tax_benefit, 2),
                "combined_benefit": round(self.combined_benefit, 2),
            },
            "transaction_codes_used": list(set(self.transaction_codes_used)),
            "date_range": {
                "start": self.date_range_start.isoformat() if self.date_range_start else None,
                "end": self.date_range_end.isoformat() if self.date_range_end else None,
            },
            "extractions": [e.to_dict() for e in self.extractions],
        }


@dataclass
class IssuerBenefitSummary:
    """Aggregate benefit summary across all insiders for one issuer."""
    issuer_name: str
    issuer_cik: str
    total_zero_dollar_transactions: int = 0
    total_implied_value: float = 0.0
    total_derivative_spread: float = 0.0
    total_tax_benefit: float = 0.0
    combined_benefit: float = 0.0
    unique_insiders: int = 0
    insider_profiles: List[InsiderBenefitProfile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issuer_name": self.issuer_name,
            "issuer_cik": self.issuer_cik,
            "aggregate": {
                "total_zero_dollar_transactions": self.total_zero_dollar_transactions,
                "total_implied_value": round(self.total_implied_value, 2),
                "total_derivative_spread": round(self.total_derivative_spread, 2),
                "total_tax_benefit": round(self.total_tax_benefit, 2),
                "combined_benefit": round(self.combined_benefit, 2),
                "unique_insiders": self.unique_insiders,
            },
            "insider_profiles": [p.to_dict() for p in self.insider_profiles],
        }


# Gift codes that may produce tax benefit
GIFT_CODES = {'G', 'W'}

# Derivative codes
DERIVATIVE_CODES = {'M', 'C', 'X', 'E', 'O', 'H', 'K'}

# Estimated marginal tax rate for gift benefit calculation
ESTIMATED_TAX_RATE = 0.37  # Top federal bracket


class FinancialBenefitExtractor:
    """
    Extracts the mathematical financial benefit from $0 transactions.

    For each $0 transaction:
    - Equity: shares x market_price = implied transfer value
    - Derivatives: (underlying_price - exercise_price) x shares = spread
    - Gifts: market_value x tax_rate = estimated tax benefit to donor
    - Aggregates per insider and per issuer
    """

    def __init__(self, tax_rate: float = ESTIMATED_TAX_RATE):
        self.tax_rate = tax_rate

    def extract_benefits(
        self,
        transactions: List[Dict[str, Any]],
        market_prices: Optional[Dict[str, float]] = None,
    ) -> List[BenefitExtraction]:
        """
        Extract financial benefit from each $0 transaction.

        Args:
            transactions: $0 transaction dicts from Form 4 parser
            market_prices: Security -> price mapping at transaction dates

        Returns:
            List of BenefitExtraction objects
        """
        extractions = []

        for txn in transactions:
            price = txn.get('price_per_share', 0)
            try:
                if float(price) != 0.0:
                    continue
            except (ValueError, TypeError):
                continue

            shares = txn.get('shares', 0)
            if shares <= 0:
                continue

            code = txn.get('transaction_code', '').upper()
            is_derivative = txn.get('is_derivative', False)
            security = txn.get('security_title', '')
            underlying = txn.get('underlying_security', '')
            owner = txn.get('owner_name', txn.get('reporting_owner_name', ''))

            # Get market price
            market_price = self._lookup_price(
                security, underlying, txn.get('transaction_date', ''),
                market_prices
            )

            # Calculate implied value
            implied_value = shares * market_price

            # Calculate derivative spread
            exercise_price = 0.0
            derivative_spread = 0.0
            if is_derivative or code in DERIVATIVE_CODES:
                try:
                    exercise_price = float(txn.get('exercise_price', 0) or 0)
                except (ValueError, TypeError):
                    exercise_price = 0.0

                underlying_price = self._lookup_price(
                    underlying or security, underlying,
                    txn.get('transaction_date', ''), market_prices
                )
                spread = max(0, underlying_price - exercise_price)
                derivative_spread = shares * spread

            # Calculate tax benefit for gifts
            tax_benefit = 0.0
            benefit_type = "equity_transfer"
            if code in GIFT_CODES:
                tax_benefit = implied_value * self.tax_rate
                benefit_type = "tax_benefit"
            elif is_derivative or code in DERIVATIVE_CODES:
                benefit_type = "derivative_spread"

            extraction = BenefitExtraction(
                transaction_date=self._parse_date(txn.get('transaction_date')),
                transaction_code=code,
                owner_name=owner,
                security_title=security,
                shares=shares,
                reported_price=0.0,
                market_price=market_price,
                implied_value=implied_value,
                is_derivative=is_derivative,
                exercise_price=exercise_price,
                derivative_spread=derivative_spread,
                tax_benefit_estimate=tax_benefit,
                benefit_type=benefit_type,
            )
            extractions.append(extraction)

        return extractions

    def build_insider_profiles(
        self,
        extractions: List[BenefitExtraction],
        filing_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[InsiderBenefitProfile]:
        """Build cumulative benefit profiles per insider."""
        profiles: Dict[str, InsiderBenefitProfile] = {}

        for ext in extractions:
            owner = ext.owner_name
            if owner not in profiles:
                profiles[owner] = InsiderBenefitProfile(owner_name=owner)

            profile = profiles[owner]
            profile.total_zero_dollar_transactions += 1
            profile.total_shares_at_zero += ext.shares
            profile.total_implied_value += ext.implied_value
            profile.total_derivative_spread += ext.derivative_spread
            profile.total_tax_benefit += ext.tax_benefit_estimate
            profile.transaction_codes_used.append(ext.transaction_code)
            profile.extractions.append(ext)

            if ext.transaction_date:
                if profile.date_range_start is None or ext.transaction_date < profile.date_range_start:
                    profile.date_range_start = ext.transaction_date
                if profile.date_range_end is None or ext.transaction_date > profile.date_range_end:
                    profile.date_range_end = ext.transaction_date

        # Calculate combined benefits
        for profile in profiles.values():
            profile.combined_benefit = (
                profile.total_implied_value +
                profile.total_derivative_spread +
                profile.total_tax_benefit
            )

        return list(profiles.values())

    def build_issuer_summary(
        self,
        insider_profiles: List[InsiderBenefitProfile],
        issuer_name: str = "",
        issuer_cik: str = "",
    ) -> IssuerBenefitSummary:
        """Build aggregate benefit summary for an issuer."""
        summary = IssuerBenefitSummary(
            issuer_name=issuer_name,
            issuer_cik=issuer_cik,
            unique_insiders=len(insider_profiles),
            insider_profiles=insider_profiles,
        )

        for profile in insider_profiles:
            summary.total_zero_dollar_transactions += profile.total_zero_dollar_transactions
            summary.total_implied_value += profile.total_implied_value
            summary.total_derivative_spread += profile.total_derivative_spread
            summary.total_tax_benefit += profile.total_tax_benefit

        summary.combined_benefit = (
            summary.total_implied_value +
            summary.total_derivative_spread +
            summary.total_tax_benefit
        )

        return summary

    def _lookup_price(
        self,
        security: str,
        underlying: str,
        txn_date: Any,
        market_prices: Optional[Dict[str, float]],
    ) -> float:
        """Look up market price with fallback strategies."""
        if not market_prices:
            return 0.0

        # Direct security lookup
        if security and security in market_prices:
            return market_prices[security]

        # Underlying security lookup
        if underlying and underlying in market_prices:
            return market_prices[underlying]

        # Date-keyed lookup
        date_str = str(txn_date) if txn_date else ''
        date_key = f"{security}:{date_str}"
        if date_key in market_prices:
            return market_prices[date_key]

        if underlying:
            date_key = f"{underlying}:{date_str}"
            if date_key in market_prices:
                return market_prices[date_key]

        return 0.0

    def _parse_date(self, val: Any) -> Optional[date]:
        """Parse date from various formats."""
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y%m%d'):
                try:
                    return datetime.strptime(val, fmt).date()
                except ValueError:
                    continue
        return None
