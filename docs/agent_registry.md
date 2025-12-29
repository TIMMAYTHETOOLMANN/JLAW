# Agent Registry - Developer Guide

## Overview

The **Dynamic Agent Registry** automatically discovers and registers Claude subagents from markdown files in `.claude/agents/` directory. This eliminates the need for hardcoded agent-violation mappings and enables true plug-and-play agent extensibility.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               DynamicAgentRegistry                          │
│                                                             │
│  1. Discovers agents from *.md files                       │
│  2. Parses YAML frontmatter                                │
│  3. Extracts violation types from content                  │
│  4. Builds reverse index (violation → agents)              │
│  5. Scores agents based on relevance                       │
└─────────────────────────────────────────────────────────────┘
         │
         ├── Reads from: .claude/agents/**/*.md
         ├── Produces: AgentCapability objects
         └── Provides: get_agents_for_violations(violations, top_k)
```

## Agent Markdown Format

### Minimal Format

Agents work with just a filename:

```markdown
<!-- forensic-financial-analyst.md -->

You are a forensic financial analyst...
```

The agent name is derived from the filename.

### Recommended Format (with Frontmatter)

```markdown
---
name: forensic-financial-analyst
description: Quantitative forensic analyst specializing in financial fraud detection
tools: Read, Write, Edit, Bash, Glob, Grep
priority: 80
---

You are an expert forensic financial analyst...
```

### Enhanced Format (with Violation Types)

For intelligent agent selection based on violations:

```markdown
---
name: forensic-financial-analyst
description: Quantitative forensic analyst specializing in financial fraud detection
tools: Read, Write, Edit, Bash, Glob, Grep
priority: 80
---

## Violation Types
- insider_trading
- accounting_fraud
- options_backdating
- financial_distress
- bankruptcy_risk

## Core Capabilities
- Beneish M-Score calculation
- Altman Z-Score analysis
...
```

## Frontmatter Schema

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | No | filename | Unique agent identifier |
| `description` | string | No | "" | Brief agent description |
| `tools` | string/array | No | [] | Comma-separated tools or array |
| `priority` | int | No | 50 | Agent priority (0-100, higher = first) |

## Violation Types Section

The `## Violation Types` section is optional but enables intelligent routing:

```markdown
## Violation Types
- insider_trading        # Exact match on "insider_trading"
- accounting_fraud       # Exact match on "accounting_fraud"
- sox_violation          # Exact match on "sox_violation"
- financial_distress     # Partial match on "financial" or "distress"
```

**Matching Logic:**
- Exact match (normalized): `insider_trading` matches `Insider Trading`, `INSIDER-TRADING`
- Partial match: `insider_trading` matches `insider_trading_rule_10b5`
- Bidirectional: Agent `insider_trading` matches violation `insider_trading_complex`

## Priority Levels

| Range | Level | Use Case |
|-------|-------|----------|
| 80-100 | Critical | Primary fraud detection agents (financial, NLP) |
| 60-79 | High | Specialized analysis (compliance, research) |
| 40-59 | Medium | Supporting agents (network mapping, transcripts) |
| 0-39 | Low | Cleanup/aggregation agents (orchestrators) |

## Agent Discovery Process

### 1. File Discovery
```python
from src.forensics.agent_registry import DynamicAgentRegistry

registry = DynamicAgentRegistry()
# Automatically scans .claude/agents/**/*.md
```

### 2. Metadata Extraction
- Parse YAML frontmatter
- Extract violation types from `## Violation Types` section
- Normalize all violation type strings (lowercase, underscores)

### 3. Reverse Index Building
```python
# Builds: violation_to_agents: Dict[str, Set[str]]
# Example: {"insider_trading": {"financial-analyst", "research-specialist"}}
```

### 4. Agent Selection
```python
violations = [
    {"type": "insider_trading"},
    {"type": "accounting_fraud"}
]

agents = registry.get_agents_for_violations(violations, top_k=5)
# Returns top 5 most relevant agents, sorted by:
# 1. Match score (# of matching violations)
# 2. Priority (higher first)
# 3. Agent name (alphabetical)
```

## Adding New Agents

### Step 1: Create Markdown File
```bash
touch .claude/agents/forensic/forensic-tax-analyst.md
```

### Step 2: Add Frontmatter
```markdown
---
name: forensic-tax-analyst
description: Tax fraud specialist for IRC violations
tools: Read, Write, Grep
priority: 75
---
```

### Step 3: Add Violation Types (Optional)
```markdown
## Violation Types
- tax_evasion
- transfer_pricing
- offshore_holdings
```

### Step 4: Add Prompt Content
```markdown
You are an expert tax forensic analyst specializing in...
```

### Step 5: No Code Changes Required!
The agent is automatically discovered on next registry initialization.

## Programmatic Usage

