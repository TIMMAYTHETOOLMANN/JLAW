"""
Rule 144(d)(3) Tacking Calculator
==================================

Implements tacking provisions for holding period calculations under Rule 144(d)(3).

Tacking allows holding periods to be combined when restricted securities are
acquired through certain non-sale transactions.

SEC Reference: 17 CFR §230.144(d)(3)
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TackingEligibility(Enum):
    """Enumeration of tacking eligibility types."""
    ELIGIBLE_CONVERSION = "Eligible Conversion"  # Security conversion (e.g., preferred to common)
    ELIGIBLE_GIFT = "Eligible Gift"  # Bona fide gift
    ELIGIBLE_ESTATE = "Eligible Estate Transfer"  # Estate/trust transfer
    ELIGIBLE_PLEDGE = "Eligible Pledge Default"  # Pledgee selling after default
    INELIGIBLE_PURCHASE = "Ineligible Purchase"  # Purchase transaction
    INELIGIBLE_OTHER = "Ineligible Other"  # Other non-qualifying transaction


@dataclass
class SecurityAcquisition:
    """Represents a single security acquisition event."""
    acquisition_date: date
    acquisition_type: str  # PURCHASE, CONVERSION, GIFT, ESTATE, PLEDGE, etc.
    shares: int
    predecessor_security: Optional[str] = None  # For conversions
    donor_holding_period_start: Optional[date] = None  # For gifts/estates
    original_acquisition_date: Optional[date] = None  # For tacking


@dataclass
class TackingAnalysis:
    """Result of tacking eligibility analysis."""
    eligible_for_tacking: bool
    tacking_type: TackingEligibility
    effective_holding_period_start: date
    actual_acquisition_date: date
    holding_period_days: int
    explanation: str
    
    def to_dict(self):
        return {
            "eligible_for_tacking": self.eligible_for_tacking,
            "tacking_type": self.tacking_type.value,
            "effective_holding_period_start": self.effective_holding_period_start.isoformat(),
            "actual_acquisition_date": self.actual_acquisition_date.isoformat(),
            "holding_period_days": self.holding_period_days,
            "explanation": self.explanation
        }


class TackingCalculator:
    """
    Calculator for Rule 144(d)(3) tacking provisions.
    
    Determines whether holding periods can be combined (tacked) for
    securities acquired through conversions, gifts, estate transfers, etc.
    """
    
    def __init__(self):
        self.logger = logger
    
    def analyze_tacking_eligibility(
        self,
        acquisition: SecurityAcquisition,
        as_of_date: Optional[date] = None
    ) -> TackingAnalysis:
        """
        Analyze whether tacking is available for a security acquisition.
        
        Args:
            acquisition: The acquisition event to analyze
            as_of_date: Date to calculate holding period as of (defaults to today)
        
        Returns:
            TackingAnalysis with eligibility determination
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        acquisition_type = acquisition.acquisition_type.upper()
        
        # Determine tacking eligibility based on acquisition type
        if acquisition_type == "CONVERSION":
            return self._analyze_conversion_tacking(acquisition, as_of_date)
        elif acquisition_type == "GIFT":
            return self._analyze_gift_tacking(acquisition, as_of_date)
        elif acquisition_type in ("ESTATE", "TRUST", "INHERITANCE"):
            return self._analyze_estate_tacking(acquisition, as_of_date)
        elif acquisition_type in ("PLEDGE", "PLEDGE_DEFAULT"):
            return self._analyze_pledge_tacking(acquisition, as_of_date)
        elif acquisition_type == "PURCHASE":
            return self._no_tacking_purchase(acquisition, as_of_date)
        else:
            return self._no_tacking_other(acquisition, as_of_date)
    
    def _analyze_conversion_tacking(
        self,
        acquisition: SecurityAcquisition,
        as_of_date: date
    ) -> TackingAnalysis:
        """
        Rule 144(d)(3)(i): Security conversions are eligible for tacking.
        
        Example: Conversion of preferred stock to common stock allows
        tacking of the holding period for the preferred stock.
        """
        if acquisition.original_acquisition_date:
            # Tacking is allowed - use original acquisition date
            effective_start = acquisition.original_acquisition_date
            holding_days = (as_of_date - effective_start).days
            
            return TackingAnalysis(
                eligible_for_tacking=True,
                tacking_type=TackingEligibility.ELIGIBLE_CONVERSION,
                effective_holding_period_start=effective_start,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    f"Conversion tacking allowed under Rule 144(d)(3)(i). "
                    f"Holding period starts from original acquisition on "
                    f"{effective_start.isoformat()}."
                )
            )
        else:
            # No original date provided - cannot tack
            holding_days = (as_of_date - acquisition.acquisition_date).days
            
            return TackingAnalysis(
                eligible_for_tacking=False,
                tacking_type=TackingEligibility.ELIGIBLE_CONVERSION,
                effective_holding_period_start=acquisition.acquisition_date,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    "Conversion tacking potentially available but original "
                    "acquisition date not provided."
                )
            )
    
    def _analyze_gift_tacking(
        self,
        acquisition: SecurityAcquisition,
        as_of_date: date
    ) -> TackingAnalysis:
        """
        Rule 144(d)(3)(ii): Gifts are eligible for tacking.
        
        Donee (recipient) can tack the donor's holding period.
        """
        if acquisition.donor_holding_period_start:
            # Tacking is allowed - use donor's holding period start
            effective_start = acquisition.donor_holding_period_start
            holding_days = (as_of_date - effective_start).days
            
            return TackingAnalysis(
                eligible_for_tacking=True,
                tacking_type=TackingEligibility.ELIGIBLE_GIFT,
                effective_holding_period_start=effective_start,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    f"Gift tacking allowed under Rule 144(d)(3)(ii). "
                    f"Donee may tack donor's holding period starting "
                    f"{effective_start.isoformat()}."
                )
            )
        else:
            # No donor holding period provided
            holding_days = (as_of_date - acquisition.acquisition_date).days
            
            return TackingAnalysis(
                eligible_for_tacking=False,
                tacking_type=TackingEligibility.ELIGIBLE_GIFT,
                effective_holding_period_start=acquisition.acquisition_date,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    "Gift tacking potentially available but donor's holding "
                    "period start date not provided."
                )
            )
    
    def _analyze_estate_tacking(
        self,
        acquisition: SecurityAcquisition,
        as_of_date: date
    ) -> TackingAnalysis:
        """
        Rule 144(d)(3)(ii): Estate/trust transfers are eligible for tacking.
        
        Beneficiary can tack the decedent's holding period.
        """
        if acquisition.donor_holding_period_start:
            # Tacking is allowed - use decedent's holding period start
            effective_start = acquisition.donor_holding_period_start
            holding_days = (as_of_date - effective_start).days
            
            return TackingAnalysis(
                eligible_for_tacking=True,
                tacking_type=TackingEligibility.ELIGIBLE_ESTATE,
                effective_holding_period_start=effective_start,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    f"Estate transfer tacking allowed under Rule 144(d)(3)(ii). "
                    f"Beneficiary may tack decedent's holding period starting "
                    f"{effective_start.isoformat()}."
                )
            )
        else:
            # No decedent holding period provided
            holding_days = (as_of_date - acquisition.acquisition_date).days
            
            return TackingAnalysis(
                eligible_for_tacking=False,
                tacking_type=TackingEligibility.ELIGIBLE_ESTATE,
                effective_holding_period_start=acquisition.acquisition_date,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    "Estate transfer tacking potentially available but "
                    "decedent's holding period start date not provided."
                )
            )
    
    def _analyze_pledge_tacking(
        self,
        acquisition: SecurityAcquisition,
        as_of_date: date
    ) -> TackingAnalysis:
        """
        Rule 144(d)(3)(iii): Pledgee selling after default may tack.
        
        If pledgor defaulted, pledgee can tack pledgor's holding period.
        """
        if acquisition.donor_holding_period_start:
            # Tacking is allowed - use pledgor's holding period
            effective_start = acquisition.donor_holding_period_start
            holding_days = (as_of_date - effective_start).days
            
            return TackingAnalysis(
                eligible_for_tacking=True,
                tacking_type=TackingEligibility.ELIGIBLE_PLEDGE,
                effective_holding_period_start=effective_start,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    f"Pledge default tacking allowed under Rule 144(d)(3)(iii). "
                    f"Pledgee may tack pledgor's holding period starting "
                    f"{effective_start.isoformat()}."
                )
            )
        else:
            # No pledgor holding period provided
            holding_days = (as_of_date - acquisition.acquisition_date).days
            
            return TackingAnalysis(
                eligible_for_tacking=False,
                tacking_type=TackingEligibility.ELIGIBLE_PLEDGE,
                effective_holding_period_start=acquisition.acquisition_date,
                actual_acquisition_date=acquisition.acquisition_date,
                holding_period_days=holding_days,
                explanation=(
                    "Pledge default tacking potentially available but "
                    "pledgor's holding period start date not provided."
                )
            )
    
    def _no_tacking_purchase(
        self,
        acquisition: SecurityAcquisition,
        as_of_date: date
    ) -> TackingAnalysis:
        """Purchase transactions are NOT eligible for tacking."""
        holding_days = (as_of_date - acquisition.acquisition_date).days
        
        return TackingAnalysis(
            eligible_for_tacking=False,
            tacking_type=TackingEligibility.INELIGIBLE_PURCHASE,
            effective_holding_period_start=acquisition.acquisition_date,
            actual_acquisition_date=acquisition.acquisition_date,
            holding_period_days=holding_days,
            explanation=(
                "Purchase transactions are not eligible for tacking under "
                "Rule 144(d)(3). Holding period begins on purchase date."
            )
        )
    
    def _no_tacking_other(
        self,
        acquisition: SecurityAcquisition,
        as_of_date: date
    ) -> TackingAnalysis:
        """Other acquisition types - no tacking."""
        holding_days = (as_of_date - acquisition.acquisition_date).days
        
        return TackingAnalysis(
            eligible_for_tacking=False,
            tacking_type=TackingEligibility.INELIGIBLE_OTHER,
            effective_holding_period_start=acquisition.acquisition_date,
            actual_acquisition_date=acquisition.acquisition_date,
            holding_period_days=holding_days,
            explanation=(
                f"Acquisition type '{acquisition.acquisition_type}' is not "
                "eligible for tacking under Rule 144(d)(3)."
            )
        )
    
    def calculate_combined_holding_period(
        self,
        acquisitions: List[SecurityAcquisition],
        as_of_date: Optional[date] = None
    ) -> Tuple[date, int, List[TackingAnalysis]]:
        """
        Calculate the combined holding period across multiple acquisitions.
        
        Args:
            acquisitions: List of acquisitions in chronological order
            as_of_date: Date to calculate holding period as of
        
        Returns:
            Tuple of (effective_start_date, total_holding_days, analyses)
        """
        if not acquisitions:
            raise ValueError("No acquisitions provided")
        
        if as_of_date is None:
            as_of_date = date.today()
        
        analyses = []
        effective_start = acquisitions[0].acquisition_date
        
        # Analyze each acquisition
        for acquisition in acquisitions:
            analysis = self.analyze_tacking_eligibility(acquisition, as_of_date)
            analyses.append(analysis)
            
            # Update effective start if tacking is available
            if analysis.eligible_for_tacking:
                if analysis.effective_holding_period_start < effective_start:
                    effective_start = analysis.effective_holding_period_start
        
        # Calculate total holding period
        total_holding_days = (as_of_date - effective_start).days
        
        return effective_start, total_holding_days, analyses
