"""
Simple Nike 2019 Analysis Runner
Bypasses console encoding issues by writing directly to file
"""

import asyncio
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

# Disable emoji logging before importing
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

def log_status(msg):
    """Log status to both console and file."""
    print(msg)
    with open('nike_analysis_status.txt', 'a') as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")

async def run_analysis():
    """Run Nike 2019 analysis and save results."""
    # Clear status file
    with open('nike_analysis_status.txt', 'w') as f:
        f.write(f"NIKE 2019 ANALYSIS STARTED - {datetime.now()}\n")
    
    from src.forensics.forensic_orchestrator import ForensicOrchestrator
    from src.forensics.config_manager import get_config
    from src.forensics.immutable_storage import StorageConfig
    
    log_status("Initializing configuration...")
    config = get_config()
    log_status("Configuration loaded")
    
    # Initialize orchestrator
    log_status("Initializing orchestrator...")
    orchestrator = ForensicOrchestrator(
        govinfo_api_key=config.config.govinfo.api_key,
        storage_config=StorageConfig(provider=config.config.storage_provider),
        audit_signing_key=b"nike-2019-simple-runner",
        user_agent="JARVIS-SIMPLE-RUNNER"
    )
    
    log_status(f"\n{'='*80}")
    log_status(f"{'NIKE 2019 ANALYSIS':^80}")
    log_status(f"{'='*80}\n")
    log_status(f"Target: Nike Inc (CIK: 0000320187)")
    log_status(f"Period: 2019-01-01 to 2019-12-31")
    log_status(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create case
    from src.forensics.forensic_orchestrator import ForensicCase
    case = ForensicCase(
        case_id="NIKE_2019_SIMPLE",
        target_cik="0000320187",
        target_company="Nike Inc",
        investigation_start=datetime.now()
    )
    
    # Collect filings
    log_status("[1/3] Collecting Nike 2019 filings...")
    filings = await orchestrator._collect_filings(
        case=case,
        filing_types=None,  # All types
        years=1  # 2019
    )
    
    log_status(f"   Found {len(filings)} filings\n")
    
    # Analyze filings
    log_status("[2/3] Analyzing filings...")
    violations_found = []
    
    for i, filing in enumerate(filings[:10], 1):  # Start with first 10
        form_type = filing.get('form_type', 'UNKNOWN')
        log_status(f"   [{i}/10] {form_type}...")
        
        try:
            # Simple analysis
            if form_type in ['4', '4/A']:
                # Form 4 analysis
                from src.forensics.insider_form4_analyzer import InsiderForm4Analyzer
                analyzer = InsiderForm4Analyzer()
                
                violations = await analyzer.analyze_form4(
                    xml_url=filing.get('document_url'),
                    filing_date_str=filing.get('filing_date'),
                    viewer_url=filing.get('viewer_url')
                )
                
                if violations:
                    violations_found.extend(violations)
                    log_status(f"      -> {len(violations)} violations")
                else:
                    log_status(f"      -> OK")
            else:
                log_status(f"      -> Skipped")
        except Exception as e:
            log_status(f"      -> Error: {str(e)[:50]}")
    
    log_status(f"\n[3/3] Saving results...")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'target': 'Nike Inc (CIK: 0000320187)',
        'period': '2019',
        'filings_found': len(filings),
        'filings_analyzed': 10,
        'violations_found': len(violations_found),
        'violations': [
            {
                'type': v.type,
                'description': v.description,
                'severity': v.severity
            }
            for v in violations_found
        ]
    }
    
    output_file = f"nike_2019_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_status(f"\n{'='*80}")
    log_status(f"{'ANALYSIS COMPLETE':^80}")
    log_status(f"{'='*80}\n")
    log_status(f"Violations Found: {len(violations_found)}")
    log_status(f"Results saved to: {output_file}\n")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(run_analysis())
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

