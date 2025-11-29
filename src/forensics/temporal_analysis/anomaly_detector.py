"""
Temporal Anomaly Detector
Detects anomalies in temporal patterns using statistical and ML techniques.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics
from collections import defaultdict

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("NumPy not available, some anomaly detection features will be limited")

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of temporal anomalies."""
    GAP = "gap"
    CLUSTER = "cluster"
    PATTERN_BREAK = "pattern_break"
    FREQUENCY_CHANGE = "frequency_change"
    OUTLIER = "outlier"


@dataclass
class GapAnomaly:
    """Represents an unusual gap in the timeline."""
    gap_duration: timedelta
    start_event: any
    end_event: any
    expected_duration: timedelta
    statistical_significance: float
    forensic_impact: str


@dataclass
class ClusterAnomaly:
    """Represents unusual clustering of events."""
    cluster_start: datetime
    cluster_end: datetime
    events_in_cluster: List[any]
    cluster_density: float
    baseline_density: float
    significance_score: float
    forensic_impact: str


@dataclass
class PatternBreak:
    """Represents a break in expected pattern."""
    break_point: datetime
    pattern_type: str
    expected_pattern: str
    actual_pattern: str
    deviation_magnitude: float
    forensic_impact: str


class TemporalAnomalyDetector:
    """
    Detects anomalies in temporal patterns.
    
    Uses statistical methods and machine learning to identify:
    - Unusual gaps in event sequences
    - Abnormal clustering of events
    - Breaks in regular patterns
    - Frequency changes
    - Statistical outliers
    """
    
    def __init__(self, sensitivity: float = 2.0):
        """
        Initialize anomaly detector.
        
        Args:
            sensitivity: Z-score threshold (default: 2.0 standard deviations)
        """
        self.sensitivity = sensitivity
        logger.info(f"TemporalAnomalyDetector initialized (sensitivity={sensitivity})")
    
    async def detect_all_anomalies(
        self,
        events: List[any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Any]]:
        """
        Detect all types of anomalies in event timeline.
        
        Args:
            events: List of temporal events
            options: Detection options
        
        Returns:
            Dictionary of anomaly types and their instances
        """
        options = options or {}
        
        results = {
            'gaps': [],
            'clusters': [],
            'pattern_breaks': [],
            'frequency_changes': [],
            'outliers': []
        }
        
        if len(events) < 3:
            logger.warning("Insufficient events for anomaly detection")
            return results
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # Detect gaps
        logger.debug("Detecting gap anomalies...")
        results['gaps'] = await self._detect_gap_anomalies(sorted_events)
        
        # Detect clusters
        logger.debug("Detecting cluster anomalies...")
        results['clusters'] = await self._detect_cluster_anomalies(sorted_events)
        
        # Detect pattern breaks
        logger.debug("Detecting pattern breaks...")
        results['pattern_breaks'] = await self._detect_pattern_breaks(sorted_events)
        
        # Detect frequency changes
        logger.debug("Detecting frequency changes...")
        results['frequency_changes'] = await self._detect_frequency_changes(sorted_events)
        
        total_anomalies = sum(len(v) for v in results.values())
        logger.info(f"Detected {total_anomalies} total anomalies")
        
        return results
    
    async def _detect_gap_anomalies(self, events: List[any]) -> List[GapAnomaly]:
        """Detect unusual gaps between events."""
        anomalies = []
        
        if len(events) < 2:
            return anomalies
        
        # Calculate all gaps
        gaps = []
        for i in range(len(events) - 1):
            gap = (events[i + 1].timestamp - events[i].timestamp).total_seconds()
            gaps.append({
                'duration': gap,
                'start_event': events[i],
                'end_event': events[i + 1],
                'index': i
            })
        
        if not gaps:
            return anomalies
        
        # Statistical analysis
        gap_durations = [g['duration'] for g in gaps]
        mean_gap = statistics.mean(gap_durations)
        
        if len(gap_durations) > 1:
            stdev_gap = statistics.stdev(gap_durations)
        else:
            stdev_gap = 0
        
        # Detect anomalous gaps (> sensitivity * stdev)
        for gap_info in gaps:
            duration = gap_info['duration']
            
            if stdev_gap > 0:
                z_score = (duration - mean_gap) / stdev_gap
                
                if z_score > self.sensitivity:
                    anomaly = GapAnomaly(
                        gap_duration=timedelta(seconds=duration),
                        start_event=gap_info['start_event'],
                        end_event=gap_info['end_event'],
                        expected_duration=timedelta(seconds=mean_gap),
                        statistical_significance=z_score,
                        forensic_impact=self._assess_gap_impact(duration, mean_gap)
                    )
                    anomalies.append(anomaly)
        
        logger.debug(f"Found {len(anomalies)} gap anomalies")
        return anomalies
    
    def _assess_gap_impact(self, actual_duration: float, expected_duration: float) -> str:
        """Assess forensic impact of a gap anomaly."""
        ratio = actual_duration / max(expected_duration, 1)
        
        if ratio > 5:
            return "CRITICAL: Extended silence period may indicate document concealment or missing records"
        elif ratio > 3:
            return "HIGH: Significant gap suggests potential reporting delay or missing documentation"
        elif ratio > 2:
            return "MEDIUM: Notable gap warrants investigation for missing information"
        else:
            return "LOW: Minor deviation from expected pattern"
    
    async def _detect_cluster_anomalies(self, events: List[any]) -> List[ClusterAnomaly]:
        """Detect unusual clustering of events."""
        anomalies = []
        
        if len(events) < 10:
            return anomalies
        
        # Define sliding window for density calculation
        window_size = timedelta(days=7)  # 1 week windows
        
        # Calculate baseline density (events per day)
        total_duration = (events[-1].timestamp - events[0].timestamp).days
        baseline_density = len(events) / max(total_duration, 1)
        
        # Slide window through timeline
        i = 0
        while i < len(events):
            window_start = events[i].timestamp
            window_end = window_start + window_size
            
            # Count events in window
            events_in_window = [
                e for e in events
                if window_start <= e.timestamp < window_end
            ]
            
            window_density = len(events_in_window) / 7.0  # events per day
            
            # Check if density is significantly higher than baseline
            if window_density > baseline_density * 3:  # 3x baseline
                significance = window_density / max(baseline_density, 0.01)
                
                anomaly = ClusterAnomaly(
                    cluster_start=window_start,
                    cluster_end=window_end,
                    events_in_cluster=events_in_window,
                    cluster_density=window_density,
                    baseline_density=baseline_density,
                    significance_score=significance,
                    forensic_impact=self._assess_cluster_impact(significance, len(events_in_window))
                )
                anomalies.append(anomaly)
                
                # Skip past this cluster
                i += len(events_in_window)
            else:
                i += 1
        
        logger.debug(f"Found {len(anomalies)} cluster anomalies")
        return anomalies
    
    def _assess_cluster_impact(self, significance: float, event_count: int) -> str:
        """Assess forensic impact of clustering."""
        if significance > 5 and event_count > 10:
            return "CRITICAL: Extreme event clustering suggests document dumping or rushed transactions"
        elif significance > 3:
            return "HIGH: Significant clustering may indicate coordinated activities or retroactive documentation"
        elif significance > 2:
            return "MEDIUM: Notable clustering warrants review for legitimacy"
        else:
            return "LOW: Minor clustering variation"
    
    async def _detect_pattern_breaks(self, events: List[any]) -> List[PatternBreak]:
        """Detect breaks in regular patterns."""
        anomalies = []
        
        # Group by event type
        by_type: Dict[str, List[any]] = defaultdict(list)
        for event in events:
            if hasattr(event, 'event_type'):
                event_type = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
                by_type[event_type].append(event)
        
        # Check each event type for pattern breaks
        for event_type, type_events in by_type.items():
            if len(type_events) < 4:
                continue
            
            # Sort by timestamp
            type_events.sort(key=lambda e: e.timestamp)
            
            # Calculate intervals
            intervals = [
                (type_events[i + 1].timestamp - type_events[i].timestamp).days
                for i in range(len(type_events) - 1)
            ]
            
            if not intervals:
                continue
            
            # Detect pattern breaks
            mean_interval = statistics.mean(intervals)
            if len(intervals) > 1:
                stdev_interval = statistics.stdev(intervals)
            else:
                stdev_interval = 0
            
            for i, interval in enumerate(intervals):
                if stdev_interval > 0:
                    z_score = abs(interval - mean_interval) / stdev_interval
                    
                    if z_score > self.sensitivity:
                        anomaly = PatternBreak(
                            break_point=type_events[i + 1].timestamp,
                            pattern_type=f"{event_type}_interval",
                            expected_pattern=f"~{mean_interval:.0f} days",
                            actual_pattern=f"{interval} days",
                            deviation_magnitude=z_score,
                            forensic_impact=self._assess_pattern_break_impact(event_type, z_score, interval, mean_interval)
                        )
                        anomalies.append(anomaly)
        
        logger.debug(f"Found {len(anomalies)} pattern breaks")
        return anomalies
    
    def _assess_pattern_break_impact(
        self, 
        event_type: str, 
        z_score: float, 
        actual: float, 
        expected: float
    ) -> str:
        """Assess forensic impact of pattern break."""
        if 'filing' in event_type.lower():
            if actual > expected * 1.5:
                return "CRITICAL: Delayed filing may violate regulatory deadlines"
            elif actual < expected * 0.5:
                return "MEDIUM: Accelerated filing schedule may indicate urgency or crisis"
        
        if z_score > 3:
            return f"HIGH: Significant deviation from {event_type} pattern requires investigation"
        elif z_score > 2:
            return f"MEDIUM: Notable {event_type} pattern irregularity"
        else:
            return f"LOW: Minor {event_type} pattern variation"
    
    async def _detect_frequency_changes(self, events: List[any]) -> List[Dict[str, Any]]:
        """Detect changes in event frequency over time."""
        changes = []
        
        if len(events) < 20:
            return changes
        
        # Divide timeline into periods
        start_date = min(e.timestamp for e in events)
        end_date = max(e.timestamp for e in events)
        total_days = (end_date - start_date).days
        
        if total_days < 90:  # Less than 3 months
            return changes
        
        # Split into quarters
        period_days = total_days // 4
        periods = []
        
        for i in range(4):
            period_start = start_date + timedelta(days=i * period_days)
            period_end = start_date + timedelta(days=(i + 1) * period_days)
            
            period_events = [
                e for e in events
                if period_start <= e.timestamp < period_end
            ]
            
            periods.append({
                'start': period_start,
                'end': period_end,
                'count': len(period_events),
                'frequency': len(period_events) / period_days
            })
        
        # Detect significant frequency changes between periods
        for i in range(len(periods) - 1):
            freq1 = periods[i]['frequency']
            freq2 = periods[i + 1]['frequency']
            
            if freq1 > 0:
                change_ratio = freq2 / freq1
                
                # Significant increase or decrease
                if change_ratio > 2.0 or change_ratio < 0.5:
                    change = {
                        'period1': periods[i],
                        'period2': periods[i + 1],
                        'change_ratio': change_ratio,
                        'direction': 'increase' if change_ratio > 1 else 'decrease',
                        'significance': abs(change_ratio - 1.0),
                        'forensic_impact': self._assess_frequency_change_impact(change_ratio)
                    }
                    changes.append(change)
        
        logger.debug(f"Found {len(changes)} frequency changes")
        return changes
    
    def _assess_frequency_change_impact(self, ratio: float) -> str:
        """Assess forensic impact of frequency change."""
        if ratio > 3.0:
            return "HIGH: Dramatic increase in activity may indicate crisis response or irregular activity"
        elif ratio < 0.33:
            return "HIGH: Significant decrease may indicate operational problems or concealment"
        elif ratio > 2.0 or ratio < 0.5:
            return "MEDIUM: Notable frequency change warrants investigation"
        else:
            return "LOW: Minor frequency variation"
    
    def calculate_timeline_statistics(self, events: List[any]) -> Dict[str, Any]:
        """Calculate statistical summary of timeline."""
        if not events:
            return {
                'total_events': 0,
                'date_range': None,
                'mean_gap': None,
                'median_gap': None,
                'stdev_gap': None
            }
        
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # Calculate gaps
        gaps = [
            (sorted_events[i + 1].timestamp - sorted_events[i].timestamp).total_seconds()
            for i in range(len(sorted_events) - 1)
        ]
        
        stats = {
            'total_events': len(events),
            'date_range': (sorted_events[0].timestamp, sorted_events[-1].timestamp),
            'total_duration_days': (sorted_events[-1].timestamp - sorted_events[0].timestamp).days
        }
        
        if gaps:
            stats.update({
                'mean_gap_days': statistics.mean(gaps) / 86400,
                'median_gap_days': statistics.median(gaps) / 86400,
                'min_gap_days': min(gaps) / 86400,
                'max_gap_days': max(gaps) / 86400,
                'stdev_gap_days': statistics.stdev(gaps) / 86400 if len(gaps) > 1 else 0
            })
        
        return stats

