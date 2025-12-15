"""
JLAW SEC Forensic Analyzer - Secure Configuration Loader
=========================================================

This module provides secure API key management with automatic loading from:
1. Environment variables (highest priority)
2. .env file in project root

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

def get_project_root() -> Path:
    """Find project root by looking for .env or .git"""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / '.env').exists() or (current / '.git').exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent


def load_dotenv_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    if env_path is None:
        env_path = get_project_root() / '.env'
    
    loaded_vars = {}
    
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}")
        return loaded_vars
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
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
    value = os.environ.get(key_name)
    if value is None:
        load_dotenv_file()
        value = os.environ.get(key_name)
    
    if value and ('YOUR_' in value or 'YOUR-' in value or value.endswith('_HERE')):
        value = None
    
    if required and not value:
        logger.warning(f"Required API key {key_name} is not set")
    
    return value


def load_all_keys() -> Dict[str, bool]:
    load_dotenv_file()
    
    key_configs = {
        'OPENAI_API_KEY': {'required': False, 'prefix': 'sk-'},
        'ANTHROPIC_API_KEY': {'required': False, 'prefix': 'sk-ant-'},
        'OPENROUTER_API_KEY': {'required': False, 'prefix': 'sk-or-'},
        'GOVINFO_API_KEY': {'required': False, 'prefix': None},
        'SEC_USER_AGENT': {'required': True, 'prefix': None},
        'POLYGON_API_KEY': {'required': False, 'prefix': None},
        'SEC_EDGAR_USER_AGENT': {'required': False, 'prefix': None},
    }
    
    results = {}
    for key_name, config in key_configs.items():
        value = os.environ.get(key_name)
        if value and ('YOUR_' in value or 'YOUR-' in value or value.endswith('_HERE')):
            results[key_name] = False
            continue
        results[key_name] = bool(value)
        
    return results


def validate_configuration() -> bool:
    load_dotenv_file()
    ai_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'OPENROUTER_API_KEY']
    for key in ai_keys:
        value = get_api_key(key)
        if value:
            return True
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
        ('POLYGON_API_KEY', 'Polygon.io Market Data'),
        ('SEC_EDGAR_USER_AGENT', 'SEC EDGAR User Agent'),
    ]
    
    for key_name, display_name in keys_to_check:
        value = os.environ.get(key_name, '')
        if not value:
            status = "❌ NOT SET"
        elif 'YOUR_' in value or 'YOUR-' in value or value.endswith('_HERE'):
            status = "⚠️  PLACEHOLDER"
        else:
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '****'
            status = f"✅ SET ({masked})"
        print(f"  {display_name:20s} : {status}")
    
    print("\n" + "="*60)


# Auto-load on import
if __name__ != '__main__':
    try:
        load_dotenv_file()
    except Exception:
        pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print_configuration_status()
    
