"""
UR4 RFID Reader Library
========================

Biblioteca Python para leitura de tags RFID com leitor UR4 via serial.

Uso como biblioteca:
    from ur4_reader import UR4Reader
    
    def on_tag_read(epc, antenna, rssi):
        print(f"Tag: {epc} | Antena: {antenna} | RSSI: {rssi}")
    
    reader = UR4Reader(port='COM4')
    reader.connect()
    reader.read_continuous(callback=on_tag_read)

Uso como CLI:
    python ur4_reader.py

Protocolo: Frame Header C8 8C + Length(2) + CMD(1) + Data + BCC(1) + Frame End 0D 0A
Compatível: Windows e Linux
"""

import serial
import serial.tools.list_ports
import time
import platform
import os
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, List

__version__ = '1.0.1'
__all__ = ['UR4Reader', 'detect_serial_port', 'list_serial_ports']

# Comandos UR4 (fixos)
CMD_START_INVENTORY = bytes([0xC8, 0x8C, 0x00, 0x0A, 0x82, 0x00, 0x00, 0x88, 0x0D, 0x0A])
CMD_STOP_INVENTORY = bytes([0xC8, 0x8C, 0x00, 0x08, 0x8C, 0x84, 0x0D, 0x0A])
CMD_GET_POWER = bytes([0xC8, 0x8C, 0x00, 0x08, 0x12, 0x1A, 0x0D, 0x0A])
CMD_GET_ANTENNA_CONFIG = bytes([0xC8, 0x8C, 0x00, 0x08, 0x2A, 0x22, 0x0D, 0x0A])
CMD_GET_MODULE_ID = bytes([0xC8, 0x8C, 0x00, 0x08, 0x04, 0x0C, 0x0D, 0x0A])

# Frame headers
FRAME_HEADER = (0xC8, 0x8C)

# Respostas
CMD_INVENTORY_RESPONSE = 0x83
CMD_POWER_RESPONSE = 0x13
CMD_ANTENNA_CONFIG_RESPONSE = 0x2B
CMD_MODULE_ID_RESPONSE = 0x05
CMD_SET_POWER_RESPONSE = 0x11
CMD_SET_ANTENNA_RESPONSE = 0x29


def detect_serial_port() -> Optional[str]:
    """
    Detecta automaticamente a porta serial do UR4
    
    Returns:
        str: Caminho da porta serial detectada ou None se não encontrada
    """
    system = platform.system()

    # Tenta porta configurada via udev rules (Linux)
    if system == "Linux" and os.path.exists('/dev/portal_rfid'):
        return '/dev/portal_rfid'

    # Lista todas as portas seriais disponíveis
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        return None

    # Prioriza portas com UR4/RFID no nome ou fabricante
    for port in ports:
        desc = (port.description + " " + (port.manufacturer or "")).lower()
        if any(keyword in desc for keyword in ['ur4', 'rfid', 'ch340', 'cp210', 'ftdi']):
            return port.device

    # Retorna a primeira porta encontrada
    if system == "Windows":
        # Prefere COMx menor (geralmente USB mais recente)
        return sorted([p.device for p in ports])[0]
    else:
        # Linux: prefere ttyUSB0 ou ttyACM0
        for pattern in ['ttyUSB', 'ttyACM']:
            for port in ports:
                if pattern in port.device:
                    return port.device
        return ports[0].device


def list_serial_ports() -> List[str]:
    """
    Lista todas as portas seriais disponíveis
    
    Returns:
        List[str]: Lista de caminhos de portas seriais
    """
    ports = serial.tools.list_ports.comports()
    return [p.device for p in ports]


