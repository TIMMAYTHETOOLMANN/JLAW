Welcome to the OpenAI Agents SDK repository. This file contains the main points for new contributors.

## Repository overview

- **Source code**: `src/agents/` contains the implementation.
- **Tests**: `tests/` with a short guide in `tests/README.md`.
- **Examples**: under `examples/`.
- **Documentation**: markdown pages live in `docs/` with `mkdocs.yml` controlling the site.
- **Utilities**: developer commands are defined in the `Makefile`.
- **PR template**: `.github/PULL_REQUEST_TEMPLATE/pull_request_template.md` describes the information every PR must include.

## Local workflow

1. Format, lint and type‑check your changes:

   ```bash
   make format
   make lint
   make mypy
   ```

2. Run the tests:

   ```bash
   make tests
   ```

   To run a single test, use `uv run pytest -s -k <test_name>`.

3. Build the documentation (optional but recommended for docs changes):

   ```bash
   make build-docs
   ```

   Coverage can be generated with `make coverage`.

All python commands should be run via `uv run python ...`

## Snapshot tests

Some tests rely on inline snapshots. See `tests/README.md` for details on updating them:

```bash
make snapshots-fix      # update existing snapshots
make snapshots-create   # create new snapshots
```

Run `make tests` again after updating snapshots to ensure they pass.

## Style notes

- Write comments as full sentences and end them with a period.

## Pull request expectations

PRs should use the template located at `.github/PULL_REQUEST_TEMPLATE/pull_request_template.md`. Provide a summary, test plan and issue number if applicable, then check that:

- New tests are added when needed.
- Documentation is updated.
- `make lint` and `make format` have been run.
- The full test suite passes.

Commit messages should be concise and written in the imperative mood. Small, focused commits are preferred.

## What reviewers look for

- Tests covering new behaviour.
- Consistent style: code formatted with `uv run ruff format`, imports sorted, and type hints passing `uv run mypy .`.
- Clear documentation for any public API changes.
- Clean history and a helpful PR description.

---

## Claude Code Subagent Integration (JLAW Forensic Platform)

### Overview

The JLAW forensic analysis platform includes 14 specialized VoltAgent Claude Code subagents for multi-agent orchestration in forensic investigations. These subagents provide domain-specific expertise across forensic analysis, infrastructure, and development.

### Subagent Categories

#### 1. Forensic Subagents (`.claude/agents/forensic/`)

Specialized agents for SEC filing analysis and fraud detection:

- **forensic-nlp-analyst**: NLP specialist for contradiction detection and linguistic analysis
- **forensic-financial-analyst**: Quantitative analyst for Beneish M-Score, Benford's Law, and ML fraud detection
- **forensic-research-specialist**: Research specialist for SEC filing retrieval and whistleblower investigation
- **forensic-compliance-auditor**: Regulatory compliance mapping to SEC rules and federal statutes

#### 2. Orchestration Subagents (`.claude/agents/orchestration/`)

Coordinate multi-agent workflows:

- **forensic-workflow-orchestrator**: Master orchestrator for comprehensive forensic investigations
- **multi-agent-coordinator**: Tactical coordinator for agent handoffs and task routing
- **context-manager**: Manages investigation context and state across agent invocations

#### 3. Infrastructure Subagents (`.claude/agents/infrastructure/`)

Support deployment and infrastructure:

- **devops-engineer**: CI/CD pipelines and deployment automation
- **security-engineer**: Evidence integrity and chain of custody verification
- **database-administrator**: Forensic data storage management
- **cloud-architect**: Cloud deployment architecture (AWS, Azure, GCP)

#### 4. Development Subagents (`.claude/agents/development/`)

Assist with development tasks:

- **python-pro**: Expert Python development for forensic modules
- **backend-developer**: REST API and microservices development
- **documentation-engineer**: Technical documentation and API docs

### Integration with JLAW Modules

Subagents integrate with core forensic modules:

- `src/forensics/enhanced_contradiction_detector.py` - NLP analysis
- `src/forensics/benfords_law_analyzer.py` - Statistical analysis
- `src/forensics/ml_fraud_detector.py` - Machine learning models
- `src/forensics/multi_tier_sec_fetcher.py` - SEC data retrieval
- `src/forensics/forensic_statutory_mapper.py` - Compliance mapping
- `src/forensics/unified_forensic_pipeline.py` - Orchestration

### Usage

Deploy and verify subagents:

```bash
python scripts/deploy_subagents.py --verbose
```

### Documentation

- **Comprehensive Guide**: [.claude/SUBAGENT_INTEGRATION.md](.claude/SUBAGENT_INTEGRATION.md)
- **Individual Subagents**: [.claude/agents/](.claude/agents/)
- **Example Invocations**: See integration guide for detailed usage examples

### Architecture

```
Forensic Workflow Orchestrator
    ↓
Multi-Agent Coordinator & Context Manager
    ↓
[NLP Analyst] [Financial Analyst] [Research Specialist] [Compliance Auditor]
    ↓
Evidence Aggregation & Report Generation
```

For detailed information on using subagents, see [.claude/SUBAGENT_INTEGRATION.md](.claude/SUBAGENT_INTEGRATION.md).
