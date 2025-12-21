"""Node 12: Earnings Call Transcript Analyzer."""

from .transcript_analyzer import EarningsCallAnalyzer  # V1 for backward compatibility
from .transcript_analyzer_v2 import (
    TranscriptAnalyzerV2,
    TranscriptAlertV2,
    Node12OutputV2,
    AlertType,
    Severity
)
from .deberta_detector import DeBERTaContradictionDetector, ContradictionResult
from .transcript_source_client import TranscriptSourceClient, TranscriptData
from .contextual_hedging_analyzer import ContextualHedgingAnalyzer, HedgingAnalysis
from .filing_narrative_comparator import FilingNarrativeComparator, NarrativeComparison
from .cross_validator import (
    EarningsCallCrossValidator,
    CrossValidationReport,
    RegFDViolation,
    ViolationType,
    ViolationSeverity,
    StatementMatch
)

__all__ = [
    'EarningsCallAnalyzer',  # V1 export for backward compatibility
    'TranscriptAnalyzerV2',
    'TranscriptAlertV2',
    'Node12OutputV2',
    'AlertType',
    'Severity',
    'DeBERTaContradictionDetector',
    'ContradictionResult',
    'TranscriptSourceClient',
    'TranscriptData',
    'ContextualHedgingAnalyzer',
    'HedgingAnalysis',
    'FilingNarrativeComparator',
    'NarrativeComparison',
    'EarningsCallCrossValidator',
    'CrossValidationReport',
    'RegFDViolation',
    'ViolationType',
    'ViolationSeverity',
    'StatementMatch'
]
