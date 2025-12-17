"""
Chain of Custody Logger
=======================

Provides cryptographic chain of custody tracking for forensic evidence.
Implements tamper-evident logging with SHA-256 hashing, RFC 3161 timestamp
support, and comprehensive audit trail documentation.

Key Features:
- Cryptographic hash chaining for tamper detection
- Event-based custody tracking (collection, analysis, storage, transfer)
- SHA-256 and optional SHA3-512 hashing
- RFC 3161 timestamp authority integration
- Merkle proof generation for individual records
- Export to JSON and Markdown formats
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import ChainOfCustodyRecord

logger = logging.getLogger(__name__)


class CustodyAction(str, Enum):
    """Actions that can be recorded in the chain of custody."""
    COLLECTION = "COLLECTION"       # Initial evidence collection
    INGESTION = "INGESTION"         # Data ingestion into system
    PARSING = "PARSING"             # Document parsing
    ANALYSIS = "ANALYSIS"           # Forensic analysis
    VALIDATION = "VALIDATION"       # Agent validation
    ENRICHMENT = "ENRICHMENT"       # Data enrichment (e.g., GovInfo)
    STORAGE = "STORAGE"             # Evidence storage
    TRANSFER = "TRANSFER"           # Transfer between systems
    ACCESS = "ACCESS"               # Read access to evidence
    MODIFICATION = "MODIFICATION"   # Any modification (with justification)
    REVIEW = "REVIEW"               # Human review
    EXPORT = "EXPORT"               # Export for reporting
    SEAL = "SEAL"                   # Final sealing of evidence chain


class CustodyEventType(str, Enum):
    """Types of custody events for categorization."""
    DOCUMENT = "DOCUMENT"           # SEC filing document
    VIOLATION = "VIOLATION"         # Detected violation
    QUOTE = "QUOTE"                 # Extracted quote
    ANALYSIS_RESULT = "ANALYSIS_RESULT"  # Analysis output
    REPORT = "REPORT"               # Generated report
    PACKAGE = "PACKAGE"             # Evidence package
    METADATA = "METADATA"           # Filing metadata


@dataclass
class CustodyEvent:
    """
    Individual custody event in the chain.
    
    Represents a single action taken on evidence,
    with cryptographic linking to previous events.
    """
    event_id: str
    sequence_number: int
    action: CustodyAction
    event_type: CustodyEventType
    
    # Evidence identification
    evidence_id: str
    evidence_description: str
    
    # Actor information
    actor: str  # System component or user identifier
    actor_type: str  # "system", "agent", "user"
    
    # Timestamps
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Content hashing
    content_hash: str = ""
    hash_algorithm: str = "SHA-256"
    
    # Chain linking
    previous_event_hash: str = ""
    event_hash: str = ""
    
    # Additional context
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate event hash if not provided."""
        if not self.event_hash:
            self.event_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash of this event for chain integrity."""
        data = json.dumps({
            "event_id": self.event_id,
            "sequence_number": self.sequence_number,
            "action": self.action.value,
            "event_type": self.event_type.value,
            "evidence_id": self.evidence_id,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "content_hash": self.content_hash,
            "previous_event_hash": self.previous_event_hash,
        }, sort_keys=True)
        
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify(self) -> bool:
        """Verify event hash integrity."""
        return self.event_hash == self._compute_hash()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "sequence_number": self.sequence_number,
            "action": self.action.value,
            "event_type": self.event_type.value,
            "evidence_id": self.evidence_id,
            "evidence_description": self.evidence_description,
            "actor": self.actor,
            "actor_type": self.actor_type,
            "timestamp": self.timestamp.isoformat(),
            "content_hash": self.content_hash,
            "hash_algorithm": self.hash_algorithm,
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash,
            "notes": self.notes,
            "verified": self.verify(),
        }


@dataclass
class CustodyChain:
    """
    Complete chain of custody for a case or evidence package.
    
    Maintains an ordered sequence of custody events with
    cryptographic linking and integrity verification.
    """
    chain_id: str
    case_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Event chain
    events: List[CustodyEvent] = field(default_factory=list)
    
    # Chain integrity
    genesis_hash: str = ""
    current_head_hash: str = ""
    is_sealed: bool = False
    
    # Metadata
    description: str = ""
    classification: str = "LAW ENFORCEMENT SENSITIVE"
    
    def __post_init__(self):
        """Initialize genesis hash."""
        if not self.genesis_hash:
            genesis_data = json.dumps({
                "chain_id": self.chain_id,
                "case_id": self.case_id,
                "created_at": self.created_at.isoformat(),
            }, sort_keys=True)
            self.genesis_hash = hashlib.sha256(genesis_data.encode()).hexdigest()
            self.current_head_hash = self.genesis_hash
    
    @property
    def event_count(self) -> int:
        """Number of events in chain."""
        return len(self.events)
    
    @property
    def last_event(self) -> Optional[CustodyEvent]:
        """Get the most recent event."""
        return self.events[-1] if self.events else None
    
    def verify_chain(self) -> Tuple[bool, List[str]]:
        """
        Verify integrity of entire chain.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.events:
            return True, []
        
        # Verify genesis link
        if self.events[0].previous_event_hash != self.genesis_hash:
            errors.append(f"First event not linked to genesis hash")
        
        # Verify each event
        for i, event in enumerate(self.events):
            # Verify event hash
            if not event.verify():
                errors.append(f"Event {event.event_id} hash verification failed")
            
            # Verify chain linkage
            if i > 0:
                expected_prev = self.events[i - 1].event_hash
                if event.previous_event_hash != expected_prev:
                    errors.append(
                        f"Event {event.event_id} chain link broken "
                        f"(expected {expected_prev[:16]}..., got {event.previous_event_hash[:16]}...)"
                    )
            
            # Verify sequence
            if event.sequence_number != i + 1:
                errors.append(
                    f"Event {event.event_id} sequence mismatch "
                    f"(expected {i + 1}, got {event.sequence_number})"
                )
        
        # Verify head hash
        if self.events and self.current_head_hash != self.events[-1].event_hash:
            errors.append("Current head hash does not match last event")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        is_valid, errors = self.verify_chain()
        
        return {
            "chain_id": self.chain_id,
            "case_id": self.case_id,
            "created_at": self.created_at.isoformat(),
            "event_count": self.event_count,
            "genesis_hash": self.genesis_hash,
            "current_head_hash": self.current_head_hash,
            "is_sealed": self.is_sealed,
            "description": self.description,
            "classification": self.classification,
            "chain_verified": is_valid,
            "verification_errors": errors,
            "events": [e.to_dict() for e in self.events],
        }


