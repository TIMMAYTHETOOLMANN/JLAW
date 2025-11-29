"""
Temporal Parser
Extracts temporal information from text and documents.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class DateExtractionResult:
    """Result of date extraction from text."""
    date: datetime
    text: str
    context: str
    confidence: float
    date_type: str  # 'explicit', 'relative', 'inferred'
    span: tuple  # (start, end) positions in text


class TemporalExtractor:
    """Extracts temporal expressions from text."""
    
    def __init__(self):
        """Initialize temporal extractor."""
        # Date patterns
        self.date_patterns = [
            # Full dates
            (r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', 'full_month_name'),
            (r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b', 'abbr_month_name'),
            (r'\b\d{1,2}/\d{1,2}/\d{4}\b', 'numeric_slash'),
            (r'\b\d{4}-\d{2}-\d{2}\b', 'iso_format'),
            
            # Quarters
            (r'\bQ[1-4]\s+\d{4}\b', 'quarter'),
            (r'\b(?:first|second|third|fourth)\s+quarter\s+\d{4}\b', 'quarter_text'),
            
            # Fiscal years
            (r'\bfiscal\s+(?:year\s+)?\d{4}\b', 'fiscal_year'),
            (r'\bFY\s*\d{4}\b', 'fy_abbr'),
            
            # Month-Year
            (r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b', 'month_year'),
            
            # Year only
            (r'\b(19|20)\d{2}\b', 'year_only'),
        ]
        
        # Relative date patterns
        self.relative_patterns = [
            (r'\byesterday\b', 'relative'),
            (r'\btoday\b', 'relative'),
            (r'\btomorrow\b', 'relative'),
            (r'\blast\s+(?:week|month|quarter|year)\b', 'relative'),
            (r'\bnext\s+(?:week|month|quarter|year)\b', 'relative'),
            (r'\b\d+\s+(?:days|weeks|months|years)\s+(?:ago|from\s+now)\b', 'relative'),
        ]
        
        logger.info("TemporalExtractor initialized")
    
    def extract_dates(self, text: str, context_window: int = 50) -> List[DateExtractionResult]:
        """
        Extract all dates from text.
        
        Args:
            text: Text to extract dates from
            context_window: Characters of context to include
        
        Returns:
            List of date extraction results
        """
        results = []
        
        # Extract explicit dates
        for pattern, pattern_type in self.date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                date_str = match.group(0)
                start, end = match.span()
                
                # Get context
                context_start = max(0, start - context_window)
                context_end = min(len(text), end + context_window)
                context = text[context_start:context_end]
                
                # Parse date
                parsed_date = self._parse_date(date_str, pattern_type)
                
                if parsed_date:
                    result = DateExtractionResult(
                        date=parsed_date,
                        text=date_str,
                        context=context,
                        confidence=0.9 if pattern_type in ['full_month_name', 'iso_format'] else 0.7,
                        date_type='explicit',
                        span=(start, end)
                    )
                    results.append(result)
        
        # Sort by position in text
        results.sort(key=lambda r: r.span[0])
        
        # Remove duplicates (same date, overlapping spans)
        unique_results = []
        for result in results:
            is_duplicate = False
            for existing in unique_results:
                if (result.date == existing.date and 
                    abs(result.span[0] - existing.span[0]) < 20):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_results.append(result)
        
        logger.debug(f"Extracted {len(unique_results)} dates from text")
        return unique_results
    
    def _parse_date(self, date_str: str, pattern_type: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        try:
            # Full month name formats
            if pattern_type == 'full_month_name':
                # Remove comma if present
                date_str = date_str.replace(',', '')
                return datetime.strptime(date_str, '%B %d %Y').replace(tzinfo=timezone.utc)
            
            # Abbreviated month name
            elif pattern_type == 'abbr_month_name':
                date_str = date_str.replace('.', '').replace(',', '')
                return datetime.strptime(date_str, '%b %d %Y').replace(tzinfo=timezone.utc)
            
            # Numeric formats
            elif pattern_type == 'numeric_slash':
                # Try MM/DD/YYYY
                return datetime.strptime(date_str, '%m/%d/%Y').replace(tzinfo=timezone.utc)
            
            # ISO format
            elif pattern_type == 'iso_format':
                return datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            
            # Quarter
            elif pattern_type in ['quarter', 'quarter_text']:
                # Extract quarter and year
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    year = int(year_match.group(0))
                    
                    # Extract quarter number
                    q_match = re.search(r'[1-4]|first|second|third|fourth', date_str, re.IGNORECASE)
                    if q_match:
                        q_str = q_match.group(0).lower()
                        q_map = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4}
                        quarter = int(q_str) if q_str.isdigit() else q_map.get(q_str, 1)
                        
                        # Use first day of quarter
                        month = (quarter - 1) * 3 + 1
                        return datetime(year, month, 1, tzinfo=timezone.utc)
            
            # Fiscal year (use year end date)
            elif pattern_type in ['fiscal_year', 'fy_abbr']:
                year_match = re.search(r'\d{4}', date_str)
                if year_match:
                    year = int(year_match.group(0))
                    # Assume fiscal year ends December 31
                    return datetime(year, 12, 31, tzinfo=timezone.utc)
            
            # Month-Year (use first day of month)
            elif pattern_type == 'month_year':
                return datetime.strptime(date_str, '%B %Y').replace(tzinfo=timezone.utc)
            
            # Year only (use January 1)
            elif pattern_type == 'year_only':
                year = int(date_str)
                if 1900 <= year <= 2100:
                    return datetime(year, 1, 1, tzinfo=timezone.utc)
            
        except ValueError as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
        
        return None


class TemporalParser:
    """
    High-level temporal parser for documents.
    """
    
    def __init__(self):
        """Initialize temporal parser."""
        self.extractor = TemporalExtractor()
        logger.info("TemporalParser initialized")
    
    def parse_document(self, document: Dict[str, Any]) -> List[DateExtractionResult]:
        """
        Parse temporal information from a document.
        
        Args:
            document: Document with 'content' field
        
        Returns:
            List of extracted dates
        """
        content = document.get('content', '')
        
        if not content:
            logger.warning("No content in document")
            return []
        
        # Extract dates
        dates = self.extractor.extract_dates(content)
        
        # Enhance with document metadata
        doc_date = document.get('filing_date') or document.get('date')
        if doc_date:
            # Add document date as high-confidence reference point
            if isinstance(doc_date, str):
                try:
                    doc_date = datetime.fromisoformat(doc_date.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            if isinstance(doc_date, datetime):
                doc_date_result = DateExtractionResult(
                    date=doc_date,
                    text=doc_date.strftime('%Y-%m-%d'),
                    context='Document filing date',
                    confidence=1.0,
                    date_type='metadata',
                    span=(0, 0)
                )
                dates.insert(0, doc_date_result)
        
        logger.info(f"Parsed {len(dates)} temporal references from document")
        return dates
    
    def extract_event_timeline(
        self, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, List[DateExtractionResult]]:
        """
        Extract timeline from multiple documents.
        
        Args:
            documents: List of documents
        
        Returns:
            Dictionary mapping document IDs to extracted dates
        """
        timeline = {}
        
        for doc in documents:
            doc_id = doc.get('id', f"doc_{len(timeline)}")
            dates = self.parse_document(doc)
            timeline[doc_id] = dates
        
        logger.info(f"Extracted timeline from {len(documents)} documents")
        return timeline
    
    def find_temporal_references(
        self, 
        text: str, 
        reference_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Find temporal references relative to a reference date.
        
        Args:
            text: Text to search
            reference_date: Reference date for relative dates
        
        Returns:
            List of temporal references with resolved dates
        """
        references = []
        
        # Find relative date expressions
        relative_patterns = [
            (r'\bprior\s+to\s+([^,\.]+)', 'before'),
            (r'\bafter\s+([^,\.]+)', 'after'),
            (r'\bduring\s+([^,\.]+)', 'during'),
            (r'\bas\s+of\s+([^,\.]+)', 'as_of'),
            (r'\buntil\s+([^,\.]+)', 'until'),
            (r'\bfrom\s+([^,\.]+)\s+to\s+([^,\.]+)', 'period'),
        ]
        
        for pattern, ref_type in relative_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                reference = {
                    'type': ref_type,
                    'text': match.group(0),
                    'span': match.span(),
                    'context': text[max(0, match.start() - 50):min(len(text), match.end() + 50)]
                }
                references.append(reference)
        
        return references

