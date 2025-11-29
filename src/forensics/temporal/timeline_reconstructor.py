"""Timeline Reconstructor - Temporal Event Ordering"""

from typing import List, Dict, Any
from datetime import datetime


class TimelineReconstructor:
    """Reconstructs timelines from events"""
    
    def reconstruct(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reconstruct timeline from events"""
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', datetime.min))
        
        return {
            'events': sorted_events,
            'start_date': sorted_events[0]['timestamp'] if sorted_events else None,
            'end_date': sorted_events[-1]['timestamp'] if sorted_events else None,
            'event_count': len(sorted_events)
        }

