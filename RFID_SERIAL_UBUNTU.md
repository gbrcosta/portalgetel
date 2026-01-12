# Portal RFID Biamar - Conexão Serial Ubuntu

## 📋 Requisitos

### Hardware
- Leitor RFID Chainway UR4
- Cabo RS232 para USB
- Computador com Ubuntu/Debian

### Software
- Ubuntu 18.04+ ou Debian 10+
- Python 3.6+
- pyserial

## 🔧 Configuração Inicial

### 1. Verificar Porta Serial

```bash
# Verificar se o UR4 está conectado
ls -la /dev/ttyUSB*

# Exemplo de saída:
# crw-rw---- 1 root dialout 188, 0 Jan 12 10:30 /dev/ttyUSB0
```

### 2. Adicionar Usuário ao Grupo dialout

```bash
# Adicionar seu usuário ao grupo dialout (necessário para acessar portas seriais)
sudo usermod -a -G dialout $USER

# IMPORTANTE: Faça logout e login novamente para aplicar as permissões
```

### 3. Instalar Dependências

```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 🚀 Executar o Sistema

### Modo Simples (Terminal)

```bash
# Executar script de inicialização
bash start_rfid_serial.sh

# OU executar diretamente
source .venv/bin/activate
python3 scripts/ur4_rfid_serial.py
```

### Modo Serviço (systemd)

Para rodar automaticamente como serviço do sistema:

#### 1. Criar arquivo de serviço

```bash
sudo nano /etc/systemd/system/biamar-rfid.service
```

#### 2. Adicionar conteúdo:

```ini
[Unit]
Description=Biamar Portal RFID (Serial)
After=network.target

[Service]
Type=simple
User=seu-usuario
Group=seu-usuario
WorkingDirectory=/caminho/para/Biamar UR4
Environment=PATH=/caminho/para/Biamar UR4/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/caminho/para/Biamar UR4/.venv/bin/python scripts/ur4_rfid_serial.py
Restart=always
RestartSec=10

# Segurança
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**⚠️ IMPORTANTE:** Substitua:
- `seu-usuario` pelo seu nome de usuário
- `/caminho/para/Biamar UR4` pelo caminho completo do projeto

#### 3. Habilitar e iniciar o serviço

```bash
# Recarregar configurações do systemd
sudo systemctl daemon-reload

# Habilitar para iniciar automaticamente
sudo systemctl enable biamar-rfid

# Iniciar o serviço
sudo systemctl start biamar-rfid

# Verificar status
sudo systemctl status biamar-rfid

# Ver logs em tempo real
sudo journalctl -u biamar-rfid -f
```

## 📊 Monitoramento

### Ver Logs

```bash
# Logs em tempo real
sudo journalctl -u biamar-rfid -f

# Últimas 50 linhas
sudo journalctl -u biamar-rfid -n 50

# Logs da última hora
sudo journalctl -u biamar-rfid --since "1 hour ago"

# Apenas erros
sudo journalctl -u biamar-rfid -p err
```

### Comandos do Serviço

```bash
# Iniciar
sudo systemctl start biamar-rfid

# Parar
sudo systemctl stop biamar-rfid

# Reiniciar
sudo systemctl restart biamar-rfid

# Status
sudo systemctl status biamar-rfid

# Desabilitar inicialização automática
sudo systemctl disable biamar-rfid
```

## 🔍 Solução de Problemas

### Porta não encontrada

```bash
# Verificar portas USB
ls -la /dev/ttyUSB*

# Verificar dispositivos USB conectados
lsusb

# Ver logs do kernel
dmesg | grep tty
```

### Sem permissão

```bash
# Verificar grupos do usuário
groups $USER

# Deve incluir 'dialout'
# Se não incluir, adicione:
sudo usermod -a -G dialout $USER

# IMPORTANTE: Faça logout e login
```

### Serviço não inicia

```bash
# Ver logs de erro
sudo journalctl -u biamar-rfid -p err -n 50

# Testar manualmente
cd "/caminho/para/Biamar UR4"
source .venv/bin/activate
python3 scripts/ur4_rfid_serial.py
```

### API não responde

```bash
# Verificar se a API está rodando
curl http://localhost:8000/api/rfid/event

# Verificar logs da API
sudo journalctl -u biamar-api -f
```

## ⚙️ Configurações

### Alterar Porta Serial

Edite o arquivo `scripts/ur4_rfid_serial.py`:

```python
PORTA_SERIAL = '/dev/ttyUSB0'  # Altere aqui
```

Ou configure via variável de ambiente:

```bash
export PORTA_SERIAL='/dev/ttyUSB1'
python3 scripts/ur4_rfid_serial.py
```

### Alterar Timeout de Duplicatas

Edite o arquivo `scripts/ur4_rfid_serial.py`:

```python
TIMEOUT_TAG = 300  # 5 minutos (em segundos)
```

### Alterar URL da API

Edite o arquivo `config.py`:

```python
API_HOST = "localhost"
API_PORT = 8000
```

## 📝 Diferenças entre Conexões

### Conexão Serial (ur4_rfid_serial.py) - **RECOMENDADO PARA UBUNTU**
- ✅ Conexão direta via USB/RS232
- ✅ Mais estável e confiável
- ✅ Menor latência
- ✅ Não depende de rede
- ✅ Funciona offline
- ❌ Requer cabo USB conectado

### Conexão Socket (ur4_rfid_reader.py)
- ✅ Conexão via rede TCP/IP
- ✅ Funciona remotamente
- ❌ Depende de configuração de rede do UR4
- ❌ Maior latência
- ❌ Pode ter problemas de conexão

## 🔗 Referências

Este script é baseado no projeto da Getel:
- https://github.com/Getel-Tecnologia/getel-portalrfid

Documentação do Chainway UR4:
- Comandos baseados no "UHF Application.pdf" do UR4
- Baudrate padrão: 115200
- Comunicação: RS232/USB

## 📞 Suporte

Em caso de problemas:

1. Verifique a conexão física do cabo USB
2. Confirme permissões do grupo dialout
3. Veja os logs: `sudo journalctl -u biamar-rfid -n 100`
4. Teste manualmente o script

---

**Desenvolvido para Biamar - Linha de Produção**

Baseado no sistema Portal RFID da Getel Tecnologia
