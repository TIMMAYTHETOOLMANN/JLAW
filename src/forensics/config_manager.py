"""
Secure Configuration Manager for JLAW Forensic System
Handles API keys, credentials, and system configuration with security best practices.
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class SECConfig:
    """SEC EDGAR configuration (no API key required)."""
    user_email: str
    user_agent: str
    requests_per_second: int = 10
    max_retries: int = 3


@dataclass
class GovInfoConfig:
    """GovInfo API configuration (API key required)."""
    api_key: str


@dataclass
class OpenAIConfig:
    """OpenAI Agent SDK configuration."""
    api_key: Optional[str]
    secondary_api_key: Optional[str] = None  # For dual-OpenAI mode
    model: str = "gpt-5"
    max_tokens: int = 8192


@dataclass
class AnthropicConfig:
    """Anthropic Claude configuration."""
    api_key: Optional[str]
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 8192


@dataclass
class AIProviderConfig:
    """AI provider selection configuration."""
    provider: str = "AUTO"
    enable_multipass: bool = True
    max_passes: int = 6


@dataclass
class SystemConfig:
    """Complete system configuration."""
    sec: SECConfig
    govinfo: GovInfoConfig
    openai: OpenAIConfig
    anthropic: AnthropicConfig
    ai_provider: AIProviderConfig
    storage_provider: str
    storage_path: str
    log_level: str
    max_workers: int
    enable_gpu: bool
    materiality_threshold: float
    similarity_threshold: float
    dossier_output_path: str


class ConfigurationManager:
    """
    Secure configuration manager.
    
    Loads configuration from:
    1. Environment variables (.env file)
    2. Configuration files
    3. Secure key storage
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to .env file
        """
        self.config_path = config_path or self._find_config_file()
        self._load_environment()
        self.config = self._build_configuration()

        logger.info("Configuration loaded successfully")

    def _find_config_file(self) -> str:
        """Find .env configuration file."""
        # Check current directory
        if Path('.env').exists():
            return '.env'

        # Check project root
        project_root = Path(__file__).parent.parent
        env_file = project_root / '.env'
        if env_file.exists():
            return str(env_file)

        # Check config directory
        config_dir = project_root / 'config'
        env_file = config_dir / '.env'
        if env_file.exists():
            return str(env_file)

        logger.warning("No .env file found, using environment variables only")
        return ''

    def _load_environment(self):
        """Load environment variables from .env file."""
        if self.config_path and Path(self.config_path).exists():
            load_dotenv(self.config_path)
            logger.info(f"Loaded configuration from {self.config_path}")
        else:
            logger.info("Using system environment variables")

    def _build_configuration(self) -> SystemConfig:
        """Build complete system configuration."""

        # SEC EDGAR Configuration (no API key required - only User-Agent)
        sec_email = self._get_env('SEC_EMAIL', 'research@forensicanalysis.edu')
        sec = SECConfig(
            user_email=sec_email,
            user_agent=self._get_env(
                'SEC_USER_AGENT',
                f"Academic-Research-Tool/1.0 (Forensic Analysis Platform)"
            ),
            requests_per_second=int(self._get_env('SEC_REQUESTS_PER_SECOND', '10')),
            max_retries=int(self._get_env('SEC_MAX_RETRIES', '3'))
        )

        # GovInfo API Configuration (API key required - optional for SEC-only use)
        govinfo = GovInfoConfig(
            api_key=self._get_env('GOVINFO_API_KEY', '')
        )

        # OpenAI Agent SDK Configuration (for intelligent web scraping)
        openai_api_key = self._get_env('OPENAI_API_KEY', '')
        openai_secondary_key = self._get_env('OPENAI_SECONDARY_API_KEY', '')
        
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not set - OpenAI Agent features disabled")
        else:
            logger.info("OpenAI Agent SDK enabled - intelligent document extraction available")
        
        if openai_secondary_key:
            logger.info("Secondary OpenAI API key detected - Dual-OpenAI mode available")

        openai = OpenAIConfig(
            api_key=openai_api_key,
            secondary_api_key=openai_secondary_key,
            model=self._get_env('OPENAI_MODEL', 'gpt-5'),
            max_tokens=int(self._get_env('OPENAI_MAX_TOKENS', '8192'))
        )

        # Propagate highest-sophistication default to Agents SDK if not explicitly set
        try:
            if not os.getenv('OPENAI_DEFAULT_MODEL'):
                os.environ['OPENAI_DEFAULT_MODEL'] = openai.model
                logger.info("OPENAI_DEFAULT_MODEL set to %s", openai.model)
        except Exception:
            # Non-fatal if environment mutation is restricted
            pass

        # Anthropic Claude Configuration (for multi-pass deep analysis)
        # Prioritize direct ANTHROPIC_API_KEY, then fall back to OpenRouter
        anthropic_api_key = self._get_env('ANTHROPIC_API_KEY', '')
        openrouter_api_key = self._get_env('OPENROUTER_API_KEY', '')
        
        if anthropic_api_key:
            # Use direct Anthropic API (preferred)
            logger.info("Anthropic Claude enabled - multi-pass deep analysis available ($15 credits)")
        elif openrouter_api_key:
            # Use OpenRouter key as fallback
            anthropic_api_key = openrouter_api_key
            logger.info("OpenRouter API key detected as Anthropic fallback")
        else:
            logger.info("ANTHROPIC_API_KEY not set - Anthropic features disabled")

        anthropic = AnthropicConfig(
            api_key=anthropic_api_key,
            model=self._get_env('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
            max_tokens=int(self._get_env('ANTHROPIC_MAX_TOKENS', '8192'))
        )

        # AI Provider Selection Configuration
        ai_provider = AIProviderConfig(
            provider=self._get_env('AI_PROVIDER', 'AUTO').upper(),
            enable_multipass=self._get_env('ENABLE_MULTIPASS_ANALYSIS', 'true').lower() == 'true',
            max_passes=int(self._get_env('MAX_ANALYSIS_PASSES', '6'))
        )

        # Validate AI provider selection
        valid_providers = {'AUTO', 'OPENAI', 'ANTHROPIC', 'NONE'}
        if ai_provider.provider not in valid_providers:
            logger.warning(f"Invalid AI_PROVIDER '{ai_provider.provider}', defaulting to AUTO")
            ai_provider.provider = 'AUTO'

        # Log selected provider
        if ai_provider.provider == 'AUTO':
            if anthropic_api_key and openai_api_key:
                logger.info("AI Provider: AUTO (Both OpenAI and Anthropic available)")
            elif openai_api_key:
                logger.info("AI Provider: AUTO (OpenAI only)")
            elif anthropic_api_key:
                logger.info("AI Provider: AUTO (Anthropic only)")
            else:
                logger.info("AI Provider: AUTO (No AI providers available, using manual)")
        else:
            logger.info(f"AI Provider: {ai_provider.provider} (Explicit override)")

        # System Configuration
        config = SystemConfig(
            sec=sec,
            govinfo=govinfo,
            openai=openai,
            anthropic=anthropic,
            ai_provider=ai_provider,
            storage_provider=self._get_env('STORAGE_PROVIDER', 'LOCAL'),
            storage_path=self._get_env('STORAGE_PATH', './forensic_storage'),
            log_level=self._get_env('LOG_LEVEL', 'INFO'),
            max_workers=int(self._get_env('MAX_WORKERS', '16')),
            enable_gpu=self._get_env('ENABLE_GPU', 'true').lower() == 'true',
            materiality_threshold=float(self._get_env('MATERIALITY_THRESHOLD', '0.05')),
            similarity_threshold=float(self._get_env('SIMILARITY_THRESHOLD', '0.85')),
            dossier_output_path=self._get_env('DOSSIER_OUTPUT_PATH', './dossiers')
        )

        # Validate configuration
        self._validate_configuration(config)

        return config

    def _get_env(self, key: str, default: str = '') -> str:
        """Get environment variable with default."""
        return os.getenv(key, default)

    def _get_required_env(self, key: str) -> str:
        """Get required environment variable, raise if missing."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not set")
        return value

    def _validate_configuration(self, config: SystemConfig):
        """Validate configuration values."""
        # Validate SEC email format (required for User-Agent)
        if '@' not in config.sec.user_email:
            raise ValueError("Invalid email format in SEC_EMAIL")

        # Validate GovInfo API key if provided
        if config.govinfo.api_key and len(config.govinfo.api_key) < 20:
            logger.warning("GovInfo API key appears to be invalid (too short)")

        # Validate thresholds
        if not 0 < config.materiality_threshold <= 1:
            raise ValueError("Materiality threshold must be between 0 and 1")

        if not 0 < config.similarity_threshold <= 1:
            raise ValueError("Similarity threshold must be between 0 and 1")

        # Create output directories
        Path(config.storage_path).mkdir(parents=True, exist_ok=True)
        Path(config.dossier_output_path).mkdir(parents=True, exist_ok=True)

        logger.info("Configuration validation passed")

    def get_sec_headers(self) -> Dict[str, str]:
        """
        Get SEC EDGAR request headers.
        
        Per SEC requirements:
        - User-Agent must include contact email (no API key needed)
        - Respectful rate limiting (max 10 requests/second)
        
        Reference: https://www.sec.gov/os/accessing-edgar-data
        """
        return {
            'User-Agent': self.config.sec.user_agent,
            'Accept': 'application/json',
            'Host': 'data.sec.gov'
        }

    def get_govinfo_params(self) -> Dict[str, str]:
        """
        Get GovInfo API parameters.
        
        GovInfo (data.gov) requires an API key for enhanced access.
        Reference: https://api.data.gov/docs/
        """
        if not self.config.govinfo.api_key:
            logger.warning("GovInfo API key not configured - using DEMO_KEY (limited access)")
            return {'api_key': 'DEMO_KEY'}

        return {
            'api_key': self.config.govinfo.api_key
        }

    def export_config(self, output_path: str, include_secrets: bool = False):
        """
        Export configuration to file.
        
        Args:
            output_path: Path to output file
            include_secrets: Whether to include API keys (NOT RECOMMENDED)
        """
        config_dict = {
            'sec': {
                'user_email': self.config.sec.user_email,
                'user_agent': self.config.sec.user_agent,
                'requests_per_second': self.config.sec.requests_per_second,
                'max_retries': self.config.sec.max_retries,
                'note': 'SEC EDGAR requires only User-Agent with email (no API key)'
            },
            'govinfo': {
                'api_key': self.config.govinfo.api_key if include_secrets else '***REDACTED***',
                'note': 'GovInfo (data.gov) API key - optional for SEC-only use'
            },
            'system': {
                'storage_provider': self.config.storage_provider,
                'storage_path': self.config.storage_path,
                'log_level': self.config.log_level,
                'max_workers': self.config.max_workers,
                'enable_gpu': self.config.enable_gpu,
                'materiality_threshold': self.config.materiality_threshold,
                'similarity_threshold': self.config.similarity_threshold,
                'dossier_output_path': self.config.dossier_output_path
            }
        }

        with open(output_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"Configuration exported to {output_path}")

    def __repr__(self) -> str:
        """String representation (safe - no secrets)."""
        govinfo_status = "Configured" if self.config.govinfo.api_key else "Not configured"
        return (
            f"ConfigurationManager(\n"
            f"  SEC EDGAR: {self.config.sec.user_email} (User-Agent based)\n"
            f"  GovInfo API: {govinfo_status}\n"
            f"  Storage: {self.config.storage_provider} @ {self.config.storage_path}\n"
            f"  Workers: {self.config.max_workers}\n"
            f"  GPU: {self.config.enable_gpu}\n"
            f")"
        )


# Global configuration singleton
_global_config: Optional[ConfigurationManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigurationManager:
    """
    Get global configuration manager instance.
    
    Args:
        config_path: Optional path to .env file
    
    Returns:
        ConfigurationManager instance
    """
    global _global_config
    if _global_config is None or config_path:
        _global_config = ConfigurationManager(config_path)
    return _global_config


def reload_config(config_path: Optional[str] = None):
    """Force reload of configuration."""
    global _global_config
    _global_config = ConfigurationManager(config_path)
    return _global_config


__all__ = [
    'ConfigurationManager',
    'SECConfig',
    'GovInfoConfig',
    'OpenAIConfig',
    'AnthropicConfig',
    'AIProviderConfig',
    'SystemConfig',
    'get_config',
    'reload_config'
]
