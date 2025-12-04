"""
Legal Search Module - Phase 3
============================
In-memory full-text legal search implementation.

This module provides a lightweight search index for legal documents
without requiring external dependencies like Elasticsearch.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    document_id: str
    document_type: str
    title: str
    full_text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)


@dataclass
class IndexedDocument:
    """Indexed legal document"""
    document_id: str
    document_type: str
    title: str
    full_text: str
    metadata: Dict[str, Any]
    indexed_at: datetime
    
    # Tokenized content for search
    tokens: Set[str] = field(default_factory=set)
    title_tokens: Set[str] = field(default_factory=set)


class ElasticsearchLegalIndex:
    """
    In-memory legal document search index
    
    Features:
    - Full-text search with TF-IDF-like scoring
    - Document type filtering
    - Citation-aware search
    - Statute number search
    - Statistics tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize search index"""
        self.config = config or {}
        
        # Document storage
        self._documents: Dict[str, IndexedDocument] = {}
        
        # Inverted index for fast search
        self._inverted_index: Dict[str, Set[str]] = {}  # token -> doc_ids
        
        # Statistics
        self._stats = {
            'documents_indexed': 0,
            'total_tokens': 0,
            'searches_performed': 0,
            'by_type': {}
        }
        
        logger.info("✅ ElasticsearchLegalIndex initialized (in-memory)")
    
    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text for indexing/search"""
        if not text:
            return set()
        
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        
        # Filter out very short tokens
        tokens = {t for t in tokens if len(t) >= 2}
        
        return tokens
    
    def index_document(
        self,
        document_id: str,
        document_type: str,
        title: str,
        full_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Index a legal document
        
        Args:
            document_id: Unique document identifier
            document_type: Type of document (statute, regulation, case)
            title: Document title
            full_text: Full document text
            metadata: Additional metadata
        
        Returns:
            Document ID
        """
        # Tokenize content
        tokens = self._tokenize(full_text)
        title_tokens = self._tokenize(title)
        all_tokens = tokens | title_tokens
        
        # Create indexed document
        doc = IndexedDocument(
            document_id=document_id,
            document_type=document_type,
            title=title,
            full_text=full_text,
            metadata=metadata or {},
            indexed_at=datetime.now(),
            tokens=tokens,
            title_tokens=title_tokens
        )
        
        # Store document
        self._documents[document_id] = doc
        
        # Update inverted index
        for token in all_tokens:
            if token not in self._inverted_index:
                self._inverted_index[token] = set()
            self._inverted_index[token].add(document_id)
        
        # Update stats
        self._stats['documents_indexed'] += 1
        self._stats['total_tokens'] = len(self._inverted_index)
        if document_type not in self._stats['by_type']:
            self._stats['by_type'][document_type] = 0
        self._stats['by_type'][document_type] += 1
        
        logger.debug(f"📄 Indexed document: {document_id} ({document_type})")
        
        return document_id
    
    def search(
        self,
        query: str,
        document_types: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[SearchResult]:
        """
        Search indexed documents
        
        Args:
            query: Search query
            document_types: Filter by document types
            max_results: Maximum results to return
        
        Returns:
            List of search results ordered by relevance
        """
        self._stats['searches_performed'] += 1
        
        if not query:
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return []
        
        # Find matching documents
        matching_docs: Dict[str, float] = {}
        
        for token in query_tokens:
            if token in self._inverted_index:
                doc_ids = self._inverted_index[token]
                for doc_id in doc_ids:
                    if doc_id not in matching_docs:
                        matching_docs[doc_id] = 0.0
                    # Increase score for each matching token
                    matching_docs[doc_id] += 1.0
        
        # Score and filter results
        results: List[SearchResult] = []
        
        for doc_id, base_score in matching_docs.items():
            doc = self._documents[doc_id]
            
            # Filter by document type if specified
            if document_types and doc.document_type not in document_types:
                continue
            
            # Calculate relevance score
            # - Base score from token matches
            # - Boost for title matches
            # - Normalize by document length
            title_matches = len(query_tokens & doc.title_tokens)
            body_matches = len(query_tokens & doc.tokens)
            
            score = (
                (title_matches * 2.0) +  # Title matches weighted 2x
                body_matches
            ) / max(1, len(query_tokens))
            
            # Boost for exact phrase match in title
            if query.lower() in doc.title.lower():
                score *= 1.5
            
            # Extract highlights
            highlights = self._extract_highlights(doc.full_text, query_tokens)
            
            result = SearchResult(
                document_id=doc.document_id,
                document_type=doc.document_type,
                title=doc.title,
                full_text=doc.full_text,
                score=score,
                metadata=doc.metadata,
                highlights=highlights
            )
            results.append(result)
        
        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results[:max_results]
    
    def search_by_citation(
        self,
        citation: str
    ) -> List[SearchResult]:
        """
        Search by legal citation
        
        Args:
            citation: Legal citation (e.g., "18 USC § 1001")
        
        Returns:
            Matching documents
        """
        results = []
        
        # Normalize citation for matching
        citation_lower = citation.lower()
        
        for doc in self._documents.values():
            # Check title for citation
            if citation_lower in doc.title.lower():
                result = SearchResult(
                    document_id=doc.document_id,
                    document_type=doc.document_type,
                    title=doc.title,
                    full_text=doc.full_text,
                    score=1.0,
                    metadata=doc.metadata,
                    highlights=[doc.title]
                )
                results.append(result)
        
        return results
    
    def search_by_statute(
        self,
        title: int,
        section: str
    ) -> List[SearchResult]:
        """
        Search by statute title and section
        
        Args:
            title: USC title number
            section: Section number/identifier
        
        Returns:
            Matching documents
        """
        results = []
        
        for doc in self._documents.values():
            # Check metadata for title/section match
            doc_title = doc.metadata.get('title') or doc.metadata.get('title_number')
            doc_section = doc.metadata.get('section')
            
            if doc_title == title and doc_section == section:
                result = SearchResult(
                    document_id=doc.document_id,
                    document_type=doc.document_type,
                    title=doc.title,
                    full_text=doc.full_text,
                    score=1.0,
                    metadata=doc.metadata,
                    highlights=[]
                )
                results.append(result)
        
        # Also search by constructed citation
        citation = f"{title} USC § {section}"
        citation_results = self.search_by_citation(citation)
        
        # Combine and deduplicate
        seen = {r.document_id for r in results}
        for r in citation_results:
            if r.document_id not in seen:
                results.append(r)
                seen.add(r.document_id)
        
        return results
    
    def _extract_highlights(
        self,
        text: str,
        query_tokens: Set[str],
        max_highlights: int = 3,
        context_chars: int = 100
    ) -> List[str]:
        """Extract text snippets containing query matches"""
        highlights = []
        text_lower = text.lower()
        
        for token in query_tokens:
            # Find token in text
            pos = text_lower.find(token)
            if pos != -1:
                # Extract context around match
                start = max(0, pos - context_chars // 2)
                end = min(len(text), pos + len(token) + context_chars // 2)
                
                snippet = text[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                
                highlights.append(snippet)
                
                if len(highlights) >= max_highlights:
                    break
        
        return highlights
    
    def get_document(self, document_id: str) -> Optional[IndexedDocument]:
        """Get a specific document by ID"""
        return self._documents.get(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the index"""
        if document_id not in self._documents:
            return False
        
        doc = self._documents[document_id]
        
        # Remove from inverted index
        all_tokens = doc.tokens | doc.title_tokens
        for token in all_tokens:
            if token in self._inverted_index:
                self._inverted_index[token].discard(document_id)
                if not self._inverted_index[token]:
                    del self._inverted_index[token]
        
        # Remove document
        del self._documents[document_id]
        
        # Update stats
        self._stats['documents_indexed'] -= 1
        self._stats['total_tokens'] = len(self._inverted_index)
        if doc.document_type in self._stats['by_type']:
            self._stats['by_type'][doc.document_type] -= 1
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            **self._stats,
            'unique_tokens': len(self._inverted_index)
        }
    
    def clear(self):
        """Clear all indexed documents"""
        self._documents.clear()
        self._inverted_index.clear()
        self._stats = {
            'documents_indexed': 0,
            'total_tokens': 0,
            'searches_performed': 0,
            'by_type': {}
        }


