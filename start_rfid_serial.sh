#!/bin/bash
# Script para iniciar o leitor RFID no Ubuntu
# Execute como: bash start_rfid_serial.sh

echo "🚀 Iniciando Portal RFID Biamar (Conexão Serial)"
echo "================================================"

# Verificar se está no diretório correto
if [ ! -f "scripts/ur4_rfid_serial.py" ]; then
    echo "❌ Erro: Execute este script do diretório raiz do projeto"
    exit 1
fi

# Verificar permissões de porta serial
if ! groups | grep -q dialout; then
    echo "⚠️  AVISO: Usuário não está no grupo 'dialout'"
    echo "   Execute: sudo usermod -a -G dialout $USER"
    echo "   Depois faça logout/login para aplicar as permissões"
    echo ""
fi

# Verificar se a porta serial existe
if [ ! -e "/dev/ttyUSB0" ]; then
    echo "⚠️  AVISO: Porta /dev/ttyUSB0 não encontrada"
    echo "   Verifique se o UR4 está conectado"
    echo "   Use: ls -la /dev/ttyUSB*"
    echo ""
fi

# Ativar ambiente virtual (se existir)
if [ -d ".venv" ]; then
    echo "📦 Ativando ambiente virtual..."
    source .venv/bin/activate
else
    echo "⚠️  Ambiente virtual não encontrado (.venv)"
    echo "   Crie com: python3 -m venv .venv"
    echo "   Instale deps: .venv/bin/pip install -r requirements.txt"
    echo ""
fi

# Verificar se pyserial está instalado
if ! python3 -c "import serial" 2>/dev/null; then
    echo "❌ Erro: pyserial não está instalado"
    echo "   Instale com: pip install pyserial"
    exit 1
fi

echo ""
echo "🔄 Iniciando monitoramento RFID..."
echo "   Pressione Ctrl+C para parar"
echo ""

# Executar o script
python3 scripts/ur4_rfid_serial.py
