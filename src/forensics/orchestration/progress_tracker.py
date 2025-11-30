"""
Progress Tracker - Real-time Progress Monitoring
================================================

Provides real-time progress tracking and monitoring for
forensic investigation workflows.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ProgressStatus(Enum):
    """Progress status states."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ProgressUpdate:
    """A single progress update."""
    timestamp: datetime
    phase: str
    step: str
    progress_percent: float
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PhaseProgress:
    """Progress tracking for a single phase."""
    phase_name: str
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    progress_percent: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    updates: List[ProgressUpdate] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvestigationProgress:
    """Complete progress tracking for an investigation."""
    case_id: str
    overall_status: ProgressStatus = ProgressStatus.NOT_STARTED
    overall_progress: float = 0.0
    current_phase: str = ""
    phases: Dict[str, PhaseProgress] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "case_id": self.case_id,
            "overall_status": self.overall_status.value,
            "overall_progress": self.overall_progress,
            "current_phase": self.current_phase,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "phases": {
                name: {
                    "status": p.status.value,
                    "progress_percent": p.progress_percent,
                    "current_step": p.current_step,
                    "total_steps": p.total_steps,
                    "completed_steps": p.completed_steps
                }
                for name, p in self.phases.items()
            }
        }


class ProgressTracker:
    """
    Real-time Progress Tracker for forensic investigations.
    
    Features:
    - Phase-level progress tracking
    - Step-level updates
    - ETA calculation
    - Progress callbacks
    - Metrics collection
    
    Example:
        tracker = ProgressTracker()
        
        # Start tracking
        tracker.start_investigation("CASE-001")
        
        # Update progress
        await tracker.update_phase_progress(
            "CASE-001",
            "document_parsing",
            50.0,
            "Processing document 5 of 10"
        )
        
        # Get progress
        progress = tracker.get_progress("CASE-001")
    """
    
    def __init__(self):
        """Initialize the Progress Tracker."""
        self._investigations: Dict[str, InvestigationProgress] = {}
        self._callbacks: List[Callable[[str, InvestigationProgress], None]] = []
        self._phase_weights: Dict[str, float] = {
            "document_parsing": 0.15,
            "intelligence_gathering": 0.15,
            "legal_correlation": 0.10,
            "temporal_analysis": 0.15,
            "prosecution_path": 0.15,
            "contradiction_detection": 0.15,
            "reporting": 0.15
        }
        
        logger.info("ProgressTracker initialized")
    
    def register_callback(
        self,
        callback: Callable[[str, InvestigationProgress], None]
    ) -> None:
        """Register a callback for progress updates."""
        self._callbacks.append(callback)
    
    def unregister_callback(
        self,
        callback: Callable[[str, InvestigationProgress], None]
    ) -> None:
        """Unregister a progress callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, case_id: str, progress: InvestigationProgress) -> None:
        """Notify all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback(case_id, progress)
            except Exception as e:
                logger.warning(f"Callback error: {e}")
    
    def start_investigation(
        self,
        case_id: str,
        phases: Optional[List[str]] = None
    ) -> InvestigationProgress:
        """
        Start tracking a new investigation.
        
        Args:
            case_id: Case identifier
            phases: List of phase names to track
            
        Returns:
            Investigation progress object
        """
        phases = phases or list(self._phase_weights.keys())
        
        progress = InvestigationProgress(
            case_id=case_id,
            overall_status=ProgressStatus.IN_PROGRESS,
            started_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        for phase in phases:
            progress.phases[phase] = PhaseProgress(phase_name=phase)
        
        self._investigations[case_id] = progress
        
        logger.info(f"Started tracking investigation: {case_id}")
        return progress
    
    def start_phase(
        self,
        case_id: str,
        phase_name: str,
        total_steps: int = 0
    ) -> Optional[PhaseProgress]:
        """
        Start a phase.
        
        Args:
            case_id: Case identifier
            phase_name: Phase name
            total_steps: Total steps in the phase
            
        Returns:
            Phase progress object
        """
        progress = self._investigations.get(case_id)
        if not progress:
            return None
        
        if phase_name not in progress.phases:
            progress.phases[phase_name] = PhaseProgress(phase_name=phase_name)
        
        phase = progress.phases[phase_name]
        phase.status = ProgressStatus.IN_PROGRESS
        phase.started_at = datetime.now()
        phase.total_steps = total_steps
        phase.completed_steps = 0
        phase.progress_percent = 0.0
        
        progress.current_phase = phase_name
        progress.last_updated = datetime.now()
        
        self._notify_callbacks(case_id, progress)
        
        logger.info(f"Started phase {phase_name} for {case_id}")
        return phase
    
    async def update_phase_progress(
        self,
        case_id: str,
        phase_name: str,
        progress_percent: float,
        message: str = "",
        step: str = "",
        metrics: Optional[Dict[str, Any]] = None
    ) -> Optional[InvestigationProgress]:
        """
        Update phase progress.
        
        Args:
            case_id: Case identifier
            phase_name: Phase name
            progress_percent: Progress percentage (0-100)
            message: Progress message
            step: Current step name
            metrics: Optional metrics
            
        Returns:
            Updated investigation progress
        """
        progress = self._investigations.get(case_id)
        if not progress:
            return None
        
        if phase_name not in progress.phases:
            progress.phases[phase_name] = PhaseProgress(phase_name=phase_name)
        
        phase = progress.phases[phase_name]
        phase.progress_percent = min(100.0, max(0.0, progress_percent))
        phase.current_step = step
        
        if metrics:
            phase.metrics.update(metrics)
        
        # Add update record
        update = ProgressUpdate(
            timestamp=datetime.now(),
            phase=phase_name,
            step=step,
            progress_percent=progress_percent,
            message=message,
            metrics=metrics or {}
        )
        phase.updates.append(update)
        
        # Keep only last 100 updates per phase
        if len(phase.updates) > 100:
            phase.updates = phase.updates[-100:]
        
        # Calculate overall progress
        self._calculate_overall_progress(progress)
        
        progress.last_updated = datetime.now()
        
        self._notify_callbacks(case_id, progress)
        
        return progress
    
    def complete_phase(
        self,
        case_id: str,
        phase_name: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Optional[PhaseProgress]:
        """
        Mark a phase as completed.
        
        Args:
            case_id: Case identifier
            phase_name: Phase name
            metrics: Final phase metrics
            
        Returns:
            Completed phase progress
        """
        progress = self._investigations.get(case_id)
        if not progress:
            return None
        
        phase = progress.phases.get(phase_name)
        if not phase:
            return None
        
        phase.status = ProgressStatus.COMPLETED
        phase.progress_percent = 100.0
        phase.completed_at = datetime.now()
        
        if metrics:
            phase.metrics.update(metrics)
        
        self._calculate_overall_progress(progress)
        progress.last_updated = datetime.now()
        
        self._notify_callbacks(case_id, progress)
        
        logger.info(f"Completed phase {phase_name} for {case_id}")
        return phase
    
    def fail_phase(
        self,
        case_id: str,
        phase_name: str,
        error: str = ""
    ) -> Optional[PhaseProgress]:
        """Mark a phase as failed."""
        progress = self._investigations.get(case_id)
        if not progress:
            return None
        
        phase = progress.phases.get(phase_name)
        if not phase:
            return None
        
        phase.status = ProgressStatus.FAILED
        phase.completed_at = datetime.now()
        phase.metrics["error"] = error
        
        progress.last_updated = datetime.now()
        
        self._notify_callbacks(case_id, progress)
        
        logger.error(f"Phase {phase_name} failed for {case_id}: {error}")
        return phase
    
    def _calculate_overall_progress(self, progress: InvestigationProgress) -> None:
        """Calculate overall progress from phase progress."""
        total_weight = 0.0
        weighted_progress = 0.0
        
        for phase_name, phase in progress.phases.items():
            weight = self._phase_weights.get(phase_name, 1.0 / len(progress.phases))
            total_weight += weight
            weighted_progress += weight * phase.progress_percent
        
        if total_weight > 0:
            progress.overall_progress = weighted_progress / total_weight
        
        # Update overall status
        all_completed = all(
            p.status == ProgressStatus.COMPLETED
            for p in progress.phases.values()
        )
        any_failed = any(
            p.status == ProgressStatus.FAILED
            for p in progress.phases.values()
        )
        
        if all_completed:
            progress.overall_status = ProgressStatus.COMPLETED
        elif any_failed:
            progress.overall_status = ProgressStatus.FAILED
        else:
            progress.overall_status = ProgressStatus.IN_PROGRESS
        
        # Estimate completion time
        self._estimate_completion(progress)
    
    def _estimate_completion(self, progress: InvestigationProgress) -> None:
        """Estimate completion time based on progress."""
        if not progress.started_at or progress.overall_progress <= 0:
            return
        
        elapsed = (datetime.now() - progress.started_at).total_seconds()
        if progress.overall_progress > 0:
            total_estimated = elapsed / (progress.overall_progress / 100.0)
            remaining = total_estimated - elapsed
            progress.estimated_completion = datetime.now() + timedelta(seconds=remaining)
    
    def complete_investigation(
        self,
        case_id: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Optional[InvestigationProgress]:
        """Mark investigation as completed."""
        progress = self._investigations.get(case_id)
        if not progress:
            return None
        
        progress.overall_status = ProgressStatus.COMPLETED
        progress.overall_progress = 100.0
        progress.last_updated = datetime.now()
        
        self._notify_callbacks(case_id, progress)
        
        logger.info(f"Completed investigation: {case_id}")
        return progress
    
    def get_progress(self, case_id: str) -> Optional[InvestigationProgress]:
        """Get progress for an investigation."""
        return self._investigations.get(case_id)
    
    def get_phase_progress(
        self,
        case_id: str,
        phase_name: str
    ) -> Optional[PhaseProgress]:
        """Get progress for a specific phase."""
        progress = self._investigations.get(case_id)
        if not progress:
            return None
        return progress.phases.get(phase_name)
    
    def get_all_progress(self) -> Dict[str, InvestigationProgress]:
        """Get progress for all investigations."""
        return dict(self._investigations)
    
    def get_active_investigations(self) -> List[str]:
        """Get list of active investigation case IDs."""
        return [
            case_id for case_id, progress in self._investigations.items()
            if progress.overall_status == ProgressStatus.IN_PROGRESS
        ]
    
    def cleanup(self, case_id: str) -> bool:
        """Remove progress tracking for a case."""
        if case_id in self._investigations:
            del self._investigations[case_id]
            return True
        return False
    
    def get_summary(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of investigation progress."""
        progress = self._investigations.get(case_id)
        if not progress:
            return None
        
        return {
            "case_id": case_id,
            "status": progress.overall_status.value,
            "progress": f"{progress.overall_progress:.1f}%",
            "current_phase": progress.current_phase,
            "phases_completed": sum(
                1 for p in progress.phases.values()
                if p.status == ProgressStatus.COMPLETED
            ),
            "total_phases": len(progress.phases),
            "estimated_completion": (
                progress.estimated_completion.isoformat()
                if progress.estimated_completion else None
            ),
            "elapsed_time": (
                str(datetime.now() - progress.started_at)
                if progress.started_at else None
            )
        }
