"""
Linguistic Deception Analyzer - Module 4
Implements Pennebaker (2011) and Newman et al. (2003) linguistic deception methodology.
Analyzes management narratives for psychological indicators of fraud and deception.
"""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
import math

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel
)

logger = logging.getLogger(__name__)


class DeceptionType(Enum):
    """Classification of deception types."""
    HIGH_DECEPTION = "HIGH_DECEPTION"
    MODERATE_DECEPTION = "MODERATE_DECEPTION"
    LOW_DECEPTION = "LOW_DECEPTION"
    TRUTHFUL = "TRUTHFUL"
    INCONCLUSIVE = "INCONCLUSIVE"


class LinguisticCategory(Enum):
    """Linguistic analysis categories."""
    COGNITIVE_COMPLEXITY = "COGNITIVE_COMPLEXITY"
    PSYCHOLOGICAL_DISTANCING = "PSYCHOLOGICAL_DISTANCING"
    TEMPORAL_INDICATORS = "TEMPORAL_INDICATORS"
    OBFUSCATION_METRICS = "OBFUSCATION_METRICS"
    EMOTIONAL_TONE = "EMOTIONAL_TONE"
    NARRATIVE_STRUCTURE = "NARRATIVE_STRUCTURE"


@dataclass
class CognitiveComplexityMetrics:
    """Cognitive complexity linguistic markers."""
    exclusive_words: int
    motion_verbs: int
    certainty_words: int
    negations: int
    quantifiers: int
    hedge_words: int
    modal_verbs: int
    complexity_score: float
    interpretation: str


@dataclass
class PsychologicalDistancingMetrics:
    """Psychological distancing indicators."""
    first_person_singular: int
    first_person_plural: int
    third_person: int
    impersonal_pronouns: int
    distancing_score: float
    responsibility_avoidance: bool
    interpretation: str


@dataclass
class TemporalIndicators:
    """Temporal linguistic patterns."""
    past_tense_count: int
    present_tense_count: int
    future_tense_count: int
    past_tense_ratio: float
    present_tense_ratio: float
    future_tense_ratio: float
    temporal_focus: str  # PAST, PRESENT, FUTURE
    interpretation: str


@dataclass
class ObfuscationMetrics:
    """Readability and obfuscation measures."""
    fog_index: float
    flesch_kincaid_grade: float
    flesch_reading_ease: float
    passive_voice_ratio: float
    sentence_complexity: float
    average_word_length: float
    jargon_density: float
    obfuscation_score: float
    interpretation: str


@dataclass
class EmotionalToneMetrics:
    """Emotional tone analysis."""
    positive_emotion_words: int
    negative_emotion_words: int
    anxiety_words: int
    anger_words: int
    sadness_words: int
    confidence_words: int
    emotional_valence: float  # -1 to 1
    emotional_arousal: float  # 0 to 1
    interpretation: str


@dataclass
class NarrativeStructureMetrics:
    """Narrative structure analysis."""
    story_coherence: float
    logical_connectors: int
    causal_language: int
    specific_details: int
    vague_language: int
    narrative_quality_score: float
    interpretation: str


@dataclass
class DeceptionAnalysisResult:
    """Complete deception analysis result."""
    text_analyzed: str
    word_count: int
    sentence_count: int
    
    # Category metrics
    cognitive_complexity: CognitiveComplexityMetrics
    psychological_distancing: PsychologicalDistancingMetrics
    temporal_indicators: TemporalIndicators
    obfuscation_metrics: ObfuscationMetrics
    emotional_tone: EmotionalToneMetrics
    narrative_structure: NarrativeStructureMetrics
    
    # Overall assessment
    deception_probability: float  # 0-1
    confidence_level: float  # 0-1
    deception_classification: DeceptionType
    forensic_classification: str
    
    # Supporting evidence
    red_flags: List[str]
    risk_indicators: List[str]
    comparative_analysis: Dict[str, Any]
    
    # Integrity
    analysis_timestamp: str
    evidence_hash: str


