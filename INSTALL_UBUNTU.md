# 🐧 Instalação no Ubuntu/Linux

Guia completo de instalação e configuração do Portal RFID no Ubuntu.

---

## 📋 Pré-requisitos

- **Ubuntu 20.04 LTS ou superior** (ou distribuições baseadas em Debian)
- **Conexão com a Internet** (para download de pacotes)
- **Permissões de sudo** (para instalação de pacotes do sistema)

---

## 🚀 Instalação Rápida

### 1. Download do Projeto

Se você recebeu o projeto em um arquivo ZIP:
```bash
cd ~/Downloads
unzip "Biamar UR4.zip" -d ~/
cd ~/Biamar\ UR4/
```

Ou clone do repositório (se aplicável):
```bash
cd ~
git clone <url-do-repositorio> "Biamar UR4"
cd "Biamar UR4"
```

### 2. Executar Instalação

```bash
bash install_ubuntu.sh
```

Este script irá:
- ✅ Atualizar repositórios do sistema
- ✅ Instalar Python 3 e pip
- ✅ Instalar Google Chrome
- ✅ Criar ambiente virtual Python
- ✅ Instalar todas as dependências
- ✅ Inicializar banco de dados
- ✅ Configurar permissões

**Tempo estimado**: 3-5 minutos

---

## ▶️ Executar o Sistema

### Iniciar Sistema Completo

```bash
bash start_ubuntu.sh
```

Este comando irá:
1. ✅ Iniciar API Backend (porta 8000)
2. ✅ Iniciar Leitor RFID (modo simulação ou real)
3. ✅ Abrir Chrome em **tela cheia** (modo kiosk) com o dashboard

O sistema rodará em **background**.

### Parar o Sistema

```bash
bash stop_ubuntu.sh
```

---

## 📊 Acessar o Dashboard

Após iniciar o sistema, o Chrome abrirá automaticamente em modo kiosk (tela cheia).

**Acesso manual**:
- Dashboard: `file://<caminho-completo>/frontend/index.html`
- API: http://localhost:8000
- Documentação API: http://localhost:8000/docs

**Sair do modo tela cheia**: 
- Pressione `F11` ou `Alt+F4` para fechar o Chrome

---

## 🔧 Configuração Personalizada

### Alterar IP do UR4

Edite o arquivo `scripts/ur4_rfid_reader.py`:
```python
UR4_IP = "192.168.1.100"  # Altere para o IP do seu UR4
```

### Alterar Porta da API

Edite o arquivo `backend/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Altere a porta
```

### Configurar Antenas RFID

Edite o arquivo `scripts/ur4_rfid_reader.py`:
```python
ANTENNA_1_REGISTER = 0  # Digital Input da Antena 1
ANTENNA_2_REGISTER = 1  # Digital Input da Antena 2
```

---

## 📝 Logs do Sistema

Os logs são salvos automaticamente em:

```bash
# Ver logs em tempo real
tail -f logs/api.log          # Log da API
tail -f logs/rfid.log         # Log do leitor RFID

# Ver últimas 50 linhas
tail -n 50 logs/api.log
```

**Localização dos logs**: `./logs/`

---

## 🔄 Inicialização Automática (Opcional)

Para que o sistema inicie automaticamente com o Ubuntu:

### Criar Serviço Systemd

1. Crie o arquivo de serviço:
```bash
sudo nano /etc/systemd/system/rfid-portal.service
```

2. Cole o conteúdo:
```ini
[Unit]
Description=Portal RFID Biamar UR4
After=network.target

[Service]
Type=forking
User=seu_usuario
WorkingDirectory=/home/seu_usuario/Biamar UR4
ExecStart=/bin/bash /home/seu_usuario/Biamar UR4/start_ubuntu.sh
ExecStop=/bin/bash /home/seu_usuario/Biamar UR4/stop_ubuntu.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Substitua** `seu_usuario` pelo seu nome de usuário do Ubuntu

4. Ative o serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rfid-portal.service
sudo systemctl start rfid-portal.service
```

