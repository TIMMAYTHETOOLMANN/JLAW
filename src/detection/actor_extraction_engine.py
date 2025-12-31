"""
Actor Extraction Engine
========================

Extracts actors (individuals/entities) from SEC filings and pattern detection results.

This module identifies and profiles actors involved in potential violations by parsing:
- Node 1 (Form 4): Insider trading actors and reporting owners
- Node 2 (DEF 14A): Board members, executives, compensation committee
- Node 5 (8-K): Material event participants
- Node 7 (13F): Institutional holders
- Node 10 (10-K/Q): CFO/CEO signatories
- 23 Pattern Detection Results

Implements fuzzy name matching and CIK alignment for deduplication.
"""

import uuid
import re
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class ActorProfile:
    """
    Comprehensive actor profile for prosecutorial intelligence.
    
    Attributes:
        actor_id: Unique identifier (UUID)
        name: Full name of actor
        actor_type: INDIVIDUAL or ENTITY
        roles: List of roles held (e.g., "CEO", "Director", "Institutional Holder")
        cik: SEC CIK number if available
        first_appearance: First date actor appears in evidence
        last_appearance: Last date actor appears in evidence
        evidence_items: List of evidence document IDs
        violations: List of violation identifiers attributed to actor
        risk_score: Risk score (0-100) based on involvement
        metadata: Additional information (positions, compensation, etc.)
    """
    actor_id: str
    name: str
    actor_type: str  # "INDIVIDUAL" or "ENTITY"
    roles: List[str] = field(default_factory=list)
    cik: Optional[str] = None
    first_appearance: Optional[date] = None
    last_appearance: Optional[date] = None
    evidence_items: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "actor_id": self.actor_id,
            "name": self.name,
            "actor_type": self.actor_type,
            "roles": self.roles,
            "cik": self.cik,
            "first_appearance": self.first_appearance.isoformat() if self.first_appearance else None,
            "last_appearance": self.last_appearance.isoformat() if self.last_appearance else None,
            "evidence_items": self.evidence_items,
            "violations": self.violations,
            "risk_score": self.risk_score,
            "metadata": self.metadata
        }
    
    def merge(self, other: 'ActorProfile') -> None:
        """
        Merge another actor profile into this one.
        
        Used for deduplication when multiple profiles refer to same actor.
        """
        # Merge roles (unique)
        self.roles = list(set(self.roles + other.roles))
        
        # Merge evidence items (unique)
        self.evidence_items = list(set(self.evidence_items + other.evidence_items))
        
        # Merge violations (unique)
        self.violations = list(set(self.violations + other.violations))
        
        # Update dates
        if other.first_appearance:
            if not self.first_appearance or other.first_appearance < self.first_appearance:
                self.first_appearance = other.first_appearance
        
        if other.last_appearance:
            if not self.last_appearance or other.last_appearance > self.last_appearance:
                self.last_appearance = other.last_appearance
        
        # Prefer non-null CIK
        if not self.cik and other.cik:
            self.cik = other.cik
        
        # Merge metadata
        self.metadata.update(other.metadata)
        
        # Take maximum risk score
        self.risk_score = max(self.risk_score, other.risk_score)


