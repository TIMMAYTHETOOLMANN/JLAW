"""
SEC Semantic Search Engine
===========================

Advanced semantic search engine for SEC filings with specialized
capabilities for forensic analysis.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """Structured search query."""
    text: str
    cik: Optional[str] = None
    company_name: Optional[str] = None
    filing_types: Optional[List[str]] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    sections: Optional[List[str]] = None
    risk_threshold: Optional[float] = None
    top_k: int = 10


@dataclass
class SearchHit:
    """Individual search result."""
    doc_id: str
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)
    
    @property
    def filing_type(self) -> str:
        return self.metadata.get('filing_type', 'UNKNOWN')
    
    @property
    def company(self) -> str:
        return self.metadata.get('company_name', 'Unknown Company')
    
    @property
    def section(self) -> str:
        return self.metadata.get('section', '')
    
    @property
    def filing_date(self) -> str:
        return self.metadata.get('filing_date', '')


@dataclass
class SearchResponse:
    """Complete search response."""
    query: str
    hits: List[SearchHit]
    total_hits: int
    search_time_ms: float
    aggregations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossFilingResult:
    """Result from cross-filing analysis."""
    source_filing: str
    related_filings: List[str]
    similarity_scores: Dict[str, float]
    common_topics: List[str]
    discrepancies: List[Dict[str, Any]]


class SECSemanticSearchEngine:
    """
    Semantic search engine optimized for SEC filings.
    
    Features:
    - Full-text semantic search
    - Metadata filtering (CIK, filing type, date, section)
    - Hybrid search (semantic + keyword)
    - Result aggregation by filing
    - Cross-filing similarity analysis
    
    Usage:
        engine = SECSemanticSearchEngine(vector_store, embedder)
        results = engine.search("revenue recognition changes")
        
        # With filters
        results = engine.search(
            "material weakness",
            filing_types=["10-K", "10-Q"],
            cik="0001318605",
            date_range=(start_date, end_date)
        )
    """
    
    def __init__(
        self,
        vector_store,
        embedder,
        enable_hybrid: bool = True,
        rerank_results: bool = True
    ):
        """
        Initialize search engine.
        
        Args:
            vector_store: Vector store instance
            embedder: Embedder instance
            enable_hybrid: Whether to use hybrid search
            rerank_results: Whether to rerank results
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.enable_hybrid = enable_hybrid
        self.rerank_results = rerank_results
        
        logger.info("SECSemanticSearchEngine initialized")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        cik: Optional[str] = None,
        filing_types: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        sections: Optional[List[str]] = None,
        **kwargs
    ) -> SearchResponse:
        """
        Perform semantic search across SEC filings.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            cik: Filter by company CIK
            filing_types: Filter by filing types (10-K, 10-Q, etc.)
            date_range: Filter by filing date range
            sections: Filter by document sections
            
        Returns:
            SearchResponse with matching documents
        """
        import time
        start_time = time.time()
        
        # Build filter
        filter_dict = self._build_filter(cik, filing_types, date_range, sections)
        
        # Get query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2 if self.rerank_results else top_k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        # Convert to SearchHit objects
        hits = [
            SearchHit(
                doc_id=r.doc_id,
                chunk_id=r.chunk_id,
                text=r.text,
                score=r.score,
                metadata=r.metadata,
                highlights=self._extract_highlights(r.text, query)
            )
            for r in results
        ]
        
        # Rerank if enabled
        if self.rerank_results and len(hits) > top_k:
            hits = self._rerank(hits, query)[:top_k]
        
        # Compute aggregations
        aggregations = self._compute_aggregations(hits)
        
        search_time = (time.time() - start_time) * 1000
        
        return SearchResponse(
            query=query,
            hits=hits[:top_k],
            total_hits=len(hits),
            search_time_ms=search_time,
            aggregations=aggregations
        )
    
    def search_by_filing(
        self,
        query: str,
        accession_number: str,
        top_k: int = 10
    ) -> SearchResponse:
        """Search within a specific filing."""
        return self.search(
            query,
            top_k=top_k,
            **{'accession_number': accession_number}
        )
    
    def find_similar_filings(
        self,
        reference_text: str,
        exclude_accession: Optional[str] = None,
        top_k: int = 5
    ) -> List[SearchHit]:
        """Find filings similar to reference text."""
        results = self.search(reference_text, top_k=top_k * 2)
        
        # Filter out reference filing and deduplicate by filing
        seen_filings = set()
        unique_hits = []
        
        for hit in results.hits:
            accession = hit.metadata.get('accession_number', '')
            if accession == exclude_accession:
                continue
            if accession not in seen_filings:
                seen_filings.add(accession)
                unique_hits.append(hit)
            
            if len(unique_hits) >= top_k:
                break
        
        return unique_hits
    
    def search_temporal(
        self,
        query: str,
        cik: str,
        years: int = 3,
        top_k_per_year: int = 5
    ) -> Dict[str, List[SearchHit]]:
        """
        Search across multiple years for temporal analysis.
        
        Args:
            query: Search query
            cik: Company CIK
            years: Number of years to search
            top_k_per_year: Results per year
            
        Returns:
            Dict mapping year to search results
        """
        from datetime import datetime, timedelta
        
        results_by_year = {}
        current_year = datetime.now().year
        
        for year_offset in range(years):
            year = current_year - year_offset
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            results = self.search(
                query,
                top_k=top_k_per_year,
                cik=cik,
                date_range=(start_date, end_date)
            )
            
            results_by_year[str(year)] = results.hits
        
        return results_by_year
    
    def _build_filter(
        self,
        cik: Optional[str],
        filing_types: Optional[List[str]],
        date_range: Optional[Tuple[datetime, datetime]],
        sections: Optional[List[str]]
    ) -> Optional[Dict[str, Any]]:
        """Build filter dictionary for vector store."""
        filter_dict = {}
        
        if cik:
            filter_dict['cik'] = cik
        
        if filing_types:
            filter_dict['filing_type'] = {'$in': filing_types}
        
        if sections:
            filter_dict['section'] = {'$in': sections}
        
        if date_range:
            start, end = date_range
            filter_dict['filing_date'] = {
                '$gte': start.isoformat(),
                '$lte': end.isoformat()
            }
        
        return filter_dict if filter_dict else None
    
    def _extract_highlights(self, text: str, query: str, context: int = 50) -> List[str]:
        """Extract text snippets around query terms."""
        import re
        
        highlights = []
        query_terms = query.lower().split()
        text_lower = text.lower()
        
        for term in query_terms:
            if len(term) < 3:
                continue
            
            for match in re.finditer(re.escape(term), text_lower):
                start = max(0, match.start() - context)
                end = min(len(text), match.end() + context)
                snippet = text[start:end]
                
                # Clean up snippet
                if start > 0:
                    snippet = '...' + snippet
                if end < len(text):
                    snippet = snippet + '...'
                
                highlights.append(snippet)
                
                if len(highlights) >= 3:
                    break
        
        return highlights[:3]
    
    def _rerank(self, hits: List[SearchHit], query: str) -> List[SearchHit]:
        """Rerank results for better relevance."""
        # Simple reranking based on keyword presence
        query_terms = set(query.lower().split())
        
        def score_hit(hit: SearchHit) -> float:
            text_lower = hit.text.lower()
            
            # Count term matches
            term_score = sum(1 for term in query_terms if term in text_lower)
            
            # Boost for section relevance
            section_boost = 1.0
            if 'risk' in query.lower() and 'risk' in hit.section.lower():
                section_boost = 1.3
            elif 'revenue' in query.lower() and 'item 7' in hit.section.lower():
                section_boost = 1.2
            
            # Combine with original score
            return hit.score * section_boost + (term_score * 0.1)
        
        hits.sort(key=score_hit, reverse=True)
        return hits
    
    def _compute_aggregations(self, hits: List[SearchHit]) -> Dict[str, Any]:
        """Compute aggregations over search results."""
        aggs = {
            'by_filing_type': defaultdict(int),
            'by_section': defaultdict(int),
            'by_company': defaultdict(int),
            'by_year': defaultdict(int),
            'score_distribution': {
                'min': float('inf'),
                'max': float('-inf'),
                'avg': 0.0
            }
        }
        
        if not hits:
            return aggs
        
        total_score = 0
        for hit in hits:
            aggs['by_filing_type'][hit.filing_type] += 1
            aggs['by_section'][hit.section] += 1
            aggs['by_company'][hit.company] += 1
            
            # Extract year from filing date
            if hit.filing_date:
                year = hit.filing_date[:4]
                aggs['by_year'][year] += 1
            
            # Score stats
            total_score += hit.score
            aggs['score_distribution']['min'] = min(aggs['score_distribution']['min'], hit.score)
            aggs['score_distribution']['max'] = max(aggs['score_distribution']['max'], hit.score)
        
        aggs['score_distribution']['avg'] = total_score / len(hits)
        
        # Convert defaultdicts to regular dicts
        for key in ['by_filing_type', 'by_section', 'by_company', 'by_year']:
            aggs[key] = dict(aggs[key])
        
        return aggs


