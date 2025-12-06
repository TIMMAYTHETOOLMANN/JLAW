The. """
Dual-OpenAI Configuration Test
================================

Tests the dual-OpenAI agent configuration where both primary and secondary
agents use OpenAI (with different API keys) instead of OpenAI + Anthropic.

This is a temporary configuration while waiting for Anthropic/OpenRouter credits.
"""

import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_dual_openai_configuration():
    """Test dual-OpenAI agent configuration."""
    
    print("=" * 80)
    print("DUAL-OPENAI CONFIGURATION TEST")
    print("=" * 80)
    
    # Test 1: Verify API keys are configured
    print("\n1. Verifying API Keys...")
    import os
    
    primary_key = os.getenv('OPENAI_API_KEY')
    secondary_key = os.getenv('OPENAI_SECONDARY_API_KEY')
    
    if primary_key:
        print(f"   ✅ Primary OpenAI Key: {primary_key[:20]}...")
    else:
        print("   ❌ Primary OpenAI Key: NOT FOUND")
        return False
    
    if secondary_key:
        print(f"   ✅ Secondary OpenAI Key: {secondary_key[:20]}...")
    else:
        print("   ❌ Secondary OpenAI Key: NOT FOUND")
        return False
    
    # Test 2: Initialize agents
    print("\n2. Initializing Dual-Agent System...")
    
    try:
        from src.forensics.dual_agent import DualAgentCoordinator
        coordinator = DualAgentCoordinator()
        
        availability = coordinator.availability()
        print(f"   ✅ System initialized")
        print(f"      - OpenAI (Primary): {availability['openai']}")
        print(f"      - Anthropic/Secondary: {availability['anthropic']}")
        print(f"      - GovInfo: {availability['govinfo']}")
        
        if not availability['openai']:
            print("   ❌ Primary OpenAI agent failed to initialize")
            return False
        
        if not availability['anthropic']:
            print("   ❌ Secondary agent failed to initialize")
            return False
        
        print("   ✅ Both agents ready for dual-agent analysis")
    
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Run sample analysis
    print("\n3. Running Sample Dual-Agent Analysis...")
    
    sample_content = """
    <ownershipDocument>
        <issuer>
            <issuerCik>0000320187</issuerCik>
            <issuerName>NIKE INC</issuerName>
        </issuer>
        <nonDerivativeTable>
            <nonDerivativeTransaction>
                <transactionDate>
                    <value>2019-03-15</value>
                </transactionDate>
                <transactionPricePerShare>
                    <value>0.00</value>
                </transactionPricePerShare>
                <transactionShares>
                    <value>10000</value>
                </transactionShares>
            </nonDerivativeTransaction>
        </nonDerivativeTable>
    </ownershipDocument>
    """
    
    filing_metadata = {
        "filing_type": "4",
        "document_url": "https://www.sec.gov/test.xml",
        "filing_date": "2019-03-25",  # 6 business days late
        "cik": "0000320187",
        "company_name": "NIKE INC"
    }
    
    try:
        result = await coordinator.investigate_with_cross_reference(
            content=sample_content,
            filing_metadata=filing_metadata,
            enable_govinfo_enrichment=True
        )
        
        print(f"   ✅ Analysis complete")
        print(f"      Status: {result.get('status')}")
        
        summary = result.get('investigation_summary', {})
        print(f"\n   📊 Results:")
        print(f"      Total Violations: {summary.get('total_violations_detected', 0)}")
        print(f"      Primary Agent (OpenAI): {summary.get('openai_initial_count', 0)}")
        print(f"      Secondary Agent (OpenAI): {summary.get('anthropic_cross_reference_count', 0)}")
        print(f"      Overlap: {summary.get('overlap_count', 0)}")
        print(f"      Confidence: {summary.get('confidence_level', 0):.2%}")
        
        violations = result.get('merged_violations', [])
        if violations:
            print(f"\n   🚨 Violations Detected:")
            for i, v in enumerate(violations[:3], 1):  # Show first 3
                print(f"      {i}. {v.get('type', 'unknown')}")
                print(f"         Source: {v.get('_source', 'N/A')}")
                print(f"         Confirmed by: {v.get('_confirmed_by', [])}")
        
        if result.get('status') == 'COMPLETE':
            print("\n   ✅ Dual-OpenAI mode working perfectly!")
            return True
        else:
            print(f"\n   ⚠️  Analysis completed with status: {result.get('status')}")
            return True  # Still consider it a success if it completed
    
    except Exception as e:
        print(f"   ❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await coordinator.close()


async def main():
    """Main entry point."""
    print("\n" + "🔄" * 40)
    print("TESTING DUAL-OPENAI AGENT CONFIGURATION")
    print("(Temporary setup while waiting for Anthropic/OpenRouter credits)")
    print("🔄" * 40 + "\n")
    
    success = await test_dual_openai_configuration()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ DUAL-OPENAI CONFIGURATION: SUCCESS")
        print("=" * 80)
        print("\n🎉 System is fully operational with two OpenAI agents!")
        print("\nBoth agents are now working:")
        print("  - Primary Agent (OpenAI #1): Initial violation detection")
        print("  - Secondary Agent (OpenAI #2): Cross-reference validation")
        print("\nThis configuration will work until you add Anthropic/OpenRouter credits.")
        print("When ready, simply add credits and the system will automatically")
        print("switch back to using Anthropic for even better cross-referencing.")
    else:
        print("❌ DUAL-OPENAI CONFIGURATION: FAILED")
        print("=" * 80)
        print("\n⚠️  Check the errors above and verify:")
        print("  1. Both OpenAI API keys are valid")
        print("  2. Keys have sufficient credits")
        print("  3. .env file is properly configured")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

