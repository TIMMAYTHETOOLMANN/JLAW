"""
DEF 14A Advisor Extractor
==========================

Automatically extracts advisor information from DEF 14A proxy statements:
- Legal advisors
- Auditors
- Compensation consultants
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class AdvisorInfo:
    """Extracted advisor information."""
    name: str
    advisor_type: str  # legal, auditor, compensation_consultant
    year: int
    context: str  # Text snippet where found
    confidence: float  # 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.advisor_type,
            "year": self.year,
            "context": self.context,
            "confidence": round(self.confidence, 2)
        }


class DEF14AAdvisorExtractor:
    """
    Extracts advisor information from DEF 14A proxy statements.
    
    Uses pattern matching and keyword detection to identify:
    - Law firms serving as legal counsel
    - Accounting firms serving as auditors
    - Compensation consulting firms
    """
    
    # Common law firm patterns
    LAW_FIRM_PATTERNS = [
        r'(\w+(?:,\s*\w+)*)\s+(?:LLP|LLC|P\.?C\.?|Attorneys|Law)',
        r'(\w+\s+&\s+\w+(?:\s+&\s+\w+)*)\s*,?\s*(?:a law firm|as legal counsel)',
    ]
    
    # Auditor keywords
    AUDITOR_KEYWORDS = [
        'independent auditor', 'independent registered public accounting firm',
        'external auditor', 'audit firm', 'independent accountant'
    ]
    
    # Big 4 accounting firms
    BIG_4_FIRMS = [
        'Deloitte', 'PwC', 'PricewaterhouseCoopers', 'Ernst & Young', 'EY',
        'KPMG'
    ]
    
    # Compensation consultant keywords
    COMP_CONSULTANT_KEYWORDS = [
        'compensation consultant', 'executive compensation', 'pay consultant',
        'compensation advisor', 'compensation committee consultant'
    ]
    
    def __init__(self):
        self.logger = logger
    
    def extract_advisors(
        self,
        def14a_text: str,
        year: int
    ) -> List[AdvisorInfo]:
        """
        Extract all advisors from DEF 14A text.
        
        Args:
            def14a_text: Full text of DEF 14A filing
            year: Filing year
        
        Returns:
            List of extracted advisors
        """
        advisors = []
        
        # Extract each type
        advisors.extend(self._extract_legal_advisors(def14a_text, year))
        advisors.extend(self._extract_auditors(def14a_text, year))
        advisors.extend(self._extract_comp_consultants(def14a_text, year))
        
        # Remove duplicates
        seen = set()
        unique_advisors = []
        for advisor in advisors:
            key = (advisor.name.lower(), advisor.advisor_type)
            if key not in seen:
                seen.add(key)
                unique_advisors.append(advisor)
        
        return unique_advisors
    
    def _extract_legal_advisors(
        self,
        text: str,
        year: int
    ) -> List[AdvisorInfo]:
        """Extract legal counsel/law firms."""
        advisors = []
        
        # Search for law firm patterns
        for pattern in self.LAW_FIRM_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                firm_name = match.group(1).strip()
                
                # Get context (surrounding text)
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end].replace('\n', ' ')
                
                # Calculate confidence based on context
                confidence = 0.5
                legal_keywords = ['legal counsel', 'law firm', 'attorney']
                for keyword in legal_keywords:
                    if keyword in context.lower():
                        confidence = min(1.0, confidence + 0.2)
                
                advisors.append(AdvisorInfo(
                    name=firm_name,
                    advisor_type='legal',
                    year=year,
                    context=context,
                    confidence=confidence
                ))
        
        return advisors
    
    def _extract_auditors(
        self,
        text: str,
        year: int
    ) -> List[AdvisorInfo]:
        """Extract auditing firms."""
        advisors = []
        
        # Search for Big 4 mentions
        for firm in self.BIG_4_FIRMS:
            pattern = re.compile(r'\b' + re.escape(firm) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(text)
            
            for match in matches:
                # Get context
                start = max(0, match.start() - 150)
                end = min(len(text), match.end() + 150)
                context = text[start:end].replace('\n', ' ')
                
                # Check if context suggests auditor role
                confidence = 0.3
                for keyword in self.AUDITOR_KEYWORDS:
                    if keyword in context.lower():
                        confidence = min(1.0, confidence + 0.3)
                        break
                
                # Only add if confidence is reasonable
                if confidence >= 0.5:
                    advisors.append(AdvisorInfo(
                        name=firm,
                        advisor_type='auditor',
                        year=year,
                        context=context,
                        confidence=confidence
                    ))
                    break  # Only one match per firm
        
        return advisors
    
    def _extract_comp_consultants(
        self,
        text: str,
        year: int
    ) -> List[AdvisorInfo]:
        """Extract compensation consultants."""
        advisors = []
        
        # Find sections mentioning compensation consultants
        for keyword in self.COMP_CONSULTANT_KEYWORDS:
            pattern = re.compile(
                r'(.{0,50})\s+' + re.escape(keyword),
                re.IGNORECASE
            )
            matches = pattern.finditer(text)
            
            for match in matches:
                # Extract potential firm name before keyword
                potential_name = match.group(1).strip()
                
                # Clean up the name
                # Look for capitalized words that might be a firm name
                words = potential_name.split()
                firm_name = ' '.join(w for w in words if w and w[0].isupper())
                
                if firm_name and len(firm_name) > 3:
                    # Get context
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].replace('\n', ' ')
                    
                    advisors.append(AdvisorInfo(
                        name=firm_name,
                        advisor_type='compensation_consultant',
                        year=year,
                        context=context,
                        confidence=0.6
                    ))
        
        return advisors
    
    def extract_from_multiple_filings(
        self,
        filings: List[Dict[str, Any]]
    ) -> Dict[int, List[AdvisorInfo]]:
        """
        Extract advisors from multiple DEF 14A filings.
        
        Args:
            filings: List of filing dicts with 'text' and 'year' keys
        
        Returns:
            Dictionary mapping year to list of advisors
        """
        results = {}
        
        for filing in filings:
            text = filing.get('text', '')
            year = filing.get('year', 0)
            
            if text and year:
                advisors = self.extract_advisors(text, year)
                results[year] = advisors
        
        return results
    
    def track_advisor_changes(
        self,
        advisors_by_year: Dict[int, List[AdvisorInfo]]
    ) -> List[Dict[str, Any]]:
        """
        Track changes in advisors across years.
        
        Args:
            advisors_by_year: Dictionary mapping year to advisors
        
        Returns:
            List of advisor change events
        """
        changes = []
        
        years = sorted(advisors_by_year.keys())
        
        for i in range(len(years) - 1):
            year1 = years[i]
            year2 = years[i + 1]
            
            advisors1 = {
                (a.name.lower(), a.advisor_type): a
                for a in advisors_by_year[year1]
            }
            advisors2 = {
                (a.name.lower(), a.advisor_type): a
                for a in advisors_by_year[year2]
            }
            
            # Find additions
            for key, advisor in advisors2.items():
                if key not in advisors1:
                    changes.append({
                        'type': 'addition',
                        'year': year2,
                        'advisor_name': advisor.name,
                        'advisor_type': advisor.advisor_type
                    })
            
            # Find removals
            for key, advisor in advisors1.items():
                if key not in advisors2:
                    changes.append({
                        'type': 'removal',
                        'year': year2,
                        'advisor_name': advisor.name,
                        'advisor_type': advisor.advisor_type
                    })
        
        return changes
