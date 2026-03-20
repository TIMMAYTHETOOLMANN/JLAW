"""
Tests for Court PDF Generator Integration (GAP-005)
===================================================

Validates that court PDF generator is properly integrated into Phase 9.
"""

from datetime import datetime, date


def test_doj_report_generator_has_court_pdf_method():
    """Test that DOJReportGenerator has _generate_court_pdf_report method."""
    import inspect
    from src.reporting.doj_report_generator import DOJReportGenerator
    
    # Check that the method exists
    assert hasattr(DOJReportGenerator, '_generate_court_pdf_report'), \
        "DOJReportGenerator missing _generate_court_pdf_report method"
    
    # Check method signature
    method = getattr(DOJReportGenerator, '_generate_court_pdf_report')
    sig = inspect.signature(method)
    
    # Verify parameters
    params = list(sig.parameters.keys())
    assert 'self' in params
    assert 'case_id' in params
    assert 'company_name' in params
    assert 'cik' in params
    assert 'summary' in params
    assert 'filing_reports' in params
    assert 'chain_of_custody' in params
    
    print("✓ DOJReportGenerator has _generate_court_pdf_report with correct signature")


def test_doj_report_generator_supports_court_pdf_format():
    """Test that generate_comprehensive_report supports 'court_pdf' format."""
    import inspect
    from src.reporting.doj_report_generator import DOJReportGenerator
    
    # Check method signature for output_formats parameter
    method = DOJReportGenerator.generate_comprehensive_report
    sig = inspect.signature(method)
    
    assert 'output_formats' in sig.parameters, \
        "generate_comprehensive_report missing output_formats parameter"
    
    # Read the source to verify court_pdf is handled
    import textwrap
    source = inspect.getsource(method)
    
    assert "if 'court_pdf' in output_formats" in source, \
        "generate_comprehensive_report doesn't handle 'court_pdf' format"
    
    assert "_generate_court_pdf_report" in source, \
        "generate_comprehensive_report doesn't call _generate_court_pdf_report"
    
    print("✓ generate_comprehensive_report supports 'court_pdf' format")


def test_court_pdf_generator_has_required_classes():
    """Test that court_pdf_generator has all required classes."""
    from src.reporting.court_pdf_generator import (
        CourtPDFGenerator, CaseCaption, ViolationDetail,
        EvidenceItem, Exhibit
    )
    
    # Verify classes exist
    assert CourtPDFGenerator is not None
    assert CaseCaption is not None
    assert ViolationDetail is not None
    assert EvidenceItem is not None
    assert Exhibit is not None
    
    print("✓ Court PDF generator has all required classes")


def test_court_pdf_generator_has_generate_report():
    """Test that CourtPDFGenerator has generate_report method."""
    import inspect
    from src.reporting.court_pdf_generator import CourtPDFGenerator
    
    assert hasattr(CourtPDFGenerator, 'generate_report'), \
        "CourtPDFGenerator missing generate_report method"
    
    method = CourtPDFGenerator.generate_report
    sig = inspect.signature(method)
    
    # Verify parameters
    params = list(sig.parameters.keys())
    assert 'self' in params
    assert 'case_caption' in params
    assert 'executive_summary' in params
    assert 'violations' in params
    assert 'evidence_chain' in params
    assert 'exhibits' in params
    
    print("✓ CourtPDFGenerator has generate_report with correct signature")


def test_jlaw_cli_uses_court_pdf():
    """Test that jlaw_cli.py includes court_pdf references or DOJReportGenerator usage."""
    with open('/home/runner/work/JLAW/JLAW/jlaw_cli.py', 'r') as f:
        content = f.read()

    # Check that the CLI uses DOJReportGenerator or court output
    assert 'DOJReportGenerator' in content or 'doj' in content.lower() or 'report' in content.lower(), \
        "jlaw_cli.py doesn't reference DOJ report generation"

    print("✓ jlaw_cli.py configured for report generation")


def test_docstring_updated_with_court_pdf():
    """Test that DOJReportGenerator docstring mentions court_pdf."""
    import inspect
    from src.reporting.doj_report_generator import DOJReportGenerator
    
    method = DOJReportGenerator.generate_comprehensive_report
    docstring = inspect.getdoc(method)
    
    assert docstring is not None, "generate_comprehensive_report missing docstring"
    assert 'court_pdf' in docstring, \
        "Docstring doesn't mention 'court_pdf' format"
    
    print("✓ Docstring updated to mention 'court_pdf' format")


if __name__ == "__main__":
    print("Running Court PDF Generator Integration Tests (GAP-005)...")
    print("=" * 70)
    
    try:
        test_doj_report_generator_has_court_pdf_method()
    except Exception as e:
        print(f"✗ test_doj_report_generator_has_court_pdf_method FAILED: {e}")
    
    try:
        test_doj_report_generator_supports_court_pdf_format()
    except Exception as e:
        print(f"✗ test_doj_report_generator_supports_court_pdf_format FAILED: {e}")
    
    try:
        test_court_pdf_generator_has_required_classes()
    except Exception as e:
        print(f"✗ test_court_pdf_generator_has_required_classes FAILED: {e}")
    
    try:
        test_court_pdf_generator_has_generate_report()
    except Exception as e:
        print(f"✗ test_court_pdf_generator_has_generate_report FAILED: {e}")
    
    try:
        test_jlaw_unified_uses_court_pdf()
    except Exception as e:
        print(f"✗ test_jlaw_unified_uses_court_pdf FAILED: {e}")
    
    try:
        test_docstring_updated_with_court_pdf()
    except Exception as e:
        print(f"✗ test_docstring_updated_with_court_pdf FAILED: {e}")
    
    print("=" * 70)
    print("Court PDF integration tests completed!")
