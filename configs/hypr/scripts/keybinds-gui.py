#!/usr/bin/env python3
# ==============================================================================
# keybinds-gui.py
# Painel Gráfico Moderno e Dedicado de Atalhos (PySide6 / Qt6 no Wayland)
# Estilizado no tema Oxocarbon / Noctalia (Material You)
# Inclui:
#   - Visualização e busca instantânea de atalhos de todo o sistema
#   - Adição interativa de novos atalhos com persistência em custom_binds.lua
#   - Recarregamento a quente do Hyprland (hyprctl reload)
#   - Abertura rápida do arquivo de binds no editor do sistema
# ==============================================================================
import sys
import os
import re
import subprocess
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QPushButton, QFrame, QButtonGroup, QAbstractItemView, QMessageBox
)

# Caminhos de configuração
CONFIG_DIR = os.path.expanduser("~/.config")
HYPR_DIR = os.path.join(CONFIG_DIR, "hypr")
BINDS_LUA = os.path.join(HYPR_DIR, "config/binds.lua")
CUSTOM_BINDS_LUA = os.path.join(HYPR_DIR, "config/custom_binds.lua")
VARIABLES_LUA = os.path.join(HYPR_DIR, "config/variables.lua")

# Importar o parser universal
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("keybinds_parser", os.path.join(SCRIPT_DIR, "keybinds-parser.py"))
    parser_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_mod)
    get_all_binds = parser_mod.get_all_binds
except Exception as e:
    def get_all_binds():
        return [("⚠️ [ERRO]", "Erro ao carregar", str(e))]

# Cores e Estilo Oxocarbon / Noctalia
DARK_BG = "#13131a"
CARD_BG = "#1a1b26"
INPUT_BG = "#222436"
BORDER_COLOR = "#2f334d"
ACCENT_PRIMARY = "#bcc2ff"
ACCENT_SECONDARY = "#c4c5dd"
ACCENT_MUTED = "#555877"
ACCENT_GREEN = "#a8f5ba"
ACCENT_CORAL = "#ffb4ab"
TEXT_COLOR = "#e4e1e9"
TEXT_MUTED = "#939ab7"
HIGHLIGHT_BG = "#282a3e"

STYLESHEET = f"""
QWidget#RootWindow, QDialog#AddShortcutDialog {{
    background-color: {DARK_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 16px;
}}

QLabel#TitleLabel {{
    color: {TEXT_COLOR};
    font-size: 19px;
    font-weight: bold;
    font-family: 'Inter', 'Noto Sans', 'Segoe UI', sans-serif;
}}

QLabel#SubtitleLabel {{
    color: {TEXT_MUTED};
    font-size: 13px;
}}

QLabel#SectionLabel {{
    color: {ACCENT_SECONDARY};
    font-weight: bold;
    font-size: 13px;
}}

QLineEdit, QComboBox {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {ACCENT_PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {HIGHLIGHT_BG};
}}

QPushButton.HeaderAction {{
    background-color: {CARD_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 500;
}}

QPushButton.HeaderAction:hover {{
    background-color: {INPUT_BG};
    border-color: {ACCENT_PRIMARY};
    color: {ACCENT_PRIMARY};
}}

QPushButton.PrimaryAction {{
    background-color: {ACCENT_PRIMARY};
    color: {DARK_BG};
    border: 1px solid {ACCENT_PRIMARY};
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: bold;
}}

QPushButton.PrimaryAction:hover {{
    background-color: #d1d5ff;
}}

QPushButton.SecondaryAction {{
    background-color: {CARD_BG};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 13px;
}}

QPushButton.SecondaryAction:hover {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
}}

QPushButton.FilterChip {{
    background-color: {CARD_BG};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
}}

QPushButton.FilterChip:hover {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border-color: {ACCENT_MUTED};
}}

QPushButton.FilterChip:checked {{
    background-color: {ACCENT_PRIMARY};
    color: {DARK_BG};
    font-weight: bold;
    border-color: {ACCENT_PRIMARY};
}}

QTableWidget#BindsTable {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    gridline-color: transparent;
    color: {TEXT_COLOR};
    selection-background-color: {HIGHLIGHT_BG};
    selection-color: {TEXT_COLOR};
    font-size: 13px;
}}

QTableWidget#BindsTable::item {{
    padding: 10px 8px;
    border-bottom: 1px solid #1e2030;
}}

QTableWidget#BindsTable::item:selected {{
    background-color: {HIGHLIGHT_BG};
    border-left: 3px solid {ACCENT_PRIMARY};
}}

QHeaderView::section {{
    background-color: {INPUT_BG};
    color: {ACCENT_SECONDARY};
    font-weight: bold;
    font-size: 12px;
    padding: 8px;
    border: none;
    border-bottom: 2px solid {BORDER_COLOR};
}}

QScrollBar:vertical {{
    background: {DARK_BG};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {ACCENT_MUTED};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QLabel#FooterLabel {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QCheckBox {{
    color: {TEXT_COLOR};
    font-size: 13px;
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    background-color: {INPUT_BG};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_PRIMARY};
    border-color: {ACCENT_PRIMARY};
}}
"""

