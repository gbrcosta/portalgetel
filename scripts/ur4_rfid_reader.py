"""
Script para comunicação com UR4 e leitura das antenas RFID
Este script simula a leitura de 2 antenas RFID conectadas ao UR4
"""
import socket
import time
import requests
import threading
from datetime import datetime
import os
import json

# Configurações
UR4_IP = "192.168.1.100"  # Altere para o IP do seu UR4
UR4_PORT = 30002  # Porta padrão para comunicação com UR4
API_URL = "http://localhost:8000/api/rfid/event"

# Configuração das antenas (registradores digitais no UR4)
ANTENNA_1_REGISTER = 0  # Digital Input 0
ANTENNA_2_REGISTER = 1  # Digital Input 1

class UR4RFIDReader:
    def __init__(self, ur4_ip, ur4_port, api_url):
        self.ur4_ip = ur4_ip
        self.ur4_port = ur4_port
        self.api_url = api_url
        self.running = False
        self.socket = None
        
        # Estado anterior das antenas
        self.antenna_1_prev_state = False
        self.antenna_2_prev_state = False
        
        # Última tag lida (simulação - em produção virá do leitor RFID)
        self.current_tag = None
        # runtime config path
        self.runtime_config_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'config_runtime.json')
    
    def connect(self):
        """Conecta ao UR4"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ur4_ip, self.ur4_port))
            print(f"Conectado ao UR4 em {self.ur4_ip}:{self.ur4_port}")
            return True
        except Exception as e:
            print(f"Erro ao conectar ao UR4: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do UR4"""
        if self.socket:
            self.socket.close()
            print("Desconectado do UR4")
    
    def read_digital_input(self, register):
        """Lê um input digital do UR4"""
        try:
            # Comando para ler input digital
            command = f"get_digital_in({register})\n"
            self.socket.send(command.encode())
            
            # Receber resposta
            response = self.socket.recv(1024).decode().strip()
            return response == "True" or response == "true"
        except Exception as e:
            print(f"Erro ao ler input digital {register}: {e}")
            return False
    
    def simulate_rfid_read(self, antenna_number):
        """
        Simula a leitura de uma tag RFID
        Em produção, aqui você integraria com o leitor RFID real
        """
        # Simulação: gera um ID de tag baseado no timestamp
        tag_id = f"TAG{int(time.time()) % 10000:04d}"
        return tag_id
    
    def send_event_to_api(self, tag_id, antenna_number):
        """Envia evento de leitura para a API"""
        try:
            # carregar potência/estado runtime (se disponível)
            antenna_power = None
            try:
                with open(self.runtime_config_path, 'r') as f:
                    cfg = json.load(f)
                    if antenna_number == 1:
                        antenna_power = cfg.get('antenna1_power')
                    else:
                        antenna_power = cfg.get('antenna2_power')
            except Exception:
                pass

            payload = {
                "tag_id": tag_id,
                "antenna_number": antenna_number,
            }
            if antenna_power is not None:
                payload['antenna_power'] = antenna_power
            response = requests.post(self.api_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Antena {antenna_number}: Tag {tag_id}")
                return True
            else:
                print(f"Erro ao enviar evento: {response.status_code}")
                return False
        except Exception as e:
            print(f"Erro ao comunicar com API: {e}")
            return False
    
    def monitor_antennas(self):
        """Monitora as antenas em loop contínuo"""
        print("\nMonitoramento das antenas iniciado...")
        print("Pressione Ctrl+C para parar\n")
        
        while self.running:
            try:
                # Ler estado das antenas
                antenna_1_state = self.read_digital_input(ANTENNA_1_REGISTER)
                antenna_2_state = self.read_digital_input(ANTENNA_2_REGISTER)

                # carregar configuração runtime (enable/disable)
                cfg = {}
                try:
                    with open(self.runtime_config_path, 'r') as f:
                        cfg = json.load(f)
                except Exception:
                    cfg = {}
                antenna1_enabled = cfg.get('antenna1_enabled', True)
                antenna2_enabled = cfg.get('antenna2_enabled', False)
                
                # Detectar mudança de estado na Antena 1 (borda de subida)
                if antenna_1_state and not self.antenna_1_prev_state and antenna1_enabled:
                    tag_id = self.simulate_rfid_read(1)
                    self.current_tag = tag_id
                    self.send_event_to_api(tag_id, 1)
                
                # Detectar mudança de estado na Antena 2 (borda de subida)
                if antenna_2_state and not self.antenna_2_prev_state and antenna2_enabled:
                    # Usar a última tag lida
                    if self.current_tag:
                        self.send_event_to_api(self.current_tag, 2)
                    else:
                        # Se não houver tag anterior, simula uma nova
                        tag_id = self.simulate_rfid_read(2)
                        self.send_event_to_api(tag_id, 2)
                
                # Atualizar estados anteriores
                self.antenna_1_prev_state = antenna_1_state
                self.antenna_2_prev_state = antenna_2_state
                
                # Aguardar antes da próxima leitura
                time.sleep(0.1)  # 100ms entre leituras
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                time.sleep(1)
    
    def start(self):
        """Inicia o monitoramento"""
        if not self.connect():
            print("Não foi possível conectar ao UR4. Iniciando em modo simulação...")
            self.start_simulation_mode()
            return
        
        self.running = True
        self.monitor_antennas()
    
    def start_simulation_mode(self):
        """Modo de simulação sem conexão com UR4 real"""
        print("\n=== MODO SIMULAÇÃO ===")
        print("Simulando detecção de tags nas antenas...")
        print("Pressione Ctrl+C para parar\n")
        
        self.running = True
        tag_counter = 1
        
        try:
            while self.running:
                # Simular tag passando pela antena 1
                tag_id = f"TAG{tag_counter:04d}"
                print(f"\n[Simulação] Tag {tag_id} detectada na Antena 1 (Início)")
                self.send_event_to_api(tag_id, 1)
                
                # Aguardar tempo de "produção" (entre 5 e 15 segundos)
                production_time = 10
                print(f"[Simulação] Aguardando {production_time}s (tempo de produção)...")
                time.sleep(production_time)
                
                # Simular tag passando pela antena 2
                print(f"[Simulação] Tag {tag_id} detectada na Antena 2 (Fim)")
                self.send_event_to_api(tag_id, 2)
                
                tag_counter += 1
                
                # Aguardar antes da próxima tag
                time.sleep(3)
                
        except KeyboardInterrupt:
            print("\n\nSimulação interrompida pelo usuário")
    
    def stop(self):
        """Para o monitoramento"""
        self.running = False
        self.disconnect()

if __name__ == "__main__":
    print("=" * 60)
    print("Portal RFID - Biamar UR4")
    print("Sistema de Monitoramento de Produção")
    print("=" * 60)
    
    reader = UR4RFIDReader(UR4_IP, UR4_PORT, API_URL)
    
    try:
        reader.start()
    except KeyboardInterrupt:
        print("\n\nEncerrando...")
    finally:
        reader.stop()
        print("Sistema encerrado")
