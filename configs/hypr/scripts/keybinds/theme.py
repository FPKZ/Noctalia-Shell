"""
Módulo de Tema Dinâmico e Folha de Estilos (QSS).
Princípio da Responsabilidade Única (SRP): gerenciar tokens visuais, cálculo de contraste e geração de QSS.
"""
import os
import re
from PySide6.QtGui import QColor

from .config import (
    GTK4_THEME, GTK3_THEME, HYPR_NOCTALIA, KITTY_THEME, DEFAULT_THEME
)

class ThemeManager:
    """Carregador e processador de temas dinâmicos integrado ao Noctalia Shell."""

    @staticmethod
    def load_theme() -> dict:
        """Lê os tokens oficiais gerados pelo Noctalia Shell (Material You / Wallpaper)."""
        theme = DEFAULT_THEME.copy()

        # 1. Fonte primária oficial: GTK 4 ou GTK 3
        css_file = GTK4_THEME if os.path.exists(GTK4_THEME) else (GTK3_THEME if os.path.exists(GTK3_THEME) else None)
        if css_file:
            try:
                with open(css_file, "r", encoding="utf-8") as f:
                    content = f.read()
                kv = {}
                for m in re.finditer(r'@define-color\s+([a-zA-Z0-9_-]+)\s+([^;]+);', content):
                    kv[m.group(1).replace('-', '_')] = m.group(2).strip()
                for m in re.finditer(r'--([a-zA-Z0-9_-]+):\s*([^;]+);', content):
                    kv[m.group(1).replace('-', '_')] = m.group(2).strip()

                if 'window_bg_color' in kv: theme['DARK_BG'] = kv['window_bg_color']
                if 'window_fg_color' in kv: theme['TEXT_COLOR'] = kv['window_fg_color']
                if 'card_bg_color' in kv: theme['CARD_BG'] = kv['card_bg_color']
                if 'popover_bg_color' in kv: theme['INPUT_BG'] = kv['popover_bg_color']
                elif 'card_bg_color' in kv: theme['INPUT_BG'] = kv['card_bg_color']
                if 'accent_color' in kv: theme['ACCENT_PRIMARY'] = kv['accent_color']
                if 'accent_fg_color' in kv: theme['ACCENT_PRIMARY_FG'] = kv['accent_fg_color']
                if 'warning_color' in kv: theme['ACCENT_BLUE'] = kv['warning_color']
                if 'success_color' in kv: theme['ACCENT_GREEN'] = kv['success_color']
                if 'destructive_bg_color' in kv: theme['ACCENT_CORAL'] = kv['destructive_bg_color']
                elif 'error_color' in kv: theme['ACCENT_CORAL'] = kv['error_color']
            except Exception as e:
                print(f"[Noctalia Theme] Erro ao ler {css_file}: {e}")

        # 2. Fonte secundária: Hyprland Noctalia Lua
        elif os.path.exists(HYPR_NOCTALIA):
            try:
                with open(HYPR_NOCTALIA, "r", encoding="utf-8") as f:
                    content = f.read()
                for m in re.finditer(r'local\s+([a-zA-Z0-9_]+)\s*=\s*"rgb\(([a-fA-F0-9]{6})\)"', content):
                    k, hex_c = m.group(1), f"#{m.group(2)}"
                    if k == "primary": theme['ACCENT_PRIMARY'] = hex_c
                    elif k == "surface": theme['DARK_BG'] = hex_c
                    elif k == "on_surface": theme['TEXT_COLOR'] = hex_c
                    elif k == "secondary": theme['ACCENT_SECONDARY'] = hex_c
                    elif k == "error": theme['ACCENT_CORAL'] = hex_c
            except Exception as e:
                print(f"[Noctalia Theme] Erro ao ler {HYPR_NOCTALIA}: {e}")

        # 3. Fonte complementar: Kitty Themes
        if os.path.exists(KITTY_THEME):
            try:
                with open(KITTY_THEME, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            k, v = parts[0], parts[1]
                            if k == "selection_background": theme["HIGHLIGHT_BG"] = v
                            elif k in ("active_border_color", "color2") and not css_file: theme["ACCENT_PRIMARY"] = v
            except Exception as e:
                print(f"[Noctalia Theme] Erro ao ler {KITTY_THEME}: {e}")

        # 4. Cálculo de contraste harmonioso para bordas e tons atenuados
        bg = QColor(theme["DARK_BG"])
        fg = QColor(theme["TEXT_COLOR"])
        is_dark = bg.lightness() < 128

        if is_dark:
            theme['BORDER_COLOR'] = QColor(theme['CARD_BG']).lighter(135).name()
            theme['TEXT_MUTED'] = fg.darker(135).name()
            theme['HIGHLIGHT_BG'] = QColor(theme['CARD_BG']).lighter(145).name()
        else:
            theme['BORDER_COLOR'] = QColor(theme['CARD_BG']).darker(115).name()
            theme['TEXT_MUTED'] = fg.lighter(135).name()
            theme['HIGHLIGHT_BG'] = QColor(theme['CARD_BG']).darker(115).name()

        return theme

    @staticmethod
    def build_stylesheet(t: dict) -> str:
        """Gera stylesheet Qt (QSS) usando tamanhos relativos e cores dinâmicas."""
        return f"""
QWidget#RootWindow, QDialog#AddShortcutDialog, QDialog#EditShortcutDialog {{
    background-color: {t['DARK_BG']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 16px;
}}

QLabel#TitleLabel {{
    color: {t['TEXT_COLOR']};
    font-size: 1.35em;
    font-weight: bold;
}}

QLabel#SubtitleLabel {{
    color: {t['TEXT_MUTED']};
    font-size: 0.9em;
}}

QLabel#SectionLabel {{
    color: {t['ACCENT_SECONDARY']};
    font-weight: bold;
    font-size: 0.95em;
}}

QLineEdit, QComboBox {{
    background-color: {t['INPUT_BG']};
    color: {t['TEXT_COLOR']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 7px 12px;
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {t['ACCENT_PRIMARY']};
}}

QPushButton.HeaderAction {{
    background-color: {t['CARD_BG']};
    color: {t['TEXT_COLOR']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 500;
}}

QPushButton.HeaderAction:hover {{
    background-color: {t['INPUT_BG']};
    border-color: {t['ACCENT_PRIMARY']};
    color: {t['ACCENT_PRIMARY']};
}}

QPushButton.PrimaryAction {{
    background-color: {t['ACCENT_PRIMARY']};
    color: {t.get('ACCENT_PRIMARY_FG', t['DARK_BG'])};
    border: 1px solid {t['ACCENT_PRIMARY']};
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: bold;
}}

QPushButton.PrimaryAction:hover {{
    opacity: 0.9;
    border-color: {t['ACCENT_SECONDARY']};
}}

QPushButton.DangerAction {{
    background-color: #3d1e24;
    color: {t['ACCENT_CORAL']};
    border: 1px solid #662d35;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}}

QPushButton.SecondaryAction {{
    background-color: {t['CARD_BG']};
    color: {t['TEXT_MUTED']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 8px 16px;
}}

QPushButton.FilterChip {{
    background-color: {t['CARD_BG']};
    color: {t['TEXT_MUTED']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 8px;
    padding: 5px 11px;
    font-weight: 500;
}}

QPushButton.FilterChip:hover {{
    background-color: {t['INPUT_BG']};
    color: {t['TEXT_COLOR']};
    border-color: {t['ACCENT_PRIMARY']};
}}

QPushButton.FilterChip:checked {{
    background-color: {t['ACCENT_PRIMARY']};
    color: {t.get('ACCENT_PRIMARY_FG', t['DARK_BG'])};
    font-weight: bold;
    border-color: {t['ACCENT_PRIMARY']};
}}

QTableWidget#BindsTable {{
    background-color: {t['CARD_BG']};
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 10px;
    gridline-color: transparent;
    color: {t['TEXT_COLOR']};
    selection-background-color: {t['HIGHLIGHT_BG']};
    selection-color: {t['TEXT_COLOR']};
}}

QTableWidget#BindsTable::item {{
    padding: 8px 6px;
    border-bottom: 1px solid {t['DARK_BG']};
}}

QTableWidget#BindsTable::item:selected {{
    background-color: {t['HIGHLIGHT_BG']};
    border-left: 3px solid {t['ACCENT_PRIMARY']};
}}

QHeaderView::section {{
    background-color: {t['DARK_BG']};
    color: {t['ACCENT_SECONDARY']};
    font-weight: bold;
    padding: 6px;
    border: none;
    border-bottom: 2px solid {t['BORDER_COLOR']};
}}

QScrollBar:vertical {{
    background: {t['DARK_BG']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {t['BORDER_COLOR']};
    min-height: 24px;
    border-radius: 4px;
}}

QLabel#FooterLabel {{
    color: {t['TEXT_MUTED']};
    font-size: 0.9em;
}}

QCheckBox {{
    color: {t['TEXT_COLOR']};
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {t['BORDER_COLOR']};
    border-radius: 4px;
    background-color: {t['INPUT_BG']};
}}

QCheckBox::indicator:checked {{
    background-color: {t['ACCENT_PRIMARY']};
    border-color: {t['ACCENT_PRIMARY']};
}}
"""

def load_noctalia_theme() -> dict:
    """Função de compatibilidade direta."""
    return ThemeManager.load_theme()

def build_stylesheet(theme: dict) -> str:
    """Função de compatibilidade direta."""
    return ThemeManager.build_stylesheet(theme)
