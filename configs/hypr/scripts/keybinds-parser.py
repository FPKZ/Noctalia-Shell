#!/usr/bin/env python3
# ==============================================================================
# keybinds-parser.py
# Analisador Universal de Atalhos do Sistema
# Lê dinamicamente:
#  1. Hyprland (binds.lua)
#  2. Noctalia Shell (ações e comandos de interface)
#  3. Terminal Kitty (janelas, abas, split e histórico)
#  4. Dolphin (gerenciador de arquivos)
#  5. Navegador Web (Firefox / Chrome)
#  6. KDE Plasma / KWin (kglobalshortcutsrc) se presente
# ==============================================================================
import os
import re
import sys
import configparser

CONFIG_DIR = os.path.expanduser("~/.config")
HYPR_DIR = os.path.join(CONFIG_DIR, "hypr")
BINDS_LUA = os.path.join(HYPR_DIR, "config/binds.lua")
KGLOBAL_SRC = os.path.join(CONFIG_DIR, "kglobalshortcutsrc")

ACTION_MAP = {
    # Janelas Hyprland
    "window.close": ("🪟 [HYPR: JANELA]", "Fechar janela ativa"),
    "window.float": ("🪟 [HYPR: JANELA]", "Alternar modo flutuante / tiled"),
    "window.fullscreen({ mode = 1": ("🪟 [HYPR: JANELA]", "Modo tela cheia (mantendo barras)"),
    "window.fullscreen": ("🪟 [HYPR: JANELA]", "Alternar tela cheia (Fullscreen)"),
    "togglesplit": ("🪟 [HYPR: JANELA]", "Alternar divisão (horizontal / vertical)"),
    "window.cycle_next": ("🪟 [HYPR: JANELA]", "Alternar para a próxima janela (Alt+Tab)"),
    "window-switcher": ("🪟 [HYPR: JANELA]", "Alternador visual de janelas (Noctalia)"),
    "hyprctl kill": ("🪟 [HYPR: JANELA]", "Forçar encerramento de janela travada (Kill)"),
    "window.move({ direction = \"u\"": ("🪟 [HYPR: JANELA]", "Mover janela ativa para cima"),
    "window.move({ direction = \"d\"": ("🪟 [HYPR: JANELA]", "Mover janela ativa para baixo"),
    "window.move({ direction = \"l\"": ("🪟 [HYPR: JANELA]", "Mover janela ativa para esquerda"),
    "window.move({ direction = \"r\"": ("🪟 [HYPR: JANELA]", "Mover janela ativa para direita"),
    "window.move({ monitor   = \"-1\"": ("🖥️ [HYPR: MONITOR]", "Mover janela para o monitor anterior"),
    "window.move({ monitor   = \"+1\"": ("🖥️ [HYPR: MONITOR]", "Mover janela para o próximo monitor"),
    "focus({ direction = \"left\"": ("🪟 [HYPR: FOCO]", "Mover foco para a janela da esquerda"),
    "focus({ direction = \"right\"": ("🪟 [HYPR: FOCO]", "Mover foco para a janela da direita"),
    "focus({ direction = \"up\"": ("🪟 [HYPR: FOCO]", "Mover foco para a janela de cima"),
    "focus({ direction = \"down\"": ("🪟 [HYPR: FOCO]", "Mover foco para a janela de baixo"),
    "window.drag": ("🖱️ [HYPR: MOUSE]", "Mover janela arrastando com botão esquerdo"),
    "window.resize()": ("🖱️ [HYPR: MOUSE]", "Redimensionar janela arrastando com botão direito"),
    "window.resize": ("🪟 [HYPR: JANELA]", "Redimensionar janela ativa via teclado"),
    "zoomfunction": ("🔍 [HYPR: ZOOM]", "Aumentar ou diminuir zoom geral da tela"),

    # Workspaces
    "workspace.toggle_special": ("🗂️ [HYPR: WORKSPACE]", "Alternar workspace especial (Scratchpad oculto)"),
    "window.move({ workspace = \"special\"": ("🗂️ [HYPR: WORKSPACE]", "Mover janela ativa para o Scratchpad"),
    "focus({ workspace = \"m+1\"": ("🗂️ [HYPR: WORKSPACE]", "Ir para próximo workspace do monitor"),
    "focus({ workspace = \"m-1\"": ("🗂️ [HYPR: WORKSPACE]", "Ir para workspace anterior do monitor"),
    "focus({ workspace = \"emptym\"": ("🗂️ [HYPR: WORKSPACE]", "Ir para o próximo workspace vazio"),
    "window.move({ workspace = \"m+1\"": ("🗂️ [HYPR: WORKSPACE]", "Mover janela para próximo workspace"),
    "window.move({ workspace = \"m-1\"": ("🗂️ [HYPR: WORKSPACE]", "Mover janela para workspace anterior"),

    # Noctalia Shell
    "panel-toggle launcher": ("🌌 [NOCTALIA]", "Lançador / Menu de Aplicativos"),
    "launcher /emo": ("🌌 [NOCTALIA]", "Seletor rápido de Emojis"),
    "panel-toggle control-center": ("🌌 [NOCTALIA]", "Central de Controle (Wi-Fi, Bluetooth, Som)"),
    "control-center notifications": ("🌌 [NOCTALIA]", "Painel de Notificações do Sistema"),
    "panel-toggle session": ("🌌 [NOCTALIA]", "Menu de Energia (Desligar, Reiniciar, Sair)"),
    "session lock": ("🌌 [NOCTALIA]", "Bloquear a tela (Lockscreen)"),
    "panel-toggle wallpaper": ("🌌 [NOCTALIA]", "Seletor de Papéis de Parede"),
    "panel-toggle clipboard": ("🌌 [NOCTALIA]", "Histórico da Área de Transferência (Clipboard)"),
    "settings-toggle": ("🌌 [NOCTALIA]", "Painel de Configurações do Noctalia"),

    # Captura e Cores
    "screenshot-region": ("📸 [CAPTURA]", "Capturar região selecionada da tela"),
    "screenshot-fullscreen": ("📸 [CAPTURA]", "Capturar tela inteira"),
    "hyprpicker": ("🎨 [UTILITÁRIO]", "Conta-gotas / Seletor de cores da tela"),

    # Mídia e Hardware
    "volume-up": ("🔊 [MÍDIA]", "Aumentar volume do áudio"),
    "volume-down": ("🔊 [MÍDIA]", "Diminuir volume do áudio"),
    "volume-mute": ("🔊 [MÍDIA]", "Mutar / Desmutar áudio"),
    "mic-mute": ("🎙️ [MÍDIA]", "Mutar / Desmutar microfone"),
    "media toggle": ("⏯️ [MÍDIA]", "Play / Pause reprodução de mídia"),
    "media next": ("⏭️ [MÍDIA]", "Próxima faixa de mídia"),
    "media previous": ("⏮️ [MÍDIA]", "Faixa anterior de mídia"),
    "brightness-up": ("☀️ [BRILHO]", "Aumentar brilho da tela"),
    "brightness-down": ("🔅 [BRILHO]", "Diminuir brilho da tela"),

    # Aplicativos Hyprland
    "TERMINAL": ("🚀 [APLICATIVO]", "Abrir Terminal Kitty"),
    "FILE_MANAGER": ("🚀 [APLICATIVO]", "Abrir Gerenciador de Arquivos (Dolphin)"),
    "BROWSER": ("🚀 [APLICATIVO]", "Abrir Navegador Web (Firefox)"),
    "EDITOR": ("🚀 [APLICATIVO]", "Abrir Editor de Texto"),
    "CALCULATOR": ("🚀 [APLICATIVO]", "Abrir Calculadora"),
    "kdeconnect-app": ("📱 [APLICATIVO]", "Abrir KDE Connect (Integração Celular)"),
    "btop": ("📊 [SISTEMA]", "Monitor de Recursos do Sistema (btop)"),
    "keybinds": ("❓ [AJUDA]", "Exibir este menu de atalhos")
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

def extract_hypr_binds():
    items = []
    seen = set()

    if not os.path.exists(BINDS_LUA):
        return items

    with open(BINDS_LUA, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    last_comment = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--") and not stripped.startswith("----") and not stripped.startswith("-- >>"):
            last_comment = stripped.lstrip("-").strip()
            continue

        if "hl.bind(" in line:
            m = re.search(r'hl\.bind\s*\(\s*([^,]+?)\s*,\s*(.+?)\s*\)', line)
            if not m:
                continue

            raw_key = m.group(1).strip()
            raw_action = m.group(2).strip()

            if "digitCode" in raw_key:
                last_comment = ""
                continue

            key = clean_key_name(raw_key)
            if key in seen:
                last_comment = ""
                continue
            seen.add(key)

            category = "⌨️ [HYPRLAND]"
            desc = ""

            for pattern, info in ACTION_MAP.items():
                if pattern in raw_action:
                    category = info[0]
                    desc = info[1]
                    break

            if not desc:
                if last_comment:
                    desc = last_comment
                else:
                    m_cmd = re.search(r'exec_cmd\s*\(\s*["\']?([^"\']+)["\']?\s*\)', raw_action)
                    if m_cmd:
                        desc = m_cmd.group(1).replace("uwsm app -- ", "").strip()
                    else:
                        desc = raw_action.replace("hl.dsp.", "").strip()

            items.append((category, key, desc))
            last_comment = ""
        else:
            if not stripped.startswith("--"):
                last_comment = ""

    # Workspaces numéricos
    items.append(("🗂️ [HYPR: WORKSPACE]", "Super + 1..9", "Alternar para workspace 1 a 9 no monitor"))
    items.append(("🗂️ [HYPR: WORKSPACE]", "Super + Shift + 1..9", "Mover janela para workspace 1 a 9"))
    items.append(("🗂️ [HYPR: WORKSPACE]", "Super + Ctrl + Setas", "Navegar para workspace adjacente"))
    items.append(("🗂️ [HYPR: WORKSPACE]", "Super + Scroll", "Rolar entre workspaces do monitor"))
    items.append(("🖥️ [HYPR: MONITOR]", "Super + 1 / 2", "Focar no Monitor 1 ou Monitor 2"))
    items.append(("🖥️ [HYPR: MONITOR]", "Super + Shift + 1 / 2", "Mover janela para Monitor 1 ou Monitor 2"))

    return items

def get_terminal_kitty_binds():
    return [
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + Enter", "Nova janela de terminal lado a lado (Split)"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + T", "Nova aba de terminal"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + W", "Fechar janela / aba atual do terminal"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + ] / [", "Navegar para a próxima / anterior janela"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + Right / Left", "Navegar para a próxima / anterior aba"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + C / V", "Copiar / Colar texto no terminal"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + + / -", "Aumentar / Diminuir tamanho da fonte"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + Backspace", "Restaurar tamanho padrão da fonte"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + F", "Pesquisar texto no histórico do terminal"),
    ]

def get_dolphin_binds():
    return [
        ("📁 [DOLPHIN: ARQUIVOS]", "Super + E", "Abrir o gerenciador de arquivos Dolphin"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + H", "Exibir / Ocultar arquivos e pastas ocultas"),
        ("📁 [DOLPHIN: ARQUIVOS]", "F4", "Abrir / Fechar terminal integrado na pasta atual"),
        ("📁 [DOLPHIN: ARQUIVOS]", "F3", "Modo de visão dividida (duas pastas lado a lado)"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + T", "Abrir nova aba de navegação"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + L", "Focar e editar barra de endereço / caminho"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + D", "Adicionar pasta atual aos Favoritos"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Alt + Up", "Subir para a pasta pai"),
    ]

def get_browser_binds():
    return [
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + T", "Abrir nova aba"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + W", "Fechar aba atual"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + Shift + T", "Reabrir última aba fechada"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + L / F6", "Focar na barra de endereço / URL"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + Shift + N / P", "Nova janela em modo anônimo / privado"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + Tab / Shift+Tab", "Alternar entre abas do navegador"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + F", "Buscar texto na página web"),
    ]

def extract_kde_binds():
    items = []
    if not os.path.exists(KGLOBAL_SRC):
        return items

    try:
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(KGLOBAL_SRC, encoding="utf-8")
        
        # Módulos de interesse no KDE
        interesting_sections = {
            "kwin": "🪟 [KDE: KWIN]",
            "kmix": "🔊 [KDE: ÁUDIO]",
            "ksmserver": "⚡ [KDE: SESSÃO]",
            "org.kde.spectacle.desktop": "📸 [KDE: CAPTURA]"
        }

        for sec, prefix in interesting_sections.items():
            if not cp.has_section(sec):
                continue
            for opt in cp.options(sec):
                if opt.startswith("_"):
                    continue
                val = cp.get(sec, opt)
                parts = [p.strip() for p in val.split(",")]
                if len(parts) >= 3 and parts[0] != "none" and parts[0]:
                    key = parts[0].replace("\\t", " ou ").replace("Meta", "Super")
                    desc = parts[2]
                    # Limpar nomes feios
                    if "Polonium" in desc or not desc:
                        continue
                    items.append((prefix, key, desc))
    except Exception:
        pass

    return items

def main():
    all_binds = []

    # 1. Hyprland & Noctalia Shell
    all_binds.extend(extract_hypr_binds())

    # 2. Terminal Kitty
    all_binds.extend(get_terminal_kitty_binds())

    # 3. Gerenciador de Arquivos Dolphin
    all_binds.extend(get_dolphin_binds())

    # 4. Navegador Web
    all_binds.extend(get_browser_binds())

    # 5. KDE Plasma (Global)
    kde_binds = extract_kde_binds()
    # Adicionar até 10 atalhos principais do KDE para não poluir
    if kde_binds:
        all_binds.extend(kde_binds[:12])

    for cat, key, desc in all_binds:
        print(f"{cat:<23} │ {key:<30} ➜  {desc}")

if __name__ == "__main__":
    main()
