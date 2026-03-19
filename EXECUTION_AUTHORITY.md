# EXECUTION AUTHORITY

> **Single Source of Truth for JLAW Pipeline Execution**

## Canonical Orchestrator

| Property          | Value                                                    |
|-------------------|----------------------------------------------------------|
| **Module**        | `src/core/unified_orchestrator.py`                       |
| **Class**         | `UnifiedForensicOrchestrator`                            |
| **CLI entry point** | `jlaw_cli.py`                                          |
| **Pipeline**      | 11-phase DOJ-grade forensic analysis                     |
| **Status**        | **ACTIVE — the ONLY valid execution path**               |

All forensic analysis **MUST** be invoked through `UnifiedForensicOrchestrator`.
No other orchestrator, controller, or engine should be instantiated directly to
run the pipeline.

```python
from src.core.unified_orchestrator import UnifiedForensicOrchestrator

orchestrator = UnifiedForensicOrchestrator(
    cik="320187",
    company_name="NIKE, Inc.",
    ticker="NKE",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("output"),
    strict_mode=True,
    auto_mode=True,
)

result = await orchestrator.execute_full_analysis()
```

---

## Deprecated Modules

The following orchestrators and controllers are **DEPRECATED**. They exist
solely for backward compatibility and **MUST NOT** be used as pipeline entry
points. Each emits a `DeprecationWarning` at instantiation time.

| Module                              | Class                        | Reason Deprecated                            |
|-------------------------------------|------------------------------|----------------------------------------------|
| `src/core/supreme_orchestrator.py`  | `SupremeOrchestrator`        | Superseded — meta-routing consolidated into `UnifiedForensicOrchestrator` |
| `src/core/intelligent_orchestrator.py` | `IntelligentOrchestrator` | Superseded — dynamic node selection built into unified pipeline |
| `src/core/master_execution_controller.py` | `MasterExecutionController` | Superseded — 9-phase pipeline replaced by 11-phase unified pipeline |
| `src/core/strict_execution_controller.py` | `StrictExecutionController` | Superseded — strict mode integrated via `strict_mode=True` parameter |
| `src/core/batch_forensic_orchestrator.py` | `BatchForensicOrchestrator` | Superseded — batch analysis should invoke `UnifiedForensicOrchestrator` in a loop |
| `src/core/forensic_meta_orchestrator.py` | `ForensicMetaOrchestrator` | Superseded — agent spawning consolidated into unified pipeline |
| `src/core/unified_agent_orchestrator.py` | `UnifiedAgentOrchestrator` | Superseded — multi-tier agent coordination built into unified pipeline |

---

## Utility Modules (NOT Orchestrators)

The following modules are **utilities** called internally by
`UnifiedForensicOrchestrator`. They are **not** entry points and should never
be invoked directly to run the full pipeline.

| Module                                    | Role                                             |
|-------------------------------------------|--------------------------------------------------|
| `src/core/recursive_engine.py`            | 15-node recursive analysis engine (called by Phase 4) |
| `src/core/recursive_engine_integration.py`| Integration bridge for nodes 2-5                 |
| `src/core/recursive_analysis_engine.py`   | RIM Phase 1 recursive analysis                   |

---

## Domain-Specific Orchestrators (Valid — Not Entry Points)

The following orchestrators coordinate specific subsystems and are called
**by** `UnifiedForensicOrchestrator` during execution. They are valid modules
but must not be used as top-level pipeline entry points.

| Module                                      | Class                          | Called During        |
|---------------------------------------------|--------------------------------|----------------------|
| `src/enhancement/orchestrator.py`           | `JLAWEnhancementOrchestrator`  | Phase 10 enhancement |
| `src/forensic_tracing/orchestrator.py`      | `ForensicTracingOrchestrator`  | Forensic tracing     |
| `src/forensics/subagents/orchestrator.py`   | `SubagentOrchestrator`         | Phase 7 subagents    |

---

## Rules

1. **ONE ENTRY POINT**: Only `UnifiedForensicOrchestrator` may be used to start
   a forensic analysis pipeline.
2. **NO DIRECT IMPORTS of deprecated orchestrators** in new code. Existing
   references are permitted for backward compatibility but should be migrated.
3. **`src/core/__init__.py` MUST NOT export** any deprecated orchestrator class.
4. **Tests** may import deprecated orchestrators to verify deprecation warnings
   but must not rely on them for pipeline execution.
5. **CLI** (`jlaw_cli.py`) must import exclusively from
   `src.core.unified_orchestrator`.

---

*Document created as part of the orchestrator consolidation effort.*
*See also: `src/core/unified_orchestrator.py` module docstring.*
