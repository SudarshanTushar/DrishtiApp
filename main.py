import os
import time
import math
import random
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RouteAI-NE: Sentinel V2", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. INTELLIGENCE DATABASE (MOCK DATA) ---
# Ye data real-time satellite se aana chahiye, demo ke liye hum hardcode kar rahe hain.

RISK_ZONES = [
    {"id": "LS_01", "type": "LANDSLIDE", "lat": 26.10, "lng": 91.77, "radius": 2.0, "severity": "CRITICAL", "advice": "Slopes Unstable - Evacuate"},
    {"id": "FL_01", "type": "FLOOD", "lat": 24.90, "lng": 92.60, "radius": 4.0, "severity": "HIGH", "advice": "Water Levels Rising"}
]

SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Base", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": "HIGH"},
    {"id": "SH_02", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": "MEDIUM"},
    {"id": "SH_03", "name": "Don Bosco Relief Camp", "lat": 26.12, "lng": 91.74, "type": "SHELTER", "capacity": "LOW"}
]

# --- 2. SENTINEL API (Risk & Alerts) ---

@app.get("/sentinel/risk-overlay")
def get_risk_overlay(lat: float, lng: float):
    """Returns Risk Circles & Satellite Status"""
    return {"zones": RISK_ZONES, "status": "ONLINE", "sat_link": "CONNECTED"}

@app.post("/sentinel/whistle")
def log_whistle(data: dict):
    print(f"🚨 DIGITAL SIREN/SOS LOGGED: {data}")
    return {"status": "LOGGED", "action": "ALERT_NDRF"}

# --- 3. COMMAND DASHBOARD (Govt View) ---

@app.get("/command/overview")
def get_dashboard_stats():
    """Returns logistics for Govt Officials"""
    return {
        "status": "ACTIVE_EMERGENCY",
        "active_disasters": 3,
        "total_sos": random.randint(120, 155),
        "deployed_resources": {
            "ambulances": 42,
            "ndrf_teams": 12,
            "drones_airborne": 8
        },
        "red_zones": RISK_ZONES
    }

# --- 4. CORE ROUTING (Safe Path Logic) ---

def get_dist(lat1, lon1, lat2, lon2):
    # Simple distance calc for sorting safe zones
    return math.sqrt((lat2-lat1)**2 + (lon2-lon1)**2)

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    """
    Decides route based on Rain Intensity.
    Also returns Top 3 Nearest Safe Zones.
    """
    
    # A. Routing Logic
    route_fast = {
        "id": "fast", "label": "FASTEST", "distance": "124.5 km", "time": "3h 10m",
        "risk": "HIGH", "hazard": "Landslide at Mile 40", "color": "#ef4444"
    }
    route_safe = {
        "id": "safe", "label": "SAFEST", "distance": "148.2 km", "time": "4h 05m",
        "risk": "LOW", "hazard": "None", "color": "#10b981"
    }

    # If rain > 40, FORCE Safe Route
    if rain_input > 40:
        recommended = route_safe
        alerts = [{"type": "HEAVY RAIN", "loc": "En Route", "severity": "Rerouting to Safe Path..."}]
    else:
        recommended = route_fast
        alerts = []

    # B. Find Nearest Safe Zones
    # Sort havens by distance to user
    sorted_havens = sorted(SAFE_HAVENS, key=lambda h: get_dist(start_lat, start_lng, h["lat"], h["lng"]))
    nearest_3 = sorted_havens[:3]

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": 95,
        "live_alerts": alerts,
        "evacuation": { "safe_havens": nearest_3 }
    }

# --- 5. VOICE AI (Sarvam Mock) ---
@app.post("/listen")
async def listen(file: UploadFile = File(...)):
    time.sleep(1) 
    return {
        "status": "success", "translated_text": "Navigate to Shillong",
        "target": "Shillong", "intent": "NAVIGATION"
    }

@app.get("/monitor-location")
def monitor(lat: float, lng: float):
    # Check if user is inside any risk zone
    in_danger = False
    for zone in RISK_ZONES:
        dist = get_dist(lat, lng, zone["lat"], zone["lng"])
        if dist < 0.05: in_danger = True # Rough approx
        
    return {
        "status": "CRITICAL" if in_danger else "SECURE",
        "geofence_data": {"in_danger_zone": in_danger}
    }
