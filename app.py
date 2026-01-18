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

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    time.sleep(0.5)
    risk = "SAFE"
    score = 92
    if rain_input > 70:
        risk, score = "CRITICAL", 45
    elif rain_input > 40:
        risk, score = "MODERATE", 75

    return {
        "distance": "124.5 km",
        "route_risk": risk,
        "confidence_score": score,
        "flood_risk": random.randint(10, 90),
        "terrain_type": "Hilly" if start_lat > 26 else "Plain"
    }

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
        
        # Call Sarvam AI
        response = requests.post(SARVAM_URL, headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            translated_text = data.get("transcript", "")
            
            # ✅ DETECT LANGUAGE (Agar Sarvam bhejta hai, nahi toh default 'hi-IN')
            # Sarvam aksar 'language_code' bhejta hai response mein
            detected_lang = data.get("language_code", "en-IN") 
            
            print(f"🗣️ Detected: {translated_text} | Lang: {detected_lang}")
            
            # --- UNIVERSAL DESTINATION FINDER ---
            target = "Unknown"
            text_lower = translated_text.lower()
            
            if "shillong" in text_lower or "silong" in text_lower: target = "Shillong"
            elif "kohima" in text_lower: target = "Kohima"
            elif "guwahati" in text_lower: target = "Guwahati"
            elif "agartala" in text_lower: target = "Agartala"
            elif "itanagar" in text_lower: target = "Itanagar"
            elif "aizawl" in text_lower: target = "Aizawl"

            return {
                "status": "success",
                "translated_text": translated_text,
                "language_code": detected_lang, # Sending Lang Code to Frontend
                "target": target
            }
        else:
            return {"status": "error", "message": "Translation Failed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
