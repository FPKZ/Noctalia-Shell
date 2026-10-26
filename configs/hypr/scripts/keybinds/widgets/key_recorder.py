"""
Widget Reutilizável de Captura e Gravação de Atalhos de Teclado.
Princípio da Responsabilidade Única (SRP) e Segregação de Interfaces (ISP).
"""
from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)

class KeySequenceRecorder(QWidget):
    """
    Widget moderno para captura dinâmica de combinações de teclado.
    Permite gravar atalhos completos (modificadores + teclas ou teclas avulsas)
    com auto-finalização ao soltar as teclas físicas pressionadas.
    """
    keySequenceChanged = Signal(str)

    def __init__(self, initial_combo: str = "", theme: dict = None, parent=None):
        super().__init__(parent)
        self.theme = theme or {}
        self.current_combo = initial_combo or ""
        self.is_recording = False
        self.active_keys = set()
        self.recorded_keys = []
        self._target_window = None

        self.setup_ui()
        self.set_combo(self.current_combo)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)

        # 1. Display da combinação gravada
        self.display_label = QLabel(self)
        self.display_label.setMinimumHeight(42)
        row_layout.addWidget(self.display_label, 1)

        # 2. Botão para Iniciar / Parar Gravação
        self.btn_record = QPushButton("🎙️ Gravar Atalho", self)
        self.btn_record.setMinimumHeight(42)
        self.btn_record.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_record.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_record.clicked.connect(self.toggle_recording)
        row_layout.addWidget(self.btn_record)

        # 3. Botão para Limpar
        self.btn_clear = QPushButton("✖", self)
        self.btn_clear.setMinimumHeight(42)
        self.btn_clear.setToolTip("Limpar atalho atual")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.btn_clear.clicked.connect(self.clear_combo)
        row_layout.addWidget(self.btn_clear)

        layout.addLayout(row_layout)

        # 4. Rótulo informativo de status
        self.hint_label = QLabel(self)
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        self._apply_idle_styles()

    def _apply_idle_styles(self):
        input_bg = self.theme.get("INPUT_BG", "#1e1e2e")
        border = self.theme.get("BORDER_COLOR", "rgba(255, 255, 255, 0.12)")
        accent = self.theme.get("ACCENT_PRIMARY", "#a855f7")
        text_color = self.theme.get("TEXT_COLOR", "#ffffff")
        card_bg = self.theme.get("CARD_BG", "#252538")

        self.display_label.setStyleSheet(
            f"background-color: {input_bg}; border: 1px solid {border}; border-radius: 8px; "
            f"padding: 8px 14px; font-family: monospace; font-size: 14px; font-weight: bold; color: {accent};"
        )
        self.btn_record.setStyleSheet(
            f"QPushButton {{ background-color: {card_bg}; border: 1px solid {border}; border-radius: 8px; "
            f"padding: 8px 18px; font-weight: bold; color: {text_color}; }} "
            f"QPushButton:hover {{ background-color: {accent}; color: #000000; border-color: {accent}; }} "
            f"QPushButton:focus {{ border: 2px solid {accent}; }}"
        )
        self.btn_clear.setStyleSheet(
            f"QPushButton {{ background-color: {card_bg}; border: 1px solid {border}; border-radius: 8px; "
            f"padding: 8px 12px; font-weight: bold; color: {text_color}; }} "
            f"QPushButton:hover {{ background-color: #ef4444; color: #ffffff; border-color: #ef4444; }} "
            f"QPushButton:focus {{ border: 2px solid {accent}; }}"
        )
        self.hint_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px;")
        self.hint_label.setText("💡 Pressione <b>Enter</b> ou <b>Espaço</b> em 'Gravar', aperte suas teclas no teclado e solte.")
        self.btn_record.setText("🎙️ Gravar Atalho")

    def _apply_recording_styles(self):
        accent_red = "#ef4444"
        self.display_label.setStyleSheet(
            f"background-color: rgba(239, 68, 68, 0.12); border: 2px solid {accent_red}; border-radius: 8px; "
            f"padding: 8px 14px; font-family: monospace; font-size: 14px; font-weight: bold; color: {accent_red};"
        )
        self.btn_record.setStyleSheet(
            f"QPushButton {{ background-color: {accent_red}; border: 2px solid {accent_red}; border-radius: 8px; "
            f"padding: 8px 18px; font-weight: bold; color: #ffffff; }} "
            f"QPushButton:hover {{ background-color: #dc2626; border-color: #dc2626; }}"
        )
        self.hint_label.setStyleSheet(f"color: {accent_red}; font-size: 12px; font-weight: bold;")
        self.hint_label.setText("🔴 Gravando... Pressione qualquer tecla ou combinação no teclado (ex: Super, Esc, Tab...) e solte.")
        self.btn_record.setText("🔴 Parar Gravação")

    def set_combo(self, combo: str):
        self.current_combo = combo.strip()
        if self.current_combo:
            self.display_label.setText(f"⌨️  {self.current_combo}")
        else:
            self.display_label.setText("⌨️  (Nenhum atalho configurado)")

    def get_combo(self) -> str:
        return self.current_combo

    def toggle_recording(self):
        if self.is_recording:
            self.cancel_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.is_recording = True
        self.active_keys = set()
        self.recorded_keys = []
        self._apply_recording_styles()
        self.display_label.setText("Pressione as teclas no teclado...")

        target = self.window()
        if target:
            self._target_window = target
            target.installEventFilter(self)

    def stop_recording(self):
        self.is_recording = False
        if self._target_window:
            self._target_window.removeEventFilter(self)
            self._target_window = None

        if self.recorded_keys:
            final_combo = self._format_combo(self.recorded_keys)
            self.set_combo(final_combo)
            self.keySequenceChanged.emit(self.current_combo)

        self._apply_idle_styles()
        if self.current_combo:
            self.hint_label.setText(f"✅ Atalho gravado com sucesso: <b>{self.current_combo}</b>")

    def cancel_recording(self):
        self.is_recording = False
        if self._target_window:
            self._target_window.removeEventFilter(self)
            self._target_window = None
        self.active_keys = set()
        self.recorded_keys = []
        self.set_combo(self.current_combo)
        self._apply_idle_styles()

    def clear_combo(self):
        if self.is_recording:
            self.cancel_recording()
        self.set_combo("")
        self.keySequenceChanged.emit("")

    def eventFilter(self, obj, event: QEvent) -> bool:
        if not getattr(self, "is_recording", False):
            return False

        if event.type() == QEvent.Type.KeyPress:
            if not isinstance(event, QKeyEvent) or event.isAutoRepeat():
                return True

            key = event.key()
            self.active_keys.add(key)
            key_name = self._key_to_name(key)

            # Sincronizar modificadores
            mods = event.modifiers().value
            if (mods & Qt.KeyboardModifier.MetaModifier.value) and "Super" not in self.recorded_keys:
                self.recorded_keys.append("Super")
            if (mods & Qt.KeyboardModifier.ControlModifier.value) and "Ctrl" not in self.recorded_keys:
                self.recorded_keys.append("Ctrl")
            if (mods & Qt.KeyboardModifier.ShiftModifier.value) and "Shift" not in self.recorded_keys:
                self.recorded_keys.append("Shift")
            if (mods & Qt.KeyboardModifier.AltModifier.value) and "Alt" not in self.recorded_keys:
                self.recorded_keys.append("Alt")

            if key_name not in self.recorded_keys:
                self.recorded_keys.append(key_name)

            temp_combo = self._format_combo(self.recorded_keys)
            self.display_label.setText(f"🔴 {temp_combo}")
            return True

        elif event.type() == QEvent.Type.KeyRelease:
            if not isinstance(event, QKeyEvent) or event.isAutoRepeat():
                return True

            key = event.key()
            if key in self.active_keys:
                self.active_keys.remove(key)

            # Liberação defensiva de modificadores via máscara de bits
            mods = event.modifiers().value
            if not (mods & Qt.KeyboardModifier.MetaModifier.value):
                self.active_keys.discard(Qt.Key.Key_Super_L)
                self.active_keys.discard(Qt.Key.Key_Super_R)
                self.active_keys.discard(Qt.Key.Key_Meta)
            if not (mods & Qt.KeyboardModifier.ControlModifier.value):
                self.active_keys.discard(Qt.Key.Key_Control)
            if not (mods & Qt.KeyboardModifier.ShiftModifier.value):
                self.active_keys.discard(Qt.Key.Key_Shift)
            if not (mods & Qt.KeyboardModifier.AltModifier.value):
                self.active_keys.discard(Qt.Key.Key_Alt)
                self.active_keys.discard(Qt.Key.Key_AltGr)

            # Ao soltar todas as teclas físicas pressionadas, finalizar gravação!
            if len(self.active_keys) == 0 and len(self.recorded_keys) > 0:
                self.stop_recording()

            return True

        return False

    def _key_to_name(self, key: int) -> str:
        if key in (Qt.Key.Key_Super_L, Qt.Key.Key_Super_R, Qt.Key.Key_Meta):
            return "Super"
        elif key in (Qt.Key.Key_Control,):
            return "Ctrl"
        elif key in (Qt.Key.Key_Shift,):
            return "Shift"
        elif key in (Qt.Key.Key_Alt, Qt.Key.Key_AltGr):
            return "Alt"
        elif key == Qt.Key.Key_Escape:
            return "Esc"
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return "Enter"
        elif key == Qt.Key.Key_Space:
            return "Space"
        elif key == Qt.Key.Key_Tab:
            return "Tab"
        elif key == Qt.Key.Key_Backspace:
            return "Backspace"
        elif key == Qt.Key.Key_Delete:
            return "Delete"
        elif key == Qt.Key.Key_Insert:
            return "Insert"
        elif key == Qt.Key.Key_Home:
            return "Home"
        elif key == Qt.Key.Key_End:
            return "End"
        elif key == Qt.Key.Key_PageUp:
            return "PageUp"
        elif key == Qt.Key.Key_PageDown:
            return "PageDown"
        elif key == Qt.Key.Key_Left:
            return "Left"
        elif key == Qt.Key.Key_Right:
            return "Right"
        elif key == Qt.Key.Key_Up:
            return "Up"
        elif key == Qt.Key.Key_Down:
            return "Down"
        elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F35:
            return f"F{key - Qt.Key.Key_F1 + 1}"
        else:
            text = QKeySequence(key).toString()
            if text:
                return text.upper()
        return f"Key_{key}"

    def _format_combo(self, keys: list) -> str:
        mods_order = ["Super", "Ctrl", "Shift", "Alt"]
        mods = [m for m in mods_order if m in keys]
        others = [k for k in keys if k not in mods_order]

        if len(mods) == 1 and len(others) == 0 and mods[0] == "Super":
            return "Super (Soltar)"
        elif len(mods) > 0 and len(others) == 0:
            return f"{mods[0]} (Soltar)" if len(mods) == 1 else " + ".join(mods)

        return " + ".join(mods + others)