class CrossFilingAnalyzer:
    """
    Analyzer for cross-filing comparisons and temporal analysis.
    
    Features:
    - Compare statements across filings
    - Detect language changes
    - Identify topic evolution
    - Find semantic discrepancies
    """
    
    def __init__(self, search_engine: SECSemanticSearchEngine, embedder):
        self.search_engine = search_engine
        self.embedder = embedder
    
    def compare_sections(
        self,
        cik: str,
        section: str,
        filing_types: List[str] = ["10-K"],
        years: int = 3
    ) -> Dict[str, Any]:
        """
        Compare a specific section across multiple years.
        
        Args:
            cik: Company CIK
            section: Section to compare (e.g., "Item 1A")
            filing_types: Filing types to include
            years: Number of years to compare
            
        Returns:
            Comparison results with similarity scores and changes
        """
        from datetime import datetime
        
        # Get section text for each year
        section_texts = {}
        current_year = datetime.now().year
        
        for year_offset in range(years):
            year = current_year - year_offset
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            results = self.search_engine.search(
                f"{section}",
                top_k=5,
                cik=cik,
                filing_types=filing_types,
                sections=[section],
                date_range=(start_date, end_date)
            )
            
            if results.hits:
                section_texts[str(year)] = " ".join(hit.text for hit in results.hits)
        
        # Compute pairwise similarities
        years_list = sorted(section_texts.keys(), reverse=True)
        similarities = {}
        
        for i in range(len(years_list) - 1):
            year1, year2 = years_list[i], years_list[i + 1]
            if year1 in section_texts and year2 in section_texts:
                sim = self._compute_similarity(
                    section_texts[year1],
                    section_texts[year2]
                )
                similarities[f"{year1}_vs_{year2}"] = sim
        
        # Identify significant changes
        significant_changes = []
        for pair, sim in similarities.items():
            if sim < 0.7:  # Low similarity indicates significant change
                years = pair.split('_vs_')
                significant_changes.append({
                    'years': years,
                    'similarity': sim,
                    'change_magnitude': 'high' if sim < 0.5 else 'medium'
                })
        
        return {
            'section': section,
            'cik': cik,
            'years_analyzed': years_list,
            'pairwise_similarities': similarities,
            'significant_changes': significant_changes,
            'overall_consistency': sum(similarities.values()) / len(similarities) if similarities else 0
        }
    
    def find_statement_evolution(
        self,
        statement: str,
        cik: str,
        years: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Track how a specific statement or topic has evolved.
        
        Args:
            statement: Statement or topic to track
            cik: Company CIK
            years: Number of years to track
            
        Returns:
            List of similar statements by year with evolution analysis
        """
        temporal_results = self.search_engine.search_temporal(
            statement,
            cik=cik,
            years=years,
            top_k_per_year=3
        )
        
        evolution = []
        prev_texts = None
        
        for year in sorted(temporal_results.keys(), reverse=True):
            hits = temporal_results[year]
            if not hits:
                continue
            
            year_data = {
                'year': year,
                'matches': [
                    {
                        'text': hit.text[:500],
                        'score': hit.score,
                        'section': hit.section,
                        'filing_type': hit.filing_type
                    }
                    for hit in hits
                ],
                'count': len(hits)
            }
            
            # Compare with previous year
            current_texts = [hit.text for hit in hits]
            if prev_texts:
                year_data['similarity_to_next_year'] = self._compute_similarity(
                    " ".join(current_texts),
                    " ".join(prev_texts)
                )
            
            prev_texts = current_texts
            evolution.append(year_data)
        
        return evolution
    
    def detect_language_changes(
        self,
        cik: str,
        keywords: List[str],
        years: int = 3
    ) -> Dict[str, Any]:
        """
        Detect significant language changes around specific keywords.
        
        Args:
            cik: Company CIK
            keywords: Keywords to track
            years: Number of years
            
        Returns:
            Analysis of language changes
        """
        changes = {}
        
        for keyword in keywords:
            evolution = self.find_statement_evolution(keyword, cik, years)
            
            # Analyze changes
            keyword_changes = {
                'keyword': keyword,
                'appearances_by_year': {
                    e['year']: e['count'] for e in evolution
                },
                'similarity_trend': [],
                'notable_changes': []
            }
            
            for i, e in enumerate(evolution):
                if 'similarity_to_next_year' in e:
                    keyword_changes['similarity_trend'].append({
                        'years': f"{e['year']}→{evolution[i+1]['year']}",
                        'similarity': e['similarity_to_next_year']
                    })
                    
                    if e['similarity_to_next_year'] < 0.6:
                        keyword_changes['notable_changes'].append({
                            'year': e['year'],
                            'type': 'significant_language_change',
                            'similarity': e['similarity_to_next_year']
                        })
            
            changes[keyword] = keyword_changes
        
        return changes
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        import numpy as np
        
        emb1 = self.embedder.embed(text1)
        emb2 = self.embedder.embed(text2)
        
        # Cosine similarity
        emb1 = np.array(emb1)
        emb2 = np.array(emb2)
        
        dot = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot / (norm1 * norm2))

