from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import time
import os
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
    
    # Securely load API Key from Heroku Config
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    try:
        # LOGIC: If Key exists, try Real AI. If not, use Simulation.
        translated_text = "Navigate to Shillong" # Default Simulation
        
        if SARVAM_API_KEY:
            # Uncomment below lines for Real AI
            # files = {"file": (file.filename, file.file, file.content_type)}
            # headers = {"Ocp-Apim-Subscription-Key": SARVAM_API_KEY}
            # response = requests.post(SARVAM_URL, headers=headers, files=files)
            # translated_text = response.json().get("transcript", "Navigate to Shillong")
            print("✅ Key Found. Using (Simulated) Real Mode.")
        else:
            print("⚠️ No Key. Using Simulation Mode.")
            time.sleep(1.5)

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
