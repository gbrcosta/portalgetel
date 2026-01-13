#!/bin/bash
# Script para iniciar o navegador em modo kiosk

echo "Aguardando serviço Portal RFID iniciar..."
sleep 15

echo "Iniciando navegador em modo kiosk..."

# Tentar Chrome primeiro, depois Chromium, depois Firefox
if command -v google-chrome &> /dev/null; then
    echo "Usando Google Chrome"
    google-chrome --kiosk http://localhost:8000 \
        --start-fullscreen \
        --disable-infobars \
        --noerrdialogs \
        --disable-session-crashed-bubble \
        --disable-restore-session-state \
        --no-first-run \
        --disable-popup-blocking \
        --password-store=basic \
        --use-mock-keychain &
elif command -v chromium-browser &> /dev/null; then
    echo "Usando Chromium"
    chromium-browser --kiosk http://localhost:8000 \
        --start-fullscreen \
        --disable-infobars \
        --no-first-run \
        --disable-popup-blocking \
        --password-store=basic \
        --use-mock-keychain &
elif command -v firefox &> /dev/null; then
    echo "Usando Firefox"
    firefox --kiosk http://localhost:8000 &
else
    echo "Nenhum navegador suportado encontrado!"
    exit 1
fi

echo "Navegador iniciado em modo kiosk"
