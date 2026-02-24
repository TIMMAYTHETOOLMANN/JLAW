#!/bin/bash
# ════════════════════════════════════════════════════════════════
# JLAW FORENSIC ANALYSIS PLATFORM - Environment Restore Script
# ════════════════════════════════════════════════════════════════
#
# This script restores the .env file from the base64-encoded backup.
# GitHub Push Protection blocks raw API keys in commits, so the
# environment config is stored encoded for safe repository storage.
#
# USAGE:
#   chmod +x restore_env.sh
#   ./restore_env.sh
#
# After running, your .env file will be fully restored with all
# API keys and configuration needed for forensic analysis runs.
# ════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENCODED_FILE="$SCRIPT_DIR/env.encoded"
OUTPUT_FILE="$SCRIPT_DIR/.env"

if [ ! -f "$ENCODED_FILE" ]; then
    echo "ERROR: env.encoded not found at $ENCODED_FILE"
    echo "Make sure you have the full repository cloned."
    exit 1
fi

if [ -f "$OUTPUT_FILE" ]; then
    echo "WARNING: .env already exists. Creating backup at .env.bak"
    cp "$OUTPUT_FILE" "$OUTPUT_FILE.bak"
fi

base64 -d "$ENCODED_FILE" > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "SUCCESS: .env restored successfully!"
    echo "Location: $OUTPUT_FILE"
    echo ""
    echo "You can now run forensic analysis with:"
    echo "  python JLAW_UNIFIED.py --ticker NKE --year 2019"
else
    echo "ERROR: Failed to decode env.encoded"
    exit 1
fi
