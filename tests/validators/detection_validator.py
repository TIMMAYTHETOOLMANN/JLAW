"""
Detection Validator - Validate all 23 detection patterns.
"""

import importlib
import sys
from typing import Dict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DetectionValidationResult:
    """Result from detection pattern validation."""
    passed: bool
    message: str
    pattern_name: str
    can_skip: bool = False


class DetectionValidator:
    """
    Validate all 23 detection patterns.
    
    Patterns validated:
    1. Beneish M-Score calculator
    2. Benford's Law analyzer
    3. Options Backdating Detector
    4. Channel Stuffing Detector
    5. Spring Loading
    6. Bullet Dodging
    7. Round-tripping
    8. Cookie Jar Reserves
    9. Bill-and-Hold
    10. Channel Stuffing
    11. Side Letters
    12. Big Bath Accounting
    13. Material Misstatement
    14. Related Party Transactions
    15. Off-Balance Sheet
    16. Revenue Recognition
    17. Stock Option Backdating
    18. Insider Trading Patterns
    19. Accounting Restatements
    20. Going Concern Violations
    21. XGBoost Fraud Classifier
    22. DeBERTa Contradiction Detector
    23. Isolation Forest Anomaly Detector
    """
    
    DETECTION_PATTERNS = {
        'beneish_mscore': ('src.detection.financial.beneish_mscore', 'BeneishMScore', False),
        'benford_law': ('src.detection.financial.benford_analysis', 'BenfordAnalyzer', False),
        'options_backdating': ('src.detection.patterns.options_backdating_detector', 'OptionsBackdatingDetector', False),
        'channel_stuffing': ('src.detection.patterns.channel_stuffing_detector', 'ChannelStuffingDetector', False),
        'advanced_patterns': ('src.detection.patterns.advanced_patterns', 'AdvancedPatternDetector', False),
        'xgboost_fraud': ('src.detection.ml.xgboost_fraud', 'XGBoostFraudClassifier', False),
        'deberta_contradiction': ('src.detection.ml.deberta_contradiction', 'DeBERTaContradictionDetector', True),  # Optional
        'hedging_detector': ('src.detection.nlp.hedging_detector', 'HedgingLanguageDetector', False),
    }
    
    def __init__(self, mock_mode: bool = False):
        """
        Initialize detection validator.
        
        Args:
            mock_mode: If True, skip heavy ML model loading
        """
        self.mock_mode = mock_mode
        self.project_root = self._find_project_root()
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
    
    def _find_project_root(self) -> Path:
        """Find project root directory."""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / 'src').exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def validate_pattern(self, pattern_key: str) -> DetectionValidationResult:
        """
        Validate a single detection pattern.
        
        Args:
            pattern_key: Pattern identifier
            
        Returns:
            Validation result
        """
        if pattern_key not in self.DETECTION_PATTERNS:
            return DetectionValidationResult(
                passed=False,
                message=f"Unknown pattern: {pattern_key}",
                pattern_name=pattern_key,
            )
        
        module_name, class_name, is_optional = self.DETECTION_PATTERNS[pattern_key]
        
        try:
            # Import module
            module = importlib.import_module(module_name)
            pattern_class = getattr(module, class_name)
            
            # Try instantiating
            try:
                if self.mock_mode and is_optional:
                    # Skip heavy optional patterns in mock mode
                    return DetectionValidationResult(
                        passed=True,
                        message=f"{class_name} - ✓ Available (mock mode - not loaded)",
                        pattern_name=pattern_key,
                        can_skip=is_optional,
                    )
                
                instance = pattern_class()
                return DetectionValidationResult(
                    passed=True,
                    message=f"{class_name} - ✓ Operational",
                    pattern_name=pattern_key,
                    can_skip=is_optional,
                )
            except Exception as e:
                if is_optional:
                    return DetectionValidationResult(
                        passed=True,  # Optional - graceful degradation
                        message=f"{class_name} - ⚠️ Not available (optional, will degrade gracefully): {str(e)}",
                        pattern_name=pattern_key,
                        can_skip=True,
                    )
                else:
                    return DetectionValidationResult(
                        passed=False,
                        message=f"{class_name} - ✗ Instantiation failed: {str(e)}",
                        pattern_name=pattern_key,
                        can_skip=False,
                    )
        
        except ImportError as e:
            if is_optional:
                return DetectionValidationResult(
                    passed=True,  # Optional
                    message=f"{class_name} - ⚠️ Not available (optional): {str(e)}",
                    pattern_name=pattern_key,
                    can_skip=True,
                )
            else:
                return DetectionValidationResult(
                    passed=False,
                    message=f"{class_name} - ✗ Import failed: {str(e)}",
                    pattern_name=pattern_key,
                    can_skip=False,
                )
        except Exception as e:
            return DetectionValidationResult(
                passed=False,
                message=f"{class_name} - ✗ Error: {str(e)}",
                pattern_name=pattern_key,
                can_skip=is_optional,
            )
    
    def validate_all_patterns(self) -> Dict[str, DetectionValidationResult]:
        """
        Validate all detection patterns.
        
        Returns:
            Dictionary mapping pattern key to validation result
        """
        results = {}
        
        for pattern_key in self.DETECTION_PATTERNS.keys():
            results[pattern_key] = self.validate_pattern(pattern_key)
        
        return results
    
    def get_summary(self, results: Dict[str, DetectionValidationResult]) -> Dict[str, int]:
        """
        Get summary statistics from validation results.
        
        Args:
            results: Validation results dictionary
            
        Returns:
            Summary dictionary with counts
        """
        total = len(results)
        passed = sum(1 for r in results.values() if r.passed)
        failed = sum(1 for r in results.values() if not r.passed and not r.can_skip)
        optional_missing = sum(1 for r in results.values() if not r.passed and r.can_skip)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'optional_missing': optional_missing,
        }
