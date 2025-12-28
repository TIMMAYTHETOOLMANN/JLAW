"""
JLAW CLI Progress Tracker
==========================

Progress tracking and status updates for long-running analysis operations.
"""

from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    from rich.console import Console
    from rich.progress import (
        Progress,
        SpinnerColumn,
        TextColumn,
        BarColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
        TimeElapsedColumn
    )
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Progress = None


class ProgressTracker:
    """Track and display progress for forensic analysis operations."""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize progress tracker.
        
        Args:
            console: Rich console instance
        """
        self.console = console
        self.progress = None
        self.current_task = None
        
        if RICH_AVAILABLE and console:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console
            )
    
    def __enter__(self):
        """Enter context manager."""
        if self.progress:
            self.progress.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.progress:
            self.progress.__exit__(exc_type, exc_val, exc_tb)
    
    def add_task(self, description: str, total: Optional[float] = None) -> int:
        """
        Add a new task to track.
        
        Args:
            description: Task description
            total: Total units of work (None for indeterminate)
            
        Returns:
            Task ID
        """
        if self.progress:
            return self.progress.add_task(description, total=total)
        else:
            # Fallback: print task start
            print(f"Starting: {description}")
            return 0
    
    def update(
        self,
        task_id: int,
        advance: Optional[float] = None,
        completed: Optional[float] = None,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Update task progress.
        
        Args:
            task_id: Task ID
            advance: Amount to advance progress
            completed: Set completed amount directly
            description: Update task description
            **kwargs: Additional progress kwargs
        """
        if self.progress:
            update_kwargs = {}
            if advance is not None:
                update_kwargs['advance'] = advance
            if completed is not None:
                update_kwargs['completed'] = completed
            if description is not None:
                update_kwargs['description'] = description
            update_kwargs.update(kwargs)
            
            self.progress.update(task_id, **update_kwargs)
        else:
            # Fallback: print progress
            if description:
                print(f"Progress: {description}")
            if completed is not None:
                print(f"  Completed: {completed}")
    
    def remove_task(self, task_id: int):
        """
        Remove a task from progress tracking.
        
        Args:
            task_id: Task ID to remove
        """
        if self.progress:
            self.progress.remove_task(task_id)
    
    def update_phase(self, phase_name: str, status: str = "running"):
        """
        Update current phase status.
        
        Args:
            phase_name: Name of the phase
            status: Status (running, complete, failed)
        """
        emoji_map = {
            'running': '⏳',
            'complete': '✅',
            'failed': '❌'
        }
        
        emoji = emoji_map.get(status, '📊')
        message = f"{emoji} {phase_name}"
        
        if self.console and RICH_AVAILABLE:
            style_map = {
                'running': 'cyan',
                'complete': 'green',
                'failed': 'red'
            }
            style = style_map.get(status, 'white')
            self.console.print(f"[{style}]{message}[/{style}]")
        else:
            print(message)


@contextmanager
def simple_progress(description: str, console: Optional[Console] = None):
    """
    Simple progress context manager for single operations.
    
    Args:
        description: Operation description
        console: Rich console instance
        
    Example:
        with simple_progress("Downloading filings..."):
            # Do work
            pass
    """
    tracker = ProgressTracker(console)
    
    with tracker:
        task_id = tracker.add_task(description)
        try:
            yield tracker
            tracker.update(task_id, completed=100)
        except Exception as e:
            if console and RICH_AVAILABLE:
                console.print(f"[red]❌ Failed: {e}[/red]")
            else:
                print(f"Failed: {e}")
            raise


class PhaseProgressTracker:
    """Track progress across multiple phases of analysis."""
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize phase progress tracker.
        
        Args:
            console: Rich console instance
        """
        self.console = console
        self.phases: Dict[str, Dict[str, Any]] = {}
        self.current_phase = None
    
    def start_phase(self, phase_name: str, total_steps: int = 100):
        """
        Start tracking a new phase.
        
        Args:
            phase_name: Name of the phase
            total_steps: Total steps in phase
        """
        self.current_phase = phase_name
        self.phases[phase_name] = {
            'status': 'running',
            'completed': 0,
            'total': total_steps,
            'start_time': None
        }
        
        if self.console and RICH_AVAILABLE:
            self.console.print(f"[cyan]⏳ Starting: {phase_name}[/cyan]")
        else:
            print(f"Starting: {phase_name}")
    
    def update_phase(self, phase_name: Optional[str] = None, completed: int = 0):
        """
        Update phase progress.
        
        Args:
            phase_name: Phase to update (None for current)
            completed: Completed steps
        """
        target_phase = phase_name or self.current_phase
        
        if target_phase and target_phase in self.phases:
            self.phases[target_phase]['completed'] = completed
            
            pct = (completed / self.phases[target_phase]['total']) * 100
            
            if self.console and RICH_AVAILABLE:
                self.console.print(f"  Progress: {pct:.0f}%")
            else:
                print(f"  Progress: {pct:.0f}%")
    
    def complete_phase(self, phase_name: Optional[str] = None, success: bool = True):
        """
        Mark phase as complete.
        
        Args:
            phase_name: Phase to complete (None for current)
            success: Whether phase succeeded
        """
        target_phase = phase_name or self.current_phase
        
        if target_phase and target_phase in self.phases:
            self.phases[target_phase]['status'] = 'complete' if success else 'failed'
            
            if self.console and RICH_AVAILABLE:
                status_text = "✅ Complete" if success else "❌ Failed"
                style = "green" if success else "red"
                self.console.print(f"[{style}]{status_text}: {target_phase}[/{style}]")
            else:
                status_text = "Complete" if success else "Failed"
                print(f"{status_text}: {target_phase}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all phases."""
        return {
            'phases': self.phases,
            'total_phases': len(self.phases),
            'completed_phases': sum(
                1 for p in self.phases.values() if p['status'] == 'complete'
            ),
            'failed_phases': sum(
                1 for p in self.phases.values() if p['status'] == 'failed'
            )
        }
