"""
Benford's Law Analyzer - Statistical Fraud Detection
===================================================

Advanced implementation of Benford's Law for detecting financial anomalies
and potential fraud in numerical datasets.

Benford's Law states that in many naturally occurring collections of numbers,
the leading digit is likely to be small. Specifically:
- 1 appears as the leading digit about 30.1% of the time
- 2 appears about 17.6% of the time
- 9 appears about 4.6% of the time

Deviations from this distribution may indicate:
- Fraudulent data
- Data manipulation
- Non-natural data generation
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import numpy as np
from scipy import stats
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BenfordsAnalysisResult:
    """Results from Benford's Law analysis"""
    dataset_name: str
    total_numbers: int
    valid_numbers: int
    
    # First digit analysis
    observed_distribution: Dict[int, float]
    expected_distribution: Dict[int, float]
    chi_square_statistic: float
    chi_square_p_value: float
    
    # Second digit analysis
    second_digit_observed: Dict[int, float]
    second_digit_expected: Dict[int, float]
    second_digit_chi_square: float
    second_digit_p_value: float
    
    # First two digits analysis
    first_two_digits_sample: Dict[int, int]
    
    # Anomaly detection
    is_suspicious: bool
    confidence_level: float
    suspicious_digits: List[int]
    deviation_scores: Dict[int, float]
    
    # Detailed metrics
    mean_absolute_deviation: float
    kullback_leibler_divergence: float
    kolmogorov_smirnov_statistic: float
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class BenfordsLawAnalyzer:
    """
    Advanced Benford's Law analyzer with multiple detection strategies
    """
    
    # Expected frequencies for first digit (Benford's Law)
    BENFORD_FIRST_DIGIT = {
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
    
    # Expected frequencies for second digit
    BENFORD_SECOND_DIGIT = {
        0: 0.1197,
        1: 0.1139,
        2: 0.1088,
        3: 0.1043,
        4: 0.1003,
        5: 0.0967,
        6: 0.0934,
        7: 0.0904,
        8: 0.0876,
        9: 0.0850
    }
    
    def __init__(
        self,
        significance_level: float = 0.05,
        suspicious_threshold: float = 0.15,
        min_sample_size: int = 100
    ):
        """
        Initialize Benford's Law analyzer
        
        Args:
            significance_level: P-value threshold for chi-square test
            suspicious_threshold: MAD threshold for suspicion flag
            min_sample_size: Minimum numbers required for reliable analysis
        """
        self.significance_level = significance_level
        self.suspicious_threshold = suspicious_threshold
        self.min_sample_size = min_sample_size
        self.logger = logging.getLogger(__name__)
    
    def analyze(
        self,
        numbers: List[float],
        dataset_name: str = "Unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> BenfordsAnalysisResult:
        """
        Perform comprehensive Benford's Law analysis
        
        Args:
            numbers: List of numerical values to analyze
            dataset_name: Name/description of the dataset
            metadata: Additional metadata about the dataset
            
        Returns:
            BenfordsAnalysisResult with complete analysis
        """
        self.logger.info(f"Starting Benford's Law analysis for {dataset_name}")
        
        # Extract valid positive numbers
        valid_numbers = self._extract_valid_numbers(numbers)
        
        if len(valid_numbers) < self.min_sample_size:
            self.logger.warning(
                f"Sample size {len(valid_numbers)} below minimum {self.min_sample_size}"
            )
        
        # First digit analysis
        first_digits = self._extract_first_digits(valid_numbers)
        observed_dist = self._calculate_distribution(first_digits)
        chi2_stat, chi2_p = self._chi_square_test(
            observed_dist,
            self.BENFORD_FIRST_DIGIT,
            len(first_digits)
        )
        
        # Second digit analysis
        second_digits = self._extract_second_digits(valid_numbers)
        second_observed = self._calculate_distribution(second_digits)
        second_chi2, second_p = self._chi_square_test(
            second_observed,
            self.BENFORD_SECOND_DIGIT,
            len(second_digits)
        )
        
        # First two digits sample
        first_two = self._extract_first_two_digits(valid_numbers)
        first_two_sample = dict(Counter(first_two).most_common(20))
        
        # Calculate deviation metrics
        mad = self._mean_absolute_deviation(observed_dist, self.BENFORD_FIRST_DIGIT)
        kl_div = self._kullback_leibler_divergence(observed_dist, self.BENFORD_FIRST_DIGIT)
        ks_stat = self._kolmogorov_smirnov_test(first_digits)
        
        # Identify suspicious digits
        deviation_scores = self._calculate_deviation_scores(
            observed_dist,
            self.BENFORD_FIRST_DIGIT
        )
        suspicious_digits = [
            digit for digit, score in deviation_scores.items()
            if abs(score) > 2.0  # 2 standard deviations
        ]
        
        # Determine if dataset is suspicious
        is_suspicious = (
            chi2_p < self.significance_level or
            mad > self.suspicious_threshold or
            len(suspicious_digits) >= 3
        )
        
        # Calculate confidence level
        confidence = self._calculate_confidence(chi2_p, mad, len(suspicious_digits))
        
        return BenfordsAnalysisResult(
            dataset_name=dataset_name,
            total_numbers=len(numbers),
            valid_numbers=len(valid_numbers),
            observed_distribution=observed_dist,
            expected_distribution=self.BENFORD_FIRST_DIGIT,
            chi_square_statistic=chi2_stat,
            chi_square_p_value=chi2_p,
            second_digit_observed=second_observed,
            second_digit_expected=self.BENFORD_SECOND_DIGIT,
            second_digit_chi_square=second_chi2,
            second_digit_p_value=second_p,
            first_two_digits_sample=first_two_sample,
            is_suspicious=is_suspicious,
            confidence_level=confidence,
            suspicious_digits=suspicious_digits,
            deviation_scores=deviation_scores,
            mean_absolute_deviation=mad,
            kullback_leibler_divergence=kl_div,
            kolmogorov_smirnov_statistic=ks_stat,
            metadata=metadata or {}
        )
    
    def _extract_valid_numbers(self, numbers: List[float]) -> List[float]:
        """Extract valid positive numbers for analysis"""
        valid = []
        for num in numbers:
            try:
                val = float(num)
                if val > 0 and not math.isnan(val) and not math.isinf(val):
                    valid.append(val)
            except (ValueError, TypeError):
                continue
        return valid
    
    def _extract_first_digits(self, numbers: List[float]) -> List[int]:
        """Extract first significant digits"""
        first_digits = []
        for num in numbers:
            str_num = f"{num:.10e}"  # Scientific notation
            first_digit = int(str_num[0])
            if 1 <= first_digit <= 9:
                first_digits.append(first_digit)
        return first_digits
    
    def _extract_second_digits(self, numbers: List[float]) -> List[int]:
        """Extract second significant digits"""
        second_digits = []
        for num in numbers:
            str_num = f"{num:.10e}".replace(".", "")
            if len(str_num) >= 2:
                try:
                    second_digit = int(str_num[1])
                    if 0 <= second_digit <= 9:
                        second_digits.append(second_digit)
                except (ValueError, IndexError):
                    continue
        return second_digits
    
    def _extract_first_two_digits(self, numbers: List[float]) -> List[int]:
        """Extract first two significant digits"""
        first_two = []
        for num in numbers:
            str_num = f"{num:.10e}".replace(".", "")
            if len(str_num) >= 2:
                try:
                    two_digits = int(str_num[:2])
                    if 10 <= two_digits <= 99:
                        first_two.append(two_digits)
                except ValueError:
                    continue
        return first_two
    
    def _calculate_distribution(self, digits: List[int]) -> Dict[int, float]:
        """Calculate observed frequency distribution"""
        if not digits:
            return {}
        
        counts = Counter(digits)
        total = len(digits)
        return {digit: count / total for digit, count in counts.items()}
    
    def _chi_square_test(
        self,
        observed: Dict[int, float],
        expected: Dict[int, float],
        n: int
    ) -> Tuple[float, float]:
        """Perform chi-square goodness-of-fit test"""
        if not observed or n == 0:
            return 0.0, 1.0
        
        chi2_stat = 0.0
        for digit in expected.keys():
            obs_freq = observed.get(digit, 0.0)
            exp_freq = expected[digit]
            obs_count = obs_freq * n
            exp_count = exp_freq * n
            
            if exp_count > 0:
                chi2_stat += ((obs_count - exp_count) ** 2) / exp_count
        
        # Degrees of freedom = number of categories - 1
        df = len(expected) - 1
        p_value = 1 - stats.chi2.cdf(chi2_stat, df)
        
        return chi2_stat, p_value
    
    def _mean_absolute_deviation(
        self,
        observed: Dict[int, float],
        expected: Dict[int, float]
    ) -> float:
        """Calculate Mean Absolute Deviation (MAD)"""
        if not observed:
            return 0.0
        
        deviations = []
        for digit in expected.keys():
            obs = observed.get(digit, 0.0)
            exp = expected[digit]
            deviations.append(abs(obs - exp))
        
        return sum(deviations) / len(deviations) if deviations else 0.0
    
    def _kullback_leibler_divergence(
        self,
        observed: Dict[int, float],
        expected: Dict[int, float]
    ) -> float:
        """Calculate KL divergence between observed and expected distributions"""
        if not observed:
            return 0.0
        
        kl_div = 0.0
        for digit in expected.keys():
            obs = observed.get(digit, 1e-10)  # Small value to avoid log(0)
            exp = expected[digit]
            if obs > 0:
                kl_div += obs * math.log(obs / exp)
        
        return kl_div
    
    def _kolmogorov_smirnov_test(self, digits: List[int]) -> float:
        """Perform Kolmogorov-Smirnov test"""
        if not digits:
            return 0.0
        
        # Create empirical CDF
        sorted_digits = sorted(digits)
        n = len(sorted_digits)
        
        # Calculate maximum deviation from expected CDF
        max_deviation = 0.0
        cumulative_expected = 0.0
        
        for digit in range(1, 10):
            cumulative_expected += self.BENFORD_FIRST_DIGIT[digit]
            cumulative_observed = sum(1 for d in sorted_digits if d <= digit) / n
            deviation = abs(cumulative_observed - cumulative_expected)
            max_deviation = max(max_deviation, deviation)
        
        return max_deviation
    
    def _calculate_deviation_scores(
        self,
        observed: Dict[int, float],
        expected: Dict[int, float]
    ) -> Dict[int, float]:
        """Calculate standardized deviation scores for each digit"""
        scores = {}
        for digit in expected.keys():
            obs = observed.get(digit, 0.0)
            exp = expected[digit]
            # Standardized residual
            variance = exp * (1 - exp)
            if variance > 0:
                score = (obs - exp) / math.sqrt(variance)
            else:
                score = 0.0
            scores[digit] = score
        return scores
    
    def _calculate_confidence(
        self,
        p_value: float,
        mad: float,
        num_suspicious: int
    ) -> float:
        """Calculate overall confidence in anomaly detection"""
        # Weight multiple indicators
        p_score = 1.0 - p_value if p_value < self.significance_level else 0.0
        mad_score = min(mad / self.suspicious_threshold, 1.0) if mad > self.suspicious_threshold else 0.0
        digit_score = min(num_suspicious / 5.0, 1.0)
        
        # Weighted average
        confidence = (0.5 * p_score + 0.3 * mad_score + 0.2 * digit_score)
        return min(confidence, 1.0)
    
    def analyze_multiple_datasets(
        self,
        datasets: Dict[str, List[float]]
    ) -> Dict[str, BenfordsAnalysisResult]:
        """Analyze multiple datasets for comparison"""
        results = {}
        for name, numbers in datasets.items():
            results[name] = self.analyze(numbers, dataset_name=name)
        return results
    
    def generate_report(self, result: BenfordsAnalysisResult) -> str:
        """Generate human-readable analysis report"""
        report = []
        report.append(f"=== Benford's Law Analysis: {result.dataset_name} ===\n")
        report.append(f"Total Numbers: {result.total_numbers}")
        report.append(f"Valid Numbers: {result.valid_numbers}\n")
        
        report.append("First Digit Distribution:")
        for digit in sorted(result.expected_distribution.keys()):
            obs = result.observed_distribution.get(digit, 0.0)
            exp = result.expected_distribution[digit]
            dev = result.deviation_scores[digit]
            marker = " ⚠️" if digit in result.suspicious_digits else ""
            report.append(
                f"  {digit}: {obs*100:5.2f}% (expected: {exp*100:5.2f}%, "
                f"deviation: {dev:+.2f}σ){marker}"
            )
        
        report.append(f"\nChi-Square Test:")
        report.append(f"  Statistic: {result.chi_square_statistic:.4f}")
        report.append(f"  P-value: {result.chi_square_p_value:.4f}")
        
        report.append(f"\nDeviation Metrics:")
        report.append(f"  MAD: {result.mean_absolute_deviation:.4f}")
        report.append(f"  KL Divergence: {result.kullback_leibler_divergence:.4f}")
        report.append(f"  KS Statistic: {result.kolmogorov_smirnov_statistic:.4f}")
        
        report.append(f"\n⚡ VERDICT:")
        if result.is_suspicious:
            report.append(f"  🚨 SUSPICIOUS - Confidence: {result.confidence_level*100:.1f}%")
            report.append(f"  Anomalous digits: {', '.join(map(str, result.suspicious_digits))}")
        else:
            report.append(f"  ✓ NORMAL - Conforms to Benford's Law")
        
        return "\n".join(report)

