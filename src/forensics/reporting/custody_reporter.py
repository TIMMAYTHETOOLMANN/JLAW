"""
Chain of Custody Reporter - Evidence Documentation
===================================================

Generates chain of custody documentation for forensic evidence.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class CustodyEvent:
    """A single custody event."""
    timestamp: datetime
    action: str  # acquired, transferred, analyzed, stored
    handler: str
    location: str
    notes: str = ""
    verification_hash: str = ""


@dataclass
class EvidenceItem:
    """A tracked evidence item."""
    evidence_id: str
    name: str
    description: str
    source: str
    file_path: Optional[str] = None
    file_hash: str = ""
    file_size: int = 0
    acquired_at: datetime = field(default_factory=datetime.now)
    custody_chain: List[CustodyEvent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CustodyReport:
    """Complete chain of custody report."""
    case_id: str
    generated_at: datetime
    evidence_items: List[EvidenceItem] = field(default_factory=list)
    total_items: int = 0
    verified_items: int = 0
    report_hash: str = ""


class CustodyReporter:
    """
    Chain of Custody Reporter
    
    Generates and manages chain of custody documentation
    for forensic evidence items.
    
    Features:
    - Evidence tracking
    - Custody chain management
    - Hash verification
    - Report generation
    
    Example:
        reporter = CustodyReporter()
        
        # Add evidence
        item = reporter.add_evidence(
            name="Financial Statement 2019",
            source="SEC EDGAR",
            file_path="/evidence/stmt.pdf"
        )
        
        # Record custody transfer
        reporter.record_transfer(item.evidence_id, "Analyst", "Lab")
        
        # Generate report
        report = reporter.generate_report("CASE-001")
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize the custody reporter."""
        self.storage_dir = storage_dir or Path("./custody_records")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._evidence: Dict[str, EvidenceItem] = {}
        self._case_evidence: Dict[str, List[str]] = {}
        
        logger.info("CustodyReporter initialized")
    
    def add_evidence(
        self,
        name: str,
        source: str,
        description: str = "",
        file_path: Optional[str] = None,
        case_id: Optional[str] = None,
        handler: str = "System",
        location: str = "Digital Storage",
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvidenceItem:
        """
        Add a new evidence item.
        
        Args:
            name: Evidence name
            source: Evidence source
            description: Evidence description
            file_path: Path to evidence file
            case_id: Associated case ID
            handler: Initial handler
            location: Initial location
            metadata: Additional metadata
            
        Returns:
            Created evidence item
        """
        evidence_id = f"EVD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self._evidence):04d}"
        
        item = EvidenceItem(
            evidence_id=evidence_id,
            name=name,
            description=description,
            source=source,
            file_path=file_path,
            metadata=metadata or {}
        )
        
        # Calculate file hash if file exists
        if file_path:
            path = Path(file_path)
            if path.exists():
                item.file_hash = self._calculate_hash(path)
                item.file_size = path.stat().st_size
        
        # Record initial acquisition
        acquisition_event = CustodyEvent(
            timestamp=datetime.now(),
            action="acquired",
            handler=handler,
            location=location,
            notes=f"Evidence acquired from {source}",
            verification_hash=item.file_hash
        )
        item.custody_chain.append(acquisition_event)
        
        self._evidence[evidence_id] = item
        
        # Associate with case
        if case_id:
            if case_id not in self._case_evidence:
                self._case_evidence[case_id] = []
            self._case_evidence[case_id].append(evidence_id)
        
        logger.info(f"Added evidence: {evidence_id} - {name}")
        return item
    
    def record_transfer(
        self,
        evidence_id: str,
        new_handler: str,
        new_location: str,
        notes: str = ""
    ) -> Optional[EvidenceItem]:
        """Record an evidence transfer."""
        item = self._evidence.get(evidence_id)
        if not item:
            return None
        
        event = CustodyEvent(
            timestamp=datetime.now(),
            action="transferred",
            handler=new_handler,
            location=new_location,
            notes=notes,
            verification_hash=item.file_hash
        )
        item.custody_chain.append(event)
        
        logger.info(f"Recorded transfer for {evidence_id}")
        return item
    
    def record_analysis(
        self,
        evidence_id: str,
        analyst: str,
        analysis_type: str,
        notes: str = ""
    ) -> Optional[EvidenceItem]:
        """Record that evidence was analyzed."""
        item = self._evidence.get(evidence_id)
        if not item:
            return None
        
        event = CustodyEvent(
            timestamp=datetime.now(),
            action="analyzed",
            handler=analyst,
            location="Analysis Lab",
            notes=f"{analysis_type}: {notes}",
            verification_hash=item.file_hash
        )
        item.custody_chain.append(event)
        
        return item
    
    def verify_evidence(self, evidence_id: str) -> bool:
        """Verify evidence integrity by checking hash."""
        item = self._evidence.get(evidence_id)
        if not item or not item.file_path:
            return False
        
        path = Path(item.file_path)
        if not path.exists():
            return False
        
        current_hash = self._calculate_hash(path)
        return current_hash == item.file_hash
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Get an evidence item by ID."""
        return self._evidence.get(evidence_id)
    
    def get_case_evidence(self, case_id: str) -> List[EvidenceItem]:
        """Get all evidence for a case."""
        evidence_ids = self._case_evidence.get(case_id, [])
        return [self._evidence[eid] for eid in evidence_ids if eid in self._evidence]
    
    def generate_report(self, case_id: str) -> CustodyReport:
        """
        Generate a chain of custody report.
        
        Args:
            case_id: Case identifier
            
        Returns:
            Complete custody report
        """
        evidence_items = self.get_case_evidence(case_id)
        
        # Verify all items
        verified_count = sum(1 for item in evidence_items if self.verify_evidence(item.evidence_id))
        
        report = CustodyReport(
            case_id=case_id,
            generated_at=datetime.now(),
            evidence_items=evidence_items,
            total_items=len(evidence_items),
            verified_items=verified_count
        )
        
        # Calculate report hash
        report_data = json.dumps({
            "case_id": case_id,
            "items": [
                {
                    "id": item.evidence_id,
                    "hash": item.file_hash,
                    "events": len(item.custody_chain)
                }
                for item in evidence_items
            ]
        }, sort_keys=True)
        report.report_hash = hashlib.sha256(report_data.encode()).hexdigest()
        
        logger.info(f"Generated custody report for case {case_id}")
        return report
    
    def export_report(
        self,
        report: CustodyReport,
        output_path: Path
    ) -> Path:
        """Export custody report to JSON file."""
        report_dict = {
            "case_id": report.case_id,
            "generated_at": report.generated_at.isoformat(),
            "total_items": report.total_items,
            "verified_items": report.verified_items,
            "report_hash": report.report_hash,
            "evidence": [
                {
                    "evidence_id": item.evidence_id,
                    "name": item.name,
                    "source": item.source,
                    "file_hash": item.file_hash,
                    "custody_chain": [
                        {
                            "timestamp": event.timestamp.isoformat(),
                            "action": event.action,
                            "handler": event.handler,
                            "location": event.location,
                            "notes": event.notes
                        }
                        for event in item.custody_chain
                    ]
                }
                for item in report.evidence_items
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        return output_path
