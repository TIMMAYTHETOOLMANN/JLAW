"""
JLAW Utilities Package
======================

Common utility functions and helpers for JLAW codebase.
"""

from .deprecation import (
    deprecated_module,
    deprecated_v1,
    emit_deprecation_warning,
    DeprecatedClassMeta
)

__all__ = [
    'deprecated_module',
    'deprecated_v1',
    'emit_deprecation_warning',
    'DeprecatedClassMeta',
]
