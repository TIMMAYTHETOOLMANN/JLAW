"""
Embedding Pipeline for SEC Documents
======================================

Provides document embedding capabilities using sentence transformers
and integration with the chunking pipeline.
"""

import os
import logging
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

# Try to import sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available")

# Try to import OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@dataclass
class EmbeddingResult:
    """Result of embedding operation."""
    text: str
    embedding: List[float]
    model: str
    token_count: int
    cache_hit: bool = False


class BaseEmbedder:
    """Base class for embedders."""
    
    def __init__(self, model_name: str, dimension: int):
        self.model_name = model_name
        self.dimension = dimension
        self._cache: Dict[str, List[float]] = {}
    
    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        raise NotImplementedError
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        raise NotImplementedError
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a query (may use different prompt)."""
        return self.embed(query)
    
    def _get_cache_key(self, text: str) -> str:
        """Get cache key for text."""
        return hashlib.md5(f"{self.model_name}:{text}".encode()).hexdigest()
    
    def _check_cache(self, text: str) -> Optional[List[float]]:
        """Check if embedding is cached."""
        key = self._get_cache_key(text)
        return self._cache.get(key)
    
    def _store_cache(self, text: str, embedding: List[float]):
        """Store embedding in cache."""
        key = self._get_cache_key(text)
        self._cache[key] = embedding


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Embedder using Sentence Transformers.
    
    Recommended models for SEC documents:
    - all-mpnet-base-v2 (768d, best quality)
    - all-MiniLM-L6-v2 (384d, faster)
    - multi-qa-mpnet-base-dot-v1 (768d, optimized for QA)
    """
    
    DEFAULT_MODEL = "sentence-transformers/all-mpnet-base-v2"
    
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: Optional[str] = None,
        cache_embeddings: bool = True
    ):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers is required")
        
        self.model = SentenceTransformer(model_name, device=device)
        dimension = self.model.get_sentence_embedding_dimension()
        
        super().__init__(model_name, dimension)
        self.cache_embeddings = cache_embeddings
        
        logger.info(f"SentenceTransformerEmbedder initialized: {model_name} (dim={dimension})")
    
    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        if self.cache_embeddings:
            cached = self._check_cache(text)
            if cached:
                return cached
        
        embedding = self.model.encode(text, convert_to_numpy=True).tolist()
        
        if self.cache_embeddings:
            self._store_cache(text, embedding)
        
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed multiple texts."""
        # Check cache for each text
        results = []
        texts_to_embed = []
        cache_indices = []
        
        if self.cache_embeddings:
            for i, text in enumerate(texts):
                cached = self._check_cache(text)
                if cached:
                    results.append((i, cached))
                else:
                    texts_to_embed.append(text)
                    cache_indices.append(i)
        else:
            texts_to_embed = texts
            cache_indices = list(range(len(texts)))
        
        # Embed remaining texts
        if texts_to_embed:
            embeddings = self.model.encode(
                texts_to_embed,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(texts_to_embed) > 100
            ).tolist()
            
            for i, (text, embedding) in enumerate(zip(texts_to_embed, embeddings)):
                idx = cache_indices[i]
                results.append((idx, embedding))
                if self.cache_embeddings:
                    self._store_cache(text, embedding)
        
        # Sort by original index
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a query with optional prefix."""
        # Some models benefit from query prefixes
        if "multi-qa" in self.model_name:
            query = f"query: {query}"
        return self.embed(query)


