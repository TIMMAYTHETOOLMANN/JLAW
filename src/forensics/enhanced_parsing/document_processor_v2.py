"""
Enhanced Document Processor - Phase 1 Core Module (ENHANCED)
============================================================
Advanced multi-modal document extraction with forensic accuracy
Implements full Enhancement Protocol Phase 1 specifications
"""
import asyncio
import logging
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime

from ..universal_document_extractor import (
    UniversalDocumentExtractor,
    ExtractionResult,
    DocumentFormat
)

logger = logging.getLogger(__name__)


@dataclass
class EnhancedExtractionResult:
    """Extended extraction result with enhanced forensic capabilities"""
    base_result: ExtractionResult
    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    temporal_events: List[Dict[str, Any]] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    sentiment_analysis: Optional[Dict[str, float]] = None
    contradiction_candidates: List[Dict[str, Any]] = field(default_factory=list)
    financial_metrics: Optional[Dict[str, Any]] = None
    extraction_confidence: float = 0.0
    content_hash: str = ""


class EnhancedDocumentProcessor:
    """Enhanced document processor with full Phase 1 NLP capabilities
    
    Enhancements:
    - Entity extraction with spaCy transformer models
    - Relationship detection using dependency parsing
    - Temporal event extraction with normalization
    - Financial metrics extraction
    - Sentiment analysis with FinBERT
    - Key phrase extraction
    - Multi-level confidence scoring
    """
    
    def __init__(self, base_extractor: Optional[UniversalDocumentExtractor] = None):
        self.base_extractor = base_extractor or UniversalDocumentExtractor()
        
        # Initialize NLP pipeline
        self._nlp = None
        self._nlp_model = None
        self._initialize_nlp()
        
        # Initialize sentiment analyzer
        self._sentiment_pipeline = None
        self._initialize_sentiment()
        
        logger.info("✅ Enhanced Document Processor initialized - Phase 1 ADVANCED ACTIVE")
    
    def _initialize_nlp(self):
        """Initialize spaCy NLP pipeline with transformer model"""
        try:
            import spacy
            # Try to load transformer model first (most accurate)
            models_to_try = ['en_core_web_trf', 'en_core_web_lg', 'en_core_web_sm']
            
            for model_name in models_to_try:
                try:
                    self._nlp = spacy.load(model_name)
                    self._nlp_model = model_name
                    logger.info(f"🧠 Loaded spaCy model: {model_name}")
                    break
                except OSError:
                    continue
            
            if not self._nlp:
                logger.warning("⚠️ No spaCy models available - entity extraction disabled")
        except Exception as e:
            logger.warning(f"spaCy initialization failed: {e}")
            self._nlp = None
    
    def _initialize_sentiment(self):
        """Initialize FinBERT sentiment analyzer for financial text"""
        try:
            from transformers import pipeline
            self._sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                max_length=512,
                truncation=True
            )
            logger.info("💹 FinBERT sentiment analyzer loaded")
        except Exception as e:
            logger.debug(f"FinBERT initialization failed (optional): {e}")
            self._sentiment_pipeline = None
    
    async def process_document(
        self,
        content: Union[str, bytes],
        url: Optional[str] = None,
        enable_financial_extraction: bool = True
    ) -> EnhancedExtractionResult:
        """Process document with enhanced forensic analysis
        
        Args:
            content: Document content (text or bytes)
            url: Optional source URL
            enable_financial_extraction: Enable financial metrics extraction
            
        Returns:
            EnhancedExtractionResult with comprehensive analysis
        """
        logger.info("🔍 Processing document with enhanced forensic capabilities")
        
        # Use existing base extractor
        base_result = await self.base_extractor.extract_document(content, url)
        text = base_result.raw_text if base_result.success else str(content)
        
        # Extract entities
        entities = await self._extract_entities(text)
        
        # Extract relationships
        relationships = await self._extract_relationships(text, entities)
        
        # Extract temporal events
        temporal_events = await self._extract_temporal_events(text)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(text)
        
        # Sentiment analysis
        sentiment = await self._analyze_sentiment(text)
        
        # Financial metrics extraction
        financial_metrics = None
        if enable_financial_extraction:
            financial_metrics = await self._extract_financial_indicators(text)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            base_result, entities, relationships, temporal_events
        )
        
        # Create enhanced result
        result = EnhancedExtractionResult(
            base_result=base_result,
            entities=entities,
            relationships=relationships,
            temporal_events=temporal_events,
            key_phrases=key_phrases,
            sentiment_analysis=sentiment,
            financial_metrics=financial_metrics,
            extraction_confidence=confidence,
            content_hash=self._hash_content(text)
        )
        
        logger.info(
            f"✅ Document processing complete - "
            f"{len(entities)} entities, "
            f"{len(relationships)} relationships, "
            f"{len(temporal_events)} temporal events"
        )
        return result
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using spaCy
        
        Entity types: PERSON, ORG, GPE, DATE, MONEY, CARDINAL, etc.
        """
        entities = []
        if not self._nlp or not text:
            return entities
        
        try:
            # Limit text size for performance
            doc = self._nlp(text[:1000000])
            
            for ent in doc.ents:
                entity = {
                    'text': ent.text,
                    'type': ent.label_.lower(),
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': 0.85  # spaCy doesn't provide direct confidence
                }
                entities.append(entity)
            
            logger.debug(f"🏷️ Extracted {len(entities)} entities")
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        
        return entities
    
    async def _extract_relationships(
        self, 
        text: str, 
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract relationships between entities using dependency parsing
        
        Extracts subject-verb-object triples from sentences
        """
        relationships = []
        if not self._nlp or not text or len(entities) < 2:
            return relationships
        
        try:
            # Limit text for performance
            doc = self._nlp(text[:500000])
            
            for sent in doc.sents:
                # Extract subject-verb-object triples
                for token in sent:
                    if token.dep_ in ('nsubj', 'nsubjpass'):
                        subject = token.text
                        verb = token.head.text
                        
                        # Find object
                        obj = None
                        for child in token.head.children:
                            if child.dep_ in ('dobj', 'attr', 'prep', 'pobj'):
                                obj = child.text
                                break
                        
                        if obj:
                            relationships.append({
                                'subject': subject,
                                'predicate': verb,
                                'object': obj,
                                'type': 'dependency',
                                'sentence': sent.text[:200]  # Limit sentence length
                            })
            
            logger.debug(f"🔗 Extracted {len(relationships)} relationships")
        except Exception as e:
            logger.warning(f"Relationship extraction failed: {e}")
        
        return relationships
    
    async def _extract_temporal_events(self, text: str) -> List[Dict[str, Any]]:
        """Extract temporal events and dates with normalization"""
        temporal_events = []
        if not self._nlp or not text:
            return temporal_events
        
        try:
            doc = self._nlp(text[:500000])
            
            for ent in doc.ents:
                if ent.label_ == 'DATE':
                    # Find context around the date
                    sent = ent.sent
                    temporal_events.append({
                        'date': ent.text,
                        'context': sent.text,
                        'start': ent.start_char,
                        'normalized': self._normalize_date(ent.text)
                    })
            
            logger.debug(f"📅 Extracted {len(temporal_events)} temporal events")
        except Exception as e:
            logger.warning(f"Temporal extraction failed: {e}")
        
        return temporal_events
    
    def _normalize_date(self, date_text: str) -> Optional[str]:
        """Normalize date to ISO 8601 format"""
        try:
            from dateutil import parser
            parsed = parser.parse(date_text, fuzzy=True)
            return parsed.isoformat()
        except Exception:
            return None
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using noun chunks"""
        key_phrases = []
        if not self._nlp or not text:
            return key_phrases
        
        try:
            doc = self._nlp(text[:200000])
            
            # Extract noun chunks as key phrases
            phrases = set()
            for chunk in doc.noun_chunks:
                # Filter for meaningful phrases
                if len(chunk.text.split()) >= 2 and len(chunk.text) > 5:
                    phrases.add(chunk.text.lower())
            
            key_phrases = sorted(list(phrases))[:50]  # Top 50
            logger.debug(f"🔑 Extracted {len(key_phrases)} key phrases")
        except Exception as e:
            logger.warning(f"Key phrase extraction failed: {e}")
        
        return key_phrases
    
    async def _analyze_sentiment(self, text: str) -> Optional[Dict[str, float]]:
        """Analyze sentiment using FinBERT for financial text"""
        if not self._sentiment_pipeline or not text:
            return None
        
        try:
            # Analyze first 2000 chars for performance
            sample = text[:2000]
            result = self._sentiment_pipeline(sample)[0]
            
            sentiment = {
                'label': result['label'].lower(),
                'score': float(result['score'])
            }
            
            logger.debug(f"💭 Sentiment: {sentiment['label']} ({sentiment['score']:.2f})")
            return sentiment
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return None
    
    async def _extract_financial_indicators(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract financial indicators from text
        
        Extracts: revenue, income, assets, liabilities, cash flow, etc.
        """
        financial_data = {
            'revenue': [],
            'income': [],
            'assets': [],
            'liabilities': [],
            'cash_flow': [],
            'metrics': []
        }
        
        # Define extraction patterns
        patterns = {
            'revenue': r'(?:revenue|sales|turnover)\s+(?:of|was|:)?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
            'income': r'(?:net\s+income|earnings|profit)\s+(?:of|was|:)?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
            'assets': r'(?:total\s+)?assets?\s+(?:of|was|:)?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
            'liabilities': r'(?:total\s+)?liabilities?\s+(?:of|was|:)?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?',
            'cash_flow': r'(?:cash\s+flow|operating\s+cash)\s+(?:of|was|:)?\s*\$?\s*([\d,]+\.?\d*)\s*(billion|million|thousand)?'
        }
        
        multipliers = {
            'thousand': 1_000,
            'million': 1_000_000,
            'billion': 1_000_000_000
        }
        
        for metric_type, pattern in patterns.items():
            regex = re.compile(pattern, re.IGNORECASE)
            
            for match in regex.finditer(text):
                try:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    
                    # Apply multiplier
                    multiplier = match.group(2)
                    if multiplier:
                        mult_lower = multiplier.lower()
                        value *= multipliers.get(mult_lower, 1)
                    
                    financial_data[metric_type].append({
                        'value': value,
                        'formatted': f"${value:,.0f}",
                        'text': match.group(0)
                    })
                except (ValueError, AttributeError):
                    continue
        
        # Return None if no financial data found
        has_data = any(len(v) > 0 for v in financial_data.values() if isinstance(v, list))
        return financial_data if has_data else None
    
    def _calculate_confidence(
        self,
        base_result: ExtractionResult,
        entities: List,
        relationships: List,
        temporal_events: List
    ) -> float:
        """Calculate overall extraction confidence
        
        Factors:
        - Base extraction success (weight: 0.4)
        - Entity extraction quality (weight: 0.3)
        - Relationship extraction (weight: 0.15)
        - Temporal extraction (weight: 0.15)
        """
        weights = {
            'base': 0.4,
            'entities': 0.3,
            'relationships': 0.15,
            'temporal': 0.15
        }
        
        scores = {}
        
        # Base extraction success
        scores['base'] = 0.90 if base_result.success else 0.40
        
        # Entity extraction quality
        if len(entities) > 10:
            scores['entities'] = 0.95
        elif len(entities) > 5:
            scores['entities'] = 0.85
        elif len(entities) > 0:
            scores['entities'] = 0.70
        else:
            scores['entities'] = 0.50
        
        # Relationship extraction
        if len(relationships) > 5:
            scores['relationships'] = 0.90
        elif len(relationships) > 0:
            scores['relationships'] = 0.75
        else:
            scores['relationships'] = 0.60
        
        # Temporal extraction
        if len(temporal_events) > 3:
            scores['temporal'] = 0.85
        elif len(temporal_events) > 0:
            scores['temporal'] = 0.75
        else:
            scores['temporal'] = 0.65
        
        # Calculate weighted score
        overall = sum(scores[key] * weights[key] for key in scores)
        return round(overall, 2)
    
    def _hash_content(self, content: str) -> str:
        """Generate SHA-256 hash of content for integrity verification"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

