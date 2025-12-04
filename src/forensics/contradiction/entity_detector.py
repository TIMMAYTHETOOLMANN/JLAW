"""Entity Detector for Contradiction Analysis"""

import re
from typing import List, Dict, Any


class EntityDetector:
    """Detects and extracts entities from statements"""
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text"""
        entities = []
        
        # Extract monetary amounts
        money_pattern = r'\$?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|M|B)?'
        for match in re.finditer(money_pattern, text, re.IGNORECASE):
            entities.append({
                'type': 'money',
                'value': match.group(0),
                'position': match.start()
            })
        
        # Extract dates
        date_pattern = r'Q[1-4]\s+\d{4}|\d{4}'
        for match in re.finditer(date_pattern, text):
            entities.append({
                'type': 'date',
                'value': match.group(0),
                'position': match.start()
            })
        
        return entities

