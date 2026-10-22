#!/usr/bin/env bash
# Script para gerar o tarball de release a partir do repositório
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$SCRIPT_DIR/noctalia-cachyos-portable.tar.gz"

echo "-> Gerando pacote portátil para Release em $OUTPUT_FILE..."
TEMP_ARCHIVE=$(mktemp /tmp/noctalia-cachyos-portable.XXXXXX.tar.gz)
cd "$SCRIPT_DIR/.."
tar --exclude=".git" --exclude="*.tar.gz" -czf "$TEMP_ARCHIVE" "cachyos-hypr-noctalia"
mv "$TEMP_ARCHIVE" "$OUTPUT_FILE"

echo "Pacote gerado com sucesso: $(ls -lh "$OUTPUT_FILE" | awk '{print $5, $9}')"
