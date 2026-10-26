"""
Widget de busca com delegação avançada de eventos de teclado.
Princípio da Substituição de Liskov (LSP): estende QLineEdit sem violar seu contrato de foco e digitação.
"""
from typing import Callable
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit

class SearchLineEdit(QLineEdit):
    """
    Campo de busca com delegação limpa de teclas para navegação e alternância.
    Suporta tanto callbacks funcionais (DIP) quanto delegação clássica via window_ref.
    """
    def __init__(
        self,
        parent=None,
        on_cycle_category: Callable[[int], None] | None = None,
        on_move_selection: Callable[[int], None] | None = None,
        on_escape: Callable[[], None] | None = None
    ):
        super().__init__(parent)
        self.window_ref = None
        self.on_cycle_category = on_cycle_category
        self.on_move_selection = on_move_selection
        self.on_escape = on_escape

    def focusNextPrevChild(self, next: bool) -> bool:
        """Interrompe a propagação do Tab e altera a categoria estritamente de 1 em 1."""
        step = 1 if next else -1
        if self.on_cycle_category:
            self.on_cycle_category(step)
            return True
        if self.window_ref and hasattr(self.window_ref, "cycle_category"):
            self.window_ref.cycle_category(step)
            return True
        return super().focusNextPrevChild(next)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        # Navegação vertical na tabela
        if key == Qt.Key.Key_Down:
            if self._trigger_move(1): return
        elif key == Qt.Key.Key_Up:
            if self._trigger_move(-1): return
        elif key == Qt.Key.Key_PageDown:
            if self._trigger_move(8): return
        elif key == Qt.Key.Key_PageUp:
            if self._trigger_move(-8): return
        elif key == Qt.Key.Key_Escape:
            if self.on_escape:
                self.on_escape()
                return
            if self.window_ref:
                if getattr(self.window_ref, "is_daemon", False):
                    self.window_ref.hide()
                else:
                    self.window_ref.close()
                return

        super().keyPressEvent(event)

    def _trigger_move(self, delta: int) -> bool:
        if self.on_move_selection:
            self.on_move_selection(delta)
            return True
        if self.window_ref and hasattr(self.window_ref, "move_table_selection"):
            self.window_ref.move_table_selection(delta)
            return True
        return False
