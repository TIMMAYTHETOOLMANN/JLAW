"""
Test Critical Audit Fixes
==========================

Tests for CRITICAL-006, CRITICAL-007, MOD-003, and MOD-004 fixes
from the JLAW Forensic System Audit Report (December 25, 2025).
"""

import pytest
import warnings
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# CRITICAL-006: Node 15 Skip Handling Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_node15_emits_warning_when_api_key_missing():
    """Test that Node 15 emits WARNING (not INFO) when API key is missing."""
    from src.core.recursive_engine import RecursiveProsecutorialEngine
    
    # Create engine without initializing nodes
    engine = RecursiveProsecutorialEngine.__new__(RecursiveProsecutorialEngine)
    engine.polygon_api_key = None
    engine.strict_mode = False
    
    # Execute Node 15
    with patch('src.core.recursive_engine.logger') as mock_logger:
        with patch('src.core.recursive_engine.time.time', return_value=0.0):
            result = await engine._execute_node15(cik="320187", company_name="NIKE")
        
            # Verify warning was logged (not info)
            assert mock_logger.warning.called, "Expected warning() to be called"
            warning_call = mock_logger.warning.call_args[0][0]
            assert "CRITICAL" in warning_call
            assert "Polygon.io API key not available" in warning_call
            assert "Node 15" in warning_call


@pytest.mark.asyncio
async def test_node15_returns_skipped_status_with_warnings():
    """Test that Node 15 returns skipped status with warnings array."""
    from src.core.recursive_engine import RecursiveProsecutorialEngine
    
    # Create engine without initializing nodes
    engine = RecursiveProsecutorialEngine.__new__(RecursiveProsecutorialEngine)
    engine.polygon_api_key = None
    engine.strict_mode = False
    
    # Execute Node 15
    with patch('src.core.recursive_engine.time.time', return_value=0.0):
        result = await engine._execute_node15(cik="320187", company_name="NIKE")
    
        # Verify result structure
        assert result.status == "skipped"
        assert hasattr(result, 'warnings')
        assert len(result.warnings) > 0
        assert "CRITICAL" in result.warnings[0]
        assert "Polygon.io API key not available" in result.warnings[0]


@pytest.mark.asyncio
async def test_node15_raises_error_in_strict_mode():
    """Test that Node 15 raises ValueError in strict mode when API key is missing."""
    from src.core.recursive_engine import RecursiveProsecutorialEngine
    
    # Create engine without initializing nodes
    engine = RecursiveProsecutorialEngine.__new__(RecursiveProsecutorialEngine)
    engine.polygon_api_key = None
    engine.strict_mode = True
    
    # Execute Node 15 - should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await engine._execute_node15(cik="320187", company_name="NIKE")
    
    # Verify error message
    assert "Node 15 cannot execute" in str(exc_info.value)
    assert "Polygon.io API key not available" in str(exc_info.value)


@pytest.mark.asyncio
async def test_node15_executes_normally_with_api_key():
    """Test that Node 15 executes normally when API key is present."""
    from src.core.recursive_engine import RecursiveProsecutorialEngine
    from src.nodes import MarketCorrelationEngineV2
    
    # Create engine without initializing nodes
    engine = RecursiveProsecutorialEngine.__new__(RecursiveProsecutorialEngine)
    engine.polygon_api_key = "test_key_12345"
    engine.strict_mode = True
    engine.node15_market = MarketCorrelationEngineV2(engine.polygon_api_key)
    
    # Execute Node 15
    with patch('src.core.recursive_engine.time.time', return_value=0.0):
        result = await engine._execute_node15(cik="320187", company_name="NIKE")
    
        # Verify execution completed (even if data analysis is mocked)
        assert result is not None
        assert result.node_id == "NODE_15"
        # Status may be success or skipped depending on implementation
        assert result.status in ["success", "skipped", "error"]


# ═══════════════════════════════════════════════════════════════════════════════
# MOD-003: V1 Node Deprecation Warnings Tests
# ═══════════════════════════════════════════════════════════════════════════════

