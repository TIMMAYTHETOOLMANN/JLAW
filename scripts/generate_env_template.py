"""
Generate .env Template - Create .env file from template.

Usage:
    python scripts/generate_env_template.py
"""

import sys
from pathlib import Path
import shutil


def generate_env_template():
    """Generate .env file from .env.example."""
    project_root = Path(__file__).resolve().parent.parent
    env_example = project_root / '.env.example'
    env_file = project_root / '.env'
    
    print("=" * 80)
    print("JLAW .env File Generator")
    print("=" * 80 + "\n")
    
    # Check if .env.example exists
    if not env_example.exists():
        print(f"❌ .env.example not found at {env_example}")
        return False
    
    # Check if .env already exists
    if env_file.exists():
        print(f"⚠️  .env file already exists at {env_file}")
        response = input("Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return False
    
    # Copy .env.example to .env
    try:
        shutil.copy(env_example, env_file)
        print(f"\n✅ Created .env file at {env_file}")
        print("\n📝 Next steps:")
        print("   1. Edit .env file with your actual API keys")
        print("   2. Update SEC_USER_AGENT with your organization name and email")
        print("   3. Add OpenAI API key (get from https://platform.openai.com/api-keys)")
        print("   4. Add Anthropic API key (get from https://console.anthropic.com/settings/keys)")
        print("\n   Required:")
        print("     SEC_USER_AGENT=YourOrg/1.0 (contact@yourorg.com)")
        print("\n   Optional (recommended):")
        print("     OPENAI_API_KEY=sk-proj-...")
        print("     ANTHROPIC_API_KEY=sk-ant-api03-...")
        print("\n✅ Run validation:")
        print("   python -m tests.config_validator")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {str(e)}")
        return False


def main():
    """Main entry point."""
    success = generate_env_template()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
