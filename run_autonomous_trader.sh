#!/usr/bin/env bash
# Autonomous trading pipeline: scanner -> analysis -> (optional) trade executor
set -euo pipefail

# Use the correct Python with ccxt installed
HERMES_PY=/root/hermes-env/bin/python3

LOG_FILE="$HOME/hermes-trader/trade_log.md"
SCANNER="$HOME/hermes-trader/full_market_scanner.py"

# Run scanner
echo "=== $(date -u +"%Y-%m-%d %H:%M:%S UTC") - Scanner Run ===" >> "$LOG_FILE"
"$HERMES_PY" "$SCANNER" >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"
