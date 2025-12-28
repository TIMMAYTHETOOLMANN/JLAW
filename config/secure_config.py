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


def is_placeholder_value(value: str) -> bool:
    """
    Check if a value is a placeholder.
    
    Args:
        value: Value to check
        
    Returns:
        True if value is a placeholder
    """
    if not value:
        return False
    
    placeholders = [
        'YOUR_', 'YOUR-', 'CHANGE_ME', '_HERE', 
        'your-email', 'your_password', '@example', 
        '@PLACEHOLDER', 'PLACEHOLDER', 'TODO',
        'FIXME', 'REPLACE_ME'
    ]
    
    for placeholder in placeholders:
        if placeholder.lower() in value.lower():
            return True
    
    return False


def validate_openai_key(api_key: Optional[str]) -> Tuple[bool, str]:
    """
    Validate OpenAI API key format and optionally test connectivity.
    
    Args:
        api_key: OpenAI API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        return False, "OpenAI API key is not set"
    
    if is_placeholder_value(api_key):
        return False, (
            "OpenAI API key contains placeholder value. "
            "Get your API key from: https://platform.openai.com/api-keys"
        )
    
    # Check format (should start with sk-proj- or sk-)
    if not (api_key.startswith('sk-proj-') or api_key.startswith('sk-')):
        return False, (
            "OpenAI API key has invalid format. "
            "Keys should start with 'sk-proj-' or 'sk-'"
        )
    
    # Check minimum length
    if len(api_key) < 20:
        return False, "OpenAI API key is too short"
    
    return True, ""


def validate_anthropic_key(api_key: Optional[str]) -> Tuple[bool, str]:
    """
    Validate Anthropic (Claude) API key format.
    
    Args:
        api_key: Anthropic API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        return False, "Anthropic API key is not set"
    
    if is_placeholder_value(api_key):
        return False, (
            "Anthropic API key contains placeholder value. "
            "Get your API key from: https://console.anthropic.com/settings/keys"
        )
    
    # Check format (should start with sk-ant-)
    if not api_key.startswith('sk-ant-'):
        return False, (
            "Anthropic API key has invalid format. "
            "Keys should start with 'sk-ant-'"
        )
    
    # Check minimum length (real keys are much longer, but allow short keys for testing)
    if len(api_key) < 15:
        return False, "Anthropic API key is too short"
    
    return True, ""


def validate_polygon_key(api_key: Optional[str]) -> Tuple[bool, str]:
    """
    Validate Polygon.io API key format.
    
    Args:
        api_key: Polygon.io API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        # Polygon is optional
        return True, "Polygon.io API key not set (optional for Node 15)"
    
    if is_placeholder_value(api_key):
        return False, (
            "Polygon.io API key contains placeholder value. "
            "Get your API key from: https://polygon.io/dashboard/api-keys"
        )
    
    # Check minimum length (Polygon keys are typically 32+ characters)
    if len(api_key) < 20:
        return False, "Polygon.io API key appears invalid (too short)"
    
    return True, ""


def validate_govinfo_key(api_key: Optional[str]) -> Tuple[bool, str]:
    """
    Validate GovInfo API key format.
    
    Args:
        api_key: GovInfo API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not api_key:
        # GovInfo is optional
        return True, "GovInfo API key not set (optional for statutory citations)"
    
    if is_placeholder_value(api_key):
        return False, (
            "GovInfo API key contains placeholder value. "
            "Request your API key from: https://api.govinfo.gov/docs/"
        )
    
    # Check minimum length
    if len(api_key) < 10:
        return False, "GovInfo API key appears invalid (too short)"
    
    return True, ""


