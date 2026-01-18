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
        risk = "CRITICAL"
        score = 45
    elif rain_input > 40:
        risk = "MODERATE"
        score = 75

    return {
        "distance": "124.5 km",
        "route_risk": risk,
        "confidence_score": score,
        "flood_risk": random.randint(10, 90),
        "terrain_type": "Hilly" if start_lat > 26 else "Plain"
    }

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    # 🔑 Get Key from Heroku
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    if not SARVAM_API_KEY:
        return {"status": "error", "message": "API Key Missing"}

    try:
        # Read file correctly
        file_content = await file.read()
        files = {"file": (file.filename, file_content, file.content_type)}
        
        # ✅ Correct Header for Sarvam
        headers = { "api-subscription-key": SARVAM_API_KEY }
        
        # Call API
        response = requests.post(SARVAM_URL, headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            translated_text = data.get("transcript", "")
            print(f"🗣️ AI Heard: {translated_text}")
            
            # Destination Logic
            target = "Unknown"
            text_lower = translated_text.lower()
            if "shillong" in text_lower: target = "Shillong"
            elif "kohima" in text_lower: target = "Kohima"
            elif "guwahati" in text_lower: target = "Guwahati"

            return {
                "status": "success",
                "translated_text": translated_text,
                "target": target
            }
        else:
            print(f"❌ API Error: {response.text}")
            return {"status": "error", "message": "Translation Failed"}

    except Exception as e:
        print(f"❌ Internal Server Error: {str(e)}")
        return {"status": "error", "message": str(e)}
