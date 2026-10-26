import unittest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from keybinds.config import DEFAULT_THEME
from keybinds.widgets.search_input import SearchLineEdit
from keybinds.dialogs.add_dialog import AddShortcutDialog, KeyCaptureLineEdit as AddKeyCapture
from keybinds.dialogs.edit_dialog import EditShortcutDialog, KeyCaptureLineEdit as EditKeyCapture

# QApplication mínima para permitir testes de widgets Qt
app = QApplication.instance() or QApplication([])

class TestWidgetsAndDialogs(unittest.TestCase):
    def test_search_line_edit_callbacks(self):
        cycled = []
        moved = []
        escaped = []

        edit = SearchLineEdit(
            on_cycle_category=lambda d: cycled.append(d),
            on_move_selection=lambda d: moved.append(d),
            on_escape=lambda: escaped.append(True)
        )

        # Simular ciclo Tab
        result = edit.focusNextPrevChild(True)
        self.assertTrue(result)
        self.assertEqual(cycled, [1])

        # Simular ciclo Shift+Tab
        result = edit.focusNextPrevChild(False)
        self.assertTrue(result)
        self.assertEqual(cycled, [1, -1])

    def test_add_shortcut_dialog_instantiation(self):
        dialog = AddShortcutDialog(theme=DEFAULT_THEME)
        self.assertIsNotNone(dialog)
        combo = dialog.get_readable_combo()
        self.assertIn("Super", combo)
        action_code = dialog.get_action_code()
        self.assertIn("hl.dsp.exec_cmd", action_code)

    def test_add_shortcut_standalone_super(self):
        dialog = AddShortcutDialog(theme=DEFAULT_THEME)
        dialog.chk_standalone_super.setChecked(True)
        self.assertTrue(dialog.is_release_bind())
        self.assertEqual(dialog.get_readable_combo(), "Super (Soltar)")
        self.assertEqual(dialog.get_combo_string(), '"SUPER_L"')

    def test_add_shortcut_noctalia_autodetect(self):
        dialog = AddShortcutDialog(theme=DEFAULT_THEME)
        # Inserir comando do Noctalia com dropdown padrão (0)
        dialog.action_type_combo.setCurrentIndex(0)
        dialog.action_param_input.setText("panel-toggle control-center home")
        action_code = dialog.get_action_code()
        self.assertEqual(action_code, 'hl.dsp.exec_cmd("noctalia msg panel-toggle control-center home")')

        # Inserir com prefixo "noctalia msg " duplicado
        dialog.action_param_input.setText("noctalia msg panel-toggle launcher")
        action_code = dialog.get_action_code()
        self.assertEqual(action_code, 'hl.dsp.exec_cmd("noctalia msg panel-toggle launcher")')

    def test_key_capture_line_edit_escape(self):
        edit = AddKeyCapture()
        # Simular pressão da tecla Escape
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        edit.keyPressEvent(event)
        self.assertEqual(edit.text(), "Esc")

    def test_edit_shortcut_dialog_instantiation(self):
        sample_item = {
            "key": "Super + Return",
            "desc": "Abrir Terminal Kitty",
            "raw_action": "hl.dsp.exec_cmd('kitty')",
            "source_type": "hyprland",
            "source_file": "/tmp/dummy.lua",
            "line_number": 10
        }
        dialog = EditShortcutDialog(bind_item=sample_item, theme=DEFAULT_THEME)
        self.assertIsNotNone(dialog)
        self.assertTrue(dialog.chk_super.isChecked())
        self.assertEqual(dialog.key_input.text(), "Return")
        self.assertEqual(dialog.desc_input.text(), "Abrir Terminal Kitty")

    def test_edit_shortcut_standalone_super(self):
        sample_standalone = {
            "key": "Super (Soltar)",
            "desc": "Abrir Menu Noctalia",
            "raw_action": 'hl.dsp.exec_cmd("noctalia msg panel-toggle launcher")',
            "source_type": "custom",
            "source_file": "/tmp/dummy_custom.lua",
            "line_number": 5
        }
        dialog = EditShortcutDialog(bind_item=sample_standalone, theme=DEFAULT_THEME)
        self.assertTrue(dialog.chk_standalone_super.isChecked())
        self.assertEqual(dialog.get_readable_combo(), "Super (Soltar)")

if __name__ == "__main__":
    unittest.main()
