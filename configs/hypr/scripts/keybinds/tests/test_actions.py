import unittest
from keybinds.actions import ActionDispatcher, is_action_executable

class TestActions(unittest.TestCase):
    def test_is_action_executable(self):
        self.assertTrue(is_action_executable("Abrir Terminal Kitty"))
        self.assertTrue(is_action_executable("Abrir Gerenciador de Arquivos Dolphin"))
        self.assertTrue(is_action_executable("Capturar Região"))
        self.assertTrue(is_action_executable("Central de Controle"))
        self.assertTrue(is_action_executable("Executar: pavucontrol"))
        self.assertFalse(is_action_executable("Mover janela para a esquerda"))
        self.assertFalse(is_action_executable("Alternar modo flutuante"))

    def test_dispatcher_mocked_execution(self):
        executed_cmds = []

        def mock_runner(cmd, env=None):
            executed_cmds.append((cmd, env))
            return None

        dispatcher = ActionDispatcher(runner=mock_runner)

        # Testar Kitty
        success = dispatcher.dispatch("Abrir Terminal Kitty")
        self.assertTrue(success)
        self.assertEqual(executed_cmds[-1][0], ["kitty"])

        # Testar Dolphin com ambiente KDE
        success = dispatcher.dispatch("Abrir Dolphin")
        self.assertTrue(success)
        self.assertEqual(executed_cmds[-1][0], ["dolphin"])
        self.assertEqual(executed_cmds[-1][1]["XDG_CURRENT_DESKTOP"], "KDE")

        # Testar comando customizado
        success = dispatcher.dispatch("Executar: btop --fast")
        self.assertTrue(success)
        self.assertEqual(executed_cmds[-1][0], ["btop", "--fast"])

    def test_dispatcher_extensibility(self):
        executed = []
        dispatcher = ActionDispatcher(runner=lambda cmd, env=None: executed.append(cmd))
        
        # Registrar novo manipulador (OCP)
        dispatcher.register_handler(
            lambda d: "spotify" in d,
            lambda d: executed.append(["spotify-player"])
        )

        success = dispatcher.dispatch("Tocar música no Spotify")
        self.assertTrue(success)
        self.assertEqual(executed[-1], ["spotify-player"])

if __name__ == "__main__":
    unittest.main()
