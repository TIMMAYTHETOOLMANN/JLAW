"""
NIKE 2019 QUICK DEPLOYMENT
===========================

Quick deployment script that directly uses the existing forensic orchestrator.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

print("=" * 100)
print("NIKE 2019 SEC FILINGS - COMPREHENSIVE FORENSIC INVESTIGATION")
print("=" * 100)
print(f"Deployment Started: {datetime.now().isoformat()}")
print()

async def main():
    """Execute Nike 2019 investigation."""
    
    try:
        # Import orchestrator
        print("📦 Loading forensic orchestrator...")
        from src.forensics.forensic_orchestrator import ForensicOrchestrator
        
        print("✅ Orchestrator loaded")
        print()
        
        # Initialize
        print("🔧 Initializing dual-agent system...")
        orchestrator = ForensicOrchestrator()
        print("✅ System initialized")
        print()
        
        # Configure investigation
        print("📋 Investigation Configuration:")
        print(f"   Company: NIKE INC (NKE)")
        print(f"   CIK: 0000320187")
        print(f"   Year: 2019")
        print(f"   Dual-Agent: Enabled (OpenAI + Anthropic)")
        print(f"   GovInfo: Enabled (USC/CFR statutes)")
        print()
        
        # Execute
        print("🚀 Starting comprehensive investigation...")
        print("   This will analyze ALL Nike 2019 SEC filings")
        print("   Expected duration: 10-30 minutes depending on filing count")
        print()
        
        result = await orchestrator.investigate_company_year(
            cik="0000320187",
            year=2019,
            include_amendments=True,
            enable_dual_agent=True,
            enable_govinfo=True
        )
        
        # Results
        print("\n" + "=" * 100)
        print("INVESTIGATION COMPLETE")
        print("=" * 100)
        
        if result.get('status') == 'SUCCESS':
            summary = result.get('summary', {})
            
            print(f"\n✅ Success!")
            print(f"\n📊 Results Summary:")
            print(f"   Filings Analyzed: {summary.get('total_filings', 0)}")
            print(f"   Violations Found: {summary.get('total_violations', 0)}")
            print(f"   Critical: {summary.get('critical_violations', 0)}")
            print(f"   High: {summary.get('high_violations', 0)}")
            print(f"   Statutes: {summary.get('statutes_correlated', 0)}")
            print(f"   Confidence: {summary.get('confidence_level', 0):.1%}")
            
            # Save
            output_dir = Path("forensic_reports/nike_2019")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            import json
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"nike_2019_results_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\n💾 Results saved: {output_file}")
            print(f"\n🎉 Deployment complete!")
            
            return True
        else:
            print(f"\n❌ Investigation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    print("\n" + "=" * 100)
    if success:
        print("✅ NIKE 2019 DEPLOYMENT: SUCCESS")
    else:
        print("❌ NIKE 2019 DEPLOYMENT: FAILED")
    print("=" * 100)
    
    sys.exit(0 if success else 1)

