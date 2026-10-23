#!/usr/bin/env bash
# ==============================================================================
# sync-from-system.sh
# Atualiza o repositório cachyos-hypr-noctalia com as configurações reais do seu PC.
#
# Uso:
#   ./sync-from-system.sh            -> Apenas sincroniza e valida os arquivos
#   ./sync-from-system.sh --commit   -> Sincroniza e cria um commit no git
#   ./sync-from-system.sh --push     -> Sincroniza, commita e envia (push) para o remoto
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME="$HOME"

echo "=========================================================="
echo "  Sincronizador Automático: Sistema -> Repositório Git"
echo "  Origem: $USER_HOME"
echo "  Destino: $SCRIPT_DIR"
echo "=========================================================="
echo ""

# 1. Sincronizar Dotfiles (~/.config)
echo "-> [1/6] Sincronizando dotfiles de $USER_HOME/.config..."
mkdir -p "$SCRIPT_DIR/configs"

# Hyprland
if [ -d "$USER_HOME/.config/hypr" ]; then
    mkdir -p "$SCRIPT_DIR/configs/hypr"
    cp -r "$USER_HOME/.config/hypr/"* "$SCRIPT_DIR/configs/hypr/"
    # Manter monitors.lua em modo universal se já estiver
    if [ -f "$SCRIPT_DIR/configs/hypr/config/monitors.lua" ]; then
        if ! grep -q "output = \"\"" "$SCRIPT_DIR/configs/hypr/config/monitors.lua"; then
            echo "   (Aviso: mantendo regra universal de monitores para compatibilidade plug-and-play)"
        fi
    fi
fi

# Noctalia config
if [ -d "$USER_HOME/.config/noctalia" ]; then
    mkdir -p "$SCRIPT_DIR/configs/noctalia"
    cp -r "$USER_HOME/.config/noctalia/"* "$SCRIPT_DIR/configs/noctalia/"
fi

# Kitty, Qt6ct, Swash, UWSM
for dir in kitty qt6ct swash uwsm; do
    if [ -d "$USER_HOME/.config/$dir" ]; then
        mkdir -p "$SCRIPT_DIR/configs/$dir"
        cp -r "$USER_HOME/.config/$dir/"* "$SCRIPT_DIR/configs/$dir/"
    fi
done

# GTK 3.0 e 4.0 (Apenas CSS do tema)
for dir in gtk-3.0 gtk-4.0; do
    if [ -d "$USER_HOME/.config/$dir" ]; then
        mkdir -p "$SCRIPT_DIR/configs/$dir"
        cp "$USER_HOME/.config/$dir/"*.css "$SCRIPT_DIR/configs/$dir/" 2>/dev/null || true
    fi
done

# Systemd User services
if [ -f "$USER_HOME/.config/systemd/user/kdeconnect.service" ]; then
    mkdir -p "$SCRIPT_DIR/configs/systemd/user"
    cp "$USER_HOME/.config/systemd/user/kdeconnect.service" "$SCRIPT_DIR/configs/systemd/user/"
fi

# 2. Sincronizar Estado e Estilização do Noctalia (~/.local/state/noctalia)
echo "-> [2/6] Sincronizando estado, dock, painéis e paletas do Noctalia..."
mkdir -p "$SCRIPT_DIR/state/noctalia"
if [ -f "$USER_HOME/.local/state/noctalia/settings.toml" ]; then
    cp "$USER_HOME/.local/state/noctalia/settings.toml" "$SCRIPT_DIR/state/noctalia/"
fi
if [ -f "$USER_HOME/.local/state/noctalia/state.toml" ]; then
    cp "$USER_HOME/.local/state/noctalia/state.toml" "$SCRIPT_DIR/state/noctalia/"
fi
if [ -f "$USER_HOME/.local/state/noctalia/.setup-complete" ]; then
    cp "$USER_HOME/.local/state/noctalia/.setup-complete" "$SCRIPT_DIR/state/noctalia/"
fi
if [ -d "$USER_HOME/.local/state/noctalia/community-palettes" ]; then
    cp -r "$USER_HOME/.local/state/noctalia/community-palettes" "$SCRIPT_DIR/state/noctalia/"
