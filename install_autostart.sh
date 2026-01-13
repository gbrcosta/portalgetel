#!/bin/bash
# Script para configurar o Portal RFID para iniciar automaticamente

echo "============================================"
echo "Portal RFID - Configuração de Auto-Início"
echo "============================================"
echo

# 1. Copiar arquivo de serviço
echo "1️⃣  Instalando serviço systemd..."
sudo cp portal-rfid.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/portal-rfid.service

# 2. Recarregar systemd
echo "2️⃣  Recarregando systemd..."
sudo systemctl daemon-reload

# 3. Habilitar serviço
echo "3️⃣  Habilitando serviço para iniciar com o sistema..."
sudo systemctl enable portal-rfid.service

# 4. Configurar autologin
echo "4️⃣  Configurando login automático..."
if [ -f /etc/gdm3/custom.conf ]; then
    # Para GDM (Ubuntu/GNOME)
    sudo bash -c "cat > /etc/gdm3/custom.conf << 'EOF'
[daemon]
AutomaticLoginEnable=true
AutomaticLogin=getel

[security]

[xdmcp]

[chooser]

[debug]
EOF"
    echo "   ✓ Autologin configurado para GDM"
elif [ -f /etc/lightdm/lightdm.conf ]; then
    # Para LightDM
    sudo bash -c "cat >> /etc/lightdm/lightdm.conf << 'EOF'

[Seat:*]
autologin-user=getel
autologin-user-timeout=0
EOF"
    echo "   ✓ Autologin configurado para LightDM"
else
    echo "   ⚠️  Display manager não reconhecido, configure manualmente"
fi

# 5. Desabilitar bloqueio de tela
echo "5️⃣  Desabilitando bloqueio de tela..."
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
gsettings set org.gnome.desktop.session idle-delay 0
echo "   ✓ Bloqueio de tela desabilitado"

# 5.1 Configurar chaveiro para não solicitar senha
echo "5.1 Configurando chaveiro..."
if command -v gnome-keyring-daemon &> /dev/null; then
    # Criar diretório do chaveiro se não existir
    mkdir -p ~/.local/share/keyrings
    # Nota: Para evitar pedido de senha, use Chrome com --password-store=basic
    echo "   ✓ Chaveiro será ignorado pelo navegador"
fi

# 6. Configurar navegador para iniciar automaticamente
echo "6️⃣  Configurando navegador em modo kiosk..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/portal-rfid-browser.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Portal RFID Browser
Exec=/bin/bash /home/getel/Documentos/portalgetel/start_kiosk.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=20
Comment=Inicia o dashboard do Portal RFID em modo kiosk
EOF
echo "   ✓ Navegador configurado para iniciar automaticamente"

echo
echo "============================================"
echo "✅ Configuração concluída!"
echo "============================================"
echo
echo "O que foi feito:"
echo "  ✓ Serviço systemd instalado"
echo "  ✓ Auto-início habilitado"
echo "  ✓ Login automático configurado"
echo "  ✓ Bloqueio de tela desabilitado"
echo "  ✓ Navegador configurado em modo kiosk"
echo
echo "Comandos úteis:"
echo "  sudo systemctl status portal-rfid   - Ver status"
echo "  sudo systemctl start portal-rfid    - Iniciar manualmente"
echo "  sudo systemctl stop portal-rfid     - Parar manualmente"
echo "  sudo systemctl restart portal-rfid  - Reiniciar"
echo "  sudo systemctl disable portal-rfid  - Desabilitar auto-início"
echo
echo "⚠️  REINICIE o computador para aplicar todas as mudanças"
echo "============================================"
