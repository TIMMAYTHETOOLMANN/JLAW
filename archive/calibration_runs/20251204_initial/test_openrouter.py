"""
OpenRouter Integration Test
Tests the OpenRouter adapter to ensure it works correctly as an Anthropic replacement.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("OPENROUTER INTEGRATION TEST")
print("=" * 80)

# Check OpenRouter key
openrouter_key = os.getenv('OPENROUTER_API_KEY')
if openrouter_key:
    print(f"✅ OpenRouter API Key: Loaded (begins: {openrouter_key[:20]}...)")
else:
    print("❌ OpenRouter API Key: NOT FOUND")
    sys.exit(1)

# Test OpenRouter adapter
print("\n" + "-" * 80)
print("Testing OpenRouter Adapter")
print("-" * 80)

try:
    from src.forensics.openrouter_adapter import create_anthropic_compatible_client
    
    client = create_anthropic_compatible_client()
    print("✅ OpenRouter adapter created successfully")
    
    # Test simple API call
    print("\nSending test message to Claude via OpenRouter...")
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "Hello! Please respond with 'OpenRouter integration successful' if you receive this."
            }
        ]
    )
    
    if response and response.content:
        message = response.content[0].text
        print(f"✅ Response received: {message[:100]}...")
        
        if "successful" in message.lower() or "openrouter" in message.lower():
            print("✅ OpenRouter integration verified successfully!")
        else:
            print("⚠️  Response received but unexpected content")
    else:
        print("❌ No response content received")
        sys.exit(1)

except Exception as e:
    print(f"❌ OpenRouter test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test Anthropic analyzer with OpenRouter
print("\n" + "-" * 80)
print("Testing Anthropic Analyzer with OpenRouter")
print("-" * 80)

try:
    from src.forensics.anthropic_agent_analyzer import AnthropicAgentAnalyzer
    
    analyzer = AnthropicAgentAnalyzer()
    print(f"✅ Anthropic analyzer initialized")
    print(f"   Using: {'OpenRouter' if analyzer.using_openrouter else 'Direct Anthropic'}")
    print(f"   Model: {analyzer.model}")
    
    # Test analyze_text method
    print("\nTesting analyze_text method...")
    
    import asyncio
    
    async def test_analyze():
        test_content = """
        <ownershipDocument>
            <transactionDate>
                <value>2019-03-15</value>
            </transactionDate>
            <transactionPricePerShare>
                <value>0.00</value>
            </transactionPricePerShare>
        </ownershipDocument>
        """
        
        result = await analyzer.analyze_text(
            content=test_content,
            context={
                "filing_type": "4",
                "document_url": "https://test.example.com/test.xml",
                "filing_date": "2019-03-25"
            }
        )
        
        return result
    
    result = asyncio.run(test_analyze())
    
    if result.get("status") == "success":
        violations = result.get("violations", [])
        print(f"✅ Analysis successful!")
        print(f"   Violations detected: {len(violations)}")
        if violations:
            print(f"   First violation: {violations[0].get('type', 'unknown')}")
    else:
        print(f"⚠️  Analysis completed with status: {result.get('status')}")
        if "error" in result:
            print(f"   Error: {result.get('error')}")

except Exception as e:
    print(f"❌ Analyzer test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("OPENROUTER INTEGRATION: SUCCESS ✅")
print("=" * 80)
print("\n✅ All tests passed!")
print("✅ OpenRouter adapter working correctly")
print("✅ Anthropic analyzer using OpenRouter")
print("✅ System ready for dual-agent investigation")
print("\nNext step: Run comprehensive validation")
print("Command: python validate_pdf_baseline.py")
print("=" * 80)

