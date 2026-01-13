# Portal RFID - Configuração de Auto-Início

## ✅ O que foi configurado:

### 1. Serviço Systemd
- **Arquivo**: `/etc/systemd/system/portal-rfid.service`
- **Status**: Habilitado para iniciar automaticamente
- O serviço inicia a API e o leitor RFID em segundo plano

### 2. Login Automático
- Configurado no GDM (gerenciador de login)
- Usuário `getel` faz login automaticamente ao ligar o computador
- Não é necessário digitar senha
- Bloqueio de tela desabilitado para evitar pedir senha após login

### 3. Navegador em Modo Kiosk
- **Arquivo**: `~/.config/autostart/portal-rfid-browser.desktop`
- Abre o navegador automaticamente em tela cheia após 20 segundos
- URL: `http://localhost:8000`
- Tenta Chrome, depois Chromium, depois Firefox

## 📋 Comandos Úteis

### Gerenciar o serviço:
```bash
sudo systemctl status portal-rfid    # Ver status
sudo systemctl start portal-rfid     # Iniciar
sudo systemctl stop portal-rfid      # Parar
sudo systemctl restart portal-rfid   # Reiniciar
sudo systemctl disable portal-rfid   # Desabilitar auto-início
sudo systemctl enable portal-rfid    # Habilitar auto-início
```

### Ver logs:
```bash
sudo journalctl -u portal-rfid -f    # Logs em tempo real
sudo journalctl -u portal-rfid -n 50 # Últimas 50 linhas
```

### Testar kiosk manualmente:
```bash
bash /home/getel/Documentos/portalgetel/start_kiosk.sh
```

## 🔧 Sair do Modo Kiosk

Para sair do modo kiosk e voltar ao desktop:
- **F11** - Sair de tela cheia
- **Alt + F4** - Fechar navegador
- **Ctrl + Alt + T** - Abrir terminal

## 🔒 Desabilitar Bloqueio de Tela (Já configurado)

O script de instalação já desabilita automaticamente o bloqueio de tela. Se precisar fazer manualmente:

```bash
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
gsettings set org.gnome.desktop.session idle-delay 0
```

## 🚀 Quando o computador reiniciar:

1. ✅ Sistema liga e faz login automaticamente (SEM pedir senha)
2. ✅ Serviço Portal RFID inicia em segundo plano
3. ✅ Após ~20 segundos, navegador abre em modo kiosk
4. ✅ Dashboard do Portal RFID aparece em tela cheia
5. ✅ Leitor RFID começa a funcionar automaticamente
6. ✅ Tela NUNCA bloqueia ou pede senha

## 📁 Arquivos de Configuração

- `/etc/systemd/system/portal-rfid.service` - Serviço do sistema
- `/etc/gdm3/custom.conf` - Configuração de autologin
- `~/.config/autostart/portal-rfid-browser.desktop` - Autostart do navegador
- `/home/getel/Documentos/portalgetel/start_service.sh` - Script de início
- `/home/getel/Documentos/portalgetel/start_kiosk.sh` - Script do kiosk

## ⚠️ Importante

Para aplicar todas as configurações, **REINICIE o computador**:
```bash
sudo reboot
```

Após reiniciar, o sistema estará 100% automático!
