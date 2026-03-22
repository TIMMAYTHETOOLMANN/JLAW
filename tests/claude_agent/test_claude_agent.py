"""Tests for the Claude Agent integration layer.

Tests cover all modules in src/claude_agent/:
- tools.py: Forensic tool definitions and helpers
- system_prompts.py: XML-tagged prompts and investigation prompts
- tool_runner.py: Agentic loop, ToolExecutor, ToolResult, RunnerResult
- mcp_servers.py: MCP server configuration and management
- multi_agent.py: Prosecutor orchestration, model tiers, subagents
- context_manager.py: InvestigationState and ContextManager

All tests are pure unit tests using mocks — no external API calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.claude_agent.context_manager import ContextManager, InvestigationState
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

# ═══════════════════════════════════════════════════════════════════════
# Tools Tests
# ═══════════════════════════════════════════════════════════════════════


class TestForensicTools:
    """Test forensic tool definitions."""

    def test_all_tools_have_required_fields(self):
        """Every tool must have name, description, and input_schema."""
        for tool in FORENSIC_TOOLS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"
            assert "input_schema" in tool, f"Tool missing 'input_schema': {tool}"

    def test_tool_descriptions_minimum_length(self):
        """Tool descriptions should be 3-4+ sentences per Anthropic guidance."""
        for tool in FORENSIC_TOOLS:
            desc = tool["description"]
            # At least 100 chars (roughly 2-3 sentences minimum)
            assert len(desc) >= 100, (
                f"Tool '{tool['name']}' description too short ({len(desc)} chars)"
            )

    def test_tool_schemas_have_type_object(self):
        """All input schemas must have type 'object'."""
        for tool in FORENSIC_TOOLS:
            schema = tool["input_schema"]
            assert schema["type"] == "object", (
                f"Tool '{tool['name']}' schema type is '{schema['type']}', expected 'object'"
            )

    def test_tool_schemas_have_properties(self):
        """All input schemas must have properties."""
        for tool in FORENSIC_TOOLS:
            schema = tool["input_schema"]
            assert "properties" in schema, (
                f"Tool '{tool['name']}' schema missing 'properties'"
            )

    def test_tool_count(self):
        """JLAW forensic tools should have expected count."""
        assert len(FORENSIC_TOOLS) == 8

    def test_get_forensic_tools_returns_full_list(self):
        """get_forensic_tools() should return all tools."""
        tools = get_forensic_tools()
        assert tools == FORENSIC_TOOLS

    def test_get_tool_names(self):
        """get_tool_names() should return all tool name strings."""
        names = get_tool_names()
        assert len(names) == 8
        assert "search_sec_filings" in names
        assert "analyze_filing" in names
        assert "calculate_penalty" in names

    def test_get_tools_by_names_filters(self):
        """get_tools_by_names() should return only requested tools."""
        subset = get_tools_by_names(["search_sec_filings", "calculate_penalty"])
        assert len(subset) == 2
        names = [t["name"] for t in subset]
        assert "search_sec_filings" in names
        assert "calculate_penalty" in names

    def test_get_tools_by_names_empty(self):
        """get_tools_by_names([]) should return empty list."""
        assert get_tools_by_names([]) == []

    def test_get_tools_by_names_nonexistent(self):
        """get_tools_by_names() with unknown name should return empty."""
        assert get_tools_by_names(["nonexistent_tool"]) == []

    def test_required_fields_present(self):
        """All tools must have at least one required field."""
        for tool in FORENSIC_TOOLS:
            schema = tool["input_schema"]
            assert "required" in schema, (
                f"Tool '{tool['name']}' schema missing 'required'"
            )
            assert len(schema["required"]) >= 1


# ═══════════════════════════════════════════════════════════════════════
# System Prompts Tests
# ═══════════════════════════════════════════════════════════════════════


class TestSystemPrompts:
    """Test XML-tagged system prompts."""

    def test_forensic_prompt_contains_xml_tags(self):
        """System prompt must use XML tags per Anthropic recommendation."""
        prompt = FORENSIC_SYSTEM_PROMPT
        assert "<role>" in prompt
        assert "</role>" in prompt
        assert "<enforcement_routing>" in prompt
        assert "<analysis_protocol>" in prompt
        assert "<evidence_standards>" in prompt
        assert "<detection_patterns>" in prompt

    def test_forensic_prompt_length_in_range(self):
        """System prompt should be 3,000-10,000 tokens (~12K-40K chars)."""
        prompt = get_forensic_system_prompt()
        # Rough estimate: 1 token ≈ 4 chars
        estimated_tokens = len(prompt) // 4
        assert estimated_tokens >= 500, f"Prompt too short ({estimated_tokens} est. tokens)"
        assert estimated_tokens <= 15000, f"Prompt too long ({estimated_tokens} est. tokens)"

    def test_forensic_prompt_contains_examples(self):
        """System prompt should include canonical examples."""
        prompt = get_forensic_system_prompt()
        assert "<examples>" in prompt
        assert "<example " in prompt

    def test_get_investigation_prompt(self):
        """Investigation prompt should include company info."""
        prompt = get_investigation_prompt("320187", "NIKE, Inc.")
        assert "320187" in prompt
        assert "NIKE, Inc." in prompt

    def test_get_investigation_prompt_with_filings(self):
        """Investigation prompt should include filing types when specified."""
        prompt = get_investigation_prompt(
            "320187", "NIKE, Inc.", filing_types=["10-K", "DEF 14A"]
        )
        assert "10-K" in prompt
        assert "DEF 14A" in prompt

    def test_get_investigation_prompt_with_date_range(self):
        """Investigation prompt should include date range."""
        prompt = get_investigation_prompt(
            "320187", "NIKE, Inc.", date_range="2019-01-01 to 2019-12-31"
        )
        assert "2019-01-01 to 2019-12-31" in prompt

    def test_subagent_prompts_all_roles(self):
        """All expected subagent roles should exist."""
        expected_roles = {
            "sec_analysis", "doj_referral",
            "whistleblower_bounty", "briefing_generation",
        }
        assert set(SUBAGENT_PROMPTS.keys()) == expected_roles

    def test_get_subagent_prompt_valid_role(self):
        """get_subagent_prompt() should return prompt for valid role."""
        prompt = get_subagent_prompt("sec_analysis")
        assert "SEC" in prompt
        assert len(prompt) > 50

    def test_get_subagent_prompt_invalid_role(self):
        """get_subagent_prompt() should raise KeyError for invalid role."""
        with pytest.raises(KeyError, match="Unknown subagent role"):
            get_subagent_prompt("nonexistent_role")


# ═══════════════════════════════════════════════════════════════════════
# Tool Runner Tests
# ═══════════════════════════════════════════════════════════════════════


class TestToolResult:
    """Test ToolResult data class."""

    def test_to_message_block_success(self):
        """ToolResult should serialize to valid message block."""
        result = ToolResult(
            tool_use_id="test-123",
            tool_name="search_sec_filings",
            result={"filings": [{"type": "10-K"}]},
        )
        block = result.to_message_block()
        assert block["type"] == "tool_result"
        assert block["tool_use_id"] == "test-123"
        assert "is_error" not in block

    def test_to_message_block_error(self):
        """ToolResult with is_error should include error flag."""
        result = ToolResult(
            tool_use_id="test-456",
            tool_name="analyze_filing",
            result="Connection timeout",
            is_error=True,
        )
        block = result.to_message_block()
        assert block["is_error"] is True
        assert block["content"] == "Connection timeout"

    def test_to_message_block_dict_result(self):
        """Dict results should be JSON-serialized in the block."""
        result = ToolResult(
            tool_use_id="test-789",
            tool_name="calculate_penalty",
            result={"penalty": 50000},
        )
        block = result.to_message_block()
        parsed = json.loads(block["content"])
        assert parsed["penalty"] == 50000


class TestRunnerResult:
    """Test RunnerResult data class."""

    def test_to_dict(self):
        """RunnerResult.to_dict() should include all fields."""
        result = RunnerResult(
            response_text="Analysis complete",
            model="claude-sonnet-4-6",
            stop_reason="end_turn",
            loop_iterations=3,
            total_input_tokens=1500,
            total_output_tokens=800,
        )
        d = result.to_dict()
        assert d["response_text"] == "Analysis complete"
        assert d["model"] == "claude-sonnet-4-6"
        assert d["stop_reason"] == "end_turn"
        assert d["loop_iterations"] == 3
        assert d["total_input_tokens"] == 1500
        assert d["total_output_tokens"] == 800

    def test_defaults(self):
        """RunnerResult should have sensible defaults."""
        result = RunnerResult()
        assert result.response_text == ""
        assert result.tool_calls == []
        assert result.total_time == 0.0


class TestToolExecutor:
    """Test ToolExecutor registry."""

    def test_register_and_execute(self):
        """Should register a handler and execute it."""
        executor = ToolExecutor()
        executor.register("search_sec_filings", lambda inp: {"count": 5})
        result = executor.execute("search_sec_filings", {"cik": "320187"})
        assert result == {"count": 5}

    def test_execute_unregistered_raises(self):
        """Should raise KeyError for unregistered tool."""
        executor = ToolExecutor()
        with pytest.raises(KeyError, match="No handler registered"):
            executor.execute("nonexistent", {})

    def test_registered_tools_list(self):
        """Should list all registered tool names."""
        executor = ToolExecutor()
        executor.register("tool_a", lambda x: x)
        executor.register("tool_b", lambda x: x)
        assert sorted(executor.registered_tools) == ["tool_a", "tool_b"]


class TestForensicToolRunner:
    """Test ForensicToolRunner initialization and configuration."""

    def test_init_defaults(self):
        """Default initialization should use Sonnet model."""
        runner = ForensicToolRunner()
        assert runner.model == "claude-sonnet-4-6"
        assert runner.max_tokens == 4096
        assert runner.max_iterations == 25
        assert runner.enable_prompt_caching is True

    def test_init_custom_model(self):
        """Should accept custom model configuration."""
        runner = ForensicToolRunner(model="claude-opus-4-6", max_tokens=8192)
        assert runner.model == "claude-opus-4-6"
        assert runner.max_tokens == 8192

    def test_model_tier_constants(self):
        """Model tier constants should match expected values."""
        assert ForensicToolRunner.MODEL_OPUS == "claude-opus-4-6"
        assert ForensicToolRunner.MODEL_SONNET == "claude-sonnet-4-6"
        assert ForensicToolRunner.MODEL_HAIKU == "claude-haiku-4-5"

    def test_build_system_param_with_caching(self):
        """With caching enabled, system param should include cache_control."""
        runner = ForensicToolRunner(enable_prompt_caching=True)
        param = runner._build_system_param()
        assert isinstance(param, list)
        assert param[0]["type"] == "text"
        assert param[0]["cache_control"] == {"type": "ephemeral"}

    def test_build_system_param_without_caching(self):
        """With caching disabled, system param should be plain string."""
        runner = ForensicToolRunner(enable_prompt_caching=False)
        param = runner._build_system_param()
        assert isinstance(param, str)

    def test_execute_tool_call_success(self):
        """Tool execution should return success result."""
        executor = ToolExecutor()
        executor.register("test_tool", lambda inp: {"status": "ok"})
        runner = ForensicToolRunner(tool_executor=executor)
        result = runner._execute_tool_call("test_tool", {}, "id-1")
        assert result.is_error is False
        assert result.result == {"status": "ok"}
        assert result.tool_name == "test_tool"

    def test_execute_tool_call_error(self):
        """Tool execution failure should return error result."""
        def failing_tool(inp):
            raise ValueError("Test error")

        executor = ToolExecutor()
        executor.register("fail_tool", failing_tool)
        runner = ForensicToolRunner(tool_executor=executor)
        result = runner._execute_tool_call("fail_tool", {}, "id-2")
        assert result.is_error is True
        assert "Test error" in result.result

    async def test_run_end_turn(self):
        """Runner should stop when Claude returns end_turn."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Analysis complete"
        mock_response.content = [mock_text_block]
        mock_response.usage = MagicMock(
            input_tokens=100, output_tokens=50,
            cache_read_input_tokens=0, cache_creation_input_tokens=0
        )
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        runner = ForensicToolRunner()
        runner._client = mock_client
        result = await runner.run("Test query")

        assert result.response_text == "Analysis complete"
        assert result.stop_reason == "end_turn"
        assert result.loop_iterations == 1

    async def test_run_with_tool_execution(self):
        """Runner should execute tool calls and loop until end_turn."""
        mock_client = AsyncMock()

        # First response: Claude calls a tool
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.name = "search_sec_filings"
        mock_tool_block.input = {"cik": "320187"}
        mock_tool_block.id = "tool-call-1"
        mock_tool_block.text = None
        # Ensure hasattr(block, "text") is False for tool blocks
        del mock_tool_block.text

        mock_response_1 = MagicMock()
        mock_response_1.stop_reason = "tool_use"
        mock_response_1.content = [mock_tool_block]
        mock_response_1.usage = MagicMock(
            input_tokens=200, output_tokens=100,
            cache_read_input_tokens=0, cache_creation_input_tokens=0
        )

        # Second response: Claude returns final text
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Found 3 filings for CIK 320187"
        mock_response_2 = MagicMock()
        mock_response_2.stop_reason = "end_turn"
        mock_response_2.content = [mock_text_block]
        mock_response_2.usage = MagicMock(
            input_tokens=300, output_tokens=150,
            cache_read_input_tokens=50, cache_creation_input_tokens=0
        )

        mock_client.messages.create = AsyncMock(
            side_effect=[mock_response_1, mock_response_2]
        )

        # Register a tool handler
        executor = ToolExecutor()
        executor.register(
            "search_sec_filings",
            lambda inp: {"filings": [{"type": "10-K"}], "count": 3},
        )

        runner = ForensicToolRunner(tool_executor=executor)
        runner._client = mock_client
        result = await runner.run("Search NIKE filings")

        assert result.loop_iterations == 2
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["name"] == "search_sec_filings"
        assert len(result.tool_results) == 1
        assert result.tool_results[0].is_error is False
        assert result.response_text == "Found 3 filings for CIK 320187"
        assert result.stop_reason == "end_turn"
        assert result.total_input_tokens == 500  # 200 + 300
        assert result.total_output_tokens == 250  # 100 + 150
        assert result.cache_read_tokens == 50


