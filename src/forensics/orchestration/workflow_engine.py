"""
Workflow Engine - Job Queue and Task Management
==============================================

DAG-based task scheduling with retries and dependency management
for forensic investigation workflows.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class Task:
    """A single workflow task."""
    task_id: str
    name: str
    handler: Callable[..., Any]
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    timeout_seconds: int = 300
    
    # Runtime state
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __hash__(self) -> int:
        return hash(self.task_id)


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    workflow_id: str
    status: TaskStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    task_results: Dict[str, Any] = field(default_factory=dict)
    failed_tasks: List[str] = field(default_factory=list)
    skipped_tasks: List[str] = field(default_factory=list)


class WorkflowEngine:
    """
    Workflow Engine for forensic investigation task management.
    
    Features:
    - DAG-based task scheduling
    - Automatic retry with exponential backoff
    - Parallel execution where dependencies allow
    - Priority-based task queuing
    - Timeout handling
    
    Example:
        engine = WorkflowEngine()
        
        # Add tasks
        engine.add_task(Task("parse", "Document Parsing", parse_docs))
        engine.add_task(Task("analyze", "Analysis", analyze, dependencies=["parse"]))
        
        # Execute workflow
        result = await engine.execute()
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 4,
        default_timeout: int = 300,
        retry_delay_base: float = 1.0
    ):
        """
        Initialize the workflow engine.
        
        Args:
            max_concurrent_tasks: Maximum tasks to run in parallel
            default_timeout: Default task timeout in seconds
            retry_delay_base: Base delay for exponential backoff
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_timeout = default_timeout
        self.retry_delay_base = retry_delay_base
        
        self._tasks: Dict[str, Task] = {}
        self._task_queue: asyncio.Queue[Task] = asyncio.Queue()
        self._running_tasks: Set[str] = set()
        self._completed_tasks: Set[str] = set()
        self._failed_tasks: Set[str] = set()
        
        self._workflow_id: Optional[str] = None
        self._started_at: Optional[datetime] = None
        
        logger.info("WorkflowEngine initialized")
    
    def add_task(self, task: Task) -> None:
        """Add a task to the workflow."""
        self._tasks[task.task_id] = task
        logger.debug(f"Added task: {task.task_id}")
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the workflow."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> WorkflowResult:
        """
        Execute the workflow.
        
        Args:
            context: Optional context dict passed to all task handlers
            
        Returns:
            WorkflowResult with execution details
        """
        self._workflow_id = f"WF-{uuid.uuid4().hex[:8].upper()}"
        self._started_at = datetime.now()
        
        logger.info(f"Starting workflow {self._workflow_id} with {len(self._tasks)} tasks")
        
        # Reset state
        self._completed_tasks.clear()
        self._failed_tasks.clear()
        self._running_tasks.clear()
        
        # Validate DAG (no cycles)
        if not self._validate_dag():
            raise ValueError("Workflow contains circular dependencies")
        
        context = context or {}
        
        try:
            # Process tasks
            await self._process_tasks(context)
            
            # Determine overall status
            if self._failed_tasks:
                status = TaskStatus.FAILED
            elif len(self._completed_tasks) == len(self._tasks):
                status = TaskStatus.COMPLETED
            else:
                status = TaskStatus.CANCELLED
            
            completed_at = datetime.now()
            duration = (completed_at - self._started_at).total_seconds()
            
            result = WorkflowResult(
                workflow_id=self._workflow_id,
                status=status,
                started_at=self._started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                task_results={
                    t.task_id: t.result for t in self._tasks.values()
                    if t.status == TaskStatus.COMPLETED
                },
                failed_tasks=list(self._failed_tasks),
                skipped_tasks=[
                    t.task_id for t in self._tasks.values()
                    if t.status == TaskStatus.SKIPPED
                ]
            )
            
            logger.info(f"Workflow {self._workflow_id} completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Workflow {self._workflow_id} failed: {e}")
            raise
    
    def _validate_dag(self) -> bool:
        """Validate that the task graph has no cycles."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = self._tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id not in visited:
                        if has_cycle(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True
            
            rec_stack.remove(task_id)
            return False
        
        for task_id in self._tasks:
            if task_id not in visited:
                if has_cycle(task_id):
                    return False
        
        return True
    
    async def _process_tasks(self, context: Dict[str, Any]) -> None:
        """Process all tasks respecting dependencies."""
        # Get tasks in topological order
        sorted_tasks = self._topological_sort()
        
        # Group tasks by dependency level for parallel execution
        levels = self._get_dependency_levels(sorted_tasks)
        
        for level in levels:
            # Run all tasks at this level in parallel
            tasks_at_level = [self._tasks[tid] for tid in level]
            
            # Check if dependencies are satisfied
            ready_tasks = [
                t for t in tasks_at_level
                if self._dependencies_satisfied(t)
            ]
            
            if ready_tasks:
                await asyncio.gather(*[
                    self._execute_task(t, context) for t in ready_tasks
                ])
    
    def _topological_sort(self) -> List[str]:
        """Return tasks in topological order."""
        visited: Set[str] = set()
        result: List[str] = []
        
        def visit(task_id: str) -> None:
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = self._tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    visit(dep_id)
            
            result.append(task_id)
        
        for task_id in self._tasks:
            visit(task_id)
        
        return result
    
    def _get_dependency_levels(self, sorted_tasks: List[str]) -> List[List[str]]:
        """Group tasks by dependency level for parallel execution."""
        levels: List[List[str]] = []
        task_level: Dict[str, int] = {}
        
        for task_id in sorted_tasks:
            task = self._tasks[task_id]
            if not task.dependencies:
                level = 0
            else:
                level = max(task_level.get(dep, 0) for dep in task.dependencies) + 1
            
            task_level[task_id] = level
            
            while len(levels) <= level:
                levels.append([])
            levels[level].append(task_id)
        
        return levels
    
    def _dependencies_satisfied(self, task: Task) -> bool:
        """Check if all dependencies are satisfied."""
        for dep_id in task.dependencies:
            if dep_id in self._failed_tasks:
                task.status = TaskStatus.SKIPPED
                return False
            if dep_id not in self._completed_tasks:
                return False
        return True
    
    async def _execute_task(self, task: Task, context: Dict[str, Any]) -> None:
        """Execute a single task with retry logic."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._running_tasks.add(task.task_id)
        
        logger.info(f"Executing task: {task.name} ({task.task_id})")
        
        while task.retries <= task.max_retries:
            try:
                # Execute with timeout
                timeout = task.timeout_seconds or self.default_timeout
                result = await asyncio.wait_for(
                    self._call_handler(task, context),
                    timeout=timeout
                )
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                self._completed_tasks.add(task.task_id)
                
                logger.info(f"Task completed: {task.name}")
                break
                
            except asyncio.TimeoutError:
                task.error = f"Task timed out after {timeout}s"
                task.retries += 1
                logger.warning(f"Task {task.name} timed out, retry {task.retries}/{task.max_retries}")
                
            except Exception as e:
                task.error = str(e)
                task.retries += 1
                logger.warning(f"Task {task.name} failed: {e}, retry {task.retries}/{task.max_retries}")
            
            if task.retries <= task.max_retries:
                # Exponential backoff
                delay = self.retry_delay_base * (2 ** (task.retries - 1))
                await asyncio.sleep(delay)
        
        if task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self._failed_tasks.add(task.task_id)
            logger.error(f"Task failed: {task.name} - {task.error}")
        
        self._running_tasks.discard(task.task_id)
    
    async def _call_handler(self, task: Task, context: Dict[str, Any]) -> Any:
        """Call the task handler."""
        if asyncio.iscoroutinefunction(task.handler):
            return await task.handler(context)
        else:
            return task.handler(context)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "workflow_id": self._workflow_id,
            "total_tasks": len(self._tasks),
            "completed": len(self._completed_tasks),
            "failed": len(self._failed_tasks),
            "running": len(self._running_tasks),
            "pending": len(self._tasks) - len(self._completed_tasks) - len(self._failed_tasks) - len(self._running_tasks),
            "tasks": {
                t.task_id: {
                    "name": t.name,
                    "status": t.status.value,
                    "retries": t.retries
                }
                for t in self._tasks.values()
            }
        }
    
    def reset(self) -> None:
        """Reset the workflow engine for reuse."""
        self._tasks.clear()
        self._completed_tasks.clear()
        self._failed_tasks.clear()
        self._running_tasks.clear()
        self._workflow_id = None
        self._started_at = None
        
        # Clear the queue
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        logger.info("WorkflowEngine reset")
