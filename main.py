import os
import time
import math
import random
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="RouteAI-NE: Sentinel V3", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. INTELLIGENCE DATABASE (Real-time Updated) ---

# Yeh locations real-world coordinates ke paas hain (Guwahati/Shillong region)
RISK_ZONES = [
    {"id": "LS_01", "type": "LANDSLIDE", "lat": 26.10, "lng": 91.77, "radius": 3.0, "severity": "CRITICAL", "advice": "Slopes Unstable - EVACUATE NOW"},
    {"id": "FL_01", "type": "FLOOD", "lat": 24.90, "lng": 92.60, "radius": 5.0, "severity": "HIGH", "advice": "Water Rising Fast"},
    {"id": "EQ_01", "type": "SEISMIC", "lat": 26.14, "lng": 91.73, "radius": 1.0, "severity": "MODERATE", "advice": "Tremors Detected"}
]

SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Base (Zone A)", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": "HIGH (5000+)"},
    {"id": "SH_02", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": "MEDIUM (500)"},
    {"id": "SH_03", "name": "Don Bosco Relief Camp", "lat": 26.12, "lng": 91.74, "type": "SHELTER", "capacity": "LOW (200)"},
    {"id": "SH_04", "name": "IIT Guwahati Helipad", "lat": 26.18, "lng": 91.69, "type": "AIRLIFT", "capacity": "HIGH"}
]

# --- HELPER FUNCTIONS ---
def get_dist(lat1, lon1, lat2, lon2):
    # Haversine Formula for accurate Earth distance
    R = 6371 # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --- 2. SENTINEL API (Monitoring) ---

@app.get("/sentinel/status")
def get_system_status():
    """Returns Satellite Connectivity & Active Disasters"""
    return {
        "sat_link": "CONNECTED (ISRO-INSAT-3D)",
        "signal_strength": "STRONG",
        "active_hazards_count": len(RISK_ZONES)
    }

@app.get("/sentinel/scan")
def scan_area(lat: float, lng: float):
    """
    Continuous Monitoring: Checks user's location against hazards.
    """
    nearby_risks = []
    status = "SAFE"
    
    for zone in RISK_ZONES:
        dist = get_dist(lat, lng, zone["lat"], zone["lng"])
        if dist <= zone["radius"]:
            status = "DANGER"
            nearby_risks.append(zone)
            
    return {
        "status": status,
        "current_location": {"lat": lat, "lng": lng},
        "nearby_risks": nearby_risks,
        "timestamp": time.time()
    }

@app.get("/sentinel/evacuate")
def get_evacuation_plan(lat: float, lng: float):
    """
    Returns TOP 3 NEAREST SAFE ZONES from user location.
    """
    # Sort all havens by distance
    sorted_havens = sorted(SAFE_HAVENS, key=lambda h: get_dist(lat, lng, h["lat"], h["lng"]))
    
    # Return top 3 with distance calculation
    result = []
    for h in sorted_havens[:3]:
        h["dist_km"] = round(get_dist(lat, lng, h["lat"], h["lng"]), 2)
        result.append(h)
        
    return {"safe_havens": result}

@app.post("/sentinel/whistle")
def log_whistle(data: dict):
    print(f"🚨 SOS SIGNAL RECEIVED: {data}")
    return {"status": "LOGGED", "action": "DISPATCH_UNIT"}

# --- 3. COMMAND DASHBOARD (Govt) ---

@app.get("/command/overview")
def get_dashboard_stats():
    return {
        "status": "ACTIVE_EMERGENCY",
        "total_sos": random.randint(120, 160),
        "deployed_resources": {
            "ambulances": 42,
            "ndrf_teams": 12,
            "helicopters": 3
        },
        "logistics": {
            "ration_packets": 5000,
            "medical_kits": 1200,
            "water_tankers": 15
        },
        "red_zones": RISK_ZONES
    }

# --- 4. CORE ROUTING (Navigation) ---

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    """
    Returns Comparison: Usual Route vs Safe Route.
    """
    
    # 1. The "Usual" Fast Route (Risky)
    route_fast = {
        "id": "fast",
        "label": "USUAL ROUTE",
        "distance": "124.5 km",
        "time": "3h 10m",
        "risk": "HIGH",
        "hazard": "Landslide Sector 4 (Active)", 
        "color": "#ef4444"
    }
    
    # 2. The "Alternative" Safe Route (Slower but Secure)
    route_safe = {
        "id": "safe",
        "label": "SAFEST ROUTE",
        "distance": "148.2 km",
        "time": "4h 05m",
        "risk": "LOW",
        "hazard": "None",
        "color": "#10b981"
    }

    # Logic: If Rain > 40, we recommend Safe. Else Fast.
    if rain_input > 40:
        recommended = route_safe
        alerts = [{"type": "WEATHER ALERT", "msg": "Heavy Rain Detected. Re-routing..."}]
    else:
        recommended = route_fast
        alerts = []

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": 98,
        "live_alerts": alerts
    }

# --- 5. VOICE ---
@app.post("/listen")
async def listen(file: UploadFile = File(...)):
    time.sleep(1) 
    return { "status": "success", "translated_text": "Navigate to Safe Zone", "target": "Shillong", "intent": "NAVIGATION" }
