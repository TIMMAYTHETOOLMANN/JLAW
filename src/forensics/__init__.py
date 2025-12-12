"""
JLAW Forensic Analysis System - Core Modules
=============================================

Minimal core system for SEC forensic analysis.

Core Components:
- config_manager: Configuration and API key management
- dual_agent: OpenAI + Anthropic dual-agent coordination
- govinfo_api_client: GovInfo API integration for statute lookup
- agent_sec_analyzer: OpenAI-based SEC document analysis
- anthropic_agent_analyzer: Anthropic-based cross-validation
- openai_secondary_agent: Secondary OpenAI agent for fallback
"""

__version__ = "2.0.0"

# Only import what exists
from .config_manager import get_config, SystemConfig
from .dual_agent import DualAgentCoordinator
from .govinfo_api_client import GovInfoAPIClient

__all__ = [
    "get_config",
    "SystemConfig", 
    "DualAgentCoordinator",
    "GovInfoAPIClient",
]

