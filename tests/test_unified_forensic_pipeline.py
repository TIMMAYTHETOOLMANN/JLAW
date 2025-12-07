"""
Test Unified Forensic Pipeline Integration
==========================================

Tests the 13-phase unified forensic pipeline with mock data.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.forensics.unified_forensic_pipeline import UnifiedForensicPipeline
from src.forensics.forensic_context import ForensicContext


@pytest.mark.asyncio
async def test_pipeline_initialization():
    """Test that the pipeline initializes correctly."""
    pipeline = UnifiedForensicPipeline()
    assert pipeline is not None
    assert pipeline.config is not None


@pytest.mark.asyncio
async def test_pipeline_execution_minimal():
    """Test pipeline execution with minimal mock data."""
    pipeline = UnifiedForensicPipeline()
    
    # Create a minimal context for testing
    context = ForensicContext(
        company_name="Test Company",
        cik="0000000001",
        analysis_period_start="2019-01-01",
        analysis_period_end="2019-12-31"
    )
    
    # Test that each phase runs without crashing (even with no data)
    try:
        # Phase 2: DocsGPT parsing
        context = await pipeline._phase_02_docsgpt_parsing(context)
        assert context is not None
        
        # Phase 3: Agent scraping
        context = await pipeline._phase_03_agent_scraping(context)
        assert context is not None
        assert 'openai_available' in context.agent_findings
        
        # Phase 4: Quantitative forensics
        context = await pipeline._phase_04_quantitative_forensics(context)
        assert context is not None
        
        # Phase 7: Linguistic deception
        context = await pipeline._phase_07_linguistic_deception(context)
        assert context is not None
        assert 'hedging_score' in context.deception_metrics
        
        # Phase 8: Temporal analysis
        context = await pipeline._phase_08_temporal_analysis(context)
        assert context is not None
        
        # Phase 10: ML fraud detection
        context = await pipeline._phase_10_ml_fraud_detection(context)
        assert context is not None
        assert 'ensemble_score' in context.ml_fraud_scores
        
        print("✅ All phases executed successfully")
        
    except Exception as e:
        pytest.fail(f"Pipeline phase failed: {e}")


@pytest.mark.asyncio
async def test_context_propagation():
    """Test that context is properly propagated through phases."""
    pipeline = UnifiedForensicPipeline()
    
    context = ForensicContext(
        company_name="Test Company",
        cik="0000000001",
        analysis_period_start="2019-01-01",
        analysis_period_end="2019-12-31"
    )
    
    # Add mock filing
    from src.forensics.forensic_context import SECFiling
    
    filing = SECFiling(
        accession_number="0000000001-19-000001",
        filing_type="10-K",
        filing_date="2019-03-15",
        cik="0000000001",
        company_name="Test Company",
        document_url="https://example.com/filing",
        raw_content="This is a test filing content with some financial data."
    )
    context.filings.append(filing)
    
    # Run Phase 2 (parsing)
    context = await pipeline._phase_02_docsgpt_parsing(context)
    
    # Verify parsed documents were created
    assert len(context.parsed_documents) > 0, "No parsed documents created"
    assert context.parsed_documents[0].doc_id == filing.accession_number
    
    print(f"✅ Context propagation working: {len(context.parsed_documents)} documents parsed")


@pytest.mark.asyncio
async def test_config_loading():
    """Test that configuration is loaded properly."""
    pipeline = UnifiedForensicPipeline()
    
    # Check that config has required sections
    assert hasattr(pipeline.config, 'config')
    
    # Check key configuration sections exist
    config = pipeline.config.config
    assert hasattr(config, 'docsgpt') or 'docsgpt' in dir(config)
    assert hasattr(config, 'agents') or 'agents' in dir(config)
    
    print("✅ Configuration loaded successfully")


def test_forensic_context_structure():
    """Test that ForensicContext has all required fields."""
    context = ForensicContext(
        company_name="Test",
        cik="0000000001",
        analysis_period_start="2019-01-01",
        analysis_period_end="2019-12-31"
    )
    
    # Verify all expected fields exist
    assert hasattr(context, 'filings')
    assert hasattr(context, 'parsed_documents')
    assert hasattr(context, 'chunks')
    assert hasattr(context, 'agent_findings')
    assert hasattr(context, 'violations')
    assert hasattr(context, 'contradictions')
    assert hasattr(context, 'criminal_referrals')
    assert hasattr(context, 'statute_mappings')
    assert hasattr(context, 'beneish_score')
    assert hasattr(context, 'altman_z_score')
    assert hasattr(context, 'fraud_probability')
    
    # Test to_dict method
    context_dict = context.to_dict()
    assert 'company_name' in context_dict
    assert 'cik' in context_dict
    assert 'filings_count' in context_dict
    
    print("✅ ForensicContext structure validated")


if __name__ == "__main__":
    # Run tests manually
    print("Running Unified Forensic Pipeline Tests\n")
    
    print("Test 1: Pipeline Initialization")
    asyncio.run(test_pipeline_initialization())
    
    print("\nTest 2: Pipeline Execution")
    asyncio.run(test_pipeline_execution_minimal())
    
    print("\nTest 3: Context Propagation")
    asyncio.run(test_context_propagation())
    
    print("\nTest 4: Config Loading")
    asyncio.run(test_config_loading())
    
    print("\nTest 5: Context Structure")
    test_forensic_context_structure()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
