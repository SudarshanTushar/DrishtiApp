from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import time
import os  # <--- IMPORT OS to read Heroku Settings
import requests

app = FastAPI()

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class LocationInput(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    rain_input: int

# --- 1. NAVIGATION ENGINE ---
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # Simulate AI calculation delay
    time.sleep(0.5)
    
    risk_level = "SAFE"
    score = 92
    if rain_input > 70:
        risk_level = "CRITICAL"
        score = 45
    elif rain_input > 40:
        risk_level = "MODERATE"
        score = 75

    return {
        "distance": "124.5 km",
        "route_risk": risk_level,
        "confidence_score": score,
        "flood_risk": random.randint(10, 90),
        "terrain_type": "Hilly" if start_lat > 26 else "Plain"
    }

# --- 2. VOICE LISTENER ---
@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    print(f"🎤 Received Audio File: {file.filename}")
    
    # ========================================================
    # 🔑 SECURE KEY LOADING FROM HEROKU
    # ========================================================
    # This reads the key from the Heroku Dashboard "Config Vars"
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    try:
        # OPTION A: REAL AI MODE (Active if Key is found)
        if SARVAM_API_KEY:
            # files = {"file": (file.filename, file.file, file.content_type)}
            # headers = {"Ocp-Apim-Subscription-Key": SARVAM_API_KEY}
            # response = requests.post(SARVAM_URL, headers=headers, files=files)
            # result = response.json()
            # translated_text = result.get("transcript", "")
            
            # Placeholder for demo until you uncomment the lines above
            print(f"✅ API Key found: {SARVAM_API_KEY[:4]}... Using Real Mode (Simulated for safety)")
            time.sleep(1)
            translated_text = "Navigate to Shillong"
        else:
            # OPTION B: FALLBACK SIMULATION (If Key is missing)
            print("⚠️ No API Key found in Heroku Settings. Using Simulation Mode.")
            time.sleep(1.5)
            translated_text = "Navigate to Shillong"

        # Determine Target
        target_city = "Unknown"
        if "Shillong" in translated_text:
            target_city = "Shillong"
        elif "Kohima" in translated_text:
            target_city = "Kohima"
        
        return {
            "status": "success",
            "detected_language": "hi-IN",
            "translated_text": translated_text,
            "action": "NAVIGATE",
            "target": target_city
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"status": "error", "message": str(e)}
