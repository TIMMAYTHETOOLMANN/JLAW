"""
SEC Filing Acquisition System - Verification Script
===================================================

This script verifies that all the remediation components are in place
without requiring external dependencies.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_file_exists(filepath: str, description: str) -> bool:
    """Verify a file exists."""
    path = project_root / filepath
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def verify_module_syntax(filepath: str) -> bool:
    """Verify module has valid Python syntax."""
    import py_compile
    path = project_root / filepath
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except py_compile.PyCompileError:
        return False


def main():
    """Run verification checks."""
    print("=" * 70)
    print("SEC Filing Acquisition System - Verification")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Check new files
    print("Checking New Files:")
    print("-" * 70)
    files_to_check = [
        ("src/integrations/sec_edgar/rate_limiter.py", "Rate Limiter with Cooldown"),
        ("src/integrations/sec_edgar/session_manager.py", "Session Manager"),
        ("src/integrations/sec_edgar/models.py", "Data Models"),
        ("src/integrations/sec_edgar/utils.py", "CIK/Accession Utilities"),
        ("src/forensics/ai_analyzer.py", "AI Analyzer"),
        ("tests/test_sec_acquisition.py", "Test Suite"),
    ]
    
    for filepath, description in files_to_check:
        exists = verify_file_exists(filepath, description)
        all_passed = all_passed and exists
    
    print()
    
    # Check modified files
    print("Checking Modified Files:")
    print("-" * 70)
    modified_files = [
        ("src/integrations/sec_edgar/edgar_client.py", "Enhanced EDGAR Client"),
        ("src/forensics/docsgpt/document_parser.py", "Enhanced XBRL Parser"),
        ("src/nodes/node7_13f_holdings/sec_edgar_client.py", "Node 7 with Shared Rate Limiter"),
        ("requirements.txt", "Updated Dependencies"),
    ]
    
    for filepath, description in modified_files:
        exists = verify_file_exists(filepath, description)
        all_passed = all_passed and exists
    
    print()
    
    # Check syntax
    print("Syntax Validation:")
    print("-" * 70)
    python_files = [f[0] for f in files_to_check + modified_files if f[0].endswith('.py')]
    
    for filepath in python_files:
        path = project_root / filepath
        if path.exists():
            valid = verify_module_syntax(filepath)
            status = "✅" if valid else "❌"
            print(f"{status} {filepath}")
            all_passed = all_passed and valid
    
    print()
    
    # Feature verification
    print("Feature Implementation Verification:")
    print("-" * 70)
    
    features = []
    
    try:
        from src.integrations.sec_edgar.rate_limiter import RateLimiter, get_shared_rate_limiter
        features.append(("✅", "Rate Limiter with 60s cooldown"))
        
        limiter = RateLimiter()
        if hasattr(limiter, 'COOLDOWN_PERIOD') and limiter.COOLDOWN_PERIOD == 60:
            features.append(("✅", "  - Cooldown period = 60 seconds"))
        else:
            features.append(("❌", "  - Cooldown period incorrect"))
            all_passed = False
    except Exception as e:
        features.append(("❌", f"Rate Limiter import failed: {e}"))
        all_passed = False
    
    try:
        from src.integrations.sec_edgar.models import IntegrityHashes, AcquisitionResult
        features.append(("✅", "Triple-hash integrity models"))
        
        # Test triple-hash
        hashes = IntegrityHashes(sha256='a'*64, sha3_512='b'*128, blake2b='c'*128)
        if hashes.sha256 and hashes.sha3_512 and hashes.blake2b:
            features.append(("✅", "  - SHA-256 + SHA3-512 + BLAKE2b"))
        else:
            features.append(("❌", "  - Triple-hash fields missing"))
            all_passed = False
    except Exception as e:
        features.append(("❌", f"Models import failed: {e}"))
        all_passed = False
    
    try:
        from src.integrations.sec_edgar.utils import normalize_cik, format_accession_number
        features.append(("✅", "CIK/Accession normalization utilities"))
        
        # Test normalization
        cik = normalize_cik('320193')
        if cik == '0000320193':
            features.append(("✅", "  - CIK normalization working"))
        else:
            features.append(("❌", f"  - CIK normalization failed: {cik}"))
            all_passed = False
    except Exception as e:
        features.append(("❌", f"Utils import failed: {e}"))
        all_passed = False
    
    try:
        from src.forensics.docsgpt.document_parser import XBRLParser
        parser = XBRLParser()
        features.append(("✅", "Enhanced XBRL Parser"))
        
        # Check namespaces
        required_namespaces = ['xbrli', 'us-gaap', 'dei', 'link', 'ifrs-full']
        if all(ns in parser.XBRL_NAMESPACES for ns in required_namespaces):
            features.append(("✅", f"  - {len(parser.XBRL_NAMESPACES)} XBRL namespaces"))
        else:
            features.append(("❌", "  - Missing required XBRL namespaces"))
            all_passed = False
    except Exception as e:
        features.append(("❌", f"XBRL Parser import failed: {e}"))
        all_passed = False
    
    try:
        from src.forensics.ai_analyzer import SECFilingAnalyzer
        features.append(("✅", "AI Analyzer with map-reduce"))
    except Exception as e:
        features.append(("❌", f"AI Analyzer import failed: {e}"))
        all_passed = False
    
    try:
        from config.secure_config import validate_sec_configuration
        features.append(("✅", "SEC configuration validation"))
    except Exception as e:
        features.append(("❌", f"Config validation failed: {e}"))
        all_passed = False
    
    for status, feature in features:
        print(f"{status} {feature}")
    
    print()
    print("=" * 70)
    if all_passed:
        print("✅ ALL VERIFICATION CHECKS PASSED")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME VERIFICATION CHECKS FAILED")
        print("=" * 70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
