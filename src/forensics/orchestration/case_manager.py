"""
Case Manager - Multi-Case Management System
============================================

Manages multiple concurrent forensic investigation cases with
persistent storage and case lifecycle management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import uuid
import json

logger = logging.getLogger(__name__)


class CaseStatus(Enum):
    """Case lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    CLOSED = "closed"


class CasePriority(Enum):
    """Case priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class CaseMetadata:
    """Metadata for a forensic case."""
    created_by: str = ""
    assigned_to: str = ""
    department: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    external_references: Dict[str, str] = field(default_factory=dict)


@dataclass
class Case:
    """A forensic investigation case."""
    case_id: str
    target: str
    title: str
    description: str
    status: CaseStatus = CaseStatus.DRAFT
    priority: CasePriority = CasePriority.NORMAL
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Case data
    input_files: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    investigation_results: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: CaseMetadata = field(default_factory=CaseMetadata)
    
    # Findings
    findings: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Scores
    risk_score: float = 0.0
    prosecution_probability: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert case to dictionary for serialization."""
        return {
            "case_id": self.case_id,
            "target": self.target,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "input_files": self.input_files,
            "output_files": self.output_files,
            "investigation_results": self.investigation_results,
            "findings": self.findings,
            "violations": self.violations,
            "risk_score": self.risk_score,
            "prosecution_probability": self.prosecution_probability
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Case":
        """Create case from dictionary."""
        case = cls(
            case_id=data["case_id"],
            target=data["target"],
            title=data["title"],
            description=data.get("description", ""),
            status=CaseStatus(data.get("status", "draft")),
            priority=CasePriority(data.get("priority", "normal")),
            input_files=data.get("input_files", []),
            output_files=data.get("output_files", []),
            investigation_results=data.get("investigation_results", {}),
            findings=data.get("findings", []),
            violations=data.get("violations", []),
            risk_score=data.get("risk_score", 0.0),
            prosecution_probability=data.get("prosecution_probability", 0.0)
        )
        
        if data.get("created_at"):
            case.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            case.updated_at = datetime.fromisoformat(data["updated_at"])
        if data.get("started_at"):
            case.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            case.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return case


class CaseManager:
    """
    Multi-Case Management System
    
    Manages the complete lifecycle of forensic investigation cases.
    
    Features:
    - Create, update, delete cases
    - Case status tracking
    - Persistent storage
    - Query and filtering
    - Case archival
    
    Example:
        manager = CaseManager()
        
        # Create a case
        case = await manager.create_case(
            target="Company XYZ",
            title="Financial Fraud Investigation"
        )
        
        # Update status
        await manager.update_status(case.case_id, CaseStatus.ACTIVE)
        
        # List active cases
        active_cases = await manager.list_cases(status=CaseStatus.ACTIVE)
    """
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        enable_persistence: bool = True
    ):
        """
        Initialize the Case Manager.
        
        Args:
            storage_dir: Directory for case storage
            enable_persistence: Enable persistent storage
        """
        self.storage_dir = storage_dir or Path("./forensic_cases")
        self.enable_persistence = enable_persistence
        
        if enable_persistence:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._cases: Dict[str, Case] = {}
        self._lock = asyncio.Lock()
        
        # Load existing cases if persistence enabled
        if enable_persistence:
            self._load_cases()
        
        logger.info("CaseManager initialized")
    
    def _load_cases(self) -> None:
        """Load cases from persistent storage."""
        case_files = list(self.storage_dir.glob("case_*.json"))
        
        for case_file in case_files:
            try:
                with open(case_file, 'r') as f:
                    data = json.load(f)
                    case = Case.from_dict(data)
                    self._cases[case.case_id] = case
            except Exception as e:
                logger.warning(f"Failed to load case file {case_file}: {e}")
        
        logger.info(f"Loaded {len(self._cases)} existing cases")
    
    async def _save_case(self, case: Case) -> None:
        """Save a case to persistent storage."""
        if not self.enable_persistence:
            return
        
        case_file = self.storage_dir / f"case_{case.case_id}.json"
        
        try:
            with open(case_file, 'w') as f:
                json.dump(case.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save case {case.case_id}: {e}")
    
    async def create_case(
        self,
        target: str,
        title: str,
        description: str = "",
        priority: CasePriority = CasePriority.NORMAL,
        input_files: Optional[List[str]] = None,
        metadata: Optional[CaseMetadata] = None
    ) -> Case:
        """
        Create a new forensic case.
        
        Args:
            target: Investigation target
            title: Case title
            description: Case description
            priority: Case priority
            input_files: Initial input files
            metadata: Case metadata
            
        Returns:
            Created case
        """
        async with self._lock:
            case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
            
            case = Case(
                case_id=case_id,
                target=target,
                title=title,
                description=description,
                priority=priority,
                input_files=input_files or [],
                metadata=metadata or CaseMetadata()
            )
            
            self._cases[case_id] = case
            await self._save_case(case)
            
            logger.info(f"Created case: {case_id} - {title}")
            return case
    
    async def get_case(self, case_id: str) -> Optional[Case]:
        """Get a case by ID."""
        return self._cases.get(case_id)
    
    async def update_case(
        self,
        case_id: str,
        **updates: Any
    ) -> Optional[Case]:
        """
        Update a case.
        
        Args:
            case_id: Case ID
            **updates: Fields to update
            
        Returns:
            Updated case or None if not found
        """
        async with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            
            for key, value in updates.items():
                if hasattr(case, key):
                    setattr(case, key, value)
            
            case.updated_at = datetime.now()
            await self._save_case(case)
            
            logger.info(f"Updated case: {case_id}")
            return case
    
    async def update_status(
        self,
        case_id: str,
        status: CaseStatus
    ) -> Optional[Case]:
        """Update case status."""
        async with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            
            old_status = case.status
            case.status = status
            case.updated_at = datetime.now()
            
            # Update timestamps based on status
            if status == CaseStatus.ACTIVE and case.started_at is None:
                case.started_at = datetime.now()
            elif status in [CaseStatus.COMPLETED, CaseStatus.CLOSED]:
                case.completed_at = datetime.now()
            
            await self._save_case(case)
            
            logger.info(f"Case {case_id} status: {old_status.value} -> {status.value}")
            return case
    
    async def add_findings(
        self,
        case_id: str,
        findings: List[Dict[str, Any]]
    ) -> Optional[Case]:
        """Add findings to a case."""
        async with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            
            case.findings.extend(findings)
            case.updated_at = datetime.now()
            await self._save_case(case)
            
            logger.info(f"Added {len(findings)} findings to case {case_id}")
            return case
    
    async def add_violations(
        self,
        case_id: str,
        violations: List[Dict[str, Any]]
    ) -> Optional[Case]:
        """Add violations to a case."""
        async with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            
            case.violations.extend(violations)
            case.updated_at = datetime.now()
            await self._save_case(case)
            
            logger.info(f"Added {len(violations)} violations to case {case_id}")
            return case
    
    async def set_investigation_results(
        self,
        case_id: str,
        results: Dict[str, Any]
    ) -> Optional[Case]:
        """Set investigation results for a case."""
        async with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            
            case.investigation_results = results
            case.updated_at = datetime.now()
            
            # Extract scores if available
            if "summary" in results:
                summary = results["summary"]
                if "overall" in summary:
                    case.prosecution_probability = summary["overall"].get(
                        "conviction_probability", 0.0
                    )
            
            await self._save_case(case)
            return case
    
    async def list_cases(
        self,
        status: Optional[CaseStatus] = None,
        priority: Optional[CasePriority] = None,
        target: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Case]:
        """
        List cases with optional filtering.
        
        Args:
            status: Filter by status
            priority: Filter by priority
            target: Filter by target (partial match)
            limit: Maximum results
            offset: Offset for pagination
            
        Returns:
            List of matching cases
        """
        cases = list(self._cases.values())
        
        # Apply filters
        if status:
            cases = [c for c in cases if c.status == status]
        if priority:
            cases = [c for c in cases if c.priority == priority]
        if target:
            cases = [c for c in cases if target.lower() in c.target.lower()]
        
        # Sort by updated_at descending
        cases.sort(key=lambda c: c.updated_at, reverse=True)
        
        # Apply pagination
        return cases[offset:offset + limit]
    
    async def delete_case(self, case_id: str) -> bool:
        """Delete a case."""
        async with self._lock:
            if case_id not in self._cases:
                return False
            
            del self._cases[case_id]
            
            # Remove from storage
            if self.enable_persistence:
                case_file = self.storage_dir / f"case_{case_id}.json"
                if case_file.exists():
                    case_file.unlink()
            
            logger.info(f"Deleted case: {case_id}")
            return True
    
    async def archive_case(self, case_id: str) -> Optional[Case]:
        """Archive a case."""
        return await self.update_status(case_id, CaseStatus.ARCHIVED)
    
    async def get_case_statistics(self) -> Dict[str, Any]:
        """Get overall case statistics."""
        cases = list(self._cases.values())
        
        status_counts = {}
        for status in CaseStatus:
            status_counts[status.value] = len([c for c in cases if c.status == status])
        
        priority_counts = {}
        for priority in CasePriority:
            priority_counts[priority.value] = len([c for c in cases if c.priority == priority])
        
        return {
            "total_cases": len(cases),
            "by_status": status_counts,
            "by_priority": priority_counts,
            "avg_risk_score": sum(c.risk_score for c in cases) / len(cases) if cases else 0,
            "avg_prosecution_probability": sum(c.prosecution_probability for c in cases) / len(cases) if cases else 0
        }
    
    async def search_cases(
        self,
        query: str,
        fields: Optional[List[str]] = None
    ) -> List[Case]:
        """
        Search cases by text query.
        
        Args:
            query: Search query
            fields: Fields to search (default: title, target, description)
            
        Returns:
            Matching cases
        """
        query = query.lower()
        fields = fields or ["title", "target", "description"]
        
        results = []
        for case in self._cases.values():
            for field_name in fields:
                value = getattr(case, field_name, "")
                if isinstance(value, str) and query in value.lower():
                    results.append(case)
                    break
        
        return results
    
    def get_case_count(self) -> int:
        """Get total number of cases."""
        return len(self._cases)
