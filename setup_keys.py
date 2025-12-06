#!/usr/bin/env python3
"""
JLAW SEC Forensic Analyzer - First-Time Setup Script
=====================================================

Run this script after cloning the repository to configure API keys.
It will:
1. Create .env file from template if it doesn't exist
2. Prompt for API keys interactively
3. Validate the configuration

Usage:
    python setup_keys.py
    
Or on Windows:
    python setup_keys.py
"""

import os
import sys
import shutil
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent


def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    root = get_project_root()
    env_file = root / '.env'
    example_file = root / '.env.example'
    
    if env_file.exists():
        print("✓ .env file already exists")
        return True
    
    if example_file.exists():
        shutil.copy(example_file, env_file)
        print("✓ Created .env from .env.example")
        return True
    else:
        print("✗ .env.example not found, creating basic .env")
        with open(env_file, 'w') as f:
            f.write("""# JLAW API Configuration
# Add your API keys below

OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=
GOVINFO_API_KEY=
SEC_USER_AGENT=JLAW Forensics System contact@your-email.org
""")
        return True


def prompt_for_keys():
    """Interactively prompt for API keys."""
    root = get_project_root()
    env_file = root / '.env'
    
    print("\n" + "="*60)
    print("JLAW SEC FORENSIC ANALYZER - API KEY SETUP")
    print("="*60)
    print("\nLeave blank to skip optional keys.\n")
    
    keys_to_configure = [
        {
            'name': 'OPENAI_API_KEY',
            'prompt': 'OpenAI API Key (sk-proj-...)',
            'required': False,
            'url': 'https://platform.openai.com/api-keys'
        },
        {
            'name': 'ANTHROPIC_API_KEY', 
            'prompt': 'Anthropic API Key (sk-ant-api03-...)',
            'required': False,
            'url': 'https://console.anthropic.com/settings/keys'
        },
        {
            'name': 'OPENROUTER_API_KEY',
            'prompt': 'OpenRouter API Key (sk-or-v1-...)',
            'required': False,
            'url': 'https://openrouter.ai/keys'
        },
        {
            'name': 'GOVINFO_API_KEY',
            'prompt': 'GovInfo API Key',
            'required': False,
            'url': 'https://api.govinfo.gov/docs/'
        },
    ]
    
    # Read current .env content
    current_values = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    current_values[key.strip()] = value.strip()
    
    # Prompt for each key
    new_values = {}
    for key_info in keys_to_configure:
        key_name = key_info['name']
        current = current_values.get(key_name, '')
        
        # Check if already has a real value
        if current and not ('YOUR_' in current or current.endswith('_HERE')):
            masked = current[:10] + '...' if len(current) > 10 else current
            print(f"\n{key_info['prompt']}")
            print(f"  Current: {masked}")
            print(f"  Get key: {key_info['url']}")
            change = input("  Change? [y/N]: ").strip().lower()
            if change != 'y':
                new_values[key_name] = current
                continue
        else:
            print(f"\n{key_info['prompt']}")
            print(f"  Get key: {key_info['url']}")
        
        value = input("  Enter key: ").strip()
        if value:
            new_values[key_name] = value
        elif current:
            new_values[key_name] = current
    
    # Update .env file
    lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    
    # Update or add keys
    updated_keys = set()
    new_lines = []
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in new_values:
                new_lines.append(f"{key}={new_values[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Add any new keys not in original file
    for key, value in new_values.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")
    
    with open(env_file, 'w') as f:
        f.writelines(new_lines)
    
    print("\n✓ Configuration saved to .env")


def validate_setup():
    """Validate the configuration."""
    try:
        sys.path.insert(0, str(get_project_root()))
        from config.secure_config import validate_configuration, print_configuration_status
        
        print_configuration_status()
        return validate_configuration()
    except ImportError:
        print("⚠ Could not import secure_config module for validation")
        return True


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         JLAW SEC FORENSIC ANALYZER - SETUP                   ║
║                                                              ║
║  This script will configure your API keys securely.         ║
║  Keys are stored in .env file (excluded from git).          ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Create .env file
    print("\n[Step 1/3] Checking .env file...")
    create_env_file()
    
    # Step 2: Prompt for keys
    print("\n[Step 2/3] Configuring API keys...")
    configure = input("Configure API keys now? [Y/n]: ").strip().lower()
    if configure != 'n':
        prompt_for_keys()
    
    # Step 3: Validate
    print("\n[Step 3/3] Validating configuration...")
    if validate_setup():
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("\nYou can now run the forensic analyzer:")
        print("  python sec_forensic_analyzer.py --help")
        print("\nTo reconfigure keys later, run:")
        print("  python setup_keys.py")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("⚠️  SETUP INCOMPLETE")
        print("="*60)
        print("\nPlease configure at least one AI API key:")
        print("  - Edit .env file directly, or")
        print("  - Run this script again")
        print("="*60)


if __name__ == '__main__':
    main()

