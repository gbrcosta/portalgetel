#!/usr/bin/env python3
"""
Portal RFID - Biamar UR4
Script de integração usando biblioteca ur4_reader
"""

import sys
import os
import requests
import time
import json
from datetime import datetime
import threading

# Adicionar biblioteca ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'biblioteca'))

from ur4_reader import UR4Reader, detect_serial_port, list_serial_ports

# Configurações da API
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config import API_HOST, API_PORT
except ImportError:
    API_HOST = "localhost"
    API_PORT = 8000

API_URL = f"http://{API_HOST}:{API_PORT}/api/rfid/event"
TIMEOUT_HTTP = 5

# Configurações do Portal
LOCAL_PORTAL = 'Biamar - Linha de Produção'
PORTAL_ID = 'biamar_ur4_01'

# Arquivo para compartilhar informações do dispositivo
DEVICE_INFO_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'device_info.json')
REFRESH_SIGNAL_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'refresh_signal.txt')
CONFIG_CHANGED_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'config_changed.txt')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'config.json')

# Estatísticas
stats = {
    'total_tags': 0,
    'inicio': 0,
    'fim': 0,
    'erros_api': 0
}


def save_device_info(reader, port, force_debug=False):
    """Salva informações do dispositivo em arquivo JSON"""
    try:
        # Verificar se o reader está conectado (is_connected é FUNÇÃO)
        if not reader or not hasattr(reader, 'is_connected') or not reader.is_connected():
            print(f"⚠️ Reader não está conectado!")
            # Salvar info de erro
            device_info = {
                "connected": False,
                "port": port,
                "error": "Dispositivo não conectado",
                "last_update": datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(DEVICE_INFO_FILE), exist_ok=True)
            with open(DEVICE_INFO_FILE, 'w') as f:
                json.dump(device_info, f, indent=2)
            return
        
        # Ativar debug apenas se forçado (atualização manual)
        old_debug = getattr(reader, 'debug', False)
        if force_debug:
            reader.debug = True
        
        # Aguardar dispositivo estar pronto
        time.sleep(0.5)
        
        # Tentar ler potências diretamente
        if force_debug:
            print(f"\n📊 DEBUG - Tentando ler potências das antenas...")
        powers = reader.get_antenna_power()
        if force_debug:
            print(f"   Resultado de get_antenna_power(): {powers}")
        
        # Pequeno delay entre comandos
        time.sleep(0.3)
        
        # Obter informações completas
        if force_debug:
            print(f"\n📊 DEBUG - Obtendo informações completas do reader...")
        info = reader.get_reader_info()
        
        # Restaurar debug
        reader.debug = old_debug
        
        if force_debug:
            print(f"\n📊 DEBUG - Informações brutas do dispositivo:")
            print(f"   Antenna Powers: {info.get('antenna_powers', {})}")
            print(f"   Active Antennas: {info.get('active_antennas', [])}")
            print(f"   Port: {info.get('port', 'N/A')}")
            print(f"   Firmware: {info.get('firmware_version', 'N/A')}")
        
        # Extrair potências das antenas
        antenna_powers = info.get('antenna_powers', {})
        
        # FALLBACK: Se não conseguir ler as potências, usar valores padrão
        # NÃO tentar configurar automaticamente para evitar travamento do dispositivo
        if not antenna_powers:
            if force_debug:
                print(f"⚠️ Não foi possível ler potências das antenas, usando valores padrão")
            
            # Usar valores padrão sem tentar configurar o dispositivo
            antenna_powers = {
                1: {'read_power': 0.0, 'write_power': 0.0},
                2: {'read_power': 0.0, 'write_power': 0.0}
            }
        
        # Extrair potências das antenas 1 e 2
        ant1_power = antenna_powers.get(1, {}).get('read_power', 5.0)
        ant2_power = antenna_powers.get(2, {}).get('read_power', 5.0)
        
        # Forçar antenas 1 e 2 como ativas
        active_antennas = [1, 2]
        
        # Module ID (retornado pelo dispositivo) vs Serial Number (gravado fisicamente)
        module_id = info.get('serial_number', 'N/A')
        
        device_info = {
            "connected": True,
            "port": info.get('port', port),
            "module_id": module_id,  # ID interno do módulo (ex: 1E004D00)
            "serial_number": "HUR40A251000022",  # Serial físico do dispositivo
            "firmware_version": info.get('firmware_version', 'N/A'),
            "hardware_version": info.get('hardware_version', 'UR4 RFID Reader'),
            "antenna1_power": f"{ant1_power:.1f} dBm",
            "antenna2_power": f"{ant2_power:.1f} dBm",
            "work_mode": info.get('work_mode', 'Active Mode'),
            "antenna_count": 2,
            "active_antennas": active_antennas,
            "last_update": datetime.now().isoformat(),
            "error": None
        }
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(DEVICE_INFO_FILE), exist_ok=True)
        
        # Salvar arquivo
        with open(DEVICE_INFO_FILE, 'w') as f:
            json.dump(device_info, f, indent=2)
        
        print(f"\n📝 Informações do dispositivo salvas:")
        print(f"   🔢 Serial: {device_info['serial_number']}")
        print(f"   🆔 Module ID: {device_info['module_id']}")
        print(f"   🔌 Porta: {device_info['port']}")
        print(f"   💾 Firmware: {device_info['firmware_version']}")
        print(f"   📶 Antena 1: {device_info['antenna1_power']}")
        print(f"   📶 Antena 2: {device_info['antenna2_power']}")
        print(f"   📡 Antenas ativas: {device_info['active_antennas']}")
        
    except Exception as e:
        print(f"⚠️ Erro ao salvar informações do dispositivo: {e}")
        import traceback
        traceback.print_exc()


