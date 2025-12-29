# JLAW Troubleshooting Guide

Common issues and solutions for JLAW SEC forensic analysis system.

---

## Quick Diagnostic

Run the built-in diagnostic tool:

```bash
python jlaw_cli.py --validate-only
```

This will check:
- Python version (≥3.10)
- Required dependencies
- API key configuration
- SEC EDGAR access
- Database connectivity (optional)

---

## Common Issues

### 1. SEC API Issues

#### Error: `SEC API Rate Limit Exceeded (429)`

**Symptoms**:
```
ERROR: SEC API returned 429 (Too Many Requests)
Retry after: 30 seconds
```

**Causes**:
- Too many concurrent requests
- Aggressive rate limit setting
- Multiple JLAW instances running

**Solutions**:

```bash
# Solution 1: Reduce rate limit in .env
SEC_RATE_LIMIT=3.0  # Conservative (was 6.0)

# Solution 2: Check for multiple instances
ps aux | grep "jlaw_cli"
# Kill duplicates if found

# Solution 3: Wait and retry
# SEC rate limits reset after ~60 seconds
```

**Prevention**:
```python
# Use shared rate limiter
from src.forensics.sdk_manager import get_sdk_manager

sdk = await get_sdk_manager()
response = await sdk.sec_request(url, user_agent)  # ✅ Rate limited
```

#### Error: `Invalid SEC User-Agent`

**Symptoms**:
```
ERROR: SEC EDGAR rejected request due to invalid User-Agent
```

**Causes**:
- Missing or placeholder `SEC_USER_AGENT` in `.env`
- Incorrect format (missing email)

**Solutions**:

```bash
# Check current User-Agent
cat .env | grep SEC_USER_AGENT

# ❌ WRONG:
SEC_USER_AGENT=YourCompany contact@example.com

# ✅ CORRECT:
SEC_USER_AGENT=ACME Corp legal@acme.com
```

**Validation**:
```python
from config.secure_config import print_configuration_status
print_configuration_status()
# Should show ✅ for SEC configuration
```

---

### 2. API Key Issues

#### Error: `OpenAI API Key Invalid`

**Symptoms**:
```
ERROR: OpenAI API authentication failed
```

**Causes**:
- Expired or revoked API key
- Typo in `.env` file
- Missing `OPENAI_API_KEY` variable

**Solutions**:

```bash
# Verify key format
cat .env | grep OPENAI_API_KEY
# Should start with "sk-"

# Test key directly
python -c "
from openai import OpenAI
client = OpenAI()
print(client.models.list())
"

# If invalid, generate new key at:
# https://platform.openai.com/api-keys
```

#### Error: `Anthropic API Key Invalid`

**Similar to OpenAI, but:**
- Key format: `sk-ant-...`
- Generate at: https://console.anthropic.com/

---

### 3. Execution Issues

#### Issue: Low Consensus Score (<70%)

**Symptoms**:
```
⚠️  Consensus score: 0.62 (below 70% threshold)
Phase gate failed: Insufficient agreement across agents
```

**Causes**:
- Agents disagree on violation interpretations
- Ambiguous evidence in filings
- Conflicting temporal patterns

**Diagnosis**:

```python
# Review individual agent findings
for agent_name, findings in result.subagent_findings.items():
    print(f"{agent_name}:")
    print(f"  Violations: {len(findings['violations'])}")
    print(f"  Confidence: {findings['confidence']:.2f}")

# Check for contradictions
primary_violations = set(v['type'] for v in result.primary_findings)
subagent_violations = set(v['type'] for v in result.subagent_findings)

contradictions = primary_violations.symmetric_difference(subagent_violations)
print(f"Contradictions: {contradictions}")
```

**Solutions**:

1. **Manual Review**: Review conflicting findings
2. **Re-run with Strict Mode**: Enable additional validation
3. **Increase Agent Count**: More agents = higher confidence
4. **Focus Investigation**: Use `investigation_type` parameter

#### Issue: Phase Gate Failure

**Symptoms**:
```
❌ Phase Gate Failed: Data Collection
Minimum threshold: 5 filings (80% success)
Actual: 3 filings (60% success)
```

**Causes by Phase**:

| Phase | Common Causes |
|-------|---------------|
| Configuration | Missing API keys, invalid CIK |
| Data Collection | SEC API down, no filings found |
| Document Parsing | Unsupported document formats |
| Node Analysis | Node execution errors |
| Evidence Chain | Hash verification failure |

**Solutions**:

```python
# Check phase execution log
for phase_result in result.phase_results:
    if not phase_result.success:
        print(f"Failed: {phase_result.phase.value}")
        print(f"Errors: {phase_result.errors}")
        
# Common fixes:
# 1. Data Collection: Verify CIK and date range
# 2. Document Parsing: Check document format support
# 3. Node Analysis: Review node error logs
```

#### Issue: High API Costs

**Symptoms**:
```
⚠️  Warning: Cost $4.50 (exceeds budget $2.00)
```

**Diagnosis**:

```python
# Load performance metrics
import json
with open("output/performance_metrics.json") as f:
    metrics = json.load(f)

# Identify expensive agents
for agent in sorted(metrics['agents'], key=lambda a: a['total_cost'], reverse=True):
    print(f"{agent['agent_name']}: ${agent['total_cost']:.2f}")
    print(f"  Tokens: {agent['total_tokens']:,}")
    print(f"  Violations: {agent['violations_found']}")
```

**Solutions**:

1. **Enable Optimization**:
```python
controller = MasterExecutionController(
    enable_optimization=True,  # ✅
    max_agents=3,              # Reduce agent count
    max_cost_usd=2.00          # Enforce budget
)
```

