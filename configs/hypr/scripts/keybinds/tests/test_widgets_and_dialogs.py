import unittest
from PySide6.QtWidgets import QApplication
from keybinds.config import DEFAULT_THEME
from keybinds.widgets.search_input import SearchLineEdit
from keybinds.dialogs.add_dialog import AddShortcutDialog
from keybinds.dialogs.edit_dialog import EditShortcutDialog

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

if __name__ == "__main__":
    unittest.main()
