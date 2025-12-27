"""
Footnote Parser Module
======================

Extract entity references from Form 4 footnotes using regex patterns.

Per Section 7.3 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 7.3: Footnote Parsing Algorithm
"""

import re
import uuid
from typing import List, Tuple
from decimal import Decimal

from src.zero_dollar.models import EntityType, EntityReference


def parse_ownership_footnotes(
    footnotes: List[str],
    reporting_person_cik: str,
    transaction_accession: str
) -> List[EntityReference]:
    """
    Extract entity references from Form 4 footnotes.
    
    Common patterns:
        - "Transferred to [Entity Name] Trust"
        - "Gift to [Entity Name] Foundation"
        - "Transferred to [Name] Family LP"
        - "Shares held by [Entity Name] LLC"
    
    Args:
        footnotes: List of footnote strings from Form 4
        reporting_person_cik: CIK of reporting person
        transaction_accession: Transaction accession number
        
    Returns:
        List[EntityReference]: Parsed entity references with classification
    """
    entity_patterns = [
        # Trust patterns
        (r'(?:transferred?\s+to|held\s+by|for\s+the\s+benefit\s+of)\s+(?:the\s+)?([A-Z][A-Za-z\s\.]+?)\s+(?:Revocable\s+)?Trust', EntityType.RLT),
        (r'([A-Z][A-Za-z\s\.]+?)\s+(?:Family\s+)?(?:Revocable\s+)?Trust', EntityType.RLT),
        (r'(?:GRAT|Grantor\s+Retained\s+Annuity\s+Trust)\s+(?:dated|established|created)', EntityType.GRAT),
        (r'([A-Z][A-Za-z\s\.]+?)\s+Irrevocable\s+Trust', EntityType.IRT),
        
        # Foundation/Charity patterns
        (r'(?:the\s+)?([A-Z][A-Za-z\s\.]+?)\s+(?:Family\s+)?Foundation', EntityType.PF),
        (r'(?:the\s+)?([A-Z][A-Za-z\s\.]+?)\s+(?:Family\s+)?Charitable', EntityType.PF),
        (r'(?:donor[\s-]?advised\s+fund|DAF)\s+(?:at|with)\s+([A-Z][A-Za-z\s\.]+)', EntityType.DAF),
        (r'charitable\s+remainder\s+(?:uni)?trust', EntityType.CRT),
        
        # Partnership/LLC patterns
        (r'([A-Z][A-Za-z\s\.]+?)\s+(?:Family\s+)?(?:Limited\s+)?Partnership', EntityType.FLP),
        (r'([A-Z][A-Za-z\s\.]+?)\s+(?:Holdings?\s+)?LLC', EntityType.LLC),
        (r'([A-Z][A-Za-z\s\.]+?)\s+(?:Holdings?\s+)?L\.?L\.?C\.?', EntityType.LLC),
        
        # Spousal/Family patterns
        (r'(?:gift\s+to|transferred?\s+to)\s+(?:his|her)\s+(?:wife|husband|spouse)', EntityType.SPOUSE),
        (r'(?:gift\s+to|transferred?\s+to)\s+(?:his|her)\s+(?:son|daughter|child)', EntityType.CHILD),
        (r'(?:UTMA|UGMA)\s+(?:account|custodial)', EntityType.CHILD),
    ]
    
    entities = []
    
    for footnote in footnotes:
        if not footnote:
            continue
            
        for pattern, entity_type in entity_patterns:
            matches = re.finditer(pattern, footnote, re.IGNORECASE)
            for match in matches:
                entity_name = match.group(1) if match.lastindex and match.lastindex >= 1 else 'Unknown'
                
                entity_ref = EntityReference(
                    entity_id=str(uuid.uuid4()),
                    raw_text=match.group(0),
                    entity_name=entity_name.strip(),
                    entity_type=entity_type,
                    transaction_accession=transaction_accession,
                    reporting_person_cik=reporting_person_cik,
                    confidence_score=float(calculate_parse_confidence(match, footnote))
                )
                entities.append(entity_ref)
    
    return entities


def calculate_parse_confidence(match: re.Match, footnote: str) -> Decimal:
    """
    Calculate confidence score for entity extraction.
    
    Higher confidence for:
    - Longer matches (more specific)
    - Explicit action verbs (transferred, gift, held by)
    - Well-formed entity names
    
    Args:
        match: Regex match object
        footnote: Full footnote text
        
    Returns:
        Confidence score from 0.0 to 1.0
    """
    base_score = Decimal('0.5')
    
    # Longer matches are more specific
    if len(match.group(0)) > 20:
        base_score += Decimal('0.2')
    
    # Explicit transfer verbs increase confidence
    if any(kw in footnote.lower() for kw in ['transferred', 'gift', 'held by']):
        base_score += Decimal('0.2')
    
    # Capitalized entity names increase confidence
    if match.group(0)[0].isupper():
        base_score += Decimal('0.1')
    
    return min(base_score, Decimal('1.0'))


def extract_entity_names(footnotes: List[str]) -> List[str]:
    """
    Extract all potential entity names from footnotes.
    
    Useful for quick scanning of footnotes without full parsing.
    
    Args:
        footnotes: List of footnote strings
        
    Returns:
        List of extracted entity names
    """
    entity_names = []
    
    # Simple pattern for capitalized multi-word names
    name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
    
    for footnote in footnotes:
        if not footnote:
            continue
        matches = re.findall(name_pattern, footnote)
        entity_names.extend(matches)
    
    return list(set(entity_names))  # Remove duplicates


def detect_ownership_transfer(footnotes: List[str]) -> bool:
    """
    Detect if footnotes indicate an ownership transfer.
    
    Args:
        footnotes: List of footnote strings
        
    Returns:
        True if transfer language detected
    """
    transfer_keywords = [
        'transferred', 'transfer', 'gift', 'gifted', 'donated',
        'conveyed', 'assigned', 'distributed', 'held by'
    ]
    
    for footnote in footnotes:
        if not footnote:
            continue
        footnote_lower = footnote.lower()
        if any(keyword in footnote_lower for keyword in transfer_keywords):
            return True
    
    return False


def extract_control_indicators(footnotes: List[str]) -> List[str]:
    """
    Extract control-related phrases from footnotes.
    
    Identifies language suggesting retained control or beneficial ownership.
    
    Args:
        footnotes: List of footnote strings
        
    Returns:
        List of control indicator phrases
    """
    control_patterns = [
        r'as\s+trustee',
        r'as\s+general\s+partner',
        r'as\s+managing\s+member',
        r'voting\s+power',
        r'investment\s+control',
        r'discretionary\s+authority',
        r'sole\s+(?:voting|dispositive)\s+power',
        r'shared\s+(?:voting|dispositive)\s+power',
    ]
    
    indicators = []
    
    for footnote in footnotes:
        if not footnote:
            continue
        for pattern in control_patterns:
            matches = re.findall(pattern, footnote, re.IGNORECASE)
            indicators.extend(matches)
    
    return indicators
