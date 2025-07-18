from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Define Models
class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    alert_type: str  # "vol", "accident", "catastrophe"
    zone: str
    reporter_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # "active", "resolved"

class AlertCreate(BaseModel):
    title: str
    description: str
    alert_type: str
    zone: str
    reporter_name: str

class AlertUpdate(BaseModel):
    status: str

# Zones principales de Côte d'Ivoire
ZONES = [
    "Abidjan", "Bouaké", "Daloa", "Korhogo", "San-Pédro", "Yamoussoukro",
    "Divo", "Gagnoa", "Abengourou", "Bondoukou", "Grand-Bassam", "Jacqueville",
    "Sassandra", "Tabou", "Soubré", "Issia", "Sinfra", "Vavoua", "Zuénoula",
    "Danané", "Man", "Touba", "Odienné", "Minignan", "Séguéla", "Katiola",
    "Dabakala", "Bondoukou", "Tanda", "Bouna", "Doropo", "Ferké", "Ouangolo"
]

ALERT_TYPES = [
    {"id": "vol", "label": "Vol/Cambriolage", "icon": "🚨"},
    {"id": "accident", "label": "Accident", "icon": "🚑"},
    {"id": "catastrophe", "label": "Catastrophe Naturelle", "icon": "⚠️"}
]

# Routes
@api_router.get("/")
async def root():
    return {"message": "API d'Alertes Communautaires - Côte d'Ivoire"}

@api_router.get("/zones")
async def get_zones():
    return {"zones": ZONES}

@api_router.get("/alert-types")
async def get_alert_types():
    return {"alert_types": ALERT_TYPES}

@api_router.post("/alerts", response_model=Alert)
async def create_alert(alert: AlertCreate):
    alert_dict = alert.dict()
    alert_obj = Alert(**alert_dict)
    
    # Save to database
    await db.alerts.insert_one(alert_obj.dict())
    
    # Broadcast to all connected WebSocket clients
    await manager.broadcast(json.dumps({
        "type": "new_alert",
        "alert": alert_obj.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }, default=str))
    
    return alert_obj

@api_router.get("/alerts", response_model=List[Alert])
async def get_alerts(zone: Optional[str] = None, alert_type: Optional[str] = None, status: Optional[str] = "active"):
    # Build query
    query = {}
    if zone:
        query["zone"] = zone
    if alert_type:
        query["alert_type"] = alert_type
    if status:
        query["status"] = status
    
    # Get alerts from database
    alerts = await db.alerts.find(query).sort("timestamp", -1).to_list(100)
    return [Alert(**alert) for alert in alerts]

@api_router.put("/alerts/{alert_id}", response_model=Alert)
async def update_alert(alert_id: str, alert_update: AlertUpdate):
    # Update alert in database
    await db.alerts.update_one(
        {"id": alert_id},
        {"$set": alert_update.dict()}
    )
    
    # Get updated alert
    alert = await db.alerts.find_one({"id": alert_id})
    if alert:
        alert_obj = Alert(**alert)
        
        # Broadcast update to all connected WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "alert_update",
            "alert": alert_obj.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }, default=str))
        
        return alert_obj
    
    return None

@api_router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str):
    alert = await db.alerts.find_one({"id": alert_id})
    if alert:
        return Alert(**alert)
    return None

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - can be enhanced with more features
            await manager.send_personal_message(f"Message reçu: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()