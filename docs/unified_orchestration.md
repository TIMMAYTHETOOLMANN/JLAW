# Unified Agent Orchestration Architecture

## Overview

The **Unified Agent Orchestrator** is the central coordination layer for JLAW's multi-tier investigation system. It harmonizes four distinct agent tiers into a single, coordinated workflow, providing context propagation, result aggregation, and comprehensive execution metrics.

**Version:** 1.0.0  
**Location:** `src/core/unified_agent_orchestrator.py`  
**Integration Point:** Phase 7 of Master Execution Controller

---

## Architecture

### Four-Tier Agent System

The orchestrator coordinates **4 distinct agent tiers**, each with specialized capabilities:

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIFIED AGENT ORCHESTRATOR                   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ TIER 1: PRIMARY DUAL-AGENT                                │ │
│  │ • OpenAI Agent SDK (gpt-4)                                │ │
│  │ • Anthropic Agent SDK (claude-3-5-sonnet-20241022)        │ │
│  │ • Initial violation detection                             │ │
│  │ • Cross-reference validation                              │ │
│  │ • Weight: 40% of consensus                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            ↓                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ TIER 2: INTELLIGENT SUBAGENT ROUTING                      │ │
│  │ • 10 Specialized Claude agents                            │ │
│  │ • Dynamic agent selection (top-K)                         │ │
│  │ • Parallel execution stages                               │ │
│  │ • Violation-type based routing                            │ │
│  │ • Weight: 40% of consensus                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            ↓                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ TIER 3: PATTERN DETECTION ALGORITHMS                      │ │
│  │ • 23 fraud detection patterns                             │ │
│  │ • M-Score, Z-Score, Benford's Law                         │ │
│  │ • Statistical validation                                  │ │
│  │ • Weight: 20% of consensus                                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            ↓                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ TIER 4: NODE-SPECIFIC ANALYZERS                           │ │
│  │ • 15 document processing nodes                            │ │
│  │ • Form 4, 10-K, 8-K, etc.                                 │ │
│  │ • Structured data extraction                              │ │
│  │ • Weight: Not included in consensus (data only)           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            ↓                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ AGGREGATION & RESULT SYNTHESIS                            │ │
│  │ • Violation deduplication                                 │ │
│  │ • Weighted consensus scoring                              │ │
│  │ • Token usage tracking                                    │ │
│  │ • Evidence chain integration                              │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Investigation Workflow

### Sequential Execution Flow

The orchestrator executes tiers sequentially to enable context propagation:

#### 1. **Tier 1: Primary Dual-Agent Analysis**

**Purpose:** Initial violation detection with dual-agent consensus

**Process:**
- Analyze filings with OpenAI Agent SDK
- Cross-validate with Anthropic Agent SDK
- Detect SEC violations (§16, SOX, 10b-5)
- Generate dual-agent consensus score

**Output:**
```python
{
    "violations": [
        {
            "type": "insider_trading",
            "statute": "17 CFR § 240.10b-5",
            "severity": "HIGH",
            "description": "...",
            "tier": "primary"
        }
    ],
    "consensus": 0.85,
    "agents": ["openai", "anthropic"]
}
```

---

#### 2. **Tier 2: Intelligent Subagent Routing**

**Purpose:** Deep specialized analysis based on Tier 1 findings

**Process:**
- **Intelligent Router** scores 10 Claude agents by relevance
- Selects top-K agents (max 5) based on violation types
- Creates parallel execution stages (3 stages)
- Routes violations to specialized agents:
  - `forensic-financial-analyst` → Financial fraud
  - `forensic-compliance-auditor` → Regulatory violations
  - `forensic-nlp-analyst` → Document analysis
  - etc.

**Output:**
```python
{
    "combined_findings": [
        {
            "agent_name": "forensic-financial-analyst",
            "finding_type": "channel_stuffing",
            "severity": "HIGH",
            "description": "..."
        }
    ],
    "agents_executed": ["forensic-financial-analyst", "forensic-compliance-auditor"],
    "consensus_score": 0.90,
    "routing_decision": {
        "selected_agents": [...],
        "execution_plan": [["agent1", "agent2"], ["agent3"]],
        "agent_scores": {"agent1": 0.95, ...}
    }
}
```

**Context Propagation:**
- Tier 1 violations passed to Tier 2 router
- Router selects agents based on violation types
- Enables intelligent, violation-specific analysis

---

#### 3. **Tier 3: Pattern Detection Algorithms**

**Purpose:** Statistical validation of agent findings

**Process:**
- Run 23 fraud detection patterns
- M-Score (earnings manipulation)
- Z-Score (bankruptcy prediction)
- Benford's Law (number fabrication)
- Insider trading patterns

