"""
Quantitative Forensic Analyzer - Advanced Financial Fraud Detection
Implements research-validated quantitative methods for fraud detection.

Research Foundation:
- Benford's Law: Hill (1995) "A Statistical Derivation of the Significant-Digit Law"
- Beneish M-Score: Beneish (1999) "The Detection of Earnings Manipulation"
- Altman Z-Score: Altman (1968) "Financial Ratios, Discriminant Analysis and Corporate Bankruptcy"
- Piotroski F-Score: Piotroski (2000) "Value Investing: The Use of Historical Financial Statement"
"""

import asyncio
import numpy as np
import scipy.stats as stats
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import math
from collections import Counter

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel
)

logger = logging.getLogger(__name__)


class FraudClassification(Enum):
    """Fraud classification types."""
    HIGH_PROBABILITY_FRAUD = "HIGH_PROBABILITY_FRAUD"
    MODERATE_FRAUD_INDICATORS = "MODERATE_FRAUD_INDICATORS"
    LOW_FRAUD_RISK = "LOW_FRAUD_RISK"
    INCONCLUSIVE = "INCONCLUSIVE"


class FinancialHealthStatus(Enum):
    """Financial health status classifications."""
    DISTRESS_ZONE = "DISTRESS_ZONE"  # Z-Score < 1.81
    GREY_ZONE = "GREY_ZONE"  # Z-Score 1.81-2.99
    SAFE_ZONE = "SAFE_ZONE"  # Z-Score > 2.99
    BANKRUPTCY_LIKELY = "BANKRUPTCY_LIKELY"  # Z-Score < 1.23


@dataclass
class BenfordAnalysis:
    """Benford's Law analysis results."""
    first_digit_distribution: Dict[int, float]
    expected_distribution: Dict[int, float]
    mad_statistic: float  # Mean Absolute Deviation
    chi_square_statistic: float
    chi_square_p_value: float
    critical_value_exceeded: bool
    degrees_of_freedom: int
    conformance_level: str  # ACCEPTABLE, QUESTIONABLE, NON_CONFORMANT
    suspicious_digits: List[int]
    interpretation: str


@dataclass
class BeneishMScore:
    """Beneish M-Score components and result."""
    dsri: float  # Days Sales in Receivables Index
    gmi: float   # Gross Margin Index
    aqi: float   # Asset Quality Index
    sgi: float   # Sales Growth Index
    depi: float  # Depreciation Index
    sgai: float  # SG&A Index
    tata: float  # Total Accruals to Total Assets
    lvgi: float  # Leverage Index
    m_score: float
    threshold: float
    manipulation_indicated: bool
    manipulation_probability: float
    component_flags: Dict[str, bool]
    interpretation: str


@dataclass
class AltmanZScore:
    """Altman Z-Score bankruptcy prediction."""
    working_capital_to_assets: float  # X1
    retained_earnings_to_assets: float  # X2
    ebit_to_assets: float  # X3
    market_value_equity_to_liabilities: float  # X4
    sales_to_assets: float  # X5
    z_score: float
    financial_health: FinancialHealthStatus
    bankruptcy_probability: float
    interpretation: str


@dataclass
class PiotroskiFScore:
    """Piotroski F-Score financial strength."""
    profitability_score: int  # 0-4
    leverage_liquidity_score: int  # 0-3
    operating_efficiency_score: int  # 0-2
    f_score: int  # 0-9
    financial_strength: str  # STRONG, MODERATE, WEAK
    components: Dict[str, bool]
    interpretation: str


@dataclass
class ComprehensiveForensicScore:
    """Complete quantitative forensic analysis."""
    analysis_timestamp: str
    company_cik: str
    company_name: str
    period: str
    
    # Component analyses
    benford_analysis: BenfordAnalysis
    beneish_m_score: BeneishMScore
    altman_z_score: AltmanZScore
    piotroski_f_score: PiotroskiFScore
    
    # Combined assessment
    fraud_classification: FraudClassification
    fraud_probability: float  # 0-1
    financial_distress_probability: float  # 0-1
    overall_risk_score: float  # 0-100
    
    # Recommendations
    red_flags: List[str]
    recommended_actions: List[str]
    forensic_priority: int  # 1-10
    
    # Evidence
    evidence_hash: str


