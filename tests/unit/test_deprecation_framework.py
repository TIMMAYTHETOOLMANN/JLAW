"""
Unit Tests for Deprecation Framework
=====================================

Tests deprecation warnings and utilities.
"""

import pytest
import warnings
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.deprecation import (
    deprecated_module,
    deprecated_v1,
    emit_deprecation_warning,
    DeprecatedClassMeta
)


class TestDeprecationFramework:
    """Test cases for deprecation utilities."""
    
    def test_deprecated_module_decorator(self):
        """Test deprecated_module decorator emits warnings."""
        
        @deprecated_module(
            reason="Test deprecation",
            replacement="NewClass",
            removal_version="3.0"
        )
        class OldClass:
            pass
        
        # Should emit deprecation warning on instantiation
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = OldClass()
            
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            assert "NewClass" in str(w[0].message)
    
    def test_deprecated_v1_decorator(self):
        """Test deprecated_v1 decorator (shorthand for v1 modules)."""
        
        @deprecated_v1("Enhanced analysis in v2")
        class AnalyzerV1:
            pass
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = AnalyzerV1()
            
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "v2" in str(w[0].message).lower()
    
    def test_deprecated_function(self):
        """Test deprecation works on functions."""
        
        @deprecated_module(
            reason="Use new_function instead",
            replacement="new_function",
            removal_version="3.0"
        )
        def old_function():
            return "result"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function()
            
            assert result == "result"
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "new_function" in str(w[0].message)
    
    def test_emit_deprecation_warning(self):
        """Test programmatic deprecation warning emission."""
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            emit_deprecation_warning(
                deprecated_item="old_api()",
                replacement="new_api()",
                removal_version="3.0",
                additional_info="See migration guide"
            )
            
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_api()" in str(w[0].message)
            assert "new_api()" in str(w[0].message)
            assert "migration guide" in str(w[0].message).lower()
    
    def test_deprecated_class_meta(self):
        """Test DeprecatedClassMeta metaclass."""
        
        class OldClassWithMeta(metaclass=DeprecatedClassMeta):
            __deprecated_replacement__ = "NewClass"
            __deprecated_version__ = "3.0"
            __deprecated_reason__ = "Replaced with enhanced version"
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            obj = OldClassWithMeta()
            
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "NewClass" in str(w[0].message)
            assert "3.0" in str(w[0].message)
    
    def test_decorated_class_still_functional(self):
        """Test that decorated classes remain functional."""
        
        @deprecated_v1("Use v2")
        class Calculator:
            def add(self, a, b):
                return a + b
        
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            calc = Calculator()
            result = calc.add(2, 3)
            
            assert result == 5
    
    def test_multiple_instantiations_emit_warnings(self):
        """Test that each instantiation emits a warning."""
        
        @deprecated_v1("Use v2")
        class TestClass:
            pass
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            obj1 = TestClass()
            obj2 = TestClass()
            obj3 = TestClass()
            
            # Each instantiation should emit a warning
            assert len(w) == 3
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
