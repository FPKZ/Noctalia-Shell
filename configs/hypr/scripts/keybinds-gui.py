#!/usr/bin/env python3
# ==============================================================================
# keybinds-gui.py
# Painel Gráfico Moderno e Dedicado de Atalhos (PySide6 / Qt6 no Wayland)
# Estilizado no tema Oxocarbon / Noctalia (Material You)
# ==============================================================================
import sys
import os
import subprocess
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QKeySequence, QShortcut, QIcon
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QPushButton, QFrame, QButtonGroup, QAbstractItemView
)

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
TEXT_COLOR = "#e4e1e9"
TEXT_MUTED = "#939ab7"
HIGHLIGHT_BG = "#282a3e"

STYLESHEET = f"""
QWidget#RootWindow {{
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

QLineEdit#SearchInput {{
    background-color: {INPUT_BG};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: {ACCENT_PRIMARY};
    selection-color: {DARK_BG};
}}

QLineEdit#SearchInput:focus {{
    border: 1px solid {ACCENT_PRIMARY};
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

QLabel#BadgeHint {{
    background-color: {INPUT_BG};
    color: {ACCENT_SECONDARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 5px;
    padding: 3px 7px;
    font-size: 11px;
    font-family: monospace;
}}
"""

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

        # Dados originais
        self.raw_binds = get_all_binds()
        self.active_category = "Todos"

        self.setup_ui()
        self.populate_table(self.raw_binds)

        # Atalho ESC para fechar
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self.close)

    def setup_ui(self):
        self.resize(1080, 680)

        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. Header (Título e Subtítulo)
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title = QLabel("⌨️  Central de Atalhos do Sistema", self)
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Hyprland • Noctalia Shell • Kitty • Dolphin • Navegador • KDE Plasma", self)
        subtitle.setObjectName("SubtitleLabel")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        esc_hint = QLabel("Pressione <b>ESC</b> para fechar", self)
        esc_hint.setObjectName("FooterLabel")
        header_layout.addWidget(esc_hint)
        main_layout.addLayout(header_layout)

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

        # Ajustes de Colunas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.table.itemDoubleClicked.connect(self.on_item_activated)
        main_layout.addWidget(self.table)

        # Navegação via teclado da busca para a tabela
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

        # Foco inicial na busca
        self.search_input.setFocus()

    def on_category_clicked(self, cat_id):
        self.active_category = cat_id
        self.filter_binds()

    def filter_binds(self):
        query = self.search_input.text().lower().strip()
        filtered = []

        for cat, key, desc in self.raw_binds:
            # Filtro por Categoria
            if self.active_category != "Todos":
                if self.active_category not in cat.upper():
                    continue

            # Filtro por Texto
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
            # 1. Categoria
            item_cat = QTableWidgetItem(cat)
            item_cat.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            # 2. Tecla (Formatada)
            formatted_key = self.format_key(key)
            item_key = QTableWidgetItem(formatted_key)
            item_key.setFont(font_mono)
            item_key.setForeground(QColor(ACCENT_PRIMARY))
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            # 3. Descrição
            item_desc = QTableWidgetItem(desc)
            item_desc.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            # 4. Ação / Executável
            is_executable = self.is_action_executable(desc)
            action_text = "↵ Executar" if is_executable else "—"
            item_act = QTableWidgetItem(action_text)
            if is_executable:
                item_act.setForeground(QColor("#a8f5ba"))
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
            "Configurações", "Bloquear a tela", "Menu de Energia"
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
