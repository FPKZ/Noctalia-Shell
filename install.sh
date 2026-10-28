#!/usr/bin/env bash
# ==============================================================================
# install.sh
# Instalador Universal: CachyOS Hyprland + Noctalia Shell + Apps Pessoais
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_USER="$(whoami)"
TARGET_HOME="$HOME"

# Carregar utilitários de seleção, pacotes e dock
if [ -f "$SCRIPT_DIR/bin/app-selector.sh" ]; then
    source "$SCRIPT_DIR/bin/app-selector.sh"
else
    echo "Erro: '$SCRIPT_DIR/bin/app-selector.sh' não encontrado!"
    exit 1
fi

echo "=========================================================="
echo "  Instalador Universal: CachyOS Hyprland + Noctalia Shell"
echo "  Destino: Usuário $TARGET_USER ($TARGET_HOME)"
echo "=========================================================="
echo ""

# 1. Verificar e instalar pacotes necessários e AUR Helper (yay)
echo "-> [1/8] Verificando e instalando componentes do Hyprland, Noctalia e Yay..."
if command -v pacman >/dev/null 2>&1; then
    # Lista atômica de pacotes para evitar conflitos de meta-pacotes com KDE Plasma
    PACKAGES=(
        hyprland
        noctalia
        swash
        kitty
        dolphin
        qt6ct
        grim
        slurp
        wl-clipboard
        uwsm
        hyprpicker
        xdg-desktop-portal-hyprland
        xorg-xhost
        adw-gtk-theme
        kde-cli-tools
        kdeconnect
        python3
        pyside6
        fzf
        which
        libnewt
        network-manager-applet
    )
    echo "Instalando pacotes base do sistema..."
    sudo pacman -S --needed --noconfirm "${PACKAGES[@]}"

    # Garantir que o gerenciador AUR 'yay' esteja instalado na máquina
    ensure_yay_installed

    # Garantir audiorelay via yay/paru se disponível
    if command -v yay >/dev/null 2>&1; then
        echo "Instalando audiorelay via yay..."
        yay -S --needed --noconfirm audiorelay 2>/dev/null || true
    elif command -v paru >/dev/null 2>&1; then
        echo "Instalando audiorelay via paru..."
        paru -S --needed --noconfirm audiorelay 2>/dev/null || true
    fi
fi

# 2. Seleção Interativa de Aplicativos Opcionais (Antes de tocar nos dotfiles)
echo ""
echo "-> [2/8] Selecionando aplicativos e configurações personalizadas..."
MANIFEST_FILE="$SCRIPT_DIR/configs/custom-apps.conf"
TMP_INSTALL_SEL=$(mktemp)

declare -A APP_PKGS
declare -A APP_DESCS

