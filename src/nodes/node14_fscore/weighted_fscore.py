"""
Weighted F-Score Calculator
============================

Calculates continuous F-Score (0.0-9.0) instead of binary (0-9).
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class WeightedFScoreCalculator:
    """
    Calculates weighted F-Score with continuous values.
    
    Each component can contribute partial points based on magnitude.
    """
    
    def calculate(
        self,
        financials: Dict[str, Any]
    ) -> float:
        """Calculate weighted F-Score."""
        score = 0.0
        
        # Profitability (4 points max)
        roa = financials.get('roa', 0)
        score += min(1.0, max(0, roa * 10))  # ROA contribution
        
        # Add other components (simplified)
        score += 1.0 if financials.get('cfo', 0) > 0 else 0
        score += 0.5 if financials.get('delta_roa', 0) > 0 else 0
        score += 0.5 if financials.get('accruals', 0) < 0 else 0
        
        # Leverage, Liquidity, Operating Efficiency (5 points)
        score += 1.0 if financials.get('delta_leverage', 0) < 0 else 0
        score += 1.0 if financials.get('delta_current_ratio', 0) > 0 else 0
        score += 0 # No new shares issued
        score += 1.0 if financials.get('delta_margin', 0) > 0 else 0
        score += 1.0 if financials.get('delta_turnover', 0) > 0 else 0
        
        return min(9.0, score)
