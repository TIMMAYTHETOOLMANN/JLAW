"""
Enhanced Contradiction Detector - Priority 1 Enhancement
Two-stage NLI pipeline: bi-encoder retrieval + cross-encoder reranking.
Achieves 92.38% SNLI accuracy per cross-encoder benchmarks.

Integration: Replaces/enhances existing contradiction detection in advanced_forensic_analytics.py
Backward Compatible: Falls back to existing methods if models unavailable
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import hashlib

# Core dependencies with graceful fallbacks
try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError, Exception):
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    CrossEncoder = None

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch
    TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError, Exception):
    TRANSFORMERS_AVAILABLE = False
    AutoModelForSequenceClassification = None
    AutoTokenizer = None
    torch = None

# JLAW core imports
from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel, ForensicBlock
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedContradiction:
    """Enhanced contradiction detection result with provenance."""
    claim1: str
    claim2: str
    contradiction_score: float
    confidence_level: str  # HIGH (>0.90), MEDIUM (0.80-0.90), LOW (<0.80)
    detection_method: str  # 'DeBERTa-v3', 'BERT', 'Ensemble'
    claim1_source: Optional[str] = None
    claim2_source: Optional[str] = None
    claim1_position: Optional[int] = None
    claim2_position: Optional[int] = None
    entailment_score: Optional[float] = None
    neutral_score: Optional[float] = None
    explanation: Optional[str] = None
    evidence_hash: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ContradictionAnalysisResult:
    """Complete contradiction analysis for a document."""
    document_id: str
    cik: str
    filing_type: str
    total_claims_analyzed: int
    contradictions_detected: List[EnhancedContradiction]
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    overall_risk_score: float
    analysis_method: str
    processing_time_seconds: float
    evidence_chain_hash: str


class EnhancedContradictionDetector:
    """
    Two-stage NLI pipeline for contradiction detection.
    
    Stage 1: Bi-encoder (all-mpnet-base-v2) for fast candidate retrieval
    Stage 2: Cross-encoder (DeBERTa-v3-base) for precision reranking
    
    Accuracy Target: 92%+ on SEC filing contradiction detection
    Precision Target: 88%+ (reduced false positives)
    Recall Target: 90%+ (maintained detection coverage)
    """
    
    # Model configurations
    BI_ENCODER_MODEL = 'all-mpnet-base-v2'
    CROSS_ENCODER_MODEL = 'cross-encoder/nli-deberta-v3-base'
    FINBERT_MODEL = 'ProsusAI/finbert'
    
    # Threshold configurations
    CONTRADICTION_THRESHOLD_HIGH = 0.90
    CONTRADICTION_THRESHOLD_MEDIUM = 0.80
    CONTRADICTION_THRESHOLD_LOW = 0.70
    ENTAILMENT_THRESHOLD = 0.80
    
    # Performance parameters
    DEFAULT_TOP_K = 100
    MAX_BATCH_SIZE = 32
    
    def __init__(
        self,
        use_finbert: bool = False,
        use_gpu: bool = True,
        fallback_enabled: bool = True
    ):
        """
        Initialize enhanced contradiction detector.
        
        Args:
            use_finbert: Enable FinBERT domain-specific model
            use_gpu: Use GPU acceleration if available
            fallback_enabled: Fall back to existing methods if models fail
        """
        self.use_finbert = use_finbert
        self.use_gpu = use_gpu and torch and torch.cuda.is_available()
        self.fallback_enabled = fallback_enabled
        
        self.logger = logging.getLogger("EnhancedContradictionDetector")
        
        # Initialize models
        self.bi_encoder = None
        self.cross_encoder = None
        self.finbert_model = None
        self.finbert_tokenizer = None
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all AI models with graceful fallback."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            self.logger.warning("⚠️ SentenceTransformers not available - install: pip install sentence-transformers")
            if not self.fallback_enabled:
                raise ImportError("SentenceTransformers required but not available")
            return
        
        try:
            # Stage 1: Bi-encoder for fast retrieval
            self.logger.info(f"Loading bi-encoder: {self.BI_ENCODER_MODEL}")
            self.bi_encoder = SentenceTransformer(self.BI_ENCODER_MODEL)
            if self.use_gpu:
                self.bi_encoder = self.bi_encoder.to('cuda')
            self.logger.info("✅ Bi-encoder loaded successfully")
            
            # Stage 2: Cross-encoder for precision reranking
            self.logger.info(f"Loading cross-encoder: {self.CROSS_ENCODER_MODEL}")
            self.cross_encoder = CrossEncoder(self.CROSS_ENCODER_MODEL)
            self.logger.info("✅ Cross-encoder (DeBERTa-v3) loaded successfully")
            
            # Optional: FinBERT for domain-specific analysis
            if self.use_finbert and TRANSFORMERS_AVAILABLE:
                try:
                    self.logger.info(f"Loading FinBERT: {self.FINBERT_MODEL}")
                    self.finbert_tokenizer = AutoTokenizer.from_pretrained(self.FINBERT_MODEL)
                    self.finbert_model = AutoModelForSequenceClassification.from_pretrained(
                        self.FINBERT_MODEL
                    )
                    if self.use_gpu:
                        self.finbert_model = self.finbert_model.to('cuda')
                    self.logger.info("✅ FinBERT loaded successfully")
                except Exception as e:
                    self.logger.warning(f"⚠️ FinBERT initialization failed: {e}")
        
        except Exception as e:
            self.logger.error(f"❌ Model initialization failed: {e}")
            if not self.fallback_enabled:
                raise
    
    async def detect_contradictions(
        self,
        claims: List[str],
        document_context: Optional[Dict[str, Any]] = None,
        top_k: int = None
    ) -> List[EnhancedContradiction]:
        """
        Detect contradictions using two-stage pipeline.
        
        Args:
            claims: List of extracted claims from document
            document_context: Optional metadata (CIK, filing_type, etc.)
            top_k: Number of candidates to retrieve in stage 1
        
        Returns:
            List of detected contradictions with confidence scores
        """
        if not claims or len(claims) < 2:
            return []
        
        if top_k is None:
            top_k = min(self.DEFAULT_TOP_K, len(claims) * len(claims))
        
        # Check if models are available
        if self.bi_encoder is None or self.cross_encoder is None:
            if self.fallback_enabled:
                self.logger.warning("⚠️ Enhanced models not available, using fallback method")
                return await self._fallback_detection(claims)
            else:
                raise RuntimeError("Enhanced models not initialized")
        
        try:
            # Stage 1: Bi-encoder fast retrieval
            candidates = await self._retrieve_candidates(claims, top_k)
            
            # Stage 2: Cross-encoder precision reranking
            contradictions = await self._rerank_with_cross_encoder(
                claims,
                candidates,
                document_context
            )
            
            # Optional: FinBERT domain-specific scoring
            if self.finbert_model is not None:
                contradictions = await self._enhance_with_finbert(contradictions)
            
            return contradictions
        
        except Exception as e:
            self.logger.error(f"❌ Contradiction detection failed: {e}")
            if self.fallback_enabled:
                return await self._fallback_detection(claims)
            raise
    
    async def _retrieve_candidates(
        self,
        claims: List[str],
        top_k: int
    ) -> List[Tuple[int, int, float]]:
        """
        Stage 1: Fast candidate retrieval using bi-encoder cosine similarity.
        
        Returns: List of (claim1_idx, claim2_idx, similarity_score) tuples
        """
        self.logger.info(f"Stage 1: Encoding {len(claims)} claims with bi-encoder")
        
        # Encode all claims
        embeddings = self.bi_encoder.encode(
            claims,
            convert_to_tensor=True,
            show_progress_bar=False
        )
        
        # Compute pairwise cosine similarities
        from sklearn.metrics.pairwise import cosine_similarity
        
        if self.use_gpu and torch:
            # GPU-accelerated similarity computation
            similarities = torch.mm(embeddings, embeddings.t())
            similarities = similarities.cpu().numpy()
        else:
            # CPU fallback
            embeddings_np = embeddings.cpu().numpy() if torch else embeddings
            similarities = cosine_similarity(embeddings_np)
        
        # Extract top-k candidates (excluding self-comparisons)
        candidates = []
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                similarity = float(similarities[i][j])
                candidates.append((i, j, similarity))
        
        # Sort by similarity and take top-k
        candidates.sort(key=lambda x: abs(x[2]), reverse=True)
        candidates = candidates[:top_k]
        
        self.logger.info(f"Stage 1 complete: Retrieved {len(candidates)} candidates")
        return candidates
    
    async def _rerank_with_cross_encoder(
        self,
        claims: List[str],
        candidates: List[Tuple[int, int, float]],
        document_context: Optional[Dict[str, Any]]
    ) -> List[EnhancedContradiction]:
        """
        Stage 2: Precision reranking with cross-encoder (DeBERTa-v3).
        
        Cross-encoder performs full attention between claim pairs for
        accurate contradiction classification.
        """
        self.logger.info(f"Stage 2: Reranking {len(candidates)} candidates with DeBERTa-v3")
        
        contradictions = []
        
        # Batch process candidates
        for i in range(0, len(candidates), self.MAX_BATCH_SIZE):
            batch = candidates[i:i + self.MAX_BATCH_SIZE]
            
            # Prepare claim pairs for cross-encoder
            pairs = [
                [claims[c[0]], claims[c[1]]]
                for c in batch
            ]
            
            # Cross-encoder prediction
            # Returns: [contradiction_prob, entailment_prob, neutral_prob]
            scores = self.cross_encoder.predict(pairs)
            
            # Process results
            for (idx1, idx2, bi_sim), score_set in zip(batch, scores):
                # Handle different score formats
                if isinstance(score_set, (list, tuple, np.ndarray)):
                    if len(score_set) >= 3:
                        contradiction_prob = float(score_set[0])
                        entailment_prob = float(score_set[1])
                        neutral_prob = float(score_set[2])
                    else:
                        contradiction_prob = float(score_set[0])
                        entailment_prob = None
                        neutral_prob = None
                else:
                    contradiction_prob = float(score_set)
                    entailment_prob = None
                    neutral_prob = None
                
                # Apply thresholds
                if contradiction_prob >= self.CONTRADICTION_THRESHOLD_LOW:
                    # Determine confidence level
                    if contradiction_prob >= self.CONTRADICTION_THRESHOLD_HIGH:
                        confidence = "HIGH"
                    elif contradiction_prob >= self.CONTRADICTION_THRESHOLD_MEDIUM:
                        confidence = "MEDIUM"
                    else:
                        confidence = "LOW"
                    
                    # Generate evidence hash
                    evidence_content = f"{claims[idx1]}||{claims[idx2]}||{contradiction_prob}"
                    evidence_hash = hashlib.sha256(evidence_content.encode()).hexdigest()
                    
                    # Create explanation
                    explanation = self._generate_explanation(
                        claims[idx1],
                        claims[idx2],
                        contradiction_prob,
                        entailment_prob,
                        neutral_prob
                    )
                    
                    contradictions.append(EnhancedContradiction(
                        claim1=claims[idx1],
                        claim2=claims[idx2],
                        contradiction_score=contradiction_prob,
                        confidence_level=confidence,
                        detection_method='DeBERTa-v3',
                        claim1_position=idx1,
                        claim2_position=idx2,
                        entailment_score=entailment_prob,
                        neutral_score=neutral_prob,
                        explanation=explanation,
                        evidence_hash=evidence_hash,
                        claim1_source=document_context.get('document_id') if document_context else None,
                        claim2_source=document_context.get('document_id') if document_context else None
                    ))
        
        self.logger.info(f"Stage 2 complete: Detected {len(contradictions)} contradictions")
        return contradictions
    
    async def _enhance_with_finbert(
        self,
        contradictions: List[EnhancedContradiction]
    ) -> List[EnhancedContradiction]:
        """
        Optional: Enhance contradiction scores with FinBERT domain knowledge.
        """
        if not self.finbert_model:
            return contradictions
        
        self.logger.info("Enhancing with FinBERT domain-specific scoring")
        
        # Process each contradiction with FinBERT
        for contradiction in contradictions:
            try:
                # Tokenize claim pair
                inputs = self.finbert_tokenizer(
                    contradiction.claim1,
                    contradiction.claim2,
                    return_tensors='pt',
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                
                if self.use_gpu:
                    inputs = {k: v.to('cuda') for k, v in inputs.items()}
                
                # Get FinBERT prediction
                with torch.no_grad():
                    outputs = self.finbert_model(**inputs)
                    finbert_score = torch.softmax(outputs.logits, dim=1)[0][0].item()
                
                # Weighted combination: 60% DeBERTa + 40% FinBERT
                combined_score = (
                    0.60 * contradiction.contradiction_score +
                    0.40 * finbert_score
                )
                
                contradiction.contradiction_score = combined_score
                contradiction.detection_method = 'DeBERTa-v3+FinBERT'
            
            except Exception as e:
                self.logger.warning(f"FinBERT enhancement failed for contradiction: {e}")
                continue
        
        return contradictions
    
    def _generate_explanation(
        self,
        claim1: str,
        claim2: str,
        contradiction_prob: float,
        entailment_prob: Optional[float],
        neutral_prob: Optional[float]
    ) -> str:
        """Generate human-readable explanation of contradiction."""
        explanation = f"Contradiction detected with {contradiction_prob:.1%} confidence. "
        
        if entailment_prob is not None and neutral_prob is not None:
            explanation += (
                f"The claims directly contradict each other "
                f"(contradiction: {contradiction_prob:.1%}, "
                f"entailment: {entailment_prob:.1%}, "
                f"neutral: {neutral_prob:.1%}). "
            )
        
        # Truncate claims for readability
        claim1_short = claim1[:100] + "..." if len(claim1) > 100 else claim1
        claim2_short = claim2[:100] + "..." if len(claim2) > 100 else claim2
        
        explanation += f"Claim 1: '{claim1_short}' vs. Claim 2: '{claim2_short}'"
        
        return explanation
    
    async def _fallback_detection(
        self,
        claims: List[str]
    ) -> List[EnhancedContradiction]:
        """
        Fallback to basic similarity-based detection if enhanced models unavailable.
        """
        self.logger.info("Using fallback contradiction detection method")
        
        # Simple keyword-based contradiction detection
        contradictions = []
        
        # Common contradiction patterns
        contradiction_patterns = [
            ('increase', 'decrease'),
            ('profit', 'loss'),
            ('growth', 'decline'),
            ('improve', 'deteriorate'),
            ('strong', 'weak'),
            ('positive', 'negative'),
        ]
        
        for i, claim1 in enumerate(claims):
            for j, claim2 in enumerate(claims[i+1:], start=i+1):
                claim1_lower = claim1.lower()
                claim2_lower = claim2.lower()
                
                for word1, word2 in contradiction_patterns:
                    if (word1 in claim1_lower and word2 in claim2_lower) or \
                       (word2 in claim1_lower and word1 in claim2_lower):
                        
                        evidence_content = f"{claim1}||{claim2}||fallback"
                        evidence_hash = hashlib.sha256(evidence_content.encode()).hexdigest()
                        
                        contradictions.append(EnhancedContradiction(
                            claim1=claim1,
                            claim2=claim2,
                            contradiction_score=0.75,  # Conservative score for fallback
                            confidence_level="MEDIUM",
                            detection_method='Fallback-Pattern',
                            claim1_position=i,
                            claim2_position=j,
                            explanation=f"Pattern-based detection: '{word1}' vs '{word2}'",
                            evidence_hash=evidence_hash
                        ))
        
        return contradictions
    
    async def analyze_document(
        self,
        document_id: str,
        cik: str,
        filing_type: str,
        claims: List[str],
        hash_chain: Optional[ForensicHashChain] = None
    ) -> ContradictionAnalysisResult:
        """
        Complete contradiction analysis for a document with integrity preservation.
        
        Args:
            document_id: Unique document identifier
            cik: Company CIK
            filing_type: SEC filing type
            claims: Extracted claims from document
            hash_chain: Optional forensic hash chain for evidence integrity
        
        Returns:
            Complete analysis result with chain of custody
        """
        import time
        start_time = time.time()
        
        self.logger.info(f"Analyzing document {document_id} ({len(claims)} claims)")
        
        # Detect contradictions
        document_context = {
            'document_id': document_id,
            'cik': cik,
            'filing_type': filing_type
        }
        
        contradictions = await self.detect_contradictions(
            claims,
            document_context=document_context
        )
        
        # Calculate statistics
        high_conf = sum(1 for c in contradictions if c.confidence_level == "HIGH")
        medium_conf = sum(1 for c in contradictions if c.confidence_level == "MEDIUM")
        low_conf = sum(1 for c in contradictions if c.confidence_level == "LOW")
        
        # Calculate overall risk score (0.0 - 1.0)
        if contradictions:
            risk_score = (
                high_conf * 1.0 +
                medium_conf * 0.6 +
                low_conf * 0.3
            ) / len(claims)
            risk_score = min(risk_score, 1.0)
        else:
            risk_score = 0.0
        
        # Generate evidence chain hash
        evidence_content = f"{document_id}||{cik}||{len(contradictions)}||{risk_score}"
        evidence_chain_hash = hashlib.sha256(evidence_content.encode()).hexdigest()
        
        # Store in hash chain if provided
        if hash_chain:
            try:
                hash_chain.add_block(
                    data={
                        'analysis_type': 'contradiction_detection',
                        'document_id': document_id,
                        'contradictions_count': len(contradictions),
                        'risk_score': risk_score
                    },
                    integrity_level=IntegrityLevel.CRITICAL
                )
            except Exception as e:
                self.logger.warning(f"Failed to add to hash chain: {e}")
        
        processing_time = time.time() - start_time
        
        result = ContradictionAnalysisResult(
            document_id=document_id,
            cik=cik,
            filing_type=filing_type,
            total_claims_analyzed=len(claims),
            contradictions_detected=contradictions,
            high_confidence_count=high_conf,
            medium_confidence_count=medium_conf,
            low_confidence_count=low_conf,
            overall_risk_score=risk_score,
            analysis_method='Enhanced-DeBERTa-v3' if self.cross_encoder else 'Fallback',
            processing_time_seconds=processing_time,
            evidence_chain_hash=evidence_chain_hash
        )
        
        self.logger.info(
            f"Analysis complete: {len(contradictions)} contradictions "
            f"(HIGH: {high_conf}, MEDIUM: {medium_conf}, LOW: {low_conf}) "
            f"Risk Score: {risk_score:.3f} in {processing_time:.2f}s"
        )
        
        return result


# Integration helper for existing JLAW system
async def integrate_enhanced_detector_with_existing_system(
    analyzer_instance,
    document_text: str,
    cik: str,
    filing_type: str
) -> Dict[str, Any]:
    """
    Integration helper to use enhanced detector with existing JLAW system.
    
    Args:
        analyzer_instance: Existing AdvancedForensicAnalyzer instance
        document_text: Full document text
        cik: Company CIK
        filing_type: Filing type
    
    Returns:
        Enhanced analysis results compatible with existing system
    """
    # Extract claims from document (reuse existing extraction)
    # This would integrate with existing claim extraction logic
    claims = []  # Placeholder - would use existing extraction
    
    # Initialize enhanced detector
    detector = EnhancedContradictionDetector(
        use_finbert=True,
        use_gpu=True,
        fallback_enabled=True
    )
    
    # Run enhanced analysis
    result = await detector.analyze_document(
        document_id=f"SEC-{filing_type}-{cik}",
        cik=cik,
        filing_type=filing_type,
        claims=claims
    )
    
    return {
        'contradictions': [
            {
                'claim1': c.claim1,
                'claim2': c.claim2,
                'score': c.contradiction_score,
                'confidence': c.confidence_level,
                'method': c.detection_method,
                'explanation': c.explanation
            }
            for c in result.contradictions_detected
        ],
        'risk_score': result.overall_risk_score,
        'processing_time': result.processing_time_seconds,
        'evidence_hash': result.evidence_chain_hash
    }

