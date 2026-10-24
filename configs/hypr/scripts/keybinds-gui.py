#!/usr/bin/env python3
# ==============================================================================
# keybinds-gui.py
# Painel Gráfico Moderno e Dedicado de Atalhos (PySide6 / Qt6 no Wayland)
# 100% Integrado ao Noctalia Shell, Paleta Dinâmica e Configurações do Sistema
#
# Principais Recursos:
#   1. Tema Dinâmico do Noctalia: Carrega paleta do Noctalia (Material You / Wallpaper)
#   2. Proporção e Fontes do Sistema: 60% largura e 65% altura da tela, fontes do sistema
#   3. Otimização de Performance: Modo Daemon para abertura instantânea (<5ms)
#   4. Navegação por TAB sem saltos duplos (percorre filtros de 1 em 1)
#   5. Digitação Global (Type-to-Search) e Navegação com Setas (↑/↓)
#   6. Atalhos Rápidos no Menu:
#      - Ctrl + N: Novo Atalho
#      - F2 ou Ctrl + E: Editar Atalho Selecionado
#      - F5 ou Ctrl + R: Recarregar Sistema e Atalhos
#      - Ctrl + O: Abrir binds.lua
#      - Ctrl + Shift + O: Abrir custom_binds.lua
#      - Esc: Fechar Menu
# ==============================================================================
import sys
import os
import re
import subprocess
from PySide6.QtCore import Qt, QSize, QEvent, QFileSystemWatcher, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QKeySequence, QShortcut, QIcon, QKeyEvent, QFontDatabase
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QFrame, QButtonGroup, QAbstractItemView, QMessageBox,
    QMenu
)

# Caminhos do sistema
CONFIG_DIR = os.path.expanduser("~/.config")
HYPR_DIR = os.path.join(CONFIG_DIR, "hypr")
BINDS_LUA = os.path.join(HYPR_DIR, "config/binds.lua")
CUSTOM_BINDS_LUA = os.path.join(HYPR_DIR, "config/custom_binds.lua")
VARIABLES_LUA = os.path.join(HYPR_DIR, "config/variables.lua")
KITTY_CONF = os.path.join(CONFIG_DIR, "kitty/kitty.conf")
KITTY_THEME = os.path.join(CONFIG_DIR, "kitty/themes/noctalia.conf")
QT6CT_COLORS = os.path.join(CONFIG_DIR, "qt6ct/colors/noctalia.conf")
GTK4_THEME = os.path.join(CONFIG_DIR, "gtk-4.0/noctalia.css")
GTK3_THEME = os.path.join(CONFIG_DIR, "gtk-3.0/noctalia.css")
HYPR_NOCTALIA = os.path.join(CONFIG_DIR, "hypr/noctalia.lua")
SINGLETON_SOCKET = "hypr_keybinds_gui_singleton_socket"

# Importar o parser universal
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

import importlib.util
spec = importlib.util.spec_from_file_location("keybinds_parser", os.path.join(SCRIPT_DIR, "keybinds-parser.py"))
parser_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser_mod)
get_all_binds = parser_mod.get_all_binds
update_hypr_bind_in_file = parser_mod.update_hypr_bind_in_file
delete_hypr_bind_in_file = parser_mod.delete_hypr_bind_in_file
update_kitty_bind = parser_mod.update_kitty_bind
readable_key_to_lua = parser_mod.readable_key_to_lua

