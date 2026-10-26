import unittest
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication
from keybinds.config import DEFAULT_THEME
from keybinds.widgets.search_input import SearchLineEdit
from keybinds.widgets.key_recorder import KeySequenceRecorder
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

    def test_key_recorder_combo_and_auto_release(self):
        rec = KeySequenceRecorder(initial_combo="Super + Return", theme=DEFAULT_THEME)
        self.assertEqual(rec.get_combo(), "Super + Return")

        # Iniciar gravação
        rec.start_recording()
        self.assertTrue(rec.is_recording)

        # 1. Pressionar Super
        e1 = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Super_L, Qt.KeyboardModifier.MetaModifier)
        rec.eventFilter(rec, e1)
        self.assertIn("Super", rec.recorded_keys)
        self.assertTrue(rec.is_recording)

        # 2. Pressionar Esc mantendo Super
        e2 = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.MetaModifier)
        rec.eventFilter(rec, e2)
        self.assertIn("Esc", rec.recorded_keys)
        self.assertTrue(rec.is_recording)

        # 3. Soltar Esc
        e3 = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Escape, Qt.KeyboardModifier.MetaModifier)
        rec.eventFilter(rec, e3)
        self.assertTrue(rec.is_recording)  # Ainda segurando Super

        # 4. Soltar Super
        e4 = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Super_L, Qt.KeyboardModifier.NoModifier)
        rec.eventFilter(rec, e4)
        # Ao soltar todas as teclas, deve finalizar automaticamente!
        self.assertFalse(rec.is_recording)
        self.assertEqual(rec.get_combo(), "Super + Esc")

    def test_key_recorder_standalone_super(self):
        rec = KeySequenceRecorder(theme=DEFAULT_THEME)
        rec.start_recording()

        # Pressionar Super isolado
        e1 = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Super_L, Qt.KeyboardModifier.MetaModifier)
        rec.eventFilter(rec, e1)
        # Soltar Super isolado
        e2 = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Super_L, Qt.KeyboardModifier.NoModifier)
        rec.eventFilter(rec, e2)

        self.assertFalse(rec.is_recording)
        self.assertEqual(rec.get_combo(), "Super (Soltar)")

    def test_add_shortcut_dialog_instantiation_and_recording(self):
        dialog = AddShortcutDialog(theme=DEFAULT_THEME)
        self.assertIsNotNone(dialog)
        combo = dialog.get_readable_combo()
        self.assertIn("Super", combo)

        # Gravar Super avulso
        dialog.key_recorder.set_combo("Super (Soltar)")
        self.assertTrue(dialog.is_release_bind())
        self.assertEqual(dialog.get_combo_string(), 'mainMod .. " + SUPER_L"')

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
        self.assertEqual(dialog.key_recorder.get_combo(), "Super + Return")
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
        self.assertEqual(dialog.key_recorder.get_combo(), "Super (Soltar)")
        self.assertTrue(dialog.is_release_bind())

    def test_escape_behavior_outside_and_inside_recording(self):
        dialog = AddShortcutDialog(theme=DEFAULT_THEME)
        
        # 1. Quando NÃO está gravando, ESC aciona reject()
        rejected = []
        dialog.reject = lambda: rejected.append(True)
        e_esc = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        dialog.keyPressEvent(e_esc)
        self.assertEqual(rejected, [True])

        # 2. Quando ESTÁ gravando, ESC é absorvido pelo gravador e NÃO aciona reject()
        dialog.key_recorder.start_recording()
        dialog.key_recorder.eventFilter(dialog, e_esc)
        self.assertIn("Esc", dialog.key_recorder.recorded_keys)
        self.assertEqual(rejected, [True])  # Continua 1, não aumentou

if __name__ == "__main__":
    unittest.main()
