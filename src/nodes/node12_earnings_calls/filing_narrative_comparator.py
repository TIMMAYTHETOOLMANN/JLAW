"""
Filing Narrative Comparator
============================

Compares earnings call narratives against 10-K/10-Q filing narratives
to detect discrepancies and contradictions.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class NarrativeComparison:
    """Result of narrative comparison."""
    topic: str
    call_narrative: str
    filing_narrative: str
    similarity_score: float  # 0.0-1.0
    discrepancy_detected: bool
    discrepancy_type: Optional[str] = None
    explanation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "call_narrative": self.call_narrative[:200] + "...",
            "filing_narrative": self.filing_narrative[:200] + "...",
            "similarity_score": round(self.similarity_score, 2),
            "discrepancy_detected": self.discrepancy_detected,
            "discrepancy_type": self.discrepancy_type,
            "explanation": self.explanation
        }


class FilingNarrativeComparator:
    """
    Compares earnings call narratives with SEC filing narratives.
    
    Analyzes:
    - Revenue/earnings discussion consistency
    - Risk factor mentions
    - Forward-looking statements
    - Material events discussion
    """
    
    # Key topics to compare
    TOPICS = [
        'revenue', 'earnings', 'profit', 'margin',
        'risk', 'outlook', 'guidance', 'operations',
        'competition', 'market', 'growth', 'investment'
    ]
    
    def __init__(self):
        self.logger = logger
    
    def compare(
        self,
        call_text: str,
        filing_text: str
    ) -> List[NarrativeComparison]:
        """
        Compare earnings call with filing.
        
        Args:
            call_text: Earnings call transcript text
            filing_text: 10-K or 10-Q filing text
        
        Returns:
            List of narrative comparisons
        """
        comparisons = []
        
        for topic in self.TOPICS:
            comparison = self._compare_topic(topic, call_text, filing_text)
            if comparison:
                comparisons.append(comparison)
        
        return comparisons
    
    def _compare_topic(
        self,
        topic: str,
        call_text: str,
        filing_text: str
    ) -> Optional[NarrativeComparison]:
        """Compare specific topic between call and filing."""
        # Extract relevant sentences
        call_sentences = self._extract_topic_sentences(topic, call_text)
        filing_sentences = self._extract_topic_sentences(topic, filing_text)
        
        if not call_sentences or not filing_sentences:
            return None
        
        # Join sentences
        call_narrative = " ".join(call_sentences[:3])  # Top 3 sentences
        filing_narrative = " ".join(filing_sentences[:3])
        
        # Calculate similarity (simplified Jaccard similarity)
        similarity = self._calculate_similarity(call_narrative, filing_narrative)
        
        # Detect discrepancies
        discrepancy = similarity < 0.3
        discrepancy_type = None
        explanation = ""
        
        if discrepancy:
            # Check for contradictory language
            if self._has_negative_language(call_narrative) != self._has_negative_language(filing_narrative):
                discrepancy_type = "sentiment_mismatch"
                explanation = "Sentiment differs between call and filing"
            else:
                discrepancy_type = "content_mismatch"
                explanation = "Content significantly differs between call and filing"
        else:
            explanation = "Narratives are consistent"
        
        return NarrativeComparison(
            topic=topic,
            call_narrative=call_narrative,
            filing_narrative=filing_narrative,
            similarity_score=similarity,
            discrepancy_detected=discrepancy,
            discrepancy_type=discrepancy_type,
            explanation=explanation
        )
    
    def _extract_topic_sentences(
        self,
        topic: str,
        text: str
    ) -> List[str]:
        """Extract sentences mentioning topic."""
        sentences = re.split(r'[.!?]+', text)
        relevant = []
        
        for sentence in sentences:
            if topic.lower() in sentence.lower():
                relevant.append(sentence.strip())
        
        return relevant
    
    def _calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """Calculate Jaccard similarity between texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _has_negative_language(self, text: str) -> bool:
        """Check for negative language."""
        negative_words = [
            'decline', 'decrease', 'loss', 'challenge', 'difficult',
            'negative', 'risk', 'concern', 'uncertainty', 'headwind'
        ]
        
        text_lower = text.lower()
        return any(word in text_lower for word in negative_words)
    
    def generate_summary(
        self,
        comparisons: List[NarrativeComparison]
    ) -> Dict[str, Any]:
        """Generate summary of comparisons."""
        total = len(comparisons)
        discrepancies = [c for c in comparisons if c.discrepancy_detected]
        
        return {
            "total_topics": total,
            "discrepancies_found": len(discrepancies),
            "avg_similarity": sum(c.similarity_score for c in comparisons) / total if total > 0 else 0,
            "discrepancy_topics": [c.topic for c in discrepancies],
            "high_risk_discrepancies": [
                c.to_dict() for c in discrepancies
                if c.similarity_score < 0.2
            ]
        }
