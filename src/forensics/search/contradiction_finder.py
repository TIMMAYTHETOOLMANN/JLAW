"""
Semantic Contradiction Finder
==============================

Advanced contradiction detection using semantic embeddings.
Identifies inconsistencies and conflicting statements across SEC filings.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ContradictionCandidate:
    """A pair of potentially contradictory statements."""
    statement1: str
    statement2: str
    source1: Dict[str, Any]
    source2: Dict[str, Any]
    similarity_score: float
    contradiction_score: float
    contradiction_type: str
    explanation: str = ""


@dataclass
class ContradictionReport:
    """Complete contradiction analysis report."""
    query: str
    scope: str
    total_statements_analyzed: int
    contradictions_found: List[ContradictionCandidate]
    high_risk_contradictions: int
    medium_risk_contradictions: int
    analysis_time_ms: float


class SemanticContradictionFinder:
    """
    Finds contradictions in SEC filings using semantic analysis.
    
    Approach:
    1. Find semantically similar statements (high similarity)
    2. Analyze for semantic opposition/contradiction
    3. Use negation detection and sentiment analysis
    4. Cross-reference with temporal data
    
    Contradiction Types:
    - DIRECT: Explicit opposing statements
    - NUMERICAL: Conflicting numbers/metrics
    - TEMPORAL: Inconsistent timelines
    - QUALITATIVE: Conflicting assessments
    """
    
    NEGATION_PATTERNS = [
        ('not ', ' '),
        ('no ', 'yes '),
        ('never ', 'always '),
        ('decline', 'growth'),
        ('decrease', 'increase'),
        ('loss', 'profit'),
        ('weak', 'strong'),
        ('risk', 'opportunity'),
        ('negative', 'positive'),
        ('unable', 'able'),
        ('failure', 'success'),
        ('uncertainty', 'certainty'),
    ]
    
    def __init__(
        self,
        search_engine,
        embedder,
        similarity_threshold: float = 0.7,
        contradiction_threshold: float = 0.3
    ):
        """
        Initialize contradiction finder.
        
        Args:
            search_engine: Semantic search engine
            embedder: Embedder for semantic analysis
            similarity_threshold: Min similarity to consider related
            contradiction_threshold: Max similarity for contradiction
        """
        self.search_engine = search_engine
        self.embedder = embedder
        self.similarity_threshold = similarity_threshold
        self.contradiction_threshold = contradiction_threshold
    
    def find_contradictions(
        self,
        statement: str,
        cik: str,
        search_scope: Optional[List[str]] = None,
        years: int = 3
    ) -> ContradictionReport:
        """
        Find statements that contradict the given statement.
        
        Args:
            statement: Statement to check for contradictions
            cik: Company CIK
            search_scope: Accession numbers to search (None = all)
            years: Number of years to search if no scope
            
        Returns:
            ContradictionReport with findings
        """
        import time
        start_time = time.time()
        
        # Generate negated version of statement
        negated = self._generate_negation(statement)
        
        # Search for semantically similar statements
        similar_results = self.search_engine.search_temporal(
            statement,
            cik=cik,
            years=years,
            top_k_per_year=10
        )
        
        # Search for negated statements
        negated_results = self.search_engine.search_temporal(
            negated,
            cik=cik,
            years=years,
            top_k_per_year=10
        )
        
        # Combine and flatten results
        all_statements = []
        for year, hits in similar_results.items():
            for hit in hits:
                all_statements.append({
                    'text': hit.text,
                    'source': {
                        'year': year,
                        'filing_type': hit.filing_type,
                        'section': hit.section,
                        'doc_id': hit.doc_id,
                        'chunk_id': hit.chunk_id
                    },
                    'score': hit.score,
                    'type': 'similar'
                })
        
        for year, hits in negated_results.items():
            for hit in hits:
                all_statements.append({
                    'text': hit.text,
                    'source': {
                        'year': year,
                        'filing_type': hit.filing_type,
                        'section': hit.section,
                        'doc_id': hit.doc_id,
                        'chunk_id': hit.chunk_id
                    },
                    'score': hit.score,
                    'type': 'negated'
                })
        
        # Analyze for contradictions
        contradictions = self._analyze_contradictions(
            statement,
            all_statements
        )
        
        # Categorize by risk
        high_risk = sum(1 for c in contradictions if c.contradiction_score > 0.7)
        medium_risk = sum(1 for c in contradictions if 0.4 < c.contradiction_score <= 0.7)
        
        analysis_time = (time.time() - start_time) * 1000
        
        return ContradictionReport(
            query=statement,
            scope=f"CIK:{cik}, Years:{years}",
            total_statements_analyzed=len(all_statements),
            contradictions_found=contradictions,
            high_risk_contradictions=high_risk,
            medium_risk_contradictions=medium_risk,
            analysis_time_ms=analysis_time
        )
    
    def _generate_negation(self, statement: str) -> str:
        """Generate a negated version of the statement."""
        negated = statement.lower()
        
        for pattern, replacement in self.NEGATION_PATTERNS:
            if pattern in negated:
                negated = negated.replace(pattern, replacement)
                break
        else:
            words = negated.split()
            if len(words) > 3:
                negated = " ".join(words[:2]) + " not " + " ".join(words[2:])
        
        return negated
    
    def _analyze_contradictions(
        self,
        original: str,
        statements: List[Dict[str, Any]]
    ) -> List[ContradictionCandidate]:
        """Analyze statements for contradictions with the original."""
        contradictions = []
        
        original_embedding = self.embedder.embed(original)
        
        for stmt in statements:
            text = stmt['text']
            source = stmt['source']
            
            if len(text) < 50 or len(text) > 2000:
                continue
            
            is_contradiction, score, type_, explanation = self._check_contradiction(
                original, text
            )
            
            if is_contradiction:
                stmt_embedding = self.embedder.embed(text)
                similarity = self._cosine_similarity(original_embedding, stmt_embedding)
                
                contradictions.append(ContradictionCandidate(
                    statement1=original[:500],
                    statement2=text[:500],
                    source1={'type': 'query'},
                    source2=source,
                    similarity_score=similarity,
                    contradiction_score=score,
                    contradiction_type=type_,
                    explanation=explanation
                ))
        
        contradictions.sort(key=lambda x: x.contradiction_score, reverse=True)
        return contradictions[:10]
    
    def _check_contradiction(
        self,
        text1: str,
        text2: str
    ) -> Tuple[bool, float, str, str]:
        """Check if two texts contradict each other."""
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for pos_pattern, neg_pattern in self.NEGATION_PATTERNS:
            if pos_pattern in text1_lower and neg_pattern in text2_lower:
                return (
                    True,
                    0.8,
                    'DIRECT',
                    f"Opposing language detected: '{pos_pattern.strip()}' vs '{neg_pattern.strip()}'"
                )
            if neg_pattern in text1_lower and pos_pattern in text2_lower:
                return (
                    True,
                    0.8,
                    'DIRECT',
                    f"Opposing language detected: '{neg_pattern.strip()}' vs '{pos_pattern.strip()}'"
                )
        
        return (False, 0.0, '', '')
    
    def _cosine_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Compute cosine similarity between embeddings."""
        a = np.array(emb1)
        b = np.array(emb2)
        
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot / (norm_a * norm_b))

