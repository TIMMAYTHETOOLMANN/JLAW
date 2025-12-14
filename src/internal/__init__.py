"""
JLAW Internal Module - Restricted Access
=========================================

This module contains internal-only components that require explicit
acknowledgment to access. These components are designed for internal
forensic analysis and should not be exposed through public APIs.

Access Control:
- Use get_internal_module() function with acknowledgment parameter
- Modules may have restricted serialization/export capabilities
"""

import sys
import warnings
from typing import Any, Optional


class InternalAccessWarning(UserWarning):
    """Warning raised when accessing internal modules."""
    pass


def get_internal_module(
    module_name: str,
    acknowledge_internal_use: bool = False
) -> Optional[Any]:
    """
    Get access to an internal module with explicit acknowledgment.
    
    Args:
        module_name: Name of the internal module to access
        acknowledge_internal_use: Must be True to access internal modules
        
    Returns:
        The requested internal module, or None if access denied
        
    Raises:
        PermissionError: If acknowledgment is not provided
        ImportError: If module does not exist
        
    Example:
        >>> bounty = get_internal_module(
        ...     'whistleblower_bounty_estimator',
        ...     acknowledge_internal_use=True
        ... )
    """
    if not acknowledge_internal_use:
        raise PermissionError(
            f"Access to internal module '{module_name}' requires explicit acknowledgment. "
            f"Set acknowledge_internal_use=True to confirm you understand this is "
            f"for internal forensic use only."
        )
    
    # Warn about internal module usage
    warnings.warn(
        f"Accessing internal module '{module_name}'. This module has restricted "
        f"usage and may not be suitable for external interfaces.",
        InternalAccessWarning,
        stacklevel=2
    )
    
    # Import the requested module
    try:
        if module_name == 'whistleblower_bounty_estimator':
            from . import whistleblower_bounty_estimator
            return whistleblower_bounty_estimator
        else:
            raise ImportError(f"Internal module '{module_name}' does not exist")
    except ImportError as e:
        raise ImportError(
            f"Failed to import internal module '{module_name}': {str(e)}"
        ) from e


__all__ = ['get_internal_module', 'InternalAccessWarning']
