"""
DeBERTa Contradiction Detector
===============================

Uses microsoft/deberta-v3-large transformer for semantic contradiction detection
in earnings call transcripts.

Identifies contradictions between:
- Management statements and prior filings
- Different speakers' statements
- Current and historical statements
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers/torch not available. Using mock mode.")


@dataclass
class ContradictionResult:
    """Result of contradiction detection."""
    statement1: str
    statement2: str
    contradiction_score: float  # 0.0-1.0
    is_contradiction: bool
    confidence: float
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement1": self.statement1[:200] + "..." if len(self.statement1) > 200 else self.statement1,
            "statement2": self.statement2[:200] + "..." if len(self.statement2) > 200 else self.statement2,
            "contradiction_score": round(self.contradiction_score, 3),
            "is_contradiction": self.is_contradiction,
            "confidence": round(self.confidence, 3),
            "explanation": self.explanation
        }


class DeBERTaContradictionDetector:
    """
    Contradiction detector using DeBERTa-v3-large.
    
    Uses Natural Language Inference (NLI) to detect contradictions
    between pairs of statements.
    """
    
    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-large",
        threshold: float = 0.7
    ):
        """
        Initialize detector.
        
        Args:
            model_name: HuggingFace model name
            threshold: Confidence threshold for contradiction (default 0.7)
        """
        self.model_name = model_name
        self.threshold = threshold
        self.logger = logger
        
        if TRANSFORMERS_AVAILABLE:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.model.eval()
                self.mock_mode = False
                self.logger.info(f"Loaded DeBERTa model: {model_name}")
            except Exception as e:
                self.logger.warning(f"Could not load model: {e}. Using mock mode.")
                self.mock_mode = True
        else:
            self.mock_mode = True
    
    def detect_contradiction(
        self,
        statement1: str,
        statement2: str
    ) -> ContradictionResult:
        """
        Detect contradiction between two statements.
        
        Args:
            statement1: First statement
            statement2: Second statement
        
        Returns:
            ContradictionResult with analysis
        """
        if self.mock_mode:
            return self._mock_detection(statement1, statement2)
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                statement1,
                statement2,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            # Get model prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=1)
            
            # Extract scores (entailment, neutral, contradiction)
            entail_score = probs[0][0].item()
            neutral_score = probs[0][1].item()
            contradiction_score = probs[0][2].item()
            
            is_contradiction = contradiction_score >= self.threshold
            confidence = contradiction_score
            
            if is_contradiction:
                explanation = f"High contradiction probability: {contradiction_score:.2%}"
            elif neutral_score > 0.5:
                explanation = f"Statements are neutral/unrelated: {neutral_score:.2%}"
            else:
                explanation = f"Statements are consistent/entailed: {entail_score:.2%}"
            
            return ContradictionResult(
                statement1=statement1,
                statement2=statement2,
                contradiction_score=contradiction_score,
                is_contradiction=is_contradiction,
                confidence=confidence,
                explanation=explanation
            )
        
        except Exception as e:
            self.logger.error(f"Error in contradiction detection: {e}")
            return self._mock_detection(statement1, statement2)
    
    def _mock_detection(self, statement1: str, statement2: str) -> ContradictionResult:
        """Mock detection for testing without model."""
        # Simple keyword-based mock detection
        neg_words = ['not', 'no', 'never', 'none', 'neither']
        
        has_negation_s1 = any(word in statement1.lower() for word in neg_words)
        has_negation_s2 = any(word in statement2.lower() for word in neg_words)
        
        # If one has negation and other doesn't, mock contradiction
        mock_score = 0.8 if has_negation_s1 != has_negation_s2 else 0.2
        
        return ContradictionResult(
            statement1=statement1,
            statement2=statement2,
            contradiction_score=mock_score,
            is_contradiction=mock_score >= self.threshold,
            confidence=mock_score,
            explanation="Mock detection (model not loaded)"
        )
    
    def batch_detect(
        self,
        statement_pairs: List[Tuple[str, str]]
    ) -> List[ContradictionResult]:
        """
        Detect contradictions in batch.
        
        Args:
            statement_pairs: List of (statement1, statement2) tuples
        
        Returns:
            List of ContradictionResult objects
        """
        results = []
        for s1, s2 in statement_pairs:
            result = self.detect_contradiction(s1, s2)
            results.append(result)
        return results
    
    def detect_contradictions_in_transcript(
        self,
        statements: List[Dict[str, str]],
        compare_to_filing: Optional[str] = None
    ) -> List[ContradictionResult]:
        """
        Detect contradictions within transcript or against filing.
        
        Args:
            statements: List of statement dicts with 'text' and 'speaker'
            compare_to_filing: Optional filing text to compare against
        
        Returns:
            List of detected contradictions
        """
        contradictions = []
        
        if compare_to_filing:
            # Compare each statement to filing
            for stmt in statements:
                result = self.detect_contradiction(
                    stmt['text'],
                    compare_to_filing[:1000]  # Use excerpt
                )
                if result.is_contradiction:
                    contradictions.append(result)
        else:
            # Compare statements pairwise within transcript
            for i in range(len(statements)):
                for j in range(i + 1, min(i + 5, len(statements))):  # Check next 4 statements
                    result = self.detect_contradiction(
                        statements[i]['text'],
                        statements[j]['text']
                    )
                    if result.is_contradiction:
                        contradictions.append(result)
        
        return contradictions