**Output:**
```python
{
    "patterns_executed": 23,
    "fraud_indicators": [
        {
            "pattern": "M-Score",
            "score": 2.8,
            "threshold": 2.22,
            "result": "FAIL"
        }
    ]
}
```

---

#### 4. **Tier 4: Node-Specific Analyzers**

**Purpose:** Document-type-specific structured data extraction

**Process:**
- Route filings to appropriate node analyzers
- Extract structured data (Form 4 → insider trades)
- Generate filing-specific metrics

**Output:**
```python
{
    "nodes_processed": 10,
    "structured_data": [
        {
            "node": "node1_form4",
            "transactions": [...]
        }
    ]
}
```

---

## Result Aggregation Strategy

### Violation Deduplication

The orchestrator deduplicates violations across all tiers using:

**Deduplication Key:**
```
key = f"{violation_type}|{statute}|{description[:100]}"
```

**Priority:**
- Violations sorted by severity (CRITICAL > HIGH > MEDIUM > LOW)
- Keeps the highest-severity version of duplicates
- Prevents double-counting across tiers

**Example:**
```python
# Input: 3 violations
violations = [
    {"type": "insider_trading", "statute": "10b-5", "severity": "HIGH"},
    {"type": "insider_trading", "statute": "10b-5", "severity": "MEDIUM"},  # Duplicate
    {"type": "accounting_fraud", "statute": "SOX-404", "severity": "CRITICAL"}
]

# Output: 2 violations (duplicate removed)
deduplicated = [
    {"type": "insider_trading", "statute": "10b-5", "severity": "HIGH"},
    {"type": "accounting_fraud", "statute": "SOX-404", "severity": "CRITICAL"}
]
```

---

### Unified Consensus Scoring

The orchestrator computes a **weighted consensus score** across tiers:

**Formula:**
```
Unified Consensus = (Primary × 0.4) + (Subagent × 0.4) + (Pattern × 0.2)
```

**Weights:**
- **Primary Tier:** 40% (dual-agent consensus)
- **Subagent Tier:** 40% (subagent agreement)
- **Pattern Tier:** 20% (patterns executed ratio)
- **Node Tier:** 0% (data extraction only)

**Example:**
```python
tier_results = {
    "primary": {"consensus": 0.85},
    "subagent": {"consensus_score": 0.90},
    "pattern": {"patterns_executed": 20}  # 20/23 = 0.87
}

# Calculation:
unified_consensus = (0.85 × 0.4) + (0.90 × 0.4) + (0.87 × 0.2)
                  = 0.34 + 0.36 + 0.174
                  = 0.874 (87.4%)
```

**Phase Gate Validation (Strict Mode):**
- Requires consensus ≥ 70%
- Aborts execution if below threshold
- Ensures high-confidence findings

---

## Token Usage Tracking

The orchestrator tracks tokens across all tiers:

**Token Sources:**
```python
{
    "primary": {
        "tokens_used": 1500  # OpenAI + Anthropic
    },
    "subagent": {
        "total_tokens": 7500  # 5 agents × ~1500 tokens
    },
    "pattern": {
        "token_count": 0  # Statistical algorithms, no LLM calls
    }
}

total_tokens = 1500 + 7500 + 0 = 9000
```

**Metrics Collected:**
- Per-agent token counts
- Per-tier token aggregation
- Total investigation tokens
- Average tokens per task

---

## Integration with Master Execution Controller

### Phase 7 Enhancement

The orchestrator is integrated into **Phase 7: Subagent Orchestration** of the master controller:

**Backward Compatibility:**
```python
# Environment variable to enable/disable
JLAW_USE_UNIFIED_ORCHESTRATOR=true  # Default: enabled

# Fallback to legacy orchestration if unified fails
if unified_orchestrator_error:
    fallback_to_legacy_subagent_orchestration()
```

**Integration Method:**
```python
async def _execute_phase_7_subagent(self):
    """Execute Phase 7: Unified Agent Orchestration."""
    
    # Initialize orchestrator
    orchestrator = UnifiedAgentOrchestrator()
    
    # Execute multi-tier investigation
    unified_result = await orchestrator.execute_investigation(
        investigation_type="full_forensic",
        filings=self.filings,
        context={"cik": self.cik, "company_name": self.company_name},
        enable_subagents=True,
        enable_patterns=False,  # Already run in Phase 5
        enable_nodes=False      # Already run in Phase 4
    )
    
    # Integrate results
    self._integrate_orchestrator_results(unified_result)
    
    # Phase gate validation
    if strict_mode and unified_result.consensus_score < 0.70:
        raise PhaseGateFailure("Consensus below 70%")
```

