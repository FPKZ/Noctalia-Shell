"""
Janela Principal do Explorador de Atalhos.
Princípio da Responsabilidade Única (SRP) e Inversão de Dependência (DIP):
Responsável pela interface de usuário, apresentação da tabela de atalhos e sincronismo com o compositor.
"""
import os
import subprocess
from PySide6.QtCore import Qt, QEvent, QFileSystemWatcher, QTimer
from PySide6.QtGui import (
    QColor, QKeySequence, QShortcut, QKeyEvent, QFontDatabase
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QButtonGroup, QMenu, QMessageBox
)

from .config import (
    BINDS_LUA, CUSTOM_BINDS_LUA, VARIABLES_LUA, KITTY_CONF,
    GTK4_THEME, GTK3_THEME, HYPR_NOCTALIA, KITTY_THEME
)
from .theme import load_noctalia_theme, build_stylesheet
from .editor import open_file_in_editor
from .actions import is_action_executable, dispatch_action
from .widgets.search_input import SearchLineEdit
from .dialogs.edit_dialog import EditShortcutDialog
from .dialogs.add_dialog import AddShortcutDialog

# Importação defensiva do parser de atalhos
try:
    from keybinds_parser import get_all_binds
except ImportError:
    import importlib.util
    script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    spec = importlib.util.spec_from_file_location("keybinds_parser", os.path.join(script_dir, "keybinds-parser.py"))
    parser_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_mod)
    get_all_binds = parser_mod.get_all_binds

