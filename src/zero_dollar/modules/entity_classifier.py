"""
Entity Classifier Module
=========================

Entity classification taxonomy for beneficial ownership chain resolution.

Per Section 7.2 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 7.2: Entity Classification Taxonomy
"""

from dataclasses import dataclass
from typing import Dict, List
from src.zero_dollar.models import EntityType


@dataclass
class EntityTypeInfo:
    """
    Information about a beneficial ownership entity type.
    
    Attributes:
        entity_type: Type of entity
        description: Human-readable description
        beneficial_ownership_indicators: How beneficial ownership is assessed
        cross_reference_sources: External data sources for verification
        control_presumption: Level of control presumption (HIGH, MODERATE, LOW)
    """
    entity_type: EntityType
    description: str
    beneficial_ownership_indicators: str
    cross_reference_sources: List[str]
    control_presumption: str  # HIGH, MODERATE, LOW


# Entity Type Taxonomy per Section 7.2
ENTITY_TYPE_TAXONOMY: Dict[EntityType, EntityTypeInfo] = {
    EntityType.RLT: EntityTypeInfo(
        EntityType.RLT,
        "Revocable Living Trust",
        "Grantor retains full control; no economic separation",
        ["State trust registries", "Form 4 footnotes"],
        "HIGH"
    ),
    EntityType.IRT: EntityTypeInfo(
        EntityType.IRT,
        "Irrevocable Trust",
        "Grantor may retain indirect control via trustee selection",
        ["IRS Form 3520", "Schedule 13D"],
        "MODERATE"
    ),
    EntityType.GRAT: EntityTypeInfo(
        EntityType.GRAT,
        "Grantor Retained Annuity Trust",
        "Grantor retains annuity interest; remainder to beneficiaries",
        ["IRS Form 709", "Form 4 footnotes"],
        "MODERATE"
    ),
    EntityType.FLP: EntityTypeInfo(
        EntityType.FLP,
        "Family Limited Partnership",
        "General partner (often grantor) retains management control",
        ["State LP filings", "Schedule 13D"],
        "HIGH"
    ),
    EntityType.LLC: EntityTypeInfo(
        EntityType.LLC,
        "Limited Liability Company",
        "Operating agreement may vest control in transferor",
        ["State LLC filings", "Schedule 13D"],
        "MODERATE"
    ),
    EntityType.DAF: EntityTypeInfo(
        EntityType.DAF,
        "Donor-Advised Fund",
        "Donor retains advisory privileges; no legal control",
        ["IRS Form 990", "Form 4 footnotes"],
        "LOW"
    ),
    EntityType.PF: EntityTypeInfo(
        EntityType.PF,
        "Private Foundation",
        "Founders often serve as directors/officers",
        ["IRS Form 990-PF", "Schedule 13D"],
        "MODERATE"
    ),
    EntityType.CRT: EntityTypeInfo(
        EntityType.CRT,
        "Charitable Remainder Trust",
        "Income interest retained; charitable remainder",
        ["IRS Form 5227", "Form 4 footnotes"],
        "MODERATE"
    ),
    EntityType.SPOUSE: EntityTypeInfo(
        EntityType.SPOUSE,
        "Spousal Transfer",
        "Aggregation required under Section 16",
        ["Form 4 footnotes", "Schedule 13D"],
        "HIGH"
    ),
    EntityType.CHILD: EntityTypeInfo(
        EntityType.CHILD,
        "Minor Child Transfer",
        "Parent may exercise control until majority",
        ["Form 4 footnotes", "State guardianship"],
        "HIGH"
    ),
}


def get_entity_type_info(entity_type: EntityType) -> EntityTypeInfo:
    """
    Get detailed information about an entity type.
    
    Args:
        entity_type: EntityType enum value
        
    Returns:
        EntityTypeInfo with description and control indicators
    """
    return ENTITY_TYPE_TAXONOMY.get(entity_type)


def get_control_presumption(entity_type: EntityType) -> str:
    """
    Get control presumption level for an entity type.
    
    Args:
        entity_type: EntityType enum value
        
    Returns:
        Control presumption level: HIGH, MODERATE, or LOW
    """
    info = ENTITY_TYPE_TAXONOMY.get(entity_type)
    return info.control_presumption if info else "LOW"


def classify_entity_by_description(description: str) -> EntityType:
    """
    Classify entity type from description text.
    
    Performs fuzzy matching against known entity type patterns.
    
    Args:
        description: Entity description from Form 4
        
    Returns:
        Most likely EntityType, or EntityType.LLC as default
    """
    desc_lower = description.lower()
    
    # Trust patterns
    if "revocable" in desc_lower and "trust" in desc_lower:
        return EntityType.RLT
    if "irrevocable" in desc_lower and "trust" in desc_lower:
        return EntityType.IRT
    if "grat" in desc_lower or "grantor retained annuity" in desc_lower:
        return EntityType.GRAT
    if "charitable remainder" in desc_lower:
        return EntityType.CRT
    
    # Foundation/Charity patterns
    if "foundation" in desc_lower:
        return EntityType.PF
    if "donor" in desc_lower and "advised" in desc_lower:
        return EntityType.DAF
    
    # Partnership/LLC patterns
    if "partnership" in desc_lower or "flp" in desc_lower:
        return EntityType.FLP
    if "llc" in desc_lower or "l.l.c" in desc_lower or "limited liability" in desc_lower:
        return EntityType.LLC
    
    # Family patterns
    if "spouse" in desc_lower or "wife" in desc_lower or "husband" in desc_lower:
        return EntityType.SPOUSE
    if "child" in desc_lower or "son" in desc_lower or "daughter" in desc_lower:
        return EntityType.CHILD
    
    # Default to LLC for unknown corporate entities
    return EntityType.LLC
