"""
Tests for DeBERTa Model Availability Check (GAP-003)
===================================================

Validates that DeBERTa model availability is explicitly checked and reported.
"""


def test_contradiction_engine_has_availability_check():
    """Test that ContradictionEngine checks model availability."""
    from src.detection.ml.deberta_contradiction import ContradictionEngine
    
    # Initialize engine
    engine = ContradictionEngine()
    
    # Check that availability methods exist
    assert hasattr(engine, 'is_model_available'), \
        "ContradictionEngine missing is_model_available method"
    
    assert hasattr(engine, 'get_analysis_mode'), \
        "ContradictionEngine missing get_analysis_mode method"
    
    assert hasattr(engine, '_model_available'), \
        "ContradictionEngine missing _model_available attribute"
    
    assert hasattr(engine, '_fallback_reason'), \
        "ContradictionEngine missing _fallback_reason attribute"
    
    print(f"✓ ContradictionEngine has model availability checks")
    print(f"  Model available: {engine.is_model_available()}")
    print(f"  Analysis mode: {engine.get_analysis_mode()}")


def test_contradiction_engine_logs_mode():
    """Test that ContradictionEngine logs its mode on initialization."""
    import inspect
    from src.detection.ml.deberta_contradiction import ContradictionEngine
    
    # Check _check_model_availability method
    assert hasattr(ContradictionEngine, '_check_model_availability'), \
        "ContradictionEngine missing _check_model_availability method"
    
    method = ContradictionEngine._check_model_availability
    source = inspect.getsource(method)
    
    # Check for explicit logging
    assert 'logger.warning' in source, \
        "_check_model_availability doesn't log warnings"
    
    assert 'logger.info' in source or 'logger.warning' in source, \
        "_check_model_availability doesn't log model status"
    
    print("✓ ContradictionEngine logs model availability on initialization")


def test_deberta_detector_has_availability_check():
    """Test that DeBERTaContradictionDetector checks model availability."""
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    # Initialize detector
    detector = DeBERTaContradictionDetector()
    
    # Check that availability methods exist
    assert hasattr(detector, 'is_model_available'), \
        "DeBERTaContradictionDetector missing is_model_available method"
    
    assert hasattr(detector, 'get_analysis_mode'), \
        "DeBERTaContradictionDetector missing get_analysis_mode method"
    
    assert hasattr(detector, '_model_available'), \
        "DeBERTaContradictionDetector missing _model_available attribute"
    
    print(f"✓ DeBERTaContradictionDetector has model availability checks")
    print(f"  Model available: {detector.is_model_available()}")
    print(f"  Analysis mode: {detector.get_analysis_mode()}")


def test_deberta_detector_logs_warnings():
    """Test that DeBERTaContradictionDetector logs warnings when model unavailable."""
    import inspect
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    # Check __init__ method
    init_method = DeBERTaContradictionDetector.__init__
    source = inspect.getsource(init_method)
    
    # Check for warning logging
    assert 'logger.warning' in source, \
        "DeBERTaContradictionDetector doesn't log warnings"
    
    assert 'Fallback' in source or 'fallback' in source, \
        "Warning doesn't mention fallback mode"
    
    print("✓ DeBERTaContradictionDetector logs warnings about model availability")


def test_contradiction_engine_fallback_graceful():
    """Test that ContradictionEngine falls back gracefully."""
    from src.detection.ml.deberta_contradiction import ContradictionEngine
    
    engine = ContradictionEngine()
    
    # Even if model not available, engine should work
    assert engine is not None
    assert engine._loaded == True, \
        "Engine not marked as loaded after initialization"
    
    print("✓ ContradictionEngine initializes successfully regardless of model availability")


def test_detector_modes_reported():
    """Test that analysis modes are properly reported."""
    from src.detection.ml.deberta_contradiction import ContradictionEngine
    from src.nodes.node12_earnings_calls.deberta_detector import DeBERTaContradictionDetector
    
    engine = ContradictionEngine()
    detector = DeBERTaContradictionDetector()
    
    # Check that modes return valid values
    engine_mode = engine.get_analysis_mode()
    detector_mode = detector.get_analysis_mode()
    
    assert engine_mode in ['ml', 'rule-based'], \
        f"Invalid engine mode: {engine_mode}"
    
    assert detector_mode in ['ml', 'mock'], \
        f"Invalid detector mode: {detector_mode}"
    
    print(f"✓ Analysis modes properly reported")
    print(f"  ContradictionEngine: {engine_mode}")
    print(f"  DeBERTaContradictionDetector: {detector_mode}")


def test_fallback_reason_captured():
    """Test that fallback reason is captured when model unavailable."""
    from src.detection.ml.deberta_contradiction import ContradictionEngine
    
    engine = ContradictionEngine()
    
    if not engine.is_model_available():
        assert engine._fallback_reason is not None, \
            "Fallback reason not captured when model unavailable"
        print(f"✓ Fallback reason captured: {engine._fallback_reason[:50]}...")
    else:
        print("✓ Model available - fallback reason not needed")


if __name__ == "__main__":
    print("Running DeBERTa Model Availability Tests (GAP-003)...")
    print("=" * 70)
    
    try:
        test_contradiction_engine_has_availability_check()
    except Exception as e:
        print(f"✗ test_contradiction_engine_has_availability_check FAILED: {e}")
    
    try:
        test_contradiction_engine_logs_mode()
    except Exception as e:
        print(f"✗ test_contradiction_engine_logs_mode FAILED: {e}")
    
    try:
        test_deberta_detector_has_availability_check()
    except Exception as e:
        print(f"✗ test_deberta_detector_has_availability_check FAILED: {e}")
    
    try:
        test_deberta_detector_logs_warnings()
    except Exception as e:
        print(f"✗ test_deberta_detector_logs_warnings FAILED: {e}")
    
    try:
        test_contradiction_engine_fallback_graceful()
    except Exception as e:
        print(f"✗ test_contradiction_engine_fallback_graceful FAILED: {e}")
    
    try:
        test_detector_modes_reported()
    except Exception as e:
        print(f"✗ test_detector_modes_reported FAILED: {e}")
    
    try:
        test_fallback_reason_captured()
    except Exception as e:
        print(f"✗ test_fallback_reason_captured FAILED: {e}")
    
    print("=" * 70)
    print("DeBERTa model availability tests completed!")
