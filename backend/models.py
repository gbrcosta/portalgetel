from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class RFIDTag(Base):
    """Modelo para armazenar informações das tags RFID"""
    __tablename__ = 'rfid_tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)

class ProductionSession(Base):
    """Modelo para sessões de produção"""
    __tablename__ = 'production_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(String(100), nullable=False, index=True)
    antenna_1_time = Column(DateTime)  # Entrada na antena 1
    antenna_2_time = Column(DateTime)  # Saída na antena 2
    duration_seconds = Column(Float)  # Tempo de produção em segundos
    status = Column(String(20), default='em_producao')  # em_producao, finalizado
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RFIDEvent(Base):
    """Modelo para registrar todos os eventos de leitura RFID"""
    __tablename__ = 'rfid_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(String(100), nullable=False, index=True)
    antenna_number = Column(Integer, nullable=False)  # 1 ou 2
    event_time = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(Integer)  # Referência à sessão de produção

class RejectedReading(Base):
    """Modelo para registrar leituras rejeitadas ou bloqueadas"""
    __tablename__ = 'rejected_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_id = Column(String(100), nullable=False, index=True)
    antenna_number = Column(Integer)
    event_time = Column(DateTime, default=datetime.utcnow, index=True)
    reason = Column(String(255), nullable=False)  # Motivo da rejeição
    reason_type = Column(String(50))  # 'validation', 'timeout', 'blocked', etc.
    
# Configuração do banco de dados
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'rfid_portal.db')

# Criar diretório do banco de dados se não existir
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
    print(f"Diretório criado: {DATABASE_DIR}")

engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Inicializa o banco de dados criando todas as tabelas"""
    # Garantir que o diretório existe
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
        print(f"Diretório do banco de dados criado: {DATABASE_DIR}")
    
    # If the DB file does not exist (we moved/removed it), use an in-memory DB
    global engine, SessionLocal
    if not os.path.exists(DATABASE_PATH):
        engine = create_engine('sqlite:///:memory:', echo=False)
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        print("Banco de dados inicializado em memória (sem persistência).")
    else:
        engine = create_engine(f'sqlite:///{DATABASE_PATH}', echo=False)
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        print(f"Banco de dados inicializado em: {DATABASE_PATH}")

def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
