"""Quick API key verification"""
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 80)
print("API KEY VERIFICATION")
print("=" * 80)

primary = os.getenv('OPENAI_API_KEY', '')
secondary = os.getenv('OPENAI_SECONDARY_API_KEY', '')
openrouter = os.getenv('OPENROUTER_API_KEY', '')
anthropic = os.getenv('ANTHROPIC_API_KEY', '')

print(f"\nPrimary OpenAI: {primary[:30] if primary else 'NOT SET'}...")
print(f"Secondary OpenAI: {secondary[:30] if secondary else 'NOT SET'}...")
print(f"OpenRouter: {openrouter[:30] if openrouter else 'NOT SET (Disabled for dual-OpenAI mode)'}...")
print(f"Anthropic: {anthropic[:30] if anthropic else 'NOT SET'}...")

print("\n" + "=" * 80)
print("CONFIGURATION STATUS")
print("=" * 80)

if primary and secondary:
    print("✅ DUAL-OPENAI MODE: Configured correctly")
    print("   - Primary Agent: OpenAI (key 1)")
    print("   - Secondary Agent: OpenAI (key 2)")
elif primary and (openrouter or anthropic):
    print("⚠️  MIXED MODE: OpenAI + Anthropic/OpenRouter")
else:
    print("❌ INCOMPLETE: Missing required API keys")

print("=" * 80)