class UR4Reader:
    """
    Classe principal para comunicação com leitor RFID UR4
    
    Attributes:
        port (str): Porta serial (ex: 'COM4' ou '/dev/ttyUSB0')
        baudrate (int): Taxa de transmissão (padrão: 115200)
        debug (bool): Ativa logs de debug
    """

    def __init__(self, port: str = 'COM4', baudrate: int = 115200, debug: bool = False):
        """Inicializa conexão com o leitor UR4"""
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        self.debug = debug
        self.is_reading = False
        self._io_lock = threading.RLock()  # Lock para coordenar I/O entre inventário e comandos

    def connect(self) -> bool:
        """
        Conecta ao UR4 via serial
        
        Returns:
            bool: True se conectado com sucesso, False caso contrário
        """
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1
            )
            if self.debug:
                print(f"[OK] Conectado: {self.port} @ {self.baudrate} baud")

            # Aguardar estabilização da conexão
            time.sleep(0.5)

            # Limpar buffers de entrada/saída
            if self.ser.in_waiting > 0:
                self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            if self.debug:
                print(f"[DEBUG] Buffers limpos, conexão estável")

            time.sleep(0.2)
            return True
        except serial.SerialException as e:
            if self.debug:
                print(f"[ERRO] Falha na conexão: {e}")
            return False

    def disconnect(self):
        """Fecha conexão serial"""
        self.is_reading = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            if self.debug:
                print("[INFO] Conexão fechada")

    def is_connected(self) -> bool:
        """Verifica se está conectado"""
        return self.ser is not None and self.ser.is_open
    
    def run_control_command(self, command: bytes, timeout: float = 1.0) -> Optional[bytes]:
        """
        Executa um comando de controle com exclusividade de I/O.
        Se estiver inventariando, pausa inventário, executa comando e retoma inventário.
        
        Args:
            command: Comando a enviar
            timeout: Tempo máximo de espera (segundos)
            
        Returns:
            Bytes da resposta ou None
        """
        if not self.is_connected():
            return None
        
        with self._io_lock:
            was_reading = self.is_reading
            if was_reading:
                # Para inventário para não "roubar" o RX
                self.send_command(CMD_STOP_INVENTORY)
                self.is_reading = False
                time.sleep(0.08)
                try:
                    if self.ser.in_waiting > 0:
                        self.ser.reset_input_buffer()
                except Exception:
                    pass
            
            try:
                resp = self.send_command_and_wait(command, timeout=timeout)
            finally:
                if was_reading:
                    # Retoma inventário
                    self.send_command(CMD_START_INVENTORY)
                    self.is_reading = True
                    time.sleep(0.05)
            
            return resp

    # ---------------------------
    # Frame utilities (interno)
    # ---------------------------
    @staticmethod
    def _calc_bcc_for_frame(frame: bytes) -> int:
        """
        Calcula BCC (XOR) para um frame completo:
        XOR de length(2) + cmd(1) + data(n), excluindo header(2), bcc(1) e end(2)
        frame = [H0 H1 L0 L1 CMD ... DATA ... BCC 0D 0A]
        """
        bcc = 0
        # do length até o último byte de data (antes do BCC)
        for b in frame[2:-3]:
            bcc ^= b
        return bcc

    def send_command_and_wait(self, command: bytes, timeout: float = 1.0) -> Optional[bytes]:
        """
        Envia comando e aguarda resposta (frame completo), com:
        - Length 16-bit (MSB+LSB)
        - Validação do trailer 0D 0A
        - Validação do BCC (XOR de length+cmd+data)
        """
        if not self.is_connected():
            return None

        if self.debug:
            print(f"[DEBUG] TX: {' '.join([f'{b:02X}' for b in command])}")

        self.ser.write(command)
        time.sleep(0.05)

        start_time = time.time()
        buffer = bytearray()

        while time.time() - start_time < timeout:
            if self.ser.in_waiting > 0:
                buffer.extend(self.ser.read(self.ser.in_waiting))

                # Alinha no header
                while len(buffer) >= 2 and not (buffer[0] == FRAME_HEADER[0] and buffer[1] == FRAME_HEADER[1]):
                    buffer.pop(0)

                # Precisa ter header + length
                if len(buffer) >= 4:
                    frame_length = (buffer[2] << 8) | buffer[3]

                    # Sanity check
                    if frame_length < 8 or frame_length > 4096:
                        buffer.pop(0)
                        continue

                    if len(buffer) >= frame_length:
                        frame = bytes(buffer[:frame_length])

                        # Valida trailer
                        if frame[-2:] != b"\x0D\x0A":
                            buffer.pop(0)
                            continue

                        # Valida BCC
                        bcc_recv = frame[-3]
                        bcc_calc = self._calc_bcc_for_frame(frame)
                        if bcc_calc != bcc_recv:
                            if self.debug:
                                print(f"[DEBUG] BCC inválido: calc=0x{bcc_calc:02X} recv=0x{bcc_recv:02X}")
                            buffer.pop(0)
                            continue

                        # OK
                        del buffer[:frame_length]
                        if self.debug:
                            print(f"[DEBUG] RX: {' '.join([f'{b:02X}' for b in frame])}")
                        return frame

            time.sleep(0.01)

        return None

    def send_command(self, command: bytes):
        """Envia comando para o UR4 (sem aguardar resposta)"""
        if self.ser and self.ser.is_open:
            if self.debug:
                print(f"[DEBUG] TX: {' '.join([f'{b:02X}' for b in command])}")
            self.ser.write(command)
            time.sleep(0.05)

    def start_inventory(self):
        """Inicia leitura contínua"""
        if self.debug:
            print("[INFO] Iniciando leitura contínua...")
        self.send_command(CMD_START_INVENTORY)
        self.is_reading = True

    def stop_inventory(self):
        """Para leitura contínua"""
        self.send_command(CMD_STOP_INVENTORY)
        self.is_reading = False
        if self.debug:
            print("[INFO] Leitura interrompida")

    def parse_tag_data(self, data: bytes) -> Optional[Dict[str, any]]:
        """
        Extrai EPC, antena e RSSI do frame de resposta
        
        Args:
            data: Bytes do frame recebido
            
        Returns:
            Dict com 'epc', 'antenna' e 'rssi' ou None se inválido
        """
        try:
            if self.debug:
                print(f"[DEBUG] RX: {' '.join([f'{b:02X}' for b in data])}")

            if len(data) < 13 or data[0] != FRAME_HEADER[0] or data[1] != FRAME_HEADER[1]:
                return None

            cmd_type = data[4]
            if cmd_type != CMD_INVENTORY_RESPONSE:
                return None

            # PC (Protocol Control) - 2 bytes
            pc = (data[5] << 8) | data[6]
            epc_len = ((pc >> 11) & 0x1F) * 2  # Tamanho EPC em bytes

            if len(data) < 7 + epc_len + 3:
                return None

            # EPC
            epc_bytes = data[7:7 + epc_len]
            epc = ''.join([f'{b:02X}' for b in epc_bytes])

            # RSSI (complemento de 2, dividido por 10)
            rssi_pos = 7 + epc_len
            rssi_raw = (data[rssi_pos] << 8) | data[rssi_pos + 1]
            if rssi_raw & 0x8000:
                rssi_raw -= 0x10000
            rssi_dbm = rssi_raw / 10.0

            # Antena
            antenna = data[rssi_pos + 2]

            return {'epc': epc, 'antenna': antenna, 'rssi': rssi_dbm}

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Erro no parse: {e}")
            return None

    def read_continuous(self, callback: Optional[Callable[[str, int, float], None]] = None,
                        anti_spam_delay: float = 0.3, print_output: bool = True):
        """
        Loop principal de leitura contínua
        """
        if not self.is_connected():
            if self.debug:
                print("[ERRO] Sem conexão ativa")
            return

        self.start_inventory()

        if print_output:
            print("[OK] Aguardando tags...")
            print("-" * 80)
            print(f"{'Horário':<12} | {'EPC':<40} | {'Ant':<3} | {'RSSI (dBm)':<10}")
            print("-" * 80)

        buffer = bytearray()
        tags_seen = {}

        try:
            while self.is_reading:
                with self._io_lock:
                    if self.ser.in_waiting > 0:
                        buffer.extend(self.ser.read(self.ser.in_waiting))

                    # Processa frames completos
                    while len(buffer) >= 10:
                        # Alinha no header
                        while len(buffer) >= 2 and not (buffer[0] == FRAME_HEADER[0] and buffer[1] == FRAME_HEADER[1]):
                            buffer.pop(0)

                        if len(buffer) < 4:
                            break

                        frame_length = (buffer[2] << 8) | buffer[3]
                        if frame_length < 8 or frame_length > 4096:
                            buffer.pop(0)
                            continue

                        if len(buffer) < frame_length:
                            break

                        frame = bytes(buffer[:frame_length])
                        del buffer[:frame_length]

                        # Validação mínima do frame
                        if frame[-2:] != b"\x0D\x0A":
                            continue
                        bcc_recv = frame[-3]
                        bcc_calc = self._calc_bcc_for_frame(frame)
                        if bcc_calc != bcc_recv:
                            if self.debug:
                                print(f"[DEBUG] Frame descartado (BCC inválido): calc=0x{bcc_calc:02X} recv=0x{bcc_recv:02X}")
                            continue

                        tag_info = self.parse_tag_data(frame)
                        if tag_info:
                            epc = tag_info['epc']
                            antenna = tag_info['antenna']
                            rssi = tag_info['rssi']
                            current_time = time.time()

                            # Anti-spam
                            if epc not in tags_seen or (current_time - tags_seen[epc]) > anti_spam_delay:
                                if callback:
                                    callback(epc, antenna, rssi)

                                if print_output:
                                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                                    print(f"{timestamp:<12} | {epc:<40} | {antenna:<3} | {rssi:<10.1f}")

                                tags_seen[epc] = current_time

                time.sleep(0.01)

        except KeyboardInterrupt:
            if print_output:
                print("\n[INFO] Interrompido pelo usuário")
        finally:
            self.stop_inventory()

    def read_single(self, timeout: float = 5.0) -> Optional[Dict[str, any]]:
        """
        Lê uma única tag (bloqueante)
        """
        if not self.is_connected():
            return None

        self.start_inventory()
        buffer = bytearray()
        start_time = time.time()

        try:
            while time.time() - start_time < timeout:
                with self._io_lock:
                    if self.ser.in_waiting > 0:
                        buffer.extend(self.ser.read(self.ser.in_waiting))

                    while len(buffer) >= 10:
                        # Alinha no header
                        while len(buffer) >= 2 and not (buffer[0] == FRAME_HEADER[0] and buffer[1] == FRAME_HEADER[1]):
                            buffer.pop(0)

                        if len(buffer) < 4:
                            break

                        frame_length = (buffer[2] << 8) | buffer[3]
                        if frame_length < 8 or frame_length > 4096:
                            buffer.pop(0)
                            continue

                        if len(buffer) < frame_length:
                            break

                        frame = bytes(buffer[:frame_length])
                        del buffer[:frame_length]

                        # Validação mínima
                        if frame[-2:] != b"\x0D\x0A":
                            continue
                        bcc_recv = frame[-3]
                        bcc_calc = self._calc_bcc_for_frame(frame)
                        if bcc_calc != bcc_recv:
                            continue

                        tag_info = self.parse_tag_data(frame)
                        if tag_info:
                            self.stop_inventory()
                            return tag_info

                time.sleep(0.01)
        finally:
            self.stop_inventory()

        return None

    def get_antenna_power(self) -> Optional[Dict[int, Dict[str, float]]]:
        """
        Obtém a potência de transmissão de cada antena
        """
        if self.debug:
            print(f"[DEBUG] Enviando comando CMD_GET_POWER...")

        response = self.run_control_command(CMD_GET_POWER, timeout=1.0)

        if self.debug:
            print(f"[DEBUG] Resposta recebida: {response}")
            if response:
                print(f"[DEBUG] Tamanho resposta: {len(response)}")
                print(f"[DEBUG] Resposta hex: {' '.join(f'{b:02X}' for b in response)}")

        if not response or len(response) < 10:
            if self.debug:
                print(f"[DEBUG] Resposta inválida (None ou muito curta)")
            return None

        if response[4] != CMD_POWER_RESPONSE:
            if self.debug:
                print(f"[DEBUG] Comando de resposta incorreto: esperado 0x{CMD_POWER_RESPONSE:02X}, recebido 0x{response[4]:02X}")
            return None

        try:
            antenna_powers = {}
            status = response[5]
            idx = 6

            if self.debug:
                print(f"[DEBUG] Status da resposta: 0x{status:02X}")
                print(f"[DEBUG] Iniciando parse das potências a partir do índice {idx}")
                print(f"[DEBUG] Bytes disponíveis para parse: {len(response) - idx - 3} (total: {len(response)}, inicio: {idx}, reserva fim: 3)")

            # Cada antena: 1 byte número + 2 bytes read + 2 bytes write
            while idx + 5 <= len(response) - 3:  # -3 para BCC e end
                antenna_num = response[idx]
                read_power_raw = (response[idx + 1] << 8) | response[idx + 2]
                write_power_raw = (response[idx + 3] << 8) | response[idx + 4]

                antenna_powers[antenna_num] = {
                    'read_power': read_power_raw / 100.0,
                    'write_power': write_power_raw / 100.0
                }

                if self.debug:
                    print(f"[DEBUG] Antena {antenna_num}: read={read_power_raw/100.0} dBm, write={write_power_raw/100.0} dBm")

                idx += 5

            if self.debug:
                print(f"[DEBUG] Total de antenas encontradas: {len(antenna_powers)}")
                if len(antenna_powers) == 0 and status == 0x00:
                    print(f"[DEBUG] ⚠️ Resposta válida mas sem dados de potência - dispositivo pode não ter potências configuradas")

            return antenna_powers if antenna_powers else None

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Erro ao processar potências: {e}")
                import traceback
                traceback.print_exc()
            return None

    def get_active_antennas(self) -> Optional[List[int]]:
        """
        Obtém lista de antenas ativas/configuradas
        """
        response = self.run_control_command(CMD_GET_ANTENNA_CONFIG, timeout=1.0)

        if not response or len(response) < 10:
            return None

        if response[4] != CMD_ANTENNA_CONFIG_RESPONSE:
            return None

        try:
            dbyte1 = response[5]
            dbyte0 = response[6]
            antenna_bits = (dbyte1 << 8) | dbyte0

            active_antennas = []
            for i in range(16):
                if antenna_bits & (1 << i):
                    active_antennas.append(i + 1)

            return active_antennas

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Erro ao processar antenas: {e}")
            return None

    def get_serial_number(self) -> Optional[str]:
        """
        Obtém o número de série do módulo UR4
        """
        response = self.run_control_command(CMD_GET_MODULE_ID, timeout=1.0)

        if not response or len(response) < 12:
            return None

        if response[4] != CMD_MODULE_ID_RESPONSE:
            return None

        try:
            if self.debug:
                print(f"[DEBUG] Resposta get_serial_number (hex): {response.hex()}")
                print(f"[DEBUG] Bytes 5-8: {[f'{response[i]:02X}' for i in range(5, 9)]}")

            module_id = ''.join([f'{response[i]:02X}' for i in range(5, 9)])

            if self.debug:
                print(f"[DEBUG] Serial Number extraído: {module_id}")

            return module_id

        except Exception as e:
            if self.debug:
                print(f"[DEBUG] Erro ao obter número de série: {e}")
            return None

    def set_antenna_power(self, antenna: int, read_power: float, write_power: float,
                         save: bool = False) -> bool:
        """
        Configura a potência de leitura e escrita de uma antena específica
        """
        if not self.is_connected():
            return False

        if not (1 <= antenna <= 16):
            if self.debug:
                print("[ERRO] Número de antena inválido (1-16)")
            return False

        if not (0.0 <= read_power <= 33.0) or not (0.0 <= write_power <= 33.0):
            if self.debug:
                print("[ERRO] Potência deve estar entre 0.0 e 33.0 dBm")
            return False

        # Status byte: bit1=1 para salvar, bit1=0 para não salvar
        status = 0x02 if save else 0x00

        # Converte potências (dBm * 100) com arredondamento
        read_power_raw = int(round(read_power * 100))
        write_power_raw = int(round(write_power * 100))

        # Data: Status, Antenna, Read_MSB, Read_LSB, Write_MSB, Write_LSB
        data = bytearray([
            status,
            antenna,
            (read_power_raw >> 8) & 0xFF,
            read_power_raw & 0xFF,
            (write_power_raw >> 8) & 0xFF,
            write_power_raw & 0xFF
        ])

        # Frame length = header(2) + len(2) + cmd(1) + data + bcc(1) + end(2)
        frame_len = 2 + 2 + 1 + len(data) + 1 + 2

        command = bytearray([
            0xC8, 0x8C,
            (frame_len >> 8) & 0xFF, frame_len & 0xFF,  # MSB, LSB corretos
            0x10
        ])
        command.extend(data)

        # BCC: XOR de tudo após header (length + cmd + data)
        bcc = 0
        for b in command[2:]:
            bcc ^= b
        command.append(bcc)

        command.extend([0x0D, 0x0A])

        if self.debug:
            print(f"[DEBUG] Configurando potência da antena {antenna}: R={read_power}dBm W={write_power}dBm")
            print(f"[DEBUG] Frame length calculado: {frame_len} bytes")
            print(f"[DEBUG] Comando: {' '.join(f'{b:02X}' for b in command)}")
            print(f"[DEBUG] BCC calculado: 0x{bcc:02X}")

        response = self.run_control_command(bytes(command), timeout=1.0)

        if self.debug:
            if response:
                print(f"[DEBUG] Resposta set_power: {' '.join(f'{b:02X}' for b in response)}")
            else:
                print(f"[DEBUG] Sem resposta do set_power")

        if not response or len(response) < 9:
            return False

        # Verifica resposta de sucesso (0x01 = sucesso)
        if response[4] == CMD_SET_POWER_RESPONSE and response[5] == 0x01:
            if self.debug:
                print(f"[OK] Potência da antena {antenna} configurada com sucesso!")
            return True

        return False

    def set_active_antennas(self, antennas: List[int], save: bool = False) -> bool:
        """
        Configura quais antenas devem estar ativas
        """
        if not self.is_connected():
            return False

        if not antennas or not all(1 <= ant <= 16 for ant in antennas):
            if self.debug:
                print("[ERRO] Números de antena inválidos (1-16)")
            return False

        # DByte2: 0x01 para salvar, 0x00 para não salvar
        dbyte2 = 0x01 if save else 0x00

        # Bits representando antenas (bit0=ant1, bit1=ant2, etc)
        antenna_bits = 0
        for ant in antennas:
            antenna_bits |= (1 << (ant - 1))

        dbyte1 = (antenna_bits >> 8) & 0xFF
        dbyte0 = antenna_bits & 0xFF

        # Monta comando (mantido)
        command = bytearray([
            0xC8, 0x8C,  # Header
            0x00, 0x0B,  # Length
            0x28,        # CMD
            dbyte2,
            dbyte1,
            dbyte0
        ])

        # BCC (já correto)
        bcc = 0
        for b in command[2:]:
            bcc ^= b
        command.append(bcc)

        command.extend([0x0D, 0x0A])

        response = self.run_control_command(bytes(command), timeout=1.0)

        if not response or len(response) < 9:
            return False

        if response[4] == CMD_SET_ANTENNA_RESPONSE and response[5] == 0x01:
            if self.debug:
                print(f"[OK] Antenas configuradas: {antennas}")
            return True

        return False

    def get_reader_info(self) -> Dict[str, any]:
        """
        Obtém informações completas do leitor
        """
        info = {
            'connected': self.is_connected(),
            'port': self.port,
            'baudrate': self.baudrate,
            'serial_number': None,
            'firmware_version': 'N/A',
            'hardware_version': 'UR4 RFID Reader',
            'work_mode': 'Active Mode',
            'active_antennas': [],
            'antenna_count': 0,
            'antenna_powers': {}
        }

        if not self.is_connected():
            return info

        serial_num = self.get_serial_number()
        if serial_num:
            info['serial_number'] = serial_num

        powers = self.get_antenna_power()
        if powers:
            info['antenna_powers'] = powers
            info['active_antennas'] = sorted(list(powers.keys()))
            info['antenna_count'] = len(powers)
        else:
            antennas = self.get_active_antennas()
            if antennas:
                physical_antennas = [a for a in antennas if 1 <= a <= 8]
                info['active_antennas'] = physical_antennas
                info['antenna_count'] = len(physical_antennas)

        return info


