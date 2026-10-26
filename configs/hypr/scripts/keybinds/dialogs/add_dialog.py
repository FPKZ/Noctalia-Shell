"""
Modal Interativo para Criar e Salvar Novo Atalho no Hyprland.
Princípio da Responsabilidade Única (SRP) e Segregação de Interfaces (ISP).
"""
import os
import re
import subprocess
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
)

from ..config import CUSTOM_BINDS_LUA
from ..widgets.key_recorder import KeySequenceRecorder, AccessibleButton

# Importação defensiva das funções do keybinds-parser
try:
    from keybinds_parser import readable_key_to_lua
except ImportError:
    import importlib.util
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    spec = importlib.util.spec_from_file_location("keybinds_parser", os.path.join(script_dir, "keybinds-parser.py"))
    parser_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser_mod)
    readable_key_to_lua = parser_mod.readable_key_to_lua

class AddShortcutDialog(QDialog):
    """Modal Interativo para Criar e Salvar Novo Atalho no Hyprland com foco em navegação por teclado."""
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("AddShortcutDialog")
        self.theme = theme
        self.setWindowTitle("Cadastrar Novo Atalho")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.resize(640, 580)
        self.setup_ui()

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        # 1. Tecla ESC
        if key == Qt.Key.Key_Escape:
            if not self.key_recorder.is_recording:
                self.reject()
                event.accept()
                return
            # Se estiver gravando, o eventFilter captura
            return

        # 2. Tecla Enter / Return
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.key_recorder.is_recording:
                # Se estiver gravando, o eventFilter captura como 'Enter'
                return

            fw = self.focusWidget()
            if fw == self.key_recorder.btn_record:
                self.key_recorder.toggle_recording()
                event.accept()
                return
            elif fw == self.key_recorder.btn_clear:
                self.key_recorder.clear_combo()
                event.accept()
                return
            elif fw == self.btn_cancel:
                self.reject()
                event.accept()
                return
            elif fw == self.btn_save:
                self.save_shortcut()
                event.accept()
                return
            elif isinstance(fw, QLineEdit):
                # Se estiver digitando em campo de texto e der Enter, salvar diretamente!
                self.save_shortcut()
                event.accept()
                return
            elif isinstance(fw, QPushButton):
                fw.click()
                event.accept()
                return

            # Previne que o QDialog chame accept() sem salvar
            event.accept()
            return

        super().keyPressEvent(event)

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

        # 1. Gravador Inteligente de Atalhos
        lbl_mod = QLabel("1. Combinação de Teclas:", self)
        lbl_mod.setObjectName("SectionLabel")
        layout.addWidget(lbl_mod)

        self.key_recorder = KeySequenceRecorder(initial_combo="", theme=self.theme, parent=self)
        self.key_recorder.keySequenceChanged.connect(self.update_preview)
        layout.addWidget(self.key_recorder)

        # Grade com parâmetros
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("2. Categoria:"), 0, 0)
        self.cat_combo = QComboBox(self)
        self.cat_combo.addItems([
            "🚀 [APLICATIVO]",
            "🗂️ [HYPR: WORKSPACE]",
            "🪟 [HYPR: JANELA]",
            "🌌 [NOCTALIA]",
            "⭐ [CUSTOM]"
        ])
        grid.addWidget(self.cat_combo, 0, 1)

        grid.addWidget(QLabel("3. Tipo de Ação:"), 1, 0)
        self.action_type_combo = QComboBox(self)
        self.action_type_combo.addItems([
            "Abrir Aplicativo / Executar Comando",
            "Focar Workspace no Monitor Atual (m~N)",
            "Mover Janela para Workspace (m~N)",
            "Ação do Noctalia (Shell)",
            "Comando Lua Livre do Hyprland"
        ])
        self.action_type_combo.currentIndexChanged.connect(self.on_action_type_changed)
        grid.addWidget(self.action_type_combo, 1, 1)

        self.action_param_label = QLabel("Comando / App:")
        grid.addWidget(self.action_param_label, 2, 0)
        self.action_param_input = QLineEdit(self)
        self.action_param_input.setPlaceholderText("Ex: obs, spotify, discord, telegram-desktop, code...")
        self.action_param_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.action_param_input, 2, 1)

        grid.addWidget(QLabel("4. Descrição:"), 3, 0)
        self.desc_input = QLineEdit(self)
        self.desc_input.setPlaceholderText("Ex: Abrir Painel de Controle ou Focar Workspace 5")
        self.desc_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.desc_input, 3, 1)

        layout.addLayout(grid)

        lbl_prev = QLabel("Pré-visualização do Atalho Gerado:", self)
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
        btn_box.addStretch()

        self.btn_cancel = AccessibleButton("Cancelar", self)
        self.btn_cancel.setProperty("class", "SecondaryAction")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = AccessibleButton("Salvar e Ativar Atalho", self)
        self.btn_save.setProperty("class", "PrimaryAction")
        self.btn_save.clicked.connect(self.save_shortcut)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

        # Focar inicialmente no botão de gravar para navegação ágil
        self.key_recorder.btn_record.setFocus()
        self.update_preview()

    def on_action_type_changed(self, idx: int):
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
            self.action_param_input.setPlaceholderText("Ex: panel-toggle control-center home, panel-toggle launcher...")
            self.cat_combo.setCurrentIndex(3)
        elif idx == 4:
            self.action_param_label.setText("Código Lua:")
            self.action_param_input.setPlaceholderText("Ex: hl.dsp.window.fullscreen()")
            self.cat_combo.setCurrentIndex(4)
        self.update_preview()

    def is_release_bind(self) -> bool:
        combo = self.get_readable_combo().lower()
        return "soltar" in combo or combo in ("super", "super_l")

    def get_combo_string(self) -> str:
        readable = self.get_readable_combo()
        if not readable:
            return 'mainMod .. " + X"'
        return readable_key_to_lua(readable)

    def get_readable_combo(self) -> str:
        return self.key_recorder.get_combo()

    def get_action_code(self) -> str:
        idx = self.action_type_combo.currentIndex()
        param = self.action_param_input.text().strip()

        # Detecção inteligente de comandos Noctalia inseridos diretamente
        is_noctalia = (idx == 3) or any(
            param.startswith(cmd) for cmd in (
                "panel-toggle", "launcher", "control-center",
                "session", "settings-toggle", "wallpaper", "clipboard", "window-switcher"
            )
        ) or param.startswith("noctalia ")

        if is_noctalia:
            # Sanitizar prefixos acidentais como "noctalia msg " ou "noctalia "
            clean_param = re.sub(r'^(noctalia\s+msg\s+|noctalia\s+)', '', param or 'panel-toggle launcher')
            return f'hl.dsp.exec_cmd("noctalia msg {clean_param}")'
        elif idx == 0:
            return f'hl.dsp.exec_cmd(launchPrefix .. "{param or "app"}")'
        elif idx == 1:
            ws = param or "5"
            return f'hl.dsp.focus({{ workspace = "m~{ws}" }})'
        elif idx == 2:
            ws = param or "5"
            return f'hl.dsp.window.move({{ workspace = "m~{ws}" }})'
        elif idx == 4:
            return param or 'hl.dsp.window.fullscreen()'
        return 'hl.dsp.window.fullscreen()'

    def update_preview(self):
        readable = self.get_readable_combo()
        combo_lua = self.get_combo_string()
        action_lua = self.get_action_code()
        desc = self.desc_input.text().strip() or (f"Ação ({readable})" if readable else "Nova Ação")
        cat = self.cat_combo.currentText()

        if self.is_release_bind():
            preview_text = f"-- category: {cat}\n-- {desc}\npcall(hl.unbind, {combo_lua})\nhl.bind({combo_lua}, {action_lua}, {{ release = true }})"
        else:
            preview_text = f"-- category: {cat}\n-- {desc}\npcall(hl.unbind, {combo_lua})\nhl.bind({combo_lua}, {action_lua})"
        self.preview_box.setText(preview_text)

    def save_shortcut(self):
        combo = self.get_readable_combo()
        if not combo:
            QMessageBox.warning(
                self, "Aviso",
                "Por favor, grave uma combinação de teclas para o atalho.\n"
                "(Pressione o botão 'Gravar Atalho' e tecle a combinação desejada)."
            )
            self.key_recorder.btn_record.setFocus()
            return

        desc = self.desc_input.text().strip() or f"Ação ({combo})"
        cat = self.cat_combo.currentText()
        combo_lua = self.get_combo_string()
        action_lua = self.get_action_code()
        is_standalone = self.is_release_bind()

        if is_standalone:
            block = (
                f"\n-- category: {cat}\n"
                f"-- {desc}\n"
                f"pcall(hl.unbind, {combo_lua})\n"
                f"hl.bind({combo_lua}, {action_lua}, {{ release = true }})\n"
            )
        else:
            block = (
                f"\n-- category: {cat}\n"
                f"-- {desc}\n"
                f"pcall(hl.unbind, {combo_lua})\n"
                f"hl.bind({combo_lua}, {action_lua})\n"
            )

        try:
            with open(CUSTOM_BINDS_LUA, "a", encoding="utf-8") as f:
                f.write(block)
            subprocess.run(["hyprctl", "reload"], check=False)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar atalho: {e}")
