from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import requests
import random
from pydantic import BaseModel

# --- IMPORT INTELLIGENCE MODULES ---
from intelligence.governance import SafetyGovernance
from intelligence.risk_model import LandslidePredictor
from intelligence.languages import LanguageConfig # NEW IMPORT

app = FastAPI(title="RouteAI-NE Government Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = LandslidePredictor()

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    ai_result = predictor.predict(rain_input, start_lat, start_lng)
    
    governance_result = SafetyGovernance.validate_risk(
        rain_mm=rain_input, 
        slope_angle=ai_result["slope_angle"], 
        ai_prediction_score=ai_result["ai_score"]
    )

    return {
        "distance": f"{random.randint(110, 140)}.5 km",
        "route_risk": governance_result["risk"],
        "confidence_score": governance_result["score"],
        "reason": governance_result["reason"],
        "source": governance_result["source"],
        "terrain_data": {
            "type": "Hilly" if start_lat > 26 else "Plain",
            "slope": f"{ai_result['slope_angle']}°",
            "soil": ai_result["soil_type"]
        }
    }

# --- NEW: LANGUAGE CONFIG ENDPOINT ---
@app.get("/languages")
def get_languages():
    return LanguageConfig.get_config()

@app.get("/offline-pack")
def download_offline_intel(region_id: str):
    return {
        "region": "NE-Sector-Alpha",
        "timestamp": time.time(),
        "emergency_contacts": ["112", "108", "0361-222222"],
        "safe_zones": [
            {"name": "Guwahati Army Camp", "lat": 26.14, "lng": 91.73},
            {"name": "Shillong Civil Hospital", "lat": 25.57, "lng": 91.88}
        ]
    }

# --- UPDATED VOICE HANDLER (MULTI-LANGUAGE) ---
@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...), language_code: str = Form("hi-IN")):
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    try:
        if SARVAM_API_KEY:
            files = {"file": (file.filename, file.file, file.content_type)}
            # Pass language_code if your API supports it, or handle translation logic here
            headers = {"Ocp-Apim-Subscription-Key": SARVAM_API_KEY}
            response = requests.post(SARVAM_URL, headers=headers, files=files)
            translated_text = response.json().get("transcript", "Navigate to Shillong")
        else:
            time.sleep(1)
            translated_text = "Navigate to Shillong"

        target_city = "Shillong" if "shillong" in translated_text.lower() else "Unknown"
        
        # Get response in requested language (Simulated translation for response)
        fallback_responses = LanguageConfig.OFFLINE_RESPONSES.get(language_code, LanguageConfig.OFFLINE_RESPONSES["en-IN"])
        voice_reply = f"{fallback_responses['SAFE']} ({target_city})" if target_city != "Unknown" else "Command not understood."

        return {
            "status": "success",
            "translated_text": translated_text,
            "voice_reply": voice_reply, # The text the phone should speak back
            "target": target_city
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
