#!/bin/bash

# ============================================
# Portal RFID - Biamar UR4
# Script de Parada para Ubuntu
# ============================================

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

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
echo -e "${BLUE}Parando Sistema...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verificar se existe arquivo de PID
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  Sistema não está em execução (arquivo PID não encontrado)${NC}"
    
    # Tentar encontrar processos manualmente
    echo "Procurando processos manualmente..."
    
    # Matar processos Python relacionados
    pkill -f "main.py" 2>/dev/null && echo "  ✓ API parada"
    pkill -f "ur4_rfid_reader.py" 2>/dev/null && echo "  ✓ Leitor RFID parado"
    
    # Fechar Chrome em modo kiosk
    pkill -f "chrome.*kiosk" 2>/dev/null && echo "  ✓ Chrome fechado"
    pkill -f "chromium.*kiosk" 2>/dev/null
    
    echo ""
    echo -e "${GREEN}✓ Limpeza concluída${NC}"
    exit 0
fi

# Ler PIDs do arquivo
echo -e "${YELLOW}📋 Lendo PIDs...${NC}"
PIDS=($(cat "$PID_FILE"))

# Parar cada processo
for PID in "${PIDS[@]}"; do
    if ps -p $PID > /dev/null 2>&1; then
        echo "  Parando processo PID: $PID"
        kill $PID 2>/dev/null
        
        # Aguardar processo terminar
        for i in {1..5}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                echo -e "    ${GREEN}✓ Processo $PID parado${NC}"
                break
            fi
            sleep 1
            
            # Se não parou após 5 segundos, força parada
            if [ $i -eq 5 ]; then
                echo -e "    ${YELLOW}⚠️  Forçando parada do processo $PID${NC}"
                kill -9 $PID 2>/dev/null
            fi
        done
    else
        echo -e "    ${YELLOW}⚠️  Processo $PID já não está rodando${NC}"
    fi
done

# Remover arquivo de PID
rm -f "$PID_FILE"

# Garantir que todos os processos foram parados
echo ""
echo -e "${YELLOW}🧹 Limpando processos restantes...${NC}"

# Matar processos relacionados
pkill -f "backend/main.py" 2>/dev/null
pkill -f "ur4_rfid_reader.py" 2>/dev/null
pkill -f "chrome.*kiosk.*index.html" 2>/dev/null
pkill -f "chromium.*kiosk.*index.html" 2>/dev/null

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ Sistema parado com sucesso!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Para iniciar novamente, execute:"
echo "  bash start_ubuntu.sh"
echo ""
