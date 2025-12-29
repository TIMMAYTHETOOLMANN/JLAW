# JLAW API Reference

Complete API documentation for JLAW SEC forensic analysis system.

---

## Core API

### MasterExecutionController

Main entry point for forensic analysis.

```python
from src.core.master_execution_controller import MasterExecutionController
from datetime import date
from pathlib import Path

controller = MasterExecutionController(
    cik: str,                    # Company CIK (e.g., "0001318605")
    company_name: str,           # Optional company name
    start_date: date,            # Analysis start date
    end_date: date,              # Analysis end date
    output_dir: Path,            # Output directory path
    strict_mode: bool = False,   # DOJ-grade enforcement
    auto_mode: bool = False      # Skip confirmations
)

# Execute full analysis
result = await controller.execute_full_analysis()
```

**Returns**: `UnifiedAnalysisResult`
- `cik`: str
- `company_name`: str
- `phase_results`: List[PhaseResult]
- `node_results`: Dict[str, NodeResult]
- `merkle_root`: str
- `dossier_path`: str
- `total_violations`: int
- `total_alerts`: int

---

## SDK Management (Phase 1)

### UnifiedSDKManager

Singleton SDK manager for OpenAI, Anthropic, and HTTP clients.

```python
from src.forensics.sdk_manager import get_sdk_manager, UnifiedSDKManager

# Get singleton instance
sdk = await get_sdk_manager()

# Access clients
openai_client = sdk.openai          # Sync OpenAI client
openai_async = sdk.openai_async     # Async OpenAI client
anthropic = sdk.anthropic           # Async Anthropic client
http_session = sdk.http_session     # aiohttp ClientSession

# SEC EDGAR requests (with rate limiting)
response = await sdk.sec_request(url: str, user_agent: str)

# Check availability
availability = sdk.get_availability()  # {"openai": True, "anthropic": True}

# Cleanup
await sdk.close()
```

**Methods**:
- `sec_request(url, user_agent)`: SEC EDGAR request with rate limiting
- `get_availability()`: Returns dict of AI provider availability
- `close()`: Close all clients and sessions

---

## Agent Registry (Phase 2)

### DynamicAgentRegistry

Agent discovery and capability matching.

```python
from src.forensics.agent_registry import DynamicAgentRegistry

registry = DynamicAgentRegistry()

# List all agents
agents = registry.list_agents()

# Get agents for violations
relevant_agents = registry.get_agents_for_violations(
    violations: List[Dict[str, Any]],
    top_k: int = 5
)

# Get specific agent
agent = registry.get_agent(agent_name: str)
```

**AgentCapability Structure**:
```python
@dataclass
class AgentCapability:
    agent_name: str
    description: str
    violation_types: Set[str]
    tools: List[str]
    priority: int
    requires_anthropic: bool
    markdown_path: Path
    prompt_template: str
```

---

## Intelligent Routing (Phase 2)

### IntelligentSubagentRouter

Agent selection and execution planning.

```python
from src.forensics.intelligent_router import IntelligentSubagentRouter

router = IntelligentSubagentRouter()

# Plan execution
decision = router.plan_execution(
    violations: List[Dict[str, Any]],
    max_agents: int = 5,
    parallel_stages: int = 2,
    min_score_threshold: float = 0.0
)
```

**Returns**: `RoutingDecision`
- `selected_agents`: List[str] - Agent names
- `execution_stages`: List[Dict] - Parallel execution stages
- `agent_scores`: Dict[str, float] - Relevance scores

---

## Unified Orchestration (Phase 3)

### UnifiedAgentOrchestrator

Multi-tier agent coordination.

```python
from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator

orchestrator = UnifiedAgentOrchestrator()

result = await orchestrator.execute_investigation(
    cik: str,
    company_name: str,
    filings: List[Dict],
    strict_mode: bool = True,
    parallel_stages: int = 2
)
```

**Returns**: `OrchestrationResult`
- `primary_findings`: List[Dict] - OpenAI + Anthropic
- `subagent_findings`: List[Dict] - Claude subagents
- `pattern_findings`: List[Dict] - 23 algorithms
- `node_findings`: Dict[str, Any] - 15 nodes
- `consensus_score`: float
- `total_violations`: int

