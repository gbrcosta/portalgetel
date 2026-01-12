#!/bin/bash

# ============================================
# Portal RFID - Biamar UR4
# Script de Inicialização para Ubuntu
# ============================================

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Criar diretório de logs se não existir
mkdir -p logs

# Arquivo de PID
PID_FILE="$SCRIPT_DIR/logs/system.pid"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}Portal RFID - Biamar UR4${NC}"
echo -e "${BLUE}Iniciando Sistema...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verificar se já está rodando
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  Sistema já está em execução!${NC}"
    echo "Para parar, execute: bash stop_ubuntu.sh"
    exit 1
fi

# Ativar ambiente virtual
echo -e "${GREEN}🐍 Ativando ambiente Python...${NC}"
source venv/bin/activate

# Verificar se ambiente virtual foi ativado
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Erro: Ambiente virtual não encontrado!${NC}"
    echo "Execute primeiro: bash install_ubuntu.sh"
    exit 1
fi

# Verificar se porta 8000 já está em uso
echo -e "${BLUE}🔍 Verificando porta 8000...${NC}"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Porta 8000 já está em uso!${NC}"
    echo "Encerrando processo anterior..."
    sudo kill -9 $(lsof -t -i:8000) 2>/dev/null || true
    sleep 2
fi

# Iniciar API Backend
echo -e "${GREEN}🚀 Iniciando API Backend...${NC}"
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 > ../logs/api.log 2>&1 &
API_PID=$!
cd ..
echo "  ✓ API iniciada (PID: $API_PID)"
echo "  📄 Log: logs/api.log"
sleep 3

# Verificar se API está rodando
if ! ps -p $API_PID > /dev/null; then
    echo -e "${RED}❌ Erro ao iniciar API!${NC}"
    echo "Últimas linhas do log:"
    tail -n 20 logs/api.log
    exit 1
fi

# Iniciar Leitor RFID
echo ""
echo -e "${GREEN}📡 Iniciando Leitor RFID (Conexão Serial)...${NC}"

# Verificar se porta serial existe
if [ -e "/dev/ttyUSB0" ]; then
    echo "  ✓ Porta /dev/ttyUSB0 encontrada"
    cd scripts
    python3 ur4_rfid_serial.py > ../logs/rfid.log 2>&1 &
    RFID_PID=$!
    cd ..
    echo "  ✓ Leitor RFID Serial iniciado (PID: $RFID_PID)"
else
    echo -e "${YELLOW}  ⚠️  Porta /dev/ttyUSB0 não encontrada${NC}"
    echo "  Tentando modo socket (UR4 via rede)..."
    cd scripts
    python3 ur4_rfid_reader.py > ../logs/rfid.log 2>&1 &
    RFID_PID=$!
    cd ..
    echo "  ✓ Leitor RFID Socket iniciado (PID: $RFID_PID)"
fi
echo "  📄 Log: logs/rfid.log"
sleep 2

# Verificar se Leitor RFID está rodando
if ! ps -p $RFID_PID > /dev/null; then
    echo -e "${YELLOW}⚠️  Aviso: Leitor RFID não iniciou (modo simulação será usado)${NC}"
    echo "Verifique o log em: logs/rfid.log"
fi

# Salvar PIDs
echo "$API_PID" > "$PID_FILE"
echo "$RFID_PID" >> "$PID_FILE"

# Aguardar API estar pronta
echo ""
echo -e "${BLUE}⏳ Aguardando API ficar online...${NC}"
API_READY=false
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ API está online!${NC}"
        API_READY=true
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

if [ "$API_READY" = false ]; then
    echo -e "${RED}❌ Timeout: API não respondeu após 30 segundos${NC}"
    echo "Últimas linhas do log:"
    tail -n 30 logs/api.log
    echo ""
    echo -e "${YELLOW}Deseja continuar mesmo assim? (s/N)${NC}"
    read -t 5 -n 1 response || response="n"
    echo ""
    if [[ ! $response =~ ^[Ss]$ ]]; then
        bash stop_ubuntu.sh
        exit 1
    fi
fi

# Abrir Chrome em tela cheia
echo ""
echo -e "${GREEN}🌐 Abrindo dashboard no Chrome...${NC}"

# Caminho completo do arquivo HTML
DASHBOARD_PATH="file://$SCRIPT_DIR/frontend/index.html"

# Tentar diferentes comandos para abrir Chrome
if command -v google-chrome &> /dev/null; then
    # Chrome instalado
    google-chrome --kiosk --app="$DASHBOARD_PATH" > /dev/null 2>&1 &
    CHROME_PID=$!
    echo "$CHROME_PID" >> "$PID_FILE"
    echo -e "  ✓ Chrome aberto em modo kiosk (PID: $CHROME_PID)"
elif command -v chromium-browser &> /dev/null; then
    # Chromium instalado
    chromium-browser --kiosk --app="$DASHBOARD_PATH" > /dev/null 2>&1 &
    CHROME_PID=$!
    echo "$CHROME_PID" >> "$PID_FILE"
    echo -e "  ✓ Chromium aberto em modo kiosk (PID: $CHROME_PID)"
else
    echo -e "${YELLOW}⚠️  Chrome não encontrado. Abra manualmente:${NC}"
    echo "  $DASHBOARD_PATH"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ Sistema iniciado com sucesso!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${YELLOW}URLs de acesso:${NC}"
echo "  📊 Dashboard: $DASHBOARD_PATH"
echo "  🔌 API: http://localhost:8000"
echo "  📖 Docs API: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Logs do sistema:${NC}"
echo "  API: logs/api.log"
echo "  RFID: logs/rfid.log"
echo ""
echo -e "${YELLOW}Para parar o sistema:${NC}"
echo "  bash stop_ubuntu.sh"
echo ""
echo -e "${YELLOW}Para visualizar logs em tempo real:${NC}"
echo "  tail -f logs/api.log"
echo "  tail -f logs/rfid.log"
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Sistema rodando em background!${NC}"
echo -e "${BLUE}============================================${NC}"
