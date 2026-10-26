"""
Modal Interativo para Criar e Salvar Novo Atalho no Hyprland.
Princípio da Responsabilidade Única (SRP) e Segregação de Interfaces (ISP).
"""
import os
import re
import subprocess
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QMessageBox
)

from ..config import CUSTOM_BINDS_LUA

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

class KeyCaptureLineEdit(QLineEdit):
    """Campo de texto inteligente que grava diretamente a tecla pressionada sem fechar o diálogo."""
    def __init__(self, parent_dialog=None):
        super().__init__(parent_dialog)
        self.parent_dialog = parent_dialog

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        # Teclas modificadoras sozinhas
        if key in (Qt.Key.Key_Super_L, Qt.Key.Key_Super_R):
            if self.parent_dialog:
                self.parent_dialog.chk_super.setChecked(True)
            return
        elif key in (Qt.Key.Key_Control, Qt.Key.Key_Meta):
            if self.parent_dialog:
                self.parent_dialog.chk_ctrl.setChecked(True)
            return
        elif key == Qt.Key.Key_Shift:
            if self.parent_dialog:
                self.parent_dialog.chk_shift.setChecked(True)
            return
        elif key == Qt.Key.Key_Alt:
            if self.parent_dialog:
                self.parent_dialog.chk_alt.setChecked(True)
            return

        # Captura de teclas especiais sem fechar o diálogo no Escape
        if key == Qt.Key.Key_Escape:
            self.setText("Esc")
            event.accept()
            return
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.setText("Enter")
            event.accept()
            return
        elif key == Qt.Key.Key_Space:
            self.setText("Space")
            event.accept()
            return
        elif key == Qt.Key.Key_Tab:
            self.setText("Tab")
            event.accept()
            return
        elif key == Qt.Key.Key_Backspace:
            self.setText("")
            event.accept()
            return

        seq_text = QKeySequence(key).toString()
        if seq_text:
            self.setText(seq_text.upper())
            event.accept()
            return

        super().keyPressEvent(event)

class AddShortcutDialog(QDialog):
    """Modal Interativo para Criar e Salvar Novo Atalho no Hyprland."""
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("AddShortcutDialog")
        self.theme = theme
        self.setWindowTitle("Cadastrar Novo Atalho")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.resize(620, 560)
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

        # Opção especial: Tecla Super Avulsa (Release / Ao Soltar)
        self.chk_standalone_super = QCheckBox("⚡ Usar apenas a tecla Super avulsa (ao soltar / tap)", self)
        self.chk_standalone_super.setStyleSheet(
            f"font-weight: bold; color: {self.theme['ACCENT_PRIMARY']}; padding: 4px;"
        )
        self.chk_standalone_super.stateChanged.connect(self.on_standalone_super_toggled)
        layout.addWidget(self.chk_standalone_super)

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
        self.key_input = KeyCaptureLineEdit(self)
        self.key_input.setPlaceholderText("Pressione ou digite a tecla (Ex: Esc, Return, Space, W, 5, F1)...")
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
        self.desc_input.setPlaceholderText("Ex: Abrir Painel de Controle ou Focar Workspace 5")
        self.desc_input.textChanged.connect(self.update_preview)
        grid.addWidget(self.desc_input, 4, 1)

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

    def keyPressEvent(self, event: QKeyEvent):
        # Impedir fechamento da janela ao pressionar Escape se o foco estiver no campo de tecla
        if event.key() == Qt.Key.Key_Escape:
            if self.key_input.hasFocus():
                self.key_input.setText("Esc")
                event.accept()
                return
        super().keyPressEvent(event)

    def on_standalone_super_toggled(self, state):
        is_standalone = self.chk_standalone_super.isChecked()
        self.chk_super.setEnabled(not is_standalone)
        self.chk_ctrl.setEnabled(not is_standalone)
        self.chk_shift.setEnabled(not is_standalone)
        self.chk_alt.setEnabled(not is_standalone)
        self.key_input.setEnabled(not is_standalone)

        if is_standalone:
            self.chk_super.setChecked(True)
            self.chk_ctrl.setChecked(False)
            self.chk_shift.setChecked(False)
            self.chk_alt.setChecked(False)
            self.key_input.setText("")
            self.cat_combo.setCurrentIndex(3)  # Noctalia
            if self.action_type_combo.currentIndex() != 3:
                self.action_type_combo.setCurrentIndex(3)
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
        return self.chk_standalone_super.isChecked()

    def get_combo_string(self) -> str:
        if self.is_release_bind():
            return '"SUPER_L"'
        readable = self.get_readable_combo()
        return readable_key_to_lua(readable)

    def get_readable_combo(self) -> str:
        if self.is_release_bind():
            return "Super (Soltar)"
        mods = []
        if self.chk_super.isChecked(): mods.append("Super")
        if self.chk_ctrl.isChecked(): mods.append("Ctrl")
        if self.chk_shift.isChecked(): mods.append("Shift")
        if self.chk_alt.isChecked(): mods.append("Alt")
        key = self.key_input.text().strip() or "X"
        mods.append(key)
        return " + ".join(mods)

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
        elif idx == 4:
            return param or 'hl.dsp.window.fullscreen()'
        return 'hl.dsp.window.fullscreen()'

    def update_preview(self):
        readable = self.get_readable_combo()
        combo_lua = self.get_combo_string()
        action_lua = self.get_action_code()
        desc = self.desc_input.text().strip() or f"Ação ({readable})"
        cat = self.cat_combo.currentText()
        
        if self.is_release_bind():
            preview_text = f"-- category: {cat}\n-- {desc}\npcall(hl.unbind, {combo_lua})\nhl.bind({combo_lua}, {action_lua}, {{ release = true }})"
        else:
            preview_text = f"-- category: {cat}\n-- {desc}\npcall(hl.unbind, {combo_lua})\nhl.bind({combo_lua}, {action_lua})"
        self.preview_box.setText(preview_text)

    def save_shortcut(self):
        is_standalone = self.is_release_bind()
        key = self.key_input.text().strip()
        if not is_standalone and not key:
            QMessageBox.warning(
                self, "Aviso",
                "Por favor, pressione ou digite a tecla principal do atalho\n"
                "(ou selecione a opção de 'Usar apenas a tecla Super avulsa')!"
            )
            return

        desc = self.desc_input.text().strip() or f"Ação ({self.get_readable_combo()})"
        cat = self.cat_combo.currentText()
        combo_lua = self.get_combo_string()
        action_lua = self.get_action_code()

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