class KeybindsWindow(QWidget):
    """Janela central de exploração e gestão de atalhos do sistema."""

    def __init__(self, is_daemon: bool = False, parent=None):
        super().__init__(parent)
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
        self.raw_binds = []

        self.load_binds()
        self.setup_ui()
        self.populate_table(self.raw_binds)
        self.setup_keyboard_shortcuts()
        self.setup_theme_watcher()

    def setup_theme_watcher(self):
        """Monitora em tempo real alterações nos arquivos de tema gerados pelo Noctalia."""
        self.theme_watcher = QFileSystemWatcher(self)
        watch_files = [GTK4_THEME, GTK3_THEME, HYPR_NOCTALIA, KITTY_THEME]
        for f in watch_files:
            if os.path.exists(f):
                self.theme_watcher.addPath(f)
        self.theme_watcher.fileChanged.connect(self.on_theme_file_changed)

    def on_theme_file_changed(self, path: str):
        # Pequeno atraso para aguardar a finalização de escritas atômicas pelo Noctalia
        QTimer.singleShot(80, lambda: self._handle_file_changed(path))

    def _handle_file_changed(self, path: str):
        if os.path.exists(path) and path not in self.theme_watcher.files():
            self.theme_watcher.addPath(path)
        self.apply_theme()

    def apply_theme(self, new_theme: dict | None = None):
        """Re-aplica dinamicamente a paleta atualizada do Noctalia em todos os componentes."""
        self.theme = new_theme or load_noctalia_theme()

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
        self.files_menu = QMenu(self)
        self.files_menu.setStyleSheet(
            f"background-color: {self.theme['CARD_BG']}; color: {self.theme['TEXT_COLOR']}; "
            f"border: 1px solid {self.theme['BORDER_COLOR']};"
        )

        act_binds = self.files_menu.addAction("📄 Abrir binds.lua (Atalhos do Hyprland) [Ctrl+O]")
        act_binds.triggered.connect(lambda: open_file_in_editor(BINDS_LUA, 1))

        act_custom = self.files_menu.addAction("⭐ Abrir custom_binds.lua (Atalhos do Usuário) [Ctrl+Shift+O]")
        act_custom.triggered.connect(lambda: open_file_in_editor(CUSTOM_BINDS_LUA, 1))

        act_vars = self.files_menu.addAction("⚙️ Abrir variables.lua (Workspaces & Monitores)")
        act_vars.triggered.connect(lambda: open_file_in_editor(VARIABLES_LUA, 1))

        act_kitty = self.files_menu.addAction("💻 Abrir kitty.conf (Atalhos do Terminal)")
        act_kitty.triggered.connect(lambda: open_file_in_editor(KITTY_CONF, 1))

        btn_files.setMenu(self.files_menu)
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
        self.banner_label.setStyleSheet(
            f"background-color: {self.theme['INPUT_BG']}; color: {self.theme['ACCENT_GREEN']}; "
            f"border: 1px solid {self.theme['BORDER_COLOR']}; border-radius: 6px; padding: 6px 12px; font-weight: 500;"
        )
        self.banner_label.setVisible(False)
        main_layout.addWidget(self.banner_label)

        # 2. Barra de Busca Inteligente
        self.search_input = SearchLineEdit(self)
        self.search_input.window_ref = self
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText(
            "🔍  Digite para filtrar por atalho, categoria, arquivo ou comando (ex: fechar, terminal, workspace, f1)..."
        )
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

    def focusNextPrevChild(self, next: bool) -> bool:
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
            if text and text.isprintable() and key not in (
                Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right
            ):
                self.search_input.setFocus()
                self.search_input.setText(self.search_input.text() + text)
                self.search_input.setCursorPosition(len(self.search_input.text()))
                return True

            if key == Qt.Key.Key_Backspace:
                self.search_input.setFocus()
                cur = self.search_input.text()
                if cur:
                    self.search_input.setText(cur[:-1])
                return True

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        if self.is_daemon:
            event.ignore()
            self.hide()
        else:
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        text = event.text()

        if key == Qt.Key.Key_Escape:
            if self.is_daemon:
                self.hide()
            else:
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

    def show_banner(self, message: str):
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

    def on_category_clicked(self, cat_id: str):
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

    def populate_table(self, binds: list):
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
            cat_upper = cat.upper()
            if "CUSTOM" in cat_upper:
                item_cat.setForeground(QColor(self.theme['ACCENT_CORAL']))
            elif any(k in cat_upper for k in ("HYPR", "JANELA", "MONITOR", "WORKSPACE")):
                item_cat.setForeground(QColor(self.theme['TEXT_COLOR']))
            else:
                item_cat.setForeground(QColor(self.theme['ACCENT_GREEN']))
            item_cat.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            item_key = QTableWidgetItem(self.format_key(key))
            item_key.setFont(font_mono)
            item_key.setForeground(QColor(self.theme['ACCENT_PRIMARY']))
            item_key.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            item_desc = QTableWidgetItem(desc)
            item_desc.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

            origin_label = f"{os.path.basename(src_file)}:{line_num}" if (src_file and line_num > 0) else (
                os.path.basename(src_file) if src_file else src_type
            )
            item_src = QTableWidgetItem(origin_label)
            item_src.setFont(font_mono)
            item_src.setForeground(QColor(self.theme['ACCENT_BLUE']))
            item_src.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            executable = is_action_executable(desc)
            item_act = QTableWidgetItem("↵ Executar" if executable else "✏️ Editar")
            item_act.setForeground(QColor(self.theme['ACCENT_GREEN'] if executable else self.theme['ACCENT_SECONDARY']))
            item_act.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, item_cat)
            self.table.setItem(row, 1, item_key)
            self.table.setItem(row, 2, item_desc)
            self.table.setItem(row, 3, item_src)
            self.table.setItem(row, 4, item_act)

        self.table.setUpdatesEnabled(True)
        if len(binds) > 0:
            self.table.selectRow(0)

    @staticmethod
    def format_key(raw_key: str) -> str:
        return " + ".join([f"[{p.strip()}]" for p in raw_key.split("+")])

    def execute_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.displayed_binds):
            return
        b = self.displayed_binds[row]
        desc = b["desc"]

        if is_action_executable(desc):
            dispatch_action(desc)
            if self.is_daemon:
                self.hide()
            else:
                self.close()
        else:
            self.on_edit_selected()

    def on_item_double_clicked(self, item):
        self.execute_selected()
