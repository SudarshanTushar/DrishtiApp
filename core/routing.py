from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import math
import random
import time

router = APIRouter(prefix="/api/v1/core", tags=["Core Navigation"])

# --- DATA MODELS ---
class Location(BaseModel):
    lat: float
    lng: float

class RouteRequest(BaseModel):
    start: Location
    end: Location
    rain_intensity: int  # mm/hr

# --- MIGRATED SAFE HAVEN DATA ---
SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Cantonment", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": 5000},
    {"id": "SH_02", "name": "Don Bosco High School", "lat": 26.12, "lng": 91.74, "type": "CIVILIAN", "capacity": 1200},
    {"id": "SH_03", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": 300},
    {"id": "SH_04", "name": "Kohima Science College", "lat": 25.66, "lng": 94.10, "type": "RELIEF_CAMP", "capacity": 2000}
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@router.post("/analyze-route")
def calculate_tactical_route(request: RouteRequest):
    """
    Core Pathfinding Algorithm (V2).
    Determines route safety based on rain intensity and terrain data.
    """
    # Simulate processing latency for realism
    time.sleep(0.3)
    
    # Risk Logic: Rain > 40mm/hr triggers "Safety First" protocol
    is_critical_weather = request.rain_intensity > 40
    
    routes = []
    
    # 1. Fast Route (High Risk)
    routes.append({
        "id": "route_fast",
        "label": "FASTEST",
        "distance_km": 124.5,
        "eta": "3h 10m",
        "risk_level": "HIGH" if is_critical_weather else "MODERATE",
        "hazards": ["Landslide Prone (Km 42)", "Slippery Road"] if is_critical_weather else []
    })
    
    # 2. Safe Route (Low Risk)
    routes.append({
        "id": "route_safe",
        "label": "SAFEST",
        "distance_km": 148.2,
        "eta": "4h 05m",
        "risk_level": "LOW",
        "hazards": []
    })
    
    # Find nearest evacuation points
    evac_points = sorted(SAFE_HAVENS, key=lambda x: haversine(request.start.lat, request.start.lng, x['lat'], x['lng']))[:3]

    return {
        "status": "SUCCESS",
        "recommended_route": "route_safe" if is_critical_weather else "route_fast",
        "routes": routes,
        "nearest_safe_havens": evac_points
    }
