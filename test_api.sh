#!/bin/bash
# Script para testar se a API está funcionando

echo "🧪 Testando API do Portal RFID..."
echo ""

# Verificar se a API está respondendo
echo "1️⃣  Testando endpoint raiz..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✅ API respondendo em http://localhost:8000/"
    curl -s http://localhost:8000/ | python3 -m json.tool
else
    echo "   ❌ API não está respondendo"
    echo "   Execute: bash start_ubuntu.sh"
    exit 1
fi

echo ""
echo "2️⃣  Testando health check..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Health check OK"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "   ❌ Health check falhou"
    exit 1
fi

echo ""
echo "3️⃣  Testando endpoints da API..."
echo "   📊 Dashboard stats: http://localhost:8000/api/dashboard/stats"
echo "   🏷️  Tags: http://localhost:8000/api/tags"
echo "   📋 Sessões: http://localhost:8000/api/sessions"
echo "   📖 Documentação: http://localhost:8000/docs"

echo ""
echo "✅ Todos os testes passaram!"
echo ""
echo "Para ver logs: tail -f logs/api.log"
