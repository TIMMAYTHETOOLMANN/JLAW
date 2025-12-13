"""
Isolation Forest Anomaly Detector
==================================

ML-based anomaly detection for market data.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest as SKLearnIsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Using mock mode.")


class IsolationForestAnomalyDetector:
    """
    Anomaly detector using Isolation Forest algorithm.
    
    Detects unusual market behavior patterns.
    """
    
    def __init__(
        self,
        contamination: float = 0.01,
        n_estimators: int = 100
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        
        if SKLEARN_AVAILABLE:
            self.model = SKLearnIsolationForest(
                contamination=contamination,
                n_estimators=n_estimators,
                random_state=42
            )
            self.mock_mode = False
        else:
            self.mock_mode = True
    
    def fit_predict(
        self,
        data: List[List[float]]
    ) -> List[int]:
        """Fit model and predict anomalies."""
        if self.mock_mode or not data:
            return [-1 if i < len(data) * self.contamination else 1 for i in range(len(data))]
        
        predictions = self.model.fit_predict(data)
        return predictions.tolist()