### Basic Discovery
```python
from src.forensics.agent_registry import DynamicAgentRegistry

registry = DynamicAgentRegistry()

# Get all agents
print(f"Total agents: {len(registry.agents)}")
print(f"Agent names: {registry.list_agents()}")
```

### Agent Selection
```python
# Get agents for specific violations
violations = [
    {"type": "insider_trading", "confidence": 0.92},
    {"type": "late_form4", "days_late": 5}
]

agents = registry.get_agents_for_violations(violations, top_k=3)

for agent in agents:
    print(f"Agent: {agent.agent_name}")
    print(f"  Priority: {agent.priority}")
    print(f"  Matches: {agent.score_for_violations(['insider_trading', 'late_form4'])}")
```

### Get Specific Agent
```python
# Get agent by name
agent = registry.get_agent("forensic-financial-analyst")
if agent:
    print(f"Description: {agent.description}")
    print(f"Tools: {agent.tools}")
    print(f"Violation types: {agent.violation_types}")
```

### Statistics
```python
stats = registry.get_statistics()
print(f"Total agents: {stats['total_agents']}")
print(f"Violation coverage: {stats['violation_coverage']}")
print(f"Priority distribution: {stats['agents_by_priority']}")
```

## Integration with Orchestrator

The registry is automatically integrated with `SubagentOrchestrator`:

```python
from src.forensics.subagents.orchestrator import SubagentOrchestrator

orchestrator = SubagentOrchestrator()
# Registry and router are initialized automatically

violations = [{"type": "insider_trading"}]
result = await orchestrator.auto_orchestrate(violations)

# Router intelligently selects top-K agents
# Executes in parallel stages based on priority
# Aggregates results with consensus tracking
```

## Best Practices

### 1. Agent Naming
- Use kebab-case: `forensic-financial-analyst`
- Be descriptive: `forensic-nlp-analyst` not `nlp-agent`
- Include domain: `forensic-` prefix for forensic agents

### 2. Priority Assignment
- Reserve 90-100 for mission-critical agents
- Use 80-89 for primary analysis agents
- Use 70-79 for specialized agents
- Use 50-69 for support agents
- Use 0-49 for orchestration/cleanup

### 3. Violation Type Definition
- Use snake_case: `insider_trading` not `Insider Trading`
- Be specific: `options_backdating` not `fraud`
- Group related: `financial_distress`, `bankruptcy_risk`

### 4. Description Quality
- Keep under 200 characters
- Highlight key capabilities
- Mention primary use cases

### 5. Tool Selection
- Only list tools agent actually uses
- Standard tools: `Read, Write, Edit, Bash, Glob, Grep`
- Specialized tools: `WebFetch, WebSearch` (if needed)

## Troubleshooting

### Agent Not Discovered
```python
# Check if file exists
from pathlib import Path
agent_file = Path(".claude/agents/forensic/my-agent.md")
print(f"Exists: {agent_file.exists()}")

# Check registry
registry = DynamicAgentRegistry()
print(f"Agents found: {registry.list_agents()}")
```

### No Agents for Violation
```python
# Check violation type normalization
violation_type = "Insider Trading"
normalized = violation_type.lower().replace(" ", "_").replace("-", "_")
print(f"Normalized: {normalized}")  # insider_trading

# Check violation coverage
stats = registry.get_statistics()
print(f"Violation coverage: {stats['violation_coverage']}")
```

### Malformed YAML
- Ensure frontmatter is between `---` delimiters
- Validate YAML syntax: https://www.yamllint.com/
- Check for proper indentation
- Avoid special characters in keys

## Examples

See:
- `examples/agent_registry_demo.py` - Complete usage examples
- `tests/test_forensics_agent_registry.py` - Unit tests
- `.claude/agents/forensic/*.md` - Real agent examples

## API Reference

### DynamicAgentRegistry

```python
class DynamicAgentRegistry:
    def __init__(self, agents_dir: Optional[Path] = None)
    def get_agents_for_violations(self, violations: List[Dict], top_k: int = 5) -> List[AgentCapability]
    def get_agent(self, name: str) -> Optional[AgentCapability]
    def list_agents(self) -> List[str]
    def get_agents_by_violation_type(self, violation_type: str) -> List[AgentCapability]
    def get_statistics(self) -> Dict[str, Any]
```

### AgentCapability

```python
@dataclass
class AgentCapability:
    agent_name: str
    description: str
    violation_types: Set[str]
    tools: List[str]
    priority: int
    requires_anthropic: bool
    markdown_path: Path
    prompt_template: str
    
    def matches_violation(self, violation_type: str) -> bool
    def score_for_violations(self, violation_types: List[str]) -> float
```

## See Also

- [Intelligent Routing Guide](./intelligent_routing.md) - Multi-agent execution
- [SDK Manager Guide](./sdk_integration.md) - API client management
- [JLAW Architecture](../README.md) - System overview
