import os
import unittest
from keybinds.config import (
    CONFIG_DIR, HYPR_DIR, BINDS_LUA, DEFAULT_THEME, SINGLETON_SOCKET
)
from keybinds.editor import EditorService, open_file_in_editor

class TestConfigAndEditor(unittest.TestCase):
    def test_config_paths(self):
        self.assertTrue(os.path.isabs(CONFIG_DIR))
        self.assertTrue(os.path.isabs(HYPR_DIR))
        self.assertTrue(os.path.isabs(BINDS_LUA))
        self.assertEqual(SINGLETON_SOCKET, "hypr_keybinds_gui_singleton_socket")
        self.assertIn("DARK_BG", DEFAULT_THEME)
        self.assertIn("ACCENT_PRIMARY", DEFAULT_THEME)

    def test_editor_service_command_resolution(self):
        test_file = "/tmp/test_binds.lua"
        cmd = EditorService.get_command(test_file, 42)
        self.assertTrue(len(cmd) >= 2)
        # Deve conter o arquivo e a linha de alguma forma
        cmd_str = " ".join(cmd)
        self.assertIn(test_file, cmd_str)
        self.assertIn("42", cmd_str)

    def test_editor_service_non_existing_file(self):
        result = open_file_in_editor("/non/existing/file/path.lua", 10)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
