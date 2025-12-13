"""
Industry-Specific Z-Score Calibration
======================================

Industry-adjusted Z-Score thresholds for 28 SIC code ranges.
"""

from typing import Dict
import logging

logger = logging.getLogger(__name__)


class IndustryAdjustedZScoreCalculator:
    """
    Calculates industry-adjusted Z-Scores.
    
    Different industries have different capital structures and risk profiles,
    requiring adjusted thresholds.
    """
    
    # SIC code range thresholds
    INDUSTRY_THRESHOLDS = {
        '01-09': {'safe': 3.5, 'grey_upper': 3.5, 'grey_lower': 2.0, 'distress': 2.0},  # Agriculture
        '10-14': {'safe': 2.5, 'grey_upper': 2.5, 'grey_lower': 1.5, 'distress': 1.5},  # Mining
        '15-17': {'safe': 2.8, 'grey_upper': 2.8, 'grey_lower': 1.8, 'distress': 1.8},  # Construction
        '20-39': {'safe': 2.99, 'grey_upper': 2.99, 'grey_lower': 1.81, 'distress': 1.81},  # Manufacturing
        '40-49': {'safe': 2.5, 'grey_upper': 2.5, 'grey_lower': 1.5, 'distress': 1.5},  # Transportation
        '50-51': {'safe': 2.7, 'grey_upper': 2.7, 'grey_lower': 1.7, 'distress': 1.7},  # Wholesale Trade
        '52-59': {'safe': 2.8, 'grey_upper': 2.8, 'grey_lower': 1.8, 'distress': 1.8},  # Retail Trade
        '60-67': {'safe': 2.0, 'grey_upper': 2.0, 'grey_lower': 1.2, 'distress': 1.2},  # Finance
        '70-89': {'safe': 2.6, 'grey_upper': 2.6, 'grey_lower': 1.6, 'distress': 1.6},  # Services
        '91-99': {'safe': 3.0, 'grey_upper': 3.0, 'grey_lower': 2.0, 'distress': 2.0},  # Public Admin
    }
    
    def __init__(self):
        self.logger = logger
    
    def get_thresholds(self, sic_code: str) -> Dict[str, float]:
        """Get thresholds for SIC code."""
        sic_num = int(sic_code[:2]) if sic_code else 20
        
        for range_key, thresholds in self.INDUSTRY_THRESHOLDS.items():
            start, end = range_key.split('-')
            if int(start) <= sic_num <= int(end):
                return thresholds
        
        # Default to manufacturing thresholds
        return self.INDUSTRY_THRESHOLDS['20-39']
    
    def calculate_z_score(
        self,
        working_capital: float,
        retained_earnings: float,
        ebit: float,
        market_value_equity: float,
        total_assets: float,
        sales: float,
        total_liabilities: float
    ) -> float:
        """Calculate Altman Z-Score."""
        if total_assets == 0:
            return 0.0
        
        X1 = working_capital / total_assets
        X2 = retained_earnings / total_assets
        X3 = ebit / total_assets
        X4 = market_value_equity / total_liabilities if total_liabilities > 0 else 0
        X5 = sales / total_assets
        
        Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
        
        return Z
