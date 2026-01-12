#!/usr/bin/env python3
"""
Script de teste para verificar se o banco de dados está funcionando
Execute: python3 test_database.py
"""
import sys
import os

# Adicionar diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("🧪 Teste de Banco de Dados - Portal RFID Biamar")
print("=" * 60)

try:
    print("\n1️⃣  Importando módulos...")
    from models import init_db, SessionLocal, RFIDTag, ProductionSession, RFIDEvent
    print("   ✅ Módulos importados com sucesso!")
    
    print("\n2️⃣  Inicializando banco de dados...")
    init_db()
    print("   ✅ Banco de dados inicializado!")
    
    print("\n3️⃣  Testando conexão...")
    db = SessionLocal()
    
    print("\n4️⃣  Contando registros...")
    tags_count = db.query(RFIDTag).count()
    sessions_count = db.query(ProductionSession).count()
    events_count = db.query(RFIDEvent).count()
    
    print(f"   📊 Tags cadastradas: {tags_count}")
    print(f"   📊 Sessões de produção: {sessions_count}")
    print(f"   📊 Eventos registrados: {events_count}")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)
    print("\nO banco de dados está funcionando corretamente! 🎉")
    print("Você pode iniciar o sistema com: bash start_ubuntu.sh")
    print("=" * 60)
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERRO NO TESTE:")
    print(f"   {type(e).__name__}: {e}")
    print("\n🔧 Possíveis soluções:")
    print("   1. Verifique se o diretório 'database/' existe")
    print("   2. Verifique permissões: ls -la database/")
    print("   3. Execute: mkdir -p database")
    print("   4. Execute: chmod 755 database")
    print("\n" + "=" * 60)
    sys.exit(1)
