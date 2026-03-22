"""
Claude Agent Integration Layer for JLAW Forensic Analysis Platform
===================================================================

Provides embedded Claude agent capabilities using the raw ``anthropic`` SDK
with the Tool Runner agentic loop pattern. This module implements:

- **Tool Runner** — Agentic loop executing forensic tools via Claude's
  tool_use API (search filings, analyze documents, detect patterns, etc.)
- **Forensic Tools** — JSON Schema tool definitions for SEC analysis,
  penalty calculation, whistleblower eligibility, and evidence chain queries.
- **System Prompts** — XML-tagged prompts with prompt caching support for
  90% cost reduction on repeated system prompt reads.
- **MCP Servers** — Configuration for Model Context Protocol servers
  providing SEC EDGAR access and custom database integration.
- **Multi-Agent Orchestration** — Prosecutor pattern with tiered Claude
  models (Opus for master, Sonnet for subagents, Haiku for triage).
- **Context Management** — Degradation prevention via compaction,
  structured state management, and fresh context design.

Architecture:
    Raw ``anthropic`` SDK (>=0.86.0) → Tool Runner pattern → Forensic tools
    → MCP servers (SEC EDGAR, anomaly DB, evidence chain)
    → Multi-agent prosecutor orchestration
    → Context degradation prevention

Usage::

    from src.claude_agent import ForensicToolRunner, ToolExecutor

    executor = ToolExecutor()
    executor.register("search_sec_filings", my_search_handler)

    runner = ForensicToolRunner(
        model="claude-sonnet-4-6",
        tool_executor=executor,
    )
    result = await runner.run("Investigate NIKE Inc (CIK 320187) for 2019")

Version: 1.0.0
"""

__version__ = "1.0.0"

from src.claude_agent.context_manager import (
    ContextManager,
    InvestigationState,
)
from src.claude_agent.mcp_servers import (
    MCPConfiguration,
    MCPServerConfig,
    get_default_mcp_config,
)
from src.claude_agent.multi_agent import (
    DEFAULT_SUBAGENTS,
    ModelTier,
    ProsecutorOrchestrator,
    ProsecutorResult,
    SubagentConfig,
    SubagentResult,
)
from src.claude_agent.system_prompts import (
    FORENSIC_SYSTEM_PROMPT,
    SUBAGENT_PROMPTS,
    get_forensic_system_prompt,
    get_investigation_prompt,
    get_subagent_prompt,
)
from src.claude_agent.tool_runner import (
    ForensicToolRunner,
    RunnerResult,
    ToolExecutor,
    ToolResult,
)
from src.claude_agent.tools import (
    FORENSIC_TOOLS,
    get_forensic_tools,
    get_tool_names,
    get_tools_by_names,
)

__all__ = [
    # Tool Runner
    "ForensicToolRunner",
    "ToolExecutor",
    "ToolResult",
    "RunnerResult",
    # Tools
    "FORENSIC_TOOLS",
    "get_forensic_tools",
    "get_tool_names",
    "get_tools_by_names",
    # System Prompts
    "FORENSIC_SYSTEM_PROMPT",
    "SUBAGENT_PROMPTS",
    "get_forensic_system_prompt",
    "get_investigation_prompt",
    "get_subagent_prompt",
    # MCP
    "MCPServerConfig",
    "MCPConfiguration",
    "get_default_mcp_config",
    # Multi-Agent
    "ModelTier",
    "SubagentConfig",
    "SubagentResult",
    "ProsecutorOrchestrator",
    "ProsecutorResult",
    "DEFAULT_SUBAGENTS",
    # Context Management
    "InvestigationState",
    "ContextManager",
]
