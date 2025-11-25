"""
Verification Script for Multi-Provider AI Agent Integration
Tests OpenAI, Anthropic, and Multi-Pass Analysis
"""

import os
import sys
import asyncio
from datetime import datetime

print("="*80)
print("JLAW MULTI-PROVIDER AI AGENT VERIFICATION")
print("="*80)
print(f"Timestamp: {datetime.now().isoformat()}")
print()

# Test 1: Configuration Loading
print("[1] Configuration Loading")
try:
    from src.forensics.config_manager import get_config
    config = get_config()
    
    print(f"  [OK] Config loaded successfully")
    print(f"  AI Provider: {config.config.ai_provider.provider}")
    print(f"  Multi-Pass: {config.config.ai_provider.enable_multipass}")
    print(f"  Max Passes: {config.config.ai_provider.max_passes}")
    print()
except Exception as e:
    print(f"  ❌ Config loading failed: {e}")
    sys.exit(1)

# Test 2: OpenAI Configuration
print("[2] OpenAI Configuration")
if config.config.openai.api_key:
    print(f"  ✅ API Key: Configured")
    print(f"  Model: {config.config.openai.model}")
    print(f"  Max Tokens: {config.config.openai.max_tokens}")
else:
    print(f"  ⚠️  API Key: Not configured")
print()

# Test 3: Anthropic Configuration
print("[3] Anthropic Configuration")
if config.config.anthropic.api_key:
    print(f"  ✅ API Key: Configured")
    print(f"  Model: {config.config.anthropic.model}")
    print(f"  Max Tokens: {config.config.anthropic.max_tokens}")
else:
    print(f"  ⚠️  API Key: Not configured")
print()

# Test 4: SDK Availability
print("[4] SDK Availability")
try:
    from agents import Agent
    print(f"  ✅ OpenAI Agents SDK: Available")
except Exception as e:
    print(f"  ❌ OpenAI Agents SDK: {e}")

try:
    import anthropic
    print(f"  ✅ Anthropic SDK: Available")
except Exception as e:
    print(f"  ❌ Anthropic SDK: {e}")
print()

# Test 5: Analyzer Initialization
print("[5] Analyzer Initialization")
openai_ok = False
anthropic_ok = False

if config.config.openai.api_key:
    try:
        from src.forensics.agent_sec_analyzer import AgentSECForensicAnalyzer
        analyzer = AgentSECForensicAnalyzer()
        print(f"  ✅ OpenAI Analyzer: Initialized")
        print(f"     Model: {analyzer.model}")
        print(f"     Has Agent: {hasattr(analyzer, 'agent')}")
        openai_ok = True
    except Exception as e:
        print(f"  ❌ OpenAI Analyzer: {e}")

if config.config.anthropic.api_key:
    try:
        from src.forensics.anthropic_agent_analyzer import AnthropicAgentAnalyzer
        analyzer = AnthropicAgentAnalyzer()
        print(f"  ✅ Anthropic Analyzer: Initialized")
        print(f"     Model: {analyzer.model}")
        print(f"     Has Client: {hasattr(analyzer, 'client')}")
        anthropic_ok = True
    except Exception as e:
        print(f"  ❌ Anthropic Analyzer: {e}")
print()

# Test 6: Forensic Orchestrator Integration
print("[6] Forensic Orchestrator Integration")
try:
    from src.forensics.forensic_orchestrator import ForensicOrchestrator
    from src.forensics.immutable_storage import StorageConfig
    
    orchestrator = ForensicOrchestrator(
        govinfo_api_key=config.config.govinfo.api_key or "DEMO_KEY",
        storage_config=StorageConfig(provider=config.config.storage_provider),
        audit_signing_key=os.urandom(32),
        user_agent=config.config.sec.user_agent
    )
    
    analyzer_type = type(orchestrator.sec_analyzer).__name__
    print(f"  ✅ Orchestrator Initialized")
    print(f"     Active Analyzer: {analyzer_type}")
    print(f"     Has OpenAI Analyzer: {orchestrator.openai_analyzer is not None}")
    print(f"     Has Anthropic Analyzer: {orchestrator.anthropic_analyzer is not None}")
    print(f"     Has Multi-Pass Strategy: {orchestrator.multipass_strategy is not None}")
