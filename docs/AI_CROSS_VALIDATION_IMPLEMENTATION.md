# AI Cross-Validation + SupremeOrchestrator Implementation

## Overview

This implementation addresses two critical gaps in the JLAW forensic analysis platform:

1. **AI Cross-Validation for Detection Patterns**: Quantitative fraud scores are now validated by dual AI agents (OpenAI + Anthropic) to provide human-like reasoning and confidence assessment.

2. **SupremeOrchestrator Meta-Controller**: A unified intelligent entry point that automatically selects the optimal execution strategy based on investigation priority.

## Part A: AI Cross-Validation for Detection Patterns

### What Was Added

#### 1. New Functions in `src/detection/patterns/advanced_patterns.py`

##### `cross_validate_pattern_with_ai()`
Cross-validates a single quantitative pattern detection result using dual AI agents.

**Signature:**
```python
async def cross_validate_pattern_with_ai(
    pattern_name: str,
    score: float,
    evidence: Dict[str, Any],
    dual_agent: Any,
    threshold: float = 0.7
) -> Dict[str, Any]
```

**Returns:**
- `ai_confidence`: Average confidence from both agents (0-100%)
- `validation_status`: "validated", "rejected", or "uncertain"
- `reasoning`: Combined reasoning from both agents
- `supporting_factors`: List of factors supporting the finding
- `contradicting_factors`: List of factors contradicting the finding
- `recommendations`: Action recommendations from agents
- `openai_analysis`: Raw OpenAI agent response
- `anthropic_analysis`: Raw Anthropic agent response

**Example Usage:**
```python
from src.detection.patterns.advanced_patterns import cross_validate_pattern_with_ai
from src.forensics.dual_agent import DualAgentCoordinator

dual_agent = DualAgentCoordinator()

result = await cross_validate_pattern_with_ai(
    pattern_name="Beneish M-Score",
    score=-2.8,
    evidence={"dsri": 1.2, "gmi": 0.95},
    dual_agent=dual_agent
)

print(f"AI Confidence: {result['ai_confidence']:.1f}%")
print(f"Status: {result['validation_status']}")
```

##### `batch_cross_validate_patterns()`
Cross-validates multiple pattern detection results in batch, filtering by severity.

**Signature:**
```python
async def batch_cross_validate_patterns(
    pattern_results: List[Dict[str, Any]],
    dual_agent: Any,
    severity_filter: Optional[List[str]] = None
) -> Dict[str, Any]
```

**Default Behavior:** Only validates HIGH and CRITICAL severity patterns.

**Returns:**
- `validated_patterns`: List of patterns with AI validation results
- `total_patterns`: Total number of patterns processed
- `patterns_evaluated`: Number of patterns that matched severity filter
- `validated_count`: Number of patterns validated by AI
- `rejected_count`: Number of patterns rejected by AI
- `uncertain_count`: Number of patterns with uncertain validation
- `average_ai_confidence`: Average AI confidence across all validations
- `high_confidence_findings`: Patterns with AI confidence > 85%

**Example Usage:**
```python
from src.detection.patterns.advanced_patterns import batch_cross_validate_patterns

pattern_results = [
    {
        "pattern_name": "Beneish M-Score",
        "severity": "CRITICAL",
        "score": -2.8,
        "confidence": 0.92,
        "evidence": {"dsri": 1.465}
    },
    {
        "pattern_name": "Altman Z-Score",
        "severity": "HIGH",
        "score": 1.2,
        "confidence": 0.85,
        "evidence": {"working_capital_ratio": 0.15}
    }
]

result = await batch_cross_validate_patterns(
    pattern_results=pattern_results,
    dual_agent=dual_agent,
    severity_filter=["HIGH", "CRITICAL"]
)

print(f"Validated: {result['validated_count']}")
print(f"Avg Confidence: {result['average_ai_confidence']:.1f}%")
```

#### 2. Integration in `src/core/master_execution_controller.py`

##### New Attribute: `ai_validation_results`
Stores AI cross-validation results for pattern detection.

```python
self.ai_validation_results: Dict[str, Any] = {}
```

