#!/usr/bin/env python3
import unittest
import pty
import os
import select
import time
import subprocess
import shutil

class TestAppSelectorTUI(unittest.TestCase):
    def setUp(self):
        self.repo_dir = "/home/felipe/cachyos-hypr-noctalia"
        self.tui_bin = os.path.join(self.repo_dir, "bin", "app_selector_tui.py")
        self.test_out = "/tmp/test_selector_out.txt"
        if os.path.exists(self.test_out):
            os.remove(self.test_out)

    def tearDown(self):
        if os.path.exists(self.test_out):
            os.remove(self.test_out)

    def test_esc_cancellation_exits_130_and_does_not_create_file(self):
        master, slave = pty.openpty()
        pid = os.fork()
        if pid == 0:
            os.close(master)
            os.dup2(slave, 0)
            os.dup2(slave, 1)
            os.dup2(slave, 2)
            os.close(slave)
            os.execlp("python3", "python3", self.tui_bin,
                      "--title", "Teste Cancelamento ESC",
                      "--out", self.test_out,
                      "app1", "Desc 1", "ON",
                      "app2", "Desc 2", "OFF")
        else:
            os.close(slave)
            time.sleep(0.15)
            # Enviar ESC
            os.write(master, b"\x1b")
            time.sleep(0.1)
            _, status = os.waitpid(pid, 0)
            exit_code = os.waitstatus_to_exitcode(status)
            os.close(master)
            self.assertEqual(exit_code, 130)
            self.assertFalse(os.path.exists(self.test_out))

    def test_q_cancellation_exits_130(self):
        master, slave = pty.openpty()
        pid = os.fork()
        if pid == 0:
            os.close(master)
            os.dup2(slave, 0)
            os.dup2(slave, 1)
            os.dup2(slave, 2)
            os.close(slave)
            os.execlp("python3", "python3", self.tui_bin,
                      "--title", "Teste Cancelamento Q",
                      "--out", self.test_out,
                      "app1", "Desc 1", "ON")
        else:
            os.close(slave)
            time.sleep(0.15)
            # Enviar Q
            os.write(master, b"q")
            time.sleep(0.1)
            _, status = os.waitpid(pid, 0)
            exit_code = os.waitstatus_to_exitcode(status)
            os.close(master)
            self.assertEqual(exit_code, 130)
            self.assertFalse(os.path.exists(self.test_out))

    def test_enter_saves_initial_selection(self):
        master, slave = pty.openpty()
        pid = os.fork()
        if pid == 0:
            os.close(master)
            os.dup2(slave, 0)
            os.dup2(slave, 1)
            os.dup2(slave, 2)
            os.close(slave)
            os.execlp("python3", "python3", self.tui_bin,
                      "--title", "Teste Enter",
                      "--out", self.test_out,
                      "discord", "Discord Chat", "ON",
                      "btop", "Monitor btop", "OFF",
                      "micro", "Editor Micro", "ON")
        else:
            os.close(slave)
            time.sleep(0.15)
            # Enviar ENTER
            os.write(master, b"\r")
            time.sleep(0.1)
            _, status = os.waitpid(pid, 0)
            exit_code = os.waitstatus_to_exitcode(status)
            os.close(master)
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(self.test_out))
            with open(self.test_out, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(lines, ["discord", "micro"])

    def test_toggle_space_and_navigation(self):
        master, slave = pty.openpty()
        pid = os.fork()
        if pid == 0:
            os.close(master)
            os.dup2(slave, 0)
            os.dup2(slave, 1)
            os.dup2(slave, 2)
            os.close(slave)
            os.execlp("python3", "python3", self.tui_bin,
                      "--title", "Teste Toggle",
                      "--out", self.test_out,
                      "app1", "Desc 1", "ON",
                      "app2", "Desc 2", "OFF")
        else:
            os.close(slave)
            time.sleep(0.15)
            # Desmarcar app1 (Espaço), descer (Down), marcar app2 (Espaço), Salvar (Enter)
            os.write(master, b" \x1b[B \r")
            time.sleep(0.1)
            _, status = os.waitpid(pid, 0)
            exit_code = os.waitstatus_to_exitcode(status)
            os.close(master)
            self.assertEqual(exit_code, 0)
            with open(self.test_out, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(lines, ["app2"])

    def test_non_interactive_fallback(self):
        # Executar sem TTY direto (redirecionando stdin de devnull)
        res = subprocess.run(
            ["python3", self.tui_bin,
             "--title", "Teste Não Interativo",
             "--out", self.test_out,
             "app1", "Desc 1", "ON",
             "app2", "Desc 2", "OFF",
             "app3", "Desc 3", "ON"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(self.test_out))
        with open(self.test_out, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertEqual(lines, ["app1", "app3"])

if __name__ == "__main__":
    unittest.main()