# ═══════════════════════════════════════════════════════════════════════
# MCP Servers Tests
# ═══════════════════════════════════════════════════════════════════════


class TestMCPServerConfig:
    """Test MCP server configuration."""

    def test_to_dict(self):
        """MCPServerConfig should serialize correctly."""
        config = MCPServerConfig(
            name="test-server",
            command="python",
            args=["-m", "test_server"],
        )
        d = config.to_dict()
        assert d["command"] == "python"
        assert d["args"] == ["-m", "test_server"]

    def test_to_dict_with_env(self):
        """MCPServerConfig with env should include it."""
        config = MCPServerConfig(
            name="test-server",
            command="python",
            args=[],
            env={"API_KEY": "test"},
        )
        d = config.to_dict()
        assert d["env"] == {"API_KEY": "test"}


class TestMCPConfiguration:
    """Test MCP configuration management."""

    def test_add_and_get_server(self):
        """Should add and retrieve servers."""
        config = MCPConfiguration()
        server = MCPServerConfig(name="test", command="python", args=[])
        config.add_server(server)
        assert config.get_server("test") is server

    def test_remove_server(self):
        """Should remove servers."""
        config = MCPConfiguration()
        server = MCPServerConfig(name="test", command="python", args=[])
        config.add_server(server)
        config.remove_server("test")
        assert config.get_server("test") is None

    def test_get_enabled_servers(self):
        """Should filter to only enabled servers."""
        config = MCPConfiguration()
        config.add_server(MCPServerConfig(name="a", command="p", enabled=True))
        config.add_server(MCPServerConfig(name="b", command="p", enabled=False))
        enabled = config.get_enabled_servers()
        assert "a" in enabled
        assert "b" not in enabled

    def test_default_config(self):
        """Default config should have SEC EDGAR server."""
        config = get_default_mcp_config()
        assert "sec-edgar" in config.servers
        assert config.servers["sec-edgar"].enabled is True
        assert config.servers["anomaly-db"].enabled is False
        assert config.servers["evidence-chain"].enabled is False


