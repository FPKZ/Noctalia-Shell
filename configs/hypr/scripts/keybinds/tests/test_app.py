import unittest
from PySide6.QtWidgets import QApplication
from keybinds.app import ApplicationServer, try_send_singleton_command, NoFocusRectStyle

app = QApplication.instance() or QApplication([])

class TestApp(unittest.TestCase):
    def test_no_focus_rect_style(self):
        style = NoFocusRectStyle()
        self.assertIsNotNone(style)

    def test_application_server_instantiation(self):
        server = ApplicationServer(is_daemon=True)
        self.assertIsNotNone(server)
        self.assertTrue(server.is_daemon)
        self.assertIsNotNone(server.server)
        self.assertIsNotNone(server.window)
        # Limpar servidor para não deixar socket aberto no teste
        server._cleanup()

    def test_singleton_command_when_no_server(self):
        # Quando nenhum servidor escuta no socket aleatório, deve retornar False sem travar
        res = try_send_singleton_command("toggle")
        self.assertFalse(res)

if __name__ == "__main__":
    unittest.main()
