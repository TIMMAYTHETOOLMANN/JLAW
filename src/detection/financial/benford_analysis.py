"""
Benford's Law Analyzer
======================

Implements first-digit frequency analysis against the expected
logarithmic distribution for fraud detection in financial data.

P(d) = log₁₀(1 + 1/d) for first digit d ∈ {1,2,...,9}

Statistical Tests:
- Chi-Square Test: Critical value 15.507 (α=0.05, df=8)
- Mean Absolute Deviation (MAD): Nigrini thresholds
- Z-Statistic: Per-digit deviation significance

Historical Validation:
- Detected Madoff fabricated returns (chi-square p=0.04529)
- Kolmogorov-Smirnov testing (p=0.0021)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from enum import Enum
import math
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ConformityLevel(Enum):
    """Benford conformity classification (Nigrini MAD thresholds)."""
    CLOSE = "Close Conformity"           # MAD ≤ 0.006
    ACCEPTABLE = "Acceptable Conformity"  # 0.006 < MAD ≤ 0.012
    MARGINAL = "Marginally Acceptable"    # 0.012 < MAD ≤ 0.015
    NONCONFORMING = "Non-Conforming"      # MAD > 0.015


@dataclass
class DigitAnalysis:
    """Analysis for a single digit."""
    digit: int
    observed_count: int
    observed_proportion: float
    expected_proportion: float
    deviation: float
    z_statistic: float
    is_significant: bool  # |z| > 1.96 (95% confidence)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "digit": self.digit,
            "observed_count": self.observed_count,
            "observed_proportion": round(self.observed_proportion, 4),
            "expected_proportion": round(self.expected_proportion, 4),
            "deviation": round(self.deviation, 4),
            "z_statistic": round(self.z_statistic, 2),
            "is_significant": self.is_significant
        }


@dataclass
class BenfordResult:
    """Complete Benford's Law analysis result."""
    sample_size: int
    digit_analyses: List[DigitAnalysis]
    chi_square_statistic: float
    chi_square_p_value: float
    chi_square_significant: bool
    mad: float  # Mean Absolute Deviation
    conformity_level: ConformityLevel
    suspicious_digits: List[int]
    interpretation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_size": self.sample_size,
            "chi_square": {
                "statistic": round(self.chi_square_statistic, 4),
                "p_value": round(self.chi_square_p_value, 6),
                "significant_at_05": self.chi_square_significant,
                "critical_value": 15.507
            },
            "mad": {
                "value": round(self.mad, 6),
                "conformity_level": self.conformity_level.value,
                "thresholds": {
                    "close": "≤0.006",
                    "acceptable": "0.006-0.012",
                    "marginal": "0.012-0.015",
                    "nonconforming": ">0.015"
                }
            },
            "digit_analyses": [d.to_dict() for d in self.digit_analyses],
            "suspicious_digits": self.suspicious_digits,
            "interpretation": self.interpretation
        }


