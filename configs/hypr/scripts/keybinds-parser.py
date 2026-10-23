#!/usr/bin/env python3
# ==============================================================================
# keybinds-parser.py
# Analisador dinâmico de atalhos do Hyprland (Lua e .conf).
# Lê os arquivos de configuração reais e extrai teclas, comandos e categorias.
# ==============================================================================
import os
import re
import sys
import subprocess

CONFIG_DIR = os.path.expanduser("~/.config/hypr")
BINDS_LUA = os.path.join(CONFIG_DIR, "config/binds.lua")
VARIABLES_LUA = os.path.join(CONFIG_DIR, "config/variables.lua")

# Tabela de correspondências amigáveis para ações conhecidas
ACTION_MAP = {
    # Janelas
    "window.close": ("🪟 [JANELA]", "Fechar janela ativa"),
    "window.float": ("🪟 [JANELA]", "Alternar modo flutuante / tiled"),
    "window.fullscreen({ mode = 1": ("🪟 [JANELA]", "Modo tela cheia (manter barras)"),
    "window.fullscreen": ("🪟 [JANELA]", "Alternar tela cheia (Fullscreen)"),
    "togglesplit": ("🪟 [JANELA]", "Alternar divisão (horizontal / vertical)"),
    "window.cycle_next": ("🪟 [JANELA]", "Alternar para a próxima janela (Alt+Tab)"),
    "window-switcher": ("🪟 [JANELA]", "Alternador visual de janelas (Noctalia)"),
    "hyprctl kill": ("🪟 [JANELA]", "Forçar encerramento de janela (Kill)"),
    "window.move({ direction = \"u\"": ("🪟 [JANELA]", "Mover janela para cima"),
    "window.move({ direction = \"d\"": ("🪟 [JANELA]", "Mover janela para baixo"),
    "window.move({ direction = \"l\"": ("🪟 [JANELA]", "Mover janela para esquerda"),
    "window.move({ direction = \"r\"": ("🪟 [JANELA]", "Mover janela para direita"),
    "window.move({ monitor   = \"-1\"": ("🖥️ [MONITOR]", "Mover janela para o monitor anterior"),
    "window.move({ monitor   = \"+1\"": ("🖥️ [MONITOR]", "Mover janela para o próximo monitor"),
    "focus({ direction = \"left\"": ("🪟 [NAVEGAÇÃO]", "Mover foco para a janela da esquerda"),
    "focus({ direction = \"right\"": ("🪟 [NAVEGAÇÃO]", "Mover foco para a janela da direita"),
    "focus({ direction = \"up\"": ("🪟 [NAVEGAÇÃO]", "Mover foco para a janela de cima"),
    "focus({ direction = \"down\"": ("🪟 [NAVEGAÇÃO]", "Mover foco para a janela de baixo"),
    "window.drag": ("🖱️ [MOUSE]", "Mover janela arrastando"),
    "window.resize()": ("🖱️ [MOUSE]", "Redimensionar janela arrastando"),
    "window.resize": ("🪟 [JANELA]", "Redimensionar janela ativa"),
    "zoomfunction": ("🔍 [ZOOM]", "Aumentar / Diminuir zoom da tela"),
    
    # Workspaces
    "workspace.toggle_special": ("🗂️ [WORKSPACE]", "Alternar workspace especial (Scratchpad)"),
    "window.move({ workspace = \"special\"": ("🗂️ [WORKSPACE]", "Mover janela para o Scratchpad"),
    "focus({ workspace = \"m+1\"": ("🗂️ [WORKSPACE]", "Ir para próximo workspace do monitor"),
    "focus({ workspace = \"m-1\"": ("🗂️ [WORKSPACE]", "Ir para workspace anterior do monitor"),
    "focus({ workspace = \"emptym\"": ("🗂️ [WORKSPACE]", "Ir para o próximo workspace vazio"),
    "window.move({ workspace = \"m+1\"": ("🗂️ [WORKSPACE]", "Mover janela para próximo workspace"),
    "window.move({ workspace = \"m-1\"": ("🗂️ [WORKSPACE]", "Mover janela para workspace anterior"),

    # Noctalia
    "panel-toggle launcher": ("🌌 [NOCTALIA]", "Lançador / Menu de Aplicativos", "noctalia msg panel-toggle launcher"),
    "launcher /emo": ("🌌 [NOCTALIA]", "Seletor de Emojis", "noctalia msg panel-toggle launcher /emo"),
    "panel-toggle control-center": ("🌌 [NOCTALIA]", "Central de Controle (Wi-Fi, Bluetooth, Áudio)", "noctalia msg panel-toggle control-center"),
    "control-center notifications": ("🌌 [NOCTALIA]", "Painel de Notificações", "noctalia msg panel-toggle control-center notifications"),
    "panel-toggle session": ("🌌 [NOCTALIA]", "Menu de Energia (Desligar, Reiniciar, Sair)", "noctalia msg panel-toggle session"),
    "session lock": ("🌌 [NOCTALIA]", "Bloquear a tela (Lockscreen)", "noctalia msg session lock"),
    "panel-toggle wallpaper": ("🌌 [NOCTALIA]", "Seletor de Papel de Parede (Wallpapers)", "noctalia msg panel-toggle wallpaper"),
    "panel-toggle clipboard": ("🌌 [NOCTALIA]", "Histórico da Área de Transferência", "noctalia msg panel-toggle clipboard"),
    "settings-toggle": ("🌌 [NOCTALIA]", "Painel de Configurações do Noctalia", "noctalia msg settings-toggle"),
    
    # Captura e Cores
    "screenshot-region": ("📸 [CAPTURA]", "Capturar região selecionada da tela", "noctalia msg screenshot-region"),
    "screenshot-fullscreen": ("📸 [CAPTURA]", "Capturar a tela inteira", "noctalia msg screenshot-fullscreen"),
    "hyprpicker": ("🎨 [UTILITÁRIO]", "Conta-gotas / Seletor de cores da tela", "hyprpicker -a -n"),

    # Mídia e Hardware
    "volume-up": ("🔊 [MÍDIA]", "Aumentar volume", "noctalia msg volume-up"),
    "volume-down": ("🔊 [MÍDIA]", "Diminuir volume", "noctalia msg volume-down"),
    "volume-mute": ("🔊 [MÍDIA]", "Mutar / Desmutar áudio", "noctalia msg volume-mute"),
    "mic-mute": ("🎙️ [MÍDIA]", "Mutar / Desmutar microfone", "noctalia msg mic-mute"),
    "media toggle": ("⏯️ [MÍDIA]", "Play / Pause reprodução de mídia", "noctalia msg media toggle"),
    "media next": ("⏭️ [MÍDIA]", "Próxima faixa de mídia", "noctalia msg media next"),
    "media previous": ("⏮️ [MÍDIA]", "Faixa anterior de mídia", "noctalia msg media previous"),
    "brightness-up": ("☀️ [BRILHO]", "Aumentar brilho da tela", "noctalia msg brightness-up"),
    "brightness-down": ("🔅 [BRILHO]", "Diminuir brilho da tela", "noctalia msg brightness-down"),

    # Aplicativos
    "TERMINAL": ("🚀 [APLICATIVO]", "Abrir Terminal Kitty", "kitty"),
    "FILE_MANAGER": ("🚀 [APLICATIVO]", "Abrir Gerenciador de Arquivos (Dolphin)", "dolphin"),
    "BROWSER": ("🚀 [APLICATIVO]", "Abrir Navegador Web (Firefox)", "firefox"),
    "EDITOR": ("🚀 [APLICATIVO]", "Abrir Editor de Texto", "gnome-text-editor"),
    "CALCULATOR": ("🚀 [APLICATIVO]", "Abrir Calculadora", "gnome-calculator"),
    "kdeconnect-app": ("📱 [APLICATIVO]", "Abrir KDE Connect", "kdeconnect-app"),
    "btop": ("📊 [SISTEMA]", "Monitor de Recursos do Sistema (btop)", "kitty -e btop"),
    "keybinds": ("❓ [AJUDA]", "Exibir este menu de atalhos", "")
}

