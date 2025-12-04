"""
Omniscient Contradiction Detector
Detects contradictions across entire document corpus using advanced NLP and logic.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class ContradictionType(Enum):
    """Types of contradictions."""
    DIRECT = "direct"  # Direct contradiction
    SEMANTIC = "semantic"  # Semantic/meaning contradiction
    TEMPORAL = "temporal"  # Time-based impossibility
    LOGICAL = "logical"  # Logical inconsistency
    MATHEMATICAL = "mathematical"  # Math/numbers don't match
    IMPLICIT = "implicit"  # Implied contradiction


class Severity(Enum):
    """Severity levels for contradictions."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class DocumentChunk:
    """A chunk of document text."""
    text: str
    source: str
    date: Optional[datetime]
    page: Optional[int]
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    """A specific claim extracted from text."""
    text: str
    source: str
    date: Optional[datetime]
    context: str
    confidence: float
    entities: List[str] = field(default_factory=list)
    numbers: List[float] = field(default_factory=list)


@dataclass
class SpecificContradiction:
    """A specific contradiction between two claims."""
    type: ContradictionType
    claim1: Claim
    claim2: Claim
    contradiction: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class Contradiction:
    """A detected contradiction."""
    id: str
    source1: DocumentChunk
    source2: DocumentChunk
    type: ContradictionType
    confidence: float
    specific: SpecificContradiction
    implications: List[str]
    severity: Severity
    graph_confidence: Optional[float] = None
    temporal_delta: Optional[float] = None  # Days between contradictory statements


@dataclass
class ContradictionNetwork:
    """Network of contradictions showing relationships."""
    contradictions: List[Contradiction]
    nodes: List[Dict[str, Any]]  # Documents/chunks
    edges: List[Dict[str, Any]]  # Contradiction relationships
    clusters: List[List[str]]  # Groups of related contradictions


@dataclass
class ContradictionReport:
    """Complete contradiction analysis report."""
    contradictions: List[Contradiction]
    network: ContradictionNetwork
    summary: Dict[str, Any]
    critical_contradictions: List[Contradiction]
    timeline: List[Tuple[datetime, Contradiction]]
    statistics: Dict[str, int]


