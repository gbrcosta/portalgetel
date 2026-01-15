# UR4 RFID Reader Library

Biblioteca Python para leitura de tags RFID com leitor UR4 via comunicação serial RS232/USB.

## 📋 Características

- ✅ **Multi-plataforma**: Windows e Linux
- ✅ **Detecção automática** de porta serial
- ✅ **API simples e intuitiva**
- ✅ **Callbacks customizáveis**
- ✅ **Leitura contínua ou única**
- ✅ **Anti-spam** configurável
- ✅ **Modo debug** para troubleshooting

## 🚀 Instalação

```bash
pip install pyserial
```

## 💻 Uso Básico

### Como CLI (linha de comando)

```bash
python ur4_reader.py
```

### Como Biblioteca

```python
from ur4_reader import UR4Reader

# Criar leitor
reader = UR4Reader(port='COM4')  # ou '/dev/ttyUSB0' no Linux

# Conectar
if reader.connect():
    # Ler tags continuamente (imprime no console)
    reader.read_continuous()
    
    # Desconectar
    reader.disconnect()
```

## 📚 Exemplos

### 1. Callback Customizado

```python
from ur4_reader import UR4Reader, detect_serial_port

def minha_funcao(epc, antenna, rssi):
    print(f"Tag: {epc} | Antena: {antenna} | RSSI: {rssi} dBm")

port = detect_serial_port()  # Detecta automaticamente
reader = UR4Reader(port=port)

if reader.connect():
    reader.read_continuous(callback=minha_funcao, print_output=False)
    reader.disconnect()
```

### 2. Leitura Única

```python
reader = UR4Reader(port='COM4')

if reader.connect():
    # Aguarda até 10 segundos por uma tag
    tag = reader.read_single(timeout=10.0)
    
    if tag:
        print(f"EPC: {tag['epc']}")
        print(f"Antena: {tag['antenna']}")
        print(f"RSSI: {tag['rssi']} dBm")
    
    reader.disconnect()
```

### 3. Enviar para API

```python
import requests

def enviar_para_api(epc, antenna, rssi):
    payload = {'tag_id': epc, 'antenna': antenna, 'rssi': rssi}
    requests.post('http://localhost:8000/api/rfid', json=payload)

reader = UR4Reader(port='COM4')
if reader.connect():
    reader.read_continuous(
        callback=enviar_para_api,
        anti_spam_delay=5.0,  # 5s entre leituras da mesma tag
        print_output=True
    )
    reader.disconnect()
```

### 4. Filtrar por Antena

```python
def processar_tag(epc, antenna, rssi):
    if antenna == 1:
        print(f"Entrada: {epc}")
    elif antenna == 2:
        print(f"Saída: {epc}")

reader = UR4Reader(port='COM4')
if reader.connect():
    reader.read_continuous(callback=processar_tag)
    reader.disconnect()
```

### 5. Obter Número de Série

```python
reader = UR4Reader(port='COM4')
if reader.connect():
    serial = reader.get_serial_number()
    print(f"Número de Série: {serial}")
    reader.disconnect()
```

### 6. Configurar Potências

```python
reader = UR4Reader(port='COM4')
if reader.connect():
    # Define potência de 30 dBm para antena 1
    reader.set_antenna_power(1, read_power=30.0, write_power=30.0, save=True)
    
    # Verifica potência configurada
    powers = reader.get_antenna_power()
    print(f"Potência antena 1: {powers[1]}")
    
    reader.disconnect()
```

### 7. Ativar/Desativar Antenas

```python
reader = UR4Reader(port='COM4')
if reader.connect():
    # Ativa apenas antenas 1, 2 e 3
    reader.set_active_antennas([1, 2, 3], save=True)
    
    # Verifica quais estão ativas
    antennas = reader.get_active_antennas()
    print(f"Antenas ativas: {antennas}")
    
    reader.disconnect()
```

### 8. Obter Todas as Informações

```python
reader = UR4Reader(port='COM4')
if reader.connect():
    info = reader.get_reader_info()
    
    print(f"Serial: {info['serial_number']}")
    print(f"Porta: {info['port']}")
    print(f"Antenas ativas: {info['active_antennas']} ({info['antenna_count']} no total)")
    
    for ant, power in info['antenna_powers'].items():
        print(f"Antena {ant}: R={power['read_power']:.1f}dBm W={power['write_power']:.1f}dBm")
    
    reader.disconnect()
```

## 🔧 API Reference

### Classe `UR4Reader`

#### Construtor
```python
UR4Reader(port='COM4', baudrate=115200, debug=False)
```

**Parâmetros:**
- `port` (str): Porta serial (ex: 'COM4', '/dev/ttyUSB0')
- `baudrate` (int): Taxa de transmissão (padrão: 115200)
- `debug` (bool): Ativa logs detalhados

