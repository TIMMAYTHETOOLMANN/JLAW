"""
Claude Agent Tool Runner — Agentic Loop with Forensic Tool Execution
=====================================================================

Implements the core agentic loop pattern using the raw ``anthropic`` SDK.
The runner executes a while-loop that continues as long as Claude returns
tool_use blocks, dispatching each call to the registered tool executor.

Architecture follows Anthropic's recommended Tool Runner pattern:
  1. Send messages to Claude with tool definitions
  2. If response contains tool_use blocks, execute them
  3. Append tool_result messages and loop
  4. When Claude returns end_turn, the loop terminates

Supports parallel tool calling, strict schema validation, and
prompt caching for 90% cost reduction on repeated system prompts.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.claude_agent.system_prompts import get_forensic_system_prompt
from src.claude_agent.tools import get_forensic_tools

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class ToolResult:
    """Result from executing a single forensic tool."""

    tool_use_id: str
    tool_name: str
    result: Any
    is_error: bool = False
    execution_time: float = 0.0

    def to_message_block(self) -> dict[str, Any]:
        """Convert to Claude tool_result message block.

        Returns:
            Dict formatted as a tool_result content block.
        """
        block: dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "content": json.dumps(self.result) if not isinstance(self.result, str) else self.result,
        }
        if self.is_error:
            block["is_error"] = True
        return block


@dataclass
class RunnerResult:
    """Result from a complete Tool Runner execution."""

    response_text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    loop_iterations: int = 0
    total_time: float = 0.0
    model: str = ""
    stop_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dict representation of the runner result.
        """
        return {
            "response_text": self.response_text,
            "tool_calls_count": len(self.tool_calls),
            "tool_results_count": len(self.tool_results),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "loop_iterations": self.loop_iterations,
            "total_time": round(self.total_time, 3),
            "model": self.model,
            "stop_reason": self.stop_reason,
        }


# ═══════════════════════════════════════════════════════════════════════
# Tool Executor Registry
# ═══════════════════════════════════════════════════════════════════════