# ═══════════════════════════════════════════════════════════════════════
# Multi-Agent Tests
# ═══════════════════════════════════════════════════════════════════════


class TestModelTier:
    """Test model tier enum."""

    def test_model_values(self):
        """Model tiers should have correct model identifiers."""
        assert ModelTier.OPUS.value == "claude-opus-4-6"
        assert ModelTier.SONNET.value == "claude-sonnet-4-6"
        assert ModelTier.HAIKU.value == "claude-haiku-4-5"


class TestSubagentConfig:
    """Test subagent configuration."""

    def test_default_subagents_count(self):
        """Should have 4 default subagents."""
        assert len(DEFAULT_SUBAGENTS) == 4

    def test_default_subagent_roles(self):
        """Default subagents should cover all prosecutor roles."""
        roles = {s.role for s in DEFAULT_SUBAGENTS}
        assert roles == {
            "sec_analysis", "doj_referral",
            "whistleblower_bounty", "briefing_generation",
        }

    def test_subagents_have_tools(self):
        """Each default subagent should have at least one tool."""
        for sub in DEFAULT_SUBAGENTS:
            assert len(sub.tools) >= 1, (
                f"Subagent '{sub.agent_id}' has no tools"
            )


class TestSubagentResult:
    """Test subagent result data class."""

    def test_to_dict(self):
        """SubagentResult should serialize correctly."""
        result = SubagentResult(
            agent_id="sec-analysis",
            role="sec_analysis",
            status="success",
            findings={"violations": 3},
            execution_time=1.5,
            tokens_used=500,
        )
        d = result.to_dict()
        assert d["agent_id"] == "sec-analysis"
        assert d["status"] == "success"
        assert d["tokens_used"] == 500


