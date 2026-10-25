#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_USER="$(whoami)"
TARGET_HOME="$HOME"

echo "=========================================================="
echo "  Instalador Universal: CachyOS Hyprland + Noctalia Shell"
echo "  Destino: Usuário $TARGET_USER ($TARGET_HOME)"
echo "=========================================================="
echo ""

# 1. Verificar e instalar pacotes necessários
echo "-> [1/7] Verificando e instalando componentes do Hyprland e Noctalia..."
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
    )
    echo "Instalando pacotes base..."
    sudo pacman -S --needed --noconfirm "${PACKAGES[@]}"

    # Garantir audiorelay via AUR (yay/paru) se disponível
    if command -v yay >/dev/null 2>&1; then
        echo "Instalando audiorelay via yay..."
        yay -S --needed --noconfirm audiorelay 2>/dev/null || true
    elif command -v paru >/dev/null 2>&1; then
        echo "Instalando audiorelay via paru..."
        paru -S --needed --noconfirm audiorelay 2>/dev/null || true
    fi
fi

# 2. Implantação de Dotfiles
echo ""
echo "-> [2/7] Implantando dotfiles em $TARGET_HOME/.config..."
mkdir -p "$TARGET_HOME/.config"
cp -r "$SCRIPT_DIR/configs/"* "$TARGET_HOME/.config/"

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

# 3. Implantação de Ícones, Temas, Wallpaper e Estado do Noctalia
echo ""
echo "-> [3/7] Instalando cursores, esquemas de cores, wallpaper e estado do Noctalia..."
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

# 4. Integridade do KDE Plasma e Configuração do Dolphin
echo ""
echo "-> [4/7] Garantindo integridade do KDE Plasma e tema do Dolphin..."
# Remover qualquer substituição indesejada de desktop files que quebre a barra de tarefas do KDE
rm -f "$TARGET_HOME/.local/share/applications/org.kde.dolphin.desktop" 2>/dev/null || true

# Reconstruir cache de aplicativos e MIME para manter o KDE 100% responsivo
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

# 5. Configurações de Rede: KDE Connect, AudioRelay e Firewall
echo ""
echo "-> [5/7] Configurando KDE Connect e AudioRelay..."
if command -v ufw >/dev/null 2>&1; then
    echo "Liberando portas no firewall UFW..."
    # Portas KDE Connect
    sudo ufw allow 1714:1764/udp comment "KDE Connect" 2>/dev/null || true
    sudo ufw allow 1714:1764/tcp comment "KDE Connect" 2>/dev/null || true
    # Portas AudioRelay
    sudo ufw allow 59100:59200/tcp comment "AudioRelay" 2>/dev/null || true
    sudo ufw allow 59100:59200/udp comment "AudioRelay" 2>/dev/null || true
    sudo ufw reload 2>/dev/null || true
fi

# Ativar serviço em segundo plano do KDE Connect no systemd user
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable --now kdeconnect.service 2>/dev/null || true

# Configurar integração SSH no shell Fish
if [ -f "$TARGET_HOME/.config/fish/config.fish" ]; then
    if ! grep -q "alias ssh=\"kitten ssh\"" "$TARGET_HOME/.config/fish/config.fish"; then
        echo -e "\n# Fix Kitty SSH terminfo\nif test \"\$TERM\" = \"xterm-kitty\"\n    alias ssh=\"kitten ssh\"\nend" >> "$TARGET_HOME/.config/fish/config.fish"
    fi
fi

# 6. Detecção de GPU e Prevenção de Flicker (Early KMS)
echo ""
echo "-> [6/7] Detectando GPU para configurar Early KMS e eliminar piscadas de tela..."
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

# 7. Sincronização com o gerenciador de login
echo ""
echo "-> [7/7] Sincronizando com tela de login (SDDM / plasmalogin)..."
sudo mkdir -p /etc/sddm.conf.d 2>/dev/null || true
if [ -d /usr/lib/sddm/sddm.conf.d ]; then
    sudo cp -n /usr/lib/sddm/sddm.conf.d/* /etc/sddm.conf.d/ 2>/dev/null || true
fi

# Garantir permissões de execução nos scripts
chmod +x "$TARGET_HOME/.config/hypr/scripts/"*.sh 2>/dev/null || true

echo ""
echo "=========================================================="
echo "  Instalação concluída com sucesso!"
echo "  Reinicie o sistema ou faça logout e selecione 'Hyprland (UWSM)'."
echo "=========================================================="
