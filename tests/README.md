# JLAW Master Test Suite Documentation

## Overview

The JLAW Master Test Suite is a **zero-failure deployment system** that validates every component before production deployment. It ensures that "deploy and discover errors" outcomes are **eliminated**.

## Architecture

```
tests/
├── jlaw_master_test_suite.py    # Main test orchestrator
├── preflight_check.py            # Quick GO/NO-GO check (< 30s)
├── config_validator.py           # Configuration validation
├── test_infrastructure.py        # Infrastructure self-test
├── validators/                   # Component validators
│   ├── environment_validator.py  # Python, deps, resources
│   ├── api_key_validator.py      # API configurations
│   ├── node_validator.py         # 15 analysis nodes
│   ├── detection_validator.py    # 23+ detection patterns
│   ├── agent_validator.py        # AI agent ecosystem
│   ├── evidence_chain_validator.py  # Evidence integrity
│   └── reporting_validator.py    # Report generation
├── utils/                        # Testing utilities
│   ├── test_reporter.py          # Multi-format reports
│   ├── remediation_engine.py     # Intelligent debugging
│   └── dependency_resolver.py    # Impact analysis
└── reports/                      # Generated reports

scripts/
├── deploy_jlaw.py                # One-click deployment
├── setup_environment.py          # Environment setup
└── generate_env_template.py      # .env generator
```

## Quick Start

### 1. Validate Test Infrastructure

```bash
# Verify test suite installation
python tests/test_infrastructure.py
```

### 2. Setup Environment (Optional)

```bash
# Create virtual environment and install dependencies
python scripts/setup_environment.py

# OR manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
# Generate .env file from template
python scripts/generate_env_template.py

# Edit .env with your API keys
# Required:
#   SEC_USER_AGENT=YourOrg/1.0 (contact@yourorg.com)
# Recommended:
#   OPENAI_API_KEY=sk-proj-...
#   ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Validate Configuration

```bash
# Check .env file and API key formats
python -m tests.config_validator
```

### 5. Run Pre-Flight Check

```bash
# Quick validation (< 30 seconds)
python -m tests.preflight_check
```

### 6. Run Full Test Suite

```bash
# Complete validation with all checks
python -m tests.jlaw_master_test_suite --full

# Mock mode (skip external API calls)
python -m tests.jlaw_master_test_suite --full --mock

# Specific category only
python -m tests.jlaw_master_test_suite --category nodes
python -m tests.jlaw_master_test_suite --category api_keys
```

### 7. One-Click Deployment

```bash
# Interactive deployment (with prompts)
python scripts/deploy_jlaw.py --interactive

# Automatic deployment (no prompts)
python scripts/deploy_jlaw.py --auto
```

## Test Categories

### Environment & Dependencies
- Python version validation (3.10+ required)
- All pip packages from requirements.txt
- Optional heavy dependencies (torch, transformers, DeBERTa)
- Virtual environment detection
- System resources check (RAM, disk space, CPU cores)

### API Key Configuration
- **SEC EDGAR API**: User-Agent validation, connectivity test
- **OpenAI API**: Key format, model access (GPT-4)
- **Anthropic API**: Key validation, Claude 3 access
- **Polygon.io API** (optional): Market data access
- **GovInfo API** (optional): Statute lookup
- **Neo4j** (optional): Connection test
- **TimescaleDB** (optional): Connection test

### 15 Analysis Nodes
- Node 1: Form 4 Insider Trading
- Node 2: DEF 14A Executive Compensation
- Node 3: 10-Q Temporal Consistency
- Node 4: 10-K SOX Certification
- Node 5: IRC §83 Tax Exposure
- Node 6: Enforcement Routing
- Node 7: 13F-HR Institutional Holdings (V2)
- Node 8: SC 13D/13G Beneficial Ownership (V2)
- Node 9: 8-K Material Events (V2)
- Node 10: Form 144 Restricted Sales (V2)
- Node 11: Executive Network Analysis (V2)
- Node 12: Earnings Call Transcripts (V2)
- Node 13: Z-Score Bankruptcy Prediction (V2)
- Node 14: F-Score Financial Strength (V2)
- Node 15: Market Correlation Engine (V2)

### Detection Patterns
- Beneish M-Score calculator
- Benford's Law analyzer
- Options Backdating Detector
- Channel Stuffing Detector
- Spring Loading, Bullet Dodging
- Round-tripping, Cookie Jar Reserves
- XGBoost Fraud Classifier
- DeBERTa Contradiction Detector (optional)
- 15+ advanced fraud patterns

### AI Agent Ecosystem
- OpenAI GPT-4 agent connectivity
- Anthropic Claude 3 agent connectivity
- Dual-agent consensus protocol
- 10 Claude subagent configurations
- Agent orchestrator

### Evidence Chain Integrity
- SHA-256, SHA3-512, BLAKE2b hash generation
- Merkle tree construction (RFC 6962)
- RFC 3161 timestamp client
- Chain of custody logger
- Evidence packager

### FRE 902(13)/(14) Compliance Tests

The security hardening test suite (`test_security_hardening.py`) provides comprehensive
validation for Federal Rules of Evidence 902(13) and 902(14) compliance:

**Triple-Hash Evidence Generation** (12 tests)
- SHA-256 hash generation and verification
- SHA3-512 hash generation and verification
- BLAKE2b hash generation and verification
- Hash determinism and uniqueness validation

**Merkle Tree Edge Cases** (14 tests)
- Single leaf handling
- Odd/even leaf node scenarios
- RFC 6962 compliance verification
- Proof generation and verification
- Order sensitivity validation

**RFC 3161 Timestamp Validation** (8 tests)
- Timestamp token creation and verification
- Trusted authority validation
- Local timestamp rejection (not court-admissible)

**Chain of Custody Lifecycle** (6 tests)
- Custody chain creation and tracking
- Multi-action recording
- Court export functionality

**Tampering Detection** (4 tests)
- Hash tampering detection
- Merkle tree tampering detection
- Subtle modification detection
- Chain link tampering detection

**FRE Compliance Validation** (6 tests)
- FRE certification generation
- Triple-hash compliance checks
- Merkle tree compliance checks
- Timestamp token compliance checks
- Custody chain compliance checks

Run FRE compliance tests:
```bash
python -m pytest tests/test_security_hardening.py -v
```

### Reporting Layer
- Markdown dossier generation
- JSON output serialization
- PDF generation (ReportLab)
- Court PDF generator (FRE 902 compliance)

## CLI Usage

### Master Test Suite

```bash
# Full test suite
python -m tests.jlaw_master_test_suite --full

