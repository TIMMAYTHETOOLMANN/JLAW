"""
Beneficial Ownership Chain Resolution Module
=============================================

Traces zero-dollar transaction destinations to identify beneficial ownership
retention through controlled entities.

Per Section 7 of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Reference:
    - Section 7: Beneficial Ownership Chain Resolution Module
    - Section 7.1: Module Objective
    - Section 7.4: Beneficial Ownership Chain Construction
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.zero_dollar.models import (
    Transaction,
    ReportingPerson,
    EntityReference,
    EntityType,
)
from .footnote_parser import parse_ownership_footnotes
from .control_assessment import assess_control_indicators, ControlAssessment
from .entity_classifier import get_control_presumption

logger = logging.getLogger(__name__)


@dataclass
class OwnershipNode:
    """
    Node in beneficial ownership chain.
    
    Represents a single entity or transfer in the ownership structure.
    
    Attributes:
        node_id: Unique node identifier
        entity: EntityReference for this node
        transaction_id: Source transaction accession number
        shares_transferred: Number of shares transferred to this entity
        schedule_13_reference: Optional Schedule 13D/G accession number
        control_indicators: Control assessment for this entity
        economic_interest_retained: Estimated economic interest (0-1)
    """
    node_id: str
    entity: EntityReference
    transaction_id: str
    shares_transferred: Decimal
    schedule_13_reference: Optional[str]
    control_indicators: ControlAssessment
    economic_interest_retained: Decimal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'node_id': self.node_id,
            'entity': self.entity.to_dict(),
            'transaction_id': self.transaction_id,
            'shares_transferred': str(self.shares_transferred),
            'schedule_13_reference': self.schedule_13_reference,
            'control_indicators': self.control_indicators.to_dict(),
            'economic_interest_retained': str(self.economic_interest_retained),
        }


@dataclass
class OwnershipChain:
    """
    Complete beneficial ownership chain from reporting person to entities.
    
    Attributes:
        chain_id: Unique chain identifier
        root_cik: Reporting person CIK (root of chain)
        root_name: Reporting person name
        nodes: List of ownership nodes
        evidence_hash: SHA-256 hash for evidence integrity
        construction_timestamp: When chain was constructed
    """
    root_cik: str
    root_name: str
    nodes: List[OwnershipNode] = field(default_factory=list)
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    evidence_hash: Optional[str] = None
    construction_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def add_node(self, node: OwnershipNode):
        """Add a node to the ownership chain."""
        self.nodes.append(node)
    
    @property
    def total_shares_transferred(self) -> Decimal:
        """Total shares transferred across all nodes."""
        return sum(node.shares_transferred for node in self.nodes)
    
    @property
    def average_control_probability(self) -> Decimal:
        """Average control retention probability across nodes."""
        if not self.nodes:
            return Decimal('0')
        probabilities = [
            node.control_indicators.overall_control_probability
            for node in self.nodes
        ]
        return sum(probabilities) / len(probabilities)
    
    @property
    def high_control_node_count(self) -> int:
        """Count of nodes with high control probability (>0.6)."""
        return sum(
            1 for node in self.nodes
            if node.control_indicators.overall_control_probability > Decimal('0.6')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'chain_id': self.chain_id,
            'root_cik': self.root_cik,
            'root_name': self.root_name,
            'node_count': len(self.nodes),
            'nodes': [node.to_dict() for node in self.nodes],
            'total_shares_transferred': str(self.total_shares_transferred),
            'average_control_probability': str(self.average_control_probability),
            'high_control_node_count': self.high_control_node_count,
            'evidence_hash': self.evidence_hash,
            'construction_timestamp': self.construction_timestamp.isoformat(),
        }


class BeneficialOwnershipModule:
    """
    Beneficial Ownership Chain Resolution Module.
    
    Traces zero-dollar transaction destinations to identify beneficial
    ownership retention through controlled entities.
    
    Per Section 7 of JLAW Zero-Dollar Transaction Forensic Specification.
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the module.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    async def analyze(
        self,
        transactions: List[Transaction],
        reporting_person: Optional[ReportingPerson] = None,
        schedule_13_filings: Optional[List[object]] = None
    ) -> OwnershipChain:
        """
        Analyze transactions to build ownership chain.
        
        Args:
            transactions: List of Transaction objects
            reporting_person: Optional ReportingPerson object
            schedule_13_filings: Optional list of Schedule 13D/G filings
            
        Returns:
            OwnershipChain object
        """
        if not transactions:
            self.logger.warning("No transactions provided for analysis")
            return OwnershipChain(root_cik="", root_name="")
        
        # Extract reporting person from first transaction if not provided
        if not reporting_person:
            first_txn = transactions[0]
            reporting_person = ReportingPerson(
                cik=first_txn.reporting_person_cik,
                name=first_txn.reporting_person_name,
                classification=None  # Will be determined elsewhere
            )
        
        # Build ownership chain
        chain = self.construct_ownership_chain(
            reporting_person=reporting_person,
            transactions=transactions,
            schedule_13_filings=schedule_13_filings or []
        )
        
        # Compute evidence hash
        chain.evidence_hash = self.compute_chain_hash(chain)
        
        self.logger.info(
            f"Constructed ownership chain {chain.chain_id} with {len(chain.nodes)} nodes"
        )
        
        return chain
    
    def construct_ownership_chain(
        self,
        reporting_person: ReportingPerson,
        transactions: List[Transaction],
        schedule_13_filings: List[object]
    ) -> OwnershipChain:
        """
        Build ownership chain from reporting person through controlled entities.
        
        Data Sources:
            1. Form 4 footnotes (parsed)
            2. Schedule 13D/13G beneficial ownership disclosures
            3. SEC EDGAR entity search (CIK matching)
            4. State corporate/LLC registries (where accessible)
        
        Args:
            reporting_person: ReportingPerson object
            transactions: List of Transaction objects
            schedule_13_filings: List of Schedule 13D/G filings
            
        Returns:
            OwnershipChain with all nodes
        """
        chain = OwnershipChain(
            root_cik=reporting_person.cik,
            root_name=reporting_person.name
        )
        
        # Process each zero-dollar transfer
        for txn in transactions:
            if not txn.is_zero_dollar:
                continue
            
            # Parse footnotes to extract entity references
            entities = parse_ownership_footnotes(
                footnotes=txn.footnotes,
                reporting_person_cik=txn.reporting_person_cik,
                transaction_accession=txn.accession_number
            )
            
            for entity in entities:
                # Attempt to link entity to Schedule 13 filings
                matched_filing = self.match_entity_to_schedule13(
                    entity, schedule_13_filings
                )
                
                # Assess control indicators
                control_assessment = assess_control_indicators(
                    entity=entity,
                    schedule_13=matched_filing
                )
                
                # Estimate economic interest retention
                economic_retention = self.estimate_economic_retention(entity)
                
                # Create ownership node
                node = OwnershipNode(
                    node_id=str(uuid.uuid4()),
                    entity=entity,
                    transaction_id=txn.accession_number,
                    shares_transferred=txn.shares,
                    schedule_13_reference=matched_filing.accession_number if matched_filing and hasattr(matched_filing, 'accession_number') else None,
                    control_indicators=control_assessment,
                    economic_interest_retained=economic_retention
                )
                
                chain.add_node(node)
                
                self.logger.debug(
                    f"Added node {node.node_id} for entity {entity.entity_name} "
                    f"(type: {entity.entity_type.value}, control: {control_assessment.overall_control_probability})"
                )
        
        return chain
    
    def match_entity_to_schedule13(
        self,
        entity: EntityReference,
        filings: List[object]
    ) -> Optional[object]:
        """
        Match parsed entity to Schedule 13D/G filings.
        
        Performs fuzzy name matching to link entities from footnotes
        to formal Schedule 13 filings.
        
        Args:
            entity: EntityReference to match
            filings: List of Schedule 13D/G filing objects
            
        Returns:
            Matched filing object or None
        """
        for filing in filings:
            if hasattr(filing, 'filer_name'):
                if self.entity_name_match(entity.entity_name, filing.filer_name):
                    return filing
            elif hasattr(filing, 'reporting_person_name'):
                if self.entity_name_match(entity.entity_name, filing.reporting_person_name):
                    return filing
        
        return None
    
    def entity_name_match(self, name1: str, name2: str) -> bool:
        """
        Fuzzy match entity names.
        
        Handles variations in capitalization, punctuation, and word order.
        
        Args:
            name1: First entity name
            name2: Second entity name
            
        Returns:
            True if names match
        """
        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Remove common punctuation
        for char in ['.', ',', '-', '_']:
            n1 = n1.replace(char, ' ')
            n2 = n2.replace(char, ' ')
        
        # Exact match
        if n1 == n2:
            return True
        
        # Substring match
        if n1 in n2 or n2 in n1:
            return True
        
        # Word overlap (at least 2 common words)
        words1 = set(n1.split())
        words2 = set(n2.split())
        common_words = words1.intersection(words2)
        
        if len(common_words) >= 2:
            return True
        
        return False
    
    def estimate_economic_retention(self, entity: EntityReference) -> Decimal:
        """
        Estimate economic interest retained based on entity type.
        
        Uses entity type taxonomy to estimate likely economic interest
        retained by the reporting person after transfer.
        
        Args:
            entity: EntityReference object
            
        Returns:
            Decimal from 0.0 to 1.0 representing estimated retention
        """
        retention_map = {
            EntityType.RLT: Decimal('1.0'),    # Full retention - revocable
            EntityType.IRT: Decimal('0.5'),    # Partial - depends on terms
            EntityType.GRAT: Decimal('0.75'),  # Annuity retained during term
            EntityType.FLP: Decimal('0.80'),   # GP interest retained
            EntityType.LLC: Decimal('0.70'),   # Manager interest retained
            EntityType.DAF: Decimal('0.10'),   # Advisory only, no legal ownership
            EntityType.PF: Decimal('0.30'),    # Board control but no ownership
            EntityType.CRT: Decimal('0.50'),   # Income interest for life
            EntityType.SPOUSE: Decimal('1.0'), # Full aggregation under Section 16
            EntityType.CHILD: Decimal('0.80'), # Parental control until majority
        }
        
        return retention_map.get(entity.entity_type, Decimal('0.25'))
    
    def compute_chain_hash(self, chain: OwnershipChain) -> str:
        """
        Compute SHA-256 hash of ownership chain for evidence integrity.
        
        Hash includes:
        - Root CIK and name
        - All node entity names and types
        - Transaction IDs
        - Shares transferred
        
        Args:
            chain: OwnershipChain object
            
        Returns:
            SHA-256 hash as hex string
        """
        hash_components = [
            chain.root_cik,
            chain.root_name,
        ]
        
        for node in chain.nodes:
            hash_components.extend([
                node.entity.entity_name,
                node.entity.entity_type.value,
                node.transaction_id,
                str(node.shares_transferred),
            ])
        
        # Join and hash
        hash_input = '|'.join(hash_components).encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()


# Convenience function for direct use
def construct_ownership_chain(
    reporting_person: ReportingPerson,
    transactions: List[Transaction],
    schedule_13_filings: Optional[List[object]] = None
) -> OwnershipChain:
    """
    Construct ownership chain (convenience function).
    
    Args:
        reporting_person: ReportingPerson object
        transactions: List of Transaction objects
        schedule_13_filings: Optional list of Schedule 13D/G filings
        
    Returns:
        OwnershipChain object
    """
    module = BeneficialOwnershipModule()
    return module.construct_ownership_chain(
        reporting_person=reporting_person,
        transactions=transactions,
        schedule_13_filings=schedule_13_filings or []
    )
