"""
Narrative Analyzer - Management Disclosure and Tone Shift Detection
====================================================================

Advanced narrative analysis system for detecting sentiment changes, hedging language,
and potential fraud indicators in management communications including SEC filings,
earnings calls, and press releases.

Features:
- Sentiment analysis with financial domain awareness
- Hedging language detection (modal verbs, uncertainty markers)
- Quarter-over-quarter tone shift detection
- Fraud pattern identification based on linguistic markers
- Deception indicators (cognitive complexity, distancing)

Usage:
    analyzer = NarrativeAnalyzer()
    
    documents = [
        NarrativeDocument(id="Q1", content="We are confident in our growth...", quarter="Q1 2024"),
        NarrativeDocument(id="Q2", content="Challenging market conditions...", quarter="Q2 2024"),
    ]
    
    result = analyzer.analyze_narrative_shifts(documents)
    if result.has_significant_shifts:
        print(f"Warning: Detected {len(result.shifts)} significant tone shifts")
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

class ShiftSeverity(Enum):
    """
    Severity classification for narrative shifts.
    
    Forensic Relevance:
    ------------------
    - MINOR: Normal business variation, no investigative action
    - MODERATE: Notable change, flag for monitoring
    - SIGNIFICANT: Material change, requires review
    - MATERIAL: Potentially misleading, investigation warranted
    - CRITICAL: Strong fraud indicator, immediate escalation
    
    SEC Materiality Standard Reference:
    ----------------------------------
    TSC Industries v. Northway (1976): Information is material if there
    is "a substantial likelihood that a reasonable shareholder would
    consider it important" in making an investment decision.
    """
    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    MATERIAL = "material"
    CRITICAL = "critical"


# Conviction word list for management confidence analysis
CONVICTION_WORDS: List[str] = [
    "confident", "certain", "clear", "clearly", "definitely",
    "strong", "strongly", "robust", "solid", "excellent",
    "outstanding", "exceptional", "remarkable", "absolutely",
    "undoubtedly", "unquestionably", "guaranteed", "committed",
    "decisive", "determined", "assured", "positive", "optimistic"
]

# Hedge words already defined - cross-reference for conviction delta analysis
HEDGE_WORDS_REF: List[str] = [
    "approximately", "roughly", "about", "around", "nearly",
    "possibly", "potentially", "might", "may", "could",
    "uncertain", "risk", "challenge", "difficult", "headwind",
    "pressure", "if", "should", "would", "believe", "expect",
    "anticipate", "estimate", "likely", "unlikely"
]


logger = logging.getLogger(__name__)


class ToneShiftType(Enum):
    """Type of tone shift detected."""
    POSITIVE_TO_NEGATIVE = "positive_to_negative"
    NEGATIVE_TO_POSITIVE = "negative_to_positive"
    CONFIDENT_TO_UNCERTAIN = "confident_to_uncertain"
    UNCERTAIN_TO_CONFIDENT = "uncertain_to_confident"
    SPECIFIC_TO_VAGUE = "specific_to_vague"
    FORWARD_TO_BACKWARD = "forward_to_backward"
    NONE = "none"


class FraudIndicatorType(Enum):
    """Type of fraud indicator."""
    EXCESSIVE_HEDGING = "excessive_hedging"
    INCONSISTENT_NARRATIVE = "inconsistent_narrative"
    DISTANCING_LANGUAGE = "distancing_language"
    TOPIC_AVOIDANCE = "topic_avoidance"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    TEMPORAL_CONFUSION = "temporal_confusion"
    BLAME_SHIFTING = "blame_shifting"
    OVEREMPHASIS = "overemphasis"


@dataclass
class SentimentScore:
    """Sentiment analysis score for a document."""
    positive_score: float
    negative_score: float
    neutral_score: float
    compound_score: float
    confidence: float
    
    @property
    def sentiment_label(self) -> str:
        """Get the dominant sentiment label."""
        if self.compound_score >= 0.05:
            return "positive"
        elif self.compound_score <= -0.05:
            return "negative"
        return "neutral"
    
    @property
    def is_positive(self) -> bool:
        return self.compound_score >= 0.05
    
    @property
    def is_negative(self) -> bool:
        return self.compound_score <= -0.05


@dataclass
class HedgingPattern:
    """Detected hedging language pattern."""
    pattern_type: str
    text: str
    position: int
    severity: float  # 0.0-1.0
    context: str


@dataclass
class FraudIndicator:
    """Potential fraud indicator from narrative analysis."""
    indicator_type: FraudIndicatorType
    description: str
    severity: float  # 0.0-1.0
    evidence: List[str]
    confidence: float
    recommendation: str


@dataclass
class NarrativeShift:
    """Detected shift in narrative tone or content."""
    shift_type: ToneShiftType
    from_document: str
    to_document: str
    magnitude: float  # 0.0-1.0
    description: str
    sentiment_before: SentimentScore
    sentiment_after: SentimentScore
    hedging_change: float  # Change in hedging frequency
    topics_dropped: List[str]
    topics_added: List[str]


@dataclass
class NarrativeDocument:
    """Document for narrative analysis."""
    id: str
    content: str
    quarter: Optional[str] = None
    document_type: str = "unknown"
    date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NarrativeAnalysisResult:
    """Result of narrative analysis."""
    documents_analyzed: int
    shifts: List[NarrativeShift]
    fraud_indicators: List[FraudIndicator]
    sentiment_trend: List[SentimentScore]
    hedging_trend: List[float]
    overall_risk_score: float
    has_significant_shifts: bool
    key_findings: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class NarrativeAnalyzer:
    """
    Narrative analysis system for detecting management communication patterns.
    
    Analyzes SEC filings, earnings calls, and other disclosures for signs of
    deception, inconsistency, and fraud through linguistic analysis.
    
    Example:
        analyzer = NarrativeAnalyzer()
        
        result = analyzer.analyze_narrative_shifts([
            NarrativeDocument("Q1", "Strong quarter with record revenue..."),
            NarrativeDocument("Q2", "Challenging conditions impacted results..."),
        ])
        
        if result.overall_risk_score > 0.7:
            print("High fraud risk detected")
    """
    
    # Positive financial sentiment words
    POSITIVE_WORDS = {
        'growth', 'profit', 'increase', 'improvement', 'strong', 'successful',
        'record', 'exceed', 'outperform', 'confident', 'optimistic', 'momentum',
        'robust', 'healthy', 'solid', 'favorable', 'positive', 'gain', 'advance',
        'accelerate', 'expand', 'enhanced', 'achieved', 'delivered', 'excellence',
        'opportunity', 'innovation', 'strategic', 'synergy', 'milestone', 'progress',
    }
    
    # Negative financial sentiment words
    NEGATIVE_WORDS = {
        'decline', 'loss', 'decrease', 'challenging', 'weak', 'difficult',
        'downturn', 'headwind', 'pressure', 'concern', 'uncertain', 'volatile',
        'adverse', 'negative', 'deteriorate', 'impair', 'risk', 'exposure',
        'shortfall', 'miss', 'underperform', 'restructure', 'layoff', 'deficit',
        'liability', 'contingency', 'litigation', 'investigation', 'restate',
        'material weakness', 'going concern', 'default', 'covenant', 'impairment',
    }
    
    # Hedging modal verbs and uncertainty markers
    HEDGING_PATTERNS = [
        (r'\bmay\b', 'modal_may', 0.3),
        (r'\bmight\b', 'modal_might', 0.4),
        (r'\bcould\b', 'modal_could', 0.3),
        (r'\bshould\b', 'modal_should', 0.2),
        (r'\bpotentially\b', 'adverb_potentially', 0.4),
        (r'\bpossibly\b', 'adverb_possibly', 0.5),
        (r'\bperhaps\b', 'adverb_perhaps', 0.5),
        (r'\bapproximately\b', 'adverb_approximately', 0.2),
        (r'\bgenerally\b', 'adverb_generally', 0.2),
        (r'\btypically\b', 'adverb_typically', 0.2),
        (r'\bbelieve\s+that\b', 'belief_statement', 0.4),
        (r'\bwe\s+believe\b', 'belief_statement', 0.4),
        (r'\bmanagement\s+believes\b', 'belief_statement', 0.4),
        (r'\bestimate\s+that\b', 'estimate_statement', 0.3),
        (r'\bexpect\s+that\b', 'expectation_statement', 0.3),
        (r'\banticipate\s+that\b', 'anticipation_statement', 0.3),
        (r'\bit\s+is\s+possible\b', 'possibility_statement', 0.5),
        (r'\buncertain\w*\b', 'uncertainty', 0.6),
        (r'\bsubject\s+to\b', 'conditional', 0.4),
        (r'\bdepending\s+on\b', 'conditional', 0.4),
        (r'\bto\s+the\s+extent\b', 'conditional', 0.4),
        (r'\bif\s+and\s+when\b', 'conditional', 0.5),
        (r'\bno\s+assurance\b', 'disclaimer', 0.7),
        (r'\bcannot\s+guarantee\b', 'disclaimer', 0.6),
        (r'\bcannot\s+predict\b', 'disclaimer', 0.6),
    ]
    
    # Distancing language patterns (third person, passive voice)
    DISTANCING_PATTERNS = [
        (r'\bthe\s+company\b', 'third_person_company', 0.3),
        (r'\bmanagement\b(?!\s+believes)', 'third_person_management', 0.3),
        (r'\bit\s+was\s+determined\b', 'passive_voice', 0.5),
        (r'\bwas\s+identified\b', 'passive_voice', 0.4),
        (r'\bwere\s+discovered\b', 'passive_voice', 0.5),
        (r'\bhas\s+been\s+noted\b', 'passive_voice', 0.4),
        (r'\bwere\s+made\b', 'passive_voice', 0.3),
        (r'\bwas\s+recognized\b', 'passive_voice', 0.3),
    ]
    
    # Blame shifting patterns
    BLAME_SHIFT_PATTERNS = [
        (r'\bdue\s+to\s+market\s+conditions\b', 'external_blame', 0.5),
        (r'\bdue\s+to\s+economic\b', 'external_blame', 0.5),
        (r'\bimpacted\s+by\s+external\b', 'external_blame', 0.6),
        (r'\bforces\s+beyond\s+our\s+control\b', 'external_blame', 0.7),
        (r'\bunforeseen\s+circumstances\b', 'external_blame', 0.6),
        (r'\blegacy\s+issues\b', 'historical_blame', 0.5),
        (r'\binherited\s+challenges\b', 'historical_blame', 0.5),
        (r'\bpredecessor\b', 'historical_blame', 0.4),
    ]
    
    def __init__(
        self,
        hedging_threshold: float = 0.02,
        sentiment_shift_threshold: float = 0.3,
        fraud_risk_threshold: float = 0.6,
        min_document_length: int = 100,
    ):
        """
        Initialize the narrative analyzer.
        
        Args:
            hedging_threshold: Hedging frequency threshold for alerts
            sentiment_shift_threshold: Minimum shift to flag
            fraud_risk_threshold: Overall risk threshold for alerts
            min_document_length: Minimum words for valid analysis
        """
        self.hedging_threshold = hedging_threshold
        self.sentiment_shift_threshold = sentiment_shift_threshold
        self.fraud_risk_threshold = fraud_risk_threshold
        self.min_document_length = min_document_length
        
        # Compile regex patterns for efficiency
        self._hedging_compiled = [
            (re.compile(pattern, re.IGNORECASE), name, severity)
            for pattern, name, severity in self.HEDGING_PATTERNS
        ]
        self._distancing_compiled = [
            (re.compile(pattern, re.IGNORECASE), name, severity)
            for pattern, name, severity in self.DISTANCING_PATTERNS
        ]
        self._blame_compiled = [
            (re.compile(pattern, re.IGNORECASE), name, severity)
            for pattern, name, severity in self.BLAME_SHIFT_PATTERNS
        ]
        
        logger.info("NarrativeAnalyzer initialized")
    
    def analyze_narrative_shifts(
        self, 
        documents: List[NarrativeDocument]
    ) -> NarrativeAnalysisResult:
        """
        Analyze narrative shifts across multiple documents.
        
        Args:
            documents: List of documents to analyze (in chronological order)
            
        Returns:
            NarrativeAnalysisResult with detected shifts and indicators
        """
        if not documents:
            return NarrativeAnalysisResult(
                documents_analyzed=0,
                shifts=[],
                fraud_indicators=[],
                sentiment_trend=[],
                hedging_trend=[],
                overall_risk_score=0.0,
                has_significant_shifts=False,
                key_findings=[],
            )
        
        logger.info(f"Analyzing narrative shifts across {len(documents)} documents")
        
        # Analyze each document
        sentiments = []
        hedging_scores = []
        
        for doc in documents:
            sentiment = self._analyze_sentiment(doc.content)
            sentiments.append(sentiment)
            
            hedging = self._calculate_hedging_score(doc.content)
            hedging_scores.append(hedging)
        
        # Detect shifts between consecutive documents
        shifts = []
        for i in range(1, len(documents)):
            shift = self._detect_shift(
                documents[i - 1],
                documents[i],
                sentiments[i - 1],
                sentiments[i],
                hedging_scores[i - 1],
                hedging_scores[i],
            )
            if shift.shift_type != ToneShiftType.NONE:
                shifts.append(shift)
        
        # Identify fraud indicators
        fraud_indicators = self._identify_fraud_indicators(
            documents, sentiments, hedging_scores, shifts
        )
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(
            sentiments, hedging_scores, shifts, fraud_indicators
        )
        
        # Generate key findings
        key_findings = self._generate_findings(
            shifts, fraud_indicators, risk_score
        )
        
        return NarrativeAnalysisResult(
            documents_analyzed=len(documents),
            shifts=shifts,
            fraud_indicators=fraud_indicators,
            sentiment_trend=sentiments,
            hedging_trend=hedging_scores,
            overall_risk_score=risk_score,
            has_significant_shifts=len(shifts) > 0,
            key_findings=key_findings,
        )
    
    def analyze_single_document(
        self, 
        document: NarrativeDocument
    ) -> Dict[str, Any]:
        """
        Analyze a single document for narrative patterns.
        
        Args:
            document: Document to analyze
            
        Returns:
            Analysis results dictionary
        """
        sentiment = self._analyze_sentiment(document.content)
        hedging = self._calculate_hedging_score(document.content)
        hedging_patterns = self._extract_hedging_patterns(document.content)
        distancing = self._calculate_distancing_score(document.content)
        blame_shifting = self._detect_blame_shifting(document.content)
        
        # Word count and complexity
        words = document.content.split()
        word_count = len(words)
        avg_word_length = sum(len(w) for w in words) / max(word_count, 1)
        sentence_count = len(re.split(r'[.!?]+', document.content))
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        return {
            'document_id': document.id,
            'sentiment': sentiment,
            'hedging_score': hedging,
            'hedging_patterns': hedging_patterns,
            'distancing_score': distancing,
            'blame_shifting_detected': blame_shifting,
            'word_count': word_count,
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length,
            'complexity_score': avg_sentence_length * avg_word_length / 100,
        }
    
    def _analyze_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment of text using domain-specific lexicon."""
        if not text:
            return SentimentScore(0.0, 0.0, 1.0, 0.0, 0.0)
        
        words = text.lower().split()
        word_count = len(words)
        
        if word_count == 0:
            return SentimentScore(0.0, 0.0, 1.0, 0.0, 0.0)
        
        positive_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        
        positive_score = positive_count / word_count
        negative_score = negative_count / word_count
        neutral_score = 1.0 - positive_score - negative_score
        
        # Compound score (-1 to 1)
        if positive_count + negative_count > 0:
            compound = (positive_count - negative_count) / (positive_count + negative_count)
        else:
            compound = 0.0
        
        # Confidence based on evidence
        confidence = min((positive_count + negative_count) / 50.0, 1.0)
        
        return SentimentScore(
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=max(0, neutral_score),
            compound_score=compound,
            confidence=confidence,
        )
    
    def _calculate_hedging_score(self, text: str) -> float:
        """Calculate hedging language frequency score."""
        if not text:
            return 0.0
        
        word_count = len(text.split())
        if word_count < self.min_document_length:
            return 0.0
        
        total_hedging = 0.0
        
        for pattern, name, severity in self._hedging_compiled:
            matches = pattern.findall(text)
            total_hedging += len(matches) * severity
        
        # Normalize by word count
        return total_hedging / word_count
    
    def _extract_hedging_patterns(self, text: str) -> List[HedgingPattern]:
        """Extract all hedging patterns from text."""
        patterns = []
        
        for regex, name, severity in self._hedging_compiled:
            for match in regex.finditer(text):
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]
                
                patterns.append(HedgingPattern(
                    pattern_type=name,
                    text=match.group(),
                    position=match.start(),
                    severity=severity,
                    context=context,
                ))
        
        return patterns
    
    def _calculate_distancing_score(self, text: str) -> float:
        """Calculate linguistic distancing score."""
        if not text:
            return 0.0
        
        word_count = len(text.split())
        if word_count < self.min_document_length:
            return 0.0
        
        total_distancing = 0.0
        
        for pattern, name, severity in self._distancing_compiled:
            matches = pattern.findall(text)
            total_distancing += len(matches) * severity
        
        return total_distancing / word_count
    
    def _detect_blame_shifting(self, text: str) -> List[Dict[str, Any]]:
        """Detect blame shifting language patterns."""
        blame_instances = []
        
        for pattern, name, severity in self._blame_compiled:
            for match in pattern.finditer(text):
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                
                blame_instances.append({
                    'type': name,
                    'text': match.group(),
                    'context': text[start:end],
                    'severity': severity,
                })
        
        return blame_instances
    
    def _detect_shift(
        self,
        doc1: NarrativeDocument,
        doc2: NarrativeDocument,
        sentiment1: SentimentScore,
        sentiment2: SentimentScore,
        hedging1: float,
        hedging2: float,
    ) -> NarrativeShift:
        """Detect narrative shift between two documents."""
        # Calculate sentiment change
        sentiment_change = sentiment2.compound_score - sentiment1.compound_score
        hedging_change = hedging2 - hedging1
        
        # Determine shift type
        shift_type = ToneShiftType.NONE
        magnitude = abs(sentiment_change)
        
        if abs(sentiment_change) >= self.sentiment_shift_threshold:
            if sentiment_change < 0:
                shift_type = ToneShiftType.POSITIVE_TO_NEGATIVE
            else:
                shift_type = ToneShiftType.NEGATIVE_TO_POSITIVE
        elif hedging_change > 0.01:
            shift_type = ToneShiftType.CONFIDENT_TO_UNCERTAIN
            magnitude = hedging_change * 10  # Scale hedging change
        elif hedging_change < -0.01:
            shift_type = ToneShiftType.UNCERTAIN_TO_CONFIDENT
            magnitude = abs(hedging_change) * 10
        
        # Detect topic changes (simplified keyword analysis)
        topics1 = self._extract_key_topics(doc1.content)
        topics2 = self._extract_key_topics(doc2.content)
        
        topics_dropped = list(topics1 - topics2)
        topics_added = list(topics2 - topics1)
        
        description = self._generate_shift_description(
            shift_type, sentiment_change, hedging_change, 
            topics_dropped, topics_added
        )
        
        return NarrativeShift(
            shift_type=shift_type,
            from_document=doc1.id,
            to_document=doc2.id,
            magnitude=min(magnitude, 1.0),
            description=description,
            sentiment_before=sentiment1,
            sentiment_after=sentiment2,
            hedging_change=hedging_change,
            topics_dropped=topics_dropped[:5],  # Top 5
            topics_added=topics_added[:5],
        )
    
    def _extract_key_topics(self, text: str) -> set:
        """Extract key topics from text (simplified)."""
        # Common financial topics
        topics = {
            'revenue', 'earnings', 'margin', 'growth', 'cash flow',
            'guidance', 'outlook', 'forecast', 'acquisition', 'expansion',
            'cost', 'expense', 'investment', 'strategy', 'product',
            'customer', 'market', 'competition', 'innovation', 'technology',
        }
        
        text_lower = text.lower()
        found_topics = set()
        
        for topic in topics:
            if topic in text_lower:
                found_topics.add(topic)
        
        return found_topics
    
    def _generate_shift_description(
        self,
        shift_type: ToneShiftType,
        sentiment_change: float,
        hedging_change: float,
        topics_dropped: List[str],
        topics_added: List[str],
    ) -> str:
        """Generate human-readable shift description."""
        if shift_type == ToneShiftType.NONE:
            return "No significant narrative shift detected"
        
        parts = []
        
        if shift_type == ToneShiftType.POSITIVE_TO_NEGATIVE:
            parts.append(f"Sentiment shifted from positive to negative (change: {sentiment_change:.2f})")
        elif shift_type == ToneShiftType.NEGATIVE_TO_POSITIVE:
            parts.append(f"Sentiment shifted from negative to positive (change: {sentiment_change:.2f})")
        elif shift_type == ToneShiftType.CONFIDENT_TO_UNCERTAIN:
            parts.append(f"Increased hedging/uncertainty language (change: {hedging_change:.4f})")
        elif shift_type == ToneShiftType.UNCERTAIN_TO_CONFIDENT:
            parts.append(f"Decreased hedging language (change: {hedging_change:.4f})")
        
        if topics_dropped:
            parts.append(f"Topics no longer mentioned: {', '.join(topics_dropped[:3])}")
        if topics_added:
            parts.append(f"New topics introduced: {', '.join(topics_added[:3])}")
        
        return "; ".join(parts)
    
    def _identify_fraud_indicators(
        self,
        documents: List[NarrativeDocument],
        sentiments: List[SentimentScore],
        hedging_scores: List[float],
        shifts: List[NarrativeShift],
    ) -> List[FraudIndicator]:
        """Identify potential fraud indicators from analysis."""
        indicators = []
        
        # Check for excessive hedging
        for i, (doc, hedge_score) in enumerate(zip(documents, hedging_scores)):
            if hedge_score > self.hedging_threshold:
                indicators.append(FraudIndicator(
                    indicator_type=FraudIndicatorType.EXCESSIVE_HEDGING,
                    description=f"Document {doc.id} contains unusually high hedging language",
                    severity=min(hedge_score / self.hedging_threshold * 0.5, 1.0),
                    evidence=[f"Hedging score: {hedge_score:.4f} (threshold: {self.hedging_threshold})"],
                    confidence=0.7,
                    recommendation="Review for intentional vagueness or liability avoidance",
                ))
        
        # Check for inconsistent narrative (large sentiment swings)
        if len(sentiments) >= 2:
            max_swing = 0.0
            for i in range(1, len(sentiments)):
                swing = abs(sentiments[i].compound_score - sentiments[i-1].compound_score)
                max_swing = max(max_swing, swing)
            
            if max_swing > 0.5:
                indicators.append(FraudIndicator(
                    indicator_type=FraudIndicatorType.INCONSISTENT_NARRATIVE,
                    description="Significant inconsistency in narrative tone across documents",
                    severity=min(max_swing, 1.0),
                    evidence=[f"Maximum sentiment swing: {max_swing:.2f}"],
                    confidence=0.6,
                    recommendation="Compare factual claims across periods for contradictions",
                ))
        
        # Check for distancing language in all documents
        for doc in documents:
            distancing = self._calculate_distancing_score(doc.content)
            if distancing > 0.01:
                indicators.append(FraudIndicator(
                    indicator_type=FraudIndicatorType.DISTANCING_LANGUAGE,
                    description=f"Elevated distancing language in {doc.id}",
                    severity=min(distancing * 50, 1.0),
                    evidence=[f"Distancing score: {distancing:.4f}"],
                    confidence=0.5,
                    recommendation="Check for accountability avoidance patterns",
                ))
        
        # Check for blame shifting
        for doc in documents:
            blame = self._detect_blame_shifting(doc.content)
            if blame:
                indicators.append(FraudIndicator(
                    indicator_type=FraudIndicatorType.BLAME_SHIFTING,
                    description=f"Blame shifting language detected in {doc.id}",
                    severity=sum(b['severity'] for b in blame) / len(blame),
                    evidence=[b['text'] for b in blame[:3]],
                    confidence=0.6,
                    recommendation="Verify external factors cited against independent sources",
                ))
        
        return indicators
    
    def _calculate_risk_score(
        self,
        sentiments: List[SentimentScore],
        hedging_scores: List[float],
        shifts: List[NarrativeShift],
        indicators: List[FraudIndicator],
    ) -> float:
        """Calculate overall fraud risk score."""
        if not sentiments:
            return 0.0
        
        scores = []
        
        # Factor 1: Sentiment trend (declining sentiment is higher risk)
        if len(sentiments) >= 2:
            trend = sentiments[-1].compound_score - sentiments[0].compound_score
            if trend < 0:
                scores.append(abs(trend) * 0.3)
        
        # Factor 2: Hedging level (higher hedging = higher risk)
        avg_hedging = sum(hedging_scores) / len(hedging_scores)
        if avg_hedging > self.hedging_threshold:
            scores.append(min(avg_hedging / self.hedging_threshold * 0.3, 0.3))
        
        # Factor 3: Significant shifts
        if shifts:
            avg_magnitude = sum(s.magnitude for s in shifts) / len(shifts)
            scores.append(avg_magnitude * 0.2)
        
        # Factor 4: Fraud indicators
        if indicators:
            avg_severity = sum(i.severity for i in indicators) / len(indicators)
            scores.append(avg_severity * 0.3)
        
        return min(sum(scores), 1.0)
    
    def _generate_findings(
        self,
        shifts: List[NarrativeShift],
        indicators: List[FraudIndicator],
        risk_score: float,
    ) -> List[str]:
        """Generate key findings from analysis."""
        findings = []
        
        if risk_score > self.fraud_risk_threshold:
            findings.append(f"HIGH RISK: Overall fraud risk score ({risk_score:.2f}) exceeds threshold")
        elif risk_score > self.fraud_risk_threshold * 0.7:
            findings.append(f"MODERATE RISK: Elevated fraud risk score ({risk_score:.2f})")
        
        for shift in shifts:
            if shift.magnitude > 0.5:
                findings.append(
                    f"Significant {shift.shift_type.value} shift detected "
                    f"from {shift.from_document} to {shift.to_document}"
                )
        
        # Group and count indicators by type
        indicator_counts: Dict[FraudIndicatorType, int] = {}
        for ind in indicators:
            indicator_counts[ind.indicator_type] = indicator_counts.get(ind.indicator_type, 0) + 1
        
        for ind_type, count in sorted(indicator_counts.items(), key=lambda x: -x[1]):
            if count > 1:
                findings.append(f"Multiple instances of {ind_type.value} detected ({count} occurrences)")
            else:
                findings.append(f"{ind_type.value} pattern detected")
        
        return findings


