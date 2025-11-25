"""
Test Advanced Statute Integrator
Demonstrates the enhanced GovInfo API integration
"""

import asyncio
import os
import json
from src.forensics.advanced_statute_integrator import AdvancedStatuteIntegrator

async def test_statute_enrichment():
    """Test statute enrichment with GovInfo API."""
    
    # Get API key from environment
    api_key = os.getenv("GOVINFO_API_KEY", "DEMO_KEY")
    
    print("=" * 80)
    print("ADVANCED STATUTE INTEGRATOR TEST")
    print("=" * 80)
    print()
    
    # Initialize integrator in strict API mode (NO FALLBACK)
    print("🔧 Initializing Advanced Statute Integrator (STRICT API MODE - NO FALLBACK)...")
    try:
        integrator = AdvancedStatuteIntegrator(api_key, strict_api_mode=True)
        print("✅ Integrator initialized in STRICT API MODE")
        print("⚠️  NOTE: System will FAIL FAST if GovInfo API is unavailable")
    except ValueError as e:
        print(f"❌ Initialization failed: {e}")
        return
    print()
    
    # Test violation (similar to what was in the JSON)
    test_violation = {
        "statute": "15 USC 78j(b)",
        "description": "Statutory violation detected - missing_mda",
        "evidence": ["Form 10-K"],
        "severity": "CIVIL",
        "confidence": 0.7
    }
    
    print("📋 Test Violation:")
    print(json.dumps(test_violation, indent=2))
    print()
    
    # Enrich the violation
    print("🚀 Enriching violation with GovInfo intelligence...")
    try:
        enriched = await integrator.enrich_violation_with_govinfo(test_violation)
        
        print("✅ Enrichment complete!")
        print()
        print("📊 Enriched Violation:")
        print("-" * 80)
        
        # Display govinfo_statute
        if "govinfo_statute" in enriched:
            statute = enriched["govinfo_statute"]
            print(f"  Citation: {statute.citation}")
            print(f"  Short Title: {statute.short_title}")
            print(f"  PDF URL: {statute.pdf_url}")
            print(f"  Text URL: {statute.text_url}")
            print(f"  Related CFR: {', '.join(statute.related_cfr)}")
            print(f"  Criminal Penalties: {statute.criminal_penalties}")
            print(f"  Civil Penalties: {statute.civil_penalties}")
        
        # Display related authorities
        if "related_authorities" in enriched:
            print()
            print("🔗 Related Authorities:")
            for auth in enriched["related_authorities"]:
                print(f"  - {auth}")
        
        # Display enforcement precedents
        if "enforcement_precedents" in enriched:
            print()
            print("⚖️ Enforcement Precedents:")
            for prec in enriched["enforcement_precedents"]:
                print(f"  - {prec.get('case', 'Unknown')}")
                print(f"    Citation: {prec.get('citation', 'N/A')}")
                print(f"    Principle: {prec.get('principle', 'N/A')}")
        
        print()
        print("-" * 80)
        
    except Exception as e:
        print(f"⚠️ Enrichment error: {e}")
    
    # Test comprehensive legal framework
    print()
    print("🏛️ Testing Comprehensive Legal Framework Generation (STRICT MODE)...")
    try:
        violations = [test_violation]
        framework = await integrator.get_comprehensive_legal_framework(violations)
        
        print("✅ Framework generated! All API calls successful.")
        print()
        print("📚 Legal Framework Summary:")
        print(f"  Primary Statutes: {len(framework.get('primary_statutes', []))}")
        print(f"  Regulations: {len(framework.get('regulations', []))}")
        print(f"  Criminal Statutes: {len(framework.get('criminal_statutes', []))}")
        print(f"  Enforcement Precedents: {len(framework.get('enforcement_precedents', []))}")
        
        # Display penalty framework
        if "penalty_framework" in framework:
            print()
            print("💰 Penalty Framework:")
            penalty = framework["penalty_framework"]
            crim = penalty.get("criminal_exposure", {})
            civil = penalty.get("civil_exposure", {})
            
            print(f"  Criminal Exposure:")
            print(f"    Max Imprisonment: {crim.get('max_imprisonment_years', 0)} years")
            print(f"    Max Individual Fine: ${crim.get('max_individual_fine', 0):,}")
            print(f"    Max Entity Fine: ${crim.get('max_entity_fine', 0):,}")
            print(f"  Civil Exposure:")
            print(f"    Total Estimated: ${civil.get('total_estimated', 0):,}")
            print(f"    Per Violation: ${civil.get('max_per_violation', 0):,}")
        
    except (ValueError, ConnectionError, TimeoutError, RuntimeError) as e:
        print()
        print("=" * 80)
        print("❌ GOVINFO API FAILURE (STRICT MODE)")
        print("=" * 80)
        print(f"Error: {e}")
        print("System configured to fail fast - no fallback data available")
        print("=" * 80)
        return
    except Exception as e:
        print(f"❌ Unexpected framework generation error: {e}")
        raise
    
    # Close session
    await integrator.close()
    print()
    print("=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_statute_enrichment())

