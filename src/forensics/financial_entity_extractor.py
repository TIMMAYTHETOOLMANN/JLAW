"""
Financial Entity Extractor - NER and Pattern Matching
===================================================

Advanced named entity recognition and pattern extraction for financial documents.
Extracts:
- Companies, executives, auditors
- Financial amounts, ratios, percentages
- Dates, quarters, fiscal years
- Accounts, line items, statements
- Geographic entities
- Legal entities and relationships
"""

import re
import logging
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span

logger = logging.getLogger(__name__)


@dataclass
class FinancialEntity:
    """Extracted financial entity"""
    type: str  # company, person, money, date, account, ratio, etc.
    text: str
    value: Optional[Any] = None  # Normalized value
    confidence: float = 1.0
    start_char: int = 0
    end_char: int = 0
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Complete extraction result"""
    text: str
    entities: List[FinancialEntity]
    entities_by_type: Dict[str, List[FinancialEntity]]
    relationships: List[Tuple[FinancialEntity, str, FinancialEntity]]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancialEntityExtractor:
    """
    Advanced financial entity extraction using NLP and pattern matching
    """
    
    # Financial patterns
    MONEY_PATTERN = re.compile(
        r'\$?\s*\(?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|trillion|thousand|M|B|T|K)?\s*\)?',
        re.IGNORECASE
    )
    
    PERCENTAGE_PATTERN = re.compile(
        r'(\d+(?:\.\d+)?)\s*%'
    )
    
    RATIO_PATTERN = re.compile(
        r'(\w+(?:\s+\w+)*?)\s+(?:ratio|rate)\s+(?:of|was|is)?\s*(\d+(?:\.\d+)?)',
        re.IGNORECASE
    )
    
    FISCAL_YEAR_PATTERN = re.compile(
        r'(?:fiscal\s+year|FY)\s*(\d{4})',
        re.IGNORECASE
    )
    
    QUARTER_PATTERN = re.compile(
        r'Q([1-4])\s*(?:FY)?\s*(\d{4})?',
        re.IGNORECASE
    )
    
    # Common financial statement line items
    FINANCIAL_LINE_ITEMS = {
        'revenue', 'sales', 'income', 'expense', 'cost', 'profit', 'loss',
        'assets', 'liabilities', 'equity', 'cash', 'debt', 'inventory',
        'receivables', 'payables', 'goodwill', 'depreciation', 'amortization',
        'ebitda', 'operating income', 'net income', 'gross margin',
        'working capital', 'retained earnings', 'stockholders equity'
    }
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize financial entity extractor
        
        Args:
            spacy_model: SpaCy model to use for NER
        """
        try:
            self.nlp = spacy.load(spacy_model)
        except OSError:
            logger.warning(f"SpaCy model {spacy_model} not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", spacy_model])
            self.nlp = spacy.load(spacy_model)
        
        self.matcher = Matcher(self.nlp.vocab)
        self._setup_patterns()
        self.logger = logging.getLogger(__name__)
    
    def _setup_patterns(self):
        """Setup custom matching patterns"""
        # Financial amount patterns
        money_pattern = [
            {"ORTH": "$"},
            {"LIKE_NUM": True},
            {"LOWER": {"IN": ["million", "billion", "thousand", "m", "b", "k"]}, "OP": "?"}
        ]
        self.matcher.add("MONEY", [money_pattern])
        
        # Fiscal period patterns
        fy_pattern = [
            {"LOWER": {"IN": ["fiscal", "fy"]}},
            {"LOWER": "year", "OP": "?"},
            {"LIKE_NUM": True}
        ]
        self.matcher.add("FISCAL_YEAR", [fy_pattern])
    
    def extract(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> ExtractionResult:
        """
        Extract financial entities from text
        
        Args:
            text: Input text to analyze
            metadata: Additional metadata
            
        Returns:
            ExtractionResult with extracted entities
        """
        self.logger.info(f"Extracting entities from {len(text)} characters")
        
        # Process with SpaCy
        doc = self.nlp(text)
        
        entities = []
        
        # Extract named entities
        entities.extend(self._extract_named_entities(doc))
        
        # Extract financial amounts
        entities.extend(self._extract_money(text))
        
        # Extract percentages
        entities.extend(self._extract_percentages(text))
        
        # Extract ratios
        entities.extend(self._extract_ratios(text))
        
        # Extract fiscal periods
        entities.extend(self._extract_fiscal_periods(text))
        
        # Extract financial line items
        entities.extend(self._extract_line_items(doc))
        
        # Remove duplicates and sort by position
        entities = self._deduplicate_entities(entities)
        entities.sort(key=lambda e: e.start_char)
        
        # Group by type
        entities_by_type = defaultdict(list)
        for entity in entities:
            entities_by_type[entity.type].append(entity)
        
        # Extract relationships
        relationships = self._extract_relationships(doc, entities)
        
        # Calculate statistics
        statistics = self._calculate_statistics(entities)
        
        return ExtractionResult(
            text=text,
            entities=entities,
            entities_by_type=dict(entities_by_type),
            relationships=relationships,
            statistics=statistics,
            metadata=metadata or {}
        )
    
    def _extract_named_entities(self, doc: Doc) -> List[FinancialEntity]:
        """Extract named entities using SpaCy NER"""
        entities = []
        for ent in doc.ents:
            entity_type = self._map_spacy_label(ent.label_)
            if entity_type:
                entities.append(FinancialEntity(
                    type=entity_type,
                    text=ent.text,
                    value=ent.text,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    context=self._get_context(doc.text, ent.start_char, ent.end_char),
                    metadata={'spacy_label': ent.label_}
                ))
        return entities
    
    def _map_spacy_label(self, label: str) -> Optional[str]:
        """Map SpaCy entity labels to financial entity types"""
        mapping = {
            'ORG': 'company',
            'PERSON': 'person',
            'GPE': 'location',
            'DATE': 'date',
            'MONEY': 'money',
            'PERCENT': 'percentage',
            'CARDINAL': 'number',
            'ORDINAL': 'ordinal',
            'QUANTITY': 'quantity'
        }
        return mapping.get(label)
    
    def _extract_money(self, text: str) -> List[FinancialEntity]:
        """Extract monetary amounts"""
        entities = []
        for match in self.MONEY_PATTERN.finditer(text):
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                
                # Check for scale indicator
                full_text = match.group(0).lower()
                if 'billion' in full_text or 'b' in full_text:
                    amount *= 1e9
                elif 'million' in full_text or 'm' in full_text:
                    amount *= 1e6
                elif 'thousand' in full_text or 'k' in full_text:
                    amount *= 1e3
                
                entities.append(FinancialEntity(
                    type='money',
                    text=match.group(0),
                    value=amount,
                    start_char=match.start(),
                    end_char=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                ))
            except ValueError:
                continue
        return entities
    
    def _extract_percentages(self, text: str) -> List[FinancialEntity]:
        """Extract percentage values"""
        entities = []
        for match in self.PERCENTAGE_PATTERN.finditer(text):
            try:
                value = float(match.group(1))
                entities.append(FinancialEntity(
                    type='percentage',
                    text=match.group(0),
                    value=value,
                    start_char=match.start(),
                    end_char=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                ))
            except ValueError:
                continue
        return entities
    
    def _extract_ratios(self, text: str) -> List[FinancialEntity]:
        """Extract financial ratios"""
        entities = []
        for match in self.RATIO_PATTERN.finditer(text):
            ratio_name = match.group(1).strip()
            ratio_value = match.group(2)
            try:
                value = float(ratio_value)
                entities.append(FinancialEntity(
                    type='ratio',
                    text=match.group(0),
                    value=value,
                    start_char=match.start(),
                    end_char=match.end(),
                    context=self._get_context(text, match.start(), match.end()),
                    metadata={'ratio_name': ratio_name}
                ))
            except ValueError:
                continue
        return entities
    
    def _extract_fiscal_periods(self, text: str) -> List[FinancialEntity]:
        """Extract fiscal years and quarters"""
        entities = []
        
        # Fiscal years
        for match in self.FISCAL_YEAR_PATTERN.finditer(text):
            year = int(match.group(1))
            entities.append(FinancialEntity(
                type='fiscal_year',
                text=match.group(0),
                value=year,
                start_char=match.start(),
                end_char=match.end(),
                context=self._get_context(text, match.start(), match.end())
            ))
        
        # Quarters
        for match in self.QUARTER_PATTERN.finditer(text):
            quarter = int(match.group(1))
            year = match.group(2)
            entities.append(FinancialEntity(
                type='quarter',
                text=match.group(0),
                value=quarter,
                start_char=match.start(),
                end_char=match.end(),
                context=self._get_context(text, match.start(), match.end()),
                metadata={'year': year if year else None}
            ))
        
        return entities
    
    def _extract_line_items(self, doc: Doc) -> List[FinancialEntity]:
        """Extract financial statement line items"""
        entities = []
        text_lower = doc.text.lower()
        
        for item in self.FINANCIAL_LINE_ITEMS:
            # Find all occurrences
            pattern = re.compile(r'\b' + re.escape(item) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(doc.text):
                entities.append(FinancialEntity(
                    type='line_item',
                    text=match.group(0),
                    value=item,
                    start_char=match.start(),
                    end_char=match.end(),
                    context=self._get_context(doc.text, match.start(), match.end())
                ))
        
        return entities
    
    def _extract_relationships(
        self,
        doc: Doc,
        entities: List[FinancialEntity]
    ) -> List[Tuple[FinancialEntity, str, FinancialEntity]]:
        """Extract relationships between entities"""
        relationships = []
        
        # Simple proximity-based relationship detection
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # If entities are close together, infer relationship
                distance = entity2.start_char - entity1.end_char
                if 0 < distance < 100:  # Within 100 characters
                    # Determine relationship type
                    if entity1.type == 'company' and entity2.type == 'money':
                        relationships.append((entity1, 'has_amount', entity2))
                    elif entity1.type == 'line_item' and entity2.type == 'money':
                        relationships.append((entity1, 'valued_at', entity2))
                    elif entity1.type == 'person' and entity2.type == 'company':
                        relationships.append((entity1, 'affiliated_with', entity2))
        
        return relationships
    
    def _deduplicate_entities(self, entities: List[FinancialEntity]) -> List[FinancialEntity]:
        """Remove duplicate entities"""
        seen = set()
        unique = []
        for entity in entities:
            key = (entity.type, entity.start_char, entity.end_char)
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        return unique
    
    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get surrounding context for an entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def _calculate_statistics(self, entities: List[FinancialEntity]) -> Dict[str, Any]:
        """Calculate extraction statistics"""
        stats = {
            'total_entities': len(entities),
            'entities_by_type': defaultdict(int)
        }
        
        for entity in entities:
            stats['entities_by_type'][entity.type] += 1
        
        # Convert defaultdict to regular dict
        stats['entities_by_type'] = dict(stats['entities_by_type'])
        
        # Calculate monetary statistics
        money_entities = [e for e in entities if e.type == 'money' and e.value]
        if money_entities:
            amounts = [e.value for e in money_entities]
            stats['money_statistics'] = {
                'count': len(amounts),
                'total': sum(amounts),
                'mean': sum(amounts) / len(amounts),
                'min': min(amounts),
                'max': max(amounts)
            }
        
        return stats
    
    def generate_report(self, result: ExtractionResult) -> str:
        """Generate human-readable extraction report"""
        report = []
        report.append("=== Financial Entity Extraction Report ===\n")
        report.append(f"Text Length: {len(result.text)} characters")
        report.append(f"Total Entities: {len(result.entities)}\n")
        
        report.append("Entities by Type:")
        for entity_type, count in sorted(result.statistics['entities_by_type'].items()):
            report.append(f"  {entity_type}: {count}")
        
        if 'money_statistics' in result.statistics:
            stats = result.statistics['money_statistics']
            report.append(f"\nMonetary Statistics:")
            report.append(f"  Count: {stats['count']}")
            report.append(f"  Total: ${stats['total']:,.2f}")
            report.append(f"  Mean: ${stats['mean']:,.2f}")
            report.append(f"  Range: ${stats['min']:,.2f} - ${stats['max']:,.2f}")
        
        report.append(f"\nRelationships Found: {len(result.relationships)}")
        
        return "\n".join(report)

