#!/usr/bin/env bash
# Every-30-min autonomous trading cycle. Logs to trade_cycles.log.
set -euo pipefail
HERMES_PY=/root/hermes-env/bin/python3
BASE="$HOME/hermes-trader"
CYCLE_LOG="$BASE/trade_cycles.log"

{
  echo "===== $(date -u +"%Y-%m-%d %H:%M:%S UTC") ====="
  "$HERMES_PY" "$BASE/autonomous_trader.py"
} >> "$CYCLE_LOG" 2>&1
