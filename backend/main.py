from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import os
import sys
import json
from pathlib import Path
import serial
import time

from models import RFIDTag, ProductionSession, RFIDEvent, RejectedReading, get_db, init_db, SessionLocal
from pydantic import BaseModel

# Inicializar banco de dados
try:
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao inicializar banco de dados: {e}")
    print(f"   Verifique as permissões do diretório database/")
    sys.exit(1)

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
    """Serve a página principal do dashboard"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Portal RFID - Biamar UR4 API", "status": "online"}

@app.get("/static/styles.css")
async def get_styles():
    """Serve o arquivo CSS"""
    css_path = Path(__file__).parent.parent / "frontend" / "styles.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS not found")

@app.get("/static/app.js")
async def get_app_js():
    """Serve o arquivo JavaScript"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS not found")

@app.get("/health")
async def health_check():
    """Health check endpoint para verificar se a API está funcionando"""
    try:
        # Testar conexão com banco de dados
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/rfid/event")
async def register_rfid_event(event: RFIDEventRequest, db: Session = Depends(get_db_session)):
    """Registra um evento de leitura RFID"""
    
    # Validar comprimento da tag (deve ter exatamente 24 caracteres)
    if len(event.tag_id) != 24:
        # Registrar leitura rejeitada
        rejected = RejectedReading(
            tag_id=event.tag_id,
            antenna_number=event.antenna_number,
            event_time=datetime.utcnow(),
            reason=f"Tag inválida: deve ter 24 caracteres (recebido: {len(event.tag_id)})",
            reason_type="validation"
        )
        db.add(rejected)
        db.commit()
        
        return {
            "success": False,
            "error": f"Tag inválida: deve ter 24 caracteres (recebido: {len(event.tag_id)})",
            "tag_id": event.tag_id
        }
    
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
    # Antena 1: Início de produção (entrada)
    if event.antenna_number == 1:
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
    
    # Antena 0 ou 2: Fim de produção (saída)
    elif event.antenna_number in [0, 2]:
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

@app.get("/api/rejected/recent")
async def get_rejected_readings(limit: int = 100, db: Session = Depends(get_db_session)):
    """Retorna leituras rejeitadas ou bloqueadas"""
    rejected = db.query(RejectedReading).order_by(
        RejectedReading.event_time.desc()
    ).limit(limit).all()
    
    return [{
        "id": r.id,
        "tag_id": r.tag_id,
        "antenna_number": r.antenna_number,
        "event_time": r.event_time,
        "reason": r.reason,
        "reason_type": r.reason_type
    } for r in rejected]


# Runtime config file for antenna settings (created if missing)
CONFIG_PATH = Path(__file__).parent / "config_runtime.json"

def _ensure_config():
    default = {
        "antenna1_enabled": True,
        "antenna2_enabled": False,
        "antenna1_power": 30,
        "antenna2_power": 30
    }
    if not CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(default, f, indent=2)
        except Exception:
            pass
    return default

def load_runtime_config():
    _ensure_config()
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return _ensure_config()

def save_runtime_config(data: dict):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def _build_frame(cmd: int, data_bytes: bytes | bytearray) -> bytes:
    """Builds a frame according to the protocol in the PDF.
    Frame: Header(2) + Length(2) + CMD(1) + Data(N) + BCC(1) + Trailer(2)
    Length = total bytes count (header..trailer)
    BCC = XOR of length bytes, cmd and data bytes
    """
    header = bytearray([0xC8, 0x8C])
    length = 8 + len(data_bytes)  # total frame size
    length_bytes = bytearray([(length >> 8) & 0xFF, length & 0xFF])
    body = bytearray([cmd]) + bytearray(data_bytes)
    bcc = 0
    for b in length_bytes + body:
        bcc ^= b
    trailer = bytearray([0x0D, 0x0A])
    return bytes(header + length_bytes + body + bytearray([bcc]) + trailer)


