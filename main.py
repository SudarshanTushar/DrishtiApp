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

# --- 1. INTELLIGENT ROUTE ANALYSIS (LIVE UPDATES) ---
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # Simulate processing time
    # time.sleep(0.2) # Fast response for live feel

    # Dynamic Risk Calculation
    base_risk = "SAFE"
    score = random.randint(85, 98) # Fluctuating score (Live feel)
    
    if rain_input > 70:
        base_risk, score = "CRITICAL", random.randint(40, 60)
    elif rain_input > 40:
        base_risk, score = "MODERATE", random.randint(65, 80)

    # --- GENERATE LIVE HAZARD ALERTS (LOCATION SPECIFIC) ---
    hazards = [
        {"type": "Landslide", "loc": "Nongpoh", "severity": "High"},
        {"type": "Heavy Rain", "loc": "Barapani", "severity": "Medium"},
        {"type": "Fog", "loc": "Upper Shillong", "severity": "Low"},
        {"type": "Road Block", "loc": "Jorabat", "severity": "High"},
        {"type": "Clear Sky", "loc": "Guwahati Bypass", "severity": "Safe"},
        {"type": "Slippery Road", "loc": "Umiam Lake", "severity": "Medium"}
    ]
    
    # Pick 2-3 random active alerts
    current_alerts = random.sample(hazards, 3)

    return {
        "distance": "124.5 km",
        "route_risk": base_risk,
        "confidence_score": score,
        "flood_risk": random.randint(rain_input - 10, rain_input + 10), # Dynamic
        "terrain_type": "Hilly (70%) / Plain (30%)", # More specific
        "sat_status": "ONLINE",
        "live_alerts": current_alerts # Sending location-specific alerts
    }

# --- 2. MULTI-LANG VOICE ENGINE ---
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
            
            print(f"🗣️ User: {translated_text} [{detected_lang}]")
            
            # Universal Target Logic
            target = "Unknown"
            txt = translated_text.lower()
            if "shillong" in txt or "silong" in txt: target = "Shillong"
            elif "kohima" in txt: target = "Kohima"
            elif "guwahati" in txt: target = "Guwahati"
            elif "agartala" in txt: target = "Agartala"
            elif "itanagar" in txt: target = "Itanagar"
            elif "aizawl" in txt: target = "Aizawl"

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
