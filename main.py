import os
import time
import math
import random
import requests
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RouteAI-NE: Monolith", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. MOCK DATABASE (THE BRAIN) ---
RISK_ZONES = [
    # A Red Zone directly on the Guwahati -> Shillong path
    {"id": "LS_01", "type": "LANDSLIDE", "lat": 26.10, "lng": 91.77, "radius": 2.0, "severity": "CRITICAL", "advice": "Slopes Unstable"},
    {"id": "FL_01", "type": "FLOOD", "lat": 24.90, "lng": 92.60, "radius": 4.0, "severity": "HIGH", "advice": "Water Rising"}
]

SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Base", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": "HIGH"},
    {"id": "SH_02", "name": "Civil Hospital", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": "LOW"}
]

# --- 2. SENTINEL INTELLIGENCE ENDPOINTS ---

@app.get("/sentinel/risk-overlay")
def get_risk_overlay(lat: float, lng: float):
    """Returns the Red Circles for the Map"""
    return {"zones": RISK_ZONES, "status": "ONLINE"}

@app.post("/sentinel/whistle")
def log_whistle(data: dict):
    print(f"🚨 SIREN LOGGED: {data}")
    return {"status": "LOGGED"}

# --- 3. COMMAND DASHBOARD ENDPOINTS ---

@app.get("/command/overview")
def get_dashboard_stats():
    """Returns the numbers for Govt Mode"""
    return {
        "status": "ACTIVE_EMERGENCY",
        "active_disasters": 3,
        "total_sos": random.randint(120, 155),
        "deployed_resources": {
            "ambulances": 42,
            "ndrf_teams": 12,
            "drones_airborne": 8
        },
        "red_zones": RISK_ZONES # Re-use same zones for consistency
    }

# --- 4. CORE ROUTING (THE RAIN LOGIC) ---

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    """
    Decides route based on Rain Slider.
    Rain > 40 = GREEN (Safe).
    Rain < 40 = RED/BLUE (Fast but Risky).
    """
    # 1. Define Routes
    route_fast = {
        "id": "fast",
        "label": "FASTEST",
        "distance": "124.5 km",
        "time": "3h 10m",
        "risk": "HIGH",
        "hazard": "Landslide at Mile 40", # <--- This text triggers the Alert
        "color": "#ef4444"
    }
    
    route_safe = {
        "id": "safe",
        "label": "SAFEST",
        "distance": "148.2 km",
        "time": "4h 05m",
        "risk": "LOW",
        "hazard": "None",
        "color": "#10b981"
    }

    # 2. The Logic Switch
    if rain_input > 40:
        recommended = route_safe
        alerts = [{"type": "HEAVY RAIN", "loc": "Sector 4", "severity": "Rerouting..."}]
    else:
        recommended = route_fast
        alerts = [] # No rain alerts, but route has hazards

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": 95,
        "live_alerts": alerts,
        "evacuation": { "safe_havens": SAFE_HAVENS }
    }

# --- 5. VOICE AI (OPTIONAL) ---
@app.post("/listen")
async def listen(file: UploadFile = File(...)):
    # Simple Mock for Demo reliability
    time.sleep(1) 
    return {
        "status": "success",
        "translated_text": "Navigate to Shillong",
        "target": "Shillong",
        "intent": "NAVIGATION"
    }

@app.get("/monitor-location")
def monitor(lat: float, lng: float):
    return {"status": "SECURE", "geofence_data": {"in_danger_zone": False}}
