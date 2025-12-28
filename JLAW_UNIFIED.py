#!/usr/bin/env python3
"""
JLAW_UNIFIED.py - Compatibility Shim
=====================================

This file provides backward compatibility by redirecting to jlaw_cli.py.

⚠️  DEPRECATION NOTICE:
This shim will be removed in v3.0. Please update your scripts to use jlaw_cli.py directly.

Migration:
  Old: python JLAW_UNIFIED.py --cik 320187 --year 2019
  New: python jlaw_cli.py --cik 320187 --year 2019

See docs/MIGRATION_V2_TO_V3.md for complete migration guide.
"""

import warnings
import sys
import subprocess
from pathlib import Path

# Emit deprecation warning
warnings.warn(
    "\n\n"
    "╔════════════════════════════════════════════════════════════════════════╗\n"
    "║                                                                        ║\n"
    "║  ⚠️  DEPRECATION WARNING                                               ║\n"
    "║                                                                        ║\n"
    "║  JLAW_UNIFIED.py is deprecated and will be removed in v3.0.           ║\n"
    "║  This shim redirects to jlaw_cli.py automatically.                    ║\n"
    "║                                                                        ║\n"
    "║  Please update your scripts to use jlaw_cli.py directly.              ║\n"
    "║  Migration guide: docs/MIGRATION_V2_TO_V3.md                          ║\n"
    "║                                                                        ║\n"
    "╚════════════════════════════════════════════════════════════════════════╝\n",
    DeprecationWarning,
    stacklevel=2
)

# Get path to jlaw_cli.py
project_root = Path(__file__).parent
jlaw_cli_path = project_root / "jlaw_cli.py"

if not jlaw_cli_path.exists():
    print("ERROR: jlaw_cli.py not found. Please reinstall JLAW.")
    sys.exit(1)

# Redirect to jlaw_cli.py with same arguments
print("\n🔄 Redirecting to jlaw_cli.py...\n")

try:
    # Use subprocess to execute jlaw_cli.py with same arguments
    result = subprocess.run(
        [sys.executable, str(jlaw_cli_path)] + sys.argv[1:],
        cwd=project_root
    )
    sys.exit(result.returncode)
except KeyboardInterrupt:
    print("\n\nInterrupted by user.")
    sys.exit(130)
except Exception as e:
    print(f"\nERROR: Failed to execute jlaw_cli.py: {e}")
    print("\nPlease run jlaw_cli.py directly:")
    print(f"  python jlaw_cli.py {' '.join(sys.argv[1:])}")
    sys.exit(1)
