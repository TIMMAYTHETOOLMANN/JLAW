"""
Earnings Call Analyzer - Corporate Communications Intelligence
============================================================

Analyzes earnings call transcripts for:
- Tone and sentiment shifts
- Management credibility indicators
- Linguistic deception detection
- Question evasion patterns
- Forward-looking statement analysis
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class EarningsCall:
    """Earnings call transcript"""
    ticker: str
    date: datetime
    quarter: str
    fiscal_year: int
    
    # Transcript sections
    prepared_remarks: str
    qa_section: str
    full_transcript: str
    
    # Participants
    executives: List[Dict[str, str]]
    analysts: List[str]
    
    # Analysis
    overall_sentiment: Optional[str] = None
    sentiment_score: float = 0.0
    deception_indicators: List[str] = None
    evasion_count: int = 0
    
    def __post_init__(self):
        if self.deception_indicators is None:
            self.deception_indicators = []


class EarningsCallAnalyzer:
    """
    Advanced earnings call transcript analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._sentiment_analyzer = None
        
        # Deception indicators (linguistic patterns)
        self.deception_patterns = {
            'distancing': ['the company', 'the business', 'they', 'them'],
            'hedging': ['basically', 'kind of', 'sort of', 'somewhat', 'relatively'],
            'evasion': ['as I said before', 'as mentioned', 'moving on', 'next question'],
            'emphasis': ['honestly', 'frankly', 'to be honest', 'believe me', 'trust me'],
            'minimization': ['only', 'just', 'merely', 'simply']
        }
        
        # Statistics
        self.stats = {
            'calls_analyzed': 0,
            'deception_detected': 0,
            'evasions_detected': 0
        }
    
    async def gather(
        self,
        target: str,
        lookback_days: int = 365,
        max_items: int = 10
    ) -> List[Any]:
        """
        Gather earnings call intelligence
        
        Args:
            target: Ticker symbol
            lookback_days: Historical window
            max_items: Maximum calls to analyze
        
        Returns:
            List of IntelligenceItem objects
        """
        logger.info(f"📞 Gathering earnings call intelligence for: {target}")
        
        # Retrieve transcripts
        transcripts = await self._retrieve_transcripts(target, lookback_days)
        
        # Analyze each transcript
        intelligence_items = []
        
        for transcript in transcripts[:max_items]:
            analysis = await self._analyze_transcript(transcript)
            items = self._convert_to_intelligence(transcript, analysis)
            intelligence_items.extend(items)
        
        logger.info(f"✓ Analyzed {len(transcripts)} earnings calls")
        
        return intelligence_items
    
    async def _retrieve_transcripts(
        self,
        ticker: str,
        lookback_days: int
    ) -> List[EarningsCall]:
        """
        Retrieve earnings call transcripts
        (Placeholder - requires Seeking Alpha, Finnhub, or similar API)
        """
        logger.info("📄 Transcript retrieval not implemented (requires API subscription)")
        
        # Would integrate with:
        # - Seeking Alpha API
        # - Finnhub earnings call transcripts
        # - Alpha Vantage earnings calendar + scraping
        
        return []
    
    async def _analyze_transcript(
        self,
        call: EarningsCall
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of earnings call transcript
        """
        analysis = {
            'sentiment': {},
            'deception_indicators': [],
            'question_evasion': [],
            'tone_shifts': [],
            'forward_looking': []
        }
        
        # Sentiment analysis
        analysis['sentiment'] = await self._analyze_sentiment(call)
        
        # Deception detection
        analysis['deception_indicators'] = self._detect_deception(call)
        
        # Question evasion
        analysis['question_evasion'] = self._detect_evasion(call)
        
        # Tone shifts (prepared vs Q&A)
        analysis['tone_shifts'] = self._analyze_tone_shift(call)
        
        # Forward-looking statements
        analysis['forward_looking'] = self._extract_forward_looking(call)
        
        self.stats['calls_analyzed'] += 1
        
        if analysis['deception_indicators']:
            self.stats['deception_detected'] += 1
        
        return analysis
    
    async def _analyze_sentiment(self, call: EarningsCall) -> Dict[str, Any]:
        """Analyze sentiment of prepared remarks vs Q&A"""
        try:
            if not self._sentiment_analyzer:
                from transformers import pipeline
                self._sentiment_analyzer = pipeline(
                    "sentiment-analysis",
                    model="ProsusAI/finbert"
                )
            
            # Analyze prepared remarks
            prepared_sentiment = self._sentiment_analyzer(
                call.prepared_remarks[:512]
            )[0]
            
            # Analyze Q&A
            qa_sentiment = self._sentiment_analyzer(
                call.qa_section[:512]
            )[0]
            
            return {
                'prepared_remarks': {
                    'label': prepared_sentiment['label'],
                    'score': prepared_sentiment['score']
                },
                'qa_section': {
                    'label': qa_sentiment['label'],
                    'score': qa_sentiment['score']
                },
                'sentiment_shift': (
                    qa_sentiment['score'] - prepared_sentiment['score']
                ) if prepared_sentiment['label'] == qa_sentiment['label'] else None
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Sentiment analysis failed: {e}")
            return {}
    
    def _detect_deception(self, call: EarningsCall) -> List[Dict[str, Any]]:
        """
        Detect linguistic deception indicators
        Based on research in forensic linguistics
        """
        indicators = []
        
        text = call.full_transcript.lower()
        
        for pattern_type, patterns in self.deception_patterns.items():
            count = 0
            examples = []
            
            for pattern in patterns:
                matches = re.finditer(r'\b' + re.escape(pattern) + r'\b', text)
                match_list = list(matches)
                count += len(match_list)
                
                if match_list:
                    # Get context for first few matches
                    for match in match_list[:3]:
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end]
                        examples.append(context)
            
            if count > 0:
                # Threshold for significance
                words = len(text.split())
                frequency = count / words * 1000  # per 1000 words
                
                if frequency > 2.0:  # Elevated usage
                    indicators.append({
                        'type': pattern_type,
                        'count': count,
                        'frequency_per_1000': round(frequency, 2),
                        'examples': examples,
                        'severity': 'high' if frequency > 5.0 else 'medium'
                    })
        
        return indicators
    
    def _detect_evasion(self, call: EarningsCall) -> List[Dict[str, Any]]:
        """
        Detect question evasion patterns in Q&A
        """
        evasions = []
        
        # Split Q&A into question-answer pairs
        qa_pairs = self._parse_qa_section(call.qa_section)
        
        for question, answer in qa_pairs:
            # Check for evasion patterns
            answer_lower = answer.lower()
            
            # Pattern 1: Redirecting to previous statements
            if any(phrase in answer_lower for phrase in [
                'as i mentioned', 'as i said', 'as we discussed', 'like i said'
            ]):
                evasions.append({
                    'type': 'redirect_to_previous',
                    'question': question[:100],
                    'answer': answer[:200]
                })
            
            # Pattern 2: Moving on without answering
            if any(phrase in answer_lower for phrase in [
                'moving on', 'next question', "let's move", 'anything else'
            ]):
                evasions.append({
                    'type': 'deflection',
                    'question': question[:100],
                    'answer': answer[:200]
                })
            
            # Pattern 3: Overly short non-substantive answer
            if len(answer.split()) < 20:
                if not any(word in answer_lower for word in [
                    'yes', 'no', 'correct', 'absolutely'
                ]):
                    evasions.append({
                        'type': 'non_substantive',
                        'question': question[:100],
                        'answer': answer
                    })
        
        call.evasion_count = len(evasions)
        self.stats['evasions_detected'] += len(evasions)
        
        return evasions
    
    def _parse_qa_section(self, qa_text: str) -> List[tuple[str, str]]:
        """Parse Q&A section into question-answer pairs"""
        # Simple parsing (production would use more sophisticated NLP)
        pairs = []
        
        # Look for common patterns
        # "Analyst: Question text\nExecutive: Answer text"
        
        lines = qa_text.split('\n')
        current_question = ""
        current_answer = ""
        in_question = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with analyst/executive name
            if any(word in line.lower() for word in ['analyst', 'question']):
                if current_question and current_answer:
                    pairs.append((current_question, current_answer))
                current_question = line
                current_answer = ""
                in_question = True
            elif any(word in line.lower() for word in ['executive', 'ceo', 'cfo', 'answer']):
                in_question = False
                current_answer = line
            else:
                if in_question:
                    current_question += " " + line
                else:
                    current_answer += " " + line
        
        # Add last pair
        if current_question and current_answer:
            pairs.append((current_question, current_answer))
        
        return pairs
    
    def _analyze_tone_shift(self, call: EarningsCall) -> Dict[str, Any]:
        """Analyze tone differences between prepared remarks and Q&A"""
        
        # Word count comparison
        prepared_words = len(call.prepared_remarks.split())
        qa_words = len(call.qa_section.split())
        
        # Average sentence length (indicator of defensiveness)
        prepared_sentences = call.prepared_remarks.count('.') + call.prepared_remarks.count('!') + 1
        qa_sentences = call.qa_section.count('.') + call.qa_section.count('!') + 1
        
        prepared_avg_len = prepared_words / prepared_sentences
        qa_avg_len = qa_words / qa_sentences
        
        # Hedging word frequency
        hedging_words = ['may', 'might', 'could', 'would', 'possibly', 'perhaps']
        
        prepared_hedging = sum(
            call.prepared_remarks.lower().count(word) for word in hedging_words
        )
        qa_hedging = sum(
            call.qa_section.lower().count(word) for word in hedging_words
        )
        
        return {
            'prepared_avg_sentence_length': prepared_avg_len,
            'qa_avg_sentence_length': qa_avg_len,
            'sentence_length_change': qa_avg_len - prepared_avg_len,
            'prepared_hedging_frequency': prepared_hedging / prepared_words * 1000,
            'qa_hedging_frequency': qa_hedging / qa_words * 1000,
            'interpretation': (
                'Defensive tone in Q&A' if qa_avg_len < prepared_avg_len * 0.7
                else 'Consistent tone'
            )
        }
    
    def _extract_forward_looking(self, call: EarningsCall) -> List[Dict[str, Any]]:
        """Extract forward-looking statements and guidance"""
        statements = []
        
        # Forward-looking keywords
        forward_patterns = [
            r'expect.*to',
            r'anticipate.*',
            r'believe.*will',
            r'guidance.*',
            r'forecast.*',
            r'project.*',
            r'estimate.*',
            r'next quarter',
            r'next year',
            r'going forward'
        ]
        
        text = call.full_transcript
        
        for pattern in forward_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Extract sentence containing the match
                start = text.rfind('.', 0, match.start()) + 1
                end = text.find('.', match.end()) + 1
                
                if start >= 0 and end > start:
                    sentence = text[start:end].strip()
                    
                    statements.append({
                        'statement': sentence,
                        'type': pattern,
                        'position': 'prepared_remarks' if match.start() < len(call.prepared_remarks)
                                   else 'qa_section'
                    })
        
        return statements
    
    def _convert_to_intelligence(
        self,
        call: EarningsCall,
        analysis: Dict[str, Any]
    ) -> List[Any]:
        """Convert earnings call analysis to intelligence items"""
        from .omniscient_gatherer import IntelligenceItem
        
        items = []
        
        # Sentiment item
        if analysis.get('sentiment'):
            sentiment = analysis['sentiment']
            
            content = (
                f"{call.ticker} earnings call sentiment: "
                f"Prepared remarks: {sentiment.get('prepared_remarks', {}).get('label', 'N/A')}, "
                f"Q&A: {sentiment.get('qa_section', {}).get('label', 'N/A')}"
            )
            
            items.append(IntelligenceItem(
                content=content,
                source='earnings_call',
                timestamp=call.date,
                entities=[call.ticker],
                confidence=0.80,
                category='earnings_sentiment',
                metadata=sentiment
            ))
        
        # Deception indicators
        if analysis.get('deception_indicators'):
            for indicator in analysis['deception_indicators']:
                content = (
                    f"{call.ticker} earnings call: Elevated {indicator['type']} "
                    f"language detected ({indicator['frequency_per_1000']:.1f} per 1000 words)"
                )
                
                items.append(IntelligenceItem(
                    content=content,
                    source='earnings_call',
                    timestamp=call.date,
                    entities=[call.ticker],
                    confidence=0.70,
                    category='deception_indicator',
                    metadata=indicator
                ))
        
        # Question evasion
        if analysis.get('question_evasion'):
            content = (
                f"{call.ticker} earnings call: {len(analysis['question_evasion'])} "
                f"potential question evasions detected"
            )
            
            items.append(IntelligenceItem(
                content=content,
                source='earnings_call',
                timestamp=call.date,
                entities=[call.ticker],
                confidence=0.65,
                category='evasion',
                metadata={'evasions': analysis['question_evasion']}
            ))
        
        return items


if __name__ == "__main__":
    # Demo
    async def demo():
        analyzer = EarningsCallAnalyzer()
        
        items = await analyzer.gather('AAPL', lookback_days=180)
        print(f"Analyzed earnings calls: {len(items)} intelligence items")
    
    asyncio.run(demo())