##### New Method: `_should_cross_validate()`
Determines if AI cross-validation should run based on:
- Detection results exist
- Patterns were executed
- Patterns have findings
- Not disabled via environment variable (`JLAW_DISABLE_AI_VALIDATION`)

##### Phase 5 Integration
AI cross-validation now runs automatically in Phase 5 after pattern detection:

1. Pattern detection executes (23 algorithms)
2. `_should_cross_validate()` checks if validation should run
3. If enabled:
   - Initialize `DualAgentCoordinator`
   - Convert NLP findings to pattern format
   - Call `batch_cross_validate_patterns()` for HIGH/CRITICAL patterns
   - Store results in `self.ai_validation_results`
4. Log validation summary

**Execution Flow:**
```
Phase 5: Advanced Detection Patterns
  ├── Execute 23 detection algorithms
  ├── Collect pattern findings
  └── AI Cross-Validation (NEW!)
      ├── Check if dual agents available
      ├── Filter HIGH/CRITICAL severity patterns
      ├── Batch cross-validate with dual agents
      └── Store validation results
```

### Configuration

AI cross-validation is **enabled by default**. To disable:

```bash
export JLAW_DISABLE_AI_VALIDATION=true
```

### Test Coverage

**File:** `tests/test_ai_cross_validation.py`

- ✅ 9 test cases covering:
  - Successful validation
  - High confidence validation → "validated" status
  - Low confidence validation → "rejected" status
  - Error handling
  - Batch filtering by severity
  - Batch statistics calculation
  - High confidence findings identification
  - PatternSeverity enum handling
  - Empty pattern list handling

**Run tests:**
```bash
pytest tests/test_ai_cross_validation.py -v
```

---

## Part B: SupremeOrchestrator Meta-Controller

### What Was Added

#### New File: `src/core/supreme_orchestrator.py`

A unified meta-controller that intelligently selects execution strategy based on investigation priority.

### Architecture

```
SupremeOrchestrator (Unified Entry Point)
    ├── TRIAGE → IntelligentOrchestrator (5-10 min)
    ├── STANDARD → MasterExecutionController (15-30 min)
    └── DOJ_REFERRAL → ForensicMetaOrchestrator (30-60 min)
```

### Core Components

#### 1. `InvestigationPriority` Enum

```python
class InvestigationPriority(Enum):
    TRIAGE = "triage"              # Fast 5-10 min scan
    STANDARD = "standard"          # Full 15-30 min analysis
    DOJ_REFERRAL = "doj_referral"  # Exhaustive 30-60 min DOJ-grade
```

#### 2. `ExecutionStrategy` Dataclass

```python
@dataclass
class ExecutionStrategy:
    orchestrator_name: str
    priority: InvestigationPriority
    estimated_duration_seconds: float
    node_count: int
    enable_strict_gates: bool
    enable_ai_validation: bool
    enable_parallel_execution: bool
    optimization_level: str
    description: str
```

#### 3. `SupremeExecutionResult` Dataclass

Complete result from supreme orchestrator execution with:
- CIK, company name, priority, strategy
- Orchestrator used
- Execution timestamps
- Node results, detection results, AI validation results
- Evidence chain, dossier path
- Total violations and alerts
- Error list

#### 4. `SupremeOrchestrator` Class

##### Key Methods

###### `select_strategy(priority, filings, available_resources)`

Selects optimal execution strategy based on investigation priority.

**Returns:** `ExecutionStrategy` with configuration

**Example:**
```python
supreme = SupremeOrchestrator()
strategy = supreme.select_strategy("standard", filings=[])

print(f"Orchestrator: {strategy.orchestrator_name}")
print(f"Duration: {strategy.estimated_duration_seconds/60:.1f} min")
print(f"Nodes: {strategy.node_count}")
print(f"AI Validation: {strategy.enable_ai_validation}")
```

###### `auto_execute(cik, company_name, dates, output_dir, priority, ...)`

Main entry point for automatic execution with optimal strategy.

**Returns:** `SupremeExecutionResult` with complete execution results

