-- Auto-start config
-- if you dont use UWSM add your auto start programs here, otherwise use XDG autostart https://wiki.archlinux.org/title/XDG_Autostart

hl.on("hyprland.start", function ()
    hl.exec_cmd("dbus-update-activation-environment --systemd --all")
    hl.exec_cmd("kwalletd6")
    hl.exec_cmd("noctalia")
    hl.exec_cmd("kdeconnect-indicator")
    hl.exec_cmd("xhost +SI:localuser:root")
    -- Configuração dinâmica de áudio (AudioRelay + PipeWire)
    hl.exec_cmd(os.getenv("HOME") .. "/.local/bin/setup-audiorelay.sh")
    -- Restaurar sessão de janelas e iniciar salvamento periódico a cada 60s
    hl.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/session.py restore")
    hl.exec_cmd("bash -c 'while true; do sleep 60; python3 $HOME/.config/hypr/scripts/session.py save; done'")
    -- Pré-aquecimento do menu de atalhos para abertura instantânea (<5ms)
    hl.exec_cmd("python3 " .. os.getenv("HOME") .. "/.config/hypr/scripts/keybinds-gui.py --daemon")
end)
