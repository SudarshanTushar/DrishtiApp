from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import time

# --- IMPORT ALL LAYERS ---
from core import routing, voice    # LAYER 1: Core Logic
from sentinel import risk_engine   # LAYER 2: Intelligence
from command import dashboard      # LAYER 3: Command & Control

app = FastAPI(title="RouteAI-NE: Sentinel V2", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTER ROUTERS ---
app.include_router(risk_engine.router) # /sentinel/...
app.include_router(dashboard.router)   # /command/...

# ==========================================
# 1. CORE OPERATIONS (Critical Path)
# ==========================================

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    """
    Calculates the safest route.
    Uses Core Logic + Sentinel Data.
    """
    # 1. Core Pathfinding
    route_data = routing.calculate_routes(start_lat, start_lng, end_lat, end_lng, rain_input)

    # 2. Sentinel Check (Is start point safe?)
    evac_havens = routing.find_nearest_safe_zones(start_lat, start_lng)

    return {
        **route_data,
        "evacuation": {
            "safe_havens": evac_havens
        },
        "rescue_spots": evac_havens
    }

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    """
    Voice Command Interface.
    Uses Sarvam AI (via Core Voice Module).
    """
    file_content = await file.read()
    return await voice.process_voice_command(file_content, file.filename, file.content_type)

# ==========================================
# 2. UTILITY ENDPOINTS
# ==========================================

@app.get("/monitor-location")
def monitor_location(lat: float, lng: float):
    """
    Background Geofence Monitor.
    Uses Sentinel Logic to check if user is in danger.
    """
    overlay = risk_engine.get_risk_overlay(lat, lng, radius_km=5)
    in_danger = len(overlay["zones"]) > 0
    
    return {
        "status": "CRITICAL" if in_danger else "SECURE",
        "geofence_data": {
            "in_danger_zone": in_danger,
            "zone_details": overlay["zones"][0] if in_danger else None
        },
        "last_update": time.strftime("%H:%M:%S")
    }
