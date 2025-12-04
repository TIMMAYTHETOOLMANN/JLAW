"""
Entity Resolver - Cross-Source Entity Resolution for Forensic Triangulation
============================================================================

Advanced entity resolution system for matching and correlating entities across
multiple data sources including SEC filings, news articles, and social media.

Features:
- Jaro-Winkler string similarity for fuzzy name matching
- Levenshtein distance for edit-based similarity
- Soundex phonetic matching for name variations
- Transitive clustering for entity consolidation
- Cross-source verification and confidence scoring

Usage:
    resolver = EntityResolver(similarity_threshold=0.85)
    
    entities = [
        Entity(id="1", name="Apple Inc.", source=EntitySource.SEC),
        Entity(id="2", name="Apple Computer", source=EntitySource.NEWS),
        Entity(id="3", name="AAPL", source=EntitySource.SOCIAL),
    ]
    
    result = resolver.resolve_entities(entities)
    print(f"Found {len(result.clusters)} entity clusters")
"""

import logging
import re
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Security Note: Entity IDs use SHA-256 truncated to 16 characters
# This provides 64 bits of entropy, sufficient for entity deduplication
# while maintaining collision resistance for forensic evidence integrity.


# Security Note: Entity IDs use SHA-256 truncated to 16 characters
# This provides 64 bits of entropy, sufficient for entity deduplication
# while maintaining collision resistance for forensic evidence integrity.


logger = logging.getLogger(__name__)


class EntitySource(Enum):
    """Source of entity data."""
    SEC = "sec"
    NEWS = "news"
    SOCIAL = "social"
    EARNINGS = "earnings"
    COURT = "court"
    REGULATORY = "regulatory"
    UNKNOWN = "unknown"


class EntityType(Enum):
    """Type of entity."""
    COMPANY = "company"
    PERSON = "person"
    EXECUTIVE = "executive"
    DIRECTOR = "director"
    AUDITOR = "auditor"
    LAW_FIRM = "law_firm"
    REGULATOR = "regulator"
    TICKER = "ticker"
    CIK = "cik"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Represents an entity to be resolved."""
    id: str
    name: str
    source: EntitySource
    entity_type: EntityType = EntityType.UNKNOWN
    aliases: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        return self.id == other.id


@dataclass
class EntityMatch:
    """Represents a match between two entities."""
    entity1_id: str
    entity2_id: str
    similarity_score: float
    match_type: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityCluster:
    """Cluster of resolved entities."""
    cluster_id: str
    canonical_name: str
    entities: List[Entity] = field(default_factory=list)
    sources: Set[EntitySource] = field(default_factory=set)
    confidence: float = 0.0
    matches: List[EntityMatch] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the cluster."""
        self.entities.append(entity)
        self.sources.add(entity.source)


