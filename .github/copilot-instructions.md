# GitHub Copilot Instructions for JLAW

## Project Overview

JLAW is a **DOJ-grade SEC filing forensic analysis platform** implementing a **15-node recursive prosecutorial engine** with 23 fraud detection patterns. The system produces courtroom-ready forensic dossiers from SEC EDGAR filings with FRE 902(13)/(14) compliant evidence chains.

### Core Architecture

- **15-Node Recursive Engine**: Sequential analysis phases (4 phases, 15 nodes total)
- **23 Detection Algorithms**: 85-97% accuracy fraud pattern detection
- **10 Claude Specialized Agents**: Domain-specific forensic analysis
- **Evidence Chain**: FRE 902(13)/(14) compliant with SHA-256 hashing and RFC 3161 timestamping
- **Dual AI Validation**: OpenAI + Anthropic cross-validation

## Coding Standards & Conventions

### Python Style

- **Python Version**: 3.10+
- **Type Hints**: Always use type hints for function parameters and return values
- **Docstrings**: Use Google-style docstrings for all modules, classes, and functions
- **Imports**: Group imports (stdlib, third-party, local) with blank lines between groups
- **Dataclasses**: Prefer `@dataclass` for data structures over plain classes
- **Async/Await**: Use async/await for I/O operations (SEC API calls, file operations)

### Module Organization

```
src/
├── core/                    # Core engine and orchestration
│   └── recursive_engine.py  # Main 15-node recursive engine
├── nodes/                   # 15 analysis nodes (node1-node15)
│   ├── __init__.py         # Centralized exports - USE V2 VERSIONS
│   ├── node1_form4/        # Form 4 insider trading
│   ├── node2_def14a/       # DEF 14A compensation
│   └── ...                 # Nodes 3-15
├── detection/              # Pattern detection (23 algorithms)
├── integrations/           # External API clients (SEC EDGAR, Polygon.io)
├── evidence_chain/         # FRE 902 compliance, custody tracking
└── reporting/              # Dossier generation
```

### Version Management

**IMPORTANT**: Always use V2 versions of node implementations when available.

- ✅ **Import from `src.nodes.__init__`**: Centralized exports always point to latest (V2) versions
- ❌ **Avoid direct module imports**: Don't import from `node7_13f_holdings.institutional_analyzer`
- ✅ **Use V2 class names**: `BankruptcyPredictorV2`, `MarketCorrelationEngineV2`, etc.

Example:
```python
# ✅ CORRECT - Uses V2 from centralized exports
from src.nodes import BankruptcyPredictorV2, MarketCorrelationEngineV2

# ❌ WRONG - Direct import bypasses V2
from src.nodes.node13_zscore.bankruptcy_predictor import BankruptcyPredictor
```

## Node Implementation Guidelines

### Node Structure

Each node should follow this pattern:

```python
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class Node{N}Output:
    """Output from Node {N} analysis."""
    violations: List[Dict[str, Any]]
    alerts: List[str]
    findings: Dict[str, Any]
    execution_time: float

class Node{N}Analyzer:
    """Node {N}: {Description}."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze(self, *args, **kwargs) -> Node{N}Output:
        """Execute Node {N} analysis."""
        # Implementation
        pass
```

### Node Phases

- **Phase 1 (Nodes 1-6)**: Core SEC Filing Analysis
  - Node 1: Form 4 Insider Trading (§16 violations)
  - Node 2: DEF 14A Executive Compensation
  - Node 3: 10-Q Temporal Consistency
  - Node 4: 10-K SOX Certification
  - Node 5: IRC §83 Tax Exposure
  - Node 6: Enforcement Routing (SEC/DOJ/IRS)

- **Phase 2 (Nodes 7-12)**: Extended Intelligence
  - Node 7: 13F-HR Institutional Holdings
  - Node 8: SC 13D/13G Beneficial Ownership
  - Node 9: 8-K Material Events
  - Node 10: Form 144 Restricted Sales
  - Node 11: Executive Network Analysis
  - Node 12: Earnings Call Transcripts

- **Phase 3 (Nodes 13-14)**: Financial Health
  - Node 13: Z-Score Bankruptcy Prediction
  - Node 14: F-Score Financial Strength

- **Phase 4 (Node 15)**: Market Correlation
  - Node 15: Market Correlation Engine (Polygon.io)

## SEC EDGAR Integration

### Rate Limiting

- **Rate**: 9 requests/second (conservative, SEC allows 10)
- **Shared Limiter**: Use `SharedRateLimiter` to prevent concurrent violations
- **Exponential Backoff**: Handle 429 responses with 2x-4x slowdown
- **User-Agent**: Always set `SEC_USER_AGENT` in `.env` (format: `Company Name contact@email.com`)

