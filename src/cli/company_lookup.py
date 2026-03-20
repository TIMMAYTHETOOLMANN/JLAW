"""
Company Lookup Table
====================

Maps company names and ticker symbols to SEC CIK numbers.
Extracted from the deprecated JLAW_UNIFIED_DEPRECATED.py to provide
a canonical, importable lookup for the CLI and other modules.
"""

COMPANY_LOOKUP: dict[str, tuple[str, str]] = {
    "NIKE": ("320187", "NIKE, Inc."),
    "NKE": ("320187", "NIKE, Inc."),
    "APPLE": ("320193", "Apple Inc."),
    "AAPL": ("320193", "Apple Inc."),
    "MICROSOFT": ("789019", "Microsoft Corporation"),
    "MSFT": ("789019", "Microsoft Corporation"),
    "TESLA": ("1318605", "Tesla, Inc."),
    "TSLA": ("1318605", "Tesla, Inc."),
    "AMAZON": ("1018724", "Amazon.com, Inc."),
    "AMZN": ("1018724", "Amazon.com, Inc."),
    "META": ("1326801", "Meta Platforms, Inc."),
    "GOOGLE": ("1652044", "Alphabet Inc."),
    "GOOGL": ("1652044", "Alphabet Inc."),
    "NETFLIX": ("1065280", "Netflix, Inc."),
    "NFLX": ("1065280", "Netflix, Inc."),
    "NVIDIA": ("1045810", "NVIDIA Corporation"),
    "NVDA": ("1045810", "NVIDIA Corporation"),
}