---

## Phase Execution (Phase 4)

### PhaseExecutionFramework

Phase gating and quality enforcement.

```python
from src.core.phase_execution_framework import PhaseExecutionFramework

framework = PhaseExecutionFramework()

# Register phase
framework.register_phase(
    phase_id: str,
    phase_name: str,
    dependencies: List[str],
    gate_rules: Dict[str, Any]
)

# Execute phases
results = await framework.execute_phases()
```

**Phase Gate Rules**:
```python
{
    "min_success_rate": 0.80,    # 80% threshold
    "required_items": 5,          # Minimum items
    "consensus_threshold": 0.70   # 70% agreement
}
```

---

## Performance Profiling (Phase 5)

### PerformanceMetricsCollector

Token usage and cost tracking.

```python
from src.profiling.performance_metrics import PerformanceMetricsCollector
from pathlib import Path

collector = PerformanceMetricsCollector()

# Track phase
phase = collector.start_phase(phase_id: str, phase_name: str)
collector.end_phase(phase_id: str)

# Track agent
agent = collector.start_agent(
    agent_name: str,
    agent_type: str,  # "openai", "anthropic", "subagent"
    tier: str         # "primary", "subagent", "pattern", "node"
)

collector.end_agent(
    agent_name: str,
    input_tokens: int,
    output_tokens: int,
    model: str,
    violations_found: int,
    status: str = "success"
)

# Export report
collector.export_detailed_report(output_path: Path)
```

**Metrics Structure**:
```python
{
    "total_cost_usd": 2.15,
    "total_tokens": 350000,
    "total_duration_seconds": 245.3,
    "agents": [
        {
            "agent_name": "forensic-analyst",
            "total_cost": 0.50,
            "input_tokens": 5000,
            "output_tokens": 1500,
            "violations_found": 3
        }
    ]
}
```

---

## Evidence Chain

### HashService

Triple-hash integrity (SHA-256 + SHA3-512 + BLAKE2b).

```python
from src.core.evidence_chain.hash_service import HashService

hash_service = HashService()

# Compute triple-hash
hashes = hash_service.compute_triple_hash(content: bytes)
# Returns: {"sha256": "...", "sha3_512": "...", "blake2b": "..."}

# Verify hash
is_valid = hash_service.verify_hash(
    content: bytes,
    expected_hash: str,
    algorithm: str = "sha256"
)
```

### MerkleTree

RFC 6962 compliant Merkle tree construction.

```python
from src.core.evidence_chain.merkle_tree import MerkleTree

merkle_tree = MerkleTree()

# Add evidence
for evidence_hash in evidence_hashes:
    merkle_tree.add_leaf(bytes.fromhex(evidence_hash))

# Get root
merkle_root = merkle_tree.get_root()  # bytes

# Generate proof
proof = merkle_tree.get_proof(leaf_index: int)

# Verify proof
is_valid = merkle_tree.verify_proof(
    leaf_hash: bytes,
    proof: List[Tuple[str, bytes]],
    root: bytes
)
```

---

## Data Structures

### PhaseResult

```python
@dataclass
class PhaseResult:
    phase: ExecutionPhase
    success: bool
    duration_seconds: float
    items_processed: int
    errors: List[str]
    data: Dict[str, Any]
    evidence_hash: Optional[str]
```

### NodeResult

```python
@dataclass
class NodeResult:
    node_id: str
    node_name: str
    status: str  # "success", "failed", "skipped"
    violations_found: int
    alerts_generated: int
    findings: Dict[str, Any]
    execution_time_seconds: float
    error_message: Optional[str]
```

### UnifiedAnalysisResult

```python
@dataclass
class UnifiedAnalysisResult:
    cik: str
    company_name: str
    analysis_start: datetime
    analysis_end: datetime
    phase_results: List[PhaseResult]
    node_results: Dict[str, NodeResult]
    detection_results: Dict[str, Any]
    evidence_chain: Dict[str, Any]
    merkle_root: str
    dossier_path: str
    pdf_path: str
    total_violations: int
    total_alerts: int
```

