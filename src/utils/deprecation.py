"""
Deprecation utilities for JLAW codebase.
=========================================

Provides decorators and utilities for marking deprecated modules, classes,
and functions with clear migration guidance.

Usage:
    from src.utils.deprecation import deprecated_v1, deprecated_module
    
    @deprecated_v1("Enhanced analysis capabilities in v2")
    class MyAnalyzerV1:
        ...
"""

import warnings
from functools import wraps
from typing import Optional, Callable


def deprecated_module(
    reason: str,
    replacement: str,
    removal_version: str = "3.0"
) -> Callable:
    """
    Decorator to mark entire modules, classes, or functions as deprecated.
    
    Args:
        reason: Why this is deprecated
        replacement: What to use instead
        removal_version: When this will be removed
        
    Returns:
        Decorator function
        
    Example:
        @deprecated_module(
            reason="Replaced with enhanced implementation",
            replacement="MyClassV2",
            removal_version="3.0"
        )
        class MyClass:
            pass
    """
    def decorator(cls_or_func):
        @wraps(cls_or_func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{cls_or_func.__name__} is deprecated. "
                f"{reason} Use {replacement} instead. "
                f"Will be removed in v{removal_version}.",
                DeprecationWarning,
                stacklevel=2
            )
            return cls_or_func(*args, **kwargs)
        return wrapper
    return decorator


def deprecated_v1(message: str = "Use v2 module instead") -> Callable:
    """
    Specific decorator for v1 modules being replaced by v2.
    
    Args:
        message: Custom deprecation message
        
    Returns:
        Decorator function
        
    Example:
        @deprecated_v1("Enhanced fraud detection in v2")
        class FraudDetectorV1:
            pass
    """
    return deprecated_module(
        reason=message,
        replacement="v2 module",
        removal_version="3.0"
    )


def emit_deprecation_warning(
    deprecated_item: str,
    replacement: str,
    removal_version: str = "3.0",
    additional_info: Optional[str] = None
) -> None:
    """
    Emit a deprecation warning programmatically.
    
    Args:
        deprecated_item: Name of deprecated item
        replacement: What to use instead
        removal_version: When this will be removed
        additional_info: Additional migration guidance
        
    Example:
        emit_deprecation_warning(
            "old_function()",
            "new_function()",
            additional_info="See docs/MIGRATION_GUIDE.md"
        )
    """
    message = (
        f"{deprecated_item} is deprecated and will be removed in v{removal_version}. "
        f"Use {replacement} instead."
    )
    
    if additional_info:
        message += f" {additional_info}"
    
    warnings.warn(message, DeprecationWarning, stacklevel=2)


class DeprecatedClassMeta(type):
    """
    Metaclass for deprecated classes that emits warnings on instantiation.
    
    Example:
        class MyOldClass(metaclass=DeprecatedClassMeta):
            __deprecated_replacement__ = "MyNewClass"
            __deprecated_version__ = "3.0"
            __deprecated_reason__ = "Enhanced implementation available"
    """
    
    def __call__(cls, *args, **kwargs):
        replacement = getattr(cls, '__deprecated_replacement__', 'newer version')
        version = getattr(cls, '__deprecated_version__', '3.0')
        reason = getattr(cls, '__deprecated_reason__', 'Deprecated')
        
        warnings.warn(
            f"{cls.__name__} is deprecated. {reason} "
            f"Use {replacement} instead. "
            f"Will be removed in v{version}.",
            DeprecationWarning,
            stacklevel=2
        )
        
        return super(DeprecatedClassMeta, cls).__call__(*args, **kwargs)