# Mock mode (no external API calls)
python -m tests.jlaw_master_test_suite --full --mock

# Specific category
python -m tests.jlaw_master_test_suite --category <category>
# Categories: environment, api_keys, nodes, detection, agents, evidence_chain, reporting

# Generate reports
python -m tests.jlaw_master_test_suite --full --report json --output test_results.json
python -m tests.jlaw_master_test_suite --full --report markdown --output test_report.md
python -m tests.jlaw_master_test_suite --full --report html --output test_report.html
python -m tests.jlaw_master_test_suite --full --report all  # Generate all formats
```

### Pre-Flight Check

```bash
# Quick GO/NO-GO validation
python -m tests.preflight_check
```

### Configuration Validator

```bash
# Validate .env file
python -m tests.config_validator
```

### Deployment

```bash
# Interactive deployment
python scripts/deploy_jlaw.py --interactive

# Automatic deployment
python scripts/deploy_jlaw.py --auto
```

## Exit Codes

The test suite uses specific exit codes for CI/CD integration:

- **0**: All tests passed - **Production ready**
- **1**: Critical failures - **Cannot deploy**
- **2**: Non-critical failures - **Can deploy with limitations**
- **3**: Configuration errors - **Needs user intervention**

## Test Reports

### JSON Report
Machine-readable format with complete test results, suitable for CI/CD pipelines.

```json
{
  "summary": {
    "total_tests": 150,
    "passed": 145,
    "failed": 2,
    "skipped": 3,
    "duration": 45.2
  },
  "exit_code": 2,
  "results": [...]
}
```

### Markdown Report
Human-readable format with:
- Summary statistics
- Deployment readiness status
- Results grouped by category
- Critical failures with remediation
- Warnings and optional features

### HTML Report
Interactive dashboard with:
- Color-coded test results
- Deployment status banner
- Summary cards
- Filterable test categories
- Error details and remediation

## Remediation Engine

When tests fail, the system provides:

1. **Root Cause Analysis**: Not just "failed", but *why* it failed
2. **Specific Remediation Steps**: Exact commands to fix issues
3. **Dependency Chain Impact**: What else breaks if this fails
4. **Severity Classification**: CRITICAL, HIGH, MEDIUM, LOW
5. **Skip Recommendation**: Can the system run without this?

### Example Remediation

```
ISSUE: SEC_USER_AGENT not configured
ROOT CAUSE: SEC requires User-Agent header with organization name and contact email

REMEDIATION STEPS:
  1. Copy .env.example to .env
  2. Update SEC_USER_AGENT with your organization name and email
  3. Format: 'CompanyName/Version (contact@company.com)'

COMMANDS TO RUN:
  $ cp .env.example .env
  $ # Edit .env and set SEC_USER_AGENT=YourOrg/1.0 (contact@yourorg.com)

