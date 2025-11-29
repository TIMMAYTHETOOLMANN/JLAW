"""Numerical Contradiction Detector"""

import re
from typing import Optional, Dict, Any


class NumericalDetector:
    """Detects numerical contradictions"""
    
    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
    
    def detect(self, stmt1: str, stmt2: str) -> Optional[Dict[str, Any]]:
        """Detect numerical contradictions between statements"""
        # Extract numbers from both statements
        nums1 = self._extract_numbers(stmt1)
        nums2 = self._extract_numbers(stmt2)
        
        # Compare numbers
        for n1 in nums1:
            for n2 in nums2:
                if self._is_contradictory(n1, n2):
                    return {
                        'type': 'numerical',
                        'value1': n1,
                        'value2': n2,
                        'difference': abs(n1 - n2) / max(n1, n2)
                    }
        return None
    
    def _extract_numbers(self, text: str) -> list:
        """Extract numerical values from text"""
        numbers = []
        # Find all numbers with optional millions/billions
        pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|M|B)?'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = float(match.group(1).replace(',', ''))
            scale = match.group(2)
            if scale and scale.lower() in ['million', 'm']:
                value *= 1e6
            elif scale and scale.lower() in ['billion', 'b']:
                value *= 1e9
            numbers.append(value)
        return numbers
    
    def _is_contradictory(self, n1: float, n2: float) -> bool:
        """Check if two numbers are contradictory"""
        if n1 == 0 or n2 == 0:
            return False
        diff = abs(n1 - n2) / max(n1, n2)
        return diff > self.threshold and diff < 0.9  # Different but related

