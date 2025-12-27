"""
Autonomous Forensic Executor
============================

Integrates InvestigationScheduler with MasterExecutionController for
automated, scheduled forensic analysis runs.

Features:
- Scheduled investigations (daily, weekly, monthly, quarterly, yearly)
- Watchlist monitoring with event-driven triggers
- Automated report generation
- Graceful shutdown and state persistence
- Command-line interface for scheduler management

Architecture:
    AutonomousForensicExecutor
        ├── InvestigationScheduler (scheduling & monitoring)
        ├── MasterExecutionController (forensic analysis)
        └── State Management (persistence & recovery)

Example:
    # Start autonomous executor
    executor = AutonomousForensicExecutor(
        output_dir="./autonomous_investigations",
        state_file="./scheduler_state.json"
    )
    
    # Schedule periodic investigation
    executor.schedule_investigation(
        cik="320187",
        company_name="NIKE, Inc.",
        frequency="weekly"
    )
    
    # Start scheduler (runs indefinitely)
    await executor.start()
"""

import asyncio
import signal
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Configuration for autonomous forensic execution."""
    cik: str
    company_name: str
    lookback_days: int = 90
    strict_mode: bool = True
    auto_mode: bool = True
    output_dir: Optional[Path] = None


class AutonomousForensicExecutor:
    """
    Autonomous forensic executor with scheduling and monitoring.
    
    Integrates InvestigationScheduler with MasterExecutionController to
    enable scheduled and event-driven forensic analysis.
    
    Features:
    - Periodic scheduled investigations
    - Watchlist monitoring for real-time alerts
    - Automated dossier generation
    - State persistence and recovery
    - Graceful shutdown handling
    
    Example:
        executor = AutonomousForensicExecutor(
            output_dir="./autonomous_investigations"
        )
        
        # Schedule weekly analysis
        executor.schedule_investigation(
            cik="320187",
            company_name="NIKE, Inc.",
            frequency="weekly"
        )
        
        # Start executor (runs indefinitely)
        await executor.start()
    """
    
    def __init__(
        self,
        output_dir: str = "./autonomous_investigations",
        state_file: Optional[str] = None,
        max_concurrent: int = 2,
        check_interval_seconds: int = 300
    ):
        """
        Initialize autonomous forensic executor.
        
        Args:
            output_dir: Base directory for investigation outputs
            state_file: Optional file for state persistence
            max_concurrent: Maximum concurrent investigations
            check_interval_seconds: Interval for checking schedules (default: 5 minutes)
        """
        # DEPRECATION WARNING
        import warnings
        warnings.warn(
            "AutonomousForensicExecutor is deprecated. "
            "Use UnifiedForensicOrchestrator from src.core.unified_orchestrator for DOJ-grade compliance. "
            "This class will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2
        )
        
        from src.core.scheduler import InvestigationScheduler
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize scheduler
        self.scheduler = InvestigationScheduler(
            output_dir=str(self.output_dir),
            max_concurrent=max_concurrent,
            check_interval_seconds=check_interval_seconds,
            state_file=state_file
        )
        
        # Override scheduler's execution method to use MasterExecutionController
        self._original_execute = self.scheduler._execute_investigation
        self.scheduler._execute_investigation = self._execute_investigation_with_controller
        
        # Shutdown flag
        self._shutdown_requested = False
        
        logger.info(
            f"AutonomousForensicExecutor initialized: "
            f"output_dir={output_dir}, max_concurrent={max_concurrent}"
        )
    
    def schedule_investigation(
        self,
        cik: str,
        company_name: str,
        frequency: str,
        start_date: Optional[date] = None,
        lookback_days: int = 90,
        strict_mode: bool = True
    ) -> str:
        """
        Schedule a periodic forensic investigation.
        
        Args:
            cik: Company CIK number
            company_name: Company name
            frequency: Schedule frequency ("daily", "weekly", "monthly", "quarterly", "yearly")
            start_date: Start date for scheduling (default: today)
            lookback_days: Days to look back for analysis (default: 90)
            strict_mode: Enable strict execution mode (default: True)
            
        Returns:
            Investigation ID
        """
        inv_id = self.scheduler.schedule_investigation(
            cik=cik,
            company_name=company_name,
            frequency=frequency,
            start_date=start_date,
            lookback_days=lookback_days
        )
        
        logger.info(
            f"Scheduled {frequency} investigation for {company_name} (CIK: {cik}), "
            f"ID: {inv_id}"
        )
        
        return inv_id
    
    def add_to_watchlist(
        self,
        cik: str,
        company_name: str,
        alert_on: list,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add company to watchlist for real-time monitoring.
        
        Args:
            cik: Company CIK number
            company_name: Company name
            alert_on: List of trigger types ("new_filing", "insider_trade", "material_event", etc.)
            metadata: Optional metadata
        """
        self.scheduler.add_to_watchlist(
            cik=cik,
            company_name=company_name,
            alert_on=alert_on,
            metadata=metadata
        )
        
        logger.info(f"Added {company_name} to watchlist")
    
    def remove_from_watchlist(self, cik: str):
        """Remove company from watchlist."""
        self.scheduler.remove_from_watchlist(cik)
    
    def unschedule_investigation(self, investigation_id: str):
        """Remove scheduled investigation."""
        self.scheduler.unschedule_investigation(investigation_id)
    
    async def start(self):
        """
        Start the autonomous executor (runs indefinitely).
        
        Handles graceful shutdown on SIGINT/SIGTERM.
        """
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        logger.info("Starting autonomous forensic executor...")
        
        try:
            await self.scheduler.start()
        except asyncio.CancelledError:
            logger.info("Executor task cancelled")
        except Exception as e:
            logger.error(f"Executor error: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the autonomous executor gracefully."""
        if self._shutdown_requested:
            return
        
        self._shutdown_requested = True
        logger.info("Stopping autonomous forensic executor...")
        
        await self.scheduler.stop()
        
        logger.info("Autonomous forensic executor stopped")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _execute_investigation_with_controller(self, event):
        """
        Execute investigation using MasterExecutionController.
        
        This method overrides the scheduler's default execution method.
        
        Args:
            event: InvestigationEvent from scheduler
        """
        from src.core.master_execution_controller import MasterExecutionController
        from src.core.scheduler import InvestigationEvent
        
        # Cast to InvestigationEvent for type checking
        if not isinstance(event, InvestigationEvent):
            logger.error(f"Invalid event type: {type(event)}")
            return
        
        logger.info(
            f"Starting investigation: {event.company_name} "
            f"(trigger: {event.trigger_type.value})"
        )
        
        try:
            # Calculate date range
            end_date = date.today()
            lookback_days = event.event_data.get('lookback_days', 90)
            start_date = end_date - timedelta(days=lookback_days)
            
            # Create output directory for this investigation
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            investigation_output_dir = self.output_dir / f"{event.cik}_{timestamp}"
            investigation_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize MasterExecutionController
            controller = MasterExecutionController(
                cik=event.cik,
                company_name=event.company_name,
                start_date=start_date,
                end_date=end_date,
                output_dir=investigation_output_dir,
                strict_mode=True,
                auto_mode=True
            )
            
            # Execute full analysis
            result = await controller.execute_full_analysis()
            
            # Mark event as processed
            event.processed = True
            
            # Log completion
            if result.get('success', False):
                logger.info(
                    f"✓ Investigation completed successfully: {event.company_name} "
                    f"(event: {event.event_id})"
                )
            else:
                logger.warning(
                    f"⚠ Investigation completed with errors: {event.company_name} "
                    f"(event: {event.event_id})"
                )
            
            # Save investigation summary
            summary_file = investigation_output_dir / "investigation_summary.json"
            with open(summary_file, 'w') as f:
                json.dump({
                    "event_id": event.event_id,
                    "trigger_type": event.trigger_type.value,
                    "cik": event.cik,
                    "company_name": event.company_name,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "timestamp": timestamp,
                    "success": result.get('success', False),
                    "execution_time_seconds": result.get('execution_time_seconds', 0)
                }, f, indent=2)
            
        except Exception as e:
            logger.error(
                f"Investigation failed for {event.company_name}: {e}",
                exc_info=True
            )
            event.processed = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current executor status."""
        scheduler_stats = self.scheduler.get_statistics()
        
        return {
            "running": scheduler_stats.get("running", False),
            "scheduled_investigations": scheduler_stats.get("scheduled_investigations", 0),
            "watchlist_entries": scheduler_stats.get("watchlist_entries", 0),
            "active_investigations": scheduler_stats.get("active_investigations", 0),
            "queued_events": scheduler_stats.get("queued_events", 0),
            "output_dir": str(self.output_dir)
        }


# ═══════════════════════════════════════════════════════════════════════
# COMMAND-LINE INTERFACE
# ═══════════════════════════════════════════════════════════════════════

async def main():
    """
    Command-line interface for autonomous forensic executor.
    
    Example usage:
        python -m src.core.autonomous_executor --schedule 320187 "NIKE, Inc." weekly
        python -m src.core.autonomous_executor --watchlist 1652044 "Alphabet Inc." new_filing,material_event
        python -m src.core.autonomous_executor --start
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="JLAW Autonomous Forensic Executor - Scheduled Investigation System"
    )
    
    # Output configuration
    parser.add_argument(
        '--output-dir',
        default='./autonomous_investigations',
        help='Output directory for investigations'
    )
    parser.add_argument(
        '--state-file',
        default='./scheduler_state.json',
        help='State file for persistence'
    )
    
    # Actions
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--schedule',
        nargs=3,
        metavar=('CIK', 'COMPANY_NAME', 'FREQUENCY'),
        help='Schedule investigation (frequency: daily/weekly/monthly/quarterly/yearly)'
    )
    action_group.add_argument(
        '--watchlist',
        nargs=3,
        metavar=('CIK', 'COMPANY_NAME', 'TRIGGERS'),
        help='Add to watchlist (triggers: comma-separated list)'
    )
    action_group.add_argument(
        '--start',
        action='store_true',
        help='Start the autonomous executor'
    )
    action_group.add_argument(
        '--status',
        action='store_true',
        help='Get executor status'
    )
    
    args = parser.parse_args()
    
    # Initialize executor
    executor = AutonomousForensicExecutor(
        output_dir=args.output_dir,
        state_file=args.state_file
    )
    
    # Execute action
    if args.schedule:
        cik, company_name, frequency = args.schedule
        inv_id = executor.schedule_investigation(
            cik=cik,
            company_name=company_name,
            frequency=frequency
        )
        print(f"Scheduled investigation: {inv_id}")
    
    elif args.watchlist:
        cik, company_name, triggers = args.watchlist
        trigger_list = [t.strip() for t in triggers.split(',')]
        executor.add_to_watchlist(
            cik=cik,
            company_name=company_name,
            alert_on=trigger_list
        )
        print(f"Added {company_name} to watchlist")
    
    elif args.start:
        print("Starting autonomous forensic executor...")
        print("Press Ctrl+C to stop")
        await executor.start()
    
    elif args.status:
        status = executor.get_status()
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())


__all__ = [
    'AutonomousForensicExecutor',
    'ExecutionConfig'
]
