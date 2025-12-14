"""
Tests for Isolation Forest Anomaly Detection
"""

import pytest
from datetime import datetime
from src.nodes.node15_market_correlation.isolation_forest import (
    IsolationForestAnomalyDetector,
    AnomalyScore,
    AnomalyDetectionResult
)


def test_isolation_forest_initialization():
    """Test IsolationForestAnomalyDetector initialization."""
    detector = IsolationForestAnomalyDetector(
        n_estimators=100,
        contamination=0.01
    )
    
    assert detector.n_estimators == 100
    assert detector.contamination == 0.01
    assert detector.fitted == False


def test_fit_predict():
    """Test fit_predict method."""
    detector = IsolationForestAnomalyDetector(contamination=0.1)
    
    # Create sample data (normal + anomalies)
    data = [[1.0, 2.0], [1.1, 2.1], [1.2, 1.9], [10.0, 10.0]]  # Last one is anomaly
    
    result = detector.fit_predict(data)
    
    assert isinstance(result, AnomalyDetectionResult)
    assert result.total_samples == 4
    assert result.num_anomalies >= 0
    assert result.anomaly_rate >= 0


def test_anomaly_score_dataclass():
    """Test AnomalyScore dataclass."""
    score = AnomalyScore(
        index=0,
        is_anomaly=True,
        anomaly_score=-0.5,
        features=[1.0, 2.0, 3.0]
    )
    
    assert score.is_anomaly == True
    assert score.anomaly_score == -0.5
    assert len(score.features) == 3
    
    # Test to_dict
    score_dict = score.to_dict()
    assert score_dict["is_anomaly"] == True
    assert "features" in score_dict


def test_fit_and_predict_separately():
    """Test fit and predict as separate operations."""
    detector = IsolationForestAnomalyDetector()
    
    # Training data (normal samples)
    train_data = [[1.0, 2.0], [1.1, 2.1], [1.2, 1.9], [0.9, 2.0]]
    detector.fit(train_data)
    
    assert detector.fitted == True
    
    # Test data (with potential anomalies)
    test_data = [[1.0, 2.0], [10.0, 10.0]]
    result = detector.predict(test_data)
    
    assert isinstance(result, AnomalyDetectionResult)
    assert result.total_samples == 2


def test_get_anomaly_scores():
    """Test getting anomaly scores without classification."""
    detector = IsolationForestAnomalyDetector()
    
    # Fit first
    data = [[1.0, 2.0], [1.1, 2.1], [1.2, 1.9]]
    detector.fit(data)
    
    # Get scores
    scores = detector.get_anomaly_scores(data)
    
    assert len(scores) == 3
    assert all(isinstance(s, float) for s in scores)


def test_parameters():
    """Test parameter retrieval."""
    detector = IsolationForestAnomalyDetector(
        n_estimators=150,
        contamination=0.05
    )
    
    params = detector._get_parameters()
    
    assert params["n_estimators"] == 150
    assert params["contamination"] == 0.05
    assert params["fitted"] == False
