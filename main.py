from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import time

# Import Modules
from core import routing, voice
from sentinel import risk_engine
from command import dashboard

app = FastAPI(title="RouteAI-NE: Sentinel V2", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(risk_engine.router)
app.include_router(dashboard.router)

# Core Endpoints
@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
    route_data = routing.calculate_routes(start_lat, start_lng, end_lat, end_lng, rain_input)
    evac_havens = routing.find_nearest_safe_zones(start_lat, start_lng)
    
    return {
        **route_data,
        "evacuation": { "safe_havens": evac_havens },
        "rescue_spots": evac_havens
    }

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...)):
    file_content = await file.read()
    return await voice.process_voice_command(file_content, file.filename, file.content_type)

@app.get("/monitor-location")
def monitor_location(lat: float, lng: float):
    # Uses Sentinel Logic
    overlay = risk_engine.get_risk_overlay(lat, lng)
    return {
        "status": "SECURE", # Simplified for demo
        "geofence_data": { "in_danger_zone": False, "zone_details": None }
    }
