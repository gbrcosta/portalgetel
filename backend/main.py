from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import os

from models import RFIDTag, ProductionSession, RFIDEvent, get_db, init_db, SessionLocal
from pydantic import BaseModel

# Inicializar banco de dados
init_db()

app = FastAPI(title="Portal RFID - Biamar UR4", version="1.0.0")

# Configurar CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic para requisições/respostas
class RFIDEventRequest(BaseModel):
    tag_id: str
    antenna_number: int

class TagResponse(BaseModel):
    id: int
    tag_id: str
    description: Optional[str]
    active: bool
    
    class Config:
        from_attributes = True

class ProductionSessionResponse(BaseModel):
    id: int
    tag_id: str
    antenna_1_time: Optional[datetime]
    antenna_2_time: Optional[datetime]
    duration_seconds: Optional[float]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_sessions: int
    active_sessions: int
    completed_today: int
    total_completed: int
    average_duration: float
    average_duration_today: float

# Dependência para obter sessão do banco
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Portal RFID - Biamar UR4 API", "status": "online"}

@app.post("/api/rfid/event")
async def register_rfid_event(event: RFIDEventRequest, db: Session = Depends(get_db_session)):
    """Registra um evento de leitura RFID"""
    
    # Criar o evento
    rfid_event = RFIDEvent(
        tag_id=event.tag_id,
        antenna_number=event.antenna_number,
        event_time=datetime.utcnow()
    )
    
    # Verificar se a tag existe, senão criar
    tag = db.query(RFIDTag).filter(RFIDTag.tag_id == event.tag_id).first()
    if not tag:
        tag = RFIDTag(tag_id=event.tag_id, description=f"Tag {event.tag_id}")
        db.add(tag)
        db.commit()
    
    # Processar baseado na antena
    if event.antenna_number == 1:
        # Antena 1: Início de produção
        # Verificar se já existe sessão ativa para esta tag
        active_session = db.query(ProductionSession).filter(
            ProductionSession.tag_id == event.tag_id,
            ProductionSession.status == 'em_producao'
        ).first()
        
        if active_session:
            # Atualizar timestamp da antena 1
            active_session.antenna_1_time = datetime.utcnow()
            active_session.updated_at = datetime.utcnow()
        else:
            # Criar nova sessão
            session = ProductionSession(
                tag_id=event.tag_id,
                antenna_1_time=datetime.utcnow(),
                status='em_producao'
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            rfid_event.session_id = session.id
    
    elif event.antenna_number == 2:
        # Antena 2: Fim de produção
        # Buscar sessão ativa para esta tag
        active_session = db.query(ProductionSession).filter(
            ProductionSession.tag_id == event.tag_id,
            ProductionSession.status == 'em_producao'
        ).first()
        
        if active_session and active_session.antenna_1_time:
            # Finalizar sessão
            active_session.antenna_2_time = datetime.utcnow()
            duration = (active_session.antenna_2_time - active_session.antenna_1_time).total_seconds()
            active_session.duration_seconds = duration
            active_session.status = 'finalizado'
            active_session.updated_at = datetime.utcnow()
            rfid_event.session_id = active_session.id
        else:
            # Sessão não encontrada ou não iniciada corretamente
            return {"error": "Sessão não encontrada ou não iniciada na antena 1"}
    
    db.add(rfid_event)
    db.commit()
    
    return {
        "success": True,
        "tag_id": event.tag_id,
        "antenna": event.antenna_number,
        "timestamp": rfid_event.event_time
    }

@app.get("/api/sessions", response_model=List[ProductionSessionResponse])
async def get_sessions(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """Retorna as sessões de produção"""
    query = db.query(ProductionSession)
    
    if status:
        query = query.filter(ProductionSession.status == status)
    
    sessions = query.order_by(ProductionSession.created_at.desc()).limit(limit).all()
    return sessions

@app.get("/api/sessions/active", response_model=List[ProductionSessionResponse])
async def get_active_sessions(db: Session = Depends(get_db_session)):
    """Retorna sessões ativas (em produção)"""
    sessions = db.query(ProductionSession).filter(
        ProductionSession.status == 'em_producao'
    ).order_by(ProductionSession.created_at.desc()).all()
    return sessions

@app.get("/api/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db_session)):
    """Retorna estatísticas para o dashboard"""
    
    total_sessions = db.query(ProductionSession).count()
    active_sessions = db.query(ProductionSession).filter(
        ProductionSession.status == 'em_producao'
    ).count()
    
    # Total de sessões completadas (histórico completo)
    total_completed = db.query(ProductionSession).filter(
        ProductionSession.status == 'finalizado'
    ).count()
    
    # Sessões completadas hoje
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    completed_today = db.query(ProductionSession).filter(
        ProductionSession.status == 'finalizado',
        ProductionSession.antenna_2_time >= today_start
    ).count()
    
    # Duração média geral (todas as sessões finalizadas)
    avg_result = db.query(ProductionSession).filter(
        ProductionSession.status == 'finalizado',
        ProductionSession.duration_seconds.isnot(None)
    ).all()
    
    if avg_result:
        durations = [s.duration_seconds for s in avg_result if s.duration_seconds]
        average_duration = sum(durations) / len(durations) if durations else 0
    else:
        average_duration = 0
    
    # Duração média das sessões de hoje
    avg_today = db.query(ProductionSession).filter(
        ProductionSession.status == 'finalizado',
        ProductionSession.antenna_2_time >= today_start,
        ProductionSession.duration_seconds.isnot(None)
    ).all()
    
    if avg_today:
        durations_today = [s.duration_seconds for s in avg_today if s.duration_seconds]
        average_duration_today = sum(durations_today) / len(durations_today) if durations_today else 0
    else:
        average_duration_today = 0
    
    return DashboardStats(
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        completed_today=completed_today,
        total_completed=total_completed,
        average_duration=average_duration,
        average_duration_today=average_duration_today
    )

@app.get("/api/tags", response_model=List[TagResponse])
async def get_tags(db: Session = Depends(get_db_session)):
    """Retorna todas as tags cadastradas"""
    tags = db.query(RFIDTag).filter(RFIDTag.active == True).all()
    return tags

@app.get("/api/events/recent")
async def get_recent_events(limit: int = 50, db: Session = Depends(get_db_session)):
    """Retorna eventos recentes"""
    events = db.query(RFIDEvent).order_by(
        RFIDEvent.event_time.desc()
    ).limit(limit).all()
    
    return [{
        "id": e.id,
        "tag_id": e.tag_id,
        "antenna_number": e.antenna_number,
        "event_time": e.event_time,
        "session_id": e.session_id
    } for e in events]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
