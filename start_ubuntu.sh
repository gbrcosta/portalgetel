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

# Aguardar um pouco mais para garantir que a API iniciou
echo "  ⏳ Aguardando API inicializar..."
sleep 5

# Verificar se API está rodando
if ! ps -p $API_PID > /dev/null; then
    echo -e "${RED}❌ Erro ao iniciar API!${NC}"
    echo "Últimas linhas do log:"
    tail -n 20 logs/api.log
    exit 1
fi

echo "  ✓ Processo da API está ativo"

# Iniciar Leitor RFID
echo ""
echo -e "${GREEN}📡 Iniciando Leitor RFID (Conexão Serial)...${NC}"

# Verificar se porta serial existe
# Detectar porta serial: preferir symlink /dev/portal_rfid, senão ttyUSB*, ttyACM*
detect_serial() {
    if [ -e "/dev/portal_rfid" ]; then
        echo "/dev/portal_rfid"
        return
    fi
    if ls /dev/ttyUSB* >/dev/null 2>&1; then
        for f in /dev/ttyUSB*; do
            [ -c "$f" ] && { echo "$f"; return; }
        done
    fi
    if ls /dev/ttyACM* >/dev/null 2>&1; then
        for f in /dev/ttyACM*; do
            [ -c "$f" ] && { echo "$f"; return; }
        done
    fi
    # fallback
    echo "/dev/ttyUSB0"
}

PORTA_SERIAL=$(detect_serial)
echo "  ✓ Porta serial selecionada: $PORTA_SERIAL"
cd scripts
python3 ur4_rfid_serial.py --port "$PORTA_SERIAL" > ../logs/rfid.log 2>&1 &
RFID_PID=$!
cd ..
echo "  ✓ Leitor RFID Serial iniciado (PID: $RFID_PID)"
echo "  📄 Log: logs/rfid.log"
sleep 2
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
API_READY=false

# Tentar diferentes endpoints
for i in {1..20}; do
    # Tentar endpoint raiz primeiro
    if curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ API está online e respondendo!${NC}"
        API_READY=true
        break
    fi
    
    # Mostrar progresso
    if [ $((i % 5)) -eq 0 ]; then
        echo "  Tentativa $i/20..."
    fi
    sleep 1
done

if [ "$API_READY" = false ]; then
    echo -e "${YELLOW}⚠️  API não respondeu aos testes de conexão${NC}"
    echo ""
    echo "Verificando log da API:"
    echo "----------------------------------------"
    tail -n 20 logs/api.log
    echo "----------------------------------------"
    echo ""
    echo -e "${YELLOW}A API pode estar funcionando mesmo assim.${NC}"
    echo -e "${YELLOW}Continuando com a inicialização...${NC}"
    echo ""
    sleep 2
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
echo -e "${GREEN}✅ Sistema iniciado!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${YELLOW}URLs de acesso:${NC}"
echo "  📊 Dashboard: $DASHBOARD_PATH"
echo "  🔌 API: http://localhost:8000"
echo "  ❤️  Health: http://localhost:8000/health"
echo "  📖 Docs API: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Processos em execução:${NC}"
echo "  API Backend: PID $API_PID"
echo "  RFID Reader: PID $RFID_PID"
[ ! -z "$CHROME_PID" ] && echo "  Chrome: PID $CHROME_PID"
echo ""
echo -e "${YELLOW}Comandos úteis:${NC}"
echo "  Parar sistema: bash stop_ubuntu.sh"
echo "  Ver log API: tail -f logs/api.log"
echo "  Ver log RFID: tail -f logs/rfid.log"
echo "  Testar API: bash test_api.sh"
echo "  Diagnóstico: bash diagnostico.sh"
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Sistema rodando em background!${NC}"
echo -e "${BLUE}============================================${NC}"
