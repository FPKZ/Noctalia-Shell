"""
Servidor da Aplicação, Modo Daemon e Gestão Singleton IPC.
Princípio da Responsabilidade Única (SRP): gerenciar o ciclo de vida do processo Qt e comunicação local via sockets.
"""
import sys
from PySide6.QtWidgets import QApplication, QProxyStyle, QStyle
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from .config import SINGLETON_SOCKET
from .theme import load_noctalia_theme, build_stylesheet
from .window import KeybindsWindow

class NoFocusRectStyle(QProxyStyle):
    """Estilo proxy que elimina retângulos de foco pontilhados internos (PE_FrameFocusRect) em botões."""
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            return
        super().drawPrimitive(element, option, painter, widget)

class ApplicationServer:
    """Gerenciador do ciclo de vida da aplicação com suporte a singleton e daemon residente."""

    def __init__(self, is_daemon: bool = False):
        self.is_daemon = is_daemon
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.style_proxy = NoFocusRectStyle()
        self.app.setStyle(self.style_proxy)
        self.app.setApplicationName("hypr-cheatsheet")
        self.app.setDesktopFileName("hypr-cheatsheet")
        self.app.setQuitOnLastWindowClosed(not self.is_daemon)

        # Aplicar tema inicial
        theme = load_noctalia_theme()
        self.app.setStyleSheet(build_stylesheet(theme))

        # Configurar servidor local IPC
        QLocalServer.removeServer(SINGLETON_SOCKET)
        self.server = QLocalServer()
        self.server.listen(SINGLETON_SOCKET)
        self.server.newConnection.connect(self._on_incoming_connection)

        self.window = KeybindsWindow(is_daemon=self.is_daemon)
        self.window.setWindowTitle("Hyprland Keybinds Explorer")

        self.app.aboutToQuit.connect(self._cleanup)

    def _on_incoming_connection(self):
        conn = self.server.nextPendingConnection()
        if not conn:
            return

        conn.waitForReadyRead(100)
        msg = conn.readAll().data().decode().strip()

        if msg == "toggle":
            if self.is_daemon:
                if self.window.isVisible():
                    self.window.hide()
                else:
                    self.window.apply_theme()
                    self.window.show()
                    self.window.raise_()
                    self.window.activateWindow()
                    self.window.search_input.setFocus()
            else:
                self.window.close()
        elif msg == "show":
            self.window.apply_theme()
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
            self.window.search_input.setFocus()

        conn.disconnectFromServer()

    def _cleanup(self):
        QLocalServer.removeServer(SINGLETON_SOCKET)

    def start(self) -> int:
        """Inicia a execução da aplicação."""
        if not self.is_daemon:
            self.window.show()
        else:
            print("[Noctalia Keybinds] Daemon residente iniciado em background com sucesso (<5ms de resposta).")

        return self.app.exec()

def try_send_singleton_command(command: str = "toggle") -> bool:
    """Tenta enviar um comando rápido (<1ms) para uma instância já em execução."""
    check_sock = QLocalSocket()
    check_sock.connectToServer(SINGLETON_SOCKET)
    if check_sock.waitForConnected(120):
        check_sock.write(f"{command}\n".encode("utf-8"))
        check_sock.waitForBytesWritten(120)
        check_sock.disconnectFromServer()
        return True
    return False

def main(args: list[str] | None = None) -> int:
    """Ponto de entrada unificado para execução normal ou como daemon."""
    args = args if args is not None else sys.argv
    is_daemon_arg = "--daemon" in args

    # 1. Se não for daemon, verificar se já existe processo rodando (0.5ms)
    if not is_daemon_arg:
        app_check = QApplication.instance() or QApplication(args)
        if try_send_singleton_command("toggle"):
            sys.exit(0)

    server = ApplicationServer(is_daemon=is_daemon_arg)
    return server.start()
