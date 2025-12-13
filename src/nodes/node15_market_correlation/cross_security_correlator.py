"""
Cross-Security Correlator
==========================

Analyzes correlations and contagion across securities.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CrossSecurityCorrelator:
    """Analyzes cross-security correlations."""
    
    def __init__(
        self,
        correlation_threshold: float = 0.7
    ):
        self.correlation_threshold = correlation_threshold
    
    def calculate_correlation(
        self,
        returns1: List[float],
        returns2: List[float]
    ) -> float:
        """Calculate correlation coefficient."""
        if not returns1 or not returns2 or len(returns1) != len(returns2):
            return 0.0
        
        # Simplified correlation calculation
        n = len(returns1)
        mean1 = sum(returns1) / n
        mean2 = sum(returns2) / n
        
        numerator = sum((returns1[i] - mean1) * (returns2[i] - mean2) for i in range(n))
        
        var1 = sum((x - mean1) ** 2 for x in returns1)
        var2 = sum((x - mean2) ** 2 for x in returns2)
        
        if var1 == 0 or var2 == 0:
            return 0.0
        
        correlation = numerator / (var1 * var2) ** 0.5
        
        return correlation
    
    def detect_contagion(
        self,
        securities_data: Dict[str, List[float]]
    ) -> List[Dict[str, Any]]:
        """Detect contagion patterns."""
        contagion_events = []
        
        symbols = list(securities_data.keys())
        
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1 = symbols[i]
                symbol2 = symbols[j]
                
                corr = self.calculate_correlation(
                    securities_data[symbol1],
                    securities_data[symbol2]
                )
                
                if abs(corr) >= self.correlation_threshold:
                    contagion_events.append({
                        'symbol1': symbol1,
                        'symbol2': symbol2,
                        'correlation': corr,
                        'contagion_detected': True
                    })
        
        return contagion_events
