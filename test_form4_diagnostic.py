"""
Test single Form 4 analysis with diagnostics
"""

import asyncio
import sys
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.insider_form4_analyzer import InsiderForm4Analyzer

async def test_form4():
    """Test single Nike Form 4 from 2019."""
    
    print("="*80)
    print("FORM 4 DIAGNOSTIC TEST")
    print("="*80)
    
    analyzer = InsiderForm4Analyzer(user_agent="NITS Recon Unit contact@nits-secops.org")
    
    # Test with a known Form 4 from Nike 2019
    # From benchmark: Filing 2019-01-22 (4 days late)
    # CORRECTED URL: Use root edgardoc.xml, not xslF345X03 subfolder
    test_form4 = {
        'xml_url': 'https://www.sec.gov/Archives/edgar/data/320187/000032018719000015/edgardoc.xml',
        'viewer_url': 'https://www.sec.gov/cgi-bin/viewer?action=view&cik=320187&accession_number=0000320187-19-000015&xbrl_type=v',
        'filing_date': '2019-01-22'  # This should be 4 days late according to benchmark
    }
    
    print(f"\nTesting Form 4:")
    print(f"  URL: {test_form4['xml_url']}")
    print(f"  Filing Date: {test_form4['filing_date']}")
    print(f"  Expected: Late filing violation (4 days)")
    print()
    
    try:
        violations = await analyzer.analyze_form4(
            test_form4['xml_url'],
            test_form4['viewer_url'],
            test_form4['filing_date']
        )
        
        print(f"\n" + "="*80)
        print(f"RESULTS: {len(violations)} violations found")
        print("="*80)
        
        if violations:
            for i, v in enumerate(violations, 1):
                print(f"\n{i}. {v.type}")
                print(f"   Severity: {v.severity}")
                print(f"   Description: {v.description}")
                print(f"   Quote: {v.exact_quote}")
                if v.estimated_damages:
                    print(f"   Damages: ${v.estimated_damages:,}")
        else:
            print("\n[FAIL] No violations detected - check diagnostics above")
        
        return len(violations) > 0
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    
    result = asyncio.run(test_form4())
    exit(0 if result else 1)

