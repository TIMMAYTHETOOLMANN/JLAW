"""
Pipeline Coordination Module
=============================

Coordinates execution stages for JLAW forensic analysis pipeline.

This module implements pipeline state management, stage execution tracking,
and error recovery per Section 12.1 of JLAW Zero-Dollar Transaction Forensic
Specification v1.0.

Reference:
    - Section 12.1: Master Orchestration Flow
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """
    Pipeline execution stages.
    
    Stages:
        ACQUISITION: SEC EDGAR Form 4 acquisition
        PARSING: XML parsing and normalization
        TEMPORAL_ANALYSIS: Temporal clustering detection
        EVENT_ANALYSIS: Event proximity analysis
        OWNERSHIP_ANALYSIS: Beneficial ownership chain resolution
        SCORING: Behavioral risk scoring
        NARRATIVE: Prosecutorial narrative generation
        PACKAGING: Evidence package creation
    """
    ACQUISITION = "acquisition"
    PARSING = "parsing"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    EVENT_ANALYSIS = "event_analysis"
    OWNERSHIP_ANALYSIS = "ownership_analysis"
    SCORING = "scoring"
    NARRATIVE = "narrative"
    PACKAGING = "packaging"


class StageStatus(Enum):
    """Stage execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """
    Result from pipeline stage execution.
    
    Attributes:
        stage: Pipeline stage executed
        status: Execution status
        start_time: When stage started
        end_time: When stage completed (if finished)
        error_message: Error message if failed
        data: Stage output data
    """
    stage: PipelineStage
    status: StageStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate stage duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'stage': self.stage.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'error_message': self.error_message,
        }


@dataclass
class PipelineState:
    """
    Pipeline execution state tracking.
    
    Attributes:
        issuer_cik: CIK of issuer being analyzed
        started_at: When pipeline started
        completed_at: When pipeline completed (if finished)
        stage_results: Results from each stage
        current_stage: Currently executing stage
        total_stages: Total number of stages
    """
    issuer_cik: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    stage_results: List[StageResult] = field(default_factory=list)
    current_stage: Optional[PipelineStage] = None
    total_stages: int = 8  # Total pipeline stages
    
    @property
    def is_complete(self) -> bool:
        """Check if pipeline is complete."""
        return self.completed_at is not None
    
    @property
    def is_successful(self) -> bool:
        """Check if pipeline completed successfully."""
        if not self.is_complete:
            return False
        return all(
            r.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
            for r in self.stage_results
        )
    
    @property
    def progress_percentage(self) -> float:
        """Calculate pipeline progress percentage."""
        completed_count = sum(
            1 for r in self.stage_results
            if r.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
        )
        return (completed_count / self.total_stages) * 100 if self.total_stages > 0 else 0
    
    def get_stage_result(self, stage: PipelineStage) -> Optional[StageResult]:
        """Get result for specific stage."""
        for result in self.stage_results:
            if result.stage == stage:
                return result
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'issuer_cik': self.issuer_cik,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_stage': self.current_stage.value if self.current_stage else None,
            'is_complete': self.is_complete,
            'is_successful': self.is_successful,
            'progress_percentage': self.progress_percentage,
            'stage_results': [r.to_dict() for r in self.stage_results],
        }


class PipelineExecutor:
    """
    Pipeline stage execution coordinator.
    
    Manages stage execution, error handling, and state tracking.
    """
    
    def __init__(self, issuer_cik: str):
        """
        Initialize pipeline executor.
        
        Args:
            issuer_cik: CIK of issuer being analyzed
        """
        self.state = PipelineState(issuer_cik=issuer_cik)
        self.logger = logging.getLogger(__name__)
    
    def start_stage(self, stage: PipelineStage) -> None:
        """
        Mark stage as started.
        
        Args:
            stage: Pipeline stage starting
        """
        self.state.current_stage = stage
        result = StageResult(
            stage=stage,
            status=StageStatus.IN_PROGRESS,
            start_time=datetime.utcnow(),
        )
        self.state.stage_results.append(result)
        self.logger.info(f"Started stage: {stage.value}")
    
    def complete_stage(
        self,
        stage: PipelineStage,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Mark stage as completed successfully.
        
        Args:
            stage: Pipeline stage completed
            data: Stage output data
        """
        result = self.state.get_stage_result(stage)
        if result:
            result.status = StageStatus.COMPLETED
            result.end_time = datetime.utcnow()
            if data:
                result.data = data
            self.logger.info(
                f"Completed stage: {stage.value} "
                f"(duration: {result.duration_seconds:.2f}s)"
            )
    
    def fail_stage(
        self,
        stage: PipelineStage,
        error_message: str,
    ) -> None:
        """
        Mark stage as failed.
        
        Args:
            stage: Pipeline stage that failed
            error_message: Error message
        """
        result = self.state.get_stage_result(stage)
        if result:
            result.status = StageStatus.FAILED
            result.end_time = datetime.utcnow()
            result.error_message = error_message
            self.logger.error(
                f"Failed stage: {stage.value} - {error_message}"
            )
    
    def skip_stage(
        self,
        stage: PipelineStage,
        reason: str,
    ) -> None:
        """
        Mark stage as skipped.
        
        Args:
            stage: Pipeline stage to skip
            reason: Reason for skipping
        """
        result = StageResult(
            stage=stage,
            status=StageStatus.SKIPPED,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            error_message=f"Skipped: {reason}",
        )
        self.state.stage_results.append(result)
        self.logger.info(f"Skipped stage: {stage.value} - {reason}")
    
    def complete_pipeline(self) -> None:
        """Mark pipeline as complete."""
        self.state.completed_at = datetime.utcnow()
        self.state.current_stage = None
        self.logger.info(
            f"Pipeline complete - Success: {self.state.is_successful}, "
            f"Progress: {self.state.progress_percentage:.1f}%"
        )
    
    def has_failed_stages(self) -> bool:
        """Check if any stages have failed."""
        return any(
            r.status == StageStatus.FAILED
            for r in self.state.stage_results
        )
    
    def get_failed_stages(self) -> List[StageResult]:
        """Get list of failed stages."""
        return [
            r for r in self.state.stage_results
            if r.status == StageStatus.FAILED
        ]
    
    def get_summary(self) -> str:
        """Get human-readable pipeline summary."""
        lines = [
            f"Pipeline Execution Summary",
            f"=" * 50,
            f"Issuer CIK: {self.state.issuer_cik}",
            f"Started: {self.state.started_at.isoformat()}",
            f"Status: {'Complete' if self.state.is_complete else 'In Progress'}",
            f"Progress: {self.state.progress_percentage:.1f}%",
            f"",
            f"Stage Results:",
        ]
        
        for result in self.state.stage_results:
            status_icon = {
                StageStatus.COMPLETED: "✓",
                StageStatus.FAILED: "✗",
                StageStatus.SKIPPED: "○",
                StageStatus.IN_PROGRESS: "⋯",
                StageStatus.PENDING: "·",
            }.get(result.status, "?")
            
            duration = f"{result.duration_seconds:.2f}s" if result.duration_seconds else "N/A"
            lines.append(
                f"  {status_icon} {result.stage.value.ljust(20)} "
                f"{result.status.value.ljust(15)} "
                f"{duration}"
            )
        
        if self.state.is_complete:
            lines.extend([
                f"",
                f"Completed: {self.state.completed_at.isoformat()}",
                f"Result: {'SUCCESS' if self.state.is_successful else 'FAILED'}",
            ])
        
        return "\n".join(lines)
