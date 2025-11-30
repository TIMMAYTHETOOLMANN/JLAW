#!/usr/bin/env python3
"""
Nike Inc. 2019 SEC Filings - Complete Fetcher
==============================================

Fetches ALL SEC filings by Nike Inc. for calendar year 2019.
Uses SEC EDGAR REST API v2.0 for production-grade data retrieval.

Company: Nike Inc.
CIK: 0000320187
Year: 2019 (January 1, 2019 - December 31, 2019)

This script retrieves:
- All filing types (10-K, 10-Q, 8-K, 4, 3, DEF 14A, etc.)
- Complete metadata (dates, accession numbers, URLs)
- Document links for evidence tracking
- Filing statistics and summary
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.forensics.real_sec_data_fetcher import RealSECDataFetcher, SECFiling

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'nike_2019_fetch_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


class Nike2019FilingFetcher:
    """Fetcher for all Nike 2019 SEC filings."""
    
    # Nike Inc. details
    COMPANY_NAME = "Nike Inc."
    CIK = "0000320187"
    
    # 2019 date range
    START_DATE = "2019-01-01"
    END_DATE = "2019-12-31"
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("forensic_storage/nike_2019_filings")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def fetch_all_filings(self) -> List[SECFiling]:
        """Fetch all Nike 2019 SEC filings."""
        
        logger.info("=" * 80)
        logger.info(f"FETCHING ALL SEC FILINGS: {self.COMPANY_NAME}")
        logger.info(f"CIK: {self.CIK}")
        logger.info(f"Year: 2019 ({self.START_DATE} to {self.END_DATE})")
        logger.info("=" * 80)
        
        async with RealSECDataFetcher() as fetcher:
            # Get all company filings
            logger.info("🔍 Retrieving company submission history from SEC EDGAR...")
            
            filings = await fetcher.get_company_filings(
                cik=self.CIK,
                start_date=self.START_DATE,
                end_date=self.END_DATE,
                filing_types=None  # Get ALL filing types
            )
            
            logger.info(f"✅ Retrieved {len(filings)} filings from SEC EDGAR")
            
            return filings
            
    def analyze_filings(self, filings: List[SECFiling]) -> Dict[str, Any]:
        """Analyze and categorize filings."""
        
        logger.info("\n" + "=" * 80)
        logger.info("FILING ANALYSIS")
        logger.info("=" * 80)
        
        # Count by filing type
        filing_type_counts = Counter(f.filing_type for f in filings)
        
        # Categorize filings
        major_filings = []  # 10-K, 10-Q
        current_reports = []  # 8-K
        insider_reports = []  # Forms 3, 4, 5
        proxy_materials = []  # DEF 14A, etc.
        other_filings = []
        
        for filing in filings:
            filing_type = filing.filing_type
            
            if filing_type in ['10-K', '10-K/A']:
                major_filings.append(filing)
            elif filing_type in ['10-Q', '10-Q/A']:
                major_filings.append(filing)
            elif '8-K' in filing_type:
                current_reports.append(filing)
            elif filing_type in ['3', '4', '4/A', '5']:
                insider_reports.append(filing)
            elif 'DEF 14A' in filing_type or 'PRE 14A' in filing_type:
                proxy_materials.append(filing)
            else:
                other_filings.append(filing)
                
        analysis = {
            'total_filings': len(filings),
            'filing_type_counts': dict(filing_type_counts),
            'categories': {
                'major_reports': {
                    'count': len(major_filings),
                    'types': list(set(f.filing_type for f in major_filings)),
                    'filings': [self._filing_to_dict(f) for f in major_filings]
                },
                'current_reports': {
                    'count': len(current_reports),
                    'types': list(set(f.filing_type for f in current_reports)),
                    'filings': [self._filing_to_dict(f) for f in current_reports]
                },
                'insider_reports': {
                    'count': len(insider_reports),
                    'types': list(set(f.filing_type for f in insider_reports)),
                    'filings': [self._filing_to_dict(f) for f in insider_reports]
                },
                'proxy_materials': {
                    'count': len(proxy_materials),
                    'types': list(set(f.filing_type for f in proxy_materials)),
                    'filings': [self._filing_to_dict(f) for f in proxy_materials]
                },
                'other': {
                    'count': len(other_filings),
                    'types': list(set(f.filing_type for f in other_filings)),
                    'filings': [self._filing_to_dict(f) for f in other_filings]
                }
            },
            'date_range': {
                'start': self.START_DATE,
                'end': self.END_DATE,
                'first_filing': min(filings, key=lambda f: f.filing_date).filing_date if filings else None,
                'last_filing': max(filings, key=lambda f: f.filing_date).filing_date if filings else None
            }
        }
        
        # Print summary
        logger.info(f"\n📊 FILING SUMMARY")
        logger.info(f"Total Filings: {analysis['total_filings']}")
        logger.info(f"\nBy Category:")
        logger.info(f"  Major Reports (10-K, 10-Q): {analysis['categories']['major_reports']['count']}")
        logger.info(f"  Current Reports (8-K): {analysis['categories']['current_reports']['count']}")
        logger.info(f"  Insider Reports (Forms 3/4/5): {analysis['categories']['insider_reports']['count']}")
        logger.info(f"  Proxy Materials: {analysis['categories']['proxy_materials']['count']}")
        logger.info(f"  Other: {analysis['categories']['other']['count']}")
        
        logger.info(f"\n📋 Filing Type Breakdown:")
        for filing_type, count in sorted(filing_type_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {filing_type}: {count}")
            
        return analysis
        
    def _filing_to_dict(self, filing: SECFiling) -> Dict[str, Any]:
        """Convert SECFiling to dictionary."""
        return {
            'accession_number': filing.accession_number,
            'filing_type': filing.filing_type,
            'filing_date': filing.filing_date,
            'report_date': filing.report_date,
            'primary_document': filing.primary_document,
            'filing_url': filing.filing_url,
            'document_url': filing.document_url,
            'size': filing.size,
            'is_xbrl': filing.is_xbrl
        }
        
    def save_filings(self, filings: List[SECFiling], analysis: Dict[str, Any]):
        """Save filings to disk."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save complete filing list (JSON)
        filings_json = self.output_dir / f"nike_2019_all_filings_{timestamp}.json"
        with open(filings_json, 'w', encoding='utf-8') as f:
            json.dump(
                [self._filing_to_dict(filing) for filing in filings],
                f,
                indent=2,
                default=str
            )
        logger.info(f"💾 Saved complete filing list: {filings_json}")
        
        # Save analysis (JSON)
        analysis_json = self.output_dir / f"nike_2019_analysis_{timestamp}.json"
        with open(analysis_json, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)
        logger.info(f"💾 Saved analysis: {analysis_json}")
        
        # Save human-readable summary (TXT)
        summary_txt = self.output_dir / f"nike_2019_summary_{timestamp}.txt"
        with open(summary_txt, 'w', encoding='utf-8') as f:
            f.write(self._generate_summary_report(filings, analysis))
        logger.info(f"💾 Saved summary report: {summary_txt}")
        
        # Save filing URLs (TXT) for easy access
        urls_txt = self.output_dir / f"nike_2019_filing_urls_{timestamp}.txt"
        with open(urls_txt, 'w', encoding='utf-8') as f:
            f.write(f"NIKE INC. 2019 SEC FILINGS - DIRECT URLS\n")
            f.write(f"={'=' * 78}\n\n")
            for filing in sorted(filings, key=lambda f: f.filing_date):
                f.write(f"{filing.filing_date} | {filing.filing_type:12s} | {filing.accession_number}\n")
                f.write(f"  Filing: {filing.filing_url}\n")
                f.write(f"  Document: {filing.document_url}\n\n")
        logger.info(f"💾 Saved filing URLs: {urls_txt}")
        
    def _generate_summary_report(self, filings: List[SECFiling], analysis: Dict[str, Any]) -> str:
        """Generate human-readable summary report."""
        
        report = f"""
{'=' * 80}
NIKE INC. - 2019 SEC FILINGS COMPLETE RETRIEVAL
{'=' * 80}

Company: Nike Inc.
CIK: {self.CIK}
Year: 2019
Date Range: {self.START_DATE} to {self.END_DATE}

Retrieved: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}

{'=' * 80}
SUMMARY STATISTICS
{'=' * 80}

Total Filings: {analysis['total_filings']}

First Filing: {analysis['date_range']['first_filing']}
Last Filing: {analysis['date_range']['last_filing']}

{'=' * 80}
FILING CATEGORIES
{'=' * 80}

Major Reports (10-K, 10-Q): {analysis['categories']['major_reports']['count']}
  Types: {', '.join(analysis['categories']['major_reports']['types'])}

Current Reports (8-K): {analysis['categories']['current_reports']['count']}

Insider Reports (Forms 3/4/5): {analysis['categories']['insider_reports']['count']}
  Types: {', '.join(analysis['categories']['insider_reports']['types'])}

Proxy Materials: {analysis['categories']['proxy_materials']['count']}
  Types: {', '.join(analysis['categories']['proxy_materials']['types']) if analysis['categories']['proxy_materials']['types'] else 'None'}

Other Filings: {analysis['categories']['other']['count']}
  Types: {', '.join(analysis['categories']['other']['types']) if analysis['categories']['other']['types'] else 'None'}

{'=' * 80}
FILING TYPE BREAKDOWN
{'=' * 80}

"""
        
        for filing_type, count in sorted(analysis['filing_type_counts'].items(), key=lambda x: -x[1]):
            report += f"{filing_type:15s} : {count:3d} filing(s)\n"
            
        report += f"""

{'=' * 80}
MAJOR REPORTS DETAIL
{'=' * 80}

"""
        
        for filing in sorted(analysis['categories']['major_reports']['filings'], key=lambda f: f['filing_date']):
            report += f"""
{filing['filing_date']} | {filing['filing_type']}
  Accession: {filing['accession_number']}
  Report Date: {filing['report_date'] or 'N/A'}
  Size: {filing['size']:,} bytes
  XBRL: {'Yes' if filing['is_xbrl'] else 'No'}
  URL: {filing['filing_url']}
"""
            
        report += f"""

{'=' * 80}
CURRENT REPORTS (8-K) - SUMMARY
{'=' * 80}

Total 8-K Filings: {analysis['categories']['current_reports']['count']}

"""
        
        for filing in sorted(analysis['categories']['current_reports']['filings'], key=lambda f: f['filing_date'])[:10]:
            report += f"{filing['filing_date']} | {filing['filing_type']} | {filing['accession_number']}\n"
            
        if analysis['categories']['current_reports']['count'] > 10:
            report += f"... and {analysis['categories']['current_reports']['count'] - 10} more\n"
            
        report += f"""

{'=' * 80}
INSIDER TRADING REPORTS - SUMMARY
{'=' * 80}

Total Insider Reports: {analysis['categories']['insider_reports']['count']}

"""
        
        for filing in sorted(analysis['categories']['insider_reports']['filings'], key=lambda f: f['filing_date'])[:10]:
            report += f"{filing['filing_date']} | {filing['filing_type']} | {filing['accession_number']}\n"
            
        if analysis['categories']['insider_reports']['count'] > 10:
            report += f"... and {analysis['categories']['insider_reports']['count'] - 10} more\n"
            
        report += f"""

{'=' * 80}
DATA QUALITY AND COMPLETENESS
{'=' * 80}

✓ All filings retrieved from official SEC EDGAR database
✓ Complete metadata including accession numbers and dates
✓ Direct URLs to SEC EDGAR for evidence verification
✓ XBRL status identified for structured data analysis
✓ Filing sizes recorded for processing planning

{'=' * 80}
NEXT STEPS
{'=' * 80}

1. Review complete filing list (JSON) for programmatic access
2. Use filing URLs for direct SEC EDGAR access
3. Process filings through JLAW forensic analysis pipeline
4. Generate evidence-backed violation reports
5. Create DOJ-style case documentation

{'=' * 80}
"""
        
        return report


async def main():
    """Main execution function."""
    
    print("=" * 80)
    print("NIKE INC. 2019 SEC FILINGS - COMPLETE FETCHER")
    print("=" * 80)
    print()
    
    fetcher = Nike2019FilingFetcher()
    
    try:
        # Fetch all filings
        filings = await fetcher.fetch_all_filings()
        
        if not filings:
            logger.error("❌ No filings found for the specified date range")
            return 1
            
        # Analyze filings
        analysis = fetcher.analyze_filings(filings)
        
        # Save results
        logger.info("\n" + "=" * 80)
        logger.info("SAVING RESULTS")
        logger.info("=" * 80)
        fetcher.save_filings(filings, analysis)
        
        # Final summary
        print("\n" + "=" * 80)
        print("✅ FETCH COMPLETE")
        print("=" * 80)
        print(f"Total Filings: {len(filings)}")
        print(f"Output Directory: {fetcher.output_dir}")
        print(f"\nFiles Generated:")
        print(f"  • Complete filing list (JSON)")
        print(f"  • Analysis breakdown (JSON)")
        print(f"  • Summary report (TXT)")
        print(f"  • Filing URLs (TXT)")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error during fetch: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

