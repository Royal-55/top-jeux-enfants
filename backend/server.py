from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
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
import base64

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
    # New fields for enhanced features
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photos: List[str] = []  # base64 encoded photos
    votes: int = 0
    voters: List[str] = []  # list of voter IDs (IP addresses or user IDs)
    verified: bool = False
    location_accuracy: Optional[float] = None  # GPS accuracy in meters

class AlertCreate(BaseModel):
    title: str
    description: str
    alert_type: str
    zone: str
    reporter_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photos: List[str] = []
    location_accuracy: Optional[float] = None

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    verified: Optional[bool] = None

class VoteRequest(BaseModel):
    voter_id: str  # IP address or user identifier

# Fonction pour déterminer la zone basée sur les coordonnées GPS
def get_zone_from_coordinates(lat: float, lon: float) -> str:
    """
    Déterminer la zone basée sur les coordonnées GPS
    Cette fonction utilise des approximations pour les principales villes de Côte d'Ivoire
    """
    # Coordonnées approximatives des principales villes de Côte d'Ivoire
    city_coords = {
        "Abidjan": {"lat": 5.3600, "lon": -4.0083, "radius": 0.5},
        "Yamoussoukro": {"lat": 6.8276, "lon": -5.2893, "radius": 0.3},
        "Bouaké": {"lat": 7.6906, "lon": -5.0300, "radius": 0.3},
        "Daloa": {"lat": 6.8770, "lon": -6.4503, "radius": 0.3},
        "Korhogo": {"lat": 9.4580, "lon": -5.6297, "radius": 0.3},
        "San-Pédro": {"lat": 4.7485, "lon": -6.6363, "radius": 0.3},
        "Man": {"lat": 7.4120, "lon": -7.5539, "radius": 0.3},
        "Divo": {"lat": 5.8370, "lon": -5.3570, "radius": 0.2},
        "Gagnoa": {"lat": 6.1317, "lon": -5.9470, "radius": 0.2},
        "Abengourou": {"lat": 6.7297, "lon": -3.4967, "radius": 0.2},
    }
    
    # Calculer la distance et trouver la ville la plus proche
    closest_city = "Autre"
    min_distance = float('inf')
    
    for city, coords in city_coords.items():
        distance = ((lat - coords["lat"])**2 + (lon - coords["lon"])**2)**0.5
        if distance < coords["radius"] and distance < min_distance:
            min_distance = distance
            closest_city = city
    
    return closest_city

# Zones principales de Côte d'Ivoire
ZONES = [
    "Abidjan", "Bouaké", "Daloa", "Korhogo", "San-Pédro", "Yamoussoukro",
    "Divo", "Gagnoa", "Abengourou", "Bondoukou", "Grand-Bassam", "Jacqueville",
    "Sassandra", "Tabou", "Soubré", "Issia", "Sinfra", "Vavoua", "Zuénoula",
    "Danané", "Man", "Touba", "Odienné", "Minignan", "Séguéla", "Katiola",
    "Dabakala", "Bondoukou", "Tanda", "Bouna", "Doropo", "Ferké", "Ouangolo", "Autre"
]

ALERT_TYPES = [
    {"id": "vol", "label": "Vol/Cambriolage", "icon": "🚨"},
    {"id": "accident", "label": "Accident", "icon": "🚑"},
    {"id": "catastrophe", "label": "Catastrophe Naturelle", "icon": "⚠️"}
]

# Routes
@api_router.get("/")
async def root():
    return {"message": "API d'Alertes Communautaires - Côte d'Ivoire v2.0"}

@api_router.get("/zones")
async def get_zones():
    return {"zones": ZONES}

@api_router.get("/alert-types")
async def get_alert_types():
    return {"alert_types": ALERT_TYPES}

@api_router.post("/detect-zone")
async def detect_zone(coordinates: dict):
    """Détecter la zone basée sur les coordonnées GPS"""
    lat = coordinates.get("latitude")
    lon = coordinates.get("longitude")
    
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Latitude et longitude requises")
    
    zone = get_zone_from_coordinates(lat, lon)
    return {"zone": zone, "latitude": lat, "longitude": lon}

@api_router.post("/alerts", response_model=Alert)
async def create_alert(alert: AlertCreate):
    alert_dict = alert.dict()
    
    # Auto-détecter la zone si les coordonnées sont fournies
    if alert.latitude and alert.longitude and not alert.zone:
        detected_zone = get_zone_from_coordinates(alert.latitude, alert.longitude)
        alert_dict["zone"] = detected_zone
    
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

