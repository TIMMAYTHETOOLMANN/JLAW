"""
Configuration Validator - Validate .env file and configuration settings.

Validates:
- .env file existence and format
- All required environment variables present
- API key format validation (regex patterns)
- File path existence checks
- Permission validation (read/write access)

Usage:
    python -m tests.config_validator
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict


class ConfigValidator:
    """
    Validate JLAW configuration files and settings.
    
    Validates:
    - .env file format
    - Required environment variables
    - API key formats
    - File paths and permissions
    """
    
    # Required environment variables
    REQUIRED_VARS = [
        'SEC_USER_AGENT',
    ]
    
    # Optional but recommended
    RECOMMENDED_VARS = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
    ]
    
    # API key format patterns
    KEY_PATTERNS = {
        'OPENAI_API_KEY': r'^sk-(proj-)?[\w-]{20,}$',
        'ANTHROPIC_API_KEY': r'^sk-ant-[\w-]{20,}$',
        'SEC_USER_AGENT': r'.+@.+\..+',  # Must contain email
    }
    
    def __init__(self):
        """Initialize configuration validator."""
        self.project_root = self._find_project_root()
        self.env_file = self.project_root / '.env'
        self.env_example = self.project_root / '.env.example'
        self.issues = []
        self.warnings = []
    
    def _find_project_root(self) -> Path:
        """Find project root directory."""
        current = Path(__file__).resolve()
        while current != current.parent:
            if (current / '.env.example').exists():
                return current
            current = current.parent
        return Path.cwd()
    
    def check_env_file_exists(self) -> bool:
        """Check if .env file exists."""
        if not self.env_file.exists():
            self.issues.append("❌ .env file not found")
            if self.env_example.exists():
                self.issues.append(f"   Create it by copying: cp .env.example .env")
            return False
        print(f"✅ .env file exists: {self.env_file}")
        return True
    
    def load_env_file(self) -> Dict[str, str]:
        """Load environment variables from .env file."""
        env_vars = {}
        
        if not self.env_file.exists():
            return env_vars
        
        try:
            with open(self.env_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Check format
                    if '=' not in line:
                        self.warnings.append(f"⚠️  Line {line_num}: Invalid format (missing '=')")
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    env_vars[key] = value
            
            print(f"✅ Loaded {len(env_vars)} configuration variables")
            return env_vars
        except Exception as e:
            self.issues.append(f"❌ Failed to parse .env file: {str(e)}")
            return {}
    
    def check_required_vars(self, env_vars: Dict[str, str]) -> bool:
        """Check required environment variables."""
        missing = []
        placeholders = []
        
        for var in self.REQUIRED_VARS:
            # Check in env_vars first, then os.environ
            value = env_vars.get(var) or os.getenv(var, '')
            
            if not value:
                missing.append(var)
            elif 'YOUR_' in value or 'YOUR-' in value or value.endswith('_HERE'):
                placeholders.append(var)
        
        if missing:
            self.issues.append(f"❌ Missing required variables: {', '.join(missing)}")
            return False
        
        if placeholders:
            self.issues.append(f"❌ Variables contain placeholders: {', '.join(placeholders)}")
            self.issues.append("   Update these with your actual API keys")
            return False
        
        print(f"✅ All {len(self.REQUIRED_VARS)} required variables configured")
        return True
    
    def check_recommended_vars(self, env_vars: Dict[str, str]):
        """Check recommended environment variables (warnings only)."""
        missing = []
        
        for var in self.RECOMMENDED_VARS:
            value = env_vars.get(var) or os.getenv(var, '')
            
            if not value or 'YOUR_' in value:
                missing.append(var)
        
        if missing:
            self.warnings.append(f"⚠️  Recommended variables not configured: {', '.join(missing)}")
            self.warnings.append("   Some features will be disabled (AI validation, subagent orchestration)")
    
    def validate_key_formats(self, env_vars: Dict[str, str]) -> bool:
        """Validate API key formats."""
        invalid = []
        
        for var, pattern in self.KEY_PATTERNS.items():
            value = env_vars.get(var) or os.getenv(var, '')
            
            if value and 'YOUR_' not in value and not re.match(pattern, value):
                invalid.append(f"{var} (invalid format)")
        
        if invalid:
            self.issues.append(f"❌ Invalid API key formats: {', '.join(invalid)}")
            return False
        
        print(f"✅ All configured API keys have valid formats")
        return True
    
    def check_file_permissions(self) -> bool:
        """Check file permissions."""
        issues = []
        
        # Check .env is readable
        if self.env_file.exists():
            if not os.access(self.env_file, os.R_OK):
                issues.append(".env file not readable")
        
        # Check output directory is writable (or can be created)
        output_dir = self.project_root / 'output'
        if output_dir.exists():
            if not os.access(output_dir, os.W_OK):
                issues.append("output/ directory not writable")
        else:
            # Check if we can create it
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_dir.rmdir()  # Clean up
            except Exception:
                issues.append("Cannot create output/ directory")
        
        # Check cache directory
        cache_dir = self.project_root / '.jlaw_cache'
        if cache_dir.exists():
            if not os.access(cache_dir, os.W_OK):
                self.warnings.append("⚠️  .jlaw_cache/ directory not writable")
        
        if issues:
            for issue in issues:
                self.issues.append(f"❌ Permission error: {issue}")
            return False
        
        print(f"✅ File permissions validated")
        return True
    
    def validate_all(self) -> bool:
        """
        Run all configuration validations.
        
        Returns:
            True if configuration is valid
        """
        print("\n" + "=" * 80)
        print("CONFIGURATION VALIDATION")
        print("=" * 80 + "\n")
        
        # Check .env exists
        if not self.check_env_file_exists():
            return False
        
        # Load .env file
        env_vars = self.load_env_file()
        
        # Run checks
        checks = [
            self.check_required_vars(env_vars),
            self.validate_key_formats(env_vars),
            self.check_file_permissions(),
        ]
        
        # Check recommended (warnings only)
        self.check_recommended_vars(env_vars)
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.issues:
            print(f"\n❌ Issues ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")
            print("\n❌ Configuration validation FAILED")
            return False
        else:
            print("\n✅ Configuration validation PASSED")
            return True


def main():
    """Main entry point."""
    validator = ConfigValidator()
    is_valid = validator.validate_all()
    
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
