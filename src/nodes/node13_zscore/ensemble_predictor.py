"""
Ensemble Bankruptcy Predictor
==============================

Combines Z-Score, F-Score, and market signals for composite prediction.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class CompositeBankruptcyPredictor:
    """
    Ensemble predictor combining multiple signals.
    
    Weights:
    - Z-Score: 40%
    - F-Score: 30%
    - Market signals: 30%
    """
    
    def __init__(
        self,
        weights: Dict[str, float] = None
    ):
        self.weights = weights or {'z': 0.4, 'f': 0.3, 'market': 0.3}
    
    def predict(
        self,
        z_score: float,
        f_score: int,
        market_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate composite prediction."""
        
        # Normalize scores to 0-1
        z_norm = max(0, min(1, (z_score - 1.0) / 3.0))
        f_norm = f_score / 9.0
        
        # Market signal score
        volume_anomaly = market_signals.get('volume_anomaly', False)
        price_decline = market_signals.get('price_decline_30d', 0)
        market_score = 0.3 if volume_anomaly else 0.5
        market_score += max(0, min(0.5, abs(price_decline) / 50))
        
        # Composite score
        composite = (
            self.weights['z'] * z_norm +
            self.weights['f'] * f_norm +
            self.weights['market'] * (1 - market_score)  # Invert market score
        )
        
        # Classification
        if composite > 0.7:
            risk = 'LOW'
        elif composite > 0.4:
            risk = 'MEDIUM'
        else:
            risk = 'HIGH'
        
        return {
            'composite_score': composite,
            'risk_level': risk,
            'components': {
                'z_score_contribution': self.weights['z'] * z_norm,
                'f_score_contribution': self.weights['f'] * f_norm,
                'market_contribution': self.weights['market'] * (1 - market_score)
            }
        }
