"""
JLAW SEC Forensic Analyzer - Configuration Module
==================================================

This module provides secure API key management and configuration loading.

Usage:
    from config import get_api_key, load_all_keys, validate_configuration
    
    # Get a specific key
    openai_key = get_api_key('OPENAI_API_KEY')
    
    # Load all keys into environment
    load_all_keys()
    
    # Validate configuration
    if validate_configuration():
        print("Ready to run!")
"""

from .secure_config import (
    get_api_key,
    get_project_root,
    load_all_keys,
    load_dotenv_file,
    print_configuration_status,
    validate_configuration,
)

__all__ = [
    'get_api_key',
    'get_project_root',
    'load_all_keys',
    'load_dotenv_file',
    'print_configuration_status',
    'validate_configuration',
]