---

## Exceptions

### EvidenceChainIntegrityError

Raised when evidence chain validation fails.

```python
from src.core.exceptions import EvidenceChainIntegrityError

try:
    verify_evidence_chain()
except EvidenceChainIntegrityError as e:
    print(f"Evidence integrity violation: {e}")
    # Critical error - halt investigation
```

### PhaseGateFailure

Raised when phase gate validation fails in strict mode.

```python
from src.core.exceptions import PhaseGateFailure

try:
    await controller.execute_full_analysis()
except PhaseGateFailure as e:
    print(f"Phase gate failed: {e}")
    # Review phase execution log
```

---

## Utilities

### Configuration

```python
from config.secure_config import get_config, print_configuration_status

# Load configuration
config = get_config()

# Print status
print_configuration_status()
# Output:
# ✅ SEC EDGAR: Configured
# ✅ OpenAI: Available
# ✅ Anthropic: Available
```

### Logging

```python
import logging

# Get logger
logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

---

## Command Line Interface

```bash
# Basic usage
jlaw --cik CIK --year YEAR

# Full options
jlaw \
  --cik CIK \
  --company "Company Name" \
  --start YYYY-MM-DD \
  --end YYYY-MM-DD \
  --mode {exploratory|forensic|batch} \
  --investigation {insider_trading|compensation|all} \
  --strict \
  --auto \
  --dry-run \
  --validate-only
```

**Options**:
- `--cik`: Company CIK (required)
- `--company`: Company name (optional)
- `--year`: Analysis year (shortcut for full year)
- `--start`, `--end`: Custom date range
- `--mode`: Execution mode
- `--investigation`: Focus area
- `--strict`: Enable DOJ-grade enforcement
- `--auto`: Skip confirmations
- `--dry-run`: Preview without execution
- `--validate-only`: Configuration check only

---

## Environment Variables

### Required

```bash
SEC_USER_AGENT=YourCompany contact@example.com
SEC_EMAIL=contact@example.com
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Optional

```bash
# SEC EDGAR
SEC_RATE_LIMIT=6.0
SEC_CACHE_DIR=.cache/sec_edgar

# Performance
MAX_AGENTS=5
ENABLE_OPTIMIZATION=true
MAX_COST_USD=5.00
PARALLEL_STAGES=2

# Databases (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5432
```

---

## Type Hints

JLAW uses comprehensive type hints for IDE support:

```python
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from pathlib import Path

async def analyze_company(
    cik: str,
    year: int,
    strict_mode: bool = True
) -> UnifiedAnalysisResult:
    """Execute forensic analysis."""
    ...
```

---

## Testing

```python
import pytest
from src.core.master_execution_controller import MasterExecutionController

@pytest.mark.asyncio
async def test_investigation():
    """Test forensic investigation."""
    controller = MasterExecutionController(
        cik="0001318605",
        start_date=date(2019, 1, 1),
        end_date=date(2019, 12, 31),
        strict_mode=True
    )
    
    result = await controller.execute_full_analysis()
    
    assert result.total_violations >= 0
    assert result.merkle_root is not None
```

**Test Markers**:
- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.benchmark`: Performance benchmarks
- `@pytest.mark.slow`: Long-running tests

---

## Version Compatibility

| JLAW Version | Python | OpenAI | Anthropic |
|--------------|--------|--------|-----------|
| 4.1.0 | ≥3.10 | ≥1.10.0 | ≥0.18.0 |
| 4.0.0 | ≥3.9 | ≥1.0.0 | ≥0.15.0 |

---

## See Also

- **System Architecture**: [docs/system_architecture.md](system_architecture.md)
- **Integration Guide**: [docs/integration_guide.md](integration_guide.md)
- **Optimization Guide**: [docs/optimization_guide.md](optimization_guide.md)
- **Troubleshooting**: [docs/troubleshooting.md](troubleshooting.md)

---

**Last Updated**: December 29, 2024  
**Version**: 4.1.0  
**Status**: Production Ready
