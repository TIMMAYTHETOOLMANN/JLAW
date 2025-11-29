"""
JLAW Phase 5: Prosecution Path Builder & Evidence Evaluator
==========================================================

Advanced prosecution strategy and evidence evaluation system.

Components:
- ProsecutionPathBuilder: Case strategy construction
- EvidenceChainAnalyzer: Evidence chain validation
- WitnessGraph: Witness relationship mapping
- BurdenOfProofCalculator: Legal burden analysis
- CaseStrengthEvaluator: Multi-factor case assessment
- ProbabilityOfConvictionEstimator: ML-based prediction
"""

from .prosecution_builder import ProsecutionPathBuilder
from .evidence_chain import EvidenceChainAnalyzer
from .witness_graph import WitnessGraph
from .burden_calculator import BurdenOfProofCalculator
from .case_evaluator import CaseStrengthEvaluator

__all__ = [
    'ProsecutionPathBuilder',
    'EvidenceChainAnalyzer',
    'WitnessGraph',
    'BurdenOfProofCalculator',
    'CaseStrengthEvaluator',
]

__version__ = '5.0.0'
__phase__ = 5

