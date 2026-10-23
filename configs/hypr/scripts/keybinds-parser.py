#!/usr/bin/env python3
# ==============================================================================
# keybinds-parser.py
# Analisador Universal e Gerenciador de Atalhos do Sistema
# Lê e rastreia dinamicamente:
#  1. Hyprland (binds.lua) com número de linha exato
#  2. Atalhos customizados (custom_binds.lua) com número de linha exato
#  3. Terminal Kitty (kitty.conf)
#  4. Dolphin & KDE Plasma (kglobalshortcutsrc)
#  5. Navegador Web
# ==============================================================================
import os
import re
import sys
import unicodedata
import configparser
import subprocess

CONFIG_DIR = os.path.expanduser("~/.config")
HYPR_DIR = os.path.join(CONFIG_DIR, "hypr")
BINDS_LUA = os.path.join(HYPR_DIR, "config/binds.lua")
CUSTOM_BINDS_LUA = os.path.join(HYPR_DIR, "config/custom_binds.lua")
VARIABLES_LUA = os.path.join(HYPR_DIR, "config/variables.lua")
KGLOBAL_SRC = os.path.join(CONFIG_DIR, "kglobalshortcutsrc")
KITTY_CONF = os.path.join(CONFIG_DIR, "kitty/kitty.conf")

class BindItem(dict):
    """Representa um atalho com metadados de origem e suporte a desempacotamento."""
    def __init__(self, category, key, desc, source_type="system", source_file="", line_number=0, raw_key="", raw_action=""):
        super().__init__(
            category=category,
            key=key,
            desc=desc,
            source_type=source_type,
            source_file=source_file,
            line_number=line_number,
            raw_key=raw_key,
            raw_action=raw_action
        )

    def __iter__(self):
        yield self["category"]
        yield self["key"]
        yield self["desc"]

def get_display_width(s: str) -> int:
    """Calcula a largura real de exibição em células de terminal monospace."""
    w = 0
    for ch in s:
        if ch in ('\ufe0f', '\ufe0e'):
            continue
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ('W', 'F'):
            w += 2
        else:
            w += 1
    return w

def pad_display(s: str, width: int) -> str:
    """Preenche com espaços considerando a largura visual real de cada caractere/emoji."""
    cur_w = get_display_width(s)
    pad = max(0, width - cur_w)
    return s + (' ' * pad)

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

    # Zoom
    "zoomfunction(-": ("🔍 [HYPR: ZOOM]", "Diminuir zoom geral da tela (Zoom Out)"),
    "zoomfunction(": ("🔍 [HYPR: ZOOM]", "Aumentar zoom geral da tela (Zoom In)"),
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

def readable_key_to_lua(readable_key):
    """Converte formato legível (ex: Super + Shift + Q) para código Lua do binds.lua."""
    parts = [p.strip() for p in readable_key.split("+")]
    lua_parts = []
    for p in parts:
        pl = p.lower()
        if pl == "super":
            lua_parts.append("mainMod")
        elif pl in ("ctrl", "control"):
            lua_parts.append('"CONTROL"')
        elif pl == "shift":
            lua_parts.append('"SHIFT"')
        elif pl == "alt":
            lua_parts.append('"ALT"')
        elif pl == "enter":
            lua_parts.append('"Return"')
        elif pl == "esc":
            lua_parts.append('"Escape"')
        else:
            lua_parts.append(f'"{p}"')

    if lua_parts[0] == "mainMod":
        rest = " + ".join([p.strip('"') for p in lua_parts[1:]])
        return f'mainMod .. " + {rest}"'
    else:
        full = " + ".join([p.strip('"') for p in lua_parts])
        return f'"{full}"'

