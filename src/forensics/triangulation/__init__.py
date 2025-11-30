"""
Triangulation - Cross-Source Entity Resolution and Evidence Correlation

This module provides entity resolution and cross-source triangulation capabilities
for correlating entities across SEC filings, news sources, and social media.
"""

from src.forensics.triangulation.entity_resolver import (
    EntityResolver,
    Entity,
    EntitySource,
    EntityCluster,
    EntityMatch,
    EntityResolutionResult,
)

__all__ = [
    "EntityResolver",
    "Entity",
    "EntitySource",
    "EntityCluster",
    "EntityMatch",
    "EntityResolutionResult",
]