# ==============================================================================
# CARREGAMENTO DINÂMICO DO TEMA DO NOCTALIA
# Lê diretamente os tokens oficiais gerados pelo Noctalia Shell (Material You)
# ==============================================================================
def load_noctalia_theme():
    # Paleta padrão segura (Material You Noctalia)
    theme = {
        "DARK_BG": "#1a110e",
        "CARD_BG": "#271e1a",
        "INPUT_BG": "#271e1a",
        "BORDER_COLOR": "#352823",
        "ACCENT_PRIMARY": "#ffb595",
        "ACCENT_PRIMARY_FG": "#542105",
        "ACCENT_SECONDARY": "#e6bead",
        "ACCENT_CORAL": "#ffb4ab",
        "ACCENT_GREEN": "#e6bead",
        "ACCENT_BLUE": "#d2c78f",
        "TEXT_COLOR": "#f1dfd8",
        "TEXT_MUTED": "#b3a5a0",
        "HIGHLIGHT_BG": "#392b26"
    }

    # 1. Fonte primária oficial: GTK 4 ou GTK 3 (gerado pelo processador de templates do Noctalia)
    css_file = GTK4_THEME if os.path.exists(GTK4_THEME) else (GTK3_THEME if os.path.exists(GTK3_THEME) else None)
    if css_file:
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                content = f.read()
            kv = {}
            for m in re.finditer(r'@define-color\s+([a-zA-Z0-9_-]+)\s+([^;]+);', content):
                kv[m.group(1).replace('-', '_')] = m.group(2).strip()
            for m in re.finditer(r'--([a-zA-Z0-9_-]+):\s*([^;]+);', content):
                kv[m.group(1).replace('-', '_')] = m.group(2).strip()

            if 'window_bg_color' in kv: theme['DARK_BG'] = kv['window_bg_color']
            if 'window_fg_color' in kv: theme['TEXT_COLOR'] = kv['window_fg_color']
            if 'card_bg_color' in kv: theme['CARD_BG'] = kv['card_bg_color']
            if 'popover_bg_color' in kv: theme['INPUT_BG'] = kv['popover_bg_color']
            elif 'card_bg_color' in kv: theme['INPUT_BG'] = kv['card_bg_color']
            if 'accent_color' in kv: theme['ACCENT_PRIMARY'] = kv['accent_color']
            if 'accent_fg_color' in kv: theme['ACCENT_PRIMARY_FG'] = kv['accent_fg_color']
            if 'warning_color' in kv: theme['ACCENT_BLUE'] = kv['warning_color']
            if 'success_color' in kv: theme['ACCENT_GREEN'] = kv['success_color']
            if 'destructive_bg_color' in kv: theme['ACCENT_CORAL'] = kv['destructive_bg_color']
            elif 'error_color' in kv: theme['ACCENT_CORAL'] = kv['error_color']
        except Exception as e:
            print(f"[Noctalia Theme] Erro ao ler {css_file}: {e}")

    # 2. Fonte secundária: Hyprland Noctalia Lua
    elif os.path.exists(HYPR_NOCTALIA):
        try:
            with open(HYPR_NOCTALIA, "r", encoding="utf-8") as f:
                content = f.read()
            for m in re.finditer(r'local\s+([a-zA-Z0-9_]+)\s*=\s*"rgb\(([a-fA-F0-9]{6})\)"', content):
                k, hex_c = m.group(1), f"#{m.group(2)}"
                if k == "primary": theme['ACCENT_PRIMARY'] = hex_c
                elif k == "surface": theme['DARK_BG'] = hex_c
                elif k == "on_surface": theme['TEXT_COLOR'] = hex_c
                elif k == "secondary": theme['ACCENT_SECONDARY'] = hex_c
                elif k == "error": theme['ACCENT_CORAL'] = hex_c
        except Exception as e:
            print(f"[Noctalia Theme] Erro ao ler {HYPR_NOCTALIA}: {e}")

    # 3. Fonte complementar: Kitty Themes
    if os.path.exists(KITTY_THEME):
        try:
            with open(KITTY_THEME, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        k, v = parts[0], parts[1]
                        if k == "selection_background": theme["HIGHLIGHT_BG"] = v
                        elif k in ("active_border_color", "color2") and not css_file: theme["ACCENT_PRIMARY"] = v
        except Exception as e:
            print(f"[Noctalia Theme] Erro ao ler {KITTY_THEME}: {e}")

    # 4. Cálculo de contraste harmonioso para bordas e tons atenuados
    bg = QColor(theme["DARK_BG"])
    fg = QColor(theme["TEXT_COLOR"])
    is_dark = bg.lightness() < 128

    if is_dark:
        theme['BORDER_COLOR'] = QColor(theme['CARD_BG']).lighter(135).name()
        theme['TEXT_MUTED'] = fg.darker(135).name()
        theme['HIGHLIGHT_BG'] = QColor(theme['CARD_BG']).lighter(145).name()
    else:
        theme['BORDER_COLOR'] = QColor(theme['CARD_BG']).darker(115).name()
        theme['TEXT_MUTED'] = fg.lighter(135).name()
        theme['HIGHLIGHT_BG'] = QColor(theme['CARD_BG']).darker(115).name()

    return theme

def build_stylesheet(t):
    """Gera stylesheet Qt (QSS) usando tamanhos relativos e cores dinâmicas."""
    return f"""
QWidget#RootWindow, QDialog#AddShortcutDialog, QDialog#EditShortcutDialog {{
    background-color: {t['DARK_BG']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 16px;
}}

QLabel#TitleLabel {{
    color: {t['TEXT_COLOR']};
    font-size: 1.35em;
    font-weight: bold;
}}

QLabel#SubtitleLabel {{
    color: {t['TEXT_MUTED']};
    font-size: 0.9em;
}}

QLabel#SectionLabel {{
    color: {t['ACCENT_SECONDARY']};
    font-weight: bold;
    font-size: 0.95em;
}}

QLineEdit, QComboBox {{
    background-color: {t['INPUT_BG']};
    color: {t['TEXT_COLOR']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 7px 12px;
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {t['ACCENT_PRIMARY']};
}}

QPushButton.HeaderAction {{
    background-color: {t['CARD_BG']};
    color: {t['TEXT_COLOR']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 500;
}}

QPushButton.HeaderAction:hover {{
    background-color: {t['INPUT_BG']};
    border-color: {t['ACCENT_PRIMARY']};
    color: {t['ACCENT_PRIMARY']};
}}

QPushButton.PrimaryAction {{
    background-color: {t['ACCENT_PRIMARY']};
    color: {t.get('ACCENT_PRIMARY_FG', t['DARK_BG'])};
    border: 1px solid {t['ACCENT_PRIMARY']};
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: bold;
}}

QPushButton.PrimaryAction:hover {{
    opacity: 0.9;
    border-color: {t['ACCENT_SECONDARY']};
}}

QPushButton.DangerAction {{
    background-color: #3d1e24;
    color: {t['ACCENT_CORAL']};
    border: 1px solid #662d35;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}}

QPushButton.SecondaryAction {{
    background-color: {t['CARD_BG']};
    color: {t['TEXT_MUTED']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 8px 16px;
}}

QPushButton.FilterChip {{
    background-color: {t['CARD_BG']};
    color: {t['TEXT_MUTED']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 5px 11px;
    font-weight: 500;
}}

QPushButton.FilterChip:hover {{
    background-color: {t['INPUT_BG']};
    color: {t['TEXT_COLOR']};
    border-color: {t['ACCENT_PRIMARY']};
}}

QPushButton.FilterChip:checked {{
    background-color: {t['ACCENT_PRIMARY']};
    color: {t.get('ACCENT_PRIMARY_FG', t['DARK_BG'])};
    font-weight: bold;
    border-color: {t['ACCENT_PRIMARY']};
}}

QTableWidget#BindsTable {{
    background-color: {t['CARD_BG']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 10px;
    gridline-color: transparent;
    color: {t['TEXT_COLOR']};
    selection-background-color: {t['HIGHLIGHT_BG']};
    selection-color: {t['TEXT_COLOR']};
}}

QTableWidget#BindsTable::item {{
    padding: 8px 6px;
    border-bottom: 1px solid {t['DARK_BG']};
}}

QTableWidget#BindsTable::item:selected {{
    background-color: {t['HIGHLIGHT_BG']};
    border-left: 3px solid {t['ACCENT_PRIMARY']};
}}

QHeaderView::section {{
    background-color: {t['DARK_BG']};
    color: {t['ACCENT_SECONDARY']};
    font-weight: bold;
    padding: 6px;
    border: none;
    border-bottom: 2px solid {t['BORDER_COLOR']};
}}

QScrollBar:vertical {{
    background: {t['DARK_BG']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {t['BORDER_COLOR']};
    min-height: 24px;
    border-radius: 4px;
}}

QLabel#FooterLabel {{
    color: {t['TEXT_MUTED']};
    font-size: 0.9em;
}}

QCheckBox {{
    color: {t['TEXT_COLOR']};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 4px;
    background-color: {t['INPUT_BG']};
}}

QCheckBox::indicator:checked {{
    background-color: {t['ACCENT_PRIMARY']};
    border-color: {t['ACCENT_PRIMARY']};
}}
"""

def open_file_in_editor(file_path, line_number=0):
    if not os.path.exists(file_path):
        return False
    editors = [
        ("kwrite", ["kwrite", "--line", str(line_number), file_path]),
        ("kate", ["kate", "--line", str(line_number), file_path]),
        ("gnome-text-editor", ["gnome-text-editor", f"+{line_number}", file_path]),
        ("code", ["code", "-g", f"{file_path}:{line_number}"]),
    ]
    for name, cmd in editors:
        if subprocess.run(["which", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            subprocess.Popen(cmd if line_number > 0 else [name, file_path])
            return True
    subprocess.Popen(["kitty", "-e", "nano", f"+{line_number}", file_path] if line_number > 0 else ["kitty", "-e", "nano", file_path])
    return True

class SearchLineEdit(QLineEdit):
    """Campo de busca com delegação limpa de teclas para navegação e alternância."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window_ref = None

    def focusNextPrevChild(self, next):
        """Interrompe a propagação do Tab e altera a categoria estritamente de 1 em 1."""
        if self.window_ref:
            self.window_ref.cycle_category(1 if next else -1)
            return True
        return super().focusNextPrevChild(next)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Down:
            if self.window_ref:
                self.window_ref.move_table_selection(1)
                return
        elif key == Qt.Key.Key_Up:
            if self.window_ref:
                self.window_ref.move_table_selection(-1)
                return
        elif key == Qt.Key.Key_PageDown:
            if self.window_ref:
                self.window_ref.move_table_selection(8)
                return
        elif key == Qt.Key.Key_PageUp:
            if self.window_ref:
                self.window_ref.move_table_selection(-8)
                return
        elif key == Qt.Key.Key_Escape:
            if self.window_ref:
                self.window_ref.close()
                return

        super().keyPressEvent(event)

class EditShortcutDialog(QDialog):
    """Modal para Editar um Atalho Específico e sua Linha de Origem."""
    def __init__(self, bind_item, theme, parent=None):
        super().__init__(parent)
        self.setObjectName("EditShortcutDialog")
        self.bind_item = bind_item
        self.theme = theme
        self.setWindowTitle("Editar Atalho Específico")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.resize(640, 540)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel(f"✏️  Editar Atalho: {self.bind_item['key']}", self)
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        source_file = self.bind_item.get("source_file", "")
        line_num = self.bind_item.get("line_number", 0)
        source_type = self.bind_item.get("source_type", "system")

        origin_text = f"<b>Origem:</b> {source_type.upper()}"
        if source_file:
            short_path = source_file.replace(os.path.expanduser("~"), "~")
            origin_text += f" &nbsp;•&nbsp; <code>{short_path}:{line_num}</code>" if line_num > 0 else f" &nbsp;•&nbsp; <code>{short_path}</code>"

        lbl_origin = QLabel(origin_text, self)
        lbl_origin.setStyleSheet(f"background-color: {self.theme['INPUT_BG']}; border: 1px solid {self.theme['BORDER_COLOR']}; border-radius: 6px; padding: 6px 12px; color: {self.theme['ACCENT_PRIMARY']};")
        layout.addWidget(lbl_origin)

        lbl_mod = QLabel("1. Combinação de Teclas:", self)
        lbl_mod.setObjectName("SectionLabel")
        layout.addWidget(lbl_mod)

        mod_box = QHBoxLayout()
        self.chk_super = QCheckBox("Super", self)
        self.chk_ctrl = QCheckBox("Ctrl", self)
        self.chk_shift = QCheckBox("Shift", self)
        self.chk_alt = QCheckBox("Alt", self)

        cur_key = self.bind_item['key']
        cur_parts = [p.strip().lower() for p in cur_key.split("+")]

        self.chk_super.setChecked("super" in cur_parts)
        self.chk_ctrl.setChecked("ctrl" in cur_parts or "control" in cur_parts)
        self.chk_shift.setChecked("shift" in cur_parts)
        self.chk_alt.setChecked("alt" in cur_parts)

        main_key = ""
        for p in cur_key.split("+"):
            p_strip = p.strip()
            if p_strip.lower() not in ("super", "ctrl", "control", "shift", "alt"):
                main_key = p_strip
                break

        for c in (self.chk_super, self.chk_ctrl, self.chk_shift, self.chk_alt):
            c.stateChanged.connect(self.update_preview)
            mod_box.addWidget(c)
        mod_box.addStretch()
        layout.addLayout(mod_box)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Tecla Principal:"), 0, 0)
        self.key_input = QLineEdit(self)
        self.key_input.setText(main_key)
        self.key_input.setPlaceholderText("Ex: Q, E, Return, Space, 5...")
        self.key_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.key_input, 0, 1)

        grid.addWidget(QLabel("Descrição da Ação:"), 1, 0)
        self.desc_input = QLineEdit(self)
        self.desc_input.setText(self.bind_item['desc'])
        self.desc_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.desc_input, 1, 1)

        grid.addWidget(QLabel("Comando / Ação:"), 2, 0)
        self.action_input = QLineEdit(self)
        self.action_input.setText(self.bind_item.get("raw_action", ""))
        self.action_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.action_input, 2, 1)

        layout.addLayout(grid)

        lbl_prev = QLabel("Pré-visualização da Linha Atualizada:", self)
        lbl_prev.setObjectName("SectionLabel")
        layout.addWidget(lbl_prev)

        self.preview_box = QLabel(self)
        self.preview_box.setStyleSheet(f"background-color: {self.theme['INPUT_BG']}; border: 1px solid {self.theme['BORDER_COLOR']}; border-radius: 8px; padding: 10px; font-family: monospace; color: {self.theme['ACCENT_GREEN']};")
        self.preview_box.setWordWrap(True)
        layout.addWidget(self.preview_box)

        btn_box = QHBoxLayout()
        if self.bind_item.get("source_type") == "custom":
            btn_del = QPushButton("🗑️ Excluir Atalho", self)
            btn_del.setProperty("class", "DangerAction")
            btn_del.clicked.connect(self.delete_shortcut)
            btn_box.addWidget(btn_del)

        if source_file and os.path.exists(source_file):
            btn_open_file = QPushButton("📝 Abrir nesta Linha no Editor", self)
            btn_open_file.setProperty("class", "SecondaryAction")
            btn_open_file.clicked.connect(self.open_at_line)
            btn_box.addWidget(btn_open_file)

        btn_box.addStretch()
        btn_cancel = QPushButton("Cancelar", self)
        btn_cancel.setProperty("class", "SecondaryAction")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Salvar Alteração", self)
        btn_save.setProperty("class", "PrimaryAction")
        btn_save.clicked.connect(self.save_changes)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)
        self.update_preview()

    def get_readable_combo(self):
        mods = []
        if self.chk_super.isChecked(): mods.append("Super")
        if self.chk_ctrl.isChecked(): mods.append("Ctrl")
        if self.chk_shift.isChecked(): mods.append("Shift")
        if self.chk_alt.isChecked(): mods.append("Alt")
        key = self.key_input.text().strip() or "X"
        mods.append(key)
        return " + ".join(mods)

    def update_preview(self):
        readable = self.get_readable_combo()
        lua_key = readable_key_to_lua(readable)
        action = self.action_input.text().strip() or self.bind_item.get("raw_action", "")
        desc = self.desc_input.text().strip()
        stype = self.bind_item.get("source_type")

        if stype in ("hyprland", "custom"):
            prev = f"-- {desc}\nhl.bind({lua_key}, {action})"
        elif stype == "kitty":
            prev = f"map {readable.lower().replace(' + ', '+')} {action}"
        else:
            prev = f"[{readable}] ➜ {desc} ({action})"
        self.preview_box.setText(prev)

    def open_at_line(self):
        source_file = self.bind_item.get("source_file", "")
        line_num = self.bind_item.get("line_number", 0)
        if source_file:
            open_file_in_editor(source_file, line_num)

    def save_changes(self):
        new_combo = self.get_readable_combo()
        new_desc = self.desc_input.text().strip()
        new_action = self.action_input.text().strip()
        stype = self.bind_item.get("source_type")
        source_file = self.bind_item.get("source_file")
        line_num = self.bind_item.get("line_number", 0)

        try:
            if stype in ("hyprland", "custom") and line_num > 0 and source_file:
                update_hypr_bind_in_file(source_file, line_num, new_combo, new_action, new_desc)
                self.accept()
            elif stype == "kitty":
                action_name = self.bind_item.get("raw_action", "")
                update_kitty_bind(new_combo, action_name)
                self.accept()
            elif stype == "hyprland_loop":
                QMessageBox.information(
                    self, "Workspaces Dinâmicos",
                    f"Workspaces são gerados dinamicamente por NUM_WPM em:\n{VARIABLES_LUA}"
                )
                self.reject()
            else:
                QMessageBox.warning(
                    self, "Aviso",
                    f"Este atalho pertence a ({stype}). Para modificá-lo, crie um atalho personalizado no Hyprland!"
                )
                self.reject()
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def delete_shortcut(self):
        source_file = self.bind_item.get("source_file")
        line_num = self.bind_item.get("line_number", 0)
        if source_file and line_num > 0:
            if delete_hypr_bind_in_file(source_file, line_num):
                self.accept()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir o atalho.")

class AddShortcutDialog(QDialog):
    """Modal Interativo para Criar e Salvar Novo Atalho no Hyprland."""
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.setObjectName("AddShortcutDialog")
        self.theme = theme
        self.setWindowTitle("Cadastrar Novo Atalho")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.resize(600, 520)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("➕  Criar Novo Atalho no Hyprland", self)
        title.setObjectName("TitleLabel")
        desc = QLabel("O novo atalho será salvo em <code>custom_binds.lua</code> e ativado imediatamente.", self)
        desc.setObjectName("SubtitleLabel")
        layout.addWidget(title)
        layout.addWidget(desc)

        lbl_mod = QLabel("1. Teclas Modificadoras:", self)
        lbl_mod.setObjectName("SectionLabel")
        layout.addWidget(lbl_mod)

        mod_box = QHBoxLayout()
        self.chk_super = QCheckBox("Super", self)
        self.chk_super.setChecked(True)
        self.chk_ctrl = QCheckBox("Ctrl", self)
        self.chk_shift = QCheckBox("Shift", self)
        self.chk_alt = QCheckBox("Alt", self)

        for c in (self.chk_super, self.chk_ctrl, self.chk_shift, self.chk_alt):
            c.stateChanged.connect(self.update_preview)
            mod_box.addWidget(c)
        mod_box.addStretch()
        layout.addLayout(mod_box)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("2. Tecla Principal:"), 0, 0)
        self.key_input = QLineEdit(self)
        self.key_input.setPlaceholderText("Ex: W, O, Return, Space, Tab, Left, 5, F2...")
        self.key_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.key_input, 0, 1)

        grid.addWidget(QLabel("3. Categoria:"), 1, 0)
        self.cat_combo = QComboBox(self)
        self.cat_combo.addItems([
            "🚀 [APLICATIVO]",
            "🗂️ [HYPR: WORKSPACE]",
            "🪟 [HYPR: JANELA]",
            "🌌 [NOCTALIA]",
            "⭐ [CUSTOM]"
        ])
        grid.addWidget(self.cat_combo, 1, 1)

        grid.addWidget(QLabel("4. Tipo de Ação:"), 2, 0)
        self.action_type_combo = QComboBox(self)
        self.action_type_combo.addItems([
            "Abrir Aplicativo / Executar Comando",
            "Focar Workspace no Monitor Atual (m~N)",
            "Mover Janela para Workspace (m~N)",
            "Ação do Noctalia (Shell)",
            "Comando Lua Livre do Hyprland"
        ])
        self.action_type_combo.currentIndexChanged.connect(self.on_action_type_changed)
        grid.addWidget(self.action_type_combo, 2, 1)

        self.action_param_label = QLabel("Comando / App:")
        grid.addWidget(self.action_param_label, 3, 0)
        self.action_param_input = QLineEdit(self)
        self.action_param_input.setPlaceholderText("Ex: obs, spotify, discord, telegram-desktop, code...")
        self.action_param_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.action_param_input, 3, 1)

        grid.addWidget(QLabel("5. Descrição:"), 4, 0)
        self.desc_input = QLineEdit(self)
        self.desc_input.setPlaceholderText("Ex: Abrir OBS Studio ou Focar Workspace 5")
        self.desc_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.desc_input, 4, 1)

        layout.addLayout(grid)

        lbl_prev = QLabel("Pré-visualização do Atalho Gerado:", self)
        lbl_prev.setObjectName("SectionLabel")
        layout.addWidget(lbl_prev)

        self.preview_box = QLabel(self)
        self.preview_box.setStyleSheet(f"background-color: {self.theme['INPUT_BG']}; border: 1px solid {self.theme['BORDER_COLOR']}; border-radius: 8px; padding: 10px; font-family: monospace; color: {self.theme['ACCENT_GREEN']};")
        self.preview_box.setWordWrap(True)
        layout.addWidget(self.preview_box)

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancelar", self)
        btn_cancel.setProperty("class", "SecondaryAction")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Salvar e Ativar Atalho", self)
        btn_save.setProperty("class", "PrimaryAction")
        btn_save.clicked.connect(self.save_shortcut)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        self.update_preview()

    def on_action_type_changed(self, idx):
        if idx == 0:
            self.action_param_label.setText("Comando / App:")
            self.action_param_input.setPlaceholderText("Ex: obs, spotify, discord, code...")
            self.cat_combo.setCurrentIndex(0)
        elif idx == 1:
            self.action_param_label.setText("Número Workspace:")
            self.action_param_input.setPlaceholderText("Ex: 5 (1 a 10)")
            self.cat_combo.setCurrentIndex(1)
        elif idx == 2:
            self.action_param_label.setText("Número Workspace:")
            self.action_param_input.setPlaceholderText("Ex: 5 (1 a 10)")
            self.cat_combo.setCurrentIndex(1)
        elif idx == 3:
            self.action_param_label.setText("Mensagem Noctalia:")
            self.action_param_input.setPlaceholderText("Ex: panel-toggle launcher...")
            self.cat_combo.setCurrentIndex(3)
        elif idx == 4:
            self.action_param_label.setText("Código Lua:")
            self.action_param_input.setPlaceholderText("Ex: hl.dsp.window.fullscreen()")
            self.cat_combo.setCurrentIndex(4)
        self.update_preview()

    def get_combo_string(self):
        readable = self.get_readable_combo()
        return readable_key_to_lua(readable)

    def get_readable_combo(self):
        mods = []
        if self.chk_super.isChecked(): mods.append("Super")
        if self.chk_ctrl.isChecked(): mods.append("Ctrl")
        if self.chk_shift.isChecked(): mods.append("Shift")
        if self.chk_alt.isChecked(): mods.append("Alt")
        key = self.key_input.text().strip() or "X"
        mods.append(key)
        return " + ".join(mods)

    def get_action_code(self):
        idx = self.action_type_combo.currentIndex()
        param = self.action_param_input.text().strip()
        if idx == 0:
            return f'hl.dsp.exec_cmd(launchPrefix .. "{param or "app"}")'
        elif idx == 1:
            ws = param or "5"
            return f'hl.dsp.focus({{ workspace = "m~{ws}" }})'
        elif idx == 2:
            ws = param or "5"
            return f'hl.dsp.window.move({{ workspace = "m~{ws}" }})'
        elif idx == 3:
            return f'hl.dsp.exec_cmd("noctalia msg {param}")'
        elif idx == 4:
            return param or 'hl.dsp.window.fullscreen()'
        return 'hl.dsp.window.fullscreen()'

    def update_preview(self):
        readable = self.get_readable_combo()
        combo_lua = self.get_combo_string()
        action_lua = self.get_action_code()
        desc = self.desc_input.text().strip() or "Ação personalizada"
        cat = self.cat_combo.currentText()
        preview_text = f"-- category: {cat}\n-- {desc}\nhl.bind({combo_lua}, {action_lua})"
        self.preview_box.setText(preview_text)

    def save_shortcut(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Aviso", "Por favor, digite a tecla principal do atalho!")
            return

        desc = self.desc_input.text().strip() or f"Ação ({self.get_readable_combo()})"
        cat = self.cat_combo.currentText()
        combo_lua = self.get_combo_string()
        action_lua = self.get_action_code()
        block = f"\n-- category: {cat}\n-- {desc}\nhl.bind({combo_lua}, {action_lua})\n"

        try:
            with open(CUSTOM_BINDS_LUA, "a", encoding="utf-8") as f:
                f.write(block)
            subprocess.run(["hyprctl", "reload"], check=False)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar atalho: {e}")

# ==============================================================================
# JANELA PRINCIPAL DO EXPLORADOR DE ATALHOS
# ==============================================================================
class KeybindsWindow(QWidget):
    def __init__(self, is_daemon=False):
        super().__init__()
        self.setObjectName("RootWindow")
        self.is_daemon = is_daemon
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.theme = load_noctalia_theme()
        self.active_category = "Todos"
        self.displayed_binds = []
        self.chip_buttons = []
        
        self.load_binds()
        self.setup_ui()
        self.populate_table(self.raw_binds)
        self.setup_keyboard_shortcuts()
        self.setup_theme_watcher()

    def setup_theme_watcher(self):
        """Monitora em tempo real alterações nos arquivos de tema do Noctalia."""
        self.theme_watcher = QFileSystemWatcher(self)
        watch_files = [GTK4_THEME, GTK3_THEME, HYPR_NOCTALIA, KITTY_THEME]
        for f in watch_files:
            if os.path.exists(f):
                self.theme_watcher.addPath(f)
        self.theme_watcher.fileChanged.connect(self.on_theme_file_changed)

    def on_theme_file_changed(self, path):
        # Pequeno atraso para aguardar a finalização de escritas atômicas pelo Noctalia
        QTimer.singleShot(80, lambda: self._handle_file_changed(path))

    def _handle_file_changed(self, path):
        if os.path.exists(path) and path not in self.theme_watcher.files():
            self.theme_watcher.addPath(path)
        self.apply_theme()

    def apply_theme(self, new_theme=None):
        """Re-aplica dinamicamente a paleta atualizada do Noctalia em todos os componentes."""
        if new_theme is None:
            self.theme = load_noctalia_theme()
        else:
            self.theme = new_theme

        # 1. Atualizar stylesheet global da aplicação
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(self.theme))

        # 2. Forçar re-polimento do estilo da janela
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

        # 3. Atualizar estilos com propriedades inline
        if hasattr(self, 'files_menu'):
            self.files_menu.setStyleSheet(
                f"background-color: {self.theme['CARD_BG']}; "
                f"color: {self.theme['TEXT_COLOR']}; "
                f"border: 1px solid {self.theme['BORDER_COLOR']};"
            )
        if hasattr(self, 'banner_label'):
            self.banner_label.setStyleSheet(
                f"background-color: {self.theme['INPUT_BG']}; "
                f"color: {self.theme['ACCENT_GREEN']}; "
                f"border: 1px solid {self.theme['BORDER_COLOR']}; "
                f"border-radius: 6px; padding: 6px 12px; font-weight: 500;"
            )

        # 4. Atualizar cores de todos os itens da tabela
        self.update_table_item_colors()

    def update_table_item_colors(self):
        """Atualiza instantaneamente os tons de todas as linhas já renderizadas."""
        if not hasattr(self, 'table'):
            return
        self.table.setUpdatesEnabled(False)
        for row in range(self.table.rowCount()):
            item_cat = self.table.item(row, 0)
            if item_cat:
                t = item_cat.text().upper()
                if "CUSTOM" in t:
                    item_cat.setForeground(QColor(self.theme['ACCENT_CORAL']))
                elif any(k in t for k in ("HYPR", "JANELA", "MONITOR", "WORKSPACE")):
                    item_cat.setForeground(QColor(self.theme['TEXT_COLOR']))
                else:
                    item_cat.setForeground(QColor(self.theme['ACCENT_GREEN']))

            item_key = self.table.item(row, 1)
            if item_key:
                item_key.setForeground(QColor(self.theme['ACCENT_PRIMARY']))

            item_desc = self.table.item(row, 2)
            if item_desc:
                item_desc.setForeground(QColor(self.theme['TEXT_COLOR']))

            item_src = self.table.item(row, 3)
            if item_src:
                item_src.setForeground(QColor(self.theme['ACCENT_BLUE']))

            item_act = self.table.item(row, 4)
            if item_act:
                is_exec = "↵" in item_act.text() or "▶" in item_act.text()
                item_act.setForeground(QColor(self.theme['ACCENT_GREEN'] if is_exec else self.theme['ACCENT_SECONDARY']))

        self.table.setUpdatesEnabled(True)
        self.table.viewport().update()

    def load_binds(self):
        self.raw_binds = get_all_binds()

    def setup_ui(self):
        # Tamanho relativo à tela (60% largura, 65% altura)
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            target_w = max(800, min(1400, int(geo.width() * 0.60)))
            target_h = max(550, min(900, int(geo.height() * 0.65)))
            self.resize(target_w, target_h)
        else:
            self.resize(1140, 720)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Header (Título, Subtítulo e Botões de Gestão com Atalhos Visíveis)
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title = QLabel("⌨️  Central de Atalhos do Sistema", self)
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Hyprland • Workspaces • Noctalia • Terminal Kitty • Dolphin • KDE", self)
        subtitle.setObjectName("SubtitleLabel")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Botão: Novo Atalho (Ctrl+N)
        btn_add = QPushButton("➕ Novo Atalho (Ctrl+N)", self)
        btn_add.setProperty("class", "HeaderAction")
        btn_add.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(btn_add)

        # Botão: Editar Atalho Selecionado (F2)
        self.btn_edit_selected = QPushButton("✏️ Editar (F2)", self)
        self.btn_edit_selected.setProperty("class", "HeaderAction")
        self.btn_edit_selected.clicked.connect(self.on_edit_selected)
        header_layout.addWidget(self.btn_edit_selected)

        # Botão: Menu de Arquivos de Binds (Ctrl+O)
        btn_files = QPushButton("📄 Binds (Ctrl+O) ▾", self)
        btn_files.setProperty("class", "HeaderAction")
        files_menu = QMenu(self)
        files_menu.setStyleSheet(f"background-color: {self.theme['CARD_BG']}; color: {self.theme['TEXT_COLOR']}; border: 1px solid {self.theme['BORDER_COLOR']};")

        act_binds = files_menu.addAction("📄 Abrir binds.lua (Atalhos do Hyprland) [Ctrl+O]")
        act_binds.triggered.connect(lambda: open_file_in_editor(BINDS_LUA, 1))

        act_custom = files_menu.addAction("⭐ Abrir custom_binds.lua (Atalhos do Usuário) [Ctrl+Shift+O]")
        act_custom.triggered.connect(lambda: open_file_in_editor(CUSTOM_BINDS_LUA, 1))

        act_vars = files_menu.addAction("⚙️ Abrir variables.lua (Workspaces & Monitores)")
        act_vars.triggered.connect(lambda: open_file_in_editor(VARIABLES_LUA, 1))

        act_kitty = files_menu.addAction("💻 Abrir kitty.conf (Atalhos do Terminal)")
        act_kitty.triggered.connect(lambda: open_file_in_editor(KITTY_CONF, 1))

        btn_files.setMenu(files_menu)
        header_layout.addWidget(btn_files)

        # Botão: Recarregar (F5 / Ctrl+R)
        btn_reload = QPushButton("🔄 Recarregar (F5)", self)
        btn_reload.setProperty("class", "HeaderAction")
        btn_reload.clicked.connect(self.reload_system_binds)
        header_layout.addWidget(btn_reload)

        # Dica ESC
        esc_hint = QLabel("<b>ESC</b> Fechar", self)
        esc_hint.setObjectName("FooterLabel")
        header_layout.addWidget(esc_hint)

        main_layout.addLayout(header_layout)

        # Banner de Notificação
        self.banner_label = QLabel("", self)
        self.banner_label.setStyleSheet(f"background-color: {self.theme['INPUT_BG']}; color: {self.theme['ACCENT_GREEN']}; border: 1px solid {self.theme['BORDER_COLOR']}; border-radius: 6px; padding: 6px 12px; font-weight: 500;")
        self.banner_label.setVisible(False)
        main_layout.addWidget(self.banner_label)

        # 2. Barra de Busca Inteligente
        self.search_input = SearchLineEdit(self)
        self.search_input.window_ref = self
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍  Digite para filtrar por atalho, categoria, arquivo ou comando (ex: fechar, terminal, workspace, f1)...")
        self.search_input.textChanged.connect(self.filter_binds)
        main_layout.addWidget(self.search_input)

        # 3. Chips de Categoria
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)

        categories = [
            ("Todos", "✨ Todos"),
            ("CUSTOM", "⭐ Customizados"),
            ("JANELA", "🪟 Janelas"),
            ("WORKSPACE", "🗂️ Workspaces"),
            ("MONITOR", "🖥️ Monitores"),
            ("NOCTALIA", "🌌 Noctalia"),
            ("APLICATIVO", "🚀 Aplicativos"),
            ("TERMINAL", "💻 Kitty"),
            ("DOLPHIN", "📁 Dolphin"),
            ("KDE", "🔵 KDE"),
        ]

        self.chip_group = QButtonGroup(self)
        self.chip_group.setExclusive(True)
        self.chip_buttons = []

        for cat_id, cat_label in categories:
            btn = QPushButton(cat_label, self)
            btn.setProperty("class", "FilterChip")
            btn.setCheckable(True)
            if cat_id == "Todos":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, c=cat_id: self.on_category_clicked(c))
            self.chip_group.addButton(btn)
            self.chip_buttons.append((cat_id, btn))
            chips_layout.addWidget(btn)

        chips_layout.addStretch()
        main_layout.addLayout(chips_layout)

        # 4. Tabela de Atalhos
        self.table = QTableWidget(self)
        self.table.setObjectName("BindsTable")
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "CATEGORIA", "ATALHO / COMBINAÇÃO", "DESCRIÇÃO DA AÇÃO", "ARQUIVO DE ORIGEM", "AÇÃO"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.table.installEventFilter(self)
        main_layout.addWidget(self.table)

        self.search_input.returnPressed.connect(self.execute_selected)

        # 5. Rodapé Informativo
        footer_layout = QHBoxLayout()
        self.count_label = QLabel(f"Total de atalhos catalogados: {len(self.raw_binds)}", self)
        self.count_label.setObjectName("FooterLabel")
        footer_layout.addWidget(self.count_label)
        footer_layout.addStretch()

        tip_arrow = QLabel(
            "<span style='color:#bcc2ff;'>↑/↓</span> Navegar &nbsp;&nbsp; "
            "<span style='color:#bcc2ff;'>Tab</span> Alternar Filtro &nbsp;&nbsp; "
            "<span style='color:#bcc2ff;'>Ctrl+N</span> Novo &nbsp;&nbsp; "
            "<span style='color:#bcc2ff;'>F2</span> Editar &nbsp;&nbsp; "
            "<span style='color:#bcc2ff;'>F5</span> Recarregar &nbsp;&nbsp; "
            "<span style='color:#bcc2ff;'>↵ Enter</span> Executar &nbsp;&nbsp; "
            "<span style='color:#bcc2ff;'>Esc</span> Sair",
            self
        )
        tip_arrow.setObjectName("FooterLabel")
        footer_layout.addWidget(tip_arrow)
        main_layout.addLayout(footer_layout)

        self.search_input.setFocus()

    def setup_keyboard_shortcuts(self):
        """Atalhos globais de teclado da janela."""
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.close)
        QShortcut(QKeySequence("Ctrl+N"), self, self.open_add_dialog)
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_system_binds)
        QShortcut(QKeySequence("F5"), self, self.reload_system_binds)
        QShortcut(QKeySequence("Ctrl+O"), self, lambda: open_file_in_editor(BINDS_LUA, 1))
        QShortcut(QKeySequence("Ctrl+Shift+O"), self, lambda: open_file_in_editor(CUSTOM_BINDS_LUA, 1))
        QShortcut(QKeySequence("Ctrl+B"), self, lambda: open_file_in_editor(BINDS_LUA, 1))
        QShortcut(QKeySequence("F2"), self, self.on_edit_selected)
        QShortcut(QKeySequence("Ctrl+E"), self, self.on_edit_selected)

    def focusNextPrevChild(self, next):
        """Evita duplo salto do Tab interceptando no nível da janela e retornando True."""
        self.cycle_category(1 if next else -1)
        return True

    def eventFilter(self, obj, event):
        """Filtro de eventos na tabela."""
        if obj == self.table and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            text = event.text()

            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.execute_selected()
                return True

            if key == Qt.Key.Key_Escape:
                self.close()
                return True

            # Redirecionar digitação livre na tabela para o campo de busca
            if text and text.isprintable() and key not in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
                self.search_input.setFocus()
                self.search_input.setText(self.search_input.text() + text)
                self.search_input.setCursorPosition(len(self.search_input.text()))
                return True

            if key == Qt.Key.Key_Backspace:
                self.search_input.setFocus()
                cur = self.search_input.text()
                if cur: self.search_input.setText(cur[:-1])
                return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        text = event.text()

        if key == Qt.Key.Key_Escape:
            self.close()
            return

        if key == Qt.Key.Key_Down:
            self.move_table_selection(1)
            return

        if key == Qt.Key.Key_Up:
            self.move_table_selection(-1)
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.execute_selected()
            return

        if text and text.isprintable() and not self.search_input.hasFocus():
            self.search_input.setFocus()
            self.search_input.setText(self.search_input.text() + text)
            self.search_input.setCursorPosition(len(self.search_input.text()))
            return

        super().keyPressEvent(event)

    def cycle_category(self, direction: int):
        """Percorre as categorias estritamente de 1 em 1."""
        if not self.chip_buttons:
            return

        cur_idx = 0
        for i, (cid, btn) in enumerate(self.chip_buttons):
            if btn.isChecked():
                cur_idx = i
                break

        next_idx = (cur_idx + direction) % len(self.chip_buttons)
        next_cat_id, next_btn = self.chip_buttons[next_idx]

        next_btn.setChecked(True)
        self.on_category_clicked(next_cat_id)
        self.search_input.setFocus()

    def move_table_selection(self, delta: int):
        rows = self.table.rowCount()
        if rows == 0:
            return
        cur = self.table.currentRow()
        new_row = (0 if delta > 0 else rows - 1) if cur < 0 else max(0, min(rows - 1, cur + delta))
        self.table.selectRow(new_row)
        item = self.table.item(new_row, 0)
        if item:
            self.table.scrollToItem(item, QAbstractItemView.ScrollHint.EnsureVisible)

    def show_banner(self, message):
        self.banner_label.setText(message)
        self.banner_label.setVisible(True)

    def open_add_dialog(self):
        dlg = AddShortcutDialog(self.theme, self)
        if dlg.exec():
            self.reload_system_binds()
            self.show_banner("✅ Novo atalho salvo em custom_binds.lua e carregado no Hyprland!")

    def on_edit_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.displayed_binds):
            QMessageBox.information(self, "Aviso", "Por favor, selecione um atalho na tabela para editar.")
            return

        bind_item = self.displayed_binds[row]
        dlg = EditShortcutDialog(bind_item, self.theme, self)
        if dlg.exec():
            self.reload_system_binds()
            self.show_banner(f"✅ Atalho '{bind_item['key']}' atualizado com sucesso no arquivo de origem!")

    def reload_system_binds(self):
        subprocess.run(["hyprctl", "reload"], check=False)
        self.apply_theme()
        self.load_binds()
        self.filter_binds()
        self.show_banner("🔄 Atalhos e tema recarregados com sucesso!")

    def on_category_clicked(self, cat_id):
        self.active_category = cat_id
        self.filter_binds()

    def filter_binds(self):
        query = self.search_input.text().lower().strip()
        filtered = []

        for b in self.raw_binds:
            cat = b["category"]
            key = b["key"]
            desc = b["desc"]
            src = b.get("source_file", "")

            if self.active_category != "Todos" and self.active_category not in cat.upper():
                continue

            if query and query not in f"{cat} {key} {desc} {src}".lower():
                continue

            filtered.append(b)

        self.populate_table(filtered)
        self.count_label.setText(f"Exibindo {len(filtered)} de {len(self.raw_binds)} atalhos")

    def populate_table(self, binds):
        """Preenchimento ultra-otimizado da tabela (<1ms) desativando redesenho em lote."""
        self.displayed_binds = binds
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(len(binds))

        # Fonte monoespaçada oficial do sistema
        font_mono = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)

        for row, b in enumerate(binds):
            cat = b["category"]
            key = b["key"]
            desc = b["desc"]
            src_file = b.get("source_file", "")
            line_num = b.get("line_number", 0)
            src_type = b.get("source_type", "")

            item_cat = QTableWidgetItem(cat)
            item_cat.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            if "CUSTOM" in cat.upper():
                item_cat.setForeground(QColor(self.theme['ACCENT_CORAL']))
            elif any(k in cat.upper() for k in ("HYPR", "JANELA", "MONITOR", "WORKSPACE")):
                item_cat.setForeground(QColor(self.theme['TEXT_COLOR']))
            else:
                item_cat.setForeground(QColor(self.theme['ACCENT_GREEN']))

            item_key = QTableWidgetItem(self.format_key(key))
            item_key.setFont(font_mono)
            item_key.setForeground(QColor(self.theme['ACCENT_PRIMARY']))
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            item_desc = QTableWidgetItem(desc)
            item_desc.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            origin_label = f"{os.path.basename(src_file)}:{line_num}" if (src_file and line_num > 0) else (os.path.basename(src_file) if src_file else src_type)
            item_src = QTableWidgetItem(origin_label)
            item_src.setFont(font_mono)
            item_src.setForeground(QColor(self.theme['ACCENT_BLUE']))
            item_src.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            is_executable = self.is_action_executable(desc)
            item_act = QTableWidgetItem("↵ Executar" if is_executable else "✏️ Editar")
            item_act.setForeground(QColor(self.theme['ACCENT_GREEN'] if is_executable else self.theme['ACCENT_SECONDARY']))
            item_act.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, item_cat)
            self.table.setItem(row, 1, item_key)
            self.table.setItem(row, 2, item_desc)
            self.table.setItem(row, 3, item_src)
            self.table.setItem(row, 4, item_act)

        self.table.setUpdatesEnabled(True)
        if len(binds) > 0:
            self.table.selectRow(0)

    def format_key(self, raw_key):
        return " + ".join([f"[{p.strip()}]" for p in raw_key.split("+")])

    def is_action_executable(self, desc):
        triggers = (
            "abrir", "terminal", "dolphin", "firefox", "calculadora",
            "kde connect", "btop", "capturar", "conta-gotas", "lançador",
            "central de controle", "wallpapers", "área de transferência",
            "configurações", "bloquear a tela", "menu de energia", "executar"
        )
        dl = desc.lower()
        return any(t in dl for t in triggers)

    def execute_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.displayed_binds):
            return
        b = self.displayed_binds[row]
        desc = b["desc"]

        if self.is_action_executable(desc):
            self.dispatch_action(desc)
            if self.is_daemon:
                self.hide()
            else:
                self.close()
        else:
            self.on_edit_selected()

    def on_item_double_clicked(self, item):
        self.execute_selected()

    def dispatch_action(self, desc):
        d = desc.lower()
        if "terminal kitty" in d: subprocess.Popen(["kitty"])
        elif "dolphin" in d:
            env = os.environ.copy()
            env["XDG_CURRENT_DESKTOP"] = "KDE"
            env["QT_QPA_PLATFORMTHEME"] = "kde"
            subprocess.Popen(["dolphin"], env=env)
        elif "firefox" in d or "navegador" in d: subprocess.Popen(["firefox"])
        elif "calculadora" in d: subprocess.Popen(["gnome-calculator"])
        elif "kde connect" in d: subprocess.Popen(["kdeconnect-app"])
        elif "btop" in d: subprocess.Popen(["kitty", "-e", "btop"])
        elif "capturar região" in d: subprocess.Popen(["noctalia", "msg", "screenshot-region"])
        elif "capturar a tela inteira" in d: subprocess.Popen(["noctalia", "msg", "screenshot-fullscreen"])
        elif "conta-gotas" in d: subprocess.Popen(["hyprpicker", "-a", "-n"])
        elif "central de controle" in d: subprocess.Popen(["noctalia", "msg", "panel-toggle", "control-center"])
        elif "lançador" in d: subprocess.Popen(["noctalia", "msg", "panel-toggle", "launcher"])
        elif "wallpapers" in d or "papéis de parede" in d: subprocess.Popen(["noctalia", "msg", "panel-toggle", "wallpaper"])
        elif "área de transferência" in d or "clipboard" in d: subprocess.Popen(["noctalia", "msg", "panel-toggle", "clipboard"])
        elif "configurações do noctalia" in d: subprocess.Popen(["noctalia", "msg", "settings-toggle"])
        elif "bloquear a tela" in d: subprocess.Popen(["noctalia", "msg", "session", "lock"])
        elif "menu de energia" in d: subprocess.Popen(["noctalia", "msg", "panel-toggle", "session"])
        elif "executar:" in d:
            cmd = desc.split(":", 1)[1].strip()
            subprocess.Popen(cmd.split())

# ==============================================================================
# ENTRADA PRINCIPAL: CLIENTE RÁPIDO & MODO DAEMON RESIDENTE
# ==============================================================================
def main():
    is_daemon_arg = "--daemon" in sys.argv

    # 1. Se não for daemon, verificar se já existe processo rodando (0.5ms)
    if not is_daemon_arg:
        app_check = QApplication(sys.argv)
        check_sock = QLocalSocket()
        check_sock.connectToServer(SINGLETON_SOCKET)
        if check_sock.waitForConnected(120):
            check_sock.write(b"toggle\n")
            check_sock.waitForBytesWritten(120)
            check_sock.disconnectFromServer()
            sys.exit(0)
    else:
        app_check = QApplication(sys.argv)

    app = app_check
    app.setApplicationName("hypr-cheatsheet")
    app.setDesktopFileName("hypr-cheatsheet")

    # Servidor local para escutar toggles instantâneos
    QLocalServer.removeServer(SINGLETON_SOCKET)
    server = QLocalServer()
    server.listen(SINGLETON_SOCKET)

    theme = load_noctalia_theme()
    app.setStyleSheet(build_stylesheet(theme))

    window = KeybindsWindow(is_daemon=is_daemon_arg)
    window.setWindowTitle("Hyprland Keybinds Explorer")

    def on_incoming_connection():
        conn = server.nextPendingConnection()
        if conn:
            conn.waitForReadyRead(100)
            msg = conn.readAll().data().decode().strip()
            if msg == "toggle":
                if is_daemon_arg:
                    if window.isVisible():
                        window.hide()
                    else:
                        window.apply_theme()
                        window.show()
                        window.raise_()
                        window.activateWindow()
                        window.search_input.setFocus()
                else:
                    window.close()
            elif msg == "show":
                window.apply_theme()
                window.show()
                window.raise_()
                window.activateWindow()
                window.search_input.setFocus()
            conn.disconnectFromServer()

    server.newConnection.connect(on_incoming_connection)

    def cleanup():
        QLocalServer.removeServer(SINGLETON_SOCKET)
    app.aboutToQuit.connect(cleanup)

    if not is_daemon_arg:
        window.show()
    else:
        print("[Noctalia Keybinds] Daemon residente iniciado em background com sucesso (<5ms de resposta).")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
