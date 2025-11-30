"""
JLAW Phase 5: Prosecution Path Builder & Evidence Evaluator
==========================================================

Advanced prosecution strategy and evidence evaluation system.

Components:
- ProsecutionPathBuilder: Case strategy construction
- EvidenceChainAnalyzer: Evidence chain validation
- WitnessGraph: Witness relationship mapping
- BurdenCalculator: Legal burden analysis
- CaseEvaluator: Multi-factor case assessment
"""

try:
    from .prosecution_builder import ProsecutionPathBuilder
    from .evidence_chain import EvidenceChainAnalyzer
    from .witness_graph import WitnessGraph
    from .burden_calculator import BurdenCalculator
    from .case_evaluator import CaseEvaluator
    
    # Aliases for backward compatibility
    BurdenOfProofCalculator = BurdenCalculator
    CaseStrengthEvaluator = CaseEvaluator
    
except ImportError:
    ProsecutionPathBuilder = None
    EvidenceChainAnalyzer = None
    WitnessGraph = None
    BurdenCalculator = None
    CaseEvaluator = None
    BurdenOfProofCalculator = None
    CaseStrengthEvaluator = None

__all__ = [
    'ProsecutionPathBuilder',
    'EvidenceChainAnalyzer',
    'WitnessGraph',
    'BurdenCalculator',
    'CaseEvaluator',
    'BurdenOfProofCalculator',
    'CaseStrengthEvaluator',
]

__version__ = '5.0.0'
__phase__ = 5