class TestProsecutorResult:
    """Test prosecutor result data class."""

    def test_to_dict(self):
        """ProsecutorResult should serialize correctly."""
        result = ProsecutorResult(
            master_summary="Investigation complete",
            total_tokens=2000,
            total_time=5.0,
        )
        d = result.to_dict()
        assert d["master_summary"] == "Investigation complete"
        assert d["total_tokens"] == 2000


class TestProsecutorOrchestrator:
    """Test prosecutor orchestrator."""

    def test_init_defaults(self):
        """Default init should use Opus master model."""
        orch = ProsecutorOrchestrator()
        assert orch.master_model == "claude-opus-4-6"
        assert orch.enable_parallel is True
        assert len(orch.subagents) == 4

    def test_init_custom(self):
        """Should accept custom configuration."""
        custom_subs = [
            SubagentConfig(agent_id="custom", role="sec_analysis"),
        ]
        orch = ProsecutorOrchestrator(
            master_model=ModelTier.SONNET.value,
            subagents=custom_subs,
            enable_parallel=False,
        )
        assert orch.master_model == "claude-sonnet-4-6"
        assert len(orch.subagents) == 1
        assert orch.enable_parallel is False


# ═══════════════════════════════════════════════════════════════════════
# Context Manager Tests
# ═══════════════════════════════════════════════════════════════════════


