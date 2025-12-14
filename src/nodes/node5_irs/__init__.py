"""
JLAW Node 5: IRC §83 Tax Exposure Calculator Module
"""

from .irc83_tax_calculator import (
    IRC83TaxCalculator,
    IRC83ViolationType,
    EquityAwardType,
    GrantType,
    EquityGrant,
    Section83bElection,
    TaxExposure,
    EquityDisposition,
    IRC83Violation
)

__all__ = [
    'IRC83TaxCalculator',
    'IRC83ViolationType',
    'EquityAwardType',
    'GrantType',
    'EquityGrant',
    'Section83bElection',
    'TaxExposure',
    'EquityDisposition',
    'IRC83Violation'
]

