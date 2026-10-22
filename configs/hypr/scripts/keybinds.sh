#!/bin/bash

# Lista formatada de atalhos do sistema (Hyprland + Noctalia)
KEYBINDS_LIST="
🪟 [JANELA]  Super + Q                    -> Fechar janela ativa
🪟 [JANELA]  Super + F                    -> Tela cheia (Fullscreen)
🪟 [JANELA]  Super + Alt + Espaço         -> Alternar janela flutuante / tiled
🪟 [JANELA]  Super + J                    -> Alternar divisão de tela (horizontal/vertical)
🪟 [JANELA]  Super + Setas                -> Mover foco entre janelas
🪟 [JANELA]  Alt + Tab                    -> Alternar para próxima janela
🪟 [JANELA]  Super + Tab                  -> Alternador visual de janelas (Noctalia)
🪟 [JANELA]  Super + Shift + Setas        -> Mover janela na direção
🪟 [JANELA]  Super + Botão Esq (arrastar) -> Mover janela com mouse
🪟 [JANELA]  Super + Botão Dir (arrastar) -> Redimensionar janela com mouse
🪟 [JANELA]  Super + Alt + Setas	  -> Redimensionar janela com mouse
🚀 [APPS]    Super + Enter (Return)       -> Terminal Kitty
🚀 [APPS]    Super + E                    -> Gerenciador de Arquivos Dolphin
🚀 [APPS]    Super + W                    -> Navegador Firefox
🚀 [APPS]    Super + T                    -> Editor de Texto
🚀 [APPS]    Super + C                    -> Calculadora
🚀 [APPS]    Super + K                    -> KDE Connect (Gerenciador do Celular)
🚀 [APPS]    Ctrl + Shift + Esc           -> Monitor do Sistema (btop)
🌌 [NOCTALIA]Super + Espaço               -> Menu / Lançador de Aplicativos
🌌 [NOCTALIA]Super + Z                    -> Configurações do Noctalia
🌌 [NOCTALIA]Super + X                    -> Central de Controle (Wi-Fi, Som, BT)
🌌 [NOCTALIA]Super + A                    -> Painel de Notificações
🌌 [NOCTALIA]Super + V                    -> Histórico da Área de Transferência
🌌 [NOCTALIA]Super + Shift + W            -> Seletor de Papel de Parede (Wallpapers)
🌌 [NOCTALIA]Super + L                    -> Bloquear tela (Lockscreen)
🌌 [NOCTALIA]Super + Alt + C              -> Menu de Desligar / Encerrar Sessão
📸 [PRINT]   Print                        -> Captura de região da tela (Swash)
📸 [PRINT]   Super + Shift + S            -> Captura de tela inteira
📸 [PRINT]   Super + P                    -> Seletor de cores da tela (Color Picker)
🖥️ [MONITOR] Super + 1 / 2                 -> Focar no Monitor 1 / Monitor 2
🖥️ [MONITOR] Super + Shift + 1 / 2         -> Mover janela para Monitor 1 / Monitor 2
🗂️ [WORKSPACE]Super + Ctrl + 1 / 2 / 3    -> Ir para Workspace 1, 2 ou 3 do monitor
🗂️ [WORKSPACE]Super + Ctrl + Setas         -> Próximo / Anterior workspace
🗂️ [WORKSPACE]Super + Scroll do Mouse     -> Rolar entre workspaces do monitor
🗂️ [WORKSPACE]Super + Shift + Ctrl + 1..3 -> Mover janela para Workspace 1..3
🗂️ [WORKSPACE]Super +  I                   -> Alternar Workspace Especial (Scratchpad)
🗂️ [WORKSPACE]Super + Shift + I            -> Mover janela para o Scratchpad
❓ [AJUDA]   Super + F1                   -> Abrir este guia de atalhos
"

# Se o noctalia dmenu estiver disponível, abre pelo launcher nativo do Noctalia
if command -v noctalia >/dev/null 2>&1; then
    echo -e "$KEYBINDS_LIST" | grep -v '^$' | noctalia dmenu -p "🔍 Atalhos do Sistema:"
else
    # Fallback em janela flutuante do Kitty com fzf
    echo -e "$KEYBINDS_LIST" | fzf --prompt="🔍 Buscar Atalho: "
fi
