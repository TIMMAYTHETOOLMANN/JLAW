"""
Sector-Relative F-Score
========================

Calculates F-Score percentile rankings by GICS sector.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SectorRelativeFScore:
    """Calculates sector-relative F-Score rankings."""
    
    GICS_SECTORS = [
        "Energy", "Materials", "Industrials", "Consumer Discretionary",
        "Consumer Staples", "Health Care", "Financials", "Information Technology",
        "Communication Services", "Utilities", "Real Estate"
    ]
    
    def calculate_percentile(
        self,
        company_fscore: float,
        sector_fscores: List[float]
    ) -> float:
        """Calculate percentile rank within sector."""
        if not sector_fscores:
            return 0.5
        
        rank = sum(1 for score in sector_fscores if score <= company_fscore)
        percentile = rank / len(sector_fscores)
        
        return percentile
