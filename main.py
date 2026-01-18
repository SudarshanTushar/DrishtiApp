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

# --- 1. CITIZEN API (Route & Hazards) ---
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # Dynamic Risk Calculation
    base_risk = "SAFE"
    score = random.randint(85, 98)
    if rain_input > 70: base_risk, score = "CRITICAL", random.randint(40, 60)
    elif rain_input > 40: base_risk, score = "MODERATE", random.randint(65, 80)

    # Live Hazards for the Citizen
    hazards = [
        {"type": "Landslide", "loc": "Nongpoh", "severity": "High"},
        {"type": "Heavy Rain", "loc": "Barapani", "severity": "Medium"}
    ]
    
    # NEW: Medical & Rescue Locations (Map Markers)
    rescue_spots = [
        {"name": "Army Base 101", "lat": start_lat + 0.02, "lng": start_lng + 0.01, "type": "MILITARY"},
        {"name": "Civil Hospital", "lat": start_lat - 0.01, "lng": start_lng + 0.02, "type": "HOSPITAL"},
        {"name": "NDRF Relief Camp", "lat": start_lat + 0.015, "lng": start_lng - 0.01, "type": "CAMP"}
    ]

    # NEW: Evacuation Plan for Citizen
    evac_plan = {
        "nearest_risk_zone": "Mile 12 Landslide Area", 
        "safe_locations": [
            {"name": "Assam Rifles Camp", "dist": "2.4 km", "type": "Military Base"},
            {"name": "Don Bosco School", "dist": "3.1 km", "type": "Relief Center"},
            {"name": "Civil Hospital", "dist": "4.8 km", "type": "Medical Aid"}
        ]
    }

    return {
        "distance": "124.5 km",
        "route_risk": base_risk,
        "confidence_score": score,
        "live_alerts": hazards,
        "rescue_spots": rescue_spots, 
        "evacuation": evac_plan
    }

# --- 2. GOVT COMMAND CENTER API (NEW) ---
# This simulates the "Big Picture" view for the Government
@app.get("/govt-intel")
def get_govt_dashboard():
    return {
        "total_sos": 127,
        "active_disasters": 3,
        "deployed_ambulances": 14,
        "drone_status": "AIRBORNE",
        "red_zones": [
            {"lat": 26.15, "lng": 91.75, "intensity": "HIGH"}, # SOS Cluster 1
            {"lat": 25.68, "lng": 94.12, "intensity": "MEDIUM"} # SOS Cluster 2
        ],
        "resources": {
            "ndrf_teams": 4,
            "ration_packets": 5000,
            "medical_kits": 1200
        }
    }

# --- 3. VOICE ENGINE (Existing Logic) ---
@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    if not SARVAM_API_KEY:
        return {"status": "error", "message": "API Key Missing"}

    try:
        file_content = await file.read()
        files = {"file": (file.filename, file_content, file.content_type)}
        headers = { "api-subscription-key": SARVAM_API_KEY }
        
        response = requests.post(SARVAM_URL, headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            translated_text = data.get("transcript", "")
            detected_lang = data.get("language_code", "en-IN")
            
            target = "Unknown"
            txt = translated_text.lower()
            if "shillong" in txt: target = "Shillong"
            elif "kohima" in txt: target = "Kohima"
            elif "guwahati" in txt: target = "Guwahati"

            return {
                "status": "success",
                "translated_text": translated_text,
                "language_code": detected_lang,
                "target": target
            }
        else:
            return {"status": "error", "message": "Translation Failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