class AddShortcutDialog(QDialog):
    """Modal Interativo para Criar e Salvar Novo Atalho no Hyprland."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AddShortcutDialog")
        self.setWindowTitle("Cadastrar Novo Atalho")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.resize(600, 520)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        # Cabeçalho
        title = QLabel("➕  Criar Novo Atalho no Hyprland", self)
        title.setObjectName("TitleLabel")
        desc = QLabel("O novo atalho será salvo em <code>custom_binds.lua</code> e ativado imediatamente.", self)
        desc.setObjectName("SubtitleLabel")
        layout.addWidget(title)
        layout.addWidget(desc)

        # 1. Modificadores
        lbl_mod = QLabel("1. Teclas Modificadoras:", self)
        lbl_mod.setObjectName("SectionLabel")
        layout.addWidget(lbl_mod)

        mod_box = QHBoxLayout()
        self.chk_super = QCheckBox("Super (Windows)", self)
        self.chk_super.setChecked(True)
        self.chk_ctrl = QCheckBox("Ctrl", self)
        self.chk_shift = QCheckBox("Shift", self)
        self.chk_alt = QCheckBox("Alt", self)

        for c in (self.chk_super, self.chk_ctrl, self.chk_shift, self.chk_alt):
            c.stateChanged.connect(self.update_preview)
            mod_box.addWidget(c)
        mod_box.addStretch()
        layout.addLayout(mod_box)

        # 2. Tecla Principal
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("2. Tecla Principal:"), 0, 0)
        self.key_input = QLineEdit(self)
        self.key_input.setPlaceholderText("Ex: W, O, Return, Space, Tab, Left, 5, F2...")
        self.key_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.key_input, 0, 1)

        # 3. Categoria
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

        # 4. Tipo de Ação
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

        # 5. Parâmetro da Ação
        self.action_param_label = QLabel("Comando / App:")
        grid.addWidget(self.action_param_label, 3, 0)
        self.action_param_input = QLineEdit(self)
        self.action_param_input.setPlaceholderText("Ex: obs, spotify, discord, telegram-desktop, code...")
        self.action_param_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.action_param_input, 3, 1)

        # 6. Descrição legível
        grid.addWidget(QLabel("5. Descrição:"), 4, 0)
        self.desc_input = QLineEdit(self)
        self.desc_input.setPlaceholderText("Ex: Abrir OBS Studio ou Focar Workspace 5")
        self.desc_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.desc_input, 4, 1)

        layout.addLayout(grid)

        # Preview em tempo real
        lbl_prev = QLabel("Pré-visualização do Atalho Gerado:", self)
        lbl_prev.setObjectName("SectionLabel")
        layout.addWidget(lbl_prev)

        self.preview_box = QLabel(self)
        self.preview_box.setStyleSheet(f"background-color: {INPUT_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 10px; font-family: monospace; color: {ACCENT_GREEN};")
        self.preview_box.setWordWrap(True)
        layout.addWidget(self.preview_box)

        # Botões de Ação
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
            self.action_param_input.setPlaceholderText("Ex: obs, spotify, discord, telegram-desktop, code...")
            self.cat_combo.setCurrentIndex(0)
        elif idx == 1:
            self.action_param_label.setText("Número Workspace:")
            self.action_param_input.setPlaceholderText("Ex: 5 (ou qualquer número de 1 a 10)")
            self.cat_combo.setCurrentIndex(1)
            if not self.desc_input.text():
                self.desc_input.setText("Focar Workspace")
        elif idx == 2:
            self.action_param_label.setText("Número Workspace:")
            self.action_param_input.setPlaceholderText("Ex: 5 (ou qualquer número de 1 a 10)")
            self.cat_combo.setCurrentIndex(1)
            if not self.desc_input.text():
                self.desc_input.setText("Mover janela para Workspace")
        elif idx == 3:
            self.action_param_label.setText("Mensagem Noctalia:")
            self.action_param_input.setPlaceholderText("Ex: panel-toggle launcher, screenshot-region...")
            self.cat_combo.setCurrentIndex(3)
        elif idx == 4:
            self.action_param_label.setText("Código Lua:")
            self.action_param_input.setPlaceholderText("Ex: hl.dsp.window.fullscreen()")
            self.cat_combo.setCurrentIndex(4)
        self.update_preview()

    def get_combo_string(self):
        mods = []
        if self.chk_super.isChecked(): mods.append("mainMod")
        if self.chk_ctrl.isChecked(): mods.append('"CONTROL"')
        if self.chk_shift.isChecked(): mods.append('"SHIFT"')
        if self.chk_alt.isChecked(): mods.append('"ALT"')

        key = self.key_input.text().strip() or "X"
        mods.append(f'"{key}"')
        return ' .. " + " .. '.join(mods)

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

        preview_text = (
            f"-- category: {cat}\n"
            f"-- {desc}\n"
            f"hl.bind({combo_lua}, {action_lua})"
        )
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

        block = (
            f"\n-- category: {cat}\n"
            f"-- {desc}\n"
            f"hl.bind({combo_lua}, {action_lua})\n"
        )

        try:
            with open(CUSTOM_BINDS_LUA, "a", encoding="utf-8") as f:
                f.write(block)
            
            # Recarregar Hyprland
            subprocess.run(["hyprctl", "reload"], check=False)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar atalho: {e}")

class KeybindsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("RootWindow")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.active_category = "Todos"
        self.load_binds()
        self.setup_ui()
        self.populate_table(self.raw_binds)

        # Atalho ESC para fechar
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self.close)

    def load_binds(self):
        self.raw_binds = get_all_binds()

    def setup_ui(self):
        self.resize(1100, 700)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Header (Título, Subtítulo e Botões de Gestão)
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

        # Botão: Novo Atalho
        btn_add = QPushButton("➕ Novo Atalho", self)
        btn_add.setProperty("class", "HeaderAction")
        btn_add.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(btn_add)

        # Botão: Editar Arquivo
        btn_edit = QPushButton("✏️ Editar Binds", self)
        btn_edit.setProperty("class", "HeaderAction")
        btn_edit.clicked.connect(self.open_editor)
        header_layout.addWidget(btn_edit)

        # Botão: Recarregar
        btn_reload = QPushButton("🔄 Recarregar", self)
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
        self.banner_label.setStyleSheet(f"background-color: {INPUT_BG}; color: {ACCENT_GREEN}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 6px 12px; font-weight: 500;")
        self.banner_label.setVisible(False)
        main_layout.addWidget(self.banner_label)

        # 2. Barra de Busca
        self.search_input = QLineEdit(self)
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍  Digite para filtrar por atalho, categoria ou comando (ex: fechar, terminal, workspace, f1)...")
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

        for cat_id, cat_label in categories:
            btn = QPushButton(cat_label, self)
            btn.setProperty("class", "FilterChip")
            btn.setCheckable(True)
            if cat_id == "Todos":
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, c=cat_id: self.on_category_clicked(c))
            self.chip_group.addButton(btn)
            chips_layout.addWidget(btn)

        chips_layout.addStretch()
        main_layout.addLayout(chips_layout)

        # 4. Tabela de Atalhos
        self.table = QTableWidget(self)
        self.table.setObjectName("BindsTable")
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["CATEGORIA", "ATALHO / COMBINAÇÃO", "DESCRIÇÃO DA AÇÃO", "EXECUTAR"])
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

        self.table.itemDoubleClicked.connect(self.on_item_activated)
        main_layout.addWidget(self.table)

        self.search_input.returnPressed.connect(self.on_search_return)

        # 5. Rodapé
        footer_layout = QHBoxLayout()
        self.count_label = QLabel(f"Total de atalhos catalogados: {len(self.raw_binds)}", self)
        self.count_label.setObjectName("FooterLabel")
        footer_layout.addWidget(self.count_label)
        footer_layout.addStretch()

        tip_arrow = QLabel("<span style='color:#bcc2ff;'>↑/↓</span> Navegar &nbsp;&nbsp; <span style='color:#bcc2ff;'>↵ Enter</span> Executar Ação &nbsp;&nbsp; <span style='color:#bcc2ff;'>Esc</span> Sair", self)
        tip_arrow.setObjectName("FooterLabel")
        footer_layout.addWidget(tip_arrow)
        main_layout.addLayout(footer_layout)

        self.search_input.setFocus()

    def show_banner(self, message):
        self.banner_label.setText(message)
        self.banner_label.setVisible(True)

    def open_add_dialog(self):
        dlg = AddShortcutDialog(self)
        if dlg.exec():
            self.reload_system_binds()
            self.show_banner("✅ Novo atalho salvo com sucesso em custom_binds.lua e carregado no Hyprland!")

    def open_editor(self):
        target_file = CUSTOM_BINDS_LUA if os.path.exists(CUSTOM_BINDS_LUA) else BINDS_LUA
        editors = ["gnome-text-editor", "kwrite", "kate", "code", "xdg-open"]
        opened = False
        for ed in editors:
            if subprocess.run(["which", ed], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                subprocess.Popen([ed, target_file])
                opened = True
                break
        if not opened:
            subprocess.Popen(["kitty", "-e", "nano", target_file])
        self.show_banner(f"📝 Arquivo aberto no editor: {os.path.basename(target_file)}")

    def reload_system_binds(self):
        subprocess.run(["hyprctl", "reload"], check=False)
        self.load_binds()
        self.filter_binds()
        self.show_banner("🔄 Atalhos do Hyprland e Noctalia recarregados com sucesso!")

    def on_category_clicked(self, cat_id):
        self.active_category = cat_id
        self.filter_binds()

    def filter_binds(self):
        query = self.search_input.text().lower().strip()
        filtered = []

        for cat, key, desc in self.raw_binds:
            if self.active_category != "Todos":
                if self.active_category not in cat.upper():
                    continue

            if query:
                combined = f"{cat} {key} {desc}".lower()
                if query not in combined:
                    continue

            filtered.append((cat, key, desc))

        self.populate_table(filtered)
        self.count_label.setText(f"Exibindo {len(filtered)} de {len(self.raw_binds)} atalhos")

    def populate_table(self, binds):
        self.table.setRowCount(len(binds))
        font_mono = QFont("JetBrains Mono", 10)
        font_mono.setStyleHint(QFont.StyleHint.Monospace)

        for row, (cat, key, desc) in enumerate(binds):
            item_cat = QTableWidgetItem(cat)
            item_cat.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            if "CUSTOM" in cat.upper():
                item_cat.setForeground(QColor(ACCENT_GREEN))

            formatted_key = self.format_key(key)
            item_key = QTableWidgetItem(formatted_key)
            item_key.setFont(font_mono)
            item_key.setForeground(QColor(ACCENT_PRIMARY))
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            item_desc = QTableWidgetItem(desc)
            item_desc.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            is_executable = self.is_action_executable(desc)
            action_text = "↵ Executar" if is_executable else "—"
            item_act = QTableWidgetItem(action_text)
            if is_executable:
                item_act.setForeground(QColor(ACCENT_GREEN))
                item_act.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                item_act.setForeground(QColor(TEXT_MUTED))
                item_act.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, item_cat)
            self.table.setItem(row, 1, item_key)
            self.table.setItem(row, 2, item_desc)
            self.table.setItem(row, 3, item_act)

        if len(binds) > 0:
            self.table.selectRow(0)

    def format_key(self, raw_key):
        parts = [p.strip() for p in raw_key.split("+")]
        return " + ".join([f"[{p}]" for p in parts])

    def is_action_executable(self, desc):
        triggers = [
            "Abrir", "Terminal", "Dolphin", "Firefox", "Calculadora",
            "KDE Connect", "btop", "Capturar", "Conta-gotas", "Lançador",
            "Central de Controle", "Wallpapers", "Área de Transferência",
            "Configurações", "Bloquear a tela", "Menu de Energia", "Executar"
        ]
        return any(t.lower() in desc.lower() for t in triggers)

    def on_search_return(self):
        if self.table.rowCount() > 0:
            self.on_item_activated(self.table.item(0, 0))

    def on_item_activated(self, item):
        row = self.table.currentRow()
        if row < 0:
            return
        desc = self.table.item(row, 2).text()
        self.dispatch_action(desc)
        self.close()

    def dispatch_action(self, desc):
        d = desc.lower()
        if "terminal kitty" in d:
            subprocess.Popen(["kitty"])
        elif "dolphin" in d:
            env = os.environ.copy()
            env["XDG_CURRENT_DESKTOP"] = "KDE"
            env["QT_QPA_PLATFORMTHEME"] = "kde"
            subprocess.Popen(["dolphin"], env=env)
        elif "firefox" in d or "navegador" in d:
            subprocess.Popen(["firefox"])
        elif "calculadora" in d:
            subprocess.Popen(["gnome-calculator"])
        elif "kde connect" in d:
            subprocess.Popen(["kdeconnect-app"])
        elif "btop" in d:
            subprocess.Popen(["kitty", "-e", "btop"])
        elif "capturar região" in d:
            subprocess.Popen(["noctalia", "msg", "screenshot-region"])
        elif "capturar a tela inteira" in d:
            subprocess.Popen(["noctalia", "msg", "screenshot-fullscreen"])
        elif "conta-gotas" in d:
            subprocess.Popen(["hyprpicker", "-a", "-n"])
        elif "central de controle" in d:
            subprocess.Popen(["noctalia", "msg", "panel-toggle", "control-center"])
        elif "lançador" in d:
            subprocess.Popen(["noctalia", "msg", "panel-toggle", "launcher"])
        elif "wallpapers" in d or "papéis de parede" in d:
            subprocess.Popen(["noctalia", "msg", "panel-toggle", "wallpaper"])
        elif "área de transferência" in d or "clipboard" in d:
            subprocess.Popen(["noctalia", "msg", "panel-toggle", "clipboard"])
        elif "configurações do noctalia" in d:
            subprocess.Popen(["noctalia", "msg", "settings-toggle"])
        elif "bloquear a tela" in d:
            subprocess.Popen(["noctalia", "msg", "session", "lock"])
        elif "menu de energia" in d:
            subprocess.Popen(["noctalia", "msg", "panel-toggle", "session"])
        elif "executar:" in d:
            cmd = desc.split(":", 1)[1].strip()
            subprocess.Popen(cmd.split())

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("hypr-cheatsheet")
    app.setDesktopFileName("hypr-cheatsheet")
    app.setStyleSheet(STYLESHEET)

    window = KeybindsWindow()
    window.setWindowTitle("Hyprland Keybinds Explorer")
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
