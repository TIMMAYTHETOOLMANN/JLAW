# Intelligent Routing Guide

## Overview

The **Intelligent Subagent Router** provides advanced multi-agent orchestration with intelligent agent selection, parallel execution staging, result fusion, and consensus tracking. It replaces hardcoded agent spawning with dynamic, capability-driven routing.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│            IntelligentSubagentRouter                          │
│                                                               │
│  1. Plan Execution Strategy                                   │
│     ├── Score agents based on violation relevance             │
│     ├── Select top-K agents                                   │
│     └── Create parallel execution stages                      │
│                                                               │
│  2. Execute Multi-Stage Workflow                              │
│     ├── Stage 1: High priority agents (parallel)              │
│     ├── Stage 2: Medium priority agents (parallel)            │
│     └── Stage 3: Low priority agents (parallel)               │
│                                                               │
│  3. Aggregate Results                                         │
│     ├── Fuse findings from all agents                         │
│     ├── Compute consensus score                               │
│     ├── Detect conflicts                                      │
│     └── Flag for manual review                                │
└───────────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. Routing Decision

A routing decision contains the execution plan:

```python
@dataclass
class RoutingDecision:
    selected_agents: List[AgentCapability]      # Agents to execute
    execution_plan: List[List[str]]             # Stages (agent names)
    estimated_cost: float                       # Token cost estimate
    confidence_threshold: float                 # Minimum consensus
    agent_scores: Dict[str, float]              # Relevance scores
```

### 2. Agent Result

Each agent produces a structured result:

```python
@dataclass
class AgentResult:
    agent_name: str                             # Agent identifier
    status: str                                 # 'success', 'error', 'timeout'
    findings: Dict[str, Any]                    # Agent findings
    recommendations: List[str]                  # Recommendations
    severity: str                               # 'critical', 'high', 'medium', 'low'
    execution_time: float                       # Seconds
    error: Optional[str]                        # Error message if failed
```

### 3. Consensus Tracking

Measures agent agreement:

```python
consensus_score = (most_common_severity_count) / (total_successful_agents)
# Range: 0.0 (no agreement) to 1.0 (complete agreement)
```

## Usage

### Basic Usage

```python
from src.forensics.intelligent_router import IntelligentSubagentRouter
from src.forensics.agent_registry import DynamicAgentRegistry

# Initialize
registry = DynamicAgentRegistry()
router = IntelligentSubagentRouter(registry)

# Define violations
violations = [
    {"type": "insider_trading", "confidence": 0.92},
    {"type": "late_form4", "days_late": 5}
]

# Plan execution
decision = router.plan_execution(
    violations=violations,
    max_agents=5,           # Top-5 most relevant
    parallel_stages=3       # 3 execution stages
)

# Execute plan
result = await router.execute(
    decision=decision,
    violations=violations,
    context={"cik": "320187", "company": "Test Corp"},
    orchestrator=None       # Optional: SubagentOrchestrator instance
)

print(f"Status: {result['status']}")
print(f"Agents executed: {result['agents_executed']}")
print(f"Consensus score: {result['consensus_score']:.2%}")
print(f"Conflicts: {len(result['conflicts'])}")
```

### Integrated with Orchestrator

```python
from src.forensics.subagents.orchestrator import SubagentOrchestrator

orchestrator = SubagentOrchestrator()
# Router is initialized automatically

violations = [{"type": "insider_trading"}]
result = await orchestrator.auto_orchestrate(violations, parallel=True)

# Result includes new Phase 2 fields:
# - consensus_score: Agent agreement metric
# - conflicts: List of conflicting findings
# - execution_time: Total execution time
```

## Execution Planning

### Agent Scoring

Agents are scored based on violation type match:

```python
# Agent with violations: ["insider_trading", "accounting_fraud"]
# Test violations: ["insider_trading", "late_form4"]

score = matches / total_violations
# score = 1/2 = 0.5 (50% relevance)
```

### Agent Selection

Top-K agents are selected and sorted by:

1. **Match Score** (descending) - More relevant violations
2. **Priority** (descending) - Higher priority first
3. **Agent Name** (ascending) - Alphabetical for determinism

```python
# Example: 3 agents for ["insider_trading"]
# 
# Agent A: score=1.0, priority=90 → Selected (1st)
# Agent B: score=1.0, priority=80 → Selected (2nd)
# Agent C: score=0.5, priority=85 → Selected (3rd)
# Agent D: score=0.0, priority=95 → Not selected (no match)
```

