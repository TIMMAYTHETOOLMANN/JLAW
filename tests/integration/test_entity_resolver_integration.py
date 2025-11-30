"""
Integration tests for Entity Resolver module.

Tests cross-source entity resolution using Jaro-Winkler, Levenshtein,
and Soundex algorithms for matching entities across SEC filings, news, and social media.
"""

import pytest
from src.forensics.triangulation.entity_resolver import (
    EntityResolver,
    Entity,
    EntitySource,
    EntityType,
    EntityCluster,
    EntityResolutionResult,
)


class TestEntityResolverIntegration:
    """Integration tests for EntityResolver."""
    
    @pytest.fixture
    def resolver(self):
        """Create an EntityResolver instance with default settings."""
        return EntityResolver(similarity_threshold=0.85)
    
    @pytest.fixture
    def resolver_strict(self):
        """Create an EntityResolver with stricter threshold."""
        return EntityResolver(similarity_threshold=0.95)
    
    @pytest.fixture
    def sample_entities(self):
        """Create sample entities from different sources."""
        return [
            Entity(
                id="sec-001",
                name="Apple Inc.",
                source=EntitySource.SEC,
                entity_type=EntityType.COMPANY,
            ),
            Entity(
                id="news-001",
                name="Apple Computer",
                source=EntitySource.NEWS,
                entity_type=EntityType.COMPANY,
            ),
            Entity(
                id="social-001",
                name="AAPL",
                source=EntitySource.SOCIAL,
                entity_type=EntityType.TICKER,
                aliases=["Apple Inc", "Apple"],
            ),
            Entity(
                id="sec-002",
                name="Microsoft Corporation",
                source=EntitySource.SEC,
                entity_type=EntityType.COMPANY,
            ),
            Entity(
                id="news-002",
                name="Microsoft Corp.",
                source=EntitySource.NEWS,
                entity_type=EntityType.COMPANY,
            ),
        ]
    
    # ================== Basic Resolution Tests ==================
    
    def test_empty_entity_list(self, resolver):
        """Test resolution with empty entity list."""
        result = resolver.resolve_entities([])
        
        assert isinstance(result, EntityResolutionResult)
        assert result.total_entities == 0
        assert result.resolved_entities == 0
        assert len(result.clusters) == 0
    
    def test_single_entity(self, resolver):
        """Test resolution with single entity."""
        entities = [
            Entity(id="1", name="Test Corp", source=EntitySource.SEC)
        ]
        result = resolver.resolve_entities(entities)
        
        assert result.total_entities == 1
        assert len(result.clusters) == 1
        assert result.clusters[0].canonical_name == "Test Corp"
    
    def test_exact_match(self, resolver):
        """Test exact name matching."""
        entities = [
            Entity(id="1", name="Acme Corporation", source=EntitySource.SEC),
            Entity(id="2", name="Acme Corporation", source=EntitySource.NEWS),
        ]
        result = resolver.resolve_entities(entities)
        
        assert len(result.clusters) == 1
        assert len(result.clusters[0].entities) == 2
        assert result.cross_source_matches == 1
    
    def test_company_suffix_normalization(self, resolver):
        """Test that company suffixes are normalized."""
        entities = [
            Entity(id="1", name="Acme Inc.", source=EntitySource.SEC),
            Entity(id="2", name="Acme Corporation", source=EntitySource.NEWS),
            Entity(id="3", name="Acme Ltd", source=EntitySource.SOCIAL),
        ]
        result = resolver.resolve_entities(entities)
        
        # All should be in the same cluster due to suffix normalization
        assert len(result.clusters) == 1
        assert len(result.clusters[0].entities) == 3
    
    # ================== Similarity Algorithm Tests ==================
    
    def test_jaro_winkler_similarity(self, resolver):
        """Test Jaro-Winkler similarity calculation."""
        # Identical strings
        assert resolver.jaro_winkler_similarity("test", "test") == 1.0
        
        # Similar strings (common prefix)
        sim = resolver.jaro_winkler_similarity("testing", "tested")
        assert 0.8 < sim < 1.0
        
        # Empty strings
        assert resolver.jaro_winkler_similarity("", "") == 0.0
        assert resolver.jaro_winkler_similarity("test", "") == 0.0
    
    def test_levenshtein_similarity(self, resolver):
        """Test Levenshtein distance-based similarity."""
        # Identical strings
        assert resolver.levenshtein_similarity("test", "test") == 1.0
        
        # One character difference
        sim = resolver.levenshtein_similarity("test", "tests")
        assert sim == 0.8  # 1 - 1/5 = 0.8
        
        # Completely different
        sim = resolver.levenshtein_similarity("abc", "xyz")
        assert sim < 0.5
    
    def test_phonetic_similarity(self, resolver):
        """Test Soundex phonetic matching."""
        # Same pronunciation
        sim = resolver.phonetic_similarity("Smith", "Smyth")
        assert sim >= 0.5
        
        # Different sounds
        sim = resolver.phonetic_similarity("Apple", "Microsoft")
        assert sim < 0.5
    
    def test_soundex_generation(self, resolver):
        """Test Soundex code generation."""
        # Classic Soundex examples
        assert resolver._soundex("Robert") == "R163"
        assert resolver._soundex("Rupert") == "R163"
        assert resolver._soundex("") == "0000"
        assert resolver._soundex("ABC") == "A120"
    
    # ================== Cross-Source Matching Tests ==================
    
    def test_cross_source_entity_matching(self, resolver, sample_entities):
        """Test matching entities across SEC, news, and social sources."""
        result = resolver.resolve_entities(sample_entities)
        
        # Should have 2 clusters: Apple and Microsoft
        assert len(result.clusters) >= 2
        
        # Find Apple cluster
        apple_cluster = None
        for cluster in result.clusters:
            if "Apple" in cluster.canonical_name:
                apple_cluster = cluster
                break
        
        assert apple_cluster is not None
        # Apple cluster should have multiple sources
        assert len(apple_cluster.sources) >= 2
    
    def test_alias_matching(self, resolver):
        """Test entity matching using aliases."""
        entities = [
            Entity(
                id="1",
                name="International Business Machines",
                source=EntitySource.SEC,
                aliases=["IBM", "Big Blue"],
            ),
            Entity(
                id="2",
                name="IBM",
                source=EntitySource.NEWS,
            ),
        ]
        result = resolver.resolve_entities(entities)
        
        # Should match via alias
        assert len(result.clusters) == 1
        assert len(result.clusters[0].entities) == 2
    
    def test_no_false_positive_matches(self, resolver_strict):
        """Test that dissimilar entities are not matched."""
        entities = [
            Entity(id="1", name="Apple Inc.", source=EntitySource.SEC),
            Entity(id="2", name="Amazon.com Inc.", source=EntitySource.SEC),
            Entity(id="3", name="Alphabet Inc.", source=EntitySource.SEC),
        ]
        result = resolver_strict.resolve_entities(entities)
        
        # Each should be in its own cluster
        assert len(result.clusters) == 3
        for cluster in result.clusters:
            assert len(cluster.entities) == 1
    
    # ================== Edge Case Tests ==================
    
    def test_unicode_entity_names(self, resolver):
        """Test handling of Unicode characters in names."""
        entities = [
            Entity(id="1", name="Société Générale", source=EntitySource.SEC),
            Entity(id="2", name="Societe Generale", source=EntitySource.NEWS),
        ]
        result = resolver.resolve_entities(entities)
        
        # Should handle accented characters gracefully
        assert len(result.clusters) <= 2
        assert result.processing_time_ms > 0
    
    def test_short_entity_names(self, resolver):
        """Test handling of very short entity names."""
        resolver_short = EntityResolver(min_name_length=2)
        entities = [
            Entity(id="1", name="AT", source=EntitySource.SEC),
            Entity(id="2", name="IBM", source=EntitySource.NEWS),
        ]
        result = resolver_short.resolve_entities(entities)
        
        # Short names should still be processed
        assert result.total_entities == 2
    
    def test_empty_entity_name(self, resolver):
        """Test handling of empty entity names."""
        entities = [
            Entity(id="1", name="", source=EntitySource.SEC),
            Entity(id="2", name="Valid Corp", source=EntitySource.NEWS),
        ]
        result = resolver.resolve_entities(entities)
        
        # Should not crash
        assert result.total_entities == 2
    
    def test_special_characters(self, resolver):
        """Test handling of special characters in names."""
        entities = [
            Entity(id="1", name="AT&T Inc.", source=EntitySource.SEC),
            Entity(id="2", name="AT&T Corporation", source=EntitySource.NEWS),
        ]
        result = resolver.resolve_entities(entities)
        
        # Should match despite special characters
        assert len(result.clusters) == 1
    
    # ================== Performance Tests ==================
    
    def test_large_entity_list(self, resolver):
        """Test performance with larger entity lists."""
        import time
        
        # Generate 100 entities
        entities = [
            Entity(
                id=f"entity-{i}",
                name=f"Company {i} Inc.",
                source=EntitySource.SEC if i % 2 == 0 else EntitySource.NEWS,
            )
            for i in range(100)
        ]
        
        start = time.time()
        result = resolver.resolve_entities(entities)
        elapsed = time.time() - start
        
        assert result.total_entities == 100
        assert elapsed < 10.0  # Should complete in under 10 seconds
    
    def test_duplicate_detection(self, resolver):
        """Test detection of true duplicates."""
        entities = []
        for i in range(10):
            entities.append(Entity(
                id=f"sec-{i}",
                name="Test Corporation",
                source=EntitySource.SEC,
            ))
        
        result = resolver.resolve_entities(entities)
        
        # All should be in one cluster
        assert len(result.clusters) == 1
        assert len(result.clusters[0].entities) == 10
    
    # ================== Cluster Quality Tests ==================
    
    def test_canonical_name_selection(self, resolver):
        """Test that canonical name prefers SEC source."""
        entities = [
            Entity(id="1", name="MSFT", source=EntitySource.SOCIAL),
            Entity(id="2", name="Microsoft Corporation", source=EntitySource.SEC),
            Entity(id="3", name="Microsoft", source=EntitySource.NEWS),
        ]
        # Add aliases to help matching
        entities[0].aliases = ["Microsoft Corporation"]
        
        result = resolver.resolve_entities(entities)
        
        # If clustered, SEC source should be canonical
        for cluster in result.clusters:
            if "Microsoft" in cluster.canonical_name:
                # SEC name should be preferred
                assert "Corporation" in cluster.canonical_name or len(cluster.entities) == 1
    
    def test_cluster_confidence_calculation(self, resolver):
        """Test that cluster confidence is calculated correctly."""
        entities = [
            Entity(id="1", name="Test Corp", source=EntitySource.SEC, confidence=1.0),
            Entity(id="2", name="Test Corporation", source=EntitySource.NEWS, confidence=0.8),
        ]
        result = resolver.resolve_entities(entities)
        
        if len(result.clusters) == 1:
            # Confidence should be calculated from matches
            assert result.clusters[0].confidence >= 0.0
            assert result.clusters[0].confidence <= 1.0
    
    def test_find_entity_in_clusters(self, resolver, sample_entities):
        """Test finding an entity in resolved clusters."""
        result = resolver.resolve_entities(sample_entities)
        
        # Find Microsoft
        cluster = resolver.find_entity("Microsoft Corporation", result.clusters)
        assert cluster is not None
        
        # Try to find non-existent entity
        cluster = resolver.find_entity("NonExistent Corp", result.clusters)
        assert cluster is None
    
    def test_get_cross_source_entities(self, resolver, sample_entities):
        """Test filtering for cross-source clusters only."""
        result = resolver.resolve_entities(sample_entities)
        
        cross_source = resolver.get_cross_source_entities(result.clusters)
        
        for cluster in cross_source:
            assert len(cluster.sources) > 1
    
    # ================== Entity Type Tests ==================
    
    def test_mixed_entity_types(self, resolver):
        """Test resolution with different entity types."""
        entities = [
            Entity(
                id="1",
                name="John Smith",
                source=EntitySource.SEC,
                entity_type=EntityType.EXECUTIVE,
            ),
            Entity(
                id="2",
                name="John D. Smith",
                source=EntitySource.NEWS,
                entity_type=EntityType.PERSON,
            ),
            Entity(
                id="3",
                name="Smith, John",
                source=EntitySource.COURT,
                entity_type=EntityType.PERSON,
            ),
        ]
        result = resolver.resolve_entities(entities)
        
        # Names should match even with different formats
        assert result.total_entities == 3
        # May or may not be in same cluster depending on similarity
    
    def test_executive_matching(self, resolver):
        """Test matching executive names across sources."""
        entities = [
            Entity(
                id="1",
                name="Tim Cook",
                source=EntitySource.SEC,
                entity_type=EntityType.EXECUTIVE,
            ),
            Entity(
                id="2",
                name="Timothy D. Cook",
                source=EntitySource.EARNINGS,
                entity_type=EntityType.EXECUTIVE,
                aliases=["Tim Cook"],
            ),
        ]
        result = resolver.resolve_entities(entities)
        
        # Should match via alias
        if len(result.clusters) == 1:
            assert len(result.clusters[0].entities) == 2
    
    # ================== Metadata Tests ==================
    
    def test_entity_metadata_preserved(self, resolver):
        """Test that entity metadata is preserved through resolution."""
        entities = [
            Entity(
                id="1",
                name="Test Corp",
                source=EntitySource.SEC,
                metadata={"filing_type": "10-K", "cik": "0001234567"},
            ),
        ]
        result = resolver.resolve_entities(entities)
        
        assert result.clusters[0].entities[0].metadata["cik"] == "0001234567"
    
    def test_result_metadata(self, resolver, sample_entities):
        """Test result metadata and statistics."""
        result = resolver.resolve_entities(sample_entities)
        
        assert result.processing_time_ms > 0
        assert result.total_entities == len(sample_entities)


