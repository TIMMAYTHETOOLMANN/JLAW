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
import re
from pathlib import Path
from typing import Optional, Dict, Tuple, List

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


def validate_sec_user_agent(user_agent: Optional[str]) -> Tuple[bool, str]:
    """
    Validate SEC User-Agent format and content.
    
    SEC requires User-Agent with company/product name and contact email.
    See: https://www.sec.gov/os/accessing-edgar-data
    
    Args:
        user_agent: User-Agent string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Examples:
        Valid: "CompanyName/1.0 (contact@company.com)"
        Valid: "ProductName admin@example.org"
        Invalid: "YourProject contact@your-email.org"  (placeholder)
        Invalid: "MyApp"  (no email)
    """
    if not user_agent:
        return False, "SEC_USER_AGENT is not set"
    
    # Check for common placeholders
    placeholders = [
        'YOUR_', 'YOUR-', 'YourProject', 'YourCompany',
        'your-email', 'contact@example', '@your-', '@PLACEHOLDER'
    ]
    for placeholder in placeholders:
        if placeholder.lower() in user_agent.lower():
            return False, (
                f"SEC_USER_AGENT contains placeholder value: '{user_agent}'. "
                f"Please update .env with your actual organization name and contact email. "
                f"Format: 'CompanyName/Version (contact@company.com)'"
            )
    
    # Check for email address (comprehensive validation)
    # Supports most valid email formats including +, apostrophes, etc.
    email_pattern = r"[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*"
    if not re.search(email_pattern, user_agent):
        return False, (
            f"SEC_USER_AGENT must include a valid email address: '{user_agent}'. "
            f"SEC requires contact information in User-Agent. "
            f"Format: 'CompanyName/Version (contact@company.com)'"
        )
    
    # Check minimum length (reasonable User-Agent should be at least 15 chars)
    if len(user_agent) < 15:
        return False, (
            f"SEC_USER_AGENT is too short: '{user_agent}'. "
            f"Include both organization name and contact email."
        )
    
    return True, ""


def validate_sec_configuration() -> Tuple[bool, List[str]]:
    """
    Validate SEC API configuration before making any requests.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check SEC_USER_AGENT
    user_agent = os.environ.get('SEC_USER_AGENT') or os.environ.get('SEC_EDGAR_USER_AGENT')
    is_valid, error_msg = validate_sec_user_agent(user_agent)
    
    if not is_valid:
        errors.append(error_msg)
        errors.append(
            "SETUP INSTRUCTIONS:\n"
            "  1. Copy .env.example to .env\n"
            "  2. Edit SEC_USER_AGENT line with your info:\n"
            "     SEC_USER_AGENT=YourCompany/1.0 (your-email@company.com)\n"
            "  3. Restart the application"
        )
    
    return len(errors) == 0, errors


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
    
    # Validate SEC configuration
    print("\n" + "-"*60)
    print("SEC API CONFIGURATION VALIDATION")
    print("-"*60 + "\n")
    
    is_valid, errors = validate_sec_configuration()
    if is_valid:
        print("  ✅ SEC API configuration is valid")
        print("  ✅ User-Agent contains email address")
        print("  ✅ Ready to make SEC EDGAR API requests")
    else:
        print("  ❌ SEC API configuration is INVALID")
        for error in errors:
            for line in error.split('\n'):
                if line.strip():
                    print(f"     {line}")
        print("\n  ⚠️  SEC API requests will FAIL until configuration is fixed")
    
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
    
