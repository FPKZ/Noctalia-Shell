#!/usr/bin/env bash
# ==============================================================================
# bin/app-selector.sh
# Módulo de Descoberta, Seleção Interativa, Instalação e Sincronização da Dock
# ==============================================================================

# Lista de pastas internas/de sistema a ignorar na varredura de ~/.config
is_system_blacklisted() {
    local name="$1"
    case "$name" in
        hypr|noctalia|kitty|qt6ct|qt5ct|swash|uwsm|systemd) return 0 ;;
        gtk-*|gtkrc*|dconf|mimeapps.list|user-dirs.*|fontconfig|autostart|xsettingsd|pulse|menus|trashrc|session) return 0 ;;
        KDE|kdeglobals|kglobalshortcutsrc|kiorc|kmenueditrc|konsolerc|konsolesshconfig|krdcrc|krunnerrc) return 0 ;;
        ksmserverrc|ktimezonedrc|kwalletrc|kwinoutputconfig.json|kwinrc|kwinrulesrc|kwriterc) return 0 ;;
        libaccounts-glib|libinput-gestures.conf|plasma*|powerdevilrc|powermanagementprofilesrc|spectaclerc) return 0 ;;
        systemmonitorrc|baloofile*|bluedevilglobalrc|dolphinrc|filetypesrc|gwenviewrc|kaccessrc) return 0 ;;
        kactivity*|kate*|kcminputrc|kconf_updaterc|kded*|partitionmanagerrc|pavucontrol.ini|QtProject.conf|Trolltech.conf) return 0 ;;
        composer|configstore|flutter|turborepo|unity3d|Android*|Antigravity*|Google|cachyos*|HTTPClient|shakaran|shelly|pupgui) return 0 ;;
        .*) return 0 ;;
        *) return 1 ;;
    esac
}

# Mapeia o diretório de configuração em ~/.config para o pacote oficial ou AUR
get_package_info() {
    local folder="$1"
    case "$folder" in
        alacritty)        echo "alacritty:Emulador de Terminal Alacritty (GPU)" ;;
        btop)             echo "btop:Monitor de Recursos Interativo btop" ;;
        discord)          echo "discord:Chat e Comunicação Discord" ;;
        fastfetch)        echo "fastfetch:Informações do Sistema no Terminal" ;;
        fish)             echo "fish:Shell Interativo Fish" ;;
        micro)            echo "micro:Editor de Texto no Terminal" ;;
        mpv)              echo "mpv:Player de Mídia Leve MPV" ;;
        qBittorrent)      echo "qbittorrent:Cliente BitTorrent qBittorrent" ;;
        vlc)              echo "vlc:Player de Mídia VLC" ;;
        telegram-desktop) echo "telegram-desktop:Telegram Desktop Messenger" ;;
        filezilla)        echo "filezilla:Cliente FTP/SFTP FileZilla" ;;
        heroic)           echo "heroic-games-launcher-bin:Heroic Games Launcher (Epic/GOG)" ;;
        remmina)          echo "remmina:Cliente de Conexão Remota Remmina" ;;
        rustdesk)         echo "rustdesk-bin:RustDesk Acesso Remoto" ;;
        Postman)          echo "postman-bin:Postman API Client" ;;
        BraveSoftware)    echo "brave-bin:Navegador Web Brave" ;;
        google-chrome)    echo "google-chrome:Navegador Google Chrome" ;;
        chromium)         echo "chromium:Navegador Web Chromium" ;;
        sunshine)         echo "sunshine:Sunshine Game Stream Host" ;;
        waybar)           echo "waybar:Barra de Status Waybar" ;;
        faugus-launcher)  echo "faugus-launcher:Faugus Launcher" ;;
        winboat)          echo "winboat:Winboat" ;;
        ZapZap)           echo "zapzap:ZapZap WhatsApp Client" ;;
        1Password)        echo "1password:Gerenciador de Senhas 1Password" ;;
        *)
            local lower
            lower=$(echo "$folder" | tr '[:upper:]' '[:lower:]')
            echo "${lower}:Configurações de $folder"
            ;;
    esac
}

