"""
Financial Domain NLP Models
===========================

Specialized transformer models for financial text analysis.

Models:
- FinBERT: ProsusAI/finbert - Sentiment analysis for financial text
- SEC-BERT: nlpaueb/sec-bert-base - Pre-trained on SEC filings

Use Cases:
- Financial sentiment analysis
- SEC filing-specific embeddings
- Domain-specific text classification
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available. Using mock mode.")


class Sentiment(Enum):
    """Financial sentiment classification."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    text: str
    sentiment: Sentiment
    confidence: float
    scores: Dict[str, float]  # All class scores
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "sentiment": self.sentiment.value,
            "confidence": round(self.confidence, 4),
            "scores": {k: round(v, 4) for k, v in self.scores.items()}
        }


class FinBERTAnalyzer:
    """
    FinBERT financial sentiment analyzer.
    
    Model: ProsusAI/finbert
    - Fine-tuned on financial text (earnings calls, news, analyst reports)
    - 3-class sentiment: positive, negative, neutral
    - ~94% accuracy on Financial PhraseBank
    
    Example:
        analyzer = FinBERTAnalyzer()
        result = analyzer.analyze("Revenue increased by 25% year-over-year")
        print(f"Sentiment: {result.sentiment.value}, Confidence: {result.confidence}")
    """
    
    MODEL_NAME = "ProsusAI/finbert"
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize FinBERT analyzer.
        
        Args:
            use_gpu: Use GPU acceleration if available
        """
        self.use_gpu = use_gpu
        
        if TRANSFORMERS_AVAILABLE:
            self.mock_mode = False
            try:
                logger.info(f"Loading FinBERT: {self.MODEL_NAME}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
                self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
                
                if use_gpu and torch.cuda.is_available():
                    self.model = self.model.to('cuda')
                
                self.device = 'cuda' if (use_gpu and torch.cuda.is_available()) else 'cpu'
                
            except Exception as e:
                logger.error(f"Failed to load FinBERT: {e}")
                self.mock_mode = True
        else:
            self.mock_mode = True
    
    def analyze(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of financial text.
        
        Args:
            text: Financial text to analyze
            
        Returns:
            SentimentResult with sentiment and confidence
        """
        if self.mock_mode:
            return self._mock_analyze(text)
        
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        if self.device == 'cuda':
            inputs = {k: v.to('cuda') for k, v in inputs.items()}
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Convert to probabilities
        probs = torch.softmax(logits, dim=1)[0]
        
        # Get sentiment (labels: positive, negative, neutral)
        labels = ["positive", "negative", "neutral"]
        scores = {label: float(probs[i]) for i, label in enumerate(labels)}
        
        # Get max confidence sentiment
        max_idx = torch.argmax(probs).item()
        sentiment = Sentiment(labels[max_idx])
        confidence = float(probs[max_idx])
        
        return SentimentResult(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            scores=scores
        )
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze multiple texts in batch.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of SentimentResult objects
        """
        if self.mock_mode:
            return [self._mock_analyze(text) for text in texts]
        
        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        if self.device == 'cuda':
            inputs = {k: v.to('cuda') for k, v in inputs.items()}
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        # Convert to probabilities
        probs = torch.softmax(logits, dim=1)
        
        # Build results
        labels = ["positive", "negative", "neutral"]
        results = []
        
        for i, text in enumerate(texts):
            text_probs = probs[i]
            scores = {label: float(text_probs[j]) for j, label in enumerate(labels)}
            
            max_idx = torch.argmax(text_probs).item()
            sentiment = Sentiment(labels[max_idx])
            confidence = float(text_probs[max_idx])
            
            results.append(SentimentResult(
                text=text,
                sentiment=sentiment,
                confidence=confidence,
                scores=scores
            ))
        
        return results
    
    def _mock_analyze(self, text: str) -> SentimentResult:
        """Mock sentiment analysis."""
        return SentimentResult(
            text=text,
            sentiment=Sentiment.NEUTRAL,
            confidence=0.6,
            scores={"positive": 0.2, "negative": 0.2, "neutral": 0.6}
        )


class SECBERTEmbedder:
    """
    SEC-BERT embeddings for SEC filings.
    
    Model: nlpaueb/sec-bert-base
    - Pre-trained on SEC filings (10-K, 10-Q, 8-K)
    - Better for SEC-specific text than general BERT
    - 768-dimensional embeddings
    
    Example:
        embedder = SECBERTEmbedder()
        embedding = embedder.embed("Management discussion and analysis...")
        # Use embedding for similarity, clustering, etc.
    """
    
    MODEL_NAME = "nlpaueb/sec-bert-base"
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize SEC-BERT embedder.
        
        Args:
            use_gpu: Use GPU acceleration if available
        """
        self.use_gpu = use_gpu
        
        if TRANSFORMERS_AVAILABLE:
            self.mock_mode = False
            try:
                logger.info(f"Loading SEC-BERT: {self.MODEL_NAME}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
                self.model = AutoModel.from_pretrained(self.MODEL_NAME)
                
                if use_gpu and torch.cuda.is_available():
                    self.model = self.model.to('cuda')
                
                self.device = 'cuda' if (use_gpu and torch.cuda.is_available()) else 'cpu'
                
            except Exception as e:
                logger.error(f"Failed to load SEC-BERT: {e}")
                self.mock_mode = True
        else:
            self.mock_mode = True
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            768-dimensional embedding vector
        """
        if self.mock_mode:
            return [0.0] * 768
        
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        if self.device == 'cuda':
            inputs = {k: v.to('cuda') for k, v in inputs.items()}
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use [CLS] token embedding
            embedding = outputs.last_hidden_state[0, 0, :]
        
        return embedding.cpu().numpy().tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.mock_mode:
            return [[0.0] * 768 for _ in texts]
        
        # Tokenize batch
        inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        if self.device == 'cuda':
            inputs = {k: v.to('cuda') for k, v in inputs.items()}
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use [CLS] token embeddings
            embeddings = outputs.last_hidden_state[:, 0, :]
        
        return embeddings.cpu().numpy().tolist()