**Example:**
```python
from src.core.supreme_orchestrator import SupremeOrchestrator
from datetime import date
from pathlib import Path

supreme = SupremeOrchestrator()

result = await supreme.auto_execute(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("./output"),
    priority="standard"  # or "triage" or "doj_referral"
)

print(f"Success: {result.success}")
print(f"Violations: {result.total_violations}")
print(f"Alerts: {result.total_alerts}")
```

###### `get_available_strategies()`

Returns list of all available execution strategies with details.

**Example:**
```python
strategies = supreme.get_available_strategies()

for strategy in strategies:
    print(f"{strategy['priority']}: {strategy['description']}")
```

### Execution Strategies

#### TRIAGE (5-10 minutes)
- **Orchestrator:** IntelligentOrchestrator
- **Nodes:** 5-7 critical nodes (selective based on investigation type)
- **Strict Gates:** Disabled
- **AI Validation:** Disabled
- **Optimization:** Aggressive
- **Use Case:** Quick initial assessment, triage for resource allocation

#### STANDARD (15-30 minutes)
- **Orchestrator:** MasterExecutionController
- **Nodes:** All 15 nodes with cross-correlation
- **Strict Gates:** Enabled
- **AI Validation:** Enabled (including pattern cross-validation)
- **Optimization:** Moderate
- **Use Case:** Standard comprehensive investigation

#### DOJ_REFERRAL (30-60 minutes)
- **Orchestrator:** ForensicMetaOrchestrator
- **Nodes:** All 15 nodes with parallel agent analysis
- **Strict Gates:** Enabled
- **AI Validation:** Enabled
- **Optimization:** None (exhaustive mode)
- **Parallel Execution:** Enabled
- **Use Case:** DOJ-grade referral preparation, maximum evidence integrity

### Test Coverage

**File:** `tests/test_supreme_orchestrator.py`

- ✅ 15 test cases covering:
  - Strategy selection for each priority level
  - Invalid priority handling
  - Strategy caching
  - Strategy serialization (to_dict)
  - Auto-execute for each priority
  - Error handling
  - ExecutionStrategy creation
  - Available strategies retrieval
  - Strategy descriptions and duration estimates

**Run tests:**
```bash
pytest tests/test_supreme_orchestrator.py -v
```

---

## Usage Examples

### Example 1: Quick Triage

```python
from src.core.supreme_orchestrator import SupremeOrchestrator
from datetime import date
from pathlib import Path

supreme = SupremeOrchestrator()

result = await supreme.auto_execute(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("./output"),
    priority="triage"
)

print(f"Duration: {(result.execution_end - result.execution_start).total_seconds()/60:.1f} min")
print(f"Violations found: {result.total_violations}")
```

### Example 2: Standard Investigation with AI Validation

```python
supreme = SupremeOrchestrator()

result = await supreme.auto_execute(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("./output"),
    priority="standard"
)

# AI validation results available
if result.ai_validation_results:
    print(f"Patterns validated: {result.ai_validation_results['validated_count']}")
    print(f"High confidence: {result.ai_validation_results['high_confidence_count']}")
    print(f"Avg AI confidence: {result.ai_validation_results['average_ai_confidence']:.1f}%")
```

### Example 3: DOJ Referral Preparation

```python
supreme = SupremeOrchestrator()

result = await supreme.auto_execute(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("./output"),
    priority="doj_referral"
)

print(f"Dossier path: {result.dossier_path}")
print(f"Evidence chain: {result.evidence_chain['merkle_root']}")
```

### Example 4: Compare Strategies Before Execution

```python
supreme = SupremeOrchestrator()

strategies = supreme.get_available_strategies()

for strategy in strategies:
    print(f"\nPriority: {strategy['priority']}")
    print(f"  Duration: {strategy['estimated_duration_minutes']} min")
    print(f"  Nodes: {strategy['node_count']}")
    print(f"  AI Validation: {strategy['enable_ai_validation']}")
    print(f"  Description: {strategy['description']}")
```

---

## Integration with Existing System

### Phase 5 Flow (with AI Cross-Validation)

