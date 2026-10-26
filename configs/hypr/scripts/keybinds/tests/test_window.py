import unittest
from PySide6.QtWidgets import QApplication
from keybinds.window import KeybindsWindow

app = QApplication.instance() or QApplication([])

class TestWindow(unittest.TestCase):
    def setUp(self):
        self.window = KeybindsWindow(is_daemon=True)

    def tearDown(self):
        self.window.close()

    def test_window_initialization(self):
        self.assertIsNotNone(self.window)
        self.assertTrue(self.window.is_daemon)
        self.assertGreaterEqual(len(self.window.raw_binds), 0)
        self.assertEqual(self.window.active_category, "Todos")

    def test_filter_binds(self):
        # Injetar atalhos mockados
        self.window.raw_binds = [
            {"category": "APLICATIVO", "key": "Super+Return", "desc": "Abrir Terminal Kitty", "source_type": "hyprland"},
            {"category": "JANELA", "key": "Super+Q", "desc": "Fechar Janela Ativa", "source_type": "hyprland"},
            {"category": "CUSTOM", "key": "Super+Alt+Z", "desc": "Meu Atalho", "source_type": "custom"},
        ]
        
        # Testar filtro por texto
        self.window.search_input.setText("Terminal")
        self.assertEqual(len(self.window.displayed_binds), 1)
        self.assertEqual(self.window.displayed_binds[0]["desc"], "Abrir Terminal Kitty")

        # Testar filtro por categoria
        self.window.search_input.setText("")
        self.window.on_category_clicked("CUSTOM")
        self.assertEqual(len(self.window.displayed_binds), 1)
        self.assertEqual(self.window.displayed_binds[0]["desc"], "Meu Atalho")

    def test_daemon_close_event_hides_window(self):
        self.window.show()
        self.window.close()
        # No modo daemon, closeEvent chama self.hide() e ignora o fechamento
        self.assertFalse(self.window.isVisible())

if __name__ == "__main__":
    unittest.main()
