"""
Transaction Code Constants
===========================

SEC Form 4 transaction code taxonomy with zero-dollar legitimacy classification.

Reference:
- Section 2.4: Transaction Code Classification
- SEC Form 4 Instructions
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class TransactionCode(str, Enum):
    """
    SEC Form 4 Transaction Codes.
    
    All 20 standard transaction codes per SEC Form 4 instructions.
    
    Values:
        P: Open market or private purchase
        S: Open market or private sale
        V: Transaction voluntarily reported earlier than required
        A: Grant, award or other acquisition
        D: Disposition to the issuer of or surrender of shares
        F: Payment of exercise price or tax liability by delivering shares
        I: Discretionary transaction per Rule 16b-3(f)
        M: Exercise or conversion of derivative security
        C: Conversion of derivative security
        E: Expiration of short derivative position
        H: Expiration of long derivative position
        O: Exercise of out-of-the-money derivative security
        X: Exercise of in-the-money or at-the-money derivative security
        G: Gift of securities
        L: Small acquisition under Rule 16a-6
        W: Acquisition or disposition by will or laws of descent
        Z: Deposit into or withdrawal from voting trust
        J: Other acquisition or disposition
        K: Transaction in equity swap or instrument with similar characteristics
        U: Disposition pursuant to tender offer
    """
    P = "P"  # Purchase
    S = "S"  # Sale
    V = "V"  # Voluntary early report
    A = "A"  # Award/Grant
    D = "D"  # Disposition to issuer
    F = "F"  # Payment via shares
    I = "I"  # Discretionary transaction
    M = "M"  # Exercise/Conversion
    C = "C"  # Conversion
    E = "E"  # Expiration (short)
    H = "H"  # Expiration (long)
    O = "O"  # Exercise (OTM)
    X = "X"  # Exercise (ITM/ATM)
    G = "G"  # Gift
    L = "L"  # Small acquisition
    W = "W"  # Will/Inheritance
    Z = "Z"  # Voting trust
    J = "J"  # Other
    K = "K"  # Equity swap
    U = "U"  # Tender offer


@dataclass
class TransactionCodeInfo:
    """
    Transaction code metadata for forensic analysis.
    
    Attributes:
        code: Single-letter transaction code
        description: Full description of transaction type
        zero_dollar_legitimacy: Legitimacy of zero-dollar pricing (0.0-1.0)
            1.0 = Always legitimate (e.g., gifts)
            0.5 = Context-dependent
            0.0 = Never legitimate
        forensic_scrutiny_level: Required scrutiny level (1-5)
            5 = Maximum scrutiny (potential fraud)
            1 = Minimal scrutiny (routine)
        typical_zero_dollar: Whether code typically involves zero-dollar
        requires_footnote: Whether zero-dollar requires footnote explanation
        derivative_related: Whether code is derivative-related
    """
    code: str
    description: str
    zero_dollar_legitimacy: float
    forensic_scrutiny_level: int
    typical_zero_dollar: bool
    requires_footnote: bool
    derivative_related: bool


# Transaction Code Taxonomy
TRANSACTION_CODE_TAXONOMY: Dict[TransactionCode, TransactionCodeInfo] = {
    TransactionCode.P: TransactionCodeInfo(
        code="P",
        description="Open market or private purchase",
        zero_dollar_legitimacy=0.0,
        forensic_scrutiny_level=5,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=False,
    ),
    TransactionCode.S: TransactionCodeInfo(
        code="S",
        description="Open market or private sale",
        zero_dollar_legitimacy=0.0,
        forensic_scrutiny_level=5,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=False,
    ),
    TransactionCode.V: TransactionCodeInfo(
        code="V",
        description="Transaction voluntarily reported earlier than required",
        zero_dollar_legitimacy=0.3,
        forensic_scrutiny_level=3,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=False,
    ),
    TransactionCode.A: TransactionCodeInfo(
        code="A",
        description="Grant, award or other acquisition",
        zero_dollar_legitimacy=0.9,
        forensic_scrutiny_level=2,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=False,
    ),
    TransactionCode.D: TransactionCodeInfo(
        code="D",
        description="Disposition to the issuer or surrender of shares",
        zero_dollar_legitimacy=0.7,
        forensic_scrutiny_level=3,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=False,
    ),
    TransactionCode.F: TransactionCodeInfo(
        code="F",
        description="Payment of exercise price or tax liability by delivering shares",
        zero_dollar_legitimacy=0.8,
        forensic_scrutiny_level=2,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=True,
    ),
    TransactionCode.I: TransactionCodeInfo(
        code="I",
        description="Discretionary transaction per Rule 16b-3(f)",
        zero_dollar_legitimacy=0.5,
        forensic_scrutiny_level=4,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=False,
    ),
    TransactionCode.M: TransactionCodeInfo(
        code="M",
        description="Exercise or conversion of derivative security",
        zero_dollar_legitimacy=0.6,
        forensic_scrutiny_level=3,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=True,
    ),
    TransactionCode.C: TransactionCodeInfo(
        code="C",
        description="Conversion of derivative security",
        zero_dollar_legitimacy=0.7,
        forensic_scrutiny_level=3,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=True,
    ),
    TransactionCode.E: TransactionCodeInfo(
        code="E",
        description="Expiration of short derivative position",
        zero_dollar_legitimacy=1.0,
        forensic_scrutiny_level=1,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=True,
    ),
    TransactionCode.H: TransactionCodeInfo(
        code="H",
        description="Expiration of long derivative position",
        zero_dollar_legitimacy=1.0,
        forensic_scrutiny_level=1,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=True,
    ),
    TransactionCode.O: TransactionCodeInfo(
        code="O",
        description="Exercise of out-of-the-money derivative security",
        zero_dollar_legitimacy=0.6,
        forensic_scrutiny_level=3,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=True,
    ),
    TransactionCode.X: TransactionCodeInfo(
        code="X",
        description="Exercise of in-the-money or at-the-money derivative security",
        zero_dollar_legitimacy=0.6,
        forensic_scrutiny_level=3,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=True,
    ),
    TransactionCode.G: TransactionCodeInfo(
        code="G",
        description="Gift of securities",
        zero_dollar_legitimacy=1.0,
        forensic_scrutiny_level=2,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=False,
    ),
    TransactionCode.L: TransactionCodeInfo(
        code="L",
        description="Small acquisition under Rule 16a-6",
        zero_dollar_legitimacy=0.5,
        forensic_scrutiny_level=3,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=False,
    ),
    TransactionCode.W: TransactionCodeInfo(
        code="W",
        description="Acquisition or disposition by will or laws of descent",
        zero_dollar_legitimacy=1.0,
        forensic_scrutiny_level=1,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=False,
    ),
    TransactionCode.Z: TransactionCodeInfo(
        code="Z",
        description="Deposit into or withdrawal from voting trust",
        zero_dollar_legitimacy=0.8,
        forensic_scrutiny_level=3,
        typical_zero_dollar=True,
        requires_footnote=False,
        derivative_related=False,
    ),
    TransactionCode.J: TransactionCodeInfo(
        code="J",
        description="Other acquisition or disposition",
        zero_dollar_legitimacy=0.4,
        forensic_scrutiny_level=4,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=False,
    ),
    TransactionCode.K: TransactionCodeInfo(
        code="K",
        description="Transaction in equity swap or instrument with similar characteristics",
        zero_dollar_legitimacy=0.5,
        forensic_scrutiny_level=4,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=True,
    ),
    TransactionCode.U: TransactionCodeInfo(
        code="U",
        description="Disposition pursuant to tender offer",
        zero_dollar_legitimacy=0.3,
        forensic_scrutiny_level=3,
        typical_zero_dollar=False,
        requires_footnote=True,
        derivative_related=False,
    ),
}


def get_transaction_code_info(code: str) -> TransactionCodeInfo:
    """
    Get transaction code information.
    
    Args:
        code: Single-letter transaction code
        
    Returns:
        TransactionCodeInfo for the code
        
    Raises:
        ValueError: If code is not recognized
    """
    try:
        transaction_code = TransactionCode(code.upper())
        return TRANSACTION_CODE_TAXONOMY[transaction_code]
    except (ValueError, KeyError):
        raise ValueError(f"Unrecognized transaction code: {code}")


def is_zero_dollar_suspicious(code: str, magnitude_tier: int) -> bool:
    """
    Determine if zero-dollar transaction is suspicious.
    
    Combines transaction code legitimacy with magnitude tier to assess
    whether a zero-dollar transaction warrants investigation.
    
    Args:
        code: Transaction code
        magnitude_tier: Magnitude tier (1-4, 4 being largest)
        
    Returns:
        True if combination is suspicious
    """
    try:
        info = get_transaction_code_info(code)
        
        # High legitimacy codes (>0.8) are rarely suspicious
        if info.zero_dollar_legitimacy > 0.8:
            return False
        
        # Low legitimacy codes (<0.5) are suspicious for any magnitude
        if info.zero_dollar_legitimacy < 0.5:
            return True
        
        # Medium legitimacy: suspicious if large magnitude (Tier 3-4)
        return magnitude_tier >= 3
        
    except ValueError:
        # Unknown code: treat as suspicious
        return True
