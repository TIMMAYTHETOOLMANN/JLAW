"""
OmniscientIntelligenceGatherer - Master Intelligence Orchestrator
=================================================================

Unified multi-source intelligence aggregation with advanced correlation,
deduplication, and cross-validation capabilities.

Architecture:
- Async parallel source gathering
- Real-time data fusion and correlation
- Entity resolution across sources
- Temporal co-occurrence detection
- Credibility scoring and source weighting
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class IntelligenceSource:
    """Metadata for intelligence source"""
    name: str
    category: str  # 'regulatory', 'market', 'social', 'media', 'corporate'
    reliability: float  # 0.0-1.0
    latency: float  # seconds
    cost: float  # USD per query
    rate_limit: int  # queries per hour
    last_accessed: Optional[datetime] = None


@dataclass
class IntelligenceItem:
    """Single piece of intelligence with provenance"""
    content: str
    source: str
    timestamp: datetime
    entities: List[str] = field(default_factory=list)
    confidence: float = 0.0
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = field(default="")
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Generate content hash for deduplication"""
        content_str = f"{self.content}|{self.timestamp.isoformat()}"
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


@dataclass
class IntelligenceReport:
    """Aggregated intelligence report with cross-source analysis"""
    target: str  # Subject of investigation (ticker, person, entity)
    intelligence_items: List[IntelligenceItem]
    entity_mentions: Dict[str, int]
    temporal_clusters: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    credibility_score: float
    sources_used: List[str]
    collection_start: datetime
    collection_end: datetime
    total_items: int
    unique_items: int