def validate_all_api_keys() -> Tuple[bool, Dict[str, Tuple[bool, str]]]:
    """
    Validate all API keys.
    
    Returns:
        Tuple of (all_valid, dict of key_name -> (is_valid, error_message))
    """
    load_dotenv_file()
    
    results = {
        'OPENAI_API_KEY': validate_openai_key(os.environ.get('OPENAI_API_KEY')),
        'ANTHROPIC_API_KEY': validate_anthropic_key(os.environ.get('ANTHROPIC_API_KEY')),
        'POLYGON_API_KEY': validate_polygon_key(os.environ.get('POLYGON_API_KEY')),
        'GOVINFO_API_KEY': validate_govinfo_key(os.environ.get('GOVINFO_API_KEY')),
        'SEC_USER_AGENT': validate_sec_user_agent(
            os.environ.get('SEC_USER_AGENT') or os.environ.get('SEC_EDGAR_USER_AGENT')
        )
    }
    
    # Check if at least one AI key is valid (required for dual-agent validation)
    ai_keys_valid = (
        results['OPENAI_API_KEY'][0] or 
        results['ANTHROPIC_API_KEY'][0]
    )
    
    # SEC user agent is always required
    sec_valid = results['SEC_USER_AGENT'][0]
    
    all_valid = ai_keys_valid and sec_valid
    
    return all_valid, results


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
    
    # Validate all API keys
    all_valid, validation_results = validate_all_api_keys()
    
    print("API KEY VALIDATION:")
    print("-" * 60)
    
    for key_name, (is_valid, error_msg) in validation_results.items():
        value = os.environ.get(key_name, '')
        
        if not value:
            status = "❌ NOT SET"
            detail = ""
        elif not is_valid:
            status = "⚠️  INVALID"
            detail = f" - {error_msg}"
        else:
            # Mask the key for security
            if len(value) > 12:
                masked = value[:8] + '...' + value[-4:]
            else:
                masked = '****'
            status = f"✅ VALID ({masked})"
            detail = ""
        
        display_name = key_name.replace('_', ' ').title()
        print(f"  {display_name:30s} : {status}{detail}")
    
    # Overall validation status
    print("\n" + "-"*60)
    print("OVERALL VALIDATION")
    print("-"*60 + "\n")
    
    if all_valid:
        print("  ✅ Configuration is valid")
        print("  ✅ At least one AI API key is configured")
        print("  ✅ SEC User-Agent is properly configured")
        print("  ✅ Ready for forensic analysis")
    else:
        print("  ❌ Configuration is INVALID")
        
        # Check what's missing
        ai_keys_valid = (
            validation_results['OPENAI_API_KEY'][0] or 
            validation_results['ANTHROPIC_API_KEY'][0]
        )
        
        if not ai_keys_valid:
            print("  ❌ No valid AI API key (OpenAI or Anthropic required)")
        
        if not validation_results['SEC_USER_AGENT'][0]:
            print("  ❌ SEC User-Agent not properly configured")
        
        print("\n  ⚠️  System cannot perform forensic analysis until configuration is fixed")
        print("  ⚠️  See errors above for specific issues")
    
    # Optional services status
    print("\n" + "-"*60)
    print("OPTIONAL SERVICES")
    print("-"*60 + "\n")
    
    polygon_valid = validation_results['POLYGON_API_KEY'][0]
    govinfo_valid = validation_results['GOVINFO_API_KEY'][0]
    
    polygon_status = "✅ CONFIGURED" if polygon_valid and os.environ.get('POLYGON_API_KEY') else "⚠️  NOT CONFIGURED"
    govinfo_status = "✅ CONFIGURED" if govinfo_valid and os.environ.get('GOVINFO_API_KEY') else "⚠️  NOT CONFIGURED"
    
    print(f"  Polygon.io (Node 15 - Market Data)    : {polygon_status}")
    print(f"  GovInfo (Statutory Citations)         : {govinfo_status}")
    
    if not (polygon_valid and os.environ.get('POLYGON_API_KEY')):
        print("     → Node 15 (Market Correlation) will be skipped")
    
    if not (govinfo_valid and os.environ.get('GOVINFO_API_KEY')):
        print("     → Live statutory citation validation unavailable")
    
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
    
