"""
JLAW Phase 6: Advanced Contradiction Detection
==============================================

Multi-modal contradiction detection across all evidence types.

Components:
- ContradictionDetectionEngine: Master orchestrator
- SemanticContradictionDetector: NLI-based semantic analysis
- NumericalContradictionDetector: Financial/numerical discrepancies
- TemporalContradictionEngine: Enhanced from Phase 4
- EntityContradictionDetector: Entity-level inconsistencies
- SourceContradictionAnalyzer: Cross-source validation
"""

try:
    from .contradiction_engine import ContradictionEngine, Contradiction
    from .semantic_detector import SemanticDetector
    from .numerical_detector import NumericalDetector
    from .entity_detector import EntityDetector
    from .source_analyzer import SourceAnalyzer
    
    # Aliases for backward compatibility
    ContradictionDetectionEngine = ContradictionEngine
    SemanticContradictionDetector = SemanticDetector
    NumericalContradictionDetector = NumericalDetector
    EntityContradictionDetector = EntityDetector
    SourceContradictionAnalyzer = SourceAnalyzer
except ImportError:
    # Fallback for missing modules
    ContradictionEngine = None
    ContradictionDetectionEngine = None

__all__ = [
    'ContradictionEngine',
    'ContradictionDetectionEngine',
    'SemanticDetector',
    'SemanticContradictionDetector',
    'NumericalDetector',
    'NumericalContradictionDetector',
    'EntityDetector',
    'EntityContradictionDetector',
    'SourceAnalyzer',
    'SourceContradictionAnalyzer',
    'Contradiction',
]

__version__ = '6.0.0'
__phase__ = 6

