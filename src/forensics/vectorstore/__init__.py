"""
Vector Store Integration Module
================================

Provides vector storage capabilities for semantic search across SEC filings.
Integrates DocsGPT's vector store implementations with JLAW's forensic analysis.

Supported Stores:
- FAISS (default, in-memory/file-based)
- MongoDB (with vector search)
- Elasticsearch
- Qdrant
- Milvus
- PGVector
"""

from .vector_creator import VectorStoreFactory, VectorStore
from .embedding_pipeline import EmbeddingPipeline, SECEmbedder
from .faiss_store import FAISSVectorStore

__all__ = [
    'VectorStoreFactory',
    'VectorStore',
    'EmbeddingPipeline',
    'SECEmbedder',
    'FAISSVectorStore',
]

