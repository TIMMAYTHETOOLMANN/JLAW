# Migration Guide: LinearExecutionOrchestrator to MasterExecutionController

## Overview

The `LinearExecutionOrchestrator` is deprecated in favor of `MasterExecutionController`,
which provides a more comprehensive 9-phase execution pipeline with:

- Intelligent optimization (30-50% speedup)
- Strict gate validation
- Evidence chain integrity
- Auto-registered agents via ForensicMetaOrchestrator
- Claude subagent auto-triggering

## Quick Migration

### Before (Deprecated)

```python
from src.core.linear_orchestrator import LinearExecutionOrchestrator
from datetime import date

orchestrator = LinearExecutionOrchestrator()
result = await orchestrator.execute(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31)
)
```

### After (Recommended)

```python
from src.core.master_execution_controller import MasterExecutionController
from datetime import date
from pathlib import Path

controller = MasterExecutionController(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("./output"),
    enable_optimization=True,  # 30-50% faster
    strict_mode=False,
    auto_mode=True
)

result = await controller.execute_full_analysis()
```

## Feature Comparison

| Feature | LinearOrchestrator | MasterExecutionController |
|---------|-------------------|---------------------------|
| Phases | 4 | 9 |
| Nodes | 15 | 15 (with V2 variants) |
| Optimization | ❌ | ✅ IntelligentOrchestrator |
| Strict Gates | ❌ | ✅ Optional |
| Evidence Chain | Basic | ✅ Merkle + RFC 3161 |
| Agent Registry | ❌ | ✅ 23+ pre-registered |
| Subagent Auto-Trigger | ❌ | ✅ Violation-based |
| PDF Reports | ❌ | ✅ DOJ-grade |

## Using the Migration Helper

For a quick transition, use the migration helper:

```python
from src.core.linear_orchestrator import LinearExecutionOrchestrator
from datetime import date

# This creates a MasterExecutionController configured like LinearOrchestrator
controller = LinearExecutionOrchestrator.create_migrated_controller(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31)
)

result = await controller.execute_full_analysis()
```

## Detailed Migration Steps

### Step 1: Update Imports

**Before:**
```python
from src.core.linear_orchestrator import LinearExecutionOrchestrator
```

**After:**
```python
from src.core.master_execution_controller import MasterExecutionController
from pathlib import Path
```

### Step 2: Update Initialization

**Before:**
```python
orchestrator = LinearExecutionOrchestrator(
    sec_user_agent="MyApp/1.0 contact@example.com",
    polygon_api_key="optional_key"
)
```

**After:**
```python
controller = MasterExecutionController(
    cik=cik,
    company_name=company_name,
    start_date=start_date,
    end_date=end_date,
    output_dir=Path("./output"),
    sec_user_agent="MyApp/1.0 contact@example.com",
    polygon_api_key="optional_key",
    enable_optimization=True,
    strict_mode=False,
    auto_mode=True
)
```

### Step 3: Update Execution Call

**Before:**
```python
result = await orchestrator.execute_analysis(
    company_cik=cik,
    company_name=name,
    start_date=start_date,
    end_date=end_date,
    case_id=optional_case_id
)
```

**After:**
```python
result = await controller.execute_full_analysis()
```

### Step 4: Update Result Handling

The result structure is similar but enhanced. Key differences:

**Before (LinearOrchestrator):**
```python
# ForensicAnalysisResult
result.total_violations
result.total_alerts
result.phase_1_result
result.phase_2_result
result.phase_3_result
result.phase_4_result
result.evidence_chain_sha256
```

**After (MasterExecutionController):**
```python
# UnifiedAnalysisResult
result.total_violations
result.total_alerts
result.phase_results  # List of all phase results
result.node_results  # Dict of node results
result.merkle_root  # Enhanced evidence chain
result.dossier_path  # DOJ-grade JSON dossier
result.pdf_path  # DOJ-grade PDF report
```

## Advanced Features Available in MasterExecutionController

### 1. Intelligent Optimization

Enable 30-50% speedup through intelligent node skipping:

```python
controller = MasterExecutionController(
    cik=cik,
    company_name=company_name,
    start_date=start_date,
    end_date=end_date,
    output_dir=output_dir,
    enable_optimization=True  # ← Enable optimization
)
```

### 2. Strict Mode

Enable strict gate validation for DOJ-grade analysis:

```python
controller = MasterExecutionController(
    cik=cik,
    company_name=company_name,
    start_date=start_date,
    end_date=end_date,
    output_dir=output_dir,
    strict_mode=True,  # ← Enable strict gates
    auto_mode=True     # Skip user confirmations
)
```

### 3. Enhanced Evidence Chain

MasterExecutionController provides:
- Triple-hash integrity (SHA-256 + SHA3-512 + BLAKE2b)
- RFC 6962 compliant Merkle trees
- RFC 3161 timestamp tokens
- FRE 902(13)/(14) compliance

