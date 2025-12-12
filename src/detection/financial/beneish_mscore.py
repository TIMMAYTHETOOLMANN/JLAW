"""
Beneish M-Score Calculator
==========================

Implements the complete 8-variable Beneish M-Score model for
earnings manipulation detection.

Academic Reference: Beneish, M.D. (1999) "The Detection of Earnings
Manipulation" Financial Analysts Journal

The model correctly identified 76% of manipulators with 17.5% false
positive rate. Cornell students used this model to identify Enron
as a manipulator in 1998 before Wall Street detection.

Thresholds:
- M-Score < -2.22: Unlikely manipulator
- -2.22 to -1.78: Gray zone (investigation required)
- M-Score > -1.78: Likely manipulator (enforcement referral)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ManipulationRisk(Enum):
    """M-Score risk classification."""
    UNLIKELY = "Unlikely Manipulator"
    GRAY_ZONE = "Gray Zone - Investigation Required"
    LIKELY = "Likely Manipulator - Enforcement Referral"


@dataclass
class MScoreVariables:
    """Individual M-Score component variables."""
    dsri: float  # Days Sales in Receivables Index
    gmi: float   # Gross Margin Index
    aqi: float   # Asset Quality Index
    sgi: float   # Sales Growth Index
    depi: float  # Depreciation Index
    sgai: float  # SG&A Index
    lvgi: float  # Leverage Index
    tata: float  # Total Accruals to Total Assets
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "DSRI": round(self.dsri, 4),
            "GMI": round(self.gmi, 4),
            "AQI": round(self.aqi, 4),
            "SGI": round(self.sgi, 4),
            "DEPI": round(self.depi, 4),
            "SGAI": round(self.sgai, 4),
            "LVGI": round(self.lvgi, 4),
            "TATA": round(self.tata, 4)
        }


@dataclass
class MScoreResult:
    """Complete M-Score calculation result."""
    m_score: float
    risk_level: ManipulationRisk
    variables: MScoreVariables
    threshold: float
    red_flags: List[str]
    interpretation: str
    
    # Individual variable flags
    dsri_flag: bool = False  # >1.0 indicates revenue inflation
    gmi_flag: bool = False   # >1.0 indicates margin deterioration
    aqi_flag: bool = False   # >1.0 indicates asset quality decline
    sgi_flag: bool = False   # High growth = manipulation incentive
    tata_flag: bool = False  # High accruals = earnings quality concern
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "m_score": round(self.m_score, 4),
            "risk_level": self.risk_level.value,
            "threshold": self.threshold,
            "is_above_threshold": self.m_score > self.threshold,
            "variables": self.variables.to_dict(),
            "red_flags": self.red_flags,
            "interpretation": self.interpretation,
            "variable_flags": {
                "dsri_revenue_inflation": self.dsri_flag,
                "gmi_margin_deterioration": self.gmi_flag,
                "aqi_asset_quality_decline": self.aqi_flag,
                "sgi_high_growth_incentive": self.sgi_flag,
                "tata_high_accruals": self.tata_flag
            }
        }


class BeneishMScoreCalculator:
    """
    Beneish M-Score Calculator for earnings manipulation detection.
    
    Formula:
    M = -4.84 + (0.92×DSRI) + (0.528×GMI) + (0.404×AQI) + (0.892×SGI) 
        + (0.115×DEPI) - (0.172×SGAI) + (4.679×TATA) - (0.327×LVGI)
    
    Variable Definitions:
    - DSRI: Days Sales in Receivables Index
    - GMI: Gross Margin Index
    - AQI: Asset Quality Index
    - SGI: Sales Growth Index
    - DEPI: Depreciation Index
    - SGAI: Sales, General & Administrative Index
    - LVGI: Leverage Index
    - TATA: Total Accruals to Total Assets
    """
    
    # Model coefficients (Beneish 1999)
    INTERCEPT = -4.84
    COEF_DSRI = 0.92
    COEF_GMI = 0.528
    COEF_AQI = 0.404
    COEF_SGI = 0.892
    COEF_DEPI = 0.115
    COEF_SGAI = -0.172
    COEF_TATA = 4.679
    COEF_LVGI = -0.327
    
    # Classification thresholds
    THRESHOLD_UNLIKELY = -2.22
    THRESHOLD_LIKELY = -1.78
    
    def calculate(
        self,
        current_year: Dict[str, float],
        prior_year: Dict[str, float]
    ) -> MScoreResult:
        """
        Calculate M-Score from financial data.
        
        Args:
            current_year: Current year financial metrics
            prior_year: Prior year financial metrics
            
        Required metrics in each dict:
        - receivables: Net accounts receivable
        - sales: Net sales/revenue
        - gross_margin: Gross profit margin (gross_profit / sales)
        - current_assets: Total current assets
        - ppe: Property, plant & equipment (net)
        - total_assets: Total assets
        - depreciation: Depreciation expense
        - sga: SG&A expenses
        - total_debt: Total debt (short + long term)
        - net_income: Net income
        - cfo: Cash flow from operations
        
        Returns:
            MScoreResult with complete analysis
        """
        # Calculate each variable
        dsri = self._calc_dsri(current_year, prior_year)
        gmi = self._calc_gmi(current_year, prior_year)
        aqi = self._calc_aqi(current_year, prior_year)
        sgi = self._calc_sgi(current_year, prior_year)
        depi = self._calc_depi(current_year, prior_year)
        sgai = self._calc_sgai(current_year, prior_year)
        lvgi = self._calc_lvgi(current_year, prior_year)
        tata = self._calc_tata(current_year)
        
        variables = MScoreVariables(
            dsri=dsri, gmi=gmi, aqi=aqi, sgi=sgi,
            depi=depi, sgai=sgai, lvgi=lvgi, tata=tata
        )
        
        # Calculate M-Score
        m_score = (
            self.INTERCEPT +
            self.COEF_DSRI * dsri +
            self.COEF_GMI * gmi +
            self.COEF_AQI * aqi +
            self.COEF_SGI * sgi +
            self.COEF_DEPI * depi +
            self.COEF_SGAI * sgai +
            self.COEF_TATA * tata +
            self.COEF_LVGI * lvgi
        )
        
        # Classify risk level
        if m_score < self.THRESHOLD_UNLIKELY:
            risk_level = ManipulationRisk.UNLIKELY
        elif m_score < self.THRESHOLD_LIKELY:
            risk_level = ManipulationRisk.GRAY_ZONE
        else:
            risk_level = ManipulationRisk.LIKELY
        
        # Identify red flags
        red_flags = []
        dsri_flag = dsri > 1.0
        gmi_flag = gmi > 1.0
        aqi_flag = aqi > 1.0
        sgi_flag = sgi > 1.2  # >20% growth
        tata_flag = tata > 0.05  # >5% accruals
        
        if dsri_flag:
            red_flags.append(f"DSRI={dsri:.2f}: Receivables growing faster than sales (revenue inflation risk)")
        if gmi_flag:
            red_flags.append(f"GMI={gmi:.2f}: Gross margin deteriorating (profitability pressure)")
        if aqi_flag:
            red_flags.append(f"AQI={aqi:.2f}: Asset quality declining (capitalization concerns)")
        if sgi_flag:
            red_flags.append(f"SGI={sgi:.2f}: High sales growth (manipulation incentive)")
        if tata_flag:
            red_flags.append(f"TATA={tata:.2f}: High accruals relative to assets (earnings quality concern)")
        
        # Generate interpretation
        interpretation = self._generate_interpretation(m_score, risk_level, red_flags)
        
        return MScoreResult(
            m_score=m_score,
            risk_level=risk_level,
            variables=variables,
            threshold=self.THRESHOLD_LIKELY,
            red_flags=red_flags,
            interpretation=interpretation,
            dsri_flag=dsri_flag,
            gmi_flag=gmi_flag,
            aqi_flag=aqi_flag,
            sgi_flag=sgi_flag,
            tata_flag=tata_flag
        )
    
    def _calc_dsri(self, curr: Dict, prior: Dict) -> float:
        """Days Sales in Receivables Index."""
        curr_ratio = self._safe_divide(curr.get('receivables', 0), curr.get('sales', 1))
        prior_ratio = self._safe_divide(prior.get('receivables', 0), prior.get('sales', 1))
        return self._safe_divide(curr_ratio, prior_ratio, 1.0)
    
    def _calc_gmi(self, curr: Dict, prior: Dict) -> float:
        """Gross Margin Index."""
        return self._safe_divide(prior.get('gross_margin', 0), curr.get('gross_margin', 1), 1.0)
    
    def _calc_aqi(self, curr: Dict, prior: Dict) -> float:
        """Asset Quality Index."""
        curr_quality = 1 - self._safe_divide(
            curr.get('current_assets', 0) + curr.get('ppe', 0),
            curr.get('total_assets', 1)
        )
        prior_quality = 1 - self._safe_divide(
            prior.get('current_assets', 0) + prior.get('ppe', 0),
            prior.get('total_assets', 1)
        )
        return self._safe_divide(curr_quality, prior_quality, 1.0)
    
    def _calc_sgi(self, curr: Dict, prior: Dict) -> float:
        """Sales Growth Index."""
        return self._safe_divide(curr.get('sales', 0), prior.get('sales', 1), 1.0)
    
    def _calc_depi(self, curr: Dict, prior: Dict) -> float:
        """Depreciation Index."""
        curr_rate = self._safe_divide(
            curr.get('depreciation', 0),
            curr.get('depreciation', 0) + curr.get('ppe', 1)
        )
        prior_rate = self._safe_divide(
            prior.get('depreciation', 0),
            prior.get('depreciation', 0) + prior.get('ppe', 1)
        )
        return self._safe_divide(prior_rate, curr_rate, 1.0)
    
    def _calc_sgai(self, curr: Dict, prior: Dict) -> float:
        """SG&A Index."""
        curr_ratio = self._safe_divide(curr.get('sga', 0), curr.get('sales', 1))
        prior_ratio = self._safe_divide(prior.get('sga', 0), prior.get('sales', 1))
        return self._safe_divide(curr_ratio, prior_ratio, 1.0)
    
    def _calc_lvgi(self, curr: Dict, prior: Dict) -> float:
        """Leverage Index."""
        curr_lev = self._safe_divide(curr.get('total_debt', 0), curr.get('total_assets', 1))
        prior_lev = self._safe_divide(prior.get('total_debt', 0), prior.get('total_assets', 1))
        return self._safe_divide(curr_lev, prior_lev, 1.0)
    
    def _calc_tata(self, curr: Dict) -> float:
        """Total Accruals to Total Assets."""
        accruals = curr.get('net_income', 0) - curr.get('cfo', 0)
        return self._safe_divide(accruals, curr.get('total_assets', 1))
    
    def _safe_divide(self, num: float, denom: float, default: float = 0.0) -> float:
        """Safe division with default value."""
        if denom == 0:
            return default
        return num / denom
    
    def _generate_interpretation(
        self, 
        m_score: float, 
        risk_level: ManipulationRisk,
        red_flags: List[str]
    ) -> str:
        """Generate human-readable interpretation."""
        if risk_level == ManipulationRisk.UNLIKELY:
            base = f"M-Score of {m_score:.2f} is below -2.22, indicating a LOW probability of earnings manipulation."
        elif risk_level == ManipulationRisk.GRAY_ZONE:
            base = f"M-Score of {m_score:.2f} is in the gray zone (-2.22 to -1.78), warranting FURTHER INVESTIGATION."
        else:
            base = f"M-Score of {m_score:.2f} exceeds -1.78, indicating a HIGH probability of earnings manipulation. ENFORCEMENT REFERRAL RECOMMENDED."
        
        if red_flags:
            base += f" {len(red_flags)} variable(s) raised red flags."
        
        return base