def callback_rfid(epc: str, antenna: int, rssi: int):
    """
    Callback chamado quando uma tag é detectada
    
    Args:
        epc: ID da tag RFID
        antenna: Número da antena (1 ou 2)
        rssi: Intensidade do sinal em dBm
    """
    global stats
    
    # Determinar sentido baseado na antena
    sentido = "inicio" if antenna == 1 else "fim"
    emoji = "➡️" if antenna == 1 else "✅"
    
    # Preparar payload para API
    payload = {
        "tag_id": epc,
        "antenna_number": antenna
    }
    
    # Timestamp para log
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    print(f"{emoji} [{timestamp}] EPC: {epc} | {sentido.upper()} | Ant:{antenna} | RSSI:{rssi}dBm")
    
    # Enviar para API
    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=TIMEOUT_HTTP
        )
        
        if response.status_code in [200, 201]:
            print(f"   ✅ Enviado com sucesso! (Status: {response.status_code})")
            stats['total_tags'] += 1
            if antenna == 1:
                stats['inicio'] += 1
            else:
                stats['fim'] += 1
        else:
            print(f"   ⚠️  Resposta inesperada: {response.status_code}")
            stats['erros_api'] += 1
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout no envio (>{TIMEOUT_HTTP}s)")
        stats['erros_api'] += 1
    except requests.exceptions.ConnectionError:
        print(f"   🔌 Erro de conexão com o servidor")
        stats['erros_api'] += 1
    except Exception as e:
        print(f"   ❌ Erro inesperado: {e}")
        stats['erros_api'] += 1


def mostrar_cabecalho():
    """Mostra informações iniciais"""
    print("=" * 70)
    print("🚪 PORTAL RFID - BIAMAR UR4")
    print("=" * 70)
    print(f"📍 Local: {LOCAL_PORTAL}")
    print(f"🆔 Portal ID: {PORTAL_ID}")
    print(f"🌐 API: {API_URL}")
    print("=" * 70)
    print("🛑 Pressione Ctrl+C para parar")
    print("-" * 70)


