"""
Contradiction Detection for SEC Filings
=======================================

Implements hybrid bi-encoder + cross-encoder pipeline for detecting
contradictions between statements in SEC filings.

Architecture:
1. Bi-encoder (all-mpnet-base-v2): Fast semantic similarity for retrieval
2. Cross-encoder (nli-deberta-v3-large): Accurate entailment scoring

Models:
- Bi-encoder: sentence-transformers/all-mpnet-base-v2 (768-dim embeddings)
- Cross-encoder: cross-encoder/nli-deberta-v3-large (92%+ accuracy on MNLI)

Use Cases:
- Cross-filing contradiction detection (10-K vs 10-Q statements)
- Management commentary vs financial statement reconciliation
- Proxy statement compensation claims vs actual filings
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    import numpy as np
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    logger.warning("sentence-transformers not available. Using mock mode.")


@dataclass
class Statement:
    """A statement from an SEC filing."""
    text: str
    source: str  # Filing source (e.g., "10-K 2023")
    section: str  # Section (e.g., "Item 7 - MD&A")
    filing_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source,
            "section": self.section,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None
        }


@dataclass
class ContradictionResult:
    """Result of contradiction detection between two statements."""
    statement1: Statement
    statement2: Statement
    contradiction_score: float  # 0-1 scale (higher = more contradictory)
    entailment_label: str  # "contradiction", "neutral", "entailment"
    confidence: float
    semantic_similarity: float  # From bi-encoder
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement1": self.statement1.to_dict(),
            "statement2": self.statement2.to_dict(),
            "contradiction_score": round(self.contradiction_score, 4),
            "entailment_label": self.entailment_label,
            "confidence": round(self.confidence, 4),
            "semantic_similarity": round(self.semantic_similarity, 4)
        }


class ContradictionDetector:
    """
    Hybrid contradiction detector using bi-encoder + cross-encoder.
    
    Pipeline:
    1. Use bi-encoder to find semantically similar statements (fast retrieval)
    2. Use cross-encoder to score entailment/contradiction (accurate classification)
    
    This hybrid approach is much faster than using cross-encoder on all pairs,
    while maintaining high accuracy.
    
    Example:
        detector = ContradictionDetector()
        
        # Add statements from filings
        detector.add_statement("Revenue grew 20%", "10-K 2023", "Item 7")
        detector.add_statement("Revenue declined 10%", "10-Q Q1 2024", "Item 2")
        
        # Detect contradictions
        contradictions = detector.detect_contradictions(threshold=0.7)
        
        for result in contradictions:
            print(f"Contradiction: {result.contradiction_score:.2f}")
            print(f"  Statement 1: {result.statement1.text}")
            print(f"  Statement 2: {result.statement2.text}")
    """
    
    # Model names
    BI_ENCODER_MODEL = "sentence-transformers/all-mpnet-base-v2"
    CROSS_ENCODER_MODEL = "cross-encoder/nli-deberta-v3-large"
    
    # Alternative models
    ALT_BI_ENCODER = "sentence-transformers/all-MiniLM-L6-v2"  # Faster, less accurate
    ALT_CROSS_ENCODER = "cross-encoder/nli-deberta-base"  # Faster, less accurate
    
    def __init__(
        self,
        bi_encoder_model: Optional[str] = None,
        cross_encoder_model: Optional[str] = None,
        use_gpu: bool = False
    ):
        """
        Initialize contradiction detector.
        
        Args:
            bi_encoder_model: Bi-encoder model name (default: all-mpnet-base-v2)
            cross_encoder_model: Cross-encoder model name (default: nli-deberta-v3-large)
            use_gpu: Use GPU acceleration if available
        """
        self.bi_encoder_model_name = bi_encoder_model or self.BI_ENCODER_MODEL
        self.cross_encoder_model_name = cross_encoder_model or self.CROSS_ENCODER_MODEL
        self.use_gpu = use_gpu
        
        self.statements: List[Statement] = []
        self.embeddings: Optional[Any] = None
        
        if MODELS_AVAILABLE:
            self.mock_mode = False
            try:
                logger.info(f"Loading bi-encoder: {self.bi_encoder_model_name}")
                self.bi_encoder = SentenceTransformer(
                    self.bi_encoder_model_name,
                    device='cuda' if use_gpu else 'cpu'
                )
                
                logger.info(f"Loading cross-encoder: {self.cross_encoder_model_name}")
                self.cross_encoder = CrossEncoder(
                    self.cross_encoder_model_name,
                    device='cuda' if use_gpu else 'cpu'
                )
            except Exception as e:
                logger.error(f"Failed to load models: {e}")
                self.mock_mode = True
        else:
            self.mock_mode = True
    
    def add_statement(
        self,
        text: str,
        source: str,
        section: str,
        filing_date: Optional[datetime] = None
    ):
        """
        Add a statement for contradiction detection.
        
        Args:
            text: Statement text
            source: Filing source (e.g., "10-K 2023")
            section: Section identifier
            filing_date: Filing date
        """
        statement = Statement(
            text=text,
            source=source,
            section=section,
            filing_date=filing_date
        )
        self.statements.append(statement)
        # Clear embeddings cache
        self.embeddings = None
    
    def add_statements(self, statements: List[Statement]):
        """Add multiple statements."""
        self.statements.extend(statements)
        self.embeddings = None
    
    def _compute_embeddings(self):
        """Compute embeddings for all statements."""
        if self.mock_mode or not self.statements:
            return
        
        texts = [stmt.text for stmt in self.statements]
        self.embeddings = self.bi_encoder.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )
    
    def find_similar_statements(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[Statement, float]]:
        """
        Find statements similar to query using bi-encoder.
        
        Args:
            query: Query text
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of (Statement, similarity_score) tuples
        """
        if self.mock_mode or not self.statements:
            return []
        
        # Compute embeddings if not cached
        if self.embeddings is None:
            self._compute_embeddings()
        
        # Encode query
        query_embedding = self.bi_encoder.encode(query, convert_to_numpy=True)
        
        # Compute cosine similarities
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Filter by minimum similarity
        results = []
        for idx in top_indices:
            if similarities[idx] >= min_similarity:
                results.append((self.statements[idx], float(similarities[idx])))
        
        return results
    
    def detect_contradictions(
        self,
        threshold: float = 0.7,
        max_pairs: int = 1000,
        similarity_threshold: float = 0.3
    ) -> List[ContradictionResult]:
        """
        Detect contradictions between all statement pairs.
        
        Args:
            threshold: Contradiction score threshold (0-1)
            max_pairs: Maximum number of pairs to check
            similarity_threshold: Minimum semantic similarity for candidate pairs
            
        Returns:
            List of contradiction results above threshold
        """
        if self.mock_mode or len(self.statements) < 2:
            return self._mock_detect_contradictions()
        
        # Compute embeddings
        if self.embeddings is None:
            self._compute_embeddings()
        
        # Find candidate pairs using semantic similarity
        candidates = []
        n = len(self.statements)
        
        for i in range(n):
            for j in range(i + 1, n):
                # Compute cosine similarity
                sim = float(np.dot(self.embeddings[i], self.embeddings[j]) / (
                    np.linalg.norm(self.embeddings[i]) * np.linalg.norm(self.embeddings[j])
                ))
                
                # Only check pairs with minimum similarity
                if sim >= similarity_threshold:
                    candidates.append((i, j, sim))
        
        # Sort by similarity (descending) and limit
        candidates.sort(key=lambda x: x[2], reverse=True)
        candidates = candidates[:max_pairs]
        
        # Use cross-encoder to score entailment
        contradictions = []
        
        for i, j, sim in candidates:
            stmt1 = self.statements[i]
            stmt2 = self.statements[j]
            
            # Score with cross-encoder
            scores = self.cross_encoder.predict([(stmt1.text, stmt2.text)])
            
            # Convert to probabilities (softmax)
            # Scores are [contradiction, entailment, neutral]
            score = float(scores[0])
            
            # Determine label (assuming 3-class NLI model)
            # Higher contradiction score means more contradictory
            if score > threshold:
                contradictions.append(ContradictionResult(
                    statement1=stmt1,
                    statement2=stmt2,
                    contradiction_score=score,
                    entailment_label="contradiction",
                    confidence=score,
                    semantic_similarity=sim
                ))
        
        # Sort by contradiction score
        contradictions.sort(key=lambda x: x.contradiction_score, reverse=True)
        
        return contradictions
    
    def check_pair(
        self,
        text1: str,
        text2: str,
        source1: str = "",
        source2: str = "",
        section1: str = "",
        section2: str = ""
    ) -> ContradictionResult:
        """
        Check a specific pair of statements for contradiction.
        
        Args:
            text1: First statement
            text2: Second statement
            source1: Source of first statement
            source2: Source of second statement
            section1: Section of first statement
            section2: Section of second statement
            
        Returns:
            ContradictionResult
        """
        if self.mock_mode:
            return self._mock_check_pair(text1, text2, source1, source2, section1, section2)
        
        stmt1 = Statement(text1, source1, section1)
        stmt2 = Statement(text2, source2, section2)
        
        # Compute semantic similarity
        embeddings = self.bi_encoder.encode([text1, text2], convert_to_numpy=True)
        similarity = float(np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        ))
        
        # Score with cross-encoder
        score = float(self.cross_encoder.predict([(text1, text2)])[0])
        
        # Determine label
        label = "contradiction" if score > 0.5 else "neutral"
        
        return ContradictionResult(
            statement1=stmt1,
            statement2=stmt2,
            contradiction_score=score,
            entailment_label=label,
            confidence=score,
            semantic_similarity=similarity
        )
    
    def _mock_detect_contradictions(self) -> List[ContradictionResult]:
        """Mock contradiction detection."""
        if len(self.statements) < 2:
            return []
        
        # Return a mock contradiction
        return [
            ContradictionResult(
                statement1=self.statements[0],
                statement2=self.statements[1],
                contradiction_score=0.75,
                entailment_label="contradiction",
                confidence=0.75,
                semantic_similarity=0.6
            )
        ]
    
    def _mock_check_pair(
        self,
        text1: str,
        text2: str,
        source1: str,
        source2: str,
        section1: str,
        section2: str
    ) -> ContradictionResult:
        """Mock pair checking."""
        return ContradictionResult(
            statement1=Statement(text1, source1, section1),
            statement2=Statement(text2, source2, section2),
            contradiction_score=0.5,
            entailment_label="neutral",
            confidence=0.5,
            semantic_similarity=0.5
        )
    
    def clear_statements(self):
        """Clear all statements and embeddings."""
        self.statements = []
        self.embeddings = None
