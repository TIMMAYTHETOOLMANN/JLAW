"""
JLAW Triangulation Module
=========================

Cross-source entity resolution and triangulation for forensic investigations.

Components:
- EntityResolver: Cross-source entity resolution with Jaro-Winkler similarity
"""

from .entity_resolver import (
    EntityMention,
    EntityResolver,
    EntityType,
    ResolutionResult,
    ResolvedEntity,
    SourceType,
)

__all__ = [
    "EntityResolver",
    "EntityMention",
    "ResolvedEntity",
    "ResolutionResult",
    "EntityType",
    "SourceType",
]

__version__ = "1.0.0"
