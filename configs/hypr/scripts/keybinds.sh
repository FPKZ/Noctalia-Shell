#!/usr/bin/env bash
# ==============================================================================
# keybinds.sh - Menu Interativo de Atalhos do Hyprland + Noctalia
# Suporta:
#   1. GUI Nativa Dedicada (PySide6 / Qt6 no Wayland) [Padrão]
#   2. Modal Flutuante no Kitty + fzf com alinhamento perfeito (--kitty)
#   3. Menu Dmenu do Noctalia Shell (--dmenu)
# ==============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSER="$SCRIPT_DIR/keybinds-parser.py"
GUI="$SCRIPT_DIR/keybinds-gui.py"

# Fallback para ~/.config/hypr/scripts se necessário
if [ ! -f "$PARSER" ]; then
    PARSER="$HOME/.config/hypr/scripts/keybinds-parser.py"
fi
if [ ! -f "$GUI" ]; then
    GUI="$HOME/.config/hypr/scripts/keybinds-gui.py"
fi

# Modo Terminal: Kitty + fzf
if [ "$1" == "--terminal" ] || [ "$1" == "--kitty" ] || [ "$1" == "--floating" ]; then
    kitty --class="hypr-cheatsheet" \
          --title="⌨️  Atalhos do Hyprland & Noctalia" \
          -o initial_window_width=1050 \
          -o initial_window_height=650 \
          -o remember_window_size=no \
          bash -c "python3 '$PARSER' | fzf --reverse \
                                           --border=rounded \
                                           --margin=1 \
                                           --padding=1 \
                                           --prompt='⚡ Buscar Atalho: ' \
                                           --header='📖 GUIA DINÂMICO DE ATALHOS | Pressione ESC para fechar' \
                                           --color='border:#555877,header:#bcc2ff,prompt:#ffb4ab,pointer:#c4c5dd,hl:#bcc2ff,info:#c4c5dd'"
    exit 0
fi

# Modo Dmenu: Noctalia nativo
if [ "$1" == "--dmenu" ] && command -v noctalia >/dev/null 2>&1; then
    SELECTED=$(python3 "$PARSER" | noctalia dmenu -p "⌨️ Buscar Atalho:")
    if [ -n "$SELECTED" ]; then
        if echo "$SELECTED" | grep -qi "Terminal Kitty"; then kitty &
        elif echo "$SELECTED" | grep -qi "Dolphin"; then env XDG_CURRENT_DESKTOP=KDE QT_QPA_PLATFORMTHEME=kde dolphin &
        elif echo "$SELECTED" | grep -qi "Firefox"; then firefox &
        elif echo "$SELECTED" | grep -qi "Calculadora"; then gnome-calculator &
        elif echo "$SELECTED" | grep -qi "KDE Connect"; then kdeconnect-app &
        elif echo "$SELECTED" | grep -qi "btop"; then kitty -e btop &
        elif echo "$SELECTED" | grep -qi "Capturar região"; then noctalia msg screenshot-region &
        elif echo "$SELECTED" | grep -qi "Capturar a tela inteira"; then noctalia msg screenshot-fullscreen &
        elif echo "$SELECTED" | grep -qi "Conta-gotas"; then hyprpicker -a -n &
        elif echo "$SELECTED" | grep -qi "Central de Controle"; then noctalia msg panel-toggle control-center &
        elif echo "$SELECTED" | grep -qi "Lançador"; then noctalia msg panel-toggle launcher &
        elif echo "$SELECTED" | grep -qi "Wallpapers"; then noctalia msg panel-toggle wallpaper &
        elif echo "$SELECTED" | grep -qi "Área de Transferência"; then noctalia msg panel-toggle clipboard &
        elif echo "$SELECTED" | grep -qi "Configurações do Noctalia"; then noctalia msg settings-toggle &
        elif echo "$SELECTED" | grep -qi "Bloquear a tela"; then noctalia msg session lock &
        elif echo "$SELECTED" | grep -qi "Menu de Energia"; then noctalia msg panel-toggle session &
        fi
    fi
    exit 0
fi

# Modo Padrão: Painel Gráfico Moderno Dedicado (PySide6)
if [ -f "$GUI" ]; then
    python3 "$GUI"
else
    # Fallback para Kitty se a GUI não estiver instalada
    kitty --class="hypr-cheatsheet" \
          -o initial_window_width=1050 \
          -o initial_window_height=650 \
          bash -c "python3 '$PARSER' | fzf --reverse --prompt='⚡ Atalhos: '"
fi