def _print_serial_ports():
    """Imprime lista de portas seriais (uso interno CLI)"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("❌ Nenhuma porta serial encontrada")
        return []

    print("\n📋 Portas seriais disponíveis:")
    for i, port in enumerate(ports, 1):
        print(f"   {i}. {port.device} - {port.description}")
    return [p.device for p in ports]


def main():
    """Função principal da CLI"""
    system = platform.system()
    print("=" * 70)
    print("       LEITOR RFID UR4 - Monitor de Tags em Tempo Real")
    print("=" * 70)
    print(f"🖥️  Sistema: {system}")
    print()

    auto_port = detect_serial_port()

    if auto_port:
        print(f"✅ Porta detectada: {auto_port}")
        port_input = input(f"Usar esta porta? (S/n): ").strip().lower()

        if port_input == 'n':
            available_ports = _print_serial_ports()
            if available_ports:
                port = input("\nDigite a porta desejada: ").strip() or available_ports[0]
            else:
                print("❌ Nenhuma porta disponível")
                return
        else:
            port = auto_port
    else:
        print("⚠️  Nenhuma porta detectada automaticamente")
        available_ports = _print_serial_ports()
        if available_ports:
            port = input("\nDigite a porta desejada: ").strip() or available_ports[0]
        else:
            print("❌ Nenhuma porta disponível")
            return

    debug = input("Modo DEBUG? (s/N): ").strip().lower() == 's'

    reader = UR4Reader(port=port, baudrate=115200, debug=debug)

    if reader.connect():
        print("\n[INFO] Pressione Ctrl+C para parar\n")
        time.sleep(1)
        reader.read_continuous()
        reader.disconnect()
    else:
        print("\n[ERRO] Falha na conexão")
        print("Verifique: porta COM, conexão física, drivers")


if __name__ == "__main__":
    main()
