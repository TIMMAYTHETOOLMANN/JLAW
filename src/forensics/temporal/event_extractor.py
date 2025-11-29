"""Event Extractor - Temporal Event Detection"""

import re
from typing import List, Dict, Any
from datetime import datetime


class EventExtractor:
    """Extracts temporal events from text"""
    
    def extract_events(self, text: str) -> List[Dict[str, Any]]:
        """Extract events with temporal markers"""
        events = []
        
        # Extract dates and associated text
        date_pattern = r'(Q[1-4]\s+\d{4}|\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})'
        
        for match in re.finditer(date_pattern, text, re.IGNORECASE):
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end]
            
            events.append({
                'date': match.group(0),
                'context': context,
                'position': match.start()
            })
        
        return events

