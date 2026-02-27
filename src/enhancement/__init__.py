"""
JLAW Forensic Dossier Enhancement Protocol v5.0.0
Codename: APEX-VALUATION

Resolves 23 critical deficiencies identified via forensic output audit.
"""

from src.enhancement.economic_benefit_engine import EconomicBenefitValuationEngine
from src.enhancement.severity_aggregator import SeverityAggregator
from src.enhancement.violation_deduplicator import ViolationDeduplicator
from src.enhancement.sox_evidence_sanitizer import SOXEvidenceSanitizer
from src.enhancement.fsl_recalibration import FSLRecalibrationEngine
from src.enhancement.pattern_narrative import PatternNarrativeSynthesizer
from src.enhancement.penalty_calculator import PenaltyExposureCalculator
from src.enhancement.temporal_recovery import TemporalAnalysisRecovery
from src.enhancement.merkle_tree import MerkleTreeBuilder
from src.enhancement.orchestrator import JLAWEnhancementOrchestrator

__all__ = [
    'EconomicBenefitValuationEngine',
    'SeverityAggregator',
    'ViolationDeduplicator',
    'SOXEvidenceSanitizer',
    'FSLRecalibrationEngine',
    'PatternNarrativeSynthesizer',
    'PenaltyExposureCalculator',
    'TemporalAnalysisRecovery',
    'MerkleTreeBuilder',
    'JLAWEnhancementOrchestrator',
]
