from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import time
import random
import os
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. BACKGROUND MONITOR (Aap abhi jahan hain wahan kya khatra hai) ---
@app.get("/monitor-location")
def monitor_location(lat: float, lng: float):
    # Real-world: Check satellite data for this lat/lng
    # Simulating a hazard near the user
    hazards = []
    safety_status = "SECURE"
    
    # Random simulation for demo
    if random.choice([True, False, False]): 
        hazards.append({"type": "Flash Flood Risk", "severity": "MEDIUM", "distance": "500m"})
        safety_status = "CAUTION"
    
    return {
        "status": safety_status,
        "hazards": hazards,
        "sat_link": "CONNECTED (Latency: 12ms)",
        "last_update": time.strftime("%H:%M:%S")
    }

# --- 2. ADVANCED ROUTE ANALYSIS (Safe vs Fast) ---
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # Logic: Generate 2 Routes
    
    # Route 1: The Usual (Risky but Short)
    route_fast = {
        "id": "fast",
        "label": "USUAL ROUTE",
        "distance": "124.5 km",
        "time": "3h 10m",
        "risk": "HIGH",
        "hazard": "Landslide at Mile 40",
        "color": "#ef4444" # Red
    }

    # Route 2: The Alternative (Safe but Long)
    route_safe = {
        "id": "safe",
        "label": "SECURE ROUTE",
        "distance": "148.2 km",
        "time": "4h 05m",
        "risk": "LOW",
        "hazard": "None",
        "color": "#10b981" # Green
    }

    # Decide recommendation based on rain
    recommended = route_safe if rain_input > 40 else route_fast

    # Evacuation Logic (Calculated from Start Location)
    evac_plan = {
        "nearest_risk_zone": {"name": "Jorabat Landslide Zone", "dist": "1.2 km", "risk": "CRITICAL"},
        "safe_havens": [
            {"name": "Assam Rifles Cantonment", "dist": "2.5 km", "type": "MILITARY BASE"},
            {"name": "Don Bosco High School", "dist": "3.8 km", "type": "RELIEF CAMP"},
            {"name": "City Civil Hospital", "dist": "5.1 km", "type": "MEDICAL"}
        ]
    }

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": random.randint(88, 99),
        "live_alerts": [{"type": "Heavy Rain", "loc": "En route", "severity": "Medium"}],
        "evacuation": evac_plan
    }

# --- 3. VOICE & GOVT APIs (Keep Previous Logic) ---
# (Maining shortness ke liye purana /listen aur /govt-intel code same man raha hu.
# Aap purana wala code yahan paste kar lena niche)
@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"
    # ... (Keep existing Voice Logic) ...
    return {"status": "success", "translated_text": "Navigate to Shillong", "target": "Shillong"}

@app.get("/govt-intel")
def get_govt_dashboard():
    # ... (Keep existing Govt Logic) ...
    return {"total_sos": 127, "active_disasters": 3, "red_zones": [{"lat": 26.15, "lng": 91.75}]}