class ActorExtractionEngine:
    """
    Extracts and deduplicates actors from SEC filings and pattern detection results.
    """
    
    def __init__(self):
        """Initialize actor extraction engine."""
        self.logger = logging.getLogger(__name__)
        self.actors: Dict[str, ActorProfile] = {}  # actor_id -> ActorProfile
        self.name_to_actor_id: Dict[str, str] = {}  # normalized_name -> actor_id
    
    def extract_actors_from_nodes(
        self,
        node_results: Dict[str, Any]
    ) -> List[ActorProfile]:
        """
        Extract actors from all node results.
        
        Args:
            node_results: Dictionary of node results from Phase 4
            
        Returns:
            List of extracted ActorProfile objects
        """
        self.logger.info("Extracting actors from node results...")
        
        # Extract from each node type
        for node_id, node_result in node_results.items():
            if hasattr(node_result, 'findings'):
                findings = node_result.findings
            else:
                findings = node_result
            
            # Node 1: Form 4 Insider Trading
            if node_id.lower() in ['node1', '1', 'form4']:
                self._extract_from_node1_form4(findings)
            
            # Node 2: DEF 14A Compensation
            elif node_id.lower() in ['node2', '2', 'def14a']:
                self._extract_from_node2_def14a(findings)
            
            # Node 5: IRC Tax Exposure (contains 8-K data)
            elif node_id.lower() in ['node5', '5', 'irc_tax']:
                self._extract_from_node5_8k(findings)
            
            # Node 7: 13F Institutional Holdings
            elif node_id.lower() in ['node7', '7', '13f']:
                self._extract_from_node7_13f(findings)
            
            # Node 10: Form 144 or 10-K/Q signatories
            elif node_id.lower() in ['node10', '10', 'form144']:
                self._extract_from_node10_signatories(findings)
        
        self.logger.info(f"Extracted {len(self.actors)} unique actors from nodes")
        return list(self.actors.values())
    
    def extract_actors_from_patterns(
        self,
        pattern_results: Dict[str, Any]
    ) -> List[ActorProfile]:
        """
        Extract actors from pattern detection results.
        
        Args:
            pattern_results: Pattern detection results from Phase 5
            
        Returns:
            List of extracted ActorProfile objects
        """
        self.logger.info("Extracting actors from pattern detection results...")
        
        # Pattern results may contain actor names in various fields
        if isinstance(pattern_results, dict):
            for pattern_name, pattern_data in pattern_results.items():
                if isinstance(pattern_data, dict):
                    # Look for actors in findings
                    if 'findings' in pattern_data:
                        self._extract_actors_from_findings(pattern_data['findings'], pattern_name)
                    
                    # Look for actors in violations
                    if 'violations' in pattern_data:
                        self._extract_actors_from_violations(pattern_data['violations'], pattern_name)
        
        self.logger.info(f"Total unique actors after pattern extraction: {len(self.actors)}")
        return list(self.actors.values())
    
    def _extract_from_node1_form4(self, findings: Dict[str, Any]) -> None:
        """Extract actors from Node 1 (Form 4) findings."""
        try:
            # Form 4 contains reporting owners and transaction parties
            if isinstance(findings, dict):
                # Check for transactions
                transactions = findings.get('transactions', [])
                if isinstance(transactions, list):
                    for txn in transactions:
                        if isinstance(txn, dict):
                            reporting_owner = txn.get('reporting_owner', txn.get('owner_name'))
                            if reporting_owner:
                                self._add_or_update_actor(
                                    name=reporting_owner,
                                    actor_type="INDIVIDUAL",
                                    roles=["Insider", "Reporting Owner"],
                                    transaction_date=self._parse_date(txn.get('transaction_date')),
                                    evidence_id=f"form4_{txn.get('accession_number', 'unknown')}",
                                    metadata={
                                        'transaction_code': txn.get('transaction_code'),
                                        'shares': txn.get('shares', 0),
                                        'price': txn.get('price_per_share', 0)
                                    }
                                )
                
                # Check for violations
                violations = findings.get('violations', [])
                if isinstance(violations, list):
                    for violation in violations:
                        if isinstance(violation, dict):
                            owner = violation.get('reporting_owner', violation.get('owner_name'))
                            if owner:
                                actor = self._add_or_update_actor(
                                    name=owner,
                                    actor_type="INDIVIDUAL",
                                    roles=["Insider", "Violation Subject"],
                                    transaction_date=self._parse_date(violation.get('transaction_date')),
                                    evidence_id=f"form4_violation_{violation.get('violation_type', 'unknown')}"
                                )
                                # Track violation
                                if actor:
                                    violation_id = f"node1_{violation.get('violation_type', 'unknown')}"
                                    if violation_id not in actor.violations:
                                        actor.violations.append(violation_id)
        except Exception as e:
            self.logger.warning(f"Error extracting actors from Node 1: {e}")
    
    def _extract_from_node2_def14a(self, findings: Dict[str, Any]) -> None:
        """Extract actors from Node 2 (DEF 14A) findings."""
        try:
            if isinstance(findings, dict):
                # Executive officers
                executives = findings.get('executives', findings.get('executive_officers', []))
                if isinstance(executives, list):
                    for exec_data in executives:
                        if isinstance(exec_data, dict):
                            name = exec_data.get('name', exec_data.get('officer_name'))
                            if name:
                                self._add_or_update_actor(
                                    name=name,
                                    actor_type="INDIVIDUAL",
                                    roles=["Executive", exec_data.get('position', 'Officer')],
                                    evidence_id=f"def14a_{exec_data.get('accession_number', 'unknown')}",
                                    metadata={
                                        'total_compensation': exec_data.get('total_compensation', 0),
                                        'salary': exec_data.get('salary', 0),
                                        'bonus': exec_data.get('bonus', 0),
                                        'stock_awards': exec_data.get('stock_awards', 0)
                                    }
                                )
                
                # Board members
                board_members = findings.get('board_members', findings.get('directors', []))
                if isinstance(board_members, list):
                    for member in board_members:
                        if isinstance(member, dict):
                            name = member.get('name')
                            if name:
                                self._add_or_update_actor(
                                    name=name,
                                    actor_type="INDIVIDUAL",
                                    roles=["Director", "Board Member"],
                                    evidence_id=f"def14a_board_{member.get('accession_number', 'unknown')}",
                                    metadata={
                                        'committee_memberships': member.get('committees', []),
                                        'compensation': member.get('compensation', 0)
                                    }
                                )
                
                # Compensation committee
                comp_committee = findings.get('compensation_committee', [])
                if isinstance(comp_committee, list):
                    for member in comp_committee:
                        name = member if isinstance(member, str) else member.get('name')
                        if name:
                            actor = self._add_or_update_actor(
                                name=name,
                                actor_type="INDIVIDUAL",
                                roles=["Compensation Committee Member"],
                                evidence_id="def14a_comp_committee"
                            )
                            if actor and "Compensation Committee Member" not in actor.roles:
                                actor.roles.append("Compensation Committee Member")
        except Exception as e:
            self.logger.warning(f"Error extracting actors from Node 2: {e}")
    
    def _extract_from_node5_8k(self, findings: Dict[str, Any]) -> None:
        """Extract actors from Node 5 (8-K Material Events) findings."""
        try:
            if isinstance(findings, dict):
                # Material events may mention executives or involved parties
                events = findings.get('events', findings.get('material_events', []))
                if isinstance(events, list):
                    for event in events:
                        if isinstance(event, dict):
                            # Look for names in various fields
                            participants = event.get('participants', [])
                            if isinstance(participants, list):
                                for participant in participants:
                                    name = participant if isinstance(participant, str) else participant.get('name')
                                    if name:
                                        self._add_or_update_actor(
                                            name=name,
                                            actor_type="INDIVIDUAL",
                                            roles=["Material Event Participant"],
                                            transaction_date=self._parse_date(event.get('event_date')),
                                            evidence_id=f"8k_{event.get('item_number', 'unknown')}"
                                        )
        except Exception as e:
            self.logger.warning(f"Error extracting actors from Node 5: {e}")
    
    def _extract_from_node7_13f(self, findings: Dict[str, Any]) -> None:
        """Extract actors from Node 7 (13F Institutional Holdings) findings."""
        try:
            if isinstance(findings, dict):
                # Institutional holders
                holders = findings.get('holders', findings.get('institutional_holders', []))
                if isinstance(holders, list):
                    for holder in holders:
                        if isinstance(holder, dict):
                            name = holder.get('name', holder.get('holder_name'))
                            if name:
                                self._add_or_update_actor(
                                    name=name,
                                    actor_type="ENTITY",
                                    roles=["Institutional Holder"],
                                    evidence_id=f"13f_{holder.get('cik', 'unknown')}",
                                    cik=holder.get('cik'),
                                    metadata={
                                        'shares_held': holder.get('shares', 0),
                                        'value': holder.get('value', 0),
                                        'percentage': holder.get('percentage', 0)
                                    }
                                )
        except Exception as e:
            self.logger.warning(f"Error extracting actors from Node 7: {e}")
    
    def _extract_from_node10_signatories(self, findings: Dict[str, Any]) -> None:
        """Extract actors from Node 10 (10-K/Q signatories) findings."""
        try:
            if isinstance(findings, dict):
                # SOX certifications and signatories
                signatories = findings.get('signatories', findings.get('certifying_officers', []))
                if isinstance(signatories, list):
                    for signatory in signatories:
                        if isinstance(signatory, dict):
                            name = signatory.get('name', signatory.get('officer_name'))
                            if name:
                                self._add_or_update_actor(
                                    name=name,
                                    actor_type="INDIVIDUAL",
                                    roles=["Certifying Officer", signatory.get('title', 'Officer')],
                                    evidence_id=f"10k_signatory_{signatory.get('accession_number', 'unknown')}",
                                    metadata={
                                        'certification_type': signatory.get('certification_type', 'SOX'),
                                        'filing_date': signatory.get('filing_date')
                                    }
                                )
        except Exception as e:
            self.logger.warning(f"Error extracting actors from Node 10: {e}")
    
    def _extract_actors_from_findings(self, findings: Any, pattern_name: str) -> None:
        """Extract actors from pattern findings."""
        try:
            if isinstance(findings, list):
                for finding in findings:
                    if isinstance(finding, dict):
                        # Look for actor names in common fields
                        for field in ['actor', 'executive', 'officer', 'participant', 'name']:
                            if field in finding:
                                name = finding[field]
                                if name and isinstance(name, str):
                                    self._add_or_update_actor(
                                        name=name,
                                        actor_type="INDIVIDUAL",
                                        roles=["Pattern Detection Subject"],
                                        evidence_id=f"pattern_{pattern_name}",
                                        metadata={'pattern': pattern_name}
                                    )
        except Exception as e:
            self.logger.warning(f"Error extracting actors from findings: {e}")
    
    def _extract_actors_from_violations(self, violations: Any, pattern_name: str) -> None:
        """Extract actors from pattern violations."""
        try:
            if isinstance(violations, list):
                for violation in violations:
                    if isinstance(violation, dict):
                        # Look for actor names
                        for field in ['actor', 'subject', 'responsible_party', 'name']:
                            if field in violation:
                                name = violation[field]
                                if name and isinstance(name, str):
                                    actor = self._add_or_update_actor(
                                        name=name,
                                        actor_type="INDIVIDUAL",
                                        roles=["Violation Subject"],
                                        evidence_id=f"pattern_violation_{pattern_name}"
                                    )
                                    if actor:
                                        violation_id = f"pattern_{pattern_name}"
                                        if violation_id not in actor.violations:
                                            actor.violations.append(violation_id)
        except Exception as e:
            self.logger.warning(f"Error extracting actors from violations: {e}")
    
    def _add_or_update_actor(
        self,
        name: str,
        actor_type: str,
        roles: List[str],
        evidence_id: Optional[str] = None,
        transaction_date: Optional[date] = None,
        cik: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ActorProfile]:
        """
        Add or update an actor profile with deduplication.
        
        Uses fuzzy name matching to identify duplicates.
        """
        # Normalize name
        normalized_name = self._normalize_name(name)
        
        # Check for existing actor
        existing_actor_id = self._find_matching_actor(normalized_name, cik)
        
        if existing_actor_id:
            # Update existing actor
            actor = self.actors[existing_actor_id]
            
            # Add new roles (unique)
            for role in roles:
                if role not in actor.roles:
                    actor.roles.append(role)
            
            # Add evidence
            if evidence_id and evidence_id not in actor.evidence_items:
                actor.evidence_items.append(evidence_id)
            
            # Update dates
            if transaction_date:
                if not actor.first_appearance or transaction_date < actor.first_appearance:
                    actor.first_appearance = transaction_date
                if not actor.last_appearance or transaction_date > actor.last_appearance:
                    actor.last_appearance = transaction_date
            
            # Update CIK if not set
            if cik and not actor.cik:
                actor.cik = cik
            
            # Update metadata
            if metadata:
                actor.metadata.update(metadata)
            
            return actor
        else:
            # Create new actor
            actor = ActorProfile(
                actor_id=str(uuid.uuid4()),
                name=name,
                actor_type=actor_type,
                roles=roles.copy(),
                cik=cik,
                first_appearance=transaction_date,
                last_appearance=transaction_date,
                evidence_items=[evidence_id] if evidence_id else [],
                violations=[],
                risk_score=0.0,
                metadata=metadata or {}
            )
            
            self.actors[actor.actor_id] = actor
            self.name_to_actor_id[normalized_name] = actor.actor_id
            
            return actor
    
    def _find_matching_actor(self, normalized_name: str, cik: Optional[str] = None) -> Optional[str]:
        """
        Find matching actor using fuzzy name matching and CIK alignment.
        
        Returns actor_id if match found, None otherwise.
        """
        # Exact match on normalized name
        if normalized_name in self.name_to_actor_id:
            return self.name_to_actor_id[normalized_name]
        
        # CIK match (highest priority)
        if cik:
            for actor_id, actor in self.actors.items():
                if actor.cik == cik:
                    # Update name mapping
                    self.name_to_actor_id[normalized_name] = actor_id
                    return actor_id
        
        # Fuzzy name matching (similarity > 0.85)
        for existing_name, actor_id in self.name_to_actor_id.items():
            similarity = SequenceMatcher(None, normalized_name, existing_name).ratio()
            if similarity > 0.85:
                # Found fuzzy match
                self.logger.debug(f"Fuzzy match: '{normalized_name}' -> '{existing_name}' (similarity: {similarity:.2f})")
                # Update mapping
                self.name_to_actor_id[normalized_name] = actor_id
                return actor_id
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize actor name for comparison.
        
        Removes titles, extra whitespace, and standardizes format.
        """
        # Remove common titles
        titles = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'jr.', 'sr.', 'ii', 'iii', 'iv']
        name_lower = name.lower().strip()
        
        for title in titles:
            name_lower = name_lower.replace(title, '')
        
        # Remove punctuation
        name_lower = name_lower.replace(',', '').replace('.', '')
        
        # Remove extra whitespace
        name_normalized = ' '.join(name_lower.split())
        
        return name_normalized
    
    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if not date_value:
            return None
        
        if isinstance(date_value, date):
            return date_value
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        if isinstance(date_value, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(date_value.replace('Z', '+00:00')).date()
            except:
                try:
                    # Try common date formats
                    from dateutil import parser
                    return parser.parse(date_value).date()
                except:
                    self.logger.debug(f"Could not parse date: {date_value}")
                    return None
        
        return None
    
    def get_all_actors(self) -> List[ActorProfile]:
        """Get all extracted actors."""
        return list(self.actors.values())
    
    def get_actor_by_id(self, actor_id: str) -> Optional[ActorProfile]:
        """Get actor by ID."""
        return self.actors.get(actor_id)
    
    def get_actors_by_role(self, role: str) -> List[ActorProfile]:
        """Get all actors with specific role."""
        return [actor for actor in self.actors.values() if role in actor.roles]
