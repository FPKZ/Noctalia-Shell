#!/usr/bin/env bash
# Script para gerar o tarball de release a partir do repositório
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="$SCRIPT_DIR/noctalia-cachyos-portable.tar.gz"

echo "-> Gerando pacote portátil para Release em $OUTPUT_FILE..."
cd "$SCRIPT_DIR/.."
tar --exclude=".git" --exclude="*.tar.gz" -czf "$OUTPUT_FILE" "cachyos-hypr-noctalia"

echo "Pacote gerado com sucesso: $(ls -lh "$OUTPUT_FILE" | awk '{print $5, $9}')"
