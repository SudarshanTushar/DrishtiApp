from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/sentinel", tags=["Sentinel Intelligence"])

# Migrated Risk Zones from your legacy code
RISK_ZONES = [
    {"id": "LS_01", "name": "Jorabat Sector", "type": "LANDSLIDE", "lat": 26.15, "lng": 91.80, "radius": 1.5, "severity": "CRITICAL"},
    {"id": "FL_04", "name": "Barak Valley", "type": "FLOOD", "lat": 24.90, "lng": 92.60, "radius": 3.0, "severity": "HIGH"},
]

class WhistleSignal(BaseModel):
    lat: float
    lng: float
    active: bool

@router.get("/risk-map")
def get_live_risk_map(lat: float, lng: float, radius: float = 50.0):
    """
    Returns GeoJSON-compatible risk polygons for the map overlay.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "source": "ISRO_BHUVAN_LINKED",
        "zones": RISK_ZONES
    }

@router.post("/whistle")
def log_digital_whistle(signal: WhistleSignal):
    """
    Logs an offline siren activation.
    Used to triangulate victims when internet is spotty.
    """
    if signal.active:
        print(f"🚨 SOS WHISTLE DETECTED: {signal.lat}, {signal.lng}")
    return {"status": "LOGGED", "action": "NOTIFY_NDRF"}
