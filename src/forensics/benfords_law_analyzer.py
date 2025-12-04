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
from datetime import datetime, timezone
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

    # ---------------------------------------------------------------------
    # Enhanced API wrappers (injected functions exposed as instance methods)
    # ---------------------------------------------------------------------
    def calculate_z_scores_enhanced(self, observed: Dict[int, float], expected: Dict[int, float], sample_size: int):
        """Instance wrapper for enhanced Z-score calculation.

        Delegates to module-level `calculate_z_scores_enhanced` injected by the
        enhancement script, exposing it via the class API for callers/tests.
        """
        # Defer import/name resolution until runtime to avoid circular refs
        return calculate_z_scores_enhanced(observed, expected, sample_size)

    def _calculate_z_scores(self, observed: Dict[int, float], expected: Dict[int, float], sample_size: int) -> Dict[int, Dict[str, float]]:
        """
        Compatibility helper returning dict-of-dicts for tests.

        Converts enhanced `ZScoreResult` objects to simple dictionaries with
        keys: 'z_score', 'p_value_approx', and 'anomaly_level'.
        """
        enhanced = calculate_z_scores_enhanced(observed, expected, sample_size)
        return {
            d: {
                "z_score": v.z_score,
                "p_value_approx": v.p_value_approx,
                "anomaly_level": v.anomaly_level,
            }
            for d, v in enhanced.items()
        }

    def calculate_fraud_probability(self, *args, **kwargs):
        """Flexible API for fraud probability scoring.

        Supports two call styles:
        1) Legacy/enhanced numeric API:
           (chi_sq_first, chi_sq_second, z_score_results, mad_first=0.0, mad_second=0.0)
           -> returns FraudProbabilityResult dataclass.

        2) Analysis-result API used by integration tests:
           (analysis_result) -> returns a simple dict with keys
           'fraud_probability' and 'risk_level' (plus components/weights).
        """
        # Case 2: single positional argument treated as an analysis result object
        if len(args) == 1 and not kwargs:
            analysis_result = args[0]
            components: Dict[str, float] = {}

            # Normalize chi-square components
            chi_sq_first = getattr(analysis_result, 'chi_squared_first', 0.0)
            chi_sq_second = getattr(analysis_result, 'chi_squared_second', 0.0)
            components["first_digit_chi_sq"] = min(1.0, chi_sq_first / 40.0)
            components["second_digit_chi_sq"] = min(1.0, chi_sq_second / 43.0)

            # Anomaly count component
            anomaly_count = len(getattr(analysis_result, 'anomalous_digits', []))
            components["anomaly_count"] = min(1.0, anomaly_count / 5.0)

            # Max Z-score component (expects dict-of-dicts as in tests)
            z_scores = getattr(analysis_result, 'z_scores', {}) or {}
            try:
                max_z = max((v.get('z_score', 0.0) for v in z_scores.values()), default=0.0)
            except AttributeError:
                # Fallback if enhanced objects were provided instead of dicts
                max_z = max((getattr(v, 'z_score', 0.0) for v in z_scores.values()), default=0.0)
            components["max_z_score"] = min(1.0, max_z / 5.0)

            weights = {
                "first_digit_chi_sq": 0.35,
                "second_digit_chi_sq": 0.25,
                "anomaly_count": 0.25,
                "max_z_score": 0.15,
            }

            fraud_probability = round(
                max(0.0, min(1.0, sum(components[k] * w for k, w in weights.items()))), 4
            )

            if fraud_probability >= 0.70:
                risk_level = "CRITICAL"
            elif fraud_probability >= 0.50:
                risk_level = "HIGH"
            elif fraud_probability >= 0.30:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            return {
                "fraud_probability": fraud_probability,
                "risk_level": risk_level,
                "component_scores": components,
                "weights_applied": weights,
            }

        # Case 1: numeric enhanced API passthrough
        chi_sq_first = args[0] if len(args) > 0 else kwargs.get('chi_sq_first', 0.0)
        chi_sq_second = args[1] if len(args) > 1 else kwargs.get('chi_sq_second', 0.0)
        z_score_results = args[2] if len(args) > 2 else kwargs.get('z_score_results', {})
        mad_first = args[3] if len(args) > 3 else kwargs.get('mad_first', 0.0)
        mad_second = args[4] if len(args) > 4 else kwargs.get('mad_second', 0.0)

        return calculate_fraud_probability_enhanced(
            chi_sq_first, chi_sq_second, z_score_results, mad_first, mad_second
        )


