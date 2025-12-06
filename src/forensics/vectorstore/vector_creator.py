"""
Vector Store Factory and Base Classes
======================================

Factory pattern for creating vector stores with unified interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Type, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    doc_id: str
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'doc_id': self.doc_id,
            'chunk_id': self.chunk_id,
            'text': self.text,
            'score': self.score,
            'metadata': self.metadata
        }


@dataclass
class SECFilingMetadata:
    """
    Metadata schema for SEC filing documents in vector store.
    """
    cik: str
    company_name: str
    filing_type: str
    filing_date: str
    accession_number: str
    fiscal_period: Optional[str] = None
    section: Optional[str] = None
    chunk_index: int = 0
    total_chunks: int = 1
    token_count: int = 0
    risk_score: Optional[float] = None
    hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cik': self.cik,
            'company_name': self.company_name,
            'filing_type': self.filing_type,
            'filing_date': self.filing_date,
            'accession_number': self.accession_number,
            'fiscal_period': self.fiscal_period,
            'section': self.section,
            'chunk_index': self.chunk_index,
            'total_chunks': self.total_chunks,
            'token_count': self.token_count,
            'risk_score': self.risk_score,
            'hash': self.hash
        }


class VectorStore(ABC):
    """
    Abstract base class for vector stores.
    
    All vector store implementations must inherit from this class
    and implement the required methods.
    """
    
    @abstractmethod
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents with embeddings to the store.
        
        Args:
            texts: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
            
        Returns:
            List of document IDs
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """Delete documents by ID."""
        pass
    
    @abstractmethod
    def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get documents by ID."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total document count."""
        pass
    
    @abstractmethod
    def save(self, path: str):
        """Save store to disk."""
        pass
    
    @abstractmethod
    def load(self, path: str):
        """Load store from disk."""
        pass
    
    def search_by_text(
        self,
        query: str,
        embedder,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search using text query (auto-embeds).
        
        Args:
            query: Text query
            embedder: Embedder instance
            top_k: Number of results
            filter_dict: Optional metadata filters
            
        Returns:
            List of SearchResult objects
        """
        query_embedding = embedder.embed_query(query)
        return self.search(query_embedding, top_k, filter_dict)


class VectorStoreFactory:
    """
    Factory for creating vector store instances.
    
    Usage:
        store = VectorStoreFactory.create("faiss", index_path="./indices")
        store.add_documents(texts, embeddings, metadatas)
        results = store.search(query_embedding, top_k=10)
    """
    
    _stores: Dict[str, Type[VectorStore]] = {}
    
    @classmethod
    def register(cls, name: str, store_class: Type[VectorStore]):
        """Register a vector store implementation."""
        cls._stores[name.lower()] = store_class
    
    @classmethod
    def create(cls, store_type: str, **kwargs) -> VectorStore:
        """
        Create a vector store instance.
        
        Args:
            store_type: Type of store (faiss, mongodb, elasticsearch, etc.)
            **kwargs: Store-specific configuration
            
        Returns:
            VectorStore instance
        """
        store_type = store_type.lower()
        
        # Try to get from registered stores
        if store_type in cls._stores:
            return cls._stores[store_type](**kwargs)
        
        # Try to import from DocsGPT
        try:
            if store_type == "faiss":
                from .faiss_store import FAISSVectorStore
                return FAISSVectorStore(**kwargs)
            elif store_type == "mongodb":
                from .mongodb_store import MongoDBVectorStore
                return MongoDBVectorStore(**kwargs)
            elif store_type == "elasticsearch":
                from .elasticsearch_store import ElasticsearchVectorStore
                return ElasticsearchVectorStore(**kwargs)
            else:
                raise ValueError(f"Unknown vector store type: {store_type}")
        except ImportError as e:
            logger.error(f"Failed to import vector store {store_type}: {e}")
            raise
    
    @classmethod
    def available_stores(cls) -> List[str]:
        """Get list of available store types."""
        return list(cls._stores.keys()) + ["faiss", "mongodb", "elasticsearch"]


# Register default stores
try:
    from .faiss_store import FAISSVectorStore
    VectorStoreFactory.register("faiss", FAISSVectorStore)
except ImportError:
    pass

