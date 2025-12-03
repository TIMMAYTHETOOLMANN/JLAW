"""Configuration Management for Phase 8 Master Forensic Controller.

Provides system configuration, phase configuration, and output configuration.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PhaseConfig:
    """Configuration for individual phases."""

    enabled: bool = True
    timeout_seconds: int = 300
    retry_count: int = 3


@dataclass
class OutputConfig:
    """Configuration for output handling."""

    output_dir: str = "forensic_storage"
    generate_html: bool = True
    generate_pdf: bool = False
    compress_artifacts: bool = False


@dataclass
class SystemConfiguration:
    """Master system configuration for all forensic phases.

    Attributes:
        phases_enabled: List of phase numbers to enable (1-9).
        output_config: Output configuration settings.
        phase_configs: Per-phase configuration settings.
        debug_mode: Enable debug logging.
        parallel_execution: Enable parallel phase execution.
    """

    phases_enabled: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7])
    output_config: Optional[OutputConfig] = None
    phase_configs: dict = field(default_factory=dict)
    debug_mode: bool = False
    parallel_execution: bool = False

    def __post_init__(self):
        if self.output_config is None:
            self.output_config = OutputConfig()

    def is_phase_enabled(self, phase_number: int) -> bool:
        """Check if a specific phase is enabled."""
        return phase_number in self.phases_enabled

    def get_phase_config(self, phase_number: int) -> PhaseConfig:
        """Get configuration for a specific phase."""
        return self.phase_configs.get(phase_number, PhaseConfig())
