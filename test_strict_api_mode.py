"""
Test Advanced Statute Integrator - STRICT API MODE (NO FALLBACK)
Demonstrates fail-fast behavior when GovInfo API is unavailable
"""

import asyncio
import os
import json
from src.forensics.advanced_statute_integrator import AdvancedStatuteIntegrator

async def test_strict_mode():
    """Test statute enrichment with STRICT API MODE (no fallback)."""
    
    # Get API key from environment (NO DEFAULT - must be set!)
    api_key = os.getenv("GOVINFO_API_KEY")
    if not api_key:
        print("[FAIL] GOVINFO_API_KEY not set in environment")
        print()
        print("ACTION REQUIRED:")
        print("  1. Get API key from https://api.data.gov/signup/")
        print("  2. Set GOVINFO_API_KEY in .env file")
        print("  3. Restart terminal to reload environment")
        return
    
    print("=" * 80)
    print("ADVANCED STATUTE INTEGRATOR TEST - STRICT API MODE")
    print("=" * 80)
    print()
    print("MODE: NO FALLBACK - System will FAIL if GovInfo API unavailable")
    print()
    
    # Initialize integrator in STRICT MODE
    print("[INIT] Initializing Advanced Statute Integrator...")
    try:
        integrator = AdvancedStatuteIntegrator(api_key, strict_api_mode=True)
        print("[OK] Integrator initialized in STRICT API MODE")
        print("[INFO] GovInfo API Key:", api_key[:20] + "..." if len(api_key) > 20 else api_key)
    except ValueError as e:
        print(f"[FAIL] Initialization error: {e}")
        print()
        print("ACTION REQUIRED:")
        print("  1. Get API key from https://api.data.gov/signup/")
        print("  2. Set GOVINFO_API_KEY in .env file")
        return
    print()
    
    # Test violation
    test_violation = {
        "statute": "15 USC 78j(b)",
        "description": "Material misstatement in MD&A",
        "evidence": ["Form 10-K"],
        "severity": "CIVIL",
        "confidence": 0.8
    }
    
    print("[TEST] Test Violation:")
    print(json.dumps(test_violation, indent=2))
    print()
    
    # Enrich the violation
    print("[RUN] Enriching violation with GovInfo API (STRICT MODE)...")
    try:
        enriched = await integrator.enrich_violation_with_govinfo(test_violation)
        
        print("[SUCCESS] Enrichment complete! GovInfo API operational.")
        print()
        print("[RESULT] Enriched Violation:")
        print("-" * 80)
        
        # Display govinfo_statute
        if "govinfo_statute" in enriched:
            statute = enriched["govinfo_statute"]
            print(f"  Citation: {statute.citation}")
            print(f"  Short Title: {statute.short_title}")
            print(f"  PDF URL: {statute.pdf_url}")
            print(f"  Text URL: {statute.text_url}")
            print(f"  Related CFR: {', '.join(statute.related_cfr)}")
            print(f"  Criminal: {statute.criminal_penalties}")
            print(f"  Civil: {statute.civil_penalties}")
        
        # Display related authorities
        if "related_authorities" in enriched:
            print()
            print("  Related Authorities:")
            for auth in enriched["related_authorities"]:
                print(f"    - {auth}")
        
        # Display precedents
        if "enforcement_precedents" in enriched:
            print()
            print("  Enforcement Precedents:")
            for prec in enriched["enforcement_precedents"]:
                print(f"    - {prec.get('case', 'Unknown')}")
                print(f"      Citation: {prec.get('citation', 'N/A')}")
        
        print("-" * 80)
        
    except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
        print()
        print("=" * 80)
        print("[FAIL] GOVINFO API FAILURE (STRICT MODE - NO FALLBACK)")
        print("=" * 80)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error: {e}")
        print()
        print("TROUBLESHOOTING:")
        print("  1. Verify GOVINFO_API_KEY is valid")
        print("  2. Check https://api.data.gov/docs/ for service status")
        print("  3. Test connectivity: ping api.govinfo.gov")
        print("  4. Check rate limits: 1000 requests/hour")
        print("  5. Try https://api.govinfo.gov/collections in browser")
        print()
        print("SYSTEM BEHAVIOR:")
        print("  - STRICT MODE enabled: NO fallback to local data")
        print("  - System FAILS FAST when API unavailable")
        print("  - This is INTENTIONAL behavior per configuration")
        print("=" * 80)
        await integrator.close()
        return
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        raise
    
    # Close session
    await integrator.close()
    print()
    print("=" * 80)
    print("[COMPLETE] TEST FINISHED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_strict_mode())

