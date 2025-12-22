# JLAW Test Suite Quick Reference

## One-Line Commands

```bash
# Quick validation (< 30s)
python -m tests.preflight_check

# Full test suite
python -m tests.jlaw_master_test_suite --full

# Mock mode (no API calls)
python -m tests.jlaw_master_test_suite --full --mock

# One-click deployment
python scripts/deploy_jlaw.py --auto
```

## Common Tasks

### Setup New Environment
```bash
python scripts/setup_environment.py
python scripts/generate_env_template.py
# Edit .env with your API keys
python -m tests.config_validator
python -m tests.preflight_check
```

### Test Specific Components
```bash
# Environment & dependencies
python -m tests.jlaw_master_test_suite --category environment

# API keys
python -m tests.jlaw_master_test_suite --category api_keys

# 15 analysis nodes
python -m tests.jlaw_master_test_suite --category nodes

# Detection patterns
python -m tests.jlaw_master_test_suite --category detection

# AI agents
python -m tests.jlaw_master_test_suite --category agents

# Evidence chain
python -m tests.jlaw_master_test_suite --category evidence_chain

# Reporting layer
python -m tests.jlaw_master_test_suite --category reporting
```

### Generate Reports
```bash
# JSON report
python -m tests.jlaw_master_test_suite --full --report json --output results.json

# Markdown report
python -m tests.jlaw_master_test_suite --full --report markdown --output report.md

# HTML report
python -m tests.jlaw_master_test_suite --full --report html --output report.html

# All formats
python -m tests.jlaw_master_test_suite --full --report all
```

## Exit Codes

- `0` = Production ready ✅
- `1` = Critical failures ❌
- `2` = Non-critical failures ⚠️
- `3` = Configuration errors 🔧

## Required Configuration

**Minimum (.env)**:
```bash
SEC_USER_AGENT=YourOrg/1.0 (contact@yourorg.com)
```

**Recommended**:
```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

## File Locations

- Configuration: `.env`
- Test reports: `tests/reports/`
- Cache: `.jlaw_cache/`
- Output: `output/`
- Logs: `output/*.log`

## Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "SEC_USER_AGENT invalid"
```bash
# Edit .env:
SEC_USER_AGENT=YourCompany/1.0 (admin@yourcompany.com)
```

### "API key missing"
```bash
python scripts/generate_env_template.py
# Edit .env with your keys
```

### "Permission denied"
```bash
chmod 600 .env
chmod 755 output/ .jlaw_cache/
```

## Quick Validation Workflow

1. **Test infrastructure**: `python tests/test_infrastructure.py`
2. **Setup environment**: `python scripts/setup_environment.py`
3. **Configure API keys**: `python scripts/generate_env_template.py` + edit .env
4. **Validate config**: `python -m tests.config_validator`
5. **Pre-flight check**: `python -m tests.preflight_check`
6. **Full test suite**: `python -m tests.jlaw_master_test_suite --full --mock`
7. **Deploy**: `python scripts/deploy_jlaw.py --auto`

## CI/CD Integration

```bash
# In CI/CD pipeline:
python -m tests.preflight_check && \
python -m tests.jlaw_master_test_suite --full --mock && \
echo "Deployment approved" || exit 1
```

## Support Resources

- Full documentation: `tests/README.md`
- System architecture: `HOLY_GRAIL_PIPELINE.md`
- Main README: `README.md`
- Strict mode: `STRICT_EXECUTION_MODE.md`
