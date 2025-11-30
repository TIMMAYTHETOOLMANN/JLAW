"""
Entity Resolution Module for Cross-Source Triangulation
========================================================

Advanced entity resolution for cross-source identity triangulation.
Enables matching entities across SEC filings, news sources, social media,
and corporate registries.

Features:
- Jaro-Winkler string similarity
- Soundex phonetic matching
- Transitive clustering
- Confidence scoring
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Types of entities that can be resolved."""

    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    SECURITY = "SECURITY"  # Stock/bond identifiers
    ACCOUNT = "ACCOUNT"
    UNKNOWN = "UNKNOWN"


class SourceType(Enum):
    """Sources from which entities can be extracted."""

    SEC_FILING = "SEC_FILING"
    NEWS_ARTICLE = "NEWS_ARTICLE"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    CORPORATE_REGISTRY = "CORPORATE_REGISTRY"
    COURT_DOCUMENT = "COURT_DOCUMENT"
    INTERNAL_DOCUMENT = "INTERNAL_DOCUMENT"


@dataclass
class EntityMention:
    """Represents a mention of an entity in a source document."""

    text: str
    entity_type: EntityType
    source_type: SourceType
    source_id: str
    context: str = ""
    position: int = 0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedEntity:
    """Represents a resolved entity with all its mentions."""

    canonical_name: str
    entity_type: EntityType
    entity_id: str
    mentions: List[EntityMention] = field(default_factory=list)
    aliases: Set[str] = field(default_factory=set)
    sources: Set[SourceType] = field(default_factory=set)
    cross_source_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionResult:
    """Results from entity resolution."""

    resolved_entities: List[ResolvedEntity]
    unresolved_mentions: List[EntityMention]
    resolution_statistics: Dict[str, Any]
    cross_source_matches: List[Dict[str, Any]]