def mostrar_estatisticas():
    """Mostra estatísticas finais"""
    print("\n" + "=" * 70)
    print("📊 ESTATÍSTICAS FINAIS:")
    print(f"   🏷️  Total de tags enviadas: {stats['total_tags']}")
    print(f"   ➡️  Início (Antena 1): {stats['inicio']}")
    print(f"   ✅  Fim (Antena 2): {stats['fim']}")
    print(f"   ❌  Erros de API: {stats['erros_api']}")
    print(f"   📍 Local: {LOCAL_PORTAL}")
    print("=" * 70)


def apply_config_to_device(reader):
    """Aplica configurações do arquivo config.json ao dispositivo"""
    try:
        if not os.path.exists(CONFIG_FILE):
            print(f"⚠️ Arquivo de configuração não encontrado")
            return False
        
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        print(f"\n🔧 Aplicando configurações ao UR4...")
        print(f"   Antena 1: {'Ativa' if config.get('antenna1_enabled', True) else 'Inativa'} @ {config.get('antenna1_power', 5)} dBm")
        print(f"   Antena 2: {'Ativa' if config.get('antenna2_enabled', True) else 'Inativa'} @ {config.get('antenna2_power', 5)} dBm")
        
        # Configurar antenas ativas
        active_antennas = []
        if config.get('antenna1_enabled', True):
            active_antennas.append(1)
        if config.get('antenna2_enabled', True):
            active_antennas.append(2)
        
        if active_antennas:
            success = reader.set_active_antennas(active_antennas)
            if success:
                print(f"   ✅ Antenas {active_antennas} configuradas")
            else:
                print(f"   ⚠️ Falha ao configurar antenas")
        
        time.sleep(0.2)
        
        # Configurar potências
        power1 = config.get('antenna1_power', 5)
        power2 = config.get('antenna2_power', 5)
        
        if reader.set_antenna_power(antenna=1, read_power=power1, write_power=power1, save=True):
            print(f"   ✅ Antena 1: {power1} dBm")
        else:
            print(f"   ⚠️ Falha ao configurar potência da antena 1")
        
        time.sleep(0.2)
        
        if reader.set_antenna_power(antenna=2, read_power=power2, write_power=power2, save=True):
            print(f"   ✅ Antena 2: {power2} dBm")
        else:
            print(f"   ⚠️ Falha ao configurar potência da antena 2")
        
        print(f"✅ Configurações aplicadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao aplicar configurações: {e}")
        return False


