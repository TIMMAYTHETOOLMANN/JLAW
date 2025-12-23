# ADR-001: Orchestration Hierarchy Design

**Status:** Accepted

**Date:** 2025-12-23

**Decision Makers:** JLAW Engineering Team

---

## Context

JLAW initially implemented multiple orchestration layers independently:
- RecursiveProsecutorialEngine (15-node execution)
- MasterExecutionController (9-phase orchestration)
- IntelligentOrchestrator (optimized node selection)
- ForensicMetaOrchestrator (parallel execution)
- SupremeOrchestrator (strategy selection)
- AutonomousForensicExecutor (scheduled execution)
- InvestigationScheduler (monitoring & alerts)

This created confusion about which orchestrator to use for different scenarios, and the unified entry point (JLAW_UNIFIED.py) did not expose the full orchestration hierarchy capabilities.

## Decision

Establish a **7-tier orchestration hierarchy** with clear separation of concerns:

```
Level 1: SupremeOrchestrator
    ├─ Strategy: TRIAGE → IntelligentOrchestrator (5-10 min)
    ├─ Strategy: STANDARD → MasterExecutionController (15-30 min)
    └─ Strategy: DOJ_REFERRAL → ForensicMetaOrchestrator (30-60 min)

Level 2: Execution Controllers
    ├─ IntelligentOrchestrator (selective node execution)
    ├─ MasterExecutionController (comprehensive 9-phase)
    └─ ForensicMetaOrchestrator (parallel exhaustive)

Level 3: Core Engines
    ├─ RecursiveProsecutorialEngine (15-node forensic analysis)
    └─ AdvancedPatternDetector (23 detection algorithms)

Level 4: Specialized Analyzers
    ├─ Node 1-15 Analyzers (domain-specific forensics)
    └─ DualAgentCoordinator (AI cross-validation)

Level 5: Integration Layers
    ├─ SECEdgarClient (SEC EDGAR API)
    ├─ PolygonClient (market data)
    └─ DocumentParser (DocsGPT)

Level 6: Autonomous Operations
    ├─ AutonomousForensicExecutor (daemon mode)
    └─ InvestigationScheduler (watchlist monitoring)

Level 7: Batch Operations
    └─ BatchForensicOrchestrator (multi-company)
```

**Key Design Principles:**

1. **Single Canonical Entry Point**: `SupremeOrchestrator.auto_execute()` for programmatic use, `JLAW_UNIFIED.py` for CLI
2. **Automatic Strategy Selection**: Based on `priority` parameter (triage/standard/doj_referral)
3. **Lazy Loading**: Orchestrators instantiated only when needed
4. **Composability**: Each layer can be used independently or composed
5. **Clear Responsibilities**: Each orchestrator has distinct purpose

## Consequences

### Positive

- **Clarity**: Developers and users know which orchestrator to use for each scenario
- **Performance**: Automatic strategy selection optimizes execution time (30-50% speedup for targeted investigations)
- **Flexibility**: Can use any layer directly or through unified interface
- **Scalability**: Easy to add new orchestrators or strategies
- **Testability**: Each layer can be tested independently

### Negative

- **Learning Curve**: New developers must understand 7-tier hierarchy
- **Complexity**: More classes and abstractions to maintain
- **Memory Overhead**: Lazy loading helps but full hierarchy in memory during execution

### Neutral

- **Migration Required**: Existing code using RecursiveProsecutorialEngine directly needs update
- **Documentation Burden**: Must maintain clear documentation of hierarchy
- **Testing Coverage**: Need comprehensive tests for all orchestration paths

## Alternatives Considered

### Alternative 1: Flat Single Orchestrator

- **Description**: Single monolithic orchestrator handling all scenarios
- **Pros**: Simple, no hierarchy to learn
- **Cons**: Massive class (2000+ lines), difficult to maintain, no optimization
- **Reason for rejection**: Violates single responsibility principle, unmaintainable

### Alternative 2: Plugin-Based Architecture

- **Description**: Base orchestrator with plugins for different strategies
- **Pros**: Extensible, clean plugin interface
- **Cons**: Over-engineered for current needs, complex plugin registration
- **Reason for rejection**: Added complexity without clear benefits

### Alternative 3: Strategy Pattern with Factory

- **Description**: Factory creates appropriate orchestrator based on strategy
- **Pros**: Clean separation, testable
- **Cons**: Similar to current approach but less explicit hierarchy
- **Reason for rejection**: Current approach is more explicit and discoverable

## Implementation Notes

### Entry Points

**CLI (JLAW_UNIFIED.py):**
```bash
# TRIAGE (5-10 min)
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strategy triage --auto

# STANDARD (15-30 min)
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strategy standard --auto

# DOJ_REFERRAL (30-60 min)
python JLAW_UNIFIED.py --cik 320187 --year 2019 --strategy doj_referral --auto
```

**Programmatic (SupremeOrchestrator):**
```python
from src.core.supreme_orchestrator import SupremeOrchestrator
from datetime import date
from pathlib import Path

supreme = SupremeOrchestrator()

result = await supreme.auto_execute(
    cik="320187",
    company_name="NIKE, Inc.",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("./output"),
    priority="standard"  # or "triage", "doj_referral"
)
```

### Migration Path

1. **Phase 1** (Week 1): Update JLAW_UNIFIED.py to use SupremeOrchestrator
2. **Phase 2** (Week 2): Update documentation and examples
3. **Phase 3** (Week 3): Deprecation warnings on direct RecursiveProsecutorialEngine usage
4. **Phase 4** (Month 2): Remove legacy direct instantiation paths

### Rollback Strategy

If issues arise:
1. Revert JLAW_UNIFIED.py to use UnifiedForensicEngine directly
2. Keep SupremeOrchestrator available for opt-in usage
3. Fix issues before re-enabling by default

## References

- **Related ADRs:**
  - ADR-002: Evidence Chain Architecture
  - ADR-003: Node Execution Strategy

- **Code References:**
  - `src/core/supreme_orchestrator.py` - Level 1 orchestrator
  - `src/core/master_execution_controller.py` - Level 2 orchestrator
  - `src/core/intelligent_orchestrator.py` - Level 2 orchestrator
  - `JLAW_UNIFIED.py` - CLI entry point

- **Documentation:**
  - `HOLY_GRAIL_PIPELINE.md` - Complete pipeline visualization
  - `README.md` - Quick start and usage examples

- **Design Inspirations:**
  - Kubernetes controller hierarchy
  - AWS Step Functions orchestration
  - Apache Airflow DAG composition

---

## Metadata

- **ADR Number:** 001
- **Created:** 2025-12-23
- **Last Updated:** 2025-12-23
- **Authors:** JLAW Engineering Team
- **Reviewers:** N/A
