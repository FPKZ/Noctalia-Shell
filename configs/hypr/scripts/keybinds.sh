#!/usr/bin/env bash
# ==============================================================================
# keybinds.sh - Menu Interativo de Atalhos do Hyprland + Noctalia
# Reconhece dinamicamente os atalhos reais de binds.lua e exibe com estilo.
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSER="$SCRIPT_DIR/keybinds-parser.py"

# Se o script python não estiver presente aqui, tentar no ~/.config/hypr/scripts/
if [ ! -f "$PARSER" ]; then
    PARSER="$HOME/.config/hypr/scripts/keybinds-parser.py"
fi

# Modo 1: Janela Modal Flutuante Estilizada (Kitty + fzf com cores Noctalia)
if [ "$1" == "--floating" ] || ! command -v noctalia >/dev/null 2>&1; then
    kitty --class="hypr-cheatsheet" \
          --title="⌨️  Atalhos do Hyprland & Noctalia" \
          -o initial_window_width=980 \
          -o initial_window_height=640 \
          -o remember_window_size=no \
          bash -c "python3 '$PARSER' | fzf --reverse \
                                           --border=rounded \
                                           --margin=1 \
                                           --padding=1 \
                                           --prompt='⚡ Buscar Atalho: ' \
                                           --header='📖 GUIA DINÂMICO DE ATALHOS | Pressione ESC para fechar' \
                                           --color='border:#555877,header:#bcc2ff,prompt:#ffb4ab,pointer:#c4c5dd,hl:#bcc2ff,info:#c4c5dd'"
else
    # Modo 2: Menu Nativo Integrado do Noctalia (Material You)
    SELECTED=$(python3 "$PARSER" | noctalia dmenu -p "⌨️ Buscar Atalho do Sistema:")
    
    # Se o usuário selecionou uma linha e pressionou Enter, disparar a ação diretamente
    if [ -n "$SELECTED" ]; then
        if echo "$SELECTED" | grep -qi "Terminal Kitty"; then
            kitty &
        elif echo "$SELECTED" | grep -qi "Dolphin"; then
            env XDG_CURRENT_DESKTOP=KDE QT_QPA_PLATFORMTHEME=kde dolphin &
        elif echo "$SELECTED" | grep -qi "Firefox"; then
            firefox &
        elif echo "$SELECTED" | grep -qi "Calculadora"; then
            gnome-calculator &
        elif echo "$SELECTED" | grep -qi "KDE Connect"; then
            kdeconnect-app &
        elif echo "$SELECTED" | grep -qi "btop"; then
            kitty -e btop &
        elif echo "$SELECTED" | grep -qi "Capturar região"; then
            noctalia msg screenshot-region &
        elif echo "$SELECTED" | grep -qi "Capturar a tela inteira"; then
            noctalia msg screenshot-fullscreen &
        elif echo "$SELECTED" | grep -qi "Conta-gotas"; then
            hyprpicker -a -n &
        elif echo "$SELECTED" | grep -qi "Central de Controle"; then
            noctalia msg panel-toggle control-center &
        elif echo "$SELECTED" | grep -qi "Lançador"; then
            noctalia msg panel-toggle launcher &
        elif echo "$SELECTED" | grep -qi "Wallpapers"; then
            noctalia msg panel-toggle wallpaper &
        elif echo "$SELECTED" | grep -qi "Área de Transferência"; then
            noctalia msg panel-toggle clipboard &
        elif echo "$SELECTED" | grep -qi "Configurações do Noctalia"; then
            noctalia msg settings-toggle &
        elif echo "$SELECTED" | grep -qi "Bloquear a tela"; then
            noctalia msg session lock &
        elif echo "$SELECTED" | grep -qi "Menu de Energia"; then
            noctalia msg panel-toggle session &
        fi
    fi
fi
