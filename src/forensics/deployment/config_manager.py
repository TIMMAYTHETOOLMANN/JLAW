"""Deployment-facing configuration manager wrapper.

Provides a thin wrapper class `ConfigManager` that delegates to the core
`src.forensics.config_manager.ConfigurationManager` to keep deployment
code decoupled from internal config layout.
"""

from __future__ import annotations

from typing import Any

from src.forensics.config_manager import ConfigurationManager as _CoreConfigManager


class ConfigManager:
    """Thin wrapper around the core ConfigurationManager."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._core = _CoreConfigManager(*args, **kwargs)
        self.config = self._core.config

    def reload(self) -> None:
        self._core.reload()
        self.config = self._core.config
