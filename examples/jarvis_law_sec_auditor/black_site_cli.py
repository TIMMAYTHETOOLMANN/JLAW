"""
JARVIS:LAW Black Site Protocol - Command Line Interface
Autonomous SEC forensics drone launcher
"""

import argparse
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sec_workflow import scan_by_ticker, scan_company_filings, scan_nike_form4s
from tools.sec_crawler import search_company_by_ticker, fetch_company_info_by_cik
from tools.utils import export_evidence_chain, get_violations_log


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS:LAW Black Site Protocol - Autonomous SEC Forensics Drone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan Nike Form 4 filings (default target)
  python black_site_cli.py --nike
  
  # Scan by ticker symbol
  python black_site_cli.py --ticker AAPL --form 10-K --start 2020 --end 2023
  
  # Scan by CIK
  python black_site_cli.py --cik 0000320187 --form 4 --start 2019 --end 2025
  
  # Export evidence chain
  python black_site_cli.py --export evidence_export.json
  
  # View violations log
  python black_site_cli.py --view-violations
        """
    )
    
    # Operation modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--nike",
        action="store_true",
        help="Execute Nike Form 4 scan (default target)"
    )
    mode_group.add_argument(
        "--ticker",
        type=str,
        help="Scan by stock ticker symbol (e.g., AAPL, TSLA)"
    )
    mode_group.add_argument(
        "--cik",
        type=str,
        help="Scan by CIK number (e.g., 0000320187)"
    )
    mode_group.add_argument(
        "--export",
        type=str,
        metavar="OUTPUT_FILE",
        help="Export evidence chain to file"
    )
    mode_group.add_argument(
        "--view-violations",
        action="store_true",
        help="View all logged violations"
    )
    mode_group.add_argument(
        "--lookup",
        type=str,
        metavar="TICKER",
        help="Look up CIK for ticker symbol"
    )
    
    # Scan parameters
    parser.add_argument(
        "--form",
        type=str,
        default="4",
        help="SEC form type (default: 4)"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=2019,
        help="Start year (default: 2019)"
    )
    parser.add_argument(
        "--end",
        type=int,
        default=2025,
        help="End year (default: 2025)"
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Company name (optional, for reporting)"
    )
    
    args = parser.parse_args()
    
    # Execute operation
    try:
        if args.nike:
            print("\n🎯 Target: Nike Inc Form 4 Filings\n")
            results = scan_nike_form4s()
            print_results(results)
            
        elif args.ticker:
            print(f"\n🎯 Target: {args.ticker} {args.form} Filings\n")
            results = scan_by_ticker(
                ticker=args.ticker,
                form_type=args.form,
                year_start=args.start,
                year_end=args.end
            )
            print_results(results)
            
        elif args.cik:
            print(f"\n🎯 Target: CIK {args.cik} {args.form} Filings\n")
            results = scan_company_filings(
                cik=args.cik,
                form_type=args.form,
                year_start=args.start,
                year_end=args.end,
                company_name=args.name or f"CIK-{args.cik}"
            )
            print_results(results)
            
        elif args.export:
            print(f"\n📦 Exporting evidence chain to: {args.export}\n")
            export_path = export_evidence_chain(args.export)
            print(f"✓ Export complete: {export_path}\n")
            
        elif args.view_violations:
            print("\n📋 Violations Log\n")
            violations = get_violations_log()
            if violations:
                for v in violations:
                    print(f"ID: {v.get('id')}")
                    print(f"Timestamp: {v.get('timestamp_utc')}")
                    print(f"Source: {v.get('source_url', 'N/A')}")
                    print(f"Company: {v.get('company', 'N/A')}")
                    print("-" * 70)
                print(f"\nTotal violations: {len(violations)}\n")
            else:
                print("No violations logged.\n")
                
        elif args.lookup:
            print(f"\n🔍 Looking up CIK for: {args.lookup}\n")
            cik = search_company_by_ticker(args.lookup)
            if cik:
                print(f"✓ CIK: {cik}\n")
                info = fetch_company_info_by_cik(cik)
                if "company_name" in info:
                    print(f"Company: {info['company_name']}")
                    print(f"SIC: {info.get('sic', 'N/A')}")
                    print(f"State: {info.get('state', 'N/A')}\n")
            else:
                print(f"✗ CIK not found for ticker '{args.lookup}'\n")
                
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_results(results: dict):
    """Print scan results summary."""
    print("\n" + "="*70)
    print("📊 SCAN RESULTS")
    print("="*70)
    print(f"Status: {results.get('status', 'unknown').upper()}")
    print(f"Total Filings: {results.get('total_filings', 0)}")
    print(f"Violations Detected: {results.get('violations_count', 0)}")
    if results.get('evidence_chain'):
        print(f"Evidence Chain: {results['evidence_chain']}")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║        JARVIS:LAW BLACK SITE PROTOCOL                             ║
║        Autonomous SEC Forensics Drone                             ║
║                                                                    ║
║        Status: OPERATIONAL                                        ║
║        Authority: Supreme                                         ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    main()

