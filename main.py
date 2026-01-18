from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import time
import requests  # Required for real AI calls (pip install requests)

app = FastAPI()

# ==========================================
# 🔌 CORS SETUP (CRITICAL FOR MOBILE APP)
# ==========================================
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

# ==========================================
# 🧠 1. NAVIGATION ENGINE (Risk Analysis)
# ==========================================
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    # Simulate sophisticated AI calculation delay
    time.sleep(0.5)
    
    # Logic: If rain is high, risk is high
    risk_level = "SAFE"
    score = 92
    
    if rain_input > 70:
        risk_level = "CRITICAL"
        score = 45
    elif rain_input > 40:
        risk_level = "MODERATE"
        score = 75

    # Return Tactical Data
    return {
        "distance": "124.5 km",
        "route_risk": risk_level,
        "confidence_score": score,
        "flood_risk": random.randint(10, 90),
        "terrain_type": "Hilly" if start_lat > 26 else "Plain"
    }

# ==========================================
# 🎤 2. VOICE LISTENER (Sarvam AI / Bhashini)
# ==========================================
@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    print(f"🎤 Received Audio File: {file.filename}")
    
    # 🔑 TODO: PASTE YOUR APPROVED API KEY HERE
    SARVAM_API_KEY = "sk_pnc5sbtu_r64TZyLFiLK8airZBaV7kbOl"
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

    try:
        # =====================================================
        # OPTION A: REAL AI MODE (Use when Key is Approved)
        # =====================================================
        # Uncomment the lines below to enable real translation:
        
        # files = {"file": (file.filename, file.file, file.content_type)}
        # headers = {"Ocp-Apim-Subscription-Key": SARVAM_API_KEY}
        # response = requests.post(SARVAM_URL, headers=headers, files=files)
        # result = response.json()
        # translated_text = result.get("transcript", "")
        # print(f"🤖 Real AI Heard: {translated_text}")

        # =====================================================
        # OPTION B: SIMULATION MODE (For Hackathon Demo)
        # =====================================================
        # We simulate that the user said "Navigate to Shillong"
        print("⚠️ Simulating AI Translation (Demo Mode)...")
        time.sleep(1.5)
        
        simulated_text = "Navigate to Shillong" 
        # In real mode, change this to: simulated_text = translated_text
        
        # Determine Target City logic
        target_city = "Unknown"
        if "Shillong" in simulated_text:
            target_city = "Shillong"
        elif "Kohima" in simulated_text:
            target_city = "Kohima"
        
        return {
            "status": "success",
            "detected_language": "hi-IN",
            "translated_text": simulated_text,
            "action": "NAVIGATE",
            "target": target_city
        }

    except Exception as e:
        print(f"❌ Error processing audio: {e}")
        return {"status": "error", "message": str(e)}

# ==========================================
# 🚀 HOW TO RUN THIS SERVER
# ==========================================
# 1. Open Terminal in 'backend' folder
# 2. Run: pip install python-multipart requests
# 3. Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000