"""
DUAL-OPENAI FINAL VALIDATION
=============================

Comprehensive test of dual-OpenAI configuration with fresh environment loading.
"""

import sys
import os

# Force reload of environment
if 'dotenv' in sys.modules:
    del sys.modules['dotenv']

from dotenv import load_dotenv
load_dotenv(override=True)  # Force override

print("=" * 80)
print("DUAL-OPENAI CONFIGURATION - FINAL VALIDATION")
print("=" * 80)

# Verify keys
primary_key = os.getenv('OPENAI_API_KEY', '')
secondary_key = os.getenv('OPENAI_SECONDARY_API_KEY', '')

print(f"\n✅ Configuration Loaded:")
print(f"   Primary Key: {primary_key[:40]}...")
print(f"   Secondary Key: {secondary_key[:40]}...")

if not primary_key or not secondary_key:
    print("\n❌ ERROR: One or both OpenAI keys not configured!")
    sys.exit(1)

# Test OpenAI connectivity
print("\n" + "-" * 80)
print("Testing OpenAI API Connectivity...")
print("-" * 80)

import openai

# Test primary key
print("\n1. Testing Primary OpenAI Key...")
try:
    client_primary = openai.OpenAI(api_key=primary_key)
    response = client_primary.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Primary key works'"}],
        max_tokens=10
    )
    print(f"   ✅ Primary Key: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ Primary Key Failed: {e}")

# Test secondary key
print("\n2. Testing Secondary OpenAI Key...")
try:
    client_secondary = openai.OpenAI(api_key=secondary_key)
    response = client_secondary.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Secondary key works'"}],
        max_tokens=10
    )
    print(f"   ✅ Secondary Key: {response.choices[0].message.content}")
except Exception as e:
    print(f"   ❌ Secondary Key Failed: {e}")

# Test system initialization
print("\n" + "-" * 80)
print("Testing Dual-Agent System Initialization...")
print("-" * 80)

try:
    from src.forensics.dual_agent import DualAgentCoordinator
    
    coordinator = DualAgentCoordinator()
    availability = coordinator.availability()
    
    print(f"\n✅ System Initialized:")
    print(f"   OpenAI (Primary): {availability['openai']}")
    print(f"   Secondary Agent: {availability['anthropic']}")
    print(f"   GovInfo: {availability['govinfo']}")
    
    if availability['openai'] and availability['anthropic']:
        print("\n🎉 DUAL-OPENAI MODE: FULLY OPERATIONAL!")
        print("\n   Both OpenAI agents are working:")
        print("   • Primary Agent (OpenAI): Initial violation detection")
        print("   • Secondary Agent (OpenAI): Cross-reference validation")
        print("\n   System is ready for forensic investigations!")
    else:
        print("\n⚠️  One or both agents failed to initialize")
        print("   Check the logs above for details")

except Exception as e:
    print(f"\n❌ System initialization failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)