```python
from src.integrations.sec_edgar.edgar_client import SECEdgarClient

async with SECEdgarClient(user_agent="YourOrg contact@example.com") as client:
    filings = await client.get_form4_filings(cik="320187", start_date=..., end_date=...)
```

### Caching Strategy

- **Persistent Cache**: File-based with configurable TTL
- **Stale Fallback**: Use expired cache if fetch fails (reliability first)
- **TTLs**: Submissions 24h, Filings 1h, XBRL 24h, Tickers 7d, Documents 30d

## Error Handling & Logging

### Logging Levels

- **DEBUG**: Detailed execution flow, cache hits/misses
- **INFO**: Node completion, major milestones
- **WARNING**: Non-critical failures, fallback to cached data
- **ERROR**: Node failures, API errors, validation failures
- **CRITICAL**: System-wide failures, evidence chain violations

### Error Handling Pattern

```python
try:
    result = await self.analyze_filing(filing)
    return NodeResult(status="success", ...)
except Exception as e:
    logger.error(f"Node {N} error: {e}", exc_info=True)
    return NodeResult(
        status="error",
        violations_found=0,
        error_message=str(e)
    )
```

## Evidence Chain & Compliance

### FRE 902(13) Requirements

When handling evidence:
1. Compute SHA-256 hash of source documents
2. Create RFC 3161 timestamp
3. Log custody chain in `evidence_chain/custody/`
4. Never modify original documents

```python
from src.evidence_chain.hash_generator import compute_hash
from src.evidence_chain.custody.chain_of_custody import CustodyLogger

hash_value = compute_hash(document_content)
custody_logger.log_acquisition(document_url, hash_value, timestamp)
```

## Testing Guidelines

- **Unit Tests**: Test individual node analyzers in isolation
- **Integration Tests**: Test SEC EDGAR client with mock responses
- **Strict Mode Tests**: Validate phase gates and exit codes
- **Coverage Target**: 80%+ for core modules

```python
# Test pattern for nodes
@pytest.mark.asyncio
async def test_node{N}_analysis():
    analyzer = Node{N}Analyzer()
    result = await analyzer.analyze(test_data)
    assert result.status == "success"
    assert len(result.violations) >= 0
```

## Performance Considerations

- **Async I/O**: Always use async/await for network calls
- **Batch Processing**: Limit filings analyzed per run (e.g., MAX_DEF14A_FILINGS_TO_ANALYZE = 3)
- **Cache First**: Check cache before making SEC API calls
- **Circuit Breaker**: Enable for production to handle SEC API outages

## Common Pitfalls to Avoid

1. ❌ **Direct V1 Imports**: Don't import V1 versions when V2 exists
2. ❌ **Rate Limit Violations**: Always use `SharedRateLimiter`
3. ❌ **Missing Type Hints**: All function parameters need types
4. ❌ **Synchronous I/O**: Use async/await for SEC API calls
5. ❌ **Modifying Evidence**: Never alter original documents
6. ❌ **Silent Failures**: Always log errors and return error status

## Strict Execution Mode

When implementing features that run in strict mode:

- **Phase Gates**: Validate data contracts between phases
- **Exit Codes**: Use specific codes (0-7) for different failure types
- **Cascade Abort**: Halt execution on critical failures
- **Abort Reports**: Generate human-readable failure reports with remediation

Exit codes:
- `0`: Complete success
- `1`: Configuration failure
- `2`: Data collection failure
- `3`: Document parsing failure
- `4`: Node execution below threshold
- `5`: Pattern detection failure
- `6`: Evidence chain integrity failure
- `7`: Dossier generation failure

## Detection Patterns

The system implements 23+ detection algorithms including:

- **Options Backdating** (Erik Lie methodology)
- **Channel Stuffing** (DSO analysis)
- **Spring Loading** (Pre-announcement timing)
- **Bullet Dodging** (Post-bad-news timing)
- **Round-tripping** (Revenue manipulation)
- **Cookie Jar Reserves** (Earnings smoothing)

When adding new patterns, follow `AdvancedPatternDetector` structure.

## Resources

- **Main Entry Point**: `JLAW_UNIFIED.py`
- **Core Engine**: `src/core/recursive_engine.py`
- **Node Exports**: `src/nodes/__init__.py`
- **SEC Client**: `src/integrations/sec_edgar/edgar_client.py`
- **Documentation**: `README.md`, `HOLY_GRAIL_PIPELINE.md`, `STRICT_EXECUTION_MODE.md`

## Quick Reference Commands

```bash
# Run interactive analysis
python JLAW_UNIFIED.py

# Run with parameters
python JLAW_UNIFIED.py --cik 320187 --company "NIKE, Inc." --year 2019

# Strict mode (DOJ-grade)
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strict --auto

# Verify SEC configuration
python -c "from config.secure_config import print_configuration_status; print_configuration_status()"
```
