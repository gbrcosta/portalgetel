#!/bin/bash

# ============================================
# Portal RFID - Biamar UR4
# Script para abrir apenas o Dashboard em tela cheia
# (Assume que API e RFID já estão rodando)
# ============================================

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Caminho completo do arquivo HTML
DASHBOARD_PATH="file://$SCRIPT_DIR/frontend/index.html"

echo "============================================"
echo "Portal RFID - Biamar UR4"
echo "Abrindo Dashboard em Tela Cheia"
echo "============================================"
echo ""

# Verificar se API está rodando
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "⚠️  Aviso: API não está respondendo!"
    echo "Certifique-se de que o sistema está rodando:"
    echo "  bash start_ubuntu.sh"
    echo ""
fi

echo "🌐 Abrindo Chrome em modo kiosk..."
echo ""

# Tentar abrir Chrome em tela cheia
if command -v google-chrome &> /dev/null; then
    google-chrome --kiosk --app="$DASHBOARD_PATH" &
    echo "✓ Chrome aberto em tela cheia"
elif command -v chromium-browser &> /dev/null; then
    chromium-browser --kiosk --app="$DASHBOARD_PATH" &
    echo "✓ Chromium aberto em tela cheia"
else
    echo "❌ Chrome não encontrado!"
    echo "Abra manualmente: $DASHBOARD_PATH"
    exit 1
fi

echo ""
echo "Pressione F11 ou Alt+F4 para sair da tela cheia"
echo ""
