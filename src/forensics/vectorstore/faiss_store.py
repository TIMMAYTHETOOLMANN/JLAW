"""
FAISS Vector Store Implementation
==================================

High-performance vector store using Facebook AI Similarity Search (FAISS).
Optimized for SEC filing semantic search with metadata filtering.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    FAISS_AVAILABLE = False
    logger.warning("faiss not available, install with: pip install faiss-cpu")


from .vector_creator import VectorStore, SearchResult


@dataclass
class StoredDocument:
    """Document stored in FAISS index."""
    id: str
    text: str
    metadata: Dict[str, Any]


class FAISSVectorStore(VectorStore):
    """
    FAISS-based vector store for SEC filings.
    
    Features:
    - High-performance similarity search
    - Metadata filtering
    - Persistence to disk
    - Multiple index types (Flat, IVF, HNSW)
    
    Usage:
        store = FAISSVectorStore(dimension=768, index_type="IVF")
        store.add_documents(texts, embeddings, metadatas)
        results = store.search(query_embedding, top_k=10)
        store.save("./index")
    """
    
    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "Flat",
        nlist: int = 100,
        index_path: Optional[str] = None,
        metric: str = "cosine"
    ):
        """
        Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension
            index_type: Index type (Flat, IVF, HNSW)
            nlist: Number of clusters for IVF
            index_path: Path for persistence
            metric: Distance metric (cosine, l2)
        """
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS is required. Install with: pip install faiss-cpu")
        if not NUMPY_AVAILABLE:
            raise ImportError("numpy is required")
        
        self.dimension = dimension
        self.index_type = index_type
        self.nlist = nlist
        self.index_path = index_path
        self.metric = metric
        
        # Create index
        self.index = self._create_index()
        
        # Document storage
        self.documents: Dict[int, StoredDocument] = {}
        self.id_to_idx: Dict[str, int] = {}
        self.idx_to_id: Dict[int, str] = {}
        self.next_idx = 0
        
        # Load if path exists
        if index_path and Path(index_path).exists():
            self.load(index_path)
        
        logger.info(f"FAISSVectorStore initialized: dim={dimension}, type={index_type}")
    
    def _create_index(self):
        """Create FAISS index based on configuration."""
        if self.metric == "cosine":
            # For cosine similarity, we normalize and use inner product
            if self.index_type == "Flat":
                index = faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "IVF":
                quantizer = faiss.IndexFlatIP(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist, faiss.METRIC_INNER_PRODUCT)
            elif self.index_type == "HNSW":
                index = faiss.IndexHNSWFlat(self.dimension, 32, faiss.METRIC_INNER_PRODUCT)
            else:
                index = faiss.IndexFlatIP(self.dimension)
        else:
            # L2 distance
            if self.index_type == "Flat":
                index = faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "IVF":
                quantizer = faiss.IndexFlatL2(self.dimension)
                index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
            elif self.index_type == "HNSW":
                index = faiss.IndexHNSWFlat(self.dimension, 32)
            else:
                index = faiss.IndexFlatL2(self.dimension)
        
        return index
    
    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity."""
        if self.metric == "cosine":
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            return vectors / norms
        return vectors
    
    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents with embeddings to the store."""
        if not texts or not embeddings:
            return []
        
        n_docs = len(texts)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [
                hashlib.md5(f"{text[:100]}_{i}".encode()).hexdigest()[:16]
                for i, text in enumerate(texts)
            ]
        
        # Prepare embeddings
        vectors = np.array(embeddings, dtype=np.float32)
        vectors = self._normalize(vectors)
        
        # Train index if needed (for IVF)
        if self.index_type == "IVF" and not self.index.is_trained:
            if len(vectors) >= self.nlist:
                self.index.train(vectors)
            else:
                # Not enough vectors, use flat index temporarily
                logger.warning(f"Not enough vectors ({len(vectors)}) to train IVF, using flat search")
                self.index = faiss.IndexFlatIP(self.dimension) if self.metric == "cosine" else faiss.IndexFlatL2(self.dimension)
        
        # Add to index
        self.index.add(vectors)
        
        # Store documents
        metadatas = metadatas or [{} for _ in range(n_docs)]
        
        for i, (text, metadata, doc_id) in enumerate(zip(texts, metadatas, ids)):
            idx = self.next_idx
            self.documents[idx] = StoredDocument(
                id=doc_id,
                text=text,
                metadata=metadata
            )
            self.id_to_idx[doc_id] = idx
            self.idx_to_id[idx] = doc_id
            self.next_idx += 1
        
        logger.info(f"Added {n_docs} documents to FAISS index (total: {self.count()})")
        return ids
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar documents."""
        if self.count() == 0:
            return []
        
        # Prepare query
        query = np.array([query_embedding], dtype=np.float32)
        query = self._normalize(query)
        
        # Search with extra results if filtering
        search_k = top_k * 3 if filter_dict else top_k
        search_k = min(search_k, self.count())
        
        # Perform search
        distances, indices = self.index.search(query, search_k)
        
        results = []
        for score, idx in zip(distances[0], indices[0]):
            if idx == -1:  # Invalid result
                continue
            
            if idx not in self.documents:
                continue
            
            doc = self.documents[idx]
            
            # Apply metadata filter
            if filter_dict:
                if not self._matches_filter(doc.metadata, filter_dict):
                    continue
            
            # Convert distance to score
            if self.metric == "cosine":
                # Inner product of normalized vectors = cosine similarity
                similarity = float(score)
            else:
                # Convert L2 distance to similarity
                similarity = 1.0 / (1.0 + float(score))
            
            results.append(SearchResult(
                doc_id=doc.metadata.get('doc_id', doc.id),
                chunk_id=doc.id,
                text=doc.text,
                score=similarity,
                metadata=doc.metadata
            ))
            
            if len(results) >= top_k:
                break
        
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria."""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                # Match any in list
                if metadata[key] not in value:
                    return False
            elif isinstance(value, dict):
                # Handle operators
                meta_val = metadata[key]
                for op, op_val in value.items():
                    if op == "$gt" and not meta_val > op_val:
                        return False
                    elif op == "$gte" and not meta_val >= op_val:
                        return False
                    elif op == "$lt" and not meta_val < op_val:
                        return False
                    elif op == "$lte" and not meta_val <= op_val:
                        return False
                    elif op == "$ne" and meta_val == op_val:
                        return False
                    elif op == "$in" and meta_val not in op_val:
                        return False
            else:
                # Exact match
                if metadata[key] != value:
                    return False
        
        return True
    
    def delete(self, ids: List[str]) -> bool:
        """Delete documents by ID (marks as deleted, doesn't rebuild index)."""
        for doc_id in ids:
            if doc_id in self.id_to_idx:
                idx = self.id_to_idx[doc_id]
                del self.documents[idx]
                del self.id_to_idx[doc_id]
                del self.idx_to_id[idx]
        
        logger.info(f"Deleted {len(ids)} documents")
        return True
    
    def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get documents by ID."""
        results = []
        for doc_id in ids:
            if doc_id in self.id_to_idx:
                idx = self.id_to_idx[doc_id]
                doc = self.documents[idx]
                results.append({
                    'id': doc.id,
                    'text': doc.text,
                    'metadata': doc.metadata
                })
        return results
    
    def count(self) -> int:
        """Get total document count."""
        return len(self.documents)
    
    def save(self, path: str):
        """Save index and documents to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        # Save documents and mappings
        with open(path / "documents.pkl", 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'id_to_idx': self.id_to_idx,
                'idx_to_id': self.idx_to_id,
                'next_idx': self.next_idx,
                'config': {
                    'dimension': self.dimension,
                    'index_type': self.index_type,
                    'nlist': self.nlist,
                    'metric': self.metric
                }
            }, f)
        
        logger.info(f"Saved FAISS index to {path}")
    
    def load(self, path: str):
        """Load index and documents from disk."""
        path = Path(path)
        
        if not (path / "index.faiss").exists():
            logger.warning(f"No index found at {path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(path / "index.faiss"))
        
        # Load documents and mappings
        with open(path / "documents.pkl", 'rb') as f:
            data = pickle.load(f)
            self.documents = data['documents']
            self.id_to_idx = data['id_to_idx']
            self.idx_to_id = data['idx_to_id']
            self.next_idx = data['next_idx']
        
        logger.info(f"Loaded FAISS index from {path} ({self.count()} documents)")
    
    def rebuild_index(self):
        """Rebuild index from stored documents (useful after deletions)."""
        if not self.documents:
            return
        
        # Get all embeddings
        # Note: FAISS doesn't store embeddings, this requires re-embedding
        logger.warning("Index rebuild requires re-embedding documents")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            'total_documents': self.count(),
            'dimension': self.dimension,
            'index_type': self.index_type,
            'metric': self.metric,
            'is_trained': getattr(self.index, 'is_trained', True)
        }