**Result Integration:**
```python
def _integrate_orchestrator_results(self, unified_result):
    """Integrate orchestrator results into execution context."""
    
    # Update execution metrics
    self.execution_metrics.update({
        "orchestrator_consensus": unified_result.consensus_score,
        "total_agents_invoked": len(unified_result.agents_invoked),
        "orchestrator_tokens": unified_result.tokens_used
    })
    
    # Add violations to evidence chain
    for violation in unified_result.aggregated_violations:
        self._add_to_evidence_chain(violation)
```

---

## Execution Metrics Framework

### AgentExecutionMetric

Tracks individual agent executions:

```python
@dataclass
class AgentExecutionMetric:
    agent_name: str
    agent_type: str  # "openai", "anthropic", "subagent", "pattern"
    start_time: float
    end_time: float
    duration_seconds: float
    tokens_used: int
    violations_found: int
    status: str  # "success", "error", "timeout"
    tier: str    # "primary", "subagent", "pattern", "node"
```

### ExecutionMetricsCollector

Collects and exports metrics:

```python
collector = ExecutionMetricsCollector()

# Start tracking
metric = collector.start_agent("forensic-financial-analyst", "subagent")

# ... execute agent ...

# End tracking
metric.tokens_used = 1500
metric.violations_found = 3
collector.end_agent(metric, status="success")

# Export metrics
collector.export_metrics("output/agent_metrics.json")
```

**Summary Statistics:**
```python
{
    "total_agents": 8,
    "total_duration": 45.2,
    "total_tokens": 9000,
    "total_violations": 12,
    "success_count": 7,
    "error_count": 1,
    "by_tier": {
        "primary": {"count": 2, "tokens": 1500, ...},
        "subagent": {"count": 5, "tokens": 7500, ...}
    }
}
```

---

## Usage Examples

### Basic Investigation

```python
from src.core.unified_agent_orchestrator import UnifiedAgentOrchestrator

orchestrator = UnifiedAgentOrchestrator()

filings = [
    {
        'form_type': '4',
        'filing_date': '2024-01-15',
        'content': 'Form 4 content...',
        'cik': '320187'
    }
]

context = {
    "cik": "320187",
    "company_name": "NIKE, Inc.",
    "case_id": "CASE-2024-001"
}

result = await orchestrator.execute_investigation(
    investigation_type="form4",
    filings=filings,
    context=context,
    enable_subagents=True,
    enable_patterns=True
)

print(f"Status: {result.status}")
print(f"Violations: {len(result.aggregated_violations)}")
print(f"Consensus: {result.consensus_score:.2%}")
print(f"Tokens: {result.tokens_used}")
```

### Tier-Specific Execution

```python
# Only Tier 1 + Tier 2 (skip patterns and nodes)
result = await orchestrator.execute_investigation(
    investigation_type="full_forensic",
    filings=filings,
    context=context,
    enable_subagents=True,
    enable_patterns=False,
    enable_nodes=False
)
```

### Metrics Export

```python
# Execute investigation
result = await orchestrator.execute_investigation(...)

# Get metrics
metrics = orchestrator.get_metrics()
print(f"Tasks executed: {metrics['tasks_executed']}")
print(f"Total tokens: {metrics['total_tokens_used']}")

# Export to file
orchestrator.export_metrics("output/orchestrator_metrics.json")
```

---

## API Reference

### UnifiedAgentOrchestrator

#### `execute_investigation()`

```python
async def execute_investigation(
    investigation_type: str,
    filings: List[Dict[str, Any]],
    context: Dict[str, Any],
    enable_subagents: bool = True,
    enable_patterns: bool = True,
    enable_nodes: bool = False
) -> UnifiedResult
```

**Parameters:**
- `investigation_type`: Type of investigation ("form4", "10k", "full_forensic")
- `filings`: List of filing dictionaries to analyze
- `context`: Investigation context (CIK, company name, date range)
- `enable_subagents`: Enable Tier 2 subagent routing
- `enable_patterns`: Enable Tier 3 pattern detection
- `enable_nodes`: Enable Tier 4 node processing

**Returns:**
- `UnifiedResult` with aggregated findings from all tiers

#### `get_metrics()`

```python
def get_metrics() -> Dict[str, Any]
```

**Returns:**
- Dictionary with execution metrics:
  - `tasks_executed`: Number of tasks completed
  - `total_tokens_used`: Total tokens across all tiers
  - `tier_invocation_counts`: Per-tier execution counts
  - `sdk_availability`: API availability status

### UnifiedResult

```python
@dataclass
class UnifiedResult:
    task_id: str
    status: str  # "success", "partial", "failure"
    tier_results: Dict[str, Any]
    aggregated_violations: List[Dict[str, Any]]
    consensus_score: float
    execution_time_seconds: float
    tokens_used: int
    agents_invoked: List[str]
    tiers_executed: List[str]
    execution_metrics: Dict[str, Any]
    errors: List[str]
```