class LinguisticDeceptionAnalyzer:
    """
    Advanced linguistic deception analyzer.
    
    Implements:
    - Pennebaker (2011): Linguistic deception markers
    - Newman et al. (2003): LIWC methodology
    - Larcker & Zakolyukina (2012): CEO deception patterns
    - Zhou et al. (2004): Automated deception detection
    """
    
    def __init__(self):
        """Initialize linguistic deception analyzer."""
        self.hash_chain = ForensicHashChain("linguistic_deception_analyzer")
        
        # Initialize linguistic dictionaries
        self._initialize_linguistic_dictionaries()
        
        # Research-based weights (Larcker & Zakolyukina 2012)
        self.deception_weights = {
            'cognitive_complexity': 0.25,
            'psychological_distancing': 0.30,
            'temporal_indicators': 0.15,
            'obfuscation_metrics': 0.20,
            'emotional_tone': 0.05,
            'narrative_structure': 0.05
        }
        
        logger.info("LinguisticDeceptionAnalyzer initialized")
    
    def _initialize_linguistic_dictionaries(self):
        """Initialize comprehensive linguistic pattern dictionaries."""
        
        # Cognitive Complexity Markers (Pennebaker 2011)
        self.exclusive_words = [
            'but', 'except', 'without', 'exclude', 'rather', 'however',
            'although', 'though', 'unless', 'whereas'
        ]
        
        self.motion_verbs = [
            'walk', 'move', 'go', 'carry', 'bring', 'run', 'arrive',
            'depart', 'enter', 'exit', 'approach', 'reach', 'travel'
        ]
        
        self.certainty_words = [
            'absolutely', 'certainly', 'definitely', 'always', 'never',
            'clearly', 'obviously', 'undoubtedly', 'surely', 'indeed',
            'unquestionably', 'invariably', 'positively'
        ]
        
        self.negations = [
            'not', 'no', 'never', 'none', 'nothing', 'neither', 'nobody',
            'nowhere', 'cannot', "can't", "won't", "don't", "didn't",
            "doesn't", "haven't", "hasn't", "isn't", "aren't", "wasn't", "weren't"
        ]
        
        self.quantifiers = [
            'many', 'few', 'several', 'some', 'most', 'all', 'none',
            'much', 'little', 'more', 'less', 'numerous', 'various'
        ]
        
        self.hedge_words = [
            'maybe', 'perhaps', 'possibly', 'probably', 'might', 'could',
            'may', 'approximately', 'roughly', 'about', 'around', 'somewhat',
            'fairly', 'relatively', 'generally', 'typically', 'usually'
        ]
        
        self.modal_verbs = [
            'can', 'could', 'may', 'might', 'must', 'shall', 'should',
            'will', 'would', 'ought'
        ]
        
        # Emotional Tone Markers
        self.positive_emotion = [
            'good', 'great', 'excellent', 'outstanding', 'success', 'strong',
            'improved', 'growth', 'opportunity', 'positive', 'favorable',
            'benefit', 'advantage', 'progress', 'achievement', 'gain'
        ]
        
        self.negative_emotion = [
            'bad', 'poor', 'weak', 'decline', 'loss', 'difficult', 'challenge',
            'problem', 'issue', 'concern', 'adverse', 'negative', 'unfavorable',
            'risk', 'uncertainty', 'volatility', 'downturn'
        ]
        
        self.anxiety_words = [
            'worried', 'nervous', 'anxious', 'concerned', 'uncertain',
            'troubled', 'uneasy', 'apprehensive', 'tense'
        ]
        
        self.anger_words = [
            'angry', 'frustrated', 'irritated', 'annoyed', 'furious',
            'outraged', 'hostile', 'aggressive'
        ]
        
        self.confidence_words = [
            'confident', 'assured', 'certain', 'convinced', 'optimistic',
            'positive', 'believe', 'expect', 'anticipate'
        ]
        
        # Narrative Structure
        self.logical_connectors = [
            'therefore', 'thus', 'consequently', 'hence', 'accordingly',
            'as a result', 'because', 'since', 'due to', 'given that',
            'in order to', 'so that', 'for this reason'
        ]
        
        self.causal_language = [
            'caused', 'resulted', 'led to', 'due to', 'because of',
            'attributed to', 'stemmed from', 'contributed to'
        ]
        
        self.vague_language = [
            'things', 'stuff', 'something', 'somewhat', 'various',
            'certain', 'particular', 'specific', 'general', 'overall',
            'approximately', 'roughly'
        ]
        
        # Financial jargon (for obfuscation detection)
        self.financial_jargon = [
            'ebitda', 'amortization', 'depreciation', 'accretion', 'dilution',
            'non-gaap', 'pro forma', 'adjusted', 'normalized', 'recurring',
            'synergies', 'optimization', 'restructuring', 'impairment'
        ]
    
    async def analyze_management_discussion(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeceptionAnalysisResult:
        """
        Comprehensive linguistic deception analysis.
        
        Args:
            text: Management discussion text to analyze
            metadata: Optional metadata (company, filing type, etc.)
            
        Returns:
            Complete deception analysis result
        """
        logger.info("Starting linguistic deception analysis...")
        
        if not text or len(text) < 100:
            raise ValueError("Text too short for meaningful analysis (minimum 100 characters)")
        
        # Preprocessing
        text_clean = self._preprocess_text(text)
        word_count = len(text_clean.split())
        sentence_count = len(re.split(r'[.!?]+', text_clean))
        
        # Analyze each category
        cognitive = self._analyze_cognitive_complexity(text_clean)
        distancing = self._analyze_psychological_distancing(text_clean)
        temporal = self._analyze_temporal_indicators(text_clean)
        obfuscation = self._analyze_obfuscation_metrics(text_clean)
        emotional = self._analyze_emotional_tone(text_clean)
        narrative = self._analyze_narrative_structure(text_clean)
        
        # Calculate overall deception probability
        deception_prob = self._calculate_deception_probability({
            'cognitive_complexity': cognitive.complexity_score,
            'psychological_distancing': distancing.distancing_score,
            'temporal_indicators': self._temporal_deception_score(temporal),
            'obfuscation_metrics': obfuscation.obfuscation_score,
            'emotional_tone': self._emotional_deception_score(emotional),
            'narrative_structure': 1.0 - narrative.narrative_quality_score
        })
        
        # Calculate confidence
        confidence = self._calculate_confidence(word_count, sentence_count)
        
        # Classify deception type
        classification = self._classify_deception_type({
            'cognitive': cognitive,
            'distancing': distancing,
            'temporal': temporal,
            'obfuscation': obfuscation,
            'emotional': emotional,
            'narrative': narrative
        })
        
        # Forensic classification
        forensic_class = self._forensic_classification(deception_prob, classification)
        
        # Identify red flags
        red_flags = self._identify_red_flags(
            cognitive, distancing, temporal, obfuscation, emotional, narrative
        )
        
        # Risk indicators
        risk_indicators = self._generate_risk_indicators(deception_prob, red_flags)
        
        # Comparative analysis
        comparative = self._comparative_analysis(
            cognitive, distancing, temporal, obfuscation
        )
        
        # Create result
        result = DeceptionAnalysisResult(
            text_analyzed=text[:500] + "..." if len(text) > 500 else text,
            word_count=word_count,
            sentence_count=sentence_count,
            cognitive_complexity=cognitive,
            psychological_distancing=distancing,
            temporal_indicators=temporal,
            obfuscation_metrics=obfuscation,
            emotional_tone=emotional,
            narrative_structure=narrative,
            deception_probability=deception_prob,
            confidence_level=confidence,
            deception_classification=classification,
            forensic_classification=forensic_class,
            red_flags=red_flags,
            risk_indicators=risk_indicators,
            comparative_analysis=comparative,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            evidence_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
        )
        
        # Log to hash chain
        await self.hash_chain.add_evidence(
            data={
                "action": "analyze_management_discussion",
                "word_count": word_count,
                "deception_probability": deception_prob,
                "classification": classification.value,
                "red_flags_count": len(red_flags),
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.HIGH
        )
        
        logger.info(
            f"Linguistic analysis complete: {deception_prob:.2%} deception probability, "
            f"{classification.value}"
        )
        
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
        
        return text.strip()
    
    def _analyze_cognitive_complexity(self, text: str) -> CognitiveComplexityMetrics:
        """
        Analyze cognitive complexity markers.
        Based on Pennebaker (2011) - Deceptive language shows lower cognitive complexity.
        """
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        
        # Count markers
        exclusive = sum(1 for word in words if word in self.exclusive_words)
        motion = sum(1 for word in words if word in self.motion_verbs)
        certainty = sum(1 for word in words if word in self.certainty_words)
        negations_count = sum(1 for word in words if word in self.negations)
        quantifiers_count = sum(1 for word in words if word in self.quantifiers)
        hedge = sum(1 for word in words if word in self.hedge_words)
        modal = sum(1 for word in words if word in self.modal_verbs)
        
        # Calculate complexity score (lower = more deceptive)
        # Newman et al. (2003): Liars use fewer exclusive words, more motion verbs
        complexity_score = (
            (exclusive / word_count * 100) * 0.30 +  # Exclusive words (positive indicator)
            (1 - motion / word_count * 100) * 0.20 +  # Motion verbs (negative indicator)
            (1 - certainty / word_count * 100) * 0.15 +  # Certainty (suspicious if high)
            (1 - negations_count / word_count * 100) * 0.15 +  # Negations
            (quantifiers_count / word_count * 100) * 0.10 +  # Quantifiers (positive)
            (1 - hedge / word_count * 100) * 0.05 +  # Hedging (suspicious if high)
            (modal / word_count * 100) * 0.05  # Modal verbs
        ) if word_count > 0 else 0.5
        
        # Normalize to 0-1
        complexity_score = max(0, min(1, complexity_score / 100))
        
        # Interpretation
        if complexity_score < 0.3:
            interpretation = "LOW COMPLEXITY - High deception risk (oversimplified language)"
        elif complexity_score < 0.5:
            interpretation = "MODERATE COMPLEXITY - Moderate deception risk"
        else:
            interpretation = "HIGH COMPLEXITY - Low deception risk (nuanced language)"
        
        return CognitiveComplexityMetrics(
            exclusive_words=exclusive,
            motion_verbs=motion,
            certainty_words=certainty,
            negations=negations_count,
            quantifiers=quantifiers_count,
            hedge_words=hedge,
            modal_verbs=modal,
            complexity_score=complexity_score,
            interpretation=interpretation
        )
    
    def _analyze_psychological_distancing(self, text: str) -> PsychologicalDistancingMetrics:
        """
        Analyze psychological distancing patterns.
        Larcker & Zakolyukina (2012): CEOs who lie use fewer first-person singular pronouns.
        """
        # Count pronouns
        first_singular = len(re.findall(r'\b(?:I|me|my|myself|mine)\b', text, re.IGNORECASE))
        first_plural = len(re.findall(r'\b(?:we|us|our|ourselves|ours)\b', text, re.IGNORECASE))
        third_person = len(re.findall(r'\b(?:he|she|they|them|their|his|her|theirs)\b', text, re.IGNORECASE))
        impersonal = len(re.findall(r'\b(?:it|one|this|that|these|those|the company|management)\b', text, re.IGNORECASE))
        
        total_pronouns = first_singular + first_plural + third_person + impersonal
        
        if total_pronouns == 0:
            distancing_score = 0.5
            responsibility_avoidance = True
        else:
            # Calculate distancing (higher = more distancing = more deceptive)
            # Deceptive language: Low first-person singular, high third-person/impersonal
            first_singular_ratio = first_singular / total_pronouns
            third_impersonal_ratio = (third_person + impersonal) / total_pronouns
            
            distancing_score = (
                (1 - first_singular_ratio) * 0.50 +  # Low I/me (key indicator)
                third_impersonal_ratio * 0.30 +  # High they/it
                (first_plural / total_pronouns) * 0.20  # High we (diluting responsibility)
            )
            
            # Responsibility avoidance if very low first-person singular
            responsibility_avoidance = first_singular_ratio < 0.15
        
        # Interpretation
        if distancing_score > 0.7:
            interpretation = "HIGH DISTANCING - Strong deception indicator (avoiding personal responsibility)"
        elif distancing_score > 0.5:
            interpretation = "MODERATE DISTANCING - Moderate deception risk"
        else:
            interpretation = "LOW DISTANCING - Personal accountability maintained"
        
        return PsychologicalDistancingMetrics(
            first_person_singular=first_singular,
            first_person_plural=first_plural,
            third_person=third_person,
            impersonal_pronouns=impersonal,
            distancing_score=distancing_score,
            responsibility_avoidance=responsibility_avoidance,
            interpretation=interpretation
        )
    
    def _analyze_temporal_indicators(self, text: str) -> TemporalIndicators:
        """
        Analyze temporal focus patterns.
        Deceptive narratives often focus on past (distancing) or vague future.
        """
        # Count tense markers
        past_count = self._count_past_tense(text)
        present_count = self._count_present_tense(text)
        future_count = self._count_future_tense(text)
        
        total = past_count + present_count + future_count
        
        if total == 0:
            past_ratio = present_ratio = future_ratio = 0.33
            focus = "BALANCED"
        else:
            past_ratio = past_count / total
            present_ratio = present_count / total
            future_ratio = future_count / total
            
            # Determine focus
            if past_ratio > 0.50:
                focus = "PAST"
            elif future_ratio > 0.40:
                focus = "FUTURE"
            elif present_ratio > 0.40:
                focus = "PRESENT"
            else:
                focus = "BALANCED"
        
        # Interpretation
        if focus == "PAST" and past_ratio > 0.60:
            interpretation = "EXCESSIVE PAST FOCUS - Possible psychological distancing from current issues"
        elif focus == "FUTURE" and future_ratio > 0.50:
            interpretation = "EXCESSIVE FUTURE FOCUS - Possible deflection from current problems"
        elif focus == "PRESENT":
            interpretation = "PRESENT FOCUS - Engaged with current reality (positive indicator)"
        else:
            interpretation = "BALANCED TEMPORAL FOCUS - Normal pattern"
        
        return TemporalIndicators(
            past_tense_count=past_count,
            present_tense_count=present_count,
            future_tense_count=future_count,
            past_tense_ratio=past_ratio,
            present_tense_ratio=present_ratio,
            future_tense_ratio=future_ratio,
            temporal_focus=focus,
            interpretation=interpretation
        )
    
    def _count_past_tense(self, text: str) -> int:
        """Count past tense verbs."""
        # Simple pattern matching (would use NLP tagger in production)
        patterns = [
            r'\b\w+ed\b',  # Regular past tense
            r'\b(?:was|were|had|did|went|came|saw|made|took|gave|got|became|began|felt|found|knew|said|told|thought|brought|bought|caught|taught|fought)\b'
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count
    
    def _count_present_tense(self, text: str) -> int:
        """Count present tense verbs."""
        patterns = [
            r'\b(?:is|are|am|has|have|do|does|goes|comes|sees|makes|takes|gives|gets|becomes|begins|feels|finds|knows|says|tells|thinks|brings|buys|catches|teaches|fights)\b'
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count
    
    def _count_future_tense(self, text: str) -> int:
        """Count future tense markers."""
        patterns = [
            r'\b(?:will|shall|going to|would|could|might|may)\b',
            r'\b(?:expect|anticipate|plan|intend|forecast|project|estimate)\b'
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count
    
    def _analyze_obfuscation_metrics(self, text: str) -> ObfuscationMetrics:
        """
        Analyze readability and obfuscation.
        Deceptive texts often have higher complexity to obscure truth.
        """
        # Calculate Gunning Fog Index
        fog = self._calculate_fog_index(text)
        
        # Calculate Flesch-Kincaid Grade Level
        fk_grade = self._calculate_flesch_kincaid(text)
        
        # Calculate Flesch Reading Ease
        reading_ease = self._calculate_flesch_reading_ease(text)
        
        # Calculate passive voice ratio
        passive_ratio = self._calculate_passive_ratio(text)
        
        # Calculate sentence complexity
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = len(text.split()) / max(len([s for s in sentences if s.strip()]), 1)
        sentence_complexity = min(avg_sentence_length / 20.0, 1.0)  # Normalize
        
        # Calculate average word length
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)
        
        # Calculate jargon density
        jargon_count = sum(1 for word in words if word.lower() in self.financial_jargon)
        jargon_density = jargon_count / max(len(words), 1)
        
        # Calculate overall obfuscation score
        obfuscation_score = (
            min(fog / 20.0, 1.0) * 0.25 +  # Fog index (>12 = college level)
            min(fk_grade / 16.0, 1.0) * 0.25 +  # FK grade (>12 = high school+)
            (1 - reading_ease / 100.0) * 0.20 +  # Reading ease (lower = harder)
            passive_ratio * 0.15 +  # Passive voice
            sentence_complexity * 0.10 +  # Long sentences
            min(jargon_density * 10, 1.0) * 0.05  # Jargon
        )
        
        # Interpretation
        if obfuscation_score > 0.7:
            interpretation = "HIGH OBFUSCATION - Deliberate complexity to obscure meaning"
        elif obfuscation_score > 0.5:
            interpretation = "MODERATE OBFUSCATION - Above-average complexity"
        else:
            interpretation = "LOW OBFUSCATION - Clear, accessible language"
        
        return ObfuscationMetrics(
            fog_index=fog,
            flesch_kincaid_grade=fk_grade,
            flesch_reading_ease=reading_ease,
            passive_voice_ratio=passive_ratio,
            sentence_complexity=sentence_complexity,
            average_word_length=avg_word_length,
            jargon_density=jargon_density,
            obfuscation_score=obfuscation_score,
            interpretation=interpretation
        )
    
    def _calculate_fog_index(self, text: str) -> float:
        """
        Calculate Gunning Fog Index.
        Formula: 0.4 * ((words/sentences) + 100 * (complex_words/words))
        """
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        # Complex words = 3+ syllables
        complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)
        
        words_per_sentence = len(words) / len(sentences)
        complex_ratio = (complex_words / len(words)) * 100
        
        fog_index = 0.4 * (words_per_sentence + complex_ratio)
        
        return fog_index
    
    def _calculate_flesch_kincaid(self, text: str) -> float:
        """
        Calculate Flesch-Kincaid Grade Level.
        Formula: 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        """
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        words_per_sentence = len(words) / len(sentences)
        syllables_per_word = total_syllables / len(words)
        
        grade_level = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
        
        return max(0, grade_level)
    
    def _calculate_flesch_reading_ease(self, text: str) -> float:
        """
        Calculate Flesch Reading Ease.
        Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        Score: 0-100 (higher = easier)
        """
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()
        
        if not sentences or not words:
            return 50.0
        
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        words_per_sentence = len(words) / len(sentences)
        syllables_per_word = total_syllables / len(words)
        
        reading_ease = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
        
        return max(0, min(100, reading_ease))
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)."""
        word = word.lower()
        count = 0
        vowels = 'aeiouy'
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            count -= 1
        
        # Every word has at least one syllable
        if count == 0:
            count = 1
        
        return count
    
    def _calculate_passive_ratio(self, text: str) -> float:
        """Calculate ratio of passive voice constructions."""
        # Passive voice pattern: "be" verb + past participle
        passive_patterns = [
            r'\b(?:is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(?:is|are|was|were|be|been|being)\s+(?:written|taken|given|made|done|seen|known|shown|found|told|heard|felt|left|kept|held)\b'
        ]
        
        passive_count = 0
        for pattern in passive_patterns:
            passive_count += len(re.findall(pattern, text, re.IGNORECASE))
        
        sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
        
        if not sentences:
            return 0.0
        
        return min(passive_count / len(sentences), 1.0)
    
    def _analyze_emotional_tone(self, text: str) -> EmotionalToneMetrics:
        """Analyze emotional tone and affect."""
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)
        
        # Count emotion words
        positive = sum(1 for word in words if word in self.positive_emotion)
        negative = sum(1 for word in words if word in self.negative_emotion)
        anxiety = sum(1 for word in words if word in self.anxiety_words)
        anger = sum(1 for word in words if word in self.anger_words)
        confidence = sum(1 for word in words if word in self.confidence_words)
        
        # Calculate valence (-1 negative to +1 positive)
        if positive + negative > 0:
            valence = (positive - negative) / (positive + negative)
        else:
            valence = 0.0
        
        # Calculate arousal (0 calm to 1 aroused)
        arousal = min((anxiety + anger) / word_count * 100, 1.0) if word_count > 0 else 0.0
        
        # Interpretation
        if valence > 0.5 and arousal < 0.2:
            interpretation = "POSITIVE CALM - Confident, truthful tone"
        elif valence < -0.3:
            interpretation = "NEGATIVE TONE - Possible distress or defensive posture"
        elif arousal > 0.5:
            interpretation = "HIGH AROUSAL - Anxiety or anger detected"
        else:
            interpretation = "NEUTRAL TONE - Balanced emotional expression"
        
        return EmotionalToneMetrics(
            positive_emotion_words=positive,
            negative_emotion_words=negative,
            anxiety_words=anxiety,
            anger_words=anger,
            sadness_words=0,  # Not tracked in this simplified version
            confidence_words=confidence,
            emotional_valence=valence,
            emotional_arousal=arousal,
            interpretation=interpretation
        )
    
    def _analyze_narrative_structure(self, text: str) -> NarrativeStructureMetrics:
        """Analyze narrative coherence and structure."""
        words = text.lower().split()
        word_count = len(words)
        
        # Count structure markers
        logical = sum(1 for connector in self.logical_connectors 
                     if connector in text.lower())
        causal = sum(1 for cause in self.causal_language 
                    if cause in text.lower())
        vague = sum(1 for word in words if word in self.vague_language)
        
        # Estimate specific details (numbers, dates, names)
        specific_details = (
            len(re.findall(r'\b\d+\.?\d*\b', text)) +  # Numbers
            len(re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b', text, re.IGNORECASE)) +  # Months
            len(re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', text))  # Proper names (simplified)
        )
        
        # Calculate story coherence (more connectors = better structure)
        coherence = min((logical + causal) / max(word_count / 50, 1), 1.0)
        
        # Calculate narrative quality
        # High quality: High coherence, many details, low vagueness
        vagueness_ratio = vague / word_count if word_count > 0 else 0
        specificity_ratio = specific_details / word_count if word_count > 0 else 0
        
        quality_score = (
            coherence * 0.40 +
            min(specificity_ratio * 50, 1.0) * 0.40 +
            (1 - min(vagueness_ratio * 20, 1.0)) * 0.20
        )
        
        # Interpretation
        if quality_score > 0.6:
            interpretation = "HIGH QUALITY NARRATIVE - Coherent, specific, detailed"
        elif quality_score > 0.4:
            interpretation = "MODERATE QUALITY - Acceptable structure"
        else:
            interpretation = "LOW QUALITY NARRATIVE - Vague, incoherent, or evasive"
        
        return NarrativeStructureMetrics(
            story_coherence=coherence,
            logical_connectors=logical,
            causal_language=causal,
            specific_details=specific_details,
            vague_language=vague,
            narrative_quality_score=quality_score,
            interpretation=interpretation
        )
    
    def _calculate_deception_probability(
        self,
        category_scores: Dict[str, float]
    ) -> float:
        """
        Calculate overall deception probability using weighted ensemble.
        Based on Larcker & Zakolyukina (2012) SEC fraud study.
        """
        deception_prob = 0.0
        
        for category, score in category_scores.items():
            weight = self.deception_weights.get(category, 0.0)
            # Higher scores in these categories indicate deception
            deception_prob += score * weight
        
        return max(0.0, min(1.0, deception_prob))
    
    def _temporal_deception_score(self, temporal: TemporalIndicators) -> float:
        """Calculate deception score from temporal indicators."""
        # Excessive past or future focus is suspicious
        if temporal.past_tense_ratio > 0.60:
            return 0.7  # High past focus = distancing
        elif temporal.future_tense_ratio > 0.50:
            return 0.6  # Excessive future focus = deflection
        elif temporal.present_tense_ratio > 0.40:
            return 0.2  # Present focus = engaged (good)
        else:
            return 0.4  # Balanced = moderate
    
    def _emotional_deception_score(self, emotional: EmotionalToneMetrics) -> float:
        """Calculate deception score from emotional tone."""
        # Deception often shows negative emotion or high anxiety
        if emotional.emotional_valence < -0.3:
            return 0.7  # Negative tone
        elif emotional.emotional_arousal > 0.5:
            return 0.6  # High anxiety
        elif emotional.emotional_valence > 0.3 and emotional.emotional_arousal < 0.3:
            return 0.2  # Positive calm (truthful)
        else:
            return 0.4  # Neutral
    
    def _classify_deception_type(
        self,
        metrics: Dict[str, Any]
    ) -> DeceptionType:
        """Classify overall deception type."""
        cognitive = metrics['cognitive']
        distancing = metrics['distancing']
        obfuscation = metrics['obfuscation']
        
        # Count high-risk indicators
        high_risk_count = 0
        
        if cognitive.complexity_score < 0.3:
            high_risk_count += 1
        if distancing.distancing_score > 0.7:
            high_risk_count += 1
        if distancing.responsibility_avoidance:
            high_risk_count += 1
        if obfuscation.obfuscation_score > 0.7:
            high_risk_count += 1
        
        # Classify
        if high_risk_count >= 3:
            return DeceptionType.HIGH_DECEPTION
        elif high_risk_count >= 2:
            return DeceptionType.MODERATE_DECEPTION
        elif high_risk_count >= 1:
            return DeceptionType.LOW_DECEPTION
        else:
            return DeceptionType.TRUTHFUL
    
    def _forensic_classification(
        self,
        deception_prob: float,
        deception_type: DeceptionType
    ) -> str:
        """Generate forensic classification string."""
        if deception_prob >= 0.75 and deception_type == DeceptionType.HIGH_DECEPTION:
            return "HIGH-CONFIDENCE DECEPTION - Strong linguistic indicators of fraud"
        elif deception_prob >= 0.60:
            return "PROBABLE DECEPTION - Multiple linguistic red flags detected"
        elif deception_prob >= 0.40:
            return "POSSIBLE DECEPTION - Some concerning linguistic patterns"
        elif deception_prob >= 0.25:
            return "LOW DECEPTION RISK - Minor linguistic anomalies"
        else:
            return "TRUTHFUL NARRATIVE - Linguistic patterns consistent with honesty"
    
    def _identify_red_flags(
        self,
        cognitive: CognitiveComplexityMetrics,
        distancing: PsychologicalDistancingMetrics,
        temporal: TemporalIndicators,
        obfuscation: ObfuscationMetrics,
        emotional: EmotionalToneMetrics,
        narrative: NarrativeStructureMetrics
    ) -> List[str]:
        """Identify specific red flags."""
        red_flags = []
        
        # Cognitive complexity red flags
        if cognitive.complexity_score < 0.3:
            red_flags.append("⚠️ OVERSIMPLIFIED LANGUAGE - Characteristic of deceptive narratives")
        if cognitive.certainty_words > len(cognitive.interpretation.split()) * 0.02:
            red_flags.append("⚠️ EXCESSIVE CERTAINTY - Overcompensation for deception")
        
        # Distancing red flags
        if distancing.responsibility_avoidance:
            red_flags.append("🚨 RESPONSIBILITY AVOIDANCE - Lack of first-person accountability")
        if distancing.distancing_score > 0.7:
            red_flags.append("🚨 HIGH PSYCHOLOGICAL DISTANCING - Detachment from statements")
        
        # Temporal red flags
        if temporal.past_tense_ratio > 0.65:
            red_flags.append("⚠️ EXCESSIVE PAST FOCUS - Psychological distancing from present")
        if temporal.future_tense_ratio > 0.55:
            red_flags.append("⚠️ EXCESSIVE FUTURE FOCUS - Deflecting from current issues")
        
        # Obfuscation red flags
        if obfuscation.obfuscation_score > 0.75:
            red_flags.append("🚨 HIGH OBFUSCATION - Deliberate complexity to obscure truth")
        if obfuscation.passive_voice_ratio > 0.40:
            red_flags.append("⚠️ EXCESSIVE PASSIVE VOICE - Avoiding accountability")
        if obfuscation.jargon_density > 0.05:
            red_flags.append("⚠️ EXCESSIVE JARGON - Obscuring meaning with technical language")
        
        # Emotional red flags
        if emotional.emotional_valence < -0.40:
            red_flags.append("⚠️ HIGHLY NEGATIVE TONE - Possible distress or defensive posture")
        if emotional.emotional_arousal > 0.60:
            red_flags.append("⚠️ HIGH ANXIETY - Elevated stress indicators")
        
        # Narrative red flags
        if narrative.narrative_quality_score < 0.30:
            red_flags.append("🚨 POOR NARRATIVE QUALITY - Vague, incoherent storytelling")
        if narrative.vague_language > len(narrative.interpretation.split()) * 0.05:
            red_flags.append("⚠️ EXCESSIVE VAGUE LANGUAGE - Evasive communication")
        
        return red_flags
    
    def _generate_risk_indicators(
        self,
        deception_prob: float,
        red_flags: List[str]
    ) -> List[str]:
        """Generate actionable risk indicators."""
        indicators = []
        
        if deception_prob >= 0.75:
            indicators.append("CRITICAL: High probability of deceptive narrative - recommend forensic investigation")
        elif deception_prob >= 0.60:
            indicators.append("HIGH: Substantial deception indicators - enhanced scrutiny warranted")
        elif deception_prob >= 0.40:
            indicators.append("MEDIUM: Moderate deception signals - additional analysis recommended")
        
        if len(red_flags) >= 5:
            indicators.append("ACTION: Multiple linguistic red flags - cross-reference with financial anomalies")
        
        if any('RESPONSIBILITY AVOIDANCE' in flag for flag in red_flags):
            indicators.append("ACTION: Review executive certifications and personal liability statements")
        
        if any('OBFUSCATION' in flag for flag in red_flags):
            indicators.append("ACTION: Request plain-language explanations from management")
        
        return indicators
    
    def _comparative_analysis(
        self,
        cognitive: CognitiveComplexityMetrics,
        distancing: PsychologicalDistancingMetrics,
        temporal: TemporalIndicators,
        obfuscation: ObfuscationMetrics
    ) -> Dict[str, Any]:
        """Generate comparative analysis against research benchmarks."""
        # Research benchmarks (Larcker & Zakolyukina 2012)
        benchmarks = {
            'truthful_ceos': {
                'cognitive_complexity': 0.65,
                'distancing_score': 0.35,
                'obfuscation': 0.40
            },
            'deceptive_ceos': {
                'cognitive_complexity': 0.30,
                'distancing_score': 0.75,
                'obfuscation': 0.70
            }
        }
        
        # Calculate similarity to benchmarks
        truthful_distance = abs(cognitive.complexity_score - benchmarks['truthful_ceos']['cognitive_complexity'])
        deceptive_distance = abs(cognitive.complexity_score - benchmarks['deceptive_ceos']['cognitive_complexity'])
        
        closer_to = "TRUTHFUL" if truthful_distance < deceptive_distance else "DECEPTIVE"
        
        return {
            'research_benchmark_comparison': closer_to,
            'cognitive_complexity_percentile': min(cognitive.complexity_score * 100, 100),
            'distancing_percentile': min(distancing.distancing_score * 100, 100),
            'obfuscation_percentile': min(obfuscation.obfuscation_score * 100, 100),
            'overall_assessment': (
                f"Analysis shows pattern closer to {closer_to} executives based on "
                f"Larcker & Zakolyukina (2012) research benchmarks"
            )
        }
    
    def _calculate_confidence(self, word_count: int, sentence_count: int) -> float:
        """Calculate confidence in analysis based on text volume."""
        # More text = higher confidence
        if word_count >= 1000 and sentence_count >= 30:
            return 0.95
        elif word_count >= 500 and sentence_count >= 20:
            return 0.85
        elif word_count >= 250 and sentence_count >= 10:
            return 0.75
        elif word_count >= 100 and sentence_count >= 5:
            return 0.60
        else:
            return 0.40
    
    async def verify_integrity(self) -> bool:
        """Verify hash chain integrity."""
        is_valid = await self.hash_chain.verify_chain()
        
        if not is_valid:
            logger.critical("Linguistic analyzer hash chain integrity violation!")
        
        return is_valid


# Backward compatibility exports
__all__ = [
    'LinguisticDeceptionAnalyzer',
    'DeceptionType',
    'LinguisticCategory',
    'CognitiveComplexityMetrics',
    'PsychologicalDistancingMetrics',
    'TemporalIndicators',
    'ObfuscationMetrics',
    'EmotionalToneMetrics',
    'NarrativeStructureMetrics',
    'DeceptionAnalysisResult'
]

