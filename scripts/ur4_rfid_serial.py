#!/usr/bin/env python3
"""
Portal RFID - Biamar UR4 (Conexão Serial)
Sistema de monitoramento contínuo de tags RFID via RS232/USB
Baseado no portal-rfid-sistema.py da Getel
"""

import serial
import time
import requests
import json
from datetime import datetime
import signal
import sys
import os

# Importar configurações
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from config import API_HOST, API_PORT
except ImportError:
    API_HOST = "localhost"
    API_PORT = 8000

# Configurações do Portal
PORTA_SERIAL = '/dev/ttyUSB0'  # Porta do UR4 via USB
BAUDRATE = 115200
LOCAL_PORTAL = 'Biamar - Linha de Produção'
PORTAL_ID = 'biamar_ur4_01'

# Configurações de Proteção Anti-Spam
TIMEOUT_TAG = 300  # 5 minutos - tempo para evitar leituras duplicadas
TIMEOUT_TAG_BARULHENTA = 10  # 10 segundos para tags muito detectadas
MAX_DETECCOES_NORMAL = 10  # máximo de detecções antes de considerar "barulhenta"
BACKOFF_MAX = 60  # máximo tempo de backoff para retry (segundos)

# Configurações de Sentido - Define antenas
ANTENA_ENTRADA = 1  # Antena 1 = Início do processo
ANTENA_SAIDA = 2    # Antena 2 = Fim do processo

# API Configuration
API_URL = f"http://{API_HOST}:{API_PORT}/api/rfid/event"
API_TOKEN = 'seu-token-aqui'  # Se necessário
TIMEOUT_HTTP = 5  # segundos

# Configurações de Log
MOSTRAR_PAYLOAD_SIMULADO = False
MOSTRAR_TIMESTAMP = True
MOSTRAR_DEBUG_PROTECAO = False  # Mostra detalhes da proteção anti-spam


