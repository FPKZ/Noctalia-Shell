"""
Modal para Editar um Atalho Específico e sua Linha de Origem.
Princípio da Segregação de Interfaces (ISP) e Responsabilidade Única (SRP).
"""
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)

from ..config import VARIABLES_LUA
from ..editor import open_file_in_editor
from ..widgets.key_recorder import KeySequenceRecorder

# Importação defensiva das funções do keybinds-parser
try:
    from keybinds_parser import (
        readable_key_to_lua, update_hypr_bind_in_file,
        delete_hypr_bind_in_file, update_kitty_bind
    )
except ImportError:
    import importlib.util
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    spec = importlib.util.spec_from_file_location("keybinds_parser", os.path.join(script_dir, "keybinds-parser.py"))
    parser_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_mod)
    readable_key_to_lua = parser_mod.readable_key_to_lua
    update_hypr_bind_in_file = parser_mod.update_hypr_bind_in_file
    delete_hypr_bind_in_file = parser_mod.delete_hypr_bind_in_file
    update_kitty_bind = parser_mod.update_kitty_bind

class EditShortcutDialog(QDialog):
    """Modal para Editar um Atalho Específico e sua Linha de Origem com foco em teclado."""
    def __init__(self, bind_item: dict, theme: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("EditShortcutDialog")
        self.bind_item = bind_item
        self.theme = theme
        self.setWindowTitle("Editar Atalho Específico")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.resize(640, 560)
        self.setup_ui()

    def keyPressEvent(self, event: QKeyEvent):
        # Quando NÃO estiver gravando atalho, ESC fecha normalmente a janela
        if event.key() == Qt.Key.Key_Escape:
            if not self.key_recorder.is_recording:
                self.reject()
                return
        super().keyPressEvent(event)

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
        lbl_origin.setStyleSheet(
            f"background-color: {self.theme['INPUT_BG']}; border: 1px solid {self.theme['BORDER_COLOR']}; "
            f"border-radius: 6px; padding: 6px 12px; color: {self.theme['ACCENT_PRIMARY']};"
        )
        layout.addWidget(lbl_origin)

        # 1. Gravador Inteligente de Atalho
        lbl_mod = QLabel("1. Combinação de Teclas:", self)
        lbl_mod.setObjectName("SectionLabel")
        layout.addWidget(lbl_mod)

        self.key_recorder = KeySequenceRecorder(
            initial_combo=self.bind_item.get('key', ''),
            theme=self.theme,
            parent=self
        )
        self.key_recorder.keySequenceChanged.connect(self.update_preview)
        layout.addWidget(self.key_recorder)

        # 2. Descrição e Ação
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Descrição da Ação:"), 0, 0)
        self.desc_input = QLineEdit(self)
        self.desc_input.setText(self.bind_item.get('desc', ''))
        self.desc_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.desc_input, 0, 1)

        grid.addWidget(QLabel("Comando / Ação:"), 1, 0)
        self.action_input = QLineEdit(self)
        self.action_input.setText(self.bind_item.get("raw_action", ""))
        self.action_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.action_input, 1, 1)

        layout.addLayout(grid)

        lbl_prev = QLabel("Pré-visualização da Linha Atualizada:", self)
        lbl_prev.setObjectName("SectionLabel")
        layout.addWidget(lbl_prev)

        self.preview_box = QLabel(self)
        self.preview_box.setStyleSheet(
            f"background-color: {self.theme['INPUT_BG']}; border: 1px solid {self.theme['BORDER_COLOR']}; "
            f"border-radius: 8px; padding: 10px; font-family: monospace; color: {self.theme['ACCENT_GREEN']};"
        )
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

        # Focar inicialmente no botão de gravar para facilitar alteração
        self.key_recorder.btn_record.setFocus()
        self.update_preview()

    def get_readable_combo(self) -> str:
        combo = self.key_recorder.get_combo()
        return combo if combo else self.bind_item.get('key', 'Super + X')

    def is_release_bind(self) -> bool:
        combo = self.get_readable_combo().lower()
        return "soltar" in combo or combo in ("super", "super_l")

    def update_preview(self):
        readable = self.get_readable_combo()
        lua_key = readable_key_to_lua(readable)
        action = self.action_input.text().strip() or self.bind_item.get("raw_action", "")
        desc = self.desc_input.text().strip()
        stype = self.bind_item.get("source_type")

        if stype in ("hyprland", "custom"):
            if self.is_release_bind() and "release" not in action:
                prev = f"-- {desc}\nhl.bind({lua_key}, {action}, {{ release = true }})"
            else:
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