@dataclass
class MultiDatasetBenfordAnalysis:
    """Results from analyzing multiple datasets with Benford's Law."""
    dataset_results: Dict[str, BenfordsAnalysisResult]
    ensemble_fraud_score: float
    comparative_analysis: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def create_ensemble_fraud_score(results: Dict[str, BenfordsAnalysisResult]) -> float:
    """
    Create ensemble fraud score from multiple Benford's Law analyses.
    
    Args:
        results: Dictionary of dataset names to analysis results
        
    Returns:
        Ensemble fraud score (0.0 - 1.0)
    """
    if not results:
        return 0.0
    
    scores = []
    for result in results.values():
        # Weight by confidence level and suspiciousness
        if result.is_suspicious:
            score = result.confidence_level
        else:
            score = 1.0 - result.confidence_level
        scores.append(score)
    
    # Return average fraud score
    return sum(scores) / len(scores)




# =============================================================================
# ENHANCEMENT: Z-Score and Fraud Probability Scoring
# Injected by JLAW Remediation Patch v1.0.0
# Enhancement Protocol Compliance: P0 Feature Parity
# =============================================================================

from typing import Dict, Any
from dataclasses import dataclass, field
import math


@dataclass
class ZScoreResult:
    """Z-score analysis result for a single digit."""
    digit: int
    z_score: float
    p_value_approx: float
    anomaly_level: str  # NORMAL, LOW, MEDIUM, HIGH, CRITICAL
    observed_frequency: float
    expected_frequency: float


@dataclass
class FraudProbabilityResult:
    """Aggregate fraud probability assessment."""
    fraud_probability: float  # 0.0 to 1.0
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    component_scores: Dict[str, float] = field(default_factory=dict)
    weights_applied: Dict[str, float] = field(default_factory=dict)
    confidence_level: str = "STANDARD"


def calculate_z_scores_enhanced(
    observed: Dict[int, float],
    expected: Dict[int, float],
    sample_size: int
) -> Dict[int, ZScoreResult]:
    """
    Calculate Z-scores for each digit with continuity correction.
    
    Statistical Methodology:
    -----------------------
    Z = (|p_obs - p_exp| - 1/(2n)) / sqrt(p_exp * (1 - p_exp) / n)
    
    Where:
    - p_obs: Observed proportion for digit d
    - p_exp: Expected Benford proportion for digit d
    - n: Sample size
    - 1/(2n): Continuity correction (Yates correction)
    
    Anomaly Classification (Two-tailed):
    ------------------------------------
    |Z| ≤ 1.645: NORMAL (p ≥ 0.10)
    1.645 < |Z| ≤ 1.960: LOW (0.05 ≤ p < 0.10)
    1.960 < |Z| ≤ 2.576: MEDIUM (0.01 ≤ p < 0.05)
    2.576 < |Z| ≤ 3.291: HIGH (0.001 ≤ p < 0.01)
    |Z| > 3.291: CRITICAL (p < 0.001)
    
    Args:
        observed: Dict mapping digit -> observed proportion
        expected: Dict mapping digit -> expected Benford proportion
        sample_size: Total number of values analyzed
        
    Returns:
        Dict mapping digit -> ZScoreResult
    """
    results = {}
    
    for digit in expected.keys():
        p_obs = observed.get(digit, 0.0)
        p_exp = expected.get(digit, 0.0)
        
        if sample_size < 10 or p_exp <= 0 or p_exp >= 1:
            results[digit] = ZScoreResult(
                digit=digit,
                z_score=0.0,
                p_value_approx=1.0,
                anomaly_level="INSUFFICIENT_DATA",
                observed_frequency=p_obs,
                expected_frequency=p_exp
            )
            continue
        
        # Continuity correction
        continuity = 1 / (2 * sample_size)
        
        # Standard error
        std_error = math.sqrt(p_exp * (1 - p_exp) / sample_size)
        
        if std_error == 0:
            results[digit] = ZScoreResult(
                digit=digit,
                z_score=0.0,
                p_value_approx=1.0,
                anomaly_level="ZERO_VARIANCE",
                observed_frequency=p_obs,
                expected_frequency=p_exp
            )
            continue
        
        # Z-score with continuity correction
        z = max(0, (abs(p_obs - p_exp) - continuity) / std_error)
        
        # Classify anomaly
        if z > 3.291:
            level, p_approx = "CRITICAL", 0.001
        elif z > 2.576:
            level, p_approx = "HIGH", 0.01
        elif z > 1.960:
            level, p_approx = "MEDIUM", 0.05
        elif z > 1.645:
            level, p_approx = "LOW", 0.10
        else:
            level, p_approx = "NORMAL", 0.50
        
        results[digit] = ZScoreResult(
            digit=digit,
            z_score=round(z, 4),
            p_value_approx=p_approx,
            anomaly_level=level,
            observed_frequency=p_obs,
            expected_frequency=p_exp
        )
    
    return results


