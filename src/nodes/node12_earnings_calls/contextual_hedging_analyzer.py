"""
Contextual Hedging Analyzer
============================

Analyzes hedging language in earnings calls with speaker attribution.
Detects uncertainty, caution, and hedging patterns.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class HedgingAnalysis:
    """Hedging language analysis result."""
    statement: str
    speaker: str
    hedging_score: float  # 0.0-1.0
    hedging_words: List[str]
    patterns_detected: List[str]
    sentiment: str  # positive, negative, neutral, cautious
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement": self.statement[:200] + "..." if len(self.statement) > 200 else self.statement,
            "speaker": self.speaker,
            "hedging_score": round(self.hedging_score, 2),
            "hedging_words": self.hedging_words,
            "patterns_detected": self.patterns_detected,
            "sentiment": self.sentiment
        }


class ContextualHedgingAnalyzer:
    """
    Analyzes hedging language in transcripts.
    
    Detects:
    - Uncertainty markers (may, might, could, possibly)
    - Qualifiers (somewhat, fairly, relatively)
    - Hedging phrases (difficult to predict, subject to change)
    - Speaker-specific patterns
    """
    
    HEDGING_WORDS = [
        'may', 'might', 'could', 'possibly', 'potentially', 'perhaps',
        'uncertain', 'unclear', 'difficult', 'challenging', 'complex',
        'approximately', 'roughly', 'around', 'about', 'somewhat',
        'fairly', 'relatively', 'generally', 'typically', 'usually',
        'believe', 'expect', 'anticipate', 'estimate', 'project'
    ]
    
    HEDGING_PHRASES = [
        r'difficult to (?:predict|forecast|estimate)',
        r'subject to (?:change|uncertainty|market conditions)',
        r'no guarantee',
        r'cannot (?:predict|guarantee|assure)',
        r'may (?:or may not|vary)',
        r'depending on (?:market|economic|business) conditions',
        r'cautiously optimistic',
        r'remain vigilant',
        r'headwinds?',
        r'tailwinds?'
    ]
    
    def __init__(self):
        self.logger = logger
    
    def analyze_statement(
        self,
        statement: str,
        speaker: str
    ) -> HedgingAnalysis:
        """
        Analyze hedging in a single statement.
        
        Args:
            statement: Statement text
            speaker: Speaker name/title
        
        Returns:
            HedgingAnalysis result
        """
        statement_lower = statement.lower()
        
        # Find hedging words
        hedging_words_found = [
            word for word in self.HEDGING_WORDS
            if re.search(r'\b' + word + r'\b', statement_lower)
        ]
        
        # Find hedging phrases
        patterns_detected = []
        for pattern in self.HEDGING_PHRASES:
            if re.search(pattern, statement_lower):
                patterns_detected.append(pattern.replace(r'\b', '').replace(r'(?:', '('))
        
        # Calculate hedging score
        word_score = len(hedging_words_found) / 10.0  # Normalize
        phrase_score = len(patterns_detected) / 5.0
        hedging_score = min(1.0, (word_score + phrase_score) / 2.0)
        
        # Determine sentiment
        negative_words = ['decline', 'decrease', 'loss', 'challenge', 'difficult', 'headwind']
        positive_words = ['grow', 'increase', 'strong', 'improve', 'optimistic', 'tailwind']
        
        neg_count = sum(1 for word in negative_words if word in statement_lower)
        pos_count = sum(1 for word in positive_words if word in statement_lower)
        
        if hedging_score > 0.5:
            sentiment = 'cautious'
        elif pos_count > neg_count:
            sentiment = 'positive'
        elif neg_count > pos_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return HedgingAnalysis(
            statement=statement,
            speaker=speaker,
            hedging_score=hedging_score,
            hedging_words=hedging_words_found,
            patterns_detected=patterns_detected,
            sentiment=sentiment
        )
    
    def analyze_transcript(
        self,
        statements: List[Dict[str, str]]
    ) -> List[HedgingAnalysis]:
        """
        Analyze hedging across entire transcript.
        
        Args:
            statements: List of statement dicts with 'text' and 'speaker'
        
        Returns:
            List of HedgingAnalysis results
        """
        analyses = []
        
        for stmt in statements:
            analysis = self.analyze_statement(
                stmt.get('text', ''),
                stmt.get('speaker', 'Unknown')
            )
            analyses.append(analysis)
        
        return analyses
    
    def detect_sentiment_shifts(
        self,
        analyses: List[HedgingAnalysis]
    ) -> List[Dict[str, Any]]:
        """
        Detect shifts in sentiment/hedging across transcript.
        
        Args:
            analyses: List of hedging analyses
        
        Returns:
            List of detected shifts
        """
        shifts = []
        
        for i in range(len(analyses) - 1):
            curr = analyses[i]
            next_stmt = analyses[i + 1]
            
            # Check for hedging increase
            if next_stmt.hedging_score > curr.hedging_score + 0.3:
                shifts.append({
                    'type': 'hedging_increase',
                    'from_statement': i,
                    'to_statement': i + 1,
                    'from_score': curr.hedging_score,
                    'to_score': next_stmt.hedging_score,
                    'speaker': next_stmt.speaker
                })
            
            # Check for sentiment change
            if curr.sentiment != next_stmt.sentiment:
                shifts.append({
                    'type': 'sentiment_change',
                    'from_statement': i,
                    'to_statement': i + 1,
                    'from_sentiment': curr.sentiment,
                    'to_sentiment': next_stmt.sentiment,
                    'speaker': next_stmt.speaker
                })
        
        return shifts