### Parallel Staging

Agents are grouped into stages based on priority:

```python
# Input: 6 agents with priorities [90, 85, 80, 75, 70, 65]
# Stages: 3

# Stage 1: [agent1(90), agent2(85)]  # High priority
# Stage 2: [agent3(80), agent4(75)]  # Medium priority
# Stage 3: [agent5(70), agent6(65)]  # Low priority

# Agents in same stage execute in parallel
# Stages execute sequentially
```

**Benefits:**
- High priority agents start first
- Parallel execution within stages
- Resource optimization
- Faster overall execution

## Result Aggregation

### Finding Fusion

Findings from all agents are combined:

```python
combined_findings = [
    {
        "agent": "financial-analyst",
        "findings": {"mscore": -1.52, "alert": True},
        "recommendations": ["Investigate revenue"],
        "severity": "high",
        "execution_time": 2.3
    },
    {
        "agent": "compliance-auditor",
        "findings": {"violations": ["Rule 10b-5"]},
        "recommendations": ["DOJ referral"],
        "severity": "high",
        "execution_time": 1.8
    }
]
```

### Consensus Computation

Measures agreement across agents:

```python
# Example: 5 agents complete successfully
# Severity assessments: ["high", "high", "high", "medium", "medium"]
# Most common: "high" (3 occurrences)

consensus_score = 3 / 5 = 0.60  # 60% agreement
```

**Interpretation:**
- 1.0 = Perfect agreement (all agents agree)
- 0.8+ = Strong consensus
- 0.6-0.8 = Moderate consensus
- <0.6 = Weak consensus (review recommended)

### Conflict Detection

Identifies disagreements requiring manual review:

```python
conflicts = [
    {
        "type": "severity_conflict",
        "description": "Agents disagree on severity: {...}",
        "agents_involved": ["agent1", "agent2"]
    }
]
```

**Conflict Types:**
- `severity_conflict`: Agents assess different severity levels
- Future: `finding_conflict`, `recommendation_conflict`

## Cost Estimation

Simple heuristic for token usage:

```python
estimated_cost = num_agents * num_violations * $0.01
# Example: 5 agents × 2 violations = $0.10
```

**Future Enhancements:**
- Actual token counting per agent
- Model-specific pricing (Claude 3.5 Sonnet, etc.)
- Dynamic cost optimization

## Advanced Features

### Custom Confidence Threshold

```python
decision = router.plan_execution(
    violations=violations,
    confidence_threshold=0.8  # Require 80% consensus
)

# Later: Use threshold for automated decisions
if result['consensus_score'] >= decision.confidence_threshold:
    print("High confidence - proceed with prosecution")
else:
    print("Low confidence - manual review required")
```

### Sequential Execution

```python
decision = router.plan_execution(
    violations=violations,
    parallel_stages=1  # Single stage = all sequential
)
```

### Execution History

```python
history = router.get_execution_history()

for record in history:
    print(f"Timestamp: {record['timestamp']}")
    print(f"Violations: {record['violations_count']}")
    print(f"Agents executed: {record['agents_executed']}")
    print(f"Consensus: {record['consensus_score']:.2%}")
```

### Custom Agent Prompts

```python
# Build prompt for specific agent
capability = registry.get_agent("forensic-financial-analyst")
prompt = router.build_agent_prompt(
    agent=capability,
    violations=violations,
    context={"cik": "320187", "filings": [...]}
)
```

## Integration Patterns

### Pattern 1: Auto-Orchestration (Default)

```python
orchestrator = SubagentOrchestrator()
result = await orchestrator.auto_orchestrate(violations)
# Uses intelligent router automatically
```

### Pattern 2: Manual Planning

```python
router = IntelligentSubagentRouter()

# Plan with custom settings
decision = router.plan_execution(
    violations=violations,
    max_agents=3,
    parallel_stages=2,
    confidence_threshold=0.85
)

# Review plan before execution
print(f"Will execute: {[a.agent_name for a in decision.selected_agents]}")
print(f"Estimated cost: ${decision.estimated_cost:.2f}")

# Execute
result = await router.execute(decision, violations, context={})
```

### Pattern 3: Iterative Refinement

```python
# First pass: Quick analysis with top-3 agents
decision1 = router.plan_execution(violations, max_agents=3)
result1 = await router.execute(decision1, violations, context={})

if result1['consensus_score'] < 0.7:
    # Low consensus - add more agents
    decision2 = router.plan_execution(violations, max_agents=7)
    result2 = await router.execute(decision2, violations, context={})
```

