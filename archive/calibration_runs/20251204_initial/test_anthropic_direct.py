"""Quick test of Anthropic API directly"""
import os
from dotenv import load_dotenv
load_dotenv(override=True)

print("=" * 80)
print("TESTING DIRECT ANTHROPIC API")
print("=" * 80)

anthropic_key = os.getenv('ANTHROPIC_API_KEY')
print(f"\nAnthropic Key: {anthropic_key[:40] if anthropic_key else 'NOT FOUND'}...")

if not anthropic_key:
    print("❌ No Anthropic API key found!")
    exit(1)

print("\n1. Testing Anthropic SDK Import...")
try:
    import anthropic
    print("   ✅ Anthropic SDK imported")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)

print("\n2. Testing Direct Anthropic API Call...")
try:
    client = anthropic.Anthropic(api_key=anthropic_key)
    
    # Try different model names to find the correct one
    model_names = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest", 
        "claude-3-5-sonnet",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229"
    ]
    
    success = False
    for model in model_names:
        try:
            print(f"   Trying model: {model}")
            message = client.messages.create(
                model=model,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Say 'Anthropic API works!'"}
                ]
            )
            response_text = message.content[0].text
            print(f"   ✅ Response: {response_text}")
            print(f"   ✅ Model that works: {model}")
            print(f"   ✅ Tokens used: {message.usage.input_tokens + message.usage.output_tokens}")
            success = True
            break
        except anthropic.NotFoundError:
            print(f"   ❌ Model {model} not found")
            continue
        except Exception as e:
            print(f"   ❌ Error with {model}: {e}")
            continue
    
    if not success:
        print("   ❌ No working model found!")
        exit(1)
    
    response_text = message.content[0].text
    print(f"   ✅ Response: {response_text}")
    print(f"   ✅ Tokens used: {message.usage.input_tokens + message.usage.output_tokens}")
    
except Exception as e:
    print(f"   ❌ API call failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n3. Testing Anthropic Agent Analyzer...")
try:
    from src.forensics.anthropic_agent_analyzer import AnthropicAgentAnalyzer
    
    analyzer = AnthropicAgentAnalyzer()
    print(f"   ✅ Analyzer initialized")
    print(f"   Using: {'OpenRouter' if analyzer.using_openrouter else 'Direct Anthropic'}")
    print(f"   Model: {analyzer.model}")
    
except Exception as e:
    print(f"   ❌ Analyzer initialization failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - ANTHROPIC API WORKING")
print("=" * 80)