class QuantitativeForensicAnalyzer:
    """
    Advanced quantitative forensic analyzer.
    
    Implements:
    - Benford's Law (Hill, 1995)
    - Beneish M-Score (Beneish, 1999)
    - Altman Z-Score (Altman, 1968)
    - Piotroski F-Score (Piotroski, 2000)
    """
    
    def __init__(self):
        """Initialize quantitative forensic analyzer."""
        self.hash_chain = ForensicHashChain("quantitative_forensic_analyzer")
        
        # Benford's Law expected first digit distribution
        self.benford_expected = {
            1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097, 5: 0.079,
            6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
        }
        
        # Critical values for chi-square test (8 df, various α)
        self.chi_square_critical = {
            0.05: 15.507,  # α = 0.05
            0.01: 20.090,  # α = 0.01
            0.001: 26.125  # α = 0.001
        }
        
        # Beneish M-Score threshold
        self.beneish_threshold = -2.22
        
        # Altman Z-Score thresholds
        self.altman_thresholds = {
            'bankruptcy': 1.23,
            'distress': 1.81,
            'grey_lower': 1.81,
            'grey_upper': 2.99,
            'safe': 2.99
        }
        
        logger.info("QuantitativeForensicAnalyzer initialized")
    
    async def comprehensive_fraud_scoring(
        self,
        financial_data: Dict[str, Any],
        prior_financial_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ComprehensiveForensicScore:
        """
        Comprehensive quantitative fraud scoring.
        
        Args:
            financial_data: Current period financial data
            prior_financial_data: Prior period financial data
            metadata: Optional metadata (company, period, etc.)
            
        Returns:
            Complete forensic analysis
        """
        logger.info("Starting comprehensive fraud scoring...")
        
        metadata = metadata or {}
        company_cik = metadata.get('cik', 'UNKNOWN')
        company_name = metadata.get('company_name', 'UNKNOWN')
        period = metadata.get('period', 'UNKNOWN')
        
        # 1. Benford's Law Analysis
        logger.info("Analyzing Benford's Law conformance...")
        benford = await self._benford_analysis(financial_data)
        
        # 2. Beneish M-Score
        logger.info("Calculating Beneish M-Score...")
        beneish = await self._beneish_m_score_analysis(
            financial_data,
            prior_financial_data
        )
        
        # 3. Altman Z-Score
        logger.info("Computing Altman Z-Score...")
        altman = await self._altman_z_score_analysis(financial_data)
        
        # 4. Piotroski F-Score
        logger.info("Evaluating Piotroski F-Score...")
        piotroski = await self._piotroski_f_score_analysis(
            financial_data,
            prior_financial_data
        )
        
        # 5. Combined fraud classification
        fraud_class, fraud_prob = self._classify_fraud_type(
            benford,
            beneish,
            altman,
            piotroski
        )
        
        # 6. Financial distress probability
        distress_prob = self._calculate_distress_probability(altman, piotroski)
        
        # 7. Overall risk score
        risk_score = self._calculate_overall_risk_score(
            benford,
            beneish,
            altman,
            piotroski,
            fraud_prob,
            distress_prob
        )
        
        # 8. Identify red flags
        red_flags = self._identify_red_flags(benford, beneish, altman, piotroski)
        
        # 9. Generate recommendations
        recommendations = self._generate_recommendations(
            fraud_class,
            benford,
            beneish,
            altman,
            piotroski
        )
        
        # 10. Calculate forensic priority
        priority = self._calculate_forensic_priority(
            fraud_prob,
            distress_prob,
            risk_score
        )
        
        # Create comprehensive result
        result = ComprehensiveForensicScore(
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            company_cik=company_cik,
            company_name=company_name,
            period=period,
            benford_analysis=benford,
            beneish_m_score=beneish,
            altman_z_score=altman,
            piotroski_f_score=piotroski,
            fraud_classification=fraud_class,
            fraud_probability=fraud_prob,
            financial_distress_probability=distress_prob,
            overall_risk_score=risk_score,
            red_flags=red_flags,
            recommended_actions=recommendations,
            forensic_priority=priority,
            evidence_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
        )
        
        # Log to hash chain
        await self.hash_chain.add_evidence(
            data={
                "action": "comprehensive_fraud_scoring",
                "company_cik": company_cik,
                "period": period,
                "fraud_probability": fraud_prob,
                "fraud_classification": fraud_class.value,
                "m_score": beneish.m_score,
                "z_score": altman.z_score,
                "f_score": piotroski.f_score,
                "risk_score": risk_score,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.CRITICAL
        )
        
        logger.info(
            f"Comprehensive scoring complete: Fraud={fraud_prob:.2%}, "
            f"M-Score={beneish.m_score:.3f}, Z-Score={altman.z_score:.3f}, "
            f"F-Score={piotroski.f_score}, Risk={risk_score:.1f}"
        )
        
        return result
    
    async def _benford_analysis(
        self,
        financial_data: Dict[str, Any]
    ) -> BenfordAnalysis:
        """
        Perform Benford's Law analysis.
        Hill (1995) - Statistical derivation of significant-digit law.
        """
        # Extract financial figures
        figures = self._extract_financial_figures(financial_data)
        
        if len(figures) < 20:
            # Insufficient data for Benford analysis
            return BenfordAnalysis(
                first_digit_distribution={},
                expected_distribution=self.benford_expected,
                mad_statistic=0.0,
                chi_square_statistic=0.0,
                chi_square_p_value=1.0,
                critical_value_exceeded=False,
                degrees_of_freedom=8,
                conformance_level="INCONCLUSIVE",
                suspicious_digits=[],
                interpretation="Insufficient data for Benford's Law analysis (minimum 20 observations required)"
            )
        
        # Calculate first digit distribution
        first_digit_dist = self._calculate_first_digit_distribution(figures)
        
        # Calculate MAD (Mean Absolute Deviation)
        mad = self._calculate_mad_statistic(first_digit_dist, self.benford_expected)
        
        # Chi-square test
        chi_square, p_value = self._benford_chi_square(first_digit_dist, len(figures))
        
        # Determine conformance
        critical_exceeded = chi_square > self.chi_square_critical[0.05]
        
        if mad < 0.006:
            conformance = "ACCEPTABLE"
        elif mad < 0.012:
            conformance = "QUESTIONABLE"
        else:
            conformance = "NON_CONFORMANT"
        
        # Identify suspicious digits (largest deviations)
        suspicious = self._identify_suspicious_digits(
            first_digit_dist,
            self.benford_expected
        )
        
        # Interpretation
        interpretation = self._interpret_benford_results(
            mad,
            chi_square,
            p_value,
            conformance,
            suspicious
        )
        
        return BenfordAnalysis(
            first_digit_distribution=first_digit_dist,
            expected_distribution=self.benford_expected,
            mad_statistic=mad,
            chi_square_statistic=chi_square,
            chi_square_p_value=p_value,
            critical_value_exceeded=critical_exceeded,
            degrees_of_freedom=8,
            conformance_level=conformance,
            suspicious_digits=suspicious,
            interpretation=interpretation
        )
    
    def _extract_financial_figures(
        self,
        financial_data: Dict[str, Any]
    ) -> List[float]:
        """Extract relevant financial figures for Benford analysis."""
        figures = []
        
        # Revenue-related
        for key in ['revenue', 'sales', 'gross_revenue']:
            if key in financial_data and financial_data[key] > 0:
                figures.append(float(financial_data[key]))
        
        # Expense-related
        for key in ['cogs', 'operating_expenses', 'sga', 'rd_expenses']:
            if key in financial_data and financial_data[key] > 0:
                figures.append(float(financial_data[key]))
        
        # Asset-related
        for key in ['total_assets', 'current_assets', 'cash', 'receivables', 
                    'inventory', 'ppe', 'intangible_assets']:
            if key in financial_data and financial_data[key] > 0:
                figures.append(float(financial_data[key]))
        
        # Liability-related
        for key in ['total_liabilities', 'current_liabilities', 'long_term_debt']:
            if key in financial_data and financial_data[key] > 0:
                figures.append(float(financial_data[key]))
        
        # Income-related
        for key in ['operating_income', 'net_income', 'ebitda']:
            if key in financial_data and abs(financial_data[key]) > 0:
                figures.append(abs(float(financial_data[key])))
        
        return figures
    
    def _calculate_first_digit_distribution(
        self,
        figures: List[float]
    ) -> Dict[int, float]:
        """Calculate observed first digit distribution."""
        first_digits = []
        
        for figure in figures:
            if figure > 0:
                # Get first digit
                first_digit = int(str(abs(int(figure)))[0])
                if 1 <= first_digit <= 9:
                    first_digits.append(first_digit)
        
        # Count frequencies
        digit_counts = Counter(first_digits)
        total = len(first_digits)
        
        # Calculate proportions
        distribution = {}
        for digit in range(1, 10):
            count = digit_counts.get(digit, 0)
            distribution[digit] = count / total if total > 0 else 0.0
        
        return distribution
    
    def _calculate_mad_statistic(
        self,
        observed: Dict[int, float],
        expected: Dict[int, float]
    ) -> float:
        """
        Calculate Mean Absolute Deviation (MAD).
        MAD = Σ|observed - expected| / n
        
        Nigrini (2012) guidelines:
        - MAD < 0.006: Close conformity
        - MAD 0.006-0.012: Acceptable conformity
        - MAD 0.012-0.015: Marginally acceptable
        - MAD > 0.015: Non-conformity
        """
        deviations = []
        for digit in range(1, 10):
            obs = observed.get(digit, 0.0)
            exp = expected.get(digit, 0.0)
            deviations.append(abs(obs - exp))
        
        mad = sum(deviations) / len(deviations)
        return mad
    
    def _benford_chi_square(
        self,
        observed_dist: Dict[int, float],
        sample_size: int
    ) -> Tuple[float, float]:
        """
        Perform chi-square goodness-of-fit test.
        
        H0: Data conforms to Benford's Law
        H1: Data does not conform to Benford's Law
        
        Returns:
            (chi_square_statistic, p_value)
        """
        chi_square = 0.0
        
        for digit in range(1, 10):
            observed = observed_dist.get(digit, 0.0) * sample_size
            expected = self.benford_expected[digit] * sample_size
            
            if expected > 0:
                chi_square += ((observed - expected) ** 2) / expected
        
        # Calculate p-value (8 degrees of freedom)
        p_value = 1 - stats.chi2.cdf(chi_square, df=8)
        
        return chi_square, p_value
    
    def _identify_suspicious_digits(
        self,
        observed: Dict[int, float],
        expected: Dict[int, float]
    ) -> List[int]:
        """Identify digits with largest deviations from expected."""
        deviations = []
        
        for digit in range(1, 10):
            obs = observed.get(digit, 0.0)
            exp = expected.get(digit, 0.0)
            deviation = abs(obs - exp)
            deviations.append((digit, deviation))
        
        # Sort by deviation, return top 3
        deviations.sort(key=lambda x: x[1], reverse=True)
        suspicious = [d[0] for d in deviations[:3] if d[1] > 0.02]  # >2% deviation
        
        return suspicious
    
    def _interpret_benford_results(
        self,
        mad: float,
        chi_square: float,
        p_value: float,
        conformance: str,
        suspicious: List[int]
    ) -> str:
        """Generate interpretation of Benford analysis."""
        if conformance == "ACCEPTABLE":
            return (
                f"Financial figures conform acceptably to Benford's Law "
                f"(MAD={mad:.4f}, χ²={chi_square:.2f}, p={p_value:.3f}). "
                f"No significant evidence of number manipulation."
            )
        elif conformance == "QUESTIONABLE":
            return (
                f"Marginal Benford conformance (MAD={mad:.4f}, χ²={chi_square:.2f}, p={p_value:.3f}). "
                f"Suspicious digits: {suspicious}. Warrants further investigation."
            )
        else:
            return (
                f"Significant deviation from Benford's Law (MAD={mad:.4f}, χ²={chi_square:.2f}, p={p_value:.3f}). "
                f"Suspicious digits: {suspicious}. Strong indicator of potential manipulation, "
                f"fabrication, or selective rounding."
            )
    
    async def _beneish_m_score_analysis(
        self,
        current: Dict[str, Any],
        prior: Optional[Dict[str, Any]]
    ) -> BeneishMScore:
        """
        Calculate Beneish M-Score.
        Beneish (1999) - Detection of earnings manipulation.
        
        M-Score > -2.22 indicates likely manipulation.
        """
        if not prior:
            # Cannot calculate without prior period
            return BeneishMScore(
                dsri=0, gmi=0, aqi=0, sgi=0, depi=0, sgai=0, tata=0, lvgi=0,
                m_score=0.0,
                threshold=self.beneish_threshold,
                manipulation_indicated=False,
                manipulation_probability=0.0,
                component_flags={},
                interpretation="Prior period data required for M-Score calculation"
            )
        
        # Calculate 8 components
        dsri = self._days_sales_receivables_index(current, prior)
        gmi = self._gross_margin_index(current, prior)
        aqi = self._asset_quality_index(current, prior)
        sgi = self._sales_growth_index(current, prior)
        depi = self._depreciation_index(current, prior)
        sgai = self._sga_expense_index(current, prior)
        tata = self._total_accruals_to_total_assets(current)
        lvgi = self._leverage_index(current, prior)
        
        # Calculate M-Score
        m_score = (
            -4.84 +
            0.92 * dsri +
            0.528 * gmi +
            0.404 * aqi +
            0.892 * sgi +
            0.115 * depi -
            0.172 * sgai +
            4.679 * tata -
            0.327 * lvgi
        )
        
        # Manipulation indicated if M-Score > -2.22
        manipulation = m_score > self.beneish_threshold
        
        # Calculate probability (logistic transformation)
        manipulation_prob = 1 / (1 + math.exp(-m_score))
        
        # Component flags (suspicious if outside normal ranges)
        component_flags = {
            'DSRI_elevated': dsri > 1.031,  # Receivables growing faster than sales
            'GMI_declining': gmi > 1.041,   # Gross margin deteriorating
            'AQI_elevated': aqi > 1.039,    # Asset quality deteriorating
            'SGI_elevated': sgi > 1.607,    # Aggressive growth
            'DEPI_elevated': depi > 1.001,  # Lower depreciation rates
            'SGAI_elevated': sgai > 1.001,  # SG&A expenses growing faster than sales
            'TATA_elevated': abs(tata) > 0.031,  # High accruals
            'LVGI_elevated': lvgi > 1.037   # Increasing leverage
        }
        
        # Interpretation
        interpretation = self._interpret_beneish_score(
            m_score,
            manipulation,
            manipulation_prob,
            component_flags
        )
        
        return BeneishMScore(
            dsri=dsri,
            gmi=gmi,
            aqi=aqi,
            sgi=sgi,
            depi=depi,
            sgai=sgai,
            tata=tata,
            lvgi=lvgi,
            m_score=m_score,
            threshold=self.beneish_threshold,
            manipulation_indicated=manipulation,
            manipulation_probability=manipulation_prob,
            component_flags=component_flags,
            interpretation=interpretation
        )
    
    def _days_sales_receivables_index(
        self,
        current: Dict[str, Any],
        prior: Dict[str, Any]
    ) -> float:
        """DSRI = (Receivables_t / Sales_t) / (Receivables_t-1 / Sales_t-1)"""
        try:
            current_dsr = current.get('receivables', 0) / current.get('revenue', 1)
            prior_dsr = prior.get('receivables', 0) / prior.get('revenue', 1)
            return current_dsr / prior_dsr if prior_dsr != 0 else 1.0
        except:
            return 1.0
    
    def _gross_margin_index(
        self,
        current: Dict[str, Any],
        prior: Dict[str, Any]
    ) -> float:
        """GMI = GrossMargin_t-1 / GrossMargin_t"""
        try:
            prior_gm = (prior.get('revenue', 0) - prior.get('cogs', 0)) / prior.get('revenue', 1)
            current_gm = (current.get('revenue', 0) - current.get('cogs', 0)) / current.get('revenue', 1)
            return prior_gm / current_gm if current_gm != 0 else 1.0
        except:
            return 1.0
    
    def _asset_quality_index(
        self,
        current: Dict[str, Any],
        prior: Dict[str, Any]
    ) -> float:
        """AQI = [1 - (CA_t + PPE_t) / TA_t] / [1 - (CA_t-1 + PPE_t-1) / TA_t-1]"""
        try:
            current_aq = 1 - (current.get('current_assets', 0) + current.get('ppe', 0)) / current.get('total_assets', 1)
            prior_aq = 1 - (prior.get('current_assets', 0) + prior.get('ppe', 0)) / prior.get('total_assets', 1)
            return current_aq / prior_aq if prior_aq != 0 else 1.0
        except:
            return 1.0
    
    def _sales_growth_index(
        self,
        current: Dict[str, Any],
        prior: Dict[str, Any]
    ) -> float:
        """SGI = Sales_t / Sales_t-1"""
        try:
            return current.get('revenue', 0) / prior.get('revenue', 1) if prior.get('revenue', 1) != 0 else 1.0
        except:
            return 1.0
    
    def _depreciation_index(
        self,
        current: Dict[str, Any],
        prior: Dict[str, Any]
    ) -> float:
        """DEPI = (Depr_t-1 / (Depr_t-1 + PPE_t-1)) / (Depr_t / (Depr_t + PPE_t))"""
        try:
            prior_rate = prior.get('depreciation', 0) / (prior.get('depreciation', 0) + prior.get('ppe', 1))
            current_rate = current.get('depreciation', 0) / (current.get('depreciation', 0) + current.get('ppe', 1))
            return prior_rate / current_rate if current_rate != 0 else 1.0
        except:
            return 1.0
    
    def _sga_expense_index(
        self,
        current: Dict[str, Any],
        prior: Dict[str, Any]
    ) -> float:
        """SGAI = (SGA_t / Sales_t) / (SGA_t-1 / Sales_t-1)"""
        try:
            current_sga_ratio = current.get('sga', 0) / current.get('revenue', 1)
            prior_sga_ratio = prior.get('sga', 0) / prior.get('revenue', 1)
            return current_sga_ratio / prior_sga_ratio if prior_sga_ratio != 0 else 1.0
        except:
            return 1.0
    
    def _total_accruals_to_total_assets(
        self,
        current: Dict[str, Any]
    ) -> float:
        """TATA = (Income - CFO) / Total Assets"""
        try:
            accruals = current.get('net_income', 0) - current.get('operating_cash_flow', 0)
            return accruals / current.get('total_assets', 1)
        except:
            return 0.0
    
    def _leverage_index(
        self,
        current: Dict[str, Any],
        prior: Dict[str, Any]
    ) -> float:
        """LVGI = Leverage_t / Leverage_t-1"""
        try:
            current_lev = current.get('total_liabilities', 0) / current.get('total_assets', 1)
            prior_lev = prior.get('total_liabilities', 0) / prior.get('total_assets', 1)
            return current_lev / prior_lev if prior_lev != 0 else 1.0
        except:
            return 1.0
    
    def _interpret_beneish_score(
        self,
        m_score: float,
        manipulation: bool,
        probability: float,
        flags: Dict[str, bool]
    ) -> str:
        """Interpret Beneish M-Score."""
        flagged_components = [k for k, v in flags.items() if v]
        
        if manipulation:
            return (
                f"M-Score of {m_score:.3f} exceeds threshold of {self.beneish_threshold} "
                f"(probability: {probability:.1%}). Earnings manipulation likely. "
                f"Suspicious components: {', '.join(flagged_components) if flagged_components else 'None'}. "
                f"Beneish (1999) showed 76% accuracy in detecting manipulators."
            )
        else:
            return (
                f"M-Score of {m_score:.3f} below threshold of {self.beneish_threshold} "
                f"(probability: {probability:.1%}). No strong indication of earnings manipulation. "
                f"{'Some components elevated: ' + ', '.join(flagged_components) if flagged_components else 'All components within normal ranges'}."
            )
    
    async def _altman_z_score_analysis(
        self,
        financial_data: Dict[str, Any]
    ) -> AltmanZScore:
        """
        Calculate Altman Z-Score for bankruptcy prediction.
        Altman (1968) - Financial ratios and corporate bankruptcy.
        
        Z-Score zones:
        - Z < 1.81: Distress zone (high bankruptcy risk)
        - 1.81 < Z < 2.99: Grey zone (moderate risk)
        - Z > 2.99: Safe zone (low risk)
        """
        try:
            # Extract data
            working_capital = financial_data.get('current_assets', 0) - financial_data.get('current_liabilities', 0)
            total_assets = financial_data.get('total_assets', 1)
            retained_earnings = financial_data.get('retained_earnings', 0)
            ebit = financial_data.get('ebit', financial_data.get('operating_income', 0))
            market_value_equity = financial_data.get('market_cap', financial_data.get('total_equity', 0))
            total_liabilities = financial_data.get('total_liabilities', 0)
            sales = financial_data.get('revenue', 0)
            
            # Calculate 5 components
            x1 = working_capital / total_assets
            x2 = retained_earnings / total_assets
            x3 = ebit / total_assets
            x4 = market_value_equity / total_liabilities if total_liabilities != 0 else 0
            x5 = sales / total_assets
            
            # Calculate Z-Score (original model for manufacturers)
            z_score = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
            
            # Determine financial health
            if z_score < self.altman_thresholds['bankruptcy']:
                health = FinancialHealthStatus.BANKRUPTCY_LIKELY
            elif z_score < self.altman_thresholds['distress']:
                health = FinancialHealthStatus.DISTRESS_ZONE
            elif z_score < self.altman_thresholds['safe']:
                health = FinancialHealthStatus.GREY_ZONE
            else:
                health = FinancialHealthStatus.SAFE_ZONE
            
            # Estimate bankruptcy probability (simplified)
            if z_score > 2.99:
                bankruptcy_prob = 0.05  # <5%
            elif z_score > 1.81:
                bankruptcy_prob = 0.25  # ~25%
            else:
                bankruptcy_prob = 0.80  # ~80%
            
            # Interpretation
            interpretation = (
                f"Altman Z-Score of {z_score:.3f} indicates {health.value}. "
                f"Bankruptcy probability: ~{bankruptcy_prob:.0%}. "
                f"Components: WC/TA={x1:.3f}, RE/TA={x2:.3f}, EBIT/TA={x3:.3f}, "
                f"MVE/TL={x4:.3f}, Sales/TA={x5:.3f}"
            )
            
        except Exception as e:
            logger.warning(f"Error calculating Altman Z-Score: {e}")
            x1 = x2 = x3 = x4 = x5 = 0.0
            z_score = 0.0
            health = FinancialHealthStatus.GREY_ZONE
            bankruptcy_prob = 0.5
            interpretation = f"Unable to calculate Z-Score: {str(e)}"
        
        return AltmanZScore(
            working_capital_to_assets=x1,
            retained_earnings_to_assets=x2,
            ebit_to_assets=x3,
            market_value_equity_to_liabilities=x4,
            sales_to_assets=x5,
            z_score=z_score,
            financial_health=health,
            bankruptcy_probability=bankruptcy_prob,
            interpretation=interpretation
        )
    
    async def _piotroski_f_score_analysis(
        self,
        current: Dict[str, Any],
        prior: Optional[Dict[str, Any]]
    ) -> PiotroskiFScore:
        """
        Calculate Piotroski F-Score for financial strength.
        Piotroski (2000) - Value investing using historical financials.
        
        F-Score ranges 0-9:
        - 8-9: Strong
        - 5-7: Moderate
        - 0-4: Weak
        """
        components = {}
        
        # Profitability (4 points)
        components['ROA_positive'] = current.get('net_income', 0) > 0
        
        if prior:
            components['CFO_positive'] = current.get('operating_cash_flow', 0) > 0
            prior_roa = prior.get('net_income', 0) / prior.get('total_assets', 1)
            current_roa = current.get('net_income', 0) / current.get('total_assets', 1)
            components['ROA_increasing'] = current_roa > prior_roa
            components['quality_earnings'] = current.get('operating_cash_flow', 0) > current.get('net_income', 0)
        else:
            components['CFO_positive'] = False
            components['ROA_increasing'] = False
            components['quality_earnings'] = False
        
        profitability = sum([
            components['ROA_positive'],
            components['CFO_positive'],
            components['ROA_increasing'],
            components['quality_earnings']
        ])
        
        # Leverage, Liquidity, Source of Funds (3 points)
        if prior:
            components['leverage_decreasing'] = (
                current.get('total_liabilities', 0) / current.get('total_assets', 1) <
                prior.get('total_liabilities', 0) / prior.get('total_assets', 1)
            )
            components['liquidity_increasing'] = (
                current.get('current_assets', 0) / current.get('current_liabilities', 1) >
                prior.get('current_assets', 0) / prior.get('current_liabilities', 1)
            )
            components['no_new_shares'] = current.get('shares_outstanding', 0) <= prior.get('shares_outstanding', 0)
        else:
            components['leverage_decreasing'] = False
            components['liquidity_increasing'] = False
            components['no_new_shares'] = False
        
        leverage_liquidity = sum([
            components['leverage_decreasing'],
            components['liquidity_increasing'],
            components['no_new_shares']
        ])
        
        # Operating Efficiency (2 points)
        if prior:
            current_gm = (current.get('revenue', 0) - current.get('cogs', 0)) / current.get('revenue', 1)
            prior_gm = (prior.get('revenue', 0) - prior.get('cogs', 0)) / prior.get('revenue', 1)
            components['margin_improving'] = current_gm > prior_gm
            
            current_turnover = current.get('revenue', 0) / current.get('total_assets', 1)
            prior_turnover = prior.get('revenue', 0) / prior.get('total_assets', 1)
            components['turnover_improving'] = current_turnover > prior_turnover
        else:
            components['margin_improving'] = False
            components['turnover_improving'] = False
        
        operating_efficiency = sum([
            components['margin_improving'],
            components['turnover_improving']
        ])
        
        # Total F-Score
        f_score = profitability + leverage_liquidity + operating_efficiency
        
        # Financial strength classification
        if f_score >= 8:
            strength = "STRONG"
        elif f_score >= 5:
            strength = "MODERATE"
        else:
            strength = "WEAK"
        
        # Interpretation
        interpretation = (
            f"Piotroski F-Score of {f_score}/9 indicates {strength} financial strength. "
            f"Profitability: {profitability}/4, Leverage/Liquidity: {leverage_liquidity}/3, "
            f"Operating Efficiency: {operating_efficiency}/2. "
            f"{'Strong fundamentals for value investment' if f_score >= 7 else 'Weak fundamentals' if f_score <= 3 else 'Mixed fundamentals'}."
        )
        
        return PiotroskiFScore(
            profitability_score=profitability,
            leverage_liquidity_score=leverage_liquidity,
            operating_efficiency_score=operating_efficiency,
            f_score=f_score,
            financial_strength=strength,
            components=components,
            interpretation=interpretation
        )
    
    def _classify_fraud_type(
        self,
        benford: BenfordAnalysis,
        beneish: BeneishMScore,
        altman: AltmanZScore,
        piotroski: PiotroskiFScore
    ) -> Tuple[FraudClassification, float]:
        """Classify fraud probability based on all indicators."""
        # Start with base probability
        fraud_prob = 0.0
        
        # Benford's Law contribution (0-0.25)
        if benford.conformance_level == "NON_CONFORMANT":
            fraud_prob += 0.25
        elif benford.conformance_level == "QUESTIONABLE":
            fraud_prob += 0.15
        
        # Beneish M-Score contribution (0-0.40)
        fraud_prob += beneish.manipulation_probability * 0.40
        
        # Altman Z-Score (financial distress can correlate with fraud) (0-0.20)
        if altman.financial_health == FinancialHealthStatus.DISTRESS_ZONE:
            fraud_prob += 0.15
        elif altman.financial_health == FinancialHealthStatus.BANKRUPTCY_LIKELY:
            fraud_prob += 0.20
        
        # Piotroski F-Score (weak fundamentals) (0-0.15)
        if piotroski.f_score <= 3:
            fraud_prob += 0.15
        elif piotroski.f_score <= 5:
            fraud_prob += 0.10
        
        # Classify
        if fraud_prob >= 0.70:
            classification = FraudClassification.HIGH_PROBABILITY_FRAUD
        elif fraud_prob >= 0.50:
            classification = FraudClassification.MODERATE_FRAUD_INDICATORS
        elif fraud_prob >= 0.30:
            classification = FraudClassification.LOW_FRAUD_RISK
        else:
            classification = FraudClassification.INCONCLUSIVE
        
        return classification, fraud_prob
    
    def _calculate_distress_probability(
        self,
        altman: AltmanZScore,
        piotroski: PiotroskiFScore
    ) -> float:
        """Calculate financial distress probability."""
        # Base on Altman Z-Score
        distress_prob = altman.bankruptcy_probability
        
        # Adjust based on Piotroski F-Score
        if piotroski.f_score <= 3:
            distress_prob = min(distress_prob * 1.3, 1.0)
        elif piotroski.f_score >= 7:
            distress_prob = max(distress_prob * 0.7, 0.0)
        
        return distress_prob
    
    def _calculate_overall_risk_score(
        self,
        benford: BenfordAnalysis,
        beneish: BeneishMScore,
        altman: AltmanZScore,
        piotroski: PiotroskiFScore,
        fraud_prob: float,
        distress_prob: float
    ) -> float:
        """Calculate overall risk score (0-100)."""
        risk = 0.0
        
        # Fraud risk component (0-50)
        risk += fraud_prob * 50
        
        # Financial distress component (0-30)
        risk += distress_prob * 30
        
        # Benford anomaly component (0-10)
        if benford.conformance_level == "NON_CONFORMANT":
            risk += 10
        elif benford.conformance_level == "QUESTIONABLE":
            risk += 5
        
        # Component flags (0-10)
        suspicious_flags = sum(beneish.component_flags.values())
        risk += min(suspicious_flags, 10)
        
        return min(risk, 100.0)
    
    def _identify_red_flags(
        self,
        benford: BenfordAnalysis,
        beneish: BeneishMScore,
        altman: AltmanZScore,
        piotroski: PiotroskiFScore
    ) -> List[str]:
        """Identify red flags from all analyses."""
        red_flags = []
        
        # Benford red flags
        if benford.conformance_level == "NON_CONFORMANT":
            red_flags.append(
                f"🚨 Benford's Law violation (MAD={benford.mad_statistic:.4f}) - "
                f"Possible number manipulation"
            )
        
        # Beneish red flags
        if beneish.manipulation_indicated:
            red_flags.append(
                f"🚨 Beneish M-Score ({beneish.m_score:.3f}) exceeds threshold - "
                f"Earnings manipulation likely ({beneish.manipulation_probability:.0%} probability)"
            )
        
        flagged_components = [k for k, v in beneish.component_flags.items() if v]
        if len(flagged_components) >= 3:
            red_flags.append(
                f"⚠️ Multiple Beneish components flagged: {', '.join(flagged_components)}"
            )
        
        # Altman red flags
        if altman.financial_health == FinancialHealthStatus.BANKRUPTCY_LIKELY:
            red_flags.append(
                f"🚨 Altman Z-Score ({altman.z_score:.3f}) indicates high bankruptcy risk - "
                f"Potential going concern issue"
            )
        elif altman.financial_health == FinancialHealthStatus.DISTRESS_ZONE:
            red_flags.append(
                f"⚠️ Altman Z-Score ({altman.z_score:.3f}) in distress zone - "
                f"Financial stress detected"
            )
        
        # Piotroski red flags
        if piotroski.f_score <= 3:
            red_flags.append(
                f"⚠️ Low Piotroski F-Score ({piotroski.f_score}/9) - "
                f"Weak financial fundamentals"
            )
        
        return red_flags
    
    def _generate_recommendations(
        self,
        fraud_class: FraudClassification,
        benford: BenfordAnalysis,
        beneish: BeneishMScore,
        altman: AltmanZScore,
        piotroski: PiotroskiFScore
    ) -> List[str]:
        """Generate investigation recommendations."""
        recommendations = []
        
        if fraud_class == FraudClassification.HIGH_PROBABILITY_FRAUD:
            recommendations.append(
                "IMMEDIATE: Initiate comprehensive forensic investigation"
            )
            recommendations.append(
                "REQUIRED: Engage independent forensic accounting firm"
            )
        
        if benford.conformance_level == "NON_CONFORMANT":
            recommendations.append(
                "ACTION: Detailed testing of transaction populations for authenticity"
            )
            recommendations.append(
                f"ACTION: Investigate digits {benford.suspicious_digits} for manipulation"
            )
        
        if beneish.manipulation_indicated:
            recommendations.append(
                "ACTION: Review revenue recognition policies and timing"
            )
            recommendations.append(
                "ACTION: Examine working capital accounts and accruals"
            )
        
        if altman.financial_health in [FinancialHealthStatus.BANKRUPTCY_LIKELY, 
                                      FinancialHealthStatus.DISTRESS_ZONE]:
            recommendations.append(
                "ACTION: Assess going concern status and disclosure requirements"
            )
            recommendations.append(
                "ACTION: Review debt covenants and liquidity position"
            )
        
        recommendations.append(
            "ONGOING: Monitor subsequent periods for pattern persistence"
        )
        
        return recommendations
    
    def _calculate_forensic_priority(
        self,
        fraud_prob: float,
        distress_prob: float,
        risk_score: float
    ) -> int:
        """Calculate forensic investigation priority (1-10)."""
        priority = 0
        
        # Base on fraud probability
        priority += fraud_prob * 5
        
        # Add distress probability
        priority += distress_prob * 3
        
        # Add risk score component
        priority += (risk_score / 100) * 2
        
        return min(max(int(priority), 1), 10)
    
    async def verify_integrity(self) -> bool:
        """Verify hash chain integrity."""
        is_valid = await self.hash_chain.verify_chain()
        
        if not is_valid:
            logger.critical("Quantitative analyzer hash chain integrity violation!")
        
        return is_valid


# Backward compatibility exports
__all__ = [
    'QuantitativeForensicAnalyzer',
    'FraudClassification',
    'FinancialHealthStatus',
    'BenfordAnalysis',
    'BeneishMScore',
    'AltmanZScore',
    'PiotroskiFScore',
    'ComprehensiveForensicScore'
]

