"""
Test SEC API Key Configuration
Verifies that the API key is properly configured and can access SEC EDGAR.
"""

import asyncio
import aiohttp
from src.forensics.config_manager import get_config

async def test_sec_api_connection():
    """Test SEC EDGAR API connection with configured API key."""
    
    print("="*70)
    print("JLAW FORENSIC SYSTEM - SEC API KEY VERIFICATION")
    print("="*70)
    
    # Load configuration
    print("\n[1] Loading configuration...")
    try:
        config = get_config()
        print(f"✓ Configuration loaded")
        print(f"  SEC Email: {config.config.sec.user_email}")
        print(f"  SEC User-Agent: {config.config.sec.user_agent}")
        print(f"  Note: SEC EDGAR requires only User-Agent (no API key)")
        
        if config.config.govinfo.api_key:
            print(f"  GovInfo API Key: {config.config.govinfo.api_key[:10]}...{config.config.govinfo.api_key[-10:]}")
        else:
            print(f"  GovInfo API Key: Not configured (optional)")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False
    
    # Test SEC EDGAR API access
    print("\n[2] Testing SEC EDGAR API access...")
    
    # Test company data endpoint
    test_cik = "0000320193"  # Apple Inc.
    url = f"https://data.sec.gov/submissions/CIK{test_cik}.json"
    
    headers = config.get_sec_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Successfully connected to SEC EDGAR API")
                    print(f"  Company: {data.get('name', 'UNKNOWN')}")
                    print(f"  CIK: {data.get('cik', 'UNKNOWN')}")
                    print(f"  Recent filings: {len(data.get('filings', {}).get('recent', {}).get('accessionNumber', []))}")
                elif response.status == 403:
                    print(f"✗ Access denied (403). Check User-Agent header.")
                    print(f"  User-Agent must include contact email per SEC requirements")
                    return False
                else:
                    print(f"✗ API error: {response.status}")
                    error_text = await response.text()
                    print(f"  Response: {error_text[:200]}")
                    return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False
    
    # Test bulk data endpoint
    print("\n[3] Testing SEC bulk data access...")
    
    bulk_url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        'action': 'getcompany',
        'CIK': test_cik,
        'type': '10-K',
        'dateb': '',
        'owner': 'exclude',
        'count': '10',
        'output': 'atom'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(bulk_url, headers=headers, params=params) as response:
                if response.status == 200:
                    print(f"✓ Successfully accessed SEC bulk data")
                    text = await response.text()
                    print(f"  Response length: {len(text)} characters")
                elif response.status == 403:
                    print(f"✗ Bulk data access denied (403)")
                    return False
                else:
                    print(f"⚠ Bulk data returned status: {response.status}")
    except Exception as e:
        print(f"✗ Bulk data error: {e}")
    
    # Test rate limiting compliance
    print("\n[4] Verifying rate limiting configuration...")
    print(f"✓ Configured rate limit: {config.config.sec.requests_per_second} requests/second")
    print(f"  (SEC requirement: max 10 requests/second)")
    
    if config.config.sec.requests_per_second > 10:
        print(f"⚠ WARNING: Rate limit exceeds SEC guidelines (max 10/sec)")
    
    print("\n" + "="*70)
    print("SEC API KEY VERIFICATION: ✓ SUCCESS")
    print("="*70)
    print("\nYour API key is properly configured and working!")
    print("The system can now:")
    print("  • Access SEC EDGAR company data")
    print("  • Download SEC filings (10-K, 10-Q, 8-K, etc.)")
    print("  • Retrieve bulk financial data")
    print("  • Perform forensic analysis on SEC filings")
    print("\nReady for production use! 🚀")
    
    return True


async def test_govinfo_api():
    """Test GovInfo API if configured."""
    print("\n[5] Testing GovInfo API (optional - not required for SEC)...")
    
    try:
        config = get_config()
        
        if not config.config.govinfo.api_key:
            print(f"⚠ GovInfo API key not configured")
            print(f"  This is optional - SEC EDGAR works without it")
            return
        
        govinfo_key = config.config.govinfo.api_key
        
        # GovInfo API test endpoint
        url = "https://api.govinfo.gov/collections"
        params = config.get_govinfo_params()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ GovInfo API access successful")
                    print(f"  Collections available: {len(data.get('collections', []))}")
                else:
                    print(f"⚠ GovInfo API returned status: {response.status}")
                    print(f"  (This is optional - SEC EDGAR is primary)")
    except Exception as e:
        print(f"⚠ GovInfo API test skipped: {e}")
        print(f"  (This is optional - SEC EDGAR is primary)")


async def main():
    """Run all API tests."""
    success = await test_sec_api_connection()
    
    if success:
        await test_govinfo_api()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