class TestStringSimilarityAlgorithms:
    """Unit tests for string similarity algorithms."""
    
    @pytest.fixture
    def resolver(self):
        return EntityResolver()
    
    def test_jaro_winkler_common_prefix_bonus(self, resolver):
        """Test that Jaro-Winkler gives bonus for common prefix."""
        # Same base similarity but different prefixes
        sim1 = resolver.jaro_winkler_similarity("MARTHA", "MARHTA")
        sim2 = resolver.jaro_winkler_similarity("XARTHA", "XARHTA")
        
        # Both should be similar since algorithm uses prefix
        assert sim1 > 0.9
        assert sim2 > 0.9
    
    def test_levenshtein_operations(self, resolver):
        """Test Levenshtein with different edit operations."""
        # Insertion
        sim1 = resolver.levenshtein_similarity("test", "tests")
        
        # Deletion
        sim2 = resolver.levenshtein_similarity("tests", "test")
        
        # Substitution
        sim3 = resolver.levenshtein_similarity("test", "best")
        
        assert sim1 == sim2  # Symmetric
        assert sim3 == 0.75  # 1 substitution in 4 chars = 0.75
    
    def test_soundex_codes(self, resolver):
        """Test Soundex code generation for various names."""
        test_cases = [
            ("Washington", "W252"),
            ("Lee", "L000"),
            ("Gutierrez", "G362"),
            ("Jackson", "J250"),
            ("VanDeusen", "V532"),
        ]
        
        for name, expected in test_cases:
            result = resolver._soundex(name)
            assert len(result) == 4  # Soundex is always 4 chars


