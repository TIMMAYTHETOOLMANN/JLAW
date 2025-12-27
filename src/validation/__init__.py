"""
Validation Module
=================

AI-powered validation modules for JLAW forensic analysis.
"""

from .ai_cross_validator import (
    AICrossValidator,
    AICrossValidationReport,
    CrossValidationResult,
    ValidationStatus,
    DetectionPattern
)

__all__ = [
    'AICrossValidator',
    'AICrossValidationReport',
    'CrossValidationResult',
    'ValidationStatus',
    'DetectionPattern'
]