IMPACT: CRITICAL - Cannot access SEC EDGAR API without valid User-Agent
CAN SKIP: No - critical for operation
DEPENDENCIES AFFECTED: All SEC filing analysis nodes (1-6, 7-10)
```

## Dependency Resolver

Tracks component dependencies and calculates cascading impact:

```
DEPENDENCY IMPACT ANALYSIS
================================================================================

🔴 CRITICAL - SEC_USER_AGENT
  Impacts 10 component(s):
    - Node 1: Form 4 Insider Trading
    - Node 2: DEF 14A Compensation
    - Node 3: 10-Q Temporal Consistency
    - Node 4: 10-K SOX Certification
    - Node 5: IRC §83 Tax Calculator
    - Node 6: Enforcement Routing
    - Node 7: 13F-HR Holdings
    - Node 8: 13D/13G Ownership
    - Node 9: 8-K Material Events
    - Node 10: Form 144 Restricted Sales

SUMMARY
================================================================================
Failed Components: 1
Critical Failures: 1
Total Impacted Components: 10
```

## Mock Mode

Mock mode allows validation without external dependencies:

```bash
python -m tests.jlaw_master_test_suite --full --mock
```

Features:
- Skips external API calls (SEC, OpenAI, Anthropic)
- Uses pre-cached test fixtures
- Validates code paths without burning API quota
- Faster execution
- Useful for development iteration

## Graceful Degradation

The system gracefully degrades when optional components are unavailable:

### Optional Dependencies
- **torch, transformers**: System uses XGBoost fallback
- **DeBERTa**: Alternative NLP methods used
- **Neo4j**: Network analysis disabled
- **TimescaleDB**: Time-series storage disabled
- **Polygon.io**: Market correlation disabled

### Optional API Keys
- **OPENAI_API_KEY**: Single-agent mode (Anthropic only)
- **ANTHROPIC_API_KEY**: Single-agent mode (OpenAI only)
- **POLYGON_API_KEY**: Node 15 disabled
- **GOVINFO_API_KEY**: Statute lookup disabled

## CI/CD Integration

### GitHub Actions Example

```yaml
name: JLAW Production Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Create .env
        run: |
          echo "SEC_USER_AGENT=${{ secrets.SEC_USER_AGENT }}" >> .env
          echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
          echo "ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}" >> .env
      
      - name: Run Pre-Flight Check
        run: python -m tests.preflight_check
      
      - name: Run Full Test Suite
        run: python -m tests.jlaw_master_test_suite --full --mock
      
      - name: Upload Test Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: tests/reports/
```

### Jenkins Example

```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'python -m venv venv'
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }
        stage('Pre-Flight') {
            steps {
                sh '. venv/bin/activate && python -m tests.preflight_check'
            }
        }
        stage('Full Validation') {
            steps {
                sh '. venv/bin/activate && python -m tests.jlaw_master_test_suite --full --mock'
            }
        }
        stage('Publish Reports') {
            steps {
                publishHTML([
                    reportDir: 'tests/reports',
                    reportFiles: 'test_report.html',
                    reportName: 'JLAW Test Report'
                ])
            }
        }
    }
    post {
        failure {
            mail to: 'devops@yourorg.com',
                 subject: "JLAW Validation Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                 body: "Check ${env.BUILD_URL} for details"
        }
    }
}
```

## Troubleshooting

### Test Infrastructure Not Working

```bash
# Validate test infrastructure itself
python tests/test_infrastructure.py
```

### Missing Dependencies

```bash
# Check what's missing
python -m tests.jlaw_master_test_suite --category environment

# Install missing packages
pip install -r requirements.txt
```

### API Configuration Issues

```bash
# Validate configuration
python -m tests.config_validator

# Check specific API
python -m tests.jlaw_master_test_suite --category api_keys
```

### Node Import Failures

```bash
# Test specific nodes
python -m tests.jlaw_master_test_suite --category nodes

# Check Python path
python -c "import sys; print('\\n'.join(sys.path))"
```

### Permission Errors

```bash
# Check file permissions
ls -la .env
ls -la output/
ls -la .jlaw_cache/