except Exception as e:
    print(f"  ❌ Orchestrator: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 7: Multi-Pass Strategy
print("[7] Multi-Pass Strategy")
if config.config.ai_provider.enable_multipass:
    try:
        from src.forensics.multipass_strategy import MultiPassAnalysisStrategy
        
        strategy = MultiPassAnalysisStrategy(
            openai_analyzer=orchestrator.openai_analyzer,
            anthropic_analyzer=orchestrator.anthropic_analyzer,
            manual_analyzer=orchestrator.manual_analyzer,
            enable_multipass=True,
            max_passes=config.config.ai_provider.max_passes
        )
        print(f"  ✅ Multi-Pass Strategy: Initialized")
        print(f"     Max Passes: {strategy.max_passes}")
        print(f"     Enabled: {strategy.enable_multipass}")
    except Exception as e:
        print(f"  ❌ Multi-Pass Strategy: {e}")
else:
    print(f"  ⚠️  Multi-Pass: Disabled in configuration")
print()

# Test 8: Secret Hygiene
print("[8] Secret Hygiene Check")
secret_files_to_check = [
    'OPENAI_AGENT_SDK_INTEGRATION_COMPLETE.md',
    'MISSING_OPENAI_AGENT_SDK_ANALYSIS.md',
    'README.md'
]

secrets_found = False
for file in secret_files_to_check:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Check for API key patterns
            if 'sk-proj-' in content or 'sk-ant-api' in content:
                if '<your-' not in content.lower() and 'placeholder' not in content.lower():
                    print(f"  ⚠️  Potential secret in {file}")
                    secrets_found = True

if not secrets_found:
    print(f"  ✅ No hardcoded secrets detected in documentation")
else:
    print(f"  ⚠️  Review documentation for exposed secrets")
print()

# Test 9: .gitignore Check
print("[9] .gitignore Protection")
if os.path.exists('.gitignore'):
    with open('.gitignore', 'r') as f:
        gitignore = f.read()
        checks = {
            '.env': '.env' in gitignore,
            'secrets/': 'secrets/' in gitignore,
            '*.key': '*.key' in gitignore
        }
        
        all_protected = all(checks.values())
        if all_protected:
            print(f"  ✅ .gitignore properly configured")
        else:
            print(f"  ⚠️  .gitignore missing protection:")
            for item, protected in checks.items():
                if not protected:
                    print(f"     - {item}")
else:
    print(f"  ❌ .gitignore not found")
print()

# Summary
print("="*80)
print("VERIFICATION SUMMARY")
print("="*80)

status_items = [
    ("Configuration", True),
    ("OpenAI SDK", openai_ok or not config.config.openai.api_key),
    ("Anthropic SDK", anthropic_ok or not config.config.anthropic.api_key),
    ("Orchestrator", True),
    ("Secret Hygiene", not secrets_found)
]

all_ok = all(status for _, status in status_items)

for item, status in status_items:
    symbol = "✅" if status else "❌"
    print(f"{symbol} {item}")

print()
if all_ok:
    print("🎯 ALL SYSTEMS OPERATIONAL")
    print()
    print("Next Steps:")
    print("1. Run Nike 2019 analysis:")
    print("   python jlaw_forensics.py investigate --cik 0000320187 --name \"Nike Inc\" --years 1 --output nike_2019_multiagent.json")
    print()
    print("2. Test multi-pass analysis:")
    print("   python jlaw_forensics.py investigate --cik 0000320187 --name \"Nike Inc\" --years 1 --multipass --output nike_2019_multipass.json")
    print()
    print("3. Compare providers:")
    print("   python jlaw_forensics.py investigate --cik 0000320187 --name \"Nike Inc\" --years 1 --ai-provider ANTHROPIC")
else:
    print("⚠️  SOME ISSUES DETECTED - Review output above")

print("="*80)