```
BEFORE:
Phase 5: Advanced Detection Patterns
  ├── Execute 23 algorithms
  ├── Store detection_results
  └── Continue to Phase 6

AFTER:
Phase 5: Advanced Detection Patterns
  ├── Execute 23 algorithms
  ├── Store detection_results
  ├── AI Cross-Validation (NEW!)
  │   ├── Check _should_cross_validate()
  │   ├── Initialize DualAgentCoordinator
  │   ├── Filter HIGH/CRITICAL patterns
  │   ├── Call batch_cross_validate_patterns()
  │   └── Store ai_validation_results
  └── Continue to Phase 6
```

### MasterExecutionController Changes

**Minimal, non-breaking changes:**
1. Added `ai_validation_results` attribute (default: empty dict)
2. Added `_should_cross_validate()` helper method
3. Added AI cross-validation block in Phase 5 (after detection, before phase result)

**Backward Compatibility:**
- If dual agents unavailable → skip validation, log warning
- If no patterns found → skip validation
- If disabled via env var → skip validation
- Existing tests continue to pass

---

## Testing

### Run All New Tests

```bash
# AI cross-validation tests
pytest tests/test_ai_cross_validation.py -v

# SupremeOrchestrator tests
pytest tests/test_supreme_orchestrator.py -v

# Both together
pytest tests/test_ai_cross_validation.py tests/test_supreme_orchestrator.py -v
```

### Run Example Demo

```bash
PYTHONPATH=/home/runner/work/JLAW/JLAW python examples/ai_cross_validation_example.py
```

---

## Performance Considerations

### AI Cross-Validation
- **Overhead:** ~30-60 seconds for batch validation (depends on pattern count and agent response time)
- **Optimization:** Only HIGH/CRITICAL patterns validated by default
- **Async:** Uses async/await for concurrent agent calls
- **Caching:** Consider caching validation results for repeated patterns

### SupremeOrchestrator
- **Strategy Selection:** < 1 second (cached after first call)
- **Lazy Loading:** Orchestrator instances only created when needed
- **No Additional Overhead:** Routes to existing orchestrators

---

## Dependencies

### Required
- `src.forensics.dual_agent.DualAgentCoordinator` (existing)
- OpenAI API key configured
- Anthropic API key configured

### Optional
- GovInfo API key (for enhanced statute cross-referencing)

---

## Environment Variables

```bash
# Disable AI cross-validation (default: false)
export JLAW_DISABLE_AI_VALIDATION=true
```

---

## Benefits

### AI Cross-Validation
✅ Adds human-like reasoning to quantitative fraud scores  
✅ Filters false positives (low AI confidence)  
✅ Highlights high-confidence findings (>85%)  
✅ Provides action recommendations  
✅ Dual-agent consensus for reliability  

### SupremeOrchestrator
✅ Single unified entry point for all execution modes  
✅ Automatic strategy selection based on priority  
✅ Clear execution time estimates  
✅ No breaking changes to existing orchestrators  
✅ Easy to extend with new strategies  

---

## Future Enhancements

### AI Cross-Validation
- [ ] Add confidence threshold configuration
- [ ] Support custom severity filters
- [ ] Cache validation results to avoid re-validation
- [ ] Add validation quality metrics (inter-agent agreement)

### SupremeOrchestrator
- [ ] Dynamic strategy selection based on available resources
- [ ] Resource usage prediction and optimization
- [ ] Strategy recommendation based on filing composition
- [ ] Execution time tracking and estimation refinement

---

## Summary

This implementation successfully addresses the two critical gaps identified in the JLAW audit:

1. **Detection patterns are now AI cross-validated**, providing dual-agent reasoning and confidence assessment for quantitative fraud scores.

2. **SupremeOrchestrator provides a unified meta-controller**, automatically routing to the optimal execution strategy based on investigation priority.

**All changes are:**
- ✅ Fully tested (24 test cases passing)
- ✅ Backward compatible (no breaking changes)
- ✅ Well-documented (comprehensive docs and examples)
- ✅ Performance-conscious (minimal overhead, lazy loading)
- ✅ Production-ready (error handling, graceful degradation)
