"""
Verification script for Agent SDK integration.
"""
from src.forensics.config_manager import get_config
from src.forensics.forensic_orchestrator import ForensicOrchestrator
from src.forensics.immutable_storage import StorageConfig
import os

print("=" * 80)
print("AGENT SDK INTEGRATION VERIFICATION")
print("=" * 80)

# Load config
config = get_config()

print(f"\n1. OpenAI Configuration:")
print(f"   API Key Loaded: {bool(config.config.openai.api_key)}")
print(f"   Model: {config.config.openai.model}")
print(f"   Max Tokens: {config.config.openai.max_tokens}")

# Create orchestrator
print(f"\n2. Initializing ForensicOrchestrator...")
orchestrator = ForensicOrchestrator(
    govinfo_api_key=config.config.govinfo.api_key,
    storage_config=StorageConfig(provider=config.config.storage_provider),
    audit_signing_key=os.urandom(32),
    user_agent=config.config.sec.user_agent
)

print(f"\n3. SEC Analyzer Type:")
print(f"   Class: {type(orchestrator.sec_analyzer).__name__}")
print(f"   Has Agent: {hasattr(orchestrator.sec_analyzer, 'agent')}")
print(f"   Has Manual Fallback: {hasattr(orchestrator.sec_analyzer, 'manual_analyzer')}")

if hasattr(orchestrator.sec_analyzer, 'agent'):
    print(f"   Agent Model: {orchestrator.sec_analyzer.model}")
    print(f"   Agent Name: {orchestrator.sec_analyzer.agent.name}")

print(f"\n4. Integration Status:")
if type(orchestrator.sec_analyzer).__name__ == 'AgentSECForensicAnalyzer':
    print("   ✅ AGENT SDK INTEGRATION ACTIVE")
    print("   ✅ Intelligent web scraping enabled")
    print("   ✅ Semantic violation detection enabled")
else:
    print("   ⚠️  Manual analyzer active")
    print("   ⚠️  Agent SDK not in use")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