class OmniscientIntelligenceGatherer:
    """
    Master intelligence orchestrator coordinating all intelligence sources
    with advanced correlation, fusion, and validation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.sources: Dict[str, IntelligenceSource] = {}
        self.gatherers = {}
        self._cache = {}
        self._initialize_sources()
        
        # Performance tracking
        self.metrics = {
            'queries_executed': 0,
            'items_collected': 0,
            'duplicates_removed': 0,
            'errors_encountered': 0,
            'avg_latency': 0.0
        }
    
    def _initialize_sources(self):
        """Initialize all intelligence source metadata"""
        self.sources = {
            'sec_edgar': IntelligenceSource(
                name='SEC EDGAR',
                category='regulatory',
                reliability=0.99,
                latency=2.0,
                cost=0.0,
                rate_limit=10  # per second
            ),
            'twitter': IntelligenceSource(
                name='Twitter API',
                category='social',
                reliability=0.60,
                latency=1.5,
                cost=0.01,
                rate_limit=300
            ),
            'reddit': IntelligenceSource(
                name='Reddit PRAW',
                category='social',
                reliability=0.65,
                latency=2.0,
                cost=0.0,
                rate_limit=60
            ),
            'stocktwits': IntelligenceSource(
                name='StockTwits',
                category='social',
                reliability=0.55,
                latency=1.0,
                cost=0.0,
                rate_limit=200
            ),
            'yfinance': IntelligenceSource(
                name='Yahoo Finance',
                category='market',
                reliability=0.85,
                latency=1.5,
                cost=0.0,
                rate_limit=2000
            ),
            'polygon': IntelligenceSource(
                name='Polygon.io',
                category='market',
                reliability=0.95,
                latency=0.5,
                cost=0.002,
                rate_limit=5
            ),
            'finnhub': IntelligenceSource(
                name='Finnhub',
                category='corporate',
                reliability=0.90,
                latency=1.0,
                cost=0.0,
                rate_limit=60
            ),
            'seeking_alpha': IntelligenceSource(
                name='Seeking Alpha',
                category='corporate',
                reliability=0.80,
                latency=3.0,
                cost=0.05,
                rate_limit=100
            )
        }
    
    async def gather_intelligence(
        self,
        target: str,
        sources: Optional[List[str]] = None,
        lookback_days: int = 90,
        max_items: int = 10000
    ) -> IntelligenceReport:
        """
        Orchestrate intelligence gathering across all specified sources
        
        Args:
            target: Investigation target (ticker symbol, CIK, person name)
            sources: List of source names to query (None = all)
            lookback_days: Historical data window
            max_items: Maximum intelligence items to collect
        
        Returns:
            IntelligenceReport with aggregated and correlated intelligence
        """
        logger.info(f"🔍 Initiating omniscient intelligence gathering for: {target}")
        collection_start = datetime.now()
        
        # Select sources
        active_sources = sources or list(self.sources.keys())
        logger.info(f"📊 Activating {len(active_sources)} intelligence sources")
        
        # Launch parallel gathering
        tasks = []
        for source_name in active_sources:
            if source_name in self.gatherers:
                task = self._gather_from_source(
                    source_name, target, lookback_days, max_items
                )
                tasks.append(task)
        
        # Execute gathering with timeout
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"❌ Intelligence gathering failed: {e}")
            results = []
        
        # Aggregate results
        all_items = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"⚠️ Source error: {result}")
                self.metrics['errors_encountered'] += 1
        
        # Deduplicate
        unique_items = self._deduplicate_items(all_items)
        logger.info(f"🔄 Deduplication: {len(all_items)} → {len(unique_items)} items")
        
        # Entity extraction and correlation
        entity_mentions = self._extract_entity_mentions(unique_items)
        
        # Temporal clustering
        temporal_clusters = self._detect_temporal_clusters(unique_items)
        
        # Contradiction detection
        contradictions = self._detect_cross_source_contradictions(unique_items)
        
        # Calculate credibility
        credibility_score = self._calculate_credibility_score(unique_items)
        
        collection_end = datetime.now()
        
        report = IntelligenceReport(
            target=target,
            intelligence_items=unique_items[:max_items],
            entity_mentions=entity_mentions,
            temporal_clusters=temporal_clusters,
            contradictions=contradictions,
            credibility_score=credibility_score,
            sources_used=active_sources,
            collection_start=collection_start,
            collection_end=collection_end,
            total_items=len(all_items),
            unique_items=len(unique_items)
        )
        
        logger.info(f"✅ Intelligence gathering complete: {len(unique_items)} unique items")
        logger.info(f"⏱️ Collection time: {(collection_end - collection_start).total_seconds():.2f}s")
        
        return report
    
    async def _gather_from_source(
        self,
        source_name: str,
        target: str,
        lookback_days: int,
        max_items: int
    ) -> List[IntelligenceItem]:
        """Gather intelligence from a single source"""
        try:
            source = self.sources[source_name]
            gatherer = self.gatherers.get(source_name)
            
            if not gatherer:
                logger.warning(f"⚠️ Gatherer not initialized: {source_name}")
                return []
            
            # Rate limiting
            await self._enforce_rate_limit(source_name)
            
            # Execute gathering
            start_time = datetime.now()
            items = await gatherer.gather(target, lookback_days, max_items)
            latency = (datetime.now() - start_time).total_seconds()
            
            # Update source metadata
            source.last_accessed = datetime.now()
            
            # Update metrics
            self.metrics['queries_executed'] += 1
            self.metrics['items_collected'] += len(items)
            
            logger.info(f"✓ {source_name}: {len(items)} items ({latency:.2f}s)")
            
            return items
            
        except Exception as e:
            logger.error(f"❌ {source_name} gathering failed: {e}")
            return []
    
    async def _enforce_rate_limit(self, source_name: str):
        """Enforce rate limiting for source"""
        source = self.sources[source_name]
        
        # Simple rate limiting (production would use token bucket)
        if source.last_accessed:
            elapsed = (datetime.now() - source.last_accessed).total_seconds()
            min_interval = 3600.0 / source.rate_limit
            
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
    
    def _deduplicate_items(self, items: List[IntelligenceItem]) -> List[IntelligenceItem]:
        """Remove duplicate items based on content hash"""
        seen_hashes = set()
        unique_items = []
        
        for item in items:
            if item.hash not in seen_hashes:
                seen_hashes.add(item.hash)
                unique_items.append(item)
            else:
                self.metrics['duplicates_removed'] += 1
        
        return unique_items
    
    def _extract_entity_mentions(self, items: List[IntelligenceItem]) -> Dict[str, int]:
        """Extract and count entity mentions across all items"""
        entity_counts = defaultdict(int)
        
        for item in items:
            for entity in item.entities:
                entity_counts[entity] += 1
        
        # Sort by frequency
        return dict(sorted(entity_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _detect_temporal_clusters(
        self,
        items: List[IntelligenceItem],
        window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Detect temporal clusters of activity (potential coordinated events)
        """
        if not items:
            return []
        
        # Sort by timestamp
        sorted_items = sorted(items, key=lambda x: x.timestamp)
        
        clusters = []
        current_cluster = [sorted_items[0]]
        
        for item in sorted_items[1:]:
            time_diff = (item.timestamp - current_cluster[-1].timestamp).total_seconds() / 3600
            
            if time_diff <= window_hours:
                current_cluster.append(item)
            else:
                if len(current_cluster) >= 5:  # Minimum cluster size
                    clusters.append({
                        'start': current_cluster[0].timestamp,
                        'end': current_cluster[-1].timestamp,
                        'item_count': len(current_cluster),
                        'sources': list(set(item.source for item in current_cluster)),
                        'significance': len(current_cluster) * len(set(item.source for item in current_cluster))
                    })
                current_cluster = [item]
        
        # Check final cluster
        if len(current_cluster) >= 5:
            clusters.append({
                'start': current_cluster[0].timestamp,
                'end': current_cluster[-1].timestamp,
                'item_count': len(current_cluster),
                'sources': list(set(item.source for item in current_cluster)),
                'significance': len(current_cluster) * len(set(item.source for item in current_cluster))
            })
        
        return sorted(clusters, key=lambda x: x['significance'], reverse=True)
    
    def _detect_cross_source_contradictions(
        self,
        items: List[IntelligenceItem]
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions across different sources
        (Basic implementation - would use NLI models in production)
        """
        contradictions = []
        
        # Group by category
        by_category = defaultdict(list)
        for item in items:
            by_category[item.category].append(item)
        
        # Look for contradictory numerical claims
        for category, category_items in by_category.items():
            if len(category_items) < 2:
                continue
            
            # Simple contradiction detection (would be enhanced with NLI)
            for i, item1 in enumerate(category_items):
                for item2 in category_items[i+1:]:
                    if item1.source != item2.source:
                        # Check for opposing sentiment or conflicting numbers
                        # (Placeholder for more sophisticated detection)
                        if self._items_contradict(item1, item2):
                            contradictions.append({
                                'item1': item1.hash,
                                'item2': item2.hash,
                                'source1': item1.source,
                                'source2': item2.source,
                                'category': category,
                                'severity': 'medium'
                            })
        
        return contradictions
    
    def _items_contradict(self, item1: IntelligenceItem, item2: IntelligenceItem) -> bool:
        """
        Check if two items contradict each other
        (Placeholder for NLI-based contradiction detection)
        """
        # Simple keyword-based contradiction detection
        negative_words = {'not', 'no', 'never', 'false', 'deny', 'reject'}
        
        content1_lower = item1.content.lower()
        content2_lower = item2.content.lower()
        
        # Very basic heuristic
        has_neg1 = any(word in content1_lower for word in negative_words)
        has_neg2 = any(word in content2_lower for word in negative_words)
        
        # Check for shared entities with opposite sentiment
        shared_entities = set(item1.entities) & set(item2.entities)
        
        return len(shared_entities) > 0 and (has_neg1 != has_neg2)
    
    def _calculate_credibility_score(self, items: List[IntelligenceItem]) -> float:
        """
        Calculate overall credibility score based on source reliability
        and cross-source corroboration
        """
        if not items:
            return 0.0
        
        # Weighted average of source reliability
        total_reliability = 0.0
        total_weight = 0
        
        for item in items:
            source_name = item.source
            if source_name in self.sources:
                reliability = self.sources[source_name].reliability
                total_reliability += reliability * item.confidence
                total_weight += item.confidence
        
        base_score = total_reliability / total_weight if total_weight > 0 else 0.5
        
        # Boost for multiple sources
        unique_sources = len(set(item.source for item in items))
        source_diversity_boost = min(unique_sources * 0.05, 0.2)
        
        # Penalty for contradictions
        # (Would be calculated from _detect_cross_source_contradictions)
        
        final_score = min(base_score + source_diversity_boost, 1.0)
        
        return round(final_score, 3)
    
    def register_gatherer(self, source_name: str, gatherer: Any):
        """Register a source-specific gatherer"""
        if source_name in self.sources:
            self.gatherers[source_name] = gatherer
            logger.info(f"✓ Registered gatherer: {source_name}")
        else:
            # Auto-register unknown sources for extensibility
            self.sources[source_name] = IntelligenceSource(
                name=source_name,
                category='custom',
                reliability=0.75,
                latency=2.0,
                cost=0.0,
                rate_limit=100
            )
            self.gatherers[source_name] = gatherer
            logger.info(f"✓ Registered custom gatherer: {source_name}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return performance metrics"""
        return self.metrics.copy()
    
    def export_report(self, report: IntelligenceReport, format: str = 'json') -> str:
        """Export intelligence report in specified format"""
        if format == 'json':
            return self._export_json(report)
        elif format == 'html':
            return self._export_html(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, report: IntelligenceReport) -> str:
        """Export report as JSON"""
        data = {
            'target': report.target,
            'collection_period': {
                'start': report.collection_start.isoformat(),
                'end': report.collection_end.isoformat()
            },
            'statistics': {
                'total_items': report.total_items,
                'unique_items': report.unique_items,
                'sources_used': report.sources_used,
                'credibility_score': report.credibility_score
            },
            'entity_mentions': report.entity_mentions,
            'temporal_clusters': report.temporal_clusters,
            'contradictions': report.contradictions,
            'intelligence_items': [
                {
                    'content': item.content,
                    'source': item.source,
                    'timestamp': item.timestamp.isoformat(),
                    'entities': item.entities,
                    'confidence': item.confidence,
                    'category': item.category
                }
                for item in report.intelligence_items[:100]  # Limit for size
            ]
        }
        
        return json.dumps(data, indent=2)
    
    def _export_html(self, report: IntelligenceReport) -> str:
        """Export report as HTML dashboard"""
        # Would use Jinja2 template in production
        html = f"""
        <html>
        <head><title>Intelligence Report: {report.target}</title></head>
        <body>
            <h1>Intelligence Report: {report.target}</h1>
            <h2>Statistics</h2>
            <ul>
                <li>Total Items: {report.total_items}</li>
                <li>Unique Items: {report.unique_items}</li>
                <li>Credibility Score: {report.credibility_score:.3f}</li>
                <li>Sources: {', '.join(report.sources_used)}</li>
            </ul>
            <h2>Top Entities</h2>
            <ul>
                {''.join(f'<li>{entity}: {count}</li>' for entity, count in list(report.entity_mentions.items())[:10])}
            </ul>
            <h2>Temporal Clusters</h2>
            <p>{len(report.temporal_clusters)} significant activity clusters detected</p>
        </body>
        </html>
        """
        return html


if __name__ == "__main__":
    # Demo usage
    async def demo():
        gatherer = OmniscientIntelligenceGatherer()
        
        # Would register actual gatherers
        # gatherer.register_gatherer('sec_edgar', SECEdgarIntegrator())
        # gatherer.register_gatherer('twitter', TwitterGatherer())
        
        report = await gatherer.gather_intelligence(
            target="AAPL",
            lookback_days=30
        )
        
        print(f"Collected {report.unique_items} unique intelligence items")
        print(f"Credibility Score: {report.credibility_score:.3f}")
        print(f"Top entities: {list(report.entity_mentions.keys())[:5]}")
    
    asyncio.run(demo())

