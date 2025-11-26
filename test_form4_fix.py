"""
Quick test to verify Form 4 parsing fix
"""

import asyncio
import sys
sys.path.insert(0, 'C:/Users/timot/IdeaProjects/JLAW')

from src.forensics.insider_form4_analyzer import InsiderForm4Analyzer

async def test_form4_fix():
    """Test the Form 4 XML extraction fix."""
    
    analyzer = InsiderForm4Analyzer(user_agent="JARVIS-NEXUS contact@nits-secops.org")
    
    # Test with the problem URL from the production run
    test_url = "https://www.sec.gov/Archives/edgar/data/320187/000112760219035995/xslF345X03/form4.xml"
    test_date = "2019-12-31"
    
    print(f"Testing Form 4 analyzer fix...")
    print(f"URL: {test_url}")
    print(f"Filing Date: {test_date}\n")
    
    violations = await analyzer.analyze_form4(
        xml_url=test_url,
        viewer_url=None,
        filing_date_str=test_date
    )
    
    print(f"\n✓ SUCCESS!")
    print(f"Found {len(violations)} violations")
    
    if violations:
        for v in violations:
            print(f"\n  Type: {v.type}")
            print(f"  Description: {v.description}")
            print(f"  Quote: {v.exact_quote}")
    else:
        print("  (No violations in this specific filing - which is normal)")
    
    return len(violations)

if __name__ == "__main__":
    result = asyncio.run(test_form4_fix())
    print(f"\n{'='*60}")
    print(f"Test complete. Violations detected: {result}")
    print(f"{'='*60}")