# Injected methods for NarrativeAnalyzer

    def _calculate_conviction_score(self, text: str) -> Dict[str, Any]:
        """
        Calculate conviction score based on presence of conviction vs hedge words.
        
        Conviction Delta Analysis:
        -------------------------
        Score = (conviction_density - hedge_density) normalized to [-1, 1]
        
        Where:
        - conviction_density = conviction_word_count / total_words
        - hedge_density = hedge_word_count / total_words
        
        Interpretation:
        --------------
        +1.0: Maximum conviction (all conviction, no hedging)
        0.0: Neutral (balanced or absent)
        -1.0: Maximum hedging (all hedging, no conviction)
        
        Returns:
            Dict with conviction_score, conviction_count, hedge_count, delta
        """
        text_lower = text.lower()
        words = text_lower.split()
        total_words = len(words)
        
        if total_words == 0:
            return {
                "conviction_score": 0.0,
                "conviction_count": 0,
                "hedge_count": 0,
                "conviction_density": 0.0,
                "hedge_density": 0.0,
                "delta": 0.0
            }
        
        conviction_count = sum(1 for w in CONVICTION_WORDS if w in text_lower)
        hedge_count = sum(1 for w in HEDGE_WORDS_REF if w in text_lower)
        
        conviction_density = conviction_count / total_words
        hedge_density = hedge_count / total_words
        
        # Normalize to [-1, 1] range
        max_density = max(conviction_density, hedge_density, 0.001)
        delta = (conviction_density - hedge_density) / max_density
        delta = max(-1.0, min(1.0, delta))
        
        return {
            "conviction_score": round(delta, 4),
            "conviction_count": conviction_count,
            "hedge_count": hedge_count,
            "conviction_density": round(conviction_density, 6),
            "hedge_density": round(hedge_density, 6),
            "delta": round(conviction_density - hedge_density, 6)
        }

    def _calculate_forensic_priority_score(
        self,
        shifts: List['NarrativeShift'],
        conviction_trajectory: List[float],
        sentiment_trajectory: List[float]
    ) -> Dict[str, Any]:
        """
        Calculate forensic priority score for investigation resource allocation.
        
        Scoring Algorithm:
        -----------------
        Base score from shift severity weights:
        - CRITICAL: +0.25 per instance
        - MATERIAL: +0.15 per instance
        - SIGNIFICANT: +0.10 per instance
        - MODERATE: +0.05 per instance
        - MINOR: +0.02 per instance
        
        Trajectory modifiers:
        - Conviction decline > 0.3: +0.15
        - Sentiment decline > 0.5: +0.15
        - Multiple consecutive declines: +0.10
        
        Returns:
            Dict with priority_score (0-1), priority_level, score_components
        """
        score = 0.0
        components = {}
        
        # Shift severity scoring
        severity_weights = {
            ShiftSeverity.CRITICAL: 0.25,
            ShiftSeverity.MATERIAL: 0.15,
            ShiftSeverity.SIGNIFICANT: 0.10,
            ShiftSeverity.MODERATE: 0.05,
            ShiftSeverity.MINOR: 0.02
        }
        
        shift_score = 0.0
        for shift in shifts:
            severity = getattr(shift, 'severity', ShiftSeverity.MINOR)
            if isinstance(severity, str):
                try:
                    severity = ShiftSeverity(severity.lower())
                except ValueError:
                    severity = ShiftSeverity.MINOR
            shift_score += severity_weights.get(severity, 0.02)
        
        shift_score = min(0.5, shift_score)  # Cap at 0.5
        components["shift_severity_score"] = round(shift_score, 4)
        score += shift_score
        
        # Conviction trajectory modifier
        if len(conviction_trajectory) >= 2:
            conviction_change = conviction_trajectory[-1] - conviction_trajectory[0]
            if conviction_change < -0.3:
                components["conviction_decline_modifier"] = 0.15
                score += 0.15
            elif conviction_change < -0.15:
                components["conviction_decline_modifier"] = 0.08
                score += 0.08
        
        # Sentiment trajectory modifier
        if len(sentiment_trajectory) >= 2:
            sentiment_change = sentiment_trajectory[-1] - sentiment_trajectory[0]
            if sentiment_change < -0.5:
                components["sentiment_decline_modifier"] = 0.15
                score += 0.15
            elif sentiment_change < -0.25:
                components["sentiment_decline_modifier"] = 0.08
                score += 0.08
        
        # Consecutive decline modifier
        consecutive_declines = 0
        for i in range(1, len(sentiment_trajectory)):
            if sentiment_trajectory[i] < sentiment_trajectory[i-1]:
                consecutive_declines += 1
            else:
                consecutive_declines = 0
        
        if consecutive_declines >= 3:
            components["consecutive_decline_modifier"] = 0.10
            score += 0.10
        
        # Normalize final score
        priority_score = min(1.0, max(0.0, score))
        
        # Priority level classification
        if priority_score >= 0.70:
            priority_level = "CRITICAL"
        elif priority_score >= 0.50:
            priority_level = "HIGH"
        elif priority_score >= 0.30:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"
        
        return {
            "priority_score": round(priority_score, 4),
            "priority_level": priority_level,
            "score_components": components
        }

    def generate_investigation_recommendations(
        self,
        shifts: List['NarrativeShift'],
        priority_score: float,
        anomalies: Dict[str, Any]
    ) -> List[str]:
        """
        Generate prioritized investigation recommendations based on analysis.
        
        Recommendation Categories:
        -------------------------
        1. IMMEDIATE: Critical findings requiring urgent action
        2. HIGH: Material findings for near-term investigation
        3. STANDARD: Routine follow-up items
        4. MONITORING: Ongoing surveillance recommendations
        
        Returns:
            List of recommendation strings with priority prefixes
        """
        recommendations = []
        
        # Critical priority recommendations
        critical_shifts = [
            s for s in shifts 
            if getattr(s, 'severity', None) in [ShiftSeverity.CRITICAL, 'critical']
        ]
        
        if critical_shifts:
            recommendations.append(
                "[IMMEDIATE] Critical narrative shifts detected - "
                "initiate detailed document review for potential material misstatement"
            )
        
        if priority_score >= 0.70:
            recommendations.append(
                "[IMMEDIATE] Forensic priority score exceeds 0.70 threshold - "
                "escalate to senior investigator for fraud assessment"
            )
        
        # High priority recommendations
        material_shifts = [
            s for s in shifts
            if getattr(s, 'severity', None) in [ShiftSeverity.MATERIAL, 'material']
        ]
        
        if material_shifts:
            recommendations.append(
                "[HIGH] Material narrative shifts identified - "
                "cross-reference with Form 4 insider transactions during shift periods"
            )
        
        if anomalies.get('guidance_revision_detected'):
            recommendations.append(
                "[HIGH] Guidance revision pattern detected - "
                "compare revised guidance to prior analyst consensus and press releases"
            )
        
        # Standard recommendations based on analysis
        if len(shifts) > 0:
            recommendations.append(
                "[STANDARD] Review contemporaneous internal communications "
                "(emails, Slack, Teams) for corroborating evidence of known issues"
            )
            recommendations.append(
                "[STANDARD] Obtain and analyze earnings call transcripts "
                "Q&A sections for analyst concerns and management deflection patterns"
            )
        
        if anomalies.get('hedge_increase_detected'):
            recommendations.append(
                "[STANDARD] Hedging language increase detected - "
                "compare to subsequent quarterly results for forecast accuracy"
            )
        
        # Monitoring recommendations
        recommendations.append(
            "[MONITORING] Establish ongoing surveillance for SEC 8-K filings "
            "from target entity for material event disclosures"
        )
        
        if priority_score >= 0.30:
            recommendations.append(
                "[MONITORING] Add entity to watchlist for automated "
                "Form 4 insider transaction alerts"
            )
        
        # Deduplicate and return
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations

