# QUICK REFERENCE: Multi-Agent AI System

## STATUS: OPERATIONAL

Both OpenAI GPT-4 and Anthropic Claude integrated and verified.

## Quick Start Commands

### Standard Analysis (Auto Provider)
```bash
python jlaw_forensics.py investigate --cik 0000320187 --name "Nike Inc" --years 1
```

### Deep Analysis (Anthropic)
```bash
python jlaw_forensics.py investigate --cik 0000320187 --name "Nike Inc" --years 1 --ai-provider ANTHROPIC
```

### Multi-Pass Analysis
```bash
python jlaw_forensics.py investigate --cik 0000320187 --name "Nike Inc" --years 1 --multipass
```

## Provider Selection

| Flag | Provider | Use Case |
|------|----------|----------|
| `--ai-provider AUTO` | Auto-select | Default, uses best available |
| `--ai-provider OPENAI` | OpenAI GPT-4 | Fast, general-purpose |
| `--ai-provider ANTHROPIC` | Anthropic Claude | Deep reasoning |
| `--ai-provider NONE` | Manual only | Disable AI completely |

## Configuration (.env)

```dotenv
AI_PROVIDER=AUTO
ENABLE_MULTIPASS_ANALYSIS=false
OPENAI_API_KEY=sk-proj-[YOUR-KEY]
ANTHROPIC_API_KEY=sk-ant-api03-[YOUR-KEY]
```

## Verification

```bash
python verify_multiagent_integration.py
```

Expected: Both OpenAI and Anthropic show as operational.

## Key Files

- **OpenAI Analyzer**: `src/forensics/agent_sec_analyzer.py`
- **Anthropic Analyzer**: `src/forensics/anthropic_agent_analyzer.py`
- **Multi-Pass**: `src/forensics/multipass_strategy.py`
- **Orchestrator**: `src/forensics/forensic_orchestrator.py`

## What Changed

1. Added Anthropic Claude for deep analysis
2. Multi-pass analysis framework (up to 4 passes)
3. Intelligent provider selection (AUTO mode)
4. CLI flags for provider control
5. Enhanced security (secrets protection)

## Expected Results

| Mode | Violations Expected |
|------|---------------------|
| Manual | 1-10 |
| OpenAI | 20-30 |
| Anthropic | 30-40 |
| Multi-Pass | 54+ (benchmark) |

## Next Steps

1. Run Nike 2019 analysis with multi-pass
2. Compare to 54+ violation benchmark
3. Monitor API costs and performance
4. Rotate any exposed API keys

## Support

- Full docs: `MULTIAGENT_AI_INTEGRATION_COMPLETE.md`
- Issues: Check ForensicOrchestrator logs
- Health: `python verify_multiagent_integration.py`

---

**Status**: Production Ready
**Date**: November 24, 2025

