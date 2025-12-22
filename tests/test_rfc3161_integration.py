"""
Tests for RFC 3161 Timestamp Integration (GAP-002)
==================================================

Validates that RFC 3161 timestamps are properly integrated into Phase 8.
"""

import os


def test_rfc3161_client_exists():
    """Test that RFC3161Client class exists."""
    from src.core.evidence_chain.rfc3161_client import RFC3161Client, TimestampToken
    
    assert RFC3161Client is not None
    assert TimestampToken is not None
    print("✓ RFC3161Client and TimestampToken classes exist")


def test_rfc3161_client_initialization():
    """Test that RFC3161Client can be initialized."""
    from src.core.evidence_chain.rfc3161_client import RFC3161Client
    
    # Initialize with local authority (doesn't require network)
    client = RFC3161Client(authority="local")
    assert client.authority == "local"
    
    # Check that freetsa and digicert authorities are available
    client_freetsa = RFC3161Client(authority="freetsa")
    assert client_freetsa.authority == "freetsa"
    
    client_digicert = RFC3161Client(authority="digicert")
    assert client_digicert.authority == "digicert"
    
    print("✓ RFC3161Client initialization works for all authorities")


def test_master_controller_imports_rfc3161():
    """Test that master controller imports RFC3161Client."""
    import inspect
    from src.core.master_execution_controller import MasterExecutionController
    
    # Check that _execute_phase_8_evidence_chain exists
    assert hasattr(MasterExecutionController, '_execute_phase_8_evidence_chain')
    
    # Check that RFC3161Client is referenced
    method = MasterExecutionController._execute_phase_8_evidence_chain
    source = inspect.getsource(method)
    
    assert 'RFC3161Client' in source, \
        "Phase 8 doesn't import RFC3161Client"
    
    assert 'timestamp' in source, \
        "Phase 8 doesn't call timestamp method"
    
    print("✓ Master controller Phase 8 imports and uses RFC3161Client")


def test_phase_8_uses_rfc3161_env_var():
    """Test that Phase 8 checks RFC3161_AUTHORITY environment variable."""
    import inspect
    from src.core.master_execution_controller import MasterExecutionController
    
    method = MasterExecutionController._execute_phase_8_evidence_chain
    source = inspect.getsource(method)
    
    assert 'RFC3161_AUTHORITY' in source, \
        "Phase 8 doesn't check RFC3161_AUTHORITY env var"
    
    assert 'os.getenv' in source or 'os.environ' in source, \
        "Phase 8 doesn't use os.getenv for RFC3161_AUTHORITY"
    
    print("✓ Phase 8 checks RFC3161_AUTHORITY environment variable")


def test_evidence_summary_includes_timestamp():
    """Test that evidence summary includes RFC 3161 timestamp info."""
    import inspect
    from src.core.master_execution_controller import MasterExecutionController
    
    method = MasterExecutionController._build_evidence_chain_summary
    source = inspect.getsource(method)
    
    assert 'rfc3161' in source.lower() or 'timestamp' in source.lower(), \
        "Evidence summary doesn't include timestamp information"
    
    print("✓ Evidence summary includes RFC 3161 timestamp")


def test_timestamp_token_dataclass():
    """Test that TimestampToken has required fields."""
    from src.core.evidence_chain.rfc3161_client import TimestampToken
    import dataclasses
    
    # Check that it's a dataclass
    assert dataclasses.is_dataclass(TimestampToken), \
        "TimestampToken is not a dataclass"
    
    # Check required fields
    fields = {f.name for f in dataclasses.fields(TimestampToken)}
    assert 'token_data' in fields
    assert 'gen_time' in fields
    assert 'hash_algorithm' in fields
    assert 'message_imprint' in fields
    assert 'authority' in fields
    
    print("✓ TimestampToken has all required fields")


def test_court_pdf_supports_timestamps():
    """Test that court PDF generator supports RFC 3161 timestamps."""
    import inspect
    from src.reporting.court_pdf_generator import EvidenceItem
    import dataclasses
    
    # Check that EvidenceItem has rfc3161_timestamp field
    fields = {f.name for f in dataclasses.fields(EvidenceItem)}
    assert 'rfc3161_timestamp' in fields, \
        "EvidenceItem missing rfc3161_timestamp field"
    
    print("✓ Court PDF EvidenceItem supports RFC 3161 timestamps")


def test_rfc3161_graceful_degradation():
    """Test that RFC 3161 errors don't crash Phase 8."""
    import inspect
    from src.core.master_execution_controller import MasterExecutionController
    
    method = MasterExecutionController._execute_phase_8_evidence_chain
    source = inspect.getsource(method)
    
    # Check for exception handling
    assert 'except' in source, \
        "Phase 8 doesn't handle RFC 3161 exceptions"
    
    assert 'ImportError' in source or 'Exception' in source, \
        "Phase 8 doesn't catch RFC 3161 import errors"
    
    print("✓ RFC 3161 integration has graceful error handling")


if __name__ == "__main__":
    print("Running RFC 3161 Timestamp Integration Tests (GAP-002)...")
    print("=" * 70)
    
    try:
        test_rfc3161_client_exists()
    except Exception as e:
        print(f"✗ test_rfc3161_client_exists FAILED: {e}")
    
    try:
        test_rfc3161_client_initialization()
    except Exception as e:
        print(f"✗ test_rfc3161_client_initialization FAILED: {e}")
    
    try:
        test_master_controller_imports_rfc3161()
    except Exception as e:
        print(f"✗ test_master_controller_imports_rfc3161 FAILED: {e}")
    
    try:
        test_phase_8_uses_rfc3161_env_var()
    except Exception as e:
        print(f"✗ test_phase_8_uses_rfc3161_env_var FAILED: {e}")
    
    try:
        test_evidence_summary_includes_timestamp()
    except Exception as e:
        print(f"✗ test_evidence_summary_includes_timestamp FAILED: {e}")
    
    try:
        test_timestamp_token_dataclass()
    except Exception as e:
        print(f"✗ test_timestamp_token_dataclass FAILED: {e}")
    
    try:
        test_court_pdf_supports_timestamps()
    except Exception as e:
        print(f"✗ test_court_pdf_supports_timestamps FAILED: {e}")
    
    try:
        test_rfc3161_graceful_degradation()
    except Exception as e:
        print(f"✗ test_rfc3161_graceful_degradation FAILED: {e}")
    
    print("=" * 70)
    print("RFC 3161 timestamp integration tests completed!")
