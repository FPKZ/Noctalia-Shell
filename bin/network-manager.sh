#!/usr/bin/env bash
# ==============================================================================
# bin/network-manager.sh
# Gerenciador de Rede Resiliente: Abre nm-connection-editor (GUI) ou nmtui no Kitty
# ==============================================================================

if command -v nm-connection-editor >/dev/null 2>&1; then
    exec nm-connection-editor "$@"
elif command -v kitty >/dev/null 2>&1 && command -v nmtui >/dev/null 2>&1; then
    exec kitty --class "network-tui" --title "Gerenciador de Rede (nmtui)" -e nmtui
elif command -v nmtui >/dev/null 2>&1; then
    exec nmtui
else
    if command -v notify-send >/dev/null 2>&1; then
        notify-send "Gerenciador de Rede" "Nenhum utilitário (nm-connection-editor ou nmtui) foi encontrado no sistema." -u critical
    fi
    exit 1
fi
