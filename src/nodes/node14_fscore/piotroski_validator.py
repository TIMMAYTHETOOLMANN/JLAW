"""
Piotroski F-Score Validator
============================

Backtests the Piotroski F-Score 13.4% annual alpha claim.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    period: str
    avg_return_high_fscore: float
    avg_return_low_fscore: float
    alpha: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "avg_return_high_fscore": round(self.avg_return_high_fscore, 4),
            "avg_return_low_fscore": round(self.avg_return_low_fscore, 4),
            "alpha": round(self.alpha, 4)
        }


class PiotroskiValidator:
    """Validates Piotroski F-Score performance."""
    
    EXPECTED_ALPHA = 0.134  # 13.4%
    
    def backtest(
        self,
        historical_data: List[Dict[str, Any]]
    ) -> BacktestResult:
        """Backtest F-Score strategy."""
        high_fscore_returns = []
        low_fscore_returns = []
        
        for record in historical_data:
            f_score = record.get('f_score', 5)
            annual_return = record.get('return', 0)
            
            if f_score >= 7:
                high_fscore_returns.append(annual_return)
            elif f_score <= 3:
                low_fscore_returns.append(annual_return)
        
        avg_high = sum(high_fscore_returns) / len(high_fscore_returns) if high_fscore_returns else 0
        avg_low = sum(low_fscore_returns) / len(low_fscore_returns) if low_fscore_returns else 0
        
        alpha = avg_high - avg_low
        
        return BacktestResult(
            period="Historical",
            avg_return_high_fscore=avg_high,
            avg_return_low_fscore=avg_low,
            alpha=alpha
        )
