"""
High-sophistication runtime profile for JLAW forensic system.

This module centralizes environment-level defaults that push the system to use
the most capable models and configurations available by default, while still
allowing callers to override via environment variables or explicit parameters.

It intentionally does NOT modify the Agents SDK defaults (to avoid breaking
generic unit tests). Instead, it sets process env vars and config defaults used
by the forensic runtime (CLI/orchestrators).
"""
from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)


def _set_env_default(key: str, value: str, force: bool = False) -> None:
    if force or os.getenv(key) in (None, ""):
        os.environ[key] = value


def apply_high_sophistication_defaults(force: bool = False) -> None:
    """Apply high-sophistication defaults for models and runtime.

    Effects (unless already set or force=True):
    - OPENAI_DEFAULT_MODEL=gpt-5 (Agents SDK default model resolution)
    - OPENAI_MODEL=gpt-5 (forensic OpenAIConfig default)
    - OPENAI_MAX_TOKENS=8192
    - ENABLE_MULTIPASS_ANALYSIS=true
    - MAX_ANALYSIS_PASSES=6
    - AI_PROVIDER=AUTO

    This is safe in CPU-only environments; heavy reasoning models will run with
    smaller batch sizes internally when applicable.
    """
    _set_env_default("OPENAI_DEFAULT_MODEL", "gpt-5", force)
    _set_env_default("OPENAI_MODEL", "gpt-5", force)
    _set_env_default("OPENAI_MAX_TOKENS", "8192", force)
    _set_env_default("ENABLE_MULTIPASS_ANALYSIS", "true", force)
    _set_env_default("MAX_ANALYSIS_PASSES", "6", force)
    _set_env_default("AI_PROVIDER", "AUTO", force)
    # Marker flag for diagnostics
    _set_env_default("JLAW_HIGH_SOPH_DEFAULTS", "true", force)
    logger.info("High-sophistication defaults applied (model=gpt-5, multipass=on)")