#### Métodos Principais

##### `connect() -> bool`
Estabelece conexão serial com o UR4.

**Retorna:** `True` se conectado com sucesso

##### `disconnect()`
Fecha a conexão serial.

##### `is_connected() -> bool`
Verifica se está conectado.

##### `read_continuous(callback=None, anti_spam_delay=0.3, print_output=True)`
Leitura contínua de tags (bloqueante até Ctrl+C).

**Parâmetros:**
- `callback` (callable): Função `callback(epc, antenna, rssi)` chamada para cada tag
- `anti_spam_delay` (float): Tempo mínimo entre leituras da mesma tag (segundos)
- `print_output` (bool): Se True, imprime no console

##### `read_single(timeout=5.0) -> dict | None`
Lê uma única tag (bloqueante).

**Parâmetros:**
- `timeout` (float): Tempo máximo de espera (segundos)

**Retorna:** `{'epc': str, 'antenna': int, 'rssi': float}` ou `None`

##### `start_inventory()`
Inicia leitura contínua no hardware.

##### `stop_inventory()`
Para leitura contínua no hardware.

#### Métodos de Configuração

##### `get_serial_number() -> str | None`
Obtém o número de série do módulo UR4.

**Retorna:** String hexadecimal com 8 caracteres (4 bytes) ou `None`

**Exemplo:**
```python
serial = reader.get_serial_number()
print(f"Serial: {serial}")  # Ex: "1E004D00"
```

##### `get_antenna_power() -> dict | None`
Obtém potências de leitura/escrita de todas as antenas.

**Retorna:** `{antenna_num: {'read_power': float, 'write_power': float}}` ou `None`

##### `get_active_antennas() -> list | None`
Lista as antenas atualmente ativas.

**Retorna:** Lista de números de antenas (ex: `[1, 2, 3]`) ou `None`

##### `set_antenna_power(antenna, read_power, write_power, save=False) -> bool`
Configura a potência de uma antena específica.

**Parâmetros:**
- `antenna` (int): Número da antena (1-16)
- `read_power` (float): Potência de leitura em dBm (0.0 a 33.0)
- `write_power` (float): Potência de escrita em dBm (0.0 a 33.0)
- `save` (bool): Se True, salva configuração permanentemente

**Retorna:** `True` se sucesso

**Exemplo:**
```python
# Configura antena 1 para 30 dBm
reader.set_antenna_power(1, 30.0, 30.0, save=True)
```

##### `set_active_antennas(antennas, save=False) -> bool`
Define quais antenas devem estar ativas.

**Parâmetros:**
- `antennas` (list): Lista de números de antenas a ativar (1-16)
- `save` (bool): Se True, salva configuração permanentemente

**Retorna:** `True` se sucesso

**Exemplo:**
```python
# Ativa apenas antenas 1, 2 e 4
reader.set_active_antennas([1, 2, 4], save=True)
```

##### `get_reader_info() -> dict`
Obtém informações completas do leitor.

**Retorna:** Dict com todas as configurações (serial, antenas, potências, etc)

**Exemplo:**
```python
info = reader.get_reader_info()
print(f"Serial: {info['serial_number']}")
print(f"Antenas ativas: {info['active_antennas']}")
print(f"Potências: {info['antenna_powers']}")
```

### Funções Utilitárias

##### `detect_serial_port() -> str | None`
Detecta automaticamente a porta serial do UR4.

**Retorna:** Caminho da porta ou `None`

##### `list_serial_ports() -> List[str]`
Lista todas as portas seriais disponíveis.

**Retorna:** Lista de caminhos de portas

## 🐧 Linux

### Permissões

```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER

# Fazer logout/login para aplicar
```

### Udev Rules (opcional)

Criar `/etc/udev/rules.d/99-ur4-rfid.rules`:

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="portal_rfid", MODE="0666"
```

Recarregar:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Agora o dispositivo estará em `/dev/portal_rfid`.

## 📝 Protocolo UR4

- **Frame Header**: `C8 8C`
- **Comando Inventory**: `82`
- **Resposta**: `83`
- **Frame End**: `0D 0A`
- **Baudrate padrão**: 115200

## 🔍 Troubleshooting

### Porta não encontrada
```bash
# Windows
# Verificar no Gerenciador de Dispositivos

# Linux
ls -la /dev/ttyUSB* /dev/ttyACM*
```

### Permissão negada (Linux)
```bash
sudo chmod 666 /dev/ttyUSB0
# ou
sudo usermod -a -G dialout $USER
# (requer logout/login)
```

### Modo Debug
```python
reader = UR4Reader(port='COM4', debug=True)
# Mostra todos os bytes enviados/recebidos
```

## 📄 Licença

MIT License

## 👨‍💻 Autor

Getel Soluções em Tecnologia