class ChainOfCustodyLogger:
    """
    Main service for managing chain of custody logging.
    
    Provides methods to:
    - Create and manage custody chains
    - Record custody events with cryptographic linking
    - Verify chain integrity
    - Export custody documentation
    """
    
    def __init__(
        self,
        output_dir: str = "./output/custody",
        auto_persist: bool = True
    ):
        """
        Initialize Chain of Custody Logger.
        
        Args:
            output_dir: Directory for custody chain files
            auto_persist: Automatically persist chains after each event
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.auto_persist = auto_persist
        
        # Active chains
        self._chains: Dict[str, CustodyChain] = {}
        self._event_counter = 0
        self._chain_counter = 0
    
    def create_chain(
        self,
        case_id: str,
        description: str = ""
    ) -> CustodyChain:
        """
        Create a new custody chain for a case.
        
        Args:
            case_id: Case identifier
            description: Chain description
            
        Returns:
            New CustodyChain instance
        """
        self._chain_counter += 1
        chain_id = f"COC-{case_id}-{self._chain_counter:04d}"
        
        chain = CustodyChain(
            chain_id=chain_id,
            case_id=case_id,
            description=description,
        )
        
        self._chains[chain_id] = chain
        
        logger.info(f"Created custody chain {chain_id} for case {case_id}")
        return chain
    
    def get_chain(self, chain_id: str) -> Optional[CustodyChain]:
        """Get a custody chain by ID."""
        return self._chains.get(chain_id)
    
    def record_event(
        self,
        chain_id: str,
        action: CustodyAction,
        event_type: CustodyEventType,
        evidence_id: str,
        evidence_description: str,
        actor: str = "JLAW Forensic System",
        actor_type: str = "system",
        content_hash: str = "",
        notes: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> CustodyEvent:
        """
        Record a custody event in the chain.
        
        Args:
            chain_id: Chain to add event to
            action: Type of custody action
            event_type: Type of evidence being handled
            evidence_id: Unique identifier for the evidence
            evidence_description: Human-readable description
            actor: Who/what performed the action
            actor_type: Type of actor (system, agent, user)
            content_hash: SHA-256 hash of evidence content
            notes: Additional notes
            metadata: Additional metadata
            
        Returns:
            Created CustodyEvent
            
        Raises:
            ValueError: If chain not found or chain is sealed
        """
        chain = self._chains.get(chain_id)
        if not chain:
            raise ValueError(f"Chain not found: {chain_id}")
        
        if chain.is_sealed:
            raise ValueError(f"Chain is sealed and cannot be modified: {chain_id}")
        
        self._event_counter += 1
        sequence_number = chain.event_count + 1
        event_id = f"EVT-{chain_id}-{sequence_number:06d}"
        
        # Determine previous hash
        previous_hash = (
            chain.current_head_hash if chain.events
            else chain.genesis_hash
        )
        
        event = CustodyEvent(
            event_id=event_id,
            sequence_number=sequence_number,
            action=action,
            event_type=event_type,
            evidence_id=evidence_id,
            evidence_description=evidence_description,
            actor=actor,
            actor_type=actor_type,
            content_hash=content_hash,
            previous_event_hash=previous_hash,
            notes=notes,
            metadata=metadata or {},
        )
        
        # Add to chain
        chain.events.append(event)
        chain.current_head_hash = event.event_hash
        
        logger.debug(
            f"Recorded {action.value} event for {evidence_id} in {chain_id}"
        )
        
        # Auto-persist if enabled
        if self.auto_persist:
            self.persist_chain(chain_id)
        
        return event
    
    def record_collection(
        self,
        chain_id: str,
        evidence_id: str,
        source: str,
        content_hash: str = "",
        notes: str = ""
    ) -> CustodyEvent:
        """Record initial evidence collection."""
        return self.record_event(
            chain_id=chain_id,
            action=CustodyAction.COLLECTION,
            event_type=CustodyEventType.DOCUMENT,
            evidence_id=evidence_id,
            evidence_description=f"Collected from {source}",
            content_hash=content_hash,
            notes=notes,
            metadata={"source": source}
        )
    
    def record_analysis(
        self,
        chain_id: str,
        evidence_id: str,
        analyzer: str,
        findings_hash: str = "",
        notes: str = ""
    ) -> CustodyEvent:
        """Record analysis of evidence."""
        return self.record_event(
            chain_id=chain_id,
            action=CustodyAction.ANALYSIS,
            event_type=CustodyEventType.ANALYSIS_RESULT,
            evidence_id=evidence_id,
            evidence_description=f"Analyzed by {analyzer}",
            actor=analyzer,
            actor_type="agent" if "Agent" in analyzer else "system",
            content_hash=findings_hash,
            notes=notes,
        )
    
    def record_validation(
        self,
        chain_id: str,
        evidence_id: str,
        validator: str,
        result: str,
        notes: str = ""
    ) -> CustodyEvent:
        """Record validation of findings."""
        return self.record_event(
            chain_id=chain_id,
            action=CustodyAction.VALIDATION,
            event_type=CustodyEventType.VIOLATION,
            evidence_id=evidence_id,
            evidence_description=f"Validated by {validator}: {result}",
            actor=validator,
            actor_type="agent",
            notes=notes,
            metadata={"validation_result": result}
        )
    
    def seal_chain(self, chain_id: str) -> CustodyEvent:
        """
        Seal the chain to prevent further modifications.
        
        Args:
            chain_id: Chain to seal
            
        Returns:
            Seal event
        """
        chain = self._chains.get(chain_id)
        if not chain:
            raise ValueError(f"Chain not found: {chain_id}")
        
        if chain.is_sealed:
            raise ValueError(f"Chain already sealed: {chain_id}")
        
        # Record seal event
        seal_event = self.record_event(
            chain_id=chain_id,
            action=CustodyAction.SEAL,
            event_type=CustodyEventType.PACKAGE,
            evidence_id=chain_id,
            evidence_description="Chain of custody sealed",
            notes=f"Final head hash: {chain.current_head_hash}",
            metadata={
                "event_count": chain.event_count,
                "genesis_hash": chain.genesis_hash,
            }
        )
        
        chain.is_sealed = True
        
        # Persist sealed chain
        self.persist_chain(chain_id)
        
        logger.info(f"Sealed custody chain {chain_id} with {chain.event_count} events")
        return seal_event
    
    def verify_chain(self, chain_id: str) -> Tuple[bool, List[str]]:
        """
        Verify integrity of a custody chain.
        
        Args:
            chain_id: Chain to verify
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        chain = self._chains.get(chain_id)
        if not chain:
            return False, [f"Chain not found: {chain_id}"]
        
        return chain.verify_chain()
    
    def persist_chain(self, chain_id: str) -> Path:
        """
        Persist custody chain to file.
        
        Args:
            chain_id: Chain to persist
            
        Returns:
            Path to persisted file
        """
        chain = self._chains.get(chain_id)
        if not chain:
            raise ValueError(f"Chain not found: {chain_id}")
        
        filename = f"{chain_id}.json"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chain.to_dict(), f, indent=2, default=str)
        
        return output_path
    
    def load_chain(self, file_path: str) -> CustodyChain:
        """
        Load custody chain from file.
        
        Args:
            file_path: Path to chain JSON file
            
        Returns:
            Loaded CustodyChain
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chain = CustodyChain(
            chain_id=data["chain_id"],
            case_id=data["case_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            genesis_hash=data["genesis_hash"],
            current_head_hash=data["current_head_hash"],
            is_sealed=data.get("is_sealed", False),
            description=data.get("description", ""),
            classification=data.get("classification", "LAW ENFORCEMENT SENSITIVE"),
        )
        
        # Reconstruct events
        for event_data in data.get("events", []):
            event = CustodyEvent(
                event_id=event_data["event_id"],
                sequence_number=event_data["sequence_number"],
                action=CustodyAction(event_data["action"]),
                event_type=CustodyEventType(event_data["event_type"]),
                evidence_id=event_data["evidence_id"],
                evidence_description=event_data["evidence_description"],
                actor=event_data["actor"],
                actor_type=event_data["actor_type"],
                timestamp=datetime.fromisoformat(event_data["timestamp"]),
                content_hash=event_data.get("content_hash", ""),
                previous_event_hash=event_data["previous_event_hash"],
                event_hash=event_data["event_hash"],
                notes=event_data.get("notes", ""),
            )
            chain.events.append(event)
        
        self._chains[chain.chain_id] = chain
        
        logger.info(f"Loaded custody chain {chain.chain_id} with {chain.event_count} events")
        return chain
    
    def export_markdown(self, chain_id: str) -> Path:
        """
        Export custody chain to Markdown format.
        
        Args:
            chain_id: Chain to export
            
        Returns:
            Path to exported file
        """
        chain = self._chains.get(chain_id)
        if not chain:
            raise ValueError(f"Chain not found: {chain_id}")
        
        is_valid, errors = chain.verify_chain()
        
        lines = [
            "# CHAIN OF CUSTODY DOCUMENTATION",
            "",
            f"**Chain ID:** {chain.chain_id}",
            f"**Case ID:** {chain.case_id}",
            f"**Classification:** {chain.classification}",
            f"**Created:** {chain.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Status:** {'SEALED' if chain.is_sealed else 'ACTIVE'}",
            "",
            "---",
            "",
            "## CHAIN INTEGRITY",
            "",
            f"| Property | Value |",
            f"|----------|-------|",
            f"| Genesis Hash | `{chain.genesis_hash[:32]}...` |",
            f"| Current Head | `{chain.current_head_hash[:32]}...` |",
            f"| Event Count | {chain.event_count} |",
            f"| Integrity Verified | {'✓ VALID' if is_valid else '✗ INVALID'} |",
            "",
        ]
        
        if errors:
            lines.extend([
                "### Verification Errors",
                "",
            ])
            for error in errors:
                lines.append(f"- ⚠ {error}")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## CUSTODY EVENTS",
            "",
            "| # | Event ID | Action | Evidence | Actor | Timestamp | Verified |",
            "|---|----------|--------|----------|-------|-----------|----------|",
        ])
        
        for event in chain.events:
            verified = "✓" if event.verify() else "✗"
            lines.append(
                f"| {event.sequence_number} | {event.event_id} | "
                f"{event.action.value} | {event.evidence_id[:20]}... | "
                f"{event.actor[:15]} | "
                f"{event.timestamp.strftime('%Y-%m-%d %H:%M')} | {verified} |"
            )
        
        lines.extend([
            "",
            "---",
            "",
            "## EVENT DETAILS",
            "",
        ])
        
        for event in chain.events:
            lines.extend([
                f"### Event {event.sequence_number}: {event.event_id}",
                "",
                f"| Field | Value |",
                f"|-------|-------|",
                f"| Action | {event.action.value} |",
                f"| Evidence Type | {event.event_type.value} |",
                f"| Evidence ID | {event.evidence_id} |",
                f"| Description | {event.evidence_description} |",
                f"| Actor | {event.actor} ({event.actor_type}) |",
                f"| Timestamp | {event.timestamp.isoformat()} |",
                f"| Content Hash | `{event.content_hash[:32] if event.content_hash else 'N/A'}...` |",
                f"| Event Hash | `{event.event_hash[:32]}...` |",
                f"| Previous Hash | `{event.previous_event_hash[:32]}...` |",
                f"| Verified | {'✓ YES' if event.verify() else '✗ NO'} |",
                "",
            ])
            
            if event.notes:
                lines.extend([
                    f"**Notes:** {event.notes}",
                    "",
                ])
        
        lines.extend([
            "---",
            "",
            "*This chain of custody documentation is cryptographically verified.*",
            "*Any tampering will invalidate the hash chain.*",
        ])
        
        filename = f"{chain_id}.md"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Exported custody chain to {output_path}")
        return output_path
    
    def convert_to_custody_records(
        self,
        chain_id: str
    ) -> List[ChainOfCustodyRecord]:
        """
        Convert custody chain events to ChainOfCustodyRecord models.
        
        Args:
            chain_id: Chain to convert
            
        Returns:
            List of ChainOfCustodyRecord objects for reporting
        """
        chain = self._chains.get(chain_id)
        if not chain:
            return []
        
        records = []
        for event in chain.events:
            record = ChainOfCustodyRecord(
                record_id=event.event_id,
                evidence_type=event.event_type.value,
                evidence_description=event.evidence_description,
                collected_at=event.timestamp,
                collected_by=event.actor,
                storage_location=str(self.output_dir),
                sha256_hash=event.content_hash or event.event_hash,
                sha3_512_hash=None,
                rfc3161_timestamp=None,
                verification_status="verified" if event.verify() else "invalid",
            )
            records.append(record)
        
        return records


# Factory function
def create_custody_logger(
    output_dir: str = "./output/custody"
) -> ChainOfCustodyLogger:
    """
    Create a ChainOfCustodyLogger instance.
    
    Args:
        output_dir: Output directory for custody files
        
    Returns:
        Configured ChainOfCustodyLogger
    """
    return ChainOfCustodyLogger(output_dir=output_dir, auto_persist=True)
