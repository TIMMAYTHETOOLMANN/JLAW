# Testing Guide

JLAW testing infrastructure and patterns.

## Test Structure

```
tests/
├── unit/                     # Unit tests
│   ├── test_nodes/
│   ├── test_detection/
│   └── test_evidence_chain/
├── integration/              # Integration tests
│   ├── test_sec_edgar/
│   └── test_orchestrator/
└── fixtures/                 # Test data
```

## Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_nodes/test_node1.py

# With coverage
pytest --cov=src --cov-report=html

# Verbose
pytest -v
```

## Writing Tests

```python
import pytest
from src.nodes import Node1Analyzer

@pytest.mark.asyncio
async def test_node1_analysis():
    analyzer = Node1Analyzer()
    result = await analyzer.analyze(test_data)
    assert result.status == "success"
    assert len(result.violations) >= 0
```

---

See [Contributing Guide](contributing.md) for code standards.
