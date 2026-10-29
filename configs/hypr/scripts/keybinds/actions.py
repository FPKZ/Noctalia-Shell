"""
Módulo de Despacho e Execução de Ações do Sistema.
Princípio Aberto/Fechado (OCP) e Responsabilidade Única (SRP):
Permite registrar e executar ações do sistema sem acoplamento direto com a interface gráfica.
"""
import os
import subprocess
from typing import Callable, Any

class ActionDispatcher:
    """Gerenciador extensível para identificar e executar ações a partir da descrição de atalhos."""

    EXECUTABLE_TRIGGERS = (
        "abrir", "terminal", "dolphin", "firefox", "calculadora",
        "kde connect", "btop", "capturar", "conta-gotas", "lançador",
        "central de controle", "wallpapers", "área de transferência",
        "configurações", "bloquear a tela", "menu de energia", "executar",
        "rede", "conexões", "stream"
    )

    def __init__(self, runner: Callable[[list[str], dict | None], Any] | None = None):
        # Runner customizado para testes ou fallback padrão com subprocess.Popen
        self._runner = runner or self._default_runner
        self._handlers: list[tuple[Callable[[str], bool], Callable[[str], Any]]] = []
        self._register_default_handlers()

    @staticmethod
    def _default_runner(cmd: list[str], env: dict | None = None):
        return subprocess.Popen(cmd, env=env)

    def register_handler(self, matcher: Callable[[str], bool], handler: Callable[[str], Any]):
        """Registra um manipulador de ação personalizado (Aberto para extensão)."""
        self._handlers.append((matcher, handler))

    def _register_default_handlers(self):
        """Registra os manipuladores nativos do sistema Hyprland e Noctalia Shell."""
        
        # Execução direta por comando prioritária (ex: "Executar: htop")
        self.register_handler(
            lambda d: "executar:" in d,
            lambda d: self._runner(d.split(":", 1)[1].strip().split())
        )

        # Terminal Kitty
        self.register_handler(
            lambda d: "terminal kitty" in d,
            lambda d: self._runner(["kitty"])
        )

        # Dolphin com variáveis de ambiente do KDE
        def _launch_dolphin(d):
            env = os.environ.copy()
            env["XDG_CURRENT_DESKTOP"] = "KDE"
            env["QT_QPA_PLATFORMTHEME"] = "kde"
            return self._runner(["dolphin"], env=env)
        self.register_handler(lambda d: "dolphin" in d, _launch_dolphin)

        # Navegador Firefox
        self.register_handler(
            lambda d: "firefox" in d or "navegador" in d,
            lambda d: self._runner(["firefox"])
        )

        # Calculadora
        self.register_handler(
            lambda d: "calculadora" in d,
            lambda d: self._runner(["gnome-calculator"])
        )

        # KDE Connect
        self.register_handler(
            lambda d: "kde connect" in d,
            lambda d: self._runner(["kdeconnect-app"])
        )

        # Btop
        self.register_handler(
            lambda d: "btop" in d,
            lambda d: self._runner(["kitty", "-e", "btop"])
        )

        # Noctalia Captura de Tela
        self.register_handler(
            lambda d: "capturar região" in d,
            lambda d: self._runner(["noctalia", "msg", "screenshot-region"])
        )
        self.register_handler(
            lambda d: "capturar a tela inteira" in d,
            lambda d: self._runner(["noctalia", "msg", "screenshot-fullscreen"])
        )

        # Conta-gotas Hyprpicker
        self.register_handler(
            lambda d: "conta-gotas" in d,
            lambda d: self._runner(["hyprpicker", "-a", "-n"])
        )

        # Painéis do Noctalia Shell
        self.register_handler(
            lambda d: "central de controle" in d,
            lambda d: self._runner(["noctalia", "msg", "panel-toggle", "control-center"])
        )
        self.register_handler(
            lambda d: "lançador" in d,
            lambda d: self._runner(["noctalia", "msg", "panel-toggle", "launcher"])
        )
        self.register_handler(
            lambda d: "wallpapers" in d or "papéis de parede" in d,
            lambda d: self._runner(["noctalia", "msg", "panel-toggle", "wallpaper"])
        )
        self.register_handler(
            lambda d: "área de transferência" in d or "clipboard" in d,
            lambda d: self._runner(["noctalia", "msg", "panel-toggle", "clipboard"])
        )
        self.register_handler(
            lambda d: "configurações do noctalia" in d,
            lambda d: self._runner(["noctalia", "msg", "settings-toggle"])
        )
        self.register_handler(
            lambda d: "bloquear a tela" in d,
            lambda d: self._runner(["noctalia", "msg", "session", "lock"])
        )
        self.register_handler(
            lambda d: "menu de energia" in d,
            lambda d: self._runner(["noctalia", "msg", "panel-toggle", "session"])
        )

        # Gerenciador de Rede
        self.register_handler(
            lambda d: "gerenciador de conexões" in d or "rede" in d,
            lambda d: self._runner(["bash", os.path.expanduser("~/.local/bin/network-manager.sh")])
        )

        # Alternador de Telas Sunshine / Moonlight
        self.register_handler(
            lambda d: "stream" in d or "alternar entre telas" in d,
            lambda d: self._runner(["bash", os.path.expanduser("~/.local/bin/sunshine-switch-monitor.sh")])
        )

    def is_executable(self, desc: str) -> bool:
        """Determina se a descrição informada representa uma ação disparável diretamente."""
        dl = desc.lower()
        return any(trigger in dl for trigger in self.EXECUTABLE_TRIGGERS)

    def dispatch(self, desc: str) -> bool:
        """Executa a ação correspondente à descrição."""
        dl = desc.lower()
        for matcher, handler in self._handlers:
            if matcher(dl):
                handler(desc)
                return True
        return False

# Instância padrão global para uso direto
default_dispatcher = ActionDispatcher()

def is_action_executable(desc: str) -> bool:
    """Função utilitária de compatibilidade direta."""
    return default_dispatcher.is_executable(desc)

def dispatch_action(desc: str) -> bool:
    """Função utilitária de compatibilidade direta."""
    return default_dispatcher.dispatch(desc)