# Varre ~/.config e retorna lista de pastas elegíveis
scan_user_apps() {
    local src_dir="${1:-$HOME/.config}"
    local apps=()
    if [ ! -d "$src_dir" ]; then
        return 0
    fi
    for entry in "$src_dir"/*; do
        if [ -d "$entry" ]; then
            local base
            base=$(basename "$entry")
            if ! is_system_blacklisted "$base"; then
                apps+=("$base")
            fi
        fi
    done
    printf "%s\n" "${apps[@]}" | sort
}

# Exibe checklist interativo no terminal (whiptail -> fzf -> fallback)
# Argumentos:
#   $1 = Título da Janela
#   $2 = Texto de Instrução
#   Array restante = lista de tuplas "TAG" "DESC" "STATUS"
prompt_checklist() {
    local title="$1"
    local prompt="$2"
    shift 2
    local items=("$@")

    # 1. Tentar whiptail se terminal estiver disponível
    if [ -t 0 ] && [ -t 1 ] && command -v whiptail >/dev/null 2>&1; then
        local choices
        choices=$(whiptail --title "$title" \
                           --checklist "$prompt" \
                           22 78 12 \
                           --separate-output \
                           "${items[@]}" 3>&1 1>&2 2>&3) || true
        echo "$choices"
        return 0
    fi

    # 2. Tentar fzf se terminal estiver disponível
    if [ -t 0 ] && [ -t 1 ] && command -v fzf >/dev/null 2>&1; then
        local fzf_input=()
        local i=0
        while [ $i -lt ${#items[@]} ]; do
            local tag="${items[$i]}"
            local desc="${items[$((i+1))]}"
            local status="${items[$((i+2))]}"
            fzf_input+=("$tag - $desc ($status)")
            i=$((i+3))
        done
        local selected
        selected=$(printf "%s\n" "${fzf_input[@]}" | fzf --multi --prompt="Selecione com TAB > " --header="$title - $prompt" | awk '{print $1}') || true
        echo "$selected"
        return 0
    fi

    # 3. Fallback não-interativo ou texto puro: retorna todos os itens marcados como ON
    local fallback_selected=()
    local i=0
    while [ $i -lt ${#items[@]} ]; do
        local tag="${items[$i]}"
        local status="${items[$((i+2))]}"
        if [ "$status" == "ON" ]; then
            fallback_selected+=("$tag")
        fi
        i=$((i+3))
    done
    printf "%s\n" "${fallback_selected[@]}"
}

# Garante a instalação do gerenciador yay (AUR Helper)
ensure_yay_installed() {
    if command -v yay >/dev/null 2>&1; then
        echo "   [yay] Gerenciador AUR (yay) já instalado e operacional: $(command -v yay)"
        return 0
    fi

    echo "-> [yay] 'yay' não encontrado. Instalando automaticamente via AUR..."
    sudo pacman -S --needed --noconfirm base-devel git

    local YAY_TMP="/tmp/yay-install-$$"
    rm -rf "$YAY_TMP"
    mkdir -p "$YAY_TMP"

    # Se estiver rodando sob sudo, rodar makepkg como o usuário normal
    local RUN_AS_USER=""
    if [ "$(id -u)" -eq 0 ] && [ -n "$SUDO_USER" ]; then
        chown -R "$SUDO_USER" "$YAY_TMP"
        RUN_AS_USER="sudo -u $SUDO_USER"
    fi

    echo "   Clonando yay-bin do AUR..."
    if $RUN_AS_USER git clone https://aur.archlinux.org/yay-bin.git "$YAY_TMP"; then
        echo "   Compilando e instalando yay-bin..."
        (cd "$YAY_TMP" && $RUN_AS_USER makepkg -si --noconfirm)
    else
        echo "   Fallback: clonando yay (código-fonte)..."
        rm -rf "$YAY_TMP"
        mkdir -p "$YAY_TMP"
        if [ -n "$RUN_AS_USER" ]; then chown -R "$SUDO_USER" "$YAY_TMP"; fi
        $RUN_AS_USER git clone https://aur.archlinux.org/yay.git "$YAY_TMP"
        (cd "$YAY_TMP" && $RUN_AS_USER makepkg -si --noconfirm)
    fi
    rm -rf "$YAY_TMP"

    if command -v yay >/dev/null 2>&1; then
        echo "-> [yay] 'yay' instalado e validado com sucesso!"
    else
        echo "-> [AVISO] Não foi possível verificar o binário do 'yay'. Verifique a instalação do AUR manualmente."
    fi
}

# Sincroniza a configuração da Dock entre settings.toml e config.toml
sync_noctalia_dock() {
    local settings_file="$1"
    local config_file="$2"

    if [ ! -f "$settings_file" ] || [ ! -f "$config_file" ]; then
        return 0
    fi

    python3 -c "
import tomllib, os, sys

settings_path = '$settings_file'
config_path = '$config_file'

try:
    with open(settings_path, 'rb') as f:
        settings = tomllib.load(f)
    dock = settings.get('dock', {})
    if not dock:
        sys.exit(0)

    with open(config_path, 'r', encoding='utf-8') as f:
        orig_config = f.read()

    lines = orig_config.splitlines(keepends=True)
    new_lines = []
    in_dock = False
    for line in lines:
        if line.strip().startswith('[dock]'):
            in_dock = True
            continue
        elif in_dock and line.strip().startswith('['):
            in_dock = False
        if not in_dock:
            new_lines.append(line)

    dock_str = '\n[dock]\n'
    for k, v in sorted(dock.items()):
        if isinstance(v, bool):
            val_str = 'true' if v else 'false'
        elif isinstance(v, float):
            val_str = f'{v:.2f}'
        elif isinstance(v, int):
            val_str = str(v)
        else:
            val_str = f'\"{v}\"'
        dock_str += f'{k} = {val_str}\n'

    final_content = ''.join(new_lines).rstrip() + '\n' + dock_str
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print('   Dock sincronizada com sucesso em config.toml!')
except Exception as e:
    print(f'   [Aviso] Erro ao sincronizar dock: {e}')
"
}
