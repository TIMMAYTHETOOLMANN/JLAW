"""
NIKE 2019 PRODUCTION DEPLOYMENT
================================

Production-grade deployment using the actual ForensicOrchestrator.
Analyzes all Nike 2019 SEC filings with dual-agent system.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def deploy_nike_2019():
    """Deploy on all Nike 2019 filings."""
    
    print("\n" + "=" * 100)
    print("NIKE INC (NKE) - 2019 SEC FILINGS FORENSIC INVESTIGATION")
    print("PRODUCTION DEPLOYMENT")
    print("=" * 100)
    print(f"\nDeployment Time: {datetime.now().isoformat()}")
    print(f"Company: NIKE INC (NKE)")
    print(f"CIK: 0000320187")
    print(f"Fiscal Year: 2019")
    print(f"Method: Dual-Agent (OpenAI + Anthropic + GovInfo)")
    print("\n" + "=" * 100)
    
    try:
        # Import required modules
        logger.info("Importing modules...")
        from src.forensics.forensic_orchestrator import ForensicOrchestrator
        from src.forensics.immutable_storage import StorageConfig
        from src.forensics.config_manager import get_config
        import os
        
        # Get configuration
        config = get_config()
        
        # Prepare storage config
        storage_config = StorageConfig(
            provider="LOCAL",
            base_path="forensic_storage",
            enable_encryption=False,
            enable_compression=True
        )
        
        # Generate audit signing key (or load from secure storage)
        audit_signing_key = b"forensic_audit_key_nike_2019_deployment"
        
        # Get GovInfo API key
        govinfo_key = os.getenv('GOVINFO_API_KEY') or config.config.govinfo.api_key
        
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = ForensicOrchestrator(
            govinfo_api_key=govinfo_key,
            storage_config=storage_config,
            audit_signing_key=audit_signing_key,
            user_agent="JLAW Forensics System contact@jlaw-forensics.org"
        )
        
        print("\n✅ System Initialized")
        print("   • Dual-Agent Coordinator: Ready")
        print("   • GovInfo Integration: Ready")
        print("   • SEC EDGAR Connection: Ready")
        
        # Start investigation
        print("\n🚀 Starting Investigation...")
        print("   Target: NIKE INC (0000320187)")
        print("   Year: 2019")
        print("   Mode: Full Tandem Investigation")
        
        # Run tandem investigation (dual-agent)
        case_id = await orchestrator.run_tandem_investigation(
            cik="0000320187",
            filing_types=["10-K", "10-Q", "8-K", "4"],  # All major forms
            start_date="2019-01-01",
            end_date="2019-12-31"
        )
        
        logger.info(f"Investigation initiated: Case ID = {case_id}")
        print(f"\n✅ Investigation Running: Case ID = {case_id}")
        
        # Wait for completion (check status periodically)
        print("\n⏳ Processing filings (this may take several minutes)...")
        
        max_wait = 1800  # 30 minutes max
        check_interval = 10  # Check every 10 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            await asyncio.sleep(check_interval)
            elapsed += check_interval
            
            status = await orchestrator.get_case_status(case_id)
            
            if status.get('status') in ['COMPLETE', 'FAILED']:
                break
            
            # Show progress
            progress = status.get('progress', {})
            print(f"   Progress: {progress.get('filings_processed', 0)}/{progress.get('total_filings', '?')} filings", end='\r')
        
        # Get final results
        print("\n\n📊 Retrieving Results...")
        final_status = await orchestrator.get_case_status(case_id)
        
        if final_status.get('status') == 'COMPLETE':
            print("\n" + "=" * 100)
            print("✅ INVESTIGATION COMPLETE")
            print("=" * 100)
            
            # Extract summary
            summary = final_status.get('summary', {})
            violations = final_status.get('violations', [])
            
            print(f"\n📋 SUMMARY:")
            print(f"   Total Filings Analyzed: {summary.get('filings_analyzed', 0)}")
            print(f"   Forms 10-K: {summary.get('forms_10k', 0)}")
            print(f"   Forms 10-Q: {summary.get('forms_10q', 0)}")
            print(f"   Forms 8-K: {summary.get('forms_8k', 0)}")
            print(f"   Forms 4: {summary.get('forms_4', 0)}")
            
            print(f"\n🚨 VIOLATIONS:")
            print(f"   Total: {len(violations)}")
            print(f"   Critical: {sum(1 for v in violations if v.get('severity') == 'CRITICAL')}")
            print(f"   High: {sum(1 for v in violations if v.get('severity') == 'HIGH')}")
            print(f"   Medium: {sum(1 for v in violations if v.get('severity') == 'MEDIUM')}")
            
            print(f"\n🤖 DUAL-AGENT METRICS:")
            print(f"   OpenAI Detections: {summary.get('openai_detections', 0)}")
            print(f"   Anthropic Validations: {summary.get('anthropic_validations', 0)}")
            print(f"   Confidence: {summary.get('confidence', 0):.1%}")
            
            print(f"\n📚 LEGAL FRAMEWORK:")
            print(f"   Statutes Correlated: {summary.get('statutes', 0)}")
            print(f"   CFR Regulations: {summary.get('regulations', 0)}")
            
            # Save results
            output_dir = Path("forensic_reports/nike_2019_production")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = output_dir / f"nike_2019_complete_{timestamp}.json"
            
            with open(result_file, 'w') as f:
                json.dump(final_status, f, indent=2, default=str)
            
            print(f"\n💾 Results Saved: {result_file}")
            
            # Generate report summary
            report_file = output_dir / f"nike_2019_summary_{timestamp}.md"
            with open(report_file, 'w') as f:
                f.write(f"""# Nike 2019 Forensic Investigation Results

**Case ID**: {case_id}
**Completion Time**: {datetime.now().isoformat()}
**Status**: COMPLETE

## Summary
- Filings Analyzed: {summary.get('filings_analyzed', 0)}
- Total Violations: {len(violations)}
- Confidence Level: {summary.get('confidence', 0):.1%}

## Dual-Agent Performance
- OpenAI Detections: {summary.get('openai_detections', 0)}
- Anthropic Validations: {summary.get('anthropic_validations', 0)}
- Agreement Rate: {summary.get('agreement_rate', 0):.1%}

## Legal Framework
- USC Statutes: {summary.get('statutes', 0)}
- CFR Regulations: {summary.get('regulations', 0)}

## Top Violations
{"".join([f"- {v.get('type')}: {v.get('severity')}\n" for v in violations[:10]])}

**Full results**: See {result_file.name}
""")
            
            print(f"💾 Summary Report: {report_file}")
            
            print("\n" + "=" * 100)
            print("🎉 DEPLOYMENT SUCCESSFUL")
            print("=" * 100)
            
            return True
            
        else:
            print(f"\n❌ Investigation failed: {final_status.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Deployment Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀" * 50)
    print("DEPLOYING ON ALL NIKE 2019 SEC FILINGS")
    print("🚀" * 50)
    
    success = asyncio.run(deploy_nike_2019())
    
    print("\n" + "=" * 100)
    if success:
        print("✅ NIKE 2019 DEPLOYMENT: COMPLETE")
        print("\nAll filings have been analyzed with dual-agent validation")
        print("Results saved in: forensic_reports/nike_2019_production/")
    else:
        print("❌ NIKE 2019 DEPLOYMENT: FAILED")
        print("\nCheck logs for details")
    print("=" * 100 + "\n")

