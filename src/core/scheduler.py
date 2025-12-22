"""
Investigation Scheduler
=======================

Autonomous monitoring and scheduled forensic analysis system for JLAW.

Features:
- Cron-like scheduling for periodic investigations
- Event-driven triggers (new filings, price anomalies)
- Watchlist monitoring (track specific CIKs)
- Automated report generation
- Alert notification system
- Resource management and throttling

Architecture:
    InvestigationScheduler
        ├── Schedule Manager (periodic tasks)
        ├── Event Monitor (filing notifications)
        ├── Watchlist Manager (tracked entities)
        └── Execution Queue (rate-limited)

Example:
    scheduler = InvestigationScheduler()
    
    # Schedule periodic analysis
    scheduler.schedule_investigation(
        cik="320187",
        company_name="NIKE, Inc.",
        frequency="weekly",
        start_date=date(2024, 1, 1)
    )
    
    # Add watchlist entry
    scheduler.add_to_watchlist(
        cik="1652044",
        company_name="Alphabet Inc.",
        alert_on=["new_filing", "insider_trade", "material_event"]
    )
    
    # Start scheduler
    await scheduler.start()
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ScheduleFrequency(Enum):
    """Investigation schedule frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TriggerType(Enum):
    """Event trigger types for automated investigations."""
    NEW_FILING = "new_filing"
    INSIDER_TRADE = "insider_trade"
    MATERIAL_EVENT = "material_event"
    PRICE_ANOMALY = "price_anomaly"
    VOLUME_SPIKE = "volume_spike"
    SCHEDULED = "scheduled"


@dataclass
class ScheduledInvestigation:
    """Configuration for a scheduled investigation."""
    investigation_id: str
    cik: str
    company_name: str
    frequency: ScheduleFrequency
    next_run: datetime
    lookback_days: int = 90
    enabled: bool = True
    last_run: Optional[datetime] = None
    run_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "investigation_id": self.investigation_id,
            "cik": self.cik,
            "company_name": self.company_name,
            "frequency": self.frequency.value,
            "next_run": self.next_run.isoformat(),
            "lookback_days": self.lookback_days,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class WatchlistEntry:
    """Watchlist entry for real-time monitoring."""
    cik: str
    company_name: str
    alert_triggers: List[TriggerType]
    last_check: Optional[datetime] = None
    alert_count: int = 0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cik": self.cik,
            "company_name": self.company_name,
            "alert_triggers": [t.value for t in self.alert_triggers],
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "alert_count": self.alert_count,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class InvestigationEvent:
    """Event triggering an investigation."""
    event_id: str
    trigger_type: TriggerType
    cik: str
    company_name: str
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "trigger_type": self.trigger_type.value,
            "cik": self.cik,
            "company_name": self.company_name,
            "event_data": self.event_data,
            "timestamp": self.timestamp.isoformat(),
            "processed": self.processed
        }