def update_device_info_periodically(reader, port, interval=120):
    """Thread para atualizar informações do dispositivo periodicamente"""
    last_signal_time = None
    last_config_time = None
    
    while True:
        time.sleep(5)  # Verifica a cada 5 segundos
        
        try:
            # Verificar se há mudança na configuração
            if os.path.exists(CONFIG_CHANGED_FILE):
                try:
                    with open(CONFIG_CHANGED_FILE, 'r') as f:
                        config_time_str = f.read().strip()
                    
                    # Se é um novo sinal de configuração, aplicar
                    if config_time_str != last_config_time:
                        last_config_time = config_time_str
                        print(f"\n🔧 Nova configuração detectada! Aplicando...")
                        
                        # Aplicar configurações
                        apply_config_to_device(reader)
                        
                        # Remover arquivo de sinal
                        os.remove(CONFIG_CHANGED_FILE)
                        
                        # Atualizar device info após aplicar config
                        time.sleep(1)
                        save_device_info(reader, port, force_debug=True)
                except Exception as e:
                    print(f"⚠️ Erro ao aplicar configuração: {e}")
            
            # Verificar se há sinal de atualização forçada
            force_update = False
            if os.path.exists(REFRESH_SIGNAL_FILE):
                try:
                    with open(REFRESH_SIGNAL_FILE, 'r') as f:
                        signal_time_str = f.read().strip()
                    
                    # Se é um novo sinal, forçar atualização
                    if signal_time_str != last_signal_time:
                        last_signal_time = signal_time_str
                        force_update = True
                        print(f"\n🔄 Atualização forçada requisitada!")
                        
                        # Remover arquivo de sinal
                        os.remove(REFRESH_SIGNAL_FILE)
                except:
                    pass
            
            # Atualizar informações se forçado ou se passou o intervalo
            current_time = time.time()
            if not hasattr(update_device_info_periodically, 'last_update'):
                update_device_info_periodically.last_update = current_time
            
            time_since_last = current_time - update_device_info_periodically.last_update
            
            if force_update or time_since_last >= interval:
                # Atualizar informações completas do dispositivo
                # Debug apenas em atualizações forçadas (botão na UI)
                save_device_info(reader, port, force_debug=force_update)
                update_device_info_periodically.last_update = current_time
                
                if not force_update:
                    print(f"\n🔄 Informações do dispositivo atualizadas automaticamente ({datetime.now().strftime('%H:%M:%S')})")
            
        except Exception as e:
            print(f"\n⚠️ Erro ao atualizar informações: {e}")


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Portal RFID Biamar UR4')
    parser.add_argument('--port', help='Porta serial (ex: COM4 ou /dev/ttyUSB0)')
    parser.add_argument('--list-ports', action='store_true', help='Lista portas disponíveis')
    parser.add_argument('--debug', action='store_true', help='Ativa modo debug')
    args = parser.parse_args()
    
    # Listar portas se solicitado
    if args.list_ports:
        print("Portas seriais disponíveis:")
        ports = list_serial_ports()
        if ports:
            for port in ports:
                print(f"  - {port}")
        else:
            print("  Nenhuma porta encontrada")
        return
    
    # Detectar ou usar porta especificada
    if args.port:
        port = args.port
        print(f"🔌 Usando porta especificada: {port}")
    else:
        print("🔍 Detectando porta serial automaticamente...")
        port = detect_serial_port()
        if not port:
            print("❌ Nenhuma porta serial encontrada!")
            print("\nPortas disponíveis:")
            for p in list_serial_ports():
                print(f"  - {p}")
            print("\nUse: python rfid_reader.py --port COM4")
            return
        print(f"✅ Porta detectada: {port}")
    
    mostrar_cabecalho()
    
    # Criar leitor
    reader = UR4Reader(port=port, debug=args.debug)
    
    # Conectar
    print(f"\n🔧 Conectando à {port}...")
    if not reader.connect():
        print(f"❌ Falha ao conectar à porta {port}")
        print("\n🔧 POSSÍVEIS SOLUÇÕES:")
        print("   1. Verifique se o dispositivo está conectado")
        print("   2. Verifique se a porta está correta: --list-ports")
        if sys.platform == "linux":
            print("   3. Verifique permissões: sudo usermod -a -G dialout $USER")
            print("   4. Faça logout/login para aplicar permissões")
        return
    
    # Iniciar thread para atualizar informações periodicamente
    update_thread = threading.Thread(
        target=update_device_info_periodically,
        args=(reader, port, 120),  # Atualiza a cada 2 minutos
        daemon=True
    )
    update_thread.start()
    
    print("✅ Conectado com sucesso!")
    
    # Aguardar dispositivo estabilizar antes de enviar comandos
    time.sleep(1.0)
    
    # Salvar informações do dispositivo (sem debug excessivo na primeira vez)
    print("📊 Coletando informações do dispositivo...")
    save_device_info(reader, port)
    
    print("🚀 Portal ATIVO - Monitorando tags...")
    print("-" * 70)
    
    try:
        # Iniciar leitura contínua com callback personalizado
        reader.read_continuous(
            callback=callback_rfid,
            anti_spam_delay=5.0,  # 5 segundos entre leituras da mesma tag
            print_output=False  # Não imprimir saída padrão (usamos nosso callback)
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Parando portal...")
    finally:
        reader.disconnect()
        mostrar_estatisticas()
        print("👋 Portal RFID finalizado. Até mais!")


if __name__ == '__main__':
    main()
