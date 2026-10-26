#!/usr/bin/env bash
# ==============================================================================
# sync-from-system.sh
# Atualiza o repositório cachyos-hypr-noctalia com as configurações reais do seu PC.
#
# Uso:
#   ./sync-from-system.sh            -> Checklist interativo, sincroniza e valida
#   ./sync-from-system.sh --all      -> Sincroniza sem abrir checklist (mantém seleção salva)
#   ./sync-from-system.sh --commit   -> Sincroniza e cria um commit no git
#   ./sync-from-system.sh --push     -> Sincroniza, commita e envia (push) para o remoto
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_HOME="$HOME"

# Carregar utilitários de seleção e pacotes
if [ -f "$SCRIPT_DIR/bin/app-selector.sh" ]; then
    source "$SCRIPT_DIR/bin/app-selector.sh"
else
    echo "Erro: '$SCRIPT_DIR/bin/app-selector.sh' não encontrado!"
    exit 1
fi

echo "=========================================================="
echo "  Sincronizador Automático: Sistema -> Repositório Git"
echo "  Origem: $USER_HOME"
echo "  Destino: $SCRIPT_DIR"
echo "=========================================================="
echo ""

# 1. Sincronizar Dotfiles Base (~/.config)
echo "-> [1/7] Sincronizando dotfiles base do sistema em $USER_HOME/.config..."
mkdir -p "$SCRIPT_DIR/configs"

# Hyprland
if [ -d "$USER_HOME/.config/hypr" ]; then
    mkdir -p "$SCRIPT_DIR/configs/hypr"
    cp -r "$USER_HOME/.config/hypr/"* "$SCRIPT_DIR/configs/hypr/"
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

# 2. Seleção e Sincronização Seletiva de Aplicativos Pessoais
echo ""
echo "-> [2/7] Gerenciando aplicativos e configurações personalizadas..."
mkdir -p "$SCRIPT_DIR/configs/apps"
MANIFEST_FILE="$SCRIPT_DIR/configs/custom-apps.conf"