if [ -f "$MANIFEST_FILE" ]; then
    INSTALL_CHECKLIST=()

    while IFS=':' read -r f_name p_name d_desc d_status; do
        [[ "$f_name" =~ ^#.*$ || -z "$f_name" ]] && continue
        APP_PKGS["$f_name"]="$p_name"
        APP_DESCS["$f_name"]="$d_desc"
        INSTALL_CHECKLIST+=("$f_name" "$d_desc" "ON")
    done < "$MANIFEST_FILE"

    if [ "$1" == "--batch" ] || [ "$2" == "--batch" ] || [ "$1" == "--all" ] || [ "$2" == "--all" ] || [ ! -t 0 ]; then
        echo "   Modo não-interativo ativo: instalando todos os aplicativos do pacote."
        for k in "${!APP_PKGS[@]}"; do
            echo "$k" >> "$TMP_INSTALL_SEL"
        done
    else
        if ! prompt_checklist "Instalação de Aplicativos Opcionais" \
            "Selecione os aplicativos e configurações que deseja instalar nesta máquina:" \
            "$TMP_INSTALL_SEL" \
            "${INSTALL_CHECKLIST[@]}"; then
            echo ""
            echo -e "\033[1;33m-> Instalação cancelada pelo usuário (ESC/Q). Nenhuma alteração foi realizada nos dotfiles.\033[0m"
            rm -f "$TMP_INSTALL_SEL"
            exit 0
        fi
    fi
fi

# 3. Implantação de Dotfiles Base em ~/.config
echo ""
echo "-> [3/8] Implantando dotfiles base em $TARGET_HOME/.config..."
mkdir -p "$TARGET_HOME/.config"

# Copiar dotfiles do sistema, ignorando pastas de apps opcionais
for d in "$SCRIPT_DIR/configs/"*; do
    b_name=$(basename "$d")
    if [ "$b_name" != "apps" ] && [ "$b_name" != "custom-apps.conf" ]; then
        cp -r "$d" "$TARGET_HOME/.config/"
    fi
done

# Ajustar caminho do tema do qt6ct para o HOME do usuário atual
sed -i "s|color_scheme_path=.*|color_scheme_path=$TARGET_HOME/.config/qt6ct/colors/noctalia.conf|g" "$TARGET_HOME/.config/qt6ct/qt6ct.conf" 2>/dev/null || true

# Auto-detectar monitores reais de vídeo na máquina de instalação
echo "Detectando monitores de vídeo conectados..."
PRIMARY_DETECTED=$(hyprctl monitors 2>/dev/null | grep -E "^Monitor " | head -n1 | awk '{print $2}' || true)
if [ -z "$PRIMARY_DETECTED" ]; then
    PRIMARY_DETECTED=$(for f in /sys/class/drm/card*-*/status; do if [ -f "$f" ] && grep -q "^connected" "$f"; then basename $(dirname "$f") | cut -d'-' -f2-; break; fi; done)
fi

SECONDARY_DETECTED=$(hyprctl monitors 2>/dev/null | grep -E "^Monitor " | sed -n '2p' | awk '{print $2}' || true)
if [ -z "$SECONDARY_DETECTED" ]; then
    SECONDARY_DETECTED=$(for f in /sys/class/drm/card*-*/status; do if [ -f "$f" ] && grep -q "^connected" "$f"; then basename $(dirname "$f") | cut -d'-' -f2-; fi; done | sed -n '2p' || true)
fi

if [ -n "$PRIMARY_DETECTED" ]; then
    echo "Monitor primário identificado: $PRIMARY_DETECTED"
    sed -i "s|MONITOR1 = .*|MONITOR1 = \"$PRIMARY_DETECTED\"|g" "$TARGET_HOME/.config/hypr/config/variables.lua" 2>/dev/null || true
    sed -i "s|PRIMARY_MONITOR = .*|PRIMARY_MONITOR = MONITOR1|g" "$TARGET_HOME/.config/hypr/config/variables.lua" 2>/dev/null || true
fi

if [ -n "$SECONDARY_DETECTED" ]; then
    echo "Monitor secundário identificado: $SECONDARY_DETECTED"
    sed -i "s|MONITOR2 = .*|MONITOR2 = \"$SECONDARY_DETECTED\"|g" "$TARGET_HOME/.config/hypr/config/variables.lua" 2>/dev/null || true
else
    sed -i "s|MONITOR2 = .*|MONITOR2 = \"\"|g" "$TARGET_HOME/.config/hypr/config/variables.lua" 2>/dev/null || true
fi

# 4. Implantação de Ícones, Temas, Wallpaper e Estado do Noctalia (com Dock 100% ativa)
echo ""
echo "-> [4/8] Instalando cursores, esquemas de cores, wallpaper e estado do Noctalia..."
mkdir -p "$TARGET_HOME/.local/share/icons"
mkdir -p "$TARGET_HOME/.local/share/color-schemes"
mkdir -p "$TARGET_HOME/.local/share/wallpapers"
mkdir -p "$TARGET_HOME/Imagens"
mkdir -p "$TARGET_HOME/.local/state/noctalia"
mkdir -p "$TARGET_HOME/.local/bin"

# Cursores
if [ -d "$SCRIPT_DIR/icons/Bibata-Modern-Ice" ]; then
    cp -r "$SCRIPT_DIR/icons/Bibata-Modern-Ice" "$TARGET_HOME/.local/share/icons/"
fi

# Esquema de cores
if [ -f "$SCRIPT_DIR/color-schemes/noctalia.colors" ]; then
    cp "$SCRIPT_DIR/color-schemes/noctalia.colors" "$TARGET_HOME/.local/share/color-schemes/"
fi

# Wallpaper personalizado (usado pelo Noctalia para gerar o tema Material You)
if [ -f "$SCRIPT_DIR/wallpapers/wp15566549.jpg" ]; then
    echo "Copiando wallpaper para $TARGET_HOME/Imagens e $TARGET_HOME/.local/share/wallpapers..."
    cp "$SCRIPT_DIR/wallpapers/wp15566549.jpg" "$TARGET_HOME/Imagens/wp15566549.jpg"
    cp "$SCRIPT_DIR/wallpapers/wp15566549.jpg" "$TARGET_HOME/.local/share/wallpapers/wp15566549.jpg"
fi

# Estado e customização do Noctalia (dock, opacidade, widgets, temas da comunidade)
if [ -d "$SCRIPT_DIR/state/noctalia" ]; then
    echo "Restaurando estado e personalizações do Noctalia (dock, barra e paleta)..."
    cp -r "$SCRIPT_DIR/state/noctalia/"* "$TARGET_HOME/.local/state/noctalia/"

    # Ajustar caminhos absolutos do usuário no settings.toml e state.toml
    sed -i "s|/home/[^/]*|$TARGET_HOME|g" "$TARGET_HOME/.local/state/noctalia/settings.toml" 2>/dev/null || true
    sed -i "s|/home/[^/]*|$TARGET_HOME|g" "$TARGET_HOME/.local/state/noctalia/state.toml" 2>/dev/null || true

    # Garantir sincronização ativa da Dock tanto em config.toml quanto em settings.toml
    if [ -f "$TARGET_HOME/.local/state/noctalia/settings.toml" ]; then
        sync_noctalia_dock "$TARGET_HOME/.local/state/noctalia/settings.toml" "$TARGET_HOME/.config/noctalia/config.toml"
    fi

    # Garantir layout 'br' e modelo 'abnt2' no estado do plugin hyprland-settings
    HS_STATE="$TARGET_HOME/.local/state/noctalia/plugins/data/michael-retunzew/hyprland-settings/state.json"
    if [ -f "$HS_STATE" ]; then
        sed -i 's/"input\.kb_layout":\s*{\s*"value":\s*"[^"]*"\s*}/"input.kb_layout":{"value":"br"}/g' "$HS_STATE" 2>/dev/null || true
        sed -i 's/"input\.kb_model":\s*{\s*"value":\s*"[^"]*"\s*}/"input.kb_model":{"value":"abnt2"}/g' "$HS_STATE" 2>/dev/null || true
    fi
fi

# Utilitários de áudio / scripts de usuário
if [ -d "$SCRIPT_DIR/bin" ]; then
    cp -r "$SCRIPT_DIR/bin/"* "$TARGET_HOME/.local/bin/"
    chmod +x "$TARGET_HOME/.local/bin/"* 2>/dev/null || true
fi

# 5. Instalação e Configuração dos Aplicativos Selecionados
echo ""
echo "-> [5/8] Instalando aplicativos opcionais selecionados e restaurando dados..."
if [ -s "$TMP_INSTALL_SEL" ]; then
    PACMAN_TO_INSTALL=()
    AUR_TO_INSTALL=()

    while IFS= read -r app_folder; do
        app_folder=$(echo "$app_folder" | tr -d '"' | xargs)
        [ -z "$app_folder" ] && continue

        pkg="${APP_PKGS[$app_folder]}"
        if [ -n "$pkg" ]; then
            if ! pacman -Qi "$pkg" >/dev/null 2>&1; then
                if pacman -Si "$pkg" >/dev/null 2>&1; then
                    PACMAN_TO_INSTALL+=("$pkg")
                else
                    AUR_TO_INSTALL+=("$pkg")
                fi
            fi
        fi

        # Restaurar configuração do app
        if [ -d "$SCRIPT_DIR/configs/apps/$app_folder" ]; then
            echo "   Restaurando configurações de $app_folder..."
            mkdir -p "$TARGET_HOME/.config/$app_folder"
            cp -r "$SCRIPT_DIR/configs/apps/$app_folder/"* "$TARGET_HOME/.config/$app_folder/" 2>/dev/null || true
            sed -i "s|/home/[^/]*|$TARGET_HOME|g" "$TARGET_HOME/.config/$app_folder/"*.json "$TARGET_HOME/.config/$app_folder/"*.conf 2>/dev/null || true
        fi
    done < "$TMP_INSTALL_SEL"

    # Instalação dos pacotes pacman acumulados
    if [ ${#PACMAN_TO_INSTALL[@]} -gt 0 ]; then
        echo "   Instalando pacotes oficiais via pacman: ${PACMAN_TO_INSTALL[*]}"
        sudo pacman -S --needed --noconfirm "${PACMAN_TO_INSTALL[@]}" 2>/dev/null || true
    fi

    # Instalação dos pacotes AUR acumulados via yay
    if [ ${#AUR_TO_INSTALL[@]} -gt 0 ]; then
        if command -v yay >/dev/null 2>&1; then
            echo "   Instalando pacotes AUR via yay: ${AUR_TO_INSTALL[*]}"
            yay -S --needed --noconfirm "${AUR_TO_INSTALL[@]}" 2>/dev/null || true
        fi
    fi
fi
rm -f "$TMP_INSTALL_SEL"

# 6. Integridade do KDE Plasma e Configuração do Dolphin
echo ""
echo "-> [6/8] Garantindo integridade do KDE Plasma e tema do Dolphin..."
rm -f "$TARGET_HOME/.local/share/applications/org.kde.dolphin.desktop" 2>/dev/null || true

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$TARGET_HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    echo "Reconstruindo cache do KDE (kbuildsycoca6)..."
    kbuildsycoca6 --noincremental 2>/dev/null || true
fi

# Configurar Dolphin com o tema Noctalia apenas para consistência visual
if [ -f "$TARGET_HOME/.config/dolphinrc" ]; then
    if ! grep -q "ColorScheme=" "$TARGET_HOME/.config/dolphinrc"; then
        echo -e "\n[UiSettings]\nColorScheme=Noctalia" >> "$TARGET_HOME/.config/dolphinrc"
    fi
else
    mkdir -p "$TARGET_HOME/.config"
    echo -e "[UiSettings]\nColorScheme=Noctalia" > "$TARGET_HOME/.config/dolphinrc"
fi

# 7. Configurações de Rede: KDE Connect, AudioRelay e Firewall / GPU
echo ""
echo "-> [7/8] Configurando KDE Connect, AudioRelay e GPU (Early KMS)..."
if command -v ufw >/dev/null 2>&1; then
    echo "Liberando portas no firewall UFW..."
    sudo ufw allow 1714:1764/udp comment "KDE Connect" 2>/dev/null || true
    sudo ufw allow 1714:1764/tcp comment "KDE Connect" 2>/dev/null || true
    sudo ufw allow 59100:59200/tcp comment "AudioRelay" 2>/dev/null || true
    sudo ufw allow 59100:59200/udp comment "AudioRelay" 2>/dev/null || true
    sudo ufw reload 2>/dev/null || true
fi

systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable --now kdeconnect.service 2>/dev/null || true

# Configurar integração SSH no shell Fish
if [ -f "$TARGET_HOME/.config/fish/config.fish" ]; then
    if ! grep -q "alias ssh=\"kitten ssh\"" "$TARGET_HOME/.config/fish/config.fish"; then
        echo -e "\n# Fix Kitty SSH terminfo\nif test \"\$TERM\" = \"xterm-kitty\"\n    alias ssh=\"kitten ssh\"\nend" >> "$TARGET_HOME/.config/fish/config.fish"
    fi
fi

# Detecção de GPU e Prevenção de Flicker (Early KMS)
if [ -f /etc/mkinitcpio.conf ]; then
    GPU_MODULE=""
    if lspci -k 2>/dev/null | grep -i -E "(vga|3d|display)" | grep -i "amdgpu" >/dev/null; then
        GPU_MODULE="amdgpu"
        echo "GPU AMD detectada: módulo amdgpu."
    elif lspci -k 2>/dev/null | grep -i -E "(vga|3d|display)" | grep -i "nvidia" >/dev/null; then
        GPU_MODULE="nvidia nvidia_modeset nvidia_uvm nvidia_drm"
        echo "GPU NVIDIA detectada: módulos nvidia."
    elif lspci -k 2>/dev/null | grep -i -E "(vga|3d|display)" | grep -i "intel" >/dev/null; then
        GPU_MODULE="i915"
        echo "GPU Intel detectada: módulo i915."
    fi

    if [ -n "$GPU_MODULE" ]; then
        if ! grep -q "$GPU_MODULE" /etc/mkinitcpio.conf; then
            echo "Adicionando $GPU_MODULE ao /etc/mkinitcpio.conf..."
            sudo sed -i "s/^MODULES=(\(.*\))/MODULES=($GPU_MODULE \1)/" /etc/mkinitcpio.conf
            sudo sed -i 's/  / /g' /etc/mkinitcpio.conf
            echo "Reconstruindo initramfs com mkinitcpio..."
            sudo mkinitcpio -P
        else
            echo "Módulo de vídeo já configurado no mkinitcpio."
        fi
    fi
fi

# 8. Sincronização com o gerenciador de login
echo ""
echo "-> [8/8] Sincronizando com tela de login (SDDM / plasmalogin)..."
sudo mkdir -p /etc/sddm.conf.d 2>/dev/null || true
if [ -d /usr/lib/sddm/sddm.conf.d ]; then
    sudo cp -n /usr/lib/sddm/sddm.conf.d/* /etc/sddm.conf.d/ 2>/dev/null || true
fi

# Garantir permissões de execução nos scripts
chmod +x "$TARGET_HOME/.config/hypr/scripts/"*.sh 2>/dev/null || true
chmod +x "$TARGET_HOME/.local/bin/"* 2>/dev/null || true

echo ""
echo "=========================================================="
echo "  Instalação concluída com sucesso!"
echo "  Reinicie o sistema ou faça logout e selecione 'Hyprland (UWSM)'."
echo "=========================================================="