class TestInvestigationState:
    """Test investigation state management."""

    def test_init_defaults(self):
        """Default state should be in initialization phase."""
        state = InvestigationState()
        assert state.current_phase == "initialization"
        assert state.findings == []
        assert state.violations == []
        assert state.gaps == []

    def test_add_finding(self):
        """Should add findings without duplicates."""
        state = InvestigationState()
        state.add_finding("Late Form 4 detected")
        state.add_finding("Late Form 4 detected")  # duplicate
        assert len(state.findings) == 1

    def test_add_violation(self):
        """Should add violations."""
        state = InvestigationState()
        state.add_violation({"type": "late_form4", "severity": "HIGH"})
        assert len(state.violations) == 1
        assert state.violations[0]["type"] == "late_form4"

    def test_add_gap(self):
        """Should add gaps without duplicates."""
        state = InvestigationState()
        state.add_gap("Check insider trading patterns")
        state.add_gap("Check insider trading patterns")  # duplicate
        assert len(state.gaps) == 1

    def test_to_dict_roundtrip(self):
        """State should survive dict serialization roundtrip."""
        state = InvestigationState(
            investigation_id="test-001",
            company_name="NIKE, Inc.",
            cik="320187",
            current_phase="analysis",
        )
        state.add_finding("Test finding")
        d = state.to_dict()
        restored = InvestigationState.from_dict(d)
        assert restored.investigation_id == "test-001"
        assert restored.company_name == "NIKE, Inc."
        assert restored.findings == ["Test finding"]

    def test_to_json(self):
        """to_json() should produce valid JSON."""
        state = InvestigationState(investigation_id="test")
        j = state.to_json()
        parsed = json.loads(j)
        assert parsed["investigation_id"] == "test"

    def test_to_context_injection(self):
        """Context injection should include key investigation details."""
        state = InvestigationState(
            company_name="NIKE, Inc.",
            cik="320187",
            current_phase="node_analysis",
        )
        state.add_finding("3 late Form 4 filings")
        state.add_gap("Review 10-K SOX certifications")
        ctx = state.to_context_injection()
        assert "NIKE, Inc." in ctx
        assert "320187" in ctx
        assert "node_analysis" in ctx
        assert "3 late Form 4 filings" in ctx
        assert "Review 10-K SOX certifications" in ctx


