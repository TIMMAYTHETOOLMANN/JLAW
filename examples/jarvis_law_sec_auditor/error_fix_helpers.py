"""
Error Fix Helpers - Safe Comparison Functions
Prevents "TypeError: '<' not supported between instances of 'NoneType' and 'str'"
"""

from typing import Any, Optional, List, Callable


def safe_compare_lt(a: Any, b: Any, default_a: Any = '', default_b: Any = '') -> bool:
    """
    Safely compare if a < b, handling None values
    
    Args:
        a: First value (may be None)
        b: Second value (may be None)
        default_a: Default value for a if None
        default_b: Default value for b if None
    
    Returns:
        bool: Result of comparison
    """
    if a is None:
        a = default_a
    if b is None:
        b = default_b
    try:
        return a < b
    except TypeError:
        return str(a) < str(b)


def safe_compare_gt(a: Any, b: Any, default_a: Any = '', default_b: Any = '') -> bool:
    """Safely compare if a > b, handling None values"""
    if a is None:
        a = default_a
    if b is None:
        b = default_b
    try:
        return a > b
    except TypeError:
        return str(a) > str(b)


def safe_sort(items: List[Any], key: Optional[Callable] = None, reverse: bool = False) -> List[Any]:
    """
    Safely sort items that might contain None values
    
    Args:
        items: List to sort (may contain None)
        key: Optional key function
        reverse: Sort in reverse order
    
    Returns:
        Sorted list with None values at the end (or start if reverse=True)
    """
    if not items:
        return []
    
    if key:
        # Sort with None values at end
        return sorted(items, key=lambda x: (x is None, key(x) if x is not None else None), reverse=reverse)
    else:
        # Sort with None values at end
        return sorted(items, key=lambda x: (x is None, x if x is not None else ''), reverse=reverse)


def safe_min(items: List[Any], default: Any = None) -> Any:
    """
    Safely get minimum value, filtering out None
    
    Args:
        items: List of items (may contain None)
        default: Value to return if no valid items
    
    Returns:
        Minimum value or default
    """
    non_none = [x for x in items if x is not None]
    return min(non_none) if non_none else default


def safe_max(items: List[Any], default: Any = None) -> Any:
    """
    Safely get maximum value, filtering out None
    
    Args:
        items: List of items (may contain None)
        default: Value to return if no valid items
    
    Returns:
        Maximum value or default
    """
    non_none = [x for x in items if x is not None]
    return max(non_none) if non_none else default


def safe_get(dictionary: dict, key: str, default: Any = '', compare_safe: bool = True) -> Any:
    """
    Safely get dictionary value with comparison-safe default
    
    Args:
        dictionary: Dictionary to get from
        key: Key to retrieve
        default: Default value if key not found
        compare_safe: If True, ensures default is comparison-safe
    
    Returns:
        Value from dictionary or default
    """
    value = dictionary.get(key, default)
    if value is None and compare_safe:
        return default
    return value


def coalesce(*values: Any) -> Any:
    """
    Return first non-None value
    
    Args:
        *values: Values to check
    
    Returns:
        First non-None value or None if all are None
    """
    for value in values:
        if value is not None:
            return value
    return None


def safe_str_compare(a: Any, b: Any, case_sensitive: bool = True) -> int:
    """
    Safely compare two values as strings
    
    Args:
        a: First value
        b: Second value
        case_sensitive: Whether comparison is case-sensitive
    
    Returns:
        -1 if a < b, 0 if equal, 1 if a > b
    """
    str_a = str(a) if a is not None else ''
    str_b = str(b) if b is not None else ''
    
    if not case_sensitive:
        str_a = str_a.lower()
        str_b = str_b.lower()
    
    if str_a < str_b:
        return -1
    elif str_a > str_b:
        return 1
    else:
        return 0


def ensure_comparable(value: Any, default: Any = 0) -> Any:
    """
    Ensure value is comparable (not None)
    
    Args:
        value: Value to check
        default: Default if None
    
    Returns:
        Original value or default
    """
    return value if value is not None else default


# Convenience functions for common types
def safe_int_compare(a: Any, b: Any, default: int = 0) -> bool:
    """Safely compare integers"""
    a_val = int(a) if a is not None else default
    b_val = int(b) if b is not None else default
    return a_val < b_val


def safe_float_compare(a: Any, b: Any, default: float = 0.0) -> bool:
    """Safely compare floats"""
    a_val = float(a) if a is not None else default
    b_val = float(b) if b is not None else default
    return a_val < b_val


def safe_date_compare(a: Any, b: Any, default: Any = None) -> bool:
    """Safely compare dates (assumes datetime objects or None)"""
    if a is None:
        return True if b is not None else False
    if b is None:
        return False
    return a < b


# Export all functions
__all__ = [
    'safe_compare_lt',
    'safe_compare_gt',
    'safe_sort',
    'safe_min',
    'safe_max',
    'safe_get',
    'coalesce',
    'safe_str_compare',
    'ensure_comparable',
    'safe_int_compare',
    'safe_float_compare',
    'safe_date_compare',
]


# Usage examples
if __name__ == '__main__':
    print("Testing safe comparison functions...")
    print()
    
    # Test safe_sort
    test_list = [None, "banana", "apple", None, "cherry"]
    print(f"Original: {test_list}")
    print(f"Sorted: {safe_sort(test_list)}")
    print()
    
    # Test safe_min/max
    test_numbers = [None, 5, 2, None, 8, 1]
    print(f"Numbers: {test_numbers}")
    print(f"Min: {safe_min(test_numbers)}")
    print(f"Max: {safe_max(test_numbers)}")
    print()
    
    # Test safe_compare
    print(f"None < 'a': {safe_compare_lt(None, 'a')}")
    print(f"'a' < None: {safe_compare_lt('a', None)}")
    print()
    
    # Test coalesce
    print(f"coalesce(None, None, 'value'): {coalesce(None, None, 'value')}")
    print()
    
    print("All tests passed!")

