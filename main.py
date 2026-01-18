import os
import time
import math
import random
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RouteAI-NE: Master Command", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. MILITARY & RESCUE DATABASE ---
RISK_ZONES = [
    {"id": "LS_01", "type": "LANDSLIDE", "lat": 26.10, "lng": 91.77, "radius": 2.5, "severity": "CRITICAL", "advice": "Slopes Unstable - EVACUATE"},
    {"id": "FL_01", "type": "FLOOD", "lat": 24.90, "lng": 92.60, "radius": 5.0, "severity": "HIGH", "advice": "Water Rising Fast"},
    {"id": "EQ_01", "type": "SEISMIC", "lat": 26.14, "lng": 91.73, "radius": 1.0, "severity": "MODERATE", "advice": "Tremors Detected"}
]

SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Cantonment", "lat": 26.15, "lng": 91.76, "type": "MILITARY BASE", "capacity": "HIGH (5000+)"},
    {"id": "SH_02", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "HOSPITAL", "capacity": "MEDIUM (500)"},
    {"id": "SH_03", "name": "IIT Guwahati Helipad", "lat": 26.18, "lng": 91.69, "type": "AIRLIFT ZONE", "capacity": "CRITICAL EVAC"},
    {"id": "SH_04", "name": "Don Bosco Relief Camp", "lat": 26.12, "lng": 91.74, "type": "SHELTER", "capacity": "LOW (200)"}
]

def get_dist(lat1, lon1, lat2, lon2):
    R = 6371 # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- 2. SENTINEL INTELLIGENCE ---
@app.get("/sentinel/status")
def get_status():
    return { "sat_link": "CONNECTED (INSAT-3D)", "signal": "STRONG", "hazards": len(RISK_ZONES) }

@app.get("/sentinel/scan")
def scan_area(lat: float, lng: float):
    # Monitor for specific user location
    status = "SAFE"
    for zone in RISK_ZONES:
        if get_dist(lat, lng, zone["lat"], zone["lng"]) <= zone["radius"]:
            status = "DANGER"
    return { "status": status, "timestamp": time.time() }

@app.get("/sentinel/evacuate")
def get_evacuation_plan(lat: float, lng: float):
    # Return sorted Safe Havens
    sorted_havens = sorted(SAFE_HAVENS, key=lambda h: get_dist(lat, lng, h["lat"], h["lng"]))
    for h in sorted_havens: h["dist_km"] = round(get_dist(lat, lng, h["lat"], h["lng"]), 2)
    return { "safe_havens": sorted_havens[:3] }

@app.get("/sentinel/risk-overlay")
def get_risk_overlay(lat: float, lng: float):
    return { "zones": RISK_ZONES }

@app.post("/sentinel/whistle")
def log_whistle(data: dict):
    print(f"🚨 SOS LOGGED: {data}")
    return {"status": "LOGGED"}

# --- 3. GOVERNMENT COMMAND DASHBOARD ---
@app.get("/command/overview")
def get_dashboard_stats():
    return {
        "status": "ACTIVE_EMERGENCY",
        "active_disasters": 3,
        "total_sos": random.randint(120, 160),
        "deployed_resources": {
            "ambulances": 42,
            "ndrf_teams": 12,
            "helicopters": 3,
            "drones": 8
        },
        "logistics": {
            "ration_packets": 5000,
            "medical_kits": 1200,
            "water_tankers": 15
        }
    }

# --- 4. TACTICAL ROUTING ---
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    route_fast = { "id": "fast", "label": "USUAL ROUTE", "distance": "124.5 km", "time": "3h 10m", "risk": "HIGH", "hazard": "Landslide Sector 4", "color": "#ef4444" }
    route_safe = { "id": "safe", "label": "MILITARY ROUTE", "distance": "148.2 km", "time": "4h 05m", "risk": "LOW", "hazard": "None", "color": "#10b981" }
    
    if rain_input > 40:
        recommended = route_safe
        alerts = [{"type": "WARN", "msg": "Heavy Rain. Re-routing to Military Supply Line."}]
    else:
        recommended = route_fast
        alerts = []

    return { "routes": [route_fast, route_safe], "recommended_id": recommended["id"], "live_alerts": alerts }

@app.post("/listen")
async def listen(file: UploadFile = File(...)):
    time.sleep(1)
    return { "status": "success", "translated_text": "Navigate to Base", "target": "Base", "intent": "NAVIGATION" }