class InvestigationScheduler:
    """
    Autonomous investigation scheduler with monitoring and alerting.
    
    Provides:
    - Periodic scheduled investigations (daily, weekly, monthly, etc.)
    - Event-driven triggers (new filings, material events)
    - Watchlist monitoring for specific entities
    - Rate-limited execution queue
    - Automated report generation
    - Alert notification system
    
    Example:
        scheduler = InvestigationScheduler(
            output_dir="./scheduled_investigations"
        )
        
        # Add scheduled investigation
        scheduler.schedule_investigation(
            cik="320187",
            company_name="NIKE, Inc.",
            frequency="weekly"
        )
        
        # Add to watchlist
        scheduler.add_to_watchlist(
            cik="1652044",
            company_name="Alphabet Inc.",
            alert_on=["new_filing", "material_event"]
        )
        
        # Start scheduler (runs indefinitely)
        await scheduler.start()
    """
    
    def __init__(
        self,
        output_dir: str = "./scheduled_investigations",
        max_concurrent: int = 3,
        check_interval_seconds: int = 300,  # 5 minutes
        state_file: Optional[str] = None
    ):
        """
        Initialize investigation scheduler.
        
        Args:
            output_dir: Directory for investigation outputs
            max_concurrent: Maximum concurrent investigations
            check_interval_seconds: Interval for checking schedules/events
            state_file: Optional file to persist scheduler state
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_concurrent = max_concurrent
        self.check_interval_seconds = check_interval_seconds
        self.state_file = Path(state_file) if state_file else None
        
        # Scheduled investigations
        self._schedules: Dict[str, ScheduledInvestigation] = {}
        
        # Watchlist
        self._watchlist: Dict[str, WatchlistEntry] = {}
        
        # Event queue
        self._event_queue: List[InvestigationEvent] = []
        
        # Active investigations tracking
        self._active_investigations: Set[str] = set()
        
        # Execution semaphore for rate limiting
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        # Running flag
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(
            f"InvestigationScheduler initialized: "
            f"output_dir={output_dir}, max_concurrent={max_concurrent}"
        )
        
        # Load state if file exists
        if self.state_file and self.state_file.exists():
            self._load_state()
    
    def schedule_investigation(
        self,
        cik: str,
        company_name: str,
        frequency: str,
        start_date: Optional[date] = None,
        lookback_days: int = 90
    ) -> str:
        """
        Schedule a periodic investigation.
        
        Args:
            cik: Company CIK number
            company_name: Company name
            frequency: Schedule frequency ("daily", "weekly", "monthly", "quarterly", "yearly")
            start_date: Start date for scheduling (default: today)
            lookback_days: Days to look back for analysis
            
        Returns:
            Investigation ID
        """
        freq = ScheduleFrequency(frequency.lower())
        start = start_date or date.today()
        
        # Calculate next run time
        next_run = self._calculate_next_run(start, freq)
        
        # Generate investigation ID
        inv_id = f"SCH-{cik}-{freq.value.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create schedule
        schedule = ScheduledInvestigation(
            investigation_id=inv_id,
            cik=cik,
            company_name=company_name,
            frequency=freq,
            next_run=next_run,
            lookback_days=lookback_days
        )
        
        self._schedules[inv_id] = schedule
        
        logger.info(
            f"Scheduled {freq.value} investigation for {company_name} (CIK: {cik}), "
            f"next run: {next_run.isoformat()}"
        )
        
        self._save_state()
        return inv_id
    
    def add_to_watchlist(
        self,
        cik: str,
        company_name: str,
        alert_on: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add company to watchlist for real-time monitoring.
        
        Args:
            cik: Company CIK number
            company_name: Company name
            alert_on: List of trigger types to monitor
            metadata: Optional metadata
        """
        triggers = [TriggerType(t.lower()) for t in alert_on]
        
        entry = WatchlistEntry(
            cik=cik,
            company_name=company_name,
            alert_triggers=triggers,
            metadata=metadata or {}
        )
        
        self._watchlist[cik] = entry
        
        logger.info(
            f"Added {company_name} (CIK: {cik}) to watchlist, "
            f"monitoring: {', '.join(t.value for t in triggers)}"
        )
        
        self._save_state()
    
    def remove_from_watchlist(self, cik: str):
        """Remove company from watchlist."""
        if cik in self._watchlist:
            entry = self._watchlist.pop(cik)
            logger.info(f"Removed {entry.company_name} from watchlist")
            self._save_state()
    
    def unschedule_investigation(self, investigation_id: str):
        """Remove scheduled investigation."""
        if investigation_id in self._schedules:
            schedule = self._schedules.pop(investigation_id)
            logger.info(
                f"Removed scheduled investigation: {schedule.company_name} "
                f"({schedule.frequency.value})"
            )
            self._save_state()
    
    async def start(self):
        """Start the scheduler (runs indefinitely)."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        logger.info("Starting investigation scheduler...")
        
        # Create main scheduler task
        self._task = asyncio.create_task(self._scheduler_loop())
        
        try:
            await self._task
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled")
    
    async def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Wait for active investigations to complete
        while self._active_investigations:
            logger.info(
                f"Waiting for {len(self._active_investigations)} active investigations to complete..."
            )
            await asyncio.sleep(5)
        
        logger.info("Scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                # Check scheduled investigations
                await self._check_schedules()
                
                # Check watchlist for events
                await self._check_watchlist()
                
                # Process event queue
                await self._process_events()
                
                # Wait before next check
                await asyncio.sleep(self.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _check_schedules(self):
        """Check for scheduled investigations that are due."""
        now = datetime.utcnow()
        
        for inv_id, schedule in list(self._schedules.items()):
            if not schedule.enabled:
                continue
            
            if now >= schedule.next_run:
                logger.info(
                    f"Triggering scheduled investigation: {schedule.company_name} "
                    f"({schedule.frequency.value})"
                )
                
                # Queue investigation
                event = InvestigationEvent(
                    event_id=f"SCH-{inv_id}-{now.strftime('%Y%m%d%H%M%S')}",
                    trigger_type=TriggerType.SCHEDULED,
                    cik=schedule.cik,
                    company_name=schedule.company_name,
                    event_data={
                        "schedule_id": inv_id,
                        "frequency": schedule.frequency.value,
                        "lookback_days": schedule.lookback_days
                    }
                )
                self._event_queue.append(event)
                
                # Update schedule
                schedule.last_run = now
                schedule.run_count += 1
                schedule.next_run = self._calculate_next_run(
                    now.date(),
                    schedule.frequency,
                    from_now=True
                )
                
                self._save_state()
    
    async def _check_watchlist(self):
        """Check watchlist for triggering events."""
        # This would integrate with SEC EDGAR API or other data sources
        # to monitor for new filings, insider trades, etc.
        
        # Placeholder implementation
        for cik, entry in self._watchlist.items():
            if not entry.enabled:
                continue
            
            # Check if enough time has passed since last check
            if entry.last_check:
                time_since_check = (datetime.utcnow() - entry.last_check).total_seconds()
                if time_since_check < 3600:  # Check at most once per hour
                    continue
            
            # Update last check time
            entry.last_check = datetime.utcnow()
            
            # In production, would check for:
            # - New filings via SEC EDGAR API
            # - Insider trades via Form 4 monitoring
            # - Material events via 8-K monitoring
            # - Price/volume anomalies via market data
    
    async def _process_events(self):
        """Process queued investigation events."""
        while self._event_queue and len(self._active_investigations) < self.max_concurrent:
            event = self._event_queue.pop(0)
            
            if event.processed:
                continue
            
            # Execute investigation asynchronously
            asyncio.create_task(self._execute_investigation(event))
    
    async def _execute_investigation(self, event: InvestigationEvent):
        """Execute an investigation for an event."""
        async with self._semaphore:
            self._active_investigations.add(event.event_id)
            
            try:
                logger.info(
                    f"Starting investigation: {event.company_name} "
                    f"(trigger: {event.trigger_type.value})"
                )
                
                # In production, would call MasterExecutionController
                # For now, just simulate execution
                
                # Placeholder: Import and execute
                # from src.core.master_execution_controller import MasterExecutionController
                # 
                # controller = MasterExecutionController(...)
                # result = await controller.execute_full_analysis()
                
                await asyncio.sleep(2)  # Simulate work
                
                event.processed = True
                
                logger.info(
                    f"Completed investigation: {event.company_name} "
                    f"(event: {event.event_id})"
                )
                
            except Exception as e:
                logger.error(
                    f"Investigation failed for {event.company_name}: {e}",
                    exc_info=True
                )
            
            finally:
                self._active_investigations.discard(event.event_id)
    
    def _calculate_next_run(
        self,
        base_date: date,
        frequency: ScheduleFrequency,
        from_now: bool = False
    ) -> datetime:
        """Calculate next run datetime based on frequency."""
        if from_now:
            base_dt = datetime.utcnow()
        else:
            # Schedule for 9:00 AM UTC (market open)
            base_dt = datetime.combine(base_date, time(9, 0))
        
        if frequency == ScheduleFrequency.DAILY:
            next_dt = base_dt + timedelta(days=1)
        elif frequency == ScheduleFrequency.WEEKLY:
            next_dt = base_dt + timedelta(weeks=1)
        elif frequency == ScheduleFrequency.MONTHLY:
            # Approximate month
            next_dt = base_dt + timedelta(days=30)
        elif frequency == ScheduleFrequency.QUARTERLY:
            next_dt = base_dt + timedelta(days=90)
        elif frequency == ScheduleFrequency.YEARLY:
            next_dt = base_dt + timedelta(days=365)
        else:
            next_dt = base_dt + timedelta(days=1)
        
        return next_dt
    
    def _save_state(self):
        """Persist scheduler state to file."""
        if not self.state_file:
            return
        
        state = {
            "schedules": {
                inv_id: sched.to_dict()
                for inv_id, sched in self._schedules.items()
            },
            "watchlist": {
                cik: entry.to_dict()
                for cik, entry in self._watchlist.items()
            },
            "last_saved": datetime.utcnow().isoformat()
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"Saved scheduler state to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save scheduler state: {e}")
    
    def _load_state(self):
        """Load scheduler state from file."""
        if not self.state_file or not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Restore schedules
            for inv_id, sched_data in state.get("schedules", {}).items():
                schedule = ScheduledInvestigation(
                    investigation_id=sched_data["investigation_id"],
                    cik=sched_data["cik"],
                    company_name=sched_data["company_name"],
                    frequency=ScheduleFrequency(sched_data["frequency"]),
                    next_run=datetime.fromisoformat(sched_data["next_run"]),
                    lookback_days=sched_data["lookback_days"],
                    enabled=sched_data["enabled"],
                    last_run=datetime.fromisoformat(sched_data["last_run"]) if sched_data.get("last_run") else None,
                    run_count=sched_data["run_count"],
                    created_at=datetime.fromisoformat(sched_data["created_at"])
                )
                self._schedules[inv_id] = schedule
            
            # Restore watchlist
            for cik, entry_data in state.get("watchlist", {}).items():
                entry = WatchlistEntry(
                    cik=entry_data["cik"],
                    company_name=entry_data["company_name"],
                    alert_triggers=[TriggerType(t) for t in entry_data["alert_triggers"]],
                    last_check=datetime.fromisoformat(entry_data["last_check"]) if entry_data.get("last_check") else None,
                    alert_count=entry_data["alert_count"],
                    enabled=entry_data["enabled"],
                    created_at=datetime.fromisoformat(entry_data["created_at"]),
                    metadata=entry_data.get("metadata", {})
                )
                self._watchlist[cik] = entry
            
            logger.info(
                f"Loaded scheduler state: {len(self._schedules)} schedules, "
                f"{len(self._watchlist)} watchlist entries"
            )
            
        except Exception as e:
            logger.error(f"Failed to load scheduler state: {e}", exc_info=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "scheduled_investigations": len(self._schedules),
            "watchlist_entries": len(self._watchlist),
            "active_investigations": len(self._active_investigations),
            "queued_events": len(self._event_queue),
            "running": self._running,
            "schedules": [s.to_dict() for s in self._schedules.values()],
            "watchlist": [w.to_dict() for w in self._watchlist.values()]
        }


__all__ = [
    'InvestigationScheduler',
    'ScheduleFrequency',
    'TriggerType',
    'ScheduledInvestigation',
    'WatchlistEntry',
    'InvestigationEvent'
]