## Performance Considerations

### Agent Count vs. Quality

| Agents | Pros | Cons |
|--------|------|------|
| 1-3 | Fast, low cost | May miss issues, low confidence |
| 4-6 | Balanced, good consensus | Moderate cost, reasonable time |
| 7-10 | High coverage, strong consensus | Higher cost, longer execution |
| 10+ | Comprehensive | Expensive, diminishing returns |

**Recommendation:** Start with 5 agents (top_k=5)

### Parallel Stages vs. Latency

| Stages | Execution Time | Use Case |
|--------|----------------|----------|
| 1 | Sequential (slowest) | Debugging, testing |
| 2-3 | Balanced | Production (recommended) |
| 4+ | Highly parallel | Large agent pools |

**Recommendation:** Use 3 stages for production

### Cost Optimization

```python
# Strategy 1: Limit agent count
decision = router.plan_execution(violations, max_agents=3)  # Not 10

# Strategy 2: Filter low-relevance violations
high_confidence = [v for v in violations if v.get('confidence', 0) > 0.8]
decision = router.plan_execution(high_confidence, max_agents=5)

# Strategy 3: Cache results (future enhancement)
# Router could cache agent results for identical inputs
```

## Testing

### Unit Tests

```python
# Test execution planning
def test_plan_execution():
    router = IntelligentSubagentRouter()
    violations = [{"type": "insider_trading"}]
    
    decision = router.plan_execution(violations, max_agents=5)
    
    assert len(decision.selected_agents) <= 5
    assert len(decision.execution_plan) > 0
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_workflow():
    router = IntelligentSubagentRouter()
    violations = [{"type": "insider_trading"}]
    
    decision = router.plan_execution(violations)
    result = await router.execute(decision, violations, context={})
    
    assert result['status'] in ['completed', 'failed']
    assert 'consensus_score' in result
```

## Troubleshooting

### No Agents Selected

```python
# Check if agents have violation types defined
registry = DynamicAgentRegistry()
stats = registry.get_statistics()
print(f"Violation coverage: {stats['violation_coverage']}")

# If empty, agents don't have "## Violation Types" section
# Router will fall back to compliance auditor
```

### Low Consensus Score

```python
# Investigate agent disagreements
if result['consensus_score'] < 0.6:
    print("Low consensus detected:")
    for conflict in result['conflicts']:
        print(f"  - {conflict['type']}: {conflict['description']}")
    
    # Review individual agent findings
    for finding in result['combined_findings']:
        print(f"{finding['agent']}: severity={finding['severity']}")
```

### High Execution Time

```python
# Check execution history
history = router.get_execution_history()
avg_time = sum(r['execution_time'] for r in history) / len(history)
print(f"Average execution time: {avg_time:.1f}s")

# Reduce stages or agent count
decision = router.plan_execution(violations, max_agents=3, parallel_stages=2)
```

## Future Enhancements

### Phase 3 (Planned)
- Agent dependency resolution (e.g., Agent B requires Agent A output)
- Conditional execution (skip agents based on confidence)
- Dynamic stage sizing (adjust parallelism based on load)

### Phase 4 (Planned)
- Result caching (avoid redundant API calls)
- Agent performance tracking (success rate, latency)
- Automatic agent selection tuning (ML-based)

## Examples

See:
- `examples/intelligent_routing_demo.py` - Complete examples
- `tests/test_intelligent_router.py` - Unit tests
- `src/forensics/subagents/orchestrator.py` - Integration example

## API Reference

### IntelligentSubagentRouter

```python
class IntelligentSubagentRouter:
    def __init__(self, registry: Optional[DynamicAgentRegistry] = None)
    
    def plan_execution(
        self,
        violations: List[Dict[str, Any]],
        max_agents: int = 5,
        parallel_stages: int = 3,
        confidence_threshold: float = 0.7
    ) -> RoutingDecision
    
    async def execute(
        self,
        decision: RoutingDecision,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any],
        orchestrator: Optional[Any] = None
    ) -> Dict[str, Any]
    
    def build_agent_prompt(
        self,
        agent: AgentCapability,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str
    
    def get_execution_history(self) -> List[Dict[str, Any]]
```

## See Also

- [Agent Registry Guide](./agent_registry.md) - Agent development and discovery
- [SDK Manager Guide](./sdk_integration.md) - API client management
- [JLAW Architecture](../README.md) - System overview