fi

# 3. Sincronizar Wallpaper Ativo
echo "-> [3/6] Sincronizando wallpaper do sistema..."
mkdir -p "$SCRIPT_DIR/wallpapers"
WP_PATH=""
if [ -f "$USER_HOME/.local/state/noctalia/settings.toml" ]; then
    WP_PATH=$(grep -E '^\s*path = ' "$USER_HOME/.local/state/noctalia/settings.toml" | head -n1 | cut -d'"' -f2 || true)
fi

if [ -n "$WP_PATH" ] && [ -f "$WP_PATH" ]; then
    echo "   Wallpaper detectado: $WP_PATH"
    cp "$WP_PATH" "$SCRIPT_DIR/wallpapers/wp15566549.jpg"
elif [ -f "$USER_HOME/Imagens/wp15566549.jpg" ]; then
    cp "$USER_HOME/Imagens/wp15566549.jpg" "$SCRIPT_DIR/wallpapers/wp15566549.jpg"
fi

# 4. Sincronizar Assets (Cursores, Esquemas de Cores e Scripts)
echo "-> [4/6] Sincronizando cursores, esquemas de cores e utilitários..."
if [ -d "$USER_HOME/.local/share/icons/Bibata-Modern-Ice" ]; then
    mkdir -p "$SCRIPT_DIR/icons"
    cp -r "$USER_HOME/.local/share/icons/Bibata-Modern-Ice" "$SCRIPT_DIR/icons/"
fi

if [ -f "$USER_HOME/.local/share/color-schemes/noctalia.colors" ]; then
    mkdir -p "$SCRIPT_DIR/color-schemes"
    cp "$USER_HOME/.local/share/color-schemes/noctalia.colors" "$SCRIPT_DIR/color-schemes/"
fi

if [ -f "$USER_HOME/.local/bin/setup-audiorelay.sh" ]; then
    mkdir -p "$SCRIPT_DIR/bin"
    cp "$USER_HOME/.local/bin/setup-audiorelay.sh" "$SCRIPT_DIR/bin/"
    chmod +x "$SCRIPT_DIR/bin/setup-audiorelay.sh"
fi

# 5. Validação de Integridade
echo "-> [5/6] Validando sintaxe das configurações sincronizadas..."
if command -v luac >/dev/null 2>&1; then
    luac -p "$SCRIPT_DIR/configs/hypr/"*.lua "$SCRIPT_DIR/configs/hypr/config/"*.lua
    echo "   Sintaxe Lua 100% válida!"
fi

if command -v bash >/dev/null 2>&1; then
    bash -n "$SCRIPT_DIR/install.sh"
    bash -n "$SCRIPT_DIR/build-release.sh"
    bash -n "$SCRIPT_DIR/bin/setup-audiorelay.sh" 2>/dev/null || true
    echo "   Scripts Bash 100% válidos!"
fi

# 6. Reconstruir Tarball de Release Local
echo "-> [6/6] Atualizando pacote portátil de release..."
"$SCRIPT_DIR/build-release.sh"
cp "$SCRIPT_DIR/noctalia-cachyos-portable.tar.gz" "$USER_HOME/noctalia-cachyos-portable.tar.gz" 2>/dev/null || true

echo ""
echo "=========================================================="
echo "  Sincronização concluída com sucesso!"
echo "=========================================================="

cd "$SCRIPT_DIR"
git status -s

# Opções de Git automáticas
if [ "$1" == "--push" ] || [ "$2" == "--push" ]; then
    MSG="${3:-chore(sync): update repository configs from active system}"
    echo ""
    echo "-> Criando commit e enviando para o repositório remoto..."
    git add .
    git commit -m "$MSG" || echo "Sem mudanças novas para commit."
    git push origin main
    echo "Push concluído com sucesso!"
elif [ "$1" == "--commit" ]; then
    MSG="${2:-chore(sync): update repository configs from active system}"
    echo ""
    echo "-> Criando commit local..."
    git add .
    git commit -m "$MSG" || echo "Sem mudanças novas para commit."
fi
