"""
JARVIS:LAW Alpha - Deployment Verification Script

This script verifies that all components are properly deployed and functional.
Run this before using the agent to ensure everything is working correctly.
"""

import os
import sys
from pathlib import Path


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_files():
    """Verify all required files exist."""
    print_header("FILE VERIFICATION")
    
    required_files = [
        "jarvis_law_alpha.py",
        "examples.py",
        "DEPLOYMENT.md",
        "SUMMARY.md",
    ]
    
    optional_files = [
        "config.py",
        "interactive_cli.py",
        "test_jarvis.py",
        "requirements.txt",
        "README.md",
        "quickstart.bat",
        "__init__.py",
    ]
    
    all_good = True
    
    print("\n📦 Required Files:")
    for filename in required_files:
        exists = Path(filename).exists()
        size = Path(filename).stat().st_size if exists else 0
        status = "✅" if exists and size > 0 else "❌"
        print(f"  {status} {filename:30} ({size:,} bytes)")
        if not exists or size == 0:
            all_good = False
    
    print("\n📦 Optional Files:")
    for filename in optional_files:
        exists = Path(filename).exists()
        size = Path(filename).stat().st_size if exists else 0
        status = "✅" if exists else "⚠️"
        print(f"  {status} {filename:30} ({size:,} bytes)")
    
    return all_good


def check_imports():
    """Verify required packages can be imported."""
    print_header("PACKAGE VERIFICATION")
    
    packages = [
        ("agents", "OpenAI Agents SDK"),
        ("httpx", "HTTP Client"),
    ]
    
    optional_packages = [
        ("litellm", "LiteLLM (for Claude support)"),
    ]
    
    all_good = True
    
    print("\n📚 Required Packages:")
    for package, name in packages:
        try:
            __import__(package)
            print(f"  ✅ {name:30} - Installed")
        except ImportError:
            print(f"  ❌ {name:30} - MISSING")
            all_good = False
    
    print("\n📚 Optional Packages:")
    for package, name in optional_packages:
        try:
            __import__(package)
            print(f"  ✅ {name:30} - Installed")
        except ImportError:
            print(f"  ⚠️  {name:30} - Not installed (recommended)")
    
    return all_good


def check_env_vars():
    """Check if required environment variables are set."""
    print_header("ENVIRONMENT VARIABLES")
    
    required_vars = [
        ("ANTHROPIC_API_KEY", "Required for Claude Sonnet 4.5"),
        ("OPENAI_API_KEY", "Required for GPT-4o summarizer"),
    ]
    
    all_good = True
    
    print("\n🔑 API Keys:")
    for var, description in required_vars:
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"  ✅ {var:20} - Set ({masked})")
        else:
            print(f"  ❌ {var:20} - NOT SET")
            print(f"     {description}")
            all_good = False
    
    return all_good


def check_agent_structure():
    """Verify the main agent file structure."""
    print_header("AGENT STRUCTURE")
    
    try:
        print("\n🤖 Checking jarvis_law_alpha.py...")
        
        with open("jarvis_law_alpha.py", "r") as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ("jarvis_law_alpha agent", "jarvis_law_alpha = Agent"),
            ("summarizer_agent", "summarizer_agent = Agent"),
            ("fetch_sec_filing tool", "@function_tool\nasync def fetch_sec_filing"),
            ("parse_transaction_tables tool", "@function_tool\ndef parse_transaction_tables"),
            ("classify_transaction_legality tool", "@function_tool\ndef classify_transaction_legality"),
            ("generate_exhibit_report tool", "@function_tool\ndef generate_exhibit_report"),
            ("summarize_violation_chain tool", "@function_tool\ndef summarize_violation_chain"),
            ("Guardrails", "@tool_input_guardrail"),
            ("Main function", "async def main()"),
        ]
        
        all_found = True
        for name, pattern in checks:
            if pattern in content:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} - NOT FOUND")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"  ❌ Error reading jarvis_law_alpha.py: {e}")
        return False


def check_memory_directory():
    """Verify memory directory structure."""
    print_header("MEMORY SYSTEM")
    
    print("\n💾 Checking memory directory...")
    
    memory_dir = Path("./memory/sec_filings")
    if memory_dir.exists():
        print(f"  ✅ Memory directory exists: {memory_dir}")
    else:
        print(f"  ⚠️  Memory directory will be created on first run")
        try:
            memory_dir.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created memory directory: {memory_dir}")
        except Exception as e:
            print(f"  ❌ Failed to create memory directory: {e}")
            return False
    
    return True


def print_summary(checks):
    """Print final summary."""
    print_header("DEPLOYMENT STATUS")
    
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\n📊 Test Results: {passed}/{total} checks passed\n")
    
    for check_name, result in checks.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {check_name:30} - {status}")
    
    print("\n" + "=" * 70)
    
    if passed == total:
        print("✅ DEPLOYMENT VERIFIED - All systems operational!")
        print("\n🚀 Ready to launch:")
        print("   python jarvis_law_alpha.py")
        return True
    else:
        print(f"⚠️  DEPLOYMENT INCOMPLETE - {total - passed} check(s) failed")
        print("\n📝 Review the errors above and:")
        print("   1. Install missing packages: pip install -r requirements.txt")
        print("   2. Set environment variables (API keys)")
        print("   3. Verify all files are present")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("  JARVIS:LAW Alpha - Deployment Verification")
    print("=" * 70)
    print("\nVerifying deployment components...\n")
    
    checks = {
        "Files": check_files(),
        "Packages": check_imports(),
        "Environment": check_env_vars(),
        "Agent Structure": check_agent_structure(),
        "Memory System": check_memory_directory(),
    }
    
    success = print_summary(checks)
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

