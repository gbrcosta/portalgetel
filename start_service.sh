#!/bin/bash
# Script simplificado para systemd

cd /home/getel/Documentos/portalgetel

# Limpar PIDs antigos
rm -f logs/system.pid logs/api.pid logs/rfid.pid

# Ativar ambiente virtual
source venv/bin/activate

# Criar diretório de logs
mkdir -p logs

# Iniciar API
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/api.log 2>&1 &
API_PID=$!
echo $API_PID > ../logs/api.pid
cd ..

# Aguardar API inicializar
sleep 3

# Iniciar leitor RFID
cd scripts
nohup python3 ur4_rfid_serial.py --port /dev/portal_rfid > ../logs/rfid.log 2>&1 &
RFID_PID=$!
echo $RFID_PID > ../logs/rfid.pid
cd ..

# Salvar PIDs no arquivo principal
echo $API_PID > logs/system.pid
echo $RFID_PID >> logs/system.pid

echo "Sistema iniciado - API: $API_PID, RFID: $RFID_PID"

# Manter o script rodando
tail -f /dev/null