```python
result = await controller.execute_full_analysis()
print(f"Merkle Root: {result.merkle_root}")
print(f"Evidence Chain: {result.evidence_chain}")
```

### 4. Auto-Registered Agents

23+ pre-registered forensic agents automatically triggered on violations:

```python
# Agents auto-trigger on violations detected in nodes
# No manual configuration needed
result = await controller.execute_full_analysis()
```

### 5. PDF Report Generation

DOJ-grade PDF reports automatically generated:

```python
result = await controller.execute_full_analysis()
print(f"PDF Report: {result.pdf_path}")
print(f"JSON Dossier: {result.dossier_path}")
```

## Common Migration Patterns

### Pattern 1: Basic Analysis

**Before:**
```python
orchestrator = LinearExecutionOrchestrator(
    sec_user_agent="MyApp/1.0 contact@example.com"
)
result = await orchestrator.execute_analysis(
    company_cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31)
)
```

**After:**
```python
controller = MasterExecutionController(
    cik="320187",
    company_name="Nike Inc",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("./output"),
    sec_user_agent="MyApp/1.0 contact@example.com"
)
result = await controller.execute_full_analysis()
```

### Pattern 2: Batch Processing

**Before:**
```python
orchestrator = LinearExecutionOrchestrator(sec_user_agent=agent)
for company in companies:
    result = await orchestrator.execute_analysis(
        company_cik=company.cik,
        company_name=company.name,
        start_date=start_date,
        end_date=end_date
    )
```

**After:**
```python
for company in companies:
    controller = MasterExecutionController(
        cik=company.cik,
        company_name=company.name,
        start_date=start_date,
        end_date=end_date,
        output_dir=Path(f"./output/{company.cik}"),
        sec_user_agent=agent
    )
    result = await controller.execute_full_analysis()
```

### Pattern 3: Custom Case IDs

**Before:**
```python
result = await orchestrator.execute_analysis(
    company_cik=cik,
    company_name=name,
    start_date=start_date,
    end_date=end_date,
    case_id="CUSTOM-CASE-123"
)
```

**After:**
```python
# MasterExecutionController auto-generates case IDs
# Custom IDs can be tracked via output_dir naming
controller = MasterExecutionController(
    cik=cik,
    company_name=name,
    start_date=start_date,
    end_date=end_date,
    output_dir=Path("./output/CUSTOM-CASE-123")
)
result = await controller.execute_full_analysis()
```

## Troubleshooting

### Issue: Missing output_dir parameter

**Error:**
```
TypeError: __init__() missing 1 required positional argument: 'output_dir'
```

**Solution:**
```python
from pathlib import Path
controller = MasterExecutionController(
    cik=cik,
    company_name=company_name,
    start_date=start_date,
    end_date=end_date,
    output_dir=Path("./output")  # ← Add this
)
```

### Issue: Different result structure

**Problem:** Accessing `result.phase_1_result` fails

**Solution:**
```python
# Old way (LinearOrchestrator)
phase_1 = result.phase_1_result

# New way (MasterExecutionController)
phase_results = result.phase_results
# Find Phase 4 (Node Analysis) which corresponds to old phases
node_analysis_phase = next(
    p for p in phase_results 
    if p.phase == ExecutionPhase.NODE_ANALYSIS
)
```

### Issue: DeprecationWarning appearing in logs

**Problem:** Seeing deprecation warnings in application logs

**Solution:** Migrate to MasterExecutionController. To suppress warnings temporarily:

```python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

## Timeline

- **v4.1.1**: Deprecation warnings added
- **v4.2.0**: Migration helper available (current)
- **v4.3.0**: Additional migration tools
- **v5.0.0**: LinearExecutionOrchestrator removed (breaking change)

## Need Help?

If you encounter issues during migration:

1. **Check the test suite** for examples:
   - `tests/test_master_execution_controller_optimization.py`
   - `tests/test_strict_execution.py`

2. **Review MasterExecutionController documentation**:
   - Main module: `src/core/master_execution_controller.py`
   - README: `README.md`

3. **Use the migration helper**:
   ```python
   controller = LinearExecutionOrchestrator.create_migrated_controller(...)
   ```

4. **Open an issue** on GitHub with:
   - Your current LinearExecutionOrchestrator code
   - Error messages or unexpected behavior
   - Expected vs actual results

## Further Reading

- [Master Execution Controller Documentation](../src/core/master_execution_controller.py)
- [Recursive Prosecutorial Engine](../src/core/recursive_engine.py)
- [Forensic Meta Orchestrator](../src/core/forensic_meta_orchestrator.py)
- [JLAW Architecture Overview](../README.md)
- [Strict Execution Mode](../STRICT_EXECUTION_MODE.md)