class EntityResolver:
    """
    Cross-source entity resolution using multiple matching strategies.

    Combines string similarity, phonetic matching, and transitive clustering
    to resolve entities across heterogeneous data sources.
    """

    # Soundex mapping for phonetic matching
    SOUNDEX_MAP = {
        "B": "1",
        "F": "1",
        "P": "1",
        "V": "1",
        "C": "2",
        "G": "2",
        "J": "2",
        "K": "2",
        "Q": "2",
        "S": "2",
        "X": "2",
        "Z": "2",
        "D": "3",
        "T": "3",
        "L": "4",
        "M": "5",
        "N": "5",
        "R": "6",
    }

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        phonetic_weight: float = 0.3,
        context_weight: float = 0.2,
        min_cluster_confidence: float = 0.7,
    ):
        """
        Initialize the entity resolver.

        Args:
            similarity_threshold: Minimum similarity for entity matching
            phonetic_weight: Weight for phonetic similarity in scoring
            context_weight: Weight for contextual similarity in scoring
            min_cluster_confidence: Minimum confidence for cluster formation
        """
        self.similarity_threshold = similarity_threshold
        self.phonetic_weight = phonetic_weight
        self.context_weight = context_weight
        self.min_cluster_confidence = min_cluster_confidence
        self.logger = logging.getLogger(__name__)

    def resolve(self, mentions: List[EntityMention]) -> ResolutionResult:
        """
        Resolve entity mentions to canonical entities.

        Args:
            mentions: List of entity mentions to resolve

        Returns:
            ResolutionResult with resolved entities and statistics
        """
        self.logger.info(f"Resolving {len(mentions)} entity mentions")

        if not mentions:
            return ResolutionResult(
                resolved_entities=[],
                unresolved_mentions=[],
                resolution_statistics={"total_mentions": 0},
                cross_source_matches=[],
            )

        # Group mentions by entity type
        mentions_by_type = self._group_by_type(mentions)

        resolved_entities = []
        unresolved_mentions = []
        cross_source_matches = []

        for entity_type, type_mentions in mentions_by_type.items():
            # Build similarity matrix
            similarity_matrix = self._build_similarity_matrix(type_mentions)

            # Perform transitive clustering
            clusters = self._transitive_clustering(type_mentions, similarity_matrix)

            # Create resolved entities from clusters
            for cluster in clusters:
                if len(cluster) >= 1:
                    resolved = self._create_resolved_entity(cluster, entity_type)
                    resolved_entities.append(resolved)

                    # Check for cross-source matches
                    if len(resolved.sources) > 1:
                        cross_source_matches.append(
                            {
                                "entity_id": resolved.entity_id,
                                "canonical_name": resolved.canonical_name,
                                "sources": list(resolved.sources),
                                "mention_count": len(resolved.mentions),
                                "confidence": resolved.cross_source_score,
                            }
                        )

        # Calculate statistics
        statistics = self._calculate_statistics(mentions, resolved_entities, cross_source_matches)

        return ResolutionResult(
            resolved_entities=resolved_entities,
            unresolved_mentions=unresolved_mentions,
            resolution_statistics=statistics,
            cross_source_matches=cross_source_matches,
        )

    def _group_by_type(
        self, mentions: List[EntityMention]
    ) -> Dict[EntityType, List[EntityMention]]:
        """Group mentions by entity type."""
        grouped = defaultdict(list)
        for mention in mentions:
            grouped[mention.entity_type].append(mention)
        return grouped

    def _build_similarity_matrix(self, mentions: List[EntityMention]) -> List[List[float]]:
        """Build pairwise similarity matrix for mentions."""
        n = len(mentions)
        matrix = [[0.0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i, n):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    similarity = self._compute_similarity(mentions[i], mentions[j])
                    matrix[i][j] = similarity
                    matrix[j][i] = similarity

        return matrix

    def _compute_similarity(self, mention1: EntityMention, mention2: EntityMention) -> float:
        """Compute overall similarity between two mentions."""
        # String similarity (Jaro-Winkler)
        string_sim = self._jaro_winkler(
            self._normalize_text(mention1.text), self._normalize_text(mention2.text)
        )

        # Phonetic similarity
        phonetic_sim = self._phonetic_similarity(mention1.text, mention2.text)

        # Context similarity (if available)
        context_sim = 0.0
        if mention1.context and mention2.context:
            context_sim = self._context_similarity(mention1.context, mention2.context)

        # Weighted combination
        base_weight = 1.0 - self.phonetic_weight - self.context_weight
        similarity = (
            base_weight * string_sim
            + self.phonetic_weight * phonetic_sim
            + self.context_weight * context_sim
        )

        # Boost score if from different sources (cross-source evidence)
        if mention1.source_type != mention2.source_type:
            similarity *= 1.1  # 10% boost for cross-source matches
            similarity = min(similarity, 1.0)

        return similarity

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        normalized = text.lower()
        # Remove common prefixes/suffixes
        for prefix in ["mr.", "mrs.", "ms.", "dr.", "the ", "inc.", "corp.", "llc"]:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :].strip()
            if normalized.endswith(prefix.rstrip(".")):
                normalized = normalized[: -len(prefix.rstrip("."))].strip()
        # Remove punctuation
        normalized = re.sub(r"[^\w\s]", "", normalized)
        # Collapse whitespace
        normalized = " ".join(normalized.split())
        return normalized

    def _jaro_winkler(self, s1: str, s2: str) -> float:
        """
        Calculate Jaro-Winkler similarity between two strings.

        Returns a value between 0 and 1, where 1 is an exact match.
        """
        if not s1 or not s2:
            return 0.0

        if s1 == s2:
            return 1.0

        len1, len2 = len(s1), len(s2)
        match_distance = max(len1, len2) // 2 - 1
        match_distance = max(0, match_distance)

        s1_matches = [False] * len1
        s2_matches = [False] * len2

        matches = 0
        transpositions = 0

        # Find matches
        for i in range(len1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len2)

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
        for i in range(len1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1

        jaro = (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3

        # Calculate common prefix (up to 4 characters)
        prefix = 0
        for i in range(min(4, len1, len2)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break

        # Winkler modification
        return jaro + prefix * 0.1 * (1 - jaro)

    def _soundex(self, text: str) -> str:
        """Generate Soundex code for a string."""
        if not text:
            return ""

        text = text.upper()
        # Keep first letter
        soundex = text[0]

        # Convert rest of string
        for char in text[1:]:
            if char in self.SOUNDEX_MAP:
                code = self.SOUNDEX_MAP[char]
                if code != soundex[-1]:  # Avoid consecutive duplicates
                    soundex += code
            # Vowels and H, W are ignored

        # Pad or truncate to 4 characters
        soundex = (soundex + "000")[:4]
        return soundex

    def _phonetic_similarity(self, text1: str, text2: str) -> float:
        """Calculate phonetic similarity using Soundex."""
        # Get Soundex for each word
        words1 = text1.split()
        words2 = text2.split()

        if not words1 or not words2:
            return 0.0

        codes1 = [self._soundex(w) for w in words1]
        codes2 = [self._soundex(w) for w in words2]

        # Match codes
        matches = 0
        total = max(len(codes1), len(codes2))

        for code1 in codes1:
            if code1 in codes2:
                matches += 1

        return matches / total if total > 0 else 0.0

    def _context_similarity(self, context1: str, context2: str) -> float:
        """Calculate contextual similarity between two contexts."""
        # Simple word overlap for now
        words1 = set(context1.lower().split())
        words2 = set(context2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _transitive_clustering(
        self, mentions: List[EntityMention], similarity_matrix: List[List[float]]
    ) -> List[List[EntityMention]]:
        """
        Perform transitive clustering based on similarity.

        Uses a union-find approach to group similar mentions.
        """
        n = len(mentions)
        if n == 0:
            return []

        # Union-Find data structure
        parent = list(range(n))
        rank = [0] * n

        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px == py:
                return
            if rank[px] < rank[py]:
                px, py = py, px
            parent[py] = px
            if rank[px] == rank[py]:
                rank[px] += 1

        # Merge similar mentions
        for i in range(n):
            for j in range(i + 1, n):
                if similarity_matrix[i][j] >= self.similarity_threshold:
                    union(i, j)

        # Group by cluster
        clusters_dict: Dict[int, List[EntityMention]] = defaultdict(list)
        for i in range(n):
            root = find(i)
            clusters_dict[root].append(mentions[i])

        return list(clusters_dict.values())

    def _create_resolved_entity(
        self, cluster: List[EntityMention], entity_type: EntityType
    ) -> ResolvedEntity:
        """Create a resolved entity from a cluster of mentions."""
        # Choose canonical name (most frequent or highest confidence)
        name_counts: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        for mention in cluster:
            normalized = self._normalize_text(mention.text)
            count, conf = name_counts[normalized]
            name_counts[normalized] = (count + 1, max(conf, mention.confidence))

        # Select canonical name by frequency, then confidence
        canonical = max(name_counts.items(), key=lambda x: (x[1][0], x[1][1]))[0]

        # Collect all variations and sources
        aliases = {self._normalize_text(m.text) for m in cluster}
        aliases.discard(canonical)

        sources = {m.source_type for m in cluster}

        # Calculate cross-source confidence score
        source_count = len(sources)
        mention_count = len(cluster)
        avg_confidence = sum(m.confidence for m in cluster) / mention_count

        # Higher score for more sources and higher individual confidence
        cross_source_score = min(avg_confidence * (1 + 0.2 * (source_count - 1)), 1.0)

        # Generate entity ID
        import hashlib

        entity_id = hashlib.md5(f"{entity_type.value}:{canonical}".encode()).hexdigest()[:12]

        return ResolvedEntity(
            canonical_name=canonical.title(),  # Title case for display
            entity_type=entity_type,
            entity_id=entity_id,
            mentions=cluster,
            aliases=aliases,
            sources=sources,
            cross_source_score=cross_source_score,
            metadata={
                "mention_count": mention_count,
                "source_count": source_count,
                "avg_confidence": avg_confidence,
            },
        )

    def _calculate_statistics(
        self,
        mentions: List[EntityMention],
        resolved: List[ResolvedEntity],
        cross_source: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate resolution statistics."""
        total_mentions = len(mentions)
        total_entities = len(resolved)
        cross_source_count = len(cross_source)

        # Calculate reduction ratio
        reduction_ratio = 1 - (total_entities / total_mentions) if total_mentions > 0 else 0

        # Source distribution
        source_dist: Dict[str, int] = defaultdict(int)
        for mention in mentions:
            source_dist[mention.source_type.value] += 1

        # Entity type distribution
        type_dist: Dict[str, int] = defaultdict(int)
        for entity in resolved:
            type_dist[entity.entity_type.value] += 1

        return {
            "total_mentions": total_mentions,
            "total_entities": total_entities,
            "reduction_ratio": reduction_ratio,
            "cross_source_matches": cross_source_count,
            "cross_source_ratio": cross_source_count / total_entities if total_entities > 0 else 0,
            "source_distribution": dict(source_dist),
            "entity_type_distribution": dict(type_dist),
        }

    def find_matching_entity(
        self, query: str, resolved_entities: List[ResolvedEntity], threshold: float = 0.8
    ) -> Optional[ResolvedEntity]:
        """
        Find a resolved entity matching a query string.

        Args:
            query: Entity name to search for
            resolved_entities: List of resolved entities to search
            threshold: Minimum similarity threshold

        Returns:
            Best matching ResolvedEntity or None
        """
        normalized_query = self._normalize_text(query)
        best_match = None
        best_score = 0.0

        for entity in resolved_entities:
            # Check canonical name
            score = self._jaro_winkler(
                normalized_query, self._normalize_text(entity.canonical_name)
            )

            # Check aliases
            for alias in entity.aliases:
                alias_score = self._jaro_winkler(normalized_query, alias)
                score = max(score, alias_score)

            if score > best_score and score >= threshold:
                best_score = score
                best_match = entity

        return best_match

    def generate_resolution_report(self, result: ResolutionResult) -> str:
        """Generate a human-readable resolution report."""
        report = []
        report.append("=" * 60)
        report.append("ENTITY RESOLUTION REPORT")
        report.append("=" * 60)
        report.append("")

        stats = result.resolution_statistics
        report.append("STATISTICS:")
        report.append(f"  Total Mentions: {stats['total_mentions']}")
        report.append(f"  Resolved Entities: {stats['total_entities']}")
        report.append(f"  Reduction Ratio: {stats['reduction_ratio']:.1%}")
        report.append(f"  Cross-Source Matches: {stats['cross_source_matches']}")
        report.append("")

        report.append("CROSS-SOURCE MATCHES:")
        for match in result.cross_source_matches[:10]:  # Top 10
            report.append(f"  - {match['canonical_name']}")
            report.append(f"    Sources: {', '.join(match['sources'])}")
            report.append(f"    Confidence: {match['confidence']:.2%}")

        if len(result.cross_source_matches) > 10:
            report.append(f"  ... and {len(result.cross_source_matches) - 10} more")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)
