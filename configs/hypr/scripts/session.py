#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time

SESSION_FILE = os.path.expanduser("~/.cache/hyprland-session.json")

# Classes para ignorar (painéis, daemons, utilitários, autenticadores)
IGNORE_CLASSES = {
    "", "noctalia", "swash", "hyprpicker", "polkit-kde-authentication-agent-1",
    "org.kde.polkit-kde-authentication-agent-1", "xwaylandvideobridge",
    "kdeconnect.daemon", "kdeconnect-indicator", "pavucontrol", "blueman-manager"
}

# Mapeamento de classe de janela para comando executável
CLASS_MAP = {
    "org.kde.dolphin": "dolphin",
    "org.kde.kate": "kate",
    "org.kde.kwrite": "kwrite",
    "org.kde.gwenview": "gwenview",
    "org.kde.konsole": "konsole",
    "org.kde.kdeconnect.app": "kdeconnect-app",
    "google-chrome": "google-chrome-stable",
    "code-oss": "code",
    "zapzap": "zapzap"
}

def get_clients():
    try:
        out = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
        return json.loads(out)
    except Exception:
        return []

def save_session():
    clients = get_clients()
    session = []
    seen = set()
    for c in clients:
        cls = c.get("class", "").strip()
        ws = c.get("workspace", {}).get("id", 1)
        # Ignorar janelas especiais (scratchpad) ou inválidas
        if ws <= 0 or cls in IGNORE_CLASSES or cls.lower() in IGNORE_CLASSES:
            continue
        
        cmd = CLASS_MAP.get(cls, cls)
        key = (cmd, ws)
        if key not in seen:
            seen.add(key)
            session.append({"cmd": cmd, "workspace": ws, "class": cls})
            
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        json.dump(session, f, indent=2)

def restore_session():
    if not os.path.exists(SESSION_FILE):
        return
    try:
        with open(SESSION_FILE, "r") as f:
            session = json.load(f)
    except Exception:
        return

    for item in session:
        cmd = item.get("cmd")
        ws = item.get("workspace", 1)
        if cmd:
            dispatch_cmd = f"[workspace {ws} silent] {cmd}"
            subprocess.run(["hyprctl", "dispatch", "exec", dispatch_cmd])
            time.sleep(0.2)

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "save"
    if action == "save":
        save_session()
    elif action == "restore":
        restore_session()