def calculate_fraud_probability_enhanced(
    chi_sq_first: float,
    chi_sq_second: float,
    z_score_results: Dict[int, ZScoreResult],
    mad_first: float = 0.0,
    mad_second: float = 0.0
) -> FraudProbabilityResult:
    """
    Calculate aggregate fraud probability from Benford's Law analysis.
    
    Scoring Algorithm:
    -----------------
    Weighted aggregation of normalized component scores:
    
    Component Weights:
    - First digit chi-squared: 30%
    - Second digit chi-squared: 20%
    - Critical/High Z-score count: 25%
    - Maximum Z-score: 15%
    - Mean Absolute Deviation (first): 10%
    
    Normalization:
    - Chi-squared: Normalized against 2x critical value (df=8: 40.17, df=9: 43.34)
    - Z-scores: Count of HIGH/CRITICAL anomalies, max 5
    - MAD: Normalized against 0.015 threshold (critical conformity)
    
    Risk Classification:
    -------------------
    0.00 - 0.25: LOW - Data conforms to Benford's Law
    0.25 - 0.50: MEDIUM - Some deviations, warrant monitoring
    0.50 - 0.75: HIGH - Significant anomalies, investigation recommended
    0.75 - 1.00: CRITICAL - Strong fraud indicators, escalate immediately
    """
    components = {}
    weights = {
        "chi_sq_first": 0.30,
        "chi_sq_second": 0.20,
        "anomaly_count": 0.25,
        "max_z_score": 0.15,
        "mad_first": 0.10
    }
    
    # Chi-squared first digit (df=8, critical=15.51, 2x=31.02)
    components["chi_sq_first"] = min(1.0, chi_sq_first / 40.0)
    
    # Chi-squared second digit (df=9, critical=16.92, 2x=33.84)
    components["chi_sq_second"] = min(1.0, chi_sq_second / 43.0)
    
    # Count HIGH/CRITICAL anomalies
    anomaly_count = sum(
        1 for r in z_score_results.values()
        if r.anomaly_level in ["HIGH", "CRITICAL"]
    )
    components["anomaly_count"] = min(1.0, anomaly_count / 5.0)
    
    # Maximum Z-score
    max_z = max((r.z_score for r in z_score_results.values()), default=0)
    components["max_z_score"] = min(1.0, max_z / 5.0)
    
    # MAD first digit (critical threshold 0.015)
    components["mad_first"] = min(1.0, mad_first / 0.025)
    
    # Weighted aggregation
    fraud_prob = sum(
        components.get(k, 0) * w
        for k, w in weights.items()
    )
    fraud_prob = round(max(0.0, min(1.0, fraud_prob)), 4)
    
    # Risk classification
    if fraud_prob >= 0.75:
        risk_level = "CRITICAL"
    elif fraud_prob >= 0.50:
        risk_level = "HIGH"
    elif fraud_prob >= 0.25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    return FraudProbabilityResult(
        fraud_probability=fraud_prob,
        risk_level=risk_level,
        component_scores={k: round(v, 4) for k, v in components.items()},
        weights_applied=weights,
        confidence_level="HIGH" if sum(1 for r in z_score_results.values() if r.anomaly_level != "INSUFFICIENT_DATA") >= 7 else "STANDARD"
    )