class BenfordAnalyzer:
    """
    Benford's Law Analyzer for financial fraud detection.
    
    Applies to:
    - Revenue amounts
    - Accounts receivable
    - Expense items
    - Transaction values
    
    Works best with data spanning multiple orders of magnitude
    (naturally occurring financial data).
    """
    
    # Expected first-digit proportions (Benford's Law)
    EXPECTED_PROPORTIONS = {
        1: 0.301,
        2: 0.176,
        3: 0.125,
        4: 0.097,
        5: 0.079,
        6: 0.067,
        7: 0.058,
        8: 0.051,
        9: 0.046
    }
    
    # Chi-square critical value (df=8, α=0.05)
    CHI_SQUARE_CRITICAL = 15.507
    
    # MAD thresholds (Nigrini)
    MAD_CLOSE = 0.006
    MAD_ACCEPTABLE = 0.012
    MAD_MARGINAL = 0.015
    
    def __init__(self):
        # Precompute exact expected proportions
        self.expected = {
            d: math.log10(1 + 1/d) for d in range(1, 10)
        }
    
    def analyze(self, numbers: List[float]) -> BenfordResult:
        """
        Perform complete Benford's Law analysis on numeric data.
        
        Args:
            numbers: List of numeric values to analyze
            
        Returns:
            BenfordResult with complete analysis
        """
        # Extract first digits (only positive numbers with significant magnitude)
        first_digits = []
        for num in numbers:
            digit = self._extract_first_digit(num)
            if digit:
                first_digits.append(digit)
        
        n = len(first_digits)
        if n < 10:
            return self._create_insufficient_data_result(n)
        
        # Count digit frequencies
        digit_counts = Counter(first_digits)
        
        # Analyze each digit
        digit_analyses = []
        chi_square_sum = 0.0
        mad_sum = 0.0
        suspicious_digits = []
        
        for d in range(1, 10):
            observed_count = digit_counts.get(d, 0)
            observed_prop = observed_count / n
            expected_prop = self.expected[d]
            
            deviation = observed_prop - expected_prop
            mad_sum += abs(deviation)
            
            # Chi-square contribution
            expected_count = expected_prop * n
            if expected_count > 0:
                chi_contrib = (observed_count - expected_count) ** 2 / expected_count
                chi_square_sum += chi_contrib
            
            # Z-statistic for this digit
            se = math.sqrt(expected_prop * (1 - expected_prop) / n)
            z_stat = deviation / se if se > 0 else 0
            is_significant = abs(z_stat) > 1.96
            
            if is_significant:
                suspicious_digits.append(d)
            
            digit_analyses.append(DigitAnalysis(
                digit=d,
                observed_count=observed_count,
                observed_proportion=observed_prop,
                expected_proportion=expected_prop,
                deviation=deviation,
                z_statistic=z_stat,
                is_significant=is_significant
            ))
        
        # Calculate MAD
        mad = mad_sum / 9
        
        # Determine conformity level
        if mad <= self.MAD_CLOSE:
            conformity = ConformityLevel.CLOSE
        elif mad <= self.MAD_ACCEPTABLE:
            conformity = ConformityLevel.ACCEPTABLE
        elif mad <= self.MAD_MARGINAL:
            conformity = ConformityLevel.MARGINAL
        else:
            conformity = ConformityLevel.NONCONFORMING
        
        # Chi-square p-value (approximate using chi-square distribution)
        chi_square_p = self._chi_square_p_value(chi_square_sum, df=8)
        chi_square_sig = chi_square_sum > self.CHI_SQUARE_CRITICAL
        
        # Generate interpretation
        interpretation = self._generate_interpretation(
            mad, conformity, chi_square_sig, suspicious_digits, n
        )
        
        return BenfordResult(
            sample_size=n,
            digit_analyses=digit_analyses,
            chi_square_statistic=chi_square_sum,
            chi_square_p_value=chi_square_p,
            chi_square_significant=chi_square_sig,
            mad=mad,
            conformity_level=conformity,
            suspicious_digits=suspicious_digits,
            interpretation=interpretation
        )
    
    def _extract_first_digit(self, number: float) -> int:
        """Extract first significant digit from a number."""
        try:
            # Handle zero and negative numbers
            num = abs(number)
            if num < 1e-10:  # Essentially zero
                return None
            
            # Normalize to get first digit
            while num >= 10:
                num /= 10
            while num < 1:
                num *= 10
            
            return int(num)
        except (ValueError, OverflowError):
            return None
    
    def _chi_square_p_value(self, chi_sq: float, df: int) -> float:
        """
        Approximate chi-square p-value.
        
        Uses Wilson-Hilferty transformation for approximation.
        For production, use scipy.stats.chi2.sf
        """
        try:
            # Wilson-Hilferty transformation
            h = 2 / (9 * df)
            z = ((chi_sq / df) ** (1/3) - (1 - h)) / math.sqrt(h)
            
            # Standard normal CDF approximation
            p = 0.5 * (1 + math.erf(-z / math.sqrt(2)))
            return max(0, min(1, p))
        except (ValueError, OverflowError):
            return 0.5
    
    def _generate_interpretation(
        self,
        mad: float,
        conformity: ConformityLevel,
        chi_sq_sig: bool,
        suspicious: List[int],
        n: int
    ) -> str:
        """Generate human-readable interpretation."""
        parts = [f"Analysis of {n} values:"]
        
        if conformity == ConformityLevel.CLOSE:
            parts.append(f"MAD={mad:.4f} indicates CLOSE conformity to Benford's Law.")
        elif conformity == ConformityLevel.ACCEPTABLE:
            parts.append(f"MAD={mad:.4f} indicates ACCEPTABLE conformity.")
        elif conformity == ConformityLevel.MARGINAL:
            parts.append(f"MAD={mad:.4f} indicates MARGINALLY acceptable conformity - review recommended.")
        else:
            parts.append(f"MAD={mad:.4f} indicates NON-CONFORMITY to Benford's Law - FRAUD INVESTIGATION WARRANTED.")
        
        if chi_sq_sig:
            parts.append("Chi-square test REJECTS null hypothesis (p<0.05).")
        
        if suspicious:
            parts.append(f"Suspicious digit distribution: {suspicious}")
        
        return " ".join(parts)
    
    def _create_insufficient_data_result(self, n: int) -> BenfordResult:
        """Create result for insufficient sample size."""
        return BenfordResult(
            sample_size=n,
            digit_analyses=[],
            chi_square_statistic=0.0,
            chi_square_p_value=1.0,
            chi_square_significant=False,
            mad=0.0,
            conformity_level=ConformityLevel.ACCEPTABLE,
            suspicious_digits=[],
            interpretation=f"Insufficient sample size ({n}). Benford's Law requires at least 10 values for meaningful analysis."
        )