---

## Error Handling

### Tier-Level Errors

Each tier execution is wrapped in try/except:

```python
try:
    tier1_result = await self._execute_tier_1_primary(filings, context)
    tier_results["primary"] = tier1_result
except Exception as e:
    logger.error(f"Tier 1 error: {e}")
    errors.append(f"Tier 1 execution error: {str(e)}")
    tier_results["primary"] = {"status": "error", "error": str(e)}
```

**Behavior:**
- Tier errors logged but don't abort entire investigation
- Status set to "partial" if some tiers succeed
- Status set to "failure" if all tiers fail

### Fallback Strategies

**Master Controller Integration:**
```python
try:
    # Try unified orchestrator
    unified_result = await orchestrator.execute_investigation(...)
except Exception as e:
    logger.error(f"Unified orchestrator error: {e}")
    # Fall back to legacy subagent orchestration
    use_legacy_orchestration()
```

---

## Performance Considerations

### Filing Limits

To prevent excessive API costs:

```python
# Tier 1: Limit to 5 filings
for filing in filings[:5]:
    result = await dual_agent.investigate_with_cross_reference(...)

# Tier 2: No limit (processes violations, not filings)
```

### Token Budgets

Estimated token usage:

| Tier | Tokens per Filing | Tokens for 5 Filings |
|------|-------------------|----------------------|
| Tier 1 (Primary) | ~2000 | ~10,000 |
| Tier 2 (Subagents) | ~1500/agent | ~7,500 (5 agents) |
| Tier 3 (Patterns) | 0 (statistical) | 0 |
| Tier 4 (Nodes) | 0 (extraction) | 0 |
| **Total** | - | **~17,500** |

### Parallel Execution

**Tier 2 Subagents:**
- Agents grouped into parallel stages (default: 3)
- Stage 1: agents execute in parallel
- Stage 2: waits for Stage 1, then executes in parallel
- Reduces total execution time

---

## Future Enhancements

### Planned Features

1. **Tier 3 Integration:** Full pattern detection integration
2. **Tier 4 Integration:** Node analyzer coordination
3. **Dynamic Weighting:** Adjust consensus weights based on tier reliability
4. **Conflict Resolution:** Automatic resolution of contradicting findings
5. **Caching:** Cache Tier 1 results for faster Tier 2 execution
6. **Rate Limiting:** Per-tier rate limit enforcement
7. **Cost Optimization:** Token budget enforcement and optimization

### Integration Opportunities

- **Evidence Chain:** Automatic evidence provenance tracking
- **Dossier Generation:** Direct integration with DOJ-grade reports
- **Real-time Monitoring:** Live orchestration metrics dashboard
- **Audit Logging:** Comprehensive audit trail for all tier executions

---

## Troubleshooting

### Common Issues

**Issue:** Unified orchestrator not enabled
```
Solution: Set JLAW_USE_UNIFIED_ORCHESTRATOR=true (default)
```

**Issue:** Low consensus score (< 70%)
```
Solution: 
- Check tier execution logs for errors
- Verify API keys for OpenAI/Anthropic
- Review violation quality from Tier 1
```

**Issue:** High token usage
```
Solution:
- Reduce number of filings analyzed
- Disable Tier 2 subagents for initial testing
- Set enable_subagents=False
```

**Issue:** Tier execution errors
```
Solution:
- Check API availability: orchestrator.sdk_manager.get_availability()
- Verify .env configuration
- Review tier-specific error logs
```

---

## Testing

### Unit Tests

Location: `tests/test_unified_agent_orchestrator.py`

**Test Coverage:**
- Orchestrator initialization
- Investigation workflow execution
- Violation deduplication
- Consensus computation
- Token counting
- Error handling
- Metrics collection

**Run Tests:**
```bash
cd /home/runner/work/JLAW/JLAW
PYTHONPATH=. pytest tests/test_unified_agent_orchestrator.py -v
```

---

## References

- **Master Execution Controller:** `src/core/master_execution_controller.py`
- **Dual-Agent Coordinator:** `src/forensics/dual_agent.py`
- **Intelligent Router:** `src/forensics/intelligent_router.py`
- **SDK Manager:** `src/forensics/sdk_manager.py`
- **Agent Registry:** `src/forensics/agent_registry.py`

---

## Changelog

### Version 1.0.0 (2024-12-29)

**Initial Release:**
- Four-tier agent coordination
- Context propagation (Tier 1 → Tier 2)
- Violation deduplication
- Weighted consensus scoring
- Execution metrics framework
- Master controller integration
- Phase gate validation
- Backward compatibility
