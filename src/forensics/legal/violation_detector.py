"""
Violation Detector - Phase 3
============================
Multi-strategy legal violation detection with pattern matching
and statutory correlation.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Pattern

logger = logging.getLogger(__name__)


@dataclass
class DetectedViolation:
    """Detected legal violation with evidence"""
    violation_type: str
    statute_citation: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    confidence: float
    evidence_text: str
    evidence_source: str
    detected_at: datetime = field(default_factory=datetime.now)
    position: int = 0
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'violation_type': self.violation_type,
            'statute_citation': self.statute_citation,
            'description': self.description,
            'severity': self.severity,
            'confidence': self.confidence,
            'evidence_text': self.evidence_text[:500],  # Truncate
            'evidence_source': self.evidence_source,
            'detected_at': self.detected_at.isoformat(),
            'position': self.position,
            'context': self.context
        }


class ViolationDetector:
    """
    Multi-strategy violation detection with pattern matching
    
    Detects violations across 7 major categories:
    - Securities fraud
    - Insider trading
    - False statements
    - Money laundering
    - Tax fraud
    - FCPA violations
    - Wire fraud
    """
    
    def __init__(self):
        """Initialize violation detector with pattern definitions"""
        
        # Define detection patterns by category
        self.patterns: Dict[str, List[Dict[str, Any]]] = {
            'securities_fraud': [
                {
                    'pattern': re.compile(
                        r'(material\s+misstatement|false\s+(?:statement|representation)|'
                        r'fraud(?:ulent)?|deceive|misrepresent|manipulat)',
                        re.IGNORECASE
                    ),
                    'statute': '15 USC § 78j(b)',
                    'severity': 'high',
                    'description': 'Securities fraud - material misstatement or fraud'
                },
                {
                    'pattern': re.compile(
                        r'(market\s+manipulation|pump\s+and\s+dump|wash\s+trad)',
                        re.IGNORECASE
                    ),
                    'statute': '15 USC § 78i',
                    'severity': 'high',
                    'description': 'Market manipulation'
                }
            ],
            'insider_trading': [
                {
                    'pattern': re.compile(
                        r'(insider\s+trad|material\s+non-?public\s+information|MNPI|'
                        r'tip(?:ping|ped)|tippee)',
                        re.IGNORECASE
                    ),
                    'statute': '15 USC § 78j(b)',
                    'severity': 'high',
                    'description': 'Insider trading on material non-public information'
                },
                {
                    'pattern': re.compile(
                        r'(purchased?\s+shares?\s+(?:based\s+on|before)|'
                        r'sold?\s+shares?\s+(?:based\s+on|before))',
                        re.IGNORECASE
                    ),
                    'statute': '17 CFR § 240.10b-5',
                    'severity': 'medium',
                    'description': 'Trading activity potentially based on inside information'
                }
            ],
            'false_statements': [
                {
                    'pattern': re.compile(
                        r'(false\s+statement|lied?\s+to|deceived?\s+(?:federal|government|SEC|FBI|DOJ)|'
                        r'perjur|obstruct)',
                        re.IGNORECASE
                    ),
                    'statute': '18 USC § 1001',
                    'severity': 'high',
                    'description': 'False statements to federal agents'
                },
                {
                    'pattern': re.compile(
                        r'(falsif(?:y|ied)|falsi?fy|misrepresent|conceal(?:ed)?)',
                        re.IGNORECASE
                    ),
                    'statute': '18 USC § 1001',
                    'severity': 'medium',
                    'description': 'Concealment or falsification'
                }
            ],
            'money_laundering': [
                {
                    'pattern': re.compile(
                        r'(money\s+launder|launder(?:ing|ed)?|proceeds\s+of|'
                        r'structur(?:e|ed|ing)|offshore\s+account|shell\s+compan)',
                        re.IGNORECASE
                    ),
                    'statute': '18 USC § 1956',
                    'severity': 'high',
                    'description': 'Money laundering'
                },
                {
                    'pattern': re.compile(
                        r'(avoid\s+detection|evade\s+report|smurfing)',
                        re.IGNORECASE
                    ),
                    'statute': '31 USC § 5324',
                    'severity': 'high',
                    'description': 'Structuring transactions to evade reporting'
                }
            ],
            'tax_fraud': [
                {
                    'pattern': re.compile(
                        r'(tax\s+(?:fraud|evasion|eva(?:de|ding))|'
                        r'underreport(?:ed|ing)?|falsif(?:y|ied)\s+(?:return|tax)|'
                        r'hidden?\s+income)',
                        re.IGNORECASE
                    ),
                    'statute': '26 USC § 7201',
                    'severity': 'high',
                    'description': 'Tax evasion or fraud'
                },
                {
                    'pattern': re.compile(
                        r'(offshore\s+(?:account|income|scheme)|'
                        r'foreign\s+(?:income|source).*(?:underreport|conceal))',
                        re.IGNORECASE
                    ),
                    'statute': '26 USC § 7206',
                    'severity': 'high',
                    'description': 'Tax fraud involving offshore accounts'
                }
            ],
            'fcpa': [
                {
                    'pattern': re.compile(
                        r'(brib(?:e|ery|ing)|corrupt\s+payment|'
                        r'foreign\s+(?:official|government).*(?:payment|bribe)|'
                        r'kickback|facilitat(?:ion|e)\s+payment)',
                        re.IGNORECASE
                    ),
                    'statute': '15 USC § 78dd-1',
                    'severity': 'high',
                    'description': 'Foreign Corrupt Practices Act - bribery'
                }
            ],
            'wire_fraud': [
                {
                    'pattern': re.compile(
                        r'(wire\s+fraud|scheme\s+to\s+defraud|'
                        r'electronic\s+(?:communication|transfer).*(?:fraud|deceiv))',
                        re.IGNORECASE
                    ),
                    'statute': '18 USC § 1343',
                    'severity': 'high',
                    'description': 'Wire fraud'
                }
            ]
        }
        
        # Statistics
        self._stats = {
            'documents_analyzed': 0,
            'violations_detected': 0,
            'pattern_matches': 0,
            'by_category': {cat: 0 for cat in self.patterns.keys()}
        }
        
        logger.info(f"✅ ViolationDetector initialized with {sum(len(v) for v in self.patterns.values())} patterns across {len(self.patterns)} categories")
    
    def detect_violations(
        self,
        text: str,
        source: str = "unknown",
        context: Optional[Dict[str, Any]] = None
    ) -> List[DetectedViolation]:
        """
        Detect legal violations in text
        
        Args:
            text: Text content to analyze
            source: Source identifier for evidence tracking
            context: Additional context information
        
        Returns:
            List of detected violations
        """
        self._stats['documents_analyzed'] += 1
        violations: List[DetectedViolation] = []
        
        # Apply each pattern category
        for category, patterns in self.patterns.items():
            for pattern_def in patterns:
                matches = pattern_def['pattern'].finditer(text)
                
                for match in matches:
                    self._stats['pattern_matches'] += 1
                    self._stats['by_category'][category] += 1
                    
                    # Extract context around match
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    evidence_text = text[start:end].strip()
                    
                    # Calculate confidence based on match quality
                    confidence = self._calculate_confidence(
                        match_text=match.group(),
                        category=category,
                        context=context
                    )
                    
                    violation = DetectedViolation(
                        violation_type=category,
                        statute_citation=pattern_def['statute'],
                        description=pattern_def['description'],
                        severity=pattern_def['severity'],
                        confidence=confidence,
                        evidence_text=evidence_text,
                        evidence_source=source,
                        position=match.start(),
                        context=context
                    )
                    
                    violations.append(violation)
        
        # Deduplicate overlapping violations
        violations = self._deduplicate_violations(violations)
        
        self._stats['violations_detected'] += len(violations)
        
        logger.info(f"🔍 Detected {len(violations)} violations in '{source}'")
        
        return violations
    
    def _calculate_confidence(
        self,
        match_text: str,
        category: str,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate confidence score for a match"""
        base_confidence = 0.75
        
        # Boost for longer/more specific matches
        if len(match_text) > 20:
            base_confidence += 0.10
        
        # Boost for certain high-confidence patterns
        high_confidence_terms = [
            'insider trading', 'money laundering', 'tax evasion',
            'false statement', 'bribery', 'wire fraud'
        ]
        if any(term in match_text.lower() for term in high_confidence_terms):
            base_confidence += 0.10
        
        # Adjust based on context if provided
        if context:
            if context.get('priority') == 'high':
                base_confidence += 0.05
        
        return min(0.95, base_confidence)
    
    def _deduplicate_violations(
        self,
        violations: List[DetectedViolation]
    ) -> List[DetectedViolation]:
        """Remove duplicate/overlapping violations"""
        if not violations:
            return violations
        
        # Sort by position and confidence
        violations.sort(key=lambda v: (v.position, -v.confidence))
        
        deduplicated: List[DetectedViolation] = []
        last_position = -1000  # Use large negative to allow first violation
        
        for v in violations:
            # If this violation is at least 50 chars from the last one, keep it
            if v.position - last_position >= 50:
                deduplicated.append(v)
                last_position = v.position
        
        return deduplicated
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics"""
        return self._stats.copy()
    
    def reset_statistics(self):
        """Reset detection statistics"""
        self._stats = {
            'documents_analyzed': 0,
            'violations_detected': 0,
            'pattern_matches': 0,
            'by_category': {cat: 0 for cat in self.patterns.keys()}
        }


if __name__ == "__main__":
    # Demo usage
    detector = ViolationDetector()
    
    test_text = """
    The company engaged in insider trading by purchasing shares based on
    material non-public information about pending acquisitions. False
    statements were made to federal investigators regarding offshore
    accounts used to launder proceeds. Tax returns were falsified to
    underreport income from foreign sources. The CEO offered bribes to
    foreign officials to secure contracts.
    """
    
    violations = detector.detect_violations(
        text=test_text,
        source="test_document"
    )
    
    print(f"\n🔍 Detection Results:")
    print(f"  Violations detected: {len(violations)}")
    
    for v in violations:
        print(f"\n  - {v.violation_type}:")
        print(f"      Statute: {v.statute_citation}")
        print(f"      Confidence: {v.confidence:.1%}")
        print(f"      Severity: {v.severity}")
        print(f"      Description: {v.description}")
    
    print(f"\n  Statistics:")
    stats = detector.get_statistics()
    print(f"    Documents analyzed: {stats['documents_analyzed']}")
    print(f"    Violations detected: {stats['violations_detected']}")
    print(f"    Pattern matches: {stats['pattern_matches']}")
