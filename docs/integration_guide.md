# JLAW Integration Guide

Complete step-by-step guide for integrating JLAW SEC forensic analysis system into your workflow.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Basic Usage](#basic-usage)
5. [Advanced Configuration](#advanced-configuration)
6. [Integration Patterns](#integration-patterns)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Start

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/TIMMAYTHETOOLMANN/JLAW.git
cd JLAW

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install -r requirements-dev.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Required: SEC EDGAR API access
SEC_USER_AGENT=YourCompany contact@example.com
SEC_EMAIL=contact@example.com

# Required: AI providers (at least one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional: Market data
POLYGON_API_KEY=...

# Optional: Databases (for advanced features)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
TIMESCALEDB_HOST=localhost
TIMESCALEDB_PORT=5432
TIMESCALEDB_USER=postgres
TIMESCALEDB_PASSWORD=...
```

### 3. Run Your First Investigation

```bash
# Interactive mode (guided)
python jlaw_cli.py --cik 0001318605 --company "Tesla, Inc." --year 2019

# Auto mode (no confirmations)
python jlaw_cli.py --cik 0001318605 --year 2019 --auto

# Strict mode (DOJ-grade with mandatory phase gates)
python jlaw_cli.py --cik 0001318605 --year 2019 --strict --auto
```

### 4. View Results

```bash
# Results saved to output/ directory
ls -la output/
cat output/TESLA_INC_2019_dossier.json
```

---

## Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 4 GB RAM minimum, 8 GB recommended
- **Storage**: 10 GB free space for evidence and reports

### Method 1: pip Install (Local)

```bash
# Install from repository
pip install -e .

# Verify installation
jlaw --help
```

### Method 2: Docker (Recommended for Production)

```bash
# Build image
docker build -t jlaw:latest .

# Run container
docker run -it --env-file .env \
  -v $(pwd)/output:/app/output \
  jlaw:latest \
  python jlaw_cli.py --cik 0001318605 --year 2019 --auto
```

### Method 3: Kubernetes (Enterprise)

```bash
# Apply manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n jlaw-forensics

# Run investigation
kubectl exec -n jlaw-forensics deployment/jlaw-forensics -- \
  python jlaw_cli.py --cik 0001318605 --year 2019 --auto
```

---

## Configuration

### Environment Variables

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SEC_USER_AGENT` | SEC EDGAR user agent | `YourCompany contact@example.com` |
| `SEC_EMAIL` | Contact email for SEC | `contact@example.com` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SEC_RATE_LIMIT` | SEC requests per second | `6.0` |
| `MAX_AGENTS` | Maximum subagents to invoke | `5` |
| `ENABLE_OPTIMIZATION` | Enable cost optimization | `true` |
| `MAX_COST_USD` | Budget limit per investigation | `5.00` |
| `STRICT_MODE` | Enable DOJ-grade validation | `false` |

### Configuration File

Create `config/user_config.yaml`:

```yaml
# SEC EDGAR Configuration
sec_edgar:
  rate_limit: 6.0          # Conservative rate limit
  user_agent: "YourCompany contact@example.com"
  cache_ttl: 86400         # 24 hours

# AI Configuration
ai:
  openai:
    model: "gpt-4-turbo"
    temperature: 0.0       # Deterministic for legal
    max_tokens: 4096
  anthropic:
    model: "claude-3-sonnet-20240229"
    temperature: 0.0
    max_tokens: 4096

# Execution Configuration
execution:
  strict_mode: true        # DOJ-grade enforcement
  auto_mode: false         # Require confirmations
  max_agents: 5            # Top-5 agent selection
  parallel_stages: 2       # Execute in 2 waves

# Performance Configuration
performance:
  enable_optimization: true
  max_cost_usd: 5.00
  budget_enforcement: true
  export_metrics: true

# Output Configuration
output:
  base_dir: "output"
  save_json: true
  save_pdf: true
  save_evidence: true
```

---

## Basic Usage

### Python API

```python
from datetime import date
from pathlib import Path
from src.core.master_execution_controller import MasterExecutionController

# Initialize controller
controller = MasterExecutionController(
    cik="0001318605",
    company_name="Tesla, Inc.",
    start_date=date(2019, 1, 1),
    end_date=date(2019, 12, 31),
    output_dir=Path("output"),
    strict_mode=True,
    auto_mode=True
)

# Execute analysis
result = await controller.execute_full_analysis()

# Access results
print(f"Company: {result.company_name}")
print(f"Violations: {result.total_violations}")
print(f"Consensus: {result.consensus_score:.2%}")
print(f"Dossier: {result.dossier_path}")
print(f"Merkle Root: {result.merkle_root}")
```

### Command Line Interface

```bash
# Basic investigation
jlaw --cik 0001318605 --company "Tesla, Inc." --year 2019

# Custom date range
jlaw --cik 0001318605 --start 2019-01-01 --end 2019-06-30

# Strict mode (DOJ-grade)
jlaw --cik 0001318605 --year 2019 --strict --auto

# Specific investigation type
jlaw --cik 0001318605 --year 2019 --investigation insider-trading

# Batch processing
jlaw --batch targets.json --mode batch --auto
```

### Batch Processing

Create `targets.json`:

```json
{
  "investigations": [
    {
      "cik": "0001318605",
      "company_name": "Tesla, Inc.",
      "start_date": "2019-01-01",
      "end_date": "2019-12-31"
    },
    {
      "cik": "0000320193",
      "company_name": "Apple Inc.",
      "start_date": "2019-01-01",
      "end_date": "2019-12-31"
    }
  ]
}
```

Run batch:

```bash
jlaw --batch targets.json --mode batch --auto
```

---

## Advanced Configuration

### Custom Agent Selection

```python
from src.forensics.intelligent_router import IntelligentSubagentRouter

router = IntelligentSubagentRouter()

# Plan execution with custom parameters
decision = router.plan_execution(
    violations=violations,
    max_agents=3,           # Top 3 agents only
    parallel_stages=1,      # Sequential execution
    min_score_threshold=0.5 # Minimum relevance score
)

print(f"Selected agents: {decision.selected_agents}")
print(f"Execution plan: {decision.execution_stages}")
```

### Performance Optimization

```python
from src.profiling.performance_metrics import PerformanceMetricsCollector

# Enable optimization
controller = MasterExecutionController(
    cik="0001318605",
    enable_optimization=True,  # Apply recommendations
    max_cost_usd=2.00,         # Budget limit
    max_agents=3               # Limit agent count
)

# Execute with profiling
result = await controller.execute_full_analysis()

# View metrics
metrics_path = Path("output/performance_metrics.json")
if metrics_path.exists():
    import json
    with open(metrics_path) as f:
        metrics = json.load(f)
    print(f"Total cost: ${metrics['total_cost_usd']:.2f}")
    print(f"Execution time: {metrics['total_duration_seconds']:.2f}s")
```

### Evidence Chain Validation

```python
from src.core.evidence_chain.hash_service import HashService
from src.core.evidence_chain.merkle_tree import MerkleTree

# Compute triple-hash
hash_service = HashService()
hashes = hash_service.compute_triple_hash(document_content)

print(f"SHA-256: {hashes['sha256']}")
print(f"SHA3-512: {hashes['sha3_512']}")
print(f"BLAKE2b: {hashes['blake2b']}")

# Build Merkle tree
merkle_tree = MerkleTree()
for evidence_hash in evidence_hashes:
    merkle_tree.add_leaf(bytes.fromhex(evidence_hash))

merkle_root = merkle_tree.get_root()
print(f"Merkle Root: {merkle_root.hex()}")
```

---

## Integration Patterns

### Pattern 1: Async Web Service

```python
from fastapi import FastAPI, BackgroundTasks
from src.core.master_execution_controller import MasterExecutionController

app = FastAPI()

@app.post("/investigate")
async def investigate(
    cik: str,
    year: int,
    background_tasks: BackgroundTasks
):
    controller = MasterExecutionController(
        cik=cik,
        start_date=date(year, 1, 1),
        end_date=date(year, 12, 31),
        auto_mode=True
    )
    
    # Execute in background
    background_tasks.add_task(controller.execute_full_analysis)
    
    return {"status": "started", "cik": cik}
```

### Pattern 2: Scheduled Batch Jobs

```python
import schedule
import time
from pathlib import Path

def daily_investigation():
    """Run daily investigations on watchlist companies."""
    watchlist = ["0001318605", "0000320193", "0000789019"]
    
    for cik in watchlist:
        controller = MasterExecutionController(
            cik=cik,
            start_date=date.today() - timedelta(days=365),
            end_date=date.today(),
            auto_mode=True
        )
        
        result = await controller.execute_full_analysis()
        print(f"Completed: {result.company_name}")

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(daily_investigation)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Pattern 3: CI/CD Integration

```yaml
# .github/workflows/forensic-analysis.yml
name: Forensic Analysis

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run investigation
        env:
          SEC_USER_AGENT: ${{ secrets.SEC_USER_AGENT }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python jlaw_cli.py \
            --cik 0001318605 \
            --year 2019 \
            --strict \
            --auto
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: investigation-results
          path: output/
```

---

## Troubleshooting

### Issue: Low Consensus Score (<70%)

**Symptoms**: Analysis completes but consensus score below 70% threshold

**Cause**: Agents disagree on violations, possibly due to ambiguous evidence

**Solution**:
```python
# Review individual agent outputs
for agent_name, findings in result.subagent_findings.items():
    print(f"\n{agent_name}:")
    print(f"  Violations: {len(findings['violations'])}")
    print(f"  Confidence: {findings['confidence']:.2f}")

# Check for contradictory findings
contradictions = find_contradictions(result)
if contradictions:
    print("Contradictory findings detected:")
    for c in contradictions:
        print(f"  - {c}")
```

### Issue: High API Costs

**Symptoms**: API costs exceed budget

**Cause**: Token-heavy agents, large documents, excessive agent invocations

**Solution**:
```python
# Enable optimization
controller = MasterExecutionController(
    enable_optimization=True,
    max_cost_usd=2.00,
    max_agents=3  # Reduce agent count
)

# Review performance metrics
metrics_path = Path("output/performance_metrics.json")
with open(metrics_path) as f:
    metrics = json.load(f)

# Identify expensive agents
expensive_agents = [
    agent for agent in metrics['agents']
    if agent['total_cost'] > 0.50
]

print("Expensive agents:")
for agent in expensive_agents:
    print(f"  {agent['agent_name']}: ${agent['total_cost']:.2f}")
```

### Issue: Phase Gate Failure

**Symptoms**: Execution halts with phase gate failure

**Cause**: Missing dependencies, invalid input, insufficient data

**Solution**:
```python
# Check phase execution log
for phase_result in result.phase_results:
    if not phase_result.success:
        print(f"Failed phase: {phase_result.phase.value}")
        print(f"Errors: {phase_result.errors}")

# Verify prerequisites
if "Data Collection" in failed_phase:
    print("Check SEC API access and rate limits")
elif "Document Parsing" in failed_phase:
    print("Check document format support")
```

### Issue: SEC API Rate Limit Errors

**Symptoms**: 429 errors, slow execution

**Cause**: Too many concurrent requests, aggressive rate limit

**Solution**:
```bash
# Reduce rate limit in .env
SEC_RATE_LIMIT=3.0  # Slower but more reliable

# Check SEC API status
curl -H "User-Agent: YourCompany contact@example.com" \
  https://www.sec.gov/cgi-bin/browse-edgar
```

---

## Best Practices

### 1. API Key Management

- **Use environment variables**, never hardcode
- **Rotate keys regularly** (every 90 days)
- **Monitor usage** to detect anomalies
- **Set budget alerts** in OpenAI/Anthropic dashboards

### 2. Cost Optimization

- **Enable optimization** mode by default
- **Limit agent count** to top 3-5 most relevant
- **Cache SEC EDGAR** responses (24h TTL)
- **Use batch processing** for multiple companies

### 3. Performance Tuning

- **Parallel execution**: Enable 2-3 parallel stages
- **Connection pooling**: Use shared aiohttp session
- **Rate limiting**: Conservative SEC limits (3-6 req/sec)
- **Timeout protection**: Set reasonable timeouts (600s)

### 4. Evidence Integrity

- **Always enable strict mode** for DOJ-grade output
- **Verify Merkle root** after execution
- **Store evidence files** securely
- **Generate RFC 3161 timestamps** for all evidence

### 5. Error Handling

- **Implement retry logic** for transient errors
- **Log all errors** with context
- **Graceful degradation** when optional services unavailable
- **Monitor phase gates** for quality enforcement

### 6. Security

- **Never commit API keys** to version control
- **Use secrets management** (e.g., AWS Secrets Manager)
- **Restrict file permissions** on evidence directories
- **Audit access logs** regularly

### 7. Monitoring

- **Track execution time** per phase
- **Monitor API costs** in real-time
- **Alert on phase gate failures**
- **Dashboard performance metrics**

---

## Example: Complete Integration

```python
"""
Complete example: Integrate JLAW into forensic analysis workflow
"""

import asyncio
from datetime import date
from pathlib import Path
from src.core.master_execution_controller import MasterExecutionController
from src.profiling.performance_metrics import PerformanceMetricsCollector

async def forensic_investigation(cik: str, year: int) -> dict:
    """
    Execute complete forensic investigation with all optimizations.
    
    Args:
        cik: Company CIK
        year: Year to analyze
    
    Returns:
        Investigation results with metrics
    """
    # Initialize controller
    output_dir = Path(f"output/{cik}_{year}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    controller = MasterExecutionController(
        cik=cik,
        start_date=date(year, 1, 1),
        end_date=date(year, 12, 31),
        output_dir=output_dir,
        strict_mode=True,        # DOJ-grade enforcement
        auto_mode=True,          # No confirmations
        enable_optimization=True # Cost optimization
    )
    
    # Execute analysis
    print(f"Starting investigation: CIK {cik}, Year {year}")
    result = await controller.execute_full_analysis()
    
    # Extract key metrics
    summary = {
        "company": result.company_name,
        "cik": result.cik,
        "violations": result.total_violations,
        "alerts": result.total_alerts,
        "consensus": result.consensus_score,
        "dossier": str(result.dossier_path),
        "merkle_root": result.merkle_root,
        "duration": (result.analysis_end - result.analysis_start).total_seconds(),
        "phases_completed": len(result.phase_results),
        "nodes_executed": len(result.node_results)
    }
    
    # Log results
    print(f"\n✅ Investigation Complete")
    print(f"   Company: {summary['company']}")
    print(f"   Violations: {summary['violations']}")
    print(f"   Consensus: {summary['consensus']:.2%}")
    print(f"   Duration: {summary['duration']:.2f}s")
    print(f"   Dossier: {summary['dossier']}")
    
    return summary

# Run investigation
if __name__ == "__main__":
    result = asyncio.run(forensic_investigation("0001318605", 2019))
```

---

## Next Steps

1. **Read [System Architecture](system_architecture.md)** for detailed design
2. **Review [Optimization Guide](optimization_guide.md)** for cost reduction
3. **Check [Troubleshooting Guide](troubleshooting.md)** for common issues
4. **Explore [API Reference](api_reference.md)** for detailed API documentation

---

## Support

- **GitHub Issues**: https://github.com/TIMMAYTHETOOLMANN/JLAW/issues
- **Documentation**: https://github.com/TIMMAYTHETOOLMANN/JLAW/blob/main/README.md
- **Email**: support@jlaw.dev (if available)

---

**Last Updated**: December 29, 2024  
**Version**: 4.1.0  
**Status**: Production Ready