5. Verificar status:
```bash
sudo systemctl status rfid-portal.service
```

### Comandos do Serviço

```bash
# Iniciar
sudo systemctl start rfid-portal

# Parar
sudo systemctl stop rfid-portal

# Reiniciar
sudo systemctl restart rfid-portal

# Ver logs
sudo journalctl -u rfid-portal -f
```

---

## 🖥️ Modo Kiosk (Tela Cheia)

O sistema abre automaticamente o Chrome em **modo kiosk** (tela cheia sem barras).

### Funcionalidades do Modo Kiosk

- ✅ Tela cheia automática
- ✅ Sem barra de endereço
- ✅ Sem botões de navegação
- ✅ Ideal para monitores dedicados
- ✅ Inicia automaticamente com o sistema

### Sair do Modo Kiosk

- **F11**: Sai da tela cheia
- **Alt+F4**: Fecha o Chrome
- Execute: `bash stop_ubuntu.sh`

### Abrir em Modo Normal (para testes)

```bash
# Abrir em janela normal
google-chrome "file://$(pwd)/frontend/index.html"
```

---

## 🛠️ Comandos Úteis

### Verificar Status dos Processos

```bash
# Ver processos do sistema
ps aux | grep -E "main.py|ur4_rfid_reader"

# Ver portas em uso
sudo netstat -tulpn | grep :8000
```

### Limpar Banco de Dados

```bash
rm -f database/rfid_portal.db
source venv/bin/activate
python3 -c "from backend.models import init_db; init_db()"
```

### Atualizar Dependências

```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## 🐛 Troubleshooting

### Erro: "API não respondeu"

```bash
# Verificar log da API
cat logs/api.log

# Testar API manualmente
curl http://localhost:8000

# Verificar se porta está em uso
sudo lsof -i :8000
```

### Erro: "Chrome não encontrado"

```bash
# Instalar Chrome manualmente
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

### Erro: "Ambiente virtual não encontrado"

```bash
# Recriar ambiente virtual
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Sistema não para corretamente

```bash
# Forçar parada de todos os processos
pkill -f "main.py"
pkill -f "ur4_rfid_reader"
pkill -f "chrome.*kiosk"
rm -f logs/system.pid
```

### Permissões negadas

```bash
# Adicionar permissões de execução
chmod +x *.sh
chmod +x scripts/*.py
```

---

## 📦 Desinstalação

```bash
# Parar o sistema
bash stop_ubuntu.sh

# Desabilitar serviço (se configurado)
sudo systemctl disable rfid-portal.service
sudo rm /etc/systemd/system/rfid-portal.service
sudo systemctl daemon-reload

# Remover diretório
cd ~
rm -rf "Biamar UR4"
```

---

## 🔐 Segurança

Para uso em produção:

1. **Firewall**: Configure para permitir apenas acesso local
```bash
sudo ufw allow from 127.0.0.1 to any port 8000
```

2. **HTTPS**: Configure certificado SSL (não incluído na POC)

3. **Autenticação**: Adicione autenticação à API (não incluído na POC)

---

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs em `./logs/`
2. Execute `bash stop_ubuntu.sh` e depois `bash start_ubuntu.sh`
3. Consulte a documentação em `README.md` e `GUIA_USO.md`

---

## ✅ Checklist Pós-Instalação

- [ ] Sistema instalado sem erros
- [ ] API responde em http://localhost:8000
- [ ] Dashboard abre no Chrome
- [ ] Leitor RFID em modo simulação funcionando
- [ ] Logs sendo gravados em `./logs/`
- [ ] Navegação entre Dashboard e Auditoria funciona
- [ ] Filtros de auditoria funcionam
- [ ] Exportação CSV funciona

---

**Sistema**: Portal RFID - Biamar UR4  
**Versão**: 1.0 POC  
**Plataforma**: Ubuntu 20.04+ / Debian-based Linux  
**Getel Soluções em Tecnologia LTDA**