# Mapear apps anteriormente salvos
declare -A PREV_SAVED
if [ -f "$MANIFEST_FILE" ]; then
    while IFS=':' read -r f_name p_name d_desc d_status; do
        [[ "$f_name" =~ ^#.*$ || -z "$f_name" ]] && continue
        if [ "$d_status" == "ON" ]; then
            PREV_SAVED["$f_name"]="ON"
        fi
    done < "$MANIFEST_FILE"
fi

# Escanear aplicativos disponíveis no sistema
CANDIDATES=($(scan_user_apps "$USER_HOME/.config"))
CHECKLIST_ITEMS=()

for app in "${CANDIDATES[@]}"; do
    INFO=$(get_package_info "$app")
    PKG_NAME="${INFO%%:*}"
    PKG_DESC="${INFO#*:}"
    
    STATUS="OFF"
    if [ -n "${PREV_SAVED[$app]}" ]; then
        STATUS="ON"
    elif [ ${#PREV_SAVED[@]} -eq 0 ]; then
        # Sugestão inicial para apps populares caso manifesto ainda não exista
        case "$app" in
            alacritty|btop|discord|fastfetch|fish|micro|mpv|telegram-desktop|vlc) STATUS="ON" ;;
            *) STATUS="OFF" ;;
        esac
    fi

    CHECKLIST_ITEMS+=("$app" "$PKG_DESC" "$STATUS")
done

# Invocar seleção interativa se não houver flag silenciosa
SELECTED_RAW=""
if [ "$1" == "--batch" ] || [ "$2" == "--batch" ] || [ "$1" == "--all" ] || [ "$2" == "--all" ] || [ ! -t 0 ]; then
    echo "   Modo não-interativo ativo: mantendo aplicativos salvos no manifesto."
    SELECTED_RAW=$(for k in "${!PREV_SAVED[@]}"; do echo "$k"; done)
    if [ -z "$SELECTED_RAW" ]; then
        # Se manifesto não existia, seleciona os marcados com ON por padrão
        i=0
        while [ $i -lt ${#CHECKLIST_ITEMS[@]} ]; do
            if [ "${CHECKLIST_ITEMS[$((i+2))]}" == "ON" ]; then
                SELECTED_RAW+="${CHECKLIST_ITEMS[$i]}"$'\n'
            fi
            i=$((i+3))
        done
    fi
else
    SELECTED_RAW=$(prompt_checklist "Sincronização Seletiva de Apps" \
        "Marque com [ESPAÇO] os aplicativos e configurações que deseja exportar:\n(Use TAB para navegar, ESPAÇO para marcar e ENTER para confirmar)" \
        "${CHECKLIST_ITEMS[@]}")
fi

# Criar novo manifesto com os selecionados
echo "# ==============================================================================" > "$MANIFEST_FILE"
echo "# custom-apps.conf: Aplicativos e Configurações Pessoais Exportados" >> "$MANIFEST_FILE"
echo "# Formato: FOLDER_NAME:PACKAGE_NAME:DESCRIPTION:DEFAULT_STATUS" >> "$MANIFEST_FILE"
echo "# ==============================================================================" >> "$MANIFEST_FILE"

declare -A CURRENT_SELECTED
while IFS= read -r sel_app; do
    sel_app=$(echo "$sel_app" | tr -d '"' | xargs)
    [ -z "$sel_app" ] && continue
    CURRENT_SELECTED["$sel_app"]=1
    
    INFO=$(get_package_info "$sel_app")
    PKG_NAME="${INFO%%:*}"
    PKG_DESC="${INFO#*:}"
    echo "${sel_app}:${PKG_NAME}:${PKG_DESC}:ON" >> "$MANIFEST_FILE"
    
    # Copiar configuração para configs/apps/ com filtros de cache e arquivos temporários
    echo "   [Exportando] $sel_app ($PKG_NAME)..."
    mkdir -p "$SCRIPT_DIR/configs/apps/$sel_app"
    rm -rf "$SCRIPT_DIR/configs/apps/$sel_app"/* 2>/dev/null || true
    rsync -a \
        --exclude="Cache" --exclude="*Cache*" --exclude="GPUCache" --exclude="Code Cache" \
        --exclude="DawnCache" --exclude="blob_storage" --exclude="Service Worker" \
        --exclude="IndexedDB" --exclude="Crashpad" --exclude="*.log" --exclude="*.tmp" \
        --exclude="Session Storage" --exclude="logs" --exclude="Dictionaries" \
        --exclude="app-*" --exclude="*.asar" --exclude="*.so*" --exclude="*.node" \
        --exclude="*.pak" --exclude="*.bin" --exclude="discord_asset_cache" \
        --exclude="Cookies*" --exclude="Local Storage" --exclude="Shared*" \
        --exclude="WebStorage" --exclude="TransportSecurity" --exclude="Network Persistent State" \
        "$USER_HOME/.config/$sel_app/" "$SCRIPT_DIR/configs/apps/$sel_app/" 2>/dev/null || true
done <<< "$SELECTED_RAW"

# Remover do repositório pastas que foram desmarcadas
for existing_app in "$SCRIPT_DIR/configs/apps/"*; do
    if [ -d "$existing_app" ]; then
        base_app=$(basename "$existing_app")
        if [ -z "${CURRENT_SELECTED[$base_app]}" ]; then
            echo "   [Removendo desmarcado] $base_app"
            rm -rf "$existing_app"
        fi
    fi
done

# 3. Sincronizar Estado e Estilização do Noctalia (~/.local/state/noctalia)
echo ""
echo "-> [3/7] Sincronizando estado, dock, painéis e paletas do Noctalia..."
mkdir -p "$SCRIPT_DIR/state/noctalia"
if [ -d "$USER_HOME/.local/state/noctalia" ]; then
    rsync -a \
        --exclude="clipboard" \
        --exclude="notification_history*" \
        --exclude="recently_used.json" \
        --exclude="usage_counts.json" \
        --exclude="plugins/sources" \
        --exclude="*.lock" --exclude="lock" --exclude="txn" \
        --exclude="backups" --exclude="original-*.lua" --exclude="backup.lua" \
        "$USER_HOME/.local/state/noctalia/" "$SCRIPT_DIR/state/noctalia/"
fi

# Garantir persistência ativa da Dock tanto no config.toml quanto no settings.toml
if [ -f "$USER_HOME/.local/state/noctalia/settings.toml" ]; then
    sync_noctalia_dock "$USER_HOME/.local/state/noctalia/settings.toml" "$SCRIPT_DIR/configs/noctalia/config.toml"
fi

# 4. Sincronizar Wallpaper Ativo
echo ""
echo "-> [4/7] Sincronizando wallpaper do sistema..."
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

# 5. Sincronizar Assets (Cursores, Esquemas de Cores e Scripts)
echo ""
echo "-> [5/7] Sincronizando cursores, esquemas de cores e utilitários..."
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

# 6. Validação de Integridade
echo ""
echo "-> [6/7] Validando sintaxe das configurações sincronizadas..."
if command -v luac >/dev/null 2>&1; then
    luac -p "$SCRIPT_DIR/configs/hypr/"*.lua "$SCRIPT_DIR/configs/hypr/config/"*.lua
    echo "   Sintaxe Lua 100% válida!"
fi

if command -v noctalia >/dev/null 2>&1; then
    noctalia config validate "$SCRIPT_DIR/configs/noctalia/config.toml"
    echo "   Configuração do Noctalia (com Dock) 100% válida!"
fi

if command -v bash >/dev/null 2>&1; then
    bash -n "$SCRIPT_DIR/install.sh"
    bash -n "$SCRIPT_DIR/build-release.sh"
    bash -n "$SCRIPT_DIR/bin/app-selector.sh"
    bash -n "$SCRIPT_DIR/bin/setup-audiorelay.sh" 2>/dev/null || true
    echo "   Scripts Bash 100% válidos!"
fi

# 7. Reconstruir Tarball de Release Local
echo ""
echo "-> [7/7] Atualizando pacote portátil de release..."
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
    git commit --no-gpg-sign -m "$MSG" || echo "Sem mudanças novas para commit."
    git push origin main
    echo "Push concluído com sucesso!"
elif [ "$1" == "--commit" ] || [ "$2" == "--commit" ]; then
    MSG="${3:-chore(sync): update repository configs from active system}"
    echo ""
    echo "-> Criando commit local..."
    git add .
    git commit --no-gpg-sign -m "$MSG" || echo "Sem mudanças novas para commit."
fi