def _apply_config_to_device(cfg: dict, port: str = '/dev/ttyUSB0') -> dict:
    """Attempt to apply config to the physical device via serial.
    Returns a dict with status and any error messages.
    """
    result = {"sent": [], "errors": []}
    try:
        ser = serial.Serial(port=port, baudrate=115200, timeout=1)
    except Exception as e:
        result['errors'].append(f"Cannot open serial port {port}: {e}")
        return result

    try:
        # Antenna selection command (0x28)
        save_flag = 0x01 if cfg.get('save_on_poweroff', True) else 0x00
        a1 = 1 if cfg.get('antenna1_enabled', True) else 0
        a2 = 1 if cfg.get('antenna2_enabled', False) else 0
        bitmask = (a2 << 1) | (a1 << 0)
        dbyte0 = bitmask & 0xFF
        dbyte1 = (bitmask >> 8) & 0xFF
        dbyte2 = save_flag
        frame_antenna = _build_frame(0x28, bytes([dbyte2, dbyte1, dbyte0]))
        try:
            ser.write(frame_antenna)
            result['sent'].append({'cmd': 'antenna', 'frame': frame_antenna.hex()})
            time.sleep(0.05)
        except Exception as e:
            result['errors'].append(f"Error sending antenna frame: {e}")

        # Transmit power for antenna 1
        for ant_idx, key in ((1, 'antenna1_power'), (2, 'antenna2_power')):
            if key in cfg:
                power_dbm = int(cfg.get(key, 30))
                power_val = int(power_dbm * 100)
                msb = (power_val >> 8) & 0xFF
                lsb = power_val & 0xFF
                status = 0x02 if cfg.get('save_on_poweroff', True) else 0x00
                data = bytes([status, ant_idx, msb, lsb, msb, lsb])
                frame_power = _build_frame(0x10, data)
                try:
                    ser.write(frame_power)
                    result['sent'].append({'cmd': f'power_a{ant_idx}', 'frame': frame_power.hex()})
                    time.sleep(0.05)
                except Exception as e:
                    result['errors'].append(f"Error sending power frame for antenna {ant_idx}: {e}")

        # Optionally read any immediate responses (non-blocking)
        time.sleep(0.1)
        try:
            resp = ser.read(ser.in_waiting or 128)
            if resp:
                result['response'] = resp.hex()
        except Exception:
            pass
    finally:
        try:
            ser.close()
        except Exception:
            pass

    return result


@app.get("/api/config")
async def get_config():
    """Retorna a configuração runtime (antenas/potência)"""
    return load_runtime_config()


@app.post("/api/config")
async def set_config(payload: dict):
    """Atualiza a configuração runtime e salva em arquivo"""
    # Validação simples
    cfg = load_runtime_config()
    try:
        if 'antenna1_enabled' in payload:
            cfg['antenna1_enabled'] = bool(payload['antenna1_enabled'])
        if 'antenna2_enabled' in payload:
            cfg['antenna2_enabled'] = bool(payload['antenna2_enabled'])
        if 'antenna1_power' in payload:
            cfg['antenna1_power'] = int(payload['antenna1_power'])
        if 'antenna2_power' in payload:
            cfg['antenna2_power'] = int(payload['antenna2_power'])

        saved = save_runtime_config(cfg)
        if not saved:
            raise Exception('Não foi possível salvar configuração')

        # Tentar aplicar imediatamente no dispositivo via serial
        apply_result = _apply_config_to_device(cfg)

        return {"success": True, "config": cfg, "applied": apply_result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Para desenvolvimento: execute com `python3 main.py`
# Para produção: use `uvicorn main:app --host 0.0.0.0 --port 8000`
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Iniciando API - Portal RFID Biamar UR4")
    print("=" * 60)
    print("📡 Servidor: http://0.0.0.0:8000")
    print("📚 Documentação: http://localhost:8000/docs")
    print("📊 Health Check: http://localhost:8000/health")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
