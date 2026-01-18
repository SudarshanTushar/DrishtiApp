import os
import time
import math
import random
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RouteAI-NE: Sentinel V2", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE ---
RISK_ZONES = [
    {"id": "LS_01", "type": "LANDSLIDE", "lat": 26.10, "lng": 91.77, "radius": 2.0, "severity": "CRITICAL", "advice": "Slopes Unstable"},
    {"id": "FL_01", "type": "FLOOD", "lat": 24.90, "lng": 92.60, "radius": 4.0, "severity": "HIGH", "advice": "Water Rising"}
]

SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Base", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": "HIGH"},
    {"id": "SH_02", "name": "Civil Hospital", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": "LOW"},
    {"id": "SH_03", "name": "Don Bosco Camp", "lat": 26.12, "lng": 91.74, "type": "RELIEF", "capacity": "MEDIUM"}
]

# --- ENDPOINTS ---

@app.get("/sentinel/risk-overlay")
def get_risk_overlay(lat: float, lng: float):
    return {"zones": RISK_ZONES, "status": "ONLINE"}

@app.post("/sentinel/whistle")
def log_whistle(data: dict):
    print(f"🚨 SIREN LOGGED: {data}")
    return {"status": "LOGGED"}

@app.get("/command/overview")
def get_dashboard_stats():
    """Returns FULL Military-Grade Intel"""
    return {
        "status": "ACTIVE_EMERGENCY",
        "active_disasters": 3,
        "total_sos": random.randint(120, 155),
        "deployed_resources": {
            "ambulances": 42,
            "ndrf_teams": 12,
            "drones_airborne": 8
        },
        # ✅ RESTORED LOGISTICS DATA
        "logistics": {
            "ration_packets": 5000,
            "medical_kits": 1200,
            "food_water_liters": 10000
        },
        "red_zones": RISK_ZONES
    }

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    route_fast = { "id": "fast", "label": "FASTEST", "distance": "124.5 km", "risk": "HIGH", "hazard": "Landslide at Mile 40", "color": "#ef4444" }
    route_safe = { "id": "safe", "label": "SAFEST", "distance": "148.2 km", "risk": "LOW", "hazard": "None", "color": "#10b981" }

    if rain_input > 40:
        recommended = route_safe
        alerts = [{"type": "HEAVY RAIN", "loc": "Sector 4", "severity": "Rerouting..."}]
    else:
        recommended = route_fast
        alerts = []

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": 95,
        "live_alerts": alerts,
        "evacuation": { "safe_havens": SAFE_HAVENS }
    }

@app.post("/listen")
async def listen(file: UploadFile = File(...)):
    time.sleep(1) 
    return { "status": "success", "translated_text": "Navigate to Shillong", "target": "Shillong", "intent": "NAVIGATION" }

@app.get("/monitor-location")
def monitor(lat: float, lng: float):
    return {"status": "SECURE", "geofence_data": {"in_danger_zone": False}}
