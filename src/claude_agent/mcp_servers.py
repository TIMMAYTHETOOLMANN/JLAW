"""
MCP Server Configuration for Claude Agent Integration
======================================================

Defines MCP (Model Context Protocol) server configurations for connecting
Claude agents to SEC EDGAR data, anomaly databases, and evidence chain
services. Uses FastMCP 3.0 patterns for forensic tool servers.

MCP is the industry standard for AI-tool integration (donated to Linux
Foundation's Agentic AI Foundation, December 2025). The protocol uses
JSON-RPC 2.0 with three primitives: Tools (AI-controlled functions),
Resources (application-controlled data), and Prompts (user-invoked templates).
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# MCP Server Configuration
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server.

    Attributes:
        name: Human-readable server name.
        command: Executable command to launch the server.
        args: Command-line arguments for the server process.
        env: Optional environment variables for the server.
        enabled: Whether this server is active.
    """

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for Agent SDK consumption.

        Returns:
            Dict with command and args suitable for ClaudeAgentOptions.
        """
        result: dict[str, Any] = {
            "command": self.command,
            "args": self.args,
        }
        if self.env:
            result["env"] = self.env
        return result


@dataclass
class MCPConfiguration:
    """Complete MCP server configuration for the forensic pipeline.

    Manages multiple MCP servers that provide SEC EDGAR access,
    anomaly database queries, and evidence chain verification.

    Attributes:
        servers: Dict mapping server names to their configurations.
    """

    servers: dict[str, MCPServerConfig] = field(default_factory=dict)

    def add_server(self, config: MCPServerConfig) -> None:
        """Register an MCP server configuration.

        Args:
            config: Server configuration to add.
        """
        self.servers[config.name] = config
        logger.debug("Registered MCP server: %s", config.name)

    def remove_server(self, name: str) -> None:
        """Remove an MCP server configuration.

        Args:
            name: Name of the server to remove.
        """
        self.servers.pop(name, None)

    def get_enabled_servers(self) -> dict[str, dict[str, Any]]:
        """Return enabled servers in Agent SDK format.

        Returns:
            Dict mapping server names to their serialized configs,
            filtered to only enabled servers.
        """
        return {
            name: config.to_dict()
            for name, config in self.servers.items()
            if config.enabled
        }

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Retrieve a specific server configuration.

        Args:
            name: Server name to look up.

        Returns:
            MCPServerConfig if found, None otherwise.
        """
        return self.servers.get(name)

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Serialize all servers to dictionary.

        Returns:
            Dict mapping all server names to their serialized configs.
        """
        return {
            name: config.to_dict()
            for name, config in self.servers.items()
        }


# ═══════════════════════════════════════════════════════════════════════
# Default MCP Server Configurations
# ═══════════════════════════════════════════════════════════════════════

# SEC EDGAR MCP server (sec-edgar-mcp package v1.0.8)
SEC_EDGAR_SERVER = MCPServerConfig(
    name="sec-edgar",
    command="python",
    args=["-m", "sec_edgar_mcp.server"],
    env={},
    enabled=True,
)

# Custom anomaly database MCP server
ANOMALY_DB_SERVER = MCPServerConfig(
    name="anomaly-db",
    command="python",
    args=["./mcp_servers/anomaly_server.py"],
    env={},
    enabled=False,  # Disabled until custom server is implemented
)

# Evidence chain MCP server for FRE 902 compliance
EVIDENCE_CHAIN_SERVER = MCPServerConfig(
    name="evidence-chain",
    command="python",
    args=["./mcp_servers/evidence_server.py"],
    env={},
    enabled=False,  # Disabled until custom server is implemented
)


def get_default_mcp_config() -> MCPConfiguration:
    """Create the default MCP configuration for JLAW forensic pipeline.

    Registers all known MCP servers. Only the SEC EDGAR server is enabled
    by default; custom servers require implementation before activation.

    Returns:
        MCPConfiguration with default server registrations.
    """
    config = MCPConfiguration()
    config.add_server(SEC_EDGAR_SERVER)
    config.add_server(ANOMALY_DB_SERVER)
    config.add_server(EVIDENCE_CHAIN_SERVER)
    return config
