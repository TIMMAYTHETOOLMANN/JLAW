"""
Hedging Language Detection
==========================

Detects hedging language in SEC filings using Loughran-McDonald dictionary
and modal verb patterns.

Hedging language indicates uncertainty or lack of commitment:
- Modal verbs: "may", "might", "could", "should", "would"
- Uncertainty words: "approximately", "estimated", "believe", "expect"
- Qualifiers: "substantially", "materially", "generally"

Academic Reference: Loughran, T., & McDonald, B. (2011)
"When is a liability not a liability? Textual analysis, dictionaries,
and 10-Ks" The Journal of Finance

Hedging density (hedges per 1000 words) correlates with:
- Earnings volatility
- Litigation risk
- Future stock returns
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Set, Optional
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class HedgingResult:
    """Result of hedging language analysis."""
    text: str
    total_words: int
    hedge_count: int
    hedging_density: float  # Hedges per 1000 words
    hedges_found: List[Dict[str, Any]]
    categories: Dict[str, int]  # Count by category
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_words": self.total_words,
            "hedge_count": self.hedge_count,
            "hedging_density": round(self.hedging_density, 2),
            "hedges_found": self.hedges_found,
            "categories": self.categories
        }


class HedgingDetector:
    """
    Hedging language detector using Loughran-McDonald dictionary.
    
    Features:
    - Modal verb detection
    - Uncertainty word detection
    - Qualifier detection
    - Hedging density calculation
    - Category breakdown
    
    Thresholds (per Loughran & McDonald):
    - Low hedging: < 10 per 1000 words
    - Moderate hedging: 10-20 per 1000 words
    - High hedging: > 20 per 1000 words
    
    Example:
        detector = HedgingDetector()
        result = detector.analyze(\"\"\"
            We believe revenue may increase substantially in the coming year,
            though results could vary materially from our estimates.
        \"\"\")
        print(f"Hedging density: {result.hedging_density:.1f} per 1000 words")
    """
    
    # Loughran-McDonald uncertainty words (subset)
    UNCERTAINTY_WORDS = {
        "approximately", "approximate", "belief", "believe", "believes",
        "estimate", "estimated", "estimates", "forecast", "forecasts",
        "indicate", "indicates", "possible", "possibly", "predict",
        "predicts", "projection", "projections", "uncertain", "uncertainty",
        "unclear", "indefinite", "unpredictable", "variable", "varies",
        "vary", "depending", "subject", "conditional", "contingent"
    }
    
    # Modal verbs indicating uncertainty
    MODAL_VERBS = {
        "may", "might", "could", "should", "would", "can"
    }
    
    # Qualifiers
    QUALIFIERS = {
        "substantially", "materially", "significantly", "generally",
        "typically", "normally", "usually", "often", "frequently",
        "occasionally", "sometimes", "potentially", "likely", "unlikely",
        "primarily", "mainly", "largely", "approximately", "roughly"
    }
    
    # Hedging phrases
    HEDGING_PHRASES = [
        r"\bwe believe\b",
        r"\bwe expect\b",
        r"\bwe anticipate\b",
        r"\bit is expected\b",
        r"\bit is believed\b",
        r"\bin our opinion\b",
        r"\bto the best of our knowledge\b",
        r"\bsubject to\b",
        r"\bcould result in\b",
        r"\bmay result in\b"
    ]
    
    def __init__(self):
        """Initialize hedging detector."""
        # Compile regex patterns for phrases
        self.phrase_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.HEDGING_PHRASES
        ]
    
    def analyze(self, text: str) -> HedgingResult:
        """
        Analyze text for hedging language.
        
        Args:
            text: Text to analyze
            
        Returns:
            HedgingResult with counts and density
        """
        # Tokenize (simple word-based)
        words = re.findall(r'\b\w+\b', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return HedgingResult(
                text=text,
                total_words=0,
                hedge_count=0,
                hedging_density=0.0,
                hedges_found=[],
                categories={}
            )
        
        # Find hedges
        hedges_found = []
        categories = {
            "modal_verbs": 0,
            "uncertainty_words": 0,
            "qualifiers": 0,
            "hedging_phrases": 0
        }
        
        # Check each word
        word_set = set(words)
        
        # Modal verbs
        for word in self.MODAL_VERBS:
            count = words.count(word)
            if count > 0:
                hedges_found.append({
                    "hedge": word,
                    "category": "modal_verb",
                    "count": count
                })
                categories["modal_verbs"] += count
        
        # Uncertainty words
        for word in self.UNCERTAINTY_WORDS:
            count = words.count(word)
            if count > 0:
                hedges_found.append({
                    "hedge": word,
                    "category": "uncertainty",
                    "count": count
                })
                categories["uncertainty_words"] += count
        
        # Qualifiers
        for word in self.QUALIFIERS:
            count = words.count(word)
            if count > 0:
                hedges_found.append({
                    "hedge": word,
                    "category": "qualifier",
                    "count": count
                })
                categories["qualifiers"] += count
        
        # Hedging phrases
        for pattern in self.phrase_patterns:
            matches = pattern.findall(text)
            if matches:
                phrase = pattern.pattern.replace(r'\b', '').replace('\\', '')
                hedges_found.append({
                    "hedge": phrase,
                    "category": "phrase",
                    "count": len(matches)
                })
                categories["hedging_phrases"] += len(matches)
        
        # Calculate total hedge count and density
        hedge_count = sum(h["count"] for h in hedges_found)
        hedging_density = (hedge_count / total_words) * 1000
        
        return HedgingResult(
            text=text,
            total_words=total_words,
            hedge_count=hedge_count,
            hedging_density=hedging_density,
            hedges_found=hedges_found,
            categories=categories
        )
    
    def compare_filings(
        self,
        filing1_text: str,
        filing2_text: str,
        filing1_name: str = "Filing 1",
        filing2_name: str = "Filing 2"
    ) -> Dict[str, Any]:
        """
        Compare hedging language between two filings.
        
        Args:
            filing1_text: Text of first filing
            filing2_text: Text of second filing
            filing1_name: Name/identifier of first filing
            filing2_name: Name/identifier of second filing
            
        Returns:
            Dictionary with comparison results
        """
        result1 = self.analyze(filing1_text)
        result2 = self.analyze(filing2_text)
        
        # Calculate change
        density_change = result2.hedging_density - result1.hedging_density
        density_change_pct = (
            (density_change / result1.hedging_density * 100)
            if result1.hedging_density > 0 else 0
        )
        
        return {
            filing1_name: result1.to_dict(),
            filing2_name: result2.to_dict(),
            "comparison": {
                "density_change": round(density_change, 2),
                "density_change_pct": round(density_change_pct, 2),
                "interpretation": self._interpret_change(density_change_pct)
            }
        }
    
    def _interpret_change(self, change_pct: float) -> str:
        """Interpret change in hedging density."""
        if change_pct > 20:
            return "Significant increase in uncertainty language (>20%)"
        elif change_pct > 10:
            return "Moderate increase in uncertainty language (10-20%)"
        elif change_pct < -20:
            return "Significant decrease in uncertainty language (<-20%)"
        elif change_pct < -10:
            return "Moderate decrease in uncertainty language (-10 to -20%)"
        else:
            return "Minimal change in uncertainty language"
    
    def get_risk_level(self, hedging_density: float) -> str:
        """
        Get risk level based on hedging density.
        
        Args:
            hedging_density: Hedges per 1000 words
            
        Returns:
            Risk level description
        """
        if hedging_density > 20:
            return "HIGH - Excessive uncertainty language"
        elif hedging_density > 10:
            return "MODERATE - Elevated uncertainty language"
        else:
            return "LOW - Normal uncertainty language"
    
    def extract_hedged_statements(
        self,
        text: str,
        context_window: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Extract sentences containing hedging language with context.
        
        Args:
            text: Text to analyze
            context_window: Number of characters before/after hedge
            
        Returns:
            List of hedged statement dictionaries
        """
        result = self.analyze(text)
        hedged_statements = []
        
        # Find each hedge in the original text
        for hedge_info in result.hedges_found:
            hedge = hedge_info["hedge"]
            
            # Find all occurrences
            pattern = re.compile(r'\b' + re.escape(hedge) + r'\b', re.IGNORECASE)
            
            for match in pattern.finditer(text):
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                
                context = text[start:end]
                
                hedged_statements.append({
                    "hedge": hedge,
                    "category": hedge_info["category"],
                    "context": context.strip(),
                    "position": match.start()
                })
        
        return hedged_statements
