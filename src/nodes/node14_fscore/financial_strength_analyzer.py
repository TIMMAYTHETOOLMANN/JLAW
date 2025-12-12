"""
NODE 14: Piotroski F-Score Financial Strength Analyzer
======================================================

Implements Piotroski's 9-point binary scoring system:
- Profitability signals (4 points)
- Leverage/Liquidity signals (3 points)
- Operating efficiency signals (2 points)

Academic Reference: Piotroski, J.D. (2000) "Value Investing: The Use of 
Historical Financial Statement Information to Separate Winners from Losers"

F-Score Interpretation:
- 8-9: Strong financial position (buy signal)
- 4-6: Average financial position (hold)
- 0-3: Weak financial position (avoid/sell)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class FinancialStrength(Enum):
    STRONG = "Strong (8-9)"
    AVERAGE = "Average (4-7)"
    WEAK = "Weak (0-3)"


class FScoreSignal(Enum):
    POSITIVE = 1
    NEGATIVE = 0


@dataclass
class FScoreInputs:
    """Financial inputs for F-Score calculation."""
    # Current Period
    net_income: float
    operating_cash_flow: float
    return_on_assets: float
    total_assets: float
    long_term_debt: float
    current_ratio: float
    shares_outstanding: int
    gross_margin: float
    asset_turnover: float
    
    # Prior Period
    prior_return_on_assets: float
    prior_long_term_debt: float
    prior_current_ratio: float
    prior_shares_outstanding: int
    prior_gross_margin: float
    prior_asset_turnover: float
    
    # Metadata
    fiscal_period: str = ""


@dataclass
class FScoreComponents:
    """Individual F-Score signal components."""
    # Profitability (4 points)
    roa_positive: FScoreSignal  # ROA > 0
    cfo_positive: FScoreSignal  # CFO > 0
    roa_improving: FScoreSignal  # ROA > Prior ROA
    accruals: FScoreSignal  # CFO > Net Income (quality of earnings)
    
    # Leverage/Liquidity (3 points)
    leverage_decreasing: FScoreSignal  # Long-term debt decreased
    liquidity_improving: FScoreSignal  # Current ratio improved
    no_dilution: FScoreSignal  # Shares not increased
    
    # Operating Efficiency (2 points)
    margin_improving: FScoreSignal  # Gross margin improved
    turnover_improving: FScoreSignal  # Asset turnover improved
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "profitability": {
                "ROA_positive": self.roa_positive.value,
                "CFO_positive": self.cfo_positive.value,
                "ROA_improving": self.roa_improving.value,
                "accruals_quality": self.accruals.value,
                "subtotal": self.roa_positive.value + self.cfo_positive.value + 
                           self.roa_improving.value + self.accruals.value
            },
            "leverage_liquidity": {
                "leverage_decreasing": self.leverage_decreasing.value,
                "liquidity_improving": self.liquidity_improving.value,
                "no_dilution": self.no_dilution.value,
                "subtotal": self.leverage_decreasing.value + self.liquidity_improving.value + 
                           self.no_dilution.value
            },
            "operating_efficiency": {
                "margin_improving": self.margin_improving.value,
                "turnover_improving": self.turnover_improving.value,
                "subtotal": self.margin_improving.value + self.turnover_improving.value
            }
        }


@dataclass
class FScoreResult:
    """Complete F-Score calculation result."""
    score: int  # 0-9
    strength: FinancialStrength
    components: FScoreComponents
    profitability_score: int  # 0-4
    leverage_score: int  # 0-3
    efficiency_score: int  # 0-2
    interpretation: str
    investment_signal: str
    evidence_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "f_score": self.score,
            "strength": self.strength.value,
            "components": self.components.to_dict(),
            "breakdown": {
                "profitability": f"{self.profitability_score}/4",
                "leverage_liquidity": f"{self.leverage_score}/3",
                "operating_efficiency": f"{self.efficiency_score}/2"
            },
            "interpretation": self.interpretation,
            "investment_signal": self.investment_signal
        }


@dataclass
class FinancialStrengthAlert:
    """Alert for financial strength changes."""
    alert_type: str
    company_id: str
    company_name: str
    current_f_score: int
    previous_f_score: Optional[int]
    score_change: Optional[int]
    strength: FinancialStrength
    risk_indicators: List[str]
    evidence_hash: str
    severity: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "company": self.company_name,
            "current_f_score": self.current_f_score,
            "previous_f_score": self.previous_f_score,
            "score_change": self.score_change,
            "strength": self.strength.value,
            "risk_indicators": self.risk_indicators,
            "severity": self.severity
        }


@dataclass
class Node14Output:
    """Output from Node 14 analysis."""
    companies_analyzed: int
    strong_count: int
    weak_count: int
    average_f_score: float
    alerts: List[FinancialStrengthAlert]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "companies_analyzed": self.companies_analyzed,
                "strong_financial": self.strong_count,
                "weak_financial": self.weak_count,
                "average_f_score": round(self.average_f_score, 2)
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class FinancialStrengthAnalyzer:
    """
    Piotroski F-Score Financial Strength Analyzer.
    
    The F-Score is a 9-point binary scoring system that measures:
    
    PROFITABILITY (4 points):
    1. ROA > 0 (positive return on assets)
    2. CFO > 0 (positive operating cash flow)
    3. ROA > Prior ROA (improving profitability)
    4. CFO > Net Income (earnings quality - accruals)
    
    LEVERAGE/LIQUIDITY (3 points):
    5. Long-term debt decreased
    6. Current ratio improved
    7. Shares outstanding not increased (no dilution)
    
    OPERATING EFFICIENCY (2 points):
    8. Gross margin improved
    9. Asset turnover improved
    
    Academic validation: F-Score >7 outperforms market by ~13.4% annually
    """
    
    def __init__(self):
        pass
    
    def calculate_f_score(self, inputs: FScoreInputs) -> FScoreResult:
        """
        Calculate Piotroski F-Score from financial inputs.
        
        Args:
            inputs: FScoreInputs with current and prior period data
            
        Returns:
            FScoreResult with complete analysis
        """
        # Profitability signals (4 points)
        roa_positive = FScoreSignal.POSITIVE if inputs.return_on_assets > 0 else FScoreSignal.NEGATIVE
        cfo_positive = FScoreSignal.POSITIVE if inputs.operating_cash_flow > 0 else FScoreSignal.NEGATIVE
        roa_improving = FScoreSignal.POSITIVE if inputs.return_on_assets > inputs.prior_return_on_assets else FScoreSignal.NEGATIVE
        accruals = FScoreSignal.POSITIVE if inputs.operating_cash_flow > inputs.net_income else FScoreSignal.NEGATIVE
        
        # Leverage/Liquidity signals (3 points)
        leverage_decreasing = FScoreSignal.POSITIVE if inputs.long_term_debt <= inputs.prior_long_term_debt else FScoreSignal.NEGATIVE
        liquidity_improving = FScoreSignal.POSITIVE if inputs.current_ratio > inputs.prior_current_ratio else FScoreSignal.NEGATIVE
        no_dilution = FScoreSignal.POSITIVE if inputs.shares_outstanding <= inputs.prior_shares_outstanding else FScoreSignal.NEGATIVE
        
        # Operating Efficiency signals (2 points)
        margin_improving = FScoreSignal.POSITIVE if inputs.gross_margin > inputs.prior_gross_margin else FScoreSignal.NEGATIVE
        turnover_improving = FScoreSignal.POSITIVE if inputs.asset_turnover > inputs.prior_asset_turnover else FScoreSignal.NEGATIVE
        
        components = FScoreComponents(
            roa_positive=roa_positive,
            cfo_positive=cfo_positive,
            roa_improving=roa_improving,
            accruals=accruals,
            leverage_decreasing=leverage_decreasing,
            liquidity_improving=liquidity_improving,
            no_dilution=no_dilution,
            margin_improving=margin_improving,
            turnover_improving=turnover_improving
        )
        
        # Calculate scores
        profitability = roa_positive.value + cfo_positive.value + roa_improving.value + accruals.value
        leverage = leverage_decreasing.value + liquidity_improving.value + no_dilution.value
        efficiency = margin_improving.value + turnover_improving.value
        
        total_score = profitability + leverage + efficiency
        
        # Classify strength
        if total_score >= 8:
            strength = FinancialStrength.STRONG
            interpretation = 'Excellent financial health across all dimensions'
            signal = 'BUY - Strong fundamentals'
        elif total_score >= 4:
            strength = FinancialStrength.AVERAGE
            interpretation = 'Mixed financial signals - monitor closely'
            signal = 'HOLD - Average fundamentals'
        else:
            strength = FinancialStrength.WEAK
            interpretation = 'Poor financial health - multiple warning signs'
            signal = 'SELL/AVOID - Weak fundamentals'
        
        return FScoreResult(
            score=total_score,
            strength=strength,
            components=components,
            profitability_score=profitability,
            leverage_score=leverage,
            efficiency_score=efficiency,
            interpretation=interpretation,
            investment_signal=signal,
            evidence_hash=self._generate_hash({'inputs': str(inputs), 'score': total_score})
        )
    
    def monitor_trends(
        self,
        historical_scores: List[Dict[str, Any]],
        company_id: str,
        company_name: str
    ) -> List[FinancialStrengthAlert]:
        """
        Monitor F-Score trends and generate alerts.
        
        Args:
            historical_scores: List of {'period': str, 'result': FScoreResult}
            company_id: Company identifier
            company_name: Company name
            
        Returns:
            List of FinancialStrengthAlert objects
        """
        alerts = []
        
        if len(historical_scores) < 2:
            return alerts
        
        sorted_scores = sorted(historical_scores, key=lambda x: x['period'])
        
        latest = sorted_scores[-1]['result']
        previous = sorted_scores[-2]['result']
        score_change = latest.score - previous.score
        
        # Alert: Deteriorated to weak
        if latest.strength == FinancialStrength.WEAK and previous.strength != FinancialStrength.WEAK:
            alerts.append(FinancialStrengthAlert(
                alert_type='DETERIORATION_TO_WEAK',
                company_id=company_id,
                company_name=company_name,
                current_f_score=latest.score,
                previous_f_score=previous.score,
                score_change=score_change,
                strength=FinancialStrength.WEAK,
                risk_indicators=[
                    f'F-Score declined from {previous.score} to {latest.score}',
                    f'Profitability: {latest.profitability_score}/4',
                    f'Leverage/Liquidity: {latest.leverage_score}/3',
                    f'Operating Efficiency: {latest.efficiency_score}/2',
                    latest.interpretation
                ],
                evidence_hash=self._generate_hash({'latest': latest.score, 'previous': previous.score}),
                severity='HIGH'
            ))
        
        # Alert: Significant decline (3+ points)
        if score_change <= -3:
            alerts.append(FinancialStrengthAlert(
                alert_type='SIGNIFICANT_DECLINE',
                company_id=company_id,
                company_name=company_name,
                current_f_score=latest.score,
                previous_f_score=previous.score,
                score_change=score_change,
                strength=latest.strength,
                risk_indicators=[
                    f'F-Score dropped {abs(score_change)} points',
                    'Multiple financial metrics deteriorating',
                    'Requires immediate investigation'
                ],
                evidence_hash=self._generate_hash({'latest': latest.score, 'previous': previous.score}),
                severity='HIGH' if latest.score <= 3 else 'MEDIUM'
            ))
        
        # Alert: Profitability collapse (all 4 profitability signals negative)
        if latest.profitability_score == 0:
            alerts.append(FinancialStrengthAlert(
                alert_type='PROFITABILITY_COLLAPSE',
                company_id=company_id,
                company_name=company_name,
                current_f_score=latest.score,
                previous_f_score=previous.score,
                score_change=score_change,
                strength=latest.strength,
                risk_indicators=[
                    'All profitability signals negative',
                    'Negative ROA',
                    'Negative operating cash flow',
                    'Declining profitability',
                    'Poor earnings quality'
                ],
                evidence_hash=self._generate_hash({'latest': latest.score, 'profitability': 0}),
                severity='CRITICAL'
            ))
        
        return alerts
    
    def identify_red_flags(self, result: FScoreResult) -> List[str]:
        """
        Identify specific red flags from F-Score components.
        """
        flags = []
        comp = result.components
        
        # Profitability flags
        if comp.roa_positive == FScoreSignal.NEGATIVE:
            flags.append('Negative return on assets - company is unprofitable')
        if comp.cfo_positive == FScoreSignal.NEGATIVE:
            flags.append('Negative operating cash flow - cash burn')
        if comp.accruals == FScoreSignal.NEGATIVE:
            flags.append('CFO < Net Income - potential earnings manipulation')
        
        # Leverage flags
        if comp.leverage_decreasing == FScoreSignal.NEGATIVE:
            flags.append('Increasing long-term debt - rising financial risk')
        if comp.liquidity_improving == FScoreSignal.NEGATIVE:
            flags.append('Declining current ratio - liquidity concerns')
        if comp.no_dilution == FScoreSignal.NEGATIVE:
            flags.append('Share dilution - equity value erosion')
        
        # Efficiency flags
        if comp.margin_improving == FScoreSignal.NEGATIVE:
            flags.append('Declining gross margin - pricing power erosion')
        if comp.turnover_improving == FScoreSignal.NEGATIVE:
            flags.append('Declining asset turnover - operational inefficiency')
        
        return flags
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()