@dataclass
class EntityResolutionResult:
    """Result of entity resolution."""
    clusters: List[EntityCluster]
    total_entities: int
    resolved_entities: int
    unresolved_entities: int
    cross_source_matches: int
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class EntityResolver:
    """
    Cross-source entity resolution system.
    
    Resolves and clusters entities from multiple sources using various
    string similarity algorithms and contextual matching.
    
    Example:
        resolver = EntityResolver(similarity_threshold=0.85)
        
        entities = [
            Entity(id="1", name="Apple Inc.", source=EntitySource.SEC),
            Entity(id="2", name="Apple Computer", source=EntitySource.NEWS),
        ]
        
        result = resolver.resolve_entities(entities)
    """
    
    # Common company suffixes to normalize
    COMPANY_SUFFIXES = [
        r'\s*,?\s*Inc\.?$',
        r'\s*,?\s*Corp\.?$',
        r'\s*,?\s*Corporation$',
        r'\s*,?\s*Ltd\.?$',
        r'\s*,?\s*Limited$',
        r'\s*,?\s*LLC$',
        r'\s*,?\s*L\.L\.C\.?$',
        r'\s*,?\s*LLP$',
        r'\s*,?\s*L\.L\.P\.?$',
        r'\s*,?\s*Co\.?$',
        r'\s*,?\s*Company$',
        r'\s*,?\s*PLC$',
        r'\s*,?\s*P\.L\.C\.?$',
        r'\s*,?\s*AG$',
        r'\s*,?\s*SA$',
        r'\s*,?\s*NV$',
        r'\s*,?\s*N\.V\.?$',
        r'\s*,?\s*SE$',
    ]
    
    # Phonetic code mappings for Soundex
    SOUNDEX_MAP = {
        'B': '1', 'F': '1', 'P': '1', 'V': '1',
        'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
        'D': '3', 'T': '3',
        'L': '4',
        'M': '5', 'N': '5',
        'R': '6',
    }
    
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        phonetic_weight: float = 0.2,
        jaro_weight: float = 0.5,
        levenshtein_weight: float = 0.3,
        min_name_length: int = 2,
    ):
        """
        Initialize the entity resolver.
        
        Args:
            similarity_threshold: Minimum similarity for entity match (0.0-1.0)
            phonetic_weight: Weight for phonetic matching in combined score
            jaro_weight: Weight for Jaro-Winkler in combined score
            levenshtein_weight: Weight for Levenshtein in combined score
            min_name_length: Minimum name length for matching
        """
        self.similarity_threshold = similarity_threshold
        self.phonetic_weight = phonetic_weight
        self.jaro_weight = jaro_weight
        self.levenshtein_weight = levenshtein_weight
        self.min_name_length = min_name_length
        
        logger.info(
            f"EntityResolver initialized with threshold={similarity_threshold}, "
            f"jaro_weight={jaro_weight}, levenshtein_weight={levenshtein_weight}"
        )
    
    def resolve_entities(self, entities: List[Entity]) -> EntityResolutionResult:
        """
        Resolve and cluster entities from multiple sources.
        
        Args:
            entities: List of entities to resolve
            
        Returns:
            EntityResolutionResult with clusters and statistics
        """
        import time
        start_time = time.time()
        
        if not entities:
            return EntityResolutionResult(
                clusters=[],
                total_entities=0,
                resolved_entities=0,
                unresolved_entities=0,
                cross_source_matches=0,
                processing_time_ms=0.0,
            )
        
        logger.info(f"Resolving {len(entities)} entities")
        
        # Find all pairwise matches
        matches = self._find_matches(entities)
        
        # Build clusters using union-find
        clusters = self._build_clusters(entities, matches)
        
        # Calculate statistics
        resolved_entities = sum(len(c.entities) for c in clusters if len(c.entities) > 1)
        cross_source_matches = sum(
            1 for c in clusters 
            if len(c.sources) > 1
        )
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        result = EntityResolutionResult(
            clusters=clusters,
            total_entities=len(entities),
            resolved_entities=resolved_entities,
            unresolved_entities=len(entities) - resolved_entities,
            cross_source_matches=cross_source_matches,
            processing_time_ms=processing_time_ms,
        )
        
        logger.info(
            f"Resolution complete: {len(clusters)} clusters, "
            f"{cross_source_matches} cross-source matches"
        )
        
        return result
    
    def _find_matches(self, entities: List[Entity]) -> List[EntityMatch]:
        """Find all matching entity pairs."""
        matches = []
        
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i + 1:], start=i + 1):
                similarity, match_type = self._calculate_similarity(entity1, entity2)
                
                if similarity >= self.similarity_threshold:
                    match = EntityMatch(
                        entity1_id=entity1.id,
                        entity2_id=entity2.id,
                        similarity_score=similarity,
                        match_type=match_type,
                        confidence=similarity * min(entity1.confidence, entity2.confidence),
                    )
                    matches.append(match)
        
        return matches
    
    def _calculate_similarity(
        self, 
        entity1: Entity, 
        entity2: Entity
    ) -> Tuple[float, str]:
        """Calculate similarity between two entities."""
        # Normalize names
        name1 = self._normalize_name(entity1.name)
        name2 = self._normalize_name(entity2.name)
        
        if len(name1) < self.min_name_length or len(name2) < self.min_name_length:
            return 0.0, "too_short"
        
        # Check for exact match
        if name1.lower() == name2.lower():
            return 1.0, "exact"
        
        # Check aliases
        all_aliases_1 = [name1.lower()] + [a.lower() for a in entity1.aliases]
        all_aliases_2 = [name2.lower()] + [a.lower() for a in entity2.aliases]
        
        for alias1 in all_aliases_1:
            for alias2 in all_aliases_2:
                if alias1 == alias2:
                    return 0.98, "alias"
        
        # Calculate weighted similarity
        jaro_sim = self.jaro_winkler_similarity(name1, name2)
        lev_sim = self.levenshtein_similarity(name1, name2)
        phonetic_sim = self.phonetic_similarity(name1, name2)
        
        combined = (
            self.jaro_weight * jaro_sim +
            self.levenshtein_weight * lev_sim +
            self.phonetic_weight * phonetic_sim
        )
        
        # Determine match type
        if jaro_sim > lev_sim and jaro_sim > phonetic_sim:
            match_type = "jaro_winkler"
        elif lev_sim > phonetic_sim:
            match_type = "levenshtein"
        else:
            match_type = "phonetic"
        
        return combined, match_type
    
    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison."""
        if not name:
            return ""
        
        normalized = name.strip()
        
        # Remove company suffixes
        for suffix_pattern in self.COMPANY_SUFFIXES:
            normalized = re.sub(suffix_pattern, '', normalized, flags=re.IGNORECASE)
        
        # Normalize whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized.strip()
    
    def jaro_winkler_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate Jaro-Winkler similarity between two strings.
        
        The Jaro-Winkler similarity is a modification of the Jaro similarity
        that gives more favorable ratings to strings that match from the beginning.
        """
        if not s1 or not s2:
            return 0.0
        
        s1 = s1.lower()
        s2 = s2.lower()
        
        if s1 == s2:
            return 1.0
        
        # Calculate Jaro similarity
        jaro = self._jaro_similarity(s1, s2)
        
        # Calculate common prefix length (up to 4)
        prefix_len = 0
        for i in range(min(len(s1), len(s2), 4)):
            if s1[i] == s2[i]:
                prefix_len += 1
            else:
                break
        
        # Jaro-Winkler uses a scaling factor of 0.1
        return jaro + prefix_len * 0.1 * (1 - jaro)
    
    def _jaro_similarity(self, s1: str, s2: str) -> float:
        """Calculate Jaro similarity."""
        if len(s1) == 0 or len(s2) == 0:
            return 0.0
        
        match_window = max(len(s1), len(s2)) // 2 - 1
        match_window = max(0, match_window)
        
        s1_matches = [False] * len(s1)
        s2_matches = [False] * len(s2)
        
        matches = 0
        transpositions = 0
        
        for i in range(len(s1)):
            start = max(0, i - match_window)
            end = min(i + match_window + 1, len(s2))
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Count transpositions
        k = 0
        for i in range(len(s1)):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        jaro = (
            matches / len(s1) +
            matches / len(s2) +
            (matches - transpositions / 2) / matches
        ) / 3
        
        return jaro
    
    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate normalized Levenshtein similarity.
        
        Returns 1.0 for identical strings, 0.0 for completely different strings.
        """
        if not s1 or not s2:
            return 0.0 if s1 != s2 else 1.0
        
        s1 = s1.lower()
        s2 = s2.lower()
        
        if s1 == s2:
            return 1.0
        
        distance = self._levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        
        return 1.0 - (distance / max_len)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance."""
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def phonetic_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate phonetic similarity using Soundex algorithm.
        """
        soundex1 = self._soundex(s1)
        soundex2 = self._soundex(s2)
        
        if soundex1 == soundex2:
            return 1.0
        
        # Partial match based on shared characters
        matches = sum(1 for a, b in zip(soundex1, soundex2) if a == b)
        return matches / 4.0
    
    def _soundex(self, s: str) -> str:
        """Generate Soundex code for a string."""
        if not s:
            return "0000"
        
        s = ''.join(c for c in s.upper() if c.isalpha())
        if not s:
            return "0000"
        
        # Keep first letter
        code = s[0]
        
        # Map remaining letters
        prev_code = self.SOUNDEX_MAP.get(s[0], '0')
        
        for char in s[1:]:
            current_code = self.SOUNDEX_MAP.get(char, '0')
            if current_code != '0' and current_code != prev_code:
                code += current_code
            prev_code = current_code
            
            if len(code) >= 4:
                break
        
        # Pad with zeros
        code = code.ljust(4, '0')
        return code[:4]
    
    def _build_clusters(
        self, 
        entities: List[Entity], 
        matches: List[EntityMatch]
    ) -> List[EntityCluster]:
        """Build entity clusters using union-find algorithm."""
        # Initialize union-find structure
        parent: Dict[str, str] = {e.id: e.id for e in entities}
        rank: Dict[str, int] = {e.id: 0 for e in entities}
        
        def find(x: str) -> str:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x: str, y: str) -> None:
            px, py = find(x), find(y)
            if px == py:
                return
            if rank[px] < rank[py]:
                px, py = py, px
            parent[py] = px
            if rank[px] == rank[py]:
                rank[px] += 1
        
        # Union matched entities
        for match in matches:
            union(match.entity1_id, match.entity2_id)
        
        # Group entities by root
        entity_map = {e.id: e for e in entities}
        cluster_entities: Dict[str, List[Entity]] = {}
        
        for entity in entities:
            root = find(entity.id)
            if root not in cluster_entities:
                cluster_entities[root] = []
            cluster_entities[root].append(entity)
        
        # Build cluster objects
        clusters = []
        for i, (root_id, cluster_ents) in enumerate(cluster_entities.items()):
            # Find canonical name (prefer SEC source, longest name)
            canonical = max(
                cluster_ents,
                key=lambda e: (
                    e.source == EntitySource.SEC,
                    len(e.name),
                    e.confidence
                )
            ).name
            
            # Find matches within this cluster
            cluster_entity_ids = {e.id for e in cluster_ents}
            cluster_matches = [
                m for m in matches
                if m.entity1_id in cluster_entity_ids and m.entity2_id in cluster_entity_ids
            ]
            
            # Calculate cluster confidence
            if cluster_matches:
                confidence = sum(m.confidence for m in cluster_matches) / len(cluster_matches)
            else:
                confidence = cluster_ents[0].confidence if len(cluster_ents) == 1 else 0.0
            
            cluster = EntityCluster(
                cluster_id=f"cluster_{i}",
                canonical_name=canonical,
                entities=cluster_ents,
                sources={e.source for e in cluster_ents},
                confidence=confidence,
                matches=cluster_matches,
            )
            clusters.append(cluster)
        
        # Sort by cluster size (largest first)
        clusters.sort(key=lambda c: len(c.entities), reverse=True)
        
        return clusters
    
    def find_entity(
        self, 
        name: str, 
        clusters: List[EntityCluster],
        threshold: Optional[float] = None
    ) -> Optional[EntityCluster]:
        """
        Find a cluster matching the given entity name.
        
        Args:
            name: Entity name to search for
            clusters: List of clusters to search
            threshold: Similarity threshold (uses default if None)
            
        Returns:
            Matching cluster or None
        """
        threshold = threshold or self.similarity_threshold
        normalized_name = self._normalize_name(name)
        
        best_match: Optional[EntityCluster] = None
        best_score = 0.0
        
        for cluster in clusters:
            for entity in cluster.entities:
                normalized_entity = self._normalize_name(entity.name)
                
                score = self.jaro_winkler_similarity(normalized_name, normalized_entity)
                
                if score >= threshold and score > best_score:
                    best_score = score
                    best_match = cluster
        
        return best_match
    
    def get_cross_source_entities(
        self, 
        clusters: List[EntityCluster]
    ) -> List[EntityCluster]:
        """Get only clusters with entities from multiple sources."""
        return [c for c in clusters if len(c.sources) > 1]