def clean_key_name(k):
    k = k.replace('mainMod .. " + ', 'Super + ')
    k = k.replace('mainMod', 'Super')
    k = k.replace('"', '').strip()
    k = re.sub(r'\s*\+\s*', ' + ', k)
    k = k.replace('Return', 'Enter')
    k = k.replace('Escape', 'Esc')
    k = k.replace('period', '.')
    k = k.replace('slash', '/')
    k = k.replace('mouse:272', 'Botão Esquerdo')
    k = k.replace('mouse:273', 'Botão Direito')
    k = k.replace('mouse_up', 'Scroll Cima')
    k = k.replace('mouse_down', 'Scroll Baixo')
    k = k.replace('SHIFT', 'Shift').replace('CONTROL', 'Ctrl').replace('ALT', 'Alt')
    return k

def extract_binds():
    items = []
    seen = set()

    if not os.path.exists(BINDS_LUA):
        return items

    with open(BINDS_LUA, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    last_comment = ""
    for line in lines:
        stripped = line.strip()
        # Capturar comentários descritivos imediatamente acima
        if stripped.startswith("--") and not stripped.startswith("----") and not stripped.startswith("-- >>"):
            last_comment = stripped.lstrip("-").strip()
            continue

        if "hl.bind(" in line:
            # Capturar tecla e ação
            m = re.search(r'hl\.bind\s*\(\s*([^,]+?)\s*,\s*(.+?)\s*\)', line)
            if not m:
                continue

            raw_key = m.group(1).strip()
            raw_action = m.group(2).strip()

            # Pular geradores numéricos de loop (adicionados explicitamente abaixo)
            if "digitCode" in raw_key:
                last_comment = ""
                continue

            key = clean_key_name(raw_key)
            if key in seen:
                last_comment = ""
                continue
            seen.add(key)

            category = "⌨️ [ATALHO]"
            desc = ""
            run_cmd = ""

            # Verificar mapeamento amigável
            for pattern, info in ACTION_MAP.items():
                if pattern in raw_action:
                    category = info[0]
                    desc = info[1]
                    if len(info) > 2:
                        run_cmd = info[2]
                    elif "noctCall" in raw_action:
                        # Extrair comando noctalia
                        m_noct = re.search(r'noctCall\s*\.\.\s*["\']([^"\']+)["\']', raw_action)
                        if m_noct:
                            run_cmd = f"noctalia msg {m_noct.group(1)}"
                    break

            # Se não encontrou no mapa, usar o comentário ou o comando cru
            if not desc:
                if last_comment:
                    desc = last_comment
                else:
                    m_cmd = re.search(r'exec_cmd\s*\(\s*["\']?([^"\']+)["\']?\s*\)', raw_action)
                    if m_cmd:
                        desc = m_cmd.group(1).replace("uwsm app -- ", "").strip()
                        run_cmd = desc
                    else:
                        desc = raw_action.replace("hl.dsp.", "").strip()

            items.append((category, key, desc, run_cmd))
            last_comment = ""
        else:
            if not stripped.startswith("--"):
                last_comment = ""

    # Adicionar atalhos de workspace universais de forma clara
    items.append(("🗂️ [WORKSPACE]", "Super + 1..9", "Alternar para workspace 1 a 9 no monitor", ""))
    items.append(("🗂️ [WORKSPACE]", "Super + Shift + 1..9", "Mover janela para workspace 1 a 9", ""))
    items.append(("🗂️ [WORKSPACE]", "Super + Ctrl + Setas", "Navegar para workspace adjacente", ""))
    items.append(("🗂️ [WORKSPACE]", "Super + Scroll", "Rolar entre workspaces do monitor", ""))
    items.append(("🖥️ [MONITOR]", "Super + 1 / 2", "Focar no Monitor 1 ou Monitor 2", ""))
    items.append(("🖥️ [MONITOR]", "Super + Shift + 1 / 2", "Mover janela para Monitor 1 ou Monitor 2", ""))

    return items

def main():
    items = extract_binds()
    # Imprimir em formato padronizado com separador tabulado
    for cat, key, desc, run_cmd in items:
        # Formato de exibição elegante
        # Guardar comando executável no final após delimitador invisível se necessário
        print(f"{cat:<18} │ {key:<28} ➜  {desc}")

if __name__ == "__main__":
    main()
