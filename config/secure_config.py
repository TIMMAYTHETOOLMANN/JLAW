"""
JLAW SEC Forensic Analyzer - Secure Configuration Loader
=========================================================

This module provides secure API key management with automatic loading from:
1. Environment variables (highest priority)
2. .env file in project root
3. System keyring (optional, for enhanced security)

Usage:
    from config.secure_config import get_api_key, load_all_keys
    
    # Get a specific key
    openai_key = get_api_key('OPENAI_API_KEY')
    
    # Load all keys into environment
    load_all_keys()
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Project root detection
def get_project_root() -> Path:
    """Find project root by looking for .env or .git"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / '.env').exists() or (current / '.git').exists():
            return current
        current = current.parent
    # Fallback to script directory's parent
    return Path(__file__).resolve().parent.parent


def load_dotenv_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from .env file.
    Returns dict of loaded variables.
    """
    if env_path is None:
        env_path = get_project_root() / '.env'
    
    loaded_vars = {}
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}")
        logger.info("Copy .env.example to .env and add your API keys")
        return loaded_vars
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    # Only set if not already in environment (env vars take priority)
                    if key not in os.environ:
                        os.environ[key] = value
                        loaded_vars[key] = value
                    else:
                        loaded_vars[key] = os.environ[key]
                        
        logger.info(f"Loaded {len(loaded_vars)} configuration variables from .env")
        
    except Exception as e:
        logger.error(f"Error loading .env file: {e}")
    
    return loaded_vars


def get_api_key(key_name: str, required: bool = False) -> Optional[str]:
    """
    Get an API key from environment.
    
    Args:
        key_name: Name of the environment variable
        required: If True, raises ValueError if key not found
        
    Returns:
        API key value or None if not found
    """
    # First try environment
    value = os.environ.get(key_name)
    
    # If not in env, try loading from .env
    if value is None:
        load_dotenv_file()
        value = os.environ.get(key_name)
    
    # Check if it's a placeholder
    if value and ('YOUR_' in value or 'YOUR-' in value or value.endswith('_HERE')):
        logger.warning(f"{key_name} appears to be a placeholder. Please set actual value.")
        value = None
    
    if required and not value:
        raise ValueError(
            f"Required API key '{key_name}' not found. "
            f"Please set it in .env file or environment variable."
        )
    
    return value


def load_all_keys() -> Dict[str, bool]:
    """
    Load all API keys from .env and validate them.
    
    Returns:
        Dict mapping key names to whether they were successfully loaded
    """
    # Load .env file
    load_dotenv_file()
    
    # Required keys for the forensic analyzer
    key_configs = {
        'OPENAI_API_KEY': {'required': False, 'prefix': 'sk-'},
        'ANTHROPIC_API_KEY': {'required': False, 'prefix': 'sk-ant-'},
        'OPENROUTER_API_KEY': {'required': False, 'prefix': 'sk-or-'},
        'GOVINFO_API_KEY': {'required': False, 'prefix': None},
        'SEC_USER_AGENT': {'required': True, 'prefix': None},
    }
    
    results = {}
    
    for key_name, config in key_configs.items():
        value = os.environ.get(key_name)
        
        # Check if valid (not placeholder)
        if value and ('YOUR_' in value or 'YOUR-' in value or value.endswith('_HERE')):
            results[key_name] = False
            continue
            
        # Check prefix if specified
        if value and config['prefix']:
            if not value.startswith(config['prefix']):
                logger.warning(f"{key_name} doesn't have expected prefix '{config['prefix']}'")
        
        results[key_name] = bool(value)
        
        if results[key_name]:
            logger.debug(f"✓ {key_name} loaded")
        elif config['required']:
            logger.error(f"✗ {key_name} is required but not set")
        else:
            logger.debug(f"○ {key_name} not set (optional)")
    
    return results


def validate_configuration() -> bool:
    """
    Validate that at least one AI API key is configured.
    
    Returns:
        True if configuration is valid for operation
    """
    load_dotenv_file()
    
    ai_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'OPENROUTER_API_KEY']
    
    for key in ai_keys:
        value = get_api_key(key)
        if value:
            logger.info(f"AI API configured via {key}")
            return True
    
    logger.error("No AI API keys configured. Please set at least one of:")
    for key in ai_keys:
        logger.error(f"  - {key}")
    
    return False


def print_configuration_status():
    """Print a summary of current configuration status."""
    print("\n" + "="*60)
    print("JLAW SEC FORENSIC ANALYZER - CONFIGURATION STATUS")
    print("="*60 + "\n")
    
    load_dotenv_file()
    
    keys_to_check = [
        ('OPENAI_API_KEY', 'OpenAI API'),
        ('OPENAI_SECONDARY_API_KEY', 'OpenAI Secondary'),
        ('ANTHROPIC_API_KEY', 'Anthropic (Claude)'),
        ('OPENROUTER_API_KEY', 'OpenRouter'),
        ('GOVINFO_API_KEY', 'GovInfo'),
        ('SEC_USER_AGENT', 'SEC User Agent'),
    ]
    
    for key_name, display_name in keys_to_check:
        value = os.environ.get(key_name, '')
        
        if not value:
            status = "❌ NOT SET"
        elif 'YOUR_' in value or 'YOUR-' in value or value.endswith('_HERE'):
            status = "⚠️  PLACEHOLDER"
        else:
            # Mask the key for display
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '****'
            status = f"✅ SET ({masked})"
        
        print(f"  {display_name:20s} : {status}")
    
    print("\n" + "="*60)
    print("To configure, edit: .env")
    print("Template available: .env.example")
    print("="*60 + "\n")


# Auto-load on import
if __name__ != '__main__':
    # Silently load .env when module is imported
    try:
        load_dotenv_file()
    except Exception:
        pass

if __name__ == '__main__':
    # When run directly, show status
    logging.basicConfig(level=logging.INFO)
    print_configuration_status()
    
    if validate_configuration():
        print("✅ Configuration is valid - ready to run")
        sys.exit(0)
    else:
        print("❌ Configuration incomplete - please update .env file")
        sys.exit(1)

