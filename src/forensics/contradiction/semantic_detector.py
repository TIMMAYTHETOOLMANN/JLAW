"""Semantic Contradiction Detector"""

from typing import Optional, Dict, Any


class SemanticDetector:
    """Detects semantic contradictions in statements"""
    
    OPPOSING_PAIRS = [
        ('growth', 'decline'),
        ('increase', 'decrease'),
        ('profit', 'loss'),
        ('strong', 'weak'),
        ('positive', 'negative'),
        ('up', 'down'),
        ('rise', 'fall'),
        ('gain', 'loss')
    ]
    
    def detect(self, stmt1: str, stmt2: str) -> Optional[Dict[str, Any]]:
        """Detect semantic contradictions"""
        stmt1_lower = stmt1.lower()
        stmt2_lower = stmt2.lower()
        
        for word1, word2 in self.OPPOSING_PAIRS:
            if word1 in stmt1_lower and word2 in stmt2_lower:
                return {
                    'type': 'semantic',
                    'opposing_terms': (word1, word2),
                    'confidence': 0.8
                }
            if word2 in stmt1_lower and word1 in stmt2_lower:
                return {
                    'type': 'semantic',
                    'opposing_terms': (word2, word1),
                    'confidence': 0.8
                }
        
        return None

