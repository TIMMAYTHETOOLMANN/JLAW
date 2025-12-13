"""
Z-Score Validator
=================

Validates Z-Score coefficients against recent bankruptcy data.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    accuracy: float
    false_positives: int
    false_negatives: int
    total_tested: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy": round(self.accuracy, 3),
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "total_tested": self.total_tested
        }


class ZScoreValidator:
    """Validates Z-Score model against recent bankruptcy events."""
    
    def validate(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Validate model against test cases."""
        correct = 0
        false_pos = 0
        false_neg = 0
        
        for case in test_cases:
            z_score = case.get('z_score', 0)
            actual_bankrupt = case.get('bankrupt', False)
            
            predicted_bankrupt = z_score < 1.81
            
            if predicted_bankrupt == actual_bankrupt:
                correct += 1
            elif predicted_bankrupt and not actual_bankrupt:
                false_pos += 1
            else:
                false_neg += 1
        
        total = len(test_cases)
        accuracy = correct / total if total > 0 else 0
        
        return ValidationResult(
            accuracy=accuracy,
            false_positives=false_pos,
            false_negatives=false_neg,
            total_tested=total
        )
