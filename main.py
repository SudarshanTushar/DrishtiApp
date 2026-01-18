import os
import time
import math
import random
import requests
import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from modules import intelligence, safety  # Ensure these modules exist as uploaded

app = FastAPI(title="RouteAI-NE: Disaster Intelligence Platform", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. V2 INTELLIGENCE LAYER (New) ---
@app.get("/api/v2/risk-layer")
def get_live_risk_layer():
    """Returns ISRO-verified risk polygons for the map overlay."""
    return intelligence.get_risk_heatmap()

@app.get("/govt-intel")
def get_govt_dashboard():
    """Returns Command Center metrics for Govt Mode."""
    return {
        "total_sos": random.randint(120, 150),
        "active_disasters": 3,
        "red_zones": intelligence.RISK_ZONES,
        "deployed_ambulances": 42,
        "drone_status": "SURVEILLANCE ACTIVE",
        "resources": {
            "ndrf_teams": 12,
            "ration_packets": 5000,
            "medical_kits": 1200
        }
    }

# --- 2. CORE ROUTING (Existing) ---
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # Simulation Logic
    time.sleep(0.5)
    
    route_fast = { "id": "fast", "label": "USUAL ROUTE", "distance": "124.5 km", "risk": "HIGH", "color": "#ef4444" }
    route_safe = { "id": "safe", "label": "SECURE ROUTE", "distance": "148.2 km", "risk": "LOW", "color": "#10b981" }
    
    # Get Evacuation Plan
    safe_zones = safety.find_nearest_safe_zones(start_lat, start_lng)

    return {
        "distance": "124.5 km",
        "route_risk": "HIGH" if rain_input > 40 else "LOW",
        "confidence_score": 92,
        "routes": [route_fast, route_safe],
        "evacuation": {
            "safe_havens": safe_zones
        },
        "rescue_spots": safe_zones
    }

@app.get("/monitor-location")
def monitor_location(lat: float, lng: float):
    """Background Sentinel for Geofencing."""
    status = intelligence.check_geofence(lat, lng)
    return {
        "geofence_data": status,
        "last_update": datetime.now().isoformat()
    }

# --- 3. VOICE INTERFACE (Existing) ---
@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    try:
        # Check for Key (Simulation Fallback)
        if not SARVAM_API_KEY:
            time.sleep(1)
            return { "status": "success", "translated_text": "Navigate to Shillong", "target": "Shillong", "intent": "NAVIGATION" }

        file_content = await file.read()
        files = {"file": (file.filename, file_content, file.content_type)}
        headers = { "Ocp-Apim-Subscription-Key": SARVAM_API_KEY }
        
        response = requests.post(SARVAM_URL, headers=headers, files=files)
        transcript = response.json().get("transcript", "")
        
        # Simple Intent Parsing
        intent = "SOS_TRIGGER" if "help" in transcript.lower() else "NAVIGATION"
        target = "Shillong" if "shillong" in transcript.lower() else "Unknown"

        return {
            "status": "success",
            "translated_text": transcript,
            "target": target,
            "intent": intent
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
