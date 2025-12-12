"""
DocsGPT Integration - Vector Store Module
=========================================

Provides vector storage and semantic search capabilities:
- FAISS in-memory vector store (default)
- Embedding generation via OpenAI or local models
- SEC filing semantic search across documents
- Cross-filing contradiction detection

Based on DocsGPT vector_store patterns.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Document stored in vector database."""
    doc_id: str
    chunk_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # SEC-specific fields
    cik: Optional[str] = None
    accession_number: Optional[str] = None
    filing_type: Optional[str] = None
    filing_date: Optional[datetime] = None
    section: Optional[str] = None


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    doc_id: str
    chunk_id: str
    text: str
    score: float  # Similarity score (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "text": self.text[:500] + "..." if len(self.text) > 500 else self.text,
            "score": round(self.score, 4),
            "metadata": self.metadata
        }


class EmbeddingGenerator:
    """
    Generate embeddings using OpenAI or local models.
    """
    
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                import os
                self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                logger.warning("OpenAI not installed, embeddings unavailable")
                self._client = None
        return self._client
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for list of texts."""
        if not self.client:
            # Fallback: return random embeddings for testing
            return [self._random_embedding() for _ in texts]
        
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [e.embedding for e in response.data]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return [self._random_embedding() for _ in texts]
    
    def embed_single(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        return self.embed([text])[0]
    
    def _random_embedding(self, dim: int = 1536) -> List[float]:
        """Generate random embedding for testing."""
        vec = np.random.randn(dim)
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()


class FAISSVectorStore:
    """
    FAISS-based vector store for SEC document embeddings.
    
    Provides:
    - Fast similarity search
    - In-memory storage (no external DB required)
    - Metadata filtering
    """
    
    def __init__(self, embedding_dim: int = 1536):
        self.embedding_dim = embedding_dim
        self.embeddings: List[np.ndarray] = []
        self.documents: List[VectorDocument] = []
        self._index = None
        self._faiss_available = False
        
        try:
            import faiss
            self._faiss_available = True
        except ImportError:
            logger.warning("FAISS not installed, using numpy fallback")
    
    def add_documents(self, documents: List[VectorDocument]) -> int:
        """Add documents to the vector store."""
        for doc in documents:
            self.documents.append(doc)
            self.embeddings.append(np.array(doc.embedding, dtype=np.float32))
        
        # Rebuild index
        self._build_index()
        
        return len(documents)
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_cik: Optional[str] = None,
        filter_filing_type: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_cik: Filter by company CIK
            filter_filing_type: Filter by filing type
            min_score: Minimum similarity score
            
        Returns:
            List of SearchResult sorted by similarity
        """
        if not self.documents:
            return []
        
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        if self._faiss_available and self._index is not None:
            return self._faiss_search(query_vec, top_k, filter_cik, filter_filing_type, min_score)
        else:
            return self._numpy_search(query_vec, top_k, filter_cik, filter_filing_type, min_score)
    
    def search_by_text(
        self,
        query_text: str,
        embedder: EmbeddingGenerator,
        top_k: int = 10,
        **filters
    ) -> List[SearchResult]:
        """Search by text query (generates embedding automatically)."""
        query_embedding = embedder.embed_single(query_text)
        return self.search(query_embedding, top_k, **filters)
    
    def find_contradictions(
        self,
        statement_embedding: List[float],
        source_accession: str,
        top_k: int = 20,
        threshold: float = 0.7
    ) -> List[Tuple[SearchResult, float]]:
        """
        Find potentially contradicting statements across filings.
        
        Returns results from OTHER filings that are semantically similar
        (which may indicate contradictions or changes).
        """
        results = self.search(statement_embedding, top_k=top_k, min_score=threshold)
        
        # Filter out results from the same filing
        contradictions = []
        for result in results:
            if result.metadata.get('accession_number') != source_accession:
                contradiction_score = result.score  # High similarity = potential contradiction
                contradictions.append((result, contradiction_score))
        
        return contradictions
    
    def _build_index(self):
        """Build FAISS index from embeddings."""
        if not self.embeddings:
            return
        
        if self._faiss_available:
            import faiss
            
            embeddings_matrix = np.vstack(self.embeddings)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_matrix)
            
            # Build index
            self._index = faiss.IndexFlatIP(self.embedding_dim)
            self._index.add(embeddings_matrix)
    
    def _faiss_search(
        self,
        query: np.ndarray,
        top_k: int,
        filter_cik: Optional[str],
        filter_filing_type: Optional[str],
        min_score: float
    ) -> List[SearchResult]:
        """Search using FAISS index."""
        import faiss
        
        # Normalize query
        query = query.reshape(1, -1)
        faiss.normalize_L2(query)
        
        # Search
        scores, indices = self._index.search(query, min(top_k * 3, len(self.documents)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or score < min_score:
                continue
            
            doc = self.documents[idx]
            
            # Apply filters
            if filter_cik and doc.cik != filter_cik:
                continue
            if filter_filing_type and doc.filing_type != filter_filing_type:
                continue
            
            results.append(SearchResult(
                doc_id=doc.doc_id,
                chunk_id=doc.chunk_id,
                text=doc.text,
                score=float(score),
                metadata={
                    'cik': doc.cik,
                    'accession_number': doc.accession_number,
                    'filing_type': doc.filing_type,
                    'section': doc.section
                }
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _numpy_search(
        self,
        query: np.ndarray,
        top_k: int,
        filter_cik: Optional[str],
        filter_filing_type: Optional[str],
        min_score: float
    ) -> List[SearchResult]:
        """Fallback search using numpy."""
        # Normalize query
        query = query / np.linalg.norm(query)
        
        # Calculate similarities
        similarities = []
        for i, emb in enumerate(self.embeddings):
            emb_norm = emb / np.linalg.norm(emb)
            sim = float(np.dot(query, emb_norm))
            similarities.append((i, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in similarities:
            if score < min_score:
                continue
            
            doc = self.documents[idx]
            
            if filter_cik and doc.cik != filter_cik:
                continue
            if filter_filing_type and doc.filing_type != filter_filing_type:
                continue
            
            results.append(SearchResult(
                doc_id=doc.doc_id,
                chunk_id=doc.chunk_id,
                text=doc.text,
                score=score,
                metadata={
                    'cik': doc.cik,
                    'accession_number': doc.accession_number,
                    'filing_type': doc.filing_type,
                    'section': doc.section
                }
            ))
            
            if len(results) >= top_k:
                break
        
        return results


class SECVectorSearchEngine:
    """
    High-level semantic search engine for SEC filings.
    
    Combines document parsing, embedding generation, and vector search
    for comprehensive SEC document analysis.
    """
    
    def __init__(self):
        self.vector_store = FAISSVectorStore()
        self.embedder = EmbeddingGenerator()
    
    def index_filing(
        self,
        chunks: List[Dict[str, Any]],
        cik: str,
        accession_number: str,
        filing_type: str,
        filing_date: datetime
    ) -> int:
        """
        Index a parsed SEC filing into the vector store.
        
        Args:
            chunks: List of document chunks from DocumentParser
            cik: Company CIK
            accession_number: SEC accession number
            filing_type: Filing type (10-K, 10-Q, etc.)
            filing_date: Filing date
            
        Returns:
            Number of chunks indexed
        """
        texts = [c.get('text', '') for c in chunks]
        embeddings = self.embedder.embed(texts)
        
        docs = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            docs.append(VectorDocument(
                doc_id=f"{accession_number}",
                chunk_id=chunk.get('chunk_id', f"{accession_number}_chunk_{i}"),
                text=chunk.get('text', ''),
                embedding=embedding,
                cik=cik,
                accession_number=accession_number,
                filing_type=filing_type,
                filing_date=filing_date,
                section=chunk.get('section')
            ))
        
        return self.vector_store.add_documents(docs)
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        cik: Optional[str] = None,
        filing_type: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search across all indexed SEC filings.
        """
        return self.vector_store.search_by_text(
            query_text=query,
            embedder=self.embedder,
            top_k=top_k,
            filter_cik=cik,
            filter_filing_type=filing_type
        )
    
    def find_cross_filing_references(
        self,
        statement: str,
        source_accession: str,
        cik: str
    ) -> List[SearchResult]:
        """
        Find related statements across other filings from the same company.
        
        Useful for:
        - Tracking guidance changes
        - Finding contradictions
        - Temporal analysis
        """
        embedding = self.embedder.embed_single(statement)
        
        results = self.vector_store.search(
            query_embedding=embedding,
            top_k=20,
            filter_cik=cik,
            min_score=0.6
        )
        
        # Exclude source filing
        return [r for r in results if r.metadata.get('accession_number') != source_accession]