class OpenAIEmbedder(BaseEmbedder):
    """
    Embedder using OpenAI API.
    
    Models:
    - text-embedding-3-small (1536d, cheaper)
    - text-embedding-3-large (3072d, best quality)
    - text-embedding-ada-002 (1536d, legacy)
    """
    
    DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536
    }
    
    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        cache_embeddings: bool = True
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required")
        
        dimension = self.DIMENSIONS.get(model_name, 1536)
        super().__init__(model_name, dimension)
        
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.cache_embeddings = cache_embeddings
        
        logger.info(f"OpenAIEmbedder initialized: {model_name} (dim={dimension})")
    
    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        if self.cache_embeddings:
            cached = self._check_cache(text)
            if cached:
                return cached
        
        response = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        embedding = response.data[0].embedding
        
        if self.cache_embeddings:
            self._store_cache(text, embedding)
        
        return embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Embed multiple texts."""
        # Check cache
        results = []
        texts_to_embed = []
        cache_indices = []
        
        if self.cache_embeddings:
            for i, text in enumerate(texts):
                cached = self._check_cache(text)
                if cached:
                    results.append((i, cached))
                else:
                    texts_to_embed.append(text)
                    cache_indices.append(i)
        else:
            texts_to_embed = texts
            cache_indices = list(range(len(texts)))
        
        # Embed in batches
        for batch_start in range(0, len(texts_to_embed), batch_size):
            batch = texts_to_embed[batch_start:batch_start + batch_size]
            
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch
            )
            
            for j, data in enumerate(response.data):
                idx = cache_indices[batch_start + j]
                embedding = data.embedding
                results.append((idx, embedding))
                
                if self.cache_embeddings:
                    self._store_cache(batch[j], embedding)
        
        # Sort by original index
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]


class SECEmbedder:
    """
    SEC-optimized embedder with specialized preprocessing.
    
    Adds SEC-specific context and normalization before embedding.
    """
    
    def __init__(
        self,
        embedder: Optional[BaseEmbedder] = None,
        model_name: str = "sentence-transformers/all-mpnet-base-v2",
        add_sec_context: bool = True
    ):
        """
        Initialize SEC embedder.
        
        Args:
            embedder: Base embedder (creates default if None)
            model_name: Model name for default embedder
            add_sec_context: Whether to add SEC-specific context
        """
        if embedder:
            self.embedder = embedder
        else:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedder = SentenceTransformerEmbedder(model_name)
            elif OPENAI_AVAILABLE:
                self.embedder = OpenAIEmbedder()
            else:
                raise ImportError("No embedding library available")
        
        self.add_sec_context = add_sec_context
        self.dimension = self.embedder.dimension
    
    def preprocess(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Preprocess text with SEC context."""
        if not self.add_sec_context or not metadata:
            return text
        
        # Add filing context
        context_parts = []
        
        if 'filing_type' in metadata:
            context_parts.append(f"SEC Filing Type: {metadata['filing_type']}")
        if 'section' in metadata:
            context_parts.append(f"Section: {metadata['section']}")
        if 'company_name' in metadata:
            context_parts.append(f"Company: {metadata['company_name']}")
        
        if context_parts:
            context = " | ".join(context_parts)
            return f"[{context}] {text}"
        
        return text
    
    def embed(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[float]:
        """Embed text with SEC preprocessing."""
        processed = self.preprocess(text, metadata)
        return self.embedder.embed(processed)
    
    def embed_batch(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[List[float]]:
        """Embed multiple texts with preprocessing."""
        if metadatas:
            processed = [
                self.preprocess(text, meta)
                for text, meta in zip(texts, metadatas)
            ]
        else:
            processed = texts
        
        return self.embedder.embed_batch(processed)
    
    def embed_query(self, query: str) -> List[float]:
        """Embed a search query."""
        return self.embedder.embed_query(query)


class EmbeddingPipeline:
    """
    Complete embedding pipeline for SEC documents.
    
    Handles chunking, embedding, and storage in a single pipeline.
    """
    
    def __init__(
        self,
        embedder: Optional[SECEmbedder] = None,
        vector_store=None,
        batch_size: int = 32
    ):
        """
        Initialize embedding pipeline.
        
        Args:
            embedder: SEC embedder instance
            vector_store: Vector store for persistence
            batch_size: Batch size for embedding
        """
        self.embedder = embedder or SECEmbedder()
        self.vector_store = vector_store
        self.batch_size = batch_size
    
    def process_document(
        self,
        document,
        chunker=None
    ) -> Dict[str, Any]:
        """
        Process a document through the full pipeline.
        
        Args:
            document: ParsedDocument instance
            chunker: Optional chunker (uses default if None)
            
        Returns:
            Processing result with chunk IDs
        """
        from ..docsgpt.sec_chunking import SECChunker
        
        # Chunk document
        if chunker is None:
            chunker = SECChunker()
        
        chunks = chunker.chunk_document(document)
        
        # Prepare for embedding
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata.to_dict() if hasattr(chunk.metadata, 'to_dict') else {} for chunk in chunks]
        
        # Add document-level metadata
        for meta in metadatas:
            meta['doc_id'] = document.doc_id
            meta['source_path'] = document.source_path
            if document.filing_type:
                meta['filing_type'] = document.filing_type.value
        
        # Generate embeddings
        embeddings = self.embedder.embed_batch(texts, metadatas)
        
        # Store if vector store configured
        chunk_ids = []
        if self.vector_store:
            ids = [chunk.metadata.chunk_id for chunk in chunks]
            chunk_ids = self.vector_store.add_documents(
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        
        return {
            'doc_id': document.doc_id,
            'num_chunks': len(chunks),
            'chunk_ids': chunk_ids,
            'total_tokens': sum(
                chunk.metadata.token_count for chunk in chunks
            )
        }
    
    def process_batch(
        self,
        documents: List,
        chunker=None
    ) -> List[Dict[str, Any]]:
        """Process multiple documents."""
        results = []
        for doc in documents:
            try:
                result = self.process_document(doc, chunker)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process document {doc.doc_id}: {e}")
                results.append({
                    'doc_id': doc.doc_id,
                    'error': str(e)
                })
        
        return results
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ):
        """Search for similar documents."""
        if not self.vector_store:
            raise ValueError("No vector store configured")
        
        query_embedding = self.embedder.embed_query(query)
        return self.vector_store.search(query_embedding, top_k, filter_dict)