2. **Use Investigation Types**:
```python
controller = MasterExecutionController(
    investigation_type="insider_trading",  # Focus analysis
)
```

3. **Review Expensive Agents**:
- Consider skipping low-ROI agents
- Reduce context window size
- Enable response streaming

---

### 4. Performance Issues

#### Issue: Slow Execution (>10 minutes)

**Diagnosis**:

```python
# Check phase timing
for phase in result.phase_results:
    print(f"{phase.phase.value}: {phase.duration_seconds:.1f}s")

# Identify bottlenecks
bottlenecks = [p for p in result.phase_results if p.duration_seconds > 60]
```

**Solutions**:

1. **Enable Caching**:
```python
from src.integrations.sec_edgar.edgar_client import SECEdgarClient

client = SECEdgarClient(
    cache_dir=Path(".cache/sec_edgar"),
    stale_fallback=True  # ✅ Use cache if available
)
```

2. **Parallel Execution**:
```python
orchestrator = UnifiedAgentOrchestrator()
result = await orchestrator.execute_investigation(
    parallel_stages=2  # ✅ Execute agents in parallel
)
```

3. **Reduce Document Count**:
```python
controller = MasterExecutionController(
    start_date=date(2019, 1, 1),
    end_date=date(2019, 3, 31)  # ✅ Q1 only (faster)
)
```

#### Issue: Memory Errors

**Symptoms**:
```
MemoryError: Unable to allocate array
```

**Causes**:
- Large PDF documents (>100 MB)
- Too many concurrent agents
- Memory leak in long-running process

**Solutions**:

1. **Increase Memory Limit** (Docker):
```yaml
services:
  jlaw:
    mem_limit: 8g  # Increase from 4g
```

2. **Process Documents Incrementally**:
```python
# Process in batches
for filing_batch in chunks(filings, size=5):
    result = await process_batch(filing_batch)
    # Clear memory between batches
    gc.collect()
```

3. **Enable Streaming**:
```python
# Stream large responses instead of buffering
async for chunk in await sdk.anthropic.messages.stream(...):
    process_chunk(chunk)
```

---

### 5. Database Issues (Optional)

#### Issue: Neo4j Connection Failed

**Symptoms**:
```
ERROR: Failed to connect to Neo4j at bolt://localhost:7687
```

**Solutions**:

```bash
# Check Neo4j status
docker compose ps neo4j
# Or: systemctl status neo4j

# Verify credentials
cat .env | grep NEO4J
# Should match Neo4j configuration

# Test connection
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
driver.verify_connectivity()
print('✅ Connected')
"
```

#### Issue: TimescaleDB Connection Failed

**Similar to Neo4j, but:**
- Default port: 5432
- Test with: `psql -h localhost -U postgres`

---

### 6. Evidence Chain Issues

#### Error: Merkle Root Verification Failed

**Symptoms**:
```
CRITICAL: Evidence chain integrity violation
Merkle root mismatch detected
```

**Causes**:
- Document modified after hashing
- File system corruption
- Race condition in multi-threaded access

**Solutions**:

1. **Re-run Investigation**:
```bash
# Complete clean re-run
rm -rf output/
python jlaw_cli.py --cik 0001318605 --year 2019 --strict --auto
```

2. **Verify File System**:
```bash
# Check for corruption
fsck /path/to/output
# Or on Docker:
docker compose exec jlaw df -h
```

3. **Disable Concurrent Access**:
```python
# Ensure single-threaded evidence chain updates
import threading
evidence_lock = threading.Lock()

with evidence_lock:
    merkle_tree.add_leaf(hash_value)
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# Run investigation with verbose logging
controller = MasterExecutionController(...)
result = await controller.execute_full_analysis()
```

### Dry Run Mode

```bash
# Preview execution plan without running
python jlaw_cli.py --cik 0001318605 --year 2019 --dry-run
```

### Interactive Mode

```bash
# Step through investigation with confirmations
python jlaw_cli.py --cik 0001318605 --year 2019
# (Omit --auto flag)
```

### Export Diagnostic Report

```python
# Generate comprehensive diagnostic report
from src.utils.diagnostics import generate_diagnostic_report

report = generate_diagnostic_report()
report.save("diagnostic_report.json")
```

---

## Getting Help

### Before Reporting Issues

1. **Check this guide** for common solutions
2. **Run validation**: `python jlaw_cli.py --validate-only`
3. **Review logs**: Check `output/logs/` directory
4. **Test API keys**: Verify OpenAI/Anthropic access
5. **Check SEC access**: Test user-agent configuration

### Reporting Bugs

Include the following information:

```bash
# System info
python --version
pip list | grep -E "(openai|anthropic|aiohttp)"

# Configuration (redact API keys)
cat .env | sed 's/=.*/=***REDACTED***/'

# Error logs
tail -n 100 output/logs/jlaw.log

# Execution command
echo "python jlaw_cli.py --cik 0001318605 --year 2019"
```

### Support Channels

- **GitHub Issues**: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- **Documentation**: https://github.com/TIMMAYTHETOOLMANN/JLAW
- **Slack**: [Join JLAW Community](https://jlaw.dev/slack) (if available)

---

## Additional Resources

- **Integration Guide**: [docs/integration_guide.md](integration_guide.md)
- **Optimization Guide**: [docs/optimization_guide.md](optimization_guide.md)
- **System Architecture**: [docs/system_architecture.md](system_architecture.md)
- **API Reference**: [docs/api_reference.md](api_reference.md)

---

**Last Updated**: December 29, 2024  
**Version**: 4.1.0  
**Status**: Production Ready
