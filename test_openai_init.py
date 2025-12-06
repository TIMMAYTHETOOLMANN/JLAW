"""Quick test to see why OpenAI analyzer isn't initializing"""
from dotenv import load_dotenv
load_dotenv()

print("Testing OpenAI analyzer initialization...")

try:
    from src.forensics.agent_sec_analyzer import AgentSECForensicAnalyzer
    analyzer = AgentSECForensicAnalyzer()
    print(f"✅ OpenAI analyzer initialized successfully")
    print(f"   Model: {analyzer.model}")
    print(f"   Agent available: {analyzer.agent is not None}")
except Exception as e:
    print(f"❌ OpenAI analyzer failed: {e}")
    import traceback
    traceback.print_exc()

