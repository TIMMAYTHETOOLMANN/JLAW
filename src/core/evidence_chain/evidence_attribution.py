"""
Evidence Attribution Linker
============================

Links evidence to actors through multiple attribution types for prosecutorial intelligence.

Attribution Types:
- DIRECT_AUTHORSHIP: Signatory on documents
- FIDUCIARY_ROLE: Role-based disclosure obligations
- TRANSACTION_PARTY: Direct participant in transactions
- BENEFICIARY: Financial gain from activities
- DISCLOSURE_OBLIGOR: SOX 302/906 certification duties

Calculates relevance scores (0-1.0) for each actor-evidence link.
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple

from src.detection.actor_extraction_engine import ActorProfile

logger = logging.getLogger(__name__)


class AttributionType(Enum):
    """Types of evidence attribution to actors."""
    DIRECT_AUTHORSHIP = "DIRECT_AUTHORSHIP"  # Signed or certified document
    FIDUCIARY_ROLE = "FIDUCIARY_ROLE"  # Role requires disclosure
    TRANSACTION_PARTY = "TRANSACTION_PARTY"  # Direct transaction participant
    BENEFICIARY = "BENEFICIARY"  # Financial benefit recipient
    DISCLOSURE_OBLIGOR = "DISCLOSURE_OBLIGOR"  # SOX 302/906 certification duty
    INDIRECT = "INDIRECT"  # Mentioned or related but not direct


@dataclass
class EvidenceAttribution:
    """
    Link between an actor and evidence item.
    
    Attributes:
        actor_id: UUID of actor
        evidence_id: Identifier of evidence item
        attribution_type: Type of attribution
        relevance_score: Relevance score (0.0-1.0)
        attribution_date: Date of attribution (e.g., signature date)
        metadata: Additional context
    """
    actor_id: str
    evidence_id: str
    attribution_type: AttributionType
    relevance_score: float  # 0.0 to 1.0
    attribution_date: Optional[date] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "actor_id": self.actor_id,
            "evidence_id": self.evidence_id,
            "attribution_type": self.attribution_type.value,
            "relevance_score": round(self.relevance_score, 3),
            "attribution_date": self.attribution_date.isoformat() if self.attribution_date else None,
            "metadata": self.metadata
        }


class EvidenceAttributionLinker:
    """
    Links evidence items to actors through various attribution mechanisms.
    """
    
    # Signature patterns in SEC filings
    # Note: Using [ ]+ instead of \s+ to avoid matching across lines
    SIGNATURE_PATTERNS = [
        r'/s/\s*([A-Z][a-z]+(?:[ ]+[A-Z][a-z]+)+)',  # /s/ John Smith
        r'Signature:\s*([A-Z][a-z]+(?:[ ]+[A-Z][a-z]+)+)',  # Signature: John Smith
        r'By:\s*/s/\s*([A-Z][a-z]+(?:[ ]+[A-Z][a-z]+)+)',  # By: /s/ John Smith
        r'Signed by:\s*([A-Z][a-z]+(?:[ ]+[A-Z][a-z]+)+)',  # Signed by: John Smith
        r'Pursuant to[^:]+:\s*/s/\s*([A-Z][a-z]+(?:[ ]+[A-Z][a-z]+)+)'  # Pursuant to...: /s/ John Smith
    ]
    
    # SOX certification roles
    SOX_CERTIFICATION_ROLES = {
        'ceo', 'chief executive officer',
        'cfo', 'chief financial officer',
        'principal executive officer',
        'principal financial officer',
        'principal accounting officer'
    }
    
    # Fiduciary roles requiring disclosure
    FIDUCIARY_DISCLOSURE_ROLES = {
        'director', 'board member', 'officer', 'executive',
        'insider', 'reporting owner', 'certifying officer'
    }
    
    def __init__(self):
        """Initialize evidence attribution linker."""
        self.logger = logging.getLogger(__name__)
        self.attributions: List[EvidenceAttribution] = []
    
    def attribute_evidence_to_actors(
        self,
        actors: List[ActorProfile],
        evidence_items: List[Dict[str, Any]],
        node_results: Optional[Dict[str, Any]] = None
    ) -> List[EvidenceAttribution]:
        """
        Create evidence attributions for all actors.
        
        Args:
            actors: List of ActorProfile objects
            evidence_items: List of evidence items with content
            node_results: Node results for additional context
            
        Returns:
            List of EvidenceAttribution objects
        """
        self.logger.info(f"Attributing {len(evidence_items)} evidence items to {len(actors)} actors...")
        
        for evidence_item in evidence_items:
            evidence_id = evidence_item.get('id', evidence_item.get('evidence_id', 'unknown'))
            content = evidence_item.get('content', '')
            evidence_type = evidence_item.get('type', 'document')
            filing_date = self._parse_date(evidence_item.get('filing_date'))
            
            # Extract signatories from content
            signatories = self._extract_signatories(content)
            
            for actor in actors:
                # Try different attribution methods
                attribution = None
                
                # Method 1: Direct authorship (signature)
                if self._is_signatory(actor, signatories):
                    attribution = self._create_attribution(
                        actor,
                        evidence_id,
                        AttributionType.DIRECT_AUTHORSHIP,
                        relevance_score=1.0,  # Highest relevance
                        filing_date=filing_date,
                        metadata={'signature_found': True}
                    )
                
                # Method 2: Fiduciary role
                elif self._has_fiduciary_role(actor):
                    attribution = self._create_attribution(
                        actor,
                        evidence_id,
                        AttributionType.FIDUCIARY_ROLE,
                        relevance_score=0.8,
                        filing_date=filing_date,
                        metadata={'fiduciary_role': True}
                    )
                
                # Method 3: Transaction party
                elif self._is_transaction_party(actor, evidence_item):
                    attribution = self._create_attribution(
                        actor,
                        evidence_id,
                        AttributionType.TRANSACTION_PARTY,
                        relevance_score=0.9,
                        filing_date=filing_date,
                        metadata={'transaction_party': True}
                    )
                
                # Method 4: Beneficiary
                elif self._is_beneficiary(actor, evidence_item):
                    attribution = self._create_attribution(
                        actor,
                        evidence_id,
                        AttributionType.BENEFICIARY,
                        relevance_score=0.85,
                        filing_date=filing_date,
                        metadata={'beneficiary': True}
                    )
                
                # Method 5: Disclosure obligor (SOX)
                elif self._is_disclosure_obligor(actor, evidence_type):
                    attribution = self._create_attribution(
                        actor,
                        evidence_id,
                        AttributionType.DISCLOSURE_OBLIGOR,
                        relevance_score=0.95,
                        filing_date=filing_date,
                        metadata={'sox_obligation': True}
                    )
                
                # Method 6: Indirect (mentioned in document)
                elif self._is_mentioned(actor, content):
                    attribution = self._create_attribution(
                        actor,
                        evidence_id,
                        AttributionType.INDIRECT,
                        relevance_score=0.5,
                        filing_date=filing_date,
                        metadata={'mentioned': True}
                    )
                
                if attribution:
                    self.attributions.append(attribution)
        
        self.logger.info(f"Created {len(self.attributions)} evidence attributions")
        return self.attributions
    
    def _extract_signatories(self, content: str) -> List[str]:
        """
        Extract signatory names from document content.
        
        Uses regex patterns to find /s/ signatures and other signature blocks.
        """
        signatories = []
        
        for pattern in self.SIGNATURE_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if name and len(name) > 3:  # Filter out false positives
                    signatories.append(name)
        
        return signatories
    
    def _is_signatory(self, actor: ActorProfile, signatories: List[str]) -> bool:
        """Check if actor's name appears in signatory list."""
        actor_name_lower = actor.name.lower()
        
        for signatory in signatories:
            signatory_lower = signatory.lower()
            
            # Exact match
            if actor_name_lower == signatory_lower:
                return True
            
            # Partial match (last name and first initial)
            actor_parts = actor_name_lower.split()
            signatory_parts = signatory_lower.split()
            
            if len(actor_parts) >= 2 and len(signatory_parts) >= 2:
                # Match last name
                if actor_parts[-1] == signatory_parts[-1]:
                    # Match first initial
                    if actor_parts[0][0] == signatory_parts[0][0]:
                        return True
        
        return False
    
    def _has_fiduciary_role(self, actor: ActorProfile) -> bool:
        """Check if actor has fiduciary role requiring disclosure."""
        roles_lower = [role.lower() for role in actor.roles]
        
        for role in roles_lower:
            for fiduciary_role in self.FIDUCIARY_DISCLOSURE_ROLES:
                if fiduciary_role in role:
                    return True
        
        return False
    
    def _is_transaction_party(self, actor: ActorProfile, evidence_item: Dict[str, Any]) -> bool:
        """Check if actor is direct transaction party."""
        # Check evidence metadata for transaction information
        metadata = evidence_item.get('metadata', {})
        
        # Form 4 transactions
        if evidence_item.get('type') == 'form4' or 'form4' in evidence_item.get('id', ''):
            reporting_owner = metadata.get('reporting_owner', metadata.get('owner_name', ''))
            if reporting_owner and reporting_owner.lower() == actor.name.lower():
                return True
        
        # Check if actor's name appears in transaction fields
        transaction_fields = ['reporting_owner', 'owner_name', 'participant', 'party']
        for field in transaction_fields:
            if field in metadata:
                value = metadata[field]
                if isinstance(value, str) and value.lower() == actor.name.lower():
                    return True
        
        return False
    
    def _is_beneficiary(self, actor: ActorProfile, evidence_item: Dict[str, Any]) -> bool:
        """Check if actor is financial beneficiary."""
        metadata = evidence_item.get('metadata', {})
        
        # Check for compensation or financial benefit
        beneficiary_fields = ['beneficiary', 'recipient', 'executive']
        for field in beneficiary_fields:
            if field in metadata:
                value = metadata[field]
                if isinstance(value, str) and value.lower() == actor.name.lower():
                    return True
        
        # Check if actor received compensation
        if actor.metadata.get('total_compensation', 0) > 0:
            # DEF 14A compensation evidence
            if 'def14a' in evidence_item.get('id', '').lower():
                return True
        
        return False
    
    def _is_disclosure_obligor(self, actor: ActorProfile, evidence_type: str) -> bool:
        """Check if actor has SOX 302/906 certification obligation."""
        roles_lower = [role.lower() for role in actor.roles]
        
        # SOX certifications required for CEO/CFO
        for role in roles_lower:
            for sox_role in self.SOX_CERTIFICATION_ROLES:
                if sox_role in role:
                    # Check if evidence is 10-K or 10-Q (SOX certifications)
                    if '10-k' in evidence_type.lower() or '10-q' in evidence_type.lower():
                        return True
        
        return False
    
    def _is_mentioned(self, actor: ActorProfile, content: str) -> bool:
        """Check if actor's name is mentioned in content."""
        if not content:
            return False
        
        content_lower = content.lower()
        actor_name_lower = actor.name.lower()
        
        # Simple substring search
        if actor_name_lower in content_lower:
            return True
        
        # Check last name only (if multi-part name)
        name_parts = actor_name_lower.split()
        if len(name_parts) >= 2:
            last_name = name_parts[-1]
            if len(last_name) > 3 and last_name in content_lower:
                return True
        
        return False
    
    def _create_attribution(
        self,
        actor: ActorProfile,
        evidence_id: str,
        attribution_type: AttributionType,
        relevance_score: float,
        filing_date: Optional[date] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceAttribution:
        """Create evidence attribution object."""
        return EvidenceAttribution(
            actor_id=actor.actor_id,
            evidence_id=evidence_id,
            attribution_type=attribution_type,
            relevance_score=relevance_score,
            attribution_date=filing_date,
            metadata=metadata or {}
        )
    
    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if not date_value:
            return None
        
        if isinstance(date_value, date):
            return date_value
        
        from datetime import datetime
        if isinstance(date_value, datetime):
            return date_value.date()
        
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
            except Exception as e:
                logger.debug(f"ISO date parsing failed for '{date_value}': {e}")
                try:
                    from dateutil import parser
                    return parser.parse(date_value).date()
                except Exception as e2:
                    logger.debug(f"Dateutil parsing also failed for '{date_value}': {e2}")
                    return None
        
        return None
    
    def get_attributions_for_actor(self, actor_id: str) -> List[EvidenceAttribution]:
        """Get all evidence attributions for specific actor."""
        return [attr for attr in self.attributions if attr.actor_id == actor_id]
    
    def get_attributions_for_evidence(self, evidence_id: str) -> List[EvidenceAttribution]:
        """Get all actor attributions for specific evidence."""
        return [attr for attr in self.attributions if attr.evidence_id == evidence_id]
    
    def get_high_relevance_attributions(
        self,
        min_relevance: float = 0.8
    ) -> List[EvidenceAttribution]:
        """Get attributions with high relevance scores."""
        return [
            attr for attr in self.attributions 
            if attr.relevance_score >= min_relevance
        ]
    
    def get_attributions_by_type(
        self,
        attribution_type: AttributionType
    ) -> List[EvidenceAttribution]:
        """Get all attributions of specific type."""
        return [
            attr for attr in self.attributions 
            if attr.attribution_type == attribution_type
        ]
    
    def calculate_actor_evidence_strength(self, actor_id: str) -> float:
        """
        Calculate overall evidence strength for an actor.
        
        Returns weighted average of relevance scores.
        """
        actor_attributions = self.get_attributions_for_actor(actor_id)
        
        if not actor_attributions:
            return 0.0
        
        # Weight by attribution type
        type_weights = {
            AttributionType.DIRECT_AUTHORSHIP: 1.0,
            AttributionType.DISCLOSURE_OBLIGOR: 0.95,
            AttributionType.TRANSACTION_PARTY: 0.9,
            AttributionType.BENEFICIARY: 0.85,
            AttributionType.FIDUCIARY_ROLE: 0.8,
            AttributionType.INDIRECT: 0.5
        }
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for attr in actor_attributions:
            weight = type_weights.get(attr.attribution_type, 0.5)
            total_weighted_score += attr.relevance_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return total_weighted_score / total_weight
