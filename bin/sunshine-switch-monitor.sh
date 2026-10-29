#!/usr/bin/env bash
# ==============================================================================
# bin/sunshine-switch-monitor.sh
# Wrapper de execução para o alternador de telas do Sunshine/Moonlight
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/sunshine-switch-monitor.py" "$@"