# Fix permissions
chmod 600 .env  # .env should be readable only by user
chmod 755 output/
chmod 755 .jlaw_cache/
```

## Best Practices

1. **Always run pre-flight check** before starting analysis
2. **Use mock mode** during development to avoid API quota
3. **Review test reports** after failures to understand issues
4. **Update .env** immediately when getting new API keys
5. **Run full test suite** before production deployments
6. **Monitor exit codes** in CI/CD pipelines
7. **Keep test reports** for audit trails
8. **Regular validation** even after successful deployment

## Support

For issues or questions:
1. Check test reports in `tests/reports/`
2. Run with `--category` to isolate issues
3. Review remediation suggestions in output
4. Check documentation: `README.md`, `HOLY_GRAIL_PIPELINE.md`
5. Examine test suite code for specific validators

## License

See LICENSE file in repository root.

---

## Phase 3: Integration & Performance Testing

### New Test Suites (Phase 3 Implementation)

The Phase 3 implementation adds comprehensive integration, circuit breaker, and performance testing:

#### Integration Tests (`tests/integration/`)

**test_full_pipeline.py** - End-to-end forensic analysis:
```bash
# Full pipeline tests with real SEC data
pytest tests/integration/test_full_pipeline.py -v

# Individual test examples:
# - test_full_forensic_analysis_apple_2019: Complete Apple 2019 analysis
# - test_full_pipeline_nike_2020: Nike 2020 analysis  
# - test_pipeline_with_multiple_filings: Multi-filing test (Microsoft)
# - test_evidence_chain_continuity: Evidence chain validation
# - test_doj_dossier_completeness: DOJ dossier validation
```

**test_node_execution.py** - Node validation:
```bash
# Test all 15 nodes execute correctly
pytest tests/integration/test_node_execution.py -v

# Tests:
# - test_all_15_nodes_execute: Validates all nodes run
# - test_23_detection_patterns: Validates detection patterns
# - test_node_error_handling: Error handling validation
```

**test_circuit_breakers.py** - Fault tolerance:
```bash
# Circuit breaker and failover tests
pytest tests/integration/test_circuit_breakers.py -m circuit_breaker -v

# Tests:
# - SEC EDGAR rate limit handling
# - OpenAI to Anthropic fallback
# - RFC3161 TSA timeout fallback  
# - Neo4j graceful degradation
# - Strict mode cascade abort
# - Partial failure recovery
```

**test_fault_injection.py** - Resilience testing:
```bash
# Fault injection tests
pytest tests/integration/test_fault_injection.py -m circuit_breaker -v

# Tests:
# - Network timeout handling
# - Memory pressure handling
# - Invalid date ranges
# - Concurrent execution
```

#### Performance Tests (`tests/performance/`)

**test_load.py** - Performance & scalability:
```bash
# Performance tests (slow - marked accordingly)
pytest tests/performance/test_load.py -m slow -v

# Tests:
# - test_concurrent_analysis_throughput: 5 concurrent analyses
# - test_sequential_analysis_performance: Single analysis timing
# - test_large_date_range_performance: Full year analysis
```

### Running Phase 3 Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run circuit breaker tests only
pytest -m circuit_breaker -v

# Run performance tests
pytest -m slow -v

# Run everything with coverage
pytest --cov=src --cov-report=html -v

# Skip slow tests (faster CI runs)
pytest -m "not slow" -v
```

### Coverage Reporting

Phase 3 includes enhanced coverage reporting:

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html:coverage_report -v

# View coverage report
open coverage_report/index.html  # macOS
xdg-open coverage_report/index.html  # Linux

# Coverage is enforced at 80% minimum in CI/CD
```

### Test Output

Tests create output in `tests/output/` (gitignored):
- `apple_2019/` - Apple analysis outputs
- `nike_2020/` - Nike analysis outputs  
- `multi_filing/` - Microsoft multi-filing test
- `evidence_chain/` - Evidence chain tests
- `load_test/` - Performance test outputs

### CI/CD Integration

The `.github/workflows/ci.yml` now includes:
- **Coverage job**: Enforces 80% minimum coverage
- **Test artifacts**: Uploads coverage reports
- **Multiple Python versions**: Tests on 3.9, 3.10, 3.11, 3.12

### Test Markers Reference

```python
@pytest.mark.unit           # Fast, isolated unit tests
@pytest.mark.integration    # End-to-end workflow tests
@pytest.mark.circuit_breaker # Fault tolerance tests
@pytest.mark.slow           # Performance tests (>30s)
```

### Known Test Behaviors

1. **Integration tests fetch real SEC data** - May take 2-10 minutes each
2. **Performance tests are slow** - Marked with `@pytest.mark.slow`
3. **Circuit breaker tests validate failure modes** - Some may show expected errors
4. **Coverage minimum is 80%** - Enforced in CI/CD pipeline

### Adding Tests

When adding new tests:
1. Place in appropriate directory (`integration/`, `performance/`, `unit/`)
2. Use proper markers (`@pytest.mark.integration`, etc.)
3. Follow naming convention: `test_*.py`
4. Create output in `tests/output/<test_name>/`
5. Add docstrings explaining test purpose
6. Update this README if adding new categories
