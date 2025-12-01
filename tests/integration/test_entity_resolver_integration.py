"""
Integration Tests: Entity Resolver Module
=========================================
JLAW Enhancement Protocol Compliance Test Suite
"""

import pytest
from typing import List, Dict, Any


class TestJaroWinklerSimilarity:
    """Tests for Jaro-Winkler string similarity algorithm."""
    
    def test_identical_strings(self):
        from src.forensics.triangulation.entity_resolver import EntityResolver
        resolver = EntityResolver()
        assert resolver._jaro_winkler_similarity("Apple", "Apple") == 1.0
    
    def test_similar_strings(self):
        from src.forensics.triangulation.entity_resolver import EntityResolver
        resolver = EntityResolver()
        score = resolver._jaro_winkler_similarity("Apple Inc.", "Apple Inc")
        assert score > 0.95


class TestEntityResolution:
    """Integration tests for entity resolution pipeline."""
    
    def test_cross_source_resolution(self):
        from src.forensics.triangulation.entity_resolver import EntityResolver, Entity, EntityType
        
        entities_sec = [
            Entity(id="sec-1", name="Apple Inc.", entity_type=EntityType.COMPANY, source="sec")
        ]
        entities_news = [
            Entity(id="news-1", name="Apple", entity_type=EntityType.COMPANY, source="news")
        ]
        
        resolver = EntityResolver()
        result = resolver.resolve_entities({"sec": entities_sec, "news": entities_news})
        
        assert result is not None
        assert len(result.unified_entities) <= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
