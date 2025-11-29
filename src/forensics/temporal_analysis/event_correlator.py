"""
Event Correlator
Correlates events across multiple timelines and identifies causal chains.
"""

import asyncio
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class EventCorrelation:
    """A correlation between two events."""
    source1: str
    source2: str
    event1: any  # TemporalEvent
    event2: any  # TemporalEvent
    correlation_type: str
    confidence: float
    temporal_offset: timedelta
    causal_chain: Optional[List[str]] = None
    explanation: str = ""


@dataclass
class CausalChain:
    """A sequence of causally related events."""
    chain_id: str
    events: List[any]  # List[TemporalEvent]
    confidence: float
    start_event: any  # TemporalEvent
    end_event: any  # TemporalEvent
    total_duration: timedelta
    description: str


class EventCorrelator:
    """
    Correlates events across multiple timelines.
    
    Identifies:
    - Concurrent events
    - Sequential patterns
    - Causal relationships
    - Cross-timeline dependencies
    """
    
    def __init__(self):
        """Initialize the event correlator."""
        logger.info("EventCorrelator initialized")
    
    async def correlate_across_timelines(
        self,
        timelines: Dict[str, List[any]]  # Dict[str, List[TemporalEvent]]
    ) -> List[EventCorrelation]:
        """
        Correlate events across multiple timelines.
        
        Args:
            timelines: Dictionary mapping source names to event lists
        
        Returns:
            List of event correlations
        """
        correlations = []
        
        # Iterate through timeline pairs
        timeline_names = list(timelines.keys())
        for i in range(len(timeline_names)):
            for j in range(i + 1, len(timeline_names)):
                source1 = timeline_names[i]
                source2 = timeline_names[j]
                timeline1 = timelines[source1]
                timeline2 = timelines[source2]
                
                # Find correlated events
                correlated = await self._find_correlated_events(
                    timeline1, timeline2
                )
                
                for pair in correlated:
                    correlation = EventCorrelation(
                        source1=source1,
                        source2=source2,
                        event1=pair['event1'],
                        event2=pair['event2'],
                        correlation_type=pair['type'],
                        confidence=pair['confidence'],
                        temporal_offset=self._calculate_offset(
                            pair['event1'], pair['event2']
                        ),
                        explanation=pair.get('explanation', '')
                    )
                    correlations.append(correlation)
        
        # Identify causal chains
        causal_chains = self._identify_causal_chains(correlations)
        
        # Add causal chain info to correlations
        for correlation in correlations:
            chain = self._find_chain_for_events(
                causal_chains,
                correlation.event1,
                correlation.event2
            )
            if chain:
                correlation.causal_chain = [e.id if hasattr(e, 'id') else str(e) for e in chain.events]
        
        logger.info(f"Found {len(correlations)} correlations across timelines")
        return correlations
    
    async def _find_correlated_events(
        self,
        timeline1: List[any],
        timeline2: List[any]
    ) -> List[Dict]:
        """Find correlated events between two timelines."""
        correlated = []
        
        # Time window for correlation (e.g., events within 7 days)
        time_window = timedelta(days=7)
        
        for event1 in timeline1:
            for event2 in timeline2:
                # Check temporal proximity
                time_diff = abs(event1.timestamp - event2.timestamp)
                
                if time_diff <= time_window:
                    # Calculate correlation type and confidence
                    correlation = self._analyze_correlation(event1, event2, time_diff)
                    
                    if correlation:
                        correlated.append(correlation)
        
        return correlated
    
    def _analyze_correlation(
        self,
        event1: any,
        event2: any,
        time_diff: timedelta
    ) -> Optional[Dict]:
        """Analyze the correlation between two events."""
        # Check for entity overlap
        entities1 = set(event1.entities_involved if hasattr(event1, 'entities_involved') else [])
        entities2 = set(event2.entities_involved if hasattr(event2, 'entities_involved') else [])
        entity_overlap = entities1 & entities2
        
        # Determine correlation type
        correlation_type = None
        confidence = 0.0
        explanation = ""
        
        # Same entity involved
        if entity_overlap:
            confidence += 0.4
            
            # Events very close in time (same day)
            if time_diff.total_seconds() < 86400:
                correlation_type = 'concurrent'
                confidence += 0.3
                explanation = f"Concurrent events involving {', '.join(entity_overlap)}"
            
            # Sequential events (event1 before event2)
            elif event1.timestamp < event2.timestamp:
                correlation_type = 'sequential'
                confidence += 0.2
                explanation = f"Sequential events involving {', '.join(entity_overlap)}"
                
                # Check for potential causality
                if self._is_potential_cause(event1, event2):
                    correlation_type = 'potential_cause'
                    confidence += 0.3
                    explanation = f"Potential causal relationship: {event1.event_type.value} -> {event2.event_type.value}"
        
        # Similar event types close in time
        elif hasattr(event1, 'event_type') and hasattr(event2, 'event_type'):
            if event1.event_type == event2.event_type and time_diff.total_seconds() < 86400:
                correlation_type = 'similar_timing'
                confidence = 0.5
                explanation = f"Similar {event1.event_type.value} events on same day"
        
        # Return correlation if confidence threshold met
        if confidence >= 0.5:
            return {
                'event1': event1,
                'event2': event2,
                'type': correlation_type,
                'confidence': confidence,
                'explanation': explanation
            }
        
        return None
    
    def _is_potential_cause(self, event1: any, event2: any) -> bool:
        """Check if event1 could potentially cause event2."""
        # Simple heuristic: check event type sequences
        if not hasattr(event1, 'event_type') or not hasattr(event2, 'event_type'):
            return False
        
        # Known causal patterns
        causal_patterns = {
            ('MEETING', 'DISCLOSURE'),
            ('TRANSACTION', 'FILING'),
            ('STATEMENT', 'REGULATORY_EVENT'),
            ('DISCLOSURE', 'LEGAL_EVENT')
        }
        
        pattern = (event1.event_type.value, event2.event_type.value)
        return pattern in causal_patterns
    
    def _calculate_offset(self, event1: any, event2: any) -> timedelta:
        """Calculate time offset between events."""
        return event2.timestamp - event1.timestamp
    
    def _identify_causal_chains(
        self,
        correlations: List[EventCorrelation]
    ) -> List[CausalChain]:
        """Identify causal chains from correlations."""
        # Build directed graph of potential causality
        graph: Dict[str, Set[str]] = defaultdict(set)
        event_map: Dict[str, any] = {}
        
        for correlation in correlations:
            if correlation.correlation_type == 'potential_cause':
                event1_id = getattr(correlation.event1, 'id', str(correlation.event1))
                event2_id = getattr(correlation.event2, 'id', str(correlation.event2))
                
                graph[event1_id].add(event2_id)
                event_map[event1_id] = correlation.event1
                event_map[event2_id] = correlation.event2
        
        # Find chains using DFS
        chains = []
        visited = set()
        
        for start_id in graph.keys():
            if start_id not in visited:
                chain_ids = self._dfs_chain(start_id, graph, visited)
                
                if len(chain_ids) >= 3:  # Minimum chain length
                    chain_events = [event_map[eid] for eid in chain_ids if eid in event_map]
                    
                    if len(chain_events) >= 3:
                        chain = CausalChain(
                            chain_id=f"chain_{len(chains)}",
                            events=chain_events,
                            confidence=0.7,  # Could be calculated based on correlation confidences
                            start_event=chain_events[0],
                            end_event=chain_events[-1],
                            total_duration=chain_events[-1].timestamp - chain_events[0].timestamp,
                            description=self._describe_chain(chain_events)
                        )
                        chains.append(chain)
        
        logger.info(f"Identified {len(chains)} causal chains")
        return chains
    
    def _dfs_chain(
        self,
        start: str,
        graph: Dict[str, Set[str]],
        visited: Set[str]
    ) -> List[str]:
        """Depth-first search to find causal chains."""
        chain = [start]
        visited.add(start)
        
        if start in graph:
            # Follow the chain
            for next_node in graph[start]:
                if next_node not in visited:
                    rest_of_chain = self._dfs_chain(next_node, graph, visited)
                    if len(rest_of_chain) > len(chain) - 1:
                        chain = [start] + rest_of_chain
                        break
        
        return chain
    
    def _find_chain_for_events(
        self,
        chains: List[CausalChain],
        event1: any,
        event2: any
    ) -> Optional[CausalChain]:
        """Find a chain that includes both events."""
        event1_id = getattr(event1, 'id', str(event1))
        event2_id = getattr(event2, 'id', str(event2))
        
        for chain in chains:
            event_ids = [getattr(e, 'id', str(e)) for e in chain.events]
            if event1_id in event_ids and event2_id in event_ids:
                return chain
        
        return None
    
    def _describe_chain(self, events: List[any]) -> str:
        """Generate description of a causal chain."""
        if not events:
            return "Empty chain"
        
        event_types = [e.event_type.value if hasattr(e, 'event_type') else 'unknown' for e in events]
        return f"Chain of {len(events)} events: {' -> '.join(event_types)}"
    
    async def analyze_cross_timeline_patterns(
        self,
        timelines: Dict[str, List[any]]
    ) -> Dict[str, any]:
        """Analyze patterns across multiple timelines."""
        patterns = {
            'concurrent_events': [],
            'sequential_patterns': [],
            'causal_chains': [],
            'synchronization_points': []
        }
        
        # Find all correlations
        correlations = await self.correlate_across_timelines(timelines)
        
        # Group by type
        for correlation in correlations:
            if correlation.correlation_type == 'concurrent':
                patterns['concurrent_events'].append(correlation)
            elif correlation.correlation_type == 'sequential':
                patterns['sequential_patterns'].append(correlation)
            elif correlation.correlation_type == 'potential_cause':
                patterns['causal_chains'].append(correlation)
        
        # Find synchronization points (multiple timelines converge)
        sync_points = self._find_synchronization_points(timelines, correlations)
        patterns['synchronization_points'] = sync_points
        
        return patterns
    
    def _find_synchronization_points(
        self,
        timelines: Dict[str, List[any]],
        correlations: List[EventCorrelation]
    ) -> List[Dict[str, any]]:
        """Find points where multiple timelines synchronize."""
        sync_points = []
        
        # Group correlations by approximate time
        time_window = timedelta(days=1)
        time_groups: Dict[datetime, List[EventCorrelation]] = defaultdict(list)
        
        for correlation in correlations:
            time_key = correlation.event1.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            time_groups[time_key].append(correlation)
        
        # Identify sync points (3+ timelines correlating at same time)
        for time_key, group in time_groups.items():
            sources = set()
            for corr in group:
                sources.add(corr.source1)
                sources.add(corr.source2)
            
            if len(sources) >= 3:
                sync_point = {
                    'date': time_key,
                    'sources': list(sources),
                    'correlation_count': len(group),
                    'significance': 'High' if len(sources) >= 4 else 'Medium'
                }
                sync_points.append(sync_point)
        
        return sync_points

