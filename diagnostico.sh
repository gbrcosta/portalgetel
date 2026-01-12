#!/bin/bash
# Script de diagnóstico do sistema

echo "🔍 DIAGNÓSTICO DO SISTEMA - Portal RFID Biamar"
echo "=" * 60

# Verificar ambiente Python
echo ""
echo "🐍 PYTHON:"
python3 --version
which python3

# Verificar ambiente virtual
echo ""
echo "📦 AMBIENTE VIRTUAL:"
if [ -d "venv" ]; then
    echo "   ✅ venv/ existe"
    if [ -f "venv/bin/python3" ]; then
        echo "   ✅ Python no venv funcional"
    else
        echo "   ❌ Python no venv não encontrado"
    fi
else
    echo "   ❌ venv/ não existe"
fi

# Verificar dependências
echo ""
echo "📚 DEPENDÊNCIAS:"
if [ -f "requirements.txt" ]; then
    echo "   ✅ requirements.txt encontrado"
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "   Instaladas:"
        pip list | grep -E "fastapi|uvicorn|sqlalchemy|pyserial|requests"
        deactivate
    fi
else
    echo "   ❌ requirements.txt não encontrado"
fi

# Verificar diretórios
echo ""
echo "📁 ESTRUTURA DE DIRETÓRIOS:"
for dir in "backend" "frontend" "scripts" "database" "logs"; do
    if [ -d "$dir" ]; then
        echo "   ✅ $dir/"
    else
        echo "   ❌ $dir/ - FALTANDO"
    fi
done

# Verificar arquivos essenciais
echo ""
echo "📄 ARQUIVOS ESSENCIAIS:"
for file in "backend/main.py" "backend/models.py" "config.py" "frontend/index.html"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file - FALTANDO"
    fi
done

# Verificar banco de dados
echo ""
echo "💾 BANCO DE DADOS:"
if [ -f "database/rfid_portal.db" ]; then
    echo "   ✅ database/rfid_portal.db existe"
    echo "   Tamanho: $(du -h database/rfid_portal.db | cut -f1)"
else
    echo "   ⚠️  database/rfid_portal.db não existe (será criado ao iniciar)"
fi

# Verificar processos rodando
echo ""
echo "⚙️  PROCESSOS:"
if pgrep -f "main.py" > /dev/null; then
    echo "   🟢 API está rodando (PID: $(pgrep -f "main.py"))"
else
    echo "   🔴 API não está rodando"
fi

if pgrep -f "ur4_rfid" > /dev/null; then
    echo "   🟢 Leitor RFID está rodando (PID: $(pgrep -f "ur4_rfid"))"
else
    echo "   🔴 Leitor RFID não está rodando"
fi

# Verificar portas
echo ""
echo "🔌 PORTAS:"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   🟢 Porta 8000 em uso"
    lsof -i :8000 | grep LISTEN
else
    echo "   🔴 Porta 8000 livre"
fi

# Verificar porta serial
echo ""
echo "📡 PORTA SERIAL:"
if [ -e "/dev/ttyUSB0" ]; then
    echo "   ✅ /dev/ttyUSB0 encontrada"
    ls -la /dev/ttyUSB0
else
    echo "   ⚠️  /dev/ttyUSB0 não encontrada"
fi

# Verificar grupo dialout
echo ""
echo "👥 PERMISSÕES:"
if groups | grep -q dialout; then
    echo "   ✅ Usuário no grupo dialout"
else
    echo "   ⚠️  Usuário NÃO está no grupo dialout"
    echo "      Execute: sudo usermod -a -G dialout $USER"
fi

# Verificar logs
echo ""
echo "📋 LOGS:"
for log in "logs/api.log" "logs/rfid.log"; do
    if [ -f "$log" ]; then
        lines=$(wc -l < "$log")
        size=$(du -h "$log" | cut -f1)
        echo "   ✅ $log ($lines linhas, $size)"
    else
        echo "   ⚠️  $log não existe"
    fi
done

# Resumo
echo ""
echo "=" * 60
echo "📊 RESUMO:"

errors=0
warnings=0

[ ! -d "venv" ] && ((errors++))
[ ! -d "database" ] && ((warnings++))
[ ! -f "database/rfid_portal.db" ] && ((warnings++))
! groups | grep -q dialout && ((warnings++))

if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo "   ✅ Sistema OK - Pronto para usar!"
elif [ $errors -eq 0 ]; then
    echo "   ⚠️  Sistema funcional com $warnings avisos"
else
    echo "   ❌ Sistema com $errors erros - Execute install_ubuntu.sh"
fi

echo "=" * 60