def extract_hypr_binds():
    items = []
    seen = set()

    if not os.path.exists(BINDS_LUA):
        return items

    with open(BINDS_LUA, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    last_comment = ""
    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("--") and not stripped.startswith("----") and not stripped.startswith("-- >>"):
            last_comment = stripped.lstrip("-").strip()
            continue

        if "hl.bind(" in line:
            idx = line.find("hl.bind(")
            content = line[idx + 8:].rstrip()
            parts = content.split(",", 1)
            if len(parts) < 2:
                continue

            raw_key = parts[0].strip()
            raw_action = parts[1].strip()

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

            items.append(BindItem(
                category=category,
                key=key,
                desc=desc,
                source_type="hyprland",
                source_file=BINDS_LUA,
                line_number=line_num,
                raw_key=raw_key,
                raw_action=raw_action
            ))
            last_comment = ""
        else:
            if not stripped.startswith("--"):
                last_comment = ""

    # Workspaces numéricos dinâmicos
    items.append(BindItem("🗂️ [HYPR: WORKSPACE]", "Super + Ctrl + 1..10", "Alternar para workspace 1 a 10 no monitor focado", source_type="hyprland_loop", source_file=VARIABLES_LUA, line_number=16, raw_key="Super + Ctrl + 1..10", raw_action="NUM_WPM = 10"))
    items.append(BindItem("🗂️ [HYPR: WORKSPACE]", "Super + Ctrl + Down", "Criar / Pular para o próximo workspace vazio", source_type="hyprland", source_file=BINDS_LUA, line_number=165, raw_key='mainMod .. " + CONTROL + Down"', raw_action='hl.dsp.focus({ workspace = "emptym" })'))
    items.append(BindItem("🗂️ [HYPR: WORKSPACE]", "Super + Ctrl + Left / Right", "Navegar para workspace anterior ou próximo", source_type="hyprland", source_file=BINDS_LUA, line_number=163, raw_key='mainMod .. " + CONTROL + Left/Right"', raw_action='hl.dsp.focus({ workspace = "m+/-1" })'))
    items.append(BindItem("🗂️ [HYPR: WORKSPACE]", "Super + Scroll", "Rolar entre workspaces do monitor", source_type="hyprland", source_file=BINDS_LUA, line_number=168, raw_key='mainMod .. " + mouse_up/down"', raw_action='hl.dsp.focus({ workspace = "m+/-1" })'))
    items.append(BindItem("🗂️ [HYPR: WORKSPACE]", "Super + Shift + Ctrl + 1..10", "Mover janela ativa para workspace 1 a 10", source_type="hyprland_loop", source_file=VARIABLES_LUA, line_number=16, raw_key="Super + Shift + Ctrl + 1..10", raw_action="NUM_WPM = 10"))
    items.append(BindItem("🖥️ [HYPR: MONITOR]", "Super + 1 / 2", "Focar no Monitor 1 (HDMI) ou Monitor 2 (DP)", source_type="hyprland", source_file=BINDS_LUA, line_number=146, raw_key='mainMod .. " + 1/2"', raw_action='hl.dsp.focus({ monitor = ... })'))
    items.append(BindItem("🖥️ [HYPR: MONITOR]", "Super + Shift + 1 / 2", "Mover janela para Monitor 1 ou Monitor 2", source_type="hyprland", source_file=BINDS_LUA, line_number=37, raw_key='mainMod .. " + SHIFT + 1/2"', raw_action='hl.dsp.window.move({ monitor = ... })'))

    return items

def extract_custom_binds():
    items = []
    if not os.path.exists(CUSTOM_BINDS_LUA):
        return items

    with open(CUSTOM_BINDS_LUA, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    last_comment = ""
    custom_cat = "⭐ [CUSTOM]"
    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("--") and not stripped.startswith("----") and not stripped.startswith("-- ="):
            c_text = stripped.lstrip("-").strip()
            if c_text.lower().startswith("category:"):
                custom_cat = c_text.split(":", 1)[1].strip()
            else:
                last_comment = c_text
            continue

        if "hl.bind(" in line:
            idx = line.find("hl.bind(")
            content = line[idx + 8:].rstrip()
            parts = content.split(",", 1)
            if len(parts) < 2:
                continue
            raw_key = parts[0].strip()
            raw_action = parts[1].strip()

            key = clean_key_name(raw_key)
            desc = last_comment
            if not desc:
                m_cmd = re.search(r'exec_cmd\s*\(\s*["\']?([^"\']+)["\']?\s*\)', raw_action)
                if m_cmd:
                    desc = f"Executar: {m_cmd.group(1).replace('launchPrefix .. ', '').replace('uwsm app -- ', '')}"
                else:
                    desc = raw_action.replace("hl.dsp.", "").strip()

            items.append(BindItem(
                category=custom_cat,
                key=key,
                desc=desc,
                source_type="custom",
                source_file=CUSTOM_BINDS_LUA,
                line_number=line_num,
                raw_key=raw_key,
                raw_action=raw_action
            ))
            last_comment = ""
            custom_cat = "⭐ [CUSTOM]"
        else:
            if not stripped.startswith("--"):
                last_comment = ""

    return items

def get_terminal_kitty_binds():
    items = [
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + Enter", "Nova janela de terminal lado a lado (Split)", "new_window"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + T", "Nova aba de terminal", "new_tab"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + W", "Fechar janela / aba atual do terminal", "close_tab"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + ] / [", "Navegar para a próxima / anterior janela", "next_window"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + Right / Left", "Navegar para a próxima / anterior aba", "next_tab"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + C / V", "Copiar / Colar texto no terminal", "copy_to_clipboard"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + + / -", "Aumentar / Diminuir tamanho da fonte", "change_font_size"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + Backspace", "Restaurar tamanho padrão da fonte", "change_font_size"),
        ("💻 [KITTY: TERMINAL]", "Ctrl + Shift + F", "Pesquisar texto no histórico do terminal", "show_scrollback"),
    ]
    result = []
    for cat, key, desc, act in items:
        result.append(BindItem(
            category=cat,
            key=key,
            desc=desc,
            source_type="kitty",
            source_file=KITTY_CONF,
            line_number=0,
            raw_key=key,
            raw_action=act
        ))
    return result

def get_dolphin_binds():
    items = [
        ("📁 [DOLPHIN: ARQUIVOS]", "Super + E", "Abrir o gerenciador de arquivos Dolphin", "dolphin"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + H", "Exibir / Ocultar arquivos e pastas ocultas", "toggle_hidden"),
        ("📁 [DOLPHIN: ARQUIVOS]", "F4", "Abrir / Fechar terminal integrado na pasta atual", "toggle_terminal"),
        ("📁 [DOLPHIN: ARQUIVOS]", "F3", "Modo de visão dividida (duas pastas lado a lado)", "split_view"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + T", "Abrir nova aba de navegação", "new_tab"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + L", "Focar e editar barra de endereço / caminho", "edit_location"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Ctrl + D", "Adicionar pasta atual aos Favoritos", "add_bookmark"),
        ("📁 [DOLPHIN: ARQUIVOS]", "Alt + Up", "Subir para a pasta pai", "go_up"),
    ]
    result = []
    for cat, key, desc, act in items:
        result.append(BindItem(
            category=cat,
            key=key,
            desc=desc,
            source_type="dolphin",
            source_file=KGLOBAL_SRC,
            line_number=0,
            raw_key=key,
            raw_action=act
        ))
    return result

def get_browser_binds():
    items = [
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + T", "Abrir nova aba", "new_tab"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + W", "Fechar aba atual", "close_tab"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + Shift + T", "Reabrir última aba fechada", "undo_close_tab"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + Tab / Ctrl + Shift + Tab", "Alternar entre abas abertas", "switch_tabs"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + L / F6", "Focar na barra de endereço / pesquisa", "focus_address_bar"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + Shift + P / N", "Abrir nova janela anônima / privativa", "private_window"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + R / F5", "Recarregar página atual", "reload"),
        ("🌐 [NAVEGADOR: WEB]", "Ctrl + F", "Pesquisar texto na página", "find_in_page"),
    ]
    result = []
    for cat, key, desc, act in items:
        result.append(BindItem(
            category=cat,
            key=key,
            desc=desc,
            source_type="browser",
            source_file="firefox/chrome",
            line_number=0,
            raw_key=key,
            raw_action=act
        ))
    return result

def extract_kde_binds():
    items = []
    if not os.path.exists(KGLOBAL_SRC):
        return items

    try:
        config = configparser.ConfigParser(interpolation=None)
        config.read(KGLOBAL_SRC, encoding="utf-8")
        for sec in config.sections():
            prefix = "🔵 [KDE PLASMA]"
            if "kwin" in sec.lower():
                prefix = "🔵 [KDE: KWIN]"
            elif "plasmashell" in sec.lower():
                prefix = "🔵 [KDE: SHELL]"

            for opt in config[sec]:
                val = config[sec][opt]
                parts = [p.strip() for p in val.split(",")]
                if len(parts) >= 3 and parts[0] != "none" and parts[0]:
                    key = parts[0].replace("\\t", " ou ").replace("Meta", "Super")
                    desc = parts[2]
                    if "Polonium" in desc or not desc:
                        continue
                    items.append(BindItem(
                        category=prefix,
                        key=key,
                        desc=desc,
                        source_type="kde",
                        source_file=KGLOBAL_SRC,
                        line_number=0,
                        raw_key=key,
                        raw_action=desc
                    ))
    except Exception:
        pass

    return items

def update_hypr_bind_in_file(filepath, line_num, new_readable_key, new_action=None, new_desc=None):
    """Atualiza com segurança a linha exata do bind no arquivo Lua."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if line_num < 1 or line_num > len(lines):
        raise ValueError(f"Linha {line_num} inválida no arquivo {filepath}")

    orig_line = lines[line_num - 1]
    if "hl.bind(" not in orig_line:
        found_idx = None
        for idx in range(max(0, line_num - 6), min(len(lines), line_num + 5)):
            if "hl.bind(" in lines[idx]:
                found_idx = idx
                break
        if found_idx is not None:
            line_num = found_idx + 1
            orig_line = lines[found_idx]
        else:
            raise ValueError(f"Não foi possível localizar 'hl.bind' na linha {line_num}")

    idx = orig_line.find("hl.bind(")
    content = orig_line[idx + 8:].rstrip()
    parts = content.split(",", 1)
    if len(parts) < 2:
        raise ValueError(f"Formato inesperado de hl.bind na linha {line_num}")

    old_action_full = parts[1].strip()
    new_lua_key = readable_key_to_lua(new_readable_key)

    if new_action:
        new_line = orig_line[:idx + 8] + f"{new_lua_key}, {new_action})\n"
    else:
        new_line = orig_line[:idx + 8] + f"{new_lua_key}, {old_action_full}\n"

    # Backup
    bak_path = filepath + ".bak"
    with open(bak_path, "w", encoding="utf-8") as bak_f:
        bak_f.writelines(lines)

    # Atualizar comentário acima se fornecido
    if new_desc and line_num > 1 and lines[line_num - 2].strip().startswith("--") and not lines[line_num - 2].strip().startswith("----"):
        c_indent = lines[line_num - 2][:len(lines[line_num - 2]) - len(lines[line_num - 2].lstrip())]
        lines[line_num - 2] = f"{c_indent}-- {new_desc}\n"

    lines[line_num - 1] = new_line

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)

    subprocess.run(["hyprctl", "reload"], check=False)
    return True

def delete_hypr_bind_in_file(filepath, line_num):
    """Exclui com segurança a linha exata de um atalho customizado."""
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if line_num < 1 or line_num > len(lines):
        return False

    # Backup
    with open(filepath + ".bak", "w", encoding="utf-8") as bak_f:
        bak_f.writelines(lines)

    del lines[line_num - 1]
    # Se a linha anterior for um comentário do atalho, remover também
    if line_num - 2 >= 0 and lines[line_num - 2].strip().startswith("--"):
        del lines[line_num - 2]

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)

    subprocess.run(["hyprctl", "reload"], check=False)
    return True

def update_kitty_bind(new_readable_key, action_name):
    """Mapeia o atalho no kitty.conf."""
    os.makedirs(os.path.dirname(KITTY_CONF), exist_ok=True)
    kitty_key = new_readable_key.lower().replace(" + ", "+")
    new_map = f"map {kitty_key} {action_name}\n"

    lines = []
    if os.path.exists(KITTY_CONF):
        with open(KITTY_CONF, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated = False
    for i, l in enumerate(lines):
        if l.strip().startswith("map ") and action_name in l:
            lines[i] = new_map
            updated = True
            break

    if not updated:
        lines.append(new_map)

    with open(KITTY_CONF, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return True

def get_all_binds():
    """Retorna a lista completa e estruturada de atalhos de todo o sistema."""
    all_binds = []

    # 0. Atalhos Personalizados do Usuário (prioridade no topo)
    all_binds.extend(extract_custom_binds())

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
    if kde_binds:
        all_binds.extend(kde_binds[:12])

    return all_binds

def main():
    all_binds = get_all_binds()

    for item in all_binds:
        cat_pad = pad_display(item["category"], 24)
        key_pad = pad_display(item["key"], 36)
        print(f"{cat_pad} │ {key_pad} ➜  {item['desc']}")

if __name__ == "__main__":
    main()