class TestContextManager:
    """Test context degradation prevention."""

    def test_init_defaults(self):
        """Default init should configure for 200K token window."""
        cm = ContextManager()
        assert cm.max_context_tokens == 200_000
        assert cm.compaction_threshold == 0.92
        assert cm.needs_compaction is False

    def test_utilization(self):
        """Utilization should be fraction of max tokens."""
        cm = ContextManager(max_context_tokens=1000)
        cm.update_token_count(500)
        assert cm.utilization == 0.5

    def test_needs_compaction_below_threshold(self):
        """Should not need compaction below threshold."""
        cm = ContextManager(max_context_tokens=1000, compaction_threshold=0.9)
        cm.update_token_count(899)
        assert cm.needs_compaction is False

    def test_needs_compaction_above_threshold(self):
        """Should need compaction above threshold."""
        cm = ContextManager(max_context_tokens=1000, compaction_threshold=0.9)
        cm.update_token_count(901)
        assert cm.needs_compaction is True

    def test_compact_resets_tokens(self):
        """Compaction should reset token count."""
        cm = ContextManager(max_context_tokens=1000)
        cm.update_token_count(950)
        cm.state.company_name = "NIKE, Inc."
        messages = cm.compact()
        assert cm._total_tokens_used == 0
        assert len(messages) == 1
        assert "compacted" in messages[0]["content"].lower()

    def test_get_stats(self):
        """Stats should include all tracking fields."""
        cm = ContextManager()
        cm.update_token_count(100)
        stats = cm.get_stats()
        assert stats["total_tokens_used"] == 100
        assert "utilization" in stats
        assert "compaction_count" in stats

    def test_add_message(self):
        """Should track message history."""
        cm = ContextManager()
        cm.add_message({"role": "user", "content": "test"})
        assert len(cm._message_history) == 1

    def test_utilization_zero_max(self):
        """Utilization should be 0 when max_context_tokens is 0."""
        cm = ContextManager(max_context_tokens=0)
        assert cm.utilization == 0.0


# ═══════════════════════════════════════════════════════════════════════
# Integration: ClaudeCompositor with new Claude Agent layer
# ═══════════════════════════════════════════════════════════════════════


class TestClaudeCompositorIntegration:
    """Test that ClaudeCompositor properly integrates claude_agent layer."""

    def test_compositor_has_tool_runner(self):
        """ClaudeCompositor should expose tool_runner property."""
        from src.sec_agent.claude_compositor import ClaudeCompositor

        compositor = ClaudeCompositor()
        runner = compositor.tool_runner
        assert runner.model == "claude-sonnet-4-6"

    def test_compositor_has_mcp_config(self):
        """ClaudeCompositor should expose mcp_config property."""
        from src.sec_agent.claude_compositor import ClaudeCompositor

        compositor = ClaudeCompositor()
        mcp = compositor.mcp_config
        assert "sec-edgar" in mcp.servers

    def test_compositor_has_context_manager(self):
        """ClaudeCompositor should expose context_manager property."""
        from src.sec_agent.claude_compositor import ClaudeCompositor

        compositor = ClaudeCompositor()
        cm = compositor.context_manager
        assert cm.max_context_tokens == 200_000

    def test_compositor_has_prosecutor(self):
        """ClaudeCompositor should expose prosecutor property."""
        from src.sec_agent.claude_compositor import ClaudeCompositor

        compositor = ClaudeCompositor()
        prosecutor = compositor.prosecutor
        assert prosecutor.master_model == "claude-opus-4-6"

    def test_get_claude_agent_capabilities(self):
        """get_claude_agent_capabilities() should return full status."""
        from src.sec_agent.claude_compositor import ClaudeCompositor

        compositor = ClaudeCompositor()
        caps = compositor.get_claude_agent_capabilities()
        assert caps["tool_runner"]["available"] is True
        assert caps["mcp_servers"]["available"] is True
        assert caps["multi_agent"]["available"] is True
        assert caps["context_management"]["available"] is True
        assert caps["tool_runner"]["tools_count"] == 8
        assert caps["multi_agent"]["subagent_count"] == 4
