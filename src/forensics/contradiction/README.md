# Contradiction Detection System

## Overview
Advanced multi-strategy contradiction detection for forensic analysis.

## Components

### ContradictionEngine
Master orchestrator for all contradiction detection strategies.

```python
from src.forensics.contradiction import ContradictionEngine

engine = ContradictionEngine()
contradictions = engine.analyze_statements([
    "Revenue was $100M",
    "Revenue was $95M"
])
```

### NumericalDetector
Detects numerical contradictions in financial data.
- Configurable threshold (default 10%)
- Scale-aware (millions, billions)
- Context-sensitive

### SemanticDetector
Identifies opposing semantic claims.
- Pattern-based detection
- Opposing term pairs
- Confidence scoring

### EntityDetector
Extracts and analyzes entities for contradictions.
- Named entity extraction
- Relationship analysis
- Position tracking

### SourceAnalyzer
Analyzes source credibility and conflicts.
- Cross-source validation
- Authority scoring
- Conflict detection

## Usage

```python
from src.forensics.contradiction import (
    ContradictionEngine,
    NumericalDetector,
    SemanticDetector
)

# Initialize components
engine = ContradictionEngine()
num_detector = NumericalDetector(threshold=0.1)
sem_detector = SemanticDetector()

# Analyze statements
statements = [
    "Q1 revenue was $100 million",
    "First quarter revenue totaled $95 million",
    "The company experienced strong growth",
    "Sales declined significantly"
]

contradictions = engine.analyze_statements(statements)

for c in contradictions:
    print(f"Type: {c.type}")
    print(f"Severity: {c.severity}")
    print(f"Confidence: {c.confidence:.2%}")
```

## Integration

Works seamlessly with:
- Entity extraction system
- Temporal analysis
- Legal analysis
- Reporting system

**Status: PRODUCTION READY** ✅

