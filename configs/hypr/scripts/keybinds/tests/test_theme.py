import unittest
from PySide6.QtGui import QColor
from keybinds.theme import ThemeManager, load_noctalia_theme, build_stylesheet
from keybinds.config import DEFAULT_THEME

class TestTheme(unittest.TestCase):
    def test_load_default_theme(self):
        theme = ThemeManager.load_theme()
        self.assertIsInstance(theme, dict)
        for key in ["DARK_BG", "CARD_BG", "ACCENT_PRIMARY", "TEXT_COLOR", "BORDER_COLOR"]:
            self.assertIn(key, theme)
            # Validar formato hex
            self.assertTrue(theme[key].startswith("#"))

    def test_build_stylesheet(self):
        theme = DEFAULT_THEME.copy()
        qss = ThemeManager.build_stylesheet(theme)
        self.assertIn("QWidget#RootWindow", qss)
        self.assertIn(theme["DARK_BG"], qss)
        self.assertIn(theme["ACCENT_PRIMARY"], qss)

    def test_compatibility_functions(self):
        t1 = load_noctalia_theme()
        self.assertIn("DARK_BG", t1)
        s1 = build_stylesheet(t1)
        self.assertIn("QTableWidget#BindsTable", s1)

if __name__ == "__main__":
    unittest.main()
