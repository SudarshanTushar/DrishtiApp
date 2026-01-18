from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import time

# --- IMPORT MODULES ---
from core import routing, voice   # <--- The new Logic Core
from sentinel import risk_engine  # <--- The V2 Intelligence Layer

app = FastAPI(title="RouteAI-NE: Disaster Intelligence Platform", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER SENTINEL (V2) ---
app.include_router(risk_engine.router)

# ==========================================
# 1. CORE NAVIGATION ENDPOINTS
# ==========================================

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    """
    Core Routing Logic.
    Delegates math to core.routing module.
    """
    # 1. Get Route Calculations
    route_data = routing.calculate_routes(start_lat, start_lng, end_lat, end_lng, rain_input)

    # 2. Get Sentinel Context (Evacuation Zones)
    # We use the routing module's safe haven logic for consistency
    evac_havens = routing.find_nearest_safe_zones(start_lat, start_lng)

    # 3. Merge Data
    return {
        **route_data,
        "evacuation": {
            "nearest_risk_zone": "Scanning...", # Placeholder for V2 async scan
            "safe_havens": evac_havens
        },
        "rescue_spots": evac_havens
    }

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    """
    Voice Interface.
    Delegates AI processing to core.voice module.
    """
    file_content = await file.read()
    
    # Process with Sarvam AI
    result = await voice.process_voice_command(
        file_content, 
        file.filename, 
        file.content_type
    )
    
    return result

# ==========================================
# 2. LEGACY / UTILITY ENDPOINTS
# ==========================================

@app.get("/monitor-location")
def monitor_location(lat: float, lng: float):
    """
    V1 Endpoint kept for backward compatibility.
    Uses V2 Sentinel logic internally.
    """
    overlay = risk_engine.get_risk_overlay(lat, lng, radius_km=5)
    in_danger = len(overlay["zones"]) > 0
    
    return {
        "status": "CRITICAL" if in_danger else "SECURE",
        "hazards": overlay["zones"],
        "sat_link": "CONNECTED (Sentinel Core)",
        "last_update": time.strftime("%H:%M:%S")
    }