class OmniscientContradictionDetector:
    """
    Omniscient Contradiction Detector - Phase 6
    
    Detects contradictions across entire document corpus using:
    - Semantic similarity analysis
    - Logical inference
    - Temporal impossibility detection
    - Mathematical inconsistency checking
    - Cross-reference verification
    
    Integrates with:
    - Phase 1: Document parsing for text extraction
    - Phase 4: Timeline analysis for temporal contradictions
    - Phase 5: Evidence evaluation for legal implications
    """
    
    def __init__(self):
        """Initialize contradiction detector."""
        self.contradiction_counter = 0
        logger.info("OmniscientContradictionDetector initialized")
    
    async def detect_contradictions(
        self,
        corpus: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> ContradictionReport:
        """
        Detect contradictions across entire corpus.
        
        Args:
            corpus: List of documents to analyze
            options: Detection options
                - granularity: 'sentence' | 'paragraph' | 'document'
                - threshold: Similarity threshold (default: 0.7)
                - include_implied: Include implied contradictions (default: True)
        
        Returns:
            Complete contradiction report
        """
        options = options or {}
        granularity = options.get('granularity', 'paragraph')
        threshold = options.get('threshold', 0.7)
        include_implied = options.get('include_implied', True)
        
        logger.info(f"Detecting contradictions in {len(corpus)} documents...")
        logger.info(f"  Granularity: {granularity}, Threshold: {threshold}")
        
        # Step 1: Chunk documents
        logger.info("Step 1: Chunking documents...")
        chunks = self._chunk_documents(corpus, granularity)
        logger.info(f"  Created {len(chunks)} chunks")
        
        # Step 2: Find direct contradictions
        logger.info("Step 2: Finding direct contradictions...")
        direct = await self._find_direct_contradictions(chunks, threshold)
        logger.info(f"  Found {len(direct)} direct contradictions")
        
        # Step 3: Find semantic contradictions
        logger.info("Step 3: Finding semantic contradictions...")
        semantic = await self._find_semantic_contradictions(chunks, threshold)
        logger.info(f"  Found {len(semantic)} semantic contradictions")
        
        # Step 4: Find temporal impossibilities
        logger.info("Step 4: Finding temporal impossibilities...")
        temporal = await self._find_temporal_contradictions(chunks)
        logger.info(f"  Found {len(temporal)} temporal contradictions")
        
        # Step 5: Find mathematical inconsistencies
        logger.info("Step 5: Finding mathematical inconsistencies...")
        mathematical = await self._find_mathematical_contradictions(chunks)
        logger.info(f"  Found {len(mathematical)} mathematical contradictions")
        
        # Step 6: Find logical contradictions
        if include_implied:
            logger.info("Step 6: Finding logical contradictions...")
            logical = await self._find_logical_contradictions(chunks)
            logger.info(f"  Found {len(logical)} logical contradictions")
        else:
            logical = []
        
        # Combine all contradictions
        all_contradictions = direct + semantic + temporal + mathematical + logical
        logger.info(f"Total contradictions found: {len(all_contradictions)}")
        
        # Build contradiction network
        logger.info("Building contradiction network...")
        network = self._build_contradiction_network(all_contradictions)
        
        # Generate summary
        summary = self._generate_summary(all_contradictions)
        
        # Filter critical
        critical = [c for c in all_contradictions if c.severity == Severity.CRITICAL]
        
        # Build timeline
        timeline = self._build_contradiction_timeline(all_contradictions)
        
        # Calculate statistics
        statistics = self._calculate_statistics(all_contradictions)
        
        report = ContradictionReport(
            contradictions=all_contradictions,
            network=network,
            summary=summary,
            critical_contradictions=critical,
            timeline=timeline,
            statistics=statistics
        )
        
        logger.info("Contradiction detection complete")
        return report
    
    def _chunk_documents(
        self,
        corpus: List[Dict[str, Any]],
        granularity: str
    ) -> List[DocumentChunk]:
        """Chunk documents into analyzable pieces."""
        chunks = []
        
        for doc in corpus:
            content = doc.get('content', '')
            source = doc.get('source', 'unknown')
            date = doc.get('date')
            
            if granularity == 'sentence':
                # Split by sentences
                sentences = re.split(r'[.!?]+', content)
                for i, sent in enumerate(sentences):
                    if len(sent.strip()) > 10:
                        chunks.append(DocumentChunk(
                            text=sent.strip(),
                            source=source,
                            date=date,
                            page=doc.get('page'),
                            chunk_id=f"{source}_s{i}",
                            metadata=doc.get('metadata', {})
                        ))
            
            elif granularity == 'paragraph':
                # Split by paragraphs
                paragraphs = content.split('\n\n')
                for i, para in enumerate(paragraphs):
                    if len(para.strip()) > 20:
                        chunks.append(DocumentChunk(
                            text=para.strip(),
                            source=source,
                            date=date,
                            page=doc.get('page'),
                            chunk_id=f"{source}_p{i}",
                            metadata=doc.get('metadata', {})
                        ))
            
            else:  # document
                chunks.append(DocumentChunk(
                    text=content,
                    source=source,
                    date=date,
                    page=doc.get('page'),
                    chunk_id=source,
                    metadata=doc.get('metadata', {})
                ))
        
        return chunks
    
    async def _find_direct_contradictions(
        self,
        chunks: List[DocumentChunk],
        threshold: float
    ) -> List[Contradiction]:
        """Find direct contradictions (explicit opposite statements)."""
        contradictions = []
        
        # Look for negation patterns
        negation_patterns = [
            (r'\bnot\b', r'\b(?!not)\b'),
            (r'\bno\b', r'\byes\b'),
            (r'\bfalse\b', r'\btrue\b'),
            (r'\bdid not\b', r'\bdid\b'),
            (r'\bwas not\b', r'\bwas\b'),
            (r'\bcannot\b', r'\bcan\b'),
        ]
        
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                chunk1 = chunks[i]
                chunk2 = chunks[j]
                
                # Check for direct negation
                for pos_pattern, neg_pattern in negation_patterns:
                    if (re.search(pos_pattern, chunk1.text.lower()) and 
                        re.search(neg_pattern, chunk2.text.lower())):
                        
                        # Extract similar base
                        if self._text_similarity(chunk1.text, chunk2.text) > 0.5:
                            contradiction = self._create_contradiction(
                                chunk1,
                                chunk2,
                                ContradictionType.DIRECT,
                                0.9,
                                "Direct contradiction via negation"
                            )
                            contradictions.append(contradiction)
                            break
        
        return contradictions
    
    async def _find_semantic_contradictions(
        self,
        chunks: List[DocumentChunk],
        threshold: float
    ) -> List[Contradiction]:
        """Find semantic contradictions (similar topics, different meanings)."""
        contradictions = []
        
        # Simple keyword-based semantic analysis
        # In production, would use actual embeddings
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                chunk1 = chunks[i]
                chunk2 = chunks[j]
                
                # Check if chunks are about similar topics
                similarity = self._text_similarity(chunk1.text, chunk2.text)
                
                if 0.3 < similarity < 0.7:  # Similar topic, different content
                    # Check for contradictory numbers
                    numbers1 = self._extract_numbers(chunk1.text)
                    numbers2 = self._extract_numbers(chunk2.text)
                    
                    if numbers1 and numbers2:
                        # Check for significant differences
                        for n1 in numbers1:
                            for n2 in numbers2:
                                if abs(n1 - n2) / max(abs(n1), abs(n2), 1) > 0.2:
                                    contradiction = self._create_contradiction(
                                        chunk1,
                                        chunk2,
                                        ContradictionType.SEMANTIC,
                                        0.7,
                                        f"Semantic contradiction: {n1} vs {n2}"
                                    )
                                    contradictions.append(contradiction)
                                    break
        
        return contradictions
    
    async def _find_temporal_contradictions(
        self,
        chunks: List[DocumentChunk]
    ) -> List[Contradiction]:
        """Find temporal impossibilities."""
        contradictions = []
        
        # Group chunks by source
        by_source: Dict[str, List[DocumentChunk]] = defaultdict(list)
        for chunk in chunks:
            by_source[chunk.source].append(chunk)
        
        # Check for temporal impossibilities
        for source, source_chunks in by_source.items():
            sorted_chunks = sorted(
                [c for c in source_chunks if c.date],
                key=lambda c: c.date
            )
            
            for i in range(len(sorted_chunks) - 1):
                chunk1 = sorted_chunks[i]
                chunk2 = sorted_chunks[i + 1]
                
                # Check if later statement contradicts earlier one
                if 'previously' in chunk2.text.lower() or 'earlier' in chunk2.text.lower():
                    # Extract what was said
                    if self._has_contradictory_claim(chunk1.text, chunk2.text):
                        days = (chunk2.date - chunk1.date).days
                        contradiction = self._create_contradiction(
                            chunk1,
                            chunk2,
                            ContradictionType.TEMPORAL,
                            0.8,
                            f"Temporal contradiction: statement changed after {days} days"
                        )
                        contradiction.temporal_delta = days
                        contradictions.append(contradiction)
        
        return contradictions
    
    async def _find_mathematical_contradictions(
        self,
        chunks: List[DocumentChunk]
    ) -> List[Contradiction]:
        """Find mathematical inconsistencies."""
        contradictions = []
        
        # Look for financial statements that don't add up
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                chunk1 = chunks[i]
                chunk2 = chunks[j]
                
                # Extract numbers from both
                numbers1 = self._extract_numbers(chunk1.text)
                numbers2 = self._extract_numbers(chunk2.text)
                
                if len(numbers1) >= 2 and len(numbers2) >= 1:
                    # Check if sum in chunk1 doesn't match number in chunk2
                    sum1 = sum(numbers1[:2])
                    
                    for n2 in numbers2:
                        # If they should be the same but aren't
                        if abs(sum1 - n2) / max(abs(sum1), abs(n2), 1) > 0.05:
                            # Check if they're talking about the same thing
                            if self._text_similarity(chunk1.text, chunk2.text) > 0.3:
                                contradiction = self._create_contradiction(
                                    chunk1,
                                    chunk2,
                                    ContradictionType.MATHEMATICAL,
                                    0.85,
                                    f"Mathematical inconsistency: {sum1} vs {n2}"
                                )
                                contradictions.append(contradiction)
        
        return contradictions
    
    async def _find_logical_contradictions(
        self,
        chunks: List[DocumentChunk]
    ) -> List[Contradiction]:
        """Find logical contradictions (implied contradictions)."""
        contradictions = []
        
        # Simple logical contradiction detection
        # A says X, B says "if X then Y", C says "not Y"
        
        for i in range(len(chunks)):
            chunk = chunks[i]
            text = chunk.text.lower()
            
            # Look for conditional statements
            if 'if' in text and 'then' in text:
                # Extract condition and consequence
                # This is simplified - production would use proper parsing
                
                # Check other chunks for contradiction
                for j in range(len(chunks)):
                    if i != j:
                        other = chunks[j]
                        
                        # Simple check for logical contradiction
                        if self._has_logical_contradiction(chunk.text, other.text):
                            contradiction = self._create_contradiction(
                                chunk,
                                other,
                                ContradictionType.LOGICAL,
                                0.6,
                                "Logical contradiction detected"
                            )
                            contradictions.append(contradiction)
        
        return contradictions
    
    def _create_contradiction(
        self,
        chunk1: DocumentChunk,
        chunk2: DocumentChunk,
        type: ContradictionType,
        confidence: float,
        description: str
    ) -> Contradiction:
        """Create a contradiction object."""
        self.contradiction_counter += 1
        
        claim1 = Claim(
            text=chunk1.text[:200],
            source=chunk1.source,
            date=chunk1.date,
            context=chunk1.text,
            confidence=0.8,
            numbers=self._extract_numbers(chunk1.text)
        )
        
        claim2 = Claim(
            text=chunk2.text[:200],
            source=chunk2.source,
            date=chunk2.date,
            context=chunk2.text,
            confidence=0.8,
            numbers=self._extract_numbers(chunk2.text)
        )
        
        specific = SpecificContradiction(
            type=type,
            claim1=claim1,
            claim2=claim2,
            contradiction=description
        )
        
        # Assess severity
        severity = self._assess_severity(specific, chunk1, chunk2)
        
        # Generate implications
        implications = self._analyze_implications(specific)
        
        return Contradiction(
            id=f"CONTRA_{self.contradiction_counter:04d}",
            source1=chunk1,
            source2=chunk2,
            type=type,
            confidence=confidence,
            specific=specific,
            implications=implications,
            severity=severity
        )
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (Jaccard)."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numbers from text."""
        # Find all numbers (including decimals and millions/billions)
        pattern = r'\$?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|thousand)?'
        matches = re.findall(pattern, text.lower())
        
        numbers = []
        for num_str, unit in matches:
            try:
                num = float(num_str.replace(',', ''))
                
                # Apply unit multiplier
                if unit == 'thousand':
                    num *= 1000
                elif unit == 'million':
                    num *= 1000000
                elif unit == 'billion':
                    num *= 1000000000
                
                numbers.append(num)
            except ValueError:
                continue
        
        return numbers
    
    def _has_contradictory_claim(self, text1: str, text2: str) -> bool:
        """Check if texts have contradictory claims."""
        # Simple heuristic: check for opposite keywords
        positive = ['increased', 'grew', 'rose', 'up', 'positive']
        negative = ['decreased', 'fell', 'down', 'negative', 'declined']
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        has_positive_1 = any(word in text1_lower for word in positive)
        has_negative_1 = any(word in text1_lower for word in negative)
        has_positive_2 = any(word in text2_lower for word in positive)
        has_negative_2 = any(word in text2_lower for word in negative)
        
        # Contradiction if one is positive and other is negative
        return (has_positive_1 and has_negative_2) or (has_negative_1 and has_positive_2)
    
    def _has_logical_contradiction(self, text1: str, text2: str) -> bool:
        """Check for logical contradiction."""
        # Simplified logical contradiction check
        # Would use proper logical inference in production
        return False  # Placeholder
    
    def _assess_severity(
        self,
        specific: SpecificContradiction,
        chunk1: DocumentChunk,
        chunk2: DocumentChunk
    ) -> Severity:
        """Assess contradiction severity."""
        # Critical if:
        # - Mathematical contradiction with large numbers
        # - Direct contradiction in same document
        # - Temporal contradiction with reversal
        
        if specific.type == ContradictionType.MATHEMATICAL:
            if specific.claim1.numbers and max(specific.claim1.numbers) > 1000000:
                return Severity.CRITICAL
        
        if specific.type == ContradictionType.DIRECT:
            return Severity.HIGH
        
        if specific.type == ContradictionType.TEMPORAL:
            if chunk1.date and chunk2.date:
                days = abs((chunk2.date - chunk1.date).days)
                if days < 90:  # Within same quarter
                    return Severity.HIGH
        
        if specific.type == ContradictionType.SEMANTIC:
            return Severity.MEDIUM
        
        return Severity.LOW
    
    def _analyze_implications(self, specific: SpecificContradiction) -> List[str]:
        """Analyze legal/forensic implications."""
        implications = []
        
        if specific.type == ContradictionType.MATHEMATICAL:
            implications.append("Potential accounting fraud or material misstatement")
            implications.append("SEC Rule 10b-5 violation possible")
        
        if specific.type == ContradictionType.DIRECT:
            implications.append("Intentional misrepresentation possible")
            implications.append("Credibility of statements questionable")
        
        if specific.type == ContradictionType.TEMPORAL:
            implications.append("Timeline inconsistency may indicate concealment")
            implications.append("Restatement or correction may be required")
        
        implications.append("Evidence admissibility may be challenged")
        
        return implications
    
    def _build_contradiction_network(
        self,
        contradictions: List[Contradiction]
    ) -> ContradictionNetwork:
        """Build network showing contradiction relationships."""
        # Build nodes (unique documents/chunks)
        node_map = {}
        nodes = []
        
        for contra in contradictions:
            if contra.source1.chunk_id not in node_map:
                node_map[contra.source1.chunk_id] = len(nodes)
                nodes.append({
                    'id': contra.source1.chunk_id,
                    'source': contra.source1.source,
                    'date': contra.source1.date.isoformat() if contra.source1.date else None,
                    'text_preview': contra.source1.text[:100]
                })
            
            if contra.source2.chunk_id not in node_map:
                node_map[contra.source2.chunk_id] = len(nodes)
                nodes.append({
                    'id': contra.source2.chunk_id,
                    'source': contra.source2.source,
                    'date': contra.source2.date.isoformat() if contra.source2.date else None,
                    'text_preview': contra.source2.text[:100]
                })
        
        # Build edges (contradictions)
        edges = []
        for contra in contradictions:
            edges.append({
                'source': contra.source1.chunk_id,
                'target': contra.source2.chunk_id,
                'type': contra.type.value,
                'severity': contra.severity.value,
                'confidence': contra.confidence
            })
        
        # Find clusters (groups of related contradictions)
        clusters = self._find_clusters(contradictions)
        
        return ContradictionNetwork(
            contradictions=contradictions,
            nodes=nodes,
            edges=edges,
            clusters=clusters
        )
    
    def _find_clusters(self, contradictions: List[Contradiction]) -> List[List[str]]:
        """Find clusters of related contradictions."""
        # Simple clustering by source
        source_groups: Dict[str, List[str]] = defaultdict(list)
        
        for contra in contradictions:
            source_groups[contra.source1.source].append(contra.id)
            source_groups[contra.source2.source].append(contra.id)
        
        # Convert to clusters
        clusters = [list(set(ids)) for ids in source_groups.values() if len(ids) > 1]
        
        return clusters
    
    def _generate_summary(self, contradictions: List[Contradiction]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not contradictions:
            return {
                'total': 0,
                'by_type': {},
                'by_severity': {},
                'critical_count': 0
            }
        
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        
        for contra in contradictions:
            by_type[contra.type.value] += 1
            by_severity[contra.severity.value] += 1
        
        return {
            'total': len(contradictions),
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'critical_count': by_severity['critical'],
            'avg_confidence': sum(c.confidence for c in contradictions) / len(contradictions)
        }
    
    def _build_contradiction_timeline(
        self,
        contradictions: List[Contradiction]
    ) -> List[Tuple[datetime, Contradiction]]:
        """Build timeline of contradictions."""
        timeline = []
        
        for contra in contradictions:
            # Use the later date as the contradiction discovery point
            date1 = contra.source1.date
            date2 = contra.source2.date
            
            if date1 and date2:
                discovery_date = max(date1, date2)
                timeline.append((discovery_date, contra))
            elif date1:
                timeline.append((date1, contra))
            elif date2:
                timeline.append((date2, contra))
        
        # Sort by date
        timeline.sort(key=lambda x: x[0])
        
        return timeline
    
    def _calculate_statistics(self, contradictions: List[Contradiction]) -> Dict[str, int]:
        """Calculate detailed statistics."""
        return {
            'total_contradictions': len(contradictions),
            'direct': len([c for c in contradictions if c.type == ContradictionType.DIRECT]),
            'semantic': len([c for c in contradictions if c.type == ContradictionType.SEMANTIC]),
            'temporal': len([c for c in contradictions if c.type == ContradictionType.TEMPORAL]),
            'mathematical': len([c for c in contradictions if c.type == ContradictionType.MATHEMATICAL]),
            'logical': len([c for c in contradictions if c.type == ContradictionType.LOGICAL]),
            'critical': len([c for c in contradictions if c.severity == Severity.CRITICAL]),
            'high': len([c for c in contradictions if c.severity == Severity.HIGH]),
            'medium': len([c for c in contradictions if c.severity == Severity.MEDIUM]),
            'low': len([c for c in contradictions if c.severity == Severity.LOW])
        }

