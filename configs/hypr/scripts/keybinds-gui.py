#!/usr/bin/env python3
# ==============================================================================
# keybinds-gui.py
# Painel Gráfico Moderno e Dedicado de Atalhos (PySide6 / Qt6 no Wayland)
# 100% Integrado ao Noctalia Shell, Paleta Dinâmica e Configurações do Sistema
#
# Arquitetura Modular SOLID (Refatorada):
#   - keybinds.config: Caminhos e constantes do sistema
#   - keybinds.theme: Leitor de tokens Material You do Noctalia e gerador QSS
#   - keybinds.editor: Despacho para editores de código e texto
#   - keybinds.actions: ActionDispatcher extensível para comandos do sistema
#   - keybinds.widgets: Widgets customizados com delegação limpa (LSP)
#   - keybinds.dialogs: Modais independentes de adição e edição de atalhos
#   - keybinds.window: Janela principal com tabela e atalhos rápidos
#   - keybinds.app: Servidor IPC, singleton e daemon residente (<5ms)
# ==============================================================================
import os
import sys

# Garantir que o diretório de scripts esteja no PYTHONPATH
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from keybinds.app import main

if __name__ == "__main__":
    sys.exit(main())
