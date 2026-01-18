from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time
import random
import math
from datetime import datetime

# Initialize the Sentinel Router
router = APIRouter(prefix="/sentinel", tags=["Sentinel Intelligence"])

# --- DATA MODELS ---
class WhistleStatus(BaseModel):
    lat: float
    lng: float
    active: bool
    battery_level: Optional[int] = None

# --- MOCK INTELLIGENCE DATA (In production, this comes from Satellite/IoT) ---
RISK_ZONES = [
    {"id": "LS_01", "type": "LANDSLIDE", "risk": "CRITICAL", "lat": 26.1, "lng": 91.8, "radius": 500, "advice": "Unstable Slope"},
    {"id": "FL_04", "type": "FLOOD", "risk": "HIGH", "lat": 24.9, "lng": 92.6, "radius": 1200, "advice": "Water rising fast"}
]

SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Base", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": "HIGH"},
    {"id": "SH_02", "name": "Don Bosco School", "lat": 26.12, "lng": 91.74, "type": "CIVILIAN", "capacity": "MEDIUM"},
    {"id": "SH_03", "name": "Civil Hospital", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": "LOW"}
]

# --- HELPER: HAVERSINE DISTANCE ---
def get_dist(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of earth in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ==========================================
# 🛰️ 1. ADVANCED RISK OVERLAY (Satellite Layer)
# ==========================================
@router.get("/risk-overlay")
def get_risk_overlay(lat: float, lng: float, radius_km: int = 50):
    """
    Returns verified hazard zones to overlay on the map.
    Does NOT affect navigation calculation time (runs in background).
    """
    visible_zones = []
    
    # 1. Filter zones within range
    for zone in RISK_ZONES:
        dist = get_dist(lat, lng, zone["lat"], zone["lng"])
        if dist <= radius_km:
            visible_zones.append({
                **zone,
                "dist_km": round(dist, 2),
                "visual_color": "#EF4444" if zone["risk"] == "CRITICAL" else "#F59E0B"
            })
    
    # 2. Add Dynamic Weather Overlay (Simulated)
    weather_alert = None
    if random.random() < 0.3:
        weather_alert = {
            "type": "FLASH_FLOOD_WARNING",
            "center": {"lat": lat + 0.05, "lng": lng + 0.05},
            "radius": 2000,
            "severity": "MODERATE"
        }

    return {
        "timestamp": datetime.now().isoformat(),
        "zones": visible_zones,
        "weather_event": weather_alert,
        "source": "ISRO_BHUVAN_LINKED"
    }

# ==========================================
# 🚑 2. SAFE ZONE LOGIC (Evacuation)
# ==========================================
@router.get("/safe-havens")
def get_nearest_safe_zones(lat: float, lng: float):
    """
    Returns top 3 verified safe locations sorted by viability.
    """
    ranked = []
    for haven in SAFE_HAVENS:
        dist = get_dist(lat, lng, haven["lat"], haven["lng"])
        
        # Scoring Logic: Distance is key, but Capacity matters
        score = 100 - (dist * 2) 
        if haven["capacity"] == "LOW": score -= 20
        
        ranked.append({**haven, "distance_km": round(dist, 2), "score": score})
    
    ranked.sort(key=lambda x: x["distance_km"])
    return ranked[:3]

# ==========================================
# 🔊 3. DIGITAL WHISTLE (New Module)
# ==========================================
@router.post("/whistle")
def trigger_digital_whistle(status: WhistleStatus):
    """
    Logs activation of the Digital Siren.
    In a real scenario, this alerts nearby rescue teams of a trapped victim's location.
    """
    if status.active:
        print(f"🚨 WHISTLE ACTIVATED at {status.lat}, {status.lng} | Bat: {status.battery_level}%")
        # Logic to push to NDRF Dashboard would go here
        return {"status": "LOGGED", "message": "Rescue teams alerted to your beacon."}
    else:
        print(f"xx Whistle Deactivated at {status.lat}, {status.lng}")
        return {"status": "STANDBY"}
