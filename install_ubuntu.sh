#!/bin/bash

# ============================================
# Portal RFID - Biamar UR4
# Script de Instalação para Ubuntu
# ============================================

echo "============================================"
echo "Portal RFID - Biamar UR4"
echo "Instalação para Ubuntu/Linux"
echo "============================================"
echo ""

# Verificar se está executando como root ou com sudo
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Não execute este script como root!"
   echo "Execute: bash install_ubuntu.sh"
   exit 1
fi

# Atualizar repositórios
echo "📦 Atualizando repositórios do sistema..."
sudo apt update

# Instalar Python 3 e pip
echo ""
echo "🐍 Verificando instalação do Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "Instalando Python 3..."
    sudo apt install -y python3 python3-pip python3-venv
else
    echo "✓ Python 3 já instalado: $(python3 --version)"
fi

# Instalar pip se necessário
if ! command -v pip3 &> /dev/null; then
    echo "Instalando pip..."
    sudo apt install -y python3-pip
fi

# Instalar Google Chrome (se não estiver instalado)
echo ""
echo "🌐 Verificando instalação do Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    echo "Instalando Google Chrome..."
    
    # Baixar e instalar Chrome
    wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt install -y /tmp/google-chrome.deb
    rm /tmp/google-chrome.deb
    
    echo "✓ Google Chrome instalado com sucesso!"
else
    echo "✓ Google Chrome já instalado"
fi

# Criar ambiente virtual Python
echo ""
echo "🔧 Criando ambiente virtual Python..."
python3 -m venv venv

# Ativar ambiente virtual e instalar dependências
echo "📚 Instalando dependências Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Dependências instaladas com sucesso!"

# Criar diretório de logs
mkdir -p logs

# Tornar scripts executáveis
echo ""
echo "🔐 Configurando permissões dos scripts..."
chmod +x start_ubuntu.sh
chmod +x stop_ubuntu.sh
chmod +x install_ubuntu.sh

# Inicializar banco de dados
echo ""
echo "💾 Inicializando banco de dados..."
source venv/bin/activate
python3 -c "from backend.models import init_db; init_db()"

echo ""
echo "============================================"
echo "✅ Instalação concluída com sucesso!"
echo "============================================"
echo ""
echo "Para iniciar o sistema, execute:"
echo "  bash start_ubuntu.sh"
echo ""
echo "Para parar o sistema, execute:"
echo "  bash stop_ubuntu.sh"
echo ""
echo "O sistema irá:"
echo "  1. Iniciar a API (backend)"
echo "  2. Iniciar o leitor RFID"
echo "  3. Abrir o dashboard no Chrome em tela cheia"
echo ""
echo "Pressione Ctrl+C para encerrar"
echo "============================================"
