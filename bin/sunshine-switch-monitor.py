#!/usr/bin/env python3
# ==============================================================================
# bin/sunshine-switch-monitor.py
# Alternador Dinâmico de Telas para Streaming via Sunshine e Moonlight no Hyprland
# Suporta 2, 3 ou mais telas, com rotação contínua (estilo Chrome Remote Desktop),
# seleção direta de tela e restauração automática (reset).
# ==============================================================================
import sys
import os
import json
import argparse
import subprocess

STATE_FILE = "/tmp/hypr_sunshine_monitor_state.json"

def get_monitors():
    """Obtém a lista de monitores ativos do Hyprland ordenados por ID."""
    try:
        out = subprocess.check_output(["hyprctl", "-j", "monitors"], text=True)
        data = json.loads(out)
        return sorted(data, key=lambda m: m.get("id", 0))
    except Exception as e:
        print(f"Erro ao consultar monitores do Hyprland: {e}", file=sys.stderr)
        return []

def load_state(total_monitors: int) -> int:
    """Carrega o offset atual (0 = tela inicial, 1 = tela 2, etc)."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                offset = data.get("offset", 0)
                if 0 <= offset < total_monitors:
                    return offset
        except Exception:
            pass
    return 0

def save_state(offset: int, monitor_name: str):
    """Salva o offset atual em arquivo temporário."""
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"offset": offset, "monitor": monitor_name}, f)
    except Exception as e:
        print(f"Aviso: erro ao salvar estado: {e}", file=sys.stderr)

def rotate_workspace_ring(monitors: list[dict]):
    """Executa a permutação cíclica entre todos os monitores conectados."""
    n = len(monitors)
    if n < 2:
        return
    for i in range(n - 1):
        m1 = monitors[i]["name"]
        m2 = monitors[i + 1]["name"]
        cmd = f"hl.dispatch(hl.dsp.workspace.swap_monitors({{ monitor1 = '{m1}', monitor2 = '{m2}' }}))"
        subprocess.run(["hyprctl", "repl", cmd], capture_output=True)

def notify(title: str, message: str):
    """Envia notificação visual na tela."""
    subprocess.run([
        "notify-send",
        "-t", "1800",
        "-a", "Sunshine / Moonlight",
        "-i", "video-display",
        title,
        message
    ], capture_output=True)

def action_cycle(monitors: list[dict]):
    n = len(monitors)
    if n <= 1:
        notify("Alternador de Telas", "Apenas 1 monitor ativo detectado no sistema.")
        return

    cur_offset = load_state(n)
    rotate_workspace_ring(monitors)
    new_offset = (cur_offset + 1) % n
    current_stream_monitor = monitors[new_offset]["name"]
    save_state(new_offset, current_stream_monitor)

    desc = f"Exibindo Tela {new_offset + 1} de {n} ({current_stream_monitor})"
    print(desc)
    notify("🖥️ Stream Moonlight", desc)

def action_reset(monitors: list[dict]):
    n = len(monitors)
    if n <= 1:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        return

    cur_offset = load_state(n)
    if cur_offset != 0:
        steps_needed = (n - cur_offset) % n
        for _ in range(steps_needed):
            rotate_workspace_ring(monitors)
        save_state(0, monitors[0]["name"])
        notify("🖥️ Stream Moonlight", f"Telas restauradas para a configuração original ({monitors[0]['name']})")
    else:
        save_state(0, monitors[0]["name"])

def action_set(monitors: list[dict], target_idx: int):
    n = len(monitors)
    if n <= 1:
        return

    target_offset = target_idx - 1
    if not (0 <= target_offset < n):
        print(f"Índice de monitor inválido: {target_idx}. Monitores disponíveis: 1 a {n}", file=sys.stderr)
        return

    cur_offset = load_state(n)
    steps_needed = (target_offset - cur_offset) % n
    for _ in range(steps_needed):
        rotate_workspace_ring(monitors)

    save_state(target_offset, monitors[target_offset]["name"])
    desc = f"Exibindo Tela {target_offset + 1} de {n} ({monitors[target_offset]['name']})"
    print(desc)
    notify("🖥️ Stream Moonlight", desc)

def main():
    parser = argparse.ArgumentParser(description="Alternador de Monitores para Sunshine/Moonlight no Hyprland")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("cycle", help="Alterna ciclicamente para a próxima tela")
    subparsers.add_parser("reset", help="Restaura as telas para a posição original")
    
    set_parser = subparsers.add_parser("set", help="Seleciona diretamente um monitor específico (1, 2, 3...)")
    set_parser.add_argument("index", type=int, help="Número do monitor (1 a N)")

    args = parser.parse_args()
    cmd = args.command or "cycle"

    monitors = get_monitors()
    if not monitors:
        print("Nenhum monitor detectado.", file=sys.stderr)
        sys.exit(1)

    if cmd == "cycle":
        action_cycle(monitors)
    elif cmd == "reset":
        action_reset(monitors)
    elif cmd == "set":
        action_set(monitors, args.index)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
