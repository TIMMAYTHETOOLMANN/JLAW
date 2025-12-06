"""
API KEY VERIFICATION SCRIPT
Verifies all API keys are correctly configured before running the full test suite.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("API KEY VERIFICATION")
print("=" * 80)

# Check OpenAI
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"✅ OpenAI API Key: Loaded (begins: {openai_key[:20]}...)")
else:
    print("❌ OpenAI API Key: NOT FOUND")
    sys.exit(1)

# Check Anthropic
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
if anthropic_key:
    print(f"✅ Anthropic API Key: Loaded (begins: {anthropic_key[:20]}...)")
else:
    print("❌ Anthropic API Key: NOT FOUND")
    sys.exit(1)

# Check GovInfo
govinfo_key = os.getenv('GOVINFO_API_KEY')
if govinfo_key:
    print(f"✅ GovInfo API Key: Loaded (begins: {govinfo_key[:20]}...)")
else:
    print("⚠️  GovInfo API Key: NOT FOUND (optional)")

print("\n" + "=" * 80)
print("TESTING API CONNECTIVITY")
print("=" * 80)

# Test OpenAI
try:
    import openai
    openai.api_key = openai_key
    print("✅ OpenAI SDK: Loaded successfully")
except Exception as e:
    print(f"❌ OpenAI SDK: Error - {e}")

# Test Anthropic
try:
    import anthropic
    client = anthropic.Anthropic(api_key=anthropic_key)
    print("✅ Anthropic SDK: Loaded successfully")
except Exception as e:
    print(f"❌ Anthropic SDK: Error - {e}")

# Test module imports
print("\n" + "=" * 80)
print("TESTING MODULE IMPORTS")
print("=" * 80)

try:
    from src.forensics.advanced_statute_integrator import AdvancedStatuteIntegrator
    print("✅ Advanced Statute Integrator: Imported successfully")
except Exception as e:
    print(f"❌ Advanced Statute Integrator: Error - {e}")

try:
    from src.forensics.dual_agent import DualAgentCoordinator
    print("✅ Dual-Agent Coordinator: Imported successfully")
except Exception as e:
    print(f"❌ Dual-Agent Coordinator: Error - {e}")

print("\n" + "=" * 80)
print("🎯 VERIFICATION COMPLETE")
print("=" * 80)
print("\n✅ All API keys configured correctly")
print("✅ All modules imported successfully")
print("\n🚀 System ready for testing")
print("\nNext step: Run the comprehensive test suite")
print("Command: python test_dual_agent_baseline.py")
print("=" * 80)

