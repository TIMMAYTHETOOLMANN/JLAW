"""
Forensic Timeline Reconstructor
Reconstructs complete forensic timelines with contradiction detection.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class TimelineResolution(Enum):
    """Timeline granularity levels."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class EventType(Enum):
    """Types of forensic events."""
    FILING = "filing"
    TRANSACTION = "transaction"
    STATEMENT = "statement"
    DISCLOSURE = "disclosure"
    MEETING = "meeting"
    COMMUNICATION = "communication"
    FINANCIAL_EVENT = "financial_event"
    LEGAL_EVENT = "legal_event"
    REGULATORY_EVENT = "regulatory_event"


class ContradictionType(Enum):
    """Types of temporal contradictions."""
    TEMPORAL_LOGIC_VIOLATION = "temporal_logic_violation"
    CONFLICTING_FACTS = "conflicting_facts"
    IMPOSSIBLE_SEQUENCE = "impossible_sequence"
    TIMELINE_INCONSISTENCY = "timeline_inconsistency"
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"


class SeverityLevel(Enum):
    """Severity levels for contradictions."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


@dataclass
class TemporalEvent:
    """A single event in the forensic timeline."""
    id: str
    event_type: EventType
    timestamp: datetime
    description: str
    source_document: str
    source_page: Optional[int]
    entities_involved: List[str]
    financial_impact: Optional[Dict[str, float]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    extracted_text: Optional[str] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, TemporalEvent):
            return False
        return self.id == other.id


@dataclass
class TemporalContradiction:
    """A detected contradiction between events."""
    contradiction_type: ContradictionType
    event1: TemporalEvent
    event2: TemporalEvent
    description: str
    severity: SeverityLevel
    forensic_significance: str
    time_delta: timedelta
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class TemporalAnomaly:
    """An anomaly detected in the timeline."""
    anomaly_type: str
    description: str
    severity: SeverityLevel
    events_involved: List[TemporalEvent]
    statistical_significance: float
    expected_pattern: str
    actual_pattern: str
    forensic_implications: str


@dataclass
class NarrativeSequence:
    """A narrative sequence of related events."""
    title: str
    events: List[TemporalEvent]
    start_date: datetime
    end_date: datetime
    key_actors: List[str]
    narrative_summary: str
    critical_moments: List[TemporalEvent]
    outcome: Optional[str] = None


@dataclass
class CriticalPeriod:
    """A critical time period identified in the timeline."""
    start_date: datetime
    end_date: datetime
    description: str
    events_count: int
    contradictions_count: int
    anomalies_count: int
    risk_score: float
    key_events: List[TemporalEvent]


@dataclass
class ForensicTimeline:
    """Complete forensic timeline analysis result."""
    events: List[TemporalEvent]
    contradictions: List[TemporalContradiction]
    anomalies: List[TemporalAnomaly]
    correlations: List[Any]  # Will be EventCorrelation
    narratives: List[NarrativeSequence]
    critical_periods: List[CriticalPeriod]
    summary: Dict[str, Any]
    timeline_integrity_score: float
    total_events: int
    date_range: Tuple[datetime, datetime]
    resolution: TimelineResolution


class ForensicTimelineReconstructor:
    """
    Advanced forensic timeline reconstruction engine.
    
    Reconstructs complete timelines from multiple document sources,
    detects contradictions, identifies anomalies, and builds narrative sequences.
    """
    
    def __init__(self):
        """Initialize the timeline reconstructor."""
        self.temporal_parser = None  # Will be injected
        self.contradiction_detector = None
        self.anomaly_detector = None
        logger.info("ForensicTimelineReconstructor initialized")
    
    async def reconstruct_timeline(
        self,
        documents: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> ForensicTimeline:
        """
        Reconstruct complete forensic timeline from multiple sources.
        
        Args:
            documents: List of document data to analyze
            options: Configuration options
                - resolution: TimelineResolution (default: day)
                - detect_anomalies: bool (default: True)
                - correlate_events: bool (default: True)
                - min_confidence: float (default: 0.5)
        
        Returns:
            ForensicTimeline with complete analysis
        """
        options = options or {}
        resolution = options.get('resolution', TimelineResolution.DAY)
        detect_anomalies = options.get('detect_anomalies', True)
        correlate_events = options.get('correlate_events', True)
        min_confidence = options.get('min_confidence', 0.5)
        
        logger.info(f"Reconstructing timeline from {len(documents)} documents...")
        
        # Step 1: Extract all temporal events
        events = await self._extract_all_events(documents, min_confidence)
        logger.info(f"Extracted {len(events)} temporal events")
        
        # Step 2: Normalize and sort timeline
        normalized_timeline = self._normalize_timeline(events, resolution)
        logger.info(f"Normalized timeline to {resolution.value} resolution")
        
        # Step 3: Detect temporal contradictions
        contradictions = await self._detect_temporal_contradictions(normalized_timeline)
        logger.info(f"Detected {len(contradictions)} contradictions")
        
        # Step 4: Identify anomalous patterns
        anomalies = []
        if detect_anomalies:
            anomalies = await self._detect_temporal_anomalies(normalized_timeline)
            logger.info(f"Detected {len(anomalies)} anomalies")
        
        # Step 5: Correlate related events (placeholder for now)
        correlations = []
        if correlate_events:
            correlations = await self._correlate_events(normalized_timeline)
            logger.info(f"Found {len(correlations)} correlations")
        
        # Step 6: Build narrative sequences
        narratives = self._build_narrative_sequences(normalized_timeline, contradictions)
        logger.info(f"Built {len(narratives)} narrative sequences")
        
        # Step 7: Identify critical periods
        critical_periods = self._identify_critical_periods(
            normalized_timeline, contradictions, anomalies
        )
        logger.info(f"Identified {len(critical_periods)} critical periods")
        
        # Step 8: Generate summary
        summary = self._generate_timeline_summary(
            normalized_timeline, contradictions, anomalies, narratives
        )
        
        # Calculate timeline integrity score
        integrity_score = self._calculate_integrity_score(
            len(events), len(contradictions), len(anomalies)
        )
        
        date_range = (
            min(e.timestamp for e in events),
            max(e.timestamp for e in events)
        ) if events else (datetime.now(timezone.utc), datetime.now(timezone.utc))
        
        return ForensicTimeline(
            events=normalized_timeline,
            contradictions=contradictions,
            anomalies=anomalies,
            correlations=correlations,
            narratives=narratives,
            critical_periods=critical_periods,
            summary=summary,
            timeline_integrity_score=integrity_score,
            total_events=len(events),
            date_range=date_range,
            resolution=resolution
        )
    
    async def _extract_all_events(
        self, 
        documents: List[Dict[str, Any]], 
        min_confidence: float
    ) -> List[TemporalEvent]:
        """Extract all temporal events from documents."""
        all_events = []
        event_id_counter = 0
        
        for doc in documents:
            doc_id = doc.get('id', f"doc_{len(all_events)}")
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # Extract dates and events from content
            extracted_events = self._extract_events_from_content(
                content, doc_id, metadata
            )
            
            # Filter by confidence
            filtered_events = [
                e for e in extracted_events if e.confidence >= min_confidence
            ]
            
            # Assign unique IDs
            for event in filtered_events:
                event.id = f"event_{event_id_counter}"
                event_id_counter += 1
            
            all_events.extend(filtered_events)
        
        # Sort by timestamp
        all_events.sort(key=lambda e: e.timestamp)
        
        return all_events
    
    def _extract_events_from_content(
        self, 
        content: str, 
        doc_id: str, 
        metadata: Dict[str, Any]
    ) -> List[TemporalEvent]:
        """Extract temporal events from document content."""
        events = []
        
        # Simple keyword-based extraction (can be enhanced with NLP)
        keywords = {
            'filing': EventType.FILING,
            'filed': EventType.FILING,
            'transaction': EventType.TRANSACTION,
            'purchase': EventType.TRANSACTION,
            'sale': EventType.TRANSACTION,
            'meeting': EventType.MEETING,
            'statement': EventType.STATEMENT,
            'disclosed': EventType.DISCLOSURE,
            'announced': EventType.DISCLOSURE
        }
        
        # Look for date patterns in content (simplified)
        import re
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b'
        dates = re.findall(date_pattern, content)
        
        for date_str in dates:
            try:
                date_obj = datetime.strptime(date_str, '%B %d, %Y')
                date_obj = date_obj.replace(tzinfo=timezone.utc)
                
                # Find context around date
                date_pos = content.find(date_str)
                context_start = max(0, date_pos - 100)
                context_end = min(len(content), date_pos + 100)
                context = content[context_start:context_end]
                
                # Determine event type from context
                event_type = EventType.STATEMENT
                for keyword, etype in keywords.items():
                    if keyword in context.lower():
                        event_type = etype
                        break
                
                event = TemporalEvent(
                    id=f"temp_{len(events)}",
                    event_type=event_type,
                    timestamp=date_obj,
                    description=context.strip(),
                    source_document=doc_id,
                    source_page=metadata.get('page'),
                    entities_involved=[],
                    financial_impact=None,
                    metadata=metadata,
                    confidence=0.7,
                    extracted_text=context
                )
                events.append(event)
            except ValueError:
                continue
        
        return events
    
    def _normalize_timeline(
        self, 
        events: List[TemporalEvent], 
        resolution: TimelineResolution
    ) -> List[TemporalEvent]:
        """Normalize timeline to specified resolution."""
        if resolution == TimelineResolution.DAY:
            # Already at day resolution
            return events
        
        # Group events by resolution period
        grouped: Dict[str, List[TemporalEvent]] = defaultdict(list)
        
        for event in events:
            if resolution == TimelineResolution.WEEK:
                # Get start of week
                start_of_week = event.timestamp - timedelta(days=event.timestamp.weekday())
                key = start_of_week.strftime('%Y-W%W')
            elif resolution == TimelineResolution.MONTH:
                key = event.timestamp.strftime('%Y-%m')
            elif resolution == TimelineResolution.QUARTER:
                quarter = (event.timestamp.month - 1) // 3 + 1
                key = f"{event.timestamp.year}-Q{quarter}"
            elif resolution == TimelineResolution.YEAR:
                key = event.timestamp.strftime('%Y')
            else:
                key = event.timestamp.isoformat()
            
            grouped[key].append(event)
        
        # For now, just return original events
        # In production, would merge similar events within same period
        return events
    
    async def _detect_temporal_contradictions(
        self, 
        timeline: List[TemporalEvent]
    ) -> List[TemporalContradiction]:
        """Detect contradictions in timeline."""
        contradictions = []
        
        # Check for impossible sequences
        for i in range(len(timeline) - 1):
            for j in range(i + 1, min(i + 100, len(timeline))):  # Check next 100 events
                event1 = timeline[i]
                event2 = timeline[j]
                
                # Check for temporal logic violations
                violation = self._check_temporal_logic_violation(event1, event2)
                if violation:
                    contradictions.append(violation)
                
                # Check for conflicting facts
                conflict = self._check_conflicting_facts(event1, event2)
                if conflict:
                    contradictions.append(conflict)
        
        return contradictions
    
    def _check_temporal_logic_violation(
        self, 
        event1: TemporalEvent, 
        event2: TemporalEvent
    ) -> Optional[TemporalContradiction]:
        """Check if two events violate temporal logic."""
        # Example: A filing cannot occur before the period it describes
        if event1.event_type == EventType.FILING and event2.event_type == EventType.TRANSACTION:
            if event1.timestamp < event2.timestamp:
                # Filing refers to a transaction that happened after filing
                if 'prior' in event1.description.lower() or 'previous' in event1.description.lower():
                    return TemporalContradiction(
                        contradiction_type=ContradictionType.TEMPORAL_LOGIC_VIOLATION,
                        event1=event1,
                        event2=event2,
                        description=f"Filing at {event1.timestamp} references transaction at {event2.timestamp}",
                        severity=SeverityLevel.MEDIUM,
                        forensic_significance="Timeline inconsistency may indicate backdating or misdating",
                        time_delta=event2.timestamp - event1.timestamp,
                        resolution_suggestions=[
                            "Verify filing dates",
                            "Check for amended filings",
                            "Review transaction dates"
                        ]
                    )
        
        return None
    
    def _check_conflicting_facts(
        self, 
        event1: TemporalEvent, 
        event2: TemporalEvent
    ) -> Optional[TemporalContradiction]:
        """Check for conflicting facts at similar times."""
        # Check if events are close in time
        time_diff = abs((event2.timestamp - event1.timestamp).total_seconds())
        
        if time_diff < 86400:  # Within 24 hours
            # Check for contradictory financial impacts
            if event1.financial_impact and event2.financial_impact:
                # Example: Check for contradictory revenue claims
                if 'revenue' in event1.financial_impact and 'revenue' in event2.financial_impact:
                    rev1 = event1.financial_impact['revenue']
                    rev2 = event2.financial_impact['revenue']
                    
                    # If revenues differ by more than 10%
                    if abs(rev1 - rev2) / max(rev1, rev2) > 0.1:
                        return TemporalContradiction(
                            contradiction_type=ContradictionType.CONFLICTING_FACTS,
                            event1=event1,
                            event2=event2,
                            description=f"Conflicting revenue figures: {rev1} vs {rev2}",
                            severity=SeverityLevel.HIGH,
                            forensic_significance="Material discrepancy in financial reporting",
                            time_delta=timedelta(seconds=time_diff),
                            resolution_suggestions=[
                                "Verify source documents",
                                "Check for restatements",
                                "Investigate accounting irregularities"
                            ]
                        )
        
        return None
    
    async def _detect_temporal_anomalies(
        self, 
        timeline: List[TemporalEvent]
    ) -> List[TemporalAnomaly]:
        """Detect anomalies in timeline."""
        anomalies = []
        
        # Detect unusual gaps
        gaps = self._detect_unusual_gaps(timeline)
        anomalies.extend(gaps)
        
        # Detect event clustering
        clusters = self._detect_event_clustering(timeline)
        anomalies.extend(clusters)
        
        # Detect pattern breaks
        pattern_breaks = self._detect_pattern_breaks(timeline)
        anomalies.extend(pattern_breaks)
        
        return anomalies
    
    def _detect_unusual_gaps(self, timeline: List[TemporalEvent]) -> List[TemporalAnomaly]:
        """Detect unusual gaps between events."""
        anomalies = []
        
        if len(timeline) < 2:
            return anomalies
        
        # Calculate time gaps between consecutive events
        gaps = []
        for i in range(len(timeline) - 1):
            gap = (timeline[i + 1].timestamp - timeline[i].timestamp).total_seconds()
            gaps.append(gap)
        
        if not gaps:
            return anomalies
        
        # Statistical analysis
        mean_gap = statistics.mean(gaps)
        stdev_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
        
        # Identify gaps that are unusually large (> 2 standard deviations)
        for i, gap in enumerate(gaps):
            if stdev_gap > 0 and gap > mean_gap + 2 * stdev_gap:
                anomaly = TemporalAnomaly(
                    anomaly_type="unusual_gap",
                    description=f"Unusual {gap / 86400:.1f} day gap between events",
                    severity=SeverityLevel.MEDIUM,
                    events_involved=[timeline[i], timeline[i + 1]],
                    statistical_significance=(gap - mean_gap) / stdev_gap if stdev_gap > 0 else 0,
                    expected_pattern=f"Average gap: {mean_gap / 86400:.1f} days",
                    actual_pattern=f"Actual gap: {gap / 86400:.1f} days",
                    forensic_implications="Missing documentation or intentional concealment period"
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_event_clustering(self, timeline: List[TemporalEvent]) -> List[TemporalAnomaly]:
        """Detect unusual clustering of events."""
        anomalies = []
        
        if len(timeline) < 10:
            return anomalies
        
        # Look for periods with unusually high event density
        window_size = timedelta(days=7)
        
        for i in range(len(timeline)):
            window_start = timeline[i].timestamp
            window_end = window_start + window_size
            
            # Count events in window
            events_in_window = [
                e for e in timeline 
                if window_start <= e.timestamp < window_end
            ]
            
            # If more than 20% of all events in a 7-day window
            if len(events_in_window) > len(timeline) * 0.2:
                anomaly = TemporalAnomaly(
                    anomaly_type="event_clustering",
                    description=f"{len(events_in_window)} events clustered in 7-day window",
                    severity=SeverityLevel.MEDIUM,
                    events_involved=events_in_window[:5],  # First 5 for brevity
                    statistical_significance=len(events_in_window) / len(timeline),
                    expected_pattern="Events distributed evenly over time",
                    actual_pattern=f"{len(events_in_window)} events in single week",
                    forensic_implications="Potential rushed transactions or document dumping"
                )
                anomalies.append(anomaly)
                break  # Only report first significant cluster
        
        return anomalies
    
    def _detect_pattern_breaks(self, timeline: List[TemporalEvent]) -> List[TemporalAnomaly]:
        """Detect breaks in expected patterns."""
        anomalies = []
        
        # Group by event type
        by_type: Dict[EventType, List[TemporalEvent]] = defaultdict(list)
        for event in timeline:
            by_type[event.event_type].append(event)
        
        # Check for pattern breaks in filings (should be regular)
        if EventType.FILING in by_type:
            filing_events = sorted(by_type[EventType.FILING], key=lambda e: e.timestamp)
            
            if len(filing_events) >= 4:
                # Calculate typical interval between filings
                intervals = [
                    (filing_events[i + 1].timestamp - filing_events[i].timestamp).days
                    for i in range(len(filing_events) - 1)
                ]
                
                if intervals:
                    mean_interval = statistics.mean(intervals)
                    
                    # Check for missing filings (interval > 1.5x typical)
                    for i, interval in enumerate(intervals):
                        if interval > mean_interval * 1.5:
                            anomaly = TemporalAnomaly(
                                anomaly_type="pattern_break",
                                description=f"Filing pattern break: {interval} days vs typical {mean_interval:.0f} days",
                                severity=SeverityLevel.HIGH,
                                events_involved=[filing_events[i], filing_events[i + 1]],
                                statistical_significance=interval / mean_interval,
                                expected_pattern=f"Filing every {mean_interval:.0f} days",
                                actual_pattern=f"Gap of {interval} days",
                                forensic_implications="Missed deadline, delayed reporting, or concealment"
                            )
                            anomalies.append(anomaly)
        
        return anomalies
    
    async def _correlate_events(self, timeline: List[TemporalEvent]) -> List[Any]:
        """Correlate related events (placeholder)."""
        # Will be implemented with EventCorrelator
        return []
    
    def _build_narrative_sequences(
        self, 
        timeline: List[TemporalEvent],
        contradictions: List[TemporalContradiction]
    ) -> List[NarrativeSequence]:
        """Build narrative sequences from timeline."""
        narratives = []
        
        # Group events by entity
        by_entity: Dict[str, List[TemporalEvent]] = defaultdict(list)
        for event in timeline:
            for entity in event.entities_involved:
                by_entity[entity].append(event)
        
        # Create narrative for each entity with multiple events
        for entity, events in by_entity.items():
            if len(events) >= 3:
                events_sorted = sorted(events, key=lambda e: e.timestamp)
                
                # Identify critical moments (events with contradictions)
                critical = [
                    e for e in events_sorted
                    if any(c.event1 == e or c.event2 == e for c in contradictions)
                ]
                
                narrative = NarrativeSequence(
                    title=f"Timeline for {entity}",
                    events=events_sorted,
                    start_date=events_sorted[0].timestamp,
                    end_date=events_sorted[-1].timestamp,
                    key_actors=[entity],
                    narrative_summary=self._generate_narrative_summary(events_sorted),
                    critical_moments=critical
                )
                narratives.append(narrative)
        
        return narratives
    
    def _generate_narrative_summary(self, events: List[TemporalEvent]) -> str:
        """Generate a summary of the narrative."""
        if not events:
            return "No events"
        
        duration = (events[-1].timestamp - events[0].timestamp).days
        event_types = defaultdict(int)
        for event in events:
            event_types[event.event_type.value] += 1
        
        type_summary = ", ".join(f"{count} {type_}" for type_, count in event_types.items())
        
        return f"Sequence of {len(events)} events over {duration} days: {type_summary}"
    
    def _identify_critical_periods(
        self,
        timeline: List[TemporalEvent],
        contradictions: List[TemporalContradiction],
        anomalies: List[TemporalAnomaly]
    ) -> List[CriticalPeriod]:
        """Identify critical time periods."""
        critical_periods = []
        
        # Define period windows (e.g., quarters)
        if not timeline:
            return critical_periods
        
        start_date = min(e.timestamp for e in timeline)
        end_date = max(e.timestamp for e in timeline)
        
        # Create quarterly periods
        current = start_date
        while current < end_date:
            period_end = current + timedelta(days=90)
            
            # Count events, contradictions, anomalies in period
            period_events = [
                e for e in timeline 
                if current <= e.timestamp < period_end
            ]
            
            period_contradictions = [
                c for c in contradictions
                if current <= c.event1.timestamp < period_end or
                   current <= c.event2.timestamp < period_end
            ]
            
            period_anomalies = [
                a for a in anomalies
                if any(current <= e.timestamp < period_end for e in a.events_involved)
            ]
            
            # Calculate risk score
            risk_score = (
                len(period_contradictions) * 10 +
                len(period_anomalies) * 5 +
                len(period_events) * 0.1
            ) / 100
            
            if risk_score > 0.3:  # Threshold for "critical"
                critical_period = CriticalPeriod(
                    start_date=current,
                    end_date=period_end,
                    description=f"High-risk period with {len(period_contradictions)} contradictions",
                    events_count=len(period_events),
                    contradictions_count=len(period_contradictions),
                    anomalies_count=len(period_anomalies),
                    risk_score=min(risk_score, 1.0),
                    key_events=period_events[:10]  # Top 10
                )
                critical_periods.append(critical_period)
            
            current = period_end
        
        return critical_periods
    
    def _generate_timeline_summary(
        self,
        timeline: List[TemporalEvent],
        contradictions: List[TemporalContradiction],
        anomalies: List[TemporalAnomaly],
        narratives: List[NarrativeSequence]
    ) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not timeline:
            return {
                'total_events': 0,
                'date_range': None,
                'event_types': {},
                'contradictions': 0,
                'anomalies': 0,
                'narratives': 0
            }
        
        event_types = defaultdict(int)
        for event in timeline:
            event_types[event.event_type.value] += 1
        
        return {
            'total_events': len(timeline),
            'date_range': (
                min(e.timestamp for e in timeline).isoformat(),
                max(e.timestamp for e in timeline).isoformat()
            ),
            'duration_days': (max(e.timestamp for e in timeline) - 
                            min(e.timestamp for e in timeline)).days,
            'event_types': dict(event_types),
            'contradictions': len(contradictions),
            'critical_contradictions': len([c for c in contradictions 
                                           if c.severity == SeverityLevel.CRITICAL]),
            'anomalies': len(anomalies),
            'narratives': len(narratives),
            'average_events_per_day': len(timeline) / max(1, (
                max(e.timestamp for e in timeline) - 
                min(e.timestamp for e in timeline)
            ).days)
        }
    
    def _calculate_integrity_score(
        self, 
        total_events: int, 
        contradictions: int, 
        anomalies: int
    ) -> float:
        """Calculate timeline integrity score (0-1, higher is better)."""
        if total_events == 0:
            return 0.0
        
        # Penalize contradictions and anomalies
        contradiction_penalty = min(contradictions * 0.1, 0.5)
        anomaly_penalty = min(anomalies * 0.05, 0.3)
        
        score = 1.0 - contradiction_penalty - anomaly_penalty
        return max(0.0, min(1.0, score))

