# Nodes API Reference

API reference for JLAW's 15 analysis nodes.

## Node Base Interface

All nodes implement the following interface:

```python
class NodeAnalyzer:
    async def analyze(self, *args, **kwargs) -> NodeOutput:
        """Execute node analysis."""
        pass

@dataclass
class NodeOutput:
    node_id: int
    node_name: str
    status: str  # "success", "error", "skipped"
    violations_found: int
    violations: List[Dict[str, Any]]
    alerts: List[str]
    findings: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
```

## Node 1: Form 4 Insider Trading

```python
from src.nodes import Node1Analyzer

analyzer = Node1Analyzer()
result = await analyzer.analyze(
    cik="320187",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31)
)
```

**Detects**: §16 violations, suspicious trading patterns

---

For complete node descriptions, see [15-Node Pipeline](../architecture/15_node_pipeline.md).
