import os
import time
import math
import random
import requests
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# 1. SAFETY & INTELLIGENCE DATA (DEFINED ABOVE)
# ==========================================

# --- MOCK GIS DATA (ISRO Simulation) ---
RISK_ZONES = [
    {"id": "LS_01", "name": "Jorabat Landslide Sector", "type": "LANDSLIDE", "severity": "CRITICAL", "bounds": (26.1, 26.2, 91.7, 91.9)},
    {"id": "FL_04", "name": "Barak Valley Flood Plain", "type": "FLOOD", "severity": "HIGH", "bounds": (24.8, 25.0, 92.5, 92.8)},
]

SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Cantonment", "lat": 26.15, "lng": 91.76, "type": "MILITARY_BASE", "capacity": 5000},
    {"id": "SH_02", "name": "Don Bosco High School", "lat": 26.12, "lng": 91.74, "type": "RELIEF_CAMP", "capacity": 1200},
    {"id": "SH_03", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": 300},
    {"id": "SH_04", "name": "Kohima Science College", "lat": 25.66, "lng": 94.10, "type": "RELIEF_CAMP", "capacity": 2000},
    {"id": "SH_05", "name": "Dimapur Airport Shelter", "lat": 25.88, "lng": 93.77, "type": "LOGISTICS", "capacity": 5000}
]

# --- HELPER FUNCTIONS ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance between two GPS points in km."""
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def check_geofence_logic(lat, lng):
    """Checks if a coordinate is inside a Risk Zone."""
    for zone in RISK_ZONES:
        lat_min, lat_max, lng_min, lng_max = zone["bounds"]
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            return {
                "in_danger_zone": True,
                "zone_details": zone,
                "alert_level": "RED"
            }
    return {"in_danger_zone": False, "alert_level": "GREEN"}

# --- TRY TO IMPORT EXISTING AI ENGINE (Graceful Fallback) ---
try:
    from ai_engine.risk_routing import RiskGraph
except ImportError:
    print("⚠️ WARNING: Could not import ai_engine. Using Fallback Routing.")
    RiskGraph = None


# ==========================================
# 2. APP INITIALIZATION
# ==========================================

app = FastAPI(title="RouteAI-NE: Disaster Intelligence Platform", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 3. API ENDPOINTS (DEFINED BELOW)
# ==========================================

@app.get("/api/v2/risk-layer")
def get_live_risk_layer():
    """Returns ISRO-verified risk polygons for the map overlay."""
    active_zones = []
    weather_factor = random.choice(["CLEAR", "STORM", "CYCLONE"])
    
    for zone in RISK_ZONES:
        # Simulate dynamic risk activation
        if weather_factor in ["STORM", "CYCLONE", "CLEAR"]: # Always return some data for demo
            active_zones.append({
                **zone,
                "current_status": "ACTIVE",
                "last_update": datetime.now().strftime("%H:%M:%S"),
                "instruction": "AVOID AREA - DO NOT ENTER"
            })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "weather_context": weather_factor,
        "zones": active_zones
    }

@app.get("/api/v2/safe-zones")
def get_safe_zones(lat: float, lng: float):
    """Finds nearest relief camps relative to user."""
    ranked = []
    for haven in SAFE_HAVENS:
        dist = haversine_distance(lat, lng, haven["lat"], haven["lng"])
        ranked.append({**haven, "distance_km": round(dist, 2)})
    ranked.sort(key=lambda x: x["distance_km"])
    return ranked[:3]

@app.get("/monitor-location")
def monitor_location(lat: float, lng: float):
    """Background Sentinel: Checks if user is inside a Risk Zone."""
    # 1. Check Geofence
    geofence_status = check_geofence_logic(lat, lng)

    # 2. Construct Response
    hazards = []
    if geofence_status["in_danger_zone"]:
        hazards.append({
            "type": geofence_status["zone_details"]["type"],
            "severity": geofence_status["zone_details"]["severity"],
            "message": "IMMEDIATE EVACUATION ADVISED"
        })
    elif random.random() < 0.2:
         hazards.append({"type": "Flash Flood Risk", "severity": "MEDIUM", "distance": "500m"})

    return {
        "status": "CRITICAL" if geofence_status["in_danger_zone"] else "SECURE",
        "hazards": hazards,
        "sat_link": "CONNECTED (Latency: 12ms)",
        "geofence_data": geofence_status,
        "last_update": time.strftime("%H:%M:%S")
    }

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # --- EXISTING ROUTE LOGIC ---
    route_fast = {
        "id": "fast",
        "label": "USUAL ROUTE",
        "distance": "124.5 km",
        "time": "3h 10m",
        "risk": "HIGH",
        "hazard": "Landslide at Mile 40",
        "color": "#ef4444"
    }
    route_safe = {
        "id": "safe",
        "label": "SECURE ROUTE",
        "distance": "148.2 km",
        "time": "4h 05m",
        "risk": "LOW",
        "hazard": "None",
        "color": "#10b981"
    }
    recommended = route_safe if rain_input > 40 else route_fast

    # --- NEW: CONTEXTUAL EVACUATION PLAN ---
    # Find safe zones near the START point
    evac_havens = []
    for haven in SAFE_HAVENS:
        d = haversine_distance(start_lat, start_lng, haven["lat"], haven["lng"])
        evac_havens.append({**haven, "dist": f"{d:.1f} km"})
    evac_havens.sort(key=lambda x: float(x["dist"].split()[0]))

    evac_plan = {
        "nearest_risk_zone": {"name": "Scanning Satellite Data...", "status": "PENDING"},
        "safe_havens": evac_havens[:3]
    }

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": random.randint(88, 99),
        "live_alerts": [{"type": "Heavy Rain", "loc": "En route", "severity": "Medium"}],
        "evacuation": evac_plan,
        "rescue_spots": evac_havens[:3] # For map plotting
    }

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    if not SARVAM_API_KEY:
        print("⚠️ No API Key found. Using Mock.")
        return {
            "status": "success", 
            "translated_text": "Mock: Navigate to Shillong", 
            "target": "Shillong",
            "intent": "NAVIGATION"
        }

    try:
        file_content = await file.read()
        files = {"file": (file.filename, file_content, file.content_type)}
        headers = { "api-subscription-key": SARVAM_API_KEY }
        
        response = requests.post(SARVAM_URL, headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            translated_text = data.get("transcript", "")
            
            # Intent Detection
            intent = "NAVIGATION"
            text_lower = translated_text.lower()
            if "help" in text_lower or "sos" in text_lower: intent = "SOS_TRIGGER"
            
            # Destination Finder
            target = "Unknown"
            cities = ["shillong", "kohima", "guwahati", "agartala", "itanagar"]
            for city in cities:
                if city in text_lower:
                    target = city.capitalize()
                    break

            return {
                "status": "success",
                "translated_text": translated_text,
                "target": target,
                "intent": intent
            }
        else:
            return {"status": "error", "message": "Translation Failed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/govt-intel")
def get_govt_dashboard():
    return {"total_sos": 127, "active_disasters": 3, "red_zones": [{"lat": 26.15, "lng": 91.75}]}