class PortalRFIDBiamar:
    def __init__(self):
        self.executando = True
        self.ser = None
        self.epcs_recentes = {}  # {epc: {'ultimo_envio': timestamp, 'ultima_deteccao': timestamp, ...}}
        self.contador_tags = 0
        self.contador_inicio = 0  # Tags na antena 1
        self.contador_fim = 0     # Tags na antena 2
        self.contador_duplicatas_evitadas = 0
        
        # Headers para requisições HTTP
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Biamar-Portal-RFID/1.0'
        }
        
        if API_TOKEN != 'seu-token-aqui':
            self.headers['Authorization'] = f'Bearer {API_TOKEN}'
        
        # Configurar handler para Ctrl+C
        signal.signal(signal.SIGINT, self.parar_portal)
        signal.signal(signal.SIGTERM, self.parar_portal)
    
    def parar_portal(self, signum, frame):
        """Handler para parar o portal graciosamente"""
        print("\n" + "="*60)
        print("🛑 PARANDO PORTAL RFID...")
        print("="*60)
        self.executando = False
        
        if self.ser and self.ser.is_open:
            try:
                # Comando para parar leitura contínua
                cmd_stop = bytes([0xC8, 0x8C, 0x00, 0x08, 0x8C, 0x84, 0x0D, 0x0A])
                self.ser.write(cmd_stop)
                time.sleep(0.2)
                self.ser.close()
                print("🔌 Conexão serial fechada.")
            except:
                pass
        
        # Mostrar estatísticas finais
        self.mostrar_estatisticas()
        print("👋 Portal RFID finalizado. Até mais!")
        sys.exit(0)
    
    def mostrar_estatisticas(self):
        """Mostra estatísticas do portal"""
        print(f"📊 ESTATÍSTICAS FINAIS:")
        print(f"   🏷️  Total de tags únicas: {self.contador_tags}")
        print(f"   ➡️  Início (Antena 1): {self.contador_inicio}")
        print(f"   ✅  Fim (Antena 2): {self.contador_fim}")
        print(f"   🛡️  Duplicatas evitadas: {self.contador_duplicatas_evitadas}")
        print(f"   📍 Local: {LOCAL_PORTAL}")
    
    def determinar_sentido(self, antena):
        """Determina o sentido baseado na antena"""
        if antena == ANTENA_ENTRADA:
            return "inicio"
        elif antena == ANTENA_SAIDA:
            return "fim"
        else:
            # Antena desconhecida, assumir baseado em número par/ímpar
            return "inicio" if antena % 2 == 1 else "fim"
    
    def deve_enviar_payload(self, epc, antena):
        """
        Determina se deve enviar o payload baseado na lógica de negócio
        Tag precisa passar pelas duas antenas (início e fim)
        """
        agora = time.time()
        
        # Se é a primeira vez que vemos esta tag
        if epc not in self.epcs_recentes:
            self.epcs_recentes[epc] = {
                'ultimo_envio': agora,
                'ultima_deteccao': agora,
                'tentativas': 0,
                'sucesso_ultimo': False,
                'primeira_antena': antena,
                'ultima_antena': antena,
                'contagem_deteccoes': 1,
                'passou_inicio': antena == ANTENA_ENTRADA,
                'passou_fim': antena == ANTENA_SAIDA
            }
            return True
        
        dados_epc = self.epcs_recentes[epc]
        tempo_desde_ultimo_envio = agora - dados_epc['ultimo_envio']
        
        # Atualizar dados da detecção atual
        dados_epc['ultima_deteccao'] = agora
        dados_epc['ultima_antena'] = antena
        dados_epc['contagem_deteccoes'] += 1
        
        # Atualizar flags de passagem
        if antena == ANTENA_ENTRADA:
            dados_epc['passou_inicio'] = True
        elif antena == ANTENA_SAIDA:
            dados_epc['passou_fim'] = True
        
        if MOSTRAR_DEBUG_PROTECAO:
            print(f"   📊 Debug: Tempo desde último envio: {tempo_desde_ultimo_envio:.1f}s | Detecções: {dados_epc['contagem_deteccoes']}")
        
        # REGRA 1: Tag mudou de antena - sempre permitir (mudança de estado)
        if dados_epc['primeira_antena'] != antena and dados_epc.get('ja_enviou_mudanca', False) == False:
            if MOSTRAR_DEBUG_PROTECAO:
                print(f"   🔄 PERMITIDO: Tag mudou de antena {dados_epc['primeira_antena']} → {antena}")
            dados_epc['ja_enviou_mudanca'] = True
            return True
        
        # REGRA 2: Timeout básico - sempre respeitar o tempo mínimo
        if tempo_desde_ultimo_envio < TIMEOUT_TAG:
            self.contador_duplicatas_evitadas += 1
            if MOSTRAR_DEBUG_PROTECAO:
                print(f"   ⏰ BLOQUEADO: Timeout {TIMEOUT_TAG}s não atingido ({tempo_desde_ultimo_envio:.1f}s)")
            return False
        
        # REGRA 3: Se o último envio falhou, permitir retry com backoff exponencial
        if not dados_epc['sucesso_ultimo']:
            backoff_time = min(TIMEOUT_TAG * (2 ** dados_epc['tentativas']), BACKOFF_MAX)
            if tempo_desde_ultimo_envio >= backoff_time:
                if MOSTRAR_DEBUG_PROTECAO:
                    print(f"   🔄 PERMITIDO: Retry após falha (backoff: {backoff_time:.1f}s)")
                return True
            else:
                self.contador_duplicatas_evitadas += 1
                if MOSTRAR_DEBUG_PROTECAO:
                    print(f"   ⏳ BLOQUEADO: Aguardando backoff ({backoff_time - tempo_desde_ultimo_envio:.1f}s restantes)")
                return False
        
        # REGRA 4: Tag muito "barulhenta" - NÃO PERMITIR mais envios
        if dados_epc['contagem_deteccoes'] > MAX_DETECCOES_NORMAL:
            self.contador_duplicatas_evitadas += 1
            if MOSTRAR_DEBUG_PROTECAO:
                print(f"   🔇 BLOQUEADO: Tag barulhenta ({dados_epc['contagem_deteccoes']} detecções)")
            return False
        
        # REGRA 5: Se passou timeout e teve sucesso, permitir reenvio
        if tempo_desde_ultimo_envio >= TIMEOUT_TAG:
            if MOSTRAR_DEBUG_PROTECAO:
                print(f"   ✅ PERMITIDO: Timeout atingido ({tempo_desde_ultimo_envio:.1f}s)")
            return True
        
        # Default: bloquear
        self.contador_duplicatas_evitadas += 1
        return False
    
    def enviar_payload(self, epc, antena):
        """Envia os dados da tag para a API com proteção anti-spam"""
        # Verificar se deve enviar
        if not self.deve_enviar_payload(epc, antena):
            return False  # Não enviou
        
        sentido = self.determinar_sentido(antena)
        agora = time.time()
        
        # Atualizar dados do EPC
        if epc not in self.epcs_recentes:
            self.epcs_recentes[epc] = {
                'ultimo_envio': agora,
                'ultima_deteccao': agora,
                'tentativas': 0,
                'sucesso_ultimo': False,
                'primeira_antena': antena,
                'ultima_antena': antena,
                'contagem_deteccoes': 1,
                'passou_inicio': antena == ANTENA_ENTRADA,
                'passou_fim': antena == ANTENA_SAIDA
            }
        
        self.epcs_recentes[epc]['ultimo_envio'] = agora
        self.epcs_recentes[epc]['tentativas'] += 1
        
        # Atualizar contadores
        if sentido == "inicio":
            self.contador_inicio += 1
            emoji_sentido = "➡️"
        else:
            self.contador_fim += 1
            emoji_sentido = "✅"
        
        payload = {
            "tag_id": epc,
            "antenna_number": antena
        }
        
        timestamp_br = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        sucesso = False
        
        try:
            print(f"{emoji_sentido} [{timestamp_br}] EPC: {epc} | {sentido.upper()} | Ant:{antena} | Tentativa:{self.epcs_recentes[epc]['tentativas']}")
            
            if MOSTRAR_PAYLOAD_SIMULADO:
                print(f"   💾 Payload:")
                print(f"      {json.dumps(payload, indent=6, ensure_ascii=False)}")
            
            response = requests.post(
                API_URL, 
                json=payload, 
                headers=self.headers,
                timeout=TIMEOUT_HTTP
            )
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Enviado com sucesso! (Status: {response.status_code})")
                sucesso = True
            else:
                print(f"   ⚠️  Resposta inesperada: {response.status_code}")
                print(f"      {response.text[:100]}...")
                    
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout no envio (>{TIMEOUT_HTTP}s)")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Erro de conexão com o servidor")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Erro na requisição: {e}")
        except Exception as e:
            print(f"   ❌ Erro inesperado: {e}")
        
        # Atualizar status do último envio
        self.epcs_recentes[epc]['sucesso_ultimo'] = sucesso
        
        # Se foi sucesso, marcar como processado e resetar tentativas
        if sucesso:
            self.epcs_recentes[epc]['tentativas'] = 0
        
        return sucesso  # Retorna True se enviou, False se não enviou
    
    def decodificar_e_processar_epc(self, resp_bytes):
        """Decodifica e processa EPCs detectados"""
        if len(resp_bytes) < 13: 
            return
            
        cmd = resp_bytes[4]
        if cmd not in [0x81, 0x83]: 
            return

        try:
            frame_len = (resp_bytes[2] << 8) + resp_bytes[3]
            data_len = frame_len - 8
            epc_len = data_len - 5
            
            if epc_len <= 0: 
                return

            epc_bytes = resp_bytes[7 : 7 + epc_len]
            ant_num = resp_bytes[-4]
            epc_hex = "".join([f"{b:02X}" for b in epc_bytes])
            
            # Tentar enviar payload (só conta se realmente enviar)
            payload_enviado = self.enviar_payload(epc_hex, ant_num)
            
            # Só contar se payload foi enviado
            if payload_enviado:
                self.contador_tags += 1
            
            # Limpar cache antigo
            self.limpar_cache_antigo()
            
        except Exception as e:
            print(f"❌ Erro ao decodificar EPC: {e}")
    
    def limpar_cache_antigo(self):
        """Remove tags antigas do cache para liberar memória"""
        agora = time.time()
        tags_para_remover = []
        
        for epc, dados in self.epcs_recentes.items():
            # Remover tags que não foram vistas há muito tempo
            tempo_sem_deteccao = agora - dados['ultima_deteccao']
            if tempo_sem_deteccao > (TIMEOUT_TAG * 10):  # 10x o timeout padrão
                tags_para_remover.append(epc)
        
        for epc in tags_para_remover:
            del self.epcs_recentes[epc]
        
        # Limpar contador de detecções periodicamente
        for dados in self.epcs_recentes.values():
            if agora - dados['ultima_deteccao'] > (TIMEOUT_TAG * 5):
                dados['contagem_deteccoes'] = max(1, dados['contagem_deteccoes'] // 2)
    
    def mostrar_cabecalho(self):
        """Mostra informações iniciais do portal"""
        print("="*60)
        print("🚪 PORTAL RFID - BIAMAR UR4 (Conexão Serial)")
        print("="*60)
        print(f"📍 Local: {LOCAL_PORTAL}")
        print(f"🆔 Portal ID: {PORTAL_ID}")
        print(f"🔌 Porta Serial: {PORTA_SERIAL}")
        print(f"⏰ Timeout Tags: {TIMEOUT_TAG}s")
        print(f"➡️  Antena Início: {ANTENA_ENTRADA}")
        print(f"✅  Antena Fim: {ANTENA_SAIDA}")
        print(f"🌐 API: {API_URL}")
        print("="*60)
        print("🔄 Status: Iniciando...")
        print("🛑 Pressione Ctrl+C para parar")
        print("-"*60)
    
    def iniciar_portal(self):
        """Inicia o portal RFID"""
        self.mostrar_cabecalho()
        
        try:
            # Conectar à porta serial
            print(f"🔧 Conectando à {PORTA_SERIAL}...")
            self.ser = serial.Serial(
                port=PORTA_SERIAL,
                baudrate=BAUDRATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            
            # Comando para leitura contínua
            cmd_continuo = bytes([0xC8, 0x8C, 0x00, 0x0A, 0x82, 0x00, 0x00, 0x88, 0x0D, 0x0A])
            
            print("✅ Conectado com sucesso!")
            print("🚀 Portal ATIVO - Monitorando tags...")
            print("-"*60)
            
            # Enviar comando de leitura contínua
            self.ser.write(cmd_continuo)
            time.sleep(0.1)
            
            # Loop principal - executa indefinidamente
            while self.executando:
                try:
                    if self.ser.in_waiting > 0:
                        resp = self.ser.read(self.ser.in_waiting)
                        self.decodificar_e_processar_epc(resp)
                    
                    time.sleep(0.05)
                    
                except Exception as e:
                    print(f"❌ Erro no loop principal: {e}")
                    time.sleep(1)
                    
        except serial.SerialException as e:
            print(f"❌ ERRO DE CONEXÃO SERIAL:")
            print(f"   {e}")
            print(f"")
            print(f"🔧 POSSÍVEIS SOLUÇÕES:")
            print(f"   1. Verifique se o dispositivo está conectado")
            print(f"   2. Verifique se a porta {PORTA_SERIAL} está correta (ls -la /dev/ttyUSB*)")
            print(f"   3. Verifique permissões: sudo usermod -a -G dialout $USER")
            print(f"   4. Faça logout/login para aplicar permissões")
            
        except Exception as e:
            print(f"❌ ERRO INESPERADO: {e}")
            
        finally:
            if self.ser and self.ser.is_open:
                try:
                    cmd_stop = bytes([0xC8, 0x8C, 0x00, 0x08, 0x8C, 0x84, 0x0D, 0x0A])
                    self.ser.write(cmd_stop)
                    time.sleep(0.1)
                    self.ser.close()
                except:
                    pass


def main():
    """Função principal"""
    print("Iniciando Portal RFID Biamar...")
    
    # Verificar se está rodando no ambiente virtual
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Executando no ambiente virtual")
    else:
        print("⚠️  Recomendado executar no ambiente virtual")
    
    # Criar e iniciar o portal
    portal = PortalRFIDBiamar()
    portal.iniciar_portal()


if __name__ == "__main__":
    main()