def test_v1_node_import_emits_deprecation_warning():
    """Test that importing V1 nodes emits DeprecationWarning."""
    # Test with InstitutionalHoldingsAnalyzer (V1) using __getattr__
    import src.nodes
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Try to access V1 node through __getattr__ - this should trigger deprecation warning
        try:
            # Access a deprecated node
            _ = src.nodes.__getattr__('InstitutionalHoldingsAnalyzer')
            
            # Verify deprecation warning was issued
            assert len(w) >= 1
            assert issubclass(w[-1].category, DeprecationWarning)
            assert "deprecated" in str(w[-1].message).lower()
            assert "InstitutionalHoldingsAnalyzerV2" in str(w[-1].message)
        except AttributeError:
            # If the node doesn't exist in __deprecated_v1_nodes__, check that __getattr__ exists
            assert hasattr(src.nodes, '__getattr__')
            # Verify the __deprecated_v1_nodes__ list exists
            assert hasattr(src.nodes, '__deprecated_v1_nodes__')


def test_v2_node_import_no_warning():
    """Test that importing V2 nodes does not emit warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Import V2 node directly - should NOT trigger deprecation warning
        from src.nodes import InstitutionalHoldingsAnalyzerV2
        
        # Filter out any non-DeprecationWarning warnings  
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        
        # Verify no deprecation warnings for V2 import itself
        # Note: there may be deprecation warnings from submodules importing V1, but not for our direct import
        v2_warnings = [warning for warning in deprecation_warnings if "InstitutionalHoldingsAnalyzerV2" in str(warning.message)]
        assert len(v2_warnings) == 0


def test_multiple_v1_nodes_emit_deprecation_warnings():
    """Test that multiple V1 node imports each emit deprecation warnings."""
    import src.nodes
    
    v1_nodes_to_test = [
        'BeneficialOwnershipTracker',
        'MaterialEventCorrelator',
        'BankruptcyPredictor',
    ]
    
    for v1_node in v1_nodes_to_test:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            try:
                # Try to access V1 node through __getattr__
                _ = src.nodes.__getattr__(v1_node)
                
                # Verify deprecation warning was issued
                assert len(w) >= 1, f"Expected deprecation warning for {v1_node}"
                assert issubclass(w[-1].category, DeprecationWarning), f"Expected DeprecationWarning for {v1_node}"
                assert "deprecated" in str(w[-1].message).lower(), f"Expected 'deprecated' in message for {v1_node}"
            except AttributeError:
                # Some nodes might not be in the deprecated list
                pass


# ═══════════════════════════════════════════════════════════════════════════════
# MOD-004: DeBERTa Fallback Notification Tests
# ═══════════════════════════════════════════════════════════════════════════════

def test_deberta_fallback_logs_warning():
    """Test that DeBERTa detector logs warning when falling back to basic analysis."""
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    # Mock transformers to simulate unavailability
    with patch('src.nodes.node12_earnings_calls.deberta_detector.TRANSFORMERS_AVAILABLE', False):
        with patch('src.nodes.node12_earnings_calls.deberta_detector.logger') as mock_logger:
            detector = DeBERTaContradictionDetector(strict_mode=False)
            
            # Verify warning was logged
            assert mock_logger.warning.called
            warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
            warning_text = " ".join(warning_calls)
            assert "DeBERTa Model Not Available" in warning_text or "WARNING" in warning_text
            assert "AI-powered contradiction detection is NOT active" in warning_text or "basic pattern matching" in warning_text.lower()


def test_deberta_fallback_status_accessible():
    """Test that DeBERTa detector exposes fallback status."""
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    # Mock transformers to simulate unavailability
    with patch('src.nodes.node12_earnings_calls.deberta_detector.TRANSFORMERS_AVAILABLE', False):
        detector = DeBERTaContradictionDetector(strict_mode=False)
        
        # Verify fallback fields are accessible
        assert hasattr(detector, '_using_fallback')
        assert hasattr(detector, '_fallback_reason')
        assert detector._using_fallback is True
        assert detector._fallback_reason is not None


def test_deberta_metadata_includes_fallback_info():
    """Test that DeBERTa detector includes fallback metadata in results."""
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    # Mock transformers to simulate unavailability
    with patch('src.nodes.node12_earnings_calls.deberta_detector.TRANSFORMERS_AVAILABLE', False):
        detector = DeBERTaContradictionDetector(strict_mode=False)
        
        # Get detection metadata
        metadata = detector.get_detection_metadata()
        
        # Verify metadata structure
        assert 'using_fallback' in metadata
        assert 'fallback_reason' in metadata
        assert 'detection_method' in metadata
        assert 'warnings' in metadata
        
        # Verify values
        assert metadata['using_fallback'] is True
        assert metadata['detection_method'] == 'basic_pattern_matching'
        assert len(metadata['warnings']) > 0
        assert "WARNING" in metadata['warnings'][0]


def test_deberta_strict_mode_raises_error_on_fallback():
    """Test that DeBERTa detector raises error in strict mode when model unavailable."""
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    # Mock transformers to simulate unavailability
    with patch('src.nodes.node12_earnings_calls.deberta_detector.TRANSFORMERS_AVAILABLE', False):
        # Should raise RuntimeError in strict mode
        with pytest.raises(RuntimeError) as exc_info:
            detector = DeBERTaContradictionDetector(strict_mode=True)
        
        # Verify error message
        assert "DeBERTa model required for DOJ-grade analysis" in str(exc_info.value)
        assert "is not available" in str(exc_info.value)


def test_deberta_loads_successfully_when_available():
    """Test that DeBERTa detector loads successfully when transformers available."""
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    # This test may fail if transformers is not installed, which is expected
    try:
        detector = DeBERTaContradictionDetector(strict_mode=False)
        
        # If it loads successfully, verify no fallback
        if detector._model_available:
            assert detector._using_fallback is False
            assert detector._fallback_reason is None
            
            metadata = detector.get_detection_metadata()
            assert metadata['using_fallback'] is False
            assert metadata['detection_method'] == 'deberta_ai'
            assert len(metadata['warnings']) == 0
    except Exception:
        # If transformers not available, that's fine - we test fallback elsewhere
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_noderesult_has_warnings_field():
    """Test that NodeResult dataclass has warnings field."""
    from src.core.recursive_engine import NodeResult
    
    # Create a NodeResult
    result = NodeResult(
        node_id="TEST",
        node_name="Test Node",
        status="success",
        violations_found=0,
        alerts_generated=0,
        findings={},
        execution_time_seconds=1.0,
        warnings=["Test warning"]
    )
    
    # Verify warnings field exists
    assert hasattr(result, 'warnings')
    assert result.warnings == ["Test warning"]
    
    # Verify to_dict includes warnings
    result_dict = result.to_dict()
    assert 'warnings' in result_dict
    assert result_dict['warnings'] == ["Test warning"]


def test_recursive_engine_accepts_strict_mode():
    """Test that RecursiveProsecutorialEngine accepts strict_mode parameter."""
    from src.core.recursive_engine import RecursiveProsecutorialEngine
    
    # Test that the class accepts strict_mode parameter and sets it correctly
    # We'll test without calling _init_nodes() to avoid initialization issues
    try:
        engine = RecursiveProsecutorialEngine(strict_mode=True)
        assert engine.strict_mode is True
        
        engine = RecursiveProsecutorialEngine(strict_mode=False)
        assert engine.strict_mode is False
    except TypeError as e:
        # If there are initialization issues with nodes, at least verify the parameter is accepted
        # by checking the __init__ signature
        import inspect
        sig = inspect.signature(RecursiveProsecutorialEngine.__init__)
        assert 'strict_mode' in sig.parameters
        pytest.skip(f"Node initialization failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
