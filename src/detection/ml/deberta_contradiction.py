"""
DeBERTa-v3 Contradiction Detection Engine
==========================================

NLI-based contradiction detection for SEC documents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class ContradictionSeverity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class ContradictionResult:
    premise: str
    hypothesis: str
    premise_source: str
    hypothesis_source: str
    confidence: float
    severity: ContradictionSeverity
    label: str
    evidence_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "premise": self.premise[:200],
            "hypothesis": self.hypothesis[:200],
            "confidence": round(self.confidence, 4),
            "severity": self.severity.value,
            "label": self.label
        }


@dataclass
class ContradictionAnalysis:
    total_pairs_analyzed: int
    contradictions_found: int
    all_contradictions: List[ContradictionResult]
    analysis_time_seconds: float
    model_used: str
    threshold_used: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_pairs": self.total_pairs_analyzed,
                "contradictions": self.contradictions_found
            },
            "model": self.model_used,
            "threshold": self.threshold_used
        }


class ContradictionEngine:
    """DeBERTa-v3 contradiction detection."""
    
    MODEL_NAME = "cross-encoder/nli-deberta-v3-large"
    
    def __init__(self, threshold: float = 0.85, use_gpu: bool = True, batch_size: int = 8):
        self.threshold = threshold
        self.use_gpu = use_gpu
        self.batch_size = batch_size
        self.model = None
        self._loaded = False
    
    def _ensure_loaded(self):
        if self._loaded:
            return
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.MODEL_NAME, max_length=512)
            self._loaded = True
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback")
            self._loaded = True
    
    def detect_contradictions(
        self,
        claim_pairs: List[Tuple[str, str, str, str]],
        min_confidence: Optional[float] = None
    ) -> ContradictionAnalysis:
        import time
        start = time.time()
        
        self._ensure_loaded()
        threshold = min_confidence or self.threshold
        contradictions = []
        
        if self.model is None:
            # Fallback mode
            return ContradictionAnalysis(
                total_pairs_analyzed=len(claim_pairs),
                contradictions_found=0,
                all_contradictions=[],
                analysis_time_seconds=time.time() - start,
                model_used="fallback",
                threshold_used=threshold
            )
        
        text_pairs = [(p[0], p[1]) for p in claim_pairs]
        scores = self.model.predict(text_pairs)
        
        for i, (score, pair) in enumerate(zip(scores, claim_pairs)):
            pred_idx = score.argmax()
            conf = float(score[pred_idx])
            label = ['contradiction', 'entailment', 'neutral'][pred_idx]
            
            if label == 'contradiction' and conf >= threshold:
                contradictions.append(ContradictionResult(
                    premise=pair[0],
                    hypothesis=pair[1],
                    premise_source=pair[2],
                    hypothesis_source=pair[3],
                    confidence=conf,
                    severity=ContradictionSeverity.HIGH if conf > 0.9 else ContradictionSeverity.MEDIUM,
                    label=label,
                    evidence_hash=hashlib.sha256(f"{pair[0]}|||{pair[1]}".encode()).hexdigest()
                ))
        
        return ContradictionAnalysis(
            total_pairs_analyzed=len(claim_pairs),
            contradictions_found=len(contradictions),
            all_contradictions=contradictions,
            analysis_time_seconds=time.time() - start,
            model_used=self.MODEL_NAME,
            threshold_used=threshold
        )

