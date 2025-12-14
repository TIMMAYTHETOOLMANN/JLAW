"""
SEC Enforcement Validator
=========================

Main validator class for testing detection algorithms against
known SEC enforcement cases.

This module provides utilities for validating fraud detection
algorithms against historical SEC enforcement actions to ensure
detection accuracy and reliability.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)


@dataclass
class EnforcementCase:
    """Known SEC enforcement case for validation."""
    case_name: str
    company_name: str
    cik: str
    enforcement_year: int
    fraud_type: str
    period_start: date
    period_end: date
    known_indicators: Dict[str, Any]
    sec_release: str  # SEC Release number
    description: str


@dataclass
class ValidationResult:
    """Result of validation against enforcement case."""
    case_name: str
    detector_name: str
    expected_detection: bool
    actual_detection: bool
    passed: bool
    confidence_score: float
    expected_indicators: Dict[str, Any]
    detected_indicators: Dict[str, Any]
    notes: str


class SECEnforcementValidator:
    """
    Validator for testing detection algorithms against known cases.
    
    Maintains a database of known SEC enforcement cases and provides
    methods to validate detection algorithms against these cases.
    """
    
    # Known enforcement cases
    ENFORCEMENT_CASES = {
        'ENRON_2001': EnforcementCase(
            case_name="Enron Corporation",
            company_name="Enron Corp",
            cik="1024401",
            enforcement_year=2001,
            fraud_type="earnings_manipulation",
            period_start=date(1999, 1, 1),
            period_end=date(2001, 10, 1),
            known_indicators={
                'm_score': {
                    'expected_range': (-1.78, 10.0),  # Should exceed -1.78 threshold
                    'years': [1999, 2000, 2001]
                },
                'benford_deviation': True,
                'spe_manipulation': True  # Special Purpose Entities
            },
            sec_release="LR-17627",
            description="Accounting fraud through SPEs, mark-to-market accounting manipulation"
        ),
        
        'WORLDCOM_2002': EnforcementCase(
            case_name="WorldCom, Inc.",
            company_name="WorldCom",
            cik="723527",
            enforcement_year=2002,
            fraud_type="expense_capitalization",
            period_start=date(2001, 1, 1),
            period_end=date(2002, 3, 31),
            known_indicators={
                'benford_deviation': {
                    'expected': True,
                    'line_items': ['line_costs', 'capex']
                },
                'expense_ratio_anomaly': True,
                'cash_flow_divergence': True
            },
            sec_release="LR-17588",
            description="$3.8B fraud by capitalizing line costs as assets"
        ),
        
        'THERANOS_2018': EnforcementCase(
            case_name="Theranos, Inc.",
            company_name="Theranos",
            cik="N/A",  # Private company
            enforcement_year=2018,
            fraud_type="material_misstatement",
            period_start=date(2013, 1, 1),
            period_end=date(2015, 12, 31),
            known_indicators={
                'revenue_fabrication': True,
                'technology_misrepresentation': True,
                'material_omissions': True
            },
            sec_release="LR-24251",
            description="Massive fraud involving false claims about blood testing technology"
        ),
        
        'NIKOLA_2020': EnforcementCase(
            case_name="Nikola Corporation",
            company_name="Nikola Corp",
            cik="1731289",
            enforcement_year=2020,
            fraud_type="pre_announcement_trading",
            period_start=date(2019, 1, 1),
            period_end=date(2020, 9, 1),
            known_indicators={
                'insider_trading': True,
                'false_statements': True,
                'pre_announcement_positioning': True
            },
            sec_release="LR-24984",
            description="Fraud involving false and misleading statements about vehicle capabilities"
        ),
        
        'LUCKIN_COFFEE_2020': EnforcementCase(
            case_name="Luckin Coffee Inc.",
            company_name="Luckin Coffee",
            cik="1767582",
            enforcement_year=2020,
            fraud_type="channel_stuffing",
            period_start=date(2019, 4, 1),
            period_end=date(2019, 12, 31),
            known_indicators={
                'fabricated_revenue': True,
                'channel_stuffing': True,
                'related_party_transactions': True,
                'revenue_inflation_amount': 310000000  # $310M
            },
            sec_release="LR-24928",
            description="$310M+ fabricated sales through fake transactions"
        )
    }
    
    def __init__(self):
        """Initialize validator."""
        self.validation_results = []
    
    def get_case(self, case_id: str) -> Optional[EnforcementCase]:
        """
        Get enforcement case by ID.
        
        Args:
            case_id: Case identifier (e.g., 'ENRON_2001')
            
        Returns:
            EnforcementCase or None if not found
        """
        return self.ENFORCEMENT_CASES.get(case_id)
    
    def validate_detector(
        self,
        case_id: str,
        detector_name: str,
        detector_output: Dict[str, Any],
        expected_detection: bool = True
    ) -> ValidationResult:
        """
        Validate a detector's output against a known enforcement case.
        
        Args:
            case_id: Case identifier
            detector_name: Name of detector being validated
            detector_output: Output from the detector
            expected_detection: Whether detection is expected (default: True)
            
        Returns:
            ValidationResult with pass/fail status
        """
        case = self.get_case(case_id)
        if not case:
            raise ValueError(f"Unknown case ID: {case_id}")
        
        # Check if detector found the fraud
        actual_detection = detector_output.get('detected', False)
        
        # Extract confidence score
        confidence_score = detector_output.get('confidence', 0.0)
        
        # Compare expected vs detected indicators
        expected_indicators = case.known_indicators
        detected_indicators = detector_output.get('indicators', {})
        
        # Determine pass/fail
        passed = (actual_detection == expected_detection)
        
        # If detection was expected, also check confidence threshold
        if expected_detection and actual_detection:
            # For known fraud cases, expect high confidence (> 0.50)
            passed = passed and (confidence_score >= 0.50)
        
        notes = self._generate_validation_notes(
            case,
            expected_detection,
            actual_detection,
            confidence_score,
            expected_indicators,
            detected_indicators
        )
        
        result = ValidationResult(
            case_name=case.case_name,
            detector_name=detector_name,
            expected_detection=expected_detection,
            actual_detection=actual_detection,
            passed=passed,
            confidence_score=confidence_score,
            expected_indicators=expected_indicators,
            detected_indicators=detected_indicators,
            notes=notes
        )
        
        self.validation_results.append(result)
        
        logger.info(f"Validation {case_id} - {detector_name}: {'PASS' if passed else 'FAIL'}")
        
        return result
    
    def _generate_validation_notes(
        self,
        case: EnforcementCase,
        expected: bool,
        actual: bool,
        confidence: float,
        expected_indicators: Dict[str, Any],
        detected_indicators: Dict[str, Any]
    ) -> str:
        """Generate notes about validation result."""
        notes = []
        
        if expected != actual:
            if expected:
                notes.append(f"FAILED: Detector did not identify known fraud case {case.case_name}")
            else:
                notes.append(f"FAILED: Detector incorrectly flagged {case.case_name}")
        else:
            notes.append(f"SUCCESS: Detection result matches expectation")
        
        if expected and actual and confidence < 0.50:
            notes.append(f"WARNING: Low confidence score ({confidence:.2f}) for known fraud case")
        
        # Check indicator alignment
        missing_indicators = []
        for indicator in expected_indicators:
            if indicator not in detected_indicators:
                missing_indicators.append(indicator)
        
        if missing_indicators:
            notes.append(f"Missing expected indicators: {', '.join(missing_indicators)}")
        
        return " | ".join(notes)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all validation results.
        
        Returns:
            Summary statistics
        """
        if not self.validation_results:
            return {
                'total_validations': 0,
                'passed': 0,
                'failed': 0,
                'pass_rate': 0.0
            }
        
        total = len(self.validation_results)
        passed = sum(1 for r in self.validation_results if r.passed)
        failed = total - passed
        
        return {
            'total_validations': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total if total > 0 else 0.0,
            'results': [
                {
                    'case': r.case_name,
                    'detector': r.detector_name,
                    'passed': r.passed,
                    'confidence': r.confidence_score
                }
                for r in self.validation_results
            ]
        }