# Injected methods for BenfordsLawAnalyzer

    def _calculate_z_scores(
        self,
        observed: Dict[int, float],
        expected: Dict[int, float],
        sample_size: int
    ) -> Dict[int, Dict[str, float]]:
        """
        Calculate Z-scores for each digit comparing observed vs expected frequencies.
        
        Statistical Basis:
        -----------------
        Z = (|observed - expected| - 1/(2n)) / sqrt(expected * (1 - expected) / n)
        
        Where:
        - observed: Observed proportion for digit
        - expected: Expected Benford proportion
        - n: Sample size
        - 1/(2n): Continuity correction factor
        
        Threshold Classification (Two-tailed):
        -------------------------------------
        |Z| > 1.645: p < 0.10 (LOW anomaly)
        |Z| > 1.960: p < 0.05 (MEDIUM anomaly)
        |Z| > 2.576: p < 0.01 (HIGH anomaly)
        |Z| > 3.291: p < 0.001 (CRITICAL anomaly)
        
        Returns:
            Dict mapping digit -> {z_score, p_value_approx, anomaly_level}
        """
        import math
        
        results = {}
        
        for digit in observed.keys():
            obs = observed.get(digit, 0)
            exp = expected.get(digit, 0)
            
            if exp <= 0 or exp >= 1 or sample_size < 10:
                results[digit] = {
                    "z_score": 0.0,
                    "p_value_approx": 1.0,
                    "anomaly_level": "INSUFFICIENT_DATA"
                }
                continue
            
            # Continuity correction
            continuity_correction = 1 / (2 * sample_size)
            
            # Standard error
            std_error = math.sqrt(exp * (1 - exp) / sample_size)
            
            if std_error == 0:
                results[digit] = {
                    "z_score": 0.0,
                    "p_value_approx": 1.0,
                    "anomaly_level": "ZERO_VARIANCE"
                }
                continue
            
            # Z-score with continuity correction
            z_score = (abs(obs - exp) - continuity_correction) / std_error
            z_score = max(0, z_score)  # Cannot be negative after abs
            
            # Classify anomaly level
            if z_score > 3.291:
                anomaly_level = "CRITICAL"
                p_approx = 0.001
            elif z_score > 2.576:
                anomaly_level = "HIGH"
                p_approx = 0.01
            elif z_score > 1.960:
                anomaly_level = "MEDIUM"
                p_approx = 0.05
            elif z_score > 1.645:
                anomaly_level = "LOW"
                p_approx = 0.10
            else:
                anomaly_level = "NORMAL"
                p_approx = 0.50
            
            results[digit] = {
                "z_score": round(z_score, 4),
                "p_value_approx": p_approx,
                "anomaly_level": anomaly_level
            }
        
        return results

    def calculate_fraud_probability(
        self,
        analysis_result: 'BenfordsAnalysisResult'
    ) -> Dict[str, float]:
        """
        Calculate aggregate fraud probability score from Benford's Law analysis.
        
        Scoring Components (Weighted):
        -----------------------------
        - First digit chi-squared: 35% weight
        - Second digit chi-squared: 25% weight
        - Anomaly count score: 25% weight
        - Maximum Z-score: 15% weight
        
        Fraud Probability Interpretation:
        ---------------------------------
        0.00 - 0.30: LOW risk - Data appears natural
        0.30 - 0.50: MEDIUM risk - Some irregularities
        0.50 - 0.70: HIGH risk - Significant deviations
        0.70 - 1.00: CRITICAL risk - Strong fraud indicators
        
        Returns:
            Dict with fraud_probability (0-1), risk_level, component_scores
        """
        components = {}
        
        # Component 1: First digit chi-squared (normalized)
        # Chi-squared critical value for df=8, alpha=0.01 is 20.09
        chi_sq_first = getattr(analysis_result, 'chi_squared_first', 0)
        chi_sq_first_normalized = min(1.0, chi_sq_first / 40.0)  # 2x critical = max
        components["first_digit_chi_sq"] = chi_sq_first_normalized
        
        # Component 2: Second digit chi-squared (normalized)
        # Chi-squared critical value for df=9, alpha=0.01 is 21.67
        chi_sq_second = getattr(analysis_result, 'chi_squared_second', 0)
        chi_sq_second_normalized = min(1.0, chi_sq_second / 43.0)
        components["second_digit_chi_sq"] = chi_sq_second_normalized
        
        # Component 3: Anomaly count score
        # Based on number of digits flagged as anomalous
        anomaly_count = len(getattr(analysis_result, 'anomalous_digits', []))
        anomaly_score = min(1.0, anomaly_count / 5.0)  # 5+ anomalies = max
        components["anomaly_count"] = anomaly_score
        
        # Component 4: Maximum Z-score
        z_scores = getattr(analysis_result, 'z_scores', {})
        max_z = max((v.get('z_score', 0) for v in z_scores.values()), default=0)
        max_z_normalized = min(1.0, max_z / 5.0)  # Z=5 = max
        components["max_z_score"] = max_z_normalized
        
        # Weighted aggregation
        weights = {
            "first_digit_chi_sq": 0.35,
            "second_digit_chi_sq": 0.25,
            "anomaly_count": 0.25,
            "max_z_score": 0.15
        }
        
        fraud_probability = sum(
            components.get(k, 0) * w
            for k, w in weights.items()
        )
        fraud_probability = round(min(1.0, max(0.0, fraud_probability)), 4)
        
        # Risk level classification
        if fraud_probability >= 0.70:
            risk_level = "CRITICAL"
        elif fraud_probability >= 0.50:
            risk_level = "HIGH"
        elif fraud_probability >= 0.30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "fraud_probability": fraud_probability,
            "risk_level": risk_level,
            "component_scores": components,
            "weights_applied": weights
        }

