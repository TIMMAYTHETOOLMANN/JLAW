"""
Zero-Dollar Transaction Database Schema
========================================

PostgreSQL schema for forensic analysis data storage.

The schema includes:
- Core transaction tables with Form 4 data
- Transaction clustering for pattern detection
- Anomaly flags and material events
- Entity and ownership structure tracking
- Behavioral risk assessments
- FRE 902(13)/(14) compliant evidence chain
- RFC 3161 timestamp tracking
- Chain of custody records

Reference: Section 11 - Data Schema Specifications

Schema file: database.sql
"""

import os
from pathlib import Path

# Get path to database.sql
SCHEMA_DIR = Path(__file__).parent
SCHEMA_FILE = SCHEMA_DIR / "database.sql"


def get_schema_sql() -> str:
    """
    Load the PostgreSQL schema SQL.
    
    Returns:
        Complete SQL schema as string
    """
    with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
        return f.read()


__all__ = [
    "get_schema_sql",
    "SCHEMA_FILE",
]