if __name__ == "__main__":
    # Demo usage
    index = ElasticsearchLegalIndex()
    
    # Index test documents
    index.index_document(
        document_id="usc_18_1001",
        document_type="statute",
        title="18 USC § 1001 - False Statements",
        full_text="Whoever knowingly and willfully falsifies, conceals, or covers up by any trick, scheme, or device a material fact, makes any materially false, fictitious, or fraudulent statement or representation...",
        metadata={'title': 18, 'section': '1001'}
    )
    
    index.index_document(
        document_id="usc_15_78j",
        document_type="statute",
        title="15 USC § 78j - Manipulative and Deceptive Devices",
        full_text="It shall be unlawful for any person, directly or indirectly, by the use of any means or instrumentality of interstate commerce or of the mails, or of any facility of any national securities exchange to use or employ, in connection with the purchase or sale of any security...",
        metadata={'title': 15, 'section': '78j'}
    )
    
    print(f"📊 Index statistics: {index.get_statistics()}")
    
    # Search tests
    results = index.search("false statements")
    print(f"\n🔍 Search 'false statements': {len(results)} results")
    for r in results:
        print(f"  - {r.title} (score: {r.score:.2f})")
    
    results = index.search_by_citation("18 USC § 1001")
    print(f"\n🔍 Citation '18 USC § 1001': {len(results)} results")
