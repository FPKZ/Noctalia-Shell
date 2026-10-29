#!/usr/bin/env python3
import unittest
import os
import json
import importlib.util

# Importar diretamente o script
spec = importlib.util.spec_from_file_location("sunshine_switch", "/home/felipe/cachyos-hypr-noctalia/bin/sunshine-switch-monitor.py")
sunshine_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sunshine_mod)

class TestSunshineSwitchMonitor(unittest.TestCase):
    def setUp(self):
        self.state_file = "/tmp/test_hypr_sunshine_state.json"
        sunshine_mod.STATE_FILE = self.state_file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

        # Mock das chamadas subprocess
        self.executed_commands = []
        sunshine_mod.subprocess.run = self.mock_subprocess_run
        sunshine_mod.notify = lambda title, msg: None

    def tearDown(self):
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def mock_subprocess_run(self, cmd, **kwargs):
        self.executed_commands.append(cmd)
        class Dummy:
            returncode = 0
        return Dummy()

    def test_cycle_2_monitors(self):
        monitors = [
            {"id": 0, "name": "DP-1"},
            {"id": 1, "name": "HDMI-A-1"}
        ]
        
        # 1º Cycle -> Vai para offset 1
        sunshine_mod.action_cycle(monitors)
        self.assertEqual(sunshine_mod.load_state(2), 1)
        self.assertTrue(any("swap_monitors" in str(c) for c in self.executed_commands))

        # 2º Cycle -> Volta para offset 0
        self.executed_commands.clear()
        sunshine_mod.action_cycle(monitors)
        self.assertEqual(sunshine_mod.load_state(2), 0)

    def test_cycle_3_monitors(self):
        monitors = [
            {"id": 0, "name": "DP-1"},
            {"id": 1, "name": "HDMI-A-1"},
            {"id": 2, "name": "DP-2"}
        ]

        # Inicia em 0 -> vai para 1
        sunshine_mod.action_cycle(monitors)
        self.assertEqual(sunshine_mod.load_state(3), 1)

        # 1 -> 2
        sunshine_mod.action_cycle(monitors)
        self.assertEqual(sunshine_mod.load_state(3), 2)

        # 2 -> 0 (volta ao início)
        sunshine_mod.action_cycle(monitors)
        self.assertEqual(sunshine_mod.load_state(3), 0)

    def test_set_and_reset_3_monitors(self):
        monitors = [
            {"id": 0, "name": "DP-1"},
            {"id": 1, "name": "HDMI-A-1"},
            {"id": 2, "name": "DP-2"}
        ]

        # Pular direto para Monitor 3
        sunshine_mod.action_set(monitors, 3)
        self.assertEqual(sunshine_mod.load_state(3), 2)

        # Resetar para a tela inicial (Monitor 1)
        sunshine_mod.action_reset(monitors)
        self.assertEqual(sunshine_mod.load_state(3), 0)

if __name__ == "__main__":
    unittest.main()