class ToolExecutor:
    """Registry for forensic tool implementations.

    Maps tool names to callable handlers. Each handler receives the tool
    input dict and returns a result (dict, str, or any JSON-serializable value).
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register(self, tool_name: str, handler: Callable[..., Any]) -> None:
        """Register a handler for a tool name.

        Args:
            tool_name: Name matching a tool definition in tools.py.
            handler: Callable that accepts tool input dict and returns result.
        """
        self._handlers[tool_name] = handler

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> Any:
        """Execute a registered tool handler.

        Args:
            tool_name: Name of the tool to execute.
            tool_input: Input parameters from Claude's tool_use block.

        Returns:
            Tool execution result.

        Raises:
            KeyError: If no handler is registered for the tool name.
        """
        if tool_name not in self._handlers:
            raise KeyError(
                f"No handler registered for tool '{tool_name}'. "
                f"Available: {list(self._handlers.keys())}"
            )
        return self._handlers[tool_name](tool_input)

    @property
    def registered_tools(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._handlers.keys())


# ═══════════════════════════════════════════════════════════════════════
# Forensic Tool Runner
# ═══════════════════════════════════════════════════════════════════════


class ForensicToolRunner:
    """Agentic loop runner for Claude forensic analysis.

    Implements the Tool Runner pattern: send query with tools, execute
    returned tool calls, loop until Claude produces a final text response.

    Args:
        model: Claude model identifier.
        max_tokens: Maximum output tokens per API call.
        max_iterations: Safety limit on agentic loop iterations.
        tool_executor: Optional pre-configured ToolExecutor instance.
        system_prompt: Optional override for the forensic system prompt.
        enable_prompt_caching: Whether to use Anthropic prompt caching.
    """

    # Model tier constants matching problem statement recommendations
    MODEL_OPUS = "claude-opus-4-6"
    MODEL_SONNET = "claude-sonnet-4-6"
    MODEL_HAIKU = "claude-haiku-4-5"

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
        max_iterations: int = 25,
        tool_executor: Optional[ToolExecutor] = None,
        system_prompt: Optional[str] = None,
        enable_prompt_caching: bool = True,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations
        self.tool_executor = tool_executor or ToolExecutor()
        self.system_prompt = system_prompt or get_forensic_system_prompt()
        self.enable_prompt_caching = enable_prompt_caching
        self._tools = get_forensic_tools()
        self._client = None

    def _get_client(self) -> Any:
        """Lazily initialize the Anthropic client.

        Returns:
            An anthropic.AsyncAnthropic client instance.

        Raises:
            ImportError: If the anthropic package is not installed.
        """
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.AsyncAnthropic()
            except ImportError as exc:
                raise ImportError(
                    "The 'anthropic' package (>=0.86.0) is required. "
                    "Install with: pip install 'anthropic>=0.86.0'"
                ) from exc
        return self._client

    def _build_system_param(self) -> Any:
        """Build the system parameter with optional prompt caching.

        When prompt caching is enabled, the system prompt is wrapped in a
        content block with cache_control to enable Anthropic's prompt
        caching (90% cost reduction on cache hits).

        Returns:
            System prompt string or list of content blocks with cache_control.
        """
        if self.enable_prompt_caching:
            return [
                {
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        return self.system_prompt

    def _execute_tool_call(
        self, tool_name: str, tool_input: dict[str, Any], tool_use_id: str
    ) -> ToolResult:
        """Execute a single tool call and return the result.

        Args:
            tool_name: Name of the tool being called.
            tool_input: Input parameters from Claude.
            tool_use_id: Unique identifier for this tool use.

        Returns:
            ToolResult with execution outcome.
        """
        start = time.monotonic()
        try:
            result = self.tool_executor.execute(tool_name, tool_input)
            elapsed = time.monotonic() - start
            logger.debug(
                "Tool '%s' executed in %.3fs", tool_name, elapsed
            )
            return ToolResult(
                tool_use_id=tool_use_id,
                tool_name=tool_name,
                result=result,
                is_error=False,
                execution_time=elapsed,
            )
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error("Tool '%s' failed: %s", tool_name, e)
            return ToolResult(
                tool_use_id=tool_use_id,
                tool_name=tool_name,
                result=f"Error executing tool '{tool_name}': {e}",
                is_error=True,
                execution_time=elapsed,
            )

    async def run(
        self,
        query: str,
        messages: Optional[list[dict[str, Any]]] = None,
    ) -> RunnerResult:
        """Execute the agentic loop for a forensic query.

        Sends the query to Claude with forensic tools attached. If Claude
        responds with tool_use blocks, executes them and loops. Continues
        until Claude returns end_turn or max_iterations is reached.

        Args:
            query: The forensic analysis query or instruction.
            messages: Optional pre-existing message history to continue.

        Returns:
            RunnerResult with final response and execution metadata.
        """
        client = self._get_client()
        start_time = time.monotonic()

        if messages is None:
            messages = [{"role": "user", "content": query}]

        result = RunnerResult(model=self.model)
        system_param = self._build_system_param()

        for iteration in range(self.max_iterations):
            result.loop_iterations = iteration + 1

            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_param,
                tools=self._tools,
                messages=messages,
            )

            # Accumulate token usage
            if hasattr(response, "usage"):
                result.total_input_tokens += getattr(
                    response.usage, "input_tokens", 0
                )
                result.total_output_tokens += getattr(
                    response.usage, "output_tokens", 0
                )
                result.cache_read_tokens += getattr(
                    response.usage, "cache_read_input_tokens", 0
                )
                result.cache_creation_tokens += getattr(
                    response.usage, "cache_creation_input_tokens", 0
                )

            # Append assistant response to message history
            messages.append(
                {"role": "assistant", "content": response.content}
            )

            result.stop_reason = response.stop_reason

            # Check if Claude is done (no more tool calls)
            if response.stop_reason == "end_turn":
                # Extract final text response
                for block in response.content:
                    if hasattr(block, "text"):
                        result.response_text += block.text
                break

            # Process tool_use blocks
            tool_results_for_message = []
            for block in response.content:
                if hasattr(block, "text"):
                    result.response_text += block.text

                if getattr(block, "type", None) == "tool_use":
                    tool_call_info = {
                        "name": block.name,
                        "input": block.input,
                        "id": block.id,
                    }
                    result.tool_calls.append(tool_call_info)

                    tool_result = self._execute_tool_call(
                        block.name, block.input, block.id
                    )
                    result.tool_results.append(tool_result)
                    tool_results_for_message.append(
                        tool_result.to_message_block()
                    )

            if tool_results_for_message:
                messages.append(
                    {"role": "user", "content": tool_results_for_message}
                )
            else:
                # No tool calls and not end_turn — safety break
                logger.warning(
                    "Tool Runner safety break: stop_reason='%s' with no tool calls",
                    response.stop_reason,
                )
                break

        result.total_time = time.monotonic() - start_time
        logger.info(
            "Tool Runner completed: %d iterations, %d tool calls, %.1fs",
            result.loop_iterations,
            len(result.tool_calls),
            result.total_time,
        )
        return result
