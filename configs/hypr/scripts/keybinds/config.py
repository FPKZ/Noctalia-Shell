"""
Módulo de Configuração e Constantes do Menu de Atalhos.
Princípio da Responsabilidade Única (SRP): gerenciar caminhos e definições de ambiente.
"""
import os

CONFIG_DIR = os.path.expanduser("~/.config")
HYPR_DIR = os.path.join(CONFIG_DIR, "hypr")
BINDS_LUA = os.path.join(HYPR_DIR, "config/binds.lua")
CUSTOM_BINDS_LUA = os.path.join(HYPR_DIR, "config/custom_binds.lua")
VARIABLES_LUA = os.path.join(HYPR_DIR, "config/variables.lua")
KITTY_CONF = os.path.join(CONFIG_DIR, "kitty/kitty.conf")
KITTY_THEME = os.path.join(CONFIG_DIR, "kitty/themes/noctalia.conf")
QT6CT_COLORS = os.path.join(CONFIG_DIR, "qt6ct/colors/noctalia.conf")
GTK4_THEME = os.path.join(CONFIG_DIR, "gtk-4.0/noctalia.css")
GTK3_THEME = os.path.join(CONFIG_DIR, "gtk-3.0/noctalia.css")
HYPR_NOCTALIA = os.path.join(CONFIG_DIR, "hypr/noctalia.lua")

SINGLETON_SOCKET = "hypr_keybinds_gui_singleton_socket"

# Paleta padrão segura (Material You Noctalia)
DEFAULT_THEME = {
    "DARK_BG": "#1a110e",
    "CARD_BG": "#271e1a",
    "INPUT_BG": "#271e1a",
    "BORDER_COLOR": "#352823",
    "ACCENT_PRIMARY": "#ffb595",
    "ACCENT_PRIMARY_FG": "#542105",
    "ACCENT_SECONDARY": "#e6bead",
    "ACCENT_CORAL": "#ffb4ab",
    "ACCENT_GREEN": "#e6bead",
    "ACCENT_BLUE": "#d2c78f",
    "TEXT_COLOR": "#f1dfd8",
    "TEXT_MUTED": "#b3a5a0",
    "HIGHLIGHT_BG": "#392b26"
}