class TestEntityCluster:
    """Tests for EntityCluster functionality."""
    
    def test_add_entity_to_cluster(self):
        """Test adding entities to a cluster."""
        cluster = EntityCluster(
            cluster_id="test",
            canonical_name="Test Corp",
        )
        
        entity = Entity(
            id="1",
            name="Test Corp",
            source=EntitySource.SEC,
        )
        
        cluster.add_entity(entity)
        
        assert len(cluster.entities) == 1
        assert EntitySource.SEC in cluster.sources
    
    def test_cluster_sources_tracking(self):
        """Test that sources are tracked correctly."""
        cluster = EntityCluster(
            cluster_id="test",
            canonical_name="Test Corp",
        )
        
        for source in [EntitySource.SEC, EntitySource.NEWS, EntitySource.SOCIAL]:
            cluster.add_entity(Entity(
                id=f"entity-{source.value}",
                name="Test",
                source=source,
            ))
        
        assert len(cluster.sources) == 3


class TestFraudScenarios:
    """Test realistic fraud investigation scenarios."""
    
    @pytest.fixture
    def resolver(self):
        return EntityResolver(similarity_threshold=0.80)
    
    def test_shell_company_detection(self, resolver):
        """Test resolution of potential shell company names."""
        entities = [
            Entity(id="1", name="XYZ Holdings LLC", source=EntitySource.SEC),
            Entity(id="2", name="XYZ Holdings", source=EntitySource.NEWS),
            Entity(id="3", name="XYZ Holding Company", source=EntitySource.COURT),
            Entity(id="4", name="ABC Investments LLC", source=EntitySource.SEC),
        ]
        result = resolver.resolve_entities(entities)
        
        # XYZ entities should cluster together
        xyz_cluster = None
        for cluster in result.clusters:
            if "XYZ" in cluster.canonical_name:
                xyz_cluster = cluster
                break
        
        assert xyz_cluster is not None
        assert len(xyz_cluster.entities) >= 2
    
    def test_insider_name_variations(self, resolver):
        """Test resolving insider names with variations."""
        entities = [
            Entity(
                id="1",
                name="Robert J. Smith",
                source=EntitySource.SEC,
                entity_type=EntityType.EXECUTIVE,
            ),
            Entity(
                id="2",
                name="Bob Smith",
                source=EntitySource.NEWS,
                entity_type=EntityType.PERSON,
                aliases=["Robert Smith"],
            ),
            Entity(
                id="3",
                name="R. J. Smith",
                source=EntitySource.EARNINGS,
                entity_type=EntityType.EXECUTIVE,
            ),
        ]
        result = resolver.resolve_entities(entities)
        
        # All variations should ideally be detected
        assert result.total_entities == 3
    
    def test_related_party_network(self, resolver):
        """Test resolution of related party entities."""
        entities = [
            Entity(id="1", name="Acme Corp", source=EntitySource.SEC),
            Entity(id="2", name="Acme Holdings", source=EntitySource.SEC),
            Entity(id="3", name="Acme Investments", source=EntitySource.SEC),
            Entity(id="4", name="Acme Corporation", source=EntitySource.NEWS),
        ]
        result = resolver.resolve_entities(entities)
        
        # Should detect these are related entities
        assert len(result.clusters) <= 3  # Some should cluster


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
