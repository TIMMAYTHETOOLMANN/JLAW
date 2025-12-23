# ADR-003: Node Execution Strategy

**Status:** Accepted

**Date:** 2025-12-23

**Decision Makers:** JLAW Engineering Team

---

## Context

JLAW implements a 15-node recursive prosecutorial engine for forensic analysis of SEC filings. Each node specializes in a specific domain (insider trading, compensation, financial reporting, etc.). The original implementation executed all 15 nodes sequentially for every investigation, regardless of:

- Investigation objectives (insider trading vs financial fraud)
- Available filing types (some companies don't file all forms)
- Resource constraints (API rate limits, execution time)
- Prior node findings (some nodes depend on others)

This resulted in:
- Unnecessary API calls to SEC EDGAR
- Wasted execution time (30-60 minutes for simple triage)
- Resource exhaustion on API rate limits
- Poor user experience for focused investigations

## Decision

Implement **intelligent node selection strategy** with three execution modes:

### 1. Investigation Type-Based Selection

Map investigation types to required/optional nodes:

**INSIDER_TRADING:**
- **Required**: Node 1 (Form 4), Node 10 (Form 144), Node 15 (Market Correlation)
- **Recommended**: Node 7 (13F), Node 8 (13D/13G), Node 9 (8-K), Node 11 (Network)
- **Optional**: Nodes 2-6, 12-14
- **Speedup**: ~60% (5-7 nodes vs 15)

**FINANCIAL_FRAUD:**
- **Required**: Node 2 (DEF 14A), Node 3 (10-Q), Node 4 (10-K), Node 5 (IRC), Node 13 (Z-Score), Node 14 (F-Score)
- **Recommended**: Node 1 (Form 4), Node 9 (8-K), Node 12 (Earnings Calls)
- **Optional**: Nodes 6-8, 10-11, 15
- **Speedup**: ~40% (9 nodes vs 15)

**COMPLIANCE:**
- **Required**: Node 3 (10-Q), Node 4 (10-K SOX), Node 9 (8-K)
- **Recommended**: Node 2 (DEF 14A), Node 6 (Routing), Node 12 (Earnings)
- **Optional**: Nodes 1, 5, 7-8, 10-11, 13-15
- **Speedup**: ~50% (6-7 nodes vs 15)

**COMPREHENSIVE:**
- **Required**: All 15 nodes
- **No optimization**

### 2. Filing Availability-Based Selection

Skip nodes if required filings not available:

```python
FILING_NODE_MAP = {
    "4": [1],                    # Form 4 → Node 1
    "DEF 14A": [2, 11],          # Proxy → Node 2, 11
    "10-Q": [3, 13, 14],         # Quarterly → Node 3, 13, 14
    "10-K": [4, 13, 14],         # Annual → Node 4, 13, 14
    "13F-HR": [7],               # Institutional → Node 7
    "SC 13D": [8],               # Ownership → Node 8
    "8-K": [9],                  # Material Events → Node 9
    "144": [10],                 # Restricted Sales → Node 10
}

DERIVED_DATA_NODES = [5, 6, 11, 13, 14, 15]  # Can run without direct filings
```

### 3. Dynamic Skip Logic

Skip nodes based on prior findings:

- **Node 5 (IRC)**: Skip if Node 2 found no compensation issues
- **Node 6 (Routing)**: Skip if no violations found in Nodes 1-5
- **Node 11 (Network)**: Skip if no insider trades in Node 1
- **Node 15 (Market)**: Skip if no price-sensitive events detected

### Implementation

**IntelligentOrchestrator (`src/core/intelligent_orchestrator.py`):**

```python
class IntelligentOrchestrator:
    def create_execution_plan(
        self,
        investigation_type: InvestigationType,
        available_filings: List[Dict[str, Any]],
        resource_constraints: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        # 1. Get node priorities for investigation type
        priorities = self.NODE_PRIORITIES[investigation_type]
        
        # 2. Filter by filing availability
        available_nodes = self._filter_by_filings(
            priorities["required"],
            available_filings
        )
        
        # 3. Add derived data nodes
        available_nodes.extend([n for n in self.DERIVED_DATA_NODES])
        
        # 4. Build execution plan
        return ExecutionPlan(
            required_nodes=available_nodes,
            optional_nodes=priorities.get("recommended", []),
            skipped_nodes=[n for n in range(1, 16) if n not in available_nodes],
            investigation_type=investigation_type.value,
            optimization_percentage=self._calculate_optimization(available_nodes)
        )
```

**Usage in MasterExecutionController:**

```python
# Create optimized plan
plan = intelligent_orchestrator.create_execution_plan(
    investigation_type=InvestigationType.INSIDER_TRADING,
    available_filings=filings
)

# Execute only required nodes
for node_id in plan.required_nodes:
    result = await engine.run_single_node(node_id, ...)
```

## Consequences

### Positive

- **30-50% Execution Speedup**: Focused investigations run much faster
- **Reduced API Calls**: Fewer SEC EDGAR requests = lower rate limit risk
- **Better UX**: Triage mode (5-10 min) vs full mode (30-60 min)
- **Resource Efficiency**: Don't waste compute on irrelevant nodes
- **Cost Savings**: Fewer AI API calls (DeBERTa, OpenAI, Anthropic)

### Negative

- **Complexity**: Node selection logic adds complexity
- **Miss Risk**: Might miss violations if node skipped incorrectly
- **Testing Burden**: Must test all investigation type combinations
- **Documentation**: Need clear guidance on when to use each mode

### Neutral

- **Optional Feature**: Comprehensive mode still available
- **Backward Compatible**: Default behavior unchanged
- **Tunable**: Node priorities can be adjusted based on findings

## Alternatives Considered

### Alternative 1: Always Execute All 15 Nodes

- **Description**: Original approach - no optimization
- **Pros**: Comprehensive, no miss risk
- **Cons**: Slow (30-60 min), wasteful, poor UX for triage
- **Reason for rejection**: User feedback demanded faster triage mode

### Alternative 2: User-Selected Node Subset

- **Description**: Let user manually pick which nodes to run
- **Pros**: Maximum control
- **Cons**: Requires deep system knowledge, error-prone
- **Reason for rejection**: Too complex for typical users

### Alternative 3: Machine Learning-Based Prediction

- **Description**: Train ML model to predict which nodes will find violations
- **Pros**: Optimal node selection based on historical data
- **Cons**: Requires training data, black box, legal risk
- **Reason for rejection**: Too complex for current maturity level, legal concerns

### Alternative 4: Parallel Execution of All Nodes

- **Description**: Run all 15 nodes in parallel
- **Pros**: Fast (limited by slowest node)
- **Cons**: Resource intensive, API rate limit violations, cost
- **Reason for rejection**: SEC EDGAR rate limits (10 req/sec) prevent full parallelization

## Implementation Notes

### Execution Strategies

**TRIAGE (5-10 minutes):**
- Uses IntelligentOrchestrator
- Investigation type-based node selection
- No strict gates or AI cross-validation
- Fast assessment for initial triage

**STANDARD (15-30 minutes):**
- Uses MasterExecutionController with optimization
- All 15 nodes but with dynamic skipping
- Strict gates enabled
- Dual-agent AI validation

**DOJ_REFERRAL (30-60 minutes):**
- Uses ForensicMetaOrchestrator
- All 15 nodes, no optimization
- Maximum evidence chain integrity
- Exhaustive analysis for DOJ-grade referrals

### CLI Integration

```bash
# Triage mode - fast insider trading check
python JLAW_UNIFIED.py --cik 320187 --year 2019 \
  --strategy triage \
  --type insider_trading

# Standard mode - comprehensive analysis
python JLAW_UNIFIED.py --cik 320187 --year 2019 \
  --strategy standard \
  --type comprehensive

# DOJ mode - exhaustive prosecutorial referral
python JLAW_UNIFIED.py --cik 320187 --year 2019 \
  --strategy doj_referral \
  --strict --auto
```

### Metrics Tracking

Track optimization effectiveness:

```python
execution_metrics = {
    "nodes_executed": 7,
    "nodes_skipped": 8,
    "optimization_percentage": 53.3,
    "execution_time_seconds": 450,
    "estimated_time_saved_seconds": 600
}
```

### Migration Path

**Phase 1** (Week 1):
- Deploy IntelligentOrchestrator
- Add --strategy and --type CLI flags
- Default to comprehensive mode (no change)

**Phase 2** (Week 2):
- Enable triage mode for rapid assessments
- Document use cases for each mode
- Collect user feedback

**Phase 3** (Month 1):
- Tune node priorities based on violation detection rates
- Add ML-based prediction (optional, experimental)
- Consider parallel execution for independent nodes

### Rollback Strategy

If optimization causes missed violations:
1. Revert to comprehensive mode as default
2. Make optimization opt-in only (--optimize flag)
3. Investigate false negative rate
4. Adjust node priorities and retry

## References

- **Related ADRs:**
  - ADR-001: Orchestration Hierarchy Design
  - ADR-002: Evidence Chain Architecture

- **Code References:**
  - `src/core/intelligent_orchestrator.py` - Node selection logic
  - `src/core/supreme_orchestrator.py` - Strategy-based routing
  - `src/core/master_execution_controller.py` - Execution controller
  - `JLAW_UNIFIED.py` - CLI integration

- **Node Implementations:**
  - `src/nodes/node1_form4/` - Insider trading
  - `src/nodes/node2_def14a/` - Executive compensation
  - `src/nodes/node3_10q/` - Quarterly reporting
  - `src/nodes/node4_10k/` - Annual reporting with SOX
  - `src/nodes/node5_irc83/` - Tax exposure
  - `src/nodes/node6_routing/` - Regulatory routing
  - `src/nodes/node7_13f_holdings/` - Institutional holdings
  - `src/nodes/node8_13d_ownership/` - Beneficial ownership
  - `src/nodes/node9_8k_events/` - Material events
  - `src/nodes/node10_form144/` - Restricted stock sales
  - `src/nodes/node11_network/` - Executive networks
  - `src/nodes/node12_earnings/` - Earnings call transcripts
  - `src/nodes/node13_zscore/` - Bankruptcy prediction
  - `src/nodes/node14_fscore/` - Financial strength
  - `src/nodes/node15_market/` - Market correlation

- **Documentation:**
  - `HOLY_GRAIL_PIPELINE.md` - Visual node pipeline
  - `README.md` - Usage examples

- **Research:**
  - Performance benchmarks showing 30-50% speedup
  - User studies on triage vs comprehensive modes
  - False negative analysis for optimized execution

---

## Metadata

- **ADR Number:** 003
- **Created:** 2025-12-23
- **Last Updated:** 2025-12-23
- **Authors:** JLAW Engineering Team
- **Reviewers:** N/A
