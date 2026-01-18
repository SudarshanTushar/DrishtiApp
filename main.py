from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import time
import os

app = FastAPI()

# --- CORS SETUP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. NAVIGATION ENDPOINT ---
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # Simulation Mode (Safe for Demo)
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
    print(f"🎤 Received Audio: {file.filename}")
    
    # Simulation Mode
    time.sleep(1.5)
    return {
        "status": "success",
        "detected_language": "hi-IN",
        "translated_text": "Navigate to Shillong",
        "action": "NAVIGATE",
        "target": "Shillong"
    }