@api_router.post("/alerts/{alert_id}/vote")
async def vote_alert(alert_id: str, vote_request: VoteRequest):
    """Voter pour une alerte (système de validation communautaire)"""
    # Vérifier si l'alerte existe
    alert = await db.alerts.find_one({"id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    
    # Vérifier si l'utilisateur a déjà voté
    voters = alert.get("voters", [])
    if vote_request.voter_id in voters:
        raise HTTPException(status_code=400, detail="Vous avez déjà voté pour cette alerte")
    
    # Ajouter le vote
    new_votes = alert.get("votes", 0) + 1
    new_voters = voters + [vote_request.voter_id]
    
    # Marquer comme vérifié si plus de 3 votes
    verified = new_votes >= 3
    
    # Mettre à jour l'alerte
    await db.alerts.update_one(
        {"id": alert_id},
        {"$set": {
            "votes": new_votes,
            "voters": new_voters,
            "verified": verified
        }}
    )
    
    # Obtenir l'alerte mise à jour
    updated_alert = await db.alerts.find_one({"id": alert_id})
    alert_obj = Alert(**updated_alert)
    
    # Broadcast update to all connected WebSocket clients
    await manager.broadcast(json.dumps({
        "type": "alert_vote",
        "alert": alert_obj.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }, default=str))
    
    return {"message": "Vote enregistré", "votes": new_votes, "verified": verified}

@api_router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    zone: Optional[str] = None, 
    alert_type: Optional[str] = None, 
    status: Optional[str] = "active",
    verified_only: Optional[bool] = False
):
    # Build query
    query = {}
    if zone:
        query["zone"] = zone
    if alert_type:
        query["alert_type"] = alert_type
    if status:
        query["status"] = status
    if verified_only:
        query["verified"] = True
    
    # Get alerts from database
    alerts = await db.alerts.find(query).sort("timestamp", -1).to_list(100)
    return [Alert(**alert) for alert in alerts]

@api_router.get("/alerts/nearby")
async def get_nearby_alerts(latitude: float, longitude: float, radius: float = 0.1):
    """Obtenir les alertes à proximité basées sur les coordonnées GPS"""
    # Calculer les limites géographiques
    lat_min = latitude - radius
    lat_max = latitude + radius
    lon_min = longitude - radius
    lon_max = longitude + radius
    
    # Requête pour les alertes dans la zone
    query = {
        "latitude": {"$gte": lat_min, "$lte": lat_max},
        "longitude": {"$gte": lon_min, "$lte": lon_max},
        "status": "active"
    }
    
    alerts = await db.alerts.find(query).sort("timestamp", -1).to_list(50)
    return [Alert(**alert) for alert in alerts]

@api_router.put("/alerts/{alert_id}", response_model=Alert)
async def update_alert(alert_id: str, alert_update: AlertUpdate):
    # Update alert in database
    update_data = {k: v for k, v in alert_update.dict().items() if v is not None}
    await db.alerts.update_one(
        {"id": alert_id},
        {"$set": update_data}
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
    
    raise HTTPException(status_code=404, detail="Alerte non trouvée")

@api_router.get("/alerts/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str):
    alert = await db.alerts.find_one({"id": alert_id})
    if alert:
        return Alert(**alert)
    raise HTTPException(status_code=404, detail="Alerte non trouvée")

@api_router.get("/stats")
async def get_stats():
    """Obtenir les statistiques des alertes"""
    total_alerts = await db.alerts.count_documents({})
    active_alerts = await db.alerts.count_documents({"status": "active"})
    verified_alerts = await db.alerts.count_documents({"verified": True})
    
    # Statistiques par type
    types_stats = {}
    for alert_type in ["vol", "accident", "catastrophe"]:
        count = await db.alerts.count_documents({"alert_type": alert_type})
        types_stats[alert_type] = count
    
    # Statistiques par zone (top 10)
    zones_pipeline = [
        {"$group": {"_id": "$zone", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    zones_stats = await db.alerts.aggregate(zones_pipeline).to_list(10)
    
    return {
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "verified_alerts": verified_alerts,
        "types_stats": types_stats,
        "zones_stats": zones_stats
    }

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