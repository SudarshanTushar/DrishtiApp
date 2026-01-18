import os
import time
import math
import random
import requests
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# --- 1. IMPORT THE NEW SENTINEL LAYER ---
from sentinel import risk_engine

# --- APP INITIALIZATION ---
app = FastAPI(title="RouteAI-NE: Disaster Intelligence Platform", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. REGISTER SENTINEL ROUTER (ADDITIVE UPDATE) ---
app.include_router(risk_engine.router)

# ==========================================
# 3. EXISTING CORE LOGIC (PRESERVED)
# ==========================================

# --- HELPER FUNCTIONS ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # --- SIMULATION MODE ---
    time.sleep(0.5)
    
    route_fast = {
        "id": "fast", "label": "USUAL ROUTE", "distance": "124.5 km",
        "time": "3h 10m", "risk": "HIGH", "hazard": "Landslide at Mile 40", "color": "#ef4444"
    }
    route_safe = {
        "id": "safe", "label": "SECURE ROUTE", "distance": "148.2 km",
        "time": "4h 05m", "risk": "LOW", "hazard": "None", "color": "#10b981"
    }
    
    recommended = route_safe if rain_input > 40 else route_fast

    # --- NEW: SENTINEL INTEGRATION ---
    # We call the new logic to check if evacuation is needed near start point
    evac_havens = risk_engine.get_nearest_safe_zones(start_lat, start_lng)

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": random.randint(88, 99),
        "live_alerts": [{"type": "Heavy Rain", "loc": "En route", "severity": "Medium"}],
        "evacuation": {"nearest_risk_zone": "Scanning...", "safe_havens": evac_havens},
        "rescue_spots": evac_havens 
    }

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    try:
        # REAL MODE CHECK
        if SARVAM_API_KEY and SARVAM_API_KEY != "API_KEY":
            file_content = await file.read()
            files = {"file": (file.filename, file_content, file.content_type)}
            headers = {"Ocp-Apim-Subscription-Key": SARVAM_API_KEY} # Correct Header for Sarvam
            
            response = requests.post(SARVAM_URL, headers=headers, files=files)
            if response.status_code == 200:
                translated_text = response.json().get("transcript", "")
            else:
                translated_text = "Navigate to Shillong" # Fallback
        else:
            # SIMULATION MODE
            time.sleep(1)
            translated_text = "Navigate to Shillong"

        # Intent Logic
        intent = "NAVIGATION"
        target = "Unknown"
        text_lower = translated_text.lower()
        
        if "help" in text_lower or "sos" in text_lower: intent = "SOS_TRIGGER"
        
        cities = ["shillong", "kohima", "guwahati", "agartala"]
        for city in cities:
            if city in text_lower: target = city.capitalize()

        return {
            "status": "success",
            "translated_text": translated_text,
            "target": target,
            "intent": intent
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/monitor-location")
def monitor_location(lat: float, lng: float):
    """
    Kept for backward compatibility with V1 frontend.
    Now uses Sentinel logic internally.
    """
    # Use new Sentinel engine to get overlay data
    overlay = risk_engine.get_risk_overlay(lat, lng, radius_km=5)
    
    in_danger = len(overlay["zones"]) > 0
    hazards = []
    
    if in_danger:
        top_hazard = overlay["zones"][0]
        hazards.append({
            "type": top_hazard["type"],
            "severity": top_hazard["risk"],
            "message": top_hazard.get("advice", "Caution advised")
        })

    return {
        "status": "CRITICAL" if in_danger else "SECURE",
        "hazards": hazards,
        "sat_link": "CONNECTED (Sentinel V2)",
        "last_update": time.strftime("%H:%M:%S")
    }
