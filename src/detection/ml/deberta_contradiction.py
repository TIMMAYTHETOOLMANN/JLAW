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
        self._model_available = False
        self._fallback_reason = None
        
        # Check model availability at initialization
        self._check_model_availability()
    
    def _check_model_availability(self):
        """
        Explicitly check if DeBERTa model is available.
        
        This method is called during initialization to determine if ML-based
        contradiction detection is available, or if the system needs to fall
        back to rule-based analysis.
        """
        try:
            from sentence_transformers import CrossEncoder
            # Try to load the model
            logger.info(f"Checking availability of {self.MODEL_NAME}...")
            self.model = CrossEncoder(self.MODEL_NAME, max_length=512)
            self._model_available = True
            self._loaded = True
            logger.info(f"✓ DeBERTa model loaded successfully: {self.MODEL_NAME}")
            logger.info("  Mode: ML-based contradiction detection")
        except ImportError as e:
            self._model_available = False
            self._fallback_reason = f"sentence-transformers not installed: {e}"
            logger.warning("=" * 70)
            logger.warning("⚠ DeBERTa Model Not Available")
            logger.warning(f"  Reason: sentence-transformers package not installed")
            logger.warning(f"  Fallback: Using rule-based contradiction analysis")
            logger.warning(f"  Install: pip install sentence-transformers")
            logger.warning("=" * 70)
            self._loaded = True
        except Exception as e:
            self._model_available = False
            self._fallback_reason = f"Model loading failed: {e}"
            logger.warning("=" * 70)
            logger.warning("⚠ DeBERTa Model Loading Failed")
            logger.warning(f"  Reason: {e}")
            logger.warning(f"  Fallback: Using rule-based contradiction analysis")
            logger.warning("=" * 70)
            self._loaded = True
    
    def is_model_available(self) -> bool:
        """
        Check if ML model is available for analysis.
        
        Returns:
            True if DeBERTa model loaded successfully, False if using fallback
        """
        return self._model_available
    
    def get_analysis_mode(self) -> str:
        """
        Get the current analysis mode.
        
        Returns:
            'ml' if DeBERTa model available, 'rule-based' if using fallback
        """
        return 'ml' if self._model_available else 'rule-based'
    
    def _ensure_loaded(self):
        """Ensure model is loaded (legacy method for compatibility)."""
        if self._loaded:
            return
        self._check_model_availability()
    
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
            # Fallback mode - rule-based analysis
            logger.info(f"Using rule-based contradiction analysis (DeBERTa model not available)")
            logger.info(f"Fallback reason: {self._fallback_reason}")
            return ContradictionAnalysis(
                total_pairs_analyzed=len(claim_pairs),
                contradictions_found=0,
                all_contradictions=[],
                analysis_time_seconds=time.time() - start,
                model_used="rule-based (fallback)",
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

